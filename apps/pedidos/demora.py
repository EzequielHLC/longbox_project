"""El Cliente ante un artículo demorado (plan 08, segunda parte).

`CO-184` muestra las opciones, `CO-094` pide la confirmación, `CO-095` registra
la decisión y `CO-098` cancela con reembolso. El Temporizador cierra las
ventanas vencidas (`CO-096`) y acredita la compensación semanal (`CO-097`).
Lo que los contratos no dicen está en B-08-004 a B-08-010.
"""

import logging
from dataclasses import dataclass
from decimal import Decimal

from django.db import transaction
from django.utils import timezone

from apps.core.models import ConfiguracionSistema, RegistroAuditoria
from apps.core.segundo_plano import despues_del_commit
from apps.pedidos import avisos
from apps.pedidos.models import LineaPedido, Pedido
from apps.pedidos.preventa import (
    fecha,
    nombre,
    puntos_de_envio,
    puntos_de_reembolso,
    ubicar_pedido,
)
from apps.pedidos.servicios import registrar_transicion
from apps.puntos import servicios as puntos
from apps.puntos.models import LotePuntos

logger = logging.getLogger(__name__)

TASA_SEMANAL = Decimal("0.05")
TOPE = Decimal("0.25")
CENTAVO = Decimal("0.01")


class DecisionRechazada(ValueError):
    """La línea ya no admite una decisión, o la opción no corresponde."""


@dataclass(frozen=True)
class Opcion:
    clave: str
    titulo: str
    descripcion: str
    consecuencia: str


PAUSAR = Opcion(
    LineaPedido.PAUSAR,
    "Esperar el pedido completo",
    "El pedido sale cuando llegue todo. No tenés que hacer nada más.",
    "Tu pedido queda en pausa y sale cuando llegue este artículo.",
)
DIFERIR = Opcion(
    LineaPedido.DESPACHO_DIFERIDO,
    "Recibir ahora lo disponible",
    "Despachamos lo que ya está. El artículo demorado queda en el local a tu nombre cuando "
    "llegue, y mientras tanto sumás el 5 % de su valor en puntos por semana de espera, hasta "
    "el 25 %.",
    "Despachamos lo disponible y este artículo queda a tu nombre en el local cuando llegue.",
)
# Plan 07, octava parte (ambigüedad 3): la misma opción en un pedido para retirar.
DIFERIR_RETIRO = Opcion(
    LineaPedido.DESPACHO_DIFERIDO,
    "Retirar ahora lo disponible",
    "Preparamos lo que ya está para que lo retires. El artículo demorado queda en el local a "
    "tu nombre cuando llegue, y mientras tanto sumás el 5 % de su valor en puntos por semana de "
    "espera, hasta el 25 %.",
    "Preparamos lo disponible para que lo retires y este artículo queda a tu nombre en el "
    "local cuando llegue.",
)
CANCELAR = Opcion(
    LineaPedido.CANCELAR,
    "Cancelar el artículo",
    "Te devolvemos el 100 % de su valor en puntos. El resto del pedido sigue su curso.",
    "Cancelás el artículo y recibís su valor en puntos. No se puede deshacer.",
)
OPCIONES = {opcion.clave: opcion for opcion in (PAUSAR, DIFERIR, CANCELAR)}


def ventana_vigente(linea, ahora=None):
    ahora = ahora or timezone.now()
    return (
        not linea.ventana_cerrada
        and linea.decision_vence_en is not None
        and ahora < linea.decision_vence_en
    )


def puede_decidir(linea):
    return (
        linea.estado == LineaPedido.ESPERANDO_DEMORADO
        and not linea.decision_demora
        and ventana_vigente(linea)
    )


def opciones_de(linea):
    """Qué opciones tiene sentido ofrecer según cómo está el pedido (B-08-009).

    Pausar, mientras el pedido siga esperando entero. Recibir lo disponible,
    si hay algo para despachar y nada más esperando una pre-venta. Cancelar,
    siempre.
    """
    pedido = linea.pedido
    estados = set(
        pedido.lineas.exclude(pk=linea.pk)
        .exclude(estado=LineaPedido.CANCELADO_REEMBOLSO)
        .values_list("estado", flat=True)
    )
    ofrecidas = []
    if pedido.estado == Pedido.ESPERANDO_DEMORADO:
        ofrecidas.append(PAUSAR)
    hay_para_despachar = bool(estados & {LineaPedido.DISPONIBLE, LineaPedido.EMPAQUETADO})
    if hay_para_despachar and LineaPedido.RESERVADO not in estados:
        ofrecidas.append(DIFERIR_RETIRO if pedido.retiro else DIFERIR)
    ofrecidas.append(CANCELAR)
    return ofrecidas


def _rechazo(linea):
    if linea.estado != LineaPedido.ESPERANDO_DEMORADO:
        return "Este artículo ya no está demorado."
    if linea.decision_demora:
        return "Ya elegiste qué hacer con este artículo."
    return "Venció el plazo para elegir. Te vamos a contactar para resolverlo."


# ---------------------------------------------------------------------------
# CO-184 consultarOpcionesAnteDemora · CO-094 seleccionarOpcionAnteDemora
# ---------------------------------------------------------------------------


@dataclass
class Situacion:
    linea: LineaPedido
    opciones: list
    fecha_estimada: object
    reembolso: int


def consultar_opciones(linea):
    """`CO-184`. Con la ventana vencida (E1) no hay opciones que mostrar."""
    if not puede_decidir(linea):
        raise DecisionRechazada(_rechazo(linea))
    producto = linea.producto.especifico
    equivalencia = ConfiguracionSistema.obtener().equivalencia_puntos
    return Situacion(
        linea=linea,
        opciones=opciones_de(linea),
        fecha_estimada=getattr(producto, "fecha_estimada", None),
        reembolso=puntos_de_reembolso(linea, equivalencia),
    )


def seleccionar_opcion(linea, clave):
    """`CO-094`: la opción con su consecuencia en una oración. No registra nada."""
    situacion = consultar_opciones(linea)
    for opcion in situacion.opciones:
        if opcion.clave == clave:
            return opcion
    raise DecisionRechazada("Esa opción no está disponible para este artículo.")


# ---------------------------------------------------------------------------
# CO-095 confirmarOpcionAnteDemora · CO-098 confirmarCancelacionDeArticuloDemorado
# ---------------------------------------------------------------------------


@dataclass
class Confirmacion:
    pedido: Pedido
    linea: LineaPedido
    opcion: Opcion
    puntos: int = 0
    saldo: int = 0


def confirmar_opcion(pedido, linea_pk, usuario, clave):
    """`CO-095`, y `CO-098` cuando la opción es cancelar.

    El pedido y la línea se toman con bloqueo: dos pestañas que confirman a la
    vez registran una sola decisión.
    """
    with transaction.atomic():
        pedido = Pedido.objects.select_for_update().get(pk=pedido.pk, usuario=usuario)
        linea = pedido.lineas.select_for_update().select_related("producto").get(pk=linea_pk)
        linea.pedido = pedido
        if not puede_decidir(linea):
            raise DecisionRechazada(_rechazo(linea))
        opcion = next((o for o in opciones_de(linea) if o.clave == clave), None)
        if opcion is None:
            raise DecisionRechazada("Esa opción no está disponible para este artículo.")
        if opcion is CANCELAR:
            return _cancelar(pedido, linea, usuario)

        momento = timezone.now()
        linea.decision_demora = opcion.clave
        linea.save(update_fields=["decision_demora"])
        if opcion is DIFERIR_RETIRO and pedido.estado == Pedido.ESPERANDO_DEMORADO:
            # Lo disponible se arma para retirar (D2): el pedido vuelve a la fila
            # del armado, y la línea diferida entra al stock en local al llegar.
            anterior = pedido.estado
            pedido.estado = Pedido.PENDIENTE_ARMADO
            pedido.save(update_fields=["estado"])
            registrar_transicion(pedido, anterior, usuario, momento)
        elif opcion is DIFERIR and pedido.estado == Pedido.ESPERANDO_DEMORADO:
            # B-08-007: lo disponible se empaqueta y el pedido pasa con ello.
            pedido.lineas.filter(estado=LineaPedido.DISPONIBLE).update(
                estado=LineaPedido.EMPAQUETADO
            )
            anterior = pedido.estado
            pedido.estado = Pedido.EMPAQUETADO
            pedido.save(update_fields=["estado"])
            registrar_transicion(pedido, anterior, usuario, momento)
        RegistroAuditoria.registrar(
            accion=RegistroAuditoria.DECISION_DEMORA,
            actor=usuario,
            objetivo=pedido,
            detalle=f"Pedido {pedido.numero}, {nombre(linea.producto)}: {opcion.titulo.lower()}.",
        )
        despues_del_commit(_avisar_decision, pedido, linea, opcion)
    return Confirmacion(pedido=pedido, linea=linea, opcion=opcion)


def _cancelar(pedido, linea, usuario):
    """`CO-098`, dentro de la transacción de `confirmar_opcion` (E1: todo o nada).

    El stock no se toca: la pre-venta nunca llegó (B-08-005).
    """
    momento = timezone.now()
    equivalencia = ConfiguracionSistema.obtener().equivalencia_puntos
    reembolso = puntos_de_reembolso(linea, equivalencia)
    linea.estado = LineaPedido.CANCELADO_REEMBOLSO
    linea.decision_demora = LineaPedido.CANCELAR
    linea.compensacion_cerrada = True
    linea.save(update_fields=["estado", "decision_demora", "compensacion_cerrada"])
    ubicar_pedido(pedido, usuario, momento)
    envio = puntos_de_envio(pedido, equivalencia) if pedido.estado == Pedido.CANCELADO else 0
    puntos.acreditar(
        usuario,
        reembolso + envio,
        origen=LotePuntos.REEMBOLSO,
        pedido=pedido,
        linea=linea,
        motivo=f"Cancelación de {nombre(linea.producto)} demorado",
    )
    descontados = puntos.descontar_ganados(usuario, linea, linea.cantidad)  # plan 00, C2
    RegistroAuditoria.registrar(
        accion=RegistroAuditoria.CANCELACION_ARTICULO_DEMORADO,
        actor=usuario,
        objetivo=pedido,
        detalle=(
            f"Pedido {pedido.numero}: canceló {nombre(linea.producto)}, reembolso de "
            f"{reembolso} pts"
            + (f" y {envio} pts del envío" if envio else "")
            + (f"; se descontaron {descontados} pts ganados con la compra" if descontados else "")
            + "."
        ),
    )
    confirmacion = Confirmacion(
        pedido=pedido,
        linea=linea,
        opcion=CANCELAR,
        puntos=reembolso + envio,
        saldo=puntos.saldo(usuario),
    )
    despues_del_commit(_avisar_cancelacion, confirmacion)
    return confirmacion


def avisar_fallo_de_cancelacion(pedido, linea):
    """`CO-098` E1: el Administrador se entera con el pedido y el artículo."""
    avisos.avisar_administradores(
        tipo="pedidos",
        asunto=f"Pedido {pedido.numero}: falló una cancelación",
        rotulo="Pedido",
        antetitulo="Demora",
        titulo="Cancelación sin completar",
        parrafos=[
            "El Cliente intentó cancelar un artículo demorado y la operación falló. "
            "No quedó ningún cambio.",
        ],
        filas=[("Pedido", pedido.numero), ("Artículo", nombre(linea.producto))],
    )


def _avisar_decision(pedido, linea, opcion):
    """`CU-PED-OPC` paso 7."""
    avisos.avisar(
        [pedido.correo_de_contacto],
        asunto=f"Tu pedido {pedido.numero}: {opcion.titulo.lower()}",
        antetitulo=f"Pedido {pedido.numero}",
        titulo=opcion.titulo,
        parrafos=[opcion.consecuencia],
        filas=[("Artículo", nombre(linea.producto))],
    )


def _avisar_cancelacion(confirmacion):
    """`CU-PED-CAN` paso 4."""
    pedido = confirmacion.pedido
    parrafos = [f"Cancelaste {nombre(confirmacion.linea.producto)} y te devolvimos su valor."]
    if pedido.estado == Pedido.CANCELADO:
        parrafos.append("El pedido quedó cancelado: no tenía otros artículos.")
    avisos.avisar(
        [pedido.correo_de_contacto],
        asunto=f"Tu pedido {pedido.numero}: artículo cancelado",
        antetitulo=f"Pedido {pedido.numero}",
        titulo="Artículo cancelado",
        parrafos=parrafos,
        filas=[
            ("Reembolso", f"{confirmacion.puntos} pts"),
            ("Saldo actual", f"{confirmacion.saldo} pts"),
        ],
    )


# ---------------------------------------------------------------------------
# CO-096 ejecutarCicloDeVencimientoDeVentanaDeDecision
# ---------------------------------------------------------------------------


def ciclo_de_ventanas(ahora=None):
    """`CO-096`: cierra las ventanas vencidas sin decisión y avisa al Administrador.

    Mira la decisión y no el estado (DME-08). El pedido no cambia.
    """
    ahora = ahora or timezone.now()
    vencidas = LineaPedido.objects.filter(
        estado=LineaPedido.ESPERANDO_DEMORADO,
        decision_demora="",
        ventana_cerrada=False,
        decision_vence_en__lte=ahora,
    ).values_list("pk", flat=True)
    cerradas = []
    for pk in list(vencidas):
        with transaction.atomic():
            linea = (
                LineaPedido.objects.select_for_update(of=("self",))
                .select_related("pedido", "producto")
                .get(pk=pk)
            )
            if linea.ventana_cerrada or linea.decision_demora:
                continue
            linea.ventana_cerrada = True
            linea.save(update_fields=["ventana_cerrada"])
            RegistroAuditoria.registrar(
                accion=RegistroAuditoria.VENCIMIENTO_VENTANA,
                objetivo=linea.pedido,
                detalle=(
                    f"Pedido {linea.pedido.numero}, {nombre(linea.producto)}: venció la "
                    "ventana de decisión sin respuesta del Cliente."
                ),
            )
            cerradas.append(linea)
    if cerradas:
        avisos.avisar_administradores(
            tipo="pedidos",
            asunto="Demoras sin respuesta del Cliente",
            rotulo="Pedido",
            antetitulo="Demora",
            titulo="Ventanas vencidas",
            parrafos=[
                "Venció el plazo para elegir y estos clientes no respondieron. "
                "Los pedidos siguen esperando el artículo.",
            ],
            filas=[(f"Pedido {linea.pedido.numero}", nombre(linea.producto)) for linea in cerradas],
        )
    return cerradas


# ---------------------------------------------------------------------------
# CO-097 ejecutarCicloDeCompensacionPorRetraso
# ---------------------------------------------------------------------------


@dataclass
class Compensacion:
    linea: LineaPedido
    semanas: int
    puntos: int
    porcentaje: Decimal


def ciclo_de_compensacion(hoy=None):
    """`CO-097`, por semanas cumplidas contra lo ya acreditado (B-08-010).

    Correrlo todos los días, o dos veces el mismo día, nunca acredita de más.
    Lo que se acumula es en pesos; lo que se acredita, en puntos hacia arriba.
    """
    hoy = hoy or timezone.localdate()
    activas = LineaPedido.objects.filter(
        estado=LineaPedido.ESPERANDO_DEMORADO,
        decision_demora=LineaPedido.DESPACHO_DIFERIDO,
        compensacion_cerrada=False,
        fecha_llegada_original__isnull=False,
    ).values_list("pk", flat=True)
    acreditadas = []
    for pk in list(activas):
        with transaction.atomic():
            linea = (
                LineaPedido.objects.select_for_update(of=("self",))
                .select_related("pedido", "pedido__usuario", "producto")
                .get(pk=pk)
            )
            resultado = _compensar(linea, hoy)
            if resultado is not None:
                acreditadas.append(resultado)
                despues_del_commit(_avisar_compensacion, resultado)
    return acreditadas


def _compensar(linea, hoy):
    if linea.compensacion_cerrada or linea.estado != LineaPedido.ESPERANDO_DEMORADO:
        return None  # E1
    valor = linea.valor
    tope = (valor * TOPE).quantize(CENTAVO)
    pedido = linea.pedido
    if linea.compensacion_acumulada >= tope:
        # E2: ya llegó al tope y seguía abierta.
        linea.compensacion_cerrada = True
        linea.save(update_fields=["compensacion_cerrada"])
        RegistroAuditoria.registrar(
            accion=RegistroAuditoria.COMPENSACION_RETRASO,
            objetivo=pedido,
            detalle=(
                f"Pedido {pedido.numero}, {nombre(linea.producto)}: la compensación ya estaba "
                "en el 25 %; se cerró sin acreditar."
            ),
        )
        return None
    semanas = (hoy - linea.fecha_llegada_original).days // 7
    objetivo = min((valor * TASA_SEMANAL * semanas).quantize(CENTAVO), tope)
    importe = objetivo - linea.compensacion_acumulada
    if importe <= 0:
        return None
    cantidad = puntos.puntos_para_cubrir(importe)
    puntos.acreditar(
        pedido.usuario,
        cantidad,
        origen=LotePuntos.COMPENSACION,
        pedido=pedido,
        linea=linea,
        motivo=f"Compensación por la demora de {nombre(linea.producto)}",
    )
    linea.compensacion_acumulada = objetivo
    linea.compensacion_cerrada = objetivo >= tope
    linea.save(update_fields=["compensacion_acumulada", "compensacion_cerrada"])
    porcentaje = (objetivo / valor * 100).quantize(Decimal("1"))
    RegistroAuditoria.registrar(
        accion=RegistroAuditoria.COMPENSACION_RETRASO,
        objetivo=pedido,
        objetivo_email=pedido.correo_de_contacto,
        detalle=(
            f"Pedido {pedido.numero}, {nombre(linea.producto)}: {cantidad} pts, "
            f"{porcentaje} % acumulado."
        ),
    )
    return Compensacion(linea=linea, semanas=semanas, puntos=cantidad, porcentaje=porcentaje)


def _avisar_compensacion(compensacion):
    """`CU-PED-CMP` paso 5."""
    linea = compensacion.linea
    avisos.avisar(
        [linea.pedido.correo_de_contacto],
        asunto=f"Sumaste {compensacion.puntos} puntos por la demora",
        antetitulo=f"Pedido {linea.pedido.numero}",
        titulo="Compensación por demora",
        parrafos=[f"{nombre(linea.producto)} sigue demorado. Te acreditamos puntos por la espera."],
        filas=[
            ("Semanas de espera", compensacion.semanas),
            ("Esta semana", f"{compensacion.puntos} pts"),
            ("Acumulado", f"{compensacion.porcentaje} % del valor"),
            ("Llegada prevista", fecha(linea.fecha_llegada_original)),
        ],
    )
