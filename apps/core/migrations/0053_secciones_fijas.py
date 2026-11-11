"""Recién llegados y Lo que se viene pasan a ser secciones fijas (plan 07, novena parte).

Hasta ahora la portada las dibujaba siempre, antes de las filas. Para que la
portada se vea igual después de la migración, se crean en ese lugar y las
filas existentes pasan detrás, en el orden que tenían.
"""

from django.db import migrations

FIJAS = (("recien_llegados", 1), ("se_viene", 2))


def crear(apps, schema_editor):
    Seccion = apps.get_model("core", "SeccionPortada")
    for indice, seccion in enumerate(
        Seccion.objects.exclude(tipo__in=[tipo for tipo, _ in FIJAS]).order_by("orden", "pk"),
        start=len(FIJAS) + 1,
    ):
        seccion.orden = indice
        seccion.save(update_fields=["orden"])
    for tipo, orden in FIJAS:
        Seccion.objects.get_or_create(tipo=tipo, defaults={"orden": orden})


def quitar(apps, schema_editor):
    apps.get_model("core", "SeccionPortada").objects.filter(
        tipo__in=[tipo for tipo, _ in FIJAS]
    ).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0052_secciones_de_la_portada"),
    ]

    operations = [migrations.RunPython(crear, quitar)]
