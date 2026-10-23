"""El mapa de colores de la tienda (plan 00 de interfaz, cuarta parte, A y B; B-17-019).

Lo que se prueba es lo que el Administrador ve cambiar: qué color lleva cada
parte, que el texto encima se calcule por contraste, y que las opciones de cada
rol las decida el servidor y no el desplegable.
"""

import pytest
from django.urls import reverse

from apps.core import colores
from apps.core.models import IdentidadVisual, RegistroAuditoria
from apps.core.tests.test_contratos_17_contenido import DATOS_VALIDOS

pytestmark = pytest.mark.django_db

URL = reverse("core:identidad_visual")
HOJA = reverse("core:tienda_css")


def guardar(client_admin, **cambios):
    return client_admin.post(URL, {**DATOS_VALIDOS, **cambios})


def hoja(client):
    return client.get(HOJA).content.decode()


def test_los_valores_iniciales_reproducen_la_tienda_de_antes(client):
    """Sin tocar el mapa, cada parte lleva el color que llevaba."""
    contenido = hoja(client)

    assert "--rol-boton: var(--tienda-primario);" in contenido
    assert "--rol-enlaces: var(--tienda-acento);" in contenido
    assert "--rol-precios: var(--texto-fuerte);" in contenido
    assert "--rol-titulos: var(--tienda-acento);" in contenido
    assert "--rol-encabezado: var(--tienda-fondo);" in contenido


def test_la_pantalla_muestra_el_mapa_con_las_opciones_de_cada_rol(client_admin):
    respuesta = client_admin.get(URL)

    contenido = respuesta.content.decode()
    assert "Mapa de colores" in contenido
    formulario = respuesta.context["form"]
    assert [c for c, _ in formulario.fields["color_rol_precios"].choices] == [
        colores.NEUTRO,
        colores.PRIMARIO,
        colores.SECUNDARIO,
        colores.ACENTO,
    ]
    assert colores.FONDO in [c for c, _ in formulario.fields["color_rol_encabezado"].choices]
    for rol in colores.ROLES:
        assert f'data-rol-color="{rol.clave}"' in contenido


def test_elegir_un_color_por_rol_cambia_la_tienda_y_queda_auditado(client_admin, client):
    guardar(client_admin, color_rol_precios=colores.ACENTO, color_rol_boton=colores.SECUNDARIO)

    identidad = IdentidadVisual.obtener()
    assert identidad.color_rol_precios == colores.ACENTO
    contenido = hoja(client)
    assert "--rol-precios: var(--tienda-acento);" in contenido
    assert "--rol-boton: var(--tienda-secundario);" in contenido
    detalle = RegistroAuditoria.objects.get(
        accion=RegistroAuditoria.MODIFICACION_IDENTIDAD_VISUAL
    ).detalle
    assert "color de precios: «neutro» → «acento»" in detalle


def test_una_opcion_ajena_al_rol_se_rechaza_en_el_servidor(client_admin):
    """El encabezado no puede ser neutro ni el botón ser el fondo: el desplegable
    no las ofrece, y un envío armado a mano tampoco pasa."""
    respuesta = guardar(client_admin, color_rol_boton=colores.FONDO, nombre_tienda="Otra")

    assert respuesta.status_code == 200
    assert respuesta.context["form"].errors["color_rol_boton"]
    assert IdentidadVisual.obtener().nombre_tienda != "Otra"


def test_un_rol_que_no_viaja_conserva_el_que_tenia(client_admin):
    guardar(client_admin, color_rol_marcas=colores.PRIMARIO)

    guardar(client_admin)

    assert IdentidadVisual.obtener().color_rol_marcas == colores.PRIMARIO


def test_el_texto_encima_de_cada_color_sale_del_contraste(client_admin, client):
    """Primario #1A2B3C es oscuro: el texto del botón va en blanco."""
    guardar(client_admin)

    contenido = hoja(client)

    assert "--rol-boton-sobre: #FFFFFF;" in contenido


def test_un_color_que_no_se_lee_sobre_el_fondo_no_se_usa_como_texto(client_admin, client):
    """Primario #1A2B3C sobre un fondo casi negro no llega a 3:1: el precio va en
    el más legible de noche o blanco, no en el primario."""
    guardar(
        client_admin,
        color_fondo="#0A0A0C",
        color_secundario="#9A9AA5",
        color_acento="#FF6A13",
        color_rol_precios=colores.PRIMARIO,
    )

    contenido = hoja(client)

    assert "--rol-precios: var(--tienda-primario);" in contenido
    assert "--rol-precios-texto: #FFFFFF;" in contenido


def test_el_encabezado_con_color_cambia_el_texto_de_su_zona(client_admin, client):
    guardar(client_admin, color_rol_encabezado=colores.ACENTO)

    contenido = hoja(client)

    assert "--rol-encabezado: var(--tienda-acento);" in contenido
    assert ".encabezado-publico, .pie-publico" in contenido
    assert "--texto: #FFFFFF;" in contenido


def test_con_el_encabezado_en_el_fondo_no_se_toca_su_texto(client):
    assert ".encabezado-publico, .pie-publico" not in hoja(client)


def test_la_hoja_de_componentes_deriva_las_variantes_del_rol():
    """A: el hover y lo presionado salen del color del rol, no de la paleta fija."""
    from pathlib import Path

    from django.conf import settings

    hoja_css = (Path(settings.BASE_DIR) / "static" / "css" / "longbox.css").read_text(
        encoding="utf-8"
    )

    assert "--rol-boton-vivo: color-mix(in oklch, var(--rol-boton)" in hoja_css
    assert "--rol-enlaces-vivo: color-mix(in oklch, var(--rol-enlaces)" in hoja_css
    assert "--acento-vivo: var(--rol-enlaces-vivo);" in hoja_css
    assert ".modo-publico .boton-primario:hover::before { background: var(--rol-boton-vivo); }" in (
        hoja_css
    )
