"""La franquicia deja de ser obligatoria y pasa a ser un dato de clasificación.

La bandera de `Tipo` no desaparece: cambia de sentido. Antes decía "sin esto no
se da de alta"; ahora dice "en este rubro tiene sentido preguntarlo". Se renombra
en vez de borrarla y crear otra para no perder qué tipos ya la tenían marcada:
un `RenameField` conserva la columna y sus valores, mientras que un borrado más
un alta dejaría a todos los cómics sin la marca.
"""

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("catalog", "0002_catalogos_iniciales"),
    ]

    operations = [
        migrations.RenameField(
            model_name="tipo",
            old_name="exige_franquicia",
            new_name="usa_franquicia",
        ),
        migrations.AlterField(
            model_name="tipo",
            name="usa_franquicia",
            field=models.BooleanField(
                default=False,
                help_text="El alta muestra el campo de universo. Sigue siendo opcional.",
                verbose_name="ofrece franquicia",
            ),
        ),
        migrations.AddField(
            model_name="franquicia",
            name="activa",
            field=models.BooleanField(default=True, verbose_name="activa"),
        ),
    ]
