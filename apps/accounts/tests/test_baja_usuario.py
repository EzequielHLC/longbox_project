"""CU-52 — Dar de Baja Usuario del Sistema."""

import pytest
from django.test import Client
from django.urls import reverse

from apps.accounts.forms import MENSAJE_CUENTA_INACTIVA, MENSAJE_UNICO_ADMINISTRADOR
from apps.accounts.models import Usuario
from apps.accounts.tests.factories import PASSWORD_DE_PRUEBA, UsuarioFactory
from apps.accounts.tests.helpers_usuarios import url_baja
from apps.core.models import RegistroAuditoria

URL_LOGIN = reverse("accounts:login")
URL_MOSTRADOR = reverse("core:mostrador")

pytestmark = pytest.mark.django_db


def test_la_pantalla_pide_confirmacion_explicita(client_admin, cajero):
    respuesta = client_admin.get(url_baja(cajero))

    assert respuesta.status_code == 200
    contenido = respuesta.content.decode()
    assert "Confirmar baja" in contenido
    # El CU pide avisar que las sesiones se cierran de inmediato.
    assert "todas las sesiones abiertas de la cuenta" in contenido
    cajero.refresh_from_db()
    assert cajero.estado == Usuario.ACTIVO  # el GET no da de baja nada


def test_la_baja_cambia_el_estado_e_invalida_las_sesiones(client_admin, cajero):
    telefono = Client()
    computadora = Client()
    telefono.force_login(cajero)
    computadora.force_login(cajero)
    assert telefono.get(URL_MOSTRADOR).status_code == 200

    respuesta = client_admin.post(url_baja(cajero))

    assert respuesta.status_code == 302
    cajero.refresh_from_db()
    assert cajero.estado == Usuario.INACTIVO
    assert cajero.is_active is False
    assert telefono.get(URL_MOSTRADOR).status_code == 302
    assert computadora.get(URL_MOSTRADOR).status_code == 302


def test_la_baja_es_logica_y_no_borra_la_cuenta(client_admin, cajero):
    client_admin.post(url_baja(cajero))

    assert Usuario.objects.filter(pk=cajero.pk).exists()


def test_un_usuario_dado_de_baja_no_puede_volver_a_iniciar_sesion(client_admin, cajero):
    client_admin.post(url_baja(cajero))

    navegador = Client()
    respuesta = navegador.post(
        URL_LOGIN, {"username": cajero.email, "password": PASSWORD_DE_PRUEBA}
    )

    assert "_auth_user_id" not in navegador.session
    assert MENSAJE_CUENTA_INACTIVA in respuesta.content.decode()


def test_no_se_puede_dar_de_baja_al_unico_administrador_activo(client_admin, administrador):
    UsuarioFactory(rol="administrador", estado=Usuario.INACTIVO)

    respuesta = client_admin.post(url_baja(administrador), follow=True)

    assert MENSAJE_UNICO_ADMINISTRADOR in respuesta.content.decode()
    administrador.refresh_from_db()
    assert administrador.estado == Usuario.ACTIVO


def test_se_puede_dar_de_baja_un_administrador_si_queda_otro_activo(client_admin, administrador):
    suplente = UsuarioFactory(rol="administrador", estado=Usuario.ACTIVO)

    client_admin.post(url_baja(suplente))

    suplente.refresh_from_db()
    assert suplente.estado == Usuario.INACTIVO


def test_darse_de_baja_a_uno_mismo_cierra_la_propia_sesion(client_admin, administrador):
    UsuarioFactory(rol="administrador", estado=Usuario.ACTIVO)  # queda quien administre

    respuesta = client_admin.post(url_baja(administrador))

    assert respuesta.status_code == 302
    assert respuesta.url == URL_LOGIN
    assert "_auth_user_id" not in client_admin.session
    administrador.refresh_from_db()
    assert administrador.estado == Usuario.INACTIVO


def test_la_baja_queda_registrada_en_auditoria(client_admin, cajero, administrador):
    client_admin.post(url_baja(cajero))

    registro = RegistroAuditoria.objects.get(accion=RegistroAuditoria.BAJA_USUARIO)
    assert registro.actor == administrador
    assert registro.objetivo == cajero
    assert registro.objetivo_email == cajero.email


def test_el_historial_del_usuario_dado_de_baja_sigue_consultable(client_admin, cajero):
    """La baja no dispara borrado ni anonimización en cascada."""
    navegador = Client()
    navegador.force_login(cajero)  # genera su registro de inicio de sesión
    historial_previo = RegistroAuditoria.objects.filter(actor=cajero).count()
    assert historial_previo > 0

    client_admin.post(url_baja(cajero))

    historial = RegistroAuditoria.objects.filter(actor=cajero)
    assert historial.count() == historial_previo
    assert historial.first().actor_email == cajero.email


def test_no_se_puede_dar_de_baja_una_cuenta_que_no_esta_activa(client_admin):
    inactivo = UsuarioFactory(rol="cajero", estado=Usuario.INACTIVO)

    respuesta = client_admin.post(url_baja(inactivo), follow=True)

    assert "Solo se puede dar de baja una cuenta activa." in respuesta.content.decode()
    assert not RegistroAuditoria.objects.filter(accion=RegistroAuditoria.BAJA_USUARIO).exists()


def test_solo_el_administrador_puede_dar_de_baja(client, cajero):
    victima = UsuarioFactory(rol="cajero")
    client.force_login(cajero)

    assert client.get(url_baja(victima)).status_code == 403
    assert client.post(url_baja(victima)).status_code == 403
    victima.refresh_from_db()
    assert victima.estado == Usuario.ACTIVO
