"""RNF-05 — Optimización automática de imágenes.

Toda imagen que sube el Administrador se procesa **antes** de guardarse:
conversión a WebP, redimensionado al lado mayor manteniendo la proporción y
compresión. El original no se conserva: lo único que llega al almacenamiento es
la versión procesada.

Hoy la usan los banners, el logo y el fondo de la tienda. Las portadas de
producto siguen como deuda del módulo 01 (plan 17, «Fuera de alcance»).

La calidad es un valor fijo: `ConfiguracionSistema` no declara el parámetro
«configurable» que pide RNF-05 (plan 17, ambigüedad 10; B-17-012).
"""

from io import BytesIO
from uuid import uuid4

from django.core.files.base import ContentFile
from PIL import Image, ImageOps, UnidentifiedImageError

FORMATOS_ADMITIDOS = {"JPEG": "JPG", "PNG": "PNG", "WEBP": "WebP"}
CALIDAD = 80

LADO_MAYOR_POR_DEFECTO = 800
LADO_MAYOR_BANNER = 1920

UN_MEGABYTE = 1024 * 1024
TAMANO_MAXIMO = 5 * UN_MEGABYTE
TAMANO_MAXIMO_BANNER = 10 * UN_MEGABYTE


class ImagenInvalida(ValueError):
    """La imagen no cumple el formato o el tamaño admitidos. El mensaje es el
    problema específico, listo para mostrar (E1 de `CO-132`, `CO-133`; E2 de
    `CO-131`)."""


def procesar(archivo, *, lado_mayor=LADO_MAYOR_POR_DEFECTO, tamano_maximo=TAMANO_MAXIMO):
    """La imagen lista para guardar, en WebP y con su lado mayor acotado.

    Devuelve un `ContentFile` con nombre propio: el nombre del archivo subido
    no llega al almacenamiento, igual que el resto del original.
    """
    if archivo.size > tamano_maximo:
        raise ImagenInvalida(
            f"La imagen pesa {archivo.size / UN_MEGABYTE:.1f} MB y el máximo es "
            f"{tamano_maximo // UN_MEGABYTE} MB."
        )

    try:
        archivo.seek(0)
        imagen = Image.open(archivo)
        formato = imagen.format
        imagen.load()
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError) as error:
        raise ImagenInvalida("El archivo no es una imagen o está dañado.") from error

    if formato not in FORMATOS_ADMITIDOS:
        admitidos = ", ".join(FORMATOS_ADMITIDOS.values())
        raise ImagenInvalida(f"El formato {formato} no se admite. Use {admitidos}.")

    # La orientación de la cámara se aplica antes de descartar los metadatos:
    # si no, una foto vertical quedaría acostada.
    imagen = ImageOps.exif_transpose(imagen)
    imagen.thumbnail((lado_mayor, lado_mayor), Image.Resampling.LANCZOS)
    if imagen.mode not in ("RGB", "RGBA"):
        imagen = imagen.convert("RGBA" if "transparency" in imagen.info else "RGB")

    salida = BytesIO()
    imagen.save(salida, "WEBP", quality=CALIDAD, method=6)
    return ContentFile(salida.getvalue(), name=f"{uuid4().hex}.webp")


def borrar(campo):
    """Saca del almacenamiento el archivo de un campo de imagen, si tiene uno.

    «La imagen anterior no se conserva» (`CO-133`): reemplazar o eliminar un
    banner, un logo o un fondo borra el archivo, no sólo la referencia.
    """
    if campo and campo.name:
        campo.storage.delete(campo.name)
