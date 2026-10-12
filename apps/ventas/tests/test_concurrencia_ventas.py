"""`CO-082` bajo concurrencia real (RNF-06). Hilos contra PostgreSQL.

El último ejemplar, vendido a la vez en dos cajas del local y por la tienda: una
sola venta lo lleva, el stock queda en cero y nadie ve un error 500.
"""

import pytest
from django.test import Client
from django.urls import reverse

from apps.accounts.models import Usuario
from apps.accounts.tests.factories import UsuarioFactory
from apps.catalog.models import Producto
from apps.catalog.tests.factories import ProductoFactory
from apps.core.tests.concurrencia import a_la_vez, errores_internos, sesion_de
from apps.pedidos.models import Pedido
from apps.tienda.models import CobroEnCurso
from apps.tienda.tests.compra_util import (
    URL_AVISO_PRUEBA,
    agregar,
    aviso_firmado,
    cliente_con_direccion,
    confirmar,
    fijar_parametros,
)

REPETICIONES = 5

pytestmark = pytest.mark.django_db(transaction=True)


def caja_con(producto):
    sesion = sesion_de(UsuarioFactory(rol=Usuario.CAJERO))
    sesion.post(reverse("ventas:agregar"), {"producto": producto.pk, "cantidad": 1})
    return sesion


def test_CO082_el_ultimo_ejemplar_vendido_a_la_vez_en_dos_cajas_y_en_la_tienda():
    fijar_parametros()
    for _ in range(REPETICIONES):
        ultimo = ProductoFactory(stock=1)
        uno, otro = caja_con(ultimo), caja_con(ultimo)
        tienda = Client()
        tienda.force_login(cliente_con_direccion())
        agregar(tienda, ultimo)
        _, cobro = confirmar(tienda)
        cuerpo, firma = aviso_firmado(cobro)

        def cobrar(sesion):
            return lambda: sesion.post(reverse("ventas:confirmar"), {"medio": "efectivo"})

        def avisar():
            return Client(raise_request_exception=False).post(
                URL_AVISO_PRUEBA,
                data=cuerpo,
                content_type="application/json",
                HTTP_X_FIRMA_PASARELA=firma,
            )

        respuestas = a_la_vez(cobrar(uno), cobrar(otro), avisar)

        assert errores_internos(respuestas) == []
        assert Pedido.objects.filter(lineas__producto=ultimo).count() == 1
        producto = Producto.objects.get(pk=ultimo.pk)
        assert (producto.stock, producto.estado) == (0, Producto.AGOTADO)
        cobro.refresh_from_db()
        assert cobro.estado in (CobroEnCurso.PROCESADO, CobroEnCurso.REEMBOLSADO)
