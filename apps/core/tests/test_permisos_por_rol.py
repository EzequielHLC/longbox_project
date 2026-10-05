"""RNF-03: el control de acceso por rol se valida siempre del lado del servidor."""

import pytest
from django.urls import reverse

from apps.accounts.tests.factories import UsuarioFactory

URL_LOGIN = reverse("accounts:login")

# La tienda es del cliente, pero desde que se resolvió C-20 (2026-10-05) la
# portada también la ve cualquiera: lo que el personal no puede abrir es el
# carrito, y lo que un invitado no puede abrir es el mostrador.
VISTAS_POR_ROL = {
    "cliente": reverse("core:tienda"),
    "cajero": reverse("core:mostrador"),
    "administrador": reverse("core:panel"),
}

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize("rol", list(VISTAS_POR_ROL))
def test_cada_rol_entra_a_su_propia_seccion(client, rol):
    client.force_login(UsuarioFactory(rol=rol))

    assert client.get(VISTAS_POR_ROL[rol]).status_code == 200


@pytest.mark.parametrize(
    ("rol", "url_ajena"),
    [
        ("cliente", VISTAS_POR_ROL["administrador"]),
        ("cliente", VISTAS_POR_ROL["cajero"]),
        ("cajero", VISTAS_POR_ROL["administrador"]),
        ("administrador", reverse("tienda:carrito")),
    ],
)
def test_un_rol_que_no_corresponde_recibe_403(client, rol, url_ajena):
    """Un request directo con el rol equivocado corta en 403, sin datos parciales."""
    client.force_login(UsuarioFactory(rol=rol))

    respuesta = client.get(url_ajena)

    assert respuesta.status_code == 403


@pytest.mark.parametrize("url", [VISTAS_POR_ROL["cajero"], VISTAS_POR_ROL["administrador"]])
def test_sin_sesion_redirige_al_login(client, url):
    respuesta = client.get(url)

    assert respuesta.status_code == 302
    assert respuesta.url.startswith(URL_LOGIN)
