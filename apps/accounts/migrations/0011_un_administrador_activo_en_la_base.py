"""I-12 en la base: siempre queda al menos un Administrador activo (plan 00 de cierre de deuda, D3).

El servicio de `accounts` ya lo cumplía, con un bloqueo de los Administradores
activos en orden de clave (B-13-006), pero sólo para las operaciones que pasan por
él: un `update()` de queryset o SQL directo podían dejar al sistema sin nadie que
lo administre. El disparador lo cierra para cualquier escritura, como el de I-13
(B-16-004).

Se dispara sólo cuando un Administrador activo deja de serlo —cambia de rol, de
estado o se borra— y no en cada escritura de la tabla. Antes de contar, bloquea a
los Administradores activos que quedan: si dos transacciones le sacan el rol a
dos Administradores distintos a la vez, la segunda espera a la primera, vuelve a
contar con lo confirmado y es la que se rechaza. Por el servicio la carrera nunca
llega hasta acá: el bloqueo ordenado la resuelve antes y con su propio mensaje.
"""

from django.db import migrations

CREAR = """
CREATE OR REPLACE FUNCTION longbox_queda_un_administrador_activo() RETURNS trigger AS $$
BEGIN
    PERFORM 1 FROM accounts_usuario
        WHERE rol = 'administrador' AND estado = 'activo'
        ORDER BY id
        FOR UPDATE;
    IF NOT EXISTS (
        SELECT 1 FROM accounts_usuario WHERE rol = 'administrador' AND estado = 'activo'
    ) THEN
        RAISE EXCEPTION 'Debe existir al menos un Administrador activo en el sistema (I-12).'
            USING ERRCODE = 'check_violation';
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER queda_un_administrador_activo_al_modificar
    AFTER UPDATE OF rol, estado ON accounts_usuario
    FOR EACH ROW
    WHEN (OLD.rol = 'administrador' AND OLD.estado = 'activo'
          AND (NEW.rol <> 'administrador' OR NEW.estado <> 'activo'))
    EXECUTE FUNCTION longbox_queda_un_administrador_activo();

CREATE TRIGGER queda_un_administrador_activo_al_borrar
    AFTER DELETE ON accounts_usuario
    FOR EACH ROW
    WHEN (OLD.rol = 'administrador' AND OLD.estado = 'activo')
    EXECUTE FUNCTION longbox_queda_un_administrador_activo();
"""

QUITAR = """
DROP TRIGGER IF EXISTS queda_un_administrador_activo_al_borrar ON accounts_usuario;
DROP TRIGGER IF EXISTS queda_un_administrador_activo_al_modificar ON accounts_usuario;
DROP FUNCTION IF EXISTS longbox_queda_un_administrador_activo();
"""


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0010_intento_fallido_flujo"),
    ]

    operations = [migrations.RunSQL(CREAR, reverse_sql=QUITAR)]
