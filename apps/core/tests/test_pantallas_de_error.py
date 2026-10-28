"""Las pantallas de error propias (plan 00 de tope de reservas y errores).

Antes, con `DEBUG` apagado, un error mostraba la página en blanco de Django. Cada
prueba provoca el error por una dirección real y mira que la respuesta sea la
pantalla del sistema, con su código de estado.
"""

import pytest
from django.template.loader import render_to_string
from django.test import Client
from django.urls import path, reverse

from apps.accounts.tests.factories import UsuarioFactory

pytestmark = pytest.mark.django_db

MEME = "img/error.webp"


def vista_que_falla(request):
    raise RuntimeError("Falla provocada por la prueba.")


# La dirección del 500: la de siempre más una vista que revienta.
urlpatterns = [path("falla/", vista_que_falla)]


def test_una_direccion_inexistente_muestra_la_pantalla_404(client):
    respuesta = client.get("/esto-no-existe/")

    assert respuesta.status_code == 404
    contenido = respuesta.content.decode()
    assert "Esta página no existe" in contenido
    assert MEME in contenido
    assert reverse("core:tienda_catalogo") in contenido


def test_el_rol_equivocado_ve_la_pantalla_403_con_el_motivo(client):
    client.force_login(UsuarioFactory(rol="cliente"))

    respuesta = client.get(reverse("core:panel"))

    assert respuesta.status_code == 403
    contenido = respuesta.content.decode()
    assert "No tenés acceso a esta pantalla" in contenido
    assert "Tu rol no tiene acceso a esta sección." in contenido


def test_un_formulario_sin_csrf_valido_ve_que_vencio():
    navegador = Client(enforce_csrf_checks=True)

    respuesta = navegador.post(reverse("accounts:login"), {"username": "a", "password": "b"})

    assert respuesta.status_code == 403
    assert "El formulario venció" in respuesta.content.decode()


def test_un_host_no_permitido_ve_la_pantalla_400(client):
    respuesta = client.get("/", HTTP_HOST="ajeno.example")

    assert respuesta.status_code == 400
    assert "No se pudo entender el pedido" in respuesta.content.decode()


@pytest.mark.urls(__name__)
def test_un_error_del_servidor_muestra_la_pantalla_500():
    navegador = Client(raise_request_exception=False)

    respuesta = navegador.get("/falla/")

    assert respuesta.status_code == 500
    contenido = respuesta.content.decode()
    assert "Algo falló de nuestro lado" in contenido
    assert MEME in contenido


def test_la_pantalla_500_se_dibuja_sin_consultar_la_base(django_assert_num_queries):
    """La del 500 se dibuja cuando algo ya falló: puede ser la base misma."""
    with django_assert_num_queries(0):
        html = render_to_string("500.html")

    assert "Algo falló de nuestro lado" in html
