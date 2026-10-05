"""Las filas de la portada de la tienda (plan 07, tercera y cuarta parte).

El Administrador las configura en tarjetas que se reordenan (B-07-010); el
Cliente las recorre de costado en la portada. Cada fila muestra sólo productos
visibles en la tienda, de lo más nuevo a lo más viejo, hasta doce. Las filas
activas también son las entradas de la cinta de accesos (B-07-012).
"""

from io import BytesIO

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from PIL import Image

from apps.catalog.models import Producto
from apps.catalog.tests.factories import (
    EtiquetaFactory,
    GrupoEtiquetaFactory,
    ProductoFactory,
)
from apps.core.models import ContenidoFAQ, FilaPortada, RegistroAuditoria
from apps.core.views_tienda import PRODUCTOS_POR_FILA

pytestmark = pytest.mark.django_db

URL_CONFIGURAR = reverse("core:filas_portada")
URL_PORTADA = reverse("core:tienda")
URL_CATALOGO = reverse("core:tienda_catalogo")


@pytest.fixture(autouse=True)
def media_temporal(settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path
    return tmp_path


def imagen(nombre="fila.png", tamano=(900, 1350)):
    salida = BytesIO()
    Image.new("RGB", tamano, (40, 120, 200)).save(salida, "PNG")
    return SimpleUploadedFile(nombre, salida.getvalue(), content_type="image/png")


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


# ---------------------------------------------------------------------------
# El gestor por tarjetas (B-07-010)
# ---------------------------------------------------------------------------


def test_reordenar_las_tarjetas_cambia_el_orden_y_se_audita(client_admin, shonen):
    seinen = EtiquetaFactory(nombre="Seinen", grupo=shonen.grupo)
    primera = FilaPortada.objects.create(etiqueta=shonen, orden=1)
    segunda = FilaPortada.objects.create(etiqueta=seinen, orden=2)

    client_admin.post(
        URL_CONFIGURAR,
        formset(
            {"id": str(primera.pk), "origen": f"e:{shonen.pk}", "orden": "2", "activa": "on"},
            {"id": str(segunda.pk), "origen": f"e:{seinen.pk}", "orden": "1", "activa": "on"},
            existentes=2,
        ),
    )

    assert [f.titulo_visible for f in FilaPortada.objects.all()] == ["Seinen", "Shonen"]
    detalle = RegistroAuditoria.objects.get(
        accion=RegistroAuditoria.MODIFICACION_FILAS_PORTADA
    ).detalle
    assert detalle == "Shonen · Seinen → Seinen · Shonen"


def test_la_imagen_de_la_fila_se_guarda_procesada_y_se_audita(client_admin, shonen):
    fila = FilaPortada.objects.create(etiqueta=shonen, orden=1)

    client_admin.post(
        URL_CONFIGURAR,
        {
            **formset(
                {"id": str(fila.pk), "origen": f"e:{shonen.pk}", "orden": "1", "activa": "on"},
                existentes=1,
            ),
            "form-0-imagen": imagen(),
        },
    )

    fila.refresh_from_db()
    assert fila.imagen.name.startswith("filas/") and fila.imagen.name.endswith(".webp")
    assert max(Image.open(fila.imagen.path).size) <= 800  # RNF-05
    detalle = RegistroAuditoria.objects.get(
        accion=RegistroAuditoria.MODIFICACION_FILAS_PORTADA
    ).detalle
    assert detalle == "Shonen → Shonen (con imagen); imagen cambiada en Shonen"


def test_un_archivo_que_no_es_imagen_se_rechaza_y_no_se_guarda_nada(client_admin, shonen):
    respuesta = client_admin.post(
        URL_CONFIGURAR,
        {
            **formset({"origen": f"e:{shonen.pk}", "orden": "1", "activa": "on"}),
            "form-0-imagen": SimpleUploadedFile("a.png", b"no es una imagen"),
        },
    )

    assert respuesta.status_code == 200
    assert respuesta.context["formularios"].forms[0].errors["imagen"]
    assert not FilaPortada.objects.exists()


def test_quitar_la_imagen_de_una_fila(client_admin, shonen):
    fila = FilaPortada.objects.create(etiqueta=shonen, orden=1, imagen="filas/vieja.webp")

    client_admin.post(
        URL_CONFIGURAR,
        formset(
            {
                "id": str(fila.pk),
                "origen": f"e:{shonen.pk}",
                "orden": "1",
                "activa": "on",
                "quitar_imagen": "on",
            },
            existentes=1,
        ),
    )

    fila.refresh_from_db()
    assert not fila.imagen


def test_el_gestor_trae_la_tarjeta_vacia_para_agregar_y_los_mandos(client_admin, shonen):
    FilaPortada.objects.create(etiqueta=shonen, orden=1)

    contenido = client_admin.get(URL_CONFIGURAR).content.decode()

    assert "data-plantilla-fila" in contenido
    assert 'name="form-__prefix__-origen"' in contenido
    assert contenido.count('<li class="tarjeta-fila') == 2  # la fila y la plantilla
    assert "data-subir" in contenido and "data-bajar" in contenido and "data-asa" in contenido
    assert 'enctype="multipart/form-data"' in contenido


# ---------------------------------------------------------------------------
# La cáscara de la tienda (B-07-011, B-07-012)
# ---------------------------------------------------------------------------


def test_el_pie_lleva_las_filas_activas_al_catalogo(client, shonen):
    """La cinta de accesos se quitó (B-07-021): los accesos quedan en el pie."""
    otra = EtiquetaFactory(nombre="Kodomo", grupo=shonen.grupo, activa=False)
    FilaPortada.objects.create(etiqueta=shonen, orden=1)
    FilaPortada.objects.create(grupo=shonen.grupo, titulo="Por demografía", orden=2)
    FilaPortada.objects.create(etiqueta=otra, orden=3)
    FilaPortada.objects.create(etiqueta=shonen, titulo="Apagada", orden=4, activa=False)

    respuesta = client.get(URL_CATALOGO, {"etiqueta": shonen.pk, "estado": "todos"})

    accesos = [(a["texto"], a["actual"]) for a in respuesta.context["accesos_tienda"]]
    assert accesos == [
        ("Novedades", False),
        ("Pre-ventas", False),
        ("Shonen", True),
        ("Por demografía", False),
    ]
    contenido = respuesta.content.decode()
    assert 'class="cinta-accesos"' not in contenido
    assert (
        f"etiqueta={shonen.pk}&amp;estado=todos"
        in contenido.partition('<footer class="pie-publico')[2]
    )


def test_el_encabezado_busca_en_el_catalogo(client):
    contenido = client.get(reverse("core:faq")).content.decode()

    assert 'class="buscador-publico"' in contenido
    assert f'action="{URL_CATALOGO}"' in contenido
    assert 'name="q"' in contenido


def test_el_globo_de_ayuda_aparece_si_hay_preguntas_publicadas(client):
    assert 'class="globo-ayuda"' not in client.get(URL_CATALOGO).content.decode()

    faq = ContenidoFAQ.obtener()
    faq.contenido = "## ¿Qué es una pre-venta?"
    faq.save()

    assert 'class="globo-ayuda"' in client.get(URL_CATALOGO).content.decode()
    assert 'class="globo-ayuda"' not in client.get(reverse("core:faq")).content.decode()


def test_la_fila_abre_con_su_imagen_o_con_el_abanico_de_portadas(client, cliente, shonen):
    seinen = EtiquetaFactory(nombre="Seinen", grupo=shonen.grupo)
    con_etiqueta(shonen, titulo="Dragon Ball")
    con_etiqueta(seinen, titulo="Berserk")
    FilaPortada.objects.create(etiqueta=shonen, orden=1, imagen="filas/shonen.webp")
    FilaPortada.objects.create(etiqueta=seinen, orden=2)

    contenido = portada(client, cliente).content.decode()

    assert 'src="/media/filas/shonen.webp"' in contenido
    assert contenido.count("fila-portada__titular--sin-imagen") == 1
    assert "fila-portada__abanico" in contenido
