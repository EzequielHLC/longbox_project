"""Los controles de formulario del modo operativo están todos vestidos.

Este archivo existe por un error concreto: la cáscara del backoffice estilaba
`input[type="text"]`, `email` y `password`, y nada más. El día que una pantalla
usó un número, una fecha y un área de texto, los tres salieron con el estilo
claro de la cáscara base —letra blanca sobre fondo blanco— y el problema se
descubrió mirando la pantalla, no corriendo la batería.

La regla que se prueba acá es la que evita que vuelva a pasar: **todo tipo de
control que alguna pantalla operativa dibuje tiene que estar cubierto**. No
alcanza con acordarse; tiene que fallar el test.
"""

import re
from pathlib import Path

import pytest
from django.conf import settings
from django.urls import reverse

from apps.catalog.tests.factories import EditorialFactory

RUTA_CAMPOS = Path(settings.BASE_DIR) / "templates" / "_campos.html"

# Tipos que no se visten con las reglas generales porque tienen su propio
# tratamiento: la casilla se dibuja de cero, el archivo lo reemplaza el
# componente de `_archivo.html`, y los ocultos y los botones no se ven.
TIPOS_CON_TRATAMIENTO_PROPIO = {"hidden", "submit", "button", "reset", "file", "checkbox", "radio"}

# Pantallas operativas representativas: entre las tres aparecen todos los tipos
# de control que el backoffice usa hoy.
PANTALLAS = ["catalog:lote_nacional", "catalog:lote_importado", "accounts:usuario_alta"]


def tipos_cubiertos():
    """Los `input[type="…"]` que `_campos.html` viste, leídos del propio archivo."""
    hoja = RUTA_CAMPOS.read_text(encoding="utf-8")
    return set(re.findall(r'input\[type="([a-z-]+)"\]', hoja))


def tipos_en(html):
    """Los `type` de los `<input>` que una pantalla dibuja de verdad."""
    return {
        tipo
        for etiqueta in re.findall(r"<input\b[^>]*>", html)
        for tipo in re.findall(r'type="([a-z-]+)"', etiqueta)
    }


def test_el_archivo_de_campos_cubre_algo():
    """Si la lectura del archivo dejara de encontrar selectores, el test de
    abajo pasaría solo y no probaría nada."""
    assert len(tipos_cubiertos()) >= 5


@pytest.mark.django_db
@pytest.mark.parametrize("pantalla", PANTALLAS)
def test_ninguna_pantalla_operativa_dibuja_un_control_sin_estilo(client_admin, pantalla):
    EditorialFactory()

    html = client_admin.get(reverse(pantalla)).content.decode()

    sin_vestir = tipos_en(html) - tipos_cubiertos() - TIPOS_CON_TRATAMIENTO_PROPIO
    assert not sin_vestir, (
        f"La pantalla {pantalla} dibuja controles que `_campos.html` no viste: {sin_vestir}. "
        "Sin estilo propio heredan el de la cáscara base y salen en blanco sobre blanco."
    )


@pytest.mark.django_db
def test_la_pantalla_de_alta_usa_los_tipos_que_habian_quedado_sin_estilo(client_admin):
    """El caso que originó el problema: número, fecha y área de texto.

    Si alguna vez dejaran de aparecer en esta pantalla, el test de arriba
    seguiría en verde sin estar mirando nada.
    """
    EditorialFactory()

    html = client_admin.get(reverse("catalog:lote_importado")).content.decode()

    assert {"number", "date"} <= tipos_en(html)
    assert "<textarea" in html


@pytest.mark.django_db
def test_el_area_de_texto_tambien_esta_cubierta(client_admin):
    hoja = RUTA_CAMPOS.read_text(encoding="utf-8")

    assert "textarea" in hoja


@pytest.mark.django_db
@pytest.mark.parametrize("pantalla", PANTALLAS)
def test_las_pantallas_operativas_traen_los_componentes_propios(client_admin, pantalla):
    """El desplegable y el selector de archivo se arman con JavaScript.

    Si la cáscara dejara de incluirlos, los controles nativos del sistema
    operativo aparecerían en medio del sistema sin que nada fallara.
    """
    EditorialFactory()

    html = client_admin.get(reverse(pantalla)).content.decode()

    assert "function mejorarSelects" in html
    assert "function mejorarArchivos" in html


@pytest.mark.django_db
def test_los_campos_obligatorios_se_marcan_solos(client_admin):
    """El asterisco sale de `field.required`, no de un dato escrito a mano."""
    EditorialFactory()

    html = client_admin.get(reverse("catalog:lote_importado")).content.decode()

    assert 'class="ml-0.5 text-signal"' in html
