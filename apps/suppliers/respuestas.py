"""La respuesta del proveedor a un pedido (plan 00 de la respuesta del proveedor).

Cuando sale un pedido, el proveedor contesta qué manda y cuándo. Eso se anota acá,
línea por línea —confirmada, con otra cantidad o no disponible— y la fecha de
llegada del pedido. Desde la web (la ficha de la propuesta y la del pedido) y
desde Telegram, con las mismas reglas:

- **Lo que se espera es lo confirmado.** Cambiar la cantidad cambia lo pendiente,
  y con eso el cupo de la pre-venta. Si el proveedor confirma menos de lo que ya
  está reservado, se acepta y se avisa (ambigüedad 3): las reservas sin cubrir se
  resuelven con la demora o la cancelación que ya existen. Nada se cancela solo.
- **Lo que no puede abastecer se cierra sin recibir**, con su motivo, por el mismo
  camino que el cierre de «Pedidos por llegar» (`llegadas.cerrar_sin_recibir`).
- **Mover la fecha de una pre-venta con reservas es una demora** (ambigüedad 4):
  no se toca la fecha que ve el Cliente, y se ofrece registrar la demora. Sin
  reservas, la pre-venta toma la fecha nueva.
- Cuando todos los proveedores de una propuesta respondieron, la propuesta se
  cierra (desvío de DME-13, aprobado).

Plan 00 de la respuesta simple (B-05-015):

- **No se confirma más de lo pedido** (R2): para más unidades, otro pedido.
- **Sólo se anota lo que cambió** (R3): una línea con la misma respuesta no se
  vuelve a registrar ni a auditar.
- **El motivo es de cada línea** (R4): cada valor de `respuestas` puede traer el
  suyo; el `motivo` general sirve a las que no lo traen («No puede abastecer»).
- Lo que llega también es una respuesta (R1): eso está en `llegadas`.

El pedido se toma con bloqueo de fila, como la llegada: la web y el chat pueden
responder a la vez, y se ordenan.
"""

from dataclasses import dataclass, field
from datetime import timedelta

from django.db import transaction
from django.utils import timezone

from apps.catalog.models import Producto, ProductoEditorial
from apps.core.models import RegistroAuditoria
from apps.suppliers import llegadas
from apps.suppliers.llegadas import OperacionRechazada
from apps.suppliers.models import LineaPedidoProveedor, PedidoProveedor

# Los motivos frecuentes de «no puede», y «Otro motivo…» para escribirlo.
MOTIVOS_NO_PUEDE = ("No tiene stock", "Está discontinuado", "No trabaja ese material")
# A los cuántos días sin respuesta se recuerda (ambigüedad 6), una sola vez.
DIAS_PARA_RECORDAR = 3


@dataclass
class Resultado:
    pedido: PedidoProveedor
    respondidas: int = 0
    # Pre-ventas con más reservas que lo que ahora se espera: (producto, reservado, esperado).
    sin_cubrir: list = field(default_factory=list)
    # Pre-ventas con reservas cuya fecha se atrasaría: se ofrece la demora.
    para_demorar: list = field(default_factory=list)
    propuesta_cerrada: bool = False


def _limpio(texto):
    return " ".join((texto or "").split())[:500]


def _normalizar(valor):
    """`(respuesta, cantidad)` o `(respuesta, cantidad, motivo)`, siempre con motivo."""
    respuesta, cantidad, *resto = valor
    return respuesta, cantidad, _limpio(resto[0] if resto else "")


def _sin_cambios(linea, respuesta, cantidad):
    """R3: la línea ya tenía esa misma respuesta."""
    if respuesta == LineaPedidoProveedor.CONFIRMADA or (
        respuesta == LineaPedidoProveedor.OTRA_CANTIDAD and cantidad == linea.cantidad_pedida
    ):
        return linea.respuesta == LineaPedidoProveedor.CONFIRMADA
    if respuesta == LineaPedidoProveedor.OTRA_CANTIDAD:
        return (
            linea.respuesta == LineaPedidoProveedor.OTRA_CANTIDAD
            and linea.cantidad_confirmada == cantidad
        )
    return False


def responder(pedido, respuestas, actor, *, fecha=None, motivo="", desde=""):
    """Anota lo que contestó el proveedor.

    `respuestas` va de línea a `(respuesta, cantidad)` o `(respuesta, cantidad,
    motivo)`: `CONFIRMADA`, `OTRA_CANTIDAD` con su cantidad, o `NO_DISPONIBLE`, que
    exige un motivo, el de la línea o el `motivo` general. `fecha` es la llegada que
    promete, si la dijo. `desde` nombra el canal en la auditoría («Telegram»).
    """
    motivo = _limpio(motivo)
    respuestas = {pk: _normalizar(valor) for pk, valor in respuestas.items()}
    if not respuestas and fecha is None:
        raise OperacionRechazada("No hay nada para anotar: elegí una respuesta o una fecha.")
    if any(
        r == LineaPedidoProveedor.NO_DISPONIBLE and not (propio or motivo)
        for r, _, propio in respuestas.values()
    ):
        raise OperacionRechazada("Para lo que no puede abastecer, el motivo es obligatorio.")

    detalle = []
    with transaction.atomic():
        pedido = PedidoProveedor.objects.select_for_update().get(pk=pedido.pk)
        resultado = Resultado(pedido=pedido)
        esperaba = _propuesta_que_espera(pedido)
        if pedido.estado == PedidoProveedor.SIN_ENVIAR:
            raise OperacionRechazada("El pedido todavía no salió: reintentá el envío primero.")
        if pedido.estado != PedidoProveedor.ABIERTO:
            raise OperacionRechazada("El pedido ya está cerrado: no espera respuesta.")
        ahora = timezone.now()
        tocados = set()
        for pk in sorted(respuestas):
            respuesta, cantidad, propio = respuestas[pk]
            linea = (
                LineaPedidoProveedor.objects.select_for_update()
                .select_related("producto")
                .filter(pk=pk, pedido=pedido)
                .first()
            )
            if linea is None:
                raise OperacionRechazada("Una de las líneas no es de este pedido.")
            if linea.estado not in LineaPedidoProveedor.ABIERTAS:
                continue
            nombre = linea.producto.especifico
            if _sin_cambios(linea, respuesta, cantidad):
                continue
            if respuesta == LineaPedidoProveedor.NO_DISPONIBLE:
                razon = propio or motivo
                llegadas.cerrar_sin_recibir(linea, razon, actor)
                linea.refresh_from_db()
                linea.respuesta = LineaPedidoProveedor.NO_DISPONIBLE
                detalle.append(f"{nombre}: no disponible ({razon})")
            elif (
                respuesta == LineaPedidoProveedor.OTRA_CANTIDAD
                and cantidad != linea.cantidad_pedida
            ):
                if cantidad is None or cantidad < 1:
                    raise OperacionRechazada(
                        f"«{nombre}»: la cantidad confirmada tiene que ser mayor que cero. "
                        "Si no la manda, marcala como no disponible."
                    )
                if cantidad > linea.cantidad_pedida:
                    raise OperacionRechazada(
                        f"«{nombre}»: no se puede confirmar más de lo pedido "
                        f"({linea.cantidad_pedida}). Para más unidades, armá otro pedido."
                    )
                linea.respuesta = LineaPedidoProveedor.OTRA_CANTIDAD
                linea.cantidad_confirmada = cantidad
                if linea.cantidad_recibida >= cantidad:
                    linea.estado = LineaPedidoProveedor.RECIBIDA
                detalle.append(f"{nombre}: confirma {cantidad} de {linea.cantidad_pedida}")
            elif respuesta in (LineaPedidoProveedor.CONFIRMADA, LineaPedidoProveedor.OTRA_CANTIDAD):
                linea.respuesta = LineaPedidoProveedor.CONFIRMADA
                linea.cantidad_confirmada = None
                detalle.append(f"{nombre}: confirmada")
            else:
                raise OperacionRechazada("Respuesta desconocida.")
            linea.respondida_en = ahora
            linea.save(
                update_fields=["respuesta", "cantidad_confirmada", "estado", "respondida_en"]
            )
            resultado.respondidas += 1
            tocados.add(linea.producto_id)

        if fecha is not None:
            detalle.append(_poner_fecha(pedido, fecha, resultado))
            tocados.update(pedido.lineas.values_list("producto_id", flat=True))

        _revisar_cupos(tocados, resultado)
        llegadas._cerrar_si_corresponde(pedido)
        if detalle:
            RegistroAuditoria.registrar(
                accion=RegistroAuditoria.RESPUESTA_PROVEEDOR,
                actor=actor,
                objetivo=pedido,
                detalle=f"{pedido}: " + "; ".join(detalle) + (f" (desde {desde})" if desde else ""),
            )
        _cerrar_la_propuesta(pedido, actor)
        # Un «no puede» ya la pudo cerrar al cerrar sus líneas: se mira el antes y el después.
        resultado.propuesta_cerrada = esperaba and not _propuesta_que_espera(pedido)
    return resultado


def confirmar_todo(pedido, actor, *, fecha=None, desde=""):
    """«Confirmó todo»: cada línea abierta que no tenía respuesta, tal como se pidió,
    y la fecha si la dijo."""
    lineas = pedido.lineas.filter(
        estado__in=LineaPedidoProveedor.ABIERTAS, respuesta=LineaPedidoProveedor.SIN_RESPUESTA
    )
    respuestas = {
        pk: (LineaPedidoProveedor.CONFIRMADA, None) for pk in lineas.values_list("pk", flat=True)
    }
    if not respuestas:
        raise OperacionRechazada("No queda ninguna línea esperando respuesta.")
    return responder(pedido, respuestas, actor, fecha=fecha, desde=desde)


def no_puede(pedido, motivo, actor, *, desde=""):
    """«No puede abastecer»: todo lo que sigue abierto, con un motivo (ambigüedad 5)."""
    lineas = pedido.lineas.filter(estado__in=LineaPedidoProveedor.ABIERTAS)
    respuestas = {
        pk: (LineaPedidoProveedor.NO_DISPONIBLE, None) for pk in lineas.values_list("pk", flat=True)
    }
    if not respuestas:
        raise OperacionRechazada("No queda ninguna línea abierta en el pedido.")
    return responder(pedido, respuestas, actor, motivo=motivo, desde=desde)


def poner_fecha(pedido, fecha, actor, *, desde=""):
    return responder(pedido, {}, actor, fecha=fecha, desde=desde)


def quitar_fecha(pedido, actor, *, desde=""):
    """La fecha mal puesta se borra (plan 00 de la respuesta simple, F5). Las pre-ventas
    conservan la suya: sin fecha nueva no hay nada que mover."""
    with transaction.atomic():
        pedido = PedidoProveedor.objects.select_for_update().get(pk=pedido.pk)
        if pedido.estado != PedidoProveedor.ABIERTO:
            raise OperacionRechazada("El pedido ya está cerrado: no espera respuesta.")
        if pedido.fecha_estimada is None:
            raise OperacionRechazada("El pedido ya no tiene fecha.")
        anterior = pedido.fecha_estimada
        pedido.fecha_estimada = None
        pedido.save(update_fields=["fecha_estimada"])
        RegistroAuditoria.registrar(
            accion=RegistroAuditoria.RESPUESTA_PROVEEDOR,
            actor=actor,
            objetivo=pedido,
            detalle=f"{pedido}: sin fecha de llegada (antes, {anterior:%d/%m/%Y})"
            + (f" (desde {desde})" if desde else ""),
        )
    return pedido


def consecuencias_de_no_puede(pedido):
    """Lo que pasaría si no puede abastecer nada, para decirlo antes de confirmar:
    cuántas líneas se cierran y qué pre-ventas con reservas pierden lo que esperaban."""
    lineas = list(
        pedido.lineas.filter(estado__in=LineaPedidoProveedor.ABIERTAS).select_related("producto")
    )
    preventas = []
    for linea in lineas:
        producto = linea.producto
        if producto.estado != Producto.PRE_VENTA:
            continue
        reservas = llegadas.reservado(producto)
        if reservas:
            preventas.append(
                {
                    "producto": producto,
                    "reservas": reservas,
                    "quedan": max(0, llegadas.pendiente(producto) - linea.pendiente),
                }
            )
    return {"lineas": len(lineas), "preventas": preventas}


def _poner_fecha(pedido, fecha, resultado):
    """La fecha del pedido, y la de las pre-ventas que no tienen reservas."""
    anterior = pedido.fecha_estimada
    pedido.fecha_estimada = fecha
    pedido.save(update_fields=["fecha_estimada"])
    for linea in pedido.lineas.filter(estado__in=LineaPedidoProveedor.ABIERTAS).select_related(
        "producto"
    ):
        producto = linea.producto
        if producto.estado != Producto.PRE_VENTA:
            continue
        especifico = producto.especifico
        if llegadas.reservado(producto) > 0:
            if especifico.llegada_vigente and fecha > especifico.llegada_vigente:
                resultado.para_demorar.append(producto)
        else:
            ProductoEditorial.objects.filter(pk=producto.pk).update(fecha_llegada=fecha)
    return f"llega el {fecha:%d/%m/%Y}" + (
        f" (antes, {anterior:%d/%m/%Y})" if anterior and anterior != fecha else ""
    )


def _revisar_cupos(productos, resultado):
    for producto in Producto.objects.filter(pk__in=productos, estado=Producto.PRE_VENTA):
        reservado, esperado = llegadas.reservado(producto), llegadas.pendiente(producto)
        if reservado > esperado:
            resultado.sin_cubrir.append((producto, reservado, esperado))


def _propuesta_que_espera(pedido):
    from apps.restock.models import PropuestaRestock

    return (
        bool(pedido.propuesta_id)
        and PropuestaRestock.objects.filter(
            pk=pedido.propuesta_id, estado=PropuestaRestock.ESPERANDO
        ).exists()
    )


def _cerrar_la_propuesta(pedido, actor):
    if not pedido.propuesta_id:
        return False
    from apps.restock import servicios as restock

    return restock.al_responder(pedido.propuesta, actor)


# ---------------------------------------------------------------------------
# El recordatorio (ambigüedad 6)
# ---------------------------------------------------------------------------


def sin_respuesta():
    """Los pedidos abiertos con alguna línea esperando respuesta."""
    abiertos = PedidoProveedor.objects.filter(estado=PedidoProveedor.ABIERTO).prefetch_related(
        "lineas"
    )
    return [pedido for pedido in abiertos if not pedido.respondido]


def recordar(ahora=None):
    """Los que llevan `DIAS_PARA_RECORDAR` sin respuesta: un aviso, una sola vez.
    Lo corre el Temporizador."""
    from apps.avisos import canales

    ahora = ahora or timezone.now()
    limite = ahora - timedelta(days=DIAS_PARA_RECORDAR)
    recordados = []
    for pedido in sin_respuesta():
        if pedido.recordado_en or pedido.creado_en > limite:
            continue
        PedidoProveedor.objects.filter(pk=pedido.pk).update(recordado_en=ahora)
        canales.avisar_pedido(pedido, recordatorio=True)
        recordados.append(pedido)
    return recordados
