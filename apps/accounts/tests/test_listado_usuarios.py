"""Buscador y filtros de la tabla de usuarios del sistema."""

import re

import pytest

from apps.accounts.models import Usuario
from apps.accounts.tests.factories import UsuarioFactory
from apps.accounts.tests.helpers_usuarios import URL_LISTA

pytestmark = pytest.mark.django_db


@pytest.fixture
def personal(db):
    return {
        "cajera_activa": UsuarioFactory(
            rol="cajero", first_name="Ana", last_name="Pérez", email="ana@longbox.test"
        ),
        "cajero_inactivo": UsuarioFactory(
            rol="cajero",
            first_name="Bruno",
            last_name="Gómez",
            email="bruno@longbox.test",
            estado=Usuario.INACTIVO,
        ),
        "admin_pendiente": UsuarioFactory(
            rol="administrador",
            first_name="Carla",
            last_name="Díaz",
            email="carla@longbox.test",
            estado=Usuario.PENDIENTE_ACTIVACION,
        ),
    }


def filas_de_la_tabla(respuesta):
    cuerpo = respuesta.content.decode()
    return re.findall(r"<tr[^>]*>.*?</tr>", cuerpo[cuerpo.index("<tbody") :], re.S)


def correos_listados(respuesta):
    contenido = respuesta.content.decode()
    return {
        correo
        for correo in ("ana@longbox.test", "bruno@longbox.test", "carla@longbox.test")
        if correo in contenido
    }


def test_la_busqueda_filtra_por_nombre(client_admin, personal):
    respuesta = client_admin.get(URL_LISTA, {"q": "Bruno"})

    assert correos_listados(respuesta) == {"bruno@longbox.test"}


def test_la_busqueda_filtra_por_correo(client_admin, personal):
    respuesta = client_admin.get(URL_LISTA, {"q": "carla@"})

    assert correos_listados(respuesta) == {"carla@longbox.test"}


def test_el_filtro_de_rol_deja_solo_ese_rol(client_admin, personal):
    respuesta = client_admin.get(URL_LISTA, {"rol": "administrador"})

    assert correos_listados(respuesta) == {"carla@longbox.test"}


def test_el_filtro_de_estado_deja_solo_ese_estado(client_admin, personal):
    respuesta = client_admin.get(URL_LISTA, {"estado": Usuario.INACTIVO})

    assert correos_listados(respuesta) == {"bruno@longbox.test"}


def test_los_filtros_se_combinan_con_la_busqueda(client_admin, personal):
    respuesta = client_admin.get(URL_LISTA, {"q": "@longbox.test", "rol": "cajero"})

    assert correos_listados(respuesta) == {"ana@longbox.test", "bruno@longbox.test"}


@pytest.mark.parametrize(
    ("filtro", "valor"),
    [("rol", "cliente"), ("rol", "inventado"), ("estado", "cualquier-cosa")],
)
def test_un_filtro_con_un_valor_invalido_se_ignora(client_admin, personal, filtro, valor):
    """Un parámetro pisado a mano en la URL no filtra de más ni rompe la vista."""
    respuesta = client_admin.get(URL_LISTA, {filtro: valor})

    assert respuesta.status_code == 200
    assert len(correos_listados(respuesta)) == 3


def test_sin_resultados_se_explica_en_la_voz_del_sistema(client_admin, personal):
    respuesta = client_admin.get(URL_LISTA, {"q": "nadie-con-este-nombre"})

    assert "Ningún usuario coincide con los criterios de búsqueda." in respuesta.content.decode()


def test_se_informa_cuantos_resultados_hay(client_admin, personal):
    completo = client_admin.get(URL_LISTA)
    filtrado = client_admin.get(URL_LISTA, {"rol": "cajero"})

    # El Administrador es el que ejecuta la acción y también figura en la tabla.
    assert "4 usuarios" in completo.content.decode()
    assert "2 usuarios" in filtrado.content.decode()


def test_la_fila_del_propio_usuario_esta_marcada(client_admin, administrador, personal):
    """El Administrador se ve a sí mismo en la tabla: conviene que lo sepa."""
    filas = filas_de_la_tabla(client_admin.get(URL_LISTA))

    marcadas = [fila for fila in filas if ">propia<" in fila]
    assert len(marcadas) == 1
    assert administrador.email in marcadas[0]


def test_los_filtros_siguen_siendo_selects_de_verdad(client_admin):
    """El desplegable propio es una mejora sobre el `select`, no un reemplazo.

    Si el HTML dejara de traer los `select`, la pantalla dejaría de funcionar
    sin JavaScript y los filtros no viajarían en el envío del formulario.
    """
    contenido = client_admin.get(URL_LISTA).content.decode()

    assert '<select id="rol" name="rol"' in contenido
    assert '<select id="estado" name="estado"' in contenido


def test_el_pedido_parcial_devuelve_solo_la_tabla(client_admin, personal):
    """Es lo que consume el buscador en vivo: el fragmento, no la pantalla."""
    respuesta = client_admin.get(URL_LISTA, {"q": "Ana", "parcial": "1"})

    contenido = respuesta.content.decode()
    assert "ana@longbox.test" in contenido
    assert "bruno@longbox.test" not in contenido
    # Ni la cáscara ni el formulario de filtros viajan en la respuesta parcial.
    assert "<html" not in contenido
    assert "filtros-usuarios" not in contenido


def test_el_pedido_parcial_tambien_exige_ser_administrador(client, cajero):
    client.force_login(cajero)

    assert client.get(URL_LISTA, {"parcial": "1"}).status_code == 403
