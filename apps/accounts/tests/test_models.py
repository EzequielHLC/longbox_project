"""El modelo de usuario: las garantías que la base sostiene por su cuenta.

Se prueban acá y no en los tests de las pantallas porque son invariantes del
modelo: valen para el alta desde el backoffice, para el registro de un cliente y
para cualquier `create()` que se escriba mañana en un comando.
"""

import pytest
from django.db import IntegrityError

from apps.accounts.models import Usuario

pytestmark = pytest.mark.django_db


def test_crear_usuario_con_rol_por_defecto():
    usuario = Usuario.objects.create_user(
        username="test", email="test@longbox.test", password="clave123"
    )
    assert usuario.rol == "cliente"


def test_la_contrasena_se_guarda_hasheada():
    usuario = Usuario.objects.create_user(
        username="hash", email="hash@longbox.test", password="clave123"
    )
    assert usuario.password != "clave123"
    assert usuario.check_password("clave123")


def test_el_correo_se_normaliza_a_minusculas():
    usuario = Usuario.objects.create_user(
        username="mayus", email="Mayus@Longbox.Test", password="clave123"
    )
    assert usuario.email == "mayus@longbox.test"


def test_no_permite_dos_cuentas_con_el_mismo_correo():
    Usuario.objects.create_user(username="uno", email="repe@longbox.test", password="clave123")

    with pytest.raises(IntegrityError):
        Usuario.objects.create_user(username="dos", email="repe@longbox.test", password="clave123")
