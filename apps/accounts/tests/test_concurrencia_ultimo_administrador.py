"""I-12 bajo concurrencia real: dos Administradores se sacan el rol o se dan de baja a la vez.

Hilos reales contra PostgreSQL, por las direcciones reales de modificación
(`CO-121`) y de baja (`CO-123`). Es la carrera que el resguardo dice cubrir con
`select_for_update()` y que nunca se había probado (`DEUDA.md`, I-12; plan 00,
D4-01). Dos cosas tienen que valer en cada repetición:

- **Siempre queda al menos un Administrador activo** (I-12).
- **Ninguna de las dos peticiones termina en error 500**: la que pierde la carrera
  se rechaza con el mensaje del resguardo. Un interbloqueo que PostgreSQL corta
  abortando una transacción cumple la invariante, pero rompe mal.
"""

import pytest

from apps.accounts.models import Usuario
from apps.accounts.tests.factories import UsuarioFactory
from apps.accounts.tests.helpers_usuarios import datos_de, url_baja, url_edicion
from apps.core.tests.concurrencia import a_la_vez, sesion_de

REPETICIONES = 10

pytestmark = pytest.mark.django_db(transaction=True)


def dos_administradores():
    """Dos Administradores y nadie más. Los de la repetición anterior se borran
    **después** de crear los nuevos: I-12 vive en la base y no deja borrar al
    último Administrador activo."""
    nuevos = (
        UsuarioFactory(rol=Usuario.ADMINISTRADOR),
        UsuarioFactory(rol=Usuario.ADMINISTRADOR),
    )
    Usuario.objects.exclude(pk__in=[usuario.pk for usuario in nuevos]).delete()
    return nuevos


def activos():
    return Usuario.objects.filter(rol=Usuario.ADMINISTRADOR, estado=Usuario.ACTIVO).count()


def test_CO121_dos_administradores_que_se_sacan_el_rol_a_la_vez_dejan_uno(django_db_blocker):
    for _ in range(REPETICIONES):
        a, b = dos_administradores()
        sesion_a, sesion_b = sesion_de(a), sesion_de(b)

        respuestas = a_la_vez(
            lambda a=a, b=b, s=sesion_a: s.post(url_edicion(b), datos_de(b, rol=Usuario.CAJERO)),
            lambda a=a, b=b, s=sesion_b: s.post(url_edicion(a), datos_de(a, rol=Usuario.CAJERO)),
        )

        assert activos() >= 1
        assert [r.status_code for r in respuestas if r.status_code >= 500] == []


def test_CO123_dos_administradores_que_se_dan_de_baja_a_la_vez_dejan_uno():
    for _ in range(REPETICIONES):
        a, b = dos_administradores()
        sesion_a, sesion_b = sesion_de(a), sesion_de(b)

        respuestas = a_la_vez(
            lambda b=b, s=sesion_a: s.post(url_baja(b)),
            lambda a=a, s=sesion_b: s.post(url_baja(a)),
        )

        assert activos() >= 1
        assert [r.status_code for r in respuestas if r.status_code >= 500] == []


def test_CO121_y_CO123_cruzados_dejan_uno():
    """Uno saca el rol y el otro da de baja, a la vez."""
    for _ in range(REPETICIONES):
        a, b = dos_administradores()
        sesion_a, sesion_b = sesion_de(a), sesion_de(b)

        respuestas = a_la_vez(
            lambda b=b, s=sesion_a: s.post(url_edicion(b), datos_de(b, rol=Usuario.CAJERO)),
            lambda a=a, s=sesion_b: s.post(url_baja(a)),
        )

        assert activos() >= 1
        assert [r.status_code for r in respuestas if r.status_code >= 500] == []
