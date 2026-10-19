"""El avance manual del pedido (`CU-PED-EST`): `CO-092` y `CO-093`.

**De a un paso y sin retroceso** (DME-07). La operación no recibe el estado
destino: en cada punto hay un único siguiente, y aceptar uno arbitrario
habilitaría saltos que el diagrama no permite.

Los dos estados de espera —de pre-venta y de artículo demorado— no se avanzan a
mano: salen por un proceso del sistema (`CO-013`, `CO-095`).
"""

import logging
from dataclasses import dataclass

from django.db import transaction
from django.template.loader import render_to_string
from django.utils import timezone

from apps.core.mail import cuerpo_html, enviar_correo
from apps.core.models import RegistroAuditoria
from apps.pedidos.models import LineaPedido, Pedido, TransicionDePedido

logger = logging.getLogger(__name__)

SIGUIENTE = {
    Pedido.PENDIENTE_ARMADO: Pedido.ARMADO,
    Pedido.ARMADO: Pedido.EMPAQUETADO,
    Pedido.EMPAQUETADO: Pedido.DESPACHADO,
}
SIGUIENTE_RETIRO = {
    Pedido.PENDIENTE_ARMADO: Pedido.ARMADO,
    Pedido.ARMADO: Pedido.EN_LOCAL,
}
AUTOMATICOS = (Pedido.ESPERANDO_PRE_VENTA, Pedido.ESPERANDO_DEMORADO)
# Qué estado toma una línea Disponible cuando el pedido llega a cada destino
# (plan 08, amb. 2). Armado no toca las líneas: DME-08 no tiene ese estado.
ESTADO_DE_LINEA = {
    Pedido.EMPAQUETADO: LineaPedido.EMPAQUETADO,
    Pedido.DESPACHADO: LineaPedido.DESPACHADO,
}
ACTIVOS = (
    Pedido.ESPERANDO_PRE_VENTA,
    Pedido.PENDIENTE_ARMADO,
    Pedido.ARMADO,
    Pedido.ESPERANDO_DEMORADO,
    Pedido.EMPAQUETADO,
)


class AvanceRechazado(ValueError):
    """`CO-092` E1, o un pedido que ya no está donde el Administrador lo vio."""


class DecisionPendiente(ValueError):
    """`CO-092` E2: hay artículos demorados sin decisión del Cliente."""

    def __init__(self, lineas):
        self.lineas = lineas
        super().__init__("Hay artículos demorados con la decisión del Cliente pendiente.")


def siguiente_estado(pedido):
    """Un pedido para retirar pasa de Armado a En el local (plan 07, octava parte)."""
    if pedido.retiro:
        return SIGUIENTE_RETIRO.get(pedido.estado)
    return SIGUIENTE.get(pedido.estado)


def pendientes_de_decision(pedido):
    return list(
        pedido.lineas.select_related("producto").filter(
            estado=LineaPedido.ESPERANDO_DEMORADO, decision_demora=""
        )
    )


def registrar_transicion(pedido, anterior, actor=None, momento=None):
    return TransicionDePedido.objects.create(
        pedido=pedido,
        estado_anterior=anterior or "",
        estado_nuevo=pedido.estado,
        actor=actor,
        ocurrida_en=momento or timezone.now(),
    )


@dataclass
class Avance:
    pedido: Pedido
    anterior: str


def avanzar(pedido, actor, *, estado_visto, confirmado=False):
    """`CO-092`, y `CO-093` cuando `confirmado` acepta la advertencia de E2.

    El pedido se toma con bloqueo y se compara contra el estado que el
    Administrador tenía en pantalla: dos administradores que avanzan a la vez el
    mismo pedido no lo saltean dos pasos.
    """
    with transaction.atomic():
        pedido = Pedido.objects.select_for_update().get(pk=pedido.pk)
        if pedido.estado in AUTOMATICOS:
            raise AvanceRechazado(
                f"Un pedido en «{pedido.get_estado_display()}» avanza sólo cuando el sistema "
                "lo resuelve: no se puede avanzar a mano."
            )
        destino = siguiente_estado(pedido)
        if destino is None:
            raise AvanceRechazado(
                f"El pedido ya está en «{pedido.get_estado_display()}»: no tiene un estado "
                "siguiente."
            )
        if pedido.estado != estado_visto:
            raise AvanceRechazado(
                "El pedido cambió mientras lo mirabas: ahora está en "
                f"«{pedido.get_estado_display()}»."
            )
        pendientes = (
            pendientes_de_decision(pedido)
            if destino in (Pedido.EMPAQUETADO, Pedido.EN_LOCAL)
            else []
        )
        if pendientes and not confirmado:
            raise DecisionPendiente(pendientes)

        anterior = pedido.estado
        momento = timezone.now()
        pedido.estado = destino
        pedido.save(update_fields=["estado"])
        if destino in ESTADO_DE_LINEA:
            # Las líneas demoradas no avanzan (CO-092 c, CO-093).
            # Tampoco la que llegó para el despacho diferido (B-08-007).
            pedido.lineas.filter(
                estado__in=(LineaPedido.DISPONIBLE, LineaPedido.EMPAQUETADO)
            ).exclude(decision_demora=LineaPedido.DESPACHO_DIFERIDO).update(
                estado=ESTADO_DE_LINEA[destino]
            )
        if destino == Pedido.EN_LOCAL:
            # Plan 07, octava parte: cada unidad entra al stock en local del Cliente.
            from apps.almacen.servicios import guardar_pedido_para_retirar

            guardar_pedido_para_retirar(pedido, actor)
        registrar_transicion(pedido, anterior, actor, momento)
        RegistroAuditoria.registrar(
            accion=RegistroAuditoria.AVANCE_ESTADO_PEDIDO,
            actor=actor,
            objetivo=pedido,
            objetivo_email=pedido.correo_de_contacto,
            detalle=(
                f"Pedido {pedido.numero}: {Pedido(estado=anterior).get_estado_display()} → "
                f"{pedido.get_estado_display()}"
                + (
                    f", con {len(pendientes)} artículo(s) con decisión pendiente"
                    if pendientes
                    else ""
                )
                + "."
            ),
        )
        transaction.on_commit(lambda: avisar_cambio_de_estado(pedido))
    return Avance(pedido=pedido, anterior=anterior)


def avisar_cambio_de_estado(pedido):
    """`CU-PED-EST` paso 4 (B-08-002): un correo al Cliente o al invitado."""
    contexto = {"pedido": pedido}
    try:
        enviar_correo(
            asunto=f"Tu pedido {pedido.numero}: {pedido.get_estado_display().lower()}",
            cuerpo=render_to_string("pedidos/correo_estado.txt", contexto),
            destinatarios=[pedido.correo_de_contacto],
            html=cuerpo_html("correo/pedido_estado.html", contexto),
        )
    except Exception:  # noqa: BLE001 - el avance ya ocurrió: un correo caído no lo deshace
        logger.exception("No se pudo avisar el estado del pedido %s.", pedido.numero)
