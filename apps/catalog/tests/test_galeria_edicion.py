"""Las imágenes en la edición de producto (plan 00 de interfaz, cuarta parte, C).

«Usar como portada» intercambia (decisión del responsable): ninguna imagen se
pierde sin que alguien la quite. El orden viaja en un campo que arma el guion;
sin él, queda el que estaba.
"""

import pytest
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.urls import reverse

from apps.catalog.models import ImagenProducto
from apps.catalog.tests.factories import ProductoFactory
from apps.catalog.tests.test_edicion_producto import datos_editoriales
from apps.core.models import RegistroAuditoria
from apps.core.tests.test_contratos_17_contenido import imagen

pytestmark = pytest.mark.django_db


@pytest.fixture
def media(settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path
    return tmp_path


def url(producto):
    return reverse("catalog:producto_editar", args=[producto.pk])


def adicional(producto, nombre, posicion):
    imagen_producto = ImagenProducto(producto=producto, posicion=posicion)
    imagen_producto.imagen.save(f"{nombre}.webp", ContentFile(b"webp"), save=False)
    imagen_producto.save()
    return imagen_producto


@pytest.fixture
def con_galeria(media):
    producto = ProductoFactory(titulo="Berserk")
    producto.portada.save("tapa.webp", ContentFile(b"tapa"), save=True)
    primera = adicional(producto, "contratapa", 0)
    segunda = adicional(producto, "interior", 1)
    return producto, primera, segunda


def test_usar_como_portada_intercambia_y_no_borra_ningun_archivo(client_admin, con_galeria):
    producto, primera, segunda = con_galeria
    tapa, interior = producto.portada.name, segunda.imagen.name

    client_admin.post(url(producto), datos_editoriales(producto, nueva_portada=segunda.pk))

    producto.refresh_from_db()
    segunda.refresh_from_db()
    assert producto.portada.name == interior
    assert segunda.imagen.name == tapa
    assert default_storage.exists(tapa)
    assert default_storage.exists(interior)
    detalle = RegistroAuditoria.objects.get(accion=RegistroAuditoria.MODIFICACION_PRODUCTO).detalle
    assert "portada" in detalle


def test_sin_portada_la_elegida_sale_de_la_galeria(client_admin, media):
    producto = ProductoFactory()
    unica = adicional(producto, "unica", 0)
    nombre = unica.imagen.name

    client_admin.post(url(producto), datos_editoriales(producto, nueva_portada=unica.pk))

    producto.refresh_from_db()
    assert producto.portada.name == nombre
    assert not producto.imagenes.exists()
    assert default_storage.exists(nombre)


def test_el_orden_que_arma_el_guion_se_guarda(client_admin, con_galeria):
    producto, primera, segunda = con_galeria

    client_admin.post(
        url(producto), datos_editoriales(producto, orden_imagenes=f"{segunda.pk},{primera.pk}")
    )

    assert list(producto.imagenes.order_by("posicion").values_list("pk", flat=True)) == [
        segunda.pk,
        primera.pk,
    ]
    detalle = RegistroAuditoria.objects.get(accion=RegistroAuditoria.MODIFICACION_PRODUCTO).detalle
    assert "nuevo orden" in detalle


def test_sin_orden_queda_el_que_estaba(client_admin, con_galeria):
    producto, primera, segunda = con_galeria

    client_admin.post(url(producto), datos_editoriales(producto, titulo="Berserk Deluxe"))

    assert list(producto.imagenes.order_by("posicion").values_list("pk", flat=True)) == [
        primera.pk,
        segunda.pk,
    ]


def test_quitar_y_reordenar_en_el_mismo_envio(client_admin, con_galeria):
    producto, primera, segunda = con_galeria
    tercera = adicional(producto, "detalle", 2)

    client_admin.post(
        url(producto),
        datos_editoriales(
            producto,
            orden_imagenes=f"{tercera.pk},{primera.pk},{segunda.pk}",
            quitar_imagenes=[primera.pk],
        ),
    )

    assert list(producto.imagenes.order_by("posicion").values_list("pk", "posicion")) == [
        (tercera.pk, 0),
        (segunda.pk, 1),
    ]


def test_no_se_usa_como_portada_una_imagen_que_se_quita(client_admin, con_galeria):
    producto, primera, _ = con_galeria
    tapa = producto.portada.name

    respuesta = client_admin.post(
        url(producto),
        datos_editoriales(producto, nueva_portada=primera.pk, quitar_imagenes=[primera.pk]),
    )

    producto.refresh_from_db()
    assert respuesta.status_code == 200
    assert respuesta.context["form"].errors["nueva_portada"]
    assert producto.portada.name == tapa


def test_no_se_sube_una_portada_y_se_elige_otra_a_la_vez(client_admin, con_galeria):
    producto, primera, _ = con_galeria

    respuesta = client_admin.post(
        url(producto),
        datos_editoriales(producto, nueva_portada=primera.pk, portada=imagen("nueva.png")),
    )

    assert respuesta.status_code == 200
    assert "Elegí una sola" in respuesta.content.decode()


def test_la_pantalla_ofrece_ordenar_usar_como_portada_y_quitar(client_admin, con_galeria):
    producto, primera, _ = con_galeria

    contenido = client_admin.get(url(producto)).content.decode()

    assert "data-galeria" in contenido
    assert f'data-imagen="{primera.pk}"' in contenido
    assert 'name="nueva_portada"' in contenido
    assert 'name="quitar_imagenes"' in contenido
    assert 'name="orden_imagenes"' in contenido
    assert "Portada actual" in contenido


def test_la_portada_se_quita_desde_su_casilla(client_admin, con_galeria):
    producto, _, _ = con_galeria
    contenido = client_admin.get(url(producto)).content.decode()
    assert 'name="portada-clear"' in contenido
    assert "data-portada-archivo" in contenido

    client_admin.post(url(producto), datos_editoriales(producto, **{"portada-clear": "on"}))

    producto.refresh_from_db()
    assert not producto.portada
