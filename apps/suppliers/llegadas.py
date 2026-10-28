"""El pedido a proveedor: registrarlo, el cupo de la pre-venta y su llegada.

Plan 00 del circuito con los proveedores. **La pre-venta es vender lo que viene
en camino**: un producto editorial sin stock con unidades pendientes en un pedido
pasa a Pre-venta y se reserva hasta su cupo, que es lo pendiente menos el margen
de Parámetros menos lo ya reservado. Con stock en el local se vende el stock; al
agotarse, si hay pedido en camino, la reserva se abre sola (decisión 4).

**Una sola llegada.** `registrar_llegada` suma lo recibido a la línea del pedido
y lleva las unidades al producto: en Pre-venta, por `CO-013` (cubre las reservas
en orden y lo que sobra queda a la venta); sin reservas, directo al stock con los
avisos de `CO-077`. La pantalla vieja de «Pre-ventas por llegar» descuenta lo que
confirma de estas mismas líneas (`descontar`), así que el stock no se cuenta dos
veces por ningún camino.

Orden de bloqueo: producto antes que las líneas del pedido, como en `preventa`.
"""

from dataclasses import dataclass, field

from django.db import transaction
from django.db.models import Sum
from django.utils import timezone

from apps.catalog.models import Producto, ProductoEditorial
from apps.core.models import ConfiguracionSistema, RegistroAuditoria
from apps.pedidos.models import LineaPedido, Pedido
from apps.suppliers.models import LineaPedidoProveedor, PedidoProveedor


class OperacionRechazada(ValueError):
    """Lo que la operación no admite, con el mensaje para la pantalla."""


# ---------------------------------------------------------------------------
# Registrar el pedido
# ---------------------------------------------------------------------------


def registrar(
    proveedor,
    origen,
    renglones,
    actor=None,
    *,
    fecha_estimada=None,
    propuesta=None,
    sesion=None,
    lote=None,
):
    """El pedido que salió, con una línea por `(producto, cantidad)`.

    Se llama **sólo cuando el pedido salió** (decisión 1): el correo exitoso de
    `CO-074`, o el alta de un lote en pre-venta. Los productos sin stock que
    tenían el pedido en camino pasan a Pre-venta.
    """
    renglones = [(producto, cantidad) for producto, cantidad in renglones if cantidad > 0]
    if not renglones:
        return None
    pedido = PedidoProveedor.objects.create(
        proveedor=proveedor,
        origen=origen,
        fecha_estimada=fecha_estimada,
        creado_por=actor,
        propuesta=propuesta,
        sesion=sesion,
        lote=lote,
    )
    LineaPedidoProveedor.objects.bulk_create(
        LineaPedidoProveedor(pedido=pedido, producto=producto, cantidad_pedida=cantidad)
        for producto, cantidad in renglones
    )
    for producto, _ in renglones:
        abrir_preventa(producto, fecha_estimada)
    return pedido


# ---------------------------------------------------------------------------
# Lo que viene en camino y el cupo
# ---------------------------------------------------------------------------


def lineas_abiertas(producto):
    return LineaPedidoProveedor.objects.filter(
        producto_id=producto.pk, estado__in=LineaPedidoProveedor.ABIERTAS
    )


def pendiente(producto):
    """Las unidades pedidas de este producto que todavía pueden llegar."""
    return sum(linea.pendiente for linea in lineas_abiertas(producto))


def reservado(producto):
    """Las unidades reservadas sin cubrir, de pedidos que siguen vigentes."""
    return (
        LineaPedido.objects.filter(
            producto_id=producto.pk,
            estado__in=(LineaPedido.RESERVADO, LineaPedido.ESPERANDO_DEMORADO),
        )
        .exclude(pedido__estado=Pedido.CANCELADO)
        .aggregate(total=Sum("cantidad"))["total"]
        or 0
    )


def cupo_total(producto):
    """Lo pendiente menos el margen de Parámetros, hacia abajo (decisión 2)."""
    margen = ConfiguracionSistema.obtener().margen_cupo_preventa
    return pendiente(producto) * (100 - margen) // 100


def cupo(producto):
    """Cuántas unidades más se pueden reservar. Nunca negativo."""
    return max(0, cupo_total(producto) - reservado(producto))


def abrir_preventa(producto, fecha_estimada=None):
    """Un producto editorial sin stock con algo en camino pasa a Pre-venta.

    Con stock no: se vende lo que hay (decisión 4), y la reserva se abre recién
    cuando se agota (`al_agotarse`). El no editorial no tiene pre-venta (I-06,
    decisión 3). Devuelve si cambió.
    """
    editorial = ProductoEditorial.objects.filter(pk=producto.pk).first()
    if editorial is None or editorial.stock > 0:
        return False
    if editorial.estado not in (Producto.ACTIVO, Producto.AGOTADO):
        return False
    if pendiente(editorial) <= 0:
        return False
    editorial.estado = Producto.PRE_VENTA
    editorial.fecha_llegada = fecha_estimada or editorial.fecha_llegada
    editorial.demorado = False
    editorial.save(update_fields=["estado", "fecha_llegada", "demorado", "actualizado_en"])
    return True


def al_agotarse(producto):
    """La venta dejó el producto en cero: si hay pedido en camino, se reserva."""
    lineas = lineas_abiertas(producto).select_related("pedido").order_by("pedido__creado_en")
    primera = lineas.first()
    return abrir_preventa(producto, primera.pedido.fecha_estimada if primera else None)


# ---------------------------------------------------------------------------
# La llegada
# ---------------------------------------------------------------------------


@dataclass
class ResumenLlegada:
    recibidas: list = field(default_factory=list)  # (línea, unidades)
    a_preventa: list = field(default_factory=list)  # productos que pasaron por CO-013
    al_stock: list = field(default_factory=list)  # productos que sumaron stock

    @property
    def unidades(self):
        return sum(unidades for _, unidades in self.recibidas)


def registrar_llegada(pedido, cantidades, actor, *, origen=""):
    """Lo que llegó de verdad, línea por línea. `cantidades` va de línea a unidades.

    Cero en una línea es «no llegó nada de esto todavía»: la línea sigue abierta.
    Llegar de más se acepta y queda en la auditoría (plan, decisión 3 anterior).
    """
    from apps.pedidos import preventa
    from apps.restock import servicios as restock

    if any(cantidad < 0 for cantidad in cantidades.values()):
        raise OperacionRechazada("Las unidades recibidas no pueden ser negativas.")
    if not any(cantidades.values()):
        raise OperacionRechazada("Indicá cuántas unidades llegaron de al menos un producto.")

    resumen = ResumenLlegada()
    with transaction.atomic():
        pedido = PedidoProveedor.objects.select_for_update().get(pk=pedido.pk)
        lineas = {
            linea.pk: linea
            for linea in pedido.lineas.select_related("producto").filter(
                estado__in=LineaPedidoProveedor.ABIERTAS
            )
        }
        ahora = timezone.now()
        for pk in sorted(cantidades):
            unidades = cantidades[pk]
            linea = lineas.get(pk)
            if not unidades:
                continue
            if linea is None:
                raise OperacionRechazada("Una de las líneas ya no está esperando mercadería.")
            producto = Producto.objects.select_for_update().get(pk=linea.producto_id)
            linea = LineaPedidoProveedor.objects.select_for_update().get(pk=linea.pk)

            linea.cantidad_recibida += unidades
            linea.estado = (
                LineaPedidoProveedor.RECIBIDA
                if linea.cantidad_recibida >= linea.cantidad_pedida
                else LineaPedidoProveedor.PARCIAL
            )
            linea.recibida_en = ahora
            linea.save(update_fields=["cantidad_recibida", "estado", "recibida_en"])
            resumen.recibidas.append((linea, unidades))

            if producto.estado == Producto.PRE_VENTA:
                # CO-013: cubre las reservas en orden; lo que sobra, a la venta.
                parcial = preventa.ResumenIngreso()
                preventa._ingresar(producto.pk, unidades, actor, origen, parcial)
                resumen.a_preventa.append(producto)
            else:
                anterior = producto.stock
                Producto.objects.filter(pk=producto.pk).update(
                    stock=anterior + unidades, estado=Producto.ACTIVO, actualizado_en=ahora
                )
                producto.stock = anterior + unidades
                restock.al_subir_stock(producto, anterior, producto.stock, origen=origen)
                resumen.al_stock.append(producto)

        _cerrar_si_corresponde(pedido)
        RegistroAuditoria.registrar(
            accion=RegistroAuditoria.LLEGADA_PEDIDO,
            actor=actor,
            objetivo=pedido,
            detalle=f"{pedido}: "
            + "; ".join(
                f"{linea.producto.especifico} llegaron {unidades} "
                f"({linea.cantidad_recibida} de {linea.cantidad_pedida})"
                + (" · de más" if linea.cantidad_recibida > linea.cantidad_pedida else "")
                for linea, unidades in resumen.recibidas
            ),
        )
    return resumen


def descontar(producto, unidades, momento=None):
    """Lo que confirmó la pantalla de pre-ventas, contra las líneas abiertas del
    producto, de la más vieja a la más nueva. Lo que sobre no se descuenta de nada:
    una pre-venta anterior al registro de pedidos puede no tener línea."""
    momento = momento or timezone.now()
    queda = unidades
    lineas = (
        lineas_abiertas(producto)
        .select_for_update()
        .select_related("pedido")
        .order_by("pedido__creado_en", "pk")
    )
    for linea in lineas:
        if queda <= 0:
            break
        toma = min(queda, linea.pendiente)
        linea.cantidad_recibida += toma
        linea.estado = (
            LineaPedidoProveedor.RECIBIDA
            if linea.cantidad_recibida >= linea.cantidad_pedida
            else LineaPedidoProveedor.PARCIAL
        )
        linea.recibida_en = momento
        linea.save(update_fields=["cantidad_recibida", "estado", "recibida_en"])
        _cerrar_si_corresponde(linea.pedido)
        queda -= toma


def cerrar_sin_recibir(linea, motivo, actor):
    """Lo que no va a llegar: la línea se cierra con su motivo, sin tocar el stock.

    Si el producto estaba en Pre-venta sólo por esta línea y nadie lo reservó,
    deja de estarlo. Si tiene reservas, sigue en Pre-venta y se avisa: quedan para
    la demora o la cancelación de la pre-venta, que deciden con el Cliente.
    """
    motivo = (motivo or "").strip()
    if not motivo:
        raise OperacionRechazada("El motivo es obligatorio.")
    with transaction.atomic():
        producto = Producto.objects.select_for_update().get(pk=linea.producto_id)
        linea = LineaPedidoProveedor.objects.select_for_update().get(pk=linea.pk)
        if linea.estado not in LineaPedidoProveedor.ABIERTAS:
            raise OperacionRechazada("Esa línea ya no está esperando mercadería.")
        faltaban = linea.pendiente
        linea.estado = LineaPedidoProveedor.SIN_RECIBIR
        linea.motivo_cierre = motivo
        linea.save(update_fields=["estado", "motivo_cierre"])
        _cerrar_si_corresponde(linea.pedido)

        con_reservas = reservado(producto) > 0
        if producto.estado == Producto.PRE_VENTA and pendiente(producto) == 0 and not con_reservas:
            Producto.objects.filter(pk=producto.pk).update(
                estado=Producto.AGOTADO if producto.stock == 0 else Producto.ACTIVO,
                actualizado_en=timezone.now(),
            )
            ProductoEditorial.objects.filter(pk=producto.pk).update(fecha_llegada=None)
        RegistroAuditoria.registrar(
            accion=RegistroAuditoria.CIERRE_SIN_RECIBIR,
            actor=actor,
            objetivo=linea.pedido,
            detalle=(
                f"{linea.pedido}: {producto.especifico}, {faltaban} sin recibir. "
                f"Motivo: {motivo}"
            ),
        )
    return con_reservas


def _cerrar_si_corresponde(pedido):
    if pedido.lineas.filter(estado__in=LineaPedidoProveedor.ABIERTAS).exists():
        return
    PedidoProveedor.objects.filter(pk=pedido.pk).update(
        estado=PedidoProveedor.CERRADO, cerrado_en=timezone.now()
    )
