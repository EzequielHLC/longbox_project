"""Plan 16, segunda parte: toda modificación deja qué se cambió y cómo estaba antes.

`CO-206` presenta el valor anterior y el nuevo por separado; las imágenes
reemplazadas se conservan para que el log las muestre (B-16-005). Las imágenes
se escriben en una carpeta temporal: ninguna prueba toca `media/`.
"""

import ast
from datetime import date
from decimal import Decimal
from io import BytesIO
from pathlib import Path

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from PIL import Image

from apps.catalog.views import _cambios_del_modelo
from apps.core import cambios, contenido
from apps.core.models import Banner, ContenidoFAQ, IdentidadVisual, RegistroAuditoria

pytestmark = pytest.mark.django_db

RAIZ = Path(__file__).resolve().parents[3]


@pytest.fixture(autouse=True)
def media_temporal(settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path
    return tmp_path


def imagen(nombre="foto.png", tamano=(1200, 675), color=(200, 30, 30)):
    salida = BytesIO()
    Image.new("RGB", tamano, color).save(salida, "PNG")
    return SimpleUploadedFile(nombre, salida.getvalue(), content_type="image/png")


def detalle(client_admin, registro):
    return client_admin.get(reverse("core:auditoria_detalle", args=[registro.pk])).content.decode()


IDENTIDAD = {
    "nombre_tienda": "Akiba Cómics",
    "correo_contacto": "hola@akiba.test",
    "telefono": "",
    "instagram": "",
    "facebook": "",
    "tiktok": "",
    "x_twitter": "",
    "color_primario": "#FF6A13",
    "color_secundario": "#444444",
    "color_acento": "#AA0000",
    "tipo_fondo": "color",
    "color_fondo": "#FAFAFA",
}


# ---------------------------------------------------------------------------
# CO-206 · el detalle
# ---------------------------------------------------------------------------


def test_CO206_el_detalle_muestra_que_se_cambio_y_como_estaba_antes(client_admin, administrador):
    registro = RegistroAuditoria.registrar(
        accion=RegistroAuditoria.PARAMETRO_MODIFICADO,
        actor=administrador,
        cambios=[("margen global", "40 %", "45 %")],
    )

    pagina = detalle(client_admin, registro)

    assert "Cómo estaba antes" in pagina and "Cómo quedó" in pagina
    assert "<td><strong>Margen global</strong></td>" in pagina
    assert 'data-rotulo="Cómo estaba antes">40 %</td>' in pagina
    assert 'data-rotulo="Cómo quedó">45 %</td>' in pagina
    # El detalle se arma de los cambios cuando el sitio no escribe uno propio.
    assert registro.detalle == "margen global: «40 %» → «45 %»"


def test_CO206_una_imagen_se_muestra_como_estaba_antes(client_admin, media_temporal):
    client_admin.post(reverse("core:banner_crear"), {"imagen": imagen("a.png")})
    banner = Banner.objects.get()
    vieja = banner.imagen.name

    client_admin.post(
        reverse("core:banner_editar", args=[banner.pk]),
        {"numero": "1", "imagen": imagen("b.png", color=(10, 10, 200))},
    )

    registro = RegistroAuditoria.objects.get(accion=RegistroAuditoria.MODIFICACION_BANNER)
    pagina = detalle(client_admin, registro)
    banner.refresh_from_db()
    assert f'src="/media/{vieja}"' in pagina
    assert f'src="/media/{banner.imagen.name}"' in pagina
    assert (media_temporal / vieja).exists()


def test_CO206_una_entrada_anterior_sin_cambios_se_sigue_viendo_por_su_detalle(
    client_admin, administrador
):
    """Postcondición negativa: el log es inmutable y las entradas viejas no se reescriben."""
    registro = RegistroAuditoria.registrar(
        accion=RegistroAuditoria.MODIFICACION_CATALOGO,
        actor=administrador,
        detalle="Editorial «Ivrea»: nombre: «Ivra» → «Ivrea»",
    )

    pagina = detalle(client_admin, registro)

    assert registro.cambios == []
    assert "«Ivra» → «Ivrea»" in pagina
    assert "Cómo estaba antes" not in pagina


def test_CO206_el_cajero_no_ve_el_detalle_por_la_direccion_real(client, cajero, administrador):
    registro = RegistroAuditoria.registrar(
        accion=RegistroAuditoria.PARAMETRO_MODIFICADO,
        actor=administrador,
        cambios=[("margen global", "40 %", "45 %")],
    )
    client.force_login(cajero)

    respuesta = client.get(reverse("core:auditoria_detalle", args=[registro.pk]))

    assert respuesta.status_code == 403
    assert "40 %" not in respuesta.content.decode()


# ---------------------------------------------------------------------------
# Lo que antes se perdía
# ---------------------------------------------------------------------------


def test_CO135_la_faq_guarda_el_contenido_anterior_entero(administrador):
    contenido.publicar_faq("# Envíos\n\nTardan tres días.", actor=administrador)

    contenido.publicar_faq("# Envíos\n\nTardan dos días.", actor=administrador)

    registro = RegistroAuditoria.objects.filter(accion=RegistroAuditoria.PUBLICACION_FAQ).first()
    assert registro.cambios == [
        {
            "campo": "contenido de la FAQ",
            "antes": "# Envíos\n\nTardan tres días.",
            "despues": "# Envíos\n\nTardan dos días.",
        }
    ]
    assert ContenidoFAQ.obtener().contenido == "# Envíos\n\nTardan dos días."


def test_CO131_reemplazar_el_logo_conserva_el_anterior_en_el_log(client_admin, media_temporal):
    client_admin.post(
        reverse("core:identidad_visual"),
        {**IDENTIDAD, "logo_nuevo": imagen("logo.png", (400, 400))},
    )
    viejo = IdentidadVisual.obtener().logo.name

    client_admin.post(
        reverse("core:identidad_visual"),
        {**IDENTIDAD, "logo_nuevo": imagen("otro.png", (400, 400), color=(0, 120, 0))},
    )

    nuevo = IdentidadVisual.obtener().logo.name
    registro = RegistroAuditoria.objects.filter(
        accion=RegistroAuditoria.MODIFICACION_IDENTIDAD_VISUAL
    ).first()
    assert nuevo != viejo
    assert {"campo": "logo", "antes": viejo, "despues": nuevo, "imagen": True} in registro.cambios
    assert (media_temporal / viejo).exists()


def test_CO131_un_color_cambiado_queda_con_su_valor_anterior(client_admin):
    client_admin.post(reverse("core:identidad_visual"), {**IDENTIDAD, "color_primario": "#1A2B3C"})

    registro = RegistroAuditoria.objects.get(accion=RegistroAuditoria.MODIFICACION_IDENTIDAD_VISUAL)
    primario = next(c for c in registro.cambios if c["campo"] == "color primario")
    assert primario == {"campo": "color primario", "antes": "#FF6A13", "despues": "#1A2B3C"}


def test_la_clave_del_modelo_nunca_entra_en_el_log():
    registro = _cambios_del_modelo(
        ("modo", "dirección", "modelo"),
        ("Local", "http://a", "qwen"),
        ("Local", "http://b", "qwen"),
        "clave de la API",
    )

    assert registro == [
        ("dirección", "http://a", "http://b"),
        ("clave de la API", "(oculta)", "reemplazada"),
    ]


def test_los_valores_se_guardan_como_texto():
    lista = cambios.a_lista(
        {"precio": (Decimal("1500.50"), None), "fecha": (date(2026, 11, 17), "")}
    )

    assert lista == [
        {"campo": "precio", "antes": "1500.50", "despues": ""},
        {"campo": "fecha", "antes": "2026-11-17", "despues": ""},
    ]


# ---------------------------------------------------------------------------
# Ningún sitio que modifica escribe sólo el texto
# ---------------------------------------------------------------------------

ACCIONES_QUE_MODIFICAN = {
    "MODIFICACION_USUARIO",
    "MODIFICACION_DATOS_CLIENTE",
    "CAMBIO_CORREO",
    "MODIFICACION_PRODUCTO",
    "PARAMETRO_MODIFICADO",
    "MODIFICACION_PROVEEDOR",
    "MODIFICACION_CATALOGO",
    "MODIFICACION_PRECIO_REFERENCIA",
    "PUBLICACION_FAQ",
    "MODIFICACION_IDENTIDAD_VISUAL",
    "MODIFICACION_BANNER",
    "MODIFICACION_OFERTA",
    "MODIFICACION_SECCIONES_PORTADA",
    "AVANCE_ESTADO_PEDIDO",
    "PLAZO_RETENCION",
    "CANALES_DE_AVISO",
    "AJUSTE_PUNTOS",
}


def _llamadas_a_registrar():
    for archivo in (RAIZ / "apps").rglob("*.py"):
        if "tests" in archivo.parts or "migrations" in archivo.parts:
            continue
        arbol = ast.parse(archivo.read_text(encoding="utf-8"))
        for nodo in ast.walk(arbol):
            if not (
                isinstance(nodo, ast.Call)
                and isinstance(nodo.func, ast.Attribute)
                and nodo.func.attr == "registrar"
                and isinstance(nodo.func.value, ast.Name)
                and nodo.func.value.id == "RegistroAuditoria"
            ):
                continue
            accion = next((k.value for k in nodo.keywords if k.arg == "accion"), None)
            if accion is None and nodo.args:
                accion = nodo.args[0]
            if isinstance(accion, ast.Attribute):
                yield archivo, nodo, accion.attr


def test_toda_modificacion_registra_como_estaba_antes():
    sin_cambios = [
        f"{archivo.relative_to(RAIZ)}:{nodo.lineno} ({accion})"
        for archivo, nodo, accion in _llamadas_a_registrar()
        if accion in ACCIONES_QUE_MODIFICAN and not any(k.arg == "cambios" for k in nodo.keywords)
    ]

    assert sin_cambios == []


def test_el_recorrido_encuentra_los_sitios_que_modifican():
    """Que la prueba anterior no pase por no encontrar nada."""
    encontradas = {accion for _, _, accion in _llamadas_a_registrar()}

    assert ACCIONES_QUE_MODIFICAN <= encontradas
