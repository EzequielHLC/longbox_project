"""`CO-204 generarReporteOperativo`: los cinco reportes de CU-REP-GEN (plan 15).

Cada reporte es una tabla —columnas, filas y una fila de totales— para que la
pantalla y el CSV de `CO-128` salgan del mismo objeto y no puedan diferir. Todo
se agrega en la base: un rango de un año no puede tardar más de 10 segundos
(RNF-02). Sólo lee.

Las decisiones del plan aprobado:

- Una venta es un pedido no Cancelado, por su fecha. Las líneas canceladas con
  reembolso no cuentan, y los reembolsos de devoluciones van en su columna.
- El costo de envío no es venta de mercadería: va en su propia columna.
- Una línea pagada con puntos cuenta como unidad vendida y no suma importe.
- Las solicitudes de reposición son las en espera hoy, creadas en el rango.
"""

from dataclasses import dataclass, field
from decimal import Decimal

from django.db.models import Case, Count, DecimalField, F, Min, Sum, Value, When
from django.db.models.functions import Coalesce, TruncDate

from apps.devoluciones.models import CasoDevolucion
from apps.pedidos.models import LineaPedido, Pedido
from apps.puntos.models import MovimientoPuntos
from apps.restock.models import SuscripcionReposicion

VENTAS_TOTALES = "ventas_totales"
VENTAS_POR_CANAL = "ventas_por_canal"
MAS_VENDIDOS = "mas_vendidos"
MOVIMIENTOS_DE_PUNTOS = "movimientos_de_puntos"
REPOSICION = "reposicion"
TIPOS = [
    (VENTAS_TOTALES, "Ventas totales"),
    (VENTAS_POR_CANAL, "Ventas por canal"),
    (MAS_VENDIDOS, "Productos más vendidos"),
    (MOVIMIENTOS_DE_PUNTOS, "Movimientos de puntos"),
    (REPOSICION, "Solicitudes de reposición activas"),
]
CANALES = {Pedido.PRESENCIAL: "Físico (mostrador)", Pedido.ONLINE: "Online"}

CERO = Value(Decimal("0"), output_field=DecimalField(max_digits=14, decimal_places=2))
IMPORTE = Case(
    When(cubierta_con_puntos=False, then=F("precio_unitario") * F("cantidad")),
    default=CERO,
    output_field=DecimalField(max_digits=14, decimal_places=2),
)


@dataclass
class Reporte:
    tipo: str
    titulo: str
    columnas: list
    filas: list = field(default_factory=list)
    totales: list | None = None

    @property
    def vacio(self):
        return not self.filas

    @property
    def encabezados(self):
        """Cada columna con si es numérica, para alinearla como sus celdas."""
        primera = self.filas[0] if self.filas else [None] * len(self.columnas)
        return [
            (nombre, isinstance(valor, (int, Decimal)) and not isinstance(valor, bool))
            for nombre, valor in zip(self.columnas, primera, strict=True)
        ]


def generar(tipo, desde, hasta, *, canal="", categoria=None, tipo_movimiento=""):
    generador = {
        VENTAS_TOTALES: _ventas_totales,
        VENTAS_POR_CANAL: _ventas_por_canal,
        MAS_VENDIDOS: _mas_vendidos,
        MOVIMIENTOS_DE_PUNTOS: _movimientos_de_puntos,
        REPOSICION: _reposicion,
    }[tipo]
    return generador(
        desde, hasta, canal=canal, categoria=categoria, tipo_movimiento=tipo_movimiento
    )


def _titulo(tipo):
    return dict(TIPOS)[tipo]


def _lineas_vendidas(desde, hasta, canal=""):
    lineas = LineaPedido.objects.filter(
        pedido__fecha__date__gte=desde, pedido__fecha__date__lte=hasta
    ).exclude(pedido__estado=Pedido.CANCELADO)
    lineas = lineas.exclude(estado=LineaPedido.CANCELADO_REEMBOLSO)
    if canal:
        lineas = lineas.filter(pedido__canal=canal)
    return lineas


def _pedidos_vendidos(desde, hasta, canal=""):
    pedidos = Pedido.objects.filter(fecha__date__gte=desde, fecha__date__lte=hasta).exclude(
        estado=Pedido.CANCELADO
    )
    if canal:
        pedidos = pedidos.filter(canal=canal)
    return pedidos


def _ventas_totales(desde, hasta, *, canal="", **_):
    por_dia = {}
    for fila in (
        _lineas_vendidas(desde, hasta, canal)
        .annotate(dia=TruncDate("pedido__fecha"))
        .values("dia")
        .annotate(
            ventas=Count("pedido", distinct=True),
            unidades=Sum("cantidad"),
            importe=Coalesce(Sum(IMPORTE), CERO),
        )
    ):
        por_dia[fila["dia"]] = [fila["ventas"], fila["unidades"], fila["importe"], Decimal("0")]
    for fila in (
        _pedidos_vendidos(desde, hasta, canal)
        .annotate(dia=TruncDate("fecha"))
        .values("dia")
        .annotate(envio=Coalesce(Sum("costo_envio"), CERO))
    ):
        if fila["dia"] in por_dia:
            por_dia[fila["dia"]][3] = fila["envio"]
    reembolsos = {}
    casos = CasoDevolucion.objects.filter(
        estado=CasoDevolucion.RESUELTO,
        resolucion__in=(CasoDevolucion.REEMBOLSO, CasoDevolucion.REEMBOLSO_MEDIO),
        resuelto_en__date__gte=desde,
        resuelto_en__date__lte=hasta,
        monto_reembolsado__gt=0,
    )
    if canal:
        casos = casos.filter(linea__pedido__canal=canal)
    for fila in (
        casos.annotate(dia=TruncDate("resuelto_en"))
        .values("dia")
        .annotate(monto=Coalesce(Sum("monto_reembolsado"), CERO))
    ):
        reembolsos[fila["dia"]] = fila["monto"]

    dias = sorted(set(por_dia) | set(reembolsos))
    filas = [
        [dia, *por_dia.get(dia, [0, 0, Decimal("0"), Decimal("0")]), reembolsos.get(dia, 0)]
        for dia in dias
    ]
    return Reporte(
        tipo=VENTAS_TOTALES,
        titulo=_titulo(VENTAS_TOTALES),
        columnas=["Día", "Ventas", "Unidades", "Importe", "Envío", "Reembolsos"],
        filas=filas,
        totales=_sumar(filas, desde_columna=1) if filas else None,
    )


def _ventas_por_canal(desde, hasta, **_):
    filas = []
    for clave, nombre in CANALES.items():
        lineas = _lineas_vendidas(desde, hasta, clave).aggregate(
            ventas=Count("pedido", distinct=True),
            unidades=Coalesce(Sum("cantidad"), 0),
            importe=Coalesce(Sum(IMPORTE), CERO),
        )
        envio = _pedidos_vendidos(desde, hasta, clave).aggregate(
            envio=Coalesce(Sum("costo_envio"), CERO)
        )["envio"]
        if lineas["ventas"]:
            filas.append([nombre, lineas["ventas"], lineas["unidades"], lineas["importe"], envio])
    return Reporte(
        tipo=VENTAS_POR_CANAL,
        titulo=_titulo(VENTAS_POR_CANAL),
        columnas=["Canal", "Ventas", "Unidades", "Importe", "Envío"],
        filas=filas,
        totales=_sumar(filas, desde_columna=1) if filas else None,
    )


def _mas_vendidos(desde, hasta, *, categoria=None, **_):
    lineas = _lineas_vendidas(desde, hasta)
    if categoria:
        lineas = lineas.filter(producto__tipo=categoria)
    filas = [
        [fila["producto__codigo"], fila["producto__titulo"], fila["unidades"], fila["importe"]]
        for fila in lineas.values("producto__codigo", "producto__titulo")
        .annotate(unidades=Sum("cantidad"), importe=Coalesce(Sum(IMPORTE), CERO))
        .order_by("-unidades", "-importe", "producto__titulo")
    ]
    return Reporte(
        tipo=MAS_VENDIDOS,
        titulo=_titulo(MAS_VENDIDOS),
        columnas=["Código", "Producto", "Unidades", "Importe"],
        filas=filas,
        totales=["", "Total", *_sumar(filas, desde_columna=2)[1:]] if filas else None,
    )


def _movimientos_de_puntos(desde, hasta, *, tipo_movimiento="", **_):
    movimientos = MovimientoPuntos.objects.filter(
        ocurrido_en__date__gte=desde, ocurrido_en__date__lte=hasta
    )
    if tipo_movimiento:
        movimientos = movimientos.filter(tipo=tipo_movimiento)
    nombres = dict(MovimientoPuntos.TIPO_CHOICES)
    filas = [
        [nombres[fila["tipo"]], fila["motivo"] or "—", fila["cantidad_movimientos"], fila["puntos"]]
        for fila in movimientos.values("tipo", "motivo")
        .annotate(cantidad_movimientos=Count("pk"), puntos=Sum("cantidad"))
        .order_by("tipo", "-puntos")
    ]
    acreditados = sum(f[3] for f in filas if f[0] == nombres[MovimientoPuntos.ACREDITACION])
    debitados = sum(f[3] for f in filas if f[0] == nombres[MovimientoPuntos.DEBITO])
    return Reporte(
        tipo=MOVIMIENTOS_DE_PUNTOS,
        titulo=_titulo(MOVIMIENTOS_DE_PUNTOS),
        columnas=["Tipo", "Motivo", "Movimientos", "Puntos"],
        filas=filas,
        totales=(
            [
                "Neto",
                f"{acreditados} acreditados − {debitados} debitados",
                "",
                acreditados - debitados,
            ]
            if filas
            else None
        ),
    )


def _reposicion(desde, hasta, *, categoria=None, **_):
    suscripciones = SuscripcionReposicion.objects.filter(
        estado__in=SuscripcionReposicion.EN_ESPERA,
        creada_en__date__gte=desde,
        creada_en__date__lte=hasta,
    )
    if categoria:
        suscripciones = suscripciones.filter(producto__tipo=categoria)
    filas = [
        [
            fila["producto__codigo"],
            fila["producto__titulo"],
            fila["suscripciones"],
            fila["primera"].date(),
        ]
        for fila in suscripciones.values("producto__codigo", "producto__titulo")
        .annotate(suscripciones=Count("pk"), primera=Min("creada_en"))
        .order_by("-suscripciones", "primera")
    ]
    total = sum(f[2] for f in filas)
    return Reporte(
        tipo=REPOSICION,
        titulo=_titulo(REPOSICION),
        columnas=["Código", "Producto", "Suscripciones en espera", "La más antigua"],
        filas=filas,
        totales=["", "Total", total, ""] if filas else None,
    )


def _sumar(filas, *, desde_columna):
    totales = ["Total"]
    for columna in range(desde_columna, len(filas[0])):
        totales.append(sum(fila[columna] for fila in filas))
    return totales


def describir_filtros(*, canal="", categoria=None, tipo_movimiento=""):
    partes = []
    if canal:
        partes.append(f"canal {CANALES[canal]}")
    if categoria:
        partes.append(f"categoría {categoria}")
    if tipo_movimiento:
        partes.append(f"movimientos {dict(MovimientoPuntos.TIPO_CHOICES)[tipo_movimiento]}")
    return ", ".join(partes) or "sin filtros"
