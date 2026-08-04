import pytest

from apps.accounts.models import Usuario


@pytest.mark.django_db
def test_crear_usuario_con_rol_por_defecto():
    usuario = Usuario.objects.create_user(username="test", password="clave123")
    assert usuario.rol == "cliente"
