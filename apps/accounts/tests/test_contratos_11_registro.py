"""Prueba de contrato de `CO-107 registrarCuentaDeCliente` (CU-CLI-ALT).

El comportamiento de la pantalla —los mensajes, el teléfono, la dirección, la
provincia— está en `test_registro_cliente.py`. Acá, cada postcondición del
contrato por separado, por la dirección real, y las tres excepciones.
"""

import pytest
from django.contrib.auth.hashers import identify_hasher
from django.urls import reverse
from django.utils import timezone

from apps.accounts.models import Usuario
from apps.accounts.tests.factories import UsuarioFactory
from apps.accounts.tests.test_registro_cliente import DATOS_REGISTRO, DIRECCION, TELEFONO
from apps.almacen.models import ArticuloRetenido
from apps.core.models import RegistroAuditoria
from apps.puntos.models import LotePuntos

pytestmark = pytest.mark.django_db

URL_REGISTRO = reverse("accounts:registro_cliente")


def registrar(client, **cambios):
    return client.post(URL_REGISTRO, {**DATOS_REGISTRO, **cambios})


def test_CO107_crea_la_cuenta_de_cliente_activa_con_sus_datos(client):
    antes = timezone.now()

    registrar(client, email="Lucia@Correo.TEST", **TELEFONO, **DIRECCION)

    usuario = Usuario.objects.get()
    assert usuario.rol == Usuario.CLIENTE
    assert usuario.estado == Usuario.ACTIVO
    assert usuario.email == "lucia@correo.test"
    assert usuario.get_full_name() == "Lucía Gómez"
    assert usuario.telefono_numero == TELEFONO["telefono_numero"]
    assert usuario.direccion == DIRECCION["direccion"]
    assert antes <= usuario.fecha_aceptacion_politica <= timezone.now()


def test_CO107_la_credencial_queda_con_hash_y_sal_unica(client):
    """RNF-04: dos cuentas con la misma contraseña no comparten el hash."""
    registrar(client)
    client.logout()
    registrar(client, email="otra@correo.test")

    primera, segunda = Usuario.objects.order_by("pk")
    assert identify_hasher(primera.password)
    assert primera.password != segunda.password
    assert primera.check_password(DATOS_REGISTRO["password1"])


def test_CO107_sin_puntos_ni_stock_almacenado(client):
    registrar(client)

    usuario = Usuario.objects.get()
    assert not LotePuntos.objects.filter(usuario=usuario).exists()
    assert not ArticuloRetenido.objects.filter(usuario=usuario).exists()


def test_CO107_queda_con_sesion_y_con_la_entrada_de_auditoria(client, mailoutbox):
    registrar(client)

    usuario = Usuario.objects.get()
    assert client.session["_auth_user_id"] == str(usuario.pk)
    registro = RegistroAuditoria.objects.get(accion=RegistroAuditoria.REGISTRO_CLIENTE)
    assert registro.actor == usuario
    assert [correo.to for correo in mailoutbox] == [["lucia@correo.test"]]


def test_CO107_E1_un_correo_registrado_en_cualquier_estado_no_duplica(client):
    UsuarioFactory(email="lucia@correo.test", rol=Usuario.CAJERO, estado=Usuario.INACTIVO)

    respuesta = registrar(client, email="LUCIA@correo.test")

    assert respuesta.status_code == 200
    assert reverse("accounts:password_reset") in respuesta.content.decode()
    assert Usuario.objects.filter(email__iexact="lucia@correo.test").count() == 1
    assert not RegistroAuditoria.objects.filter(accion=RegistroAuditoria.REGISTRO_CLIENTE).exists()


@pytest.mark.parametrize(
    "cambios",
    [{"password2": "OtraClave2026"}, {"password1": "corta", "password2": "corta"}],
)
def test_CO107_E2_contrasenas_invalidas_no_crean_y_conservan_lo_escrito(client, cambios):
    respuesta = registrar(client, **cambios)

    assert respuesta.status_code == 200
    assert respuesta.context["form"]["email"].value() == "lucia@correo.test"
    assert not Usuario.objects.exists()


def test_CO107_E3_sin_aceptar_la_politica_se_bloquea(client, mailoutbox):
    respuesta = registrar(client, acepta_politica="")

    assert respuesta.context["form"].errors["acepta_politica"]
    assert not Usuario.objects.exists()
    assert mailoutbox == []
