"""Pruebas de contrato de la caja (`CU-CAJ-CIE`, plan 14): `CO-203`, `CO-126`, `CO-127`."""

from datetime import timedelta
from decimal import Decimal

import pytest
from django.urls import reverse
from django.utils import timezone
from freezegun import freeze_time

from apps.caja.models import CierreDeCaja
from apps.core.models import RegistroAuditoria
from apps.pedidos.models import Pedido, TransaccionPago
from apps.pedidos.tests.util import crear_pedido

pytestmark = pytest.mark.django_db

URL = reverse("caja:caja")
URL_CERRAR = reverse("caja:cerrar")


@pytest.fixture
def caja(client, cajero):
    client.force_login(cajero)
    return client


def transaccion(
    medio=TransaccionPago.EFECTIVO,
    monto="1000",
    canal=Pedido.PRESENCIAL,
    estado=TransaccionPago.APROBADO,
    hace_dias=0,
):
    pedido = crear_pedido(correo_invitado="x@correo.test", con_pago=False)
    Pedido.objects.filter(pk=pedido.pk).update(canal=canal)
    return TransaccionPago.objects.create(
        pedido=pedido,
        medio=medio,
        monto=Decimal(monto),
        estado=estado,
        registrada_en=timezone.now() - timedelta(days=hace_dias),
    )


@pytest.fixture
def jornada(db):
    return {
        "efectivo": transaccion(TransaccionPago.EFECTIVO, "1000"),
        "tarjeta": transaccion(TransaccionPago.TARJETA, "2500"),
        "online": transaccion(TransaccionPago.PASARELA, "4000", canal=Pedido.ONLINE),
        "pendiente": transaccion(
            TransaccionPago.TRANSFERENCIA, "700", estado=TransaccionPago.PENDIENTE_VERIFICACION
        ),
        "rechazada": transaccion(TransaccionPago.TARJETA, "900", estado=TransaccionPago.RECHAZADO),
    }


# ===========================================================================
# CO-203 · solicitarCierreDeCaja
# ===========================================================================


def test_CO203_el_resumen_previo_totaliza_por_canal_y_por_medio(caja, jornada):
    resumen = caja.get(URL).context["resumen"]

    assert resumen.total_presencial == Decimal("3500")
    assert resumen.total_online == Decimal("4000")
    assert dict(resumen.por_medio)["Tarjeta"] == Decimal("2500")
    assert resumen.total_global == Decimal("7500")
    assert len(resumen.incluidas) == 3


def test_CO203_A1_lista_las_pendientes_de_verificacion_aparte(caja, jornada):
    respuesta = caja.get(URL)

    assert [t.pk for t in respuesta.context["resumen"].pendientes] == [jornada["pendiente"].pk]
    assert "pendientes de verificación" in respuesta.content.decode()


def test_CO203_avisa_lo_de_dias_anteriores_sin_cerrar(caja):
    transaccion(hace_dias=2)
    transaccion()

    assert caja.get(URL).context["resumen"].de_dias_anteriores == 1


def test_CO203_cuenta_las_compras_pagadas_solo_con_puntos(caja):
    transaccion()
    crear_pedido(correo_invitado="y@correo.test", con_pago=False)

    assert caja.get(URL).context["resumen"].solo_puntos == 1


def test_CO203_E2_sin_movimientos(caja):
    contenido = caja.get(URL).content.decode()

    assert "No hay movimientos para consolidar." in contenido
    assert "Confirmar cierre de caja" not in contenido


def test_CO203_no_modifica_el_estado_del_sistema(caja, jornada):
    caja.get(URL)

    assert not CierreDeCaja.objects.exists()
    assert not TransaccionPago.objects.filter(incluida_en_cierre=True).exists()


# ===========================================================================
# CO-126 · confirmarCierreDeCaja
# ===========================================================================


def test_CO126_a_se_crea_el_cierre(caja, jornada):
    respuesta = caja.post(URL_CERRAR)

    cierre = CierreDeCaja.objects.get()
    assert respuesta.url == reverse("caja:cierre", args=[cierre.pk])


def test_CO126_b_el_cierre_queda_asociado_a_las_transacciones_incluidas(caja, jornada):
    caja.post(URL_CERRAR)

    cierre = CierreDeCaja.objects.get()
    assert set(cierre.transacciones.values_list("pk", flat=True)) == {
        jornada["efectivo"].pk,
        jornada["tarjeta"].pk,
        jornada["online"].pk,
    }


def test_CO126_c_fecha_totales_y_cuentas(caja, jornada, cajero):
    caja.post(URL_CERRAR)

    cierre = CierreDeCaja.objects.get()
    assert cierre.fecha_jornada == timezone.localdate()
    assert (cierre.total_presencial, cierre.total_online) == (Decimal("3500"), Decimal("4000"))
    assert (cierre.total_efectivo, cierre.total_tarjeta, cierre.total_pasarela) == (
        Decimal("1000"),
        Decimal("2500"),
        Decimal("4000"),
    )
    assert cierre.total_transferencia == 0
    assert cierre.total_global == Decimal("7500")
    assert (cierre.transacciones_incluidas, cierre.transacciones_excluidas) == (3, 1)
    assert cierre.realizado_por == cajero


def test_CO126_c_las_incluidas_pasan_a_incluidas_en_cierre(caja, jornada):
    assert not jornada["efectivo"].incluida_en_cierre

    caja.post(URL_CERRAR)

    jornada["efectivo"].refresh_from_db()
    assert jornada["efectivo"].incluida_en_cierre is True


def test_CO126_c_las_pendientes_y_rechazadas_quedan_fuera(caja, jornada):
    caja.post(URL_CERRAR)

    for clave in ("pendiente", "rechazada"):
        jornada[clave].refresh_from_db()
        assert jornada[clave].incluida_en_cierre is False
        assert jornada[clave].cierre is None


def test_CO126_queda_en_la_auditoria_con_los_totales(caja, jornada, cajero):
    caja.post(URL_CERRAR)

    registro = RegistroAuditoria.objects.get(accion=RegistroAuditoria.CIERRE_CAJA)
    assert registro.actor == cajero
    assert "total 7500" in registro.detalle
    assert "1 excluida(s)" in registro.detalle


def test_CO126_E1_no_hay_segundo_cierre_en_el_dia(caja, jornada):
    caja.post(URL_CERRAR)
    posterior = transaccion(TransaccionPago.EFECTIVO, "300")

    respuesta = caja.post(URL_CERRAR, follow=True)

    assert CierreDeCaja.objects.count() == 1
    posterior.refresh_from_db()
    assert posterior.incluida_en_cierre is False
    contenido = respuesta.content.decode()
    assert "La caja de hoy ya está cerrada." in contenido
    assert "1 transacción(es) posteriores esperan el próximo cierre." in contenido


def test_CO126_lo_vendido_despues_entra_en_el_cierre_siguiente(caja, jornada, cajero):
    caja.post(URL_CERRAR)
    posterior = transaccion(TransaccionPago.EFECTIVO, "300")

    with freeze_time(timezone.now() + timedelta(days=1)):
        caja.force_login(cajero)  # la sesión de ayer ya venció
        caja.post(URL_CERRAR)

    posterior.refresh_from_db()
    assert CierreDeCaja.objects.count() == 2
    assert posterior.cierre.fecha_jornada == timezone.localdate() + timedelta(days=1)


def test_CO126_E2_sin_movimientos_no_hay_cierre(caja):
    respuesta = caja.post(URL_CERRAR, follow=True)

    assert not CierreDeCaja.objects.exists()
    assert "No hay movimientos para consolidar." in respuesta.content.decode()


def test_CO126_la_base_no_admite_dos_cierres_de_la_misma_fecha(cajero):
    from django.db import IntegrityError

    CierreDeCaja.objects.create(fecha_jornada=timezone.localdate(), realizado_por=cajero)
    with pytest.raises(IntegrityError):
        CierreDeCaja.objects.create(fecha_jornada=timezone.localdate(), realizado_por=cajero)


# ===========================================================================
# CO-127 · exportarCierreDeCaja
# ===========================================================================


def test_CO127_el_csv_trae_cada_transaccion_y_los_totales(caja, jornada):
    caja.post(URL_CERRAR)
    cierre = CierreDeCaja.objects.get()

    respuesta = caja.get(reverse("caja:exportar", args=[cierre.pk]))

    contenido = respuesta.content.decode("utf-8-sig")
    assert respuesta["Content-Type"].startswith("text/csv")
    assert jornada["online"].pedido.numero in contenido
    assert "Tarjeta" in contenido
    assert "Total,,,,7500.00" in contenido


def test_CO127_queda_en_la_auditoria(caja, jornada, cajero):
    caja.post(URL_CERRAR)

    caja.get(reverse("caja:exportar", args=[CierreDeCaja.objects.get().pk]))

    registro = RegistroAuditoria.objects.get(accion=RegistroAuditoria.EXPORTACION_CIERRE)
    assert registro.actor == cajero


# ===========================================================================
# Acceso
# ===========================================================================


@pytest.mark.parametrize("nombre", ["caja:caja", "caja:cierres"])
def test_acceso_el_cliente_recibe_403_en_la_caja(client, cliente, nombre):
    client.force_login(cliente)

    assert client.get(reverse(nombre)).status_code == 403


def test_acceso_el_cliente_no_puede_cerrar(client, cliente, jornada):
    client.force_login(cliente)

    assert client.post(URL_CERRAR).status_code == 403
    assert not CierreDeCaja.objects.exists()


def test_acceso_el_administrador_tambien_cierra(client_admin, jornada):
    client_admin.post(URL_CERRAR)

    assert CierreDeCaja.objects.count() == 1
