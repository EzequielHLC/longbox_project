"""Siembra los tipos de material y los formatos con los que arranca el negocio.

Van en una migración y no en un comando aparte porque son **precondición para
usar el sistema**: sin al menos un tipo cargado no se puede dar de alta ningún
producto, y una instalación nueva quedaría trabada esperando que alguien
adivine qué cargar primero.

No son datos congelados: los cinco tipos y los siete formatos se editan, se
desactivan y se amplían desde la pantalla de parámetros globales. Esta migración
solo decide con qué arranca el sistema, no qué puede llegar a tener.
"""

from django.db import migrations

# Las dos banderas de cada tipo son la regla de negocio: qué campos le pide el
# alta a un producto de esa clase.
#
#   usa_formato       → el tamaño fija su precio y entra en la tabla de precios.
#   exige_franquicia  → no se da de alta sin declarar su universo (RF-04).
TIPOS = [
    # (nombre, usa_formato, exige_franquicia, orden)
    ("Manga", True, False, 10),
    ("Cómic", True, True, 20),
    ("Artbook", False, False, 30),
    ("Novela ligera", False, False, 40),
    ("Libro", False, False, 50),
]

FORMATOS = [
    # (nombre, medidas, orden). Los tres primeros son de manga, los tres
    # siguientes de cómic, y el último es el comodín de las ediciones especiales.
    ("Tankōbon", "11,5 × 17,5 cm", 10),
    ("B6", "12,8 × 18,2 cm", 20),
    ("A5", "14,8 × 21 cm", 30),
    ("Grapa", "17 × 26 cm", 40),
    ("Rústica", "17 × 26 cm, lomo encolado", 50),
    ("Tapa dura", "18 × 27,5 cm", 60),
    ("Deluxe", "edición ampliada", 70),
]


def sembrar(apps, schema_editor):
    Tipo = apps.get_model("catalog", "Tipo")
    Formato = apps.get_model("catalog", "Formato")

    for nombre, usa_formato, exige_franquicia, orden in TIPOS:
        Tipo.objects.get_or_create(
            nombre=nombre,
            defaults={
                "usa_formato": usa_formato,
                "exige_franquicia": exige_franquicia,
                "orden": orden,
            },
        )

    for nombre, descripcion, orden in FORMATOS:
        Formato.objects.get_or_create(
            nombre=nombre, defaults={"descripcion": descripcion, "orden": orden}
        )


def borrar(apps, schema_editor):
    """Vuelta atrás: solo borra lo sembrado si nadie lo usó todavía.

    Un tipo con productos cargados no se puede borrar —la clave foránea lo
    protege— y tampoco debería: la migración inversa existe para deshacer una
    instalación recién hecha, no para vaciar un catálogo en uso.
    """
    Tipo = apps.get_model("catalog", "Tipo")
    Formato = apps.get_model("catalog", "Formato")

    Tipo.objects.filter(nombre__in=[nombre for nombre, *_ in TIPOS], productos__isnull=True).delete()
    Formato.objects.filter(
        nombre__in=[nombre for nombre, *_ in FORMATOS], productos__isnull=True
    ).delete()


class Migration(migrations.Migration):
    dependencies = [("catalog", "0001_initial")]

    operations = [migrations.RunPython(sembrar, borrar)]
