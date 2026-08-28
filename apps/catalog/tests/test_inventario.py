"""Inventario y ficha de producto: la contraparte de lectura del alta.

No son un CU: existen porque E1 exige enlazar a la ficha del producto con el que
se chocó, y porque después de cargar un lote hay que poder ver que quedó
cargado. Editar y dar de baja son CU-09 y CU-10 (Módulo 02).
"""

from decimal import Decimal

import pytest
from django.db import IntegrityError
from django.urls import reverse
from django.utils.formats import localize

from apps.accounts.tests.factories import UsuarioFactory
from apps.catalog.models import Producto
from apps.catalog.tests.factories import (
    EditorialFactory,
    EtiquetaFactory,
    FormatoFactory,
    LoteAltaFactory,
    ProductoFactory,
    TipoFactory,
)
from apps.catalog.tests.helpers_lote import URL_INVENTARIO, URL_NACIONAL, url_ficha

pytestmark = pytest.mark.django_db


def test_el_inventario_lista_los_productos_cargados(client_admin):
    ProductoFactory(titulo="Akira")

    respuesta = client_admin.get(URL_INVENTARIO)

    assert respuesta.status_code == 200
    assert "Akira" in respuesta.content.decode()


def test_el_buscador_filtra_por_titulo(client_admin):
    ProductoFactory(titulo="Akira")
    ProductoFactory(titulo="Berserk")

    respuesta = client_admin.get(URL_INVENTARIO, {"q": "akira"})

    contenido = respuesta.content.decode()
    assert "Akira" in contenido
    assert "Berserk" not in contenido


def test_los_filtros_ignoran_un_valor_inventado(client_admin):
    """Un valor arbitrario en la query string no rompe ni filtra de más."""
    ProductoFactory(titulo="Akira")

    respuesta = client_admin.get(URL_INVENTARIO, {"estado": "inventado"})

    assert respuesta.status_code == 200
    assert "Akira" in respuesta.content.decode()


def test_el_filtro_de_estado_funciona(client_admin):
    ProductoFactory(titulo="Akira", estado=Producto.ACTIVO)
    ProductoFactory(titulo="Berserk", estado=Producto.PRE_VENTA)

    respuesta = client_admin.get(URL_INVENTARIO, {"estado": Producto.PRE_VENTA})

    contenido = respuesta.content.decode()
    assert "Berserk" in contenido
    assert "Akira" not in contenido


def test_el_filtro_de_etiqueta_funciona(client_admin):
    """Las etiquetas no identifican un producto, pero son la forma natural de
    recortar el catálogo: "todo lo de Marvel" cruza editoriales y tipos, y
    ninguno de los otros filtros junta eso."""
    marvel = EtiquetaFactory(nombre="Marvel")
    con_etiqueta = ProductoFactory(titulo="Civil War")
    con_etiqueta.etiquetas.add(marvel)
    ProductoFactory(titulo="Akira")

    respuesta = client_admin.get(URL_INVENTARIO, {"etiqueta": marvel.pk})

    contenido = respuesta.content.decode()
    assert "Civil War" in contenido
    assert "Akira" not in contenido


def test_el_desplegable_de_etiquetas_solo_ofrece_las_que_filtran_algo(client_admin):
    """Es el único eje que puede no aplicarle a ningún producto —ninguna es
    obligatoria—, así que una etiqueta sin productos ocuparía lugar en el
    desplegable sin filtrar nada."""
    con_productos = EtiquetaFactory(nombre="Marvel")
    sin_productos = EtiquetaFactory(nombre="Star Trek")
    producto = ProductoFactory(titulo="Civil War")
    producto.etiquetas.add(con_productos)

    ofrecidas = client_admin.get(URL_INVENTARIO).context["etiquetas"]

    assert con_productos in ofrecidas
    assert sin_productos not in ofrecidas


def test_un_producto_puede_tener_varias_etiquetas(client_admin):
    """Es el defecto que la franquicia no podía expresar: Marvel publica cómics
    de Star Wars, o sea Marvel **y** Star Wars."""
    marvel = EtiquetaFactory(nombre="Marvel")
    star_wars = EtiquetaFactory(nombre="Star Wars")
    producto = ProductoFactory(titulo="Star Wars: Darth Vader")
    producto.etiquetas.set([marvel, star_wars])

    for etiqueta in (marvel, star_wars):
        respuesta = client_admin.get(URL_INVENTARIO, {"etiqueta": etiqueta.pk})
        assert "Darth Vader" in respuesta.content.decode()


def test_la_ficha_agrupa_las_etiquetas_por_su_grupo(client_admin):
    """Sin el grupo, la ficha mostraría "Marvel, Shonen, Edición limitada" como
    una bolsa. Es el mismo motivo por el que la tienda las necesita agrupadas."""
    producto = ProductoFactory(titulo="Civil War")
    producto.etiquetas.add(EtiquetaFactory(nombre="Marvel"))

    contenido = client_admin.get(url_ficha(producto)).content.decode()

    assert "Etiquetas" in contenido
    assert "Franquicia" in contenido
    assert "Marvel" in contenido


def test_el_parcial_devuelve_solo_el_fragmento_de_la_tabla(client_admin):
    ProductoFactory(titulo="Akira")

    respuesta = client_admin.get(URL_INVENTARIO, {"parcial": "1"})

    contenido = respuesta.content.decode()
    assert "Akira" in contenido
    # El fragmento no trae la cáscara de la pantalla.
    assert "<html" not in contenido


def test_la_ficha_muestra_los_datos_del_producto(client_admin):
    producto = ProductoFactory(titulo="Akira", volumen=3, autor="Katsuhiro Otomo")

    respuesta = client_admin.get(url_ficha(producto))

    contenido = respuesta.content.decode()
    assert "Akira" in contenido
    assert "Katsuhiro Otomo" in contenido


def test_la_ficha_marca_la_portada_pendiente(client_admin):
    producto = ProductoFactory()

    respuesta = client_admin.get(url_ficha(producto))

    assert "Imagen pendiente" in respuesta.content.decode()


def test_la_ficha_de_un_importado_muestra_la_composicion_del_precio(client_admin):
    lote = LoteAltaFactory(
        origen="importado", cre=Decimal("0.100000"), margen_aplicado=Decimal("0.4")
    )
    producto = ProductoFactory(
        origen=Producto.IMPORTADO,
        costo_origen=Decimal("1000"),
        precio_base=Decimal("1100.00"),
        precio=Decimal("1540.00"),
        lote=lote,
    )

    respuesta = client_admin.get(url_ficha(producto))

    contenido = respuesta.content.decode()
    assert "Composición del precio" in contenido
    # El dinero sale con el formato local (es-AR, coma decimal); el CRE, sin
    # localizar, porque es un factor de cálculo y no un importe.
    assert localize(Decimal("1100.00")) in contenido
    assert "0.100000" in contenido


def test_la_ficha_avisa_cuando_el_precio_es_manual(client_admin):
    producto = ProductoFactory(precio_manual=True)

    respuesta = client_admin.get(url_ficha(producto))

    assert "fijó a mano" in respuesta.content.decode()


def test_el_inventario_avisa_cuando_esta_vacio(client_admin):
    respuesta = client_admin.get(URL_INVENTARIO)

    assert "No hay productos cargados en el catálogo." in respuesta.content.decode()


def test_el_alta_avisa_si_falta_configurar_editoriales(client_admin):
    """Sin editoriales no se puede dar de alta nada, y la pantalla lo dice.

    Los tipos vienen sembrados con la instalación; las editoriales las carga el
    negocio, así que son lo primero que puede faltar.
    """
    respuesta = client_admin.get(URL_NACIONAL)

    assert "Todavía no hay editoriales" in respuesta.content.decode()


def test_con_editoriales_cargadas_no_aparece_el_aviso(client_admin):
    EditorialFactory()

    respuesta = client_admin.get(URL_NACIONAL)

    assert "Todavía no hay" not in respuesta.content.decode()


@pytest.mark.parametrize("rol_sin_permiso", ["cliente", "cajero"])
def test_el_inventario_no_filtra_datos_a_otros_roles(client, rol_sin_permiso):
    """403 sin datos parciales, igual que la tabla de usuarios."""
    ProductoFactory(titulo="Akira")
    client.force_login(UsuarioFactory(rol=rol_sin_permiso))

    respuesta = client.get(URL_INVENTARIO)

    assert respuesta.status_code == 403
    assert "Akira" not in respuesta.content.decode()


def test_la_ficha_tampoco_se_abre_con_otro_rol(client, cajero):
    producto = ProductoFactory(titulo="Akira")
    client.force_login(cajero)

    assert client.get(url_ficha(producto)).status_code == 403


@pytest.mark.parametrize("pantalla", ["catalog:lote_nacional", "catalog:lote_importado"])
def test_las_dos_pantallas_de_alta_se_dibujan_enteras(client_admin, pantalla):
    """Humo: las dos cargan con sus ítems vacíos y con el molde del `<template>`.

    El molde usa `empty_form`, que se arma por un camino distinto del de los
    ítems normales: si le faltara un argumento, la pantalla reventaría recién al
    abrirla y no al validar.
    """
    EditorialFactory()

    respuesta = client_admin.get(reverse(pantalla))

    assert respuesta.status_code == 200
    contenido = respuesta.content.decode()
    assert 'id="molde-item"' in contenido
    assert "{#" not in contenido


def test_cada_item_ofrece_quitarlo_y_duplicarlo(client_admin):
    """Contrato con el script de la pantalla: los `data-` son lo que busca.

    Duplicar existe porque cargar los doce tomos de una serie es el caso normal
    y es donde más se tipea de más.
    """
    EditorialFactory()

    html = client_admin.get(URL_NACIONAL).content.decode()

    assert html.count("data-quitar") >= 3
    assert html.count("data-duplicar") >= 3
    assert "data-numero" in html


def test_el_molde_de_items_nuevos_trae_los_mismos_campos_que_los_dibujados(client_admin):
    """El ítem que se agrega desde el navegador sale del `empty_form`.

    Se arma por un camino distinto del de los ítems normales: si le faltara un
    campo, el ítem agregado se guardaría incompleto y nadie lo notaría.
    """
    EditorialFactory()

    html = client_admin.get(URL_NACIONAL).content.decode()
    molde = html.split('<template id="molde-item">')[1].split("</template>")[0]

    for campo in ["titulo", "volumen", "editorial", "formato", "precio", "stock", "portada"]:
        assert f"form-__prefix__-{campo}" in molde, campo


def test_el_alta_de_importados_muestra_la_calculadora_de_envio(client_admin):
    EditorialFactory()

    respuesta = client_admin.get(reverse("catalog:lote_importado"))

    contenido = respuesta.content.decode()
    assert "Calculadora de envío" in contenido
    assert "Costo relativo de envío" in contenido


def test_el_alta_de_nacionales_no_muestra_la_calculadora_de_envio(client_admin):
    EditorialFactory()

    respuesta = client_admin.get(reverse("catalog:lote_nacional"))

    assert "Calculadora de envío" not in respuesta.content.decode()


def test_el_menu_del_administrador_ofrece_el_catalogo(client_admin):
    respuesta = client_admin.get(URL_INVENTARIO)

    contenido = respuesta.content.decode()
    assert "Nuevo lote nacional" in contenido
    assert "Nuevo lote importado" in contenido


def test_no_se_pueden_cargar_dos_productos_con_la_misma_tupla(client_admin):
    """La restricción de la base es la que realmente garantiza la unicidad:
    dos altas simultáneas pasarían las dos validaciones de formulario."""
    comun = {
        "editorial": EditorialFactory(),
        "tipo": TipoFactory(nombre="Manga"),
        "formato": FormatoFactory(nombre="B6"),
    }
    ProductoFactory(titulo="Akira", volumen=1, **comun)

    with pytest.raises(IntegrityError):
        ProductoFactory(titulo="AKIRA", volumen=1, **comun)


@pytest.mark.parametrize("sin_formato", [True, False])
def test_la_restriccion_tambien_alcanza_a_los_productos_sin_formato(client_admin, sin_formato):
    """En SQL dos nulos no son iguales: sin el `Coalesce` de la restricción, dos
    importados del mismo tomo entrarían los dos sin que nada lo impida."""
    comun = {
        "editorial": EditorialFactory(),
        "tipo": TipoFactory(nombre="Manga"),
        "formato": FormatoFactory(nombre="B6") if not sin_formato else None,
    }
    ProductoFactory(titulo="Berserk", volumen=1, **comun)

    with pytest.raises(IntegrityError):
        ProductoFactory(titulo="Berserk", volumen=1, **comun)
