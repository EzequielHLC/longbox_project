"""Las inferencias del panel (`core.inteligencia`).

Fuera del documento formal, a pedido del responsable (2026-11-12): no hay
contrato que citar. Lo que se prueba es que cada inferencia haga la cuenta que
dice, y sobre todo que **se calle cuando no hay base**: un pronóstico inventado
es peor que ninguno.
"""

from datetime import date, timedelta
from decimal import Decimal

import pytest
from django.urls import reverse
from django.utils import timezone

from apps.catalog.models import Producto
from apps.catalog.tests.factories import (
    EditorialFactory,
    ProductoFactory,
    TipoFactory,
)
from apps.core import inteligencia
from apps.pedidos.models import LineaPedido, Pedido
from apps.pedidos.tests.util import crear_pedido
from apps.suppliers.models import LineaPedidoProveedor, PedidoProveedor

pytestmark = pytest.mark.django_db


def _en(pedido, dia):
    momento = timezone.make_aware(timezone.datetime(dia.year, dia.month, dia.day, 12))
    Pedido.objects.filter(pk=pedido.pk).update(fecha=momento)
    return pedido


def _venta(producto, cantidad, dia, precio="1000"):
    """Un pedido de `cantidad` unidades de `producto`, el día `dia`, sin envío."""
    pedido = crear_pedido(lineas=(), costo_envio="0")
    LineaPedido.objects.create(
        pedido=pedido,
        producto=producto,
        cantidad=cantidad,
        precio_unitario=Decimal(precio),
        estado=LineaPedido.DISPONIBLE,
    )
    return _en(pedido, dia)


def _viejo(producto, dias=120):
    Producto.objects.filter(pk=producto.pk).update(creado_en=timezone.now() - timedelta(days=dias))
    return producto


# ===========================================================================
# Proyección del mes
# ===========================================================================


def test_sin_dos_semanas_de_historia_no_proyecta():
    hoy = date(2026, 11, 12)
    _en(crear_pedido(costo_envio="0"), hoy - timedelta(days=5))

    assert inteligencia.proyeccion(hoy) is None


def test_un_ritmo_parejo_proyecta_ese_ritmo_por_los_dias_que_faltan():
    hoy = date(2026, 11, 12)
    # $ 1.000 todos los días desde el 1 de octubre.
    dia = date(2026, 10, 1)
    while dia < hoy:
        _en(crear_pedido(lineas=(("1000", 1),), costo_envio="0"), dia)
        dia += timedelta(days=1)

    p = inteligencia.proyeccion(hoy)

    # Del 1 al 11 de noviembre: 11.000. Hoy y los 18 que faltan, a 1.000.
    assert p["vendido"] == Decimal("11000")
    assert p["proyectado"] == Decimal("30000")
    # Sin variación entre días, la banda es nula.
    assert p["piso"] == p["techo"] == Decimal("30000")
    assert p["anterior"] == Decimal("31000")
    assert p["diferencia"] == Decimal("-1000")
    assert p["variacion"] == -3
    assert p["dias_restantes"] == 18


def test_la_proyeccion_respeta_el_dia_de_la_semana():
    hoy = date(2026, 11, 12)  # jueves
    dia = date(2026, 10, 1)
    while dia < hoy:
        # Sólo se vende los sábados.
        if dia.weekday() == 5:
            _en(crear_pedido(lineas=(("7000", 1),), costo_envio="0"), dia)
        dia += timedelta(days=1)

    p = inteligencia.proyeccion(hoy)

    # Noviembre ya tuvo el 7; faltan los sábados 14, 21 y 28.
    assert p["vendido"] == Decimal("7000")
    assert p["proyectado"] == Decimal("28000")
    assert p["piso"] >= p["vendido"]
    assert p["techo"] > p["proyectado"]


def test_si_hoy_ya_se_vendio_mas_que_lo_esperado_cuenta_lo_vendido():
    hoy = date(2026, 11, 12)
    dia = date(2026, 10, 1)
    while dia < hoy:
        _en(crear_pedido(lineas=(("1000", 1),), costo_envio="0"), dia)
        dia += timedelta(days=1)
    _en(crear_pedido(lineas=(("9000", 1),), costo_envio="0"), hoy)

    p = inteligencia.proyeccion(hoy)

    assert p["vendido"] == Decimal("20000")
    assert p["proyectado"] == Decimal("38000")  # 11.000 + 9.000 de hoy + 18 × 1.000


# ===========================================================================
# Reposición sugerida
# ===========================================================================


def test_sugiere_reponer_lo_que_se_agota_y_cuanto_pedir():
    hoy = timezone.localdate()
    rapido = ProductoFactory(titulo="Rápido", stock=3)
    _venta(rapido, 30, hoy - timedelta(days=2))  # 1 por día: se agota en 3 días
    lento = ProductoFactory(titulo="Lento", stock=50)
    _venta(lento, 3, hoy - timedelta(days=2))

    filas = inteligencia.reposicion(hoy)

    assert [f.producto.titulo for f in filas] == ["Rápido"]
    assert filas[0].dias == 3
    assert filas[0].urgente
    assert filas[0].sugerido == 27  # un mes de venta (30) menos el stock


def test_lo_que_viene_en_camino_se_descuenta_y_si_alcanza_no_se_lista():
    hoy = timezone.localdate()
    poco = ProductoFactory(titulo="Poco en camino", stock=2)
    _venta(poco, 30, hoy)
    bastante = ProductoFactory(titulo="Bastante en camino", stock=2)
    _venta(bastante, 30, hoy)
    pedido = PedidoProveedor.objects.create(origen=PedidoProveedor.LOTE)
    LineaPedidoProveedor.objects.create(pedido=pedido, producto=poco, cantidad_pedida=10)
    LineaPedidoProveedor.objects.create(pedido=pedido, producto=bastante, cantidad_pedida=40)

    filas = inteligencia.reposicion(hoy)

    assert [(f.producto.titulo, f.en_camino, f.sugerido) for f in filas] == [
        ("Poco en camino", 10, 18)
    ]


def test_el_agotado_que_se_vende_va_primero_y_la_pre_venta_no_entra():
    hoy = timezone.localdate()
    agotado = ProductoFactory(titulo="Agotado", stock=0, estado=Producto.AGOTADO)
    _venta(agotado, 6, hoy)
    preventa = ProductoFactory(titulo="Pre-venta", stock=0, estado=Producto.PRE_VENTA)
    _venta(preventa, 9, hoy)
    otro = ProductoFactory(titulo="Otro", stock=4)
    _venta(otro, 10, hoy)

    filas = inteligencia.reposicion(hoy)

    assert [f.producto.titulo for f in filas] == ["Agotado", "Otro"]
    assert filas[0].dias == 0


def test_las_ventas_canceladas_no_son_ritmo():
    hoy = timezone.localdate()
    producto = ProductoFactory(stock=1)
    pedido = _venta(producto, 30, hoy)
    Pedido.objects.filter(pk=pedido.pk).update(estado=Pedido.CANCELADO)

    assert inteligencia.reposicion(hoy) == []


# ===========================================================================
# Stock inmovilizado
# ===========================================================================


def test_suma_la_plata_parada_de_lo_que_no_se_vende():
    hoy = timezone.localdate()
    quieto = _viejo(ProductoFactory(titulo="Quieto", stock=3, precio=Decimal("12000")))
    _venta(quieto, 1, hoy - timedelta(days=90))
    _viejo(ProductoFactory(titulo="Nunca", stock=1, precio=Decimal("5000")))
    vendido = _viejo(ProductoFactory(titulo="Se vende", stock=8))
    _venta(vendido, 1, hoy - timedelta(days=10))
    _viejo(ProductoFactory(titulo="Sin stock", stock=0, estado=Producto.AGOTADO))
    ProductoFactory(titulo="Recién llegado", stock=4)

    q = inteligencia.inmovilizado(hoy)

    assert q.productos == 2
    assert q.unidades == 4
    assert q.total == Decimal("41000")
    assert [p.titulo for p in q.filas] == ["Quieto", "Nunca"]
    assert q.filas[0].ultima_venta == hoy - timedelta(days=90)
    assert q.filas[1].ultima_venta is None


# ===========================================================================
# Tendencias y días de la semana
# ===========================================================================


def test_las_tendencias_comparan_contra_los_30_dias_anteriores():
    hoy = timezone.localdate()
    manga = TipoFactory(nombre="Manga")
    comic = TipoFactory(nombre="Cómic")
    ivrea = EditorialFactory(nombre="Ivrea")
    tomo = ProductoFactory(tipo=manga, editorial=ivrea)
    revista = ProductoFactory(tipo=comic)
    _venta(tomo, 4, hoy - timedelta(days=40), precio="1000")
    _venta(tomo, 6, hoy - timedelta(days=3), precio="1000")
    _venta(revista, 5, hoy - timedelta(days=40), precio="2000")
    _venta(revista, 1, hoy - timedelta(days=3), precio="2000")

    t = inteligencia.tendencias(hoy)
    suben = {(m.dimension, m.nombre): m for m in t["suben"]}
    bajan = {(m.dimension, m.nombre): m for m in t["bajan"]}

    assert suben[("Tipo", "Manga")].diferencia == Decimal("2000")
    assert suben[("Tipo", "Manga")].variacion == 50
    assert suben[("Editorial", "Ivrea")].variacion == 50
    assert bajan[("Tipo", "Cómic")].diferencia == Decimal("-8000")
    assert bajan[("Tipo", "Cómic")].variacion == -80
    assert bajan[("Tipo", "Cómic")].ancho == 100


def test_poco_movimiento_no_es_tendencia_y_lo_nuevo_no_tiene_por_ciento():
    hoy = timezone.localdate()
    novedad = ProductoFactory(tipo=TipoFactory(nombre="Novedad"))
    _venta(novedad, 5, hoy)
    suelto = ProductoFactory(tipo=TipoFactory(nombre="Suelto"))
    _venta(suelto, 2, hoy)

    suben = {m.nombre: m for m in inteligencia.tendencias(hoy)["suben"]}

    assert suben["Novedad"].variacion is None
    assert "Suelto" not in suben


def test_el_mejor_dia_de_la_semana():
    hoy = date(2026, 11, 12)
    for semana in range(8):
        sabado = date(2026, 11, 7) - timedelta(weeks=semana)
        _en(crear_pedido(lineas=(("6000", 1),), costo_envio="0"), sabado)
        _en(crear_pedido(lineas=(("1000", 1),), costo_envio="0"), sabado + timedelta(days=3))

    semana = inteligencia.dias_de_la_semana(hoy)

    assert semana["mejor"] == "Sábado"
    assert semana["dias"][5]["promedio"] == Decimal("6000")
    assert semana["dias"][5]["alto"] == 100
    assert semana["veces"] == 6.0


def test_sin_ventas_no_hay_dia_de_la_semana():
    assert inteligencia.dias_de_la_semana(date(2026, 11, 12)) is None


# ===========================================================================
# Las señales y el panel
# ===========================================================================


def test_las_senales_ponen_primero_lo_urgente():
    hoy = timezone.localdate()
    producto = ProductoFactory(titulo="Berserk 1", stock=1)
    _venta(producto, 30, hoy)
    _viejo(ProductoFactory(titulo="Quieto", stock=2, precio=Decimal("3000")))

    senales = inteligencia.armar(hoy)["senales"]

    assert senales[0][0] == "atencion"
    assert "«Berserk 1» se agota en menos de una semana" in senales[0][1]
    assert any(
        f"${inteligencia.ESPACIO_DURO}6.000 parados en 1 producto sin ventas" in frase
        for _, frase in senales
    )


def test_sin_datos_no_inventa_nada():
    datos = inteligencia.armar(date(2026, 11, 12))

    assert datos["senales"] == []
    assert datos["proyeccion"] is None
    assert datos["reposicion"] == []


def test_el_panel_muestra_la_inteligencia_y_lo_dice_cuando_no_hay_base(client_admin):
    html = client_admin.get(reverse("core:panel")).content.decode()

    assert "Inteligencia del negocio" in html
    assert "Hacen falta al menos dos semanas de ventas para proyectar el mes." in html
    assert "Nada se agota en las próximas tres semanas" in html


def test_el_panel_lista_la_reposicion_con_enlace_a_la_ficha(client_admin):
    producto = ProductoFactory(titulo="Vagabond 3", stock=1)
    _venta(producto, 30, timezone.localdate())

    html = client_admin.get(reverse("core:panel")).content.decode()

    assert reverse("catalog:producto_detalle", args=[producto.pk]) in html
    assert "Reposición sugerida" in html


def test_el_cajero_no_ve_el_panel_ni_sus_cifras(client, cajero):
    client.force_login(cajero)

    respuesta = client.get(reverse("core:panel"))

    assert respuesta.status_code in (302, 403)
    assert b"Inteligencia del negocio" not in respuesta.content
