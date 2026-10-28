"""El correo que otra alta confirmó mientras ésta se validaba (plan 00 de cierre de deuda, D1).

El formulario ya dijo que el correo estaba libre y, antes de guardar, otro pedido
crea la cuenta con ese correo. La restricción de la base es la que no deja pasar
el duplicado; lo que se prueba es que el usuario reciba **el aviso del contrato**
y no un error 500, y que no quede nada a medias: ni cuenta, ni correo, ni
auditoría.
"""

import pytest
from django.urls import reverse

from apps.accounts.forms import (
    MENSAJE_CORREO_EN_USO,
    MENSAJE_CORREO_YA_REGISTRADO,
    FormularioRegistroCliente,
    FormularioUsuarioPersonal,
)
from apps.accounts.models import Usuario
from apps.accounts.tests.factories import UsuarioFactory
from apps.accounts.tests.helpers_usuarios import DATOS_DE_ALTA, URL_ALTA, datos_de, url_edicion
from apps.accounts.tests.test_registro_cliente import DATOS_REGISTRO
from apps.core.models import RegistroAuditoria
from apps.core.tests.concurrencia import gana_la_carrera

pytestmark = pytest.mark.django_db

URL_REGISTRO = reverse("accounts:registro_cliente")


def test_CO107_E1_el_correo_registrado_mientras_se_validaba_avisa_sin_error(client, mailoutbox):
    correo = DATOS_REGISTRO["email"]

    with gana_la_carrera(
        FormularioRegistroCliente, lambda: UsuarioFactory(email=correo, rol=Usuario.CLIENTE)
    ):
        respuesta = client.post(URL_REGISTRO, DATOS_REGISTRO)

    assert respuesta.status_code == 200
    contenido = respuesta.content.decode()
    assert MENSAJE_CORREO_YA_REGISTRADO in contenido
    # E1: «se ofrece enlace a CO-117», igual que cuando el formulario lo ve antes.
    assert reverse("accounts:password_reset") in contenido
    assert respuesta.context["form"]["nombre_completo"].value() == DATOS_REGISTRO["nombre_completo"]
    assert Usuario.objects.filter(email__iexact=correo).count() == 1
    assert "_auth_user_id" not in client.session
    assert mailoutbox == []
    assert not RegistroAuditoria.objects.filter(accion=RegistroAuditoria.REGISTRO_CLIENTE).exists()


def test_CO120_E2_el_correo_dado_de_alta_mientras_se_validaba_avisa_sin_error(
    client_admin, mailoutbox
):
    correo = DATOS_DE_ALTA["email"]

    with gana_la_carrera(
        FormularioUsuarioPersonal, lambda: UsuarioFactory(email=correo, rol=Usuario.CAJERO)
    ):
        respuesta = client_admin.post(URL_ALTA, DATOS_DE_ALTA)

    assert respuesta.status_code == 200
    assert MENSAJE_CORREO_EN_USO in respuesta.content.decode()
    assert Usuario.objects.filter(email__iexact=correo).count() == 1
    assert mailoutbox == []
    assert not RegistroAuditoria.objects.filter(accion=RegistroAuditoria.ALTA_USUARIO).exists()


def test_CO121_E2_el_correo_tomado_mientras_se_validaba_la_edicion_avisa_sin_error(client_admin):
    cajero = UsuarioFactory(email="cajero@longbox.test", rol=Usuario.CAJERO)
    nuevo = "nuevo@longbox.test"

    with gana_la_carrera(
        FormularioUsuarioPersonal, lambda: UsuarioFactory(email=nuevo, rol=Usuario.CLIENTE)
    ):
        respuesta = client_admin.post(url_edicion(cajero), datos_de(cajero, email=nuevo))

    assert respuesta.status_code == 200
    assert MENSAJE_CORREO_EN_USO in respuesta.content.decode()
    cajero.refresh_from_db()
    assert cajero.email == "cajero@longbox.test"
    assert not RegistroAuditoria.objects.filter(
        accion=RegistroAuditoria.MODIFICACION_USUARIO
    ).exists()
