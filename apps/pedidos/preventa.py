"""El ciclo de la pre-venta del lado del Administrador (plan 01).

`CO-011` y `CO-012` avisan; `CO-013` confirma lo que llegó; `CO-014` y `CO-015`
registran una demora; `CO-026` y `CO-027` cancelan un título que la editorial no
va a publicar. Lo que los contratos no dicen está en B-01-006 a B-01-010 y en
B-08-008.

**Orden de bloqueo: producto, pedido, línea.** Todas las escrituras del ciclo y
de la demora toman las filas en ese orden, así que dos de ellas no se traban
entre sí.
"""

import logging
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import timedelta

from django.db import transaction
from django.db.models import Count, Q, Sum
from django.urls import reverse
from django.utils import timezone

from apps.almacen import servicios as almacen
from apps.catalog.models import Producto, ProductoEditorial
from apps.core.models import ConfiguracionSistema, RegistroAuditoria
from apps.core.segundo_plano import despues_del_commit
from apps.pedidos import avisos
from apps.pedidos.models import AvisoDePreVenta, LineaPedido, Pedido
from apps.pedidos.servicios import AUTOMATICOS, avisar_cambio_de_estado, registrar_transicion
from apps.puntos import servicios as puntos
from apps.puntos.models import LotePuntos
from apps.restock import servicios as restock

logger = logging.getLogger(__name__)

PENDIENTES = (LineaPedido.RESERVADO, LineaPedido.ESPERANDO_DEMORADO)


class OperacionRechazada(ValueError):
    """La operación no se puede hacer sobre el producto o el pedido como están."""


def nombre(producto):
    return str(producto.especifico)


def fecha(dia):
    return dia.strftime("%d/%m/%Y") if dia else "sin fecha"


# ---------------------------------------------------------------------------
# Lo común: reservas, estado del pedido y reembolsos
# ---------------------------------------------------------------------------


def reservas_pendientes(producto):
    """Las reservas sin cubrir, en el orden en que se compraron (B-01-007)."""
    return LineaPedido.objects.filter(producto_id=producto.pk, estado__in=PENDIENTES).order_by(
        "pedido__fecha", "pedido__pk", "pk"
    )


def _bloquear(lineas_qs):
    """Pedidos y líneas con bloqueo, en ese orden. Devuelve las líneas."""
    ids = list(lineas_qs.values_list("pedido_id", flat=True))
    pedidos = {
        p.pk: p
        for p in Pedido.objects.select_for_update(of=("self",))
        .filter(pk__in=ids)
        .select_related("usuario")
        .order_by("pk")
    }
    lineas = list(lineas_qs.select_for_update(of=("self",)))
    for linea in lineas:
        linea.pedido = pedidos[linea.pedido_id]
    return lineas


def ubicar_pedido(pedido, actor, momento):
    """El estado de un pedido en espera según sus líneas. Devuelve si cambió.

    Sólo mueve los pedidos que esperan algo del sistema: uno que el Cliente
    partió con la opción 2 ya está en manos del Administrador.
    """
    if pedido.estado not in AUTOMATICOS:
        return False
    estados = set(
        pedido.lineas.exclude(estado=LineaPedido.CANCELADO_REEMBOLSO).values_list(
            "estado", flat=True
        )
    )
    if not estados:
        nuevo = Pedido.CANCELADO
    elif LineaPedido.ESPERANDO_DEMORADO in estados:
        nuevo = Pedido.ESPERANDO_DEMORADO
    elif LineaPedido.RESERVADO in estados:
        nuevo = Pedido.ESPERANDO_PRE_VENTA
    else:
        nuevo = Pedido.PENDIENTE_ARMADO
    if nuevo == pedido.estado:
        return False
    anterior = pedido.estado
    pedido.estado = nuevo
    pedido.save(update_fields=["estado"])
    registrar_transicion(pedido, anterior, actor, momento)
    RegistroAuditoria.registrar(
        accion=RegistroAuditoria.TRANSICION_PEDIDO,
        actor=actor,
        objetivo=pedido,
        objetivo_email=pedido.correo_de_contacto,
        detalle=(
            f"Pedido {pedido.numero}: {Pedido(estado=anterior).get_estado_display()} → "
            f"{pedido.get_estado_display()}."
        ),
    )
    return True


def puntos_de_reembolso(linea, equivalencia):
    """B-01-010: lo pagado en dinero, a puntos hacia arriba; lo pagado con puntos, igual."""
    if linea.cubierta_con_puntos:
        return linea.puntos_canjeados
    return puntos.puntos_para_cubrir(linea.valor, equivalencia)


def puntos_de_envio(pedido, equivalencia):
    """B-08-008: el envío vuelve sólo si el pedido se queda sin artículos."""
    if not pedido.costo_envio:
        return 0
    return puntos.puntos_para_cubrir(pedido.costo_envio, equivalencia)


def _enlace_al_pedido(origen, pedido):
    if not origen or not pedido.usuario_id:
        return ""
    return origen + reverse("cuenta:pedido", args=[pedido.numero])


# ---------------------------------------------------------------------------
# «Pre-ventas por llegar» (B-01-006) y el bloque del panel
# ---------------------------------------------------------------------------


@dataclass
class FilaPreVenta:
    producto: ProductoEditorial
    llegada: object
    reservadas: int
    pedidos: int

    @property
    def vencida(self):
        return self.llegada is not None and self.llegada < timezone.localdate()


@dataclass
class GrupoDeLlegada:
    llegada: object
    editorial: object
    filas: list = field(default_factory=list)

    @property
    def clave(self):
        return f"{self.llegada.isoformat() if self.llegada else 'sin-fecha'}-{self.editorial.pk}"

    @property
    def vencido(self):
        return self.llegada is not None and self.llegada < timezone.localdate()

    @property
    def es_hoy(self):
        return self.llegada == timezone.localdate()


def _con_reservas(qs):
    pendientes = Q(lineas_pedido__estado__in=PENDIENTES)
    return qs.annotate(
        reservadas=Sum("lineas_pedido__cantidad", filter=pendientes, default=0),
        pedidos_con_reserva=Count("lineas_pedido__pedido", filter=pendientes, distinct=True),
    )


def filas_de_preventa(qs=None):
    qs = qs if qs is not None else ProductoEditorial.objects.all()
    productos = _con_reservas(
        qs.filter(estado=Producto.PRE_VENTA).select_related("editorial", "tipo", "formato")
    )
    return [
        FilaPreVenta(
            producto=p,
            llegada=p.llegada_vigente,
            reservadas=p.reservadas,
            pedidos=p.pedidos_con_reserva,
        )
        for p in productos
    ]


def por_llegar():
    """Las pre-ventas agrupadas por fecha de llegada vigente y editorial."""
    grupos = {}
    for fila in filas_de_preventa():
        clave = (fila.llegada, fila.producto.editorial_id)
        if clave not in grupos:
            grupos[clave] = GrupoDeLlegada(llegada=fila.llegada, editorial=fila.producto.editorial)
        grupos[clave].filas.append(fila)
    for grupo in grupos.values():
        grupo.filas.sort(key=lambda f: (f.producto.titulo.lower(), f.producto.volumen or 0))
    sin_fecha = timezone.localdate().replace(year=9999)
    return sorted(
        grupos.values(),
        key=lambda g: (g.llegada or sin_fecha, g.editorial.nombre.lower()),
    )


@dataclass
class Proximas:
    vencidas: list
    hoy: list
    proximas: list

    @property
    def total(self):
        return len(self.vencidas) + len(self.hoy) + len(self.proximas)


def proximas_para_el_panel():
    """El bloque del panel: lo atrasado, lo de hoy y lo de los próximos N días."""
    hoy = timezone.localdate()
    horizonte = hoy + timedelta(days=ConfiguracionSistema.obtener().dias_aviso_preventa)
    vencidas, de_hoy, proximas = [], [], []
    for fila in filas_de_preventa():
        if fila.llegada is None or fila.llegada > horizonte:
            continue
        if fila.llegada < hoy:
            vencidas.append(fila)
        elif fila.llegada == hoy:
            de_hoy.append(fila)
        else:
            proximas.append(fila)
    orden = lambda f: (f.llegada, f.producto.titulo.lower())  # noqa: E731
    return Proximas(
        sorted(vencidas, key=orden), sorted(de_hoy, key=orden), sorted(proximas, key=orden)
    )


# ---------------------------------------------------------------------------
# CO-011 ejecutarCicloVigilanciaPreventa · CO-012 ejecutarCicloEscaladoPorInaccion
# ---------------------------------------------------------------------------


@dataclass
class ResumenVigilancia:
    proximas: list = field(default_factory=list)
    de_hoy: list = field(default_factory=list)
    escaladas: list = field(default_factory=list)


def ciclo_de_vigilancia(hoy=None):
    """`CO-011` y `CO-012`: avisan y no cambian nada (B-01-009).

    Cada aviso se anota: correr el ciclo dos veces el mismo día no repite
    correos. El escalado se repite una vez por día mientras siga sin resolver.
    """
    hoy = hoy or timezone.localdate()
    horizonte = hoy + timedelta(days=ConfiguracionSistema.obtener().dias_aviso_preventa)
    resumen = ResumenVigilancia()
    for fila in filas_de_preventa():
        llegada = fila.llegada
        if llegada is None or llegada > horizonte:
            continue
        if llegada > hoy:
            tipo, referencia, destino = AvisoDePreVenta.PROXIMIDAD, llegada, resumen.proximas
        elif llegada == hoy or fila.producto.demorado:
            tipo, referencia, destino = AvisoDePreVenta.LLEGADA, llegada, resumen.de_hoy
        else:
            tipo, referencia, destino = AvisoDePreVenta.ESCALADO, hoy, resumen.escaladas
        _, nuevo = AvisoDePreVenta.objects.get_or_create(
            producto=fila.producto, tipo=tipo, fecha=referencia
        )
        if nuevo:
            destino.append(fila)

    for fila in resumen.escaladas:
        RegistroAuditoria.registrar(
            accion=RegistroAuditoria.ESCALADO_PREVENTA,
            objetivo=fila.producto,
            detalle=(
                f"{fila.producto}: la llegada del {fecha(fila.llegada)} pasó sin ingreso "
                f"ni demora. {fila.pedidos} pedido(s) esperando."
            ),
        )

    filas = lambda lista: [  # noqa: E731
        (
            f"{f.producto} · {f.producto.editorial}",
            f"{fecha(f.llegada)} · {f.pedidos} pedido(s)",
        )
        for f in lista
    ]
    if resumen.proximas or resumen.de_hoy:
        avisos.avisar_administradores(
            asunto="Pre-ventas por llegar",
            antetitulo="Pre-ventas",
            titulo="Por llegar",
            parrafos=[
                "Estas pre-ventas llegan hoy o en los próximos días.",
                "Confirme el ingreso desde «Pre-ventas por llegar».",
            ],
            filas=filas(resumen.de_hoy + resumen.proximas),
        )
    if resumen.escaladas:
        avisos.avisar_administradores(
            asunto="Pre-ventas sin resolver",
            antetitulo="Pre-ventas",
            titulo="Sin resolver",
            parrafos=[
                "La fecha de llegada de estas pre-ventas pasó sin ingreso ni demora.",
                "Confirme el ingreso o registre la demora desde «Pre-ventas por llegar».",
            ],
            filas=filas(resumen.escaladas),
        )
    return resumen


# ---------------------------------------------------------------------------
# CO-014 solicitarRegistroDeDemora · CO-015 confirmarRegistroDeDemora
# ---------------------------------------------------------------------------


@dataclass
class InformeDemora:
    producto: ProductoEditorial
    pedidos: int
    clientes: int


@dataclass
class ResumenDemora:
    producto: ProductoEditorial
    pedidos: list = field(default_factory=list)
    clientes: set = field(default_factory=set)
    errores: list = field(default_factory=list)


def validar_demora(producto, fecha_estimada=None):
    """Las precondiciones de `CO-014` y su E1."""
    hoy = timezone.localdate()
    if not producto.esta_en_pre_venta:
        raise OperacionRechazada("El producto no está en pre-venta.")
    if producto.demorado:
        raise OperacionRechazada("El producto ya tiene una demora registrada.")
    if producto.fecha_llegada and producto.fecha_llegada < hoy:
        raise OperacionRechazada(
            "La fecha de llegada ya pasó. Confirme el ingreso desde «Pre-ventas por llegar»."
        )
    if fecha_estimada and fecha_estimada <= hoy:
        raise OperacionRechazada("La nueva fecha estimada debe ser posterior a hoy.")


def informe_de_demora(producto):
    """`CO-014`: a cuántos pedidos y clientes alcanza. No registra nada."""
    lineas = reservas_pendientes(producto).filter(estado=LineaPedido.RESERVADO)
    return InformeDemora(
        producto=producto,
        pedidos=lineas.values("pedido").distinct().count(),
        clientes=lineas.values("pedido__usuario").distinct().count(),
    )


def registrar_demora(producto, actor, *, fecha_estimada=None, nota="", origen=""):
    """`CO-015`, desde la ficha del producto."""
    with transaction.atomic():
        p = ProductoEditorial.objects.select_for_update().get(pk=producto.pk)
        validar_demora(p, fecha_estimada)
        return _aplicar_demora(
            p,
            actor,
            timezone.now(),
            fecha_estimada=fecha_estimada,
            nota=nota,
            origen=origen,
        )


def _aplicar_demora(p, actor, momento, *, fecha_estimada=None, nota="", origen="", lineas=None):
    """Las postcondiciones de `CO-015` sobre un producto ya bloqueado.

    `lineas` son las reservas a demorar; por omisión, todas las que esperan.
    Cada pedido va en su propio punto de guardado (E2): si uno falla, el resto
    sigue y el producto queda demorado igual.
    """
    fecha_original = p.fecha_llegada
    p.demorado = True
    p.fecha_estimada = fecha_estimada
    p.nota_demora = nota
    p.save(update_fields=["demorado", "fecha_estimada", "nota_demora", "actualizado_en"])

    if lineas is None:
        lineas = _bloquear(reservas_pendientes(p).filter(estado=LineaPedido.RESERVADO))
    vence = momento + timedelta(hours=ConfiguracionSistema.obtener().ventana_decision_horas)
    por_pedido = defaultdict(list)
    for linea in lineas:
        por_pedido[linea.pedido].append(linea)

    resumen = ResumenDemora(producto=p)
    for pedido, suyas in por_pedido.items():
        try:
            with transaction.atomic():
                _demorar_pedido(pedido, suyas, fecha_original, vence, actor, momento)
        except Exception as error:  # noqa: BLE001 - E2: el fallo de un pedido no frena a los demás
            logger.exception("No se pudo demorar el pedido %s.", pedido.numero)
            RegistroAuditoria.registrar(
                accion=RegistroAuditoria.INCIDENTE_PREVENTA,
                actor=actor,
                objetivo=pedido,
                detalle=(
                    f"Demora de {p} en el pedido {pedido.numero}: falló "
                    f"({error.__class__.__name__})."
                ),
            )
            resumen.errores.append(pedido.numero)
            continue
        resumen.pedidos.append(pedido)
        resumen.clientes.add(pedido.correo_de_contacto)
        despues_del_commit(_avisar_demora, pedido, suyas, p, origen)

    RegistroAuditoria.registrar(
        accion=RegistroAuditoria.REGISTRO_DEMORA,
        actor=actor,
        objetivo=p,
        detalle=(
            f"{p}: demorado"
            + (f", nueva fecha estimada {fecha(fecha_estimada)}" if fecha_estimada else "")
            + f". {len(resumen.pedidos)} pedido(s) afectado(s), "
            f"{len(resumen.clientes)} cliente(s) notificado(s)"
            + (f"; fallaron los pedidos {', '.join(resumen.errores)}" if resumen.errores else "")
            + "."
        ),
    )
    if resumen.errores:
        despues_del_commit(
            avisos.avisar_administradores,
            asunto=f"Demora de {p}: pedidos sin actualizar",
            antetitulo="Demora",
            titulo="Pedidos sin actualizar",
            parrafos=[
                f"La demora de {p} quedó registrada, pero estos pedidos no se pudieron "
                "actualizar.",
            ],
            filas=[("Pedido", numero) for numero in resumen.errores],
        )
    return resumen


def _demorar_pedido(pedido, lineas, fecha_original, vence, actor, momento):
    for linea in lineas:
        linea.estado = LineaPedido.ESPERANDO_DEMORADO
        linea.fecha_llegada_original = fecha_original
        linea.decision_vence_en = vence
        linea.ventana_cerrada = False
        linea.save(
            update_fields=[
                "estado",
                "fecha_llegada_original",
                "decision_vence_en",
                "ventana_cerrada",
            ]
        )
    ubicar_pedido(pedido, actor, momento)


def _avisar_demora(pedido, lineas, producto, origen):
    """`CU-ALT-DEM` paso 6 (c): las tres opciones y el acceso directo."""
    vence = timezone.localtime(lineas[0].decision_vence_en)
    filas = [("Artículo", nombre(linea.producto)) for linea in lineas]
    filas.append(("Llegada prevista", fecha(lineas[0].fecha_llegada_original)))
    if producto.fecha_estimada:
        filas.append(("Nueva fecha estimada", fecha(producto.fecha_estimada)))
    avisos.avisar(
        [pedido.correo_de_contacto],
        asunto=f"Tu pedido {pedido.numero}: un artículo se demora",
        antetitulo=f"Pedido {pedido.numero}",
        titulo="Artículo demorado",
        parrafos=[
            "Un artículo de tu pedido no llega en la fecha prevista.",
            "Podés esperar el pedido completo, recibir ahora lo disponible o cancelar el "
            f"artículo con reembolso en puntos. Tenés tiempo hasta el {vence:%d/%m/%Y %H:%M}.",
        ],
        filas=filas,
        enlace=_enlace_al_pedido(origen, pedido),
        texto_enlace="Elegir qué hacer",
    )


# ---------------------------------------------------------------------------
# CO-013 confirmarIngresoDeLote
# ---------------------------------------------------------------------------


@dataclass
class ResumenIngreso:
    activados: list = field(default_factory=list)
    parciales: list = field(default_factory=list)
    demorados: list = field(default_factory=list)
    sin_cambios: list = field(default_factory=list)
    errores: list = field(default_factory=list)
    pedidos: list = field(default_factory=list)
    clientes: set = field(default_factory=set)

    def sumar(self, otro):
        for campo in ("activados", "parciales", "demorados", "sin_cambios", "errores", "pedidos"):
            getattr(self, campo).extend(getattr(otro, campo))
        self.clientes |= otro.clientes


def _cubrir(lineas, disponibles):
    """B-01-007: lo que llega cubre las reservas en orden, línea entera, sin saltear."""
    cubiertas = []
    for linea in lineas:
        if linea.cantidad > disponibles:
            break
        disponibles -= linea.cantidad
        cubiertas.append(linea)
    return cubiertas, disponibles


@dataclass
class Previsualizacion:
    producto: ProductoEditorial
    unidades: int
    reservas: int
    cubiertas: int
    a_la_venta: int
    se_demora: bool

    @property
    def completa(self):
        return self.cubiertas == self.reservas


def previsualizar_ingreso(producto, unidades):
    """Lo que hará `CO-013` con un producto, sin escribir nada."""
    lineas = list(reservas_pendientes(producto))
    if unidades > 0:
        cubiertas, sobran = _cubrir(lineas, producto.stock + unidades)
        completa = len(cubiertas) == len(lineas)
        return Previsualizacion(
            producto=producto,
            unidades=unidades,
            reservas=len(lineas),
            cubiertas=len(cubiertas),
            a_la_venta=sobran if completa else 0,
            se_demora=not completa and not producto.demorado,
        )
    llegada = producto.llegada_vigente
    vencido = llegada is not None and llegada <= timezone.localdate()
    return Previsualizacion(
        producto=producto,
        unidades=0,
        reservas=len(lineas),
        cubiertas=0,
        a_la_venta=0,
        se_demora=vencido and not producto.demorado,
    )


def confirmar_ingreso(unidades, actor, *, origen=""):
    """`CO-013`. `unidades` va de producto a unidades recibidas; cero es faltante.

    Una transacción por producto (E3): si uno falla, queda como estaba y los
    demás siguen.
    """
    if any(cantidad < 0 for cantidad in unidades.values()):
        raise OperacionRechazada("Las unidades recibidas no pueden ser negativas.")
    resumen = ResumenIngreso()
    for pk in sorted(unidades):
        parcial = ResumenIngreso()
        try:
            with transaction.atomic():
                if unidades[pk] > 0:
                    _ingresar(pk, unidades[pk], actor, origen, parcial)
                else:
                    _faltante(pk, actor, origen, parcial)
        except (
            Exception
        ) as error:  # noqa: BLE001 - E3: el fallo de un producto no frena a los demás
            logger.exception("No se pudo confirmar el ingreso del producto %s.", pk)
            producto = ProductoEditorial.objects.filter(pk=pk).first()
            RegistroAuditoria.registrar(
                accion=RegistroAuditoria.INCIDENTE_PREVENTA,
                actor=actor,
                objetivo=producto,
                detalle=(
                    f"Confirmación de ingreso de {producto or pk}: falló y quedó como estaba "
                    f"({error.__class__.__name__})."
                ),
            )
            resumen.errores.append(str(producto or pk))
            continue
        resumen.sumar(parcial)

    if resumen.errores:
        despues_del_commit(
            avisos.avisar_administradores,
            asunto="Ingreso de pre-ventas con errores",
            antetitulo="Ingreso",
            titulo="Productos sin confirmar",
            parrafos=[
                "Estos productos no se pudieron confirmar y siguen en pre-venta. "
                "Vuelva a intentarlo desde «Pre-ventas por llegar».",
            ],
            filas=[("Producto", titulo) for titulo in resumen.errores],
        )
    return resumen


def _ingresar(pk, cantidad, actor, origen, resumen):
    p = ProductoEditorial.objects.select_for_update().get(pk=pk)
    if not p.esta_en_pre_venta:
        raise OperacionRechazada(f"«{p}» ya no está en pre-venta.")
    momento = timezone.now()
    lineas = _bloquear(reservas_pendientes(p))

    cubiertas, disponibles = _cubrir(lineas, p.stock + cantidad)
    sin_cubrir = lineas[len(cubiertas) :]

    for linea in cubiertas:
        linea.estado = LineaPedido.DISPONIBLE
        # B-08-006: la compensación corre hasta que el artículo llega.
        linea.compensacion_cerrada = linea.compensacion_cerrada or linea.despacho_diferido
        linea.save(update_fields=["estado", "compensacion_cerrada"])

    p.stock = disponibles
    if not sin_cubrir:
        p.estado = Producto.ACTIVO if disponibles else Producto.AGOTADO
        p.demorado = False
        p.fecha_estimada = None
        p.nota_demora = ""
    p.save(
        update_fields=[
            "estado",
            "stock",
            "demorado",
            "fecha_estimada",
            "nota_demora",
            "actualizado_en",
        ]
    )
    RegistroAuditoria.registrar(
        accion=RegistroAuditoria.CONFIRMACION_INGRESO,
        actor=actor,
        objetivo=p,
        detalle=(
            f"{p}: llegaron {cantidad} unidad(es), cubren {len(cubiertas)} de "
            f"{len(lineas)} reserva(s). "
            + (
                f"Pre-venta → {p.get_estado_display()}, {disponibles} a la venta."
                if not sin_cubrir
                else "Sigue en Pre-venta."
            )
        ),
    )

    vistos = []
    for linea in cubiertas:
        pedido = linea.pedido
        if pedido in vistos:
            continue
        vistos.append(pedido)
        resumen.clientes.add(pedido.correo_de_contacto)
        if ubicar_pedido(pedido, actor, momento):
            resumen.pedidos.append(pedido.numero)
            despues_del_commit(avisar_cambio_de_estado, pedido)

    # La opción 2: lo que llega queda guardado a nombre del Cliente (plan 18).
    for linea in cubiertas:
        if linea.despacho_diferido:
            almacen.retener_linea(linea, actor, origen=origen)

    if sin_cubrir:
        resumen.parciales.append(p)
        reservadas = [linea for linea in sin_cubrir if linea.estado == LineaPedido.RESERVADO]
        if not p.demorado:
            demora = _aplicar_demora(p, actor, momento, origen=origen, lineas=reservadas)
            resumen.clientes |= demora.clientes
    else:
        resumen.activados.append(p)
        # B-05-001: las unidades que quedan a la venta avisan a los suscriptores.
        restock.al_subir_stock(p, 0, disponibles, origen=origen)


def _faltante(pk, actor, origen, resumen):
    """A1, con B-01-008: sólo se demora lo que ya tendría que haber llegado."""
    p = ProductoEditorial.objects.select_for_update().get(pk=pk)
    if not p.esta_en_pre_venta:
        raise OperacionRechazada(f"«{p}» ya no está en pre-venta.")
    llegada = p.llegada_vigente
    if p.demorado or llegada is None or llegada > timezone.localdate():
        resumen.sin_cambios.append(p)
        return
    demora = _aplicar_demora(p, actor, timezone.now(), origen=origen)
    resumen.demorados.append(p)
    resumen.clientes |= demora.clientes


# ---------------------------------------------------------------------------
# CO-026 solicitarCancelacionDePreventaEnLote · CO-027 confirmarCancelacionDePreventaEnLote
# ---------------------------------------------------------------------------


@dataclass
class ReembolsoDeCliente:
    usuario: object
    reservas: list = field(default_factory=list)
    puntos_articulos: int = 0
    puntos_envio: int = 0
    pedidos_cancelados: list = field(default_factory=list)

    @property
    def puntos(self):
        return self.puntos_articulos + self.puntos_envio


@dataclass
class InformeCancelacion:
    producto: ProductoEditorial
    clientes: list

    @property
    def reservas(self):
        return sum(len(c.reservas) for c in self.clientes)

    @property
    def total_puntos(self):
        return sum(c.puntos for c in self.clientes)


def _reembolsos(lineas):
    """Lo que vuelve a cada cliente (B-01-010), con el envío de los pedidos
    que se quedan sin artículos (B-08-008)."""
    equivalencia = ConfiguracionSistema.obtener().equivalencia_puntos
    clientes = {}
    canceladas = {linea.pk for linea in lineas}
    for linea in lineas:
        pedido = linea.pedido
        cliente = clientes.setdefault(pedido.usuario_id, ReembolsoDeCliente(usuario=pedido.usuario))
        cliente.reservas.append(linea)
        cliente.puntos_articulos += puntos_de_reembolso(linea, equivalencia)
    for cliente in clientes.values():
        for pedido in {linea.pedido for linea in cliente.reservas}:
            vivas = set(
                pedido.lineas.exclude(estado=LineaPedido.CANCELADO_REEMBOLSO).values_list(
                    "pk", flat=True
                )
            )
            if vivas <= canceladas and pedido.estado in AUTOMATICOS:
                cliente.puntos_envio += puntos_de_envio(pedido, equivalencia)
                cliente.pedidos_cancelados.append(pedido)
    return sorted(clientes.values(), key=lambda c: c.usuario.email if c.usuario else "")


def informe_de_cancelacion(producto):
    """`CO-026`: reservas, clientes y puntos a reembolsar. No registra nada."""
    lineas = list(reservas_pendientes(producto).select_related("pedido", "pedido__usuario"))
    return InformeCancelacion(producto=producto, clientes=_reembolsos(lineas))


def cancelar_preventa(producto, actor):
    """`CO-027`. Atomicidad total: si falla un cliente, no queda nada hecho (E1)."""
    with transaction.atomic():
        p = ProductoEditorial.objects.select_for_update().get(pk=producto.pk)
        if not p.esta_en_pre_venta:
            raise OperacionRechazada("El producto no está en pre-venta.")
        momento = timezone.now()
        lineas = _bloquear(reservas_pendientes(p))
        informe = InformeCancelacion(producto=p, clientes=_reembolsos(lineas))

        p.estado = Producto.CANCELADO_EDITORIAL
        p.save(update_fields=["estado", "actualizado_en"])
        for linea in lineas:
            linea.estado = LineaPedido.CANCELADO_REEMBOLSO
            linea.compensacion_cerrada = True
            linea.save(update_fields=["estado", "compensacion_cerrada"])
        for pedido in {linea.pedido for linea in lineas}:
            ubicar_pedido(pedido, actor, momento)
        for cliente in informe.clientes:
            if cliente.usuario is None or not cliente.puntos:
                continue
            puntos.acreditar(
                cliente.usuario,
                cliente.puntos,
                origen=LotePuntos.REEMBOLSO,
                motivo=f"Cancelación de {p} por la editorial",
            )
            for linea in cliente.reservas:  # plan 00, C2
                puntos.descontar_ganados(cliente.usuario, linea, linea.cantidad)
            despues_del_commit(_avisar_cancelacion, cliente, p)

        RegistroAuditoria.registrar(
            accion=RegistroAuditoria.CANCELACION_PREVENTA_LOTE,
            actor=actor,
            objetivo=p,
            detalle=(
                f"{p}: Pre-venta → Cancelado por editorial. {informe.reservas} reserva(s) "
                f"cancelada(s), {informe.total_puntos} pts emitidos."
            ),
        )
    return informe


def _avisar_cancelacion(cliente, producto):
    """`CU-ALT-CAN` paso 5."""
    filas = [("Reembolso", f"{cliente.puntos_articulos} pts")]
    if cliente.puntos_envio:
        filas.append(("Envío", f"{cliente.puntos_envio} pts"))
    filas.append(("Saldo actual", f"{puntos.saldo(cliente.usuario)} pts"))
    parrafos = [
        f"La editorial canceló definitivamente {producto}. Te devolvimos lo que pagaste "
        "en puntos.",
    ]
    if cliente.pedidos_cancelados:
        numeros = ", ".join(p.numero for p in cliente.pedidos_cancelados)
        parrafos.append(f"El pedido {numeros} quedó cancelado: no tenía otros artículos.")
    avisos.avisar(
        [cliente.usuario.email],
        asunto=f"Cancelación de {producto}",
        antetitulo="Pre-venta cancelada",
        titulo=str(producto),
        parrafos=parrafos,
        filas=filas,
    )
