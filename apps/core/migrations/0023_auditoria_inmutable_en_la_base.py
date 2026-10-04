"""I-13 en la base: el log de auditoría no se modifica ni se borra por ningún camino.

`save()` y `delete()` del modelo ya lo rechazaban, pero un `update()` o `delete()`
de queryset, o SQL directo, pasaban por al lado (B-16-004). El disparador lo
cierra en PostgreSQL.

La única escritura que admite es la que hace la propia base al eliminar una
cuenta o un tipo de objeto: poner en nulo `actor_id` u `objetivo_tipo_id`
(`on_delete=SET_NULL`), sin tocar ninguna otra columna. El correo del actor
queda desnormalizado en la entrada, así que la traza sobrevive.

`TRUNCATE` no lo detiene un disparador de fila: exige ser dueño de la tabla, y
Django lo usa para vaciar la base de pruebas.
"""

from django.db import migrations

CREAR = """
CREATE OR REPLACE FUNCTION longbox_auditoria_inmutable() RETURNS trigger AS $$
BEGIN
    IF TG_OP = 'DELETE' THEN
        RAISE EXCEPTION 'El log de auditoría es inmutable: no se puede borrar (I-13).';
    END IF;
    IF (NEW.actor_id IS NOT DISTINCT FROM OLD.actor_id OR NEW.actor_id IS NULL)
       AND (NEW.objetivo_tipo_id IS NOT DISTINCT FROM OLD.objetivo_tipo_id
            OR NEW.objetivo_tipo_id IS NULL)
       AND (to_jsonb(NEW) - 'actor_id' - 'objetivo_tipo_id')
           = (to_jsonb(OLD) - 'actor_id' - 'objetivo_tipo_id')
    THEN
        RETURN NEW;
    END IF;
    RAISE EXCEPTION 'El log de auditoría es inmutable: no se puede modificar (I-13).';
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER auditoria_inmutable
    BEFORE UPDATE OR DELETE ON core_registroauditoria
    FOR EACH ROW EXECUTE FUNCTION longbox_auditoria_inmutable();
"""

QUITAR = """
DROP TRIGGER IF EXISTS auditoria_inmutable ON core_registroauditoria;
DROP FUNCTION IF EXISTS longbox_auditoria_inmutable();
"""


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0022_alter_registroauditoria_accion"),
    ]

    operations = [migrations.RunSQL(CREAR, reverse_sql=QUITAR)]
