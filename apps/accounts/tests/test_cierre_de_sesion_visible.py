"""Todo rol con sesión tiene a la vista cómo cerrarla (CU-AUT-FIN).

Existe por un defecto concreto: la cáscara pública no ofrecía cerrar sesión, así
que el Cliente no tenía forma de salir, y en el teléfono el Cajero no lo
encontraba en el menú, que es lo que se abre en pantalla angosta.

Cerrar sesión es un POST: lo que se busca es el formulario, no un enlace.
"""

import re

import pytest
from django.urls import reverse

URL_LOGOUT = reverse("accounts:logout")
FORMULARIO_DE_SALIDA = re.compile(
    rf'<form method="post" action="{re.escape(URL_LOGOUT)}"[^>]*>.*?Cerrar sesión.*?</form>', re.S
)

pytestmark = pytest.mark.django_db


def _menu(html):
    inicio = html.index('<aside id="menu-lateral"')
    return html[inicio : html.index("</aside>", inicio)]


def test_el_cliente_puede_cerrar_sesion_desde_la_tienda(client, cliente):
    client.force_login(cliente)

    html = client.get(reverse("core:tienda")).content.decode()

    assert FORMULARIO_DE_SALIDA.search(html)
    assert cliente.email in html


def test_sin_sesion_la_tienda_ofrece_ingresar_y_no_salir(client):
    html = client.get(reverse("core:tienda"), follow=True).content.decode()

    assert not FORMULARIO_DE_SALIDA.search(html)


def test_el_cajero_encuentra_cerrar_sesion_en_el_menu(client, cajero):
    client.force_login(cajero)

    html = client.get(reverse("core:mostrador")).content.decode()

    assert FORMULARIO_DE_SALIDA.search(_menu(html))


def test_el_menu_del_cajero_no_ofrece_el_panel_del_administrador(client, cajero):
    """El Panel le respondería 403: el menú no ofrece caminos que no existen."""
    client.force_login(cajero)

    html = client.get(reverse("core:mostrador")).content.decode()

    assert f'href="{reverse("core:panel")}"' not in html
    assert f'href="{reverse("core:mostrador")}"' in _menu(html)
    assert f'href="{reverse("catalog:producto_lista")}"' in _menu(html)


def test_el_cajero_puede_abrir_el_inventario_que_le_ofrece_el_menu(client, cajero):
    client.force_login(cajero)

    assert client.get(reverse("catalog:producto_lista")).status_code == 200


def test_el_administrador_tambien_tiene_la_salida_en_el_menu(client_admin):
    html = client_admin.get(reverse("core:panel")).content.decode()

    assert FORMULARIO_DE_SALIDA.search(_menu(html))
