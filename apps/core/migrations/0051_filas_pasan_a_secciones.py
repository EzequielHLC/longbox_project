"""Las filas de la portada pasan a ser secciones (`CU-CFG-SEC`; plan 07, novena parte).

Se renombra el modelo, no se copia: la tabla y sus filas siguen siendo las
mismas. La restricción vieja («etiqueta o grupo») se quita acá y vuelve en la
migración siguiente condicionada al tipo, porque una sección que no es de
productos no tiene origen.
"""

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0050_modelo_de_respaldo"),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name="filaportada",
            name="fila_portada_de_etiqueta_o_de_grupo",
        ),
        migrations.RenameModel(old_name="FilaPortada", new_name="SeccionPortada"),
    ]
