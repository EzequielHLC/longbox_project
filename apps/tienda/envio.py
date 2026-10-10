"""El costo de envío (B-07-032) y cuánto falta para que sea gratis (B-07-037).

Lo usan el carrito, el checkout y el resumen del invitado. Vive aparte porque el
carrito y la compra lo necesitan los dos, y la compra ya depende del carrito.
"""

from dataclasses import dataclass
from decimal import ROUND_FLOOR, Decimal

from apps.core.models import ConfiguracionSistema


def costo_de_envio(subtotal_productos, configuracion=None):
    """Gratis desde el monto mínimo; si no, el costo fijo de Parámetros.

    Se compara contra el subtotal de los productos antes del canje (B-07-033):
    canjear puntos nunca encarece el envío. No depende del destino.
    """
    configuracion = configuracion or ConfiguracionSistema.obtener()
    if subtotal_productos >= configuracion.monto_minimo_envio_gratuito:
        return Decimal("0")
    return configuracion.costo_envio


@dataclass
class EstadoDeEnvio:
    """Lo que dibuja la barra: el costo, lo que falta y cuánto se avanzó."""

    subtotal: Decimal
    costo: Decimal
    minimo: Decimal

    @property
    def gratis(self):
        return self.costo == 0

    @property
    def falta(self):
        return max(self.minimo - self.subtotal, Decimal("0"))

    @property
    def porcentaje(self):
        if self.minimo <= 0 or self.subtotal >= self.minimo:
            return 100
        return int((self.subtotal * 100 / self.minimo).to_integral_value(rounding=ROUND_FLOOR))


def estado_de_envio(subtotal_productos, configuracion=None):
    configuracion = configuracion or ConfiguracionSistema.obtener()
    return EstadoDeEnvio(
        subtotal=subtotal_productos,
        costo=costo_de_envio(subtotal_productos, configuracion),
        minimo=configuracion.monto_minimo_envio_gratuito,
    )
