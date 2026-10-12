"""El código de cliente (B-06-001): seis cifras, único, sólo para cuentas de Cliente."""

import pytest
from django.db import IntegrityError
from django.urls import reverse

from apps.accounts.models import Usuario
from apps.accounts.tests.factories import UsuarioFactory

pytestmark = pytest.mark.django_db


def test_una_cuenta_de_cliente_nace_con_un_codigo_de_seis_cifras():
    cliente = UsuarioFactory(rol=Usuario.CLIENTE)

    assert len(cliente.codigo_cliente) == 6
    assert cliente.codigo_cliente.isdigit()
    assert not cliente.codigo_cliente.startswith("0")


@pytest.mark.parametrize("rol", [Usuario.CAJERO, Usuario.ADMINISTRADOR])
def test_el_personal_no_tiene_codigo_de_cliente(rol):
    assert UsuarioFactory(rol=rol).codigo_cliente is None


def test_el_codigo_no_cambia_al_volver_a_guardar():
    cliente = UsuarioFactory(rol=Usuario.CLIENTE)
    codigo = cliente.codigo_cliente

    cliente.first_name = "Otro"
    cliente.save()

    cliente.refresh_from_db()
    assert cliente.codigo_cliente == codigo


def test_la_base_no_admite_dos_cuentas_con_el_mismo_codigo():
    cliente = UsuarioFactory(rol=Usuario.CLIENTE)

    with pytest.raises(IntegrityError):
        UsuarioFactory(rol=Usuario.CLIENTE, codigo_cliente=cliente.codigo_cliente)


def test_el_cliente_ve_su_codigo_en_mi_cuenta(client):
    cliente = UsuarioFactory(rol=Usuario.CLIENTE)
    client.force_login(cliente)

    contenido = client.get(reverse("cuenta:datos")).content.decode()

    assert cliente.codigo_cliente in contenido


def test_el_administrador_busca_un_cliente_por_su_codigo(client_admin):
    buscado = UsuarioFactory(rol=Usuario.CLIENTE)
    UsuarioFactory(rol=Usuario.CLIENTE)

    respuesta = client_admin.get(reverse("accounts:cliente_lista"), {"q": buscado.codigo_cliente})

    assert list(respuesta.context["clientes"]) == [buscado]
