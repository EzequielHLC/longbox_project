"""B-01-025: las etiquetas de los grupos «de serie» siguen a la serie entera.

Cambiar «Serie en curso» por «Serie completa» en un tomo la cambia en todos los
tomos de la serie (mismo título, misma editorial), con una sola entrada de
auditoría. Sólo viaja **lo que cambió**, y sólo de los grupos de serie: lo propio
de cada tomo queda.
"""

import pytest
from django.urls import reverse

from apps.catalog import services
from apps.catalog.models import GrupoEtiqueta
from apps.catalog.tests.factories import (
    EditorialFactory,
    EtiquetaFactory,
    GrupoEtiquetaFactory,
    ProductoFactory,
)
from apps.catalog.tests.test_edicion_producto import datos_editoriales
from apps.core.models import RegistroAuditoria

pytestmark = pytest.mark.django_db


@pytest.fixture
def serie():
    ivrea = EditorialFactory(nombre="Ivrea")
    estado = GrupoEtiquetaFactory(nombre="Estado de la serie")
    GrupoEtiqueta.objects.filter(pk=estado.pk).update(de_serie=True)
    genero = GrupoEtiquetaFactory(nombre="Género")
    en_curso = EtiquetaFactory(nombre="Serie en curso", grupo=estado)
    completa = EtiquetaFactory(nombre="Serie completa", grupo=estado)
    accion = EtiquetaFactory(nombre="Acción", grupo=genero)
    tomos = [ProductoFactory(titulo="Berserk", volumen=n, editorial=ivrea) for n in (1, 2, 3)]
    for tomo in tomos:
        tomo.etiquetas.add(en_curso)
    return {
        "tomos": tomos,
        "en_curso": en_curso,
        "completa": completa,
        "accion": accion,
        "ivrea": ivrea,
    }


def guardar(client, producto, etiquetas):
    datos = datos_editoriales(producto)
    datos["etiquetas"] = [etiqueta.pk for etiqueta in etiquetas]
    return client.post(reverse("catalog:producto_editar", args=[producto.pk]), datos, follow=True)


def etiquetas_de(producto):
    return set(producto.etiquetas.values_list("nombre", flat=True))


def test_cambiar_el_estado_en_un_tomo_lo_cambia_en_toda_la_serie(client_admin, serie):
    uno, dos, tres = serie["tomos"]

    respuesta = guardar(client_admin, uno, [serie["completa"]])

    for tomo in (uno, dos, tres):
        assert etiquetas_de(tomo) == {"Serie completa"}
    assert "también en los 2 tomos restantes" in respuesta.content.decode()
    detalle = RegistroAuditoria.objects.get(
        accion=RegistroAuditoria.MODIFICACION_PRODUCTO, objetivo_pk=uno.pk
    ).detalle
    assert "aplicadas a 2 tomo(s) más" in detalle
    # Una sola entrada: los otros tomos no se auditan uno por uno.
    assert not RegistroAuditoria.objects.filter(
        accion=RegistroAuditoria.MODIFICACION_PRODUCTO, objetivo_pk__in=[dos.pk, tres.pk]
    ).exists()


def test_lo_propio_de_cada_tomo_no_viaja(client_admin, serie):
    uno, dos, _ = serie["tomos"]

    guardar(client_admin, uno, [serie["en_curso"], serie["accion"]])

    assert "Acción" in etiquetas_de(uno)
    assert etiquetas_de(dos) == {"Serie en curso"}


def test_sólo_viaja_lo_que_cambió(client_admin, serie):
    uno, dos, _ = serie["tomos"]
    # El tomo 2 ya tenía algo distinto en el grupo de serie: se respeta.
    dos.etiquetas.add(serie["completa"])

    guardar(client_admin, uno, [serie["en_curso"], serie["accion"]])

    assert etiquetas_de(dos) == {"Serie en curso", "Serie completa"}


def test_otra_editorial_no_es_la_misma_serie(client_admin, serie):
    panini = ProductoFactory(
        titulo="Berserk", volumen=1, editorial=EditorialFactory(nombre="Panini")
    )
    panini.etiquetas.add(serie["en_curso"])

    guardar(client_admin, serie["tomos"][0], [serie["completa"]])

    assert etiquetas_de(panini) == {"Serie en curso"}


def test_un_grupo_que_no_es_de_serie_no_se_reparte(serie):
    uno, dos, _ = serie["tomos"]

    assert services.aplicar_a_la_serie(uno, {serie["accion"].pk}, set()) == 0
    assert "Acción" not in etiquetas_de(dos)


def test_sin_otros_tomos_no_hay_nada_que_repartir(serie):
    solo = ProductoFactory(titulo="Akira", volumen=1, editorial=serie["ivrea"])

    assert services.aplicar_a_la_serie(solo, {serie["completa"].pk}, set()) == 0


def test_la_edición_avisa_qué_grupos_son_de_la_serie(client_admin, serie):
    html = client_admin.get(
        reverse("catalog:producto_editar", args=[serie["tomos"][0].pk])
    ).content.decode()

    assert "Estado de la serie" in html.split("son de la serie")[0][-200:]


def test_un_grupo_se_marca_de_serie_desde_su_pantalla_y_se_audita(client_admin):
    grupo = GrupoEtiquetaFactory(nombre="Colección")

    client_admin.post(
        reverse("catalog:grupo_etiqueta_editar", args=[grupo.pk]),
        {"nombre": "Colección", "de_serie": "on"},
    )

    grupo.refresh_from_db()
    assert grupo.de_serie
    assert RegistroAuditoria.objects.filter(detalle__contains="de serie").exists()
