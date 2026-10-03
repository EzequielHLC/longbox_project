"""Los textos configurables de la portada (B-17-015) y el formato de los importes."""

from decimal import Decimal

import pytest
from django.urls import reverse

from apps.catalog.tests.factories import ProductoFactory
from apps.core.models import IdentidadVisual, RegistroAuditoria
from apps.core.templatetags.moneda import pesos

pytestmark = pytest.mark.django_db

DATOS = {
    "nombre_tienda": "Akiba",
    "correo_contacto": "hola@akiba.test",
    "color_primario": "#FF6A13",
    "color_secundario": "#9A9AA5",
    "color_acento": "#FF6A13",
    "tipo_fondo": "color",
    "color_fondo": "#0A0A0C",
}


@pytest.mark.parametrize(
    ("valor", "esperado"),
    [
        (Decimal("18500.00"), "$ 18.500"),
        (Decimal("24900.5"), "$ 24.900,50"),
        (Decimal("1234.5678"), "$ 1.234,5678"),
        (Decimal("0"), "$ 0"),
        (None, ""),
    ],
)
def test_los_importes_se_escriben_como_en_la_guia(valor, esperado):
    assert pesos(valor) == esperado


def test_la_portada_muestra_los_textos_que_escribe_el_administrador(
    client_admin, client, cliente, administrador
):
    client_admin.post(
        reverse("core:identidad_visual"),
        {
            **DATOS,
            "portada_antetitulo": "Llegó el envío",
            "portada_titulo": "Neón roto",
            "portada_bajada": "Tomos nuevos todas las semanas.",
            "ticker_mensajes": "Envíos a todo el país\n\nFirma de autores el sábado",
            "descripcion_tienda": "La comiquería del barrio.",
        },
    )
    client.force_login(cliente)

    contenido = client.get(reverse("core:tienda")).content.decode()

    for texto in (
        "— Llegó el envío",
        'data-texto="Neón roto"',
        "Tomos nuevos todas las semanas.",
        "<span>Envíos a todo el país</span>",
        "<span>Firma de autores el sábado</span>",
        "La comiquería del barrio.",
    ):
        assert texto in contenido, texto
    detalle = RegistroAuditoria.objects.get(
        accion=RegistroAuditoria.MODIFICACION_IDENTIDAD_VISUAL
    ).detalle
    assert "título de la portada: «Historietas de noche» → «Neón roto»" in detalle


def test_un_texto_vacio_vuelve_a_su_valor_inicial(client_admin):
    client_admin.post(reverse("core:identidad_visual"), {**DATOS, "portada_titulo": "   "})

    assert IdentidadVisual.obtener().portada_titulo == "Historietas de noche"


def test_sin_mensajes_el_ticker_anuncia_lo_ultimo_que_llego(client, cliente):
    ProductoFactory(titulo="Barrio Cero", stock=2)
    client.force_login(cliente)

    contenido = client.get(reverse("core:tienda")).content.decode()

    assert "<span>Llegó Barrio Cero</span>" in contenido
