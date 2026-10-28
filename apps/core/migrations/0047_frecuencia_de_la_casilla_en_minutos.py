"""La frecuencia de la casilla pasa de horas a minutos (B-04-015).

Se conserva el valor: las 24 horas por defecto, que nadie eligió, pasan a los 5
minutos nuevos; cualquier otro valor se multiplica por 60.
"""

import django.core.validators
from django.db import migrations, models


def a_minutos(apps, schema_editor):
    Configuracion = apps.get_model("core", "ConfiguracionSistema")
    for configuracion in Configuracion.objects.all():
        horas = configuracion.frecuencia_casilla_horas
        configuracion.frecuencia_casilla_minutos = 5 if horas == 24 else horas * 60
        configuracion.save(update_fields=["frecuencia_casilla_minutos"])


def a_horas(apps, schema_editor):
    Configuracion = apps.get_model("core", "ConfiguracionSistema")
    for configuracion in Configuracion.objects.all():
        minutos = configuracion.frecuencia_casilla_minutos
        configuracion.frecuencia_casilla_horas = 24 if minutos == 5 else max(1, minutos // 60)
        configuracion.save(update_fields=["frecuencia_casilla_horas"])


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0046_acciones_de_perfil_y_avisos"),
    ]

    operations = [
        migrations.AddField(
            model_name="configuracionsistema",
            name="frecuencia_casilla_minutos",
            field=models.PositiveIntegerField(
                default=5,
                help_text="Cada cuántos minutos se lee la casilla de novedades.",
                validators=[django.core.validators.MinValueValidator(1)],
                verbose_name="frecuencia de monitoreo de la casilla (minutos)",
            ),
        ),
        migrations.RunPython(a_minutos, a_horas),
        migrations.RemoveField(
            model_name="configuracionsistema",
            name="frecuencia_casilla_horas",
        ),
    ]
