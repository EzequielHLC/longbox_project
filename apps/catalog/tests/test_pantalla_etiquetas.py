"""Las pantallas de etiquetas: los grupos (CU-CAT-GRC) y las etiquetas de cada
grupo (CU-CAT-ETC).

Las etiquetas salieron de Parámetros globales por una razón de escala: son el
único catálogo abierto y crecen con cada franquicia, género y colección nueva.
Se operan buscando y no recorriendo (`CO-165`), y por eso se listan por grupo,
paginadas y con buscador.
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

URL_GRUPOS = reverse("catalog:etiquetas")


def url_de(grupo, **parametros):
    url = reverse("catalog:grupo_etiquetas", args=[grupo.pk])
    if parametros:
        url += "?" + "&".join(f"{clave}={valor}" for clave, valor in parametros.items())
    return url


# ---------------------------------------------------------------------------
# Los grupos
# ---------------------------------------------------------------------------


def test_los_grupos_enlazan_a_sus_etiquetas(client_admin):
    grupo = GrupoEtiquetaFactory(nombre="Franquicia de prueba")

    contenido = client_admin.get(URL_GRUPOS).content.decode()

    assert "Franquicia de prueba" in contenido
    assert url_de(grupo) in contenido


def test_un_grupo_inactivo_se_marca(client_admin):
    GrupoEtiquetaFactory(nombre="Grupo apagado", activo=False)

    contenido = client_admin.get(URL_GRUPOS).content.decode()

    assert "Grupo apagado" in contenido
    assert "marca-estado--apagado" in contenido


def test_sin_grupos_ofrece_el_alta(client_admin):
    Etiqueta.objects.all().delete()
    GrupoEtiqueta.objects.all().delete()

    contenido = client_admin.get(URL_GRUPOS).content.decode()

    assert "Todavía no hay grupos de etiquetas registrados" in contenido
    assert reverse("catalog:grupo_etiqueta_crear") in contenido


# ---------------------------------------------------------------------------
# Las etiquetas de un grupo
# ---------------------------------------------------------------------------


def test_lista_las_etiquetas_del_grupo_y_no_las_de_otro(client_admin):
    grupo = GrupoEtiquetaFactory(nombre="Franquicia de prueba")
    EtiquetaFactory(nombre="Berserk de prueba", grupo=grupo)
    EtiquetaFactory(nombre="De otro grupo", grupo=GrupoEtiquetaFactory(nombre="Otro"))

    contenido = client_admin.get(url_de(grupo)).content.decode()

    assert "Berserk de prueba" in contenido
    assert "De otro grupo" not in contenido


def test_muestra_cuantos_productos_usan_cada_etiqueta(client_admin):
    etiqueta = EtiquetaFactory(nombre="Usada de prueba", grupo=GrupoEtiquetaFactory(nombre="Uso"))
    for _ in range(3):
        ProductoFactory().etiquetas.add(etiqueta)

    respuesta = client_admin.get(url_de(etiqueta.grupo))

    assert respuesta.context["registros"][0].cantidad_productos == 3


def test_cada_etiqueta_enlaza_a_su_modificacion_y_a_su_baja(client_admin):
    etiqueta = EtiquetaFactory(nombre="Con enlace")

    contenido = client_admin.get(url_de(etiqueta.grupo)).content.decode()

    assert reverse("catalog:etiqueta_editar", args=[etiqueta.pk]) in contenido
    assert reverse("catalog:etiqueta_baja", args=[etiqueta.pk]) in contenido


def test_el_buscador_filtra(client_admin):
    grupo = GrupoEtiquetaFactory(nombre="Género de prueba")
    EtiquetaFactory(nombre="Shonen de prueba", grupo=grupo)
    EtiquetaFactory(nombre="Seinen de prueba", grupo=grupo)

    contenido = client_admin.get(url_de(grupo, q="shonen")).content.decode()

    assert "Shonen de prueba" in contenido
    assert "Seinen de prueba" not in contenido


def test_el_filtro_por_estado(client_admin):
    grupo = GrupoEtiquetaFactory(nombre="Con estados")
    EtiquetaFactory(nombre="Viva", grupo=grupo)
    EtiquetaFactory(nombre="Apagada", grupo=grupo, activa=False)

    activas = client_admin.get(url_de(grupo, estado="activos")).content.decode()
    inactivas = client_admin.get(url_de(grupo, estado="inactivos")).content.decode()

    assert "Viva" in activas and "Apagada" not in activas
    assert "Apagada" in inactivas and "Viva" not in inactivas


def test_sin_coincidencias_lo_dice(client_admin):
    grupo = GrupoEtiquetaFactory(nombre="Con una")
    EtiquetaFactory(nombre="Única", grupo=grupo)

    contenido = client_admin.get(url_de(grupo, q="zzz")).content.decode()

    assert "Ninguna etiqueta coincide" in contenido


def test_el_listado_se_pagina_de_a_cincuenta(client_admin):
    """`CO-165` dice «paginado» sin decir cuánto: se toma el tamaño de `CO-205`."""
    grupo = GrupoEtiquetaFactory(nombre="Grande")
    Etiqueta.objects.bulk_create(
        [Etiqueta(nombre=f"Etiqueta {numero:03}", grupo=grupo) for numero in range(55)]
    )

    primera = client_admin.get(url_de(grupo))
    segunda = client_admin.get(url_de(grupo, page=2))

    assert len(primera.context["registros"]) == 50
    assert len(segunda.context["registros"]) == 5


def test_un_grupo_dado_de_baja_lo_avisa_y_no_ofrece_alta(client_admin):
    grupo = GrupoEtiquetaFactory(nombre="Apagado", activo=False)

    contenido = client_admin.get(url_de(grupo)).content.decode()

    assert "el grupo está dado de baja" in contenido
    assert reverse("catalog:etiqueta_crear") not in contenido


# ---------------------------------------------------------------------------
# Acceso y vuelta
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("rol", ["cajero", "cliente"])
def test_solo_el_administrador_las_consulta(client, rol):
    client.force_login(UsuarioFactory(rol=rol))
    grupo = GrupoEtiquetaFactory()

    assert client.get(URL_GRUPOS).status_code == 403
    assert client.get(url_de(grupo)).status_code == 403


def test_sin_sesion_redirige_al_login(client):
    respuesta = client.get(URL_GRUPOS)

    assert respuesta.status_code == 302
    assert reverse("accounts:login") in respuesta["Location"]


def test_el_alta_de_etiqueta_vuelve_a_su_grupo(client_admin):
    grupo = GrupoEtiquetaFactory(nombre="Destino")

    respuesta = client_admin.post(
        reverse("catalog:etiqueta_crear"), {"nombre": "Nueva", "grupo": grupo.pk}
    )

    assert respuesta.status_code == 302
    assert respuesta["Location"] == url_de(grupo)


def test_el_alta_desde_un_grupo_lo_trae_elegido(client_admin):
    grupo = GrupoEtiquetaFactory(nombre="Preelegido")

    respuesta = client_admin.get(reverse("catalog:etiqueta_crear") + f"?grupo={grupo.pk}")

    assert respuesta.context["form"].initial["grupo"] == grupo.pk


def test_el_alta_de_grupo_vuelve_a_los_grupos(client_admin):
    respuesta = client_admin.post(
        reverse("catalog:grupo_etiqueta_crear"), {"nombre": "Edición especial"}
    )

    assert respuesta.status_code == 302
    assert respuesta["Location"] == URL_GRUPOS
