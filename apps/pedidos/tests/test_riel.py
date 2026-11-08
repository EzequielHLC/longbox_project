"""El riel de estados del pedido (plan 00 de interfaz, 4.2).

Los pasos salen de la tabla de transiciones del servidor y las fechas, de las
transiciones del pedido: el riel no muestra un paso que el pedido no recorre.
"""

from datetime import timedelta

import pytest
from django.urls import reverse
from django.utils import timezone

from apps.accounts.tests.factories import UsuarioFactory
from apps.pedidos.models import Pedido
from apps.pedidos.riel import recorrido, riel_de
from apps.pedidos.tests.util import crear_pedido

pytestmark = pytest.mark.django_db


def _estados(riel):
    return [paso.estado for paso in riel.pasos]


def test_el_envio_recorre_hasta_despachado():
    pedido = crear_pedido(estado=Pedido.EMPAQUETADO)

    riel = riel_de(pedido)

    assert _estados(riel) == [
        Pedido.PENDIENTE_ARMADO,
        Pedido.ARMADO,
        Pedido.EMPAQUETADO,
        Pedido.DESPACHADO,
    ]
    assert [paso.hecho for paso in riel.pasos] == [True, True, True, False]
    assert riel.actual.estado == Pedido.EMPAQUETADO
    assert not riel.interrupcion


def test_el_retiro_termina_en_el_local():
    pedido = crear_pedido(UsuarioFactory(rol="cliente"))
    pedido.modalidad = Pedido.RETIRO

    assert recorrido(pedido) == [Pedido.PENDIENTE_ARMADO, Pedido.ARMADO, Pedido.EN_LOCAL]


def test_cada_paso_lleva_la_fecha_de_su_transicion():
    pedido = crear_pedido(estado=Pedido.ARMADO, hace_dias=1)
    armado = timezone.now() - timedelta(hours=2)
    pedido.transiciones.create(
        estado_anterior=Pedido.PENDIENTE_ARMADO, estado_nuevo=Pedido.ARMADO, ocurrida_en=armado
    )

    pasos = {paso.estado: paso for paso in riel_de(pedido).pasos}

    assert pasos[Pedido.ARMADO].fecha == armado
    assert pasos[Pedido.EMPAQUETADO].fecha is None


def test_una_cancelacion_queda_en_el_ultimo_paso_alcanzado_y_se_dice():
    pedido = crear_pedido(estado=Pedido.PENDIENTE_ARMADO)
    pedido.transiciones.create(
        estado_anterior=Pedido.PENDIENTE_ARMADO, estado_nuevo=Pedido.CANCELADO
    )
    pedido.estado = Pedido.CANCELADO

    riel = riel_de(pedido)

    assert riel.interrupcion == "Cancelado"
    assert riel.actual.estado == Pedido.PENDIENTE_ARMADO


def test_esperando_la_pre_venta_no_alcanzo_ningun_paso():
    pedido = crear_pedido(estado=Pedido.ESPERANDO_PRE_VENTA)

    riel = riel_de(pedido)

    assert riel.interrupcion == "Esperando stock de pre-venta"
    assert riel.actual is None
    assert not any(paso.hecho for paso in riel.pasos)


def test_el_cliente_ve_el_riel_animable_y_el_administrador_sin_animacion(client):
    cliente = UsuarioFactory(rol="cliente")
    pedido = crear_pedido(cliente, estado=Pedido.ARMADO)
    client.force_login(cliente)

    propio = client.get(reverse("cuenta:pedido", args=[pedido.numero])).content.decode()

    assert f'data-riel="{pedido.numero}" data-riel-estado="armado"' in propio
    assert 'aria-current="step"' in propio

    client.force_login(UsuarioFactory(rol="administrador"))
    detalle = client.get(reverse("pedidos:detalle", args=[pedido.pk])).content.decode()

    assert 'class="riel' in detalle
    assert "data-riel=" not in detalle


@pytest.mark.parametrize("vista", ["cuenta:pedido", "cuenta:pedidos"])
def test_el_estado_interrumpido_se_dice_una_sola_vez_en_mi_cuenta(client, vista):
    # La cinta del riel ya dice «Esperando stock de pre-venta»: el rótulo no la repite.
    cliente = UsuarioFactory(rol="cliente")
    pedido = crear_pedido(cliente, estado=Pedido.ESPERANDO_PRE_VENTA)
    client.force_login(cliente)
    args = [pedido.numero] if vista == "cuenta:pedido" else []

    contenido = client.get(reverse(vista, args=args)).content.decode()

    # Hasta los productos: los «Movimientos» del costado son el historial, no un rótulo.
    cabecera = contenido.split('id="titulo-productos"')[0]
    assert cabecera.count("Esperando stock de pre-venta") == 1


def test_sin_interrupcion_el_estado_sigue_con_su_rotulo(client):
    cliente = UsuarioFactory(rol="cliente")
    pedido = crear_pedido(cliente, estado=Pedido.ARMADO)
    client.force_login(cliente)

    contenido = client.get(reverse("cuenta:pedido", args=[pedido.numero])).content.decode()

    assert '<span class="marca-estado marca-estado--atencion">Armado</span>' in contenido
