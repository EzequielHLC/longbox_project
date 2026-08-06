"""CU-47 — Cerrar Sesión."""

import pytest
from django.test import Client
from django.urls import reverse

from apps.core.models import RegistroAuditoria

URL_LOGOUT = reverse("accounts:logout")
URL_LOGIN = reverse("accounts:login")
URL_PROTEGIDA = reverse("core:tienda")

pytestmark = pytest.mark.django_db


def test_logout_invalida_la_sesion_actual(client, cliente):
    client.force_login(cliente)

    respuesta = client.post(URL_LOGOUT)

    assert respuesta.status_code == 302
    assert respuesta.url == URL_LOGIN
    assert "_auth_user_id" not in client.session

    posterior = client.get(URL_PROTEGIDA)
    assert posterior.status_code == 302
    assert posterior.url.startswith(URL_LOGIN)


def test_logout_no_afecta_las_sesiones_de_otros_dispositivos(cliente):
    telefono = Client()
    computadora = Client()
    telefono.force_login(cliente)
    computadora.force_login(cliente)

    telefono.post(URL_LOGOUT)

    assert "_auth_user_id" not in telefono.session
    assert computadora.get(URL_PROTEGIDA).status_code == 200


def test_logout_queda_registrado_en_auditoria(client, cliente):
    client.force_login(cliente)

    client.post(URL_LOGOUT)

    registro = RegistroAuditoria.objects.get(accion=RegistroAuditoria.CIERRE_SESION)
    assert registro.actor == cliente


def test_logout_no_acepta_get(client, cliente):
    """Un GET no puede desloguear: evita que un enlace externo cierre la sesión."""
    client.force_login(cliente)

    respuesta = client.get(URL_LOGOUT)

    assert respuesta.status_code == 405
    assert "_auth_user_id" in client.session
