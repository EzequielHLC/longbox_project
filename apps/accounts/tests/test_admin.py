"""El rol se administra desde el admin de Django hasta que exista el CU-51."""

import pytest
from django.urls import reverse

from apps.accounts.models import Usuario
from apps.accounts.tests.factories import UsuarioFactory

pytestmark = pytest.mark.django_db


@pytest.fixture
def superusuario():
    return Usuario.objects.create_superuser(
        username="root", email="root@longbox.test", password="ClaveSegura123"
    )


def test_el_formulario_de_usuario_incluye_el_campo_rol(client, superusuario):
    client.force_login(superusuario)

    url = reverse("admin:accounts_usuario_change", args=[superusuario.pk])
    respuesta = client.get(url)

    assert respuesta.status_code == 200
    assert 'name="rol"' in respuesta.content.decode()


def test_el_rol_se_puede_cambiar_desde_la_lista(client, superusuario):
    usuario = UsuarioFactory(rol="cliente")
    client.force_login(superusuario)
    url = reverse("admin:accounts_usuario_changelist")

    respuesta = client.post(
        url,
        {
            "form-TOTAL_FORMS": "2",
            "form-INITIAL_FORMS": "2",
            "form-MIN_NUM_FORMS": "0",
            "form-MAX_NUM_FORMS": "1000",
            "form-0-id": str(usuario.pk),
            "form-0-rol": "cajero",
            "form-0-is_active": "on",
            "form-1-id": str(superusuario.pk),
            "form-1-rol": "administrador",
            "form-1-is_active": "on",
            "_save": "Guardar",
        },
    )

    assert respuesta.status_code == 302
    usuario.refresh_from_db()
    assert usuario.rol == "cajero"


def test_el_log_de_auditoria_no_se_puede_editar_ni_borrar_desde_el_admin(client, superusuario):
    client.force_login(superusuario)

    respuesta = client.get(reverse("admin:core_registroauditoria_changelist"))

    assert respuesta.status_code == 200
    modeladmin = respuesta.context["cl"].model_admin
    peticion = respuesta.wsgi_request
    assert not modeladmin.has_add_permission(peticion)
    assert not modeladmin.has_change_permission(peticion)
    assert not modeladmin.has_delete_permission(peticion)
