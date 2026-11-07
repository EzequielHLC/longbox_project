"""Restock: la propuesta pendiente se trabaja desde su ficha (B-05-011) y se puede
armar a mano, vacía (B-05-012).

La ficha usa las mismas operaciones de `CU-RST-APR` que «Restock» (`CO-069` a
`CO-071`); lo nuevo es que cada formulario vuelve a la pantalla de la que vino.
"""

import pytest
from django.urls import reverse

from apps.catalog.models import Producto
from apps.catalog.tests.factories import EditorialFactory, ProductoFactory
from apps.core.models import RegistroAuditoria
from apps.core.tests.concurrencia import a_la_vez
from apps.restock import servicios
from apps.restock.models import PropuestaRestock
from apps.suppliers.tests.factories import ProveedorFactory
from apps.tienda.tests.compra_util import fijar_parametros

pytestmark = pytest.mark.django_db


@pytest.fixture
def propuesta(db):
    fijar_parametros(cantidad_minima_restock=3, margen_stock_restock=2)
    editorial = EditorialFactory()
    ProveedorFactory(editorial=editorial)
    for _ in range(2):
        ProductoFactory(editorial=editorial, stock=0, estado=Producto.AGOTADO)
    return servicios.ciclo_semanal().propuesta


def ficha(propuesta):
    return reverse("restock:propuesta_detalle", args=[propuesta.pk])


# ---------------------------------------------------------------------------
# B-05-011 · la ficha de la pendiente se trabaja
# ---------------------------------------------------------------------------


def test_la_ficha_de_la_pendiente_tiene_los_controles(client_admin, propuesta):
    html = client_admin.get(ficha(propuesta)).content.decode()

    assert "Guardar cantidades" in html and "Agregar un producto" in html
    assert f'name="volver" value="{ficha(propuesta)}"' in html


def test_cambiar_cantidades_desde_la_ficha_vuelve_a_la_ficha(client_admin, propuesta):
    linea = propuesta.lineas.first()
    clave = linea.producto.especifico.editorial.proveedores.get().pk

    respuesta = client_admin.post(
        reverse("restock:cantidades", args=[clave]),
        {f"cantidad-{linea.pk}": "9", "volver": ficha(propuesta)},
    )

    assert respuesta.url == ficha(propuesta) + f"#grupo-{clave}"
    linea.refresh_from_db()
    assert linea.cantidad_sugerida == 9


def test_quitar_desde_la_ficha_vuelve_a_la_ficha(client_admin, propuesta):
    linea = propuesta.lineas.first()

    respuesta = client_admin.post(
        reverse("restock:linea", args=[linea.pk]), {"accion": "quitar", "volver": ficha(propuesta)}
    )

    assert respuesta.url == ficha(propuesta)
    assert not propuesta.lineas.filter(pk=linea.pk).exists()


def test_agregar_desde_la_ficha_vuelve_a_la_ficha(client_admin, propuesta):
    otro = ProductoFactory(stock=5)

    respuesta = client_admin.post(
        reverse("restock:agregar"),
        {"producto": otro.codigo, "cantidad": "2", "volver": ficha(propuesta)},
    )

    assert respuesta.url == ficha(propuesta)
    assert propuesta.lineas.filter(producto=otro).exists()


def test_sin_volver_sigue_yendo_a_restock(client_admin, propuesta):
    linea = propuesta.lineas.first()

    respuesta = client_admin.post(reverse("restock:linea", args=[linea.pk]), {"cantidad": "4"})

    assert respuesta.url == reverse("restock:propuesta")


def test_volver_a_otro_sitio_no_se_sigue(client_admin, propuesta):
    linea = propuesta.lineas.first()

    respuesta = client_admin.post(
        reverse("restock:linea", args=[linea.pk]),
        {"cantidad": "4", "volver": "https://otro.test/robar"},
    )

    assert respuesta.url == reverse("restock:propuesta")


def test_la_ficha_de_una_cerrada_sigue_siendo_de_lectura(client_admin, propuesta):
    PropuestaRestock.objects.filter(pk=propuesta.pk).update(estado=PropuestaRestock.CERRADA)

    html = client_admin.get(ficha(propuesta)).content.decode()

    assert "Guardar cantidades" not in html and "Agregar un producto" not in html


# ---------------------------------------------------------------------------
# B-05-012 · armada a mano
# ---------------------------------------------------------------------------


def test_armar_una_a_mano_la_deja_vacía_pendiente_y_auditada(client_admin, administrador):
    respuesta = client_admin.post(reverse("restock:a_mano"))

    assert respuesta.url == reverse("restock:propuesta")
    propuesta = PropuestaRestock.objects.get()
    assert propuesta.estado == PropuestaRestock.PENDIENTE
    assert propuesta.tipo_disparo == PropuestaRestock.A_MANO
    assert not propuesta.lineas.exists()
    assert RegistroAuditoria.objects.filter(
        accion=RegistroAuditoria.PROPUESTA_RESTOCK, actor=administrador, detalle__contains="a mano"
    ).exists()
    html = client_admin.get(reverse("restock:propuesta")).content.decode()
    assert "La propuesta está vacía" in html and "Cerrar la propuesta vacía" in html


def test_a_la_armada_a_mano_se_le_cargan_productos(client_admin, administrador):
    servicios.armar_a_mano(administrador)
    tomo = ProductoFactory(stock=4)

    client_admin.post(reverse("restock:agregar"), {"producto": tomo.codigo, "cantidad": "6"})

    linea = PropuestaRestock.objects.get().lineas.get()
    assert (linea.producto_id, linea.cantidad_sugerida, linea.anadida_a_mano) == (tomo.pk, 6, True)


def test_con_una_pendiente_no_se_arma_otra(client_admin, propuesta):
    client_admin.post(reverse("restock:a_mano"))

    assert PropuestaRestock.objects.count() == 1


def test_la_armada_a_mano_no_cuenta_como_el_ciclo_de_la_semana(administrador):
    fijar_parametros(cantidad_minima_restock=3, margen_stock_restock=2)
    servicios.cerrar_vacia(servicios.armar_a_mano(administrador), administrador)
    editorial = EditorialFactory()
    ProveedorFactory(editorial=editorial)
    ProductoFactory(editorial=editorial, stock=0, estado=Producto.AGOTADO)

    resultado = servicios.ciclo_semanal()

    assert resultado.propuesta is not None


def test_cerrar_la_vacía_la_cierra_y_audita(client_admin, administrador):
    servicios.armar_a_mano(administrador)

    client_admin.post(reverse("restock:cerrar_vacia"))

    propuesta = PropuestaRestock.objects.get()
    assert propuesta.estado == PropuestaRestock.CERRADA and propuesta.cerrada_en
    assert RegistroAuditoria.objects.filter(
        accion=RegistroAuditoria.CIERRE_PROPUESTA_RESTOCK, detalle__contains="vacía"
    ).exists()


def test_una_con_productos_no_se_cierra_como_vacía(client_admin, propuesta):
    client_admin.post(reverse("restock:cerrar_vacia"))

    propuesta.refresh_from_db()
    assert propuesta.estado == PropuestaRestock.PENDIENTE


def test_cerrar_vacía_sin_pendiente_lo_dice(client_admin):
    respuesta = client_admin.post(reverse("restock:cerrar_vacia"), follow=True)

    assert "No hay una propuesta pendiente" in respuesta.content.decode()


# Foco reforzado: control de acceso y concurrencia.


@pytest.mark.parametrize("nombre", ["restock:a_mano", "restock:cerrar_vacia"])
def test_el_cajero_no_arma_ni_cierra_por_la_dirección_real(client, cajero, nombre):
    client.force_login(cajero)

    assert client.post(reverse(nombre)).status_code == 403
    assert not PropuestaRestock.objects.exists()


@pytest.mark.django_db(transaction=True)
def test_dos_administradores_a_la_vez_arman_una_sola(administrador):
    def armar():
        try:
            servicios.armar_a_mano(administrador)
        except servicios.OperacionRechazada:
            return "rechazada"
        return "armada"

    resultados = a_la_vez(armar, armar)

    assert sorted(resultados) == ["armada", "rechazada"]
    assert PropuestaRestock.objects.filter(estado=PropuestaRestock.PENDIENTE).count() == 1
