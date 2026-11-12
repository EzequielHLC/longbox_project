"""Lo que muestran los gráficos del panel del Administrador (B-00-032).

Sólo lee, y sólo de datos que el sistema ya tiene: los pedidos, sus líneas, las
devoluciones y el catálogo. **Lo vendido es lo cobrado en dinero, neto**:

- lo cubierto con puntos no suma, como en la caja;
- un pedido cancelado no cuenta, y una línea cancelada con reembolso tampoco;
- lo devuelto por el medio de pago se resta el día que se resolvió, como en el
  reporte de ventas totales (`apps.reportes.servicios`), para que el panel y el
  reporte digan lo mismo;
- el envío suma a lo vendido pero no al ticket promedio: el ticket mide la
  compra, no lo que cobró el correo.

La geometría de los gráficos (alto de cada barra, en porcentaje del máximo) se
calcula acá y no en la plantilla, para que la plantilla sólo dibuje.
"""

from dataclasses import dataclass
from datetime import timedelta
from decimal import Decimal

from django.db.models import Case, Count, DecimalField, F, Q, Sum, Value, When
from django.db.models.functions import Coalesce, TruncDate
from django.utils import timezone

from apps.catalog.models import Producto
from apps.devoluciones.models import CasoDevolucion
from apps.pedidos.models import LineaPedido, Pedido

DIAS = 30
TOP = 5
# Una variación en por ciento contra menos pedidos que éstos no dice nada: con
# uno solo, un pedido grande es un «+300 %». Debajo se muestra sólo en pesos.
BASE_PARA_COMPARAR = 5

CERO = Value(Decimal("0"), output_field=DecimalField(max_digits=14, decimal_places=2))
IMPORTE = Case(
    When(cubierta_con_puntos=False, then=F("precio_unitario") * F("cantidad")),
    default=CERO,
    output_field=DecimalField(max_digits=14, decimal_places=2),
)


# ---------------------------------------------------------------------------
# Lo vendido, neto, por día
# ---------------------------------------------------------------------------


def lineas_vendidas(desde, hasta, canal=""):
    """Las líneas que cuentan como venta: ni de pedidos cancelados ni canceladas con reembolso."""
    lineas = (
        LineaPedido.objects.filter(pedido__fecha__date__gte=desde, pedido__fecha__date__lte=hasta)
        .exclude(pedido__estado=Pedido.CANCELADO)
        .exclude(estado=LineaPedido.CANCELADO_REEMBOLSO)
    )
    return lineas.filter(pedido__canal=canal) if canal else lineas


def _pedidos_vendidos(desde, hasta, canal=""):
    pedidos = Pedido.objects.filter(fecha__date__gte=desde, fecha__date__lte=hasta).exclude(
        estado=Pedido.CANCELADO
    )
    return pedidos.filter(canal=canal) if canal else pedidos


def _reembolsos(desde, hasta, canal=""):
    casos = CasoDevolucion.objects.filter(
        estado=CasoDevolucion.RESUELTO,
        resuelto_en__date__gte=desde,
        resuelto_en__date__lte=hasta,
        monto_reembolsado__gt=0,
    )
    return casos.filter(linea__pedido__canal=canal) if canal else casos


@dataclass
class Dia:
    fecha: object
    importe: Decimal = Decimal("0")  # las líneas cobradas en dinero
    envio: Decimal = Decimal("0")
    reembolsos: Decimal = Decimal("0")
    pedidos: int = 0
    pedidos_con_importe: int = 0
    alto: float = 0  # por ciento del día que más vendió

    @property
    def total(self):
        return self.importe + self.envio - self.reembolsos

    @property
    def es_hoy(self):
        return self.fecha == timezone.localdate()


def por_dia(desde, hasta, canal=""):
    """Un `Dia` por cada fecha del tramo, con días vacíos incluidos. Cuatro consultas."""
    dias = {
        desde + timedelta(days=i): Dia(fecha=desde + timedelta(days=i))
        for i in range((hasta - desde).days + 1)
    }
    for fila in (
        lineas_vendidas(desde, hasta, canal)
        .annotate(dia=TruncDate("pedido__fecha"))
        .values("dia")
        .annotate(
            importe=Coalesce(Sum(IMPORTE), CERO),
            con_importe=Count("pedido", distinct=True, filter=Q(cubierta_con_puntos=False)),
        )
    ):
        dias[fila["dia"]].importe = fila["importe"]
        dias[fila["dia"]].pedidos_con_importe = fila["con_importe"]
    for fila in (
        _pedidos_vendidos(desde, hasta, canal)
        .annotate(dia=TruncDate("fecha"))
        .values("dia")
        .annotate(envio=Coalesce(Sum("costo_envio"), CERO), pedidos=Count("pk"))
    ):
        dias[fila["dia"]].envio = fila["envio"]
        dias[fila["dia"]].pedidos = fila["pedidos"]
    for fila in (
        _reembolsos(desde, hasta, canal)
        .annotate(dia=TruncDate("resuelto_en"))
        .values("dia")
        .annotate(monto=Coalesce(Sum("monto_reembolsado"), CERO))
    ):
        dias[fila["dia"]].reembolsos = fila["monto"]
    return list(dias.values())


@dataclass
class Tramo:
    """La suma de varios días: lo vendido neto y con qué se armó."""

    importe: Decimal = Decimal("0")
    envio: Decimal = Decimal("0")
    reembolsos: Decimal = Decimal("0")
    pedidos: int = 0
    pedidos_con_importe: int = 0

    @classmethod
    def de(cls, dias):
        tramo = cls()
        for dia in dias:
            tramo.importe += dia.importe
            tramo.envio += dia.envio
            tramo.reembolsos += dia.reembolsos
            tramo.pedidos += dia.pedidos
            tramo.pedidos_con_importe += dia.pedidos_con_importe
        return tramo

    @property
    def total(self):
        return self.importe + self.envio - self.reembolsos

    @property
    def ticket(self):
        """Lo que se compra por pedido, sin el envío y sin los pagados del todo con puntos."""
        if not self.pedidos_con_importe:
            return Decimal("0")
        return (self.importe / self.pedidos_con_importe).quantize(Decimal("1"))


def ventas_por_dia(hoy=None, dias=DIAS):
    hoy = hoy or timezone.localdate()
    serie = por_dia(hoy - timedelta(days=dias - 1), hoy)
    maximo = max((max(d.total, 0) for d in serie), default=Decimal("0"))
    for dia in serie:
        dia.alto = float(max(dia.total, 0) / maximo * 100) if maximo else 0
    return serie


def comparar(actual, previo, pedidos_previos):
    """La diferencia en pesos siempre que haya con qué; en por ciento sólo con base suficiente."""
    if not pedidos_previos:
        return {"diferencia": None, "variacion": None}
    variacion = None
    if pedidos_previos >= BASE_PARA_COMPARAR and previo > 0:
        variacion = round(float((actual - previo) / previo * 100))
    return {"diferencia": actual - previo, "variacion": variacion}


def mes(hoy=None):
    """Lo vendido en el mes hasta hoy, contra el mismo tramo del mes anterior."""
    hoy = hoy or timezone.localdate()
    inicio = hoy.replace(day=1)
    anterior_fin = inicio - timedelta(days=1)
    anterior_inicio = anterior_fin.replace(day=1)
    # El mismo tramo: del 1 al mismo día (o al último, si el mes anterior es más corto).
    anterior_hasta = anterior_inicio.replace(day=min(hoy.day, anterior_fin.day))
    actual = Tramo.de(por_dia(inicio, hoy))
    anterior = Tramo.de(por_dia(anterior_inicio, anterior_hasta))
    return {
        "total": actual.total,
        "pedidos": actual.pedidos,
        "ticket": actual.ticket,
        "envio": actual.envio,
        "reembolsos": actual.reembolsos,
        "anterior": anterior.total,
        "pedidos_anteriores": anterior.pedidos,
        **comparar(actual.total, anterior.total, anterior.pedidos),
    }


def mas_vendidos(hoy=None, dias=DIAS, cuantos=TOP):
    hoy = hoy or timezone.localdate()
    filas = list(
        lineas_vendidas(hoy - timedelta(days=dias - 1), hoy)
        .values("producto_id")
        .annotate(unidades=Sum("cantidad"))
        .order_by("-unidades", "producto_id")[:cuantos]
    )
    productos = {
        p.pk: p
        for p in Producto.objects.filter(pk__in=[f["producto_id"] for f in filas]).select_related(
            "productoeditorial", "productonoeditorial"
        )
    }
    maximo = filas[0]["unidades"] if filas else 0
    return [
        {
            "producto": productos[f["producto_id"]].especifico,
            "unidades": f["unidades"],
            "ancho": f["unidades"] / maximo * 100 if maximo else 0,
        }
        for f in filas
        if f["producto_id"] in productos
    ]


def catalogo():
    """El catálogo a la venta, por lo que se puede vender hoy.

    «Con stock» es lo que se puede comprar ya: Activo **y** con unidades. Un
    Activo en cero (por una venta del mostrador que todavía no lo pasó a
    Agotado, o por un ajuste) se cuenta con los agotados, que es lo que es.
    """
    cuentas = Producto.objects.aggregate(
        con_stock=Count("pk", filter=Q(estado=Producto.ACTIVO, stock__gt=0)),
        pre_venta=Count("pk", filter=Q(estado=Producto.PRE_VENTA)),
        sin_stock=Count(
            "pk",
            filter=Q(estado=Producto.AGOTADO) | Q(estado=Producto.ACTIVO, stock=0),
        ),
    )
    tramos = [
        ("Con stock", cuentas["con_stock"], "ok"),
        ("En pre-venta", cuentas["pre_venta"], "dato"),
        ("Sin stock", cuentas["sin_stock"], "senal"),
    ]
    total = sum(n for _, n, _ in tramos)
    return {
        "total": total,
        "tramos": [
            {
                "nombre": nombre,
                "cantidad": n,
                "tono": tono,
                "ancho": n / total * 100 if total else 0,
            }
            for nombre, n, tono in tramos
        ],
    }


def canales(hoy=None, dias=DIAS):
    """Lo vendido neto en los últimos días, partido entre la tienda online y el mostrador."""
    hoy = hoy or timezone.localdate()
    desde = hoy - timedelta(days=dias - 1)
    tramos = [
        ("Tienda online", Tramo.de(por_dia(desde, hoy, Pedido.ONLINE)).total, "dato"),
        ("Mostrador", Tramo.de(por_dia(desde, hoy, Pedido.PRESENCIAL)).total, "senal"),
    ]
    total = sum((max(n, 0) for _, n, _ in tramos), Decimal("0"))
    return {
        "total": total,
        "tramos": [
            {
                "nombre": nombre,
                "cantidad": n,
                "tono": tono,
                "ancho": float(max(n, 0) / total * 100) if total else 0,
            }
            for nombre, n, tono in tramos
        ],
    }


def armar(hoy=None):
    serie = ventas_por_dia(hoy)
    treinta = Tramo.de(serie)
    return {
        "serie": serie,
        "vendido_30": treinta.total,
        "reembolsos_30": treinta.reembolsos,
        "con_ventas": any(d.pedidos or d.reembolsos for d in serie),
        "mes": mes(hoy),
        "mas_vendidos": mas_vendidos(hoy),
        "catalogo": catalogo(),
        "canales": canales(hoy),
    }
