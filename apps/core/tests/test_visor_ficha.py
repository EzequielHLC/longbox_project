"""El visor de imágenes de la ficha pública (plan 00 de interfaz, cuarta parte, D)."""

import pytest
from django.core.files.base import ContentFile
from django.urls import reverse

from apps.catalog.tests.factories import ProductoFactory
from apps.catalog.tests.test_galeria_edicion import adicional

pytestmark = pytest.mark.django_db


@pytest.fixture
def media(settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path
    return tmp_path


def ficha(client, producto):
    return client.get(reverse("core:tienda_producto", args=[producto.pk])).content.decode()


def test_la_portada_y_las_adicionales_son_miniaturas_del_visor(client, media):
    producto = ProductoFactory(stock=2)
    producto.portada.save("tapa.webp", ContentFile(b"tapa"), save=True)
    adicional(producto, "contratapa", 0)
    adicional(producto, "interior", 1)

    contenido = ficha(client, producto)

    assert (
        contenido.count("data-visor-miniatura>")
        + contenido.count('data-visor-miniatura aria-current="true">')
        == 3
    )
    assert "data-visor-dialogo" in contenido
    assert 'aria-label="Ampliar la imagen"' in contenido


def test_sin_adicionales_no_hay_miniaturas_pero_se_amplia(client, media):
    producto = ProductoFactory(stock=2)
    producto.portada.save("tapa.webp", ContentFile(b"tapa"), save=True)

    contenido = ficha(client, producto)

    assert "data-visor-miniatura>" not in contenido
    assert "data-visor-dialogo" in contenido


def test_sin_portada_queda_la_tapa_dibujada_y_no_hay_ampliacion(client):
    producto = ProductoFactory(stock=2)

    contenido = ficha(client, producto)

    assert "portada-vacia--tapa" in contenido
    assert "data-visor-dialogo" not in contenido


def test_la_ficha_del_backoffice_usa_el_mismo_visor(client_admin, media):
    producto = ProductoFactory(stock=2)
    producto.portada.save("tapa.webp", ContentFile(b"tapa"), save=True)
    adicional(producto, "contratapa", 0)

    contenido = client_admin.get(
        reverse("catalog:producto_detalle", args=[producto.pk])
    ).content.decode()

    assert "data-visor-dialogo" in contenido
    assert contenido.count("data-visor-miniatura") >= 2


def test_las_hojas_de_estilo_llevan_su_version(client):
    """Sin versión el navegador sigue usando la hoja vieja y la pantalla se ve rota."""
    import re

    contenido = client.get(reverse("core:tienda")).content.decode()

    assert re.search(r'/static/css/longbox\.css\?v=\d+"', contenido)
    assert re.search(r'/static/css/tokens\.css\?v=\d+"', contenido)
