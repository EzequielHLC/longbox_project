"""I-20 bajo concurrencia real: dos Administradores registran ofertas solapadas a la vez.

Hilos reales contra PostgreSQL (plan 00, D4-06). El alta valida el solapamiento
con un bloqueo sobre el producto del alcance (`CO-054`): tiene que quedar **una
sola oferta** y la otra respuesta tiene que informar el conflicto, sin un 500.
"""

from datetime import timedelta

import pytest
from django.urls import reverse
from django.utils import timezone

from apps.accounts.models import Usuario
from apps.accounts.tests.factories import UsuarioFactory
from apps.catalog.models import Oferta
from apps.catalog.tests.factories import ProductoFactory
from apps.core.tests.concurrencia import a_la_vez, errores_internos, sesion_de

REPETICIONES = 5

pytestmark = pytest.mark.django_db(transaction=True)


def test_CO054_dos_ofertas_solapadas_registradas_a_la_vez_dejan_una():
    a = UsuarioFactory(rol=Usuario.ADMINISTRADOR)
    b = UsuarioFactory(rol=Usuario.ADMINISTRADOR)
    hoy = timezone.localdate()
    for indice in range(REPETICIONES):
        producto = ProductoFactory(titulo=f"Carrera {indice}")
        datos = {
            "descripcion": "Carrera",
            "fecha_inicio": (hoy + timedelta(days=1)).isoformat(),
            "fecha_vencimiento": (hoy + timedelta(days=5)).isoformat(),
            "tipo_descuento": Oferta.PORCENTAJE,
            "valor": "10",
            "alcance": Oferta.PRODUCTO,
            "producto": f"{producto.codigo} — {producto.titulo}",
        }
        sesion_a, sesion_b = sesion_de(a), sesion_de(b)
        url = reverse("catalog:oferta_alta")

        respuestas = a_la_vez(
            lambda s=sesion_a: s.post(url, datos), lambda s=sesion_b: s.post(url, datos)
        )

        assert Oferta.objects.filter(producto=producto).count() == 1
        assert errores_internos(respuestas) == []
        rechazadas = [r for r in respuestas if r.status_code == 200]
        assert len(rechazadas) == 1
        assert "Se superpone con la oferta" in rechazadas[0].content.decode()
