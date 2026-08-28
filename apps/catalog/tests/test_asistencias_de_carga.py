"""Las ayudas que la pantalla de carga pide al servidor mientras se escribe.

Son dos: la consulta del precio de referencia —que es lo que hace que el precio
se pre-complete al elegir la clasificación— y el alta de editorial sin abandonar
el lote. Las dos existen para no perder lo escrito: mandar a otra pantalla a
quien tiene medio lote cargado termina en un lote cargado mal "para no volver a
empezar".

Las etiquetas **no** tienen atajo, y está explicado en `CatalogoRapidoView`: el
atajo agrega una opción a un `<select>` y las etiquetas son casillas agrupadas.
"""

import pytest
from django.urls import reverse

from apps.accounts.tests.factories import UsuarioFactory
from apps.catalog.models import Editorial
from apps.catalog.tests.factories import (
    EditorialFactory,
    FormatoFactory,
    PrecioReferenciaFactory,
    TipoFactory,
)
from apps.core.models import RegistroAuditoria

pytestmark = pytest.mark.django_db

URL_PRECIO = reverse("catalog:precio_referencia")
URL_EDITORIAL = reverse("catalog:editorial_rapida")


# ---------------------------------------------------------------------------
# Precio de referencia
# ---------------------------------------------------------------------------


def test_devuelve_el_precio_de_la_combinacion(client_admin):
    referencia = PrecioReferenciaFactory(pvp="12500")

    respuesta = client_admin.get(
        URL_PRECIO,
        {
            "editorial": referencia.editorial.pk,
            "tipo": referencia.tipo.pk,
            "formato": referencia.formato.pk,
        },
    )

    # Como texto y no como número: en JSON un decimal viaja como coma flotante,
    # y de este lado hay dinero.
    assert respuesta.json() == {"pvp": "12500.00"}


def test_una_combinacion_sin_precio_devuelve_nulo(client_admin):
    respuesta = client_admin.get(
        URL_PRECIO,
        {
            "editorial": EditorialFactory().pk,
            "tipo": TipoFactory(nombre="Manga").pk,
            "formato": FormatoFactory(nombre="B6").pk,
        },
    )

    assert respuesta.json() == {"pvp": None}


def test_cambiar_solo_el_formato_cambia_el_precio(client_admin):
    """Es la razón de ser de la consulta: el tamaño es lo que fija el precio."""
    editorial = EditorialFactory()
    tipo = TipoFactory(nombre="Manga")
    b6 = FormatoFactory(nombre="B6")
    deluxe = FormatoFactory(nombre="Deluxe")
    PrecioReferenciaFactory(editorial=editorial, tipo=tipo, formato=b6, pvp="12500")
    PrecioReferenciaFactory(editorial=editorial, tipo=tipo, formato=deluxe, pvp="28000")

    comun = {"editorial": editorial.pk, "tipo": tipo.pk}
    assert client_admin.get(URL_PRECIO, {**comun, "formato": b6.pk}).json()["pvp"] == "12500.00"
    assert client_admin.get(URL_PRECIO, {**comun, "formato": deluxe.pk}).json()["pvp"] == "28000.00"


@pytest.mark.parametrize("basura", ["", "abc", "-1", "999999"])
def test_un_parametro_invalido_no_rompe_la_consulta(client_admin, basura):
    respuesta = client_admin.get(
        URL_PRECIO, {"editorial": basura, "tipo": basura, "formato": basura}
    )

    assert respuesta.status_code == 200
    assert respuesta.json() == {"pvp": None}


def test_la_consulta_de_precios_no_se_abre_sin_ser_administrador(client, cajero):
    client.force_login(cajero)

    assert client.get(URL_PRECIO).status_code == 403


# ---------------------------------------------------------------------------
# Alta rápida de editorial
# ---------------------------------------------------------------------------


def test_crea_la_editorial_y_devuelve_su_identificador(client_admin):
    respuesta = client_admin.post(URL_EDITORIAL, {"nombre": "Ivrea", "activa": "on"})

    assert respuesta.status_code == 200
    editorial = Editorial.objects.get(nombre="Ivrea")
    assert respuesta.json() == {"id": editorial.pk, "nombre": "Ivrea"}


def test_el_alta_rapida_normaliza_igual_que_la_pantalla_completa(client_admin):
    """Los dos caminos crean lo mismo, así que usan el mismo formulario: si
    tuvieran reglas distintas, el atajo sería la puerta para meter duplicados.
    """
    client_admin.post(URL_EDITORIAL, {"nombre": "  Ovni   Press ", "activa": "on"})

    assert Editorial.objects.get().nombre == "Ovni Press"


def test_el_alta_rapida_rechaza_una_editorial_repetida(client_admin):
    EditorialFactory(nombre="Ivrea")

    respuesta = client_admin.post(URL_EDITORIAL, {"nombre": "IVREA", "activa": "on"})

    assert respuesta.status_code == 400
    assert "Ivrea" in respuesta.json()["errores"][0]
    assert Editorial.objects.count() == 1


def test_el_alta_rapida_rechaza_un_nombre_vacio(client_admin):
    respuesta = client_admin.post(URL_EDITORIAL, {"nombre": "  ", "activa": "on"})

    assert respuesta.status_code == 400
    assert not Editorial.objects.exists()


def test_el_alta_rapida_queda_auditada(client_admin, administrador):
    client_admin.post(URL_EDITORIAL, {"nombre": "Ivrea", "activa": "on"})

    registro = RegistroAuditoria.objects.get(accion=RegistroAuditoria.PARAMETRO_MODIFICADO)
    assert registro.actor == administrador
    assert "alta rápida" in registro.detalle


def test_la_editorial_nueva_se_puede_usar_enseguida(client_admin):
    """Sin esto el atajo no serviría de nada: habría que recargar la pantalla y
    perder el lote a medio escribir."""
    client_admin.post(URL_EDITORIAL, {"nombre": "Ivrea", "activa": "on"})
    editorial = Editorial.objects.get(nombre="Ivrea")

    respuesta = client_admin.get(reverse("catalog:lote_nacional"))

    ofrecidas = respuesta.context["cabecera"].fields["editorial"].queryset
    assert editorial in ofrecidas


@pytest.mark.parametrize("rol_sin_permiso", ["cliente", "cajero"])
def test_el_alta_rapida_es_solo_del_administrador(client, rol_sin_permiso):
    client.force_login(UsuarioFactory(rol=rol_sin_permiso))

    assert client.post(URL_EDITORIAL, {"nombre": "Ivrea"}).status_code == 403
    assert not Editorial.objects.exists()


# ---------------------------------------------------------------------------
# Las reglas de tipo que la pantalla necesita para esconder campos
# ---------------------------------------------------------------------------


def test_la_pantalla_recibe_las_banderas_de_cada_tipo(client_admin):
    """Qué muestra cada tipo viaja como dato y no escrito en el JavaScript: es
    la misma bandera —y la misma lista de formatos— que lee el servidor, así los
    dos lados no pueden discrepar."""
    EditorialFactory()

    respuesta = client_admin.get(reverse("catalog:lote_nacional"))

    reglas = respuesta.context["reglas_de_tipo"]
    comic = next(regla for regla in reglas.values() if regla["nombre"] == "Cómic")
    artbook = next(regla for regla in reglas.values() if regla["nombre"] == "Artbook")

    assert comic["usa_formato"] is True
    assert artbook["usa_formato"] is False
    # Y qué formatos aplican a cada uno, que es lo que recorta el desplegable.
    assert "formatos" in comic
    assert 'id="reglas-de-tipo"' in respuesta.content.decode()
