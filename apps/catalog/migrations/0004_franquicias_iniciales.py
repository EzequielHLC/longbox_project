"""Siembra las franquicias que la propia fuente usa como ejemplo.

RF-04 nombra "Universo DC", "Marvel" y "Star Wars" al explicar por qué la
franquicia es un discriminante independiente de la editorial. Se siembran esas
tres y ninguna más: a diferencia de los tipos y los formatos —que son catálogos
casi cerrados— las franquicias crecen con el uso, así que la lista inicial no
pretende ser completa. Existe para que la pantalla no arranque vacía y para que
el primer cómic se pueda clasificar sin pasar antes por otra pantalla.
"""

from django.db import migrations

FRANQUICIAS = ["Marvel", "Star Wars", "Universo DC"]


def sembrar(apps, schema_editor):
    Franquicia = apps.get_model("catalog", "Franquicia")
    for nombre in FRANQUICIAS:
        Franquicia.objects.get_or_create(nombre=nombre)


def borrar(apps, schema_editor):
    """Solo deshace una instalación recién hecha: no vacía un catálogo en uso."""
    Franquicia = apps.get_model("catalog", "Franquicia")
    Franquicia.objects.filter(nombre__in=FRANQUICIAS, productos__isnull=True).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("catalog", "0003_franquicia_opcional"),
    ]

    operations = [
        migrations.RunPython(sembrar, borrar),
    ]
