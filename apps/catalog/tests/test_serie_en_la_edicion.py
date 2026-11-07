"""B-01-024: la edición de un tomo ofrece los datos de su serie, como el borrador.

La serie son los **otros** tomos: el que se edita no se cuenta, o un tomo solo se
ofrecería sus propios datos.
"""

import json

import pytest
from django.urls import reverse

from apps.catalog import services
from apps.catalog.tests.factories import EditorialFactory, EtiquetaFactory, ProductoFactory

pytestmark = pytest.mark.django_db


@pytest.fixture
def ivrea():
    return EditorialFactory(nombre="Ivrea")


def editar(producto):
    return reverse("catalog:producto_editar", args=[producto.pk])


def test_la_serie_no_cuenta_el_tomo_que_se_edita(ivrea):
    uno = ProductoFactory(titulo="Berserk", volumen=1, editorial=ivrea, autor="Miura")

    assert services.serie_de("Berserk", ivrea, excluir=uno.pk) is None
    dos = ProductoFactory(titulo="Berserk", volumen=2, editorial=ivrea)
    serie = services.serie_de("berserk", ivrea, excluir=dos.pk)
    assert serie.tomos == 1 and serie.autor == "Miura"


def test_la_edición_ofrece_los_datos_de_los_otros_tomos(client_admin, ivrea):
    adultos = EtiquetaFactory(nombre="Seinen")
    uno = ProductoFactory(
        titulo="Berserk",
        volumen=1,
        editorial=ivrea,
        autor="Kentaro Miura",
        descripcion="Guts, el espadachín negro.",
        solo_adultos=True,
    )
    uno.etiquetas.add(adultos)
    dos = ProductoFactory(titulo="Berserk", volumen=2, editorial=ivrea, autor="")

    respuesta = client_admin.get(editar(dos))

    html = respuesta.content.decode()
    assert "Datos de la serie" in html and "Usar los datos de la serie" in html
    datos = respuesta.context["serie_datos"]
    assert datos == {
        "autor": "Kentaro Miura",
        "sinopsis": "Guts, el espadachín negro.",
        "solo_adultos": True,
        "etiquetas": [adultos.pk],
    }
    assert json.dumps(datos["autor"]) in html


def test_un_tomo_solo_no_ofrece_serie(client_admin, ivrea):
    solo = ProductoFactory(titulo="Akira", volumen=1, editorial=ivrea, autor="Otomo")

    respuesta = client_admin.get(editar(solo))

    assert respuesta.context["serie"] is None
    assert "Datos de la serie" not in respuesta.content.decode()


def test_otra_editorial_no_es_la_misma_serie(client_admin, ivrea):
    ProductoFactory(titulo="Berserk", volumen=1, editorial=EditorialFactory(nombre="Panini"))
    dos = ProductoFactory(titulo="Berserk", volumen=2, editorial=ivrea)

    assert client_admin.get(editar(dos)).context["serie"] is None


def test_lo_no_editorial_no_tiene_serie(client_admin):
    from apps.catalog.tests.factories import ProductoNoEditorialFactory

    figura = ProductoNoEditorialFactory()

    assert "serie" not in client_admin.get(editar(figura)).context
