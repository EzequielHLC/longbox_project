"""Las ofertas (módulo 03, plan 03 segunda parte).

`CO-054` registrar, `CO-055` registrar aceptando el tope de $1, `CO-056` editar,
`CO-057` y `CO-058` la baja en dos pasos, `CO-059` el ciclo del Temporizador, y
las consultas `CO-169` y `CO-170`.

**El precio guardado del producto no se toca.** Una oferta cambia el precio
visible (`apps.catalog.precio_visible`). Lo que sí se escribe, en cada operación
que cambia qué descuenta, es el precio vigente de las líneas de carrito de los
productos alcanzados: es la postcondición «las `LineaCarrito` afectadas quedaron
actualizadas» de cada contrato.

**Alcance** (plan 03, tercera parte). Una oferta tiene un solo destino: un
producto, un tipo de material, una editorial, una etiqueta o un grupo de
etiquetas. Cuando a un producto le aplican varias, manda la más específica
(`Oferta.PRECEDENCIA`); las reglas de cuál cobra viven en
`precio_visible.OfertasDelDia`.

**Solapamiento (I-20).** Dos ofertas vivas sobre el mismo destino no pueden
compartir días. Sobre destinos distintos sí, y decide la precedencia. La
validación y el alta van en una transacción con bloqueo sobre el destino, para
que dos administradores no registren a la vez dos ofertas que se pisan.
"""

from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal

from django.db import transaction
from django.db.models import Q

from apps.catalog.models import Editorial, Etiqueta, GrupoEtiqueta, Oferta, Producto, Tipo
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
    editorial: Editorial | None = None
    etiqueta: Etiqueta | None = None
    grupo: GrupoEtiqueta | None = None

    @classmethod
    def de(cls, oferta):
        return cls(
            descripcion=oferta.descripcion,
            fecha_inicio=oferta.fecha_inicio,
            fecha_vencimiento=oferta.fecha_vencimiento,
            tipo_descuento=oferta.tipo_descuento,
            valor=oferta.valor,
            alcance=oferta.alcance,
            **{campo: getattr(oferta, campo) for campo in Oferta.CAMPO_DEL_ALCANCE.values()},
        )

    @property
    def destino(self):
        return getattr(self, Oferta.CAMPO_DEL_ALCANCE[self.alcance])

    def destinos(self):
        """Los cinco campos de destino, con valor sólo el del alcance."""
        return {
            campo: getattr(self, campo) if alcance == self.alcance else None
            for alcance, campo in Oferta.CAMPO_DEL_ALCANCE.items()
        }


# ---------------------------------------------------------------------------
# Alcance
# ---------------------------------------------------------------------------


def _filtro_del_destino(oferta):
    """Los productos del destino, en cualquier estado."""
    destino = oferta.destino
    if oferta.alcance == Oferta.PRODUCTO:
        return Q(pk=destino.pk)
    if oferta.alcance == Oferta.TIPO:
        return Q(tipo=destino)
    if oferta.alcance == Oferta.EDITORIAL:
        return Q(productoeditorial__editorial=destino)
    if oferta.alcance == Oferta.ETIQUETA:
        return Q(etiquetas=destino)
    return Q(etiquetas__grupo=destino, etiquetas__activa=True)


def productos_del_alcance(oferta):
    """Los productos que la oferta descuenta: el elegido, o los de la tienda de su destino.

    Del tipo, la editorial, la etiqueta o el grupo cuentan los que se ofrecen en
    la tienda, Activos y en Pre-venta (plan 03, segunda parte, ambigüedad 5, y
    tercera parte, decisión 6). Del grupo, los que llevan alguna de sus etiquetas
    activas. `oferta` puede ser una `Oferta` o unos `DatosDeOferta`.
    """
    productos = Producto.objects.filter(
        pk__in=Producto.objects.filter(_filtro_del_destino(oferta)).values("pk")
    )
    if oferta.alcance != Oferta.PRODUCTO:
        productos = productos.filter(estado__in=ESTADOS_EN_TIENDA)
    return productos


def productos_tocados(oferta):
    """Los productos cuyo precio visible puede cambiar: los del destino en cualquier estado.

    Es el conjunto que se usa para actualizar carritos: una línea con un
    producto que hoy está Agotado también tiene que quedar con su precio.
    """
    return Producto.objects.filter(
        pk__in=Producto.objects.filter(_filtro_del_destino(oferta)).values("pk")
    )


def describir_alcance(oferta):
    destino = oferta.destino
    if oferta.alcance == Oferta.PRODUCTO:
        return f"Producto: {destino.titulo} ({destino.codigo})"
    if oferta.alcance == Oferta.ETIQUETA:
        return f"Etiqueta: {destino.nombre} ({destino.grupo.nombre})"
    return f"{dict(Oferta.ALCANCES)[oferta.alcance]}: {destino.nombre}"


def describir_descuento(tipo_descuento, valor):
    if tipo_descuento == Oferta.PORCENTAJE:
        texto = f"{Decimal(valor).normalize():f}".replace(".", ",")
        return f"{texto} %"
    return _pesos(valor)


def describir(oferta, hoy=None):
    hoy = hoy or hoy_local()
    return (
        f"«{oferta.descripcion}» · {describir_descuento(oferta.tipo_descuento, oferta.valor)} · "
        f"{describir_alcance(oferta)} · "
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
    """La oferta viva sobre el mismo destino que comparte días con éstas, o `None` (E2)."""
    candidatas = Oferta.objects.vivas(hoy).filter(
        alcance=datos.alcance,
        fecha_inicio__lte=datos.fecha_vencimiento,
        fecha_vencimiento__gte=datos.fecha_inicio,
        **{Oferta.CAMPO_DEL_ALCANCE[datos.alcance]: datos.destino},
    )
    if excluir is not None:
        candidatas = candidatas.exclude(pk=excluir)
    return candidatas.order_by("fecha_inicio", "pk").first()


def bajo_tope(datos):
    """E3: los productos cuyo precio no supera el monto fijo. Quedarían en cero o menos."""
    if datos.tipo_descuento != Oferta.MONTO_FIJO:
        return []
    return list(
        productos_del_alcance(datos).filter(precio__lte=datos.valor).order_by("titulo", "pk")
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


def destino_sin_productos(datos):
    """A1: un tipo, una editorial, una etiqueta o un grupo sin productos en la tienda.

    Es un aviso, no un rechazo: la oferta los alcanzará cuando los haya.
    """
    return datos.alcance != Oferta.PRODUCTO and not productos_del_alcance(datos).exists()


def validar_destino(datos):
    """Una editorial, una etiqueta o un grupo dados de baja no reciben ofertas nuevas.

    Una oferta sobre un destino inactivo no descuenta (plan 03, tercera parte,
    decisión 5): registrarla sería una oferta que nunca se ve. Se valida al dar
    de alta y al cambiar de destino; la que ya estaba se puede seguir editando.
    """
    destino = datos.destino
    if datos.alcance == Oferta.EDITORIAL and not destino.activa:
        raise OfertaRechazada("La editorial está dada de baja.", campo="editorial")
    if datos.alcance == Oferta.ETIQUETA and not (destino.activa and destino.grupo.activo):
        raise OfertaRechazada("La etiqueta o su grupo están dados de baja.", campo="etiqueta")
    if datos.alcance == Oferta.GRUPO and not destino.activo:
        raise OfertaRechazada("El grupo de etiquetas está dado de baja.", campo="grupo")


def _bloquear_destino(datos):
    destino = datos.destino
    type(destino).objects.select_for_update().get(pk=destino.pk)


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
        validar_destino(datos)
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
            **datos.destinos(),
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
            _actualizar_carritos(productos_tocados(oferta))
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
        antes = DatosDeOferta.de(oferta)
        _bloquear_destino(datos)
        if (antes.alcance, antes.destino) != (datos.alcance, datos.destino):
            validar_destino(datos)
        validar(datos, hoy=hoy, excluir=oferta.pk)
        afectados = bajo_tope(datos)
        if afectados and not aceptar_tope:
            raise TopeRequerido(afectados)

        tocados_antes = list(productos_tocados(oferta).values_list("pk", flat=True))
        cambios = _cambios(antes, datos)
        if not cambios:
            return []

        for campo, _ in CAMPOS_EDITABLES:
            setattr(oferta, campo, getattr(datos, campo))
        for campo, destino in datos.destinos().items():
            setattr(oferta, campo, destino)
        oferta.estado = Oferta.ACTIVA if datos.fecha_inicio <= hoy else Oferta.PROGRAMADA
        oferta.save()

        RegistroAuditoria.registrar(
            accion=RegistroAuditoria.MODIFICACION_OFERTA,
            actor=actor,
            objetivo=oferta,
            ip=ip,
            detalle=f"«{oferta.descripcion}»: " + "; ".join(cambios),
        )
        tocados = set(tocados_antes) | set(productos_tocados(oferta).values_list("pk", flat=True))
        _actualizar_carritos(Producto.objects.filter(pk__in=tocados))
    return cambios


def _cambios(antes, despues):
    cambios = []
    for campo, nombre in CAMPOS_EDITABLES:
        anterior, nuevo = getattr(antes, campo), getattr(despues, campo)
        if campo == "alcance":
            anterior = describir_alcance(antes)
            nuevo = describir_alcance(despues)
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
    """Los productos a los que esta oferta les descuenta hoy (una más específica puede taparla)."""
    del_dia = OfertasDelDia(hoy)
    productos = del_dia.anotar(list(productos_del_alcance(oferta)))
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
        alcance=describir_alcance(oferta),
        con_descuento=len(_con_descuento_de(oferta, hoy)),
        carritos=_carritos_con(productos_tocados(oferta)),
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
        tocados = productos_tocados(oferta)
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
            _actualizar_carritos(productos_tocados(oferta))
            resultado.activadas.append(oferta)

        a_vencer = Oferta.objects.select_for_update().filter(
            estado__in=(Oferta.PROGRAMADA, Oferta.ACTIVA), fecha_vencimiento__lt=hoy
        )
        for oferta in a_vencer:
            oferta.estado = Oferta.VENCIDA
            oferta.save(update_fields=["estado", "actualizada_en"])
            _actualizar_carritos(productos_tocados(oferta))
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

    Un producto al que hoy le cobra otra oferta —una más específica o, en el
    mismo nivel, una que empezó antes— queda «tapado»: se cobra con ésa (plan
    03, segunda parte, ambigüedad 3, y tercera parte, decisiones 1 y 3).
    """
    del_dia = OfertasDelDia(hoy)
    productos = del_dia.anotar(list(productos_del_alcance(oferta).order_by("titulo", "pk")))
    filas = []
    for producto in productos:
        aplicada = producto.oferta_aplicada
        filas.append(
            ProductoDeLaOferta(
                producto=producto,
                precio_original=producto.precio,
                precio_con_descuento=descontar(producto.precio, oferta),
                tapado_por=aplicada if aplicada is not None and aplicada.pk != oferta.pk else None,
            )
        )
    return filas
