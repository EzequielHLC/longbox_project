"""Consulta de cuentas de Cliente desde el backoffice (solo lectura)."""

import pytest
from django.urls import reverse

from apps.accounts.models import Usuario
from apps.accounts.tests.factories import UsuarioFactory

pytestmark = pytest.mark.django_db

URL_CLIENTES = reverse("accounts:cliente_lista")


@pytest.fixture
def clientela(db):
    """Tres clientes de distintas provincias, más una cuenta de personal."""
    UsuarioFactory(
        email="lucia@correo.test",
        first_name="Lucía",
        last_name="Gómez",
        rol=Usuario.CLIENTE,
        provincia="Misiones",
        telefono_area="376",
        telefono_numero="4112233",
    )
    UsuarioFactory(
        email="martin@correo.test",
        first_name="Martín",
        rol=Usuario.CLIENTE,
        provincia="Corrientes",
    )
    UsuarioFactory(
        email="baja@correo.test",
        first_name="Rosa",
        rol=Usuario.CLIENTE,
        estado=Usuario.INACTIVO,
        provincia="Misiones",
    )
    UsuarioFactory(email="cajero@longbox.test", rol=Usuario.CAJERO)


def test_la_pantalla_lista_solo_cuentas_de_cliente(client_admin, clientela):
    contenido = client_admin.get(URL_CLIENTES).content.decode()

    assert "lucia@correo.test" in contenido
    assert "martin@correo.test" in contenido
    # Las cuentas de personal tienen su propia pantalla.
    assert "cajero@longbox.test" not in contenido


def test_la_tabla_no_ofrece_acciones_sobre_las_cuentas(client_admin, clientela):
    """Es de consulta: dar de baja un Cliente es el CU-49, todavía sin documentar.

    Se mira el fragmento de la tabla y no la pantalla entera: la cáscara del
    backoffice trae las clases de los botones definidas en su CSS, así que
    buscarlas en el HTML completo daría un falso positivo.
    """
    tabla = client_admin.get(URL_CLIENTES, {"parcial": "1"}).content.decode()

    assert "boton-menor" not in tabla
    assert "<a " not in tabla


def test_muestra_el_telefono_armado_y_la_direccion(client_admin):
    UsuarioFactory(
        email="lucia@correo.test",
        rol=Usuario.CLIENTE,
        telefono_area="376",
        telefono_numero="4112233",
        direccion="Av. Mitre 1234",
        localidad="Posadas",
        codigo_postal="N3300ABC",
        provincia="Misiones",
    )

    contenido = client_admin.get(URL_CLIENTES).content.decode()

    assert "+54 376 4112233" in contenido
    assert "Av. Mitre 1234, N3300ABC Posadas, Misiones" in contenido


def test_avisa_cuando_una_cuenta_no_tiene_consentimiento_registrado(client_admin, clientela):
    """Una cuenta sin fecha de aceptación no salió del registro público."""
    contenido = client_admin.get(URL_CLIENTES).content.decode()

    assert "Sin registrar" in contenido


@pytest.mark.parametrize("termino", ["lucia", "Gómez", "4112233"])
def test_el_buscador_encuentra_por_nombre_correo_y_telefono(client_admin, clientela, termino):
    contenido = client_admin.get(URL_CLIENTES, {"q": termino}).content.decode()

    assert "lucia@correo.test" in contenido
    assert "martin@correo.test" not in contenido


def test_el_filtro_por_provincia(client_admin, clientela):
    contenido = client_admin.get(URL_CLIENTES, {"provincia": "Corrientes"}).content.decode()

    assert "martin@correo.test" in contenido
    assert "lucia@correo.test" not in contenido


def test_el_filtro_por_estado(client_admin, clientela):
    contenido = client_admin.get(URL_CLIENTES, {"estado": "inactivo"}).content.decode()

    assert "baja@correo.test" in contenido
    assert "lucia@correo.test" not in contenido


def test_una_provincia_inventada_en_la_url_se_ignora(client_admin, clientela):
    """Un valor cualquiera en la query string no filtra de más ni rompe."""
    respuesta = client_admin.get(URL_CLIENTES, {"provincia": "Tokio"})

    assert respuesta.status_code == 200
    assert respuesta.context["clientes"].count() == 3


def test_el_pedido_parcial_devuelve_solo_la_tabla(client_admin, clientela):
    contenido = client_admin.get(URL_CLIENTES, {"parcial": "1"}).content.decode()

    assert "lucia@correo.test" in contenido
    # El fragmento no trae la cáscara de la pantalla.
    assert "<html" not in contenido


@pytest.mark.parametrize("rol_sin_permiso", ["cliente", "cajero"])
def test_solo_el_administrador_consulta_los_clientes(client, rol_sin_permiso):
    """RNF-03: el control es del servidor, no de que el menú no muestre el enlace."""
    UsuarioFactory(email="lucia@correo.test", rol=Usuario.CLIENTE)
    client.force_login(UsuarioFactory(rol=rol_sin_permiso))

    respuesta = client.get(URL_CLIENTES)

    assert respuesta.status_code == 403
    assert "lucia@correo.test" not in respuesta.content.decode()


def test_sin_sesion_redirige_al_login(client):
    respuesta = client.get(URL_CLIENTES)

    assert respuesta.status_code == 302
    assert reverse("accounts:login") in respuesta.url
