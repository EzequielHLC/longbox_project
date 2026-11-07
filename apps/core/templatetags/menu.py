"""Lo que espera al Administrador, contado en el menú (plan 00 de interfaz, U5).

Cuentas chicas, sólo cuando se dibuja el menú del Administrador: pedidos por
armar, reclamos de devolución sin resolver, productos de la propuesta de restock
pendiente, pedidos a proveedor sin enviar y correos sin decidir. Sólo leen.
"""

from django import template

from apps.devoluciones.models import CasoDevolucion
from apps.pedidos.models import Pedido
from apps.restock.models import LineaPropuestaRestock, PropuestaRestock
from apps.suppliers.models import CorreoProveedor, PedidoProveedor

register = template.Library()


@register.simple_tag
def pendientes_del_menu():
    return {
        "pedidos": Pedido.objects.filter(
            canal=Pedido.ONLINE, estado=Pedido.PENDIENTE_ARMADO
        ).count(),
        "devoluciones": CasoDevolucion.objects.filter(estado=CasoDevolucion.PENDIENTE).count(),
        "restock": LineaPropuestaRestock.objects.filter(
            propuesta__estado=PropuestaRestock.PENDIENTE,
            estado_despacho=LineaPropuestaRestock.PENDIENTE,
        ).count(),
        # B-00-031: lo que espera una mano en «Compras a proveedores».
        "sin_enviar": PedidoProveedor.objects.filter(estado=PedidoProveedor.SIN_ENVIAR).count(),
        "correos": CorreoProveedor.objects.pendientes().count(),
    }
