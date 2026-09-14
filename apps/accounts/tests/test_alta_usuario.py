"""CU-USR-ALT — Dar de Alta Usuario del Sistema."""

import pytest
from django.core import mail
from django.test import Client

from apps.accounts.forms import MENSAJE_CORREO_EN_USO
from apps.accounts.models import Usuario
from apps.accounts.tests.factories import UsuarioFactory
from apps.accounts.tests.helpers_usuarios import (
    DATOS_DE_ALTA,
    URL_ALTA,
    URL_LISTA,
    crear_usuario_pendiente,
)
from apps.core.models import RegistroAuditoria

pytestmark = pytest.mark.django_db


def test_el_alta_deja_la_cuenta_pendiente_de_activacion(client_admin):
    respuesta = client_admin.post(URL_ALTA, DATOS_DE_ALTA)

    assert respuesta.status_code == 302
    usuario = Usuario.objects.get(email="ana@longbox.test")
    assert usuario.estado == Usuario.PENDIENTE_ACTIVACION
    assert usuario.rol == "cajero"
    assert usuario.get_full_name() == "Ana María Pérez"
    # Django bloquea el login por las suyas mientras la cuenta no esté activa.
    assert usuario.is_active is False


def test_el_alta_genera_un_token_de_activacion_utilizable(client_admin):
    _, enlace = crear_usuario_pendiente(client_admin)

    # El destinatario abre el enlace sin sesión iniciada: si el token es válido,
    # Django lo manda al formulario para elegir contraseña.
    assert Client().get(enlace).status_code == 302


def test_la_cuenta_nueva_no_tiene_contrasena_utilizable(client_admin):
    usuario, _ = crear_usuario_pendiente(client_admin)

    assert usuario.has_usable_password() is False


def test_el_alta_avisa_por_correo_al_usuario_nuevo(client_admin):
    client_admin.post(URL_ALTA, DATOS_DE_ALTA)

    assert len(mail.outbox) == 1
    correo = mail.outbox[0]
    assert correo.to == ["ana@longbox.test"]
    assert "activación de cuenta" in correo.subject.lower()
    assert "48 horas" in correo.body


def test_el_alta_queda_registrada_en_auditoria_con_el_rol(client_admin, administrador):
    client_admin.post(URL_ALTA, DATOS_DE_ALTA)

    registro = RegistroAuditoria.objects.get(accion=RegistroAuditoria.ALTA_USUARIO)
    assert registro.actor == administrador
    assert registro.objetivo.email == "ana@longbox.test"
    assert "Cajero" in registro.detalle


def test_un_correo_ya_usado_por_una_cuenta_activa_es_rechazado(client_admin):
    UsuarioFactory(email="ana@longbox.test", rol="cajero", estado=Usuario.ACTIVO)

    respuesta = client_admin.post(URL_ALTA, DATOS_DE_ALTA)

    assert respuesta.status_code == 200
    assert MENSAJE_CORREO_EN_USO in respuesta.content.decode()
    assert Usuario.objects.filter(email="ana@longbox.test").count() == 1
    assert mail.outbox == []


def test_un_correo_ya_usado_por_una_cuenta_pendiente_es_rechazado(client_admin):
    crear_usuario_pendiente(client_admin)
    mail.outbox.clear()

    respuesta = client_admin.post(URL_ALTA, DATOS_DE_ALTA)

    assert respuesta.status_code == 200
    assert MENSAJE_CORREO_EN_USO in respuesta.content.decode()
    assert Usuario.objects.filter(email="ana@longbox.test").count() == 1
    assert mail.outbox == []


def test_un_campo_obligatorio_vacio_no_crea_la_cuenta(client_admin):
    respuesta = client_admin.post(URL_ALTA, {**DATOS_DE_ALTA, "nombre_completo": ""})

    assert respuesta.status_code == 200
    assert respuesta.context["form"].errors["nombre_completo"]
    assert not Usuario.objects.filter(email="ana@longbox.test").exists()


def test_el_formulario_no_ofrece_cliente_como_rol(client_admin):
    respuesta = client_admin.get(URL_ALTA)

    opciones = dict(respuesta.context["form"].fields["rol"].choices)
    assert set(opciones) == {"cajero", "administrador"}


def test_un_post_con_rol_cliente_es_rechazado(client_admin):
    """La restricción del rol es del servidor, no del `select` del navegador."""
    respuesta = client_admin.post(URL_ALTA, {**DATOS_DE_ALTA, "rol": "cliente"})

    assert respuesta.status_code == 200
    assert respuesta.context["form"].errors["rol"]
    assert not Usuario.objects.filter(email="ana@longbox.test").exists()


@pytest.mark.parametrize("rol_sin_permiso", ["cliente", "cajero"])
def test_solo_el_administrador_accede_al_alta(client, rol_sin_permiso):
    client.force_login(UsuarioFactory(rol=rol_sin_permiso))

    assert client.get(URL_ALTA).status_code == 403
    assert client.post(URL_ALTA, DATOS_DE_ALTA).status_code == 403
    assert not Usuario.objects.filter(email="ana@longbox.test").exists()


def test_la_lista_de_usuarios_no_filtra_datos_a_otros_roles(client, cajero):
    """403 sin datos parciales: el cajero no ve ni un pedazo de la tabla."""
    UsuarioFactory(rol="administrador", email="jefa@longbox.test")
    client.force_login(cajero)

    respuesta = client.get(URL_LISTA)

    assert respuesta.status_code == 403
    assert "jefa@longbox.test" not in respuesta.content.decode()


def test_la_lista_muestra_solo_cuentas_de_personal(client_admin, cliente, cajero):
    respuesta = client_admin.get(URL_LISTA)

    contenido = respuesta.content.decode()
    assert cajero.email in contenido
    assert cliente.email not in contenido
