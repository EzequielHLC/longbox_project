"""CU-46 — Iniciar Sesión."""

import pytest
from django.urls import reverse

from apps.accounts.forms import (
    MENSAJE_CREDENCIALES,
    MENSAJE_CUENTA_INACTIVA,
)
from apps.accounts.tests.factories import PASSWORD_DE_PRUEBA, UsuarioFactory
from apps.core.models import RegistroAuditoria

URL_LOGIN = reverse("accounts:login")

pytestmark = pytest.mark.django_db


def hay_sesion(client):
    return "_auth_user_id" in client.session


@pytest.mark.parametrize(
    ("rol", "destino"),
    [
        ("cliente", "core:tienda"),
        ("cajero", "core:mostrador"),
        ("administrador", "core:panel"),
    ],
)
def test_login_exitoso_crea_sesion_y_redirige_segun_rol(client, rol, destino):
    usuario = UsuarioFactory(rol=rol)

    respuesta = client.post(URL_LOGIN, {"username": usuario.email, "password": PASSWORD_DE_PRUEBA})

    assert respuesta.status_code == 302
    assert respuesta.url == reverse(destino)
    assert client.session["_auth_user_id"] == str(usuario.pk)


def test_login_exitoso_registra_el_inicio_en_auditoria(client, cliente):
    client.post(URL_LOGIN, {"username": cliente.email, "password": PASSWORD_DE_PRUEBA})

    registro = RegistroAuditoria.objects.get(accion=RegistroAuditoria.INICIO_SESION)
    assert registro.actor == cliente
    assert registro.actor_email == cliente.email


def test_login_acepta_el_correo_sin_distinguir_mayusculas(client, cliente):
    respuesta = client.post(
        URL_LOGIN, {"username": cliente.email.upper(), "password": PASSWORD_DE_PRUEBA}
    )

    assert respuesta.status_code == 302
    assert hay_sesion(client)


def test_contrasena_incorrecta_no_crea_sesion_y_muestra_mensaje_generico(client, cliente):
    respuesta = client.post(URL_LOGIN, {"username": cliente.email, "password": "otra-clave"})

    assert respuesta.status_code == 200
    assert not hay_sesion(client)
    assert MENSAJE_CREDENCIALES in respuesta.content.decode()


def test_correo_inexistente_devuelve_exactamente_el_mismo_mensaje(client, cliente):
    """No debe poder distinguirse "no existe la cuenta" de "erraste la clave"."""
    con_cuenta_real = client.post(URL_LOGIN, {"username": cliente.email, "password": "otra-clave"})
    sin_cuenta = client.post(
        URL_LOGIN, {"username": "nadie@longbox.test", "password": "otra-clave"}
    )

    assert sin_cuenta.status_code == con_cuenta_real.status_code == 200
    assert not hay_sesion(client)
    errores_sin_cuenta = list(sin_cuenta.context["form"].non_field_errors())
    errores_con_cuenta = list(con_cuenta_real.context["form"].non_field_errors())
    assert errores_sin_cuenta == errores_con_cuenta == [MENSAJE_CREDENCIALES]


def test_cuenta_inactiva_no_crea_sesion(client):
    usuario = UsuarioFactory(is_active=False)

    respuesta = client.post(URL_LOGIN, {"username": usuario.email, "password": PASSWORD_DE_PRUEBA})

    assert respuesta.status_code == 200
    assert not hay_sesion(client)
    assert MENSAJE_CUENTA_INACTIVA in respuesta.content.decode()


def test_cuenta_inactiva_no_se_revela_a_quien_no_sabe_la_contrasena(client):
    """Sin la contraseña correcta, una cuenta inactiva responde como cualquier otra."""
    usuario = UsuarioFactory(is_active=False)

    respuesta = client.post(URL_LOGIN, {"username": usuario.email, "password": "otra-clave"})

    contenido = respuesta.content.decode()
    assert MENSAJE_CREDENCIALES in contenido
    assert MENSAJE_CUENTA_INACTIVA not in contenido


def test_usuario_con_sesion_activa_no_ve_la_pantalla_de_login(client, cliente):
    """Precondición del CU: no tiene una sesión vigente en el dispositivo."""
    client.force_login(cliente)

    respuesta = client.get(URL_LOGIN)

    assert respuesta.status_code == 302
    assert respuesta.url == reverse("core:tienda")
