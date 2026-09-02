"""Alta de lote de material editorial importado."""

from decimal import Decimal

import pytest

from apps.catalog.forms import ADVERTENCIA_PRECIO_MANUAL, MENSAJE_COTIZACION_EN_PESOS
from apps.catalog.models import LoteAlta, Producto, ProductoEditorial
from apps.catalog.tests.factories import EditorialFactory, ProductoFactory, TipoFactory
from apps.catalog.tests.helpers_lote import URL_IMPORTADO, item, payload
from apps.core.models import ConfiguracionSistema, RegistroAuditoria

pytestmark = pytest.mark.django_db

MARGEN = Decimal("0.40")


@pytest.fixture(autouse=True)
def margen_fijo(db):
    """Precondición del alta importada: el margen global está configurado.

    Se fija acá para que los números esperados de cada test no dependan del
    valor que tenga el `.env` de quien corre la batería.
    """
    configuracion = ConfiguracionSistema.obtener()
    configuracion.margen_ganancia = MARGEN
    configuracion.save()
    return MARGEN


@pytest.fixture
def editorial():
    return EditorialFactory(nombre="Viz Media")


@pytest.fixture
def tipo():
    return TipoFactory(nombre="Manga")


def lote_importado(items, editorial, tipo=None, **cabecera):
    """El POST de un lote importado con la calculadora de envío completa.

    El formato no se declara: en un lote importado el precio sale del costo de
    origen y no de ninguna tabla, así que el tamaño es un dato descriptivo que
    no traba el alta.
    """
    datos = {
        "editorial": editorial.pk,
        "tipo": (tipo or TipoFactory(nombre="Manga")).pk,
        "costo_envio_total": "10000",
        "valor_compra_total": "100000",
    }
    datos.update(cabecera)
    return payload(items, **datos)


# ---------------------------------------------------------------------------
# CRE y fórmula (pasos 2, 3 y 6)
# ---------------------------------------------------------------------------


def test_el_cre_y_el_margen_quedan_congelados_en_el_lote(client_admin, editorial):
    """Postcondición del CU: la auditoría tiene que poder decir con qué números
    se fijaron estos precios, y los dos cambian con el tiempo."""
    datos = lote_importado([item("Berserk", 1, costo_origen="1000")], editorial)

    client_admin.post(URL_IMPORTADO, datos)

    lote = LoteAlta.objects.get()
    assert lote.origen == LoteAlta.IMPORTADO
    assert lote.cre == Decimal("0.100000")
    assert lote.margen_aplicado == MARGEN


def test_el_precio_final_sale_de_la_formula_de_rf_10(client_admin, editorial):
    """`C × (1 + R) × (1 + M)` = 1000 × 1,1 × 1,4 = 1540."""
    datos = lote_importado([item("Berserk", 1, costo_origen="1000")], editorial)

    respuesta = client_admin.post(URL_IMPORTADO, datos)

    assert respuesta.status_code == 302
    producto = ProductoEditorial.objects.get()
    assert producto.costo_origen == Decimal("1000")
    assert producto.precio_base == Decimal("1100.00")
    assert producto.precio == Decimal("1540.00")
    assert producto.origen == ProductoEditorial.IMPORTADO


def test_el_cre_del_lote_se_aplica_a_todos_los_items(client_admin, editorial):
    datos = lote_importado(
        [
            item("Berserk", 1, costo_origen="1000"),
            item("Berserk", 2, costo_origen="2000"),
        ],
        editorial,
    )

    client_admin.post(URL_IMPORTADO, datos)

    assert ProductoEditorial.objects.get(volumen=1).precio == Decimal("1540.00")
    assert ProductoEditorial.objects.get(volumen=2).precio == Decimal("3080.00")


def test_el_costo_en_origen_es_obligatorio(client_admin, editorial):
    datos = lote_importado([item("Berserk", 1)], editorial)

    respuesta = client_admin.post(URL_IMPORTADO, datos)

    assert respuesta.status_code == 200
    assert respuesta.context["formset"].errors[0]["costo_origen"]
    assert not ProductoEditorial.objects.exists()


def test_la_calculadora_de_envio_es_obligatoria(client_admin, editorial, tipo):
    """Sin los dos totales no hay CRE, y sin CRE no hay precio."""
    datos = payload([item("Berserk", 1, costo_origen="1000")], editorial=editorial.pk, tipo=tipo.pk)

    respuesta = client_admin.post(URL_IMPORTADO, datos)

    assert respuesta.status_code == 200
    assert respuesta.context["cabecera"].errors["costo_envio_total"]
    assert not ProductoEditorial.objects.exists()


# ---------------------------------------------------------------------------
# Precio manual (paso 7 y A1)
# ---------------------------------------------------------------------------


def test_editar_el_precio_final_sin_confirmar_muestra_la_advertencia(client_admin, editorial):
    """El CU pide que el Administrador confirme. El chequeo va del lado del
    servidor: un cartel de JavaScript esquivado no debería poder romper el
    vínculo con el margen global."""
    datos = lote_importado([item("Berserk", 1, costo_origen="1000", precio="2000")], editorial)

    respuesta = client_admin.post(URL_IMPORTADO, datos)

    assert respuesta.status_code == 200
    assert ADVERTENCIA_PRECIO_MANUAL in respuesta.context["formset"].errors[0]["precio"]
    assert not ProductoEditorial.objects.exists()


def test_editar_el_precio_final_confirmado_marca_precio_manual(client_admin, editorial):
    datos = lote_importado(
        [
            item(
                "Berserk",
                1,
                costo_origen="1000",
                precio="2000",
                confirma_precio_manual="on",
            )
        ],
        editorial,
    )

    respuesta = client_admin.post(URL_IMPORTADO, datos)

    assert respuesta.status_code == 302
    producto = ProductoEditorial.objects.get()
    assert producto.precio == Decimal("2000")
    assert producto.precio_manual is True


def test_el_precio_base_no_cambia_al_editar_el_precio_final(client_admin, editorial):
    """RF-10: el precio base se almacena siempre y nunca se deriva del final.

    Es lo que permite recalcular ante un cambio de margen sin volver a pedir los
    datos del lote.
    """
    datos = lote_importado(
        [
            item(
                "Berserk",
                1,
                costo_origen="1000",
                precio="2000",
                confirma_precio_manual="on",
            )
        ],
        editorial,
    )

    client_admin.post(URL_IMPORTADO, datos)

    assert ProductoEditorial.objects.get().precio_base == Decimal("1100.00")


def test_confirmar_el_precio_calculado_no_lo_marca_como_manual(client_admin, editorial):
    """Escribir el mismo número que calculó el sistema no es editarlo."""
    datos = lote_importado([item("Berserk", 1, costo_origen="1000", precio="1540.00")], editorial)

    respuesta = client_admin.post(URL_IMPORTADO, datos)

    assert respuesta.status_code == 302
    assert ProductoEditorial.objects.get().precio_manual is False


def test_un_lote_sin_ediciones_deja_todos_los_productos_alcanzables_por_la_propagacion(
    client_admin, editorial
):
    """Para que el recálculo de CU-13 los alcance a todos por defecto."""
    datos = lote_importado(
        [
            item("Berserk", 1, costo_origen="1000"),
            item("Berserk", 2, costo_origen="1500"),
        ],
        editorial,
    )

    client_admin.post(URL_IMPORTADO, datos)

    assert ProductoEditorial.objects.filter(precio_manual=True).count() == 0


# ---------------------------------------------------------------------------
# Conversión de moneda (agregado a la fuente)
# ---------------------------------------------------------------------------


def test_la_cotizacion_convierte_el_costo_en_origen_a_pesos(client_admin, editorial):
    datos = lote_importado(
        [item("Berserk", 1, costo_origen="10")],
        editorial,
        moneda_origen="USD",
        cotizacion="1000",
    )

    respuesta = client_admin.post(URL_IMPORTADO, datos)

    assert respuesta.status_code == 302
    producto = ProductoEditorial.objects.get()
    # 10 USD → $10.000 → base $11.000 → final $15.400
    assert producto.precio_base == Decimal("11000.00")
    assert producto.precio == Decimal("15400.00")
    # El costo se guarda como se declaró, en la moneda de origen.
    assert producto.costo_origen == Decimal("10")


def test_un_lote_en_pesos_se_guarda_con_cotizacion_uno(client_admin, editorial):
    """Se guarda el 1 en vez de dejarlo en nulo: así el cálculo de cualquier
    ítem se reconstruye igual, con conversión o sin ella."""
    datos = lote_importado([item("Berserk", 1, costo_origen="1000")], editorial)

    client_admin.post(URL_IMPORTADO, datos)

    lote = LoteAlta.objects.get()
    assert lote.moneda_origen == "ARS"
    assert lote.cotizacion == Decimal("1")
    assert lote.tiene_conversion is False


@pytest.mark.parametrize("moneda", ["usd", "BRL", "XXX", "'; DROP TABLE"])
def test_una_moneda_fuera_del_catalogo_es_rechazada(client_admin, editorial, moneda):
    """El negocio importa en tres monedas y el desplegable ofrece esas tres.

    El chequeo vive en el servidor: el desplegable de la pantalla no es una
    restricción, es una comodidad.
    """
    datos = lote_importado(
        [item("Berserk", 1, costo_origen="10")],
        editorial,
        moneda_origen=moneda,
        cotizacion="1000",
    )

    respuesta = client_admin.post(URL_IMPORTADO, datos)

    assert respuesta.status_code == 200
    assert respuesta.context["cabecera"].errors["moneda_origen"]
    assert not ProductoEditorial.objects.exists()


def test_una_moneda_extranjera_sin_cotizacion_es_rechazada(client_admin, editorial):
    datos = lote_importado([item("Berserk", 1, costo_origen="10")], editorial, moneda_origen="USD")

    respuesta = client_admin.post(URL_IMPORTADO, datos)

    assert respuesta.status_code == 200
    assert respuesta.context["cabecera"].errors["cotizacion"]
    assert not ProductoEditorial.objects.exists()


def test_una_cotizacion_sobre_un_lote_en_pesos_es_rechazada(client_admin, editorial):
    """Se rechaza en vez de ignorarla: descartar en silencio un número que
    alguien escribió es la forma más rápida de que un precio salga mal sin que
    nadie se entere."""
    datos = lote_importado([item("Berserk", 1, costo_origen="10")], editorial, cotizacion="1000")

    respuesta = client_admin.post(URL_IMPORTADO, datos)

    assert respuesta.status_code == 200
    assert MENSAJE_COTIZACION_EN_PESOS in respuesta.context["cabecera"].errors["cotizacion"]
    assert not ProductoEditorial.objects.exists()


def test_la_pantalla_ofrece_la_cotizacion_de_referencia(client_admin, editorial):
    """La sugerencia se ofrece; el que decide es el Administrador."""
    respuesta = client_admin.get(URL_IMPORTADO)

    referencia = respuesta.context["cotizaciones"]
    assert set(referencia["valores"]) == {"USD", "EUR", "JPY"}
    # Va como JSON escapado y no incrustada en el JavaScript de la pantalla.
    assert 'id="cotizaciones-de-referencia"' in respuesta.content.decode()


# ---------------------------------------------------------------------------
# Estado, duplicados y auditoría
# ---------------------------------------------------------------------------


def test_el_estado_sigue_la_misma_logica_que_cu_01(client_admin, editorial):
    datos = lote_importado(
        [item("Berserk", 1, costo_origen="1000")], editorial, fecha_llegada="2026-12-01"
    )

    client_admin.post(URL_IMPORTADO, datos)

    assert ProductoEditorial.objects.get().estado == Producto.PRE_VENTA


def test_un_duplicado_se_excluye_y_el_resto_se_registra(client_admin, editorial, tipo):
    # Sin formato, igual que los ítems del lote: es la forma en que dos
    # importados del mismo tomo tienen que chocar entre sí.
    ProductoFactory(titulo="Berserk", volumen=1, editorial=editorial, tipo=tipo, formato=None)
    datos = lote_importado(
        [
            item("Berserk", 1, costo_origen="1000"),
            item("Berserk", 2, costo_origen="1000"),
        ],
        editorial,
        tipo,
    )

    respuesta = client_admin.post(URL_IMPORTADO, datos)

    assert respuesta.status_code == 302
    assert ProductoEditorial.objects.filter(origen=ProductoEditorial.IMPORTADO).count() == 1
    assert len(LoteAlta.objects.get().rechazados) == 1


def test_dos_importados_sin_formato_del_mismo_tomo_chocan_entre_si(client_admin, editorial, tipo):
    """En SQL dos nulos no son iguales, así que sin el `Coalesce` de la
    restricción el mismo tomo entraría dos veces sin que nada lo impida."""
    ProductoFactory(titulo="Berserk", volumen=1, editorial=editorial, tipo=tipo, formato=None)
    datos = lote_importado([item("Berserk", 1, costo_origen="1000")], editorial, tipo)

    client_admin.post(URL_IMPORTADO, datos)

    assert ProductoEditorial.objects.count() == 1
    assert len(LoteAlta.objects.get().rechazados) == 1


def test_la_auditoria_conserva_el_cre_y_el_margen_usados(client_admin, editorial):
    datos = lote_importado([item("Berserk", 1, costo_origen="1000")], editorial)
    client_admin.post(URL_IMPORTADO, datos)

    # El margen global cambia después del alta: la traza no se mueve.
    configuracion = ConfiguracionSistema.obtener()
    configuracion.margen_ganancia = Decimal("0.75")
    configuracion.save()

    registro = RegistroAuditoria.objects.get(accion=RegistroAuditoria.ALTA_LOTE_EDITORIAL)
    assert "CRE aplicado: 0.100000" in registro.detalle
    assert "margen vigente: 0.40" in registro.detalle
    assert LoteAlta.objects.get().margen_aplicado == MARGEN


def test_el_resumen_muestra_el_desglose_del_lote(client_admin, editorial):
    datos = lote_importado([item("Berserk", 1, costo_origen="1000")], editorial)

    respuesta = client_admin.post(URL_IMPORTADO, datos, follow=True)

    contenido = respuesta.content.decode()
    assert "Costo relativo de envío" in contenido
    # El CRE se muestra sin localizar: es un factor de cálculo, y el punto
    # decimal es lo que se compara contra la fórmula de la documentación.
    assert "0.100000" in contenido
