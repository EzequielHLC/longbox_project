"""I-05, I-06 e I-09 en la base: valen **por cualquier camino** (plan 00 de cierre de deuda, D3).

Hasta acá vivían en `clean()` y en los validadores de los campos, y una escritura
que no pasara por el formulario —un `update()` de queryset como el de la
propagación de precios, SQL directo— las salteaba. Cada prueba escribe por uno de
esos caminos y comprueba que la base la rechaza; y que lo que la invariante sí
admite se sigue pudiendo escribir.
"""

from decimal import Decimal

import pytest
from django.db import IntegrityError, connection, transaction

from apps.catalog.models import (
    LoteAlta,
    Producto,
    ProductoEditorial,
    TablaPrecioReferencia,
    Tipo,
)
from apps.catalog.tests.factories import (
    PrecioReferenciaFactory,
    ProductoFactory,
    ProductoNoEditorialFactory,
    TipoFactory,
    TipoNoEditorialFactory,
)

pytestmark = pytest.mark.django_db


def rechazada(operacion, motivo=""):
    """Corre la operación en su propio punto de guardado y dice si la base la rechazó."""
    try:
        with transaction.atomic():
            operacion()
    except IntegrityError as error:
        return motivo in str(error)
    return False


# ---------------------------------------------------------------------------
# I-09 · ningún importe es negativo y ningún precio de venta es cero
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("precio", [Decimal("0"), Decimal("-1")])
def test_I09_un_precio_de_venta_cero_o_negativo_se_rechaza_aunque_sea_por_update(precio):
    producto = ProductoFactory()

    assert rechazada(lambda: Producto.objects.filter(pk=producto.pk).update(precio=precio))
    producto.refresh_from_db()
    assert producto.precio > 0


def test_I09_tambien_en_el_producto_no_editorial():
    producto = ProductoNoEditorialFactory()

    assert rechazada(lambda: Producto.objects.filter(pk=producto.pk).update(precio=0))


def test_I09_el_pvp_de_la_tabla_no_puede_ser_cero():
    fila = PrecioReferenciaFactory()

    assert rechazada(lambda: TablaPrecioReferencia.objects.filter(pk=fila.pk).update(pvp=0))


@pytest.mark.parametrize("campo", ["precio_base", "costo_origen"])
def test_I09_el_precio_base_y_el_costo_en_origen_no_son_negativos(campo):
    producto = ProductoFactory(costo_origen=Decimal("10"))

    assert rechazada(lambda: ProductoEditorial.objects.filter(pk=producto.pk).update(**{campo: -1}))


@pytest.mark.parametrize(
    "importe",
    [
        {"costo_envio_total": -1},
        {"valor_compra_total": 0},
        {"cre": -1},
        {"margen_aplicado": -1},
        {"cotizacion": 0},
    ],
    ids=["envio", "compra", "cre", "margen", "cotizacion"],
)
def test_I09_los_importes_del_lote_respetan_sus_topes_en_la_base(importe):
    lote = LoteAlta.objects.create(origen=LoteAlta.IMPORTADO)

    assert rechazada(lambda: LoteAlta.objects.filter(pk=lote.pk).update(**importe))


def test_I09_un_lote_nacional_sin_importes_se_admite():
    lote = LoteAlta.objects.create(origen=LoteAlta.NACIONAL)

    assert lote.costo_envio_total is None
    assert lote.cotizacion is None


def test_I09_un_importado_sin_costo_en_origen_y_un_precio_base_cero_se_admiten():
    """El costo en origen sólo existe en importados, y un precio base cero no es un
    precio de venta: la invariante pide no negativo, no positivo."""
    producto = ProductoFactory(costo_origen=None)

    ProductoEditorial.objects.filter(pk=producto.pk).update(precio_base=0)

    producto.refresh_from_db()
    assert producto.precio_base == 0


# ---------------------------------------------------------------------------
# I-06 · el material no editorial no admite Pre-venta ni Cancelado por editorial
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("estado", [Producto.PRE_VENTA, Producto.CANCELADO_EDITORIAL])
def test_I06_el_no_editorial_no_pasa_a_preventa_ni_a_cancelado_por_ningun_camino(estado):
    producto = ProductoNoEditorialFactory()

    assert rechazada(lambda: Producto.objects.filter(pk=producto.pk).update(estado=estado))
    producto.refresh_from_db()
    assert producto.estado == Producto.ACTIVO


@pytest.mark.parametrize("estado", [Producto.PRE_VENTA, Producto.CANCELADO_EDITORIAL])
def test_I06_el_editorial_si_los_admite(estado):
    producto = ProductoFactory()

    Producto.objects.filter(pk=producto.pk).update(estado=estado)

    producto.refresh_from_db()
    assert producto.estado == estado


# ---------------------------------------------------------------------------
# I-05 · el tipo de un producto pertenece al mismo rubro que el producto
# ---------------------------------------------------------------------------


def test_I05_un_tomo_no_toma_un_tipo_no_editorial_por_update():
    producto = ProductoFactory()
    figura = TipoNoEditorialFactory()

    assert rechazada(lambda: Producto.objects.filter(pk=producto.pk).update(tipo=figura), "I-05")


def test_I05_una_figura_no_toma_un_tipo_editorial_por_update():
    producto = ProductoNoEditorialFactory()
    manga = TipoFactory()

    assert rechazada(lambda: Producto.objects.filter(pk=producto.pk).update(tipo=manga), "I-05")


def test_I05_un_alta_por_sql_con_el_tipo_del_otro_rubro_se_rechaza():
    figura = TipoNoEditorialFactory()

    def insertar():
        with connection.cursor() as cursor:
            cursor.execute(
                "INSERT INTO catalog_producto (titulo, tipo_id, clase, estado, precio, stock,"
                " codigo_barras, descripcion, solo_adultos, portada, creado_en, actualizado_en)"
                " VALUES ('Tomo', %s, 'editorial', 'activo', 100, 1, '', '', false, '',"
                " now(), now())",
                [figura.pk],
            )

    assert rechazada(insertar, "I-05")


def test_I05_el_cambio_a_otro_tipo_del_mismo_rubro_se_admite():
    producto = ProductoFactory()
    otro = TipoFactory()

    Producto.objects.filter(pk=producto.pk).update(tipo=otro)

    producto.refresh_from_db()
    assert producto.tipo == otro


def test_I05_un_tipo_con_productos_no_cambia_de_rubro():
    producto = ProductoFactory()

    assert rechazada(
        lambda: Tipo.objects.filter(pk=producto.tipo_id).update(clase=Producto.NO_EDITORIAL), "I-05"
    )


def test_I05_un_tipo_sin_productos_si_cambia_de_rubro():
    tipo = TipoFactory()

    Tipo.objects.filter(pk=tipo.pk).update(clase=Producto.NO_EDITORIAL)

    tipo.refresh_from_db()
    assert tipo.clase == Producto.NO_EDITORIAL
