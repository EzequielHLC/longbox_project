"""`CU-AVI-RES` · el resumen de la mañana (plan 00 del bot, etapa 3, punto 1; B-19-011).

Una vez por día, a la hora de Parámetros, a los Administradores que lo eligieron
(por defecto, por Telegram). **Sale siempre** (ambigüedad 2): un día sin nada
pendiente también lo dice, y así se sabe que el bot y el reloj andan.

Lo dispara el reloj por minuto (`core.reloj`). En la VM y en esta PC pueden correr
dos relojes a la vez: el día se marca con bloqueo de fila antes de mandar, y el
segundo encuentra el día ya marcado.
"""

from dataclasses import dataclass
from datetime import timedelta

from django.db import transaction
from django.utils import timezone

from apps.avisos.canales import avisar_administradores, enlace
from apps.avisos.models import RESUMEN
from apps.core.models import ConfiguracionSistema
from apps.core.templatetags.moneda import pesos

LLEGAN_HOY_A_LA_VISTA = 5


@dataclass
class Resultado:
    estado: str  # "enviado", "no es la hora" o "ya salió"


def si_corresponde(ahora=None):
    """Lo manda si ya es la hora y hoy no salió."""
    ahora = timezone.localtime(ahora or timezone.now())
    configuracion = ConfiguracionSistema.obtener()
    if ahora.time() < configuracion.hora_resumen:
        return Resultado("no es la hora")
    hoy = ahora.date()
    with transaction.atomic():
        configuracion = ConfiguracionSistema.objects.select_for_update().get(pk=configuracion.pk)
        if configuracion.resumen_enviado_el == hoy:
            return Resultado("ya salió")
        configuracion.resumen_enviado_el = hoy
        configuracion.save(update_fields=["resumen_enviado_el"])
    enviar(hoy)
    return Resultado("enviado")


def enviar(hoy):
    avisar_administradores(RESUMEN, **armar(hoy))


def armar(hoy):
    """El aviso del día, con lo que espera una decisión, lo que llega y lo de ayer."""
    from apps.caja.models import CierreDeCaja
    from apps.catalog.models import BorradorProducto, Producto, ProductoEditorial
    from apps.pedidos.models import Pedido
    from apps.restock import servicios as restock
    from apps.suppliers.models import CorreoProveedor, PedidoProveedor

    ayer = hoy - timedelta(days=1)
    preventas = [
        p
        for p in ProductoEditorial.objects.filter(estado=Producto.PRE_VENTA).order_by("titulo")
        if p.llegada_vigente and p.llegada_vigente <= hoy
    ]
    llegan_hoy = [p for p in preventas if p.llegada_vigente == hoy]
    atrasadas = len(preventas) - len(llegan_hoy)
    pedidos_atrasados = sum(
        1
        for p in PedidoProveedor.objects.filter(estado=PedidoProveedor.ABIERTO)
        if p.fecha_estimada and p.fecha_estimada < hoy
    )
    ventas = list(
        Pedido.objects.filter(canal=Pedido.ONLINE, fecha__date=ayer)
        .exclude(estado=Pedido.CANCELADO)
        .prefetch_related("lineas")
    )
    cierre = CierreDeCaja.objects.filter(fecha_jornada=ayer).first()
    filas = [
        ("Correos de proveedores sin decidir", CorreoProveedor.objects.pendientes().count()),
        ("Borradores para revisar", BorradorProducto.objects.pendientes().count()),
        (
            "Pedidos de clientes por armar",
            Pedido.objects.filter(estado=Pedido.PENDIENTE_ARMADO).count(),
        ),
        ("Propuesta de restock", "pendiente" if restock.pendiente() else "ninguna"),
        ("Pre-ventas que llegan hoy", len(llegan_hoy)),
        ("Pre-ventas atrasadas", atrasadas),
        ("Pedidos a proveedores atrasados", pedidos_atrasados),
        (
            "Ventas online de ayer",
            (
                f"{len(ventas)} por {pesos(sum((p.total for p in ventas), 0))}"
                if ventas
                else "ninguna"
            ),
        ),
        ("Caja de ayer", f"cerrada, {pesos(cierre.total_global)}" if cierre else "sin cerrar"),
    ]
    parrafos = []
    if llegan_hoy:
        titulos = ", ".join(str(p) for p in llegan_hoy[:LLEGAN_HOY_A_LA_VISTA])
        resto = len(llegan_hoy) - LLEGAN_HOY_A_LA_VISTA
        parrafos.append(f"Llegan hoy: {titulos}" + (f" y {resto} más." if resto > 0 else "."))
    return {
        "asunto": f"Longbox — resumen del {hoy:%d/%m/%Y}",
        "antetitulo": "Resumen de la mañana",
        "titulo": f"Buen día: así arranca el {hoy:%d/%m}",
        "parrafos": parrafos,
        "filas": filas,
        "enlace": enlace("core:panel"),
        "texto_enlace": "Abrir el panel",
    }
