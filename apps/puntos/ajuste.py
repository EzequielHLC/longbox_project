"""`CU-PTS-ADM`: el Administrador corrige el saldo de un Cliente (plan 10, segunda parte).

`CO-191` presenta los puntos del Cliente; `CO-106` registra el ajuste. No es el
mecanismo ordinario de acreditación ni de débito: es para casos de soporte, con
motivo obligatorio y la traza completa en la auditoría.

El débito no toca lo comprometido en un canje en curso (ambigüedad 1): rompería
una compra que el Cliente está pagando.
"""

from dataclasses import dataclass
from functools import partial

from django.conf import settings
from django.db import transaction
from django.urls import reverse

from apps.accounts.models import Usuario
from apps.core.models import ConfiguracionSistema, RegistroAuditoria
from apps.pedidos import avisos
from apps.puntos import servicios
from apps.puntos.caducidad import usable_hasta
from apps.puntos.models import LotePuntos, MovimientoPuntos

MOVIMIENTOS_RECIENTES = 20
LARGO_MOTIVO = 300


class AjusteRechazado(ValueError):
    """El ajuste no se registra. `maximo` lo trae E1, para que se corrija."""

    def __init__(self, mensaje, *, maximo=None):
        super().__init__(mensaje)
        self.maximo = maximo


def _cliente_activo(cliente):
    if cliente.rol != Usuario.CLIENTE or cliente.estado != Usuario.ACTIVO:
        raise AjusteRechazado("Sólo se ajustan los puntos de una cuenta de cliente activa.")


# ---------------------------------------------------------------------------
# CO-191 consultarPuntosDeCliente
# ---------------------------------------------------------------------------


@dataclass
class Panel:
    cliente: Usuario
    saldo: int
    saldo_en_pesos: object
    comprometido: int
    debitable: int
    lotes: list
    movimientos: list


def consultar(cliente):
    """El saldo, los lotes, lo comprometido y los movimientos recientes. Sólo lee."""
    _cliente_activo(cliente)
    equivalencia = ConfiguracionSistema.obtener().equivalencia_puntos
    lotes = list(
        LotePuntos.objects.filter(usuario=cliente, estado=LotePuntos.ACTIVO).order_by(
            "caduca_el", "pk"
        )
    )
    comprometido = servicios.comprometidos(cliente)
    reparto = servicios.reparto_comprometido(lotes, comprometido)
    for lote in lotes:
        lote.comprometido = reparto.get(lote.pk, 0)
        lote.hasta = usable_hasta(lote)
    saldo = sum(lote.disponible for lote in lotes)
    return Panel(
        cliente=cliente,
        saldo=saldo,
        saldo_en_pesos=saldo * equivalencia,
        comprometido=min(comprometido, saldo),
        debitable=max(saldo - comprometido, 0),
        lotes=lotes,
        movimientos=list(
            MovimientoPuntos.objects.filter(usuario=cliente)
            .select_related("pedido")
            .order_by("-ocurrido_en", "-pk")[:MOVIMIENTOS_RECIENTES]
        ),
    )


# ---------------------------------------------------------------------------
# CO-106 registrarAjusteManualDePuntos
# ---------------------------------------------------------------------------


@dataclass
class Ajuste:
    tipo: str
    cantidad: int
    anterior: int
    saldo: int


def ajustar(cliente, actor, tipo, cantidad, motivo):
    motivo = (motivo or "").strip()
    _cliente_activo(cliente)
    if tipo not in dict(MovimientoPuntos.TIPO_CHOICES):
        raise AjusteRechazado("Elegí si el ajuste acredita o debita.")
    if not isinstance(cantidad, int) or cantidad <= 0:
        raise AjusteRechazado("La cantidad tiene que ser un número entero mayor que cero.")
    if not motivo:
        raise AjusteRechazado("El motivo es obligatorio.")  # E2
    if len(motivo) > LARGO_MOTIVO:
        raise AjusteRechazado(f"El motivo admite hasta {LARGO_MOTIVO} caracteres.")

    with transaction.atomic():
        # Los lotes se bloquean antes de leer el saldo: el que se audita es el
        # mismo sobre el que se ajusta.
        servicios._activos_bloqueados(cliente)
        anterior = servicios.saldo(cliente)
        if tipo == MovimientoPuntos.ACREDITACION:
            movimiento = servicios.acreditar(
                cliente, cantidad, origen=LotePuntos.AJUSTE_MANUAL, motivo=motivo
            )
        else:
            try:
                movimiento = servicios.debitar_no_comprometidos(cliente, cantidad, motivo=motivo)
            except servicios.SaldoInsuficiente as error:  # E1
                maximo = servicios.debitable(cliente)
                raise AjusteRechazado(
                    f"El máximo que se puede debitar es {maximo} puntos.", maximo=maximo
                ) from error
        hecho = Ajuste(
            tipo=tipo, cantidad=cantidad, anterior=anterior, saldo=movimiento.saldo_resultante
        )
        etiqueta = dict(MovimientoPuntos.TIPO_CHOICES)[tipo]
        RegistroAuditoria.registrar(
            accion=RegistroAuditoria.AJUSTE_PUNTOS,
            actor=actor,
            objetivo=cliente,
            detalle=(
                f"{etiqueta} de {cantidad} pts. Saldo: {anterior} → {hecho.saldo}. "
                f"Motivo: {motivo}"
            ),
        )
        transaction.on_commit(partial(_avisar, cliente, hecho, etiqueta))
    return hecho


def _avisar(cliente, hecho, etiqueta):
    enlace = settings.URL_PUBLICA + reverse("cuenta:puntos") if settings.URL_PUBLICA else ""
    avisos.avisar(
        [cliente.email],
        asunto="Ajustamos tus puntos",
        rotulo="Puntos",
        antetitulo="Tus puntos",
        titulo="Ajuste de puntos",
        parrafos=["Hicimos un ajuste en tu saldo de puntos."],
        filas=[
            (etiqueta, f"{hecho.cantidad} pts"),
            ("Tu saldo", f"{hecho.saldo} pts"),
        ],
        enlace=enlace,
        texto_enlace="Ver mis puntos",
    )
