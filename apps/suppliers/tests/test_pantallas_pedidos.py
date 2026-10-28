"""Las pantallas de los pedidos a proveedores y de las propuestas pasadas (plan 00 del circuito).

Por la dirección real, como pide `CLAUDE.md` para el control de acceso. Sin código
de contrato todavía: los casos de uso nuevos esperan el que asigne el responsable.
"""

from datetime import date, timedelta

import pytest
from django.urls import reverse

from apps.accounts.tests.factories import UsuarioFactory
from apps.catalog.models import Producto
from apps.catalog.tests.factories import EditorialFactory, ProductoFactory
from apps.pedidos.tests.util import reservar
from apps.restock import servicios as restock
from apps.suppliers import llegadas
from apps.suppliers.models import LineaPedidoProveedor, PedidoProveedor
from apps.suppliers.tests.factories import ProveedorFactory
from apps.tienda.tests.compra_util import fijar_parametros

pytestmark = pytest.mark.django_db


@pytest.fixture
def ivrea(db):
    return ProveedorFactory(razon_social="Distribuidora Ivrea", editorial=EditorialFactory())


@pytest.fixture
def pedido(ivrea):
    producto = ProductoFactory(
        titulo="Akira", stock=0, estado=Producto.AGOTADO, editorial=ivrea.editorial
    )
    return llegadas.registrar(ivrea, PedidoProveedor.MANUAL, [(producto, 6)])


def direcciones(pedido):
    linea = pedido.lineas.get()
    return [
        reverse("suppliers:pedido_lista"),
        reverse("suppliers:pedido_nuevo"),
        reverse("suppliers:pedido_detalle", args=[pedido.pk]),
        reverse("suppliers:pedido_cerrar_linea", args=[linea.pk]),
        reverse("restock:propuesta_lista"),
    ]


@pytest.mark.parametrize("rol", ["cajero", "cliente"])
def test_el_rol_equivocado_recibe_403_en_cada_pantalla(client, pedido, rol):
    client.force_login(UsuarioFactory(rol=rol))

    for url in direcciones(pedido):
        assert client.get(url).status_code == 403, url
    respuesta = client.post(
        reverse("suppliers:pedido_llegada", args=[pedido.pk]),
        {f"llegaron_{pedido.lineas.get().pk}": "6", "confirmar": "1"},
    )
    assert respuesta.status_code == 403
    assert pedido.lineas.get().cantidad_recibida == 0


def test_sin_sesion_lleva_al_ingreso(client, pedido):
    respuesta = client.get(reverse("suppliers:pedido_lista"))

    assert respuesta.status_code == 302
    assert reverse("accounts:login") in respuesta.url


def test_la_lista_muestra_lo_que_esta_por_llegar(client_admin, pedido):
    contenido = client_admin.get(reverse("suppliers:pedido_lista")).content.decode()

    assert f"#{pedido.pk}" in contenido
    assert "Distribuidora Ivrea" in contenido
    cerrados = client_admin.get(reverse("suppliers:pedido_lista"), {"estado": "cerrados"})
    assert f"#{pedido.pk}<" not in cerrados.content.decode()


def test_la_llegada_se_revisa_antes_y_no_cambia_nada_hasta_confirmar(client_admin, pedido, cliente):
    reservar(cliente, pedido.lineas.get().producto, cantidad=2)
    linea = pedido.lineas.get()
    url = reverse("suppliers:pedido_llegada", args=[pedido.pk])

    revision = client_admin.post(url, {f"llegaron_{linea.pk}": "4"})

    fila = revision.context["filas"][0]
    assert (fila["unidades"], fila["cubre"], fila["a_la_venta"]) == (4, 2, 2)
    assert "Llegada parcial" in revision.content.decode()
    linea.refresh_from_db()
    assert linea.cantidad_recibida == 0

    client_admin.post(url, {f"llegaron_{linea.pk}": "4", "confirmar": "1"})

    linea.refresh_from_db()
    assert (linea.cantidad_recibida, linea.estado) == (4, LineaPedidoProveedor.PARCIAL)


@pytest.mark.parametrize("valor", ["-3", "dos", ""])
def test_una_llegada_mal_escrita_o_vacia_no_registra(client_admin, pedido, valor):
    linea = pedido.lineas.get()

    respuesta = client_admin.post(
        reverse("suppliers:pedido_llegada", args=[pedido.pk]),
        {f"llegaron_{linea.pk}": valor, "confirmar": "1"},
        follow=True,
    )

    linea.refresh_from_db()
    assert linea.cantidad_recibida == 0
    assert "Error" in respuesta.content.decode() or "Indicá" in respuesta.content.decode()


def test_cerrar_una_linea_pide_motivo_y_lo_guarda(client_admin, pedido):
    linea = pedido.lineas.get()
    url = reverse("suppliers:pedido_cerrar_linea", args=[linea.pk])

    assert "No va a llegar" in client_admin.get(url).content.decode()
    client_admin.post(url, {"motivo": ""})
    linea.refresh_from_db()
    assert linea.estado == LineaPedidoProveedor.PENDIENTE

    client_admin.post(url, {"motivo": "El proveedor no tiene stock"})
    linea.refresh_from_db()
    assert (linea.estado, linea.motivo_cierre) == (
        LineaPedidoProveedor.SIN_RECIBIR,
        "El proveedor no tiene stock",
    )


def test_nuevo_pedido_a_mano_manda_el_correo_y_abre_la_preventa(client_admin, ivrea, mailoutbox):
    producto = ProductoFactory(
        titulo="Berserk", stock=0, estado=Producto.AGOTADO, editorial=ivrea.editorial
    )
    fecha = date.today() + timedelta(days=10)

    respuesta = client_admin.post(
        reverse("suppliers:pedido_nuevo"),
        {
            "proveedor": ivrea.pk,
            "fecha_estimada": fecha.isoformat(),
            "renglon-TOTAL_FORMS": "5",
            "renglon-INITIAL_FORMS": "0",
            "renglon-0-producto": producto.codigo,
            "renglon-0-cantidad": "8",
        },
    )

    pedido = PedidoProveedor.objects.get()
    assert respuesta.url == reverse("suppliers:pedido_detalle", args=[pedido.pk])
    assert (pedido.origen, pedido.fecha_estimada) == (PedidoProveedor.MANUAL, fecha)
    assert pedido.lineas.get().cantidad_pedida == 8
    assert mailoutbox[-1].to == [ivrea.correo_comercial]
    producto.refresh_from_db()
    assert producto.estado == Producto.PRE_VENTA


def test_nuevo_pedido_con_un_codigo_que_no_existe_no_sale(client_admin, ivrea, mailoutbox):
    respuesta = client_admin.post(
        reverse("suppliers:pedido_nuevo"),
        {
            "proveedor": ivrea.pk,
            "renglon-TOTAL_FORMS": "5",
            "renglon-INITIAL_FORMS": "0",
            "renglon-0-producto": "NO-EXISTE",
            "renglon-0-cantidad": "2",
        },
    )

    assert respuesta.status_code == 200
    assert "No hay un producto con el código o ISBN «NO-EXISTE»" in respuesta.content.decode()
    assert not PedidoProveedor.objects.exists()
    assert mailoutbox == []


def test_las_propuestas_pasadas_se_ven_con_sus_pedidos(client_admin, ivrea, administrador):
    fijar_parametros(cantidad_minima_restock=3, margen_stock_restock=2)
    ProductoFactory(stock=0, estado=Producto.AGOTADO, editorial=ivrea.editorial)
    propuesta = restock.ciclo_semanal().propuesta
    restock.despachar(propuesta, ivrea.pk, administrador)

    lista = client_admin.get(reverse("restock:propuesta_lista")).content.decode()
    ficha = client_admin.get(reverse("restock:propuesta_detalle", args=[propuesta.pk]))

    assert reverse("restock:propuesta_detalle", args=[propuesta.pk]) in lista
    contenido = ficha.content.decode()
    assert "Pedidos que salieron" in contenido
    assert reverse("suppliers:pedido_detalle", args=[PedidoProveedor.objects.get().pk]) in contenido


def test_CO072_el_despacho_lleva_la_llegada_estimada(client_admin, ivrea):
    fijar_parametros(cantidad_minima_restock=3, margen_stock_restock=2)
    ProductoFactory(stock=0, estado=Producto.AGOTADO, editorial=ivrea.editorial)
    restock.ciclo_semanal()
    fecha = date.today() + timedelta(days=7)

    client_admin.post(
        reverse("restock:proveedor", args=[ivrea.pk]),
        {"accion": "despachar", "fecha_estimada": fecha.isoformat()},
    )

    assert PedidoProveedor.objects.get().fecha_estimada == fecha


def test_una_fecha_imposible_se_toma_como_sin_fecha(client_admin, ivrea):
    fijar_parametros(cantidad_minima_restock=3, margen_stock_restock=2)
    ProductoFactory(stock=0, estado=Producto.AGOTADO, editorial=ivrea.editorial)
    restock.ciclo_semanal()

    client_admin.post(
        reverse("restock:proveedor", args=[ivrea.pk]),
        {"accion": "despachar", "fecha_estimada": "2026-02-31"},
    )

    assert PedidoProveedor.objects.get().fecha_estimada is None
