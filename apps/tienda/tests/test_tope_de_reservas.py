"""El tope de las reservas de pre-venta (plan 00 de tope de reservas, B-07-041).

Cada Cliente puede tener hasta el «máximo de unidades por reserva» de Parámetros
de una misma pre-venta, **contando lo que ya reservó en pedidos en curso**: la
línea del carrito más los pedidos ni cancelados ni entregados. Se aplica al
agregar (`CO-083`), al cambiar la cantidad (`CO-084`) y en la consulta (`CO-178`),
que marca la línea que se pasa y así el pago no avanza (`CO-179`).
"""

import pytest
from django.urls import reverse

from apps.catalog.models import Producto
from apps.catalog.tests.factories import ProductoFactory
from apps.core.models import ConfiguracionSistema
from apps.pedidos.models import LineaPedido, Pedido
from apps.pedidos.tests.util import reservar
from apps.tienda import carrito as servicio
from apps.tienda.models import Carrito, LineaCarrito
from apps.tienda.tests.compra_util import URL_PAGAR, fijar_parametros

pytestmark = pytest.mark.django_db


@pytest.fixture
def berserk(db):
    return ProductoFactory(titulo="Berserk 42", estado=Producto.PRE_VENTA, stock=0)


@pytest.fixture
def navegador(client, cliente):
    client.force_login(cliente)
    return client


def agregar(client, producto, cantidad):
    return client.post(reverse("tienda:agregar", args=[producto.pk]), {"cantidad": cantidad})


def avisos(client):
    respuesta = client.get(reverse("tienda:carrito"))
    return [str(m) for m in respuesta.context["messages"]]


def test_CO083_el_tope_cuenta_lo_reservado_en_pedidos_en_curso(navegador, cliente, berserk):
    reservar(cliente, berserk, cantidad=3)

    agregar(navegador, berserk, 5)

    assert LineaCarrito.objects.get().cantidad == 2
    assert "contando sus pedidos" in avisos(navegador)[0]


def test_CO083_con_el_maximo_ya_reservado_no_agrega_y_lo_dice(navegador, cliente, berserk):
    reservar(cliente, berserk, cantidad=5)

    agregar(navegador, berserk, 1)

    assert not LineaCarrito.objects.exists()
    assert "Ya reservaste 5 unidades de «Berserk 42»" in avisos(navegador)[0]


def test_CO083_lo_cancelado_o_entregado_no_cuenta_como_reserva(navegador, cliente, berserk):
    cancelado, _ = reservar(cliente, berserk, cantidad=5)
    Pedido.objects.filter(pk=cancelado.pk).update(estado=Pedido.CANCELADO)
    _, linea = reservar(cliente, berserk, cantidad=5)
    LineaPedido.objects.filter(pk=linea.pk).update(estado=LineaPedido.DESPACHADO)
    _, reembolsada = reservar(cliente, berserk, cantidad=5)
    LineaPedido.objects.filter(pk=reembolsada.pk).update(estado=LineaPedido.CANCELADO_REEMBOLSO)

    agregar(navegador, berserk, 5)

    assert LineaCarrito.objects.get().cantidad == 5


def test_CO083_las_reservas_de_otro_cliente_no_cuentan(navegador, berserk, django_user_model):
    from apps.accounts.tests.factories import UsuarioFactory

    reservar(UsuarioFactory(rol="cliente"), berserk, cantidad=5)

    agregar(navegador, berserk, 5)

    assert LineaCarrito.objects.get().cantidad == 5


def test_CO083_un_activo_sigue_con_el_tope_del_stock_y_no_el_de_reserva(navegador):
    akira = ProductoFactory(titulo="Akira", stock=9)

    agregar(navegador, akira, 8)

    assert LineaCarrito.objects.get().cantidad == 8


def test_CO178_la_linea_que_pasa_el_tope_queda_marcada(navegador, cliente, berserk):
    """Ambigüedad 2 del plan: bajar el parámetro marca, no recorta."""
    agregar(navegador, berserk, 5)
    configuracion = ConfiguracionSistema.obtener()
    configuracion.maximo_reserva_preventa = 3
    configuracion.save()

    consultado = servicio.consultar(Carrito.objects.get(usuario=cliente))

    item = consultado.lineas[0]
    assert item.disponibilidad == servicio.STOCK_INSUFICIENTE
    assert item.maximo == 3
    assert not consultado.se_puede_pagar
    contenido = navegador.get(reverse("tienda:carrito")).content.decode()
    assert "Pasa el máximo por reserva · podés tener 3" in contenido
    assert LineaCarrito.objects.get().cantidad == 5


def test_CO179_la_reserva_hecha_en_otra_pestana_bloquea_el_pago(navegador, cliente, berserk):
    """La línea esperaba en el carrito mientras otro pedido completaba la reserva."""
    fijar_parametros()
    agregar(navegador, berserk, 3)
    reservar(cliente, berserk, cantidad=3)

    respuesta = navegador.post(URL_PAGAR)

    assert respuesta.url == reverse("tienda:carrito")


def test_CO086_la_fusion_respeta_el_tope_contando_los_pedidos(client, cliente, berserk):
    reservar(cliente, berserk, cantidad=4)
    persistido = Carrito.objects.create(usuario=cliente, persistencia=Carrito.PERSISTENTE)
    sesion = Carrito.objects.create(persistencia=Carrito.DE_SESION)
    for carrito in (persistido, sesion):
        LineaCarrito.objects.create(
            carrito=carrito, producto=berserk, cantidad=2, precio_vigente=1, precio_visto=1
        )

    servicio.fusionar(sesion, cliente)

    assert persistido.lineas.get().cantidad == 1


def test_la_ficha_ofrece_hasta_lo_que_queda_de_reserva(navegador, cliente, berserk):
    reservar(cliente, berserk, cantidad=2)

    contenido = navegador.get(reverse("core:tienda_producto", args=[berserk.pk])).content.decode()

    assert 'max="3"' in contenido
    assert 'Hasta <span class="datos">5</span> unidades por Cliente' in contenido


def test_la_ficha_sin_reserva_disponible_no_ofrece_reservar(navegador, cliente, berserk):
    reservar(cliente, berserk, cantidad=5)

    contenido = navegador.get(reverse("core:tienda_producto", args=[berserk.pk])).content.decode()

    assert "Ya tenés reservado el máximo por Cliente" in contenido
    assert reverse("tienda:agregar", args=[berserk.pk]) not in contenido
