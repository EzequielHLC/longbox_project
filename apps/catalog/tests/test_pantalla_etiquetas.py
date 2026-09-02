"""La pantalla de etiquetas, que salió de Parámetros globales.

Se separó por una razón de escala, no de prolijidad: los otros catálogos de
parámetros son cerrados y chicos —nueve tipos, siete formatos, un puñado de
editoriales— y se tocan una vez por semestre. Las etiquetas son el único catálogo
abierto: crecen con cada franquicia, género y colección nueva.

Un catálogo que crece necesita buscador, y un buscador dentro de una pantalla que
tiene otras cinco secciones filtra la pantalla equivocada.
"""

import pytest
from django.urls import reverse

from apps.accounts.tests.factories import UsuarioFactory
from apps.catalog.models import Etiqueta, GrupoEtiqueta
from apps.catalog.tests.factories import (
    EtiquetaFactory,
    GrupoEtiquetaFactory,
    ProductoFactory,
)

pytestmark = pytest.mark.django_db

URL = reverse("catalog:etiquetas")


# ---------------------------------------------------------------------------
# La pantalla
# ---------------------------------------------------------------------------


def test_lista_las_etiquetas_agrupadas(client_admin):
    """Agrupadas porque es como se piensan y como se eligen: nadie busca "una
    etiqueta", busca una franquicia o un género."""
    grupo = GrupoEtiquetaFactory(nombre="Franquicia de prueba")
    EtiquetaFactory(nombre="Berserk de prueba", grupo=grupo)

    contenido = client_admin.get(URL).content.decode()

    assert "Franquicia de prueba" in contenido
    assert "Berserk de prueba" in contenido


def test_muestra_cuantos_productos_usan_cada_etiqueta(client_admin):
    """Es el dato que decide si una etiqueta se puede desactivar sin romper nada."""
    etiqueta = EtiquetaFactory(nombre="Seinen de prueba")
    ProductoFactory().etiquetas.add(etiqueta)

    contexto = client_admin.get(URL).context
    visibles = [e for g in contexto["grupos"] for e in g.etiquetas_visibles]

    assert next(e for e in visibles if e.nombre == "Seinen de prueba").cantidad_productos == 1


def test_cada_etiqueta_enlaza_a_su_edicion(client_admin):
    etiqueta = EtiquetaFactory(nombre="Shonen de prueba")

    contenido = client_admin.get(URL).content.decode()

    assert reverse("catalog:etiqueta_editar", args=[etiqueta.pk]) in contenido


def test_un_grupo_inactivo_se_marca(client_admin):
    """Desactivarlo saca del alta a todas sus etiquetas, así que tiene que verse."""
    GrupoEtiquetaFactory(nombre="Grupo apagado", activo=False)

    contenido = client_admin.get(URL).content.decode()

    assert "Grupo apagado" in contenido
    assert "Inactivo" in contenido


def test_sin_grupos_avisa_que_no_se_puede_cargar_ninguna(client_admin):
    """Toda etiqueta pertenece a un grupo. Enterarse en el formulario, con el
    nombre ya escrito, es tarde."""
    Etiqueta.objects.all().delete()
    GrupoEtiqueta.objects.all().delete()

    contenido = client_admin.get(URL).content.decode()

    assert "todavía no hay ninguno" in contenido


# ---------------------------------------------------------------------------
# El buscador
# ---------------------------------------------------------------------------


def test_el_buscador_filtra(client_admin):
    grupo = GrupoEtiquetaFactory(nombre="Grupo de prueba")
    EtiquetaFactory(nombre="Berserk de prueba", grupo=grupo)
    EtiquetaFactory(nombre="Vagabond de prueba", grupo=grupo)

    contenido = client_admin.get(URL, {"q": "berserk"}).content.decode()

    assert "Berserk de prueba" in contenido
    assert "Vagabond de prueba" not in contenido


def test_un_grupo_sin_coincidencias_no_se_dibuja(client_admin):
    """Con el buscador escrito, una lista de encabezados vacíos es ruido que hay
    que saltear para llegar al único resultado."""
    otro = GrupoEtiquetaFactory(nombre="Grupo vacio de prueba")
    EtiquetaFactory(nombre="Nada que ver", grupo=otro)
    EtiquetaFactory(nombre="Berserk de prueba", grupo=GrupoEtiquetaFactory(nombre="Con resultado"))

    contenido = client_admin.get(URL, {"q": "berserk"}).content.decode()

    assert "Con resultado" in contenido
    assert "Grupo vacio de prueba" not in contenido


def test_sin_coincidencias_lo_dice(client_admin):
    respuesta = client_admin.get(URL, {"q": "no-existe-nada-asi"})

    assert "Ninguna etiqueta coincide" in respuesta.content.decode()


def test_el_buscador_en_vivo_devuelve_solo_el_fragmento(client_admin):
    """`?parcial=1` reemplaza la zona de resultados sin recargar la pantalla."""
    contenido = client_admin.get(URL, {"parcial": "1"}).content.decode()

    assert "<html" not in contenido


# ---------------------------------------------------------------------------
# Permisos (RNF-03)
# ---------------------------------------------------------------------------


def test_el_cajero_no_administra_etiquetas(client):
    client.force_login(UsuarioFactory(rol="cajero"))

    assert client.get(URL).status_code == 403


def test_sin_sesion_redirige_al_login(client):
    assert client.get(URL).status_code == 302


# ---------------------------------------------------------------------------
# Los formularios vuelven acá, no a parámetros
# ---------------------------------------------------------------------------


def test_el_alta_de_etiqueta_vuelve_a_esta_pantalla(client_admin):
    grupo = GrupoEtiquetaFactory(nombre="Destino de prueba")

    respuesta = client_admin.post(
        reverse("catalog:etiqueta_crear"),
        {"nombre": "Nueva de prueba", "grupo": grupo.pk, "activa": "on"},
    )

    assert respuesta.status_code == 302
    assert respuesta.url == URL


def test_el_alta_de_grupo_vuelve_a_esta_pantalla(client_admin):
    respuesta = client_admin.post(
        reverse("catalog:grupo_etiqueta_crear"),
        {"nombre": "Grupo nuevo de prueba", "activo": "on"},
    )

    assert respuesta.status_code == 302
    assert respuesta.url == URL
