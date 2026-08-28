"""Retira `Franquicia` y la bandera de `Tipo` que la ofrecía.

Corre después del traslado de datos de `0008`, nunca antes. La bandera
`usa_franquicia` se va con ella: las etiquetas que la reemplazan aplican a todo
tipo de material, así que la bandera habría valido siempre `True`.
"""

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("catalog", "0008_franquicias_a_etiquetas"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="producto",
            name="franquicia",
        ),
        migrations.RemoveField(
            model_name="tipo",
            name="usa_franquicia",
        ),
        migrations.DeleteModel(
            name="Franquicia",
        ),
    ]
