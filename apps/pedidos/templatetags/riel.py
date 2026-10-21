"""El riel de un pedido desde la plantilla (plan 00 de interfaz, P7).

Una venta de mostrador no recorre nada: no tiene riel. Con las transiciones
precargadas (`prefetch_related("transiciones")`), no hace consultas.
"""

from django import template

from apps.pedidos.models import Pedido
from apps.pedidos.riel import riel_de

register = template.Library()


@register.filter
def riel(pedido):
    if pedido.canal == Pedido.PRESENCIAL:
        return None
    return riel_de(pedido, list(pedido.transiciones.all()))
