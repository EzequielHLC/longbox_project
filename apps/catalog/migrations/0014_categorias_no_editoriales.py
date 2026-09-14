"""Siembra las cuatro categorías no editoriales de CU-CAT-ALT.

`Tipo` pasó a clasificar los dos rubros (corrección 23: la "categoría" de CU-CAT-ALT
y el "formato" de RF-04 son el mismo eje, y la fuente nunca lo dice). Los tipos
que ya existían son todos editoriales y el valor por defecto del campo los deja
bien; lo que faltaba era el otro lado del catálogo.

Son exactamente los cuatro que CU-CAT-ALT paso 2 enumera. **Ninguno usa formato**: el
tamaño físico fija el precio de un tomo, no el de una figura — y una escala 1/7
es una etiqueta descriptiva, no una grilla de precios.
"""

from django.db import migrations

CATEGORIAS = [
    # (nombre, orden). El orden los deja después de los editoriales, que van de
    # 10 a 50, porque son el rubro secundario del negocio.
    ("TCG", 60),
    ("Figura", 70),
    ("Merchandising", 80),
    ("Insumo", 90),
]


def sembrar(apps, schema_editor):
    Tipo = apps.get_model("catalog", "Tipo")
    for nombre, orden in CATEGORIAS:
        Tipo.objects.get_or_create(
            nombre=nombre,
            defaults={"clase": "no_editorial", "usa_formato": False, "orden": orden},
        )


def desmontar(apps, schema_editor):
    """Solo borra las que nadie usó todavía.

    Mismo criterio que la siembra de los catálogos iniciales: una categoría con
    productos cargados no se puede quitar sin llevarse los productos, y eso no es
    lo que una vuelta atrás tiene que hacer.
    """
    Tipo = apps.get_model("catalog", "Tipo")
    Tipo.objects.filter(
        nombre__in=[nombre for nombre, _ in CATEGORIAS], productos__isnull=True
    ).delete()


class Migration(migrations.Migration):
    dependencies = [("catalog", "0013_jerarquia_de_producto")]

    operations = [migrations.RunPython(sembrar, desmontar)]
