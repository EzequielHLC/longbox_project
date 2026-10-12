"""El cierre de caja (`CU-CAJ-CIE`): `CO-203`, `CO-126` y `CO-127`.

Entra en un cierre toda transacción aprobada que todavía no esté en uno, aunque
sea de un día anterior sin cerrar (B-14-002). Las pendientes de verificación se
listan aparte y quedan para el próximo cierre (A1). Las compras pagadas sólo con
puntos no tienen transacción: se informan como cantidad.
"""

import csv
from dataclasses import dataclass, field
from decimal import Decimal

from django.db import IntegrityError, transaction
from django.utils import timezone

from apps.caja.models import CierreDeCaja
from apps.core.models import RegistroAuditoria
from apps.pedidos.models import Pedido, TransaccionPago

CERO = Decimal("0")

MEDIO_A_CAMPO = {
    TransaccionPago.EFECTIVO: "total_efectivo",
    TransaccionPago.TRANSFERENCIA: "total_transferencia",
    TransaccionPago.TARJETA: "total_tarjeta",
    TransaccionPago.PASARELA: "total_pasarela",
}


class CierreRechazado(ValueError):
    """E1 o E2: no se genera cierre. El mensaje es el que lee el usuario."""


def _sin_cierre():
    return TransaccionPago.objects.filter(incluida_en_cierre=False).select_related("pedido")


@dataclass
class Resumen:
    """`CO-203`: lo que se consolidaría si se cerrara ahora."""

    incluidas: list = field(default_factory=list)
    pendientes: list = field(default_factory=list)
    solo_puntos: int = 0
    cierre_de_hoy: CierreDeCaja | None = None

    def _suma(self, condicion):
        return sum((t.monto for t in self.incluidas if condicion(t)), CERO)

    @property
    def total_presencial(self):
        return self._suma(lambda t: t.pedido.canal == Pedido.PRESENCIAL)

    @property
    def total_online(self):
        return self._suma(lambda t: t.pedido.canal == Pedido.ONLINE)

    @property
    def por_canal(self):
        return [("Físico", self.total_presencial), ("Online", self.total_online)]

    @property
    def por_medio(self):
        return [
            (etiqueta, self._suma(lambda t, m=medio: t.medio == m))
            for medio, etiqueta in TransaccionPago.MEDIO_CHOICES
        ]

    @property
    def total_global(self):
        return self._suma(lambda t: True)

    @property
    def de_dias_anteriores(self):
        hoy = timezone.localdate()
        return sum(1 for t in self.incluidas if timezone.localdate(t.registrada_en) < hoy)


def resumen_previo():
    """`CO-203`. Sólo lee. Con E1, trae el cierre de hoy; las ventas posteriores esperan."""
    transacciones = list(_sin_cierre().order_by("registrada_en", "pk"))
    ultimo = CierreDeCaja.objects.order_by("-realizado_en").first()
    solo_puntos = Pedido.objects.filter(transaccion__isnull=True)
    if ultimo:
        solo_puntos = solo_puntos.filter(fecha__gt=ultimo.realizado_en)
    return Resumen(
        incluidas=[t for t in transacciones if t.estado == TransaccionPago.APROBADO],
        pendientes=[t for t in transacciones if t.estado == TransaccionPago.PENDIENTE_VERIFICACION],
        solo_puntos=solo_puntos.count(),
        cierre_de_hoy=CierreDeCaja.objects.filter(fecha_jornada=timezone.localdate()).first(),
    )


def confirmar(actor):
    """`CO-126`. Las transacciones se toman con bloqueo: una venta que se confirma mientras
    tanto queda para el cierre siguiente, nunca en dos ni en ninguno."""
    hoy = timezone.localdate()
    if CierreDeCaja.objects.filter(fecha_jornada=hoy).exists():
        raise CierreRechazado(
            "La caja de hoy ya está cerrada. Lo cobrado después va al próximo cierre."
        )
    try:
        with transaction.atomic():
            transacciones = list(_sin_cierre().select_for_update(of=("self",)).order_by("pk"))
            incluidas = [t for t in transacciones if t.estado == TransaccionPago.APROBADO]
            excluidas = [
                t for t in transacciones if t.estado == TransaccionPago.PENDIENTE_VERIFICACION
            ]
            if not incluidas:
                raise CierreRechazado("No hay movimientos para consolidar.")
            totales = {campo: CERO for campo in MEDIO_A_CAMPO.values()}
            presencial = online = CERO
            for t in incluidas:
                totales[MEDIO_A_CAMPO[t.medio]] += t.monto
                if t.pedido.canal == Pedido.PRESENCIAL:
                    presencial += t.monto
                else:
                    online += t.monto
            cierre = CierreDeCaja.objects.create(
                fecha_jornada=hoy,
                total_presencial=presencial,
                total_online=online,
                total_global=presencial + online,
                transacciones_incluidas=len(incluidas),
                transacciones_excluidas=len(excluidas),
                realizado_por=actor,
                **totales,
            )
            TransaccionPago.objects.filter(pk__in=[t.pk for t in incluidas]).update(
                incluida_en_cierre=True, cierre=cierre
            )
            RegistroAuditoria.registrar(
                accion=RegistroAuditoria.CIERRE_CAJA,
                actor=actor,
                objetivo=cierre,
                detalle=(
                    f"Cierre del {hoy:%d/%m/%Y}: {len(incluidas)} transacción(es), total "
                    f"{cierre.total_global} (físico {presencial}, online {online}); "
                    f"{len(excluidas)} excluida(s) por verificar."
                ),
            )
    except IntegrityError as error:
        # Otro usuario cerró la caja de hoy en el mismo instante (I-23).
        raise CierreRechazado("La caja de hoy ya está cerrada.") from error
    return cierre


def exportar(cierre, salida, actor):
    """`CO-127`: cada transacción del cierre y los totales, en CSV. Queda auditado."""
    escritor = csv.writer(salida)
    escritor.writerow(["Fecha", "Pedido", "Canal", "Medio de pago", "Monto"])
    for t in cierre.transacciones.select_related("pedido").order_by("registrada_en", "pk"):
        escritor.writerow(
            [
                timezone.localtime(t.registrada_en).strftime("%d/%m/%Y %H:%M"),
                t.pedido.numero,
                t.pedido.get_canal_display(),
                t.get_medio_display(),
                t.monto,
            ]
        )
    escritor.writerow([])
    for etiqueta, total in [*cierre.por_canal, *cierre.por_medio, ("Total", cierre.total_global)]:
        escritor.writerow([etiqueta, "", "", "", total])
    RegistroAuditoria.registrar(
        accion=RegistroAuditoria.EXPORTACION_CIERRE,
        actor=actor,
        objetivo=cierre,
        detalle=f"Cierre del {cierre.fecha_jornada:%d/%m/%Y}.",
    )
