"""Los avisos de venta (plan 00 del bot, etapa 3, punto 2; B-19-011).

Sale uno por cada pago online aprobado, con lo que se vendió y lo que quedó
reservado de pre-venta, y otro si esa venta agotó el cupo de una pre-venta. **Sólo
las ventas online** (ambigüedad 3): la del mostrador la hace alguien que está en
el local. Corre después de confirmar la transacción y en segundo plano: un
Telegram caído no frena ni deshace un pago.
"""

from apps.avisos.canales import avisar_administradores, enlace
from apps.avisos.models import VENTAS
from apps.core.templatetags.moneda import pesos


def avisar_venta(pedido):
    from apps.catalog.models import Producto
    from apps.suppliers import llegadas

    lineas = list(pedido.lineas.select_related("producto"))
    filas = [
        (
            f"{linea.producto.especifico} × {linea.cantidad}",
            pesos(linea.subtotal)
            + (" · reserva" if linea.producto.estado == Producto.PRE_VENTA else ""),
        )
        for linea in lineas
    ]
    if pedido.costo_envio:
        filas.append(("Envío", pesos(pedido.costo_envio)))
    cliente = (
        pedido.usuario.get_full_name() or pedido.usuario.email
        if pedido.usuario_id
        else f"{pedido.correo_invitado} (invitado)"
    )
    avisar_administradores(
        VENTAS,
        asunto=f"Longbox — venta online {pedido.numero}",
        antetitulo="Venta online",
        titulo=f"{pedido} · {pesos(pedido.total)}",
        parrafos=[f"{cliente}, {'retira en el local' if pedido.retiro else 'con envío'}."],
        filas=filas,
        enlace=enlace("pedidos:detalle", pedido.pk),
        texto_enlace="Ver el pedido",
    )
    agotadas = {
        linea.producto_id: linea.producto
        for linea in lineas
        if linea.producto.estado == Producto.PRE_VENTA and llegadas.cupo(linea.producto) == 0
    }
    for producto in agotadas.values():
        avisar_administradores(
            VENTAS,
            asunto=f"Longbox — la pre-venta de {producto} agotó su cupo",
            antetitulo="Pre-venta sin cupo",
            titulo=f"{producto.especifico} agotó el cupo",
            parrafos=[
                f"Con el {pedido} se reservó todo lo que viene en camino "
                f"({llegadas.reservado(producto)} unidades). Nadie más puede reservarla "
                "hasta que se pida más al proveedor."
            ],
            enlace=enlace("pedidos:preventas"),
            texto_enlace="Ver las pre-ventas",
        )
