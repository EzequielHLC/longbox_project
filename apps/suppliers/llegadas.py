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
    error_de_envio="",
):
    """El pedido que salió, con una línea por `(producto, cantidad)`.

    Se llama cuando el pedido salió (decisión 1): el correo exitoso de `CO-074`, o
    el alta de un lote en pre-venta. Los productos sin stock que tenían el pedido en
    camino pasan a Pre-venta.

    Con `error_de_envio`, el correo **no** salió (B-05-014): queda «Sin enviar», a la
    vista para reintentarlo, y no abre ninguna pre-venta ni da cupo.
    """
    renglones = [(producto, cantidad) for producto, cantidad in renglones if cantidad > 0]
    if not renglones:
        return None
    pedido = PedidoProveedor.objects.create(
        proveedor=proveedor,
        origen=origen,
        estado=PedidoProveedor.SIN_ENVIAR if error_de_envio else PedidoProveedor.ABIERTO,
        error_de_envio=error_de_envio[:300],
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
    if not error_de_envio:
        for producto, _ in renglones:
            abrir_preventa(producto, fecha_estimada)
    return pedido


# ---------------------------------------------------------------------------
# Lo que viene en camino y el cupo
# ---------------------------------------------------------------------------


def lineas_abiertas(producto):
    """Lo que viene en camino: sólo de pedidos que salieron (B-05-014)."""
    return LineaPedidoProveedor.objects.filter(
        producto_id=producto.pk,
        estado__in=LineaPedidoProveedor.ABIERTAS,
        pedido__estado=PedidoProveedor.ABIERTO,
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
    # B-05-019: sumaron stock sin volver a la venta (cancelados o descatalogados).
    fuera_de_venta: list = field(default_factory=list)

    @property
    def unidades(self):
        return sum(unidades for _, unidades in self.recibidas)


def registrar_llegada(pedido, cantidades, actor, *, origen="", ingreso=None, vistas=None):
    """Lo que llegó de verdad, línea por línea. `cantidades` va de línea a unidades.

    Cero en una línea es «no llegó nada de esto todavía»: la línea sigue abierta.
    Llegar de más se acepta y queda en la auditoría (plan, decisión 3 anterior).

    `ingreso` junta lo que `CO-013` hizo con las pre-ventas, para quien lo quiera
    contar (la pantalla unificada, B-05-017).

    `vistas` va de línea a lo recibido que mostraba la revisión. Si al bloquear la
    línea ya no coincide, otro registro se adelantó y nada se suma: dos
    administradores con la misma caja la cuentan una vez.
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
            if vistas is not None and vistas.get(pk) != linea.cantidad_recibida:
                raise OperacionRechazada(
                    "Otra persona registró una llegada de este pedido mientras revisabas. "
                    "Volvé a «Por llegar» y cargá lo que falte."
                )

            linea.cantidad_recibida += unidades
            linea.estado = (
                LineaPedidoProveedor.RECIBIDA
                if linea.cantidad_recibida >= linea.esperada
                else LineaPedidoProveedor.PARCIAL
            )
            linea.recibida_en = ahora
            linea.save(
                update_fields=[
                    "cantidad_recibida",
                    "estado",
                    "recibida_en",
                    *_confirmar(linea, ahora),
                ]
            )
            resumen.recibidas.append((linea, unidades))

            if producto.estado == Producto.PRE_VENTA:
                # CO-013: cubre las reservas en orden; lo que sobra, a la venta.
                parcial = preventa.ResumenIngreso()
                preventa._ingresar(producto.pk, unidades, actor, origen, parcial)
                if ingreso is not None:
                    ingreso.sumar(parcial)
                resumen.a_preventa.append(producto)
            else:
                anterior = producto.stock
                # B-05-019: sólo vuelve a la venta lo que estaba a la venta. Un
                # producto cancelado por la editorial (terminal, CO-027) o
                # descatalogado (se reactiva con CO-036) suma el stock y conserva
                # su estado.
                a_la_venta = producto.estado in (Producto.ACTIVO, Producto.AGOTADO)
                if a_la_venta:
                    producto.estado = Producto.ACTIVO
                Producto.objects.filter(pk=producto.pk).update(
                    stock=anterior + unidades, estado=producto.estado, actualizado_en=ahora
                )
                producto.stock = anterior + unidades
                if a_la_venta:
                    restock.al_subir_stock(producto, anterior, producto.stock, origen=origen)
                    resumen.al_stock.append(producto)
                else:
                    resumen.fuera_de_venta.append(producto)

        _cerrar_si_corresponde(pedido)
        _propuesta_respondida(pedido, actor)
        RegistroAuditoria.registrar(
            accion=RegistroAuditoria.LLEGADA_PEDIDO,
            actor=actor,
            objetivo=pedido,
            detalle=f"{pedido}: "
            + "; ".join(
                f"{linea.producto.especifico} llegaron {unidades} "
                f"({linea.cantidad_recibida} de {linea.esperada})"
                + (" · de más" if linea.cantidad_recibida > linea.esperada else "")
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
            if linea.cantidad_recibida >= linea.esperada
            else LineaPedidoProveedor.PARCIAL
        )
        linea.recibida_en = momento
        linea.save(
            update_fields=[
                "cantidad_recibida",
                "estado",
                "recibida_en",
                *_confirmar(linea, momento),
            ]
        )
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
        _propuesta_respondida(linea.pedido, actor)

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


def cerrar_lineas_de(producto, motivo, actor):
    """B-05-019: lo que se pidió de un producto que ya no se vende no se espera.

    Al cancelar la pre-venta (`CO-027`) o descatalogar (`CO-034`), las líneas
    abiertas de pedidos enviados o sin enviar se cierran como no recibidas, con
    el motivo, y dejan de figurar en «Por llegar». Devuelve cuántas se cerraron.
    """
    lineas = list(
        LineaPedidoProveedor.objects.filter(
            producto_id=producto.pk,
            estado__in=LineaPedidoProveedor.ABIERTAS,
            pedido__estado__in=(PedidoProveedor.ABIERTO, PedidoProveedor.SIN_ENVIAR),
        ).order_by("pk")
    )
    for linea in lineas:
        cerrar_sin_recibir(linea, motivo, actor)
    return len(lineas)


def _confirmar(linea, momento):
    """R1 del plan 00 de la respuesta simple: **lo que llega es una respuesta**. Una
    línea que nadie había respondido queda confirmada entera al llegar algo; si
    después no manda el resto, se cierra como siempre. Devuelve los campos a guardar."""
    if linea.respuesta != LineaPedidoProveedor.SIN_RESPUESTA:
        return []
    linea.respuesta = LineaPedidoProveedor.CONFIRMADA
    linea.respondida_en = momento
    return ["respuesta", "respondida_en"]


def _propuesta_respondida(pedido, actor):
    """Lo que llega, o se da por perdido, también es la respuesta del proveedor: la
    propuesta que esperaba puede cerrarse (plan 00 de la respuesta del proveedor)."""
    if pedido.propuesta_id:
        from apps.restock import servicios as restock

        restock.al_responder(pedido.propuesta, actor)


def _cerrar_si_corresponde(pedido):
    if pedido.lineas.filter(estado__in=LineaPedidoProveedor.ABIERTAS).exists():
        return
    PedidoProveedor.objects.filter(pk=pedido.pk).update(
        estado=PedidoProveedor.CERRADO, cerrado_en=timezone.now()
    )
