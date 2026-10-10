"""Pedidos armados a mano para las pruebas de los módulos 08, 10 y 11."""

from datetime import timedelta
from decimal import Decimal

from django.utils import timezone

from apps.catalog.tests.factories import ProductoFactory
from apps.pedidos.models import LineaPedido, Pedido, TransaccionPago, TransicionDePedido


def crear_pedido(
    usuario=None,
    *,
    estado=Pedido.PENDIENTE_ARMADO,
    correo_invitado="",
    lineas=(("10000", 1),),
    costo_envio="1500",
    hace_dias=0,
    con_pago=True,
):
    """Un pedido online con sus líneas, su pago y su primera transición."""
    fecha = timezone.now() - timedelta(days=hace_dias)
    if usuario is None and not correo_invitado:
        correo_invitado = "invitado@correo.test"
    pedido = Pedido.objects.create(
        canal=Pedido.ONLINE,
        estado=estado,
        usuario=usuario,
        correo_invitado="" if usuario else correo_invitado,
        envio_direccion="Av. Colón 1234",
        envio_localidad="Córdoba",
        envio_provincia="Córdoba",
        envio_codigo_postal="X5000ABC",
        costo_envio=Decimal(costo_envio),
        fecha=fecha,
    )
    pedido.asignar_numero()
    total = Decimal(costo_envio)
    for precio, cantidad, *resto in lineas:
        puntos = resto[0] if resto else 0
        LineaPedido.objects.create(
            pedido=pedido,
            producto=ProductoFactory(stock=5, precio=Decimal(precio)),
            cantidad=cantidad,
            precio_unitario=Decimal(precio),
            cubierta_con_puntos=bool(puntos),
            puntos_canjeados=puntos,
            estado=LineaPedido.DISPONIBLE,
        )
        if not puntos:
            total += Decimal(precio) * cantidad
    if con_pago:
        TransaccionPago.objects.create(
            pedido=pedido,
            medio=TransaccionPago.PASARELA,
            monto=total,
            estado=TransaccionPago.APROBADO,
            referencia=f"prueba-{pedido.pk}",
        )
    TransicionDePedido.objects.create(
        pedido=pedido, estado_nuevo=estado, actor=usuario, ocurrida_en=fecha
    )
    return pedido
