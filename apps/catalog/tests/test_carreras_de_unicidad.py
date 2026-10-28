"""El código, el ISBN o la edición que otra alta confirmó mientras ésta se validaba.

Plan 00 de cierre de deuda, D1. El formulario ya dijo que el valor estaba libre y,
antes de guardar, otro pedido lo ocupa. La restricción de la base es la que no
deja pasar el duplicado; lo que se prueba es que el Administrador reciba **el
aviso del contrato** —con la ficha en conflicto y el criterio— y no un error 500,
y que no quede nada a medias: ni producto, ni auditoría, ni la portada subida.

De paso, `CO-028` E3 y `CO-030` E2 piden el enlace también sin carrera, y hasta
acá el choque de códigos sólo decía el mensaje genérico de unicidad.
"""

from decimal import Decimal
from io import BytesIO
from unittest.mock import patch

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from PIL import Image

from apps.catalog import services
from apps.catalog.forms import ProductoEditorialForm, ProductoNoEditorialForm
from apps.catalog.models import LoteAlta, Producto, ProductoEditorial, ProductoNoEditorial
from apps.catalog.tests.factories import (
    EditorialFactory,
    FormatoFactory,
    ProductoFactory,
    ProductoNoEditorialFactory,
    TipoFactory,
    TipoNoEditorialFactory,
)
from apps.catalog.tests.test_contratos_02_producto import alta, url_editar
from apps.catalog.tests.test_edicion_producto import datos_editoriales, datos_no_editoriales
from apps.core.models import RegistroAuditoria
from apps.core.tests.concurrencia import gana_la_carrera

pytestmark = pytest.mark.django_db

URL_ALTA = reverse("catalog:producto_no_editorial_alta")
BERSERK = "9789878271583"
CODIGOS = {"codigo": "FIG-001", "codigo_barras": "4580590170000"}
CRITERIOS = {"codigo": "código interno", "codigo_barras": "código de barras"}


@pytest.fixture
def categoria(db):
    return TipoNoEditorialFactory(nombre="Figura")


@pytest.fixture
def media(settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path
    return tmp_path


def png(lado=1200):
    salida = BytesIO()
    Image.new("RGB", (lado, lado), (180, 40, 40)).save(salida, "PNG")
    return SimpleUploadedFile("tapa.png", salida.getvalue(), content_type="image/png")


def archivos_en(carpeta):
    return [ruta for ruta in carpeta.rglob("*") if ruta.is_file()]


def ficha(producto):
    return reverse("catalog:producto_detalle", args=[producto.pk])


def auditorias(accion):
    return RegistroAuditoria.objects.filter(accion=accion)


# ---------------------------------------------------------------------------
# CO-028 E3 — el alta no editorial
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("campo", list(CODIGOS))
def test_CO028_E3_el_codigo_ajeno_enlaza_la_ficha_en_conflicto(client_admin, categoria, campo):
    existente = ProductoNoEditorialFactory(tipo=categoria, **{campo: CODIGOS[campo]})

    respuesta = client_admin.post(
        URL_ALTA, alta(categoria, titulo="Otra figura", **{campo: CODIGOS[campo]})
    )

    assert respuesta.status_code == 200
    contenido = respuesta.content.decode()
    assert ficha(existente) in contenido
    assert CRITERIOS[campo] in contenido
    assert respuesta.context["conflicto"]["producto"].pk == existente.pk
    assert ProductoNoEditorial.objects.count() == 1


@pytest.mark.parametrize("campo", list(CODIGOS))
def test_CO028_E3_el_codigo_tomado_mientras_se_validaba_bloquea_y_enlaza(
    client_admin, categoria, campo
):
    ganador = []

    def otra_alta():
        ganador.append(ProductoNoEditorialFactory(tipo=categoria, **{campo: CODIGOS[campo]}))

    with gana_la_carrera(ProductoNoEditorialForm, otra_alta):
        respuesta = client_admin.post(
            URL_ALTA, alta(categoria, titulo="Otra figura", **{campo: CODIGOS[campo]})
        )

    assert respuesta.status_code == 200
    assert ficha(ganador[0]) in respuesta.content.decode()
    assert ProductoNoEditorial.objects.count() == 1
    assert not auditorias(RegistroAuditoria.ALTA_PRODUCTO_NO_EDITORIAL).exists()


def test_CO028_E3_la_portada_del_alta_que_perdio_no_queda_en_el_almacenamiento(
    client_admin, categoria, media
):
    def otra_alta():
        ProductoNoEditorialFactory(tipo=categoria, codigo_barras=CODIGOS["codigo_barras"])

    with gana_la_carrera(ProductoNoEditorialForm, otra_alta):
        respuesta = client_admin.post(
            URL_ALTA,
            {**alta(categoria, codigo_barras=CODIGOS["codigo_barras"]), "portada": png()},
        )

    assert respuesta.status_code == 200
    assert archivos_en(media) == []


# ---------------------------------------------------------------------------
# CO-030 E2 — la edición
# ---------------------------------------------------------------------------


def test_CO030_E2_el_codigo_de_barras_ajeno_enlaza_la_ficha_y_el_criterio(client_admin):
    existente = ProductoFactory(codigo_barras=CODIGOS["codigo_barras"])
    otro = ProductoFactory(titulo="Vagabond")

    respuesta = client_admin.post(
        url_editar(otro), datos_editoriales(otro, codigo_barras=CODIGOS["codigo_barras"])
    )

    assert respuesta.status_code == 200
    contenido = respuesta.content.decode()
    assert ficha(existente) in contenido
    assert "código de barras" in contenido
    otro.refresh_from_db()
    assert otro.codigo_barras == ""
    assert not auditorias(RegistroAuditoria.MODIFICACION_PRODUCTO).exists()


def test_CO030_E2_el_codigo_de_barras_tomado_mientras_se_validaba_no_actualiza(
    client_admin, categoria, media
):
    otro = ProductoNoEditorialFactory(tipo=categoria, titulo="Llavero Sasuke")
    ganador = []

    def otra_edicion():
        ganador.append(
            ProductoNoEditorialFactory(tipo=categoria, codigo_barras=CODIGOS["codigo_barras"])
        )

    with gana_la_carrera(ProductoNoEditorialForm, otra_edicion):
        respuesta = client_admin.post(
            url_editar(otro),
            {
                **datos_no_editoriales(otro, codigo_barras=CODIGOS["codigo_barras"]),
                "portada": png(),
            },
        )

    assert respuesta.status_code == 200
    assert ficha(ganador[0]) in respuesta.content.decode()
    otro.refresh_from_db()
    assert otro.codigo_barras == ""
    assert not otro.portada
    assert archivos_en(media) == []
    assert not auditorias(RegistroAuditoria.MODIFICACION_PRODUCTO).exists()


def test_CO030_E2_el_isbn_tomado_mientras_se_validaba_no_actualiza(client_admin):
    """El ISBN vive en la tabla de la hija: el choque llega después de escribir el padre."""
    otro = ProductoFactory(titulo="Vagabond")
    ganador = []

    def otra_carga():
        ganador.append(ProductoFactory(titulo="Berserk", isbn=BERSERK))

    with gana_la_carrera(ProductoEditorialForm, otra_carga):
        respuesta = client_admin.post(url_editar(otro), datos_editoriales(otro, isbn=BERSERK))

    assert respuesta.status_code == 200
    assert ficha(ganador[0]) in respuesta.content.decode()
    otro.refresh_from_db()
    assert otro.isbn == ""
    assert otro.titulo == "Vagabond"
    assert not auditorias(RegistroAuditoria.MODIFICACION_PRODUCTO).exists()


# ---------------------------------------------------------------------------
# CO-003 — el ítem del lote
# ---------------------------------------------------------------------------


def test_CO003_el_tomo_cargado_mientras_tanto_se_excluye_como_duplicado(administrador):
    """E1 de `CU-ALT-NAC`: un duplicado excluye ese ítem y el lote sigue."""
    editorial, tipo, formato = EditorialFactory(), TipoFactory(), FormatoFactory()
    lote = LoteAlta(origen=LoteAlta.NACIONAL, editorial=editorial, tipo=tipo, formato=formato)
    comun = {
        "editorial": editorial,
        "tipo": tipo,
        "formato": formato,
        "origen": ProductoEditorial.NACIONAL,
        "estado": Producto.ACTIVO,
        "precio": Decimal("24900"),
        "precio_base": Decimal("24900"),
        "stock": 2,
    }
    items = [
        {**comun, "titulo": "Berserk", "volumen": 1, "isbn": BERSERK},
        {**comun, "titulo": "Berserk", "volumen": 2, "isbn": ""},
    ]
    buscar = services.buscar_duplicado
    ganador = []

    def chequeo_que_llega_tarde(*argumentos, **opciones):
        if not ganador:
            ganador.append(ProductoFactory(titulo="Berserk (otra carga)", isbn=BERSERK))
            return None
        return buscar(*argumentos, **opciones)

    with patch("apps.catalog.services.buscar_duplicado", side_effect=chequeo_que_llega_tarde):
        resultado = services.registrar_lote(lote=lote, items=items, actor=administrador)

    assert [p.volumen for p in resultado.creados] == [2]
    assert [r["producto_existente"] for r in resultado.rechazados] == [ganador[0].pk]
    assert ProductoEditorial.objects.filter(isbn=BERSERK).count() == 1
    assert auditorias(RegistroAuditoria.ALTA_LOTE_EDITORIAL).count() == 1
