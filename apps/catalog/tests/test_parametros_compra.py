"""`CO-130` en la sección «Compra online» de Parámetros (plan 07, sexta parte).

Logística y Fidelización de `CU-CFG-PAR`, el costo de envío (B-07-032) y la
pasarela (B-07-031). Cada cambio queda auditado con el valor anterior y el nuevo.
"""

from decimal import Decimal

import pytest
from django.urls import reverse

from apps.core.models import ConfiguracionSistema, RegistroAuditoria

pytestmark = pytest.mark.django_db

URL = reverse("catalog:parametros")

VALIDOS = {
    "guardar_compra": "1",
    "costo_envio": "2500",
    "monto_minimo_envio_gratuito": "75000",
    "ventana_decision_horas": "72",
    "plazo_retencion_meses": "3",
    "dias_aviso_retencion": "7",
    "plazo_devolucion_dias": "10",
    "plazo_garantia_dias": "90",
    "equivalencia_puntos": "20",
    "porcentaje_puntos": "3",
    "caducidad_puntos_meses": "6",
    "dias_aviso_caducidad_puntos": "3",
    "maximo_reserva_preventa": "5",
    "margen_cupo_preventa": "10",
    "pasarela": ConfiguracionSistema.PASARELA_MERCADOPAGO,
}


def test_CO130_los_parametros_de_la_compra_pasan_a_los_declarados(client_admin):
    antes = ConfiguracionSistema.obtener()
    assert (antes.costo_envio, antes.equivalencia_puntos) == (Decimal("8000"), Decimal("10"))

    respuesta = client_admin.post(URL, VALIDOS)

    despues = ConfiguracionSistema.obtener()
    assert respuesta.url == URL
    assert despues.costo_envio == Decimal("2500")
    assert despues.monto_minimo_envio_gratuito == Decimal("75000")
    assert despues.equivalencia_puntos == Decimal("20")
    assert despues.caducidad_puntos_meses == 6
    assert despues.pasarela == ConfiguracionSistema.PASARELA_MERCADOPAGO


def test_CO130_una_entrada_de_auditoria_por_cada_parametro_modificado(client_admin, administrador):
    client_admin.post(URL, VALIDOS)

    registros = RegistroAuditoria.objects.filter(accion=RegistroAuditoria.PARAMETRO_MODIFICADO)
    detalles = set(registros.values_list("detalle", flat=True))
    assert detalles == {
        "costo de envío: 8000 → 2500",
        "monto mínimo para envío gratuito: 100000 → 75000",
        "valor del punto ($): 10 → 20",
        "reintegro en puntos (%): 5 → 3",
        "caducidad de puntos (meses): 12 → 6",
        "pasarela de pago: Pasarela de prueba → MercadoPago",
    }
    assert {registro.actor for registro in registros} == {administrador}


def test_CO130_solo_se_audita_lo_que_cambio(client_admin):
    client_admin.post(URL, {**VALIDOS, "costo_envio": "8000"})

    detalles = RegistroAuditoria.objects.filter(
        accion=RegistroAuditoria.PARAMETRO_MODIFICADO
    ).values_list("detalle", flat=True)
    assert not any(detalle.startswith("costo de envío") for detalle in detalles)
    assert len(detalles) == 5


def test_CO130_guardar_sin_cambios_no_deja_entradas(client_admin):
    client_admin.post(
        URL,
        {
            "guardar_compra": "1",
            "costo_envio": "8000",
            "monto_minimo_envio_gratuito": "100000",
            "ventana_decision_horas": "72",
            "plazo_retencion_meses": "3",
            "dias_aviso_retencion": "7",
            "equivalencia_puntos": "10",
            "porcentaje_puntos": "5",
            "caducidad_puntos_meses": "12",
            "dias_aviso_caducidad_puntos": "3",
            "maximo_reserva_preventa": "5",
            "margen_cupo_preventa": "10",
            "pasarela": ConfiguracionSistema.PASARELA_PRUEBA,
        },
    )

    assert not RegistroAuditoria.objects.filter(
        accion=RegistroAuditoria.PARAMETRO_MODIFICADO
    ).exists()


def test_CO130_b_la_configuracion_queda_asociada_al_administrador(client_admin, administrador):
    client_admin.post(URL, VALIDOS)

    assert ConfiguracionSistema.obtener().actualizado_por == administrador


def test_CO130_los_valores_operativos_no_cambian_al_guardar_la_compra(client_admin):
    antes = ConfiguracionSistema.obtener()

    client_admin.post(URL, VALIDOS)

    despues = ConfiguracionSistema.obtener()
    assert despues.stock_inicial_por_defecto == antes.stock_inicial_por_defecto
    assert despues.intervalo_carrusel == antes.intervalo_carrusel


@pytest.mark.parametrize(
    ("campo", "valor"),
    [
        ("costo_envio", "-1"),
        ("monto_minimo_envio_gratuito", "0"),
        ("equivalencia_puntos", "0"),
        ("porcentaje_puntos", "0"),
        ("porcentaje_puntos", "100.01"),
        ("caducidad_puntos_meses", "0"),
        ("ventana_decision_horas", "0"),
        ("pasarela", "otra"),
    ],
)
def test_CO130_un_valor_fuera_de_rango_no_se_guarda(client_admin, campo, valor):
    respuesta = client_admin.post(URL, {**VALIDOS, campo: valor})

    assert respuesta.status_code == 200
    assert respuesta.context["form_compra"].errors[campo]
    assert ConfiguracionSistema.obtener().costo_envio == Decimal("8000")
    assert not RegistroAuditoria.objects.filter(
        accion=RegistroAuditoria.PARAMETRO_MODIFICADO
    ).exists()


def test_CO130_la_pantalla_muestra_la_seccion_de_compra_online(client_admin):
    contenido = client_admin.get(URL).content.decode()

    assert "Compra online" in contenido
    assert 'name="guardar_compra"' in contenido


@pytest.mark.parametrize("rol", ["cajero", "cliente"])
def test_acceso_solo_el_administrador_guarda_la_compra_online(client, request, rol):
    client.force_login(request.getfixturevalue(rol))

    respuesta = client.post(URL, VALIDOS)

    assert respuesta.status_code in (302, 403)
    assert ConfiguracionSistema.obtener().costo_envio == Decimal("8000")


def test_la_pantalla_muestra_que_significan_los_dos_numeros(client_admin):
    contenido = client_admin.get(URL).content.decode()

    assert "1 punto = $" in contenido
    assert "% de cada compra" in contenido
    # 5 % de $10.000 = $500, a $10 el punto: 50 puntos.
    assert '<span class="datos">50</span> puntos' in contenido


def test_CO130_el_maximo_por_reserva_pasa_al_declarado_y_se_audita(client_admin):
    """Plan 00 de tope de reservas: el parámetro nuevo, en Comercial."""
    assert ConfiguracionSistema.obtener().maximo_reserva_preventa == 5

    client_admin.post(URL, {**VALIDOS, "maximo_reserva_preventa": "3"})

    assert ConfiguracionSistema.obtener().maximo_reserva_preventa == 3
    assert RegistroAuditoria.objects.filter(
        accion=RegistroAuditoria.PARAMETRO_MODIFICADO,
        detalle="máximo por reserva (unidades): 5 → 3",
    ).exists()


def test_CO130_E1_el_maximo_por_reserva_es_al_menos_uno(client_admin):
    respuesta = client_admin.post(URL, {**VALIDOS, "maximo_reserva_preventa": "0"})

    assert respuesta.status_code == 200
    assert ConfiguracionSistema.obtener().maximo_reserva_preventa == 5


def test_CO130_el_margen_del_cupo_pasa_al_declarado_y_se_audita(client_admin):
    """Plan 00 del circuito, decisión 2: el margen global del cupo de pre-venta."""
    client_admin.post(URL, {**VALIDOS, "margen_cupo_preventa": "15"})

    assert ConfiguracionSistema.obtener().margen_cupo_preventa == 15
    assert RegistroAuditoria.objects.filter(
        accion=RegistroAuditoria.PARAMETRO_MODIFICADO,
        detalle="margen del cupo de pre-venta (%): 10 → 15",
    ).exists()


def test_CO130_E1_el_margen_del_cupo_no_pasa_del_50(client_admin):
    respuesta = client_admin.post(URL, {**VALIDOS, "margen_cupo_preventa": "80"})

    assert respuesta.status_code == 200
    assert ConfiguracionSistema.obtener().margen_cupo_preventa == 10
