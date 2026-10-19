"""Acceso al ajuste de puntos por la dirección real, y débitos y caducidades a la vez."""

import pytest
from django.urls import reverse

from apps.accounts.tests.factories import UsuarioFactory
from apps.core.models import RegistroAuditoria
from apps.core.tests.concurrencia import a_la_vez, errores_internos, sesion_de
from apps.puntos import caducidad, servicios
from apps.puntos.models import LotePuntos, MovimientoPuntos
from apps.tienda.tests.compra_util import dar_puntos, fijar_parametros


@pytest.mark.django_db
@pytest.mark.parametrize("rol", ["cajero", "cliente"])
def test_acceso_solo_el_administrador_consulta_y_ajusta_puntos(client, request, rol):
    titular = UsuarioFactory(rol="cliente")
    dar_puntos(titular, 100)
    url = reverse("accounts:cliente_puntos", args=[titular.pk])
    usuario = titular if rol == "cliente" else request.getfixturevalue(rol)
    client.force_login(usuario)

    respuestas = [
        client.get(url),
        client.post(url, {"tipo": "acreditacion", "cantidad": "500", "motivo": "Yo"}),
    ]

    assert {r.status_code for r in respuestas} == {403}
    assert servicios.saldo(titular) == 100


@pytest.mark.django_db
def test_acceso_sin_sesion_el_ajuste_lleva_al_ingreso(client):
    titular = UsuarioFactory(rol="cliente")

    respuesta = client.post(
        reverse("accounts:cliente_puntos", args=[titular.pk]),
        {"tipo": "acreditacion", "cantidad": "500", "motivo": "x"},
    )

    assert respuesta.status_code == 302
    assert reverse("accounts:login") in respuesta.url
    assert not LotePuntos.objects.exists()


@pytest.mark.django_db
def test_acceso_el_panel_de_puntos_no_existe_para_una_cuenta_de_personal(client_admin, cajero):
    respuesta = client_admin.get(reverse("accounts:cliente_puntos", args=[cajero.pk]))

    assert respuesta.status_code == 404


@pytest.mark.django_db(transaction=True)
def test_concurrencia_dos_debitos_que_suman_mas_que_el_saldo_registran_uno():
    fijar_parametros()
    titular = UsuarioFactory(rol="cliente")
    dar_puntos(titular, 100)
    url = reverse("accounts:cliente_puntos", args=[titular.pk])
    una = sesion_de(UsuarioFactory(rol="administrador"))
    otra = sesion_de(UsuarioFactory(rol="administrador"))
    datos = {"tipo": "debito", "cantidad": "70", "motivo": "Corrección"}

    respuestas = a_la_vez(lambda: una.post(url, datos), lambda: otra.post(url, datos))

    assert errores_internos(respuestas) == []
    assert servicios.saldo(titular) == 30
    assert MovimientoPuntos.objects.count() == 1
    assert RegistroAuditoria.objects.filter(accion=RegistroAuditoria.AJUSTE_PUNTOS).count() == 1


@pytest.mark.django_db(transaction=True)
def test_concurrencia_la_caducidad_y_un_debito_sobre_el_mismo_lote_no_lo_cuentan_dos_veces():
    fijar_parametros()
    titular = UsuarioFactory(rol="cliente")
    lote = dar_puntos(titular, 100, dias=0)
    panel = sesion_de(UsuarioFactory(rol="administrador"))
    url = reverse("accounts:cliente_puntos", args=[titular.pk])

    respuestas = a_la_vez(
        lambda: panel.post(url, {"tipo": "debito", "cantidad": "60", "motivo": "Corrección"}),
        lambda: caducidad.ciclo() and None,
    )

    lote.refresh_from_db()
    assert errores_internos([r for r in respuestas if r is not None]) == []
    assert lote.estado == LotePuntos.VENCIDO
    assert lote.disponible == 0
    debitado = sum(MovimientoPuntos.objects.values_list("cantidad", flat=True))
    assert debitado == 100
