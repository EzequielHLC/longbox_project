"""Las filas de la portada de la tienda (plan 07, tercera parte; B-07-009).

El Administrador las configura; el Cliente las recorre de costado en la portada.
Cada fila muestra sólo productos visibles en la tienda, de lo más nuevo a lo más
viejo, hasta doce.
"""

import pytest
from django.urls import reverse

from apps.catalog.models import Producto
from apps.catalog.tests.factories import (
    EtiquetaFactory,
    GrupoEtiquetaFactory,
    ProductoFactory,
)
from apps.core.models import FilaPortada, RegistroAuditoria
from apps.core.views_tienda import PRODUCTOS_POR_FILA

pytestmark = pytest.mark.django_db

URL_CONFIGURAR = reverse("core:filas_portada")
URL_PORTADA = reverse("core:tienda")


def formset(*filas, existentes=0):
    datos = {
        "form-TOTAL_FORMS": str(len(filas)),
        "form-INITIAL_FORMS": str(existentes),
        "form-MIN_NUM_FORMS": "0",
        "form-MAX_NUM_FORMS": "1000",
    }
    for indice, fila in enumerate(filas):
        for campo, valor in fila.items():
            datos[f"form-{indice}-{campo}"] = valor
    return datos


@pytest.fixture
def shonen(db):
    return EtiquetaFactory(nombre="Shonen", grupo=GrupoEtiquetaFactory(nombre="Demografía"))


def con_etiqueta(etiqueta, **datos):
    producto = ProductoFactory(stock=3, **datos)
    producto.etiquetas.add(etiqueta)
    return producto


def portada(client, cliente):
    client.force_login(cliente)
    return client.get(URL_PORTADA)


# ---------------------------------------------------------------------------
# Configuración
# ---------------------------------------------------------------------------


def test_el_administrador_agrega_una_fila_de_etiqueta_y_otra_de_grupo(
    client_admin, administrador, shonen
):
    respuesta = client_admin.post(
        URL_CONFIGURAR,
        formset(
            {"origen": f"e:{shonen.pk}", "titulo": "", "orden": "1", "activa": "on"},
            {
                "origen": f"g:{shonen.grupo_id}",
                "titulo": "Por demografía",
                "orden": "2",
                "activa": "on",
            },
        ),
    )

    assert respuesta.status_code == 302
    filas = list(FilaPortada.objects.all())
    assert [(f.etiqueta_id, f.grupo_id, f.titulo_visible) for f in filas] == [
        (shonen.pk, None, "Shonen"),
        (None, shonen.grupo_id, "Por demografía"),
    ]
    registro = RegistroAuditoria.objects.get(accion=RegistroAuditoria.MODIFICACION_FILAS_PORTADA)
    assert registro.actor == administrador
    assert registro.detalle == "ninguna → Shonen · Por demografía"


def test_una_fila_sin_origen_se_rechaza_y_no_se_guarda_nada(client_admin):
    respuesta = client_admin.post(
        URL_CONFIGURAR, formset({"origen": "", "titulo": "Sin origen", "orden": "1"})
    )

    assert respuesta.status_code == 200
    assert not FilaPortada.objects.exists()


def test_eliminar_una_fila(client_admin, shonen):
    fila = FilaPortada.objects.create(etiqueta=shonen, orden=1)

    client_admin.post(
        URL_CONFIGURAR,
        formset(
            {
                "id": str(fila.pk),
                "origen": f"e:{shonen.pk}",
                "orden": "1",
                "activa": "on",
                "DELETE": "on",
            },
            existentes=1,
        ),
    )

    assert not FilaPortada.objects.exists()
    detalle = RegistroAuditoria.objects.get(
        accion=RegistroAuditoria.MODIFICACION_FILAS_PORTADA
    ).detalle
    assert detalle == "Shonen → ninguna"


def test_guardar_sin_cambios_no_audita(client_admin, shonen):
    fila = FilaPortada.objects.create(etiqueta=shonen, orden=1)

    client_admin.post(
        URL_CONFIGURAR,
        formset(
            {"id": str(fila.pk), "origen": f"e:{shonen.pk}", "orden": "1", "activa": "on"},
            existentes=1,
        ),
    )

    assert not RegistroAuditoria.objects.filter(
        accion=RegistroAuditoria.MODIFICACION_FILAS_PORTADA
    ).exists()


@pytest.mark.parametrize("rol", ["cajero", "cliente"])
def test_solo_el_administrador_configura_las_filas(client, request, rol, shonen):
    client.force_login(request.getfixturevalue(rol))

    assert client.get(URL_CONFIGURAR).status_code == 403
    respuesta = client.post(URL_CONFIGURAR, formset({"origen": f"e:{shonen.pk}", "orden": "1"}))
    assert respuesta.status_code == 403
    assert not FilaPortada.objects.exists()


# ---------------------------------------------------------------------------
# La portada
# ---------------------------------------------------------------------------


def test_la_portada_muestra_las_filas_en_su_orden_con_sus_productos(client, cliente, shonen):
    seinen = EtiquetaFactory(nombre="Seinen", grupo=shonen.grupo)
    con_etiqueta(shonen, titulo="Dragon Ball")
    con_etiqueta(seinen, titulo="Berserk")
    FilaPortada.objects.create(grupo=shonen.grupo, titulo="Todas las demografías", orden=2)
    FilaPortada.objects.create(etiqueta=shonen, orden=1)

    respuesta = portada(client, cliente)

    filas = respuesta.context["filas"]
    assert [fila.titulo_visible for fila in filas] == ["Shonen", "Todas las demografías"]
    assert [p.titulo for p in filas[0].productos] == ["Dragon Ball"]
    assert {p.titulo for p in filas[1].productos} == {"Dragon Ball", "Berserk"}
    contenido = respuesta.content.decode()
    assert f"etiqueta={shonen.pk}&amp;estado=todos" in contenido
    assert f"grupo={shonen.grupo_id}&amp;estado=todos" in contenido


def test_la_fila_trae_hasta_doce_y_sin_lo_que_la_tienda_no_muestra(client, cliente, shonen):
    for indice in range(PRODUCTOS_POR_FILA + 3):
        con_etiqueta(shonen, titulo=f"Tomo {indice:02d}")
    con_etiqueta(shonen, titulo="Descatalogado", estado=Producto.DESCATALOGADO)
    con_etiqueta(shonen, titulo="Para adultos", solo_adultos=True)
    FilaPortada.objects.create(etiqueta=shonen, orden=1)

    productos = portada(client, cliente).context["filas"][0].productos

    titulos = [p.titulo for p in productos]
    assert len(titulos) == PRODUCTOS_POR_FILA
    assert titulos[0] == f"Tomo {PRODUCTOS_POR_FILA + 2:02d}"  # lo más nuevo primero
    assert "Descatalogado" not in titulos
    assert "Para adultos" not in titulos


def test_no_se_dibujan_las_filas_vacias_inactivas_o_de_etiquetas_dadas_de_baja(
    client, cliente, shonen
):
    vacia = EtiquetaFactory(nombre="Josei", grupo=shonen.grupo)
    de_baja = EtiquetaFactory(nombre="Kodomo", grupo=shonen.grupo, activa=False)
    con_etiqueta(shonen)
    con_etiqueta(de_baja)
    FilaPortada.objects.create(etiqueta=vacia, orden=1)
    FilaPortada.objects.create(etiqueta=de_baja, orden=2)
    FilaPortada.objects.create(etiqueta=shonen, orden=3, activa=False)

    assert portada(client, cliente).context["filas"] == []


def test_el_catalogo_filtra_por_grupo_para_el_ver_todo(client, shonen):
    otro_grupo = EtiquetaFactory(
        nombre="Universo DC", grupo=GrupoEtiquetaFactory(nombre="Franquicia")
    )
    con_etiqueta(shonen, titulo="Naruto")
    con_etiqueta(otro_grupo, titulo="Batman")

    respuesta = client.get(
        reverse("core:tienda_catalogo"), {"grupo": shonen.grupo_id, "estado": "todos"}
    )

    assert [p.titulo for p in respuesta.context["productos"]] == ["Naruto"]
