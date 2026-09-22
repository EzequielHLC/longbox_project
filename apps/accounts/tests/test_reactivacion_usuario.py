"""Reactivación y congelamiento de una cuenta dada de baja.

La describe CU-USR-REA · Reactivar Cuenta de Usuario del Sistema, con CO-124,
CO-199 y CO-122.
"""

import pytest
from django.core import mail
from django.test import Client
from django.urls import reverse

from apps.accounts.forms import MENSAJE_CUENTA_CON_HISTORIAL, MENSAJE_CUENTA_CONGELADA
from apps.accounts.models import Usuario
from apps.accounts.tests.factories import PASSWORD_DE_PRUEBA, UsuarioFactory
from apps.accounts.tests.helpers_usuarios import (
    URL_LISTA,
    datos_de,
    enlace_de_activacion,
    url_baja,
    url_edicion,
)
from apps.core.models import RegistroAuditoria

URL_LOGIN = reverse("accounts:login")

pytestmark = pytest.mark.django_db


def url_reactivar(usuario):
    return reverse("accounts:usuario_reactivar", args=[usuario.pk])


def reactivar(client, usuario, rol=None):
    """CO-124 toma el rol con el que la cuenta vuelve; sin él la operación no está completa."""
    return client.post(url_reactivar(usuario), {"rol": rol or usuario.rol})


@pytest.fixture
def dado_de_baja(client_admin):
    """Un cajero que trabajó (tiene sesión iniciada) y después fue dado de baja."""
    usuario = UsuarioFactory(rol="cajero", first_name="Ana", last_name="Pérez")
    Client().force_login(usuario)  # deja `last_login`: la cuenta se usó
    client_admin.post(url_baja(usuario))
    usuario.refresh_from_db()
    assert usuario.estado == Usuario.INACTIVO
    return usuario


# --------------------------------------------------------------------------
# Reactivación
# --------------------------------------------------------------------------


def test_la_pantalla_pide_confirmacion_explicita(client_admin, dado_de_baja):
    respuesta = client_admin.get(url_reactivar(dado_de_baja))

    assert respuesta.status_code == 200
    assert "Reactivar cuenta" in respuesta.content.decode()
    dado_de_baja.refresh_from_db()
    assert dado_de_baja.estado == Usuario.INACTIVO  # el GET no reactiva nada


def test_reactivar_deja_la_cuenta_pendiente_y_manda_enlace(client_admin, dado_de_baja):
    mail.outbox.clear()

    respuesta = reactivar(client_admin, dado_de_baja)

    assert respuesta.status_code == 302
    dado_de_baja.refresh_from_db()
    assert dado_de_baja.estado == Usuario.PENDIENTE_ACTIVACION
    assert dado_de_baja.is_active is False
    assert len(mail.outbox) == 1
    assert mail.outbox[0].to == [dado_de_baja.email]


def test_reactivar_invalida_la_contrasena_anterior(client_admin, dado_de_baja):
    """El acceso no vuelve con la credencial vieja: hay que elegir una nueva."""
    reactivar(client_admin, dado_de_baja)

    dado_de_baja.refresh_from_db()
    assert dado_de_baja.has_usable_password() is False
    assert dado_de_baja.check_password(PASSWORD_DE_PRUEBA) is False


def test_una_cuenta_reactivada_no_puede_entrar_hasta_usar_el_enlace(client_admin, dado_de_baja):
    mail.outbox.clear()
    reactivar(client_admin, dado_de_baja)

    navegador = Client()
    navegador.post(URL_LOGIN, {"username": dado_de_baja.email, "password": PASSWORD_DE_PRUEBA})
    assert "_auth_user_id" not in navegador.session

    # Con el enlace, elige contraseña nueva y recupera el acceso.
    enlace = enlace_de_activacion(mail.outbox[0])
    formulario = navegador.get(enlace)
    navegador.post(
        formulario.url,
        {"new_password1": "ClaveNuevaDeVuelta9", "new_password2": "ClaveNuevaDeVuelta9"},
    )

    dado_de_baja.refresh_from_db()
    assert dado_de_baja.estado == Usuario.ACTIVO
    navegador.post(URL_LOGIN, {"username": dado_de_baja.email, "password": "ClaveNuevaDeVuelta9"})
    assert navegador.get(reverse("core:mostrador")).status_code == 200


def test_la_cuenta_reactivada_conserva_su_historial(client_admin, dado_de_baja):
    """El historial es de la cuenta y sobrevive a la vuelta.

    El rol no entra acá: no se conserva, se elige (CO-124). Que la reactivación pueda dejarlo
    igual que antes es una decisión de quien reactiva, no una propiedad de la operación.
    """
    registros_previos = RegistroAuditoria.objects.filter(actor=dado_de_baja).count()
    assert registros_previos > 0

    reactivar(client_admin, dado_de_baja)

    assert RegistroAuditoria.objects.filter(actor=dado_de_baja).count() == registros_previos


def test_la_reactivacion_puede_devolver_la_cuenta_con_otro_rol(client_admin, dado_de_baja):
    """CO-124: «u.rol quedó con el valor declarado», no con el que tenía al darse de baja."""
    assert dado_de_baja.rol == Usuario.CAJERO

    reactivar(client_admin, dado_de_baja, rol=Usuario.ADMINISTRADOR)

    dado_de_baja.refresh_from_db()
    assert dado_de_baja.rol == Usuario.ADMINISTRADOR


def test_la_reactivacion_queda_en_auditoria(client_admin, dado_de_baja, administrador):
    reactivar(client_admin, dado_de_baja)

    registro = RegistroAuditoria.objects.get(accion=RegistroAuditoria.REACTIVACION_USUARIO)
    assert registro.actor == administrador
    assert registro.objetivo == dado_de_baja
    assert Usuario.INACTIVO in registro.detalle
    assert Usuario.PENDIENTE_ACTIVACION in registro.detalle


def test_no_se_reactiva_una_cuenta_que_no_esta_de_baja(client_admin, cajero):
    respuesta = client_admin.post(url_reactivar(cajero), {"rol": cajero.rol}, follow=True)

    assert "Solo se puede reactivar una cuenta dada de baja." in respuesta.content.decode()
    cajero.refresh_from_db()
    assert cajero.estado == Usuario.ACTIVO
    assert mail.outbox == []


def test_solo_el_administrador_puede_reactivar(client, cajero, dado_de_baja):
    client.force_login(cajero)

    assert client.get(url_reactivar(dado_de_baja)).status_code == 403
    assert client.post(url_reactivar(dado_de_baja)).status_code == 403
    dado_de_baja.refresh_from_db()
    assert dado_de_baja.estado == Usuario.INACTIVO


# --------------------------------------------------------------------------
# Congelamiento
# --------------------------------------------------------------------------


def test_no_se_puede_abrir_la_edicion_de_una_cuenta_de_baja(client_admin, dado_de_baja):
    respuesta = client_admin.get(url_edicion(dado_de_baja), follow=True)

    assert MENSAJE_CUENTA_CONGELADA in respuesta.content.decode()


def test_un_post_directo_tampoco_modifica_una_cuenta_de_baja(client_admin, dado_de_baja):
    """RNF-03: esconder el botón no es una restricción; el chequeo va en la vista."""
    respuesta = client_admin.post(
        url_edicion(dado_de_baja),
        datos_de(dado_de_baja, email="secuestrada@longbox.test", rol="administrador"),
        follow=True,
    )

    assert MENSAJE_CUENTA_CONGELADA in respuesta.content.decode()
    dado_de_baja.refresh_from_db()
    assert dado_de_baja.email != "secuestrada@longbox.test"
    assert dado_de_baja.rol == "cajero"


def test_la_tabla_ofrece_reactivar_y_no_editar(client_admin, dado_de_baja):
    contenido = client_admin.get(URL_LISTA).content.decode()

    assert url_reactivar(dado_de_baja) in contenido
    assert url_edicion(dado_de_baja) not in contenido


def test_una_cuenta_reactivada_no_se_puede_eliminar(client_admin, dado_de_baja):
    """Quedó Pendiente, pero tiene historial: el borrado físico no corresponde."""
    reactivar(client_admin, dado_de_baja)
    dado_de_baja.refresh_from_db()
    assert dado_de_baja.esta_pendiente_de_activacion

    url_eliminar = reverse("accounts:usuario_eliminar", args=[dado_de_baja.pk])
    respuesta = client_admin.post(url_eliminar, follow=True)

    assert MENSAJE_CUENTA_CON_HISTORIAL in respuesta.content.decode()
    assert Usuario.objects.filter(pk=dado_de_baja.pk).exists()
