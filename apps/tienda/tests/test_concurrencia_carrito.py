"""`CO-083` bajo concurrencia real: dos pestañas suman el mismo producto a la vez.

Hilos reales contra PostgreSQL (plan 00, D4-05). El carrito se toma con bloqueo y
la línea es única por producto: tiene que quedar **una línea con la suma** de las
dos, sin un error 500 por la restricción de unicidad.
"""

import pytest
from django.urls import reverse

from apps.accounts.models import Usuario
from apps.accounts.tests.factories import UsuarioFactory
from apps.catalog.tests.factories import ProductoFactory
from apps.core.tests.concurrencia import a_la_vez, errores_internos, sesion_de
from apps.tienda.models import LineaCarrito

REPETICIONES = 10

pytestmark = pytest.mark.django_db(transaction=True)


def test_CO083_dos_pestanas_que_agregan_a_la_vez_dejan_una_linea_con_la_suma():
    for _ in range(REPETICIONES):
        cliente = UsuarioFactory(rol=Usuario.CLIENTE)
        producto = ProductoFactory(stock=10)
        url = reverse("tienda:agregar", args=[producto.pk])
        pestana_1, pestana_2 = sesion_de(cliente), sesion_de(cliente)

        respuestas = a_la_vez(
            lambda s=pestana_1: s.post(url, {"cantidad": 1}),
            lambda s=pestana_2: s.post(url, {"cantidad": 2}),
        )

        lineas = list(LineaCarrito.objects.filter(carrito__usuario=cliente))
        assert len(lineas) == 1
        assert lineas[0].cantidad == 3
        assert errores_internos(respuestas) == []
