"""I-13: una entrada del log no se modifica ni se borra, **por ningún camino**.

`save()` y `delete()` del modelo ya rechazaban la escritura, pero un `update()` o
un `delete()` de queryset, o una sentencia SQL directa, pasaban por al lado
(plan 00, decisión 4; B-16-004). Ahora la base misma lo impide con un
disparador. Lo único que admite es lo que hace la propia base cuando se elimina
una cuenta o un tipo de objeto: poner en nulo la referencia (`SET_NULL`), sin
tocar nada más de la entrada.

Límite conocido: `TRUNCATE` sobre la tabla no lo detiene un disparador de fila.
Exige ser el dueño de la tabla, y Django lo usa para vaciar la base entre pruebas.
"""

import pytest
from django.db import DatabaseError, connection, transaction

from apps.accounts.models import Usuario
from apps.accounts.tests.factories import UsuarioFactory
from apps.core.models import RegistroAuditoria

pytestmark = pytest.mark.django_db


@pytest.fixture
def entrada(administrador):
    return RegistroAuditoria.registrar(
        accion=RegistroAuditoria.ALTA_USUARIO,
        actor=administrador,
        detalle="alta original",
    )


def rechazada(operacion):
    """Corre la operación en su propio punto de guardado y dice si la base la rechazó."""
    try:
        with transaction.atomic():
            operacion()
    except DatabaseError as error:
        return "inmutable" in str(error)
    return False


def test_I13_un_update_de_queryset_no_modifica_la_entrada(entrada):
    assert rechazada(
        lambda: RegistroAuditoria.objects.filter(pk=entrada.pk).update(detalle="alterada")
    )
    entrada.refresh_from_db()
    assert entrada.detalle == "alta original"


def test_I13_un_delete_de_queryset_no_borra_la_entrada(entrada):
    assert rechazada(lambda: RegistroAuditoria.objects.filter(pk=entrada.pk).delete())
    assert RegistroAuditoria.objects.filter(pk=entrada.pk).exists()


@pytest.mark.parametrize(
    "sentencia",
    [
        "UPDATE core_registroauditoria SET detalle = 'sql directo' WHERE id = %s",
        "UPDATE core_registroauditoria SET ocurrido_en = now() - interval '1 year' WHERE id = %s",
        "DELETE FROM core_registroauditoria WHERE id = %s",
    ],
    ids=["update_detalle", "update_fecha", "delete"],
)
def test_I13_el_sql_directo_tampoco_puede(entrada, sentencia):
    def ejecutar():
        with connection.cursor() as cursor:
            cursor.execute(sentencia, [entrada.pk])

    assert rechazada(ejecutar)
    entrada.refresh_from_db()
    assert entrada.detalle == "alta original"


def test_I13_eliminar_la_cuenta_del_actor_conserva_la_entrada_con_el_correo():
    """El `SET_NULL` de la clave foránea es la única escritura que la base admite."""
    # Otro Administrador queda activo: I-12 no deja borrar al último.
    UsuarioFactory(rol=Usuario.ADMINISTRADOR)
    actor = UsuarioFactory(rol=Usuario.ADMINISTRADOR, email="se.va@longbox.test")
    registro = RegistroAuditoria.registrar(
        accion=RegistroAuditoria.ALTA_USUARIO, actor=actor, detalle="sigue intacta"
    )

    actor.delete()

    registro.refresh_from_db()
    assert registro.actor is None
    assert registro.actor_email == "se.va@longbox.test"
    assert registro.detalle == "sigue intacta"


def test_I13_poner_en_nulo_el_actor_junto_con_otro_cambio_se_rechaza(entrada):
    def ejecutar():
        with connection.cursor() as cursor:
            cursor.execute(
                "UPDATE core_registroauditoria SET actor_id = NULL, detalle = 'x' WHERE id = %s",
                [entrada.pk],
            )

    assert rechazada(ejecutar)


def test_I13_las_altas_siguen_funcionando(administrador):
    RegistroAuditoria.registrar(accion=RegistroAuditoria.ALTA_USUARIO, actor=administrador)

    assert RegistroAuditoria.objects.filter(accion=RegistroAuditoria.ALTA_USUARIO).exists()
