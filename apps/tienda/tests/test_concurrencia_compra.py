"""`CO-089` bajo concurrencia real (RNF-06; B-07-035). Hilos contra PostgreSQL.

Lo que se provoca es la carrera, no se la simula: dos avisos de pago que llegan a
la vez. El resultado tiene que ser uno de los estados válidos y nunca un tercero:
un pedido y un reembolso, nunca dos pedidos ni stock negativo.
"""

import pytest
from django.test import Client
from django.urls import reverse

from apps.catalog.models import Producto
from apps.core.tests.concurrencia import a_la_vez, errores_internos
from apps.pedidos.models import Pedido, TransaccionPago
from apps.puntos.models import LotePuntos
from apps.tienda.models import CobroEnCurso, LineaCarrito
from apps.tienda.tests.compra_util import (
    URL_AVISO_PRUEBA,
    agregar,
    aviso_firmado,
    cliente_con_direccion,
    confirmar,
    dar_puntos,
    fijar_parametros,
    producto,
)

REPETICIONES = 5

pytestmark = pytest.mark.django_db(transaction=True)


def cobro_de(prod, *, cantidad=1, cliente=None):
    """Un cliente que confirmó la compra y está en la pasarela."""
    navegador = Client()
    navegador.force_login(cliente or cliente_con_direccion())
    agregar(navegador, prod, cantidad)
    _, cobro = confirmar(navegador)
    return cobro


def enviar(cobro):
    cuerpo, firma = aviso_firmado(cobro)
    return lambda: Client(raise_request_exception=False).post(
        URL_AVISO_PRUEBA, data=cuerpo, content_type="application/json", HTTP_X_FIRMA_PASARELA=firma
    )


def test_CO089_dos_pagos_aprobados_del_ultimo_ejemplar_generan_un_solo_pedido():
    fijar_parametros()
    for _ in range(REPETICIONES):
        ultimo = producto(stock=1)
        primero, segundo = cobro_de(ultimo), cobro_de(ultimo)

        respuestas = a_la_vez(enviar(primero), enviar(segundo))

        primero.refresh_from_db()
        segundo.refresh_from_db()
        assert errores_internos(respuestas) == []
        assert Pedido.objects.filter(lineas__producto=ultimo).count() == 1
        assert Producto.objects.get(pk=ultimo.pk).stock == 0
        assert Producto.objects.get(pk=ultimo.pk).estado == Producto.AGOTADO
        assert sorted([primero.estado, segundo.estado]) == [
            CobroEnCurso.PROCESADO,
            CobroEnCurso.REEMBOLSADO,
        ]


def test_CO089_el_mismo_aviso_repetido_en_paralelo_genera_un_solo_pedido():
    fijar_parametros()
    for _ in range(REPETICIONES):
        prod = producto(stock=10)
        cobro = cobro_de(prod, cantidad=2)

        respuestas = a_la_vez(enviar(cobro), enviar(cobro), enviar(cobro))

        assert errores_internos(respuestas) == []
        assert Pedido.objects.filter(cobro=cobro).count() == 1
        assert TransaccionPago.objects.filter(referencia=f"prueba-{cobro.referencia}").count() == 1
        assert Producto.objects.get(pk=prod.pk).stock == 8


def test_CO089_el_mismo_saldo_canjeado_en_dos_compras_a_la_vez_se_gasta_una_sola_vez():
    fijar_parametros()
    for _ in range(REPETICIONES):
        cliente = cliente_con_direccion()
        dar_puntos(cliente, 300)
        cobros = []
        for _vez in range(2):
            prod = producto(precio="3000")
            navegador = Client()
            navegador.force_login(cliente)
            agregar(navegador, prod)
            linea = LineaCarrito.objects.get(carrito__usuario=cliente, producto=prod)
            navegador.post(reverse("compra:canje", args=[linea.pk]))
            _, cobro = confirmar(navegador)
            cobros.append(cobro)
            LineaCarrito.objects.filter(pk=linea.pk).delete()

        respuestas = a_la_vez(*(enviar(cobro) for cobro in cobros))

        assert errores_internos(respuestas) == []
        estados = sorted(CobroEnCurso.objects.get(pk=c.pk).estado for c in cobros)
        assert estados == [CobroEnCurso.PROCESADO, CobroEnCurso.REEMBOLSADO]
        manual = LotePuntos.objects.get(usuario=cliente, origen=LotePuntos.AJUSTE_MANUAL)
        assert (manual.disponible, manual.estado) == (0, LotePuntos.AGOTADO)
