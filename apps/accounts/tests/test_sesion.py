"""CU-46, comportamiento adicional: expiración por inactividad y renovación."""

import pytest
from django.urls import reverse

from apps.accounts.views import MENSAJE_SESION_EXPIRADA

URL_LOGIN = reverse("accounts:login")
URL_RENOVAR = reverse("accounts:renovar_sesion")

pytestmark = pytest.mark.django_db


def test_el_login_avisa_cuando_se_llega_por_sesion_expirada(client):
    respuesta = client.get(f"{URL_LOGIN}?expirada=1")

    assert MENSAJE_SESION_EXPIRADA in respuesta.content.decode()


def test_el_login_normal_no_muestra_el_aviso_de_expiracion(client):
    respuesta = client.get(URL_LOGIN)

    assert MENSAJE_SESION_EXPIRADA not in respuesta.content.decode()


def test_renovar_extiende_la_sesion_del_usuario_autenticado(client, cliente, settings):
    client.force_login(cliente)

    respuesta = client.post(URL_RENOVAR)

    assert respuesta.status_code == 200
    assert respuesta.json()["segundos_restantes"] == settings.SESSION_COOKIE_AGE


def test_renovar_sin_sesion_redirige_al_login(client):
    respuesta = client.post(URL_RENOVAR)

    assert respuesta.status_code == 302
    assert respuesta.url.startswith(URL_LOGIN)


def test_renovar_no_acepta_get(client, cliente):
    client.force_login(cliente)

    assert client.get(URL_RENOVAR).status_code == 405
