"""Las consultas de compras: `CO-235`, `CO-236`, `CO-238` y `CO-240`.

Contratos redactados en la versión 14 del documento para pantallas que ya estaban construidas. Una
consulta no tiene postcondiciones: su prueba es ejercerla por la dirección real y afirmar lo que
presenta y que nada cambió (ESPECIFICACION.md, apartado 3).
"""

from datetime import timedelta

import pytest
from django.urls import reverse
from django.utils import timezone

from apps.catalog.models import Producto
from apps.catalog.tests.factories import EditorialFactory, ProductoFactory
from apps.core.models import RegistroAuditoria
from apps.restock import servicios as restock
from apps.restock.models import PropuestaRestock
from apps.suppliers import llegadas
from apps.suppliers.models import LineaPedidoProveedor, PedidoProveedor
from apps.suppliers.tests.factories import ProveedorFactory
from apps.tienda.tests.compra_util import fijar_parametros

pytestmark = pytest.mark.django_db


@pytest.fixture
def ivrea(db):
    return ProveedorFactory(razon_social="Distribuidora Ivrea", editorial=EditorialFactory())


def agotado(proveedor, titulo):
    return ProductoFactory(
        titulo=titulo, stock=0, estado=Producto.AGOTADO, editorial=proveedor.editorial
    )


def foto():
    """Todo lo que una consulta de compras podría tocar."""
    return (
        list(PropuestaRestock.objects.order_by("pk").values_list("estado", "cerrada_en")),
        list(PedidoProveedor.objects.order_by("pk").values_list("estado", "error_de_envio")),
        list(
            LineaPedidoProveedor.objects.order_by("pk").values_list(
                "cantidad_pedida", "cantidad_recibida", "estado", "respuesta"
            )
        ),
        list(Producto.objects.order_by("pk").values_list("estado", "stock")),
        RegistroAuditoria.objects.count(),
    )


@pytest.fixture
def despachada(ivrea, administrador):
    """Una propuesta con su pedido ya enviado, y otra cerrada vacía, más vieja."""
    vieja = restock.armar_a_mano(administrador)
    restock.cerrar_vacia(vieja, administrador)
    PropuestaRestock.objects.filter(pk=vieja.pk).update(
        fecha_generacion=timezone.now() - timedelta(days=30)
    )
    fijar_parametros(cantidad_minima_restock=3, margen_stock_restock=2)
    agotado(ivrea, "Akira")
    propuesta = restock.ciclo_semanal().propuesta
    restock.despachar(propuesta, ivrea.pk, administrador)
    return propuesta


# ---------------------------------------------------------------------------
# CO-235 consultarPropuestasDeRestock
# ---------------------------------------------------------------------------


def test_CO235_presenta_todas_las_propuestas_de_la_mas_reciente_a_la_mas_antigua(
    client_admin, despachada
):
    respuesta = client_admin.get(reverse("restock:propuesta_lista"))

    propuestas = list(respuesta.context["pagina"])
    assert [p.pk for p in propuestas] == list(
        PropuestaRestock.objects.order_by("-fecha_generacion", "-pk").values_list("pk", flat=True)
    )
    assert propuestas[0] == despachada
    assert PropuestaRestock.CERRADA in {p.estado for p in propuestas}


def test_CO235_consultar_las_propuestas_no_cambia_nada(client_admin, despachada):
    antes = foto()

    client_admin.get(reverse("restock:propuesta_lista"))

    assert foto() == antes


def test_CO235_sin_propuestas_presenta_la_vista_vacia(client_admin):
    respuesta = client_admin.get(reverse("restock:propuesta_lista"))

    assert "Todavía no se generó ninguna propuesta." in respuesta.content.decode()


# ---------------------------------------------------------------------------
# CO-236 consultarFichaDePropuesta
# ---------------------------------------------------------------------------


def test_CO236_la_ficha_agrupa_por_proveedor_con_el_pedido_que_genero(
    client_admin, despachada, ivrea
):
    respuesta = client_admin.get(reverse("restock:propuesta_detalle", args=[despachada.pk]))

    contenido = respuesta.content.decode()
    assert "Distribuidora Ivrea" in contenido
    pedido = PedidoProveedor.objects.get(propuesta=despachada)
    assert reverse("suppliers:pedido_detalle", args=[pedido.pk]) in contenido


def test_CO236_consultar_la_ficha_no_cambia_nada(client_admin, despachada):
    antes = foto()

    client_admin.get(reverse("restock:propuesta_detalle", args=[despachada.pk]))

    assert foto() == antes


# ---------------------------------------------------------------------------
# CO-238 consultarFichaDePedidoAProveedor
# ---------------------------------------------------------------------------


@pytest.fixture
def pedido(ivrea):
    return llegadas.registrar(
        ivrea,
        PedidoProveedor.MANUAL,
        [(agotado(ivrea, "Berserk"), 8)],
        fecha_estimada=timezone.localdate() + timedelta(days=5),
    )


def test_CO238_la_ficha_presenta_cada_linea_con_lo_pedido_y_lo_recibido(client_admin, pedido):
    respuesta = client_admin.get(reverse("suppliers:pedido_detalle", args=[pedido.pk]))

    assert respuesta.context["pedido"] == pedido
    (fila,) = respuesta.context["filas"]
    linea = pedido.lineas.get()
    assert fila["linea"] == linea
    contenido = respuesta.content.decode()
    assert "Berserk" in contenido and str(linea.cantidad_pedida) in contenido


def test_CO238_consultar_la_ficha_del_pedido_no_cambia_nada(client_admin, pedido):
    antes = foto()

    client_admin.get(reverse("suppliers:pedido_detalle", args=[pedido.pk]))

    assert foto() == antes


# ---------------------------------------------------------------------------
# CO-240 consultarPorLlegar
# ---------------------------------------------------------------------------


def test_CO240_consultar_por_llegar_no_cambia_nada(client_admin, pedido):
    antes = foto()

    respuesta = client_admin.get(reverse("suppliers:por_llegar"))

    assert respuesta.status_code == 200
    assert foto() == antes


def test_CO240_sin_nada_por_llegar_presenta_la_vista_vacia(client_admin):
    respuesta = client_admin.get(reverse("suppliers:por_llegar"))

    assert "No se espera nada." in respuesta.content.decode()


@pytest.mark.parametrize("rol", ["cajero", "cliente"])
@pytest.mark.parametrize("nombre", ["restock:propuesta_lista", "suppliers:por_llegar"])
def test_CO235_CO240_el_rol_equivocado_no_consulta_por_la_direccion_real(
    client, rol, nombre, request
):
    client.force_login(request.getfixturevalue(rol))

    assert client.get(reverse(nombre)).status_code == 403


# ---------------------------------------------------------------------------
# CO-243 cerrarLineaSinRecibir: las postcondiciones que la prueba de la pantalla no mira
# ---------------------------------------------------------------------------


def test_CO243_cerrar_la_linea_no_toca_el_stock_y_saca_la_preventa_sin_reservas(
    pedido, administrador
):
    linea = pedido.lineas.get()
    producto = Producto.objects.get(pk=linea.producto_id)
    assert producto.estado == Producto.PRE_VENTA
    stock_antes = producto.stock

    llegadas.cerrar_sin_recibir(linea, "El proveedor no lo reedita", administrador)

    producto.refresh_from_db()
    linea.refresh_from_db()
    pedido.refresh_from_db()
    assert producto.stock == stock_antes
    assert producto.estado == Producto.AGOTADO
    assert producto.especifico.fecha_llegada is None
    assert (linea.estado, linea.motivo_cierre) == (
        LineaPedidoProveedor.SIN_RECIBIR,
        "El proveedor no lo reedita",
    )
    assert pedido.estado == PedidoProveedor.CERRADO
    assert RegistroAuditoria.objects.filter(
        accion=RegistroAuditoria.CIERRE_SIN_RECIBIR, actor=administrador
    ).exists()


def test_CO243_una_linea_ya_cerrada_no_se_vuelve_a_cerrar(pedido, administrador):
    linea = pedido.lineas.get()
    llegadas.cerrar_sin_recibir(linea, "No llega", administrador)
    auditoria = RegistroAuditoria.objects.count()

    with pytest.raises(llegadas.OperacionRechazada, match="ya no está esperando"):
        llegadas.cerrar_sin_recibir(linea, "Otra vez", administrador)

    assert RegistroAuditoria.objects.count() == auditoria
