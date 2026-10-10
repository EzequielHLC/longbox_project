"""Control de acceso y frontera de la compra, siempre por la dirección real.

El personal no compra con su cuenta de trabajo (plan 07, segunda parte, amb. 3);
el resultado de un cobro lo ve sólo quien lo inició; y el aviso de la pasarela
se autentica por su firma, no por quién lo manda.
"""

import pytest
from django.test import Client
from django.urls import reverse

from apps.pedidos.models import Pedido
from apps.tienda.models import CobroEnCurso
from apps.tienda.pasarelas import PasarelaDePrueba
from apps.tienda.tests.compra_util import (
    URL_AVISO_PRUEBA,
    URL_CHECKOUT,
    URL_CONFIRMAR,
    URL_INVITADO,
    URL_PAGAR,
    agregar,
    avisar,
    cliente_con_direccion,
    confirmar,
    fijar_parametros,
    producto,
)

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def parametros(db):
    return fijar_parametros()


@pytest.mark.parametrize("rol", ["cajero", "administrador"])
@pytest.mark.parametrize(
    ("metodo", "url"),
    [
        ("post", URL_PAGAR),
        ("get", URL_CHECKOUT),
        ("post", URL_CONFIRMAR),
        ("get", URL_INVITADO),
        ("post", reverse("compra:canje_listo")),
    ],
)
def test_acceso_el_personal_recibe_403_en_la_compra(client, request, rol, metodo, url):
    client.force_login(request.getfixturevalue(rol))

    respuesta = getattr(client, metodo)(url)

    assert respuesta.status_code == 403


def test_acceso_el_checkout_pide_iniciar_sesion_al_invitado(client):
    respuesta = client.get(URL_CHECKOUT)

    assert respuesta.url.startswith(reverse("accounts:login"))


def test_acceso_el_resultado_de_otro_cliente_responde_404(client):
    duenio = cliente_con_direccion()
    client.force_login(duenio)
    agregar(client, producto())
    _, cobro = confirmar(client)
    otro = Client()
    otro.force_login(cliente_con_direccion())

    assert otro.get(reverse("compra:resultado", args=[cobro.referencia])).status_code == 404
    assert Client().get(reverse("compra:resultado", args=[cobro.referencia])).status_code == 404


def test_frontera_un_aviso_con_firma_invalida_se_rechaza_sin_efecto(client):
    client.force_login(cliente_con_direccion())
    agregar(client, producto())
    _, cobro = confirmar(client)
    cuerpo, _ = PasarelaDePrueba().armar_aviso(cobro, aprobado=True)

    respuesta = Client().post(
        URL_AVISO_PRUEBA,
        data=cuerpo,
        content_type="application/json",
        HTTP_X_FIRMA_PASARELA="0" * 64,
    )

    cobro.refresh_from_db()
    assert respuesta.status_code == 400
    assert cobro.estado == CobroEnCurso.PENDIENTE
    assert not Pedido.objects.exists()


def test_frontera_un_aviso_sin_firma_se_rechaza(client):
    respuesta = client.post(URL_AVISO_PRUEBA, data=b"{}", content_type="application/json")

    assert respuesta.status_code == 400


def test_frontera_un_aviso_firmado_ilegible_se_rechaza(client):
    cuerpo = b"no es json"
    firma = PasarelaDePrueba().firmar(cuerpo)

    respuesta = client.post(
        URL_AVISO_PRUEBA, data=cuerpo, content_type="application/json", HTTP_X_FIRMA_PASARELA=firma
    )

    assert respuesta.status_code == 400


def test_frontera_un_aviso_de_una_referencia_desconocida_responde_404(client):
    cobro = CobroEnCurso(referencia="f" * 32, monto=1)

    respuesta = avisar(client, cobro)

    assert respuesta.status_code == 404


def test_frontera_una_pasarela_inexistente_responde_400(client):
    respuesta = client.post(
        reverse("compra:aviso", args=["otra"]), data=b"{}", content_type="application/json"
    )

    assert respuesta.status_code == 400


def test_frontera_el_aviso_no_pide_csrf(client):
    """Viene de servidor a servidor: con CSRF exigido, ninguna pasarela podría avisar."""
    navegador = Client(enforce_csrf_checks=True)
    client.force_login(cliente_con_direccion())
    agregar(client, producto())
    _, cobro = confirmar(client)

    respuesta = avisar(navegador, cobro)

    assert respuesta.status_code == 200
    assert Pedido.objects.count() == 1


def test_frontera_la_pasarela_de_prueba_no_procesa_dos_veces(client):
    client.force_login(cliente_con_direccion())
    agregar(client, producto())
    _, cobro = confirmar(client)
    url = reverse("compra:pasarela_prueba", args=[cobro.referencia])

    client.post(url, {"resultado": "aprobar"})
    respuesta = client.post(url, {"resultado": "aprobar"})

    assert respuesta.url == reverse("compra:resultado", args=[cobro.referencia])
    assert Pedido.objects.count() == 1
    assert "ya se resolvió" in client.get(url).content.decode()


def test_frontera_la_pasarela_de_prueba_rechaza_con_un_motivo_conocido(client):
    client.force_login(cliente_con_direccion())
    agregar(client, producto())
    _, cobro = confirmar(client)

    client.post(
        reverse("compra:pasarela_prueba", args=[cobro.referencia]),
        {"resultado": "rechazar", "motivo": "<script>inventado</script>"},
    )

    cobro.refresh_from_db()
    assert cobro.estado == CobroEnCurso.RECHAZADO
    assert cobro.mensaje == "Fondos insuficientes."


def test_frontera_un_cobro_pendiente_muestra_la_espera(client):
    client.force_login(cliente_con_direccion())
    agregar(client, producto())
    _, cobro = confirmar(client)

    contenido = client.get(reverse("compra:resultado", args=[cobro.referencia])).content.decode()

    assert "Esperando la confirmación del pago" in contenido
    assert 'http-equiv="refresh"' in contenido
