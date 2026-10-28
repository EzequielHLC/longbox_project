"""El pedido a proveedor, el cupo de la pre-venta y la llegada (plan 00 del circuito).

Sin código de contrato todavía: los casos de uso nuevos esperan el código que les
asigne el responsable (`CLAUDE.md`). Las pruebas que tocan contratos existentes
llevan el suyo.
"""

from datetime import date, timedelta
from decimal import Decimal

import pytest
from django.urls import reverse

from apps.accounts.tests.factories import UsuarioFactory
from apps.catalog import services as catalogo
from apps.catalog.models import LoteAlta, Producto, ProductoEditorial
from apps.catalog.tests.factories import (
    EditorialFactory,
    FormatoFactory,
    ProductoFactory,
    TipoFactory,
)
from apps.core.models import ConfiguracionSistema, RegistroAuditoria
from apps.pedidos import preventa
from apps.pedidos.models import LineaPedido
from apps.pedidos.tests.util import reservar
from apps.restock import servicios as restock
from apps.restock.models import SuscripcionReposicion
from apps.suppliers import llegadas
from apps.suppliers.models import LineaPedidoProveedor, PedidoProveedor
from apps.suppliers.tests.factories import ProveedorFactory
from apps.tienda.models import LineaCarrito
from apps.tienda.tests.compra_util import fijar_parametros

pytestmark = pytest.mark.django_db


@pytest.fixture
def ivrea(db):
    editorial = EditorialFactory(nombre="Ivrea")
    return ProveedorFactory(razon_social="Distribuidora Ivrea", editorial=editorial)


def pedir(proveedor, producto, cantidad, actor=None, **referencias):
    return llegadas.registrar(
        proveedor, PedidoProveedor.MANUAL, [(producto, cantidad)], actor, **referencias
    )


def agotado(**campos):
    return ProductoFactory(stock=0, estado=Producto.AGOTADO, **campos)


# ---------------------------------------------------------------------------
# El pedido nace cuando sale
# ---------------------------------------------------------------------------


def test_CO003_una_preventa_del_lote_nace_sin_stock_y_su_cantidad_queda_pedida(
    ivrea, administrador
):
    """B-01-016: lo declarado en un ítem con fecha es lo que se pidió, no stock."""
    tipo, formato = TipoFactory(), FormatoFactory()
    fecha = date.today() + timedelta(days=20)
    lote = LoteAlta(origen=LoteAlta.NACIONAL, editorial=ivrea.editorial, tipo=tipo)
    comun = {
        "editorial": ivrea.editorial,
        "tipo": tipo,
        "formato": formato,
        "origen": ProductoEditorial.NACIONAL,
        "precio": Decimal("9000"),
        "precio_base": Decimal("9000"),
    }
    items = [
        {
            **comun,
            "titulo": "Akira",
            "volumen": 1,
            "estado": Producto.PRE_VENTA,
            "fecha_llegada": fecha,
            "stock": 12,
        },
        {**comun, "titulo": "Akira", "volumen": 2, "estado": Producto.ACTIVO, "stock": 3},
    ]

    resultado = catalogo.registrar_lote(lote=lote, items=items, actor=administrador)

    preventa_, en_mano = sorted(resultado.creados, key=lambda p: p.volumen)
    assert (preventa_.stock, preventa_.estado) == (0, Producto.PRE_VENTA)
    assert en_mano.stock == 3  # lo que no es pre-venta sí está en la mano
    linea = LineaPedidoProveedor.objects.get()
    assert (linea.producto_id, linea.cantidad_pedida) == (preventa_.pk, 12)
    assert (linea.pedido.origen, linea.pedido.proveedor, linea.pedido.lote) == (
        PedidoProveedor.LOTE,
        ivrea,
        resultado.lote,
    )
    assert linea.pedido.fecha_estimada == fecha


def test_CO072_despachar_restock_registra_el_pedido_y_abre_la_preventa_de_lo_agotado(
    ivrea, administrador
):
    fijar_parametros(cantidad_minima_restock=3, margen_stock_restock=2)
    sin_stock = agotado(editorial=ivrea.editorial, titulo="Akira")
    con_stock = ProductoFactory(stock=1, estado=Producto.ACTIVO, editorial=ivrea.editorial)
    propuesta = restock.ciclo_semanal().propuesta
    fecha = date.today() + timedelta(days=15)

    restock.despachar(propuesta, ivrea.pk, administrador, fecha_estimada=fecha)

    pedido = PedidoProveedor.objects.get()
    assert (pedido.origen, pedido.propuesta, pedido.fecha_estimada) == (
        PedidoProveedor.RESTOCK,
        propuesta,
        fecha,
    )
    assert set(pedido.lineas.values_list("producto_id", flat=True)) == {sin_stock.pk, con_stock.pk}
    sin_stock.refresh_from_db()
    con_stock.refresh_from_db()
    # Decisión 4: lo que no tiene stock se reserva; lo que tiene, se vende.
    assert sin_stock.estado == Producto.PRE_VENTA
    assert sin_stock.productoeditorial.fecha_llegada == fecha
    assert con_stock.estado == Producto.ACTIVO


def test_CO074_un_pedido_que_no_salio_no_queda_registrado(ivrea, administrador):
    from unittest import mock

    fijar_parametros(cantidad_minima_restock=3, margen_stock_restock=2)
    agotado(editorial=ivrea.editorial)
    propuesta = restock.ciclo_semanal().propuesta

    with mock.patch("apps.suppliers.pedidos.enviar_correo", side_effect=OSError("caído")):
        restock.despachar(propuesta, ivrea.pk, administrador)

    assert not PedidoProveedor.objects.exists()


# ---------------------------------------------------------------------------
# El cupo
# ---------------------------------------------------------------------------


def test_el_cupo_es_lo_pedido_menos_el_margen_menos_lo_reservado(ivrea, cliente):
    configuracion = ConfiguracionSistema.obtener()
    configuracion.margen_cupo_preventa = 10
    configuracion.save()
    producto = agotado(editorial=ivrea.editorial)
    pedir(ivrea, producto, 40)
    reservar(cliente, producto, cantidad=6)

    assert llegadas.cupo_total(producto) == 36  # las 40 figuras del responsable
    assert llegadas.cupo(producto) == 30


def test_sin_pedido_no_hay_cupo_aunque_este_en_preventa():
    producto = ProductoFactory(estado=Producto.PRE_VENTA, stock=0, pedido_en_camino=0)

    assert llegadas.cupo(producto) == 0


def test_un_producto_no_editorial_no_pasa_a_preventa(ivrea):
    """Decisión 3: la pre-venta sigue siendo editorial (I-06)."""
    from apps.catalog.tests.factories import ProductoNoEditorialFactory

    figura = ProductoNoEditorialFactory(stock=0)

    pedir(ivrea, figura, 10)

    figura.refresh_from_db()
    assert figura.estado != Producto.PRE_VENTA


def test_al_agotarse_con_un_pedido_en_camino_pasa_a_preventa(ivrea):
    producto = ProductoFactory(stock=0, estado=Producto.ACTIVO, editorial=ivrea.editorial)
    pedir(ivrea, producto, 5)  # con stock 0 ya abre; probamos el caso de venderse
    Producto.objects.filter(pk=producto.pk).update(estado=Producto.ACTIVO, stock=0)

    assert llegadas.al_agotarse(producto) is True
    producto.refresh_from_db()
    assert producto.estado == Producto.PRE_VENTA


def test_CO083_con_el_cupo_lleno_no_se_reserva_y_se_dice(client, cliente, ivrea):
    producto = agotado(editorial=ivrea.editorial, titulo="Berserk 42")
    pedir(ivrea, producto, 2)  # con el margen del 10 %: cupo 1
    reservar(cliente, producto, cantidad=1)
    client.force_login(cliente)

    client.post(reverse("tienda:agregar", args=[producto.pk]), {"cantidad": 1})

    assert not LineaCarrito.objects.filter(producto=producto).exists()
    mensajes = [str(m) for m in client.get(reverse("tienda:carrito")).context["messages"]]
    assert "La pre-venta de «Berserk 42» está completa" in mensajes[0]


def test_CO075_con_la_preventa_completa_se_puede_pedir_el_aviso(client, cliente, ivrea):
    """Ambigüedad 5 del plan: la lista de espera se avisa si llega de más."""
    producto = agotado(editorial=ivrea.editorial)
    pedir(ivrea, producto, 1)  # cupo 0 con el margen
    client.force_login(cliente)

    ficha = client.get(reverse("core:tienda_producto", args=[producto.pk])).content.decode()
    client.post(reverse("restock:aviso", args=[producto.pk]))

    assert "La pre-venta está completa" in ficha
    assert "Avisarme si llegan de más" in ficha
    assert SuscripcionReposicion.objects.filter(usuario=cliente, producto=producto).exists()


def test_CO089_el_ultimo_lugar_del_cupo_pagado_dos_veces_se_rechaza_la_segunda(cliente, ivrea):
    from apps.tienda.compra import FalloDeMaterializacion, _materializar
    from apps.tienda.models import CobroEnCurso

    producto = agotado(editorial=ivrea.editorial)
    pedir(ivrea, producto, 2)  # cupo 1

    def cobro():
        return CobroEnCurso.objects.create(
            referencia=f"ref-{CobroEnCurso.objects.count()}",
            usuario=cliente,
            lineas=[{"producto": producto.pk, "cantidad": 1, "precio": "9000", "puntos": 0}],
            monto=Decimal("9000"),
            costo_envio=Decimal("0"),
            envio={
                "direccion": "Colón 1",
                "localidad": "Córdoba",
                "provincia": "Córdoba",
                "codigo_postal": "X5000",
            },
        )

    _materializar(cobro(), "pago-1")
    with pytest.raises(FalloDeMaterializacion, match="Se completó la pre-venta"):
        _materializar(cobro(), "pago-2")


# ---------------------------------------------------------------------------
# La llegada
# ---------------------------------------------------------------------------


def test_una_llegada_parcial_cubre_reservas_y_deja_la_linea_abierta(ivrea, cliente, administrador):
    producto = agotado(editorial=ivrea.editorial)
    pedido = pedir(ivrea, producto, 10)
    _, reserva = reservar(cliente, producto, cantidad=2)
    linea = pedido.lineas.get()

    llegadas.registrar_llegada(pedido, {linea.pk: 4}, administrador)

    linea.refresh_from_db()
    reserva.refresh_from_db()
    producto.refresh_from_db()
    assert (linea.cantidad_recibida, linea.estado) == (4, LineaPedidoProveedor.PARCIAL)
    assert reserva.estado == LineaPedido.DISPONIBLE
    assert producto.stock == 2  # 4 llegaron, 2 cubrieron la reserva
    assert PedidoProveedor.objects.get().estado == PedidoProveedor.ABIERTO
    assert RegistroAuditoria.objects.filter(accion=RegistroAuditoria.LLEGADA_PEDIDO).exists()


def test_llegar_todo_o_de_mas_cierra_el_pedido_y_queda_auditado(ivrea, administrador):
    producto = ProductoFactory(stock=2, estado=Producto.ACTIVO, editorial=ivrea.editorial)
    pedido = pedir(ivrea, producto, 5)
    linea = pedido.lineas.get()

    llegadas.registrar_llegada(pedido, {linea.pk: 6}, administrador)

    linea.refresh_from_db()
    producto.refresh_from_db()
    assert (linea.cantidad_recibida, linea.estado) == (6, LineaPedidoProveedor.RECIBIDA)
    assert (producto.stock, producto.estado) == (8, Producto.ACTIVO)
    assert PedidoProveedor.objects.get().estado == PedidoProveedor.CERRADO
    detalle = RegistroAuditoria.objects.get(accion=RegistroAuditoria.LLEGADA_PEDIDO).detalle
    assert "de más" in detalle


def test_CO077_lo_que_llega_avisa_a_la_lista_de_espera(
    ivrea, administrador, mailoutbox, django_capture_on_commit_callbacks
):
    producto = ProductoFactory(stock=1, estado=Producto.ACTIVO, editorial=ivrea.editorial)
    pedido = pedir(ivrea, producto, 3)
    suscriptor = UsuarioFactory(rol="cliente")
    Producto.objects.filter(pk=producto.pk).update(stock=0, estado=Producto.AGOTADO)
    SuscripcionReposicion.objects.create(usuario=suscriptor, producto=producto)
    producto.refresh_from_db()

    with django_capture_on_commit_callbacks(execute=True):
        llegadas.registrar_llegada(pedido, {pedido.lineas.get().pk: 3}, administrador)

    assert any(suscriptor.email in correo.to for correo in mailoutbox)


def test_una_llegada_sin_unidades_se_rechaza(ivrea, administrador):
    producto = agotado(editorial=ivrea.editorial)
    pedido = pedir(ivrea, producto, 3)

    with pytest.raises(llegadas.OperacionRechazada):
        llegadas.registrar_llegada(pedido, {pedido.lineas.get().pk: 0}, administrador)


def test_CO013_lo_confirmado_en_preventas_por_llegar_se_descuenta_del_pedido(ivrea, administrador):
    """Una sola verdad: la misma llegada no se puede registrar por las dos pantallas."""
    producto = agotado(editorial=ivrea.editorial)
    pedido = pedir(ivrea, producto, 5)

    preventa.confirmar_ingreso({producto.pk: 5}, administrador)

    linea = pedido.lineas.get()
    assert (linea.cantidad_recibida, linea.estado) == (5, LineaPedidoProveedor.RECIBIDA)
    assert PedidoProveedor.objects.get().estado == PedidoProveedor.CERRADO


def test_cerrar_sin_recibir_exige_motivo_y_saca_de_preventa_lo_que_nadie_reservo(
    ivrea, administrador
):
    producto = agotado(editorial=ivrea.editorial)
    pedido = pedir(ivrea, producto, 5)
    linea = pedido.lineas.get()

    with pytest.raises(llegadas.OperacionRechazada):
        llegadas.cerrar_sin_recibir(linea, "  ", administrador)
    con_reservas = llegadas.cerrar_sin_recibir(linea, "La editorial no lo reimprime", administrador)

    linea.refresh_from_db()
    producto.refresh_from_db()
    assert con_reservas is False
    assert (linea.estado, linea.motivo_cierre) == (
        LineaPedidoProveedor.SIN_RECIBIR,
        "La editorial no lo reimprime",
    )
    assert producto.estado == Producto.AGOTADO
    assert RegistroAuditoria.objects.filter(accion=RegistroAuditoria.CIERRE_SIN_RECIBIR).exists()


def test_cerrar_sin_recibir_con_reservas_deja_la_preventa_y_lo_avisa(ivrea, cliente, administrador):
    producto = agotado(editorial=ivrea.editorial)
    pedido = pedir(ivrea, producto, 5)
    reservar(cliente, producto, cantidad=1)

    con_reservas = llegadas.cerrar_sin_recibir(pedido.lineas.get(), "No llega", administrador)

    producto.refresh_from_db()
    assert con_reservas is True
    assert producto.estado == Producto.PRE_VENTA
