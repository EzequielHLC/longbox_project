"""Las ofertas (módulo 03, plan 03 segunda parte).

`CO-054` registrar, `CO-055` registrar aceptando el tope de $1, `CO-056` editar,
`CO-057` y `CO-058` la baja en dos pasos, `CO-059` el ciclo del Temporizador, y
las consultas `CO-169` y `CO-170`.

**El precio guardado del producto no se toca.** Una oferta cambia el precio
visible (`apps.catalog.precio_visible`). Lo que sí se escribe, en cada operación
que cambia qué descuenta, es el precio vigente de las líneas de carrito de los
productos alcanzados: es la postcondición «las `LineaCarrito` afectadas quedaron
actualizadas» de cada contrato.

**Solapamiento (I-20).** Dos ofertas vivas sobre el mismo producto, o sobre el
mismo tipo, no pueden compartir días. Una individual y una de su tipo sí: manda
la individual (plan 03, segunda parte, ambigüedad 3). La validación y el alta van
en una transacción con bloqueo sobre el producto o el tipo del alcance, para
que dos administradores no registren a la vez dos ofertas que se pisan.
"""

from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal

from django.db import transaction
from django.db.models import Q

from apps.catalog.models import Oferta, Producto, Tipo
from apps.catalog.precio_visible import OfertasDelDia, descontar, hoy_local
from apps.core.models import RegistroAuditoria

ESTADOS_EN_TIENDA = (Producto.ACTIVO, Producto.PRE_VENTA)

# Quién figura en el log cuando actúa el Temporizador (`CO-059`).
TEMPORIZADOR = "Temporizador del Sistema"


class OfertaRechazada(ValueError):
    """Una validación que no se cumple. `campo` dice dónde mostrarla."""

    def __init__(self, mensaje, campo=None):
        super().__init__(mensaje)
        self.campo = campo


class TopeRequerido(Exception):
    """`CU-PVP-ALT` E3: el monto fijo alcanza o supera el precio de estos productos."""

    def __init__(self, afectados):
        super().__init__("El descuento deja productos en cero o menos.")
        self.afectados = afectados


@dataclass
class DatosDeOferta:
    descripcion: str
    fecha_inicio: date
    fecha_vencimiento: date
    tipo_descuento: str
    valor: Decimal
    alcance: str
    producto: Producto | None = None
    tipo: Tipo | None = None

    @classmethod
    def de(cls, oferta):
        return cls(
            descripcion=oferta.descripcion,
            fecha_inicio=oferta.fecha_inicio,
            fecha_vencimiento=oferta.fecha_vencimiento,
            tipo_descuento=oferta.tipo_descuento,
            valor=oferta.valor,
            alcance=oferta.alcance,
            producto=oferta.producto,
            tipo=oferta.tipo,
        )


# ---------------------------------------------------------------------------
# Alcance
# ---------------------------------------------------------------------------


def productos_del_alcance(alcance, producto=None, tipo=None):
    """Los productos que la oferta descuenta: el elegido, o los de la tienda de ese tipo.

    Del tipo cuentan los que se ofrecen en la tienda, Activos y en Pre-venta
    (plan 03, segunda parte, ambigüedad 5).
    """
    if alcance == Oferta.PRODUCTO:
        return Producto.objects.filter(pk=producto.pk)
    return Producto.objects.filter(tipo=tipo, estado__in=ESTADOS_EN_TIENDA)


def productos_tocados(alcance, producto=None, tipo=None):
    """Los productos cuyo precio visible puede cambiar: los del tipo en cualquier estado.

    Es el conjunto que se usa para actualizar carritos: una línea con un
    producto que hoy está Agotado también tiene que quedar con su precio.
    """
    if alcance == Oferta.PRODUCTO:
        return Producto.objects.filter(pk=producto.pk)
    return Producto.objects.filter(tipo=tipo)


def _tocados_por(oferta):
    return productos_tocados(oferta.alcance, oferta.producto, oferta.tipo)


def describir_alcance(alcance, producto=None, tipo=None):
    if alcance == Oferta.PRODUCTO:
        return f"Producto: {producto.titulo} ({producto.codigo})"
    return f"Tipo de material: {tipo.nombre}"


def describir_descuento(tipo_descuento, valor):
    if tipo_descuento == Oferta.PORCENTAJE:
        texto = f"{Decimal(valor).normalize():f}".replace(".", ",")
        return f"{texto} %"
    return _pesos(valor)


def describir(oferta, hoy=None):
    hoy = hoy or hoy_local()
    return (
        f"«{oferta.descripcion}» · {describir_descuento(oferta.tipo_descuento, oferta.valor)} · "
        f"{describir_alcance(oferta.alcance, oferta.producto, oferta.tipo)} · "
        f"{oferta.fecha_inicio:%d/%m/%Y} a {oferta.fecha_vencimiento:%d/%m/%Y} · "
        f"{dict(Oferta.ESTADOS)[oferta.estado_en(hoy)]}"
    )


def _pesos(valor):
    entero = Decimal(valor).quantize(Decimal("1"))
    texto = f"{entero:,}".replace(",", ".")
    if Decimal(valor) != entero:
        centavos = f"{Decimal(valor):.2f}".split(".")[1]
        texto = f"{texto},{centavos}"
    return f"$ {texto}"


# ---------------------------------------------------------------------------
# Validaciones — CU-PVP-ALT paso 5, las mismas en CU-PVP-EDI paso 4
# ---------------------------------------------------------------------------


def solapada(datos, *, hoy, excluir=None):
    """La oferta viva del mismo alcance que comparte días con éstas, o `None` (E2)."""
    candidatas = Oferta.objects.vivas(hoy).filter(
        alcance=datos.alcance,
        fecha_inicio__lte=datos.fecha_vencimiento,
        fecha_vencimiento__gte=datos.fecha_inicio,
    )
    if datos.alcance == Oferta.PRODUCTO:
        candidatas = candidatas.filter(producto=datos.producto)
    else:
        candidatas = candidatas.filter(tipo=datos.tipo)
    if excluir is not None:
        candidatas = candidatas.exclude(pk=excluir)
    return candidatas.order_by("fecha_inicio", "pk").first()


def bajo_tope(datos):
    """E3: los productos cuyo precio no supera el monto fijo. Quedarían en cero o menos."""
    if datos.tipo_descuento != Oferta.MONTO_FIJO:
        return []
    return list(
        productos_del_alcance(datos.alcance, datos.producto, datos.tipo)
        .filter(precio__lte=datos.valor)
        .order_by("titulo", "pk")
    )


def validar(datos, *, hoy, excluir=None):
    """Coherencia de fechas (E1), solapamiento (E2) y un porcentaje posible.

    El tope de los montos fijos (E3) no se valida acá: no rechaza, pide confirmación.
    """
    if datos.fecha_vencimiento <= hoy:
        raise OfertaRechazada(
            "El vencimiento tiene que ser una fecha futura.", campo="fecha_vencimiento"
        )
    if datos.fecha_inicio > datos.fecha_vencimiento:
        raise OfertaRechazada(
            "La fecha de inicio no puede ser posterior al vencimiento.", campo="fecha_inicio"
        )
    if datos.tipo_descuento == Oferta.PORCENTAJE and datos.valor >= 100:
        raise OfertaRechazada("Un descuento del 100 % o más deja el precio en cero.", campo="valor")
    conflicto = solapada(datos, hoy=hoy, excluir=excluir)
    if conflicto is not None:
        desde = max(conflicto.fecha_inicio, datos.fecha_inicio)
        hasta = min(conflicto.fecha_vencimiento, datos.fecha_vencimiento)
        raise OfertaRechazada(
            f"Se superpone con la oferta «{conflicto.descripcion}» del "
            f"{desde:%d/%m/%Y} al {hasta:%d/%m/%Y}."
        )


def tipo_sin_productos(datos):
    """A1: un tipo sin productos en la tienda. Es un aviso, no un rechazo."""
    return (
        datos.alcance == Oferta.TIPO
        and not productos_del_alcance(datos.alcance, tipo=datos.tipo).exists()
    )


def _bloquear_destino(datos):
    if datos.alcance == Oferta.PRODUCTO:
        Producto.objects.select_for_update().get(pk=datos.producto.pk)
    else:
        Tipo.objects.select_for_update().get(pk=datos.tipo.pk)


def _actualizar_carritos(productos):
    """Se importa acá: el carrito depende del catálogo, y no al revés."""
    from apps.tienda.carrito import actualizar_precios

    return actualizar_precios(productos)


def _carritos_con(productos):
    from apps.tienda.carrito import carritos_con

    return carritos_con(productos)


# ---------------------------------------------------------------------------
# Alta — CO-054 y CO-055
# ---------------------------------------------------------------------------


def registrar(datos, *, actor, ip=None, aceptar_tope=False, hoy=None):
    """`CO-054`, o `CO-055` con `aceptar_tope`: la oferta queda Activa o Programada.

    Si el monto fijo deja productos en cero o menos y no se aceptó el tope,
    levanta `TopeRequerido` con la lista (E3) y no registra nada.
    """
    hoy = hoy or hoy_local()
    with transaction.atomic():
        _bloquear_destino(datos)
        validar(datos, hoy=hoy)
        afectados = bajo_tope(datos)
        if afectados and not aceptar_tope:
            raise TopeRequerido(afectados)

        oferta = Oferta.objects.create(
            descripcion=datos.descripcion,
            fecha_inicio=datos.fecha_inicio,
            fecha_vencimiento=datos.fecha_vencimiento,
            tipo_descuento=datos.tipo_descuento,
            valor=datos.valor,
            alcance=datos.alcance,
            producto=datos.producto if datos.alcance == Oferta.PRODUCTO else None,
            tipo=datos.tipo if datos.alcance == Oferta.TIPO else None,
            estado=Oferta.ACTIVA if datos.fecha_inicio <= hoy else Oferta.PROGRAMADA,
        )
        detalle = describir(oferta, hoy)
        if afectados:
            detalle += f" · precio mínimo de $ 1 en {len(afectados)} producto(s)"
        RegistroAuditoria.registrar(
            accion=RegistroAuditoria.ALTA_OFERTA,
            actor=actor,
            objetivo=oferta,
            ip=ip,
            detalle=detalle,
        )
        if oferta.estado == Oferta.ACTIVA:
            _actualizar_carritos(_tocados_por(oferta))
    return oferta


# ---------------------------------------------------------------------------
# Edición — CO-168 y CO-056
# ---------------------------------------------------------------------------

CAMPOS_EDITABLES = (
    ("descripcion", "descripción"),
    ("fecha_inicio", "fecha de inicio"),
    ("fecha_vencimiento", "fecha de vencimiento"),
    ("tipo_descuento", "tipo de descuento"),
    ("valor", "valor"),
    ("alcance", "alcance"),
)


def se_puede_editar(oferta, hoy=None):
    """`CO-168`: Activa o Programada. Vencida y Dada de baja no se editan (E2)."""
    return oferta.estado_en(hoy or hoy_local()) not in Oferta.TERMINALES


def editar(oferta, datos, *, actor, ip=None, aceptar_tope=False, hoy=None):
    """`CO-056`: los campos nuevos y, si cambió qué descuenta, los carritos al día.

    Si el alcance se redujo (A1), los productos que quedaron afuera vuelven a su
    precio sin descuento: no hace falta tocarlos, porque el descuento nunca se
    escribió en ellos. Lo que se actualiza son sus líneas de carrito.

    Devuelve la lista de cambios, vacía si no hubo ninguno.
    """
    hoy = hoy or hoy_local()
    with transaction.atomic():
        oferta = Oferta.objects.select_for_update().get(pk=oferta.pk)
        if not se_puede_editar(oferta, hoy):
            raise OfertaRechazada(
                "Una oferta vencida o dada de baja no se puede modificar. "
                "Para volver a aplicar el descuento, creá una oferta nueva."
            )
        _bloquear_destino(datos)
        validar(datos, hoy=hoy, excluir=oferta.pk)
        afectados = bajo_tope(datos)
        if afectados and not aceptar_tope:
            raise TopeRequerido(afectados)

        antes = DatosDeOferta.de(oferta)
        tocados_antes = list(_tocados_por(oferta).values_list("pk", flat=True))
        cambios = _cambios(antes, datos)
        if not cambios:
            return []

        for campo, _ in CAMPOS_EDITABLES:
            setattr(oferta, campo, getattr(datos, campo))
        oferta.producto = datos.producto if datos.alcance == Oferta.PRODUCTO else None
        oferta.tipo = datos.tipo if datos.alcance == Oferta.TIPO else None
        oferta.estado = Oferta.ACTIVA if datos.fecha_inicio <= hoy else Oferta.PROGRAMADA
        oferta.save()

        RegistroAuditoria.registrar(
            accion=RegistroAuditoria.MODIFICACION_OFERTA,
            actor=actor,
            objetivo=oferta,
            ip=ip,
            detalle=f"«{oferta.descripcion}»: " + "; ".join(cambios),
        )
        tocados = set(tocados_antes) | set(_tocados_por(oferta).values_list("pk", flat=True))
        _actualizar_carritos(Producto.objects.filter(pk__in=tocados))
    return cambios


def _cambios(antes, despues):
    cambios = []
    for campo, nombre in CAMPOS_EDITABLES:
        anterior, nuevo = getattr(antes, campo), getattr(despues, campo)
        if campo == "alcance":
            anterior = describir_alcance(antes.alcance, antes.producto, antes.tipo)
            nuevo = describir_alcance(despues.alcance, despues.producto, despues.tipo)
        elif campo == "valor":
            anterior = describir_descuento(antes.tipo_descuento, antes.valor)
            nuevo = describir_descuento(despues.tipo_descuento, despues.valor)
        elif campo == "tipo_descuento":
            anterior = dict(Oferta.TIPOS_DE_DESCUENTO)[anterior]
            nuevo = dict(Oferta.TIPOS_DE_DESCUENTO)[nuevo]
        elif isinstance(anterior, date):
            anterior, nuevo = f"{anterior:%d/%m/%Y}", f"{nuevo:%d/%m/%Y}"
        if anterior != nuevo:
            cambios.append(f"{nombre}: «{anterior}» → «{nuevo}»")
    return cambios


# ---------------------------------------------------------------------------
# Baja — CO-057 y CO-058
# ---------------------------------------------------------------------------


class OfertaVencida(OfertaRechazada):
    """`CU-PVP-BAJ` E1: ya venció; los precios ya se restauraron."""


@dataclass
class InformeDeBaja:
    oferta: Oferta
    alcance: str
    con_descuento: int
    carritos: int
    consecuencia: str = (
        "Los precios de los productos en alcance vuelven a su valor sin descuento de inmediato, "
        "y los carritos que los tienen se actualizan."
    )


def _con_descuento_de(oferta, hoy):
    """Los productos a los que esta oferta les descuenta hoy (la individual puede taparla)."""
    del_dia = OfertasDelDia(hoy)
    productos = productos_del_alcance(oferta.alcance, oferta.producto, oferta.tipo)
    return [
        producto
        for producto in productos
        if (aplicada := del_dia.aplicada(producto)) is not None and aplicada.pk == oferta.pk
    ]


def _verificar_baja(oferta, hoy):
    estado = oferta.estado_en(hoy)
    if estado == Oferta.VENCIDA:
        raise OfertaVencida(
            "La oferta ya venció y los precios originales ya se restauraron automáticamente."
        )
    if estado == Oferta.DADA_DE_BAJA:
        raise OfertaRechazada("La oferta ya está dada de baja.")


def solicitar_baja(oferta, *, hoy=None):
    """`CO-057`: el impacto de la baja. No cambia nada."""
    hoy = hoy or hoy_local()
    _verificar_baja(oferta, hoy)
    return InformeDeBaja(
        oferta=oferta,
        alcance=describir_alcance(oferta.alcance, oferta.producto, oferta.tipo),
        con_descuento=len(_con_descuento_de(oferta, hoy)),
        carritos=_carritos_con(_tocados_por(oferta)),
    )


@dataclass
class ResumenDeBaja:
    oferta: Oferta
    productos: int
    carritos: int


def confirmar_baja(oferta, *, actor, ip=None, hoy=None):
    """`CO-058`: Dada de baja, terminal. Los precios vuelven y los carritos también."""
    hoy = hoy or hoy_local()
    with transaction.atomic():
        oferta = Oferta.objects.select_for_update().get(pk=oferta.pk)
        _verificar_baja(oferta, hoy)
        con_descuento = _con_descuento_de(oferta, hoy)
        tocados = _tocados_por(oferta)
        carritos = _carritos_con(tocados)
        oferta.estado = Oferta.DADA_DE_BAJA
        oferta.save(update_fields=["estado", "actualizada_en"])
        _actualizar_carritos(tocados)
        RegistroAuditoria.registrar(
            accion=RegistroAuditoria.BAJA_OFERTA,
            actor=actor,
            objetivo=oferta,
            ip=ip,
            detalle=(
                f"{describir(oferta, hoy)}; {len(con_descuento)} productos con precio "
                f"restaurado; {carritos} carritos actualizados"
            ),
        )
    return ResumenDeBaja(oferta, len(con_descuento), carritos)


# ---------------------------------------------------------------------------
# Temporizador — CO-059
# ---------------------------------------------------------------------------


@dataclass
class ResultadoDelCiclo:
    activadas: list = field(default_factory=list)
    vencidas: list = field(default_factory=list)


def ejecutar_ciclo(*, hoy=None):
    """`CO-059`: activa las Programadas que llegaron y vence las que pasaron.

    El precio visible ya descontaba o había dejado de descontar por las fechas;
    esto deja el estado guardado al día, los carritos con su precio y, por
    cada vencimiento, la entrada «Vencimiento automático de oferta».
    """
    hoy = hoy or hoy_local()
    resultado = ResultadoDelCiclo()
    with transaction.atomic():
        a_activar = Oferta.objects.select_for_update().filter(
            estado=Oferta.PROGRAMADA, fecha_inicio__lte=hoy, fecha_vencimiento__gte=hoy
        )
        for oferta in a_activar:
            oferta.estado = Oferta.ACTIVA
            oferta.save(update_fields=["estado", "actualizada_en"])
            _actualizar_carritos(_tocados_por(oferta))
            resultado.activadas.append(oferta)

        a_vencer = Oferta.objects.select_for_update().filter(
            estado__in=(Oferta.PROGRAMADA, Oferta.ACTIVA), fecha_vencimiento__lt=hoy
        )
        for oferta in a_vencer:
            oferta.estado = Oferta.VENCIDA
            oferta.save(update_fields=["estado", "actualizada_en"])
            _actualizar_carritos(_tocados_por(oferta))
            RegistroAuditoria.registrar(
                accion=RegistroAuditoria.VENCIMIENTO_AUTOMATICO_OFERTA,
                actor_email=TEMPORIZADOR,
                objetivo=oferta,
                detalle=describir(oferta, hoy),
            )
            resultado.vencidas.append(oferta)
    return resultado


# ---------------------------------------------------------------------------
# Consultas — CO-169 y CO-170
# ---------------------------------------------------------------------------


def filtro_de_estado(estado, hoy):
    """El estado de la lista es el de las fechas, aunque el Temporizador no haya corrido."""
    if estado == Oferta.DADA_DE_BAJA:
        return Q(estado=Oferta.DADA_DE_BAJA)
    vivas = ~Q(estado=Oferta.DADA_DE_BAJA)
    if estado == Oferta.VENCIDA:
        return vivas & Q(fecha_vencimiento__lt=hoy)
    if estado == Oferta.ACTIVA:
        return vivas & Q(fecha_inicio__lte=hoy, fecha_vencimiento__gte=hoy)
    if estado == Oferta.PROGRAMADA:
        return vivas & Q(fecha_inicio__gt=hoy)
    return Q()


@dataclass
class ProductoDeLaOferta:
    producto: Producto
    precio_original: Decimal
    precio_con_descuento: Decimal
    tapado_por: Oferta | None = None


def productos_afectados(oferta, *, hoy=None):
    """`CO-170`: cada producto del alcance con su precio original y con descuento.

    En una oferta por tipo, un producto con su propia oferta individual vigente
    queda «tapado»: se cobra con la individual (ambigüedad 3).
    """
    del_dia = OfertasDelDia(hoy)
    filas = []
    for producto in productos_del_alcance(oferta.alcance, oferta.producto, oferta.tipo).order_by(
        "titulo", "pk"
    ):
        aplicada = del_dia.aplicada(producto)
        tapado = aplicada if aplicada is not None and aplicada.pk != oferta.pk else None
        filas.append(
            ProductoDeLaOferta(
                producto=producto,
                precio_original=producto.precio,
                precio_con_descuento=descontar(producto.precio, oferta),
                tapado_por=tapado if tapado and tapado.alcance == Oferta.PRODUCTO else None,
            )
        )
    return filas
