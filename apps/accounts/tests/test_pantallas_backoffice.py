"""Chequeos de las pantallas del Módulo 13 que no son de lógica de negocio."""

import pytest

from apps.accounts.tests.helpers_usuarios import URL_ALTA, URL_LISTA, url_baja, url_edicion

pytestmark = pytest.mark.django_db


def urls_de_backoffice(usuario):
    return [URL_LISTA, URL_ALTA, url_edicion(usuario), url_baja(usuario)]


def test_ninguna_pantalla_filtra_comentarios_del_template(client_admin, cajero):
    """`{# ... #}` solo comenta una línea: si ocupa más, Django lo imprime.

    Es un error fácil de reintroducir y que solo se ve abriendo la pantalla,
    así que queda cubierto acá.
    """
    for url in urls_de_backoffice(cajero):
        contenido = client_admin.get(url).content.decode()
        assert "{#" not in contenido, f"Hay un comentario sin cerrar en {url}"
        assert "{%" not in contenido, f"Hay una etiqueta sin interpretar en {url}"
