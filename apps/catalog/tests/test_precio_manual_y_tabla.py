"""Un precio fijado a mano sobrevive a los cambios de la tabla de referencia.

`CO-005` (b): confirmar un precio a mano rompe la asociación del producto con
la tabla, y por eso `CO-048` no lo alcanza. Vale para el alta por lote
(`CU-ALT-NAC` A3) y para la edición (`CU-CAT-EDI` A1). B-01-014.
"""

from decimal import Decimal

import pytest

from apps.catalog import tabla_de_precios
from apps.catalog.models import ProductoEditorial
from apps.catalog.tests.factories import PrecioReferenciaFactory
from apps.catalog.tests.helpers_lote import URL_NACIONAL, item, lote_nacional

pytestmark = pytest.mark.django_db


@pytest.fixture
def referencia():
    return PrecioReferenciaFactory(pvp=Decimal("10000"))


def test_un_precio_manual_del_lote_no_lo_pisa_un_cambio_de_la_tabla(
    client_admin, referencia, administrador
):
    client_admin.post(
        URL_NACIONAL,
        lote_nacional(
            [item("Akira", 1), item("Akira", 2, precio="9900", confirma_precio_manual="on")],
            referencia,
        ),
    )

    tabla_de_precios.confirmar_modificacion(referencia, Decimal("12000"), actor=administrador)

    assert ProductoEditorial.objects.get(volumen=1).precio == Decimal("12000")
    assert ProductoEditorial.objects.get(volumen=2).precio == Decimal("9900")


def test_el_precio_manual_del_lote_no_queda_asociado_a_la_tabla(client_admin, referencia):
    client_admin.post(
        URL_NACIONAL,
        lote_nacional([item("Akira", 2, precio="9900", confirma_precio_manual="on")], referencia),
    )

    producto = ProductoEditorial.objects.get()
    assert producto.precio_manual is True
    assert producto.precio_referencia is None
    assert tabla_de_precios.solicitar_baja(referencia) == 0


def test_un_precio_corregido_en_la_edicion_tampoco_lo_pisa_la_tabla(
    client_admin, referencia, administrador
):
    """CU-CAT-EDI A1: la misma regla que en el alta (CO-005, compartida)."""
    from apps.catalog.tests.test_edicion_producto import datos_editoriales, url

    client_admin.post(URL_NACIONAL, lote_nacional([item("Akira", 1)], referencia))
    producto = ProductoEditorial.objects.get()
    assert producto.precio_referencia == referencia

    client_admin.post(
        url(producto), datos_editoriales(producto, precio="9500", confirma_precio_manual="on")
    )
    tabla_de_precios.confirmar_modificacion(referencia, Decimal("12000"), actor=administrador)

    producto.refresh_from_db()
    assert (producto.precio, producto.precio_manual) == (Decimal("9500"), True)
    assert producto.precio_referencia is None


def test_la_base_no_admite_un_precio_manual_asociado_a_la_tabla(referencia):
    from django.db import IntegrityError, transaction

    from apps.catalog.tests.factories import ProductoFactory

    producto = ProductoFactory(precio_manual=True)
    with pytest.raises(IntegrityError), transaction.atomic():
        ProductoEditorial.objects.filter(pk=producto.pk).update(precio_referencia=referencia)
