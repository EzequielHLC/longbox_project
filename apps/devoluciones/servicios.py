"""Devoluciones (plan 09; reformuladas en el plan 00, C1).

Dos tipos de reclamo sobre una línea entregada:

- **Arrepentimiento** (`CO-185`, `CO-099` con motivo Arrepentimiento): desde el
  botón de arrepentimiento, sin registración —con sesión o con el número de
  pedido y el correo de la compra—, sólo en pedidos online y dentro del plazo de
  arrepentimiento. Cubre la línea entera. Se resuelve con el reembolso por el
  medio de pago (o en puntos, si se pagó con puntos) cuando el local recibe el
  artículo, que vuelve al stock.
- **Garantía** (`CO-185`, `CO-099` con Defecto o Error de imprenta): desde «Mi
  cuenta», con fotos, dentro del plazo de garantía. Cubre una unidad. Se resuelve
  con un cambio (`CO-100`), con puntos (`CO-101`) o por el medio de pago.

El Administrador consulta (`CO-186`, `CO-187`) y resuelve o rechaza (`CO-102`).
**Lo que no es registrar se coordina por fuera del sistema**, por correo o
teléfono: la prueba de destrucción, la devolución del artículo.

**El plazo corre desde la entrega que el sistema conoce**: el despacho, o el
retiro en el local (B-09-002; límite «Trazabilidad logística de última milla»).

**Orden de bloqueo: producto, caso.**
"""

import logging
from dataclasses import dataclass, field
from datetime import timedelta
from decimal import Decimal

from django.conf import settings
from django.db import IntegrityError, transaction
from django.db.models import Min, Q
from django.urls import reverse
from django.utils import timezone

from apps.catalog.models import Producto
from apps.core import imagenes
from apps.core.models import ConfiguracionSistema, RegistroAuditoria
from apps.core.segundo_plano import despues_del_commit
from apps.devoluciones.models import CasoDevolucion, EvidenciaDevolucion
from apps.pedidos import avisos
from apps.pedidos.models import LineaPedido, Pedido, TransaccionPago
from apps.puntos import servicios as puntos
from apps.puntos.models import LotePuntos

logger = logging.getLogger(__name__)

MAXIMO_IMAGENES = 5
LARGO_DESCRIPCION = 2000

ARREPENTIMIENTO = "arrepentimiento"
GARANTIA = "garantia"


class OperacionRechazada(ValueError):
    """El reclamo o el caso no están como la operación necesita."""


class PlazoVencido(OperacionRechazada):
    """`CO-099` E1, `CO-185` E1."""


class CasoExistente(OperacionRechazada):
    """`CO-099` E2, `CO-185` E2: se informa el caso y su estado."""

    def __init__(self, mensaje, casos=()):
        super().__init__(mensaje)
        self.casos = list(casos)


class EvidenciaInvalida(OperacionRechazada):
    """`CO-099` E3 (sin foto) y E4 (una foto que no se admite)."""


class SinStock(OperacionRechazada):
    """`CO-100` E1: el reemplazo no tiene stock disponible."""


def nombre(producto):
    return str(producto.especifico)


def _fecha(momento):
    return timezone.localtime(momento).strftime("%d/%m/%Y")


def _enlace(origen, nombre_url, *args):
    origen = origen or settings.URL_PUBLICA
    return origen + reverse(nombre_url, args=args) if origen else ""


def _tiene_caso(linea):
    try:
        linea.caso_devolucion  # noqa: B018 - la relación inversa existe o levanta
    except CasoDevolucion.DoesNotExist:
        return False
    return True


def tipo_de(motivo):
    return ARREPENTIMIENTO if motivo == CasoDevolucion.ARREPENTIMIENTO else GARANTIA


# ---------------------------------------------------------------------------
# El plazo y lo que se puede reclamar
# ---------------------------------------------------------------------------


def plazo_dias(tipo=ARREPENTIMIENTO):
    configuracion = ConfiguracionSistema.obtener()
    if tipo == GARANTIA:
        return configuracion.plazo_garantia_dias
    return configuracion.plazo_devolucion_dias


def despachado_en(pedido):
    """El momento en que el pedido pasó a Despachado (B-09-002), o en que se vendió
    en el mostrador (B-06-005)."""
    transicion = (
        pedido.transiciones.filter(estado_nuevo__in=(Pedido.DESPACHADO, Pedido.VENDIDO_EN_LOCAL))
        .order_by("-ocurrida_en", "-pk")
        .first()
    )
    return transicion.ocurrida_en if transicion else pedido.fecha


def plazo_vence(pedido, dias=None):
    return despachado_en(pedido) + timedelta(days=plazo_dias() if dias is None else dias)


# Un pedido para retirar nunca se despacha: cada línea cuenta desde que se
# retiró —o se envió desde el stock en local— alguna de sus unidades.
ENTREGADOS = ("retirado", "despachado")


def entregada_en(linea):
    if not linea.pedido.retiro:
        return despachado_en(linea.pedido)
    return linea.articulos_retenidos.filter(estado__in=ENTREGADOS).aggregate(
        momento=Min("actualizado_en")
    )["momento"]


def vence_linea(linea, tipo=ARREPENTIMIENTO):
    return entregada_en(linea) + timedelta(days=plazo_dias(tipo))


def _en_condiciones(pedido):
    return pedido.estado in (Pedido.DESPACHADO, Pedido.VENDIDO_EN_LOCAL) or (
        pedido.retiro and pedido.estado == Pedido.EN_LOCAL
    )


def _admite_tipo(pedido, tipo):
    if tipo == ARREPENTIMIENTO:
        return pedido.canal == Pedido.ONLINE  # venta a distancia
    return bool(pedido.usuario_id)  # la garantía se reclama desde «Mi cuenta»


def lineas_reclamables(pedido):
    """Las que llegaron al Cliente con el pedido: ni canceladas ni diferidas. En un
    pedido para retirar, las que tienen alguna unidad entregada."""
    lineas = LineaPedido.objects.filter(pedido=pedido)
    if pedido.retiro:
        lineas = lineas.filter(articulos_retenidos__estado__in=ENTREGADOS).distinct()
    else:
        lineas = lineas.filter(estado__in=LineaPedido.ENTREGADAS)
    return lineas.select_related(
        "pedido", "producto", "producto__productoeditorial", "caso_devolucion"
    ).order_by("pk")


@dataclass
class EstadoDeReclamo:
    """Para el detalle del pedido: si el botón se ofrece y hasta cuándo."""

    puede: bool
    hasta: object


def estado_de_reclamo(pedido, tipo=GARANTIA, ahora=None):
    if not _admite_tipo(pedido, tipo) or not _en_condiciones(pedido):
        return None
    libres = [linea for linea in lineas_reclamables(pedido) if not _tiene_caso(linea)]
    if not libres:
        return None
    ahora = ahora or timezone.now()
    vences = [vence_linea(linea, tipo) for linea in libres]
    vigentes = [vence for vence in vences if ahora <= vence]
    return EstadoDeReclamo(puede=bool(vigentes), hasta=max(vigentes or vences))


def admite_reclamos(pedido, tipo=GARANTIA, ahora=None):
    estado = estado_de_reclamo(pedido, tipo, ahora)
    return bool(estado and estado.puede)


def _verificar_pedido(pedido, tipo):
    if not _admite_tipo(pedido, tipo):
        raise OperacionRechazada(
            "El arrepentimiento es para compras online."
            if tipo == ARREPENTIMIENTO
            else "Para reclamar un defecto, ingresá a tu cuenta o escribinos al local."
        )
    if not _en_condiciones(pedido):
        raise OperacionRechazada(
            "Todavía no retiraste nada de este pedido."
            if pedido.retiro
            else "Sólo se puede reclamar sobre un pedido despachado."
        )


def _sin_lineas(pedido):
    if pedido.retiro:
        return "Todavía no retiraste nada de este pedido."
    return "Este pedido no tiene artículos para reclamar."


def _plazo_vencido(vence, tipo):
    que = "arrepentirte de la compra" if tipo == ARREPENTIMIENTO else "reclamar un defecto"
    return PlazoVencido(f"El plazo para {que} venció el {_fecha(vence)}.")  # E1


# ---------------------------------------------------------------------------
# CO-185 iniciarSolicitudDeDevolucion · CO-099 registrarCasoDeDevolucion
# ---------------------------------------------------------------------------


@dataclass
class Solicitud:
    pedido: Pedido
    tipo: str
    lineas: list
    existentes: list = field(default_factory=list)
    vence: object = None

    @property
    def motivos(self):
        if self.tipo == ARREPENTIMIENTO:
            return []
        return [
            par
            for par in CasoDevolucion.MOTIVO_CHOICES
            if par[0] in CasoDevolucion.MOTIVOS_DE_GARANTIA
        ]


def iniciar_solicitud(pedido, tipo=GARANTIA):
    """`CO-185`: los artículos que todavía admiten un reclamo de ese tipo. Sólo lee."""
    _verificar_pedido(pedido, tipo)
    lineas = list(lineas_reclamables(pedido))
    if not lineas:
        raise OperacionRechazada(_sin_lineas(pedido))
    ahora = timezone.now()
    vences = {linea.pk: vence_linea(linea, tipo) for linea in lineas}
    vigentes = [linea for linea in lineas if ahora <= vences[linea.pk]]
    if not vigentes:
        raise _plazo_vencido(max(vences.values()), tipo)
    libres = [linea for linea in vigentes if not _tiene_caso(linea)]
    existentes = [linea.caso_devolucion for linea in lineas if _tiene_caso(linea)]
    if not libres:
        raise CasoExistente(  # E2
            "Ya hay un reclamo por cada artículo de este pedido.", casos=existentes
        )
    return Solicitud(
        pedido=pedido,
        tipo=tipo,
        lineas=libres,
        existentes=existentes,
        vence=min(vences[linea.pk] for linea in libres),
    )


def _procesar_evidencia(archivos, *, obligatoria=True):
    archivos = [archivo for archivo in archivos if archivo]
    if not archivos and obligatoria:
        raise EvidenciaInvalida(  # E3
            "Adjuntá al menos una foto del artículo: la evidencia es obligatoria para "
            "procesar el reclamo."
        )
    if len(archivos) > MAXIMO_IMAGENES:
        raise EvidenciaInvalida(f"Se admiten hasta {MAXIMO_IMAGENES} fotos por reclamo.")
    procesadas = []
    for archivo in archivos:
        try:
            procesadas.append(imagenes.procesar(archivo))
        except imagenes.ImagenInvalida as error:  # E4: el problema específico de ese archivo
            raise EvidenciaInvalida(
                f"«{archivo.name}»: {error} Adjuntá una imagen válida."
            ) from error
    return procesadas


@dataclass
class Apertura:
    casos: list
    vence: object

    @property
    def caso(self):
        return self.casos[0]


def _linea_para(pedido, linea_pk, tipo):
    linea = lineas_reclamables(pedido).filter(pk=linea_pk).first()
    if linea is None:
        raise OperacionRechazada("Elegí el artículo sobre el que querés reclamar.")
    vence = vence_linea(linea, tipo)
    if timezone.now() > vence:
        raise _plazo_vencido(vence, tipo)
    if _tiene_caso(linea):
        raise CasoExistente(  # E2
            "Ya hay un reclamo por este artículo.", casos=[linea.caso_devolucion]
        )
    return linea, vence


def _descripcion(texto):
    texto = (texto or "").strip()
    if len(texto) > LARGO_DESCRIPCION:
        raise OperacionRechazada(f"La descripción admite hasta {LARGO_DESCRIPCION} caracteres.")
    return texto


def _crear(pedido, linea, *, usuario, motivo, unidades, descripcion, fotos):
    caso = CasoDevolucion.objects.create(
        linea=linea,
        usuario=usuario,
        correo=usuario.email if usuario else pedido.correo_de_contacto,
        motivo=motivo,
        unidades=unidades,
        descripcion=descripcion,
        abierto_en=timezone.now(),
    )
    for foto in fotos:
        evidencia = EvidenciaDevolucion(caso=caso)
        evidencia.imagen.save(foto.name, foto, save=True)
    RegistroAuditoria.registrar(
        accion=RegistroAuditoria.APERTURA_DEVOLUCION,
        actor=usuario,
        actor_email=caso.correo,
        objetivo=caso,
        objetivo_email=caso.correo,
        detalle=(
            f"Caso {caso.numero}: pedido {pedido.numero}, {unidades} × {nombre(linea.producto)}, "
            f"{caso.get_motivo_display().lower()}, {len(fotos)} foto(s)."
        ),
    )
    return caso


def _con_unicidad(lineas, crear):
    """I-19: otra pestaña pudo abrir el caso de la misma línea mientras tanto."""
    try:
        with transaction.atomic():
            return crear()
    except IntegrityError as error:
        existentes = list(CasoDevolucion.objects.filter(linea__in=lineas))
        if not existentes:
            raise
        raise CasoExistente("Ya hay un reclamo por este artículo.", casos=existentes) from error


def registrar_caso(pedido, linea_pk, usuario, motivo, descripcion, archivos, *, origen=""):
    """`CO-099` de garantía. Todo o nada: con una foto inválida no queda nada."""
    if pedido.usuario_id != usuario.pk:
        raise OperacionRechazada("El pedido no es tuyo.")
    if motivo not in CasoDevolucion.MOTIVOS_DE_GARANTIA:
        raise OperacionRechazada("Elegí el motivo del reclamo.")
    _verificar_pedido(pedido, GARANTIA)
    if not lineas_reclamables(pedido).exists():
        raise OperacionRechazada(_sin_lineas(pedido))
    linea, vence = _linea_para(pedido, linea_pk, GARANTIA)
    descripcion = _descripcion(descripcion)
    fotos = _procesar_evidencia(archivos)

    def crear():
        caso = _crear(
            pedido,
            linea,
            usuario=usuario,
            motivo=motivo,
            unidades=1,
            descripcion=descripcion,
            fotos=fotos,
        )
        despues_del_commit(_avisar_apertura, [caso], origen)
        return [caso]

    return Apertura(casos=_con_unicidad([linea], crear), vence=vence)


def registrar_arrepentimiento(pedido, lineas_pks, *, usuario=None, descripcion="", origen=""):
    """`CO-099` de arrepentimiento: un caso por línea elegida, la línea entera.

    Sin sesión, quien llega acá ya probó el número de pedido y su correo
    (`pedido_por_numero_y_correo`). Todo o nada.
    """
    if usuario is not None and pedido.usuario_id not in (None, usuario.pk):
        raise OperacionRechazada("El pedido no es tuyo.")
    _verificar_pedido(pedido, ARREPENTIMIENTO)
    if not lineas_reclamables(pedido).exists():
        raise OperacionRechazada(_sin_lineas(pedido))
    pks = list(dict.fromkeys(lineas_pks))
    if not pks:
        raise OperacionRechazada("Elegí al menos un artículo.")
    elegidas = [_linea_para(pedido, pk, ARREPENTIMIENTO) for pk in pks]
    descripcion = _descripcion(descripcion)

    def crear():
        casos = [
            _crear(
                pedido,
                linea,
                usuario=usuario if usuario is not None else pedido.usuario,
                motivo=CasoDevolucion.ARREPENTIMIENTO,
                unidades=linea.cantidad,
                descripcion=descripcion,
                fotos=[],
            )
            for linea, _ in elegidas
        ]
        despues_del_commit(_avisar_apertura, casos, origen)
        return casos

    casos = _con_unicidad([linea for linea, _ in elegidas], crear)
    return Apertura(casos=casos, vence=min(vence for _, vence in elegidas))


def pedido_por_numero_y_correo(numero, correo):
    """El pedido online que corresponde a ese número y a ese correo, o `None`.

    El botón de arrepentimiento no pide registración: el número de pedido y el
    correo de la compra, juntos, prueban que quien pide es quien compró.
    """
    numero, correo = (numero or "").strip(), (correo or "").strip().lower()
    if not numero or not correo:
        return None
    pedido = (
        Pedido.objects.filter(numero=numero, canal=Pedido.ONLINE).select_related("usuario").first()
    )
    if pedido is None or pedido.correo_de_contacto.lower() != correo:
        return None
    return pedido


def _avisar_apertura(casos, origen):
    """`CU-DEV-SOL` paso 5 y 6: el Administrador sabe del caso, y el Cliente recibe
    su código (Res. 424/2020)."""
    primero = casos[0]
    pedido = primero.linea.pedido
    codigos = ", ".join(caso.numero for caso in casos)
    filas = [(caso.numero, f"{caso.unidades} × {nombre(caso.linea.producto)}") for caso in casos]
    avisos.avisar_administradores(
        tipo="devoluciones",
        asunto=f"Nuevo reclamo {codigos}",
        rotulo="Devoluciones",
        antetitulo="Caso de devolución",
        titulo=primero.get_motivo_display(),
        parrafos=[f"{primero.correo} abrió un reclamo sobre el pedido {pedido.numero}."],
        filas=filas,
        enlace=_enlace(origen, "devoluciones:detalle", primero.pk),
        texto_enlace="Revisar el caso",
        # B-19-014: por Telegram, con sus fotos achicadas (ambigüedad 6 del plan
        # de la etapa 3, aprobada): sólo a los Administradores vinculados.
        fotos=[evidencia.imagen for caso in casos for evidencia in caso.evidencias.all()],
    )
    if primero.es_arrepentimiento:
        siguiente = (
            "Te vamos a escribir para coordinar la devolución del artículo. Cuando lo "
            "recibamos, te reintegramos lo que pagaste."
        )
    else:
        siguiente = (
            "Te vamos a escribir para revisar el defecto y coordinar el cambio o el reintegro."
        )
    avisos.avisar(
        [primero.correo],
        asunto=f"Recibimos tu reclamo {codigos}",
        rotulo="Devoluciones",
        antetitulo=f"Pedido {pedido.numero}",
        titulo=primero.get_motivo_display(),
        parrafos=[f"Registramos tu reclamo. Tu código es {codigos}.", siguiente],
        filas=filas,
    )


# ---------------------------------------------------------------------------
# CO-186 consultarCasosDeDevolucion · CO-187 consultarDetalleDeCasoDeDevolucion
# ---------------------------------------------------------------------------

FILTROS = {  # noqa: RUF012 - el filtro del historial (E2)
    "pendientes": (CasoDevolucion.PENDIENTE,),
    "resueltos": (CasoDevolucion.RESUELTO,),
    "rechazados": (CasoDevolucion.RECHAZADO,),
    "historial": (CasoDevolucion.RESUELTO, CasoDevolucion.RECHAZADO),
}


def consultar_casos(filtro="pendientes"):
    """`CO-186`: los pendientes, los más antiguos primero; o el historial filtrado."""
    estados = FILTROS.get(filtro, FILTROS["pendientes"])
    return (
        CasoDevolucion.objects.filter(estado__in=estados)
        .select_related(
            "usuario",
            "linea__pedido",
            "linea__producto",
            "linea__producto__productoeditorial",
        )
        .order_by("abierto_en", "pk")
    )


def detalle(caso_pk):
    """`CO-187`: el caso con su contacto, su pedido, su ítem y sus fotos."""
    return (
        CasoDevolucion.objects.select_related(
            "usuario",
            "linea__pedido",
            "linea__producto",
            "linea__producto__productoeditorial",
            "producto_reemplazo",
            "resuelto_por",
        )
        .prefetch_related("evidencias")
        .get(pk=caso_pk)
    )


@dataclass
class Opciones:
    """Qué resoluciones admite el caso (plan 00, C1)."""

    cambio: bool
    puntos: bool
    medio: bool


def opciones(caso):
    linea = caso.linea
    pagado_en_dinero = not linea.cubierta_con_puntos
    medio = pagado_en_dinero and _cobrado_por_la_pasarela(linea.pedido)
    if caso.es_arrepentimiento:
        return Opciones(cambio=False, puntos=not pagado_en_dinero, medio=medio)
    return Opciones(cambio=bool(caso.usuario_id), puntos=bool(caso.usuario_id), medio=medio)


def _pagos_por_la_pasarela(pedido):
    return TransaccionPago.objects.filter(
        pedido=pedido, medio=TransaccionPago.PASARELA, estado=TransaccionPago.APROBADO
    )


def _cobrado_por_la_pasarela(pedido):
    return pedido.canal == Pedido.ONLINE and _pagos_por_la_pasarela(pedido).exists()


def con_stock(producto):
    return producto.estado == Producto.ACTIVO and producto.stock > 0


def _reemplazos_de(caso):
    """R7: un tomo de la misma editorial y el mismo formato; si no es editorial, el
    mismo producto."""
    reclamado = caso.linea.producto.especifico
    editorial = getattr(reclamado, "editorial_id", None)
    formato = getattr(reclamado, "formato_id", None)
    if editorial and formato:
        return Producto.objects.filter(
            productoeditorial__editorial_id=editorial, productoeditorial__formato_id=formato
        )
    return Producto.objects.filter(pk=caso.linea.producto_id)


def buscar_reemplazos(caso, texto, limite=20):
    """Los candidatos al cambio. Los que no tienen stock se muestran sin poder elegirse (E1)."""
    texto = (texto or "").strip()
    if not texto:
        return []
    productos = (
        _reemplazos_de(caso)
        .filter(Q(titulo__icontains=texto) | Q(codigo__iexact=texto))
        .exclude(estado__in=(Producto.DESCATALOGADO, Producto.CANCELADO_EDITORIAL))
        .select_related("productoeditorial")
        .order_by("titulo", "pk")[:limite]
    )
    resultado = list(productos)
    for producto in resultado:
        producto.con_stock = con_stock(producto)
    return resultado


def _caso_pendiente(caso_pk):
    caso = (
        CasoDevolucion.objects.select_for_update(of=("self",))
        .select_related("usuario", "linea__pedido", "linea__producto")
        .get(pk=caso_pk)
    )
    if caso.estado != CasoDevolucion.PENDIENTE:
        raise OperacionRechazada(
            f"El caso ya está {caso.get_estado_display().lower()}: no se registró nada."
        )
    return caso


def _cerrar(caso, actor, resolucion, ahora, **campos):
    caso.estado = CasoDevolucion.RESUELTO
    caso.resolucion = resolucion
    caso.resuelto_en = ahora
    caso.resuelto_por = actor
    for nombre_campo, valor in campos.items():
        setattr(caso, nombre_campo, valor)
    caso.save(update_fields=["estado", "resolucion", "resuelto_en", "resuelto_por", *campos.keys()])


def _volver_al_stock(caso, ahora):
    """El arrepentimiento: el artículo que el local recibió vuelve a la venta."""
    producto = Producto.objects.select_for_update().get(pk=caso.linea.producto_id)
    estado = producto.estado
    if estado == Producto.AGOTADO:
        estado = Producto.ACTIVO
    Producto.objects.filter(pk=producto.pk).update(
        stock=producto.stock + caso.unidades, estado=estado, actualizado_en=ahora
    )
    from apps.restock import servicios as restock

    despues_del_commit(restock.reposicion, producto, caso.unidades)


# ---------------------------------------------------------------------------
# CO-100 resolverCasoConCambio
# ---------------------------------------------------------------------------


def resolver_con_cambio(caso_pk, producto_pk, actor, *, origen=""):
    """El reemplazo queda a nombre del Cliente en el stock en local, para retirar o
    pedir el envío sin costo. Se resuelve después de la prueba de destrucción, que
    se pide y se ve por fuera del sistema."""
    from apps.almacen.models import ArticuloRetenido, vencimiento_desde

    with transaction.atomic():
        producto = Producto.objects.select_for_update().filter(pk=producto_pk).first()
        if producto is None:
            raise OperacionRechazada("Elegí el producto de reemplazo.")
        caso = _caso_pendiente(caso_pk)
        if not opciones(caso).cambio:
            raise OperacionRechazada("Este reclamo no se resuelve con un cambio.")
        if not _reemplazos_de(caso).filter(pk=producto.pk).exists():
            raise OperacionRechazada(
                "El reemplazo tiene que ser de la misma editorial y el mismo formato."
            )
        if not con_stock(producto):
            raise SinStock(  # E1
                f"«{nombre(producto)}» no tiene stock disponible. Elegí otro producto o "
                "resolvé con un reembolso."
            )
        ahora = timezone.now()
        antes = producto.stock
        queda = antes - 1
        Producto.objects.filter(pk=producto.pk).update(
            stock=queda,
            estado=Producto.AGOTADO if queda == 0 else Producto.ACTIVO,
            actualizado_en=ahora,
        )
        hoy = timezone.localdate()
        ArticuloRetenido.objects.create(
            usuario=caso.usuario,
            producto=producto,
            linea_pedido=caso.linea,
            valor=caso.linea.precio_unitario,
            fecha_ingreso=hoy,
            fecha_vencimiento=vencimiento_desde(
                hoy, ConfiguracionSistema.obtener().plazo_retencion_meses
            ),
            procedencia=ArticuloRetenido.CAMBIO,
        )
        _cerrar(caso, actor, CasoDevolucion.CAMBIO, ahora, producto_reemplazo=producto)
        RegistroAuditoria.registrar(
            accion=RegistroAuditoria.DEVOLUCION_CON_CAMBIO,
            actor=actor,
            objetivo=caso,
            objetivo_email=caso.correo,
            detalle=(
                f"Caso {caso.numero}: cambio de {nombre(caso.linea.producto)} por "
                f"{nombre(producto)}, al stock en local del Cliente. Stock del reemplazo: "
                f"{antes} → {queda}."
            ),
        )
        despues_del_commit(_avisar_cambio, caso, producto, origen)
    return caso


def _avisar_cambio(caso, producto, origen):
    avisos.avisar(
        [caso.correo],
        asunto=f"Tu reclamo {caso.numero}: autorizamos el cambio",
        rotulo="Devoluciones",
        antetitulo=f"Reclamo {caso.numero}",
        titulo="Cambio autorizado",
        parrafos=[
            f"Revisamos tu reclamo sobre {nombre(caso.linea.producto)} y autorizamos el cambio.",
            "El reemplazo quedó a tu nombre en el local: retiralo o pedí el envío, sin costo, "
            "desde «Mi cuenta», en Stock en local.",
        ],
        filas=[("Reemplazo", nombre(producto))],
        enlace=_enlace(origen, "cuenta:stock"),
        texto_enlace="Ver mi stock en el local",
    )


# ---------------------------------------------------------------------------
# CO-101 resolverCasoConReembolsoEnPuntos, y por el medio de pago (plan 00, C1)
# ---------------------------------------------------------------------------


def puntos_de_reembolso(linea, equivalencia=None):
    """El 100 % del valor de una unidad, en puntos (B-01-010, B-09-004)."""
    return puntos.puntos_de_una_unidad(linea, equivalencia)


def _completa_el_pedido(caso):
    """Si con este caso el Cliente se arrepiente del pedido entero: se le reintegra
    también el envío (plan 00, ambigüedad 2)."""
    if not caso.es_arrepentimiento:
        return False
    pedido = caso.linea.pedido
    vivas = pedido.lineas.exclude(estado=LineaPedido.CANCELADO_REEMBOLSO).exclude(pk=caso.linea_id)
    return not vivas.exclude(
        caso_devolucion__motivo=CasoDevolucion.ARREPENTIMIENTO,
        caso_devolucion__estado=CasoDevolucion.RESUELTO,
    ).exists()


@dataclass
class Reembolso:
    caso: CasoDevolucion
    puntos: int = 0
    monto: Decimal = Decimal("0")
    saldo: int = 0


def resolver_con_reembolso(caso_pk, actor, *, origen=""):
    """En puntos: el valor de las unidades, menos lo que ganaron con la compra (C2)."""
    with transaction.atomic():
        caso = _caso_pendiente(caso_pk)
        if not opciones(caso).puntos:
            raise OperacionRechazada("Este reclamo no se reembolsa en puntos.")
        linea = caso.linea
        ahora = timezone.now()
        if caso.es_arrepentimiento:
            _volver_al_stock(caso, ahora)
        cantidad = puntos_de_reembolso(linea) * caso.unidades
        envio = 0
        if _completa_el_pedido(caso) and linea.pedido.costo_envio:
            envio = puntos.puntos_para_cubrir(linea.pedido.costo_envio)
        _cerrar(caso, actor, CasoDevolucion.REEMBOLSO, ahora)
        puntos.acreditar(
            caso.usuario,
            cantidad + envio,
            origen=LotePuntos.REEMBOLSO,
            pedido=linea.pedido,
            linea=linea,
            caso=caso,
            motivo=f"Reembolso del reclamo {caso.numero}",
        )
        puntos.descontar_ganados(caso.usuario, linea, caso.unidades)
        RegistroAuditoria.registrar(
            accion=RegistroAuditoria.DEVOLUCION_CON_REEMBOLSO,
            actor=actor,
            objetivo=caso,
            objetivo_email=caso.correo,
            detalle=(
                f"Caso {caso.numero}: reembolso de {cantidad + envio} pts por "
                f"{caso.unidades} × {nombre(linea.producto)}"
                + (" (vuelve al stock)" if caso.es_arrepentimiento else "")
                + "."
            ),
        )
        hecho = Reembolso(caso=caso, puntos=cantidad + envio, saldo=puntos.saldo(caso.usuario))
        despues_del_commit(_avisar_reembolso, hecho, origen)
    return hecho


def monto_por_el_medio(caso):
    """Lo pagado en dinero por las unidades, más el envío si completa el pedido."""
    linea = caso.linea
    monto = linea.precio_unitario * caso.unidades
    if _completa_el_pedido(caso):
        monto += linea.pedido.costo_envio
    return monto


def resolver_con_reembolso_por_el_medio(caso_pk, actor, *, origen=""):
    """Se registra lo que el local devuelve desde el panel de la pasarela.

    El sistema no mueve el dinero (plan 00, descartes): devolverlo desde la API
    pediría transacciones negativas en la caja (I-09).
    """
    with transaction.atomic():
        caso = _caso_pendiente(caso_pk)
        if not opciones(caso).medio:
            raise OperacionRechazada(
                "Este reclamo no se reembolsa por el medio de pago: no se cobró por la pasarela."
            )
        linea = caso.linea
        ahora = timezone.now()
        if caso.es_arrepentimiento:
            _volver_al_stock(caso, ahora)
        monto = monto_por_el_medio(caso)
        _cerrar(caso, actor, CasoDevolucion.REEMBOLSO_MEDIO, ahora, monto_reembolsado=monto)
        descontados = puntos.descontar_ganados(caso.usuario, linea, caso.unidades)
        transaccion = _pagos_por_la_pasarela(linea.pedido).first()
        RegistroAuditoria.registrar(
            accion=RegistroAuditoria.DEVOLUCION_REEMBOLSO_MEDIO,
            actor=actor,
            objetivo=caso,
            objetivo_email=caso.correo,
            detalle=(
                f"Caso {caso.numero}: reembolso por el medio de pago de {monto} "
                f"(pago {transaccion.referencia or transaccion.pk}) por {caso.unidades} × "
                f"{nombre(linea.producto)}"
                + (" (vuelve al stock)" if caso.es_arrepentimiento else "")
                + (f"; se descontaron {descontados} pts ganados" if descontados else "")
                + "."
            ),
        )
        hecho = Reembolso(caso=caso, monto=monto)
        despues_del_commit(_avisar_reembolso, hecho, origen)
    return hecho


def _avisar_reembolso(hecho, origen):
    caso = hecho.caso
    if hecho.monto:
        filas = [("Reintegro", f"$ {hecho.monto}")]
        parrafo = (
            "Te reintegramos lo que pagaste por el mismo medio de pago. Según tu banco, "
            "puede tardar unos días en verse."
        )
    else:
        filas = [("Acreditados", f"{hecho.puntos} pts"), ("Tu saldo", f"{hecho.saldo} pts")]
        parrafo = "Te acreditamos el valor del artículo en puntos."
    avisos.avisar(
        [caso.correo],
        asunto=f"Tu reclamo {caso.numero}: te reintegramos",
        rotulo="Devoluciones",
        antetitulo=f"Reclamo {caso.numero}",
        titulo="Reintegro",
        parrafos=[parrafo],
        filas=filas,
        enlace=_enlace(origen, "cuenta:puntos") if hecho.puntos else "",
        texto_enlace="Ver mis puntos" if hecho.puntos else "",
    )


# ---------------------------------------------------------------------------
# CO-102 rechazarCasoDeDevolucion
# ---------------------------------------------------------------------------


def rechazar(caso_pk, actor, motivo, *, origen=""):
    motivo = (motivo or "").strip()
    if not motivo:
        raise OperacionRechazada("El motivo del rechazo es obligatorio.")
    with transaction.atomic():
        caso = _caso_pendiente(caso_pk)
        caso.estado = CasoDevolucion.RECHAZADO
        caso.motivo_rechazo = motivo
        caso.resuelto_en = timezone.now()
        caso.resuelto_por = actor
        caso.save(update_fields=["estado", "motivo_rechazo", "resuelto_en", "resuelto_por"])
        RegistroAuditoria.registrar(
            accion=RegistroAuditoria.RECHAZO_DEVOLUCION,
            actor=actor,
            objetivo=caso,
            objetivo_email=caso.correo,
            detalle=f"Caso {caso.numero}: rechazado. Motivo: {motivo}",
        )
        despues_del_commit(_avisar_rechazo, caso, origen)
    return caso


def _avisar_rechazo(caso, origen):
    avisos.avisar(
        [caso.correo],
        asunto=f"Tu reclamo {caso.numero}: no corresponde",
        rotulo="Devoluciones",
        antetitulo=f"Reclamo {caso.numero}",
        titulo="Reclamo rechazado",
        parrafos=[
            f"Revisamos tu reclamo sobre {nombre(caso.linea.producto)} y no corresponde.",
            f"Motivo: {caso.motivo_rechazo}",
        ],
    )
