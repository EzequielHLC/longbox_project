"""CU-USR-ALT, del lado del usuario nuevo: activar la cuenta y elegir contraseña."""

from datetime import datetime, timedelta

import pytest
from django.test import Client
from django.urls import reverse
from freezegun import freeze_time

from apps.accounts.models import Usuario
from apps.accounts.tests.helpers_usuarios import crear_usuario_pendiente
from apps.core.models import RegistroAuditoria

URL_LOGIN = reverse("accounts:login")
URL_MOSTRADOR = reverse("core:mostrador")
CONTRASENA_ELEGIDA = "MiPrimeraClave789"
MOMENTO_DEL_ALTA = datetime(2026, 8, 5, 10, 0, 0)

pytestmark = pytest.mark.django_db


def activar(navegador, enlace, contrasena=CONTRASENA_ELEGIDA):
    """Sigue el enlace del correo y completa el formulario de contraseña."""
    respuesta = navegador.get(enlace)
    return navegador.post(respuesta.url, {"new_password1": contrasena, "new_password2": contrasena})


def test_activar_la_cuenta_la_deja_activa_y_con_contrasena(client_admin):
    usuario, enlace = crear_usuario_pendiente(client_admin)

    respuesta = activar(Client(), enlace)

    assert respuesta.status_code == 302
    usuario.refresh_from_db()
    assert usuario.estado == Usuario.ACTIVO
    assert usuario.is_active is True
    assert usuario.check_password(CONTRASENA_ELEGIDA)


def test_al_terminar_se_ofrece_iniciar_sesion(client_admin):
    _, enlace = crear_usuario_pendiente(client_admin)
    navegador = Client()

    respuesta = navegador.get(activar(navegador, enlace).url)

    assert respuesta.status_code == 200
    assert "La cuenta se activó" in respuesta.content.decode()


def test_despues_de_activar_la_cuenta_puede_iniciar_sesion(client_admin):
    usuario, enlace = crear_usuario_pendiente(client_admin)
    activar(Client(), enlace)

    navegador = Client()
    navegador.post(URL_LOGIN, {"username": usuario.email, "password": CONTRASENA_ELEGIDA})

    assert navegador.get(URL_MOSTRADOR).status_code == 200


def test_una_cuenta_pendiente_no_puede_iniciar_sesion(client_admin):
    usuario, _ = crear_usuario_pendiente(client_admin)

    navegador = Client()
    navegador.post(URL_LOGIN, {"username": usuario.email, "password": CONTRASENA_ELEGIDA})

    assert "_auth_user_id" not in navegador.session


def test_el_enlace_vale_48_horas(client_admin):
    with freeze_time(MOMENTO_DEL_ALTA):
        _, enlace = crear_usuario_pendiente(client_admin)

    with freeze_time(MOMENTO_DEL_ALTA + timedelta(hours=47)):
        assert Client().get(enlace).status_code == 302


def test_el_enlace_vencido_es_rechazado(client_admin):
    with freeze_time(MOMENTO_DEL_ALTA):
        usuario, enlace = crear_usuario_pendiente(client_admin)

    with freeze_time(MOMENTO_DEL_ALTA + timedelta(hours=49)):
        respuesta = Client().get(enlace)

    assert respuesta.status_code == 200
    assert "El enlace ya no es válido" in respuesta.content.decode()
    usuario.refresh_from_db()
    assert usuario.estado == Usuario.PENDIENTE_ACTIVACION


def test_el_enlace_no_se_puede_usar_dos_veces(client_admin):
    _, enlace = crear_usuario_pendiente(client_admin)
    activar(Client(), enlace)

    segundo_uso = Client().get(enlace)

    assert segundo_uso.status_code == 200
    assert "El enlace ya no es válido" in segundo_uso.content.decode()


def test_una_contrasena_debil_no_activa_la_cuenta(client_admin):
    usuario, enlace = crear_usuario_pendiente(client_admin)

    navegador = Client()
    respuesta = activar(navegador, enlace, contrasena="123")

    assert respuesta.status_code == 200
    assert respuesta.context["form"].errors
    usuario.refresh_from_db()
    assert usuario.estado == Usuario.PENDIENTE_ACTIVACION


def test_la_activacion_queda_registrada_en_auditoria(client_admin):
    usuario, enlace = crear_usuario_pendiente(client_admin)

    activar(Client(), enlace)

    registro = RegistroAuditoria.objects.get(accion=RegistroAuditoria.ACTIVACION_CUENTA)
    assert registro.objetivo == usuario
