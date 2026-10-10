"""La barra del envío gratis (B-07-037): el cálculo y dónde se dibuja."""

from decimal import Decimal

import pytest
from django.core import mail
from django.urls import reverse

from apps.pedidos.models import Pedido
from apps.tienda.envio import EstadoDeEnvio, estado_de_envio
from apps.tienda.tests.compra_util import (
    agregar,
    avisar,
    cliente_con_direccion,
    confirmar,
    fijar_parametros,
    producto,
)


@pytest.mark.parametrize(
    ("subtotal", "porcentaje", "falta"),
    [
        ("0", 0, "50000"),
        ("12500", 25, "37500"),
        ("49999.99", 99, "0.01"),
        ("50000", 100, "0"),
        ("90000", 100, "0"),
    ],
)
def test_la_barra_avanza_con_el_subtotal_sobre_el_minimo(subtotal, porcentaje, falta):
    envio = EstadoDeEnvio(
        subtotal=Decimal(subtotal), costo=Decimal("1500"), minimo=Decimal("50000")
    )

    assert envio.porcentaje == porcentaje
    assert envio.falta == Decimal(falta)


@pytest.mark.django_db
def test_desde_el_minimo_el_envio_es_gratis():
    fijar_parametros()

    assert estado_de_envio(Decimal("50000")).gratis is True
    assert estado_de_envio(Decimal("49999.99")).costo == Decimal("1500")


@pytest.mark.django_db
def test_el_carrito_muestra_el_envio_la_barra_y_el_total_con_envio(client):
    fijar_parametros()
    agregar(client, producto(precio="12500.50"))

    contenido = client.get(reverse("tienda:carrito")).content.decode()

    assert '<progress class="barra-envio__pista" max="100" value="25"' in contenido
    assert "para el envío gratis" in contenido
    assert "$ 14.000,50" in contenido or "$\xa014.000,50" in contenido


@pytest.mark.django_db
def test_al_alcanzar_el_minimo_dice_que_el_envio_es_gratis(client):
    fijar_parametros()
    agregar(client, producto(precio="60000"))

    contenido = client.get(reverse("tienda:carrito")).content.decode()

    assert "Tenés envío gratis." in contenido
    assert "barra-envio__pista--completa" in contenido


@pytest.mark.django_db
def test_el_checkout_tambien_dibuja_la_barra(client):
    fijar_parametros()
    client.force_login(cliente_con_direccion())
    agregar(client, producto(precio="10000"))

    contenido = client.get(reverse("compra:checkout")).content.decode()

    assert 'value="20"' in contenido


@pytest.mark.django_db
def test_CO089_la_confirmacion_lleva_el_enlace_de_seguimiento(
    client, django_capture_on_commit_callbacks
):
    fijar_parametros()
    client.force_login(cliente_con_direccion())
    agregar(client, producto())
    _, cobro = confirmar(client)

    with django_capture_on_commit_callbacks(execute=True):
        avisar(client, cobro)

    pedido = Pedido.objects.get()
    assert f"http://testserver/cuenta/pedidos/{pedido.numero}/" in mail.outbox[-1].body
