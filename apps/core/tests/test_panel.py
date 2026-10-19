"""Tablero de entrada del Administrador y menú lateral del backoffice."""

import pytest
from django.urls import reverse

from apps.accounts.models import Usuario
from apps.accounts.tests.factories import UsuarioFactory
from apps.core.models import RegistroAuditoria

pytestmark = pytest.mark.django_db

URL_PANEL = reverse("core:panel")


def test_las_cifras_cuentan_cada_estado_por_separado(client_admin):
    UsuarioFactory(rol=Usuario.CAJERO, estado=Usuario.ACTIVO)
    UsuarioFactory(rol=Usuario.CAJERO, estado=Usuario.PENDIENTE_ACTIVACION)
    UsuarioFactory(rol=Usuario.CAJERO, estado=Usuario.INACTIVO)
    UsuarioFactory(rol=Usuario.CLIENTE)
    UsuarioFactory(rol=Usuario.CLIENTE)

    cuentas = client_admin.get(URL_PANEL).context["cuentas"]

    # El Administrador de la sesión también es personal activo.
    assert cuentas["personal_activo"] == 2
    assert cuentas["pendientes"] == 1
    assert cuentas["dados_de_baja"] == 1
    assert cuentas["clientes"] == 2


def test_muestra_la_actividad_reciente_del_log(client_admin, administrador):
    RegistroAuditoria.registrar(
        accion=RegistroAuditoria.ALTA_USUARIO,
        actor=administrador,
        objetivo_email="nueva@longbox.test",
    )

    respuesta = client_admin.get(URL_PANEL)

    assert "nueva@longbox.test" in respuesta.content.decode()
    # Lo más nuevo primero. (La otra entrada es el inicio de sesión del propio
    # Administrador, que la fixture registra al abrir la sesión.)
    ultimo = respuesta.context["actividad"][0]
    assert ultimo.accion == RegistroAuditoria.ALTA_USUARIO
    assert ultimo.objetivo_email == "nueva@longbox.test"


def test_la_actividad_se_recorta_a_las_ultimas_doce_entradas(client_admin, administrador):
    for _ in range(15):
        RegistroAuditoria.registrar(accion=RegistroAuditoria.INICIO_SESION, actor=administrador)

    assert len(client_admin.get(URL_PANEL).context["actividad"]) == 12


def test_los_bloqueos_del_dia_se_muestran(client_admin):
    RegistroAuditoria.registrar(
        accion=RegistroAuditoria.BLOQUEO_POR_INTENTOS, actor_email="atacante@correo.test"
    )

    assert client_admin.get(URL_PANEL).context["bloqueos_del_dia"] == 1


def test_sin_bloqueos_el_contador_esta_en_cero(client_admin):
    assert client_admin.get(URL_PANEL).context["bloqueos_del_dia"] == 0


@pytest.mark.parametrize("rol_sin_permiso", ["cliente", "cajero"])
def test_solo_el_administrador_entra_al_panel(client, rol_sin_permiso):
    client.force_login(UsuarioFactory(rol=rol_sin_permiso))

    assert client.get(URL_PANEL).status_code == 403


# ---------------------------------------------------------------------------
# Menú lateral
# ---------------------------------------------------------------------------


def test_el_menu_lateral_enlaza_las_secciones_disponibles(client_admin):
    contenido = client_admin.get(URL_PANEL).content.decode()

    assert reverse("accounts:usuario_lista") in contenido
    assert reverse("accounts:cliente_lista") in contenido
    # Los módulos que todavía no existen se muestran, pero no enlazan.
    assert "Próximamente" in contenido
    assert "Reportes" in contenido


def test_el_menu_marca_la_pantalla_en_la_que_se_esta(client_admin):
    contenido = client_admin.get(reverse("accounts:usuario_lista")).content.decode()

    assert "menu-enlace--actual" in contenido
