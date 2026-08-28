"""Traslada las franquicias a etiquetas del grupo "Franquicia".

Va sola, entre la migración que crea las etiquetas y la que borra la tabla
vieja: así el traslado corre con las dos estructuras vivas y la vuelta atrás es
posible en cada paso.

Se siembran además los grupos con los que el catálogo arranca. No pretenden ser
la lista completa —igual que las franquicias sembradas en su momento— sino que
la pantalla no arranque vacía y que el primer producto se pueda describir sin
tener que inventar la taxonomía desde cero.
"""

from django.db import migrations

GRUPO_FRANQUICIA = "Franquicia"

# El orden es el que van a tener los filtros en la tienda: primero por lo que la
# gente busca (el universo), después por lo que acota (género), y al final lo
# que distingue una edición de otra.
GRUPOS = [
    (GRUPO_FRANQUICIA, 10),
    ("Género", 20),
    ("Colección", 30),
    ("Edición", 40),
]


def trasladar(apps, schema_editor):
    GrupoEtiqueta = apps.get_model("catalog", "GrupoEtiqueta")
    Etiqueta = apps.get_model("catalog", "Etiqueta")
    Franquicia = apps.get_model("catalog", "Franquicia")
    Producto = apps.get_model("catalog", "Producto")

    for nombre, orden in GRUPOS:
        GrupoEtiqueta.objects.get_or_create(nombre=nombre, defaults={"orden": orden})

    grupo = GrupoEtiqueta.objects.get(nombre=GRUPO_FRANQUICIA)

    # Cada franquicia pasa a ser una etiqueta de su grupo, conservando si estaba
    # activa: desactivar una franquicia era sacarla de los desplegables sin
    # perder sus productos, y eso tiene que seguir valiendo igual.
    equivalencia = {}
    for franquicia in Franquicia.objects.all():
        etiqueta, _ = Etiqueta.objects.get_or_create(
            nombre=franquicia.nombre,
            grupo=grupo,
            defaults={"activa": franquicia.activa},
        )
        equivalencia[franquicia.pk] = etiqueta

    # Y cada producto que tenía una franquicia se queda con la etiqueta
    # equivalente. Es lo único de este archivo que puede perder datos si se
    # omite, así que va antes de que la columna desaparezca.
    for producto in Producto.objects.exclude(franquicia__isnull=True):
        producto.etiquetas.add(equivalencia[producto.franquicia_id])


def volver(apps, schema_editor):
    """La vuelta: cada etiqueta del grupo Franquicia vuelve a ser una franquicia.

    No se borran los grupos ni las etiquetas de los demás grupos: pueden tener
    productos que la estructura vieja no sabe representar, y hacerlos desaparecer
    en silencio sería peor que dejar filas de más.
    """
    GrupoEtiqueta = apps.get_model("catalog", "GrupoEtiqueta")
    Etiqueta = apps.get_model("catalog", "Etiqueta")
    Franquicia = apps.get_model("catalog", "Franquicia")

    grupo = GrupoEtiqueta.objects.filter(nombre=GRUPO_FRANQUICIA).first()
    if grupo is None:
        return

    for etiqueta in Etiqueta.objects.filter(grupo=grupo):
        franquicia, _ = Franquicia.objects.get_or_create(
            nombre=etiqueta.nombre, defaults={"activa": etiqueta.activa}
        )
        # Un producto puede tener varias etiquetas y una sola franquicia, así
        # que la vuelta se queda con la primera que encuentre. Es una pérdida
        # real de información, y es exactamente por qué el cambio se hace en
        # esta dirección y no en la otra.
        for producto in etiqueta.productos.filter(franquicia__isnull=True):
            producto.franquicia = franquicia
            producto.save(update_fields=["franquicia"])


class Migration(migrations.Migration):

    dependencies = [
        ("catalog", "0007_etiquetas_y_formatos_por_tipo"),
    ]

    operations = [
        migrations.RunPython(trasladar, volver),
    ]
