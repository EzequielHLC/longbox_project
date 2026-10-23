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


def ordenar(producto, *, orden=(), portada_desde=None):
    """El orden de las adicionales y «Usar como portada» (plan 00 de interfaz,
    cuarta parte, C). Va **antes** de `actualizar`, que quita y renumera
    respetando este orden. Devuelve lo que cambió para el historial.

    «Usar como portada» intercambia (decisión del responsable): la portada
    anterior pasa a ser una imagen adicional en el lugar de la elegida, así no
    se pierde ninguna imagen que nadie quitó. Sin portada anterior, la elegida
    sale de la galería. Ningún archivo se borra: sólo cambian de lugar.
    """
    partes = []
    if portada_desde is not None and portada_desde.producto_id == producto.pk:
        anterior = producto.portada.name
        producto.portada = portada_desde.imagen.name
        producto.save(update_fields=["portada"])
        if anterior:
            portada_desde.imagen = anterior
            portada_desde.save(update_fields=["imagen"])
        else:
            ImagenProducto.objects.filter(pk=portada_desde.pk).delete()

    actuales = list(producto.imagenes.order_by("posicion", "pk"))
    if orden:
        por_pk = {imagen.pk: imagen for imagen in actuales}
        nuevas = [por_pk[pk] for pk in orden if pk in por_pk]
        nuevas += [imagen for imagen in actuales if imagen not in nuevas]
        if [i.pk for i in nuevas] != [i.pk for i in actuales]:
            for posicion, imagen in enumerate(nuevas):
                if imagen.posicion != posicion:
                    imagen.posicion = posicion
                    imagen.save(update_fields=["posicion"])
            partes.append("imágenes adicionales: nuevo orden")
    return partes


def describir(agregadas, quitadas):
    """El cambio de la galería tal como se lee en el historial."""
    partes = []
    if agregadas:
        partes.append(f"{agregadas} agregada" + ("s" if agregadas != 1 else ""))
    if quitadas:
        partes.append(f"{quitadas} quitada" + ("s" if quitadas != 1 else ""))
    return "imágenes adicionales: " + ", ".join(partes) if partes else ""
