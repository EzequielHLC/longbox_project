"""Acto 2 · Casos borde: entradas válidas pero extremas, y entradas inválidas (plan 00).

Cada caso declara lo que tiene que pasar: se acepta tal cual, se rechaza con un
mensaje, o se trata como el mismo dato que ya existe. Ninguno puede terminar en
un error 500 ni dejar un registro a medias.
"""

from datetime import datetime, timedelta
from decimal import Decimal

import pytest
from django.urls import reverse
from django.utils import timezone
from freezegun import freeze_time

from apps.catalog import isbn, precios
from apps.catalog.forms import IMPORTE_MAXIMO
from apps.catalog.models import Editorial, Oferta, ProductoNoEditorial
from apps.catalog.precio_visible import precio_visible
from apps.catalog.tests.factories import ProductoFactory, TipoNoEditorialFactory

pytestmark = pytest.mark.django_db

URL_EDITORIAL = reverse("catalog:editorial_crear")
URL_NO_EDITORIAL = reverse("catalog:producto_no_editorial_alta")


def alta_no_editorial(cliente, **cambios):
    categoria = TipoNoEditorialFactory()
    datos = {
        "titulo": "Figura de prueba",
        "tipo": categoria.pk,
        "precio": "45000",
        "stock": "3",
        "codigo": "",
        "codigo_barras": "",
        "marca": "",
        "descripcion": "",
    }
    datos.update(cambios)
    return cliente.post(URL_NO_EDITORIAL, datos)


# ---------------------------------------------------------------------------
# D2-01 · Textos
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "nombre",
    ["Ñandú Ediciones", "鬼滅の刃 Ediciones", "Editorial 🦇 Nocturna", "Éditions Çà"],
    ids=["eñe", "japonés", "emoji", "acentos"],
)
def test_D2_01_los_textos_no_latinos_se_guardan_tal_cual(client_admin, nombre):
    client_admin.post(URL_EDITORIAL, {"nombre": nombre})

    assert Editorial.objects.filter(nombre=nombre).exists()


def test_D2_01_el_maximo_exacto_entra_y_uno_mas_se_rechaza(client_admin):
    maximo = Editorial._meta.get_field("nombre").max_length
    justo, pasado = "E" * maximo, "F" * (maximo + 1)

    client_admin.post(URL_EDITORIAL, {"nombre": justo})
    respuesta = client_admin.post(URL_EDITORIAL, {"nombre": pasado})

    assert Editorial.objects.filter(nombre=justo).exists()
    assert not Editorial.objects.filter(nombre=pasado).exists()
    assert respuesta.status_code == 200


def test_D2_01_solo_espacios_se_rechaza(client_admin):
    antes = Editorial.objects.count()

    respuesta = client_admin.post(URL_EDITORIAL, {"nombre": "     "})

    assert Editorial.objects.count() == antes
    assert respuesta.status_code == 200


def test_D2_01_mayusculas_y_espacios_sobrantes_son_el_mismo_nombre(client_admin):
    client_admin.post(URL_EDITORIAL, {"nombre": "One Piece Press"})

    respuesta = client_admin.post(URL_EDITORIAL, {"nombre": "  one   PIECE press "})

    assert Editorial.objects.filter(nombre__iexact="one piece press").count() == 1
    assert "Ya existe una editorial llamada «One Piece Press»." in respuesta.content.decode()


# ---------------------------------------------------------------------------
# D2-02 · Códigos
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "valor",
    ["978-84-376-0494-7", "9788437604947", "0-306-40615-2", "0306406152", "0-8044-2957-X"],
    ids=["13 con guiones", "13 sin guiones", "10 con guiones", "10 sin guiones", "10 con X"],
)
def test_D2_02_isbn_valido_con_y_sin_guiones(valor):
    assert isbn.es_valido(isbn.normalizar(valor))


@pytest.mark.parametrize(
    "valor", ["978-84-376-0494-8", "8437604943", "97884376049"], ids=["13 mal", "10 mal", "corto"]
)
def test_D2_02_isbn_con_digito_incorrecto_se_rechaza_con_motivo(valor):
    assert not isbn.es_valido(isbn.normalizar(valor))
    assert isbn.motivo_de_rechazo(isbn.normalizar(valor))


def test_D2_02_codigo_interno_repetido_se_bloquea(client_admin):
    alta_no_editorial(client_admin, codigo="FIG-001")

    respuesta = alta_no_editorial(client_admin, codigo="FIG-001", titulo="Otra figura")

    assert ProductoNoEditorial.objects.filter(codigo="FIG-001").count() == 1
    assert respuesta.status_code == 200


def test_D2_02_codigo_de_barras_repetido_se_bloquea(client_admin):
    alta_no_editorial(client_admin, codigo_barras="7791234567896")

    respuesta = alta_no_editorial(client_admin, codigo_barras="7791234567896", titulo="Otra")

    assert ProductoNoEditorial.objects.filter(codigo_barras="7791234567896").count() == 1
    assert respuesta.status_code == 200


# ---------------------------------------------------------------------------
# D2-03 · Dinero
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "precio",
    ["0", "-1", "-0.01", "0.001", "12.345", "99999999999", "abc"],
    ids=[
        "cero",
        "negativo",
        "centavo negativo",
        "tres decimales",
        "tres decimales 2",
        "un dígito de más",
        "texto",
    ],
)
def test_D2_03_precios_imposibles_se_rechazan_sin_registrar(client_admin, precio):
    antes = ProductoNoEditorial.objects.count()

    respuesta = alta_no_editorial(client_admin, precio=precio)

    assert respuesta.status_code == 200
    assert ProductoNoEditorial.objects.count() == antes


def test_D2_03_el_importe_maximo_exacto_entra_y_un_centavo_mas_se_rechaza(client_admin):
    alta_no_editorial(client_admin, precio=str(IMPORTE_MAXIMO), titulo="Justo")
    respuesta = alta_no_editorial(client_admin, precio=str(IMPORTE_MAXIMO + Decimal("0.01")))

    assert ProductoNoEditorial.objects.get().precio == IMPORTE_MAXIMO
    assert f"El máximo es ${IMPORTE_MAXIMO}." in respuesta.content.decode()


def test_D2_03_el_cre_conserva_sus_decimales_hasta_el_precio_final():
    """Redondear el CRE antes de aplicarlo cambia el precio: el cálculo no lo hace.

    Con un envío de 1234,56 sobre una compra de 9876,54 el CRE es 0,125000…;
    redondeado a dos decimales sería 0,13 y el tomo costaría $ 45 más.
    """
    cre = precios.calcular_cre(Decimal("1234.56"), Decimal("9876.54"))
    base = precios.calcular_precio_base(Decimal("8000"), cre)
    final = precios.calcular_precio_final(base, Decimal("0.40"))

    redondeado = precios.calcular_precio_final(
        precios.calcular_precio_base(Decimal("8000"), cre.quantize(Decimal("0.01"))),
        Decimal("0.40"),
    )
    assert final == Decimal("12600.00")
    assert redondeado != final


# ---------------------------------------------------------------------------
# D2-04 · Plazos en hora argentina
# ---------------------------------------------------------------------------

ARGENTINA = timezone.get_fixed_timezone(-180)


def test_D2_04_la_oferta_descuenta_hasta_las_23_59_y_no_a_las_00_00():
    producto = ProductoFactory(precio=Decimal("10000"))
    vencimiento = timezone.localdate() + timedelta(days=3)
    Oferta.objects.create(
        descripcion="Hasta medianoche",
        fecha_inicio=timezone.localdate(),
        fecha_vencimiento=vencimiento,
        tipo_descuento=Oferta.PORCENTAJE,
        valor=Decimal("10"),
        alcance=Oferta.PRODUCTO,
        producto=producto,
        estado=Oferta.ACTIVA,
    )
    ultimo_minuto = datetime.combine(vencimiento, datetime.min.time(), ARGENTINA) + timedelta(
        hours=23, minutes=59
    )

    with freeze_time(ultimo_minuto):
        assert precio_visible(producto) == Decimal("9000.00")
    with freeze_time(ultimo_minuto + timedelta(minutes=1)):
        assert precio_visible(producto) == Decimal("10000")
