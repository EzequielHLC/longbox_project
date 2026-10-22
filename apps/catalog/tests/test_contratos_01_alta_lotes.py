"""Pruebas de contrato del alta de lotes (`CU-ALT-NAC`, `CU-ALT-IMP`): V1 del plan 00.

`CO-001` a `CO-010`, más `CO-005`, que es transversal. Por la dirección real.

**Cómo se mapean al sistema construido.** El lote no se arma paso a paso en el
servidor: es un solo formulario que viaja entero al confirmar. Abrir el lote
(`CO-001`), declarar la cabecera (`CO-002`, `CO-007`, `CO-008`) y agregar
ítems (`CO-003`, `CO-009`) ocurren en la pantalla y se materializan con
`CO-006`. Por eso las postcondiciones de cada operación se verifican sobre el
estado que deja ese único envío, y las que dicen «ninguna» se verifican con que
el envío que las dispara no guarde nada. Las advertencias (`CO-004`, `CO-010`)
son la primera mitad; su confirmación (`CO-005`) se valida en el servidor.

Postcondiciones negativas: un repetido dentro del lote no guarda nada; una
advertencia sin confirmar no guarda nada; sobrescribir la cotización no toca el
respaldo de cotizaciones ni otros lotes.
"""

from datetime import timedelta
from decimal import Decimal

import pytest
from django.urls import reverse
from django.utils import timezone

from apps.catalog.forms import (
    ADVERTENCIA_PRECIO_MANUAL,
    ADVERTENCIA_PRECIO_MANUAL_NACIONAL,
    MENSAJE_REPETIDO_EN_LOTE,
    MENSAJE_REPETIDO_POR_ISBN,
)
from apps.catalog.models import LoteAlta, Producto, ProductoEditorial
from apps.catalog.tests.factories import (
    EditorialFactory,
    PrecioReferenciaFactory,
    ProductoFactory,
    TipoFactory,
)
from apps.catalog.tests.helpers_lote import (
    URL_IMPORTADO,
    URL_NACIONAL,
    item,
    lote_nacional,
    payload,
)
from apps.core import cotizaciones
from apps.core.models import ConfiguracionSistema, RegistroAuditoria

pytestmark = pytest.mark.django_db

MARGEN = Decimal("0.40")


@pytest.fixture
def referencia():
    """Precondición de CO-001 nacional: la tabla tiene al menos una combinación."""
    return PrecioReferenciaFactory(pvp=Decimal("10000"))


@pytest.fixture
def margen(db):
    """Precondición de CO-001 importado: el margen global está configurado."""
    configuracion = ConfiguracionSistema.obtener()
    configuracion.margen_ganancia = MARGEN
    configuracion.save()
    return MARGEN


def lote_importado(items, **cabecera):
    datos = {
        "editorial": EditorialFactory(nombre="Viz Media").pk,
        "tipo": TipoFactory(nombre="Manga").pk,
        "costo_envio_total": "10000",
        "valor_compra_total": "100000",
    }
    datos.update(cabecera)
    return payload(items, **datos)


# ===========================================================================
# CO-001 · iniciarLoteEditorial
# ===========================================================================


def test_CO001_abrir_la_pantalla_no_crea_ningun_lote(client_admin, referencia):
    """El lote en curso vive en la pantalla hasta confirmarse."""
    assert client_admin.get(URL_NACIONAL).status_code == 200

    assert not LoteAlta.objects.exists()


def test_CO001_a_b_c_el_lote_nacional_queda_con_su_creador_origen_y_fecha(
    client_admin, administrador, referencia
):
    antes = timezone.now()

    client_admin.post(URL_NACIONAL, lote_nacional([item("Akira", 1)], referencia))

    lote = LoteAlta.objects.get()
    assert lote.creado_por == administrador
    assert lote.origen == LoteAlta.NACIONAL
    assert antes <= lote.creado_en <= timezone.now()


def test_CO001_c_el_origen_importado_queda_fijado(client_admin, margen):
    client_admin.post(URL_IMPORTADO, lote_importado([item("Berserk", 1, costo_origen="1000")]))

    assert LoteAlta.objects.get().origen == LoteAlta.IMPORTADO


# ===========================================================================
# CO-002 · declararCabeceraLote
# ===========================================================================


def test_CO002_b_la_cabecera_asocia_editorial_tipo_y_formato(client_admin, referencia):
    client_admin.post(URL_NACIONAL, lote_nacional([item("Akira", 1)], referencia))

    lote = LoteAlta.objects.get()
    assert (lote.editorial, lote.tipo, lote.formato) == (
        referencia.editorial,
        referencia.tipo,
        referencia.formato,
    )


def test_CO002_c_la_fecha_de_llegada_declarada_queda_en_el_lote(client_admin, referencia):
    llegada = timezone.localdate() + timedelta(days=10)

    client_admin.post(
        URL_NACIONAL,
        lote_nacional([item("Akira", 1)], referencia, fecha_llegada=llegada.isoformat()),
    )

    assert LoteAlta.objects.get().fecha_llegada == llegada


def test_CO002_sin_cabecera_el_lote_es_mixto_y_no_asocia_nada(client_admin, referencia):
    client_admin.post(
        URL_NACIONAL,
        payload(
            [
                item(
                    "Akira",
                    1,
                    editorial=referencia.editorial.pk,
                    tipo=referencia.tipo.pk,
                    formato=referencia.formato.pk,
                )
            ]
        ),
    )

    lote = LoteAlta.objects.get()
    assert lote.es_mixto
    assert (lote.editorial, lote.tipo, lote.formato) == (None, None, None)


def test_CO002_salida_el_precio_de_la_combinacion_completa_o_nada(client_admin, referencia):
    url = reverse("catalog:precio_referencia")
    completa = {
        "editorial": referencia.editorial.pk,
        "tipo": referencia.tipo.pk,
        "formato": referencia.formato.pk,
    }

    assert client_admin.get(url, completa).json() == {"pvp": "10000.00"}
    assert client_admin.get(url, {**completa, "formato": ""}).json() == {"pvp": None}


# ===========================================================================
# CO-003 · agregarItemLote
# ===========================================================================


def test_CO003_c_el_precio_sale_de_la_tabla_y_el_producto_queda_asociado(client_admin, referencia):
    client_admin.post(URL_NACIONAL, lote_nacional([item("Akira", 1)], referencia))

    producto = ProductoEditorial.objects.get()
    assert producto.precio == Decimal("10000")
    assert producto.precio_referencia == referencia


def test_CO003_c_sin_combinacion_en_la_tabla_el_precio_es_el_declarado(client_admin):
    from apps.catalog.tests.factories import FormatoFactory

    PrecioReferenciaFactory()  # la tabla no está vacía, pero no tiene esta terna
    terna = {
        "editorial": EditorialFactory().pk,
        "tipo": TipoFactory().pk,
        "formato": FormatoFactory().pk,
    }

    client_admin.post(URL_NACIONAL, payload([item("Dune", 1, precio="15000")], **terna))

    producto = ProductoEditorial.objects.get()
    assert (producto.precio, producto.precio_referencia) == (Decimal("15000"), None)


def test_CO003_c_sin_portada_queda_con_imagen_pendiente(client_admin, referencia):
    client_admin.post(URL_NACIONAL, lote_nacional([item("Akira", 1)], referencia))

    assert ProductoEditorial.objects.get().portada_pendiente is True


@pytest.mark.parametrize(("dias", "estado"), [(10, Producto.PRE_VENTA), (None, Producto.ACTIVO)])
def test_CO003_c_el_estado_sigue_a_la_fecha_de_llegada(client_admin, referencia, dias, estado):
    cabecera = {}
    if dias is not None:
        cabecera["fecha_llegada"] = (timezone.localdate() + timedelta(days=dias)).isoformat()

    client_admin.post(URL_NACIONAL, lote_nacional([item("Akira", 1)], referencia, **cabecera))

    assert ProductoEditorial.objects.get().estado == estado


def test_CO003_E_un_repetido_por_la_combinacion_no_guarda_nada_y_dice_con_cual_choca(
    client_admin, referencia
):
    respuesta = client_admin.post(
        URL_NACIONAL, lote_nacional([item("Akira", 1), item("akira", 1)], referencia)
    )

    assert respuesta.status_code == 200
    assert not LoteAlta.objects.exists()
    assert not ProductoEditorial.objects.exists()
    assert MENSAJE_REPETIDO_EN_LOTE.format(numero=1) in respuesta.content.decode()


def test_CO003_E_un_repetido_por_isbn_dice_el_criterio(client_admin, referencia):
    isbn = "9780306406157"  # un ISBN-13 con su dígito verificador válido

    respuesta = client_admin.post(
        URL_NACIONAL,
        lote_nacional([item("Akira", 1, isbn=isbn), item("Otro título", 7, isbn=isbn)], referencia),
    )

    assert not ProductoEditorial.objects.exists()
    assert MENSAJE_REPETIDO_POR_ISBN.format(numero=1, isbn=isbn) in respuesta.content.decode()


# ===========================================================================
# CO-004 · fijarPrecioManualItem  ·  CO-005 · confirmarPrecioManual (nacional)
# ===========================================================================


def test_CO004_la_advertencia_sin_confirmar_no_cambia_nada(client_admin, referencia):
    """Postcondición: ninguna. El cambio ocurre recién en CO-005."""
    respuesta = client_admin.post(
        URL_NACIONAL, lote_nacional([item("Akira", 1, precio="9900")], referencia)
    )

    assert respuesta.status_code == 200
    assert ADVERTENCIA_PRECIO_MANUAL_NACIONAL in respuesta.content.decode()
    assert not LoteAlta.objects.exists()
    assert not ProductoEditorial.objects.exists()


def test_CO005_b_c_confirmado_rompe_el_vinculo_y_fija_el_precio_a_mano(client_admin, referencia):
    client_admin.post(
        URL_NACIONAL,
        lote_nacional([item("Akira", 1, precio="9900", confirma_precio_manual="on")], referencia),
    )

    producto = ProductoEditorial.objects.get()
    assert producto.precio == Decimal("9900")
    assert producto.precio_manual is True
    assert producto.precio_referencia is None


def test_CO005_la_auditoria_del_lote_registra_los_precios_a_mano(client_admin, referencia):
    """En un lote, la entrada es la consolidada de CO-006 (B-01-013)."""
    client_admin.post(
        URL_NACIONAL,
        lote_nacional(
            [item("Akira", 1), item("Akira", 2, precio="9900", confirma_precio_manual="on")],
            referencia,
        ),
    )

    (registro,) = RegistroAuditoria.objects.filter(accion=RegistroAuditoria.ALTA_LOTE_EDITORIAL)
    assert "1 con precio fijado a mano" in registro.detalle


# ===========================================================================
# CO-006 · confirmarLote
# ===========================================================================


def test_CO006_a_b_c_cada_item_es_un_producto_con_sus_asociaciones_y_valores(
    client_admin, referencia
):
    client_admin.post(
        URL_NACIONAL,
        lote_nacional([item("Akira", 1, stock=4), item("Akira", 2)], referencia),
    )

    lote = LoteAlta.objects.get()
    uno, dos = ProductoEditorial.objects.order_by("volumen")
    assert {uno.lote_id, dos.lote_id} == {lote.pk}
    assert (uno.editorial, uno.tipo, uno.formato) == (
        referencia.editorial,
        referencia.tipo,
        referencia.formato,
    )
    assert uno.codigo and dos.codigo and uno.codigo != dos.codigo
    assert (uno.stock, dos.stock) == (4, 0)
    assert uno.clave_edicion and uno.clave_edicion != dos.clave_edicion


def test_CO006_E1_un_duplicado_del_catalogo_se_excluye_con_motivo_y_el_resto_se_crea(
    client_admin, referencia
):
    ProductoFactory(
        titulo="Akira",
        volumen=1,
        editorial=referencia.editorial,
        tipo=referencia.tipo,
        formato=referencia.formato,
    )

    client_admin.post(URL_NACIONAL, lote_nacional([item("Akira", 1), item("Akira", 2)], referencia))

    lote = LoteAlta.objects.get()
    assert ProductoEditorial.objects.filter(lote=lote).count() == 1
    assert len(lote.rechazados) == 1
    assert lote.rechazados[0]


def test_CO006_una_unica_entrada_de_auditoria_consolidada(client_admin, referencia):
    client_admin.post(
        URL_NACIONAL, lote_nacional([item("Akira", n) for n in range(1, 4)], referencia)
    )

    registros = RegistroAuditoria.objects.filter(accion=RegistroAuditoria.ALTA_LOTE_EDITORIAL)
    assert registros.count() == 1
    assert "3 ítem(s) creado(s)" in registros.get().detalle


def test_CO006_importado_guarda_precio_base_y_costo_en_origen(client_admin, margen):
    client_admin.post(URL_IMPORTADO, lote_importado([item("Berserk", 1, costo_origen="1000")]))

    producto = ProductoEditorial.objects.get()
    assert (producto.costo_origen, producto.precio_base) == (Decimal("1000"), Decimal("1100.00"))


# ===========================================================================
# CO-007 · declararCalculadoraLote  ·  CO-008 · sobrescribirCotizacion
# ===========================================================================


def test_CO007_c_la_calculadora_y_el_margen_quedan_congelados_en_el_lote(client_admin, margen):
    client_admin.post(
        URL_IMPORTADO,
        lote_importado(
            [item("Berserk", 1, costo_origen="10")],
            moneda_origen="USD",
            cotizacion="1000",
            costo_envio_total="3",
            valor_compra_total="7",
        ),
    )

    lote = LoteAlta.objects.get()
    assert lote.moneda_origen == "USD"
    assert (lote.costo_envio_total, lote.valor_compra_total) == (Decimal("3"), Decimal("7"))
    assert lote.cre == Decimal("0.428571")  # 3 / 7, con seis decimales
    assert lote.margen_aplicado == MARGEN


def test_CO007_cambiar_el_margen_despues_no_cambia_el_lote(client_admin, margen):
    client_admin.post(URL_IMPORTADO, lote_importado([item("Berserk", 1, costo_origen="1000")]))
    configuracion = ConfiguracionSistema.obtener()
    configuracion.margen_ganancia = Decimal("0.90")
    configuracion.save()

    assert LoteAlta.objects.get().margen_aplicado == MARGEN


def test_CO008_c_la_cotizacion_declarada_reemplaza_a_la_del_servicio(client_admin, margen):
    respaldo = cotizaciones.RUTA_RESPALDO.read_bytes()

    client_admin.post(
        URL_IMPORTADO,
        lote_importado(
            [item("Berserk", 1, costo_origen="10")], moneda_origen="USD", cotizacion="1234.5"
        ),
    )

    lote = LoteAlta.objects.get()
    assert lote.cotizacion == Decimal("1234.5")
    # Negativa: el valor sobrescrito no vuelve al servicio de cotizaciones.
    assert cotizaciones.RUTA_RESPALDO.read_bytes() == respaldo


# ===========================================================================
# CO-009 · agregarItemLoteImportado  ·  CO-010 · fijarPrecioFinalManual
# ===========================================================================


def test_CO009_c_precio_base_y_final_salen_del_cre_y_del_margen(client_admin, margen):
    """1000 × (1 + 0,1) = 1100; 1100 × (1 + 0,4) = 1540."""
    client_admin.post(URL_IMPORTADO, lote_importado([item("Berserk", 1, costo_origen="1000")]))

    producto = ProductoEditorial.objects.get()
    assert producto.precio_base == Decimal("1100.00")
    assert producto.precio == Decimal("1540.00")


def test_CO009_A3_sin_imagen_se_registra_con_imagen_pendiente(client_admin, margen):
    client_admin.post(URL_IMPORTADO, lote_importado([item("Berserk", 1, costo_origen="1000")]))

    assert ProductoEditorial.objects.get().portada_pendiente is True


def test_CO010_la_advertencia_sin_confirmar_no_cambia_nada(client_admin, margen):
    respuesta = client_admin.post(
        URL_IMPORTADO, lote_importado([item("Berserk", 1, costo_origen="1000", precio="2000")])
    )

    assert respuesta.status_code == 200
    assert ADVERTENCIA_PRECIO_MANUAL in respuesta.content.decode()
    assert not ProductoEditorial.objects.exists()


def test_CO005_c_importado_confirmado_conserva_el_precio_base_calculado(client_admin, margen):
    client_admin.post(
        URL_IMPORTADO,
        lote_importado(
            [item("Berserk", 1, costo_origen="1000", precio="2000", confirma_precio_manual="on")]
        ),
    )

    producto = ProductoEditorial.objects.get()
    assert (producto.precio, producto.precio_manual) == (Decimal("2000"), True)
    assert producto.precio_base == Decimal("1100.00")


# ===========================================================================
# Acceso: por la dirección real, con el rol equivocado
# ===========================================================================


@pytest.mark.parametrize("url", [URL_NACIONAL, URL_IMPORTADO])
@pytest.mark.parametrize("rol", ["cajero", "cliente"])
def test_acceso_solo_el_administrador_carga_lotes(client, request, rol, url, referencia):
    from apps.accounts.tests.factories import UsuarioFactory

    client.force_login(UsuarioFactory(rol=rol))

    respuesta = client.post(url, lote_nacional([item("Akira", 1)], referencia))

    assert respuesta.status_code == 403
    assert not LoteAlta.objects.exists()
