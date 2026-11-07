"""Lo que muestran los gráficos del panel del Administrador (B-00-032).

Sólo lee, y sólo de datos que el sistema ya tiene: los pedidos, sus líneas y el
catálogo. La plata es la que se cobró en dinero —lo cubierto con puntos no suma,
como en la caja— y un pedido cancelado no cuenta.

La geometría de los gráficos (alto de cada barra, en porcentaje del máximo) se
calcula acá y no en la plantilla, para que la plantilla sólo dibuje.
"""

from collections import defaultdict
from dataclasses import dataclass
from datetime import timedelta
from decimal import Decimal

from django.db.models import Count, Sum
from django.utils import timezone

from apps.catalog.models import Producto
from apps.pedidos.models import LineaPedido, Pedido

DIAS = 30
TOP = 5


@dataclass
class Dia:
    fecha: object
    total: Decimal
    pedidos: int
    alto: float = 0  # por ciento del día que más vendió

    @property
    def es_hoy(self):
        return self.fecha == timezone.localdate()


def _vendido(pedidos):
    """La plata cobrada de unos pedidos: lo que no cubrieron los puntos, más el envío."""
    return sum((p.subtotal + p.costo_envio for p in pedidos), Decimal("0"))


def _pedidos_entre(desde, hasta):
    return (
        Pedido.objects.filter(fecha__date__gte=desde, fecha__date__lte=hasta)
        .exclude(estado=Pedido.CANCELADO)
        .prefetch_related("lineas")
    )


def ventas_por_dia(hoy=None, dias=DIAS):
    hoy = hoy or timezone.localdate()
    desde = hoy - timedelta(days=dias - 1)
    por_dia = defaultdict(list)
    for pedido in _pedidos_entre(desde, hoy):
        por_dia[timezone.localtime(pedido.fecha).date()].append(pedido)
    serie = [
        Dia(
            fecha=desde + timedelta(days=i),
            total=_vendido(por_dia[desde + timedelta(days=i)]),
            pedidos=len(por_dia[desde + timedelta(days=i)]),
        )
        for i in range(dias)
    ]
    maximo = max((d.total for d in serie), default=Decimal("0"))
    for dia in serie:
        dia.alto = float(dia.total / maximo * 100) if maximo else 0
    return serie


def mes(hoy=None):
    """Lo vendido en el mes hasta hoy, contra el mismo tramo del mes anterior."""
    hoy = hoy or timezone.localdate()
    inicio = hoy.replace(day=1)
    anterior_fin = inicio - timedelta(days=1)
    anterior_inicio = anterior_fin.replace(day=1)
    # El mismo tramo: del 1 al mismo día (o al último, si el mes anterior es más corto).
    anterior_hasta = anterior_inicio.replace(day=min(hoy.day, anterior_fin.day))
    actuales = list(_pedidos_entre(inicio, hoy))
    anteriores = list(_pedidos_entre(anterior_inicio, anterior_hasta))
    total, previo = _vendido(actuales), _vendido(anteriores)
    variacion = None
    if previo:
        variacion = round(float((total - previo) / previo * 100))
    return {
        "total": total,
        "pedidos": len(actuales),
        "ticket": (total / len(actuales)) if actuales else Decimal("0"),
        "variacion": variacion,
    }


def mas_vendidos(hoy=None, dias=DIAS, cuantos=TOP):
    hoy = hoy or timezone.localdate()
    desde = hoy - timedelta(days=dias - 1)
    filas = list(
        LineaPedido.objects.filter(pedido__fecha__date__gte=desde)
        .exclude(pedido__estado=Pedido.CANCELADO)
        .exclude(estado=LineaPedido.CANCELADO_REEMBOLSO)
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
    """El catálogo por estado, con el ancho de cada tramo para una barra apilada."""
    cuentas = dict(
        Producto.objects.exclude(estado=Producto.DESCATALOGADO)
        .values_list("estado")
        .annotate(n=Count("pk"))
        .values_list("estado", "n")
    )
    tramos = [
        ("Con stock", cuentas.get(Producto.ACTIVO, 0), "ok"),
        ("En pre-venta", cuentas.get(Producto.PRE_VENTA, 0), "dato"),
        ("Agotados", cuentas.get(Producto.AGOTADO, 0), "senal"),
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
    """Lo vendido en los últimos días, partido entre la tienda online y el mostrador."""
    hoy = hoy or timezone.localdate()
    pedidos = list(_pedidos_entre(hoy - timedelta(days=dias - 1), hoy))
    tramos = [
        ("Tienda online", _vendido(p for p in pedidos if p.canal == Pedido.ONLINE), "dato"),
        ("Mostrador", _vendido(p for p in pedidos if p.canal == Pedido.PRESENCIAL), "senal"),
    ]
    total = sum((n for _, n, _ in tramos), Decimal("0"))
    return {
        "total": total,
        "tramos": [
            {
                "nombre": nombre,
                "cantidad": n,
                "tono": tono,
                "ancho": float(n / total * 100) if total else 0,
            }
            for nombre, n, tono in tramos
        ],
    }


def armar(hoy=None):
    serie = ventas_por_dia(hoy)
    return {
        "serie": serie,
        "vendido_30": sum((d.total for d in serie), Decimal("0")),
        "con_ventas": any(d.total for d in serie),
        "mes": mes(hoy),
        "mas_vendidos": mas_vendidos(hoy),
        "catalogo": catalogo(),
        "canales": canales(hoy),
    }
