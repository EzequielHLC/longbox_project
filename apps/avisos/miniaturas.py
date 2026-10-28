"""Las imágenes que salen por Telegram, achicadas (B-19-008, B-19-014).

Telegram recibe una foto en JPEG; las del sistema están en WebP y en tamaño de
ficha. Se mandan chicas: alcanzan para decidir, y una evidencia de devolución
—un dato personal del Cliente— sale con la menor resolución que sirve.
"""

from io import BytesIO

from PIL import Image

LADO_MAXIMO = 800


def miniatura(campo):
    """Los bytes JPEG de un `ImageField`, o `None` si no hay imagen o no se lee."""
    if not campo:
        return None
    try:
        with campo.open("rb") as archivo, Image.open(archivo) as imagen:
            imagen = imagen.convert("RGB")
            imagen.thumbnail((LADO_MAXIMO, LADO_MAXIMO))
            salida = BytesIO()
            imagen.save(salida, "JPEG", quality=85)
    except (OSError, ValueError):
        return None
    return salida.getvalue()
