"""Reglas que tienen que cumplir todas las plantillas del proyecto."""

import re
from pathlib import Path

import pytest
from django.conf import settings
from django.urls import reverse

# Django lexea las plantillas con `({%.*?%}|{{.*?}}|{#.*?#})` y **sin**
# `re.DOTALL`: el punto no cruza saltos de línea. Un comentario `{# … #}` de
# dos o más líneas no llega a reconocerse como token y termina impreso tal cual
# en la pantalla, a la vista del usuario. Para varias líneas va `comment`.
COMENTARIO_MULTILINEA = re.compile(r"\{#(?:(?!#\})[^\n])*\n")


def plantillas_del_proyecto():
    raices = [Path(settings.BASE_DIR) / "templates", Path(settings.BASE_DIR) / "apps"]
    return sorted(archivo for raiz in raices for archivo in raiz.rglob("*.html"))


def test_hay_plantillas_para_revisar():
    """Si el recorrido dejara de encontrar archivos, el test de abajo pasaría solo."""
    assert len(plantillas_del_proyecto()) > 10


def test_ninguna_plantilla_usa_comentarios_de_varias_lineas():
    culpables = [
        f"{archivo.relative_to(settings.BASE_DIR)}"
        for archivo in plantillas_del_proyecto()
        if COMENTARIO_MULTILINEA.search(archivo.read_text(encoding="utf-8"))
    ]

    assert not culpables, (
        "Estas plantillas tienen un comentario {# … #} de más de una línea, que Django no "
        f"reconoce y termina imprimiendo en pantalla: {culpables}. Usar el tag `comment`."
    )


@pytest.mark.django_db
def test_las_pantallas_publicas_se_renderizan_sin_sesion(client):
    """Humo: las tres pantallas públicas cargan enteras para un visitante."""
    for nombre in ["accounts:login", "accounts:registro_cliente", "core:terminos"]:
        respuesta = client.get(reverse(nombre))

        assert respuesta.status_code == 200, nombre
        # Si se colara un comentario sin cerrar, el `{#` saldría en el HTML.
        assert "{#" not in respuesta.content.decode(), nombre
