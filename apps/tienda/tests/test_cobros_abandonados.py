"""Los cobros abandonados (plan 00, C3) y la sincronización de cotizaciones (A2)."""

from datetime import timedelta
from decimal import Decimal
from io import StringIO
from unittest.mock import patch

import pytest
from django.core.management import call_command
from django.utils import timezone

from apps.core.models import RegistroAuditoria
from apps.pedidos.models import Pedido
from apps.tienda import compra
from apps.tienda.models import CobroEnCurso
from apps.tienda.pasarelas import PasarelaDePrueba
from apps.tienda.tests.compra_util import cliente_con_direccion, fijar_parametros, producto

pytestmark = pytest.mark.django_db


def _cobro(*, hace_horas, usuario=None):
    prod = producto(stock=3)
    cobro = CobroEnCurso.objects.create(
        referencia=f"cobro-{hace_horas}",
        pasarela="prueba",
        usuario=usuario,
        correo_invitado="" if usuario else "invitado@correo.test",
        lineas=[{"producto": prod.pk, "cantidad": 1, "precio": "10000", "puntos": 0}],
        costo_envio=Decimal("0"),
        monto=Decimal("10000"),
    )
    CobroEnCurso.objects.filter(pk=cobro.pk).update(
        creado_en=timezone.now() - timedelta(hours=hace_horas)
    )
    cobro.refresh_from_db()
    return cobro


def test_un_cobro_pendiente_de_mas_de_un_dia_se_descarta():
    viejo = _cobro(hace_horas=25)
    reciente = _cobro(hace_horas=2)

    descartados = compra.descartar_abandonados()

    viejo.refresh_from_db()
    reciente.refresh_from_db()
    assert descartados == 1
    assert viejo.estado == CobroEnCurso.DESCARTADO
    assert reciente.estado == CobroEnCurso.PENDIENTE


def test_un_pago_aprobado_despues_de_descartado_se_reembolsa_y_no_genera_pedido(mailoutbox):
    fijar_parametros()
    cobro = _cobro(hace_horas=25, usuario=cliente_con_direccion())
    compra.descartar_abandonados()
    pasarela = PasarelaDePrueba()

    with patch.object(pasarela, "reembolsar", return_value=True) as reembolsar:
        compra.registrar_resultado(
            cobro.referencia, referencia_pago="pago-1", monto=cobro.monto, pasarela=pasarela
        )
        compra.registrar_resultado(
            cobro.referencia, referencia_pago="pago-1", monto=cobro.monto, pasarela=pasarela
        )

    cobro.refresh_from_db()
    assert cobro.estado == CobroEnCurso.REEMBOLSADO
    assert reembolsar.call_count == 1  # idempotente
    assert not Pedido.objects.exists()
    assert RegistroAuditoria.objects.filter(accion=RegistroAuditoria.INCIDENTE_COMPRA).count() == 1
    assert mailoutbox and mailoutbox[-1].to == [cobro.correo_de_contacto]


def test_CO155_y_los_cobros_abandonados_corren_en_el_temporizador():
    _cobro(hace_horas=30)
    salida = StringIO()

    call_command("ejecutar_temporizador", stdout=salida)

    texto = salida.getvalue()
    assert "cobros abandonados: 1 descartados" in texto
    # La red está cortada: la cotización conserva el respaldo anterior (A2).
    assert "cotizaciones: la API no respondio" in texto


def test_CO155_la_sincronizacion_guarda_el_respaldo_cuando_la_api_responde():
    from apps.core import cotizaciones

    catalogo = {"fecha": "2026-10-19", "valores": {"USD": Decimal("1200")}}
    with (
        patch.object(cotizaciones, "descargar_cotizaciones", return_value=catalogo),
        patch.object(cotizaciones, "guardar_respaldo") as guardar,
    ):
        resultado = cotizaciones.sincronizar()

    assert resultado == catalogo
    guardar.assert_called_once_with({"cotizaciones": catalogo})
