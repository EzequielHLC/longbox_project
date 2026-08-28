"""El ISBN: normalización, dígito verificador y detección de duplicados.

La primera mitad no toca la base —igual que `test_precios.py`— porque la
aritmética del verificador se prueba mejor con una tabla de casos que con un
formulario de por medio.
"""

from decimal import Decimal

import pytest
from django.db import IntegrityError
from django.urls import reverse

from apps.catalog import isbn as isbn_util
from apps.catalog.models import Producto
from apps.catalog.services import buscar_duplicado
from apps.catalog.tests.factories import (
    EditorialFactory,
    FormatoFactory,
    PrecioReferenciaFactory,
    ProductoFactory,
    TipoFactory,
)
from apps.catalog.tests.helpers_lote import URL_NACIONAL, item, lote_nacional

# Tres ISBN reales de material que existe, con su dígito verificador correcto.
BERSERK = "9789878271583"
BLUE_PERIOD = "9789878274652"
# Un ISBN-10 válido, del material de fondo que todavía los trae.
VIEJO = "0306406152"


@pytest.fixture
def referencia(db):
    """La precondición del alta nacional: la tabla tiene una combinación."""
    return PrecioReferenciaFactory()


# ---------------------------------------------------------------------------
# Normalización
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "escrito",
    ["978-987-827-158-3", "978 987 827 158 3", " 9789878271583 ", "978–987–827–158–3"],
)
def test_se_guarda_sin_guiones_ni_espacios(escrito):
    """Se normaliza al guardar y no solo al comparar: si no, el mismo ISBN
    escrito de dos formas serían dos productos para cualquier consulta que se
    olvide de normalizar, y la restricción de la base es una de esas."""
    assert isbn_util.normalizar(escrito) == BERSERK


def test_la_x_final_va_en_mayuscula():
    """Es un dígito que vale diez, no una letra: en minúscula rompería la
    comparación exacta."""
    assert isbn_util.normalizar("043942089x") == "043942089X"


def test_un_valor_vacio_se_normaliza_a_cadena_vacia():
    assert isbn_util.normalizar(None) == ""
    assert isbn_util.normalizar("   ") == ""


# ---------------------------------------------------------------------------
# Dígito verificador
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("valido", [BERSERK, BLUE_PERIOD, VIEJO, "043942089X"])
def test_un_isbn_bien_formado_pasa(valido):
    assert isbn_util.es_valido(valido)


def test_un_digito_cambiado_se_detecta():
    """Es el caso que justifica verificar: un ISBN mal copiado no falla de forma
    ruidosa, pasa a identificar un producto que no existe y el chequeo de
    duplicados deja de encontrar el que sí."""
    con_error = BERSERK[:-1] + str((int(BERSERK[-1]) + 1) % 10)

    assert not isbn_util.es_valido(con_error)
    assert isbn_util.motivo_de_rechazo(con_error) == isbn_util.MENSAJE_VERIFICADOR


@pytest.mark.parametrize("largo_raro", ["978987827158", "97898782715831", "12345"])
def test_un_largo_que_no_es_de_isbn_se_rechaza(largo_raro):
    assert isbn_util.motivo_de_rechazo(largo_raro) == isbn_util.MENSAJE_LARGO


@pytest.mark.parametrize("con_letras", ["97898782715A3", "X789878271583", "978987827158X"])
def test_las_letras_donde_no_van_se_rechazan(con_letras):
    assert isbn_util.motivo_de_rechazo(con_letras) == isbn_util.MENSAJE_CARACTERES


def test_verificar_no_consulta_nada_externo(sin_red):
    """La fixture corta la red. Que esto pase confirma que la verificación es
    aritmética y no una consulta a una base de ISBN — que es justamente lo que
    RF-05 excluye del alcance del proyecto."""
    assert isbn_util.es_valido(BERSERK)


# ---------------------------------------------------------------------------
# Unicidad en la base
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_dos_productos_no_pueden_compartir_isbn():
    ProductoFactory(isbn=BERSERK)

    with pytest.raises(IntegrityError):
        ProductoFactory(isbn=BERSERK)


@pytest.mark.django_db
def test_muchos_productos_pueden_no_tener_isbn():
    """La restricción es parcial a propósito: el "sin ISBN" se representa con la
    cadena vacía, y una unicidad común los haría chocar a todos entre sí."""
    ProductoFactory(isbn="")
    ProductoFactory(isbn="")

    assert Producto.objects.filter(isbn="").count() == 2


# ---------------------------------------------------------------------------
# Detección de duplicados
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_el_isbn_encuentra_el_duplicado_aunque_el_titulo_este_escrito_distinto():
    """Es lo que la tupla no atrapa, y el motivo por el que el ISBN va primero:
    el mismo tomo anunciado con otro nombre sigue siendo el mismo tomo."""
    existente = ProductoFactory(titulo="Berserk Deluxe", volumen=5, isbn=BERSERK)

    encontrado = buscar_duplicado(
        "Berserk edición deluxe vol. 5",
        99,
        TipoFactory(nombre="Otro tipo"),
        None,
        EditorialFactory(nombre="Otra editorial"),
        isbn=BERSERK,
    )

    assert encontrado == existente


@pytest.mark.django_db
def test_sin_isbn_se_cae_a_la_tupla_de_siempre():
    existente = ProductoFactory(titulo="Akira", volumen=1)

    encontrado = buscar_duplicado(
        "akira",
        1,
        existente.tipo,
        existente.formato,
        existente.editorial,
    )

    assert encontrado == existente


@pytest.mark.django_db
def test_un_isbn_que_no_esta_no_impide_encontrar_por_la_tupla():
    """Un producto viejo cargado sin ISBN puede ser el mismo tomo que uno nuevo
    que sí lo trae: si el ISBN no encuentra nada, todavía hay que mirar la
    tupla."""
    existente = ProductoFactory(titulo="Akira", volumen=1, isbn="")

    encontrado = buscar_duplicado(
        "Akira",
        1,
        existente.tipo,
        existente.formato,
        existente.editorial,
        isbn=BERSERK,
    )

    assert encontrado == existente


# ---------------------------------------------------------------------------
# El alta en lote
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_el_alta_guarda_el_isbn_normalizado(client_admin, referencia):
    datos = lote_nacional([item("Akira", 1, isbn="978-987-827-158-3")], referencia)

    assert client_admin.post(URL_NACIONAL, datos).status_code == 302
    assert Producto.objects.get().isbn == BERSERK


@pytest.mark.django_db
def test_un_isbn_invalido_frena_el_item(client_admin, referencia):
    datos = lote_nacional([item("Akira", 1, isbn="9789878271584")], referencia)

    respuesta = client_admin.post(URL_NACIONAL, datos)

    assert respuesta.status_code == 200
    assert respuesta.context["formset"].errors[0]["isbn"]
    assert not Producto.objects.exists()


@pytest.mark.django_db
def test_el_isbn_es_opcional(client_admin, referencia):
    """No todo producto tiene uno, y exigirlo trabaría el alta de todo el
    material que no responde a estándares editoriales (RF-05)."""
    datos = lote_nacional([item("Akira", 1)], referencia)

    assert client_admin.post(URL_NACIONAL, datos).status_code == 302
    assert Producto.objects.get().isbn == ""


@pytest.mark.django_db
def test_un_item_con_isbn_ya_cargado_se_excluye_del_lote(client_admin, referencia):
    """E1 de CU-01 con el criterio nuevo: el duplicado se excluye e informa, y
    los demás ítems del lote se cargan igual."""
    ProductoFactory(titulo="Cualquier otra cosa", isbn=BERSERK)
    datos = lote_nacional(
        [item("Akira", 1, isbn=BERSERK), item("Berserk", 1, isbn=BLUE_PERIOD)],
        referencia,
    )

    respuesta = client_admin.post(URL_NACIONAL, datos)

    assert respuesta.status_code == 302
    assert Producto.objects.filter(lote__isnull=False).count() == 1
    assert Producto.objects.get(lote__isnull=False).isbn == BLUE_PERIOD


@pytest.mark.django_db
def test_dos_items_con_el_mismo_isbn_en_el_mismo_envio_se_marcan(client_admin, referencia):
    """A11 con el criterio nuevo: se marca el segundo, y se detecta aunque los
    títulos estén escritos distinto."""
    datos = lote_nacional(
        [item("Berserk Deluxe", 5, isbn=BERSERK), item("Berserk ed. deluxe", 5, isbn=BERSERK)],
        referencia,
    )

    respuesta = client_admin.post(URL_NACIONAL, datos)

    assert respuesta.status_code == 200
    assert not respuesta.context["formset"].errors[0]
    assert respuesta.context["formset"].errors[1]["titulo"]


@pytest.mark.django_db
def test_la_ficha_muestra_el_isbn(client_admin):
    producto = ProductoFactory(isbn=BERSERK)

    contenido = client_admin.get(
        reverse("catalog:producto_detalle", args=[producto.pk])
    ).content.decode()

    assert BERSERK in contenido


@pytest.mark.django_db
def test_dos_ediciones_del_mismo_tomo_tienen_isbn_distinto(client_admin):
    """Es la razón por la que el ISBN resuelve lo que A13 resolvía con esfuerzo:
    el B6 y el Deluxe del mismo volumen son dos ediciones y dos ISBN."""
    editorial = EditorialFactory()
    tipo = TipoFactory(nombre="Manga")
    b6 = FormatoFactory(nombre="B6")
    deluxe = FormatoFactory(nombre="Deluxe")
    PrecioReferenciaFactory(editorial=editorial, tipo=tipo, formato=b6, pvp="12500")
    PrecioReferenciaFactory(editorial=editorial, tipo=tipo, formato=deluxe, pvp="28000")

    ProductoFactory(
        titulo="Berserk", volumen=5, editorial=editorial, tipo=tipo, formato=b6, isbn=BERSERK
    )
    otra_edicion = ProductoFactory(
        titulo="Berserk",
        volumen=5,
        editorial=editorial,
        tipo=tipo,
        formato=deluxe,
        isbn=BLUE_PERIOD,
        precio=Decimal("28000"),
    )

    assert Producto.objects.count() == 2
    assert otra_edicion.isbn != BERSERK
