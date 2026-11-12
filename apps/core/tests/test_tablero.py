"""Los gráficos de ventas del panel del Administrador (B-00-032) y el menú en bloques (B-00-031)."""

from datetime import date, timedelta
from decimal import Decimal

import pytest
from django.urls import reverse
from django.utils import timezone

from apps.catalog.models import Producto
from apps.catalog.tests.factories import ProductoFactory
from apps.core import tablero
from apps.devoluciones.models import CasoDevolucion
from apps.pedidos.models import LineaPedido, Pedido
from apps.pedidos.tests.util import como_venta_de_mostrador, crear_pedido

pytestmark = pytest.mark.django_db


def _en(pedido, dia):
    """Mueve el pedido al mediodía de `dia`, para que la fecha no dependa de la hora."""
    momento = timezone.make_aware(timezone.datetime(dia.year, dia.month, dia.day, 12))
    Pedido.objects.filter(pk=pedido.pk).update(fecha=momento)
    return pedido


def test_cada_dia_suma_lo_cobrado_y_el_envio_y_el_mejor_dia_es_la_columna_entera():
    hoy = date(2026, 10, 28)
    _en(crear_pedido(lineas=(("10000", 2),), costo_envio="1500"), hoy)
    _en(crear_pedido(lineas=(("5000", 1),), costo_envio="0"), hoy - timedelta(days=1))

    serie = tablero.ventas_por_dia(hoy)

    assert len(serie) == 30
    assert serie[0].fecha == hoy - timedelta(days=29)
    assert serie[-1].total == Decimal("21500")
    assert serie[-1].pedidos == 1
    assert serie[-1].alto == 100
    assert serie[-2].alto == pytest.approx(5000 / 21500 * 100)


def test_un_pedido_cancelado_no_suma_ni_en_el_dia_ni_en_el_ranking():
    hoy = date(2026, 10, 28)
    cancelado = _en(crear_pedido(estado=Pedido.CANCELADO, lineas=(("9000", 3),)), hoy)

    assert tablero.ventas_por_dia(hoy)[-1].total == 0
    assert all(
        f["producto"].pk != cancelado.lineas.first().producto_id for f in tablero.mas_vendidos(hoy)
    )
    assert tablero.armar(hoy)["con_ventas"] is False


def test_lo_cubierto_con_puntos_no_es_plata_vendida():
    hoy = date(2026, 10, 28)
    _en(crear_pedido(lineas=(("10000", 1, 500), ("2000", 1)), costo_envio="0"), hoy)

    assert tablero.ventas_por_dia(hoy)[-1].total == Decimal("2000")


def test_el_mes_se_compara_contra_el_mismo_tramo_del_mes_anterior():
    hoy = date(2026, 10, 10)
    _en(crear_pedido(lineas=(("15000", 1),), costo_envio="0"), date(2026, 10, 5))
    for dia in range(1, tablero.BASE_PARA_COMPARAR + 1):
        _en(crear_pedido(lineas=(("2000", 1),), costo_envio="0"), date(2026, 9, dia))
    # Fuera del tramo comparable (después del 10 de septiembre): no cuenta.
    _en(crear_pedido(lineas=(("99000", 1),), costo_envio="0"), date(2026, 9, 20))

    mes = tablero.mes(hoy)

    assert mes["total"] == Decimal("15000")
    assert mes["pedidos"] == 1
    assert mes["ticket"] == Decimal("15000")
    assert mes["anterior"] == Decimal("10000")
    assert mes["diferencia"] == Decimal("5000")
    assert mes["variacion"] == 50


def test_con_poca_base_la_variacion_va_solo_en_pesos():
    hoy = date(2026, 10, 10)
    _en(crear_pedido(lineas=(("15000", 1),), costo_envio="0"), date(2026, 10, 5))
    _en(crear_pedido(lineas=(("5000", 1),), costo_envio="0"), date(2026, 9, 8))

    mes = tablero.mes(hoy)

    # Un pedido no alcanza para un «+200 %»: la diferencia sí se dice, en pesos.
    assert mes["diferencia"] == Decimal("10000")
    assert mes["variacion"] is None


def test_lo_devuelto_por_el_medio_de_pago_se_resta_el_dia_que_se_resolvio(administrador):
    hoy = date(2026, 10, 28)
    pedido = _en(crear_pedido(lineas=(("10000", 1), ("4000", 1)), costo_envio="0"), hoy)
    CasoDevolucion.objects.create(
        linea=pedido.lineas.get(precio_unitario=Decimal("4000")),
        correo="cliente@correo.test",
        motivo=CasoDevolucion.ARREPENTIMIENTO,
        estado=CasoDevolucion.RESUELTO,
        resolucion=CasoDevolucion.REEMBOLSO_MEDIO,
        monto_reembolsado=Decimal("4000"),
        resuelto_en=timezone.make_aware(timezone.datetime(2026, 10, 28, 15)),
        resuelto_por=administrador,
    )

    dia = tablero.ventas_por_dia(hoy)[-1]
    mes = tablero.mes(hoy)

    assert dia.total == Decimal("10000")
    assert dia.reembolsos == Decimal("4000")
    assert mes["total"] == Decimal("10000")
    assert mes["reembolsos"] == Decimal("4000")
    # El ticket mide la compra: no se achica por la devolución ni crece por el envío.
    assert mes["ticket"] == Decimal("14000")


def test_una_linea_cancelada_con_reembolso_no_es_venta():
    hoy = date(2026, 10, 28)
    pedido = _en(crear_pedido(lineas=(("10000", 1), ("3000", 2)), costo_envio="0"), hoy)
    pedido.lineas.filter(precio_unitario=Decimal("3000")).update(
        estado=LineaPedido.CANCELADO_REEMBOLSO
    )

    assert tablero.ventas_por_dia(hoy)[-1].total == Decimal("10000")
    assert [f["unidades"] for f in tablero.mas_vendidos(hoy)] == [1]


def test_el_ticket_no_lleva_el_envio_ni_los_pedidos_pagados_con_puntos():
    hoy = date(2026, 10, 28)
    _en(crear_pedido(lineas=(("10000", 1),), costo_envio="2500"), hoy)
    _en(crear_pedido(lineas=(("8000", 1, 400),), costo_envio="0"), hoy)

    mes = tablero.mes(hoy)

    assert mes["total"] == Decimal("12500")
    assert mes["ticket"] == Decimal("10000")


def test_sin_ventas_el_mes_pasado_no_hay_variacion():
    hoy = date(2026, 10, 10)
    _en(crear_pedido(costo_envio="0"), date(2026, 10, 2))

    assert tablero.mes(hoy)["variacion"] is None


def test_el_tramo_del_mes_anterior_se_corta_en_su_ultimo_dia():
    # El 31 de marzo se compara contra el 1 al 28 de febrero, no revienta.
    for dia in (24, 25, 26, 27, 28):
        _en(crear_pedido(lineas=(("1600", 1),), costo_envio="0"), date(2026, 2, dia))
    _en(crear_pedido(lineas=(("4000", 1),), costo_envio="0"), date(2026, 3, 31))

    assert tablero.mes(date(2026, 3, 31))["variacion"] == -50


def test_lo_mas_vendido_ordena_por_unidades_y_el_primero_es_la_barra_entera():
    hoy = timezone.localdate()
    pedido = crear_pedido(lineas=(("1000", 4), ("1000", 1)))

    filas = tablero.mas_vendidos(hoy)

    assert [f["unidades"] for f in filas] == [4, 1]
    assert filas[0]["ancho"] == 100
    assert filas[1]["ancho"] == 25
    assert filas[0]["producto"].pk == pedido.lineas.order_by("-cantidad").first().producto_id


def test_el_catalogo_se_parte_por_estado_sin_los_descatalogados():
    ProductoFactory.create_batch(3, estado=Producto.ACTIVO, stock=2)
    ProductoFactory(estado=Producto.AGOTADO, stock=0)
    ProductoFactory(estado=Producto.DESCATALOGADO, stock=0)

    catalogo = tablero.catalogo()
    tramos = {t["nombre"]: t for t in catalogo["tramos"]}

    assert catalogo["total"] == 4
    assert tramos["Con stock"]["cantidad"] == 3
    assert tramos["Con stock"]["ancho"] == 75
    assert tramos["Sin stock"]["cantidad"] == 1
    assert tramos["En pre-venta"]["cantidad"] == 0


def test_un_activo_en_cero_se_cuenta_sin_stock():
    ProductoFactory(estado=Producto.ACTIVO, stock=2)
    ProductoFactory(estado=Producto.ACTIVO, stock=0)

    tramos = {t["nombre"]: t["cantidad"] for t in tablero.catalogo()["tramos"]}

    assert tramos == {"Con stock": 1, "En pre-venta": 0, "Sin stock": 1}


def test_los_canales_separan_la_tienda_del_mostrador():
    hoy = timezone.localdate()
    crear_pedido(lineas=(("3000", 1),), costo_envio="0")
    como_venta_de_mostrador(crear_pedido(lineas=(("1000", 1),), costo_envio="0"))

    canales = tablero.canales(hoy)
    tramos = {t["nombre"]: t for t in canales["tramos"]}

    assert canales["total"] == Decimal("4000")
    assert tramos["Tienda online"]["cantidad"] == Decimal("3000")
    assert tramos["Mostrador"]["ancho"] == 25


def test_el_panel_dibuja_los_graficos_con_su_vista_de_tabla(client_admin):
    crear_pedido(lineas=(("10000", 1),))

    html = client_admin.get(reverse("core:panel")).content.decode()

    assert "Vendido este mes" in html
    assert "grafico-dias__columna" in html
    assert "Ver como tabla" in html
    assert "Lo más vendido" in html
    assert "El catálogo hoy" in html


def test_el_panel_sin_ventas_lo_dice_en_vez_de_dibujar_barras_vacias(client_admin):
    html = client_admin.get(reverse("core:panel")).content.decode()

    assert "Todavía no hay ventas en los últimos 30 días." in html
    assert "grafico-dias__columna" not in html


def test_el_menu_separa_los_pedidos_de_clientes_de_los_pedidos_a_proveedores(client_admin):
    html = client_admin.get(reverse("core:panel")).content.decode()

    for rotulo in ("Ventas y clientes", "Compras a proveedores", "Administración"):
        assert rotulo in html
    assert "Pedidos de clientes" in html
    assert "Pedidos a proveedores" in html
    assert "Pedidos por llegar" not in html
