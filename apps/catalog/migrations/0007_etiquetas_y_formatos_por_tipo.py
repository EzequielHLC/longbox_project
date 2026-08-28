"""Etiquetas agrupadas, formatos por tipo y la marca de material adulto.

Se separa en tres migraciones a propósito. Esta crea lo nuevo, la siguiente
traslada los datos de `Franquicia`, y la última recién ahí borra lo viejo. Todo
junto en una sola dejaría la conversión de datos entre un `AddField` y un
`RemoveField` de la misma tabla, que es donde una vuelta atrás se vuelve
irrecuperable.
"""

import django.db.models.deletion
from django.db import migrations, models
from django.db.models.functions import Lower


class Migration(migrations.Migration):

    dependencies = [
        ("catalog", "0006_producto_isbn"),
    ]

    operations = [
        migrations.CreateModel(
            name="GrupoEtiqueta",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                ("nombre", models.CharField(max_length=60, unique=True, verbose_name="nombre")),
                ("activo", models.BooleanField(default=True, verbose_name="activo")),
                (
                    "orden",
                    models.PositiveSmallIntegerField(
                        default=0,
                        help_text="Posición en los filtros. Menor va primero.",
                        verbose_name="orden",
                    ),
                ),
            ],
            options={
                "verbose_name": "grupo de etiquetas",
                "verbose_name_plural": "grupos de etiquetas",
                "ordering": ["orden", "nombre"],
            },
        ),
        migrations.CreateModel(
            name="Etiqueta",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                ("nombre", models.CharField(max_length=80, verbose_name="nombre")),
                ("activa", models.BooleanField(default=True, verbose_name="activa")),
                (
                    "grupo",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="etiquetas",
                        to="catalog.grupoetiqueta",
                        verbose_name="grupo",
                    ),
                ),
            ],
            options={
                "verbose_name": "etiqueta",
                "verbose_name_plural": "etiquetas",
                "ordering": ["grupo__orden", "grupo__nombre", "nombre"],
            },
        ),
        migrations.AddConstraint(
            model_name="etiqueta",
            constraint=models.UniqueConstraint(
                Lower("nombre"), "grupo", name="etiqueta_unica_por_nombre_y_grupo"
            ),
        ),
        migrations.AddField(
            model_name="producto",
            name="etiquetas",
            field=models.ManyToManyField(
                blank=True,
                related_name="productos",
                to="catalog.etiqueta",
                verbose_name="etiquetas",
            ),
        ),
        migrations.AddField(
            model_name="producto",
            name="solo_adultos",
            field=models.BooleanField(
                default=False,
                help_text="Se excluye del catálogo público.",
                verbose_name="solo para adultos",
            ),
        ),
        migrations.AddField(
            model_name="formato",
            name="tipos",
            field=models.ManyToManyField(
                blank=True,
                help_text="Sin declarar ninguno, el formato se ofrece para todos los tipos.",
                related_name="formatos",
                to="catalog.tipo",
                verbose_name="tipos en los que aplica",
            ),
        ),
    ]
