"""Integración con georef-ar-api: caché, respaldo y degradación."""

import json
from unittest.mock import patch

import pytest
from django.conf import settings
from django.core.management import call_command
from django.core.management.base import CommandError
from django.urls import reverse

from apps.core import georef, integraciones

RESPUESTA_PROVINCIAS = {
    "provincias": [{"nombre": "Misiones"}, {"nombre": "Corrientes"}, {"nombre": "Buenos Aires"}]
}

RESPUESTA_LOCALIDADES = {
    "localidades": [{"nombre": "Posadas"}, {"nombre": "Oberá"}, {"nombre": "Posadas"}]
}


def api_responde(datos):
    """Reemplaza la llamada HTTP. Ningún test toca la red: en CI no hay."""
    return patch.object(georef, "_pedir", return_value=datos)


def api_caida():
    return patch.object(georef, "_pedir", return_value=None)


# ---------------------------------------------------------------------------
# Provincias
# ---------------------------------------------------------------------------


def test_las_provincias_salen_de_la_api_ordenadas():
    with api_responde(RESPUESTA_PROVINCIAS):
        assert georef.obtener_provincias() == ["Buenos Aires", "Corrientes", "Misiones"]


def test_la_segunda_consulta_sale_de_la_cache():
    """No se castiga a un servicio público gratuito con una consulta por visita."""
    with api_responde(RESPUESTA_PROVINCIAS) as pedir:
        georef.obtener_provincias()
        georef.obtener_provincias()
        georef.obtener_provincias()

    assert pedir.call_count == 1


def test_si_la_api_no_responde_se_usa_el_respaldo_local():
    """El registro no puede depender de que un tercero esté en línea."""
    with api_caida():
        provincias = georef.obtener_provincias()

    assert len(provincias) == 24
    assert "Misiones" in provincias


def test_el_respaldo_se_cachea_por_menos_tiempo_que_la_api():
    """Si el servicio vuelve enseguida, no seguimos un día con la foto vieja."""
    with api_caida(), patch.object(integraciones.cache, "set") as guardar:
        georef.obtener_provincias()

    _, _, vigencia = guardar.call_args.args
    assert vigencia == integraciones.CACHE_TRAS_FALLA_SEGUNDOS
    assert vigencia < settings.GEOREF_CACHE_SEGUNDOS


def test_un_error_de_red_no_se_propaga():
    """`pedir_json` traga la excepción: la pantalla tiene que renderizar igual."""
    with patch.object(integraciones, "urlopen", side_effect=OSError("sin red")):
        assert integraciones.pedir_json("https://ejemplo.test", timeout=1) is None


def test_el_respaldo_versionado_tiene_las_veinticuatro_jurisdicciones():
    datos = json.loads(georef.RUTA_RESPALDO.read_text(encoding="utf-8"))

    assert len(datos["provincias"]) == 24
    assert "Ciudad Autónoma de Buenos Aires" in datos["provincias"]


# ---------------------------------------------------------------------------
# Localidades
# ---------------------------------------------------------------------------


def test_las_localidades_se_devuelven_sin_repetir_y_ordenadas():
    with api_responde(RESPUESTA_LOCALIDADES):
        assert georef.obtener_localidades("Misiones") == ["Oberá", "Posadas"]


def test_sin_provincia_no_se_consulta_la_api():
    with api_responde(RESPUESTA_LOCALIDADES) as pedir:
        assert georef.obtener_localidades("") == []

    assert pedir.call_count == 0


def test_si_la_api_no_responde_las_localidades_quedan_vacias():
    """Se pierde la sugerencia, no la posibilidad de escribir la localidad."""
    with api_caida():
        assert georef.obtener_localidades("Misiones") == []


def test_la_cache_de_localidades_es_por_provincia():
    with api_responde(RESPUESTA_LOCALIDADES) as pedir:
        georef.obtener_localidades("Misiones")
        georef.obtener_localidades("Misiones")
        georef.obtener_localidades("Corrientes")

    assert pedir.call_count == 2


# ---------------------------------------------------------------------------
# Endpoint que consume el formulario
# ---------------------------------------------------------------------------


def test_el_endpoint_de_localidades_es_publico(client):
    """El registro es público (CU-CLI-ALT): pedir localidades no puede exigir sesión."""
    with api_responde(RESPUESTA_LOCALIDADES):
        respuesta = client.get(reverse("core:localidades"), {"provincia": "Misiones"})

    assert respuesta.status_code == 200
    assert respuesta.json() == {"localidades": ["Oberá", "Posadas"]}


def test_el_endpoint_sin_provincia_devuelve_lista_vacia(client):
    respuesta = client.get(reverse("core:localidades"))

    assert respuesta.status_code == 200
    assert respuesta.json() == {"localidades": []}


# ---------------------------------------------------------------------------
# Comando de sincronización
# ---------------------------------------------------------------------------


def test_el_comando_reescribe_el_respaldo(tmp_path):
    destino = tmp_path / "georef.json"

    with (
        api_responde(RESPUESTA_PROVINCIAS),
        patch.object(georef, "RUTA_RESPALDO", destino),
    ):
        call_command("sincronizar_georef")

    assert json.loads(destino.read_text(encoding="utf-8")) == {
        "provincias": ["Buenos Aires", "Corrientes", "Misiones"]
    }


def test_el_comando_no_pisa_el_respaldo_si_la_api_falla(tmp_path):
    """Un respaldo vacío es peor que uno viejo: deja el formulario sin provincias."""
    destino = tmp_path / "georef.json"
    destino.write_text('{"provincias": ["Misiones"]}', encoding="utf-8")

    with api_caida(), patch.object(georef, "RUTA_RESPALDO", destino):
        with pytest.raises(CommandError):
            call_command("sincronizar_georef")

    assert json.loads(destino.read_text(encoding="utf-8")) == {"provincias": ["Misiones"]}
