from functools import cache

from apps.tienda import carrito as servicio


def carrito_tienda(request):
    """Las unidades del carrito, para el encabezado de la tienda.

    Va como función: la plantilla la llama sólo si la lee, y las del mostrador
    no la leen nunca. Se calcula una vez por respuesta. `None` para el
    personal, que no tiene carrito.
    """

    @cache
    def unidades():
        if not servicio.puede_tener_carrito(request.user):
            return None
        return servicio.unidades_en(servicio.carrito_de(request))

    return {"unidades_en_carrito": unidades}
