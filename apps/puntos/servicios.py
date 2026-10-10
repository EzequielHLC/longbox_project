"""Saldo, acreditación y débito de puntos (RF-19, RF-20; B-07-033).

Lo que la compra necesita del módulo 10. La consulta del Cliente, la caducidad
y el ajuste manual llegan con ese módulo.

**Los puntos son enteros y el dinero es `Decimal`.** La conversión redondea
siempre contra el error: lo que se acredita, hacia abajo; lo que pide un canje,
hacia arriba (B-07-033).
"""

import calendar
from datetime import date
from decimal import ROUND_CEILING, ROUND_FLOOR, Decimal

from django.db.models import Sum
from django.utils import timezone

from apps.core.models import ConfiguracionSistema
from apps.puntos.models import LotePuntos, MovimientoPuntos


class SaldoInsuficiente(ValueError):
    """El saldo no alcanza para debitar lo pedido."""


def saldo(usuario):
    """I-18: la suma de `disponible` de los lotes Activos."""
    if not getattr(usuario, "is_authenticated", False):
        return 0
    total = LotePuntos.objects.filter(usuario=usuario, estado=LotePuntos.ACTIVO).aggregate(
        total=Sum("disponible")
    )["total"]
    return total or 0


def puntos_por_monto(monto, *, porcentaje=None, valor=None):
    """Puntos que acredita un monto pagado en dinero (B-10-004), hacia abajo.

    El porcentaje es el reintegro en pesos; se convierte a puntos con el valor
    del punto. Con 5 % y 1 punto = $10, una compra de $10.000 suma 50 puntos.
    """
    if porcentaje is None or valor is None:
        configuracion = ConfiguracionSistema.obtener()
        porcentaje = configuracion.porcentaje_puntos if porcentaje is None else porcentaje
        valor = configuracion.equivalencia_puntos if valor is None else valor
    reintegro = Decimal(monto) * porcentaje / 100
    return int((reintegro / valor).to_integral_value(rounding=ROUND_FLOOR))


def puntos_para_cubrir(importe, equivalencia=None):
    """Cuántos puntos cuesta cubrir un importe con el canje: hacia arriba."""
    equivalencia = equivalencia or ConfiguracionSistema.obtener().equivalencia_puntos
    return int((Decimal(importe) / equivalencia).to_integral_value(rounding=ROUND_CEILING))


def _sumar_meses(dia, meses):
    """El mismo día, `meses` después; el 31 de un mes corto cae en su último día."""
    anio, mes = divmod(dia.month - 1 + meses, 12)
    anio, mes = dia.year + anio, mes + 1
    return date(anio, mes, min(dia.day, calendar.monthrange(anio, mes)[1]))


def acreditar(usuario, cantidad, *, origen, pedido=None, motivo=""):
    """Un lote nuevo con la caducidad estándar y su movimiento de Acreditación.

    Se llama dentro de la transacción de quien acredita (`CO-089`): si la
    compra se deshace, el lote se deshace con ella.
    """
    if cantidad <= 0:
        return None
    ahora = timezone.now()
    meses = ConfiguracionSistema.obtener().caducidad_puntos_meses
    lote = LotePuntos.objects.create(
        usuario=usuario,
        cantidad_acreditada=cantidad,
        disponible=cantidad,
        origen=origen,
        acreditado_en=ahora,
        caduca_el=_sumar_meses(timezone.localdate(ahora), meses),
    )
    movimiento = MovimientoPuntos.objects.create(
        usuario=usuario,
        tipo=MovimientoPuntos.ACREDITACION,
        cantidad=cantidad,
        saldo_resultante=saldo(usuario),
        motivo=motivo,
        ocurrido_en=ahora,
        pedido=pedido,
    )
    movimiento.lotes.add(lote)
    return movimiento


def debitar(usuario, cantidad, *, pedido=None, motivo=""):
    """Consume lotes Activos en orden de caducidad más próxima (`CU-PTS-CJE`).

    Toma los lotes con bloqueo: dos compras que canjean a la vez no pueden
    gastar dos veces el mismo saldo. Si no alcanza, no toca nada.
    """
    if cantidad <= 0:
        return None
    lotes = list(
        LotePuntos.objects.select_for_update()
        .filter(usuario=usuario, estado=LotePuntos.ACTIVO)
        .order_by("caduca_el", "pk")
    )
    if sum(lote.disponible for lote in lotes) < cantidad:
        raise SaldoInsuficiente(f"El saldo no alcanza para {cantidad} puntos.")

    falta = cantidad
    consumidos = []
    for lote in lotes:
        if falta == 0:
            break
        usado = min(lote.disponible, falta)
        lote.disponible -= usado
        if lote.disponible == 0:
            lote.estado = LotePuntos.AGOTADO
        lote.save(update_fields=["disponible", "estado"])
        consumidos.append(lote)
        falta -= usado

    movimiento = MovimientoPuntos.objects.create(
        usuario=usuario,
        tipo=MovimientoPuntos.DEBITO,
        cantidad=cantidad,
        saldo_resultante=saldo(usuario),
        motivo=motivo,
        pedido=pedido,
    )
    movimiento.lotes.add(*consumidos)
    return movimiento
