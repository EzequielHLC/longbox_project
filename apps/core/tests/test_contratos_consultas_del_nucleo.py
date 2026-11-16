"""Las consultas del núcleo: `CO-219`, `CO-245`, `CO-246`, `CO-249` y `CO-252`.

Contratos redactados en la versión 14 del documento para pantallas que ya estaban construidas y
probadas por su comportamiento. Una consulta no tiene postcondiciones: su prueba la ejerce por la
dirección real y afirma lo que presenta y que nada cambió (ESPECIFICACION.md, apartado 3).
"""

import pytest
from django.urls import reverse

from apps.catalog.models import Producto
from apps.catalog.tests.factories import ProductoFactory
from apps.core.models import (
    Banner,
    ConfiguracionSistema,
    ContenidoFAQ,
    RegistroAuditoria,
    SeccionPortada,
)

pytestmark = pytest.mark.django_db


def foto():
    """Todo lo que una consulta del núcleo podría tocar."""
    return (
        RegistroAuditoria.objects.count(),
        list(SeccionPortada.objects.order_by("pk").values_list("orden", "activa")),
        Banner.objects.count(),
        ContenidoFAQ.obtener().contenido,
        list(Producto.objects.order_by("pk").values_list("estado", "stock")),
        ConfiguracionSistema.obtener().resumen_enviado_el,
    )


# ---------------------------------------------------------------------------
# CO-219 consultarPanelDeAdministracion
# ---------------------------------------------------------------------------


def test_CO219_el_panel_presenta_ventas_inteligencia_y_pendientes(client_admin):
    contenido = client_admin.get(reverse("core:panel")).content.decode()

    for parte in ("Ventas", "Inteligencia del negocio", "Pedidos", "Cuentas", "Actividad reciente"):
        assert parte in contenido


def test_CO219_consultar_el_panel_no_cambia_nada_ni_se_audita(client_admin):
    ProductoFactory(stock=3)
    antes = foto()

    client_admin.get(reverse("core:panel"))

    assert foto() == antes


@pytest.mark.parametrize("rol", ["cajero", "cliente"])
def test_CO219_el_rol_equivocado_no_ve_el_panel_por_la_direccion_real(client, rol, request):
    client.force_login(request.getfixturevalue(rol))

    assert client.get(reverse("core:panel")).status_code == 403


# ---------------------------------------------------------------------------
# CO-245 consultarPortada
# ---------------------------------------------------------------------------


def test_CO245_la_portada_es_publica_y_presenta_las_secciones_activas_en_su_orden(client):
    respuesta = client.get(reverse("core:tienda"))

    assert respuesta.status_code == 200
    activas = list(
        SeccionPortada.objects.filter(activa=True).order_by("orden").values_list("pk", flat=True)
    )
    mostradas = [getattr(s, "seccion", s).pk for s in respuesta.context["secciones"]]
    assert set(mostradas) <= set(activas)
    assert mostradas == [pk for pk in activas if pk in mostradas]


@pytest.mark.parametrize("con_sesion", [False, True])
def test_CO245_consultar_la_portada_no_cambia_nada(client, cliente, con_sesion):
    ProductoFactory(stock=3)
    if con_sesion:
        client.force_login(cliente)  # el inicio de sesión se audita: va antes de la foto
    antes = foto()

    client.get(reverse("core:tienda"))

    assert foto() == antes


# ---------------------------------------------------------------------------
# CO-246 consultarPreguntasFrecuentes
# ---------------------------------------------------------------------------


def test_CO246_presenta_lo_publicado_sin_sesion(client):
    faq = ContenidoFAQ.obtener()
    faq.contenido = "# Envíos\n\nDespachamos en 48 horas."
    faq.save()

    contenido = client.get(reverse("core:faq")).content.decode()

    assert "Despachamos en 48 horas." in contenido


def test_CO246_A1_sin_contenido_publicado_no_aparece_el_globo_de_ayuda(client):
    faq = ContenidoFAQ.obtener()
    faq.contenido = ""
    faq.save()

    assert 'class="globo-ayuda"' not in client.get(reverse("core:tienda")).content.decode()


def test_CO246_consultar_las_preguntas_no_cambia_nada(client):
    antes = foto()

    client.get(reverse("core:faq"))

    assert foto() == antes


# ---------------------------------------------------------------------------
# CO-249 consultarPoliticaDePrivacidad
# ---------------------------------------------------------------------------


def test_CO249_la_politica_es_publica_y_presenta_sus_cinco_apartados(client):
    respuesta = client.get(reverse("core:politica_privacidad"))

    assert respuesta.status_code == 200
    contenido = respuesta.content.decode()
    for apartado in (
        "Datos que se recogen",
        "Para qué se usan",
        "Conservación y resguardo",
        "Derechos del titular",
        "Contacto",
    ):
        assert apartado in contenido


def test_CO249_consultar_la_politica_no_cambia_nada(client):
    antes = foto()

    client.get(reverse("core:politica_privacidad"))

    assert foto() == antes


# ---------------------------------------------------------------------------
# CO-252 consultarSeccionesDeLaPortada
# ---------------------------------------------------------------------------


def test_CO252_presenta_las_secciones_como_tarjetas_en_su_orden(client_admin):
    respuesta = client_admin.get(reverse("core:secciones_portada"))

    assert respuesta.status_code == 200
    contenido = respuesta.content.decode()
    for seccion in SeccionPortada.objects.order_by("orden"):
        assert seccion.get_tipo_display() in contenido


def test_CO252_consultar_las_secciones_no_cambia_nada(client_admin):
    antes = foto()

    client_admin.get(reverse("core:secciones_portada"))

    assert foto() == antes
