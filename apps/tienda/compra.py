"""La compra online (plan 07, sexta parte): `CU-TDA-CMP` y `CU-TDA-INV`.

El recorrido tiene dos mitades, y la separación es la de los contratos:

- **Antes del pago** nada cambia en el dominio. `CO-179` y `CO-180` verifican,
  `CO-087` guarda la dirección del checkout en la sesión, `CO-103` y `CO-104`
  marcan líneas del carrito sin tocar ningún lote de puntos, y `CO-088` (o
  `CO-091`) congela lo que se cobra en un `CobroEnCurso` y manda al Cliente a
  la pasarela.
- **Al aprobarse el pago**, `CO-089` materializa todo en una sola transacción:
  pedido, líneas, transacción de pago, stock, puntos y carrito. Un pago
  rechazado no deja nada que revertir, porque no se escribió nada.

**El stock no se reserva hasta `CO-089`** (`CO-083`, notas). Dos clientes pueden
estar pagando el último ejemplar; el primero que aprueba se lo lleva, y el
segundo cae en E3: reembolso, carrito intacto y aviso (B-07-035).
"""

import logging
import secrets
from dataclasses import dataclass, field
from datetime import timedelta
from decimal import Decimal
from functools import cached_property

from django.db import transaction
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone

from apps.accounts.models import Usuario
from apps.catalog.models import Producto
from apps.core.mail import cuerpo_html, enviar_correo
from apps.core.models import ConfiguracionSistema, RegistroAuditoria
from apps.pedidos.models import LineaPedido, Pedido, TransaccionPago
from apps.pedidos.servicios import registrar_transicion
from apps.puntos import servicios as puntos
from apps.puntos.models import LotePuntos
from apps.tienda import carrito as servicio_carrito
from apps.tienda.envio import costo_de_envio, estado_de_envio
from apps.tienda.models import Carrito, CobroEnCurso, LineaCarrito

logger = logging.getLogger(__name__)

CAMPOS_DE_ENVIO = ("direccion", "depto", "localidad", "provincia", "codigo_postal")
OBLIGATORIOS_DE_ENVIO = ("direccion", "localidad", "provincia", "codigo_postal")


class BloqueoDeAvance(ValueError):
    """`CO-179`, `CO-180` E1, `CO-090` E2: el carrito no se puede comprar así.

    El mensaje es el que lee el Cliente; el control vuelve al carrito, que marca
    las líneas a resolver.
    """


class CanjeRechazado(ValueError):
    """`CO-103` E1: el saldo no alcanza para cubrir la línea entera."""


class FalloDeMaterializacion(RuntimeError):
    """`CO-089` E3: el pago se aprobó y el pedido no se pudo generar."""


# ---------------------------------------------------------------------------
# Envío (B-07-032)
# ---------------------------------------------------------------------------


def direccion_predeterminada(usuario):
    """La del perfil del Cliente (`CU-TDA-CMP` paso 2). Vacía si no la cargó."""
    return {campo: getattr(usuario, campo, "") or "" for campo in CAMPOS_DE_ENVIO}


def direccion_completa(envio):
    return all((envio or {}).get(campo) for campo in OBLIGATORIOS_DE_ENVIO)


def texto_de_direccion(envio):
    envio = envio or {}
    partes = [envio.get("direccion"), envio.get("depto"), envio.get("localidad")]
    provincia = " ".join(p for p in (envio.get("provincia"), envio.get("codigo_postal")) if p)
    return ", ".join(p for p in [*partes, provincia] if p)


# ---------------------------------------------------------------------------
# El resumen del checkout
# ---------------------------------------------------------------------------


@dataclass
class LineaDeCheckout:
    consultada: servicio_carrito.LineaConsultada
    puntos_necesarios: int

    @property
    def linea(self):
        return self.consultada.linea

    @property
    def producto(self):
        return self.consultada.producto

    @property
    def precio(self):
        return self.consultada.precio

    @property
    def importe(self):
        """El precio de la línea entera, a precio con oferta (`CO-103`, notas)."""
        return self.consultada.subtotal

    @property
    def cubierta(self):
        return self.linea.cubierta_con_puntos

    @property
    def a_pagar(self):
        return Decimal("0") if self.cubierta else self.importe


@dataclass
class Resumen:
    """`CO-180` (salida) y `CO-090` (salida): lo que el Cliente confirma."""

    lineas: list = field(default_factory=list)
    costo_envio: Decimal = Decimal("0")
    envio: dict = field(default_factory=dict)
    saldo: int = 0
    minimo_envio_gratuito: Decimal = Decimal("0")
    con_puntos: bool = True
    # Plan 07, octava parte: sin dirección y sin costo de envío.
    retiro: bool = False

    @property
    def subtotal_productos(self):
        return sum((linea.importe for linea in self.lineas), Decimal("0"))

    @property
    def subtotal_dinero(self):
        return sum((linea.a_pagar for linea in self.lineas), Decimal("0"))

    @property
    def cubierto_con_puntos(self):
        return self.subtotal_productos - self.subtotal_dinero

    @property
    def total(self):
        return self.subtotal_dinero + self.costo_envio

    @property
    def puntos_aplicados(self):
        return sum(linea.puntos_necesarios for linea in self.lineas if linea.cubierta)

    @property
    def saldo_restante(self):
        """Informativo (`CO-103`, salida): todavía no se debitó nada."""
        return self.saldo - self.puntos_aplicados

    @property
    def puntos_a_acreditar(self):
        return puntos.puntos_por_monto(self.subtotal_dinero) if self.con_puntos else 0

    @property
    def envio_gratis(self):
        return self.costo_envio == 0

    @cached_property
    def estado_envio(self):
        """La barra del envío gratis (B-07-037)."""
        return estado_de_envio(self.subtotal_productos)

    @property
    def direccion_completa(self):
        return self.retiro or direccion_completa(self.envio)

    @property
    def tiene_pre_venta(self):
        return any(linea.consultada.pre_venta for linea in self.lineas)


def resumen(carrito, *, usuario=None, envio=None, retiro=False):
    """Las líneas con su precio de hoy, el canje, el envío y el total.

    Un invitado no tiene puntos: sus líneas nunca están cubiertas, aunque una
    marca quedara de antes (`CO-090`: «No se ofrece opción de canje»).
    """
    configuracion = ConfiguracionSistema.obtener()
    consultado = servicio_carrito.consultar(carrito)
    con_puntos = bool(usuario and usuario.is_authenticated)
    lineas = []
    for item in consultado.lineas:
        if not con_puntos:
            item.linea.cubierta_con_puntos = False
        lineas.append(
            LineaDeCheckout(
                consultada=item,
                puntos_necesarios=puntos.puntos_para_cubrir(
                    item.subtotal, configuracion.equivalencia_puntos
                ),
            )
        )
    retiro = bool(retiro and con_puntos)  # D4: sólo con cuenta
    hecho = Resumen(
        lineas=lineas,
        envio={} if retiro else dict(envio or {}),
        saldo=puntos.saldo(usuario) if con_puntos else 0,
        minimo_envio_gratuito=configuracion.monto_minimo_envio_gratuito,
        con_puntos=con_puntos,
        retiro=retiro,
    )
    hecho.costo_envio = (
        Decimal("0") if retiro else costo_de_envio(hecho.subtotal_productos, configuracion)
    )
    return hecho


# ---------------------------------------------------------------------------
# CO-179 procederAlPago · CO-180 iniciarCheckout · CO-181 iniciarCompraComoInvitado
# ---------------------------------------------------------------------------


def proceder_al_pago(carrito):
    """`CO-179`: al menos una línea y todas Disponibles. Sólo lee."""
    consultado = servicio_carrito.consultar(carrito)
    if consultado.vacio:
        raise BloqueoDeAvance("Tu carrito está vacío.")
    if not consultado.se_puede_pagar:
        raise BloqueoDeAvance(
            "Para avanzar al pago, quitá los productos no disponibles y ajustá las "
            "cantidades marcadas."
        )
    return consultado


def iniciar_checkout(carrito, usuario, envio, *, retiro=False):
    """`CO-180`: el resumen, verificando en el momento que todo conserve stock (E1)."""
    consultado = servicio_carrito.consultar(carrito)
    afectadas = [
        item.producto.titulo
        for item in consultado.lineas
        if item.disponibilidad != servicio_carrito.DISPONIBLE
    ]
    if consultado.vacio:
        raise BloqueoDeAvance("Tu carrito está vacío.")
    if afectadas:
        raise BloqueoDeAvance(
            "Mientras armabas el pedido cambió la disponibilidad de "
            + ", ".join(f"«{titulo}»" for titulo in afectadas)
            + ". Revisá el carrito antes de seguir."
        )
    return resumen(carrito, usuario=usuario, envio=envio, retiro=retiro)


def iniciar_compra_como_invitado(carrito):
    """`CO-181`: la compra de invitado no admite pre-ventas (precondición)."""
    consultado = proceder_al_pago(carrito)
    reservas = [item.producto.titulo for item in consultado.lineas if item.pre_venta]
    if reservas:
        raise BloqueoDeAvance(
            "Reservar una pre-venta requiere una cuenta: "
            + ", ".join(f"«{titulo}»" for titulo in reservas)
            + ". Iniciá sesión o quitala del carrito para comprar como invitado."
        )
    return consultado


def cuenta_con_correo(correo):
    """`CU-TDA-INV` A1 (B-07-036): si el correo es de una cuenta de cliente."""
    return Usuario.objects.filter(email__iexact=correo, rol=Usuario.CLIENTE).exists()


# ---------------------------------------------------------------------------
# CO-087 declararDireccionDeEnvio
# ---------------------------------------------------------------------------


def declarar_direccion_de_envio(sesion, direccion, subtotal_productos):
    """La dirección del checkout en curso pasa a la declarada.

    Se guarda en la sesión: **`Usuario` no se toca** (postcondición negativa).
    Devuelve el costo de envío, que no depende del destino (B-07-032).
    """
    sesion[CLAVE_ENVIO] = {campo: direccion.get(campo, "") for campo in CAMPOS_DE_ENVIO}
    return costo_de_envio(subtotal_productos)


CLAVE_ENVIO = "checkout_envio"
CLAVE_RETIRO = "checkout_retiro"
CLAVE_INVITADO = "checkout_invitado"
CLAVE_COBROS = "checkout_cobros"


def declarar_modalidad(sesion, retiro):
    """`CO-087` (plan 07, octava parte): envío a domicilio o retiro en el local.

    Como la dirección, vive en la sesión del checkout: no cambia el perfil.
    """
    sesion[CLAVE_RETIRO] = bool(retiro)


def retiro_del_checkout(sesion):
    return bool(sesion.get(CLAVE_RETIRO))


def envio_del_checkout(sesion, usuario):
    """La declarada en este checkout, o la del perfil si no se declaró ninguna."""
    declarada = sesion.get(CLAVE_ENVIO)
    if declarada:
        return declarada
    return direccion_predeterminada(usuario)


# ---------------------------------------------------------------------------
# CO-103 aplicarCanjeDePuntosAItem · CO-104 revertirCanjeDePuntosDeItem
# ---------------------------------------------------------------------------


def aplicar_canje(linea, usuario):
    """`CO-103`: la línea queda cubierta con puntos, con precio efectivo cero.

    El saldo se verifica contra el precio **de hoy** de la línea (E2) y contra
    lo que ya comprometieron las otras líneas marcadas. **Ningún `LotePuntos`
    cambia** y no se audita: el débito es de `CO-089`.
    """
    disponible = puntos.saldo(usuario)
    if disponible <= 0:
        raise CanjeRechazado("No tenés puntos disponibles para canjear.")
    hecho = resumen(linea.carrito, usuario=usuario)
    propia = next((item for item in hecho.lineas if item.linea.pk == linea.pk), None)
    if propia is None or propia.cubierta:
        return hecho
    if propia.puntos_necesarios > hecho.saldo_restante:
        raise CanjeRechazado(
            f"Para cubrir «{linea.producto.titulo}» hacen falta {propia.puntos_necesarios} "
            f"puntos y te quedan {hecho.saldo_restante}. No se puede canjear una parte "
            "del precio: probá con otro producto."
        )
    LineaCarrito.objects.filter(pk=linea.pk).update(cubierta_con_puntos=True)
    return resumen(linea.carrito, usuario=usuario)


def revertir_canje(linea, usuario):
    """`CO-104`: la línea vuelve a su precio. Ningún `LotePuntos` cambia."""
    LineaCarrito.objects.filter(pk=linea.pk).update(cubierta_con_puntos=False)
    return resumen(linea.carrito, usuario=usuario)


def verificar_canje(hecho):
    """Que el saldo de hoy alcance para todo lo marcado; si no, se pide revisar."""
    if hecho.puntos_aplicados > hecho.saldo:
        raise CanjeRechazado(
            f"Las líneas marcadas suman {hecho.puntos_aplicados} puntos y tu saldo es de "
            f"{hecho.saldo}. Quitá el canje de alguna antes de confirmar."
        )


# ---------------------------------------------------------------------------
# CO-088 confirmarPedido · CO-091 confirmarPedidoDeInvitado
# ---------------------------------------------------------------------------


@dataclass
class Confirmacion:
    cobro: CobroEnCurso
    redireccion: str | None = None
    pedido: Pedido | None = None


def _congelar(hecho, carrito, *, pasarela, request, usuario=None, correo_invitado=""):
    """El cobro en curso: lo que se cobra, como está en este momento (B-07-034)."""
    return CobroEnCurso.objects.create(
        referencia=secrets.token_hex(16),
        origen=request.build_absolute_uri("/").rstrip("/"),
        pasarela=pasarela,
        usuario=usuario,
        correo_invitado=correo_invitado,
        carrito=carrito,
        envio={campo: hecho.envio.get(campo, "") for campo in CAMPOS_DE_ENVIO},
        lineas=[
            {
                "producto": item.producto.pk,
                "cantidad": item.linea.cantidad,
                "precio": str(item.precio),
                "puntos": item.puntos_necesarios if item.cubierta else 0,
            }
            for item in hecho.lineas
        ],
        costo_envio=hecho.costo_envio,
        monto=hecho.total,
        puntos_a_debitar=hecho.puntos_aplicados,
        retiro=hecho.retiro,
    )


def confirmar_pedido(carrito, usuario, envio, request, pasarela, *, retiro=False):
    """`CO-088`: congela el cobro y, según el total, va a la pasarela o confirma.

    Total mayor que cero: ninguna postcondición sobre el dominio, sólo la
    solicitud de cobro. Total cero (A2, sólo con envío gratuito): las
    postcondiciones de `CO-089` en el momento, sin `TransaccionPago`.
    """
    hecho = iniciar_checkout(carrito, usuario, envio, retiro=retiro)
    if not hecho.direccion_completa:
        raise BloqueoDeAvance("Completá la dirección de envío antes de confirmar.")
    verificar_canje(hecho)
    cobro = _congelar(hecho, carrito, pasarela=pasarela.clave, request=request, usuario=usuario)
    if cobro.monto == 0:
        cobro = registrar_resultado(cobro.referencia, referencia_pago=None, monto=Decimal("0"))
        return Confirmacion(cobro=cobro, pedido=cobro.pedido)
    return _solicitar_cobro(cobro, pasarela, request)


def confirmar_pedido_de_invitado(carrito, datos, request, pasarela):
    """`CO-091`: no hay variante de total cero; siempre va a la pasarela."""
    iniciar_compra_como_invitado(carrito)
    hecho = iniciar_checkout(carrito, None, datos)
    cobro = _congelar(
        hecho, carrito, pasarela=pasarela.clave, request=request, correo_invitado=datos["correo"]
    )
    return _solicitar_cobro(cobro, pasarela, request)


def _solicitar_cobro(cobro, pasarela, request):
    """La solicitud de cobro con su referencia. Si la pasarela no la acepta, no se
    cobró nada: el cobro queda descartado y el Cliente puede volver a intentar."""
    redireccion = pasarela.iniciar_cobro(cobro, request)
    if not redireccion:
        cobro.estado = CobroEnCurso.RECHAZADO
        cobro.mensaje = "La pasarela no aceptó iniciar el cobro."
        cobro.resuelto_en = timezone.now()
        cobro.save(update_fields=["estado", "mensaje", "resuelto_en"])
    return Confirmacion(cobro=cobro, redireccion=redireccion)


# ---------------------------------------------------------------------------
# CO-089 registrarResultadoDePago
# ---------------------------------------------------------------------------


def registrar_resultado_de_pago(aviso, pasarela):
    """El aviso de la pasarela. Idempotente: un cobro resuelto no se vuelve a tocar."""
    if not aviso.aprobado:
        return registrar_rechazo(aviso.referencia, aviso.mensaje)
    return registrar_resultado(
        aviso.referencia,
        referencia_pago=aviso.referencia_pago,
        monto=aviso.monto,
        pasarela=pasarela,
    )


def registrar_rechazo(referencia, mensaje):
    """E2: no se genera pedido ni se toca stock ni puntos. Queda en el log."""
    with transaction.atomic():
        cobro = CobroEnCurso.objects.select_for_update().filter(referencia=referencia).first()
        if cobro is None or cobro.estado != CobroEnCurso.PENDIENTE:
            return cobro
        cobro.estado = CobroEnCurso.RECHAZADO
        cobro.mensaje = mensaje or "La pasarela rechazó el pago."
        cobro.resuelto_en = timezone.now()
        cobro.save(update_fields=["estado", "mensaje", "resuelto_en"])
        RegistroAuditoria.registrar(
            accion=RegistroAuditoria.PAGO_RECHAZADO,
            actor=cobro.usuario,
            actor_email=cobro.correo_de_contacto,
            objetivo=cobro,
            detalle=f"Cobro {cobro.referencia} por {cobro.monto}: {cobro.mensaje}",
        )
    return cobro


def registrar_resultado(referencia, *, referencia_pago, monto, pasarela=None):
    """Pago aprobado: materializa el pedido, o reembolsa si no se puede (E3).

    El cobro se toma con bloqueo: dos avisos repetidos que llegan a la vez se
    ordenan, y el segundo encuentra el cobro ya procesado y no hace nada.
    """
    tardio = _reembolso_tardio(referencia, referencia_pago, monto)
    if tardio is not None:
        if pasarela is not None:
            pasarela.reembolsar(tardio, referencia_pago)
        _avisar_fallo(tardio)
        return tardio
    fallo = None
    with transaction.atomic():
        cobro = CobroEnCurso.objects.select_for_update().filter(referencia=referencia).first()
        if cobro is None or cobro.estado != CobroEnCurso.PENDIENTE:
            return cobro
        try:
            if monto != cobro.monto:
                raise FalloDeMaterializacion(
                    f"La pasarela informó {monto} y el cobro era por {cobro.monto}."
                )
            with transaction.atomic():
                if cobro.tipo == CobroEnCurso.DESPACHO:
                    from apps.almacen.servicios import materializar_despacho

                    materializar_despacho(cobro, referencia_pago)
                    pedido = None
                else:
                    pedido = _materializar(cobro, referencia_pago)
        except Exception as error:  # noqa: BLE001 - E3: todo fallo técnico se reembolsa
            fallo = error
            logger.exception("No se pudo generar el pedido del cobro %s.", cobro.referencia)
            # Sin pasarela (A2) no hubo cargo: no hay nada que reembolsar.
            cobro.estado = CobroEnCurso.REEMBOLSADO if referencia_pago else CobroEnCurso.RECHAZADO
            cobro.mensaje = str(error)[:300]
            cobro.resuelto_en = timezone.now()
            cobro.save(update_fields=["estado", "mensaje", "resuelto_en"])
            RegistroAuditoria.registrar(
                accion=RegistroAuditoria.INCIDENTE_COMPRA,
                actor=cobro.usuario,
                actor_email=cobro.correo_de_contacto,
                objetivo=cobro,
                detalle=(
                    f"Cobro {cobro.referencia} aprobado por {monto} sin pedido: {error}."
                    + (" Se inició el reembolso." if referencia_pago else "")
                ),
            )
        else:
            if pedido is not None:
                transaction.on_commit(lambda: _avisar_confirmacion(pedido, cobro.origen))

    if fallo is not None and referencia_pago:
        if pasarela is not None:
            pasarela.reembolsar(cobro, referencia_pago)
        _avisar_fallo(cobro)
    return cobro


# ---------------------------------------------------------------------------
# Los cobros abandonados (plan 00, C3)
# ---------------------------------------------------------------------------

ABANDONO = timedelta(hours=24)


def descartar_abandonados(ahora=None):
    """El Temporizador descarta los cobros pendientes de más de 24 horas.

    Es el mismo plazo que deja de comprometer los puntos de un canje
    (B-10-005). No toca stock ni puntos: un cobro pendiente todavía no
    reservó nada.
    """
    ahora = ahora or timezone.now()
    return CobroEnCurso.objects.filter(
        estado=CobroEnCurso.PENDIENTE, creado_en__lt=ahora - ABANDONO
    ).update(
        estado=CobroEnCurso.DESCARTADO,
        mensaje="Abandonado: la pasarela no avisó en 24 horas.",
        resuelto_en=ahora,
    )


def _reembolso_tardio(referencia, referencia_pago, monto):
    """Un pago que la pasarela aprueba después de descartado el cobro se reembolsa:
    el carrito ya pudo cambiar (plan 00, ambigüedad 7). Idempotente."""
    if not referencia_pago:
        return None
    with transaction.atomic():
        cobro = CobroEnCurso.objects.select_for_update().filter(referencia=referencia).first()
        if cobro is None or cobro.estado != CobroEnCurso.DESCARTADO:
            return None
        cobro.estado = CobroEnCurso.REEMBOLSADO
        cobro.mensaje = "Pago aprobado después de descartado el cobro: se reembolsa."
        cobro.resuelto_en = timezone.now()
        cobro.save(update_fields=["estado", "mensaje", "resuelto_en"])
        RegistroAuditoria.registrar(
            accion=RegistroAuditoria.INCIDENTE_COMPRA,
            actor=cobro.usuario,
            actor_email=cobro.correo_de_contacto,
            objetivo=cobro,
            detalle=(
                f"Cobro {cobro.referencia} aprobado por {monto} después de descartado por "
                "abandono. Se inició el reembolso."
            ),
        )
    return cobro


def _materializar(cobro, referencia_pago):
    """Las postcondiciones de `CO-089`, en orden. Se llama dentro de un `atomic`.

    Los productos se bloquean en orden de clave: dos compras que comparten
    productos los toman en el mismo orden y no se interbloquean (B-13-006).
    """
    ahora = timezone.now()
    ids = [linea["producto"] for linea in cobro.lineas]
    productos = {
        p.pk: p for p in Producto.objects.select_for_update().filter(pk__in=ids).order_by("pk")
    }
    for linea in cobro.lineas:
        producto = productos.get(linea["producto"])
        if producto is None or producto.estado not in (Producto.ACTIVO, Producto.PRE_VENTA):
            raise FalloDeMaterializacion("Un producto del pedido dejó de estar a la venta.")
        if producto.estado == Producto.ACTIVO and producto.stock < linea["cantidad"]:
            raise FalloDeMaterializacion(f"Ya no hay stock suficiente de «{producto.titulo}».")

    con_pre_venta = any(
        productos[linea["producto"]].estado == Producto.PRE_VENTA for linea in cobro.lineas
    )
    # (a)(b)(c) El pedido, con su estado inicial según RF-18 y la dirección copiada.
    if cobro.retiro and not cobro.usuario_id:
        raise FalloDeMaterializacion("El retiro en el local requiere una cuenta.")  # D4
    envio = {} if cobro.retiro else (cobro.envio or {})
    pedido = Pedido.objects.create(
        canal=Pedido.ONLINE,
        modalidad=Pedido.RETIRO if cobro.retiro else Pedido.ENVIO,
        estado=Pedido.ESPERANDO_PRE_VENTA if con_pre_venta else Pedido.PENDIENTE_ARMADO,
        usuario=cobro.usuario,
        correo_invitado="" if cobro.usuario_id else cobro.correo_invitado,
        envio_direccion=envio.get("direccion", ""),
        envio_depto=envio.get("depto", ""),
        envio_localidad=envio.get("localidad", ""),
        envio_provincia=envio.get("provincia", ""),
        envio_codigo_postal=envio.get("codigo_postal", ""),
        costo_envio=cobro.costo_envio,
        fecha=ahora,
    )
    pedido.asignar_numero()
    registrar_transicion(pedido, None, cobro.usuario, ahora)

    subtotal_dinero = Decimal("0")
    for linea in cobro.lineas:
        producto = productos[linea["producto"]]
        precio = Decimal(linea["precio"])
        cubierta = linea["puntos"] > 0
        LineaPedido.objects.create(
            pedido=pedido,
            producto=producto,
            cantidad=linea["cantidad"],
            precio_unitario=precio,
            cubierta_con_puntos=cubierta,
            puntos_canjeados=linea["puntos"],
            estado=(
                LineaPedido.RESERVADO
                if producto.estado == Producto.PRE_VENTA
                else LineaPedido.DISPONIBLE
            ),
        )
        if not cubierta:
            subtotal_dinero += precio * linea["cantidad"]
        # (c) El stock de lo inmediato baja; lo que llega a cero pasa a Agotado.
        # Por `update()`: `Producto.save()` no se usa sobre la fila padre.
        if producto.estado == Producto.ACTIVO:
            queda = producto.stock - linea["cantidad"]
            Producto.objects.filter(pk=producto.pk).update(
                stock=queda,
                estado=Producto.AGOTADO if queda == 0 else Producto.ACTIVO,
                actualizado_en=ahora,
            )

    # (a)(b)(c) La transacción de pago. Sin pasarela (A2), no hay.
    if referencia_pago:
        TransaccionPago.objects.create(
            pedido=pedido,
            medio=TransaccionPago.PASARELA,
            monto=cobro.monto,
            estado=TransaccionPago.APROBADO,
            referencia=referencia_pago,
            registrada_en=ahora,
        )

    # (c) Puntos: el débito de lo canjeado y la acreditación de lo pagado en
    # dinero, sin el envío (B-07-033). Un invitado no tiene puntos.
    acreditados = 0
    if cobro.usuario_id:
        puntos.debitar(cobro.usuario, cobro.puntos_a_debitar, pedido=pedido)
        acreditados = puntos.puntos_por_monto(subtotal_dinero)
        puntos.acreditar(cobro.usuario, acreditados, origen=LotePuntos.COMPRA, pedido=pedido)

    # (a) El carrito pierde las líneas compradas (B-07-034).
    if cobro.carrito_id:
        LineaCarrito.objects.filter(carrito_id=cobro.carrito_id, producto_id__in=ids).delete()
        Carrito.objects.filter(pk=cobro.carrito_id).update(actualizado_en=ahora)

    cobro.estado = CobroEnCurso.PROCESADO
    cobro.pedido = pedido
    cobro.resuelto_en = ahora
    cobro.save(update_fields=["estado", "pedido", "resuelto_en"])

    RegistroAuditoria.registrar(
        accion=RegistroAuditoria.COMPRA_ONLINE,
        actor=cobro.usuario,
        actor_email=cobro.correo_de_contacto,
        objetivo=pedido,
        detalle=(
            f"Pedido {pedido.numero} ({pedido.get_estado_display()}): "
            f"{len(cobro.lineas)} línea(s), cobrado {cobro.monto}"
            + (
                ", retiro en el local"
                if cobro.retiro
                else (f", envío {cobro.costo_envio}" if cobro.costo_envio else ", envío gratis")
            )
            + (f", canjeó {cobro.puntos_a_debitar} pts" if cobro.puntos_a_debitar else "")
            + (f", acreditó {acreditados} pts" if acreditados else "")
            + ("" if referencia_pago else ", sin pasarela (todo con puntos)")
            + "."
        ),
    )
    return pedido


# ---------------------------------------------------------------------------
# Los correos, después del commit
# ---------------------------------------------------------------------------


def _avisar_confirmacion(pedido, origen=""):
    """`CU-TDA-CMP` paso 7, `CU-TDA-INV` paso 9. Si el correo falla, el pedido queda.

    Con cuenta, lleva el enlace de seguimiento al pedido en «Mi cuenta» (`CU-CLI-HIS`).
    El invitado sigue su pedido por correo.
    """
    try:
        contexto = {"pedido": pedido, "lineas": list(pedido.lineas.select_related("producto"))}
        if pedido.usuario_id and origen:
            contexto["enlace"] = origen + reverse("cuenta:pedido", args=[pedido.numero])
        enviar_correo(
            asunto=f"Recibimos tu pedido {pedido.numero}",
            cuerpo=_texto("tienda/correo_pedido.txt", contexto),
            destinatarios=[pedido.correo_de_contacto],
            html=cuerpo_html("correo/pedido_confirmado.html", contexto),
        )
    except Exception:  # noqa: BLE001 - el pedido ya existe: un correo caído no lo deshace
        logger.exception("No se pudo enviar la confirmación del pedido %s.", pedido.numero)


def _avisar_fallo(cobro):
    """E3: el cargo se revierte. Se avisa por correo además de la pantalla."""
    if cobro.tipo == CobroEnCurso.DESPACHO:
        from apps.pedidos import avisos

        avisos.avisar(
            [cobro.correo_de_contacto],
            asunto="No pudimos generar tu envío: el cargo se revierte",
            rotulo="Stock en local",
            antetitulo="Envío de stock almacenado",
            titulo="Envío no generado",
            parrafos=[
                "El pago se aprobó, pero uno de los artículos ya no estaba disponible. "
                "El cargo se revierte en tu medio de pago.",
            ],
        )
        return
    contexto = {"cobro": cobro}
    try:
        enviar_correo(
            asunto="No pudimos completar tu compra: el cargo se revierte",
            cuerpo=_texto("tienda/correo_compra_fallida.txt", contexto),
            destinatarios=[cobro.correo_de_contacto],
            html=cuerpo_html("correo/compra_fallida.html", contexto),
        )
    except Exception:  # noqa: BLE001
        logger.exception("No se pudo avisar el fallo del cobro %s.", cobro.referencia)


def _texto(plantilla, contexto):
    return render_to_string(plantilla, contexto)
