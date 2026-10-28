"""Las consultas del bot (`CU-AVI-CON`, decisión 10 del plan): fijas y de sólo lectura.

Cada una lee y devuelve el texto para el chat, en el HTML de Telegram. Se llegan
por su comando (`/stock`, `/llega`, `/pendientes`, `/caja`) o por una pregunta
libre, que el modelo traduce a una de ellas (`asistente.elegir_consulta`).
**Ninguna escribe**: lo que cambia algo se hace en la web.
"""

import html
import re
from datetime import timedelta

from django.db.models import Q
from django.utils import timezone

from apps.avisos.canales import enlace
from apps.catalog import isbn as isbn_util
from apps.catalog.models import BorradorProducto, Producto, ProductoEditorial
from apps.core.templatetags.moneda import pesos
from apps.suppliers import llegadas
from apps.suppliers.extraccion import separar_volumen
from apps.suppliers.models import CorreoProveedor, PedidoProveedor

LIMITE = 5
_NUMERO_AL_FINAL = re.compile(r"^(?P<titulo>.*?\S)\s+(?P<numero>\d+)$")


def _e(texto):
    return html.escape(str(texto))


def _fecha(valor):
    return valor.strftime("%d/%m/%Y") if valor else "sin fecha"


# ---------------------------------------------------------------------------
# /stock
# ---------------------------------------------------------------------------


def buscar(texto, limite=LIMITE):
    """Productos por código, por ISBN o por título (con su tomo si lo trae)."""
    texto = " ".join((texto or "").split())
    if not texto:
        return []
    productos = Producto.objects.exclude(estado=Producto.DESCATALOGADO).select_related(
        "productoeditorial", "productonoeditorial"
    )
    exacto = Q(codigo__iexact=texto)
    isbn = isbn_util.normalizar(texto)
    if isbn:
        exacto |= Q(productoeditorial__isbn=isbn)
    encontrados = list(productos.filter(exacto)[:limite])
    if encontrados:
        return encontrados
    titulo, volumen = separar_volumen(texto)
    if volumen is None and (pegado := _NUMERO_AL_FINAL.match(texto)):
        titulo, volumen = pegado.group("titulo"), int(pegado.group("numero"))
    filtro = Q(titulo__icontains=titulo)
    if volumen is not None:
        filtro &= Q(productoeditorial__volumen=volumen)
    return list(productos.filter(filtro).order_by("titulo", "productoeditorial__volumen")[:limite])


def stock(texto):
    if not texto:
        return "Decime qué buscar: <code>/stock Chainsaw Man 12</code>, un código o un ISBN."
    encontrados = buscar(texto)
    if not encontrados:
        return f"No encontré nada con «{_e(texto)}»."
    bloques = []
    for producto in encontrados:
        especifico = producto.especifico
        linea = (
            f"<b>{_e(especifico)}</b> · <code>{_e(producto.codigo)}</code>\n"
            f"Stock {producto.stock} · {_e(producto.get_estado_display())} · "
            f"{_e(pesos(producto.precio))}"
        )
        if producto.estado == Producto.PRE_VENTA:
            linea += (
                f"\nLlega el {_fecha(especifico.llegada_vigente)} · "
                f"{llegadas.reservado(producto)} reservadas · cupo {llegadas.cupo(producto)}"
            )
        bloques.append(linea)
    return "\n\n".join(bloques)


# ---------------------------------------------------------------------------
# /llega
# ---------------------------------------------------------------------------


def llega(dias=7):
    hoy = timezone.localdate()
    hasta = hoy + timedelta(days=dias)
    preventas = [
        p
        for p in ProductoEditorial.objects.filter(estado=Producto.PRE_VENTA).order_by(
            "fecha_llegada", "titulo", "volumen"
        )
        if p.llegada_vigente and p.llegada_vigente <= hasta
    ]
    pedidos = [
        p
        for p in PedidoProveedor.objects.filter(estado=PedidoProveedor.ABIERTO)
        .select_related("proveedor")
        .prefetch_related("lineas")
        .order_by("fecha_estimada")
        if p.fecha_estimada and p.fecha_estimada <= hasta
    ]
    if not preventas and not pedidos:
        return f"No llega nada en los próximos {dias} días, y no hay nada atrasado."
    partes = []
    if preventas:
        filas = [
            f"• {_e(p)} — {_fecha(p.llegada_vigente)}"
            + (" <b>(atrasada)</b>" if p.llegada_vigente < hoy else "")
            for p in preventas[:15]
        ]
        partes.append(f"<b>Pre-ventas</b> ({len(preventas)})\n" + "\n".join(filas))
    if pedidos:
        filas = [
            f"• Pedido #{p.pk} · {_e(p.nombre_proveedor)} — {_fecha(p.fecha_estimada)}"
            f" · faltan {p.unidades_pendientes}"
            + (" <b>(atrasado)</b>" if p.fecha_estimada < hoy else "")
            for p in pedidos[:10]
        ]
        partes.append(f"<b>Pedidos a proveedores</b> ({len(pedidos)})\n" + "\n".join(filas))
    ver = enlace("suppliers:pedido_lista")
    if ver:
        partes.append(f'<a href="{_e(ver)}">Pedidos por llegar</a>')
    return "\n\n".join(partes)


# ---------------------------------------------------------------------------
# /pendientes
# ---------------------------------------------------------------------------


def pendientes():
    from apps.pedidos.models import Pedido
    from apps.restock import servicios as restock

    correos = CorreoProveedor.objects.pendientes().select_related("proveedor")
    borradores = BorradorProducto.objects.pendientes().count()
    por_armar = Pedido.objects.filter(estado=Pedido.PENDIENTE_ARMADO).count()
    propuesta = restock.pendiente()
    filas = [
        f"• Correos de proveedores sin decidir: <b>{correos.count()}</b>",
        f"• Borradores para revisar: <b>{borradores}</b>",
        f"• Pedidos de clientes por armar: <b>{por_armar}</b>",
        f"• Propuesta de restock: <b>{'pendiente' if propuesta else 'ninguna'}</b>",
    ]
    texto = "<b>Lo que espera una decisión</b>\n" + "\n".join(filas)
    ultimos = list(correos[:3])
    if ultimos:
        texto += "\n\n" + "\n".join(
            f"✉ {_e(c.proveedor)}: {_e(c.asunto or 'sin asunto')}" for c in ultimos
        )
    return texto


# ---------------------------------------------------------------------------
# /caja
# ---------------------------------------------------------------------------


def caja():
    from apps.caja import servicios as caja_servicios

    resumen = caja_servicios.resumen_previo()
    if resumen.cierre_de_hoy:
        return f"La caja de hoy ya se cerró: {_e(pesos(resumen.cierre_de_hoy.total_global))}."
    filas = [f"• {_e(canal)}: {_e(pesos(monto))}" for canal, monto in resumen.por_canal]
    texto = f"<b>Cobrado sin cerrar: {_e(pesos(resumen.total_global))}</b>\n" + "\n".join(filas)
    if resumen.pendientes:
        texto += f"\n\n{len(resumen.pendientes)} pago(s) esperando verificación."
    return texto
