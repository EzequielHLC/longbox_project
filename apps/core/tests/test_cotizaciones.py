"""Cotización del peso frente a las monedas con las que se importa."""

import json
from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import patch

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError

from apps.core import cotizaciones, integraciones

# Respuesta con base en dólares: la cotización del euro y la del yen salen por
# paridad cruzada, que es lo que evita hacer tres pedidos.
RESPUESTA = {
    "result": "success",
    "time_last_update_unix": 1_755_302_400,  # 2025-08-16
    "base_code": "USD",
    "rates": {"USD": 1, "ARS": 1500.0, "EUR": 0.8, "JPY": 150.0, "BRL": 5.4},
}


def api_responde(datos):
    return patch.object(integraciones, "pedir_json", return_value=datos)


def api_caida():
    return patch.object(integraciones, "pedir_json", return_value=None)


def test_el_dolar_sale_directo_de_la_paridad_contra_el_peso():
    with api_responde(RESPUESTA):
        assert cotizaciones.cotizacion_de("USD") == Decimal("1500.0000")


def test_el_euro_y_el_yen_salen_por_paridad_cruzada():
    """1500 pesos por dólar y 0,8 euros por dólar dan 1875 pesos por euro."""
    with api_responde(RESPUESTA):
        assert cotizaciones.cotizacion_de("EUR") == Decimal("1875.0000")
        assert cotizaciones.cotizacion_de("JPY") == Decimal("10.0000")


def test_solo_se_ofrecen_las_tres_monedas_del_negocio():
    """El servicio devuelve 160 monedas; el desplegable ofrece tres."""
    with api_responde(RESPUESTA):
        assert set(cotizaciones.obtener_cotizaciones()["valores"]) == {"USD", "EUR", "JPY"}

    assert cotizaciones.cotizacion_de("BRL") is None


def test_el_peso_vale_un_peso_sin_consultar_nada():
    """La moneda local no depende de que ningún servicio esté en línea."""
    with api_caida():
        assert cotizaciones.cotizacion_de(cotizaciones.MONEDA_LOCAL) == Decimal("1")


def test_una_respuesta_sin_exito_se_trata_como_caida():
    with api_responde({"result": "error", "rates": {}}):
        assert cotizaciones.descargar_cotizaciones() == {}


def test_una_respuesta_sin_la_paridad_del_peso_no_sirve():
    with api_responde({"result": "success", "rates": {"EUR": 0.8}}):
        assert cotizaciones.descargar_cotizaciones() == {}


@pytest.mark.parametrize("valor", [0, -5, "no es un número", None])
def test_una_paridad_rota_no_genera_una_cotizacion(valor):
    """Un cero o un negativo no son un dato: son una respuesta rota.

    Dejarlos pasar pondría el precio de todo un lote importado en cero.
    """
    with api_responde({"result": "success", "rates": {"ARS": valor, "EUR": 0.8}}):
        assert cotizaciones.descargar_cotizaciones() == {}


def test_una_moneda_rota_se_descarta_sin_tirar_abajo_las_otras():
    with api_responde({"result": "success", "rates": {"ARS": 1500.0, "EUR": 0, "JPY": 150.0}}):
        valores = cotizaciones.obtener_cotizaciones()["valores"]

    assert "EUR" not in valores
    assert valores["USD"] == "1500.0000"
    assert valores["JPY"] == "10.0000"


def test_la_segunda_consulta_sale_de_la_cache():
    with api_responde(RESPUESTA) as pedir:
        cotizaciones.obtener_cotizaciones()
        cotizaciones.obtener_cotizaciones()

    assert pedir.call_count == 1


def test_si_la_api_no_responde_se_usa_el_respaldo_local():
    with api_caida():
        valores = cotizaciones.obtener_cotizaciones().get("valores", {})

    assert set(valores) == {"USD", "EUR", "JPY"}
    assert all(Decimal(valor) > 0 for valor in valores.values())


def test_el_respaldo_versionado_tiene_las_tres_monedas_y_su_fecha():
    guardado = json.loads(cotizaciones.RUTA_RESPALDO.read_text(encoding="utf-8"))["cotizaciones"]

    assert set(guardado["valores"]) == {"USD", "EUR", "JPY"}
    assert date.fromisoformat(guardado["fecha"])


def test_una_cotizacion_de_hace_meses_se_marca_como_desactualizada():
    """El aviso existe porque un tipo de cambio viejo no es como una provincia
    vieja: usarlo sin mirarlo deja mal el precio de todo el lote."""
    vieja = (date.today() - timedelta(days=30)).isoformat()

    with (
        api_responde({**RESPUESTA, "time_last_update_unix": None}),
        patch.object(cotizaciones, "_fecha_de", return_value=vieja),
    ):
        assert cotizaciones.esta_desactualizada() is True


def test_una_cotizacion_de_hoy_no_se_marca_como_desactualizada():
    with (
        api_responde(RESPUESTA),
        patch.object(cotizaciones, "_fecha_de", return_value=date.today().isoformat()),
    ):
        assert cotizaciones.esta_desactualizada() is False


def test_sin_ninguna_cotizacion_se_considera_desactualizada():
    """Ante la duda, se avisa: es preferible una revisión de más que un precio
    calculado con un dato que nadie sabe de cuándo es."""
    with api_caida(), patch.object(cotizaciones, "obtener_cotizaciones", return_value={}):
        assert cotizaciones.esta_desactualizada() is True


def test_el_resumen_para_la_pantalla_trae_todo_masticado():
    with api_responde(RESPUESTA):
        resumen = cotizaciones.resumen_para_pantalla()

    assert set(resumen) == {"valores", "fecha", "desactualizada"}
    assert resumen["valores"]["USD"] == "1500.0000"
    assert isinstance(resumen["fecha"], date)


def test_el_comando_reescribe_el_respaldo(tmp_path):
    destino = tmp_path / "cotizaciones.json"

    with api_responde(RESPUESTA), patch.object(cotizaciones, "RUTA_RESPALDO", destino):
        call_command("sincronizar_cotizaciones")

    guardado = json.loads(destino.read_text(encoding="utf-8"))["cotizaciones"]
    assert guardado["valores"]["USD"] == "1500.0000"


def test_el_comando_no_pisa_el_respaldo_si_la_api_falla(tmp_path):
    destino = tmp_path / "cotizaciones.json"
    destino.write_text('{"cotizaciones": {"fecha": "2026-01-01", "valores": {}}}', encoding="utf-8")

    with api_caida(), patch.object(cotizaciones, "RUTA_RESPALDO", destino):
        with pytest.raises(CommandError):
            call_command("sincronizar_cotizaciones")

    assert json.loads(destino.read_text(encoding="utf-8"))["cotizaciones"]["fecha"] == "2026-01-01"


def test_las_cabeceras_de_las_integraciones_son_ascii():
    """Un valor de cabecera HTTP viaja en ASCII.

    Con tildes, Cloudflare —que está delante de buena parte de las APIs
    públicas— contesta 403, y el error llega como un rechazo genérico que no
    dice nada de la causa. Este test es el recordatorio de por qué el
    identificador del proyecto está escrito sin acentos.
    """
    for nombre, valor in integraciones.CABECERAS.items():
        assert valor.isascii(), f"La cabecera {nombre} tiene caracteres no ASCII: {valor!r}"
