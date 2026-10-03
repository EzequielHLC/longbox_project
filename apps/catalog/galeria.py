"""Las imágenes adicionales de un producto (B-01-003).

Las imágenes llegan ya procesadas por `core.imagenes.procesar` (RNF-05): el
formulario las procesa al validar, así que una inválida nunca llega hasta acá.
"""

from django.db import transaction

from apps.catalog.models import ImagenProducto


def actualizar(producto, *, nuevas=(), quitar=()):
    """Agrega las nuevas al final y quita las marcadas. Devuelve `(agregadas, quitadas)`.

    Las posiciones quedan consecutivas desde 0. Los archivos de las quitadas se
    borran cuando la transacción confirma: si algo falla, siguen ahí.
    """
    quitadas = [imagen for imagen in quitar if imagen.producto_id == producto.pk]
    nombres = [imagen.imagen.name for imagen in quitadas]
    ImagenProducto.objects.filter(pk__in=[imagen.pk for imagen in quitadas]).delete()

    restantes = list(producto.imagenes.order_by("posicion", "pk"))
    for posicion, imagen in enumerate(restantes):
        if imagen.posicion != posicion:
            imagen.posicion = posicion
            imagen.save(update_fields=["posicion"])

    for desplazamiento, archivo in enumerate(nuevas):
        ImagenProducto.objects.create(
            producto=producto, imagen=archivo, posicion=len(restantes) + desplazamiento
        )

    if nombres:
        almacenamiento = ImagenProducto.imagen.field.storage
        transaction.on_commit(lambda: [almacenamiento.delete(nombre) for nombre in nombres])
    return len(nuevas), len(quitadas)


def describir(agregadas, quitadas):
    """El cambio de la galería tal como se lee en el historial."""
    partes = []
    if agregadas:
        partes.append(f"{agregadas} agregada" + ("s" if agregadas != 1 else ""))
    if quitadas:
        partes.append(f"{quitadas} quitada" + ("s" if quitadas != 1 else ""))
    return "imágenes adicionales: " + ", ".join(partes) if partes else ""
