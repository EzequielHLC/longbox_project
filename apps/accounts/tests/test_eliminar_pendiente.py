"""Eliminación de una cuenta que nunca se activó.

La describe CU-USR-ELI · Eliminar Cuenta Nunca Activada, con CO-200 y CO-125:
sin esto, una cuenta cargada con el correo equivocado queda pendiente para
siempre y ese correo bloqueado, porque el CU-USR-BAJ exige estado Activo para
dar de baja.
"""

import pytest
from django.core import mail
from django.urls import reverse

from apps.accounts.forms import MENSAJE_CUENTA_CON_HISTORIAL
from apps.accounts.models import Usuario
from apps.accounts.tests.factories import UsuarioFactory
from apps.accounts.tests.helpers_usuarios import (
    DATOS_DE_ALTA,
    URL_ALTA,
    crear_usuario_pendiente,
)
from apps.core.models import RegistroAuditoria

pytestmark = pytest.mark.django_db


def url_eliminar(usuario):
    return reverse("accounts:usuario_eliminar", args=[usuario.pk])


def test_la_pantalla_pide_confirmacion_explicita(client_admin):
    usuario, _ = crear_usuario_pendiente(client_admin)

    respuesta = client_admin.get(url_eliminar(usuario))

    assert respuesta.status_code == 200
    assert "Eliminar cuenta" in respuesta.content.decode()
    assert Usuario.objects.filter(pk=usuario.pk).exists()  # el GET no borra nada


def test_eliminar_una_cuenta_pendiente_la_borra(client_admin):
    usuario, _ = crear_usuario_pendiente(client_admin)

    respuesta = client_admin.post(url_eliminar(usuario))

    assert respuesta.status_code == 302
    assert not Usuario.objects.filter(pk=usuario.pk).exists()


def test_eliminar_libera_el_correo_para_darlo_de_alta_de_nuevo(client_admin):
    """Es el motivo por el que existe esta operación."""
    usuario, _ = crear_usuario_pendiente(client_admin)
    client_admin.post(url_eliminar(usuario))
    mail.outbox.clear()

    respuesta = client_admin.post(URL_ALTA, DATOS_DE_ALTA)

    assert respuesta.status_code == 302
    assert Usuario.objects.filter(email=DATOS_DE_ALTA["email"]).count() == 1
    assert len(mail.outbox) == 1


@pytest.mark.parametrize("estado", [Usuario.ACTIVO, Usuario.INACTIVO])
def test_una_cuenta_que_alguna_vez_se_uso_no_se_elimina(client_admin, estado):
    usuario = UsuarioFactory(rol="cajero", estado=estado)

    respuesta = client_admin.post(url_eliminar(usuario), follow=True)

    assert MENSAJE_CUENTA_CON_HISTORIAL in respuesta.content.decode()
    assert Usuario.objects.filter(pk=usuario.pk).exists()


def test_la_auditoria_sobrevive_al_borrado_con_el_correo(client_admin, administrador):
    usuario, _ = crear_usuario_pendiente(client_admin)
    correo = usuario.email

    client_admin.post(url_eliminar(usuario))

    registro = RegistroAuditoria.objects.get(accion=RegistroAuditoria.ELIMINACION_PENDIENTE)
    assert registro.actor == administrador
    # La clave foránea se pone en NULL al desaparecer la cuenta, pero el correo
    # desnormalizado deja la traza de a quién se eliminó.
    assert registro.objetivo is None
    assert registro.objetivo_email == correo


def test_el_registro_del_alta_tambien_sigue_consultable(client_admin):
    usuario, _ = crear_usuario_pendiente(client_admin)

    client_admin.post(url_eliminar(usuario))

    alta = RegistroAuditoria.objects.get(accion=RegistroAuditoria.ALTA_USUARIO)
    assert alta.objetivo_email == "ana@longbox.test"


def test_solo_el_administrador_puede_eliminar(client, client_admin, cajero):
    usuario, _ = crear_usuario_pendiente(client_admin)
    client.force_login(cajero)

    assert client.get(url_eliminar(usuario)).status_code == 403
    assert client.post(url_eliminar(usuario)).status_code == 403
    assert Usuario.objects.filter(pk=usuario.pk).exists()
