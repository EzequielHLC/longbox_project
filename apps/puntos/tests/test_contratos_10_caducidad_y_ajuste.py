"""Contratos de la caducidad y el ajuste manual de puntos (plan 10, segunda parte).

`CO-105`, con el aviso previo que pidió el responsable, `CO-191` y `CO-106`.
"""

from datetime import timedelta
from io import StringIO
from unittest.mock import patch

import pytest
from django.core.management import call_command
from django.urls import reverse
from django.utils import timezone

from apps.accounts.tests.factories import UsuarioFactory
from apps.core.models import ConfiguracionSistema, RegistroAuditoria
from apps.puntos import ajuste, caducidad, servicios
from apps.puntos.models import LotePuntos, MovimientoPuntos
from apps.tienda.models import CobroEnCurso
from apps.tienda.tests.compra_util import dar_puntos, fijar_parametros

HOY = timezone.localdate


def _acciones(accion):
    return RegistroAuditoria.objects.filter(accion=accion)


def _canje_pendiente(usuario, puntos, *, hace_horas=1):
    cobro = CobroEnCurso.objects.create(
        referencia=f"canje-{usuario.pk}-{puntos}-{hace_horas}",
        pasarela="prueba",
        usuario=usuario,
        costo_envio=0,
        monto=1000,
        puntos_a_debitar=puntos,
    )
    CobroEnCurso.objects.filter(pk=cobro.pk).update(
        creado_en=timezone.now() - timedelta(hours=hace_horas)
    )
    return cobro


@pytest.fixture
def titular(db):
    fijar_parametros()
    return UsuarioFactory(rol="cliente", first_name="Ana", last_name="Lectora")


# ---------------------------------------------------------------------------
# CO-105 ejecutarCicloDeCaducidadDePuntos
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_CO105_el_lote_con_caducidad_alcanzada_pasa_a_vencido_con_disponible_cero(titular):
    lote = dar_puntos(titular, 300, dias=0)
    LotePuntos.objects.filter(pk=lote.pk).update(disponible=120)
    lote.refresh_from_db()
    assert (lote.estado, lote.disponible) == (LotePuntos.ACTIVO, 120)

    caducidad.ciclo()

    lote.refresh_from_db()
    assert lote.estado == LotePuntos.VENCIDO
    assert lote.disponible == 0


@pytest.mark.django_db
def test_CO105_el_saldo_del_cliente_baja_en_lo_que_vencio(titular):
    dar_puntos(titular, 300, dias=-2)
    dar_puntos(titular, 50, dias=40)
    assert servicios.saldo(titular) == 350

    caducidad.ciclo()

    assert servicios.saldo(titular) == 50


@pytest.mark.django_db
def test_CO105_los_lotes_con_caducidad_futura_no_se_tocan(titular):
    vigente = dar_puntos(titular, 80, dias=1)

    caducidad.ciclo()

    vigente.refresh_from_db()
    assert (vigente.estado, vigente.disponible) == (LotePuntos.ACTIVO, 80)


@pytest.mark.django_db
def test_CO105_E2_un_lote_comprometido_en_un_canje_en_curso_no_se_modifica(titular):
    comprometido = dar_puntos(titular, 100, dias=0)
    libre = dar_puntos(titular, 200, dias=0)
    _canje_pendiente(titular, 100)

    resumen = caducidad.ciclo()

    comprometido.refresh_from_db()
    libre.refresh_from_db()
    assert (comprometido.estado, comprometido.disponible) == (LotePuntos.ACTIVO, 100)
    assert libre.estado == LotePuntos.VENCIDO
    assert resumen.diferidos == [comprometido.pk]


@pytest.mark.django_db
def test_CO105_E2_un_canje_abandonado_hace_mas_de_un_dia_no_difiere_la_caducidad(titular):
    lote = dar_puntos(titular, 100, dias=0)
    _canje_pendiente(titular, 100, hace_horas=25)

    caducidad.ciclo()

    lote.refresh_from_db()
    assert lote.estado == LotePuntos.VENCIDO


@pytest.mark.django_db
def test_CO105_registra_cada_lote_con_el_cliente_la_cantidad_y_la_fecha(titular):
    lote = dar_puntos(titular, 300, dias=-1)

    caducidad.ciclo()

    registro = _acciones(RegistroAuditoria.CADUCIDAD_PUNTOS).get()
    assert registro.objetivo == lote
    assert registro.objetivo_email == titular.email
    assert "300 pts" in registro.detalle
    assert lote.caduca_el.strftime("%d/%m/%Y") in registro.detalle
    assert registro.ocurrido_en is not None


@pytest.mark.django_db
def test_CO105_el_historial_muestra_el_debito_por_caducidad_con_su_saldo(titular):
    dar_puntos(titular, 300, dias=0)
    dar_puntos(titular, 40, dias=90)

    caducidad.ciclo()

    movimiento = MovimientoPuntos.objects.get()
    assert movimiento.tipo == MovimientoPuntos.DEBITO
    assert movimiento.cantidad == 300
    assert movimiento.motivo == "Caducidad"
    assert movimiento.saldo_resultante == 40


@pytest.mark.django_db
def test_CO105_avisa_a_cada_cliente_una_vez_con_sus_lotes_y_su_saldo(titular, mailoutbox):
    dar_puntos(titular, 300, dias=0)
    dar_puntos(titular, 20, dias=-3)
    dar_puntos(titular, 40, dias=90)
    otro = UsuarioFactory(rol="cliente")
    dar_puntos(otro, 10, dias=0)

    caducidad.ciclo()

    del_titular = [m for m in mailoutbox if m.to == [titular.email]]
    assert len(del_titular) == 1
    aviso = del_titular[0]
    assert "320 puntos" in aviso.subject
    assert "300 pts" in aviso.body and "20 pts" in aviso.body
    assert "40 pts" in aviso.body  # el saldo actualizado
    assert any(m.to == [otro.email] for m in mailoutbox)


@pytest.mark.django_db
def test_CO105_A1_sin_lotes_vencidos_no_invalida_ni_avisa_ni_registra(titular, mailoutbox):
    dar_puntos(titular, 100, dias=90)

    resumen = caducidad.ciclo()

    assert resumen.vencidos == []
    assert mailoutbox == []
    assert not _acciones(RegistroAuditoria.CADUCIDAD_PUNTOS).exists()


@pytest.mark.django_db
def test_CO105_E1_un_lote_que_falla_queda_como_estaba_y_el_ciclo_sigue(titular):
    falla = dar_puntos(titular, 100, dias=0)
    otro = UsuarioFactory(rol="cliente")
    sigue = dar_puntos(otro, 50, dias=0)
    original = caducidad._vencer_lote

    def vencer(lote_pk, hoy):
        if lote_pk == falla.pk:
            raise RuntimeError("se cortó la base")
        return original(lote_pk, hoy)

    with patch.object(caducidad, "_vencer_lote", side_effect=vencer):
        resumen = caducidad.ciclo()

    falla.refresh_from_db()
    sigue.refresh_from_db()
    assert (falla.estado, falla.disponible) == (LotePuntos.ACTIVO, 100)
    assert sigue.estado == LotePuntos.VENCIDO
    assert resumen.incidentes == [falla.pk]
    incidente = _acciones(RegistroAuditoria.INCIDENTE_CADUCIDAD).get()
    assert "se cortó la base" in incidente.detalle


@pytest.mark.django_db
def test_CO105_los_puntos_vencidos_no_se_recuperan_al_correr_otra_vez(titular, mailoutbox):
    lote = dar_puntos(titular, 100, dias=0)
    caducidad.ciclo()
    avisos = len(mailoutbox)

    caducidad.ciclo()

    lote.refresh_from_db()
    assert lote.estado == LotePuntos.VENCIDO
    assert MovimientoPuntos.objects.count() == 1
    assert _acciones(RegistroAuditoria.CADUCIDAD_PUNTOS).count() == 1
    assert len(mailoutbox) == avisos


@pytest.mark.django_db
def test_CO105_corre_en_el_temporizador(titular):
    lote = dar_puntos(titular, 100, dias=0)
    salida = StringIO()

    call_command("ejecutar_temporizador", stdout=salida)

    lote.refresh_from_db()
    assert lote.estado == LotePuntos.VENCIDO
    assert "puntos: 1 lotes vencidos" in salida.getvalue()


# ---------------------------------------------------------------------------
# El aviso previo (decisión del responsable sobre la ambigüedad 5)
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_aviso_previo_sale_dentro_de_los_dias_configurados_una_sola_vez(titular, mailoutbox):
    fijar_parametros(dias_aviso_caducidad_puntos=3)
    por_vencer = dar_puntos(titular, 150, dias=3)
    lejos = dar_puntos(titular, 70, dias=4)

    caducidad.ciclo()
    caducidad.ciclo()

    avisos = [m for m in mailoutbox if "por vencer" in m.subject]
    assert len(avisos) == 1
    assert "150 puntos" in avisos[0].subject
    hasta = (HOY() + timedelta(days=2)).strftime("%d/%m/%Y")
    assert hasta in avisos[0].body
    por_vencer.refresh_from_db()
    lejos.refresh_from_db()
    assert por_vencer.aviso_caducidad is True
    assert lejos.aviso_caducidad is False
    assert por_vencer.estado == LotePuntos.ACTIVO


@pytest.mark.django_db
def test_aviso_previo_toma_los_dias_del_parametro(titular, mailoutbox):
    fijar_parametros(dias_aviso_caducidad_puntos=7)
    dar_puntos(titular, 70, dias=6)

    caducidad.ciclo()

    assert any("por vencer" in m.subject for m in mailoutbox)


@pytest.mark.django_db
def test_CO130_el_aviso_previo_se_configura_en_parametros(client_admin):
    fijar_parametros()
    datos = {
        "guardar_compra": "1",
        "costo_envio": "1500",
        "monto_minimo_envio_gratuito": "50000",
        "ventana_decision_horas": "72",
        "plazo_retencion_meses": "3",
        "dias_aviso_retencion": "7",
        "plazo_devolucion_dias": "10",
        "plazo_garantia_dias": "90",
        "equivalencia_puntos": "10",
        "porcentaje_puntos": "10",
        "caducidad_puntos_meses": "12",
        "dias_aviso_caducidad_puntos": "5",
        "maximo_reserva_preventa": "5",
        "margen_cupo_preventa": "10",
        "pasarela": ConfiguracionSistema.PASARELA_PRUEBA,
    }
    assert ConfiguracionSistema.obtener().dias_aviso_caducidad_puntos == 3

    client_admin.post(reverse("catalog:parametros"), datos)

    assert ConfiguracionSistema.obtener().dias_aviso_caducidad_puntos == 5
    assert _acciones(RegistroAuditoria.PARAMETRO_MODIFICADO).get().detalle.endswith("3 → 5")


# ---------------------------------------------------------------------------
# CO-191 consultarPuntosDeCliente
# ---------------------------------------------------------------------------


def _url(cliente):
    return reverse("accounts:cliente_puntos", args=[cliente.pk])


@pytest.mark.django_db
def test_CO191_presenta_saldo_lotes_comprometido_y_movimientos_sin_modificar_nada(
    titular, client_admin
):
    dar_puntos(titular, 100, dias=10)
    dar_puntos(titular, 250, dias=200)
    servicios.acreditar(titular, 30, origen=LotePuntos.COMPRA)
    _canje_pendiente(titular, 120)
    lotes = list(LotePuntos.objects.values_list("pk", "disponible", "estado"))
    registros = RegistroAuditoria.objects.count()

    respuesta = client_admin.get(_url(titular))

    panel = respuesta.context["panel"]
    assert panel.saldo == 380
    assert panel.saldo_en_pesos == 3800  # 1 punto = $ 10
    assert panel.comprometido == 120
    assert panel.debitable == 260
    assert [lote.comprometido for lote in panel.lotes] == [100, 20, 0]
    assert len(panel.movimientos) == 1
    assert list(LotePuntos.objects.values_list("pk", "disponible", "estado")) == lotes
    assert RegistroAuditoria.objects.count() == registros


@pytest.mark.django_db
def test_CO191_la_ficha_del_cliente_lleva_a_sus_puntos(titular, client_admin):
    ficha = client_admin.get(reverse("accounts:cliente_ficha", args=[titular.pk]))

    assert _url(titular) in ficha.content.decode()


@pytest.mark.django_db
def test_CO191_una_cuenta_inactiva_no_admite_el_panel(client_admin):
    inactivo = UsuarioFactory(rol="cliente", estado="inactivo")

    respuesta = client_admin.get(_url(inactivo))

    assert respuesta.url == reverse("accounts:cliente_ficha", args=[inactivo.pk])


# ---------------------------------------------------------------------------
# CO-106 registrarAjusteManualDePuntos
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_CO106_la_acreditacion_crea_un_lote_de_ajuste_manual_con_la_caducidad_estandar(
    titular, administrador
):
    fijar_parametros(caducidad_puntos_meses=12)
    assert not LotePuntos.objects.exists()

    ajuste.ajustar(titular, administrador, MovimientoPuntos.ACREDITACION, 75, "No se acreditó")

    lote = LotePuntos.objects.get()
    assert lote.usuario == titular
    assert lote.origen == LotePuntos.AJUSTE_MANUAL
    assert lote.cantidad_acreditada == lote.disponible == 75
    assert lote.caduca_el == servicios._sumar_meses(HOY(), 12)


@pytest.mark.django_db
def test_CO106_el_debito_consume_lotes_por_caducidad_y_el_que_llega_a_cero_se_agota(
    titular, administrador
):
    primero = dar_puntos(titular, 50, dias=10)
    segundo = dar_puntos(titular, 100, dias=90)

    ajuste.ajustar(titular, administrador, MovimientoPuntos.DEBITO, 80, "Acreditación duplicada")

    primero.refresh_from_db()
    segundo.refresh_from_db()
    assert (primero.disponible, primero.estado) == (0, LotePuntos.AGOTADO)
    assert (segundo.disponible, segundo.estado) == (70, LotePuntos.ACTIVO)


@pytest.mark.django_db
def test_CO106_el_debito_no_toca_lo_comprometido_en_un_canje(titular, administrador):
    primero = dar_puntos(titular, 100, dias=10)
    segundo = dar_puntos(titular, 100, dias=90)
    _canje_pendiente(titular, 100)

    ajuste.ajustar(titular, administrador, MovimientoPuntos.DEBITO, 60, "Corrección")

    primero.refresh_from_db()
    segundo.refresh_from_db()
    assert primero.disponible == 100
    assert segundo.disponible == 40


@pytest.mark.django_db
@pytest.mark.parametrize("tipo", [MovimientoPuntos.ACREDITACION, MovimientoPuntos.DEBITO])
def test_CO106_crea_el_movimiento_con_tipo_cantidad_motivo_y_saldo(titular, administrador, tipo):
    dar_puntos(titular, 100, dias=90)

    hecho = ajuste.ajustar(titular, administrador, tipo, 40, "Caso de soporte 12")

    movimiento = MovimientoPuntos.objects.get()
    assert movimiento.usuario == titular
    assert movimiento.tipo == tipo
    assert movimiento.cantidad == 40
    assert movimiento.motivo == "Caso de soporte 12"
    assert movimiento.saldo_resultante == hecho.saldo == (140 if tipo == "acreditacion" else 60)


@pytest.mark.django_db
def test_CO106_registra_tipo_cantidad_saldos_motivo_y_administrador(titular, administrador):
    dar_puntos(titular, 100, dias=90)

    ajuste.ajustar(titular, administrador, MovimientoPuntos.DEBITO, 30, "Doble acreditación")

    registro = _acciones(RegistroAuditoria.AJUSTE_PUNTOS).get()
    assert registro.actor == administrador
    assert registro.objetivo == titular
    assert registro.detalle == "Débito de 30 pts. Saldo: 100 → 70. Motivo: Doble acreditación"


@pytest.mark.django_db
def test_CO106_avisa_al_cliente_el_tipo_la_cantidad_y_el_saldo(
    titular, administrador, mailoutbox, django_capture_on_commit_callbacks
):
    with django_capture_on_commit_callbacks(execute=True):
        ajuste.ajustar(titular, administrador, MovimientoPuntos.ACREDITACION, 25, "Soporte")

    aviso = mailoutbox[-1]
    assert aviso.to == [titular.email]
    assert "Acreditación: 25 pts" in aviso.body
    assert "Tu saldo: 25 pts" in aviso.body


@pytest.mark.django_db
def test_CO106_presenta_el_saldo_actualizado_al_administrador(titular, client_admin):
    respuesta = client_admin.post(
        _url(titular),
        {"tipo": MovimientoPuntos.ACREDITACION, "cantidad": "40", "motivo": "Soporte"},
        follow=True,
    )

    assert "pasó de 0 a 40 pts" in respuesta.content.decode()
    assert respuesta.context["panel"].saldo == 40


@pytest.mark.django_db
def test_CO106_E1_un_debito_mayor_que_lo_libre_informa_el_maximo_y_no_registra(
    titular, client_admin
):
    lote = dar_puntos(titular, 100, dias=90)
    _canje_pendiente(titular, 30)

    respuesta = client_admin.post(
        _url(titular), {"tipo": MovimientoPuntos.DEBITO, "cantidad": "80", "motivo": "Soporte"}
    )

    lote.refresh_from_db()
    assert respuesta.status_code == 200
    assert respuesta.context["maximo"] == 70
    assert "70 puntos" in respuesta.context["error"]
    assert lote.disponible == 100
    assert not MovimientoPuntos.objects.exists()
    assert not _acciones(RegistroAuditoria.AJUSTE_PUNTOS).exists()


@pytest.mark.django_db
def test_CO106_E2_sin_motivo_no_registra_y_conserva_lo_ingresado(titular, client_admin):
    respuesta = client_admin.post(
        _url(titular), {"tipo": MovimientoPuntos.ACREDITACION, "cantidad": "40", "motivo": "  "}
    )

    assert "obligatorio" in respuesta.context["error"]
    assert respuesta.context["datos"]["cantidad"] == "40"
    assert not LotePuntos.objects.exists()
    assert not _acciones(RegistroAuditoria.AJUSTE_PUNTOS).exists()


@pytest.mark.django_db
@pytest.mark.parametrize("cantidad", ["0", "-5", "diez", ""])
def test_CO106_la_cantidad_tiene_que_ser_mayor_que_cero(titular, client_admin, cantidad):
    respuesta = client_admin.post(
        _url(titular),
        {"tipo": MovimientoPuntos.ACREDITACION, "cantidad": cantidad, "motivo": "Soporte"},
    )

    assert "mayor que cero" in respuesta.context["error"]
    assert not LotePuntos.objects.exists()


@pytest.mark.django_db
def test_CO106_una_cuenta_inactiva_no_admite_ajustes(administrador):
    inactivo = UsuarioFactory(rol="cliente", estado="inactivo")

    with pytest.raises(ajuste.AjusteRechazado):
        ajuste.ajustar(inactivo, administrador, MovimientoPuntos.ACREDITACION, 10, "Soporte")

    assert not LotePuntos.objects.exists()


@pytest.mark.django_db
def test_CO106_volver_sin_confirmar_no_registra_nada(titular, client_admin):
    client_admin.get(_url(titular))

    assert not MovimientoPuntos.objects.exists()
    assert not _acciones(RegistroAuditoria.AJUSTE_PUNTOS).exists()
