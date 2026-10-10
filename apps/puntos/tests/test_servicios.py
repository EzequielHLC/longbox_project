"""Unidad: la conversión de dinero a puntos, la caducidad y el débito FIFO (B-07-033)."""

from datetime import date
from decimal import Decimal

import pytest
from django.db import IntegrityError

from apps.accounts.tests.factories import UsuarioFactory
from apps.puntos import servicios
from apps.puntos.models import LotePuntos, MovimientoPuntos
from apps.tienda.compra import costo_de_envio
from apps.tienda.tests.compra_util import dar_puntos, fijar_parametros


@pytest.mark.parametrize(
    ("monto", "esperado"),
    [("0", 0), ("99.99", 0), ("100", 1), ("199.99", 1), ("10000", 100), ("18000", 180)],
)
def test_la_acreditacion_es_el_reintegro_en_pesos_convertido_a_puntos(monto, esperado):
    """10 % de reintegro y 1 punto = $10: cada $100 pagados suman 1 punto, hacia abajo."""
    puntos = servicios.puntos_por_monto(
        Decimal(monto), porcentaje=Decimal("10"), valor=Decimal("10")
    )
    assert puntos == esperado


def test_el_ejemplo_de_parametros_5_por_ciento_y_10_pesos():
    puntos = servicios.puntos_por_monto(
        Decimal("10000"), porcentaje=Decimal("5"), valor=Decimal("10")
    )
    assert puntos == 50


def test_cambiar_el_valor_del_punto_no_cambia_el_reintegro_en_pesos():
    for valor in (Decimal("1"), Decimal("10"), Decimal("25")):
        puntos = servicios.puntos_por_monto(Decimal("10000"), porcentaje=Decimal("5"), valor=valor)
        assert puntos * valor == Decimal("500")


@pytest.mark.parametrize(
    ("importe", "esperado"),
    [("10", 1), ("10.01", 2), ("3000", 300), ("3001", 301), ("0.01", 1)],
)
def test_el_canje_redondea_hacia_arriba(importe, esperado):
    assert servicios.puntos_para_cubrir(Decimal(importe), Decimal("10")) == esperado


def test_una_equivalencia_con_centavos_no_pierde_precision():
    assert (
        servicios.puntos_por_monto(Decimal("100"), porcentaje=Decimal("100"), valor=Decimal("0.30"))
        == 333
    )
    assert servicios.puntos_para_cubrir(Decimal("100"), Decimal("0.30")) == 334


@pytest.mark.parametrize(
    ("dia", "meses", "esperado"),
    [
        (date(2026, 1, 31), 1, date(2026, 2, 28)),
        (date(2028, 1, 31), 1, date(2028, 2, 29)),
        (date(2026, 10, 9), 12, date(2027, 10, 9)),
        (date(2026, 11, 30), 3, date(2027, 2, 28)),
    ],
)
def test_la_caducidad_suma_meses_de_calendario(dia, meses, esperado):
    assert servicios._sumar_meses(dia, meses) == esperado


@pytest.mark.django_db
def test_el_saldo_es_la_suma_de_los_lotes_activos():
    cliente = UsuarioFactory(rol="cliente")
    dar_puntos(cliente, 100)
    dar_puntos(cliente, 50)
    LotePuntos.objects.create(
        usuario=cliente,
        cantidad_acreditada=70,
        disponible=70,
        origen=LotePuntos.COMPRA,
        caduca_el=date(2020, 1, 1),
        estado=LotePuntos.VENCIDO,
    )

    assert servicios.saldo(cliente) == 150


@pytest.mark.django_db
def test_el_debito_consume_primero_el_lote_que_caduca_antes():
    cliente = UsuarioFactory(rol="cliente")
    lejano = dar_puntos(cliente, 100, dias=300)
    proximo = dar_puntos(cliente, 100, dias=10)

    servicios.debitar(cliente, 150)

    proximo.refresh_from_db()
    lejano.refresh_from_db()
    assert (proximo.disponible, proximo.estado) == (0, LotePuntos.AGOTADO)
    assert (lejano.disponible, lejano.estado) == (50, LotePuntos.ACTIVO)
    assert MovimientoPuntos.objects.get().saldo_resultante == 50


@pytest.mark.django_db
def test_un_debito_que_no_alcanza_no_toca_ningun_lote():
    cliente = UsuarioFactory(rol="cliente")
    lote = dar_puntos(cliente, 100)

    with pytest.raises(servicios.SaldoInsuficiente):
        servicios.debitar(cliente, 101)

    lote.refresh_from_db()
    assert lote.disponible == 100
    assert not MovimientoPuntos.objects.exists()


@pytest.mark.django_db
def test_acreditar_o_debitar_cero_no_hace_nada():
    cliente = UsuarioFactory(rol="cliente")

    assert servicios.acreditar(cliente, 0, origen=LotePuntos.COMPRA) is None
    assert servicios.debitar(cliente, 0) is None
    assert not LotePuntos.objects.exists()


@pytest.mark.django_db
def test_la_base_no_admite_un_lote_con_mas_disponible_que_lo_acreditado():
    cliente = UsuarioFactory(rol="cliente")

    with pytest.raises(IntegrityError):
        LotePuntos.objects.create(
            usuario=cliente,
            cantidad_acreditada=10,
            disponible=11,
            origen=LotePuntos.COMPRA,
            caduca_el=date(2030, 1, 1),
        )


@pytest.mark.django_db
def test_la_base_no_admite_un_lote_activo_sin_disponible():
    cliente = UsuarioFactory(rol="cliente")

    with pytest.raises(IntegrityError):
        LotePuntos.objects.create(
            usuario=cliente,
            cantidad_acreditada=10,
            disponible=0,
            origen=LotePuntos.COMPRA,
            caduca_el=date(2030, 1, 1),
        )


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("subtotal", "esperado"),
    [("49999.99", Decimal("1500")), ("50000", Decimal("0")), ("80000", Decimal("0"))],
)
def test_el_envio_es_gratis_desde_el_monto_minimo_inclusive(subtotal, esperado):
    fijar_parametros()

    assert costo_de_envio(Decimal(subtotal)) == esperado
