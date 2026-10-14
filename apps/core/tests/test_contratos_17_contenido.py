"""Pruebas de contrato del módulo 17 · contenido de la tienda.

FAQ (`CU-CFG-FAQ`), banners (`CU-CFG-BNC`, `BNA`, `BNM`, `BNB`), identidad visual
(`CU-CFG-VIS`) y el procesamiento de imágenes de RNF-05. Las imágenes se
escriben en una carpeta temporal: ninguna prueba toca `media/`.
"""

from io import BytesIO

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from PIL import Image

from apps.core import contenido, imagenes
from apps.core.models import (
    Banner,
    ConfiguracionSistema,
    ContenidoFAQ,
    IdentidadVisual,
    RegistroAuditoria,
)

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def media_temporal(settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path
    return tmp_path


def imagen(nombre="foto.png", tamano=(2400, 1350), formato="PNG", color=(200, 30, 30)):
    salida = BytesIO()
    Image.new("RGB", tamano, color).save(salida, formato)
    return SimpleUploadedFile(nombre, salida.getvalue(), content_type=f"image/{formato.lower()}")


def auditorias(accion):
    return RegistroAuditoria.objects.filter(accion=accion)


def archivos(carpeta):
    return sorted(p.name for p in carpeta.rglob("*") if p.is_file())


# ===========================================================================
# RNF-05
# ===========================================================================


def test_RNF05_un_banner_grande_se_guarda_solo_en_webp_con_1920_de_lado_mayor(media_temporal):
    procesada = imagenes.procesar(
        imagen(tamano=(3000, 1000)), lado_mayor=imagenes.LADO_MAYOR_BANNER
    )

    resultado = Image.open(BytesIO(procesada.read()))
    assert resultado.format == "WEBP"
    assert max(resultado.size) == 1920
    assert procesada.name.endswith(".webp")
    assert archivos(media_temporal) == []


def test_RNF05_por_defecto_el_lado_mayor_es_800():
    procesada = imagenes.procesar(imagen(tamano=(1200, 1600), formato="JPEG"))

    assert max(Image.open(BytesIO(procesada.read())).size) == 800


@pytest.mark.parametrize(
    ("archivo", "mensaje"),
    [
        (SimpleUploadedFile("a.png", b"no es una imagen"), "no es una imagen"),
        (lambda: imagen("a.gif", (50, 50), "GIF"), "no se admite"),
    ],
)
def test_RNF05_una_imagen_invalida_informa_el_problema_especifico(archivo, mensaje):
    archivo = archivo() if callable(archivo) else archivo
    with pytest.raises(imagenes.ImagenInvalida, match=mensaje):
        imagenes.procesar(archivo)


def test_RNF05_una_imagen_que_excede_el_tamano_se_rechaza():
    pesada = SimpleUploadedFile("a.png", b"0" * (6 * imagenes.UN_MEGABYTE))

    with pytest.raises(imagenes.ImagenInvalida, match="pesa 6.0 MB y el máximo es 5 MB"):
        imagenes.procesar(pesada)


# ===========================================================================
# FAQ — CO-210, CO-135, CO-136
# ===========================================================================


def test_CO210_consultar_faq_presenta_lo_publicado_en_el_editor(client_admin):
    faq = ContenidoFAQ.obtener()
    faq.contenido = "# Envíos"
    faq.save()

    respuesta = client_admin.get(reverse("core:faq_editor"))

    assert respuesta.context["form"].initial["contenido"] == "# Envíos"


def test_CO135_publicar_reemplaza_el_contenido_y_queda_en_la_tienda(
    client, client_admin, administrador, cliente
):
    client_admin.post(
        reverse("core:faq_editor"), {"contenido": "## ¿Envían?\n\nSí, a todo el país."}
    )

    faq = ContenidoFAQ.obtener()
    assert faq.contenido.startswith("## ¿Envían?")
    assert faq.actualizado_en is not None
    assert auditorias(RegistroAuditoria.PUBLICACION_FAQ).get().actor == administrador
    client.force_login(cliente)
    publicada = client.get(reverse("core:faq")).content.decode()
    assert "<h2>¿Envían?</h2>" in publicada


def test_CO135_la_vista_previa_no_publica(client_admin):
    respuesta = client_admin.post(
        reverse("core:faq_editor"), {"contenido": "**borrador**", "vista_previa": "1"}
    )

    assert "<strong>borrador</strong>" in respuesta.content.decode()
    assert ContenidoFAQ.obtener().contenido == ""
    assert not auditorias(RegistroAuditoria.PUBLICACION_FAQ).exists()


def test_CO135_el_markdown_se_publica_sin_html_crudo(client):
    """C-16: lo que el Administrador escribe no puede inyectar guiones."""
    contenido.publicar_faq("<script>alert(1)</script>\n\n[x](javascript:alert(1))", actor=None)

    publicada = client.get(reverse("core:faq")).content.decode()

    assert "<script>alert" not in publicada
    assert 'href="javascript:' not in publicada


def test_CO135_vacio_no_publica_sin_confirmacion(client_admin):
    contenido.publicar_faq("# Algo", actor=None)
    registros = RegistroAuditoria.objects.count()

    respuesta = client_admin.post(reverse("core:faq_editor"), {"contenido": "   "})

    assert "va a quedar en blanco" in respuesta.content.decode()
    assert ContenidoFAQ.obtener().contenido == "# Algo"
    assert RegistroAuditoria.objects.count() == registros


def test_CO136_confirmar_la_faq_vacia_la_deja_en_blanco(client_admin, administrador):
    contenido.publicar_faq("# Algo", actor=None)

    client_admin.post(reverse("core:faq_editor"), {"contenido": "", "confirmar_vacia": "1"})

    assert ContenidoFAQ.obtener().contenido == ""
    assert auditorias(RegistroAuditoria.PUBLICACION_FAQ).filter(actor=administrador).exists()


# ===========================================================================
# Banners — CO-209, CO-132, CO-133, CO-134
# ===========================================================================


def cargar(client_admin, cantidad):
    for numero in range(cantidad):
        client_admin.post(reverse("core:banner_crear"), {"imagen": imagen(f"b{numero}.png")})
    return list(Banner.objects.all())


def test_CO132_agregar_banner_lo_pone_al_final_procesado_y_publicado(
    client_admin, administrador, cliente, client
):
    primero, segundo = cargar(client_admin, 2)

    assert (primero.posicion, segundo.posicion) == (0, 1)
    assert segundo.imagen.name.endswith(".webp")
    assert max(Image.open(segundo.imagen.path).size) == 1920
    assert auditorias(RegistroAuditoria.ALTA_BANNER).filter(actor=administrador).count() == 2
    client.force_login(cliente)
    portada = client.get(reverse("core:tienda")).content.decode()
    assert segundo.imagen.url in portada


def test_CO132_E1_una_imagen_invalida_no_agrega_nada(client_admin):
    respuesta = client_admin.post(
        reverse("core:banner_crear"), {"imagen": SimpleUploadedFile("x.png", b"basura")}
    )

    assert "no es una imagen" in respuesta.content.decode()
    assert not Banner.objects.exists()


def test_CO209_consultar_banners_en_orden_con_la_vista_previa(client_admin):
    cargar(client_admin, 3)
    configuracion = ConfiguracionSistema.obtener()
    configuracion.intervalo_carrusel = 7
    configuracion.save()

    respuesta = client_admin.get(reverse("core:banner_lista"))

    assert [b.numero for b in respuesta.context["banners"]] == [1, 2, 3]
    assert 'data-intervalo="7"' in respuesta.content.decode()


def test_CO133_mover_un_banner_reajusta_a_los_demas(client_admin, administrador):
    a, b, c = cargar(client_admin, 3)

    client_admin.post(reverse("core:banner_editar", args=[c.pk]), {"numero": "1"})

    orden = list(Banner.objects.values_list("pk", "posicion"))
    assert orden == [(c.pk, 0), (a.pk, 1), (b.pk, 2)]
    registro = auditorias(RegistroAuditoria.MODIFICACION_BANNER).get()
    assert registro.actor == administrador
    assert "posición: 3 → 1" in registro.detalle


def test_CO133_reemplazar_la_imagen_conserva_la_posicion_y_borra_la_anterior(
    client_admin, media_temporal, django_capture_on_commit_callbacks
):
    a, b = cargar(client_admin, 2)
    vieja = b.imagen.name

    # El archivo viejo se borra cuando la transacción confirma.
    with django_capture_on_commit_callbacks(execute=True):
        client_admin.post(
            reverse("core:banner_editar", args=[b.pk]),
            {"numero": "2", "imagen": imagen("nueva.jpg", formato="JPEG")},
        )

    b.refresh_from_db()
    assert b.posicion == 1
    assert b.imagen.name != vieja
    assert not (media_temporal / vieja).exists()


def test_CO133_E1_imagen_invalida_no_registra_tampoco_la_posicion(client_admin):
    a, b = cargar(client_admin, 2)
    registros = RegistroAuditoria.objects.count()

    client_admin.post(
        reverse("core:banner_editar", args=[b.pk]),
        {"numero": "1", "imagen": SimpleUploadedFile("x.png", b"basura")},
    )

    assert list(Banner.objects.values_list("pk", flat=True)) == [a.pk, b.pk]
    assert RegistroAuditoria.objects.count() == registros


def test_CO133_la_posicion_fuera_de_rango_se_rechaza(client_admin):
    a, b = cargar(client_admin, 2)

    respuesta = client_admin.post(reverse("core:banner_editar", args=[a.pk]), {"numero": "5"})

    assert respuesta.context["form"].errors["numero"]


def test_CO134_eliminar_reajusta_y_conserva_el_orden_relativo(
    client_admin, media_temporal, django_capture_on_commit_callbacks
):
    a, b, c = cargar(client_admin, 3)
    archivo = b.imagen.name

    with django_capture_on_commit_callbacks(execute=True):
        client_admin.post(reverse("core:banner_baja", args=[b.pk]))

    assert list(Banner.objects.values_list("pk", "posicion")) == [(a.pk, 0), (c.pk, 1)]
    assert not (media_temporal / archivo).exists()
    assert auditorias(RegistroAuditoria.BAJA_BANNER).count() == 1


def test_CO134_sin_confirmacion_no_hay_eliminacion(client_admin):
    """CU-CFG-BNB A1: abrir la confirmación y volver."""
    (banner,) = cargar(client_admin, 1)

    client_admin.get(reverse("core:banner_baja", args=[banner.pk]))

    assert Banner.objects.filter(pk=banner.pk).exists()
    assert not auditorias(RegistroAuditoria.BAJA_BANNER).exists()


def test_el_carrusel_tiene_anterior_siguiente_y_pausar(client_admin, client, cliente):
    """`identidad_visual.md`: un contenido que cambia solo debe poder detenerse."""
    cargar(client_admin, 2)
    client.force_login(cliente)

    portada = client.get(reverse("core:tienda")).content.decode()

    for control in ("data-anterior", "data-siguiente", "data-pausar"):
        assert control in portada


# ===========================================================================
# Identidad visual — CO-208, CO-131
# ===========================================================================


DATOS_VALIDOS = {
    "nombre_tienda": "  Akiba   Cómics ",
    "correo_contacto": "hola@akiba.test",
    "telefono": "",
    "instagram": "https://instagram.com/akiba",
    "facebook": "",
    "tiktok": "",
    "x_twitter": "",
    "color_primario": "#1a2b3c",
    "color_secundario": "#444444",
    "color_acento": "#AA0000",
    "tipo_fondo": "color",
    "color_fondo": "#FAFAFA",
}


def test_CO208_consultar_identidad_presenta_los_valores_actuales(client_admin):
    respuesta = client_admin.get(reverse("core:identidad_visual"))

    assert respuesta.context["form"].initial["color_primario"] == "#FF6A13"


def test_CO131_actualizar_identidad_aplica_a_la_tienda_y_audita_lo_anterior(
    client_admin, administrador, client
):
    client_admin.post(reverse("core:identidad_visual"), DATOS_VALIDOS)

    identidad = IdentidadVisual.obtener()
    assert identidad.nombre_tienda == "Akiba Cómics"
    assert identidad.color_primario == "#1A2B3C"
    registro = auditorias(RegistroAuditoria.MODIFICACION_IDENTIDAD_VISUAL).get()
    assert registro.actor == administrador
    assert "color primario: «#FF6A13» → «#1A2B3C»" in registro.detalle
    hoja = client.get(reverse("core:tienda_css")).content.decode()
    assert "--tienda-primario: #1A2B3C;" in hoja
    assert "--tienda-acento: #AA0000;" in hoja


def test_CO131_E1_un_hex_invalido_no_aplica_ningun_cambio(client_admin):
    datos = {**DATOS_VALIDOS, "color_acento": "#12345G", "nombre_tienda": "Otra"}

    respuesta = client_admin.post(reverse("core:identidad_visual"), datos)

    assert respuesta.context["form"].errors["color_acento"]
    identidad = IdentidadVisual.obtener()
    assert identidad.nombre_tienda == "Longbox"
    assert not auditorias(RegistroAuditoria.MODIFICACION_IDENTIDAD_VISUAL).exists()


def test_CO131_el_nombre_y_el_correo_son_obligatorios(client_admin):
    datos = {**DATOS_VALIDOS, "nombre_tienda": " ", "correo_contacto": ""}

    respuesta = client_admin.post(reverse("core:identidad_visual"), datos)

    errores = respuesta.context["form"].errors
    assert "nombre_tienda" in errores and "correo_contacto" in errores


def test_CO131_E2_una_imagen_invalida_se_descarta_y_no_aplica_nada(client_admin):
    datos = {**DATOS_VALIDOS, "logo_nuevo": SimpleUploadedFile("logo.svg", b"<svg/>")}

    respuesta = client_admin.post(reverse("core:identidad_visual"), datos)

    assert respuesta.context["form"].errors["logo_nuevo"]
    assert not IdentidadVisual.obtener().logo


def test_CO131_el_fondo_puede_ser_una_imagen(client_admin, client):
    """C-07: el fondo de la tienda puede ser imagen."""
    datos = {
        **DATOS_VALIDOS,
        "tipo_fondo": "imagen",
        "fondo_nuevo": imagen("fondo.jpg", formato="JPEG"),
    }

    client_admin.post(reverse("core:identidad_visual"), datos)

    identidad = IdentidadVisual.obtener()
    assert identidad.imagen_fondo.name.endswith(".webp")
    hoja = client.get(reverse("core:tienda_css")).content.decode()
    assert f'url("{identidad.imagen_fondo.url}")' in hoja


def test_CO131_la_tienda_carga_la_hoja_sin_cambiar_el_backoffice(client_admin, cliente, client):
    client_admin.post(reverse("core:identidad_visual"), DATOS_VALIDOS)
    client.force_login(cliente)

    tienda = client.get(reverse("core:tienda")).content.decode()
    panel = client_admin.get(reverse("core:panel")).content.decode()

    assert reverse("core:tienda_css") in tienda
    assert "Akiba Cómics" in tienda
    assert reverse("core:tienda_css") not in panel


# ===========================================================================
# Intervalo del carrusel (CU-CFG-PAR, sección Tienda; B-17-003)
# ===========================================================================


def test_el_intervalo_del_carrusel_nace_en_10_y_se_edita_en_parametros(client_admin):
    assert ConfiguracionSistema.obtener().intervalo_carrusel == 10

    client_admin.post(
        reverse("catalog:parametros"),
        {"stock_inicial_por_defecto": "1", "intervalo_carrusel": "6", "dias_aviso_preventa": "2"},
    )

    assert ConfiguracionSistema.obtener().intervalo_carrusel == 6


def test_el_intervalo_no_puede_ser_cero(client_admin):
    respuesta = client_admin.post(
        reverse("catalog:parametros"),
        {"stock_inicial_por_defecto": "1", "intervalo_carrusel": "0", "dias_aviso_preventa": "2"},
    )

    assert respuesta.context["form"].errors["intervalo_carrusel"]


# ===========================================================================
# Control de acceso
# ===========================================================================


@pytest.mark.parametrize(
    "ruta", ["core:faq_editor", "core:banner_lista", "core:banner_crear", "core:identidad_visual"]
)
def test_el_cajero_no_edita_el_contenido_de_la_tienda(client, cajero, ruta):
    client.force_login(cajero)

    assert client.get(reverse(ruta)).status_code == 403
    assert client.post(reverse(ruta), {"contenido": "x"}).status_code == 403
    assert ContenidoFAQ.obtener().contenido == ""


def test_CO131_la_imagen_del_ingreso_se_procesa_y_se_audita(client_admin):
    """B-07-020: la imagen que acompaña a las pantallas de acceso, en la identidad."""
    datos = {**DATOS_VALIDOS, "acceso_nueva": imagen("ingreso.png", (1200, 1600))}

    client_admin.post(reverse("core:identidad_visual"), datos)

    identidad = IdentidadVisual.obtener()
    assert identidad.imagen_acceso.name.endswith(".webp")
    registro = auditorias(RegistroAuditoria.MODIFICACION_IDENTIDAD_VISUAL).latest("pk")
    assert "imagen del ingreso cargado" in registro.detalle


def test_CO131_quitar_el_logo_y_la_imagen_del_ingreso_vuelve_a_lo_predeterminado(client_admin):
    """B-07-025: las dos imágenes se pueden quitar; la tienda vuelve a su vista
    predeterminada y la auditoría lo dice."""
    client_admin.post(
        reverse("core:identidad_visual"),
        {
            **DATOS_VALIDOS,
            "logo_nuevo": imagen("logo.png", (400, 400)),
            "acceso_nueva": imagen("ingreso.png", (900, 1200)),
        },
    )

    client_admin.post(
        reverse("core:identidad_visual"),
        {**DATOS_VALIDOS, "quitar_logo": "on", "quitar_acceso": "on"},
    )

    identidad = IdentidadVisual.obtener()
    assert not identidad.logo
    assert not identidad.imagen_acceso
    detalle = auditorias(RegistroAuditoria.MODIFICACION_IDENTIDAD_VISUAL).latest("pk").detalle
    assert "logo quitado" in detalle
    assert "imagen del ingreso quitado" in detalle
    pantalla = client_admin.get(reverse("core:identidad_visual")).content.decode()
    assert pantalla.count("imagen-configurable__predeterminada") == 2
