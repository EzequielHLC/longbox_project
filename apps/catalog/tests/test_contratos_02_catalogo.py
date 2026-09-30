"""Pruebas de contrato del módulo 02 · Catálogo.

Se escriben desde el contrato, según `docs/pruebas/ESPECIFICACION.md` apartado 3.

Por ahora cubre `CO-156 cancelarOperacion` en la baja y en la reactivación de
producto (CU-CAT-BAJ A1, CU-CAT-REA A1). La reactivación sumó la operación a su
DSS el 2026-09-30; el contrato ya la referenciaba.
"""

import pytest
from django.urls import reverse

from apps.catalog.models import Producto
from apps.catalog.tests.factories import ProductoFactory
from apps.core.models import RegistroAuditoria

pytestmark = pytest.mark.django_db


def _foto(producto):
    producto.refresh_from_db()
    return (producto.estado, producto.precio, producto.stock, producto.titulo)


@pytest.mark.parametrize(
    ("ruta", "estado_inicial"),
    [
        ("catalog:producto_baja", Producto.ACTIVO),
        ("catalog:producto_reactivar", Producto.DESCATALOGADO),
    ],
)
def test_CO156_abandonar_la_confirmacion_no_cambia_el_producto(client_admin, ruta, estado_inicial):
    """Postcondición: «ninguna. El objeto conserva todos sus atributos,
    asociaciones y estado. No se genera entrada de auditoría»."""
    producto = ProductoFactory(estado=estado_inicial, stock=3)
    antes = _foto(producto)
    registros = RegistroAuditoria.objects.count()

    # Abrir la confirmación y no confirmar es exactamente abandonar la operación.
    assert client_admin.get(reverse(ruta, args=[producto.pk])).status_code == 200

    assert _foto(producto) == antes
    assert RegistroAuditoria.objects.count() == registros
