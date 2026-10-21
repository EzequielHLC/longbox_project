"""El mostrador y la caja del plan 00 de interfaz, segunda parte (12 y 13).

El vuelto es una cuenta para mostrar: no cambia nada de la venta. Las ventas de
la jornada son una lectura de lo que va a cerrar `CO-126`.
"""

from decimal import Decimal

import pytest
from django.urls import reverse

from apps.catalog.tests.factories import ProductoFactory
from apps.pedidos.models import Pedido, TransaccionPago
from apps.tienda.tests.compra_util import fijar_parametros

pytestmark = pytest.mark.django_db

URL = reverse("core:mostrador")


@pytest.fixture(autouse=True)
def parametros(db):
    return fijar_parametros()


@pytest.fixture
def caja(client, cajero):
    client.force_login(cajero)
    return client


def _agregar(caja, precio="10000"):
    producto = ProductoFactory(stock=5, precio=Decimal(precio))
    caja.post(reverse("ventas:agregar"), {"producto": producto.pk, "cantidad": 1})
    return producto


def test_la_fila_recien_agregada_destella_una_sola_vez(caja):
    producto = _agregar(caja)

    primera = caja.get(URL)
    segunda = caja.get(URL)

    assert primera.context["ultimo_agregado"] == producto.pk
    assert 'class="fila-destacada"' in primera.content.decode()
    assert 'class="fila-destacada"' not in segunda.content.decode()


def test_con_efectivo_el_vuelto_se_muestra_y_la_venta_no_cambia(caja):
    _agregar(caja, "8500")

    respuesta = caja.post(
        reverse("ventas:confirmar"),
        {"medio": TransaccionPago.EFECTIVO, "recibido": "10.000"},
        follow=True,
    )

    pedido = Pedido.objects.get()
    assert pedido.transaccion.monto == Decimal("8500")
    assert respuesta.context["recien_registrada"]
    assert respuesta.context["vuelto"] == Decimal("1500")
    assert "Venta registrada" in respuesta.content.decode()


def test_venta_registrada_se_dice_una_vez_y_el_comprobante_sigue_solo(caja):
    _agregar(caja)
    caja.post(reverse("ventas:confirmar"), {"medio": TransaccionPago.TARJETA})
    url = reverse("ventas:comprobante", args=[Pedido.objects.get().numero])

    primera = caja.get(url)
    segunda = caja.get(url)

    assert primera.context["recien_registrada"] and primera.context["vuelto"] is None
    assert not segunda.context["recien_registrada"]
    assert "Venta registrada" not in segunda.content.decode()


def test_lo_recibido_que_no_alcanza_no_da_vuelto(caja):
    _agregar(caja, "8500")

    respuesta = caja.post(
        reverse("ventas:confirmar"),
        {"medio": TransaccionPago.EFECTIVO, "recibido": "5000"},
        follow=True,
    )

    assert respuesta.context["vuelto"] is None


def test_las_ventas_de_la_jornada_llevan_a_su_comprobante_y_se_filtran_por_medio(caja):
    _agregar(caja)
    caja.post(reverse("ventas:confirmar"), {"medio": TransaccionPago.EFECTIVO})
    _agregar(caja)
    caja.post(reverse("ventas:confirmar"), {"medio": TransaccionPago.TARJETA})
    efectivo, tarjeta = Pedido.objects.order_by("pk")

    todas = caja.get(reverse("caja:caja"))
    solo_tarjeta = caja.get(reverse("caja:caja"), {"medio": TransaccionPago.TARJETA})

    assert [t.pedido_id for t in todas.context["ventas"]] == [tarjeta.pk, efectivo.pk]
    assert reverse("ventas:comprobante", args=[efectivo.numero]) in todas.content.decode()
    assert [t.pedido_id for t in solo_tarjeta.context["ventas"]] == [tarjeta.pk]


def test_ver_las_ventas_de_la_jornada_no_cierra_nada(caja):
    _agregar(caja)
    caja.post(reverse("ventas:confirmar"), {"medio": TransaccionPago.EFECTIVO})

    caja.get(reverse("caja:caja"))

    assert not TransaccionPago.objects.filter(incluida_en_cierre=True).exists()
