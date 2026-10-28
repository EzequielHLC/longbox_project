"""Las pre-ventas que ya existían reciben su pedido (plan 00 del circuito, ambigüedad 1).

Desde el plan, una pre-venta se reserva contra lo pendiente de un pedido a
proveedor. Las que ya estaban cargadas no tenían ninguno: cada una con stock o con
reservas recibe un pedido «anterior al registro de pedidos» por la mayor de las dos
cantidades, y su stock queda en cero, porque ese stock eran unidades pedidas, no en
la mano (B-01-016: se contaban dos veces al llegar).

Una pre-venta sin stock ni reservas no recibe nada: no hay de dónde sacar una
cantidad sin inventarla. Queda sin cupo hasta que se registre su pedido a mano.
"""

from django.db import migrations
from django.db.models import Sum

RESERVAS = ("reservado", "esperando_demorado")


def armar_pedidos(apps, schema_editor):
    ProductoEditorial = apps.get_model("catalog", "ProductoEditorial")
    Producto = apps.get_model("catalog", "Producto")
    LineaPedido = apps.get_model("pedidos", "LineaPedido")
    Proveedor = apps.get_model("suppliers", "Proveedor")
    PedidoProveedor = apps.get_model("suppliers", "PedidoProveedor")
    LineaPedidoProveedor = apps.get_model("suppliers", "LineaPedidoProveedor")

    for producto in ProductoEditorial.objects.filter(estado="pre_venta"):
        reservas = (
            LineaPedido.objects.filter(producto_id=producto.pk, estado__in=RESERVAS)
            .exclude(pedido__estado="cancelado")
            .aggregate(total=Sum("cantidad"))["total"]
            or 0
        )
        cantidad = max(producto.stock, reservas)
        if cantidad <= 0:
            continue
        proveedor = producto.proveedor or (
            Proveedor.objects.filter(editorial_id=producto.editorial_id).order_by("pk").first()
        )
        pedido = PedidoProveedor.objects.create(
            proveedor=proveedor, origen="migracion", fecha_estimada=producto.fecha_llegada
        )
        LineaPedidoProveedor.objects.create(
            pedido=pedido, producto_id=producto.pk, cantidad_pedida=cantidad
        )
        Producto.objects.filter(pk=producto.pk).update(stock=0)


class Migration(migrations.Migration):
    dependencies = [
        ("suppliers", "0006_pedidos_a_proveedor"),
        ("pedidos", "0007_venta_de_mostrador"),
        ("catalog", "0025_importes_del_lote"),
    ]

    operations = [migrations.RunPython(armar_pedidos, migrations.RunPython.noop)]
