"""«Agregar un producto» a la propuesta, también por título (B-05-016).

`CO-071` agrega «cualquier producto del catálogo»; antes sólo se encontraba por el
código, el ISBN o el código de barras exactos, y el error decía «no hay un producto
con el código…» aunque se hubiera escrito un título. Ahora el buscador ofrece el
catálogo, el servidor también acepta el título con su número, y el mensaje dice
qué pasó de verdad.
"""

import pytest
from django.urls import reverse

from apps.accounts.models import Usuario
from apps.accounts.tests.factories import UsuarioFactory
from apps.catalog.busqueda import SEPARADOR
from apps.catalog.busqueda import buscar_para_pedir as buscar_para_agregar
from apps.catalog.models import Producto
from apps.catalog.tests.factories import (
    EditorialFactory,
    ProductoFactory,
    ProductoNoEditorialFactory,
)
from apps.restock import servicios
from apps.restock.models import LineaPropuestaRestock
from apps.suppliers.tests.factories import ProveedorFactory

pytestmark = pytest.mark.django_db


@pytest.fixture
def ivrea(db):
    editorial = EditorialFactory(nombre="Ivrea")
    ProveedorFactory(editorial=editorial)
    return editorial


@pytest.fixture
def propuesta(administrador):
    return servicios.armar_a_mano(administrador)


@pytest.fixture
def sakamoto(ivrea):
    return ProductoFactory(titulo="Sakamoto Days", volumen=24, isbn="", editorial=ivrea, stock=20)


def agregar(cliente, texto, cantidad=5):
    return cliente.post(
        reverse("restock:agregar"), {"producto": texto, "cantidad": cantidad}, follow=True
    )


def agregados(propuesta):
    return list(
        LineaPropuestaRestock.objects.filter(propuesta=propuesta).values_list(
            "producto_id", flat=True
        )
    )


@pytest.mark.parametrize(
    "texto",
    ["Sakamoto Days 24", "sakamoto days #24", "Sakamoto 24", "SAKAMOTO DAYS 24"],
)
def test_CO071_por_título_y_número(client_admin, propuesta, sakamoto, texto):
    agregar(client_admin, texto)

    assert agregados(propuesta) == [sakamoto.pk]


def test_CO071_la_opción_del_buscador_trae_el_código(client_admin, propuesta, sakamoto):
    agregar(client_admin, f"{sakamoto.codigo}{SEPARADOR}Sakamoto Days #24")

    assert agregados(propuesta) == [sakamoto.pk]


def test_CO071_el_isbn_con_guiones(client_admin, propuesta, ivrea):
    tomo = ProductoFactory(isbn="9789878271583", editorial=ivrea)

    agregar(client_admin, "978-987-827-158-3")

    assert agregados(propuesta) == [tomo.pk]


def test_el_buscador_ofrece_lo_que_se_puede_pedir(client_admin, propuesta, sakamoto, ivrea):
    cancelado = ProductoFactory(
        titulo="Cancelado", estado=Producto.CANCELADO_EDITORIAL, editorial=ivrea
    )

    html = client_admin.get(reverse("restock:propuesta")).content.decode()

    assert f"{sakamoto.codigo}{SEPARADOR}Sakamoto Days #24" in html
    assert cancelado.codigo not in html
    assert 'data-autocompletado="productos-para-agregar"' in html


# Los mensajes dicen qué pasó, y no se agrega nada (postcondición negativa).


def test_sin_número_pide_el_número(client_admin, propuesta, sakamoto):
    respuesta = agregar(client_admin, "Sakamoto Days")

    assert "escribí también el número del tomo" in respuesta.content.decode()
    assert agregados(propuesta) == []


def test_un_título_que_no_existe_lo_dice(client_admin, propuesta, sakamoto):
    respuesta = agregar(client_admin, "Vinland Saga 3")

    assert "ni título" in respuesta.content.decode()
    assert agregados(propuesta) == []


def test_más_de_uno_pide_elegir(propuesta, ivrea):
    ProductoFactory(titulo="Sakamoto Days", volumen=24, editorial=ivrea)
    ProductoFactory(titulo="Sakamoto Days Deluxe", volumen=24, editorial=ivrea)

    producto, problema = buscar_para_agregar("Sakamoto 24")

    assert producto is None
    assert "más de un producto" in problema and "Elegí uno de la lista" in problema


def test_un_cancelado_dice_que_está_cancelado(client_admin, propuesta, ivrea):
    cancelado = ProductoFactory(estado=Producto.CANCELADO_EDITORIAL, editorial=ivrea)

    respuesta = agregar(client_admin, cancelado.codigo)

    html = respuesta.content.decode()
    assert "cancelado por la editorial" in html and "Volver a anunciar" in html
    assert agregados(propuesta) == []


def test_un_descatalogado_dice_que_está_dado_de_baja(propuesta, ivrea):
    baja = ProductoFactory(estado=Producto.DESCATALOGADO, editorial=ivrea)

    producto, problema = buscar_para_agregar(baja.codigo)

    assert producto is None and "dado de baja" in problema


def test_lo_no_editorial_dice_que_no_es_un_tomo(propuesta):
    figura = ProductoNoEditorialFactory()

    producto, problema = buscar_para_agregar(figura.codigo)

    assert producto is None and "no es material editorial" in problema


def test_vacío_lo_pide():
    assert buscar_para_agregar("   ") == (
        None,
        "Escribí el código, el ISBN o el título del producto.",
    )


# Foco reforzado: control de acceso por la dirección real.


def test_el_cajero_no_agrega(client, propuesta, sakamoto):
    client.force_login(UsuarioFactory(rol=Usuario.CAJERO))

    respuesta = client.post(
        reverse("restock:agregar"), {"producto": sakamoto.codigo, "cantidad": 2}
    )

    assert respuesta.status_code in (403, 302)
    assert agregados(propuesta) == []
