"""El objetivo del log de auditoría deja de ser una cuenta y pasa a ser genérico.

Escrita a mano porque `makemigrations` no puede saber que la columna vieja
(`objetivo_id`, una clave foránea a `Usuario`) y las nuevas describen el mismo
dato: sin el paso de copia, el historial del Módulo 13 quedaría sin objetivo.
"""

import django.db.models.deletion
from django.db import migrations, models

APP_DEL_USUARIO = "accounts"
MODELO_DEL_USUARIO = "usuario"


def cuentas_al_objetivo_generico(apps, schema_editor):
    """Pasa los objetivos ya registrados (todos cuentas) al par tipo + clave."""
    RegistroAuditoria = apps.get_model("core", "RegistroAuditoria")
    ContentType = apps.get_model("contenttypes", "ContentType")

    tipo_usuario, _ = ContentType.objects.get_or_create(
        app_label=APP_DEL_USUARIO, model=MODELO_DEL_USUARIO
    )
    RegistroAuditoria.objects.filter(objetivo__isnull=False).update(
        objetivo_tipo=tipo_usuario, objetivo_pk=models.F("objetivo")
    )


def objetivo_generico_a_cuentas(apps, schema_editor):
    """Vuelta atrás: solo puede recuperar los objetivos que sean cuentas."""
    RegistroAuditoria = apps.get_model("core", "RegistroAuditoria")
    ContentType = apps.get_model("contenttypes", "ContentType")

    tipo_usuario = ContentType.objects.filter(
        app_label=APP_DEL_USUARIO, model=MODELO_DEL_USUARIO
    ).first()
    if tipo_usuario is None:
        return
    RegistroAuditoria.objects.filter(objetivo_tipo=tipo_usuario).update(
        objetivo=models.F("objetivo_pk")
    )


class Migration(migrations.Migration):
    dependencies = [
        ("contenttypes", "0002_remove_content_type_name"),
        ("core", "0005_alter_registroauditoria_accion"),
    ]

    operations = [
        migrations.AddField(
            model_name="registroauditoria",
            name="objetivo_tipo",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="registros_auditoria",
                to="contenttypes.contenttype",
            ),
        ),
        migrations.AddField(
            model_name="registroauditoria",
            name="objetivo_pk",
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
        migrations.RunPython(cuentas_al_objetivo_generico, objetivo_generico_a_cuentas),
        migrations.RemoveField(model_name="registroauditoria", name="objetivo"),
        migrations.AddIndex(
            model_name="registroauditoria",
            index=models.Index(
                fields=["objetivo_tipo", "objetivo_pk"], name="core_regist_objetiv_c2b253_idx"
            ),
        ),
        migrations.AlterField(
            model_name="registroauditoria",
            name="accion",
            field=models.CharField(
                choices=[
                    ("inicio_sesion", "Inicio de sesión"),
                    ("cierre_sesion", "Cierre de sesión"),
                    ("bloqueo_por_intentos", "Bloqueo por intentos fallidos"),
                    ("cambio_contrasena", "Cambio de contraseña"),
                    ("alta_usuario", "Alta de usuario del sistema"),
                    ("modificacion_usuario", "Modificación de usuario del sistema"),
                    ("baja_usuario", "Baja de usuario del sistema"),
                    ("reactivacion_usuario", "Reactivación de usuario del sistema"),
                    ("reenvio_activacion", "Reenvío del enlace de activación"),
                    ("activacion_cuenta", "Activación de cuenta"),
                    ("eliminacion_pendiente", "Eliminación de cuenta pendiente de activación"),
                    ("registro_cliente", "Registro de cuenta de cliente"),
                    ("alta_lote_editorial", "Alta de lote de material editorial"),
                ],
                max_length=40,
            ),
        ),
    ]
