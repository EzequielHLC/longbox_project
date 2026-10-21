"""La tienda pública, plan 07, quinta parte (B-07-013 a B-07-019, C-20).

El catálogo con filtros de varios valores que se aplican mientras se cambian,
la portada abierta a los invitados, «Lo que se viene», los carteles de tomo,
agregar al carrito desde la tarjeta y las pantallas de acceso partidas.
"""

import json
from datetime import timedelta

import pytest
from django.urls import reverse
from django.utils import timezone

from apps.catalog.models import Producto
from apps.catalog.tests.factories import (
    EditorialFactory,
    EtiquetaFactory,
    GrupoEtiquetaFactory,
    ProductoFactory,
    TipoFactory,
)
from apps.core.models import IdentidadVisual
from apps.core.views_tienda import DIAS_DE_NOVEDAD
from apps.tienda.models import LineaCarrito

pytestmark = pytest.mark.django_db

URL_CATALOGO = reverse("core:tienda_catalogo")
URL_PORTADA = reverse("core:tienda")


def titulos(respuesta):
    return [p.titulo for p in respuesta.context["productos"]]


# ---------------------------------------------------------------------------
# Catálogo: filtros de varios valores (B-07-013)
# ---------------------------------------------------------------------------


def test_CO176_varios_tipos_a_la_vez_suman_productos(client):
    manga, comic = TipoFactory(nombre="Manga"), TipoFactory(nombre="Cómic")
    ProductoFactory(titulo="Berserk", tipo=manga, stock=2)
    ProductoFactory(titulo="Batman", tipo=comic, stock=2)
    ProductoFactory(titulo="Otro", tipo=TipoFactory(nombre="Libro"), stock=2)

    respuesta = client.get(URL_CATALOGO, {"tipo": [manga.pk, comic.pk]})

    assert sorted(titulos(respuesta)) == ["Batman", "Berserk"]


def test_CO176_etiquetas_del_mismo_grupo_suman_y_de_grupos_distintos_restringen(client):
    demografia = GrupoEtiquetaFactory(nombre="Demografía")
    genero = GrupoEtiquetaFactory(nombre="Género")
    shonen = EtiquetaFactory(nombre="Shonen", grupo=demografia)
    seinen = EtiquetaFactory(nombre="Seinen", grupo=demografia)
    accion = EtiquetaFactory(nombre="Acción", grupo=genero)
    for titulo, etiquetas in (
        ("Naruto", [shonen, accion]),
        ("Berserk", [seinen, accion]),
        ("Yotsuba", [seinen]),
    ):
        ProductoFactory(titulo=titulo, stock=1).etiquetas.set(etiquetas)

    ambas = client.get(URL_CATALOGO, {"etiqueta": [shonen.pk, seinen.pk]})
    con_accion = client.get(URL_CATALOGO, {"etiqueta": [shonen.pk, seinen.pk, accion.pk]})

    assert sorted(titulos(ambas)) == ["Berserk", "Naruto", "Yotsuba"]
    assert sorted(titulos(con_accion)) == ["Berserk", "Naruto"]


def test_CO176_los_estados_son_interruptores(client):
    ProductoFactory(titulo="Con stock", stock=3)
    ProductoFactory(titulo="Sin stock", stock=0)
    ProductoFactory(titulo="Reserva", estado=Producto.PRE_VENTA, stock=0)

    por_defecto = client.get(URL_CATALOGO)
    dos = client.get(URL_CATALOGO, {"f": "1", "estado": ["disponible", "pre_venta"]})
    ninguno = client.get(URL_CATALOGO, {"f": "1"})

    assert titulos(por_defecto) == ["Con stock"]
    assert sorted(titulos(dos)) == ["Con stock", "Reserva"]
    assert sorted(titulos(ninguno)) == ["Con stock", "Reserva", "Sin stock"]


def test_CO176_proximos_a_llegar_ordena_por_la_fecha_vigente(client):
    hoy = timezone.localdate()
    ProductoFactory(
        titulo="Lejos", estado=Producto.PRE_VENTA, fecha_llegada=hoy + timedelta(days=30)
    )
    ProductoFactory(
        titulo="Demorado",
        estado=Producto.PRE_VENTA,
        fecha_llegada=hoy + timedelta(days=2),
        fecha_estimada=hoy + timedelta(days=60),
    )
    ProductoFactory(
        titulo="Cerca", estado=Producto.PRE_VENTA, fecha_llegada=hoy + timedelta(days=5)
    )

    respuesta = client.get(URL_CATALOGO, {"estado": "pre_venta", "orden": "llegada"})

    assert titulos(respuesta) == ["Cerca", "Lejos", "Demorado"]


def test_CO176_con_parcial_responde_solo_los_resultados(client):
    ProductoFactory(titulo="Berserk", stock=1)

    respuesta = client.get(URL_CATALOGO, {"q": "berserk", "parcial": "1"})
    contenido = respuesta.content.decode()

    assert "Berserk" in contenido
    assert "<html" not in contenido
    assert "data-filtros" not in contenido
    assert "parcial" not in respuesta.context["parametros"]


def test_el_panel_ofrece_solo_opciones_con_productos(client):
    con = EditorialFactory(nombre="Ivrea")
    EditorialFactory(nombre="Sin productos")
    ProductoFactory(editorial=con, stock=1)

    respuesta = client.get(URL_CATALOGO)

    assert [e.nombre for e in respuesta.context["editoriales"]] == ["Ivrea"]
    contenido = respuesta.content.decode()
    assert 'role="switch" name="editorial"' in contenido
    assert 'class="buscador-publico"' not in contenido  # la búsqueda grande la reemplaza


# ---------------------------------------------------------------------------
# Portada pública, «Lo que se viene» y carteles (C-20, B-07-015, B-07-017)
# ---------------------------------------------------------------------------


def test_un_invitado_ve_la_portada(client):
    respuesta = client.get(URL_PORTADA)

    assert respuesta.status_code == 200
    assert client.get("/").url == URL_PORTADA


def test_lo_que_se_viene_trae_las_pre_ventas_la_mas_proxima_primero(client):
    hoy = timezone.localdate()
    ProductoFactory(
        titulo="Lejos", estado=Producto.PRE_VENTA, fecha_llegada=hoy + timedelta(days=40)
    )
    ProductoFactory(
        titulo="Cerca", estado=Producto.PRE_VENTA, fecha_llegada=hoy + timedelta(days=3)
    )
    ProductoFactory(titulo="Ya está", stock=4)

    se_viene = client.get(URL_PORTADA).context["se_viene"]

    assert [p.titulo for p in se_viene.productos] == ["Cerca", "Lejos"]
    assert "orden=llegada" in se_viene.ver_todo


def test_sin_pre_ventas_no_hay_lo_que_se_viene(client):
    ProductoFactory(stock=4)

    assert client.get(URL_PORTADA).context["se_viene"] is None


def test_carteles_de_tomo_1_y_de_novedad(client):
    """B-07-024: «¡TOMO 1!» en el tomo 1 de una serie; «¡NOVEDAD!» en lo que se dio
    de alta hace menos de treinta días y ya está a la venta."""
    editorial = EditorialFactory(nombre="Ivrea")
    uno = ProductoFactory(titulo="Berserk", volumen=1, editorial=editorial, stock=1)
    nuevo = ProductoFactory(titulo="Berserk", volumen=3, editorial=editorial, stock=1)
    viejo = ProductoFactory(titulo="Berserk", volumen=2, editorial=editorial, stock=1)
    reserva = ProductoFactory(
        titulo="Berserk", volumen=4, editorial=editorial, estado=Producto.PRE_VENTA
    )
    unico = ProductoFactory(titulo="Solanin", volumen=1, editorial=editorial, stock=1)
    Producto.objects.filter(pk=viejo.pk).update(
        creado_en=timezone.now() - timedelta(days=DIAS_DE_NOVEDAD + 1)
    )

    respuesta = client.get(URL_CATALOGO, {"estado": "todos"})
    carteles = {p.pk: getattr(p, "cartel", None) for p in respuesta.context["productos"]}

    assert carteles[uno.pk] == "¡TOMO 1!"
    assert carteles[nuevo.pk] == "¡NOVEDAD!"
    assert carteles[viejo.pk] is None
    assert carteles[reserva.pk] is None  # la pre-venta tiene su rótulo
    assert carteles[unico.pk] == "¡NOVEDAD!"  # un tomo solo no es «tomo 1» de nada
    assert "cartel-tomo--primero" in respuesta.content.decode()


# ---------------------------------------------------------------------------
# Agregar desde la tarjeta (B-07-014)
# ---------------------------------------------------------------------------


def test_la_tarjeta_ofrece_agregar_a_invitados_y_clientes_y_no_al_personal(
    client, cliente, administrador
):
    con_stock = ProductoFactory(titulo="Con stock", stock=2)
    ProductoFactory(titulo="Sin stock", stock=0)
    accion = reverse("tienda:agregar", args=[con_stock.pk])

    invitado = client.get(URL_CATALOGO, {"estado": "todos"}).content.decode()
    client.force_login(cliente)
    del_cliente = client.get(URL_CATALOGO, {"estado": "todos"}).content.decode()
    client.force_login(administrador)
    del_personal = client.get(URL_CATALOGO, {"estado": "todos"}).content.decode()

    assert f'action="{accion}"' in invitado
    assert f'action="{accion}"' in del_cliente
    assert invitado.count("data-agregar-rapido>") == 1  # el agotado no tiene botón
    assert "data-agregar-rapido>" not in del_personal


def test_CO083_agregar_desde_la_tarjeta_responde_json_con_las_unidades(client, cliente):
    producto = ProductoFactory(titulo="Berserk", stock=5)
    client.force_login(cliente)
    url = reverse("tienda:agregar", args=[producto.pk])

    client.post(url, {"cantidad": "1"}, headers={"X-Requested-With": "fetch"})
    respuesta = client.post(url, {"cantidad": "1"}, headers={"X-Requested-With": "fetch"})

    datos = json.loads(respuesta.content)
    assert respuesta.status_code == 200
    carrito = datos.pop("carrito")
    assert datos == {
        "nivel": "exito",
        "mensaje": "Se agregó «Berserk» en el carrito.",
        "unidades": 2,
    }
    # Plan 00 de interfaz, U2: lo que muestra el carrito lateral.
    assert carrito["titulo"] == "Berserk"
    assert carrito["total"] and carrito["precio"]
    assert LineaCarrito.objects.get(producto=producto).cantidad == 2


def test_CO083_desde_la_tarjeta_el_tope_de_stock_se_avisa_igual(client):
    producto = ProductoFactory(titulo="Berserk", stock=1)
    url = reverse("tienda:agregar", args=[producto.pk])

    client.post(url, {"cantidad": "1"}, headers={"X-Requested-With": "fetch"})
    respuesta = client.post(url, {"cantidad": "1"}, headers={"X-Requested-With": "fetch"})

    datos = json.loads(respuesta.content)
    assert datos["nivel"] == "atencion"
    assert datos["unidades"] == 1


def test_CO083_el_personal_no_agrega_desde_la_tarjeta(client, administrador):
    producto = ProductoFactory(stock=5)
    client.force_login(administrador)

    respuesta = client.post(
        reverse("tienda:agregar", args=[producto.pk]),
        {"cantidad": "1"},
        headers={"X-Requested-With": "fetch"},
    )

    assert respuesta.status_code == 403
    assert not LineaCarrito.objects.exists()


# ---------------------------------------------------------------------------
# Pantallas de acceso (B-07-018)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("nombre", ["accounts:login", "accounts:registro_cliente"])
def test_las_pantallas_de_acceso_van_partidas_y_sin_distracciones(client, nombre):
    contenido = client.get(reverse(nombre)).content.decode()

    assert 'class="acceso"' in contenido
    assert 'class="buscador-publico"' not in contenido
    assert 'class="globo-ayuda"' not in contenido


def test_el_acceso_muestra_la_imagen_del_ingreso_o_el_logo_o_el_nombre(client):
    """B-07-020: la imagen que carga el Administrador; sin ella, el logo; sin logo,
    el nombre de la tienda. Nunca la portada de un producto."""
    ProductoFactory(stock=1, portada="portadas/x.webp")
    identidad = IdentidadVisual.obtener()
    url = reverse("accounts:login")

    solo_nombre = client.get(url).content.decode()
    identidad.logo = "identidad/logo.webp"
    identidad.save()
    con_logo = client.get(url).content.decode()
    identidad.imagen_acceso = "identidad/ingreso.webp"
    identidad.save()
    con_imagen = client.get(url).content.decode()

    assert 'class="acceso__nombre"' in solo_nombre
    assert "portadas/x.webp" not in solo_nombre
    assert 'src="/media/identidad/logo.webp" alt="" class="acceso__logo"' in con_logo
    assert 'src="/media/identidad/ingreso.webp" alt="" class="acceso__imagen"' in con_imagen
    assert "acceso__logo" not in con_imagen


def test_el_ticker_nombra_cada_serie_una_vez(client):
    """B-07-023: dos tomos de la misma serie recién llegados son un solo «Llegó»."""
    ProductoFactory(titulo="Blue Exorcist", volumen=29, stock=1)
    ProductoFactory(titulo="Blue Exorcist", volumen=30, stock=1)
    ProductoFactory(titulo="Berserk", volumen=1, stock=1)

    respuesta = client.get(URL_PORTADA)

    assert sorted(respuesta.context["llegaron"]) == ["Berserk", "Blue Exorcist"]
    assert respuesta.content.decode().count("<span>Llegó Blue Exorcist</span>") == 1


def test_el_menu_de_la_tienda_es_todo_texto(client):
    """B-07-027: los enlaces del menú público son rótulos, sin íconos."""
    contenido = client.get(URL_CATALOGO).content.decode()
    menu = contenido.partition('<nav aria-label="Tienda">')[2].partition("</nav>")[0]

    assert "Carrito" in menu
    assert "<svg" not in menu.partition("<details")[0]


# ---------------------------------------------------------------------------
# El carrito que se actualiza solo (B-07-028)
# ---------------------------------------------------------------------------

FETCH = {"X-Requested-With": "fetch"}


def _con_linea(client, producto, cantidad="1"):
    client.post(reverse("tienda:agregar", args=[producto.pk]), {"cantidad": cantidad})
    return LineaCarrito.objects.get(producto=producto)


def test_CO084_cambiar_la_cantidad_devuelve_el_carrito_recalculado(client, cliente):
    client.force_login(cliente)
    linea = _con_linea(client, ProductoFactory(titulo="Berserk", stock=5))

    respuesta = client.post(
        reverse("tienda:cantidad", args=[linea.pk]), {"cantidad": "3"}, headers=FETCH
    )

    datos = json.loads(respuesta.content)
    linea.refresh_from_db()
    assert linea.cantidad == 3
    assert datos["nivel"] == "exito"
    assert datos["unidades"] == 3
    assert "3 unidad(es)" in datos["html"]
    assert "data-cantidad-linea" in datos["html"]
    assert "<html" not in datos["html"]


def test_CO084_sin_stock_suficiente_se_topea_y_se_avisa(client):
    linea = _con_linea(client, ProductoFactory(titulo="Berserk", stock=2))

    respuesta = client.post(
        reverse("tienda:cantidad", args=[linea.pk]), {"cantidad": "9"}, headers=FETCH
    )

    datos = json.loads(respuesta.content)
    linea.refresh_from_db()
    assert linea.cantidad == 2
    assert datos["nivel"] == "atencion"
    assert "Hay 2 disponibles" in datos["mensaje"]


def test_CO085_quitar_devuelve_el_carrito_sin_la_linea(client):
    linea = _con_linea(client, ProductoFactory(titulo="Berserk", stock=2))

    respuesta = client.post(reverse("tienda:quitar", args=[linea.pk]), headers=FETCH)

    datos = json.loads(respuesta.content)
    assert not LineaCarrito.objects.exists()
    assert datos["unidades"] == 0
    assert "Tu carrito está vacío." in datos["html"]


def test_sin_guion_el_carrito_sigue_con_su_boton(client):
    linea = _con_linea(client, ProductoFactory(stock=5))

    respuesta = client.post(reverse("tienda:cantidad", args=[linea.pk]), {"cantidad": "2"})
    pantalla = client.get(reverse("tienda:carrito")).content.decode()

    assert respuesta.status_code == 302
    assert "data-sin-guion>Actualizar</button>" in pantalla


# ---------------------------------------------------------------------------
# Navegación (B-07-029, B-07-030)
# ---------------------------------------------------------------------------


def test_la_ficha_ofrece_mas_de_la_serie_en_orden(client):
    editorial = EditorialFactory(nombre="Ivrea")
    tomos = [
        ProductoFactory(titulo="Berserk", volumen=v, editorial=editorial, stock=1)
        for v in (3, 1, 2)
    ]
    ProductoFactory(titulo="Otra", volumen=1, editorial=editorial, stock=1)

    respuesta = client.get(reverse("core:tienda_producto", args=[tomos[1].pk]))

    serie = respuesta.context["serie"]
    assert [p.productoeditorial.volumen for p in serie.productos] == [2, 3]
    assert "Más de Berserk" in respuesta.content.decode()


def test_un_tomo_solo_no_tiene_mas_de_la_serie(client):
    producto = ProductoFactory(titulo="Solanin", stock=1)

    assert client.get(reverse("core:tienda_producto", args=[producto.pk])).context["serie"] is None


def test_las_filas_no_llevan_contador_y_la_busqueda_tiene_atajo(client):
    ProductoFactory(titulo="Reserva", estado=Producto.PRE_VENTA)

    contenido = client.get(URL_PORTADA).content.decode()

    assert "data-contador" not in contenido
    assert 'aria-keyshortcuts="/"' in contenido
