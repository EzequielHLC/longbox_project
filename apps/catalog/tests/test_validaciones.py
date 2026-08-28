"""Entradas mal puestas en la carga de lotes.

La pantalla también valida, pero lo que se prueba acá es el servidor: cada uno
de estos envíos se puede armar con las herramientas del navegador abiertas, sin
pasar por ningún control del JavaScript. Si una regla no está en este archivo,
en la práctica no existe.
"""

from datetime import timedelta
from decimal import Decimal

import pytest
from django.utils import timezone

from apps.catalog.forms import (
    IMPORTE_MAXIMO,
    MENSAJE_FECHA_PASADA,
    MENSAJE_REPETIDO_EN_LOTE,
    STOCK_MAXIMO,
    VOLUMEN_MAXIMO,
)
from apps.catalog.models import LoteAlta, Producto
from apps.catalog.tests.factories import (
    EditorialFactory,
    FormatoFactory,
    PrecioReferenciaFactory,
    TipoFactory,
)
from apps.catalog.tests.helpers_lote import (
    URL_IMPORTADO,
    URL_NACIONAL,
    item,
    lote_nacional,
    payload,
)

pytestmark = pytest.mark.django_db

AYER = (timezone.localdate() - timedelta(days=1)).isoformat()
MANANA = (timezone.localdate() + timedelta(days=1)).isoformat()


@pytest.fixture
def referencia():
    return PrecioReferenciaFactory()


def lote_importado(items, editorial, **cabecera):
    datos = {
        "editorial": editorial.pk,
        "tipo": TipoFactory(nombre="Manga").pk,
        "costo_envio_total": "10000",
        "valor_compra_total": "100000",
    }
    datos.update(cabecera)
    return payload(items, **datos)


def errores(respuesta, campo, indice=0):
    return respuesta.context["formset"].errors[indice].get(campo, [])


# ---------------------------------------------------------------------------
# Números negativos
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("campo", ["precio", "stock"])
def test_un_valor_negativo_en_el_item_es_rechazado(client_admin, referencia, campo):
    datos = lote_nacional([item("Akira", 1, **{campo: "-1"})], referencia)

    respuesta = client_admin.post(URL_NACIONAL, datos)

    assert respuesta.status_code == 200
    assert errores(respuesta, campo)
    assert not Producto.objects.exists()


def test_un_volumen_negativo_es_rechazado(client_admin, referencia):
    datos = lote_nacional([item("Akira", -1)], referencia)

    respuesta = client_admin.post(URL_NACIONAL, datos)

    assert respuesta.status_code == 200
    assert errores(respuesta, "volumen")
    assert not Producto.objects.exists()


def test_un_costo_en_origen_negativo_es_rechazado(client_admin):
    editorial = EditorialFactory()
    datos = lote_importado([item("Berserk", 1, costo_origen="-500")], editorial)

    respuesta = client_admin.post(URL_IMPORTADO, datos)

    assert respuesta.status_code == 200
    assert errores(respuesta, "costo_origen")
    assert not Producto.objects.exists()


@pytest.mark.parametrize("campo", ["costo_envio_total", "valor_compra_total"])
def test_un_total_negativo_del_lote_es_rechazado(client_admin, campo):
    editorial = EditorialFactory()
    datos = lote_importado([item("Berserk", 1, costo_origen="1000")], editorial, **{campo: "-1"})

    respuesta = client_admin.post(URL_IMPORTADO, datos)

    assert respuesta.status_code == 200
    assert respuesta.context["cabecera"].errors[campo]
    assert not LoteAlta.objects.exists()


def test_una_cotizacion_negativa_es_rechazada(client_admin):
    editorial = EditorialFactory()
    datos = lote_importado(
        [item("Berserk", 1, costo_origen="10")],
        editorial,
        moneda_origen="USD",
        cotizacion="-1200",
    )

    respuesta = client_admin.post(URL_IMPORTADO, datos)

    assert respuesta.status_code == 200
    assert respuesta.context["cabecera"].errors["cotizacion"]


# ---------------------------------------------------------------------------
# Ceros donde el cero no es un valor
# ---------------------------------------------------------------------------


def test_un_precio_en_cero_es_rechazado(client_admin, referencia):
    """Un producto de precio cero no es una promoción, es un cero de menos."""
    datos = lote_nacional([item("Akira", 1, precio="0")], referencia)

    respuesta = client_admin.post(URL_NACIONAL, datos)

    assert respuesta.status_code == 200
    assert errores(respuesta, "precio")


def test_un_valor_de_compra_en_cero_es_rechazado(client_admin):
    """Es el divisor del CRE: sin él no hay contra qué prorratear el envío."""
    editorial = EditorialFactory()
    datos = lote_importado(
        [item("Berserk", 1, costo_origen="1000")], editorial, valor_compra_total="0"
    )

    respuesta = client_admin.post(URL_IMPORTADO, datos)

    assert respuesta.status_code == 200
    assert respuesta.context["cabecera"].errors["valor_compra_total"]


def test_un_envio_en_cero_es_valido(client_admin):
    """Hay proveedores que bonifican el envío: el CRE da cero y el precio base
    termina siendo el costo. Es un caso legítimo, no un error."""
    editorial = EditorialFactory()
    datos = lote_importado(
        [item("Berserk", 1, costo_origen="1000")], editorial, costo_envio_total="0"
    )

    respuesta = client_admin.post(URL_IMPORTADO, datos)

    assert respuesta.status_code == 302
    producto = Producto.objects.get()
    assert producto.precio_base == Decimal("1000.00")
    assert LoteAlta.objects.get().cre == Decimal("0")


def test_un_stock_en_cero_es_valido(client_admin, referencia):
    datos = lote_nacional([item("Akira", 1, stock="0")], referencia)

    assert client_admin.post(URL_NACIONAL, datos).status_code == 302
    assert Producto.objects.get().stock == 0


# ---------------------------------------------------------------------------
# Valores absurdos: el cero de más que se escribe solo
# ---------------------------------------------------------------------------


def test_un_volumen_absurdo_es_rechazado(client_admin, referencia):
    datos = lote_nacional([item("Akira", VOLUMEN_MAXIMO + 1)], referencia)

    respuesta = client_admin.post(URL_NACIONAL, datos)

    assert respuesta.status_code == 200
    assert errores(respuesta, "volumen")


def test_un_stock_absurdo_es_rechazado(client_admin, referencia):
    datos = lote_nacional([item("Akira", 1, stock=STOCK_MAXIMO + 1)], referencia)

    respuesta = client_admin.post(URL_NACIONAL, datos)

    assert respuesta.status_code == 200
    assert errores(respuesta, "stock")


def test_un_precio_absurdo_es_rechazado(client_admin, referencia):
    datos = lote_nacional([item("Akira", 1, precio=IMPORTE_MAXIMO + 1)], referencia)

    respuesta = client_admin.post(URL_NACIONAL, datos)

    assert respuesta.status_code == 200
    assert errores(respuesta, "precio")


# ---------------------------------------------------------------------------
# Texto: lo que no es un número tampoco entra
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("basura", ["mil pesos", "1,5,6", "1e999", "∞", "<script>x</script>"])
def test_un_precio_que_no_es_un_numero_es_rechazado(client_admin, referencia, basura):
    datos = lote_nacional([item("Akira", 1, precio=basura)], referencia)

    respuesta = client_admin.post(URL_NACIONAL, datos)

    assert respuesta.status_code == 200
    assert errores(respuesta, "precio")
    assert not Producto.objects.exists()


@pytest.mark.parametrize("basura", ["uno", "1.5", "0x10"])
def test_un_volumen_que_no_es_entero_es_rechazado(client_admin, referencia, basura):
    datos = lote_nacional([item("Akira", basura)], referencia)

    respuesta = client_admin.post(URL_NACIONAL, datos)

    assert respuesta.status_code == 200
    assert errores(respuesta, "volumen")


def test_un_titulo_de_una_sola_letra_es_rechazado(client_admin, referencia):
    datos = lote_nacional([item("A", 1)], referencia)

    respuesta = client_admin.post(URL_NACIONAL, datos)

    assert respuesta.status_code == 200
    assert errores(respuesta, "titulo")


def test_un_titulo_de_solo_espacios_es_rechazado(client_admin, referencia):
    """Django recorta los extremos, así que el campo queda vacío y obligatorio."""
    datos = lote_nacional([item("     ", 1, precio="7000")], referencia)

    respuesta = client_admin.post(URL_NACIONAL, datos)

    assert respuesta.status_code == 200
    assert errores(respuesta, "titulo")


def test_los_espacios_de_mas_del_titulo_se_normalizan(client_admin, referencia):
    """Sin esto, "Akira  vol" y "Akira vol" serían dos productos distintos para
    cualquiera que compare sin normalizar."""
    datos = lote_nacional([item("  Akira   Edición   Deluxe ", 1)], referencia)

    client_admin.post(URL_NACIONAL, datos)

    assert Producto.objects.get().titulo == "Akira Edición Deluxe"


def test_un_estado_inventado_es_rechazado(client_admin, referencia):
    """El alta ofrece dos estados; los otros tres son consecuencia de algo
    posterior y no se pueden elegir desde acá."""
    datos = lote_nacional([item("Akira", 1, estado="cancelado_editorial")], referencia)

    respuesta = client_admin.post(URL_NACIONAL, datos)

    assert respuesta.status_code == 200
    assert errores(respuesta, "estado")
    assert not Producto.objects.exists()


def test_un_formato_inexistente_es_rechazado(client_admin):
    editorial = EditorialFactory()
    tipo = TipoFactory(nombre="Manga")
    datos = payload(
        [item("Akira", 1, formato="999999", precio="7000")],
        editorial=editorial.pk,
        tipo=tipo.pk,
    )

    respuesta = client_admin.post(URL_NACIONAL, datos)

    assert respuesta.status_code == 200
    assert errores(respuesta, "formato")


def test_un_tipo_inexistente_es_rechazado(client_admin):
    editorial = EditorialFactory()
    datos = payload([item("Akira", 1, tipo="999999", precio="7000")], editorial=editorial.pk)

    respuesta = client_admin.post(URL_NACIONAL, datos)

    assert respuesta.status_code == 200
    assert errores(respuesta, "tipo")


def test_una_editorial_inexistente_es_rechazada(client_admin):
    tipo = TipoFactory(nombre="Manga")
    formato = FormatoFactory(nombre="B6")
    datos = payload(
        [item("Akira", 1, editorial="999999", precio="7000")],
        tipo=tipo.pk,
        formato=formato.pk,
    )

    respuesta = client_admin.post(URL_NACIONAL, datos)

    assert respuesta.status_code == 200
    assert errores(respuesta, "editorial")


def test_una_editorial_inactiva_no_se_puede_elegir(client_admin):
    """Una editorial dada de baja no se ofrece, y tampoco se acepta si alguien
    manda su identificador a mano."""
    inactiva = EditorialFactory(nombre="Cerrada", activa=False)
    tipo = TipoFactory(nombre="Manga")
    formato = FormatoFactory(nombre="B6")
    datos = payload(
        [item("Akira", 1, editorial=inactiva.pk, precio="7000")],
        tipo=tipo.pk,
        formato=formato.pk,
    )

    respuesta = client_admin.post(URL_NACIONAL, datos)

    assert respuesta.status_code == 200
    assert errores(respuesta, "editorial")


# ---------------------------------------------------------------------------
# Fechas
# ---------------------------------------------------------------------------


def test_una_fecha_de_llegada_pasada_es_rechazada_en_el_item(client_admin, referencia):
    datos = lote_nacional([item("Akira", 1, fecha_llegada=AYER)], referencia)

    respuesta = client_admin.post(URL_NACIONAL, datos)

    assert respuesta.status_code == 200
    assert MENSAJE_FECHA_PASADA in errores(respuesta, "fecha_llegada")
    assert not Producto.objects.exists()


def test_una_fecha_de_llegada_pasada_es_rechazada_en_la_cabecera(client_admin, referencia):
    datos = lote_nacional([item("Akira", 1)], referencia, fecha_llegada=AYER)

    respuesta = client_admin.post(URL_NACIONAL, datos)

    assert respuesta.status_code == 200
    assert MENSAJE_FECHA_PASADA in respuesta.context["cabecera"].errors["fecha_llegada"]


def test_la_fecha_de_hoy_se_acepta(client_admin, referencia):
    """El lote que llega hoy es el caso más común de todos."""
    datos = lote_nacional([item("Akira", 1)], referencia, fecha_llegada=timezone.localdate())

    assert client_admin.post(URL_NACIONAL, datos).status_code == 302
    assert Producto.objects.get().estado == Producto.PRE_VENTA


def test_una_fecha_invalida_es_rechazada(client_admin, referencia):
    datos = lote_nacional([item("Akira", 1, fecha_llegada="2026-02-31")], referencia)

    respuesta = client_admin.post(URL_NACIONAL, datos)

    assert respuesta.status_code == 200
    assert errores(respuesta, "fecha_llegada")


def test_pre_venta_sin_fecha_es_rechazada(client_admin, referencia):
    """El ciclo que transiciona las pre-ventas busca por fecha de llegada: una
    pre-venta sin fecha no se puede vigilar y quedaría colgada para siempre."""
    datos = lote_nacional([item("Akira", 1, estado=Producto.PRE_VENTA)], referencia)

    respuesta = client_admin.post(URL_NACIONAL, datos)

    assert respuesta.status_code == 200
    assert errores(respuesta, "fecha_llegada")


def test_pre_venta_con_fecha_de_la_cabecera_se_acepta(client_admin, referencia):
    datos = lote_nacional(
        [item("Akira", 1, estado=Producto.PRE_VENTA)], referencia, fecha_llegada=MANANA
    )

    assert client_admin.post(URL_NACIONAL, datos).status_code == 302


# ---------------------------------------------------------------------------
# Repetidos dentro del mismo envío
# ---------------------------------------------------------------------------


def test_dos_items_identicos_en_el_mismo_lote_se_marcan(client_admin, referencia):
    """Distinto del duplicado contra el catálogo: este todavía se puede
    corregir sin perder nada, y avisarlo al guardar sería tarde."""
    datos = lote_nacional([item("Akira", 1), item("Akira", 1)], referencia)

    respuesta = client_admin.post(URL_NACIONAL, datos)

    assert respuesta.status_code == 200
    assert MENSAJE_REPETIDO_EN_LOTE in errores(respuesta, "titulo", indice=1)
    assert not Producto.objects.exists()


def test_el_repetido_se_detecta_sin_distinguir_mayusculas(client_admin, referencia):
    datos = lote_nacional([item("Akira", 1), item("AKIRA", 1)], referencia)

    respuesta = client_admin.post(URL_NACIONAL, datos)

    assert respuesta.status_code == 200
    assert MENSAJE_REPETIDO_EN_LOTE in errores(respuesta, "titulo", indice=1)


def test_el_primero_de_los_repetidos_no_se_marca(client_admin, referencia):
    """Solo se señala el que sobra: marcar los dos obligaría a adivinar cuál
    de los dos había que borrar."""
    datos = lote_nacional([item("Akira", 1), item("Akira", 1)], referencia)

    respuesta = client_admin.post(URL_NACIONAL, datos)

    assert not errores(respuesta, "titulo", indice=0)


def test_dos_volumenes_distintos_no_son_repetidos(client_admin, referencia):
    datos = lote_nacional([item("Akira", 1), item("Akira", 2)], referencia)

    assert client_admin.post(URL_NACIONAL, datos).status_code == 302
    assert Producto.objects.count() == 2


# ---------------------------------------------------------------------------
# Estructura del envío
# ---------------------------------------------------------------------------


def test_un_contador_de_items_manipulado_no_rompe_la_pantalla(client_admin, referencia):
    """El formulario de gestión viaja en el HTML y se puede editar a mano.

    Django lo trata como dato no confiable y devuelve un formulario inválido;
    lo que no puede pasar es que la pantalla explote con un 500.
    """
    datos = lote_nacional([item("Akira", 1)], referencia)
    datos["form-TOTAL_FORMS"] = "no es un número"

    respuesta = client_admin.post(URL_NACIONAL, datos)

    assert respuesta.status_code == 200
    assert not Producto.objects.exists()


def test_un_envio_sin_formulario_de_gestion_no_rompe_la_pantalla(client_admin, referencia):
    respuesta = client_admin.post(URL_NACIONAL, {"editorial": referencia.editorial.pk})

    assert respuesta.status_code == 200
    assert not Producto.objects.exists()


def test_los_items_vacios_se_descartan_sin_dar_error(client_admin, referencia):
    """La pantalla arranca con tres ítems en blanco: los que no se toquen no
    tienen por qué reclamar campos obligatorios."""
    datos = lote_nacional([item("Akira", 1), item("", ""), item("", "")], referencia)

    assert client_admin.post(URL_NACIONAL, datos).status_code == 302
    assert Producto.objects.count() == 1


# ---------------------------------------------------------------------------
# Portada
# ---------------------------------------------------------------------------


def test_un_archivo_que_no_es_imagen_es_rechazado(client_admin, referencia):
    from django.core.files.uploadedfile import SimpleUploadedFile

    datos = lote_nacional([item("Akira", 1)], referencia)
    datos["form-0-portada"] = SimpleUploadedFile(
        "portada.jpg", b"esto no es una imagen", content_type="image/jpeg"
    )

    respuesta = client_admin.post(URL_NACIONAL, datos)

    assert respuesta.status_code == 200
    assert errores(respuesta, "portada")
    assert not Producto.objects.exists()
