# Migración de datos: alinea el nuevo campo `estado` con el `is_active` que
# ya traían las cuentas creadas antes del Módulo 13.

from django.db import migrations


def estado_desde_is_active(apps, schema_editor):
    Usuario = apps.get_model("accounts", "Usuario")
    Usuario.objects.filter(is_active=False).update(estado="inactivo")


def is_active_desde_estado(apps, schema_editor):
    Usuario = apps.get_model("accounts", "Usuario")
    Usuario.objects.exclude(estado="activo").update(is_active=False)


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0003_usuario_actualizado_en_usuario_estado"),
    ]

    operations = [
        migrations.RunPython(estado_desde_is_active, is_active_desde_estado),
    ]
