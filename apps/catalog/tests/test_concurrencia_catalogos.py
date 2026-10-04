"""Doble clic en el alta de un catálogo: dos envíos del mismo nombre a la vez.

Hilos reales contra PostgreSQL (plan 00, D4-04). Los dos pedidos pasan la
validación del formulario —todavía no existe ninguno— y el segundo choca contra la
restricción de unicidad de la base. Tiene que quedar **un solo registro** y el
perdedor tiene que recibir el mismo aviso de duplicado que daría el formulario,
**nunca un error 500** (B-17-016).
"""

import pytest
from django.urls import reverse

from apps.accounts.models import Usuario
from apps.accounts.tests.factories import UsuarioFactory
from apps.catalog.models import Editorial, Tipo
from apps.core.tests.concurrencia import a_la_vez, sesion_de

REPETICIONES = 10

pytestmark = pytest.mark.django_db(transaction=True)


def sesiones_de_administrador():
    admin = UsuarioFactory(rol=Usuario.ADMINISTRADOR)
    return [sesion_de(admin), sesion_de(admin)]


@pytest.mark.parametrize(
    ("ruta", "modelo", "extra"),
    [
        ("catalog:editorial_crear", Editorial, {}),
        ("catalog:tipo_crear", Tipo, {"clase": "editorial", "usa_formato": "on"}),
    ],
    ids=["editorial", "tipo"],
)
def test_CO137_y_CO141_doble_envio_del_alta_deja_uno_y_avisa_sin_error(ruta, modelo, extra):
    a, b = sesiones_de_administrador()
    url = reverse(ruta)
    for indice in range(REPETICIONES):
        datos = {"nombre": f"Doble clic {indice}", **extra}

        respuestas = a_la_vez(lambda s=a: s.post(url, datos), lambda s=b: s.post(url, datos))

        assert modelo.objects.filter(nombre__iexact=datos["nombre"]).count() == 1
        assert [r.status_code for r in respuestas if r.status_code >= 500] == []
        perdedoras = [r for r in respuestas if r.status_code == 200]
        for respuesta in perdedoras:
            assert "ya existe" in respuesta.content.decode().lower()
