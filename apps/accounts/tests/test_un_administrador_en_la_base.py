"""I-12 en la base: siempre queda al menos un Administrador activo (plan 00 de cierre de deuda, D3).

El servicio ya lo cumplía con su bloqueo ordenado (B-13-006, probado en
`test_concurrencia_ultimo_administrador.py`). Estas pruebas escriben **por fuera
del servicio** —`update()` y `delete()` de queryset, hilos que se cruzan sin pasar
por él— y comprueban que la base no deja al sistema sin Administrador.
"""

import pytest
from django.db import DatabaseError, IntegrityError, connection, transaction

from apps.accounts.models import Usuario
from apps.accounts.tests.factories import UsuarioFactory
from apps.core.tests.concurrencia import a_la_vez


def rechazada(operacion):
    try:
        with transaction.atomic():
            operacion()
    except IntegrityError as error:
        return "I-12" in str(error)
    return False


def activos():
    return Usuario.objects.filter(rol=Usuario.ADMINISTRADOR, estado=Usuario.ACTIVO).count()


@pytest.fixture
def unico(db):
    administrador = UsuarioFactory(rol=Usuario.ADMINISTRADOR)
    Usuario.objects.filter(rol=Usuario.ADMINISTRADOR).exclude(pk=administrador.pk).update(
        rol=Usuario.CAJERO
    )
    return administrador


@pytest.mark.parametrize(
    "cambio",
    [{"rol": Usuario.CAJERO}, {"estado": Usuario.INACTIVO}],
    ids=["sin-el-rol", "dado-de-baja"],
)
def test_I12_el_unico_administrador_no_deja_de_serlo_por_update(unico, cambio):
    assert rechazada(lambda: Usuario.objects.filter(pk=unico.pk).update(**cambio))
    assert activos() == 1


def test_I12_el_unico_administrador_no_se_borra(unico):
    assert rechazada(lambda: Usuario.objects.filter(pk=unico.pk).delete())
    assert activos() == 1


def test_I12_con_otro_activo_uno_si_deja_de_serlo(unico):
    otro = UsuarioFactory(rol=Usuario.ADMINISTRADOR)

    Usuario.objects.filter(pk=otro.pk).update(rol=Usuario.CAJERO)

    assert activos() == 1


def test_I12_las_demas_escrituras_del_administrador_no_se_frenan(unico):
    """El disparador mira sólo el rol y el estado: el último ingreso, el nombre o la
    contraseña del único Administrador se siguen guardando."""
    unico.set_password("Clave-Nueva-2026")
    unico.save()
    Usuario.objects.filter(pk=unico.pk).update(first_name="Otro nombre")

    guardado = Usuario.objects.get(pk=unico.pk)
    assert guardado.first_name == "Otro nombre"
    assert guardado.check_password("Clave-Nueva-2026")


@pytest.mark.django_db(transaction=True)
def test_I12_dos_escrituras_cruzadas_por_fuera_del_servicio_dejan_uno():
    """La carrera que el servicio evita con su bloqueo ordenado, sin el servicio.

    Cada hilo le saca el rol a uno de los dos. La base hace esperar al segundo y,
    con lo confirmado a la vista, lo rechaza; si los dos llegaron a tomar su fila
    antes, PostgreSQL corta el interbloqueo abortando uno. En los dos casos uno
    falla y queda un Administrador.
    """
    for _ in range(10):
        a = UsuarioFactory(rol=Usuario.ADMINISTRADOR)
        b = UsuarioFactory(rol=Usuario.ADMINISTRADOR)
        Usuario.objects.exclude(pk__in=[a.pk, b.pk]).delete()

        def sacar_el_rol(usuario):
            try:
                with transaction.atomic():
                    Usuario.objects.filter(pk=usuario.pk).update(rol=Usuario.CAJERO)
                return "ok"
            except DatabaseError:
                return "rechazada"
            finally:
                connection.close()

        resultados = a_la_vez(lambda: sacar_el_rol(a), lambda: sacar_el_rol(b))

        assert sorted(resultados) == ["ok", "rechazada"]
        assert activos() == 1
