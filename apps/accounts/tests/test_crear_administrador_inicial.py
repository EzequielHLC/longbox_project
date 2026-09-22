"""El comando de consola que crea la primera cuenta Administrador.

Es una tarea de consola, fuera del modelo de casos de uso: ocupa el lugar que
tenía `createsuperuser` antes de que se retirara el admin de Django. Lo que estas
pruebas cuidan son las dos reglas que lo justifican —no crea un superusuario, y
no corre dos veces— y la tercera que lo hace auditable.
"""

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError
from django.urls import reverse

from apps.accounts.models import Usuario
from apps.accounts.tests.factories import UsuarioFactory
from apps.core.models import RegistroAuditoria

pytestmark = pytest.mark.django_db

DATOS = {
    "email": "primera@longbox.test",
    "nombre": "Ana Pérez",
    "password": "ClaveInicialSegura9",
}


def crear(**cambios):
    call_command("crear_administrador_inicial", **{**DATOS, **cambios})


def test_crea_una_cuenta_administrador_activa():
    crear()

    usuario = Usuario.objects.get(email=DATOS["email"])
    assert usuario.rol == Usuario.ADMINISTRADOR
    assert usuario.estado == Usuario.ACTIVO
    assert usuario.check_password(DATOS["password"])


def test_la_cuenta_no_es_un_superusuario():
    """La regla que sacó al admin de Django: no existe ninguna cuenta fuera de los tres roles."""
    crear()

    usuario = Usuario.objects.get(email=DATOS["email"])
    assert usuario.is_superuser is False
    assert usuario.is_staff is False


def test_el_nombre_queda_partido_como_lo_guarda_django():
    crear()

    usuario = Usuario.objects.get(email=DATOS["email"])
    assert usuario.get_full_name() == "Ana Pérez"


def test_queda_en_el_registro_de_auditoria_y_sin_actor():
    """Es la única cuenta del sistema que nace sin que otra cuenta la haya creado."""
    crear()

    registro = RegistroAuditoria.objects.get(accion=RegistroAuditoria.ALTA_ADMINISTRADOR_INICIAL)
    assert registro.actor is None
    assert registro.objetivo == Usuario.objects.get(email=DATOS["email"])


def test_no_corre_si_ya_hay_un_administrador_activo():
    UsuarioFactory(rol=Usuario.ADMINISTRADOR, estado=Usuario.ACTIVO)
    cuentas_antes = Usuario.objects.count()

    with pytest.raises(CommandError):
        crear()

    assert Usuario.objects.count() == cuentas_antes


def test_si_el_unico_administrador_esta_de_baja_el_comando_si_corre():
    """La condición es que no haya ninguno **activo**: un sistema con el único Administrador
    dado de baja no tiene quién lo administre, que es justo el caso que este comando resuelve."""
    UsuarioFactory(rol=Usuario.ADMINISTRADOR, estado=Usuario.INACTIVO)

    crear()

    assert Usuario.objects.filter(
        email=DATOS["email"], rol=Usuario.ADMINISTRADOR, estado=Usuario.ACTIVO
    ).exists()


def test_un_cajero_activo_no_cuenta_como_administrador():
    UsuarioFactory(rol=Usuario.CAJERO, estado=Usuario.ACTIVO)

    crear()

    assert Usuario.objects.filter(email=DATOS["email"]).exists()


def test_un_correo_ya_registrado_se_rechaza():
    """I-10: el correo identifica una sola cuenta en cualquier estado."""
    UsuarioFactory(rol=Usuario.CAJERO, email=DATOS["email"], estado=Usuario.INACTIVO)

    with pytest.raises(CommandError):
        crear()


def test_una_contrasena_debil_se_rechaza_como_en_cualquier_otro_camino():
    with pytest.raises(CommandError):
        crear(password="12345")

    assert not Usuario.objects.filter(email=DATOS["email"]).exists()


def test_un_nombre_que_no_es_un_nombre_se_rechaza():
    with pytest.raises(CommandError):
        crear(nombre="A1")

    assert not Usuario.objects.filter(email=DATOS["email"]).exists()


def test_un_correo_sin_arroba_se_rechaza():
    with pytest.raises(CommandError):
        crear(email="no-es-un-correo")


def test_la_cuenta_creada_puede_iniciar_sesion(client):
    """La prueba de que sirve para algo: es el arranque del sistema."""
    crear()

    client.post(
        reverse("accounts:login"),
        {"username": DATOS["email"], "password": DATOS["password"]},
    )

    assert "_auth_user_id" in client.session
