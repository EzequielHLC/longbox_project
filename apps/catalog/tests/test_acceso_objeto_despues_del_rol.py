"""Revisión integral, R-09: el rol se verifica antes de buscar el objeto.

Si la pantalla busca el registro antes de mirar el rol, el rol equivocado recibe
404 cuando no existe y 403 cuando existe: la respuesta revela qué claves hay.
Por la dirección real, con un Cajero y con un Cliente.
"""

import pytest
from django.urls import reverse

from apps.accounts.tests.factories import UsuarioFactory
from apps.catalog.tests.factories import GrupoEtiquetaFactory, PrecioReferenciaFactory

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize("rol", ["cajero", "cliente"])
@pytest.mark.parametrize(
    ("ruta", "fabrica"),
    [
        ("catalog:precio_editar", PrecioReferenciaFactory),
        ("catalog:grupo_etiquetas", GrupoEtiquetaFactory),
    ],
)
def test_el_rol_equivocado_recibe_403_exista_o_no_el_registro(client, rol, ruta, fabrica):
    client.force_login(UsuarioFactory(rol=rol))
    existe = fabrica()

    respuestas = [
        client.get(reverse(ruta, args=[existe.pk])),
        client.get(reverse(ruta, args=[existe.pk + 1000])),
        client.post(reverse(ruta, args=[existe.pk + 1000]), {}),
    ]

    assert [r.status_code for r in respuestas] == [403, 403, 403]


@pytest.mark.parametrize("ruta", ["catalog:precio_editar", "catalog:grupo_etiquetas"])
def test_el_administrador_sigue_recibiendo_404_si_no_existe(client_admin, ruta):
    assert client_admin.get(reverse(ruta, args=[999999])).status_code == 404
