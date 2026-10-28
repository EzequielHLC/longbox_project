"""La capa de carga entre pantallas (plan 00 de tope de reservas y errores, C).

El comportamiento del guion —qué clics la activan y cuáles no, y el salvavidas
de 12 segundos— se verificó en Chrome sin interfaz con un arnés que dispara cada
caso (ver `docs/ESTADO.md`). Acá, lo que se puede afirmar desde el servidor: que
el panel y la tienda la cargan, y que la pantalla de error no.
"""

import pytest
from django.urls import reverse

from apps.accounts.tests.factories import UsuarioFactory

pytestmark = pytest.mark.django_db

CAPA = 'id="capa-carga"'


def test_el_panel_tiene_la_capa(client):
    client.force_login(UsuarioFactory(rol="administrador"))

    assert CAPA in client.get(reverse("core:panel")).content.decode()


def test_la_tienda_tambien_la_tiene(client):
    """Antes estaba sólo en el panel."""
    assert CAPA in client.get(reverse("core:tienda")).content.decode()


def test_la_capa_no_se_activa_con_los_clics_que_abren_otra_pestana(client):
    contenido = client.get(reverse("core:tienda")).content.decode()

    for filtro in ("evento.ctrlKey", "evento.metaKey", "evento.shiftKey", "evento.button !== 0"):
        assert filtro in contenido
    assert "SALVAVIDAS" in contenido


def test_la_pantalla_de_error_no_carga_la_capa(client):
    assert CAPA not in client.get("/esto-no-existe/").content.decode()
