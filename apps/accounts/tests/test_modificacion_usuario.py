"""CU-USR-MOD — Modificar Usuario del Sistema."""

import pytest
from django.core import mail
from django.test import Client
from django.urls import reverse

from apps.accounts.forms import MENSAJE_CORREO_EN_USO, MENSAJE_UNICO_ADMINISTRADOR
from apps.accounts.models import Usuario
from apps.accounts.tests.factories import UsuarioFactory
from apps.accounts.tests.helpers_usuarios import (
    crear_usuario_pendiente,
    datos_de,
    enlace_de_activacion,
    url_edicion,
    url_reenviar_activacion,
)
from apps.core.models import RegistroAuditoria

URL_MOSTRADOR = reverse("core:mostrador")

pytestmark = pytest.mark.django_db


def navegador_de(usuario):
    """Simula el dispositivo donde ese usuario tiene su sesión abierta."""
    navegador = Client()
    navegador.force_login(usuario)
    return navegador


def test_el_formulario_precarga_los_datos_actuales(client_admin, cajero):
    respuesta = client_admin.get(url_edicion(cajero))

    formulario = respuesta.context["form"]
    assert formulario.initial["email"] == cajero.email
    assert formulario.initial["rol"] == "cajero"
    assert formulario.fields["nombre_completo"].initial == cajero.get_full_name()


def test_modificar_datos_sin_tocar_el_rol_no_invalida_la_sesion(client_admin, cajero):
    navegador_del_cajero = navegador_de(cajero)
    assert navegador_del_cajero.get(URL_MOSTRADOR).status_code == 200

    respuesta = client_admin.post(
        url_edicion(cajero), datos_de(cajero, nombre_completo="Otro Nombre")
    )

    assert respuesta.status_code == 302
    cajero.refresh_from_db()
    assert cajero.get_full_name() == "Otro Nombre"
    assert navegador_del_cajero.get(URL_MOSTRADOR).status_code == 200


def test_modificar_el_rol_invalida_la_sesion_del_usuario(client_admin, cajero):
    navegador_del_cajero = navegador_de(cajero)
    assert navegador_del_cajero.get(URL_MOSTRADOR).status_code == 200

    client_admin.post(url_edicion(cajero), datos_de(cajero, rol="administrador"))

    cajero.refresh_from_db()
    assert cajero.rol == "administrador"
    # 302 (redirige al login), no 403: la sesión ya no existe.
    assert navegador_del_cajero.get(URL_MOSTRADOR).status_code == 302


def test_modificar_el_rol_no_toca_las_sesiones_de_los_demas(client_admin, cajero, cliente):
    navegador_del_cliente = navegador_de(cliente)

    client_admin.post(url_edicion(cajero), datos_de(cajero, rol="administrador"))

    assert navegador_del_cliente.get(reverse("core:tienda")).status_code == 200


def test_no_se_le_puede_quitar_el_rol_al_unico_administrador_activo(client_admin, administrador):
    # Un Administrador inactivo no cuenta como respaldo.
    UsuarioFactory(rol="administrador", estado=Usuario.INACTIVO)

    respuesta = client_admin.post(url_edicion(administrador), datos_de(administrador, rol="cajero"))

    assert respuesta.status_code == 200
    assert MENSAJE_UNICO_ADMINISTRADOR in respuesta.content.decode()
    administrador.refresh_from_db()
    assert administrador.rol == "administrador"


def test_se_le_puede_quitar_el_rol_si_queda_otro_administrador_activo(client_admin):
    otro_administrador = UsuarioFactory(rol="administrador", estado=Usuario.ACTIVO)

    respuesta = client_admin.post(
        url_edicion(otro_administrador), datos_de(otro_administrador, rol="cajero")
    )

    assert respuesta.status_code == 302
    otro_administrador.refresh_from_db()
    assert otro_administrador.rol == "cajero"


def test_cambiarse_el_rol_a_uno_mismo_cierra_la_propia_sesion(client_admin, administrador):
    """La sesión invalidada puede ser la del propio Administrador que edita."""
    UsuarioFactory(rol="administrador", estado=Usuario.ACTIVO)  # queda quien administre

    respuesta = client_admin.post(url_edicion(administrador), datos_de(administrador, rol="cajero"))

    assert respuesta.status_code == 302
    assert respuesta.url == reverse("accounts:login")
    assert "_auth_user_id" not in client_admin.session


def test_un_correo_ya_usado_por_otra_cuenta_no_actualiza_nada(client_admin, cajero):
    otra = UsuarioFactory(rol="administrador", email="ocupado@longbox.test")

    respuesta = client_admin.post(url_edicion(cajero), datos_de(cajero, email=otra.email))

    assert respuesta.status_code == 200
    assert MENSAJE_CORREO_EN_USO in respuesta.content.decode()
    cajero.refresh_from_db()
    assert cajero.email != otra.email


def test_conservar_el_propio_correo_no_es_un_conflicto(client_admin, cajero):
    respuesta = client_admin.post(url_edicion(cajero), datos_de(cajero, nombre_completo="Ana Ruiz"))

    assert respuesta.status_code == 302


def test_la_auditoria_registra_valores_anteriores_y_nuevos(client_admin, cajero):
    correo_anterior = cajero.email

    client_admin.post(
        url_edicion(cajero),
        datos_de(cajero, email="nuevo@longbox.test", rol="administrador"),
    )

    registro = RegistroAuditoria.objects.get(accion=RegistroAuditoria.MODIFICACION_USUARIO)
    assert registro.objetivo == cajero
    # No alcanza con el estado final: tienen que estar los dos valores.
    assert correo_anterior in registro.detalle
    assert "nuevo@longbox.test" in registro.detalle
    assert "Cajero" in registro.detalle
    assert "Administrador" in registro.detalle


def test_guardar_sin_cambios_no_ensucia_la_auditoria(client_admin, cajero):
    client_admin.post(url_edicion(cajero), datos_de(cajero))

    assert not RegistroAuditoria.objects.filter(
        accion=RegistroAuditoria.MODIFICACION_USUARIO
    ).exists()


def test_regenerar_el_enlace_de_activacion_invalida_el_anterior(client_admin):
    usuario, enlace_anterior = crear_usuario_pendiente(client_admin)

    respuesta = client_admin.post(url_reenviar_activacion(usuario))

    assert respuesta.status_code == 302
    enlace_nuevo = enlace_de_activacion(mail.outbox[-1])
    assert enlace_nuevo != enlace_anterior
    assert Client().get(enlace_nuevo).status_code == 302
    # El viejo ya no valida: se queda en la pantalla de "enlace no válido".
    assert Client().get(enlace_anterior).status_code == 200


def test_regenerar_el_enlace_queda_en_auditoria(client_admin):
    usuario, _ = crear_usuario_pendiente(client_admin)

    client_admin.post(url_reenviar_activacion(usuario))

    registro = RegistroAuditoria.objects.get(accion=RegistroAuditoria.REENVIO_ACTIVACION)
    assert registro.objetivo == usuario


def test_no_se_regenera_el_enlace_de_una_cuenta_ya_activa(client_admin, cajero):
    respuesta = client_admin.post(url_reenviar_activacion(cajero), follow=True)

    assert "pendiente de activación" in respuesta.content.decode()
    assert mail.outbox == []


def test_solo_el_administrador_puede_editar(client, cajero):
    client.force_login(cajero)

    assert client.get(url_edicion(cajero)).status_code == 403
    assert (
        client.post(url_edicion(cajero), datos_de(cajero, rol="administrador")).status_code == 403
    )
    cajero.refresh_from_db()
    assert cajero.rol == "cajero"
