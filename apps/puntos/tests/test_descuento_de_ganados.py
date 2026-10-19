"""Los puntos ganados con una compra que se reembolsa (plan 00, C2; RF-19).

Se prueban en cada reembolso que los descuenta: `CO-098` (cancelar el demorado),
`CO-027` (cancelación en lote) y `CO-154` (vencimiento en el local). `CO-101`
está en las pruebas de devoluciones.
"""

from decimal import Decimal

import pytest

from apps.almacen import servicios as almacen
from apps.almacen.models import ArticuloRetenido
from apps.pedidos import demora, preventa
from apps.pedidos.models import LineaPedido
from apps.pedidos.tests.util import crear_pedido, demorar
from apps.puntos import servicios as puntos
from apps.puntos.models import LotePuntos, MovimientoPuntos
from apps.tienda.tests.compra_util import cliente_con_direccion, dar_puntos, fijar_parametros


@pytest.fixture
def titular(db):
    fijar_parametros()
    return cliente_con_direccion()


def _ganar(usuario, pedido, cantidad):
    return puntos.acreditar(usuario, cantidad, origen=LotePuntos.COMPRA, pedido=pedido)


def _debitos():
    return MovimientoPuntos.objects.filter(
        tipo=MovimientoPuntos.DEBITO, motivo=puntos.MOTIVO_GANADOS
    )


@pytest.mark.django_db
def test_lo_ganado_se_reparte_en_proporcion_a_lo_pagado_hacia_abajo(titular):
    # $ 10.000 + 2 × $ 5.000 pagados en dinero, 199 puntos ganados.
    pedido = crear_pedido(titular, lineas=(("10000", 1), ("5000", 2)))
    _ganar(titular, pedido, 199)
    cara, barata = pedido.lineas.order_by("-precio_unitario")

    assert puntos.ganados_por_unidad(cara) == 99  # 199 × 10.000 / 20.000 = 99,5
    assert puntos.ganados_por_unidad(barata) == 49  # 199 × 5.000 / 20.000 = 49,75


@pytest.mark.django_db
def test_una_unidad_pagada_con_puntos_no_gano_nada(titular):
    pedido = crear_pedido(titular, lineas=(("10000", 1, 1000), ("5000", 1)))
    _ganar(titular, pedido, 50)
    canjeada = pedido.lineas.get(cubierta_con_puntos=True)

    assert puntos.ganados_por_unidad(canjeada) == 0


@pytest.mark.django_db
def test_el_descuento_nunca_deja_el_saldo_negativo_ni_toca_lo_comprometido(titular):
    from apps.tienda.models import CobroEnCurso

    pedido = crear_pedido(titular, lineas=(("10000", 1),))
    _ganar(titular, pedido, 100)
    LotePuntos.objects.filter(usuario=titular).update(disponible=40)  # gastó casi todo
    dar_puntos(titular, 30)
    CobroEnCurso.objects.create(
        referencia="canje",
        pasarela="prueba",
        usuario=titular,
        costo_envio=0,
        monto=Decimal("0"),
        puntos_a_debitar=30,
    )

    descontados = puntos.descontar_ganados(titular, pedido.lineas.get())

    assert descontados == 40  # 70 de saldo, 30 comprometidos en el canje
    assert puntos.saldo(titular) == 30


@pytest.mark.django_db
def test_CO098_cancelar_el_demorado_descuenta_lo_que_gano(titular):
    _, pedido, linea = demorar(titular, precio="10000", otros=(("5000", 1),))
    _ganar(titular, pedido, 150)

    demora.confirmar_opcion(pedido, linea.pk, titular, LineaPedido.CANCELAR)

    debito = _debitos().get()
    assert debito.cantidad == 100  # 150 × 10.000 / 15.000
    assert debito.linea_pedido == linea


@pytest.mark.django_db
def test_CO027_la_cancelacion_en_lote_descuenta_lo_que_gano_cada_reserva(titular, administrador):
    producto, pedido, linea = demorar(titular, precio="10000", otros=())
    _ganar(titular, pedido, 100)

    preventa.cancelar_preventa(producto, administrador)

    assert _debitos().get().cantidad == 100
    # 100 ganados + 1000 del tomo + 150 del envío (el pedido queda vacío) − 100 descontados.
    assert puntos.saldo(titular) == 1150


@pytest.mark.django_db
def test_CO154_el_vencimiento_descuenta_lo_que_gano_la_unidad(titular):
    pedido = crear_pedido(titular, lineas=(("10000", 2),))
    _ganar(titular, pedido, 200)
    linea = pedido.lineas.get()
    almacen.retener_linea(linea, None)
    articulo = ArticuloRetenido.objects.filter(linea_pedido=linea).first()
    from django.utils import timezone

    ArticuloRetenido.objects.filter(pk=articulo.pk).update(fecha_vencimiento=timezone.localdate())

    almacen.ciclo_de_vencimiento()

    assert _debitos().get().cantidad == 100  # una de las dos unidades
