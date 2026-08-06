import pytest

from apps.accounts.tests.factories import UsuarioFactory
from apps.core.models import RegistroAuditoria, RegistroAuditoriaError

pytestmark = pytest.mark.django_db


def test_registrar_completa_el_correo_del_actor():
    usuario = UsuarioFactory()

    registro = RegistroAuditoria.registrar(
        accion=RegistroAuditoria.INICIO_SESION, actor=usuario, ip="127.0.0.1"
    )

    assert registro.actor_email == usuario.email
    assert registro.ocurrido_en is not None


def test_una_entrada_de_auditoria_no_se_puede_modificar():
    registro = RegistroAuditoria.registrar(
        accion=RegistroAuditoria.INICIO_SESION, actor_email="alguien@longbox.test"
    )

    registro.detalle = "editado"
    with pytest.raises(RegistroAuditoriaError):
        registro.save()


def test_una_entrada_de_auditoria_no_se_puede_borrar():
    registro = RegistroAuditoria.registrar(
        accion=RegistroAuditoria.INICIO_SESION, actor_email="alguien@longbox.test"
    )

    with pytest.raises(RegistroAuditoriaError):
        registro.delete()

    assert RegistroAuditoria.objects.count() == 1


def test_la_traza_sobrevive_a_la_baja_del_usuario():
    usuario = UsuarioFactory()
    RegistroAuditoria.registrar(accion=RegistroAuditoria.INICIO_SESION, actor=usuario)

    usuario.delete()

    registro = RegistroAuditoria.objects.get()
    assert registro.actor is None
    assert registro.actor_email != ""
