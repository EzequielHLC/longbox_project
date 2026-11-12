"""Inferencias para decidir, en el panel del Administrador.

Una función fuera del documento de análisis, a pedido del responsable
(2026-11-12): no tiene caso de uso ni contrato, sólo lee y no cambia nada. Cada
inferencia sale de lo vendido —neto, con la misma regla que `core.tablero`— y
se calla cuando no hay base para afirmarla: un pronóstico con tres días de
historia es peor que ninguno.

- **Proyección del mes**: cuánto se cierra el mes a este ritmo, con una banda.
- **Reposición sugerida**: qué se agota pronto y cuánto pedir.
- **Stock inmovilizado**: lo que no se vende hace tiempo y cuánta plata hay parada.
- **Tendencias**: qué tipos, editoriales y etiquetas suben o bajan, y qué día
  de la semana se vende más.
"""

import math
import statistics
from dataclasses import dataclass, field
from datetime import timedelta
from decimal import ROUND_HALF_UP, Decimal

from django.db.models import DecimalField, ExpressionWrapper, F, Max, Min, Q, Sum
from django.db.models.functions import Coalesce
from django.utils import timezone

from apps.catalog.models import Producto
from apps.core.tablero import (
    BASE_PARA_COMPARAR,
    CERO,
    IMPORTE,
    Tramo,
    comparar,
    lineas_vendidas,
    por_dia,
)
from apps.pedidos.models import Pedido
from apps.suppliers.models import LineaPedidoProveedor, PedidoProveedor

# La proyección pide al menos dos semanas de ventas y mira las últimas cuatro,
# día de la semana por día de la semana: un sábado se parece a otro sábado.
HISTORIA_MINIMA = 14
SEMANAS_DE_RITMO = 4
# La banda cubre ~80 % de los meses con ese ritmo, si los días fueran independientes.
Z_BANDA = 1.28

VENTANA_VELOCIDAD = 30  # días para medir a qué ritmo sale cada producto
HORIZONTE = 21  # lo que se agota antes de esto se sugiere reponer
COBERTURA = 30  # días de venta que deja cubiertos el pedido sugerido
URGENTE = 7  # se agota en menos de una semana

DIAS_INMOVIL = 60
TENDENCIA_DIAS = 30
UNIDADES_MINIMAS = 3  # para hablar de una tendencia
CUANTOS = 6

ESPACIO_DURO = "\u00a0"  # el espacio que no corta renglón
NOMBRE_DEL_DIA = ("Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo")


def _pesos(valor):
    return Decimal(valor).quantize(Decimal("1"), rounding=ROUND_HALF_UP)


def _primera_venta():
    primera = Pedido.objects.exclude(estado=Pedido.CANCELADO).aggregate(primera=Min("fecha"))[
        "primera"
    ]
    return timezone.localtime(primera).date() if primera else None


# ---------------------------------------------------------------------------
# Proyección del mes
# ---------------------------------------------------------------------------


def proyeccion(hoy=None):
    """El cierre del mes a este ritmo, o `None` si todavía no hay historia para estimarlo.

    El ritmo es el promedio de cada día de la semana en las últimas cuatro
    semanas cerradas (hasta ayer). Lo que falta del mes se estima día por día con
    ese promedio; hoy cuenta lo que ya se vendió o lo esperado, lo que sea mayor.
    """
    hoy = hoy or timezone.localdate()
    primera = _primera_venta()
    if primera is None or (hoy - primera).days < HISTORIA_MINIMA:
        return None
    ayer = hoy - timedelta(days=1)
    historia = por_dia(ayer - timedelta(days=7 * SEMANAS_DE_RITMO - 1), ayer)
    por_dia_semana = {}
    for dia in historia:
        por_dia_semana.setdefault(dia.fecha.weekday(), []).append(dia.total)
    ritmo = {d: sum(v, Decimal("0")) / len(v) for d, v in por_dia_semana.items()}

    inicio = hoy.replace(day=1)
    fin = (inicio + timedelta(days=32)).replace(day=1) - timedelta(days=1)
    del_mes = por_dia(inicio, hoy)
    hasta_ayer = Tramo.de(del_mes[:-1]).total
    de_hoy = del_mes[-1].total
    restantes = [hoy + timedelta(days=i) for i in range(1, (fin - hoy).days + 1)]
    esperado = max(de_hoy, ritmo[hoy.weekday()]) + sum(
        (ritmo[d.weekday()] for d in restantes), Decimal("0")
    )
    proyectado = hasta_ayer + esperado
    desvio = statistics.pstdev([float(d.total) for d in historia])
    banda = Decimal(Z_BANDA * desvio * math.sqrt(len(restantes) + 1))
    vendido = hasta_ayer + de_hoy
    piso, techo = max(vendido, proyectado - banda), proyectado + banda

    anterior_fin = inicio - timedelta(days=1)
    anterior = Tramo.de(por_dia(anterior_fin.replace(day=1), anterior_fin))
    escala = max(techo, anterior.total, Decimal("1"))
    return {
        "vendido": _pesos(vendido),
        "proyectado": _pesos(proyectado),
        "piso": _pesos(piso),
        "techo": _pesos(techo),
        "anterior": _pesos(anterior.total),
        "mes_anterior": anterior_fin,
        "dias_restantes": len(restantes),
        **comparar(proyectado, anterior.total, anterior.pedidos),
        # La geometría del medidor, en por ciento de la escala.
        "ancho_vendido": float(vendido / escala * 100),
        "ancho_proyectado": float(proyectado / escala * 100),
        "desde_banda": float(piso / escala * 100),
        "ancho_banda": float((techo - piso) / escala * 100),
        "marca_anterior": float(anterior.total / escala * 100) if anterior.pedidos else None,
    }


# ---------------------------------------------------------------------------
# Reposición sugerida
# ---------------------------------------------------------------------------


@dataclass
class Reposicion:
    producto: Producto
    stock: int
    vendidas: int
    en_camino: int
    dias: int
    sugerido: int

    @property
    def urgente(self):
        return self.dias < URGENTE

    @property
    def por_dia(self):
        return self.vendidas / VENTANA_VELOCIDAD


def _en_camino(productos):
    """Las unidades que todavía pueden llegar de pedidos a proveedor que salieron."""
    camino = {}
    for linea in LineaPedidoProveedor.objects.filter(
        producto_id__in=productos,
        estado__in=LineaPedidoProveedor.ABIERTAS,
        pedido__estado=PedidoProveedor.ABIERTO,
    ):
        camino[linea.producto_id] = camino.get(linea.producto_id, 0) + linea.pendiente
    return camino


def reposicion(hoy=None, cuantos=CUANTOS * 2):
    """Lo que, al ritmo de los últimos 30 días, se agota antes de tres semanas.

    Sugiere pedir lo que cubre un mes de venta, descontado el stock y lo que ya
    viene en camino; si con eso ya alcanza, no lo lista. Las pre-ventas no
    entran: su stock es lo que viene.
    """
    hoy = hoy or timezone.localdate()
    vendidas = dict(
        lineas_vendidas(hoy - timedelta(days=VENTANA_VELOCIDAD - 1), hoy)
        .filter(producto__estado__in=(Producto.ACTIVO, Producto.AGOTADO))
        .values("producto_id")
        .annotate(unidades=Sum("cantidad"))
        .values_list("producto_id", "unidades")
    )
    if not vendidas:
        return []
    camino = _en_camino(vendidas)
    productos = Producto.objects.filter(pk__in=vendidas).select_related(
        "productoeditorial", "productonoeditorial"
    )
    filas = []
    for producto in productos:
        ritmo = vendidas[producto.pk] / VENTANA_VELOCIDAD
        dias = producto.stock / ritmo
        en_camino = camino.get(producto.pk, 0)
        sugerido = math.ceil(ritmo * COBERTURA) - producto.stock - en_camino
        if dias >= HORIZONTE or sugerido <= 0:
            continue
        filas.append(
            Reposicion(
                producto=producto.especifico,
                stock=producto.stock,
                vendidas=vendidas[producto.pk],
                en_camino=en_camino,
                dias=math.floor(dias),
                sugerido=sugerido,
            )
        )
    filas.sort(key=lambda f: (f.dias, -f.vendidas, f.producto.pk))
    return filas[:cuantos]


# ---------------------------------------------------------------------------
# Stock inmovilizado
# ---------------------------------------------------------------------------


@dataclass
class Inmovilizado:
    total: Decimal = Decimal("0")
    productos: int = 0
    unidades: int = 0
    filas: list = field(default_factory=list)


def inmovilizado(hoy=None, dias=DIAS_INMOVIL, cuantos=CUANTOS):
    """Lo que está a la venta con stock y no se vendió en los últimos `dias`.

    Se mide a precio de venta: es la plata que el local tendría si lo vendiera.
    Un producto dado de alta hace menos de `dias` no cuenta: no tuvo tiempo.
    """
    hoy = hoy or timezone.localdate()
    limite = hoy - timedelta(days=dias - 1)
    recientes = lineas_vendidas(limite, hoy).values("producto_id")
    quietos = (
        Producto.objects.filter(estado=Producto.ACTIVO, stock__gt=0, creado_en__date__lt=limite)
        .exclude(pk__in=recientes)
        .annotate(
            plata=ExpressionWrapper(
                F("stock") * F("precio"), output_field=DecimalField(max_digits=14, decimal_places=2)
            ),
            ultima=Max(
                "lineas_pedido__pedido__fecha",
                filter=~Q(lineas_pedido__pedido__estado=Pedido.CANCELADO),
            ),
        )
    )
    resumen = quietos.aggregate(
        total=Coalesce(Sum("plata"), CERO), unidades=Coalesce(Sum("stock"), 0)
    )
    filas = list(
        quietos.select_related("productoeditorial", "productonoeditorial").order_by("-plata", "pk")[
            :cuantos
        ]
    )
    for fila in filas:
        fila.ultima_venta = timezone.localtime(fila.ultima).date() if fila.ultima else None
    return Inmovilizado(
        total=resumen["total"],
        productos=quietos.count(),
        unidades=resumen["unidades"],
        filas=filas,
    )


# ---------------------------------------------------------------------------
# Tendencias
# ---------------------------------------------------------------------------

DIMENSIONES = (
    ("Tipo", "producto__tipo__nombre"),
    ("Editorial", "producto__productoeditorial__editorial__nombre"),
    ("Etiqueta", "producto__etiquetas__nombre"),
)


@dataclass
class Movimiento:
    dimension: str
    nombre: str
    actual: Decimal
    previo: Decimal
    unidades: int
    variacion: int | None
    ancho: float = 0

    @property
    def diferencia(self):
        return self.actual - self.previo


def _importes(campo, desde, hasta):
    return {
        fila[campo]: (fila["importe"], fila["unidades"])
        for fila in lineas_vendidas(desde, hasta)
        .exclude(**{f"{campo}__isnull": True})
        .values(campo)
        .annotate(importe=Coalesce(Sum(IMPORTE), CERO), unidades=Sum("cantidad"))
    }


def tendencias(hoy=None, dias=TENDENCIA_DIAS, cuantos=CUANTOS // 2 + 1):
    """Los que más suben y más bajan en pesos, contra los `dias` anteriores.

    Una etiqueta cuenta cada línea de sus productos, así que una venta puede
    sumar en varias. Sólo entra lo que movió al menos tres unidades en alguno de
    los dos tramos; el por ciento, sólo si el tramo anterior lo tiene también.
    """
    hoy = hoy or timezone.localdate()
    desde = hoy - timedelta(days=dias - 1)
    antes_hasta = desde - timedelta(days=1)
    antes_desde = antes_hasta - timedelta(days=dias - 1)
    movimientos = []
    for dimension, campo in DIMENSIONES:
        actual = _importes(campo, desde, hoy)
        previo = _importes(campo, antes_desde, antes_hasta)
        for nombre in set(actual) | set(previo):
            importe, unidades = actual.get(nombre, (Decimal("0"), 0))
            antes, unidades_antes = previo.get(nombre, (Decimal("0"), 0))
            if max(unidades, unidades_antes) < UNIDADES_MINIMAS or importe == antes:
                continue
            variacion = None
            if unidades_antes >= UNIDADES_MINIMAS and antes > 0:
                variacion = round(float((importe - antes) / antes * 100))
            movimientos.append(Movimiento(dimension, nombre, importe, antes, unidades, variacion))
    suben = sorted(
        (m for m in movimientos if m.diferencia > 0), key=lambda m: (-m.diferencia, m.nombre)
    )[:cuantos]
    bajan = sorted(
        (m for m in movimientos if m.diferencia < 0), key=lambda m: (m.diferencia, m.nombre)
    )[:cuantos]
    maximo = max((abs(m.diferencia) for m in suben + bajan), default=Decimal("0"))
    for movimiento in suben + bajan:
        movimiento.ancho = float(abs(movimiento.diferencia) / maximo * 100) if maximo else 0
    return {"suben": suben, "bajan": bajan}


def dias_de_la_semana(hoy=None, semanas=8):
    """Lo vendido en promedio cada día de la semana, en las últimas semanas cerradas."""
    hoy = hoy or timezone.localdate()
    ayer = hoy - timedelta(days=1)
    serie = por_dia(ayer - timedelta(days=7 * semanas - 1), ayer)
    if not any(d.pedidos for d in serie):
        return None
    sumas = [Decimal("0")] * 7
    for dia in serie:
        sumas[dia.fecha.weekday()] += dia.total
    promedios = [_pesos(s / semanas) for s in sumas]
    maximo = max(max(promedios), Decimal("1"))
    mejor = promedios.index(max(promedios))
    general = sum(promedios, Decimal("0")) / 7
    return {
        "dias": [
            {
                "nombre": NOMBRE_DEL_DIA[i],
                "corto": NOMBRE_DEL_DIA[i][:3],
                "promedio": promedios[i],
                "alto": float(max(promedios[i], 0) / maximo * 100),
                "mejor": i == mejor,
            }
            for i in range(7)
        ],
        "mejor": NOMBRE_DEL_DIA[mejor],
        "veces": round(float(promedios[mejor] / general), 1) if general > 0 else None,
        "semanas": semanas,
    }


# ---------------------------------------------------------------------------
# Las señales: una frase por inferencia, para leer de un vistazo
# ---------------------------------------------------------------------------


def _plural(dia):
    """«Sábado» → «Sábados»; «Lunes» queda igual."""
    return dia if dia.endswith("s") else f"{dia}s"


def _contar(cuantos, singular, plural):
    return f"{cuantos:,}".replace(",", ".") + " " + (singular if cuantos == 1 else plural)


def _miles(valor):
    return f"${ESPACIO_DURO}{_pesos(valor):,}".replace(",", ".")


def senales(datos):
    """Las inferencias en una frase cada una, de la más urgente a la más tranquila."""
    lista = []
    reponer = datos["reposicion"]
    urgentes = [f for f in reponer if f.urgente]
    if urgentes:
        nombre = urgentes[0].producto.titulo
        resto = f" y {len(urgentes) - 1} más" if len(urgentes) > 1 else ""
        lista.append(
            (
                "atencion",
                f"«{nombre}»{resto} se agota{'n' if resto else ''} en menos de una semana "
                "al ritmo actual.",
            )
        )
    elif reponer:
        cuantos = len(reponer)
        lista.append(
            (
                "inventario",
                f"{_contar(cuantos, 'producto', 'productos')} "
                f"se agota{'n' if cuantos > 1 else ''} antes de tres semanas.",
            )
        )
    proyeccion_ = datos["proyeccion"]
    if proyeccion_:
        frase = f"A este ritmo el mes cierra cerca de {_miles(proyeccion_['proyectado'])}"
        if proyeccion_["variacion"] is not None:
            signo = "más" if proyeccion_["variacion"] >= 0 else "menos"
            frase += f", un {abs(proyeccion_['variacion'])} % {signo} que el mes pasado"
        lista.append(("reportes", frase + "."))
    quieto = datos["inmovilizado"]
    if quieto.productos:
        lista.append(
            (
                "precios",
                f"{_miles(quieto.total)} parados en "
                f"{_contar(quieto.productos, 'producto', 'productos')} sin ventas "
                f"hace {DIAS_INMOVIL} días: candidatos a una oferta.",
            )
        )
    semana = datos["semana"]
    if semana and semana["veces"] and semana["veces"] >= 1.3:
        lista.append(
            (
                "reloj",
                f"Los {_plural(semana['mejor']).lower()} se vende "
                + f"{semana['veces']:.1f}".replace(".", ",")
                + " veces el promedio diario.",
            )
        )
    suben = datos["tendencias"]["suben"]
    if suben:
        primero = suben[0]
        lista.append(
            (
                "etiqueta",
                f"{primero.dimension} «{primero.nombre}» es lo que más crece: "
                f"{_miles(primero.diferencia)} más que los 30 días anteriores.",
            )
        )
    return lista


def armar(hoy=None):
    hoy = hoy or timezone.localdate()
    datos = {
        "proyeccion": proyeccion(hoy),
        "reposicion": reposicion(hoy),
        "inmovilizado": inmovilizado(hoy),
        "tendencias": tendencias(hoy),
        "semana": dias_de_la_semana(hoy),
        "base_para_comparar": BASE_PARA_COMPARAR,
        "dias_inmovil": DIAS_INMOVIL,
    }
    datos["senales"] = senales(datos)
    return datos
