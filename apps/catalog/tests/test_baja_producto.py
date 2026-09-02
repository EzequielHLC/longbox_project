"""CU-10 — Dar de Baja Producto (Editorial o No Editorial), y la reactivación.

La fuente da solo la descripción resumida. De ella salen las tres reglas que
concentran estos tests:

- **La baja es lógica.** La postcondición pide conservar el producto en el
  inventario interno y en el historial de ventas, así que nunca hay un `DELETE`.
- **El informe de impacto va antes de la confirmación.** El CU lo enumera como
  parte de la decisión, no como un trámite posterior, y por eso la baja es una
  pantalla propia.
- **Los pedidos activos no se cancelan.** El CU lo dice explícitamente para
  garantizar los compromisos ya asumidos con el cliente. Hoy no hay pedidos que
  cancelar, pero la baja tampoco toca nada más que el estado.

Las cuatro categorías del informe pertenecen a Pedidos, Restock, Pricing y
Tienda, que no existen. Se declaran igual y en `None`: un cero se leería como
"no afecta a nadie", que es la conclusión equivocada para decidir una baja.

La reactivación no la describe ningún CU. Existe porque sin ella la baja es un
camino de ida y la precondición de CU-09 —un producto de baja se edita— no
serviría para nada.
"""

import pytest
from django.urls import reverse

from apps.accounts.tests.factories import UsuarioFactory
from apps.catalog.models import Producto
from apps.catalog.services import calcular_impacto_de_baja
from apps.catalog.tests.factories import ProductoFactory, ProductoNoEditorialFactory
from apps.core.models import RegistroAuditoria

pytestmark = pytest.mark.django_db


def url_baja(producto):
    return reverse("catalog:producto_baja", args=[producto.pk])


def url_reactivar(producto):
    return reverse("catalog:producto_reactivar", args=[producto.pk])


# ---------------------------------------------------------------------------
# El informe de impacto, que es el paso previo a la confirmación
# ---------------------------------------------------------------------------


def test_la_pantalla_muestra_las_cuatro_categorias(client_admin):
    """Las cuatro se declaran aunque ninguna se pueda calcular: agregar cada una
    después es llenar un hueco y no rediseñar la pantalla."""
    contenido = client_admin.get(url_baja(ProductoFactory())).content.decode()

    assert "Pedidos activos que lo incluyen" in contenido
    assert "Suscripciones de reposición" in contenido
    assert "Ofertas vigentes" in contenido
    assert "Carritos de clientes" in contenido


def test_lo_que_no_se_puede_calcular_se_dice(client_admin):
    """Un cero se leería como "no afecta a nadie"."""
    contenido = client_admin.get(url_baja(ProductoFactory())).content.decode()

    assert "No disponible todavía" in contenido


def test_el_informe_trae_el_stock_y_el_estado(client_admin):
    """No son categorías del CU. Van porque son lo único verificable hoy, y sin
    ellos la decisión se tomaría sin ningún dato del producto."""
    producto = ProductoFactory(stock=7, estado=Producto.ACTIVO)

    impacto = client_admin.get(url_baja(producto)).context["impacto"]

    assert impacto.stock == 7
    assert impacto.estado == "Activo"


def test_hoy_ninguna_categoria_se_puede_determinar():
    impacto = calcular_impacto_de_baja(ProductoFactory())

    assert impacto.todo_sin_determinar
    assert all(valor is None for _, valor in impacto.categorias)


def test_ver_el_informe_no_da_de_baja(client_admin):
    """El GET es el informe, no la acción."""
    producto = ProductoFactory(estado=Producto.ACTIVO)

    client_admin.get(url_baja(producto))

    producto.refresh_from_db()
    assert producto.estado == Producto.ACTIVO


# ---------------------------------------------------------------------------
# La baja
# ---------------------------------------------------------------------------


def test_la_baja_descataloga_el_producto(client_admin):
    producto = ProductoFactory(estado=Producto.ACTIVO)

    respuesta = client_admin.post(url_baja(producto))

    producto.refresh_from_db()
    assert producto.estado == Producto.DESCATALOGADO
    assert respuesta.url == reverse("catalog:producto_detalle", args=[producto.pk])


def test_la_baja_no_borra_nada(client_admin):
    """La postcondición pide conservarlo en el inventario y en el historial."""
    producto = ProductoFactory(stock=4)
    codigo = producto.codigo

    client_admin.post(url_baja(producto))

    producto.refresh_from_db()
    assert Producto.objects.filter(pk=producto.pk).exists()
    assert producto.codigo == codigo
    assert producto.stock == 4


def test_tambien_se_da_de_baja_un_articulo_no_editorial(client_admin):
    producto = ProductoNoEditorialFactory(estado=Producto.ACTIVO)

    client_admin.post(url_baja(producto))

    producto.refresh_from_db()
    assert producto.estado == Producto.DESCATALOGADO


def test_un_producto_en_pre_venta_se_puede_dar_de_baja(client_admin):
    producto = ProductoFactory(estado=Producto.PRE_VENTA)

    client_admin.post(url_baja(producto))

    producto.refresh_from_db()
    assert producto.estado == Producto.DESCATALOGADO


def test_la_baja_queda_registrada(client_admin, administrador):
    producto = ProductoFactory(stock=3, estado=Producto.ACTIVO)

    client_admin.post(url_baja(producto))

    registro = RegistroAuditoria.objects.get(accion=RegistroAuditoria.BAJA_PRODUCTO)
    assert registro.actor == administrador
    assert registro.objetivo_pk == producto.pk
    # El estado y el stock al momento de la baja: después de descatalogarlo, el
    # producto ya no dice desde dónde vino.
    assert "Activo" in registro.detalle
    assert "3" in registro.detalle


def test_una_segunda_baja_no_registra_de_nuevo(client_admin):
    """El clásico doble envío. La precondición se vuelve a chequear del lado del
    servidor y no solo escondiendo el botón."""
    producto = ProductoFactory(estado=Producto.ACTIVO)

    client_admin.post(url_baja(producto))
    client_admin.post(url_baja(producto))

    assert RegistroAuditoria.objects.filter(accion=RegistroAuditoria.BAJA_PRODUCTO).count() == 1


def test_un_titulo_cancelado_por_editorial_no_admite_la_baja(client_admin):
    """Es un estado terminal: un tomo cancelado no llega nunca y no se reactiva.
    Descatalogarlo lo movería a un estado del que sí se vuelve, borrando la
    única marca de que ese tomo no existe."""
    producto = ProductoFactory(estado=Producto.CANCELADO_EDITORIAL)

    client_admin.post(url_baja(producto))

    producto.refresh_from_db()
    assert producto.estado == Producto.CANCELADO_EDITORIAL


def test_la_pantalla_lo_dice_antes_de_ofrecer_el_boton(client_admin):
    producto = ProductoFactory(estado=Producto.CANCELADO_EDITORIAL)

    contenido = client_admin.get(url_baja(producto)).content.decode()

    assert "no admite otra baja" in contenido
    assert "Confirmar baja" not in contenido


# ---------------------------------------------------------------------------
# La reactivación
# ---------------------------------------------------------------------------


def test_la_reactivacion_devuelve_el_producto_al_catalogo(client_admin):
    producto = ProductoFactory(estado=Producto.DESCATALOGADO)

    client_admin.post(url_reactivar(producto))

    producto.refresh_from_db()
    assert producto.estado == Producto.ACTIVO


def test_vuelve_con_la_misma_identidad(client_admin):
    """Volver a cargarlo no sería equivalente: el código es único e inmutable,
    así que el producto reingresaría con otra identidad y sin su historial."""
    producto = ProductoFactory(estado=Producto.DESCATALOGADO, stock=6)
    codigo, precio = producto.codigo, producto.precio

    client_admin.post(url_reactivar(producto))

    producto.refresh_from_db()
    assert producto.codigo == codigo
    assert producto.precio == precio
    assert producto.stock == 6


def test_vuelve_a_activo_y_no_al_estado_anterior(client_admin):
    """Un producto que estaba en Pre-venta cuando se lo dio de baja lleva meses
    fuera del catálogo, y su fecha de llegada ya no describe nada."""
    producto = ProductoFactory(estado=Producto.PRE_VENTA)
    client_admin.post(url_baja(producto))

    client_admin.post(url_reactivar(producto))

    producto.refresh_from_db()
    assert producto.estado == Producto.ACTIVO


def test_la_reactivacion_queda_registrada(client_admin):
    producto = ProductoFactory(estado=Producto.DESCATALOGADO)

    client_admin.post(url_reactivar(producto))

    registro = RegistroAuditoria.objects.get(accion=RegistroAuditoria.REACTIVACION_PRODUCTO)
    assert registro.objetivo_pk == producto.pk


def test_reactivar_algo_que_ya_esta_activo_no_hace_nada(client_admin):
    producto = ProductoFactory(estado=Producto.ACTIVO)

    client_admin.post(url_reactivar(producto))

    assert not RegistroAuditoria.objects.filter(
        accion=RegistroAuditoria.REACTIVACION_PRODUCTO
    ).exists()


def test_el_ciclo_completo_conserva_el_historial(client_admin):
    """Es lo que la baja lógica se propuso conservar: las dos entradas apuntan al
    mismo producto y la ficha las muestra juntas."""
    producto = ProductoFactory(estado=Producto.ACTIVO)

    client_admin.post(url_baja(producto))
    client_admin.post(url_reactivar(producto))

    acciones = set(
        RegistroAuditoria.objects.filter(objetivo_pk=producto.pk).values_list("accion", flat=True)
    )
    assert RegistroAuditoria.BAJA_PRODUCTO in acciones
    assert RegistroAuditoria.REACTIVACION_PRODUCTO in acciones


# ---------------------------------------------------------------------------
# Las acciones en la ficha
# ---------------------------------------------------------------------------


def test_la_ficha_ofrece_editar_y_dar_de_baja(client_admin):
    producto = ProductoFactory(estado=Producto.ACTIVO)

    contenido = client_admin.get(
        reverse("catalog:producto_detalle", args=[producto.pk])
    ).content.decode()

    assert url_baja(producto) in contenido
    assert reverse("catalog:producto_editar", args=[producto.pk]) in contenido


def test_la_ficha_de_un_descatalogado_ofrece_reactivar_y_no_dar_de_baja(client_admin):
    producto = ProductoFactory(estado=Producto.DESCATALOGADO)

    contenido = client_admin.get(
        reverse("catalog:producto_detalle", args=[producto.pk])
    ).content.decode()

    assert url_reactivar(producto) in contenido
    assert url_baja(producto) not in contenido


def test_la_ficha_del_cajero_no_ofrece_ninguna_accion(client):
    """CU-11 paso 6 se la reserva al Administrador. No se esconde con CSS: no se
    dibuja, que es lo único que cuenta."""
    client.force_login(UsuarioFactory(rol="cajero"))
    producto = ProductoFactory()

    contenido = client.get(reverse("catalog:producto_detalle", args=[producto.pk])).content.decode()

    assert url_baja(producto) not in contenido
    assert reverse("catalog:producto_editar", args=[producto.pk]) not in contenido


# ---------------------------------------------------------------------------
# Permisos (RNF-03)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("ruta", [url_baja, url_reactivar])
def test_el_cajero_no_da_de_baja_ni_reactiva(client, ruta):
    client.force_login(UsuarioFactory(rol="cajero"))
    producto = ProductoFactory()

    assert client.get(ruta(producto)).status_code == 403
    assert client.post(ruta(producto)).status_code == 403


@pytest.mark.parametrize("ruta", [url_baja, url_reactivar])
def test_sin_sesion_redirige_al_login(client, ruta):
    assert client.get(ruta(ProductoFactory())).status_code == 302
