"""Historial del producto, galería de imágenes, medidas de los formatos, alta al
vuelo de etiquetas y equivalencias de moneda (sesión del 2026-10-02).

Las imágenes se escriben en una carpeta temporal: ninguna prueba toca `media/`.
"""

import re
from decimal import Decimal
from io import BytesIO

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from PIL import Image

from apps.catalog.models import Etiqueta, GrupoEtiqueta, ImagenProducto, ProductoEditorial
from apps.catalog.tests.factories import (
    EtiquetaFactory,
    FormatoFactory,
    GrupoEtiquetaFactory,
    PrecioReferenciaFactory,
    ProductoFactory,
    TipoNoEditorialFactory,
)
from apps.catalog.tests.helpers_lote import URL_NACIONAL, item, lote_nacional, url_ficha
from apps.core import cotizaciones
from apps.core.models import RegistroAuditoria

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def media_temporal(settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path
    return tmp_path


def imagen(nombre="foto.png", tamano=(1200, 1600)):
    salida = BytesIO()
    Image.new("RGB", tamano, (40, 80, 160)).save(salida, "PNG")
    return SimpleUploadedFile(nombre, salida.getvalue(), content_type="image/png")


def datos_de_edicion(client_admin, producto, **cambios):
    """El POST de la edición tal como lo arma la pantalla, más los cambios."""
    formulario = client_admin.get(reverse("catalog:producto_editar", args=[producto.pk])).context[
        "form"
    ]
    datos = {}
    for nombre in formulario.fields:
        if nombre in ("imagenes_nuevas", "quitar_imagenes", "portada"):
            continue
        valor = formulario[nombre].value()
        if valor is None or valor is False:
            continue
        if isinstance(valor, list):
            datos[nombre] = [str(v) for v in valor]
        elif valor is True:
            datos[nombre] = "on"
        else:
            datos[nombre] = str(valor)
    datos.update(cambios)
    return datos


def editar(client_admin, producto, **cambios):
    return client_admin.post(
        reverse("catalog:producto_editar", args=[producto.pk]),
        datos_de_edicion(client_admin, producto, **cambios),
        follow=True,
    )


# ===========================================================================
# Historial de modificaciones
# ===========================================================================


def test_el_historial_de_un_tomo_cargado_por_lote_empieza_en_su_alta(client_admin):
    referencia = PrecioReferenciaFactory()
    client_admin.post(URL_NACIONAL, lote_nacional([item("Akira", 1, stock=2)], referencia))
    producto = ProductoEditorial.objects.get(titulo="Akira")

    historial = client_admin.get(url_ficha(producto)).context["historial"]

    assert [r.accion for r in historial] == [RegistroAuditoria.ALTA_LOTE_EDITORIAL]


def test_cambiar_solo_las_etiquetas_se_registra_y_se_avisa(client_admin):
    producto = ProductoFactory(titulo="Akira")
    etiqueta = EtiquetaFactory(nombre="Seinen")

    respuesta = editar(client_admin, producto, etiquetas=[str(etiqueta.pk)])

    assert "Se actualizó «Akira»." in [str(m) for m in respuesta.context["messages"]]
    registro = RegistroAuditoria.objects.get(accion=RegistroAuditoria.MODIFICACION_PRODUCTO)
    assert "etiquetas: «ninguna» → «Seinen»" in registro.detalle


def test_una_sinopsis_distinta_del_mismo_largo_tambien_se_registra(client_admin):
    producto = ProductoFactory(descripcion="abcd")

    editar(client_admin, producto, descripcion="wxyz")

    registro = RegistroAuditoria.objects.get(accion=RegistroAuditoria.MODIFICACION_PRODUCTO)
    assert "descripción: «4 caracteres» → «4 caracteres»" in registro.detalle


def test_el_detalle_usa_comillas_angulares(client_admin):
    producto = ProductoFactory(stock=2)

    editar(client_admin, producto, stock="5")

    registro = RegistroAuditoria.objects.get(accion=RegistroAuditoria.MODIFICACION_PRODUCTO)
    assert "stock: «2» → «5»" in registro.detalle


# ===========================================================================
# Galería de imágenes adicionales
# ===========================================================================


def test_la_edicion_agrega_imagenes_procesadas_y_las_registra(client_admin):
    producto = ProductoFactory()

    editar(client_admin, producto, imagenes_nuevas=[imagen("a.png"), imagen("b.png")])

    imagenes = list(producto.imagenes.all())
    assert [i.posicion for i in imagenes] == [0, 1]
    assert all(i.imagen.name.endswith(".webp") for i in imagenes)
    assert max(Image.open(imagenes[0].imagen.path).size) == 800
    registro = RegistroAuditoria.objects.get(accion=RegistroAuditoria.MODIFICACION_PRODUCTO)
    assert "imágenes adicionales: 2 agregadas" in registro.detalle


def test_quitar_una_imagen_reordena_y_borra_el_archivo(
    client_admin, media_temporal, django_capture_on_commit_callbacks
):
    producto = ProductoFactory()
    editar(client_admin, producto, imagenes_nuevas=[imagen("a.png"), imagen("b.png")])
    primera, segunda = producto.imagenes.all()
    archivo = primera.imagen.name

    with django_capture_on_commit_callbacks(execute=True):
        editar(client_admin, producto, quitar_imagenes=[str(primera.pk)])

    assert list(producto.imagenes.values_list("pk", "posicion")) == [(segunda.pk, 0)]
    assert not (media_temporal / archivo).exists()


def test_no_se_pasan_de_ocho_imagenes(client_admin):
    producto = ProductoFactory()

    respuesta = editar(
        client_admin, producto, imagenes_nuevas=[imagen(f"{n}.png") for n in range(9)]
    )

    assert respuesta.context["form"].errors["imagenes_nuevas"]
    assert not ImagenProducto.objects.exists()


def test_una_imagen_invalida_se_nombra_y_no_guarda_nada(client_admin):
    producto = ProductoFactory(stock=2)

    respuesta = editar(
        client_admin,
        producto,
        stock="9",
        imagenes_nuevas=[imagen("buena.png"), SimpleUploadedFile("rota.png", b"nada")],
    )

    assert "«rota.png»" in respuesta.context["form"].errors["imagenes_nuevas"][0]
    producto.refresh_from_db()
    assert producto.stock == 2
    assert not ImagenProducto.objects.exists()


def test_el_alta_no_editorial_carga_imagenes_y_la_ficha_las_muestra(client_admin):
    tipo = TipoNoEditorialFactory(nombre="Figura")

    client_admin.post(
        reverse("catalog:producto_no_editorial_alta"),
        {
            "titulo": "Figura de prueba",
            "tipo": tipo.pk,
            "precio": "50000",
            "stock": "1",
            "imagenes_nuevas": [imagen("frente.png"), imagen("dorso.png")],
        },
    )

    producto = tipo.productos.get()
    contenido = client_admin.get(url_ficha(producto)).content.decode()
    assert producto.imagenes.count() == 2
    assert "data-visor-miniatura" in contenido
    registro = RegistroAuditoria.objects.get(accion=RegistroAuditoria.ALTA_PRODUCTO_NO_EDITORIAL)
    assert "imágenes adicionales: 2 agregadas" in registro.detalle


# ===========================================================================
# Medidas de los formatos en los desplegables
# ===========================================================================


def test_los_desplegables_de_formato_muestran_las_medidas(client_admin):
    referencia = PrecioReferenciaFactory()
    FormatoFactory(nombre="A5 de prueba", descripcion="14,8 × 21 cm")

    contenido = client_admin.get(URL_NACIONAL).content.decode()
    edicion = client_admin.get(
        reverse("catalog:producto_editar", args=[ProductoFactory(formato=referencia.formato).pk])
    ).content.decode()

    assert "A5 de prueba · 14,8 × 21 cm" in contenido
    assert "A5 de prueba · 14,8 × 21 cm" in edicion


# ===========================================================================
# Alta al vuelo de etiquetas y grupos
# ===========================================================================

URL_RAPIDA = reverse("catalog:etiqueta_rapida")


def test_el_dialogo_recibe_los_grupos_activos(client_admin):
    GrupoEtiquetaFactory(nombre="Activo de prueba")
    GrupoEtiquetaFactory(nombre="Apagado de prueba", activo=False)

    nombres = [g["nombre"] for g in client_admin.get(URL_RAPIDA).json()["grupos"]]

    assert "Activo de prueba" in nombres
    assert "Apagado de prueba" not in nombres


def test_crea_la_etiqueta_en_un_grupo_existente(client_admin):
    grupo = GrupoEtiquetaFactory(nombre="Género de prueba")

    respuesta = client_admin.post(URL_RAPIDA, {"nombre": " Isekai ", "grupo": grupo.pk})

    etiqueta = Etiqueta.objects.get(nombre="Isekai", grupo=grupo)
    assert respuesta.json() == {
        "id": etiqueta.pk,
        "nombre": "Isekai",
        "grupo": "Género de prueba",
        "texto": "Género de prueba · Isekai",
    }
    assert RegistroAuditoria.objects.filter(accion=RegistroAuditoria.ALTA_CATALOGO).count() == 1


def test_crea_el_grupo_nuevo_y_la_etiqueta_juntos(client_admin):
    client_admin.post(
        URL_RAPIDA, {"nombre": "1/6", "grupo": "nuevo", "grupo_nuevo": "Escala de prueba"}
    )

    grupo = GrupoEtiqueta.objects.get(nombre="Escala de prueba")
    assert grupo.etiquetas.filter(nombre="1/6").exists()
    assert RegistroAuditoria.objects.filter(accion=RegistroAuditoria.ALTA_CATALOGO).count() == 2


def test_si_la_etiqueta_falla_tampoco_queda_el_grupo(client_admin):
    respuesta = client_admin.post(
        URL_RAPIDA, {"nombre": "x", "grupo": "nuevo", "grupo_nuevo": "Grupo huérfano"}
    )

    assert respuesta.status_code == 400
    assert not GrupoEtiqueta.objects.filter(nombre="Grupo huérfano").exists()
    assert not RegistroAuditoria.objects.filter(accion=RegistroAuditoria.ALTA_CATALOGO).exists()


def test_el_cajero_no_crea_etiquetas_al_vuelo(client, cajero):
    client.force_login(cajero)

    assert client.post(URL_RAPIDA, {"nombre": "Nueva", "grupo": "nuevo"}).status_code == 403


def test_las_altas_ofrecen_el_alta_al_vuelo_de_etiquetas(client_admin):
    contenido = client_admin.get(reverse("catalog:producto_no_editorial_alta")).content.decode()

    assert "data-etiqueta-rapida" in contenido


# ===========================================================================
# Equivalencias de moneda
# ===========================================================================


def test_las_equivalencias_dividen_por_la_cotizacion_de_referencia():
    valores = {"USD": "1000.00", "EUR": "1250.00", "JPY": "7.50"}

    resultado = {e["moneda"]: e["valor"] for e in cotizaciones.equivalencias(15000, valores)}

    assert resultado == {"USD": Decimal("15.00"), "EUR": Decimal("12.00"), "JPY": Decimal("2000")}


def test_la_tabla_de_precios_muestra_las_equivalencias(client_admin, monkeypatch):
    monkeypatch.setattr(
        cotizaciones,
        "obtener_cotizaciones",
        lambda: {"fecha": "2026-10-02", "valores": {"USD": "1000", "EUR": "1250", "JPY": "7.5"}},
    )
    PrecioReferenciaFactory(pvp=Decimal("15000"))

    contenido = client_admin.get(reverse("catalog:precio_lista")).content.decode()

    assert re.search(r"US\$ 15[.,]00", contenido)
    assert "Equivalencias de referencia" in contenido
