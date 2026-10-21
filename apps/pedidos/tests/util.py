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


# ---------------------------------------------------------------------------
# Pre-ventas y reservas (planes 01 y 08, segunda parte)
# ---------------------------------------------------------------------------


def crear_preventa(*, dias=5, precio="10000", stock=0, **extra):
    """Un tomo en Pre-venta que llega dentro de `dias` días (negativo: ya pasó)."""
    from apps.catalog.models import Producto

    return ProductoFactory(
        estado=Producto.PRE_VENTA,
        stock=stock,
        precio=Decimal(precio),
        fecha_llegada=timezone.localdate() + timedelta(days=dias),
        **extra,
    )


def reservar(
    usuario, producto, *, cantidad=1, puntos=0, otros=(), costo_envio="1500", hace_minutos=0
):
    """Un pedido Esperando pre-venta con una reserva de `producto`.

    `otros` son líneas Disponibles de productos en stock, como `(precio, cantidad)`.
    Devuelve el pedido y la línea reservada.
    """
    fecha = timezone.now() - timedelta(minutes=hace_minutos)
    pedido = Pedido.objects.create(
        canal=Pedido.ONLINE,
        estado=Pedido.ESPERANDO_PRE_VENTA,
        usuario=usuario,
        envio_direccion="Av. Colón 1234",
        envio_localidad="Córdoba",
        envio_provincia="Córdoba",
        envio_codigo_postal="X5000ABC",
        costo_envio=Decimal(costo_envio),
        fecha=fecha,
    )
    pedido.asignar_numero()
    linea = LineaPedido.objects.create(
        pedido=pedido,
        producto=producto,
        cantidad=cantidad,
        precio_unitario=producto.precio,
        cubierta_con_puntos=bool(puntos),
        puntos_canjeados=puntos,
        estado=LineaPedido.RESERVADO,
    )
    for precio, unidades in otros:
        LineaPedido.objects.create(
            pedido=pedido,
            producto=ProductoFactory(stock=5, precio=Decimal(precio)),
            cantidad=unidades,
            precio_unitario=Decimal(precio),
            estado=LineaPedido.DISPONIBLE,
        )
    TransicionDePedido.objects.create(
        pedido=pedido, estado_nuevo=pedido.estado, actor=usuario, ocurrida_en=fecha
    )
    return pedido, linea


def demorar(usuario, *, otros=(("5000", 1),), dias=3, precio="10000", puntos=0, costo_envio="1500"):
    """Un pedido con un artículo demorado sin decisión, por `CO-015`."""
    from apps.pedidos import preventa

    producto = crear_preventa(dias=dias, precio=precio)
    pedido, linea = reservar(usuario, producto, otros=otros, puntos=puntos, costo_envio=costo_envio)
    preventa.registrar_demora(producto, None)
    pedido.refresh_from_db()
    linea.refresh_from_db()
    producto.refresh_from_db()
    return producto, pedido, linea


def como_venta_de_mostrador(pedido):
    """Pasa un pedido armado a mano a venta de mostrador: canal, modalidad y estado
    van juntos (B-06-005), y la base rechaza cambiar sólo el canal."""
    Pedido.objects.filter(pk=pedido.pk).update(
        canal=Pedido.PRESENCIAL, modalidad=Pedido.MOSTRADOR, estado=Pedido.VENDIDO_EN_LOCAL
    )
    pedido.lineas.filter(estado=LineaPedido.DESPACHADO).update(
        estado=LineaPedido.ENTREGADO_EN_LOCAL
    )
    pedido.transiciones.filter(estado_nuevo=Pedido.DESPACHADO).update(
        estado_nuevo=Pedido.VENDIDO_EN_LOCAL
    )
    pedido.refresh_from_db()
    return pedido
