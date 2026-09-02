"""Grupos de etiquetas para el rubro no editorial.

Los cinco grupos que sembró la migración inicial —Demografía, Franquicia,
Género, Colección, Edición— describen material editorial. La pantalla de un
producto no editorial ofrecía esos cinco y ninguno aplicable: una figura no tiene
demografía ni género literario, y etiquetarla como "Seinen" es ruido que después
ensucia los filtros de la tienda.

Los tres que se agregan son los ejes por los que se busca merchandising en una
comiquería: quién lo fabrica, de qué está hecho y a qué escala está. Franquicia
ya existía y sirve para los dos rubros —una figura de Marvel y un cómic de Marvel
comparten franquicia—, así que no se duplica.

Las etiquetas de ejemplo son las que hacen que la pantalla se pueda usar el
primer día. Como el resto de los catálogos, se editan, se desactivan y se amplían
desde la pantalla de etiquetas: esta migración decide con qué arranca el sistema,
no qué puede llegar a tener.
"""

from django.db import migrations

GRUPOS = [
    # (nombre, etiquetas de ejemplo)
    (
        "Fabricante",
        ["Bandai", "Good Smile Company", "Banpresto", "Funko", "Kotobukiya"],
    ),
    (
        "Escala",
        ["1/7", "1/8", "Nendoroid", "Figma", "Tamaño real"],
    ),
    (
        "Material",
        ["PVC", "Resina", "Peluche", "Metal", "Papel"],
    ),
]

# Franquicia ya existe y vale para los dos rubros. Se le suman las que aparecen
# en el mostrador de una comiquería y no son editoriales de por sí.
FRANQUICIAS = ["Pokémon", "Dragon Ball", "Hatsune Miku"]


def sembrar(apps, schema_editor):
    GrupoEtiqueta = apps.get_model("catalog", "GrupoEtiqueta")
    Etiqueta = apps.get_model("catalog", "Etiqueta")

    for nombre, etiquetas in GRUPOS:
        grupo, _ = GrupoEtiqueta.objects.get_or_create(nombre=nombre, defaults={"activo": True})
        for etiqueta in etiquetas:
            Etiqueta.objects.get_or_create(
                grupo=grupo, nombre=etiqueta, defaults={"activa": True}
            )

    franquicia = GrupoEtiqueta.objects.filter(nombre="Franquicia").first()
    if franquicia is not None:
        for nombre in FRANQUICIAS:
            Etiqueta.objects.get_or_create(
                grupo=franquicia, nombre=nombre, defaults={"activa": True}
            )


def quitar(apps, schema_editor):
    """Solo lo que esta migración sembró, y solo si nadie lo usa.

    Una etiqueta con productos asociados no se borra: revertir una migración de
    datos no puede llevarse por delante trabajo hecho después.
    """
    GrupoEtiqueta = apps.get_model("catalog", "GrupoEtiqueta")
    Etiqueta = apps.get_model("catalog", "Etiqueta")

    for nombre, etiquetas in GRUPOS:
        Etiqueta.objects.filter(
            grupo__nombre=nombre, nombre__in=etiquetas, productos__isnull=True
        ).delete()
        GrupoEtiqueta.objects.filter(nombre=nombre, etiquetas__isnull=True).delete()

    Etiqueta.objects.filter(
        grupo__nombre="Franquicia", nombre__in=FRANQUICIAS, productos__isnull=True
    ).delete()


class Migration(migrations.Migration):
    dependencies = [("catalog", "0018_sin_campo_de_orden")]

    operations = [migrations.RunPython(sembrar, quitar)]
