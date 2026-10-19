"""`CO-105 ejecutarCicloDeCaducidadDePuntos` y el aviso previo (plan 10, segunda parte).

Lo corre el Temporizador una vez por día. Primero vence: un lote Activo con
puntos cuya fecha de caducidad llegó (`<=` hoy, ambigüedad 3) pasa a Vencido, en
su propia transacción. Después avisa: los lotes que vencen dentro de los días
configurados reciben un aviso, una sola vez, «animando a la compra» (decisión
del responsable sobre la ambigüedad 5).

**Los lotes comprometidos en un canje no vencen** (E2): un pago pendiente los
va a debitar. Se difieren al ciclo siguiente.

Correrlo dos veces no repite nada: un lote vencido deja de ser Activo, y uno
avisado queda marcado.
"""

import logging
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import timedelta

from django.conf import settings
from django.db import transaction
from django.urls import reverse
from django.utils import timezone

from apps.core.models import ConfiguracionSistema, RegistroAuditoria
from apps.pedidos import avisos
from apps.puntos import servicios
from apps.puntos.models import LotePuntos, MovimientoPuntos

logger = logging.getLogger(__name__)

MOTIVO = "Caducidad"


@dataclass
class ResumenCaducidad:
    vencidos: list = field(default_factory=list)
    diferidos: list = field(default_factory=list)
    incidentes: list = field(default_factory=list)
    avisados: list = field(default_factory=list)


def _fecha(dia):
    return dia.strftime("%d/%m/%Y")


def usable_hasta(lote):
    """El último día en que se pueden canjear: el anterior al de caducidad."""
    return lote.caduca_el - timedelta(days=1)


def _enlace(nombre_url):
    return settings.URL_PUBLICA + reverse(nombre_url) if settings.URL_PUBLICA else ""


def ciclo(hoy=None):
    hoy = hoy or timezone.localdate()
    resumen = ResumenCaducidad()
    _vencer(hoy, resumen)
    _avisar_proximos(hoy, resumen)
    return resumen


# ---------------------------------------------------------------------------
# La caducidad
# ---------------------------------------------------------------------------


def _vencer(hoy, resumen):
    por_cliente = defaultdict(list)
    for lote in LotePuntos.objects.filter(
        estado=LotePuntos.ACTIVO, disponible__gt=0, caduca_el__lte=hoy
    ).order_by("usuario_id", "caduca_el", "pk"):
        por_cliente[lote.usuario_id].append(lote.pk)

    for ids in por_cliente.values():
        vencidos = []
        for lote_pk in ids:
            try:
                hecho = _vencer_lote(lote_pk, hoy)
            except Exception as error:  # noqa: BLE001 - E1: un lote que falla no frena el ciclo
                logger.exception("Falló la caducidad del lote de puntos %s.", lote_pk)
                _registrar_incidente(lote_pk, error)
                resumen.incidentes.append(lote_pk)
                continue
            if hecho is None:
                resumen.diferidos.append(lote_pk)
            elif hecho:
                vencidos.append(hecho)
        if vencidos:
            resumen.vencidos.extend(vencidos)
            _avisar_caducidad(vencidos)


@dataclass
class Vencido:
    lote: LotePuntos
    cantidad: int
    saldo: int


def _vencer_lote(lote_pk, hoy):
    """Las postcondiciones de `CO-105` sobre un lote, en su propia transacción.

    Devuelve el vencimiento, `None` si quedó diferido por un canje (E2), o
    `False` si ya no hay nada que vencer.
    """
    with transaction.atomic():
        lote = LotePuntos.objects.select_related("usuario").get(pk=lote_pk)
        usuario = lote.usuario
        # Todos los Activos del Cliente, en el orden del débito del canje: lo
        # comprometido se calcula sobre lo que está bloqueado.
        lotes = servicios._activos_bloqueados(usuario)
        lote = next((candidato for candidato in lotes if candidato.pk == lote_pk), None)
        if lote is None or lote.disponible == 0 or lote.caduca_el > hoy:
            return False
        reparto = servicios.reparto_comprometido(lotes, servicios.comprometidos(usuario))
        if reparto.get(lote.pk):
            return None  # E2

        cantidad = lote.disponible
        lote.disponible = 0
        lote.estado = LotePuntos.VENCIDO
        lote.save(update_fields=["disponible", "estado"])
        movimiento = MovimientoPuntos.objects.create(
            usuario=usuario,
            tipo=MovimientoPuntos.DEBITO,
            cantidad=cantidad,
            saldo_resultante=servicios.saldo(usuario),
            motivo=MOTIVO,
        )
        movimiento.lotes.add(lote)
        RegistroAuditoria.registrar(
            accion=RegistroAuditoria.CADUCIDAD_PUNTOS,
            objetivo=lote,
            objetivo_email=usuario.email,
            detalle=(
                f"{usuario.email}: vencieron {cantidad} pts del lote que caducaba el "
                f"{_fecha(lote.caduca_el)}."
            ),
        )
        lote.usuario = usuario
        return Vencido(lote=lote, cantidad=cantidad, saldo=movimiento.saldo_resultante)


def _registrar_incidente(lote_pk, error):
    lote = LotePuntos.objects.select_related("usuario").filter(pk=lote_pk).first()
    RegistroAuditoria.registrar(
        accion=RegistroAuditoria.INCIDENTE_CADUCIDAD,
        objetivo=lote,
        objetivo_email=lote.usuario.email if lote else "",
        detalle=(
            f"Lote {lote_pk}: no se pudo vencer ({type(error).__name__}: {error}). "
            "Queda como estaba y se reintenta en el próximo ciclo."
        ),
    )


def _avisar_caducidad(vencidos):
    usuario = vencidos[0].lote.usuario
    total = sum(v.cantidad for v in vencidos)
    avisos.avisar(
        [usuario.email],
        asunto=f"Vencieron {total} puntos",
        rotulo="Puntos",
        antetitulo="Tus puntos",
        titulo="Vencieron puntos",
        parrafos=[
            f"Vencieron {total} puntos que no llegaste a usar. Los puntos vencidos no se "
            "recuperan.",
        ],
        filas=[
            *((f"Vencían el {_fecha(v.lote.caduca_el)}", f"{v.cantidad} pts") for v in vencidos),
            ("Tu saldo", f"{vencidos[-1].saldo} pts"),
        ],
        enlace=_enlace("cuenta:puntos"),
        texto_enlace="Ver mis puntos",
    )


# ---------------------------------------------------------------------------
# El aviso previo (decisión del responsable)
# ---------------------------------------------------------------------------


def _avisar_proximos(hoy, resumen):
    dias = ConfiguracionSistema.obtener().dias_aviso_caducidad_puntos
    por_cliente = defaultdict(list)
    for lote in (
        LotePuntos.objects.filter(
            estado=LotePuntos.ACTIVO,
            disponible__gt=0,
            aviso_caducidad=False,
            caduca_el__gt=hoy,
            caduca_el__lte=hoy + timedelta(days=dias),
        )
        .select_related("usuario")
        .order_by("usuario_id", "caduca_el", "pk")
    ):
        por_cliente[lote.usuario_id].append(lote)

    for lotes in por_cliente.values():
        marcados = LotePuntos.objects.filter(
            pk__in=[lote.pk for lote in lotes], aviso_caducidad=False
        ).update(aviso_caducidad=True)
        if not marcados:
            continue  # otra corrida lo avisó entre la consulta y la marca
        _avisar_proximo(lotes)
        resumen.avisados.extend(lotes)


def _avisar_proximo(lotes):
    usuario = lotes[0].usuario
    total = sum(lote.disponible for lote in lotes)
    hasta = usable_hasta(lotes[0])
    avisos.avisar(
        [usuario.email],
        asunto=f"Tenés {total} puntos por vencer",
        rotulo="Puntos",
        antetitulo="Tus puntos",
        titulo="Usalos antes de que venzan",
        parrafos=[
            f"Tenés {total} puntos que vencen pronto. Podés usarlos hasta el {_fecha(hasta)} "
            "para llevarte un tomo sin pagarlo en dinero.",
        ],
        filas=[
            (f"Hasta el {_fecha(usable_hasta(lote))}", f"{lote.disponible} pts") for lote in lotes
        ],
        enlace=_enlace("core:tienda"),
        texto_enlace="Ir a la tienda",
    )
