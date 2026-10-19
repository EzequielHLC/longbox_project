"""Saldo, acreditación y débito de puntos (RF-19, RF-20; B-07-033).

Lo que la compra necesita del módulo 10. La consulta del Cliente, la caducidad
y el ajuste manual llegan con ese módulo.

**Los puntos son enteros y el dinero es `Decimal`.** La conversión redondea
siempre contra el error: lo que se acredita, hacia abajo; lo que pide un canje,
hacia arriba (B-07-033).
"""

import calendar
from datetime import date, timedelta
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


def puntos_de_una_unidad(linea, equivalencia=None):
    """El 100 % del valor de una unidad de la línea, en puntos (B-01-010, B-09-004).

    Lo pagado en dinero se convierte hacia arriba; lo pagado con puntos devuelve
    su parte de los puntos canjeados, también hacia arriba.
    """
    if linea.cubierta_con_puntos:
        return -(-linea.puntos_canjeados // linea.cantidad)
    return puntos_para_cubrir(linea.precio_unitario, equivalencia)


def _sumar_meses(dia, meses):
    """El mismo día, `meses` después; el 31 de un mes corto cae en su último día."""
    anio, mes = divmod(dia.month - 1 + meses, 12)
    anio, mes = dia.year + anio, mes + 1
    return date(anio, mes, min(dia.day, calendar.monthrange(anio, mes)[1]))


def acreditar(usuario, cantidad, *, origen, pedido=None, linea=None, caso=None, motivo=""):
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
        linea_pedido=linea,
        caso_devolucion=caso,
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


# ---------------------------------------------------------------------------
# Lo comprometido en un canje en curso (plan 10, segunda parte, ambigüedad 1)
# ---------------------------------------------------------------------------

# Un cobro pendiente más viejo que esto está abandonado: no traba los puntos.
VIGENCIA_DE_UN_CANJE = timedelta(hours=24)


def comprometidos(usuario, ahora=None):
    """Los puntos que un pago pendiente va a debitar al aprobarse.

    La compra no marca los lotes: debita al aprobarse el pago, en orden de
    caducidad. Mientras tanto, lo que el cobro va a consumir son los primeros
    N puntos de esos lotes, y eso es lo que `CO-105` no vence y `CO-106` no
    debita.
    """
    from apps.tienda.models import CobroEnCurso

    desde = (ahora or timezone.now()) - VIGENCIA_DE_UN_CANJE
    total = CobroEnCurso.objects.filter(
        usuario=usuario,
        tipo=CobroEnCurso.COMPRA,
        estado=CobroEnCurso.PENDIENTE,
        creado_en__gte=desde,
    ).aggregate(total=Sum("puntos_a_debitar"))["total"]
    return total or 0


def reparto_comprometido(lotes, cantidad):
    """Cuánto de cada lote (en orden de caducidad) cubre lo comprometido."""
    reparto, falta = {}, cantidad
    for lote in lotes:
        if falta <= 0:
            break
        tomado = min(lote.disponible, falta)
        reparto[lote.pk] = tomado
        falta -= tomado
    return reparto


def _activos_bloqueados(usuario):
    """Los lotes Activos con bloqueo, en el orden del débito del canje: sin deadlocks."""
    return list(
        LotePuntos.objects.select_for_update()
        .filter(usuario=usuario, estado=LotePuntos.ACTIVO)
        .order_by("caduca_el", "pk")
    )


def debitable(usuario, ahora=None):
    """El máximo que admite un débito manual: el saldo menos lo comprometido (`CO-106` E1)."""
    return max(saldo(usuario) - comprometidos(usuario, ahora), 0)


def debitar_no_comprometidos(usuario, cantidad, *, motivo="", pedido=None, linea=None):
    """`CO-106`: consume lo libre de cada lote, en orden de caducidad.

    Lo comprometido queda en los primeros lotes, para el pago que lo va a
    debitar. Si lo libre no alcanza, no toca nada.
    """
    lotes = _activos_bloqueados(usuario)
    reparto = reparto_comprometido(lotes, comprometidos(usuario))
    libres = {lote.pk: lote.disponible - reparto.get(lote.pk, 0) for lote in lotes}
    if sum(libres.values()) < cantidad:
        raise SaldoInsuficiente(f"El máximo debitable es {sum(libres.values())} puntos.")

    falta, consumidos = cantidad, []
    for lote in lotes:
        if falta == 0:
            break
        usado = min(libres[lote.pk], falta)
        if not usado:
            continue
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
        linea_pedido=linea,
    )
    movimiento.lotes.add(*consumidos)
    return movimiento


# ---------------------------------------------------------------------------
# Los puntos ganados con una compra que se reembolsa (plan 00, C2; RF-19)
# ---------------------------------------------------------------------------

MOTIVO_GANADOS = "Descuento de los puntos ganados con la compra"


def ganados_por_unidad(linea):
    """Lo que una unidad pagada en dinero sumó en la compra, hacia abajo.

    La acreditación de la compra es una por pedido (B-07-033); se reparte en
    proporción a lo pagado en dinero. Lo pagado con puntos no sumó nada.
    """
    if linea.cubierta_con_puntos:
        return 0
    pedido = linea.pedido
    ganados = sum(
        MovimientoPuntos.objects.filter(
            pedido=pedido, tipo=MovimientoPuntos.ACREDITACION, lotes__origen=LotePuntos.COMPRA
        )
        .distinct()
        .values_list("cantidad", flat=True)
    )
    if not ganados:
        return 0
    pagado = sum(
        (
            otra.precio_unitario * otra.cantidad
            for otra in pedido.lineas.all()
            if not otra.cubierta_con_puntos
        ),
        Decimal("0"),
    )
    if pagado <= 0:
        return 0
    return int((ganados * linea.precio_unitario / pagado).to_integral_value(rounding=ROUND_FLOOR))


def descontar_ganados(usuario, linea, unidades=1):
    """Debita lo que ganaron `unidades` de la línea, hasta donde alcance lo libre.

    Se llama después de acreditar el reembolso, dentro de su transacción: el
    saldo nunca queda negativo y lo comprometido en un canje no se toca.
    """
    if usuario is None:
        return 0
    cantidad = min(ganados_por_unidad(linea) * unidades, debitable(usuario))
    if cantidad <= 0:
        return 0
    debitar_no_comprometidos(
        usuario, cantidad, motivo=MOTIVO_GANADOS, pedido=linea.pedido, linea=linea
    )
    return cantidad
