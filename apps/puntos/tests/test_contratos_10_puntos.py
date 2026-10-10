"""Pruebas de contrato de «Mis puntos» (plan 10): `CO-188` y `CO-189`, y el saldo
siempre a la vista en el encabezado (B-10-002)."""

from datetime import timedelta
from decimal import Decimal

import pytest
from django.urls import reverse
from django.utils import timezone

from apps.accounts.models import Usuario
from apps.accounts.tests.factories import UsuarioFactory
from apps.pedidos.tests.util import crear_pedido
from apps.puntos import servicios
from apps.puntos.models import LotePuntos, MovimientoPuntos
from apps.tienda.tests.compra_util import dar_puntos, fijar_parametros

pytestmark = pytest.mark.django_db

URL = reverse("cuenta:puntos")


@pytest.fixture(autouse=True)
def parametros(db):
    return fijar_parametros()


@pytest.fixture
def titular(db):
    return UsuarioFactory(rol=Usuario.CLIENTE)


@pytest.fixture
def navegador(client, titular):
    client.force_login(titular)
    return client


def historial(titular):
    pedido = crear_pedido(titular)
    servicios.acreditar(titular, 1000, origen=LotePuntos.COMPRA, pedido=pedido)
    servicios.debitar(titular, 300, pedido=pedido)
    return pedido


# ===========================================================================
# CO-188 · consultarPuntos
# ===========================================================================


def test_CO188_el_saldo_con_su_equivalencia_en_pesos(navegador, titular):
    dar_puntos(titular, 150)

    respuesta = navegador.get(URL)

    assert respuesta.context["saldo"] == 150
    assert respuesta.context["saldo_en_pesos"] == Decimal("1500")
    assert "1.500" in respuesta.content.decode()


def test_CO188_cada_lote_con_origen_monto_disponible_y_caducidad(navegador, titular):
    lote = dar_puntos(titular, 200)
    LotePuntos.objects.filter(pk=lote.pk).update(disponible=120)

    respuesta = navegador.get(URL)

    contenido = respuesta.content.decode()
    assert "120 de 200 pts" in contenido
    assert "Ajuste manual" in contenido
    assert lote.caduca_el.strftime("%d/%m/%Y") in contenido


def test_CO188_destaca_los_lotes_que_vencen_dentro_de_30_dias(navegador, titular):
    cerca = dar_puntos(titular, 10, dias=30)
    lejos = dar_puntos(titular, 10, dias=31)

    lotes = {lote.pk: lote for lote in navegador.get(URL).context["lotes"]}

    assert lotes[cerca.pk].proximo_a_vencer is True
    assert lotes[lejos.pk].proximo_a_vencer is False


def test_CO188_el_historial_descendente_con_saldo_resultante_y_su_pedido(navegador, titular):
    pedido = historial(titular)

    respuesta = navegador.get(URL)

    movimientos = list(respuesta.context["movimientos"])
    assert [m.tipo for m in movimientos] == [MovimientoPuntos.DEBITO, MovimientoPuntos.ACREDITACION]
    assert [m.saldo_resultante for m in movimientos] == [700, 1000]
    assert reverse("cuenta:pedido", args=[pedido.numero]) in respuesta.content.decode()


def test_CO188_A1_sin_puntos_saldo_cero_y_mensajes(navegador):
    respuesta = navegador.get(URL)

    contenido = respuesta.content.decode()
    assert respuesta.context["saldo"] == 0
    assert "Todavía no tenés puntos" in contenido
    assert "Todavía no hay movimientos" in contenido


def test_CO188_no_muestra_los_puntos_de_otro_cliente(navegador):
    dar_puntos(UsuarioFactory(rol=Usuario.CLIENTE), 999)

    respuesta = navegador.get(URL)

    assert respuesta.context["saldo"] == 0
    assert respuesta.context["lotes"] == []


def test_CO188_no_modifica_el_estado_del_sistema(navegador, titular):
    historial(titular)
    antes = list(LotePuntos.objects.values_list("pk", "disponible", "estado"))

    navegador.get(URL)

    assert list(LotePuntos.objects.values_list("pk", "disponible", "estado")) == antes
    assert MovimientoPuntos.objects.count() == 2


# ===========================================================================
# CO-189 · filtrarMovimientosDePuntos
# ===========================================================================


def test_CO189_filtra_por_tipo_y_muestra_el_total(navegador, titular):
    historial(titular)

    respuesta = navegador.get(URL, {"tipo": MovimientoPuntos.DEBITO})

    assert [m.tipo for m in respuesta.context["movimientos"]] == [MovimientoPuntos.DEBITO]
    assert "1 movimiento" in respuesta.content.decode()


def test_CO189_filtra_por_rango_de_fechas(navegador, titular):
    historial(titular)
    viejo = MovimientoPuntos.objects.get(tipo=MovimientoPuntos.ACREDITACION)
    MovimientoPuntos.objects.filter(pk=viejo.pk).update(
        ocurrido_en=timezone.now() - timedelta(days=40)
    )
    desde = (timezone.localdate() - timedelta(days=5)).isoformat()

    respuesta = navegador.get(URL, {"desde": desde})

    assert [m.tipo for m in respuesta.context["movimientos"]] == [MovimientoPuntos.DEBITO]


def test_CO189_E1_sin_resultados_informa_y_ofrece_limpiar(navegador, titular):
    historial(titular)
    manana = (timezone.localdate() + timedelta(days=1)).isoformat()

    contenido = navegador.get(URL, {"desde": manana}).content.decode()

    assert "Ningún movimiento coincide con el filtro." in contenido
    assert "Limpiar filtros" in contenido


def test_CO189_un_filtro_invalido_se_ignora(navegador, titular):
    historial(titular)

    respuesta = navegador.get(URL, {"tipo": "inventado", "desde": "ayer"})

    assert len(respuesta.context["movimientos"]) == 2


# ===========================================================================
# El saldo en el encabezado (B-10-002)
# ===========================================================================


def test_el_saldo_esta_a_la_vista_en_la_tienda(navegador, titular):
    dar_puntos(titular, 75)

    contenido = navegador.get(reverse("core:tienda")).content.decode()

    assert 'class="encabezado-publico__puntos"' in contenido
    assert "Tus puntos: 75, equivalen a $" in contenido
    assert "Mis puntos · 75" in contenido


@pytest.mark.parametrize("rol", [None, "cajero", "administrador"])
def test_el_saldo_no_aparece_para_invitados_ni_personal(client, request, rol):
    if rol:
        client.force_login(request.getfixturevalue(rol))

    contenido = client.get(reverse("core:tienda")).content.decode()

    assert "encabezado-publico__puntos" not in contenido
