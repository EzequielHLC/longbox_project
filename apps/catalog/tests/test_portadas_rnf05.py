"""RNF-05 en las portadas de producto (plan 00 de cierre de deuda, D2).

La condición de verificación del requisito, en cada camino por el que entra una
portada: «Una imagen subida en formato PNG o JPG de resolución superior a 800px
debe almacenarse en el servidor únicamente en su versión procesada en WebP y con
sus dimensiones reducidas, sin que el archivo original persista. El tamaño del
archivo resultante no debe superar los 150KB para imágenes de portada estándar.»

La imagen de prueba es fotográfica —degradés con grano—, no un color plano: un
color plano pesa nada en cualquier formato y no probaría el tope de 150 KB.
"""

from decimal import Decimal
from io import BytesIO
from types import SimpleNamespace

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from PIL import Image

from apps.catalog import borradores
from apps.catalog.models import BorradorProducto, ProductoEditorial, ProductoNoEditorial
from apps.catalog.tests.factories import (
    EditorialFactory,
    PrecioReferenciaFactory,
    ProductoNoEditorialFactory,
    TipoFactory,
    TipoNoEditorialFactory,
)
from apps.catalog.tests.helpers_lote import URL_IMPORTADO, URL_NACIONAL, item, lote_nacional
from apps.catalog.tests.helpers_lote import payload as payload_lote
from apps.catalog.tests.test_contratos_02_producto import alta, url_editar
from apps.catalog.tests.test_edicion_producto import datos_no_editoriales
from apps.catalog.tests.test_pantalla_revision import campos_de
from apps.core.models import ConfiguracionSistema
from apps.suppliers.models import CorreoProveedor
from apps.suppliers.tests.factories import ProveedorFactory

pytestmark = pytest.mark.django_db

URL_ALTA = reverse("catalog:producto_no_editorial_alta")
LADO = 800
TOPE = 150 * 1024


@pytest.fixture(autouse=True)
def media(settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path
    return tmp_path


@pytest.fixture
def correo(db):
    proveedor = ProveedorFactory()
    return CorreoProveedor.objects.create(
        proveedor=proveedor,
        message_id="<tapa@proveedor.test>",
        remitente=proveedor.correo_comercial,
        estado=CorreoProveedor.PROCESADO,
    )


def foto(formato="PNG", ancho=2000, alto=1500):
    """Bytes de una imagen con el detalle de una tapa escaneada."""
    degrade = Image.linear_gradient("L").resize((ancho, alto))
    radial = Image.radial_gradient("L").resize((ancho, alto))
    grano = Image.effect_noise((ancho, alto), 40)
    imagen = Image.merge("RGB", (degrade, radial, Image.blend(degrade, grano, 0.5)))
    salida = BytesIO()
    imagen.save(salida, formato)
    return salida.getvalue()


def subida(formato="PNG", nombre="tapa.png"):
    return SimpleUploadedFile(nombre, foto(formato), content_type=f"image/{formato.lower()}")


def archivos_en(carpeta):
    return [ruta for ruta in carpeta.rglob("*") if ruta.is_file()]


def verificar_rnf05(campo, carpeta):
    """La condición de verificación, entera, sobre el archivo guardado."""
    assert campo.name.endswith(".webp")
    with Image.open(campo.path) as guardada:
        assert guardada.format == "WEBP"
        assert max(guardada.size) == LADO
        assert guardada.size == (LADO, LADO * 3 // 4)  # mantiene la proporción
    assert campo.size <= TOPE
    # El original no persiste: no hay ningún archivo que no sea WebP.
    assert [ruta.suffix for ruta in archivos_en(carpeta)] == [".webp"]


# ---------------------------------------------------------------------------
# Los caminos por los que entra una portada
# ---------------------------------------------------------------------------


def test_CO003_la_portada_del_lote_nacional_queda_en_webp_sin_el_original(client_admin, media):
    referencia = PrecioReferenciaFactory(pvp=Decimal("10000"))
    datos = lote_nacional([item("Akira", 1)], referencia)
    datos["form-0-portada"] = subida()

    client_admin.post(URL_NACIONAL, datos)

    verificar_rnf05(ProductoEditorial.objects.get().portada, media)


def test_CO009_la_portada_del_lote_importado_queda_en_webp_sin_el_original(client_admin, media):
    configuracion = ConfiguracionSistema.obtener()
    configuracion.margen_ganancia = Decimal("0.40")
    configuracion.save()
    datos = payload_lote(
        [item("Berserk", 1, costo_origen="1000")],
        editorial=EditorialFactory().pk,
        tipo=TipoFactory().pk,
        costo_envio_total="10000",
        valor_compra_total="100000",
    )
    datos["form-0-portada"] = subida(formato="JPEG", nombre="tapa.jpg")

    client_admin.post(URL_IMPORTADO, datos)

    verificar_rnf05(ProductoEditorial.objects.get().portada, media)


def test_CO028_la_portada_del_alta_no_editorial_queda_en_webp_sin_el_original(client_admin, media):
    respuesta = client_admin.post(URL_ALTA, {**alta(TipoNoEditorialFactory()), "portada": subida()})

    assert respuesta.status_code == 302
    verificar_rnf05(ProductoNoEditorial.objects.get().portada, media)


def test_CO030_la_portada_que_reemplaza_queda_en_webp_sin_el_original(client_admin, media):
    producto = ProductoNoEditorialFactory(tipo=TipoNoEditorialFactory())

    client_admin.post(url_editar(producto), {**datos_no_editoriales(producto), "portada": subida()})

    producto.refresh_from_db()
    verificar_rnf05(producto.portada, media)


def test_CO020_la_portada_que_se_le_carga_a_un_borrador_queda_en_webp(client_admin, media, correo):
    borrador = BorradorProducto.objects.create(
        correo=correo,
        proveedor=correo.proveedor,
        titulo="Berserk",
        volumen=1,
        precio=Decimal("24900"),
    )
    url = reverse("catalog:borrador_detalle", args=[borrador.pk])

    client_admin.post(url, {**campos_de(borrador), "portada": subida()})

    borrador.refresh_from_db()
    verificar_rnf05(borrador.portada, media)


def test_la_portada_del_correo_se_procesa_al_adjuntarla_al_borrador(media, correo):
    """Ambigüedad 1 del plan: la revisión ve la misma imagen que se va a guardar."""
    borrador = BorradorProducto.objects.create(
        correo=correo, proveedor=correo.proveedor, titulo="Berserk", volumen=1, cid_portada="tapa"
    )

    borradores._adjuntar_portada(
        borrador, {"tapa": SimpleNamespace(nombre="tapa.png", contenido=foto())}
    )

    borrador.refresh_from_db()
    verificar_rnf05(borrador.portada, media)
    assert borrador.reparos == []


# ---------------------------------------------------------------------------
# Lo que no se admite
# ---------------------------------------------------------------------------


def test_CO028_una_portada_gif_se_rechaza_y_no_registra(client_admin, media):
    """Ambigüedad 3 del plan: el mismo criterio que las imágenes adicionales."""
    respuesta = client_admin.post(
        URL_ALTA,
        {**alta(TipoNoEditorialFactory()), "portada": subida(formato="GIF", nombre="tapa.gif")},
    )

    assert respuesta.status_code == 200
    assert "El formato GIF no se admite" in respuesta.content.decode()
    assert not ProductoNoEditorial.objects.exists()
    assert archivos_en(media) == []


def test_un_adjunto_gif_del_correo_deja_el_reparo_y_ningun_archivo(media, correo):
    borrador = BorradorProducto.objects.create(
        correo=correo, proveedor=correo.proveedor, titulo="Berserk", volumen=1, cid_portada="tapa"
    )

    borradores._adjuntar_portada(
        borrador, {"tapa": SimpleNamespace(nombre="tapa.gif", contenido=foto("GIF"))}
    )

    borrador.refresh_from_db()
    assert not borrador.portada
    assert borrador.reparos == ["La portada del correo no se pudo guardar."]
    assert archivos_en(media) == []
