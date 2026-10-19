"""El stock almacenado en local (plan 18).

El artículo entra cuando llega uno de despacho diferido (`CO-095` opción 2,
desde `CO-013`). El Cliente lo consulta (`CO-215`) y pide el envío (`CO-216`,
`CO-151`, con el pago de `CO-089` si corresponde). El local lo despacha
(`CO-152`) o lo entrega en el mostrador (`CO-227`), el Administrador cambia su
plazo (`CO-153`) y el Temporizador lo vence (`CO-154`).

**Orden de bloqueo: producto, artículo.** Las escrituras que tocan stock toman
primero el producto, como el resto del sistema.
"""

import logging
import secrets
from dataclasses import dataclass, field
from datetime import timedelta
from decimal import Decimal
from functools import partial

from django.conf import settings
from django.db import transaction
from django.db.models import F, Q
from django.urls import reverse
from django.utils import timezone

from apps.almacen.models import (
    EXTENSION_AUTOMATICA,
    ArticuloRetenido,
    SolicitudDespacho,
    vencimiento_desde,
)
from apps.catalog.models import Producto
from apps.core.models import ConfiguracionSistema, RegistroAuditoria
from apps.pedidos import avisos
from apps.pedidos.models import TransaccionPago

logger = logging.getLogger(__name__)

CAMPOS_DE_ENVIO = ("direccion", "depto", "localidad", "provincia", "codigo_postal")
OBLIGATORIOS_DE_ENVIO = ("direccion", "localidad", "provincia", "codigo_postal")


class OperacionRechazada(ValueError):
    """El artículo no está como hace falta, o los datos no alcanzan."""


def nombre(articulo):
    return str(articulo.producto.especifico)


def fecha(dia):
    return dia.strftime("%d/%m/%Y") if dia else "—"


def _enlace(origen, nombre_url, *args):
    origen = origen or settings.URL_PUBLICA
    return origen + reverse(nombre_url, args=args) if origen else ""


# ---------------------------------------------------------------------------
# El ingreso: la opción 2 de CO-095 cuando el artículo llega (B-18-002)
# ---------------------------------------------------------------------------


def _retener(linea, hoy, vence):
    """Un artículo por unidad de la línea (B-18-002). La procedencia la da el pedido."""
    pedido = linea.pedido
    return ArticuloRetenido.objects.bulk_create(
        ArticuloRetenido(
            usuario_id=pedido.usuario_id,
            producto_id=linea.producto_id,
            linea_pedido=linea,
            valor=linea.precio_unitario,
            fecha_ingreso=hoy,
            fecha_vencimiento=vence,
            procedencia=(
                ArticuloRetenido.PARA_RETIRAR
                if pedido.retiro
                else ArticuloRetenido.DESPACHO_DIFERIDO
            ),
        )
        for _ in range(linea.cantidad)
    )


def retener_linea(linea, actor, *, origen=""):
    """Un artículo por unidad de la línea, Disponible, con el plazo de Parámetros.

    Se llama dentro de la transacción de `CO-013`: si el ingreso se deshace, los
    artículos también. En un pedido para retirar, el artículo demorado que llega
    queda con esa procedencia (plan 07, octava parte, ambigüedad 3).
    """
    hoy = timezone.localdate()
    vence = vencimiento_desde(hoy, ConfiguracionSistema.obtener().plazo_retencion_meses)
    pedido = linea.pedido
    articulos = _retener(linea, hoy, vence)
    RegistroAuditoria.registrar(
        accion=RegistroAuditoria.INGRESO_STOCK_ALMACENADO,
        actor=actor,
        objetivo=pedido.usuario,
        detalle=(
            f"Pedido {pedido.numero}: {len(articulos)} × {linea.producto} al stock almacenado "
            f"de {pedido.correo_de_contacto}, vence el {fecha(vence)}."
        ),
    )
    transaction.on_commit(partial(_avisar_ingreso, pedido, linea, vence, origen))
    return articulos


def _avisar_ingreso(pedido, linea, vence, origen):
    avisos.avisar(
        [pedido.correo_de_contacto],
        asunto=f"Tu pedido {pedido.numero}: llegó el artículo demorado",
        antetitulo=f"Pedido {pedido.numero}",
        titulo="Llegó tu artículo",
        parrafos=[
            f"Llegó {linea.producto.especifico}. Queda en el local a tu nombre: podés pedir "
            "el envío o retirarlo.",
        ],
        filas=[("Guardado hasta", fecha(vence))],
        enlace=_enlace(origen, "cuenta:stock"),
        texto_enlace="Ver mi stock en el local",
    )


# ---------------------------------------------------------------------------
# El pedido para retirar (plan 07, octava parte): CO-092 de Armado a En el local
# ---------------------------------------------------------------------------


def guardar_pedido_para_retirar(pedido, actor):
    """Cada unidad de lo armado entra al stock en local del Cliente.

    Se llama dentro de la transacción de `CO-092`. Las líneas demoradas, las
    canceladas y las de despacho diferido no entran acá: la diferida entra
    cuando llega, por `retener_linea`. El aviso es el del cambio de estado.
    """
    from apps.pedidos.models import LineaPedido

    hoy = timezone.localdate()
    vence = vencimiento_desde(hoy, ConfiguracionSistema.obtener().plazo_retencion_meses)
    lineas = list(
        pedido.lineas.filter(estado__in=(LineaPedido.DISPONIBLE, LineaPedido.EMPAQUETADO))
        .exclude(decision_demora=LineaPedido.DESPACHO_DIFERIDO)
        .select_related("producto")
    )
    articulos = []
    for linea in lineas:
        linea.pedido = pedido
        articulos.extend(_retener(linea, hoy, vence))
    if articulos:
        RegistroAuditoria.registrar(
            accion=RegistroAuditoria.INGRESO_STOCK_ALMACENADO,
            actor=actor,
            objetivo=pedido.usuario,
            detalle=(
                f"Pedido {pedido.numero} para retirar: {len(articulos)} artículo(s) al stock "
                f"almacenado de {pedido.correo_de_contacto}, vencen el {fecha(vence)}."
            ),
        )
    return articulos


# ---------------------------------------------------------------------------
# CO-215 consultarStockAlmacenadoPropio · CO-217 consultarStockAlmacenado
# ---------------------------------------------------------------------------


def dias_de_aviso():
    return ConfiguracionSistema.obtener().dias_aviso_retencion


def del_cliente(usuario):
    """`CO-215`: lo que el local guarda hoy a su nombre (los finales, no)."""
    return (
        ArticuloRetenido.objects.filter(usuario=usuario)
        .exclude(estado__in=ArticuloRetenido.FINALES)
        .select_related("producto", "producto__productoeditorial", "linea_pedido__pedido")
        .order_by("fecha_vencimiento", "pk")
    )


@dataclass
class Filtros:
    cliente: str = ""
    producto: str = ""
    estado: str = ""
    desde: object = None
    hasta: object = None

    @property
    def activos(self):
        return any((self.cliente, self.producto, self.estado, self.desde, self.hasta))


def consultar(filtros):
    """`CO-217`: todos los clientes, todos los estados, con los filtros de la ficha."""
    articulos = ArticuloRetenido.objects.select_related(
        "usuario", "producto", "producto__productoeditorial", "solicitud"
    )
    if filtros.cliente:
        q = filtros.cliente
        articulos = articulos.filter(
            Q(usuario__email__icontains=q)
            | Q(usuario__first_name__icontains=q)
            | Q(usuario__last_name__icontains=q)
            | Q(usuario__codigo_cliente=q)
        )
    if filtros.producto:
        q = filtros.producto
        articulos = articulos.filter(Q(producto__titulo__icontains=q) | Q(producto__codigo=q))
    if filtros.estado:
        articulos = articulos.filter(estado=filtros.estado)
    if filtros.desde:
        articulos = articulos.filter(fecha_vencimiento__gte=filtros.desde)
    if filtros.hasta:
        articulos = articulos.filter(fecha_vencimiento__lte=filtros.hasta)
    return articulos.order_by("fecha_vencimiento", "pk")


def historial_de_plazo(articulo):
    """`CO-218`: los cambios de plazo, del registro de auditoría (los de `CO-153`
    y las extensiones automáticas de `CO-154`)."""
    from django.contrib.contenttypes.models import ContentType

    return RegistroAuditoria.objects.filter(
        objetivo_tipo=ContentType.objects.get_for_model(ArticuloRetenido),
        objetivo_pk=articulo.pk,
        accion__in=(RegistroAuditoria.PLAZO_RETENCION, RegistroAuditoria.VENCIMIENTO_RETENCION),
    ).order_by("-ocurrido_en", "-pk")


# ---------------------------------------------------------------------------
# CO-216 solicitarDespachoDeStockAlmacenado · CO-151 confirmarDespachoDeStockAlmacenado
# ---------------------------------------------------------------------------


def direccion_predeterminada(usuario):
    return {campo: getattr(usuario, campo, "") or "" for campo in CAMPOS_DE_ENVIO}


def direccion_completa(envio):
    return all((envio or {}).get(campo) for campo in OBLIGATORIOS_DE_ENVIO)


def texto_de_direccion(envio):
    envio = envio or {}
    partes = [envio.get("direccion"), envio.get("depto"), envio.get("localidad")]
    provincia = " ".join(p for p in (envio.get("provincia"), envio.get("codigo_postal")) if p)
    return ", ".join(p for p in [*partes, provincia] if p)


@dataclass
class ResumenDespacho:
    articulos: list
    envio: dict
    valor: Decimal = Decimal("0")
    costo_envio: Decimal = Decimal("0")
    minimo: Decimal = Decimal("0")

    @property
    def gratis(self):
        return self.costo_envio == 0

    @property
    def direccion_completa(self):
        return direccion_completa(self.envio)

    @property
    def texto_direccion(self):
        return texto_de_direccion(self.envio)


def resumen_de_despacho(usuario, ids, envio):
    """`CO-216`: el valor, el costo de envío y la dirección. No registra nada.

    El envío es gratis desde el monto mínimo, como en la compra (B-18-007).
    """
    from apps.tienda.envio import costo_de_envio

    articulos = list(
        ArticuloRetenido.objects.filter(
            pk__in=ids, usuario=usuario, estado=ArticuloRetenido.DISPONIBLE
        ).select_related("producto", "producto__productoeditorial")
    )
    if not articulos:
        raise OperacionRechazada("Elegí al menos un artículo disponible.")
    if len(articulos) != len(set(ids)):
        raise OperacionRechazada("Uno de los artículos elegidos ya no está disponible.")
    configuracion = ConfiguracionSistema.obtener()
    valor = sum((a.valor for a in articulos), Decimal("0"))
    # Plan 00, C1: el reemplazo de un cambio por garantía viaja sin costo.
    sin_costo = all(a.de_cambio for a in articulos)
    return ResumenDespacho(
        articulos=articulos,
        envio={campo: (envio or {}).get(campo, "") for campo in CAMPOS_DE_ENVIO},
        valor=valor,
        costo_envio=Decimal("0") if sin_costo else costo_de_envio(valor, configuracion),
        minimo=configuracion.monto_minimo_envio_gratuito,
    )


@dataclass
class Despacho:
    solicitud: SolicitudDespacho | None = None
    cobro: object = None
    redireccion: str | None = None


def confirmar_despacho(usuario, ids, envio, *, request, pasarela=None):
    """`CO-151`. Gratis: la solicitud queda generada. Pago (A1): se congela el
    cobro y se va a la pasarela; la solicitud se genera cuando el pago se aprueba."""
    hecho = resumen_de_despacho(usuario, ids, envio)
    if not hecho.direccion_completa:
        raise OperacionRechazada("Completá la dirección de envío antes de confirmar.")  # E1
    origen = request.build_absolute_uri("/").rstrip("/")
    if hecho.gratis:
        with transaction.atomic():
            solicitud = _generar_solicitud(
                usuario, [a.pk for a in hecho.articulos], hecho.envio, Decimal("0"), origen
            )
        return Despacho(solicitud=solicitud)

    from apps.tienda.compra import _solicitar_cobro
    from apps.tienda.models import CobroEnCurso

    cobro = CobroEnCurso.objects.create(
        referencia=secrets.token_hex(16),
        tipo=CobroEnCurso.DESPACHO,
        origen=origen,
        pasarela=pasarela.clave,
        usuario=usuario,
        envio=hecho.envio,
        lineas=[{"articulo": a.pk} for a in hecho.articulos],
        costo_envio=hecho.costo_envio,
        monto=hecho.costo_envio,
    )
    confirmacion = _solicitar_cobro(cobro, pasarela, request)
    return Despacho(cobro=confirmacion.cobro, redireccion=confirmacion.redireccion)


def materializar_despacho(cobro, referencia_pago):
    """`CO-089` para un cobro de envío: la solicitud y su transacción.

    Se llama dentro del `atomic` de `registrar_resultado`. Si un artículo ya no
    está Disponible —venció o se pidió en otra pestaña mientras se pagaba—, se
    levanta y la compra reembolsa (E3).
    """
    ids = [linea["articulo"] for linea in cobro.lineas]
    solicitud = _generar_solicitud(cobro.usuario, ids, cobro.envio, cobro.costo_envio, cobro.origen)
    TransaccionPago.objects.create(
        solicitud=solicitud,
        medio=TransaccionPago.PASARELA,
        monto=cobro.monto,
        estado=TransaccionPago.APROBADO,
        referencia=referencia_pago,
    )
    cobro.estado = cobro.PROCESADO
    cobro.solicitud = solicitud
    cobro.resuelto_en = timezone.now()
    cobro.save(update_fields=["estado", "solicitud", "resuelto_en"])
    return solicitud


def _generar_solicitud(usuario, ids, envio, costo, origen):
    """Las postcondiciones de `CO-151` sobre artículos tomados con bloqueo."""
    articulos = list(
        ArticuloRetenido.objects.select_for_update(of=("self",))
        .filter(pk__in=ids, usuario=usuario)
        .select_related("producto")
        .order_by("pk")
    )
    if len(articulos) != len(set(ids)) or any(
        a.estado != ArticuloRetenido.DISPONIBLE for a in articulos
    ):
        raise OperacionRechazada("Uno de los artículos elegidos ya no está disponible.")
    solicitud = SolicitudDespacho.objects.create(
        usuario=usuario,
        envio_direccion=envio.get("direccion", ""),
        envio_depto=envio.get("depto", ""),
        envio_localidad=envio.get("localidad", ""),
        envio_provincia=envio.get("provincia", ""),
        envio_codigo_postal=envio.get("codigo_postal", ""),
        costo_envio=costo,
    )
    ArticuloRetenido.objects.filter(pk__in=[a.pk for a in articulos]).update(
        estado=ArticuloRetenido.PENDIENTE_DESPACHO, solicitud=solicitud
    )
    RegistroAuditoria.registrar(
        accion=RegistroAuditoria.SOLICITUD_DESPACHO,
        actor=usuario,
        objetivo=solicitud,
        objetivo_email=usuario.email,
        detalle=(
            f"Solicitud {solicitud.numero}: {len(articulos)} artículo(s), envío "
            + ("gratis" if not costo else f"{costo} pagado")
            + "."
        ),
    )
    transaction.on_commit(partial(_avisar_solicitud, solicitud, articulos, origen))
    return solicitud


def _avisar_solicitud(solicitud, articulos, origen):
    """`CU-STK-DES` paso 5: el Administrador recibe la solicitud."""
    avisos.avisar_administradores(
        asunto=f"Envío de stock almacenado {solicitud.numero}",
        rotulo="Stock en local",
        antetitulo="Solicitud de despacho",
        titulo=solicitud.numero,
        parrafos=[
            f"{solicitud.usuario.get_full_name() or solicitud.usuario.email} pidió el envío "
            f"de {len(articulos)} artículo(s) a {solicitud.direccion_de_envio}.",
        ],
        filas=[("Artículo", nombre(a)) for a in articulos],
        enlace=_enlace(origen, "almacen:solicitud", solicitud.pk),
        texto_enlace="Ver la solicitud",
    )


# ---------------------------------------------------------------------------
# CO-152 confirmarDespachoFisico · CO-227 confirmarRetiroEnLocal
# ---------------------------------------------------------------------------


def despachar(ids, actor, *, origen=""):
    """`CO-152` sobre uno o varios artículos de una solicitud (B-18-007).

    Todos o ninguno: si alguno cambió de estado desde que se lo vio (E1), no se
    registra nada.
    """
    with transaction.atomic():
        articulos = list(
            ArticuloRetenido.objects.select_for_update(of=("self",))
            .filter(pk__in=ids)
            .select_related("usuario", "producto", "solicitud")
            .order_by("pk")
        )
        if not articulos or len(articulos) != len(set(ids)):
            raise OperacionRechazada("No se encontraron los artículos.")
        if any(a.estado != ArticuloRetenido.PENDIENTE_DESPACHO for a in articulos):
            raise OperacionRechazada(
                "Un artículo cambió de estado desde que lo abriste: no se registró nada."
            )
        ArticuloRetenido.objects.filter(pk__in=[a.pk for a in articulos]).update(
            estado=ArticuloRetenido.DESPACHADO
        )
        for articulo in articulos:
            RegistroAuditoria.registrar(
                accion=RegistroAuditoria.DESPACHO_STOCK_ALMACENADO,
                actor=actor,
                objetivo=articulo,
                objetivo_email=articulo.usuario.email,
                detalle=(
                    f"{nombre(articulo)}: Pendiente de despacho → Despachado "
                    f"(solicitud {articulo.solicitud.numero})."
                ),
            )
        transaction.on_commit(partial(_avisar_despacho, articulos, origen))
    return articulos


def _avisar_despacho(articulos, origen):
    solicitud = articulos[0].solicitud
    avisos.avisar(
        [articulos[0].usuario.email],
        asunto=f"Tu envío {solicitud.numero} salió",
        rotulo="Stock en local",
        antetitulo=f"Envío {solicitud.numero}",
        titulo="Despachado",
        parrafos=[f"Despachamos tus artículos a {solicitud.direccion_de_envio}."],
        filas=[("Artículo", nombre(a)) for a in articulos],
    )


def disponibles_del_pedido(pedido_pk):
    """Lo que un pedido tiene todavía para entregar en el mostrador."""
    return (
        ArticuloRetenido.objects.filter(
            linea_pedido__pedido_id=pedido_pk, estado=ArticuloRetenido.DISPONIBLE
        )
        .select_related("usuario", "producto", "producto__productoeditorial", "linea_pedido")
        .order_by("pk")
    )


def retirar_pedido(pedido_pk, actor, ids_vistos):
    """«Entregar todo» (plan 07, octava parte, ambigüedad 5): `CO-227` sobre cada
    artículo disponible del pedido, con el titular verificado una sola vez.

    Todo o nada: si alguno cambió desde que se vio, no se registra ninguno.
    """
    with transaction.atomic():
        articulos = list(
            ArticuloRetenido.objects.select_for_update(of=("self",))
            .filter(pk__in=ids_vistos, linea_pedido__pedido_id=pedido_pk)
            .select_related("usuario", "producto")
            .order_by("pk")
        )
        if not articulos or len(articulos) != len(set(ids_vistos)):
            raise OperacionRechazada("No hay artículos para entregar en este pedido.")
        if any(a.estado != ArticuloRetenido.DISPONIBLE for a in articulos):
            raise OperacionRechazada(
                "Un artículo cambió de estado desde que lo abriste: no se registró nada."
            )
        for articulo in articulos:
            retirar(articulo.pk, actor)
    return articulos


def retirar(articulo_pk, actor):
    """`CO-227`: lo entrega el mostrador al titular. No se avisa: está presente."""
    with transaction.atomic():
        articulo = (
            ArticuloRetenido.objects.select_for_update(of=("self",))
            .select_related("usuario", "producto")
            .get(pk=articulo_pk)
        )
        if articulo.estado != ArticuloRetenido.DISPONIBLE:
            raise OperacionRechazada(
                "El artículo cambió de estado desde que lo abriste: no se registró nada."
            )
        articulo.estado = ArticuloRetenido.RETIRADO
        articulo.save(update_fields=["estado", "actualizado_en"])
        RegistroAuditoria.registrar(
            accion=RegistroAuditoria.RETIRO_EN_LOCAL,
            actor=actor,
            objetivo=articulo,
            objetivo_email=articulo.usuario.email,
            detalle=(
                f"{nombre(articulo)}: Disponible → Retirado en local por "
                f"{articulo.usuario.get_full_name() or articulo.usuario.email}."
            ),
        )
    return articulo


# ---------------------------------------------------------------------------
# CO-153 modificarPlazoDeRetencion
# ---------------------------------------------------------------------------


def modificar_plazo(articulo_pk, actor, nueva_fecha, motivo, *, origen=""):
    motivo = (motivo or "").strip()
    if nueva_fecha is None or nueva_fecha <= timezone.localdate():
        raise OperacionRechazada("La nueva fecha debe ser posterior a hoy.")  # E1
    if not motivo:
        raise OperacionRechazada("El motivo es obligatorio.")  # E2
    with transaction.atomic():
        articulo = (
            ArticuloRetenido.objects.select_for_update(of=("self",))
            .select_related("usuario", "producto")
            .get(pk=articulo_pk)
        )
        if not articulo.corre_plazo:
            raise OperacionRechazada(
                "Sólo se modifica el plazo de un artículo que lo tiene vigente."
            )
        anterior = articulo.fecha_vencimiento
        articulo.fecha_vencimiento = nueva_fecha
        articulo.save(update_fields=["fecha_vencimiento", "actualizado_en"])
        RegistroAuditoria.registrar(
            accion=RegistroAuditoria.PLAZO_RETENCION,
            actor=actor,
            objetivo=articulo,
            objetivo_email=articulo.usuario.email,
            detalle=(
                f"{nombre(articulo)}: {fecha(anterior)} → {fecha(nueva_fecha)}. "
                f"Motivo: {motivo}"
            ),
        )
        transaction.on_commit(partial(_avisar_plazo, articulo, anterior, origen))
    return articulo


def _avisar_plazo(articulo, anterior, origen):
    avisos.avisar(
        [articulo.usuario.email],
        asunto="Cambió el plazo de un artículo guardado",
        rotulo="Stock en local",
        antetitulo="Stock en local",
        titulo="Nuevo plazo",
        parrafos=[f"Cambió la fecha hasta la que guardamos {nombre(articulo)}."],
        filas=[
            ("Antes", fecha(anterior)),
            ("Ahora", fecha(articulo.fecha_vencimiento)),
        ],
        enlace=_enlace(origen, "cuenta:stock"),
        texto_enlace="Ver mi stock en el local",
    )


# ---------------------------------------------------------------------------
# CO-154 ejecutarCicloDeVencimientoDeRetencion
# ---------------------------------------------------------------------------


@dataclass
class ResumenVencimiento:
    avisados: list = field(default_factory=list)
    reintegrados: list = field(default_factory=list)
    extendidos: list = field(default_factory=list)


def ciclo_de_vencimiento(hoy=None):
    """`CO-154`, con B-18-005 y B-18-006. Correrlo dos veces no repite nada."""
    hoy = hoy or timezone.localdate()
    dias = dias_de_aviso()
    resumen = ResumenVencimiento()

    # Paso 3: el aviso, una vez por fecha de vencimiento. Pendiente de despacho no (E1).
    por_avisar = ArticuloRetenido.objects.filter(
        estado=ArticuloRetenido.DISPONIBLE,
        fecha_vencimiento__gt=hoy,
        fecha_vencimiento__lte=hoy + timedelta(days=dias),
    ).exclude(aviso_para=F("fecha_vencimiento"))
    for pk in list(por_avisar.values_list("pk", flat=True)):
        with transaction.atomic():
            articulo = (
                ArticuloRetenido.objects.select_for_update(of=("self",))
                .select_related("usuario", "producto")
                .get(pk=pk)
            )
            if articulo.estado != ArticuloRetenido.DISPONIBLE or (
                articulo.aviso_para == articulo.fecha_vencimiento
            ):
                continue
            articulo.aviso_para = articulo.fecha_vencimiento
            articulo.save(update_fields=["aviso_para"])
            resumen.avisados.append(articulo)
            transaction.on_commit(partial(_avisar_proximo, articulo))

    # Paso 4 y A1: lo vencido.
    vencidos = ArticuloRetenido.objects.filter(
        estado__in=ArticuloRetenido.CON_PLAZO, fecha_vencimiento__lte=hoy
    ).values_list("pk", "producto_id")
    for pk, producto_id in list(vencidos):
        with transaction.atomic():
            producto = Producto.objects.select_for_update().get(pk=producto_id)
            articulo = (
                ArticuloRetenido.objects.select_for_update(of=("self",))
                .select_related("usuario", "producto")
                .get(pk=pk)
            )
            if articulo.fecha_vencimiento is None or articulo.fecha_vencimiento > hoy:
                continue
            if articulo.estado == ArticuloRetenido.DISPONIBLE:
                _reintegrar(articulo, producto)
                resumen.reintegrados.append(articulo)
            elif articulo.estado == ArticuloRetenido.PENDIENTE_DESPACHO:
                _extender(articulo, hoy)
                resumen.extendidos.append(articulo)

    if resumen.extendidos:
        avisos.avisar_administradores(
            asunto="Envíos de stock almacenado vencidos",
            rotulo="Stock en local",
            antetitulo="Stock en local",
            titulo="Despachos pendientes vencidos",
            parrafos=[
                "Estos artículos vencieron con el envío pendiente. Se extendió su plazo tres "
                "días: confirme el despacho.",
            ],
            filas=[
                (f"{nombre(a)} · {a.usuario.email}", fecha(a.fecha_vencimiento))
                for a in resumen.extendidos
            ],
        )
    return resumen


def _reintegrar(articulo, producto):
    """Al stock general, con el valor de la unidad en puntos.

    El Cliente la pagó entera: vuelve con su valor en puntos, cualquiera sea la
    procedencia (plan 07, octava parte, D3; plan 00, C2). Sin compensación.
    """
    anterior = producto.estado
    producto.stock += 1
    if producto.estado == Producto.AGOTADO:
        producto.estado = Producto.ACTIVO
    Producto.objects.filter(pk=producto.pk).update(
        stock=producto.stock, estado=producto.estado, actualizado_en=timezone.now()
    )
    articulo.estado = ArticuloRetenido.VENCIDO
    articulo.save(update_fields=["estado", "actualizado_en"])
    reembolso = _reembolsar(articulo)
    RegistroAuditoria.registrar(
        accion=RegistroAuditoria.VENCIMIENTO_RETENCION,
        objetivo=articulo,
        objetivo_email=articulo.usuario.email,
        detalle=(
            f"{nombre(articulo)} de {articulo.usuario.email}: Disponible → Vencido y devuelto al "
            f"stock. Stock {producto.stock - 1} → {producto.stock}"
            + (
                f", {dict(Producto.ESTADO_CHOICES)[anterior]} → Activo"
                if anterior != producto.estado
                else ""
            )
            + (f". Reembolso de {reembolso} pts" if reembolso else "")
            + "."
        ),
    )
    transaction.on_commit(partial(_avisar_reintegro, articulo, reembolso))
    transaction.on_commit(partial(_reponer, producto, 1))


def _reembolsar(articulo):
    """D3: el valor de la unidad en puntos, con la regla de los demás reembolsos."""
    from apps.puntos import servicios as puntos
    from apps.puntos.models import LotePuntos

    linea = articulo.linea_pedido
    if linea is None:
        cantidad = puntos.puntos_para_cubrir(articulo.valor)
    else:
        cantidad = puntos.puntos_de_una_unidad(linea)
    puntos.acreditar(
        articulo.usuario,
        cantidad,
        origen=LotePuntos.REEMBOLSO,
        pedido=linea.pedido if linea else None,
        linea=linea,
        motivo=f"{nombre(articulo)} sin retirar: venció el plazo",
    )
    if linea is not None:
        puntos.descontar_ganados(articulo.usuario, linea)
    return cantidad


def _reponer(producto, unidades):
    """B-05-001: el artículo que vuelve al stock también cuenta como reposición."""
    from apps.restock import servicios as restock

    restock.reposicion(producto, unidades)


def _extender(articulo, hoy):
    """A1 y B-18-005: tres días más y alerta, cada vez que vence pendiente."""
    anterior = articulo.fecha_vencimiento
    articulo.fecha_vencimiento = anterior + EXTENSION_AUTOMATICA
    articulo.save(update_fields=["fecha_vencimiento", "actualizado_en"])
    RegistroAuditoria.registrar(
        accion=RegistroAuditoria.VENCIMIENTO_RETENCION,
        objetivo=articulo,
        objetivo_email=articulo.usuario.email,
        detalle=(
            f"{nombre(articulo)} de {articulo.usuario.email}: venció con el despacho pendiente. "
            f"Plazo {fecha(anterior)} → {fecha(articulo.fecha_vencimiento)} (extensión automática)."
        ),
    )


def _avisar_proximo(articulo):
    avisos.avisar(
        [articulo.usuario.email],
        asunto=f"{nombre(articulo)} vence el {fecha(articulo.fecha_vencimiento)}",
        rotulo="Stock en local",
        antetitulo="Stock en local",
        titulo="Próximo a vencer",
        parrafos=[
            f"Guardamos {nombre(articulo)} a tu nombre hasta el "
            f"{fecha(articulo.fecha_vencimiento)}. "
            + "Después vuelve a la venta y te devolvemos su valor en puntos.",
            "Pedí el envío o pasá a retirarlo desde «Mi cuenta», en Stock en local.",
        ],
    )


def _avisar_reintegro(articulo, reembolso=0):
    avisos.avisar(
        [articulo.usuario.email],
        asunto=f"{nombre(articulo)} volvió a la venta",
        rotulo="Stock en local",
        antetitulo="Stock en local",
        titulo="Plazo vencido",
        parrafos=[
            (
                f"Venció el plazo de {nombre(articulo)} y volvió a la venta. Te devolvimos su "
                f"valor en puntos: {reembolso} pts."
                if reembolso
                else f"Venció el plazo de {nombre(articulo)} y volvió a la venta. No tiene "
                "recupero ni reembolso."
            ),
        ],
    )
