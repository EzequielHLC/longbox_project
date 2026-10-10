"""Frontera con MercadoPago (B-07-031). La red está cortada: cada respuesta se declara.

Lo que importa probar es que el aviso **no se cree**: el resultado sale de la
consulta del pago a la API, y un aviso que apunta a un pago que la API no
confirma no genera nada.
"""

from decimal import Decimal
from unittest.mock import patch

import pytest
from django.test import RequestFactory, override_settings
from django.urls import reverse

from apps.core import integraciones
from apps.core.models import ConfiguracionSistema
from apps.pedidos.models import Pedido, TransaccionPago
from apps.tienda import mercadopago
from apps.tienda.mercadopago import AvisoSinResultado, MercadoPago, SinCredencial
from apps.tienda.models import CobroEnCurso
from apps.tienda.pasarelas import AvisoInvalido, pasarela
from apps.tienda.tests.compra_util import (
    agregar,
    cliente_con_direccion,
    confirmar,
    fijar_parametros,
    producto,
)

pytestmark = pytest.mark.django_db

URL_AVISO_MP = reverse("compra:aviso", args=["mercadopago"])


def responde(*respuestas):
    """Parchea la puerta HTTP con estas respuestas, en orden."""
    return patch.object(
        integraciones,
        "pedir",
        side_effect=[integraciones.Respuesta(datos=datos) for datos in respuestas],
    )


def pago(cobro, estado="approved", monto=None):
    return {
        "id": 123,
        "status": estado,
        "status_detail": (
            "accredited" if estado == "approved" else "cc_rejected_insufficient_amount"
        ),
        "external_reference": cobro.referencia,
        "transaction_amount": float(monto if monto is not None else cobro.monto),
    }


@pytest.fixture
def navegador(client):
    fijar_parametros(pasarela=ConfiguracionSistema.PASARELA_MERCADOPAGO)
    client.force_login(cliente_con_direccion())
    agregar(client, producto(precio="10000"))
    return client


@override_settings(MERCADOPAGO_ACCESS_TOKEN="TEST-token")
def test_frontera_mp_la_preferencia_lleva_la_referencia_y_redirige_al_init_point(navegador):
    with responde({"id": "pref-1", "init_point": "https://mp.test/pagar"}) as pedir:
        respuesta, cobro = confirmar(navegador)

    assert respuesta.url == "https://mp.test/pagar"
    cuerpo = pedir.call_args.kwargs["cuerpo"]
    assert cuerpo["external_reference"] == cobro.referencia
    assert cuerpo["items"][0]["unit_price"] == float(cobro.monto)
    assert cuerpo["notification_url"].endswith(URL_AVISO_MP)
    assert pedir.call_args.kwargs["cabeceras"]["Authorization"] == "Bearer TEST-token"
    cobro.refresh_from_db()
    assert cobro.id_externo == "pref-1"


@override_settings(MERCADOPAGO_ACCESS_TOKEN="TEST-token")
def test_frontera_mp_sin_respuesta_no_cobra_y_vuelve_al_carrito(navegador):
    with patch.object(integraciones, "pedir", return_value=integraciones.Respuesta(motivo="x")):
        respuesta, cobro = confirmar(navegador)

    assert respuesta.url == reverse("tienda:carrito")
    assert cobro.estado == CobroEnCurso.RECHAZADO


@override_settings(MERCADOPAGO_ACCESS_TOKEN="")
def test_frontera_mp_sin_credencial_no_inicia_el_cobro(navegador):
    respuesta, _ = confirmar(navegador)

    assert respuesta.url == reverse("compra:checkout")
    assert not Pedido.objects.exists()


@override_settings(MERCADOPAGO_ACCESS_TOKEN="TEST-token")
def test_frontera_mp_el_aviso_se_confirma_consultando_el_pago(navegador, client):
    with responde({"id": "pref-1", "init_point": "https://mp.test/pagar"}):
        _, cobro = confirmar(navegador)

    with responde(pago(cobro)) as pedir:
        respuesta = client.post(
            URL_AVISO_MP,
            data={"type": "payment", "data": {"id": "123"}},
            content_type="application/json",
        )

    assert respuesta.status_code == 200
    assert pedir.call_args.args[0].endswith("/v1/payments/123")
    assert TransaccionPago.objects.get().referencia == "mp-123"
    assert Pedido.objects.count() == 1


@override_settings(MERCADOPAGO_ACCESS_TOKEN="TEST-token")
def test_frontera_mp_un_aviso_por_parametros_tambien_se_lee(navegador, client):
    with responde({"id": "pref-1", "init_point": "https://mp.test/pagar"}):
        _, cobro = confirmar(navegador)

    with responde(pago(cobro)):
        client.post(f"{URL_AVISO_MP}?topic=payment&id=123")

    assert Pedido.objects.count() == 1


@override_settings(MERCADOPAGO_ACCESS_TOKEN="TEST-token")
def test_frontera_mp_un_pago_que_la_api_no_confirma_no_genera_nada(navegador, client):
    with responde({"id": "pref-1", "init_point": "https://mp.test/pagar"}):
        _, cobro = confirmar(navegador)

    with patch.object(integraciones, "pedir", return_value=integraciones.Respuesta(motivo="x")):
        respuesta = client.post(
            URL_AVISO_MP,
            data={"type": "payment", "data": {"id": "999"}},
            content_type="application/json",
        )

    cobro.refresh_from_db()
    assert respuesta.status_code == 400
    assert cobro.estado == CobroEnCurso.PENDIENTE
    assert not Pedido.objects.exists()


@override_settings(MERCADOPAGO_ACCESS_TOKEN="TEST-token")
def test_frontera_mp_un_pago_pendiente_o_de_otro_tema_se_acusa_sin_efecto(navegador, client):
    with responde({"id": "pref-1", "init_point": "https://mp.test/pagar"}):
        _, cobro = confirmar(navegador)

    with responde(pago(cobro, estado="in_process")):
        pendiente = client.post(
            URL_AVISO_MP,
            data={"type": "payment", "data": {"id": "1"}},
            content_type="application/json",
        )
    otro_tema = client.post(
        URL_AVISO_MP,
        data={"type": "merchant_order", "data": {"id": "1"}},
        content_type="application/json",
    )

    assert (pendiente.status_code, otro_tema.status_code) == (200, 200)
    cobro.refresh_from_db()
    assert cobro.estado == CobroEnCurso.PENDIENTE


@override_settings(MERCADOPAGO_ACCESS_TOKEN="TEST-token")
def test_frontera_mp_un_pago_rechazado_registra_el_rechazo(navegador, client):
    with responde({"id": "pref-1", "init_point": "https://mp.test/pagar"}):
        _, cobro = confirmar(navegador)

    with responde(pago(cobro, estado="rejected")):
        client.post(
            URL_AVISO_MP,
            data={"type": "payment", "data": {"id": "1"}},
            content_type="application/json",
        )

    cobro.refresh_from_db()
    assert cobro.estado == CobroEnCurso.RECHAZADO
    assert cobro.mensaje == "cc_rejected_insufficient_amount"


@override_settings(MERCADOPAGO_ACCESS_TOKEN="TEST-token")
def test_frontera_mp_E3_pide_el_reembolso_del_pago(navegador, client):
    with responde({"id": "pref-1", "init_point": "https://mp.test/pagar"}):
        _, cobro = confirmar(navegador)

    with responde(pago(cobro, monto=Decimal("1")), {"id": 9, "status": "approved"}) as pedir:
        client.post(
            URL_AVISO_MP,
            data={"type": "payment", "data": {"id": "123"}},
            content_type="application/json",
        )

    reembolso = pedir.call_args_list[-1]
    assert reembolso.args[0].endswith("/v1/payments/123/refunds")
    assert reembolso.kwargs["cabeceras"]["X-Idempotency-Key"] == f"reembolso-{cobro.referencia}"
    cobro.refresh_from_db()
    assert cobro.estado == CobroEnCurso.REEMBOLSADO


def test_frontera_mp_sin_credencial_ninguna_llamada_sale():
    with pytest.raises(SinCredencial):
        MercadoPago(token="")._cabeceras()


def test_frontera_mp_un_aviso_sin_pago_es_invalido():
    with pytest.raises(AvisoInvalido):
        MercadoPago(token="t")._id_del_pago(b'{"type": "payment", "data": {}}', "")


def test_frontera_mp_un_cuerpo_ilegible_sin_parametros_no_es_un_pago():
    with pytest.raises(AvisoSinResultado):
        MercadoPago(token="t")._id_del_pago(b"no es json", "")


def test_frontera_mp_el_reembolso_rechazado_se_informa():
    cobro = CobroEnCurso(referencia="r" * 32)
    with patch.object(integraciones, "pedir", return_value=integraciones.Respuesta(motivo="x")):
        assert MercadoPago(token="t").reembolsar(cobro, "mp-1") is False


@override_settings(ALLOWED_HOSTS=["tienda.test"])
def test_frontera_mp_la_preferencia_usa_direcciones_absolutas():
    peticion = RequestFactory().get("/", HTTP_HOST="tienda.test")
    cobro = CobroEnCurso(referencia="a" * 32, monto=Decimal("100"))
    cobro.save = lambda **kwargs: None
    with responde({"id": "p", "init_point": "https://mp.test/x"}) as pedir:
        MercadoPago(token="t").iniciar_cobro(cobro, peticion)

    cuerpo = pedir.call_args.kwargs["cuerpo"]
    assert cuerpo["back_urls"]["success"].startswith("http://tienda.test/")
    assert cuerpo["notification_url"].startswith("http://tienda.test/")


def test_frontera_una_pasarela_desconocida_no_existe():
    with pytest.raises(AvisoInvalido):
        pasarela("otra")


def test_frontera_mercadopago_se_elige_por_su_clave():
    assert isinstance(pasarela("mercadopago"), mercadopago.MercadoPago)
