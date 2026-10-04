"""Doble clic en el alta de un proveedor (`CO-060`): dos envíos idénticos a la vez.

Hilos reales contra PostgreSQL (plan 00, D4-04). La razón social y el correo
comercial son únicos en la base. Tiene que quedar un solo proveedor y el
perdedor tiene que recibir el aviso de duplicado del formulario, **nunca un error
500** (B-04-006).
"""

import pytest
from django.urls import reverse

from apps.accounts.models import Usuario
from apps.accounts.tests.factories import UsuarioFactory
from apps.core.tests.concurrencia import a_la_vez, sesion_de
from apps.suppliers.models import Proveedor

REPETICIONES = 10

pytestmark = pytest.mark.django_db(transaction=True)


def test_CO060_doble_envio_del_alta_deja_uno_y_avisa_sin_error():
    admin = UsuarioFactory(rol=Usuario.ADMINISTRADOR)
    sesiones = [sesion_de(admin), sesion_de(admin)]
    url = reverse("suppliers:proveedor_alta")

    for indice in range(REPETICIONES):
        datos = {
            "razon_social": f"Distribuidora Doble {indice}",
            "correo_comercial": f"doble{indice}@proveedor.test",
            "procesa_novedades": "on",
        }

        respuestas = a_la_vez(*[lambda s=s: s.post(url, datos) for s in sesiones])

        assert Proveedor.objects.filter(razon_social=datos["razon_social"]).count() == 1
        assert [r.status_code for r in respuestas if r.status_code >= 500] == []
