"""Catálogo de códigos telefónicos de país."""

import json
from unittest.mock import patch

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError

from apps.core import integraciones, paises

RESPUESTA = {
    "error": False,
    "data": [
        {"name": "Argentina", "code": "AR", "dial_code": "+54"},
        {"name": "Brazil", "code": "BR", "dial_code": "+55"},
        # El servicio devuelve algunos con el área adentro: el código de país
        # de E.164 es solo el primer grupo.
        {"name": "AmericanSamoa", "code": "AS", "dial_code": "+1 684"},
        # Y alguna fila rota, que no tiene que romper el catálogo entero.
        {"name": "Ninguno", "code": "XX", "dial_code": None},
    ],
}


def api_responde(datos):
    return patch.object(integraciones, "pedir_json", return_value=datos)


def api_caida():
    return patch.object(integraciones, "pedir_json", return_value=None)


def test_los_paises_salen_de_la_api_ordenados_por_nombre():
    with api_responde(RESPUESTA):
        assert paises.obtener_paises() == [
            ["+1", "AmericanSamoa (+1)"],
            ["+54", "Argentina (+54)"],
            ["+55", "Brazil (+55)"],
        ]


def test_una_fila_sin_codigo_se_descarta_sin_romper_el_resto():
    with api_responde(RESPUESTA):
        codigos = [codigo for codigo, _ in paises.obtener_paises()]

    assert "Ninguno" not in str(codigos)
    assert len(codigos) == 3


def test_el_codigo_se_recorta_al_primer_grupo_de_digitos():
    """ "+1 684" es Estados Unidos con un área adentro: el país es "+1"."""
    with api_responde(RESPUESTA):
        etiquetas = dict((etiqueta, codigo) for codigo, etiqueta in paises.obtener_paises())

    assert etiquetas["AmericanSamoa (+1)"] == "+1"


def test_una_respuesta_con_error_se_trata_como_caida():
    with api_responde({"error": True, "data": []}):
        assert paises.descargar_paises() == []


def test_la_segunda_consulta_sale_de_la_cache():
    with api_responde(RESPUESTA) as pedir:
        paises.obtener_paises()
        paises.obtener_paises()

    assert pedir.call_count == 1


def test_si_la_api_no_responde_se_usa_el_respaldo_local():
    with api_caida():
        catalogo = paises.obtener_paises()

    codigos = [codigo for codigo, _ in catalogo]
    assert "+54" in codigos
    assert len(codigos) > 100


def test_todos_los_codigos_del_respaldo_entran_en_el_campo():
    """`Usuario.telefono_pais` tiene `max_length=4`: "+999" es el tope."""
    catalogo = json.loads(paises.RUTA_RESPALDO.read_text(encoding="utf-8"))["paises"]

    assert all(len(codigo) <= 4 for codigo, _ in catalogo)
    assert all(codigo.startswith("+") for codigo, _ in catalogo)


def test_el_comando_reescribe_el_respaldo(tmp_path):
    destino = tmp_path / "paises.json"

    with api_responde(RESPUESTA), patch.object(paises, "RUTA_RESPALDO", destino):
        call_command("sincronizar_paises")

    guardado = json.loads(destino.read_text(encoding="utf-8"))
    assert ["+54", "Argentina (+54)"] in guardado["paises"]


def test_el_comando_no_pisa_el_respaldo_si_la_api_falla(tmp_path):
    destino = tmp_path / "paises.json"
    destino.write_text('{"paises": [["+54", "Argentina (+54)"]]}', encoding="utf-8")

    with api_caida(), patch.object(paises, "RUTA_RESPALDO", destino):
        with pytest.raises(CommandError):
            call_command("sincronizar_paises")

    assert json.loads(destino.read_text(encoding="utf-8"))["paises"] == [["+54", "Argentina (+54)"]]
