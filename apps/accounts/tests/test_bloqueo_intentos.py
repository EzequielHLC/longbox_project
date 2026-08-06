"""CU-46, excepción: 5 intentos fallidos consecutivos bloquean el acceso."""

from datetime import timedelta

import pytest
from django.core import mail
from django.test import Client
from django.urls import reverse
from django.utils import timezone
from freezegun import freeze_time

from apps.accounts.forms import MENSAJE_BLOQUEO, MENSAJE_CREDENCIALES
from apps.accounts.models import IntentoFallido
from apps.accounts.tests.factories import PASSWORD_DE_PRUEBA, UsuarioFactory
from apps.core.models import RegistroAuditoria

URL_LOGIN = reverse("accounts:login")
INTENTOS_MAXIMOS = 5
IP_ATACANTE = "10.0.0.7"

pytestmark = pytest.mark.django_db


def intentar(client, email, password="clave-incorrecta", ip=IP_ATACANTE):
    return client.post(URL_LOGIN, {"username": email, "password": password}, REMOTE_ADDR=ip)


def test_quinto_intento_fallido_bloquea_el_acceso(client, cliente):
    for _ in range(INTENTOS_MAXIMOS):
        respuesta = intentar(client, cliente.email)
        assert MENSAJE_CREDENCIALES in respuesta.content.decode()

    bloqueado = intentar(client, cliente.email)

    assert MENSAJE_BLOQUEO in bloqueado.content.decode()
    assert IntentoFallido.objects.count() == INTENTOS_MAXIMOS


def test_el_bloqueo_rechaza_incluso_la_contrasena_correcta(client, cliente):
    for _ in range(INTENTOS_MAXIMOS):
        intentar(client, cliente.email)

    respuesta = intentar(client, cliente.email, password=PASSWORD_DE_PRUEBA)

    assert "_auth_user_id" not in client.session
    assert MENSAJE_BLOQUEO in respuesta.content.decode()


def test_el_bloqueo_avisa_al_correo_registrado_y_queda_auditado(client, cliente):
    for _ in range(INTENTOS_MAXIMOS):
        intentar(client, cliente.email)

    assert len(mail.outbox) == 1
    assert mail.outbox[0].to == [cliente.email]
    registro = RegistroAuditoria.objects.get(accion=RegistroAuditoria.BLOQUEO_POR_INTENTOS)
    assert registro.actor == cliente
    assert registro.ip == IP_ATACANTE


def test_el_bloqueo_se_levanta_al_pasar_la_ventana_de_tiempo(client, cliente, settings):
    momento = timezone.now()
    with freeze_time(momento):
        for _ in range(INTENTOS_MAXIMOS):
            intentar(client, cliente.email)
        assert MENSAJE_BLOQUEO in intentar(client, cliente.email).content.decode()

    despues = momento + timedelta(minutes=settings.LOGIN_BLOQUEO_MINUTOS + 1)
    with freeze_time(despues):
        respuesta = intentar(client, cliente.email, password=PASSWORD_DE_PRUEBA)

    assert respuesta.status_code == 302
    assert client.session["_auth_user_id"] == str(cliente.pk)


def test_los_intentos_de_otra_ip_no_bloquean_la_cuenta(cliente):
    """El bloqueo es por dispositivo: un tercero no puede dejar afuera al titular."""
    atacante = Client()
    for _ in range(INTENTOS_MAXIMOS):
        intentar(atacante, cliente.email, ip=IP_ATACANTE)

    titular = Client()
    respuesta = intentar(titular, cliente.email, password=PASSWORD_DE_PRUEBA, ip="192.168.0.10")

    assert respuesta.status_code == 302
    assert titular.session["_auth_user_id"] == str(cliente.pk)


def test_un_login_exitoso_corta_la_racha_de_intentos(client, cliente):
    for _ in range(INTENTOS_MAXIMOS - 1):
        intentar(client, cliente.email)

    intentar(client, cliente.email, password=PASSWORD_DE_PRUEBA)

    assert IntentoFallido.objects.count() == 0


def test_tambien_se_cuentan_los_intentos_contra_correos_inexistentes(client):
    """Si solo contáramos cuentas reales, la diferencia revelaría cuáles existen."""
    for _ in range(INTENTOS_MAXIMOS):
        intentar(client, "nadie@longbox.test")

    respuesta = intentar(client, "nadie@longbox.test")

    assert MENSAJE_BLOQUEO in respuesta.content.decode()
    # No hay a quién avisarle: no se manda correo a una dirección desconocida.
    assert mail.outbox == []


def test_una_cuenta_inactiva_con_clave_correcta_no_suma_intentos(client):
    usuario = UsuarioFactory(is_active=False)

    intentar(client, usuario.email, password=PASSWORD_DE_PRUEBA)

    assert IntentoFallido.objects.count() == 0
