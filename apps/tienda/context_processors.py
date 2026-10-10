from functools import cache

from apps.accounts.models import Usuario
from apps.core.models import ConfiguracionSistema
from apps.puntos import servicios as servicios_puntos
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

    @cache
    def puntos():
        """El saldo del Cliente para el encabezado (B-10-002); `None` si no es Cliente."""
        if not (request.user.is_authenticated and request.user.rol == Usuario.CLIENTE):
            return None
        saldo = servicios_puntos.saldo(request.user)
        return {
            "saldo": saldo,
            "en_pesos": saldo * ConfiguracionSistema.obtener().equivalencia_puntos,
        }

    return {"unidades_en_carrito": unidades, "puntos_del_cliente": puntos}
