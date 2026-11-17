"""Las secciones de la portada (`CU-CFG-SEC`, `CU-TDA-POR`; plan 07, novena parte).

Nacieron como las filas de la tercera y cuarta parte (B-07-009, B-07-010): las
pruebas de las filas siguen acá, sobre el modelo nuevo. El contrato es
`guardarSeccionesDeLaPortada` (`CO-253`): las pruebas
llevan ese rótulo hasta que el responsable lo numere.

El Administrador arma las secciones en tarjetas que se reordenan; la portada
las dibuja en su orden, cada una según su tipo, y nunca con un producto que el
catálogo público no mostraría.
"""

from io import BytesIO

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import IntegrityError, transaction
from django.urls import reverse
from PIL import Image

from apps.catalog.models import Producto
from apps.catalog.tests.factories import (
    EditorialFactory,
    EtiquetaFactory,
    GrupoEtiquetaFactory,
    ProductoFactory,
    TipoFactory,
)
from apps.core.models import (
    Banner,
    ContenidoFAQ,
    ImagenDeSeccion,
    RegistroAuditoria,
    SeccionPortada,
)
from apps.core.views_tienda import PRODUCTOS_POR_FILA, VITRINA

pytestmark = pytest.mark.django_db

URL_CONFIGURAR = reverse("core:secciones_portada")
URL_PORTADA = reverse("core:tienda")
URL_CATALOGO = reverse("core:tienda_catalogo")
FIJAS = "Recién llegados (recién llegados) · Lo que se viene (lo que se viene)"


@pytest.fixture(autouse=True)
def media_temporal(settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path
    return tmp_path


def imagen(nombre="fila.png", tamano=(900, 1350)):
    salida = BytesIO()
    Image.new("RGB", tamano, (40, 120, 200)).save(salida, "PNG")
    return SimpleUploadedFile(nombre, salida.getvalue(), content_type="image/png")


def formset(*secciones, existentes=0):
    """Lo que manda la pantalla: cada sección con su tipo y sus imágenes.

    Una sección es un diccionario de campos; `imagenes` es la lista de las suyas
    y `imagenes_existentes`, cuántas de esas ya estaban guardadas.
    """
    datos = {
        "form-TOTAL_FORMS": str(len(secciones)),
        "form-INITIAL_FORMS": str(existentes),
        "form-MIN_NUM_FORMS": "0",
        "form-MAX_NUM_FORMS": "1000",
    }
    for indice, seccion in enumerate(secciones):
        seccion = dict(seccion)
        imagenes = seccion.pop("imagenes", [])
        previas = seccion.pop("imagenes_existentes", 0)
        seccion.setdefault("tipo", SeccionPortada.PRODUCTOS)
        seccion.setdefault("orden", str(indice + 3))  # detrás de las fijas
        for campo, valor in seccion.items():
            datos[f"form-{indice}-{campo}"] = valor
        prefijo = f"form-{indice}-img"
        datos[f"{prefijo}-TOTAL_FORMS"] = str(len(imagenes))
        datos[f"{prefijo}-INITIAL_FORMS"] = str(previas)
        datos[f"{prefijo}-MIN_NUM_FORMS"] = "0"
        datos[f"{prefijo}-MAX_NUM_FORMS"] = "1000"
        for numero, foto in enumerate(imagenes):
            foto = {"forma_texto": ImagenDeSeccion.RECUADRO, "orden": str(numero + 1), **foto}
            for campo, valor in foto.items():
                datos[f"{prefijo}-{numero}-{campo}"] = valor
    return datos


@pytest.fixture
def shonen(db):
    return EtiquetaFactory(nombre="Shonen", grupo=GrupoEtiquetaFactory(nombre="Demografía"))


def con_etiqueta(etiqueta, **datos):
    datos.setdefault("stock", 3)
    producto = ProductoFactory(**datos)
    producto.etiquetas.add(etiqueta)
    return producto


def portada(client, cliente):
    client.force_login(cliente)
    return client.get(URL_PORTADA)


def nuevas(respuesta):
    """Las secciones que dibuja la portada, sin las dos fijas."""
    return [s for s in respuesta.context["secciones"] if not s.fija]


def auditoria():
    return RegistroAuditoria.objects.get(accion=RegistroAuditoria.MODIFICACION_SECCIONES_PORTADA)


def con_imagen(seccion, orden=1, **datos):
    datos.setdefault("imagen", "secciones/una.webp")
    return ImagenDeSeccion.objects.create(seccion=seccion, orden=orden, **datos)


def accesos(*destinos, **datos):
    seccion = SeccionPortada.objects.create(tipo=SeccionPortada.ACCESOS, orden=10, **datos)
    for orden, (titulo, destino) in enumerate(destinos, start=1):
        con_imagen(seccion, orden, titulo=titulo, **destino)
    return seccion


# ---------------------------------------------------------------------------
# Recién llegados y Lo que se viene nacen con la migración
# ---------------------------------------------------------------------------


def test_las_dos_secciones_fijas_existen_desde_la_migracion():
    assert [(s.tipo, s.orden) for s in SeccionPortada.objects.all()] == [
        (SeccionPortada.RECIEN_LLEGADOS, 1),
        (SeccionPortada.SE_VIENE, 2),
    ]


# ---------------------------------------------------------------------------
# CO-253 guardarSeccionesDeLaPortada
# ---------------------------------------------------------------------------


def test_CO253_agregar_secciones_de_productos_por_etiqueta_y_por_grupo(
    client_admin, administrador, shonen
):
    respuesta = client_admin.post(
        URL_CONFIGURAR,
        formset(
            {"origen": f"e:{shonen.pk}", "titulo": "", "activa": "on"},
            {
                "origen": f"g:{shonen.grupo_id}",
                "titulo": "Por demografía",
                "presentacion": SeccionPortada.VITRINA,
                "activa": "on",
            },
        ),
    )

    assert respuesta.status_code == 302
    secciones = list(SeccionPortada.objects.filter(tipo=SeccionPortada.PRODUCTOS))
    assert [(s.etiqueta_id, s.grupo_id, s.titulo_visible, s.presentacion) for s in secciones] == [
        (shonen.pk, None, "Shonen", SeccionPortada.FILA),
        (None, shonen.grupo_id, "Por demografía", SeccionPortada.VITRINA),
    ]
    registro = auditoria()
    assert registro.actor == administrador
    assert registro.detalle == (
        f"{FIJAS} → {FIJAS} · Shonen (productos) · Por demografía (productos) (vitrina)"
    )


def test_CO253_agregar_accesos_con_sus_imagenes_y_destinos(client_admin, shonen):
    producto = con_etiqueta(shonen, titulo="Dragon Ball")
    editorial = EditorialFactory(nombre="Ivrea")

    respuesta = client_admin.post(
        URL_CONFIGURAR,
        {
            **formset(
                {
                    "tipo": SeccionPortada.ACCESOS,
                    "titulo": "Atajos",
                    "activa": "on",
                    "imagenes": [
                        {"titulo": "Shonen", "lleva_a": f"e:{shonen.pk}"},
                        {"titulo": "Pre-ventas", "lleva_a": ImagenDeSeccion.PREVENTAS},
                        {
                            "titulo": "Goku",
                            "lleva_a": ImagenDeSeccion.PRODUCTO,
                            "codigo_producto": producto.codigo.lower(),
                        },
                        {"titulo": "Ivrea", "lleva_a": f"d:{editorial.pk}"},
                    ],
                }
            ),
            **{f"form-0-img-{n}-imagen": imagen(f"{n}.png") for n in range(4)},
        },
    )

    assert respuesta.status_code == 302
    seccion = SeccionPortada.objects.get(tipo=SeccionPortada.ACCESOS)
    assert [
        (i.titulo, i.destino, getattr(i.dato_del_destino, "pk", None), i.orden)
        for i in seccion.imagenes.all()
    ] == [
        ("Shonen", ImagenDeSeccion.ETIQUETA, shonen.pk, 1),
        ("Pre-ventas", ImagenDeSeccion.PREVENTAS, None, 2),
        ("Goku", ImagenDeSeccion.PRODUCTO, producto.pk, 3),
        ("Ivrea", ImagenDeSeccion.EDITORIAL, editorial.pk, 4),
    ]
    for guardada in seccion.imagenes.all():
        assert guardada.imagen.name.startswith("secciones/")
        assert guardada.imagen.name.endswith(".webp")  # RNF-05
    assert "Atajos (accesos con foto): Shonen→una etiqueta" in auditoria().detalle


@pytest.mark.parametrize(
    ("tipo", "cantidad"),
    [
        (SeccionPortada.ACCESOS, 2),
        (SeccionPortada.ACCESOS, 9),
        (SeccionPortada.PANEL, 2),
        (SeccionPortada.CINTA, 3),
    ],
)
def test_CO253_un_tipo_fuera_de_su_cantidad_de_imagenes_no_guarda_nada(
    client_admin, tipo, cantidad
):
    respuesta = client_admin.post(
        URL_CONFIGURAR,
        {
            **formset(
                {
                    "tipo": tipo,
                    "titulo": "Sección",
                    "activa": "on",
                    "imagenes": [{"titulo": f"Foto {n}"} for n in range(cantidad)],
                }
            ),
            **{f"form-0-img-{n}-imagen": imagen(f"{n}.png") for n in range(cantidad)},
        },
    )

    assert respuesta.status_code == 200
    assert f"y tiene {cantidad}." in respuesta.content.decode()
    assert not SeccionPortada.objects.filter(tipo=tipo).exists()
    assert not ImagenDeSeccion.objects.exists()
    assert not RegistroAuditoria.objects.filter(
        accion=RegistroAuditoria.MODIFICACION_SECCIONES_PORTADA
    ).exists()


@pytest.mark.parametrize(
    "destino",
    [{"lleva_a": "https://otro.sitio/"}, {"lleva_a": "e:999999"}, {"lleva_a": "x:1"}],
)
def test_CO253_un_destino_fuera_de_la_lista_se_rechaza(client_admin, destino):
    respuesta = client_admin.post(
        URL_CONFIGURAR,
        {
            **formset(
                {
                    "tipo": SeccionPortada.PANEL,
                    "titulo": "Panel",
                    "activa": "on",
                    "imagenes": [{"titulo": "Foto", **destino}],
                }
            ),
            "form-0-img-0-imagen": imagen(),
        },
    )

    assert respuesta.status_code == 200
    assert not SeccionPortada.objects.filter(tipo=SeccionPortada.PANEL).exists()


def test_CO253_un_codigo_de_producto_que_no_existe_se_rechaza(client_admin):
    respuesta = client_admin.post(
        URL_CONFIGURAR,
        {
            **formset(
                {
                    "tipo": SeccionPortada.PANEL,
                    "titulo": "Panel",
                    "activa": "on",
                    "imagenes": [
                        {"titulo": "Foto", "lleva_a": "producto", "codigo_producto": "NO-1"}
                    ],
                }
            ),
            "form-0-img-0-imagen": imagen(),
        },
    )

    assert "No hay ningún producto con ese código." in respuesta.content.decode()
    assert not ImagenDeSeccion.objects.exists()


def test_CO253_una_imagen_sin_archivo_se_rechaza_salvo_la_onomatopeya_de_la_pagina(
    client_admin,
):
    sin_archivo = client_admin.post(
        URL_CONFIGURAR,
        formset(
            {
                "tipo": SeccionPortada.PANEL,
                "titulo": "Panel",
                "activa": "on",
                "imagenes": [{"titulo": "Foto"}],
            }
        ),
    )
    assert "Falta la imagen." in sin_archivo.content.decode()

    # Fuera de la página, la onomatopeya no saltea la imagen aunque se mande a mano.
    grito_en_panel = client_admin.post(
        URL_CONFIGURAR,
        formset(
            {
                "tipo": SeccionPortada.PANEL,
                "titulo": "Panel",
                "activa": "on",
                "imagenes": [{"titulo": "¡Pum!", "texto": "¡PUM!", "forma_texto": "grito"}],
            }
        ),
    )
    assert "la onomatopeya sin imagen es sólo de la" in grito_en_panel.content.decode()
    assert not ImagenDeSeccion.objects.exists()

    pagina = client_admin.post(
        URL_CONFIGURAR,
        {
            **formset(
                {
                    "tipo": SeccionPortada.PAGINA,
                    "titulo": "Del local",
                    "activa": "on",
                    "imagenes": [
                        {"titulo": "Uno", "texto": "Abrimos el viernes"},
                        {"titulo": "", "texto": "¡KRAK!", "forma_texto": "grito"},
                        {"titulo": "Tres", "texto": "¡Volvió!", "forma_texto": "globo"},
                    ],
                }
            ),
            "form-0-img-0-imagen": imagen("a.png"),
            "form-0-img-2-imagen": imagen("c.png"),
        },
    )
    assert pagina.status_code == 302
    grito = ImagenDeSeccion.objects.get(forma_texto=ImagenDeSeccion.GRITO)
    assert not grito.imagen and grito.texto == "¡KRAK!"


def test_CO253_las_fijas_no_se_quitan(client_admin):
    recien = SeccionPortada.objects.get(tipo=SeccionPortada.RECIEN_LLEGADOS)

    respuesta = client_admin.post(
        URL_CONFIGURAR,
        formset(
            {
                "id": str(recien.pk),
                "tipo": SeccionPortada.RECIEN_LLEGADOS,
                "activa": "on",
                "DELETE": "on",
            },
            existentes=1,
        ),
    )

    assert respuesta.status_code == 200
    assert "no se quitan" in respuesta.content.decode()
    assert SeccionPortada.objects.filter(pk=recien.pk).exists()


def test_CO253_apagar_una_fija_la_saca_de_la_portada(client_admin, client, cliente):
    recien = SeccionPortada.objects.get(tipo=SeccionPortada.RECIEN_LLEGADOS)
    ProductoFactory(titulo="Berserk", stock=2)

    client_admin.post(
        URL_CONFIGURAR,
        formset(
            {"id": str(recien.pk), "tipo": SeccionPortada.RECIEN_LLEGADOS, "orden": "1"},
            existentes=1,
        ),
    )

    recien.refresh_from_db()
    assert not recien.activa
    assert "Recién llegados (recién llegados) (inactiva)" in auditoria().detalle
    secciones = portada(client, cliente).context["secciones"]
    assert SeccionPortada.RECIEN_LLEGADOS not in [s.tipo for s in secciones]


def test_CO253_el_tipo_de_una_seccion_no_cambia(client_admin, shonen):
    seccion = SeccionPortada.objects.create(etiqueta=shonen, orden=3)

    respuesta = client_admin.post(
        URL_CONFIGURAR,
        formset(
            {"id": str(seccion.pk), "tipo": SeccionPortada.CINTA, "orden": "3", "activa": "on"},
            existentes=1,
        ),
    )

    assert respuesta.status_code == 200
    seccion.refresh_from_db()
    assert seccion.tipo == SeccionPortada.PRODUCTOS


def test_CO253_una_de_productos_sin_origen_se_rechaza_y_no_se_guarda_nada(client_admin):
    respuesta = client_admin.post(
        URL_CONFIGURAR, formset({"origen": "", "titulo": "Sin origen", "activa": "on"})
    )

    assert respuesta.status_code == 200
    assert not SeccionPortada.objects.filter(tipo=SeccionPortada.PRODUCTOS).exists()


def test_CO253_el_origen_y_la_vitrina_se_ignoran_fuera_de_las_de_productos(client_admin, shonen):
    client_admin.post(
        URL_CONFIGURAR,
        {
            **formset(
                {
                    "tipo": SeccionPortada.PANEL,
                    "titulo": "Panel",
                    "origen": f"e:{shonen.pk}",
                    "presentacion": SeccionPortada.VITRINA,
                    "activa": "on",
                    "imagenes": [{"titulo": "Foto"}],
                }
            ),
            "form-0-img-0-imagen": imagen(),
        },
    )

    panel = SeccionPortada.objects.get(tipo=SeccionPortada.PANEL)
    assert (panel.etiqueta_id, panel.grupo_id, panel.presentacion) == (
        None,
        None,
        SeccionPortada.FILA,
    )


def test_CO253_eliminar_una_seccion_con_sus_imagenes(client_admin):
    seccion = accesos(*[(f"A{n}", {}) for n in range(3)], titulo="Atajos")

    client_admin.post(
        URL_CONFIGURAR,
        formset(
            {
                "id": str(seccion.pk),
                "tipo": SeccionPortada.ACCESOS,
                "titulo": "Atajos",
                "orden": "10",
                "activa": "on",
                "DELETE": "on",
            },
            existentes=1,
        ),
    )

    assert not SeccionPortada.objects.filter(pk=seccion.pk).exists()
    assert not ImagenDeSeccion.objects.exists()
    assert auditoria().detalle.endswith(f"→ {FIJAS}")


def test_CO253_quitar_una_imagen_y_reordenar_las_demas(client_admin, shonen):
    seccion = accesos(*[(f"A{n}", {}) for n in range(4)], titulo="Atajos")
    primera, segunda, tercera, cuarta = seccion.imagenes.all()

    def fila(foto, orden, **extra):
        return {"id": str(foto.pk), "titulo": foto.titulo, "orden": str(orden), **extra}

    client_admin.post(
        URL_CONFIGURAR,
        formset(
            {
                "id": str(seccion.pk),
                "tipo": SeccionPortada.ACCESOS,
                "titulo": "Atajos",
                "orden": "10",
                "activa": "on",
                "imagenes_existentes": 4,
                "imagenes": [
                    fila(primera, 3),
                    fila(segunda, 1),
                    fila(tercera, 2, DELETE="on"),
                    fila(cuarta, 2),
                ],
            },
            existentes=1,
        ),
    )

    assert [i.titulo for i in seccion.imagenes.all()] == ["A1", "A3", "A0"]
    assert "Atajos (accesos con foto): A1→sin enlace · A3→sin enlace · A0→sin enlace" in (
        auditoria().detalle
    )


def test_CO253_guardar_sin_cambios_no_audita(client_admin, shonen):
    seccion = SeccionPortada.objects.create(etiqueta=shonen, orden=3)

    client_admin.post(
        URL_CONFIGURAR,
        formset(
            {"id": str(seccion.pk), "origen": f"e:{shonen.pk}", "orden": "3", "activa": "on"},
            existentes=1,
        ),
    )

    assert not RegistroAuditoria.objects.filter(
        accion=RegistroAuditoria.MODIFICACION_SECCIONES_PORTADA
    ).exists()


@pytest.mark.parametrize("rol", ["cajero", "cliente"])
def test_CO253_solo_el_administrador_configura_las_secciones(client, request, rol, shonen):
    """Control de acceso por la dirección real, con el rol equivocado."""
    client.force_login(request.getfixturevalue(rol))

    assert client.get(URL_CONFIGURAR).status_code == 403
    respuesta = client.post(URL_CONFIGURAR, formset({"origen": f"e:{shonen.pk}"}))
    assert respuesta.status_code == 403
    assert not SeccionPortada.objects.filter(tipo=SeccionPortada.PRODUCTOS).exists()


def test_sin_sesion_el_gestor_lleva_al_ingreso(client):
    respuesta = client.get(URL_CONFIGURAR)

    assert respuesta.status_code == 302
    assert reverse("accounts:login") in respuesta["Location"]


# ---------------------------------------------------------------------------
# Las restricciones viven en la base, no sólo en la pantalla
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "datos",
    [
        {"tipo": SeccionPortada.PRODUCTOS},
        {"tipo": SeccionPortada.ACCESOS, "con_etiqueta": True},
        {"tipo": SeccionPortada.CINTA, "presentacion": SeccionPortada.VITRINA},
        {"tipo": SeccionPortada.RECIEN_LLEGADOS},
    ],
)
def test_la_base_rechaza_una_seccion_incoherente(shonen, datos):
    datos = dict(datos)
    if datos.pop("con_etiqueta", False):
        datos["etiqueta"] = shonen
    with pytest.raises(IntegrityError), transaction.atomic():
        SeccionPortada.objects.create(**datos)


@pytest.mark.parametrize(
    "datos",
    [
        {"destino": ImagenDeSeccion.ETIQUETA},
        {"destino": ImagenDeSeccion.SIN_ENLACE, "con_etiqueta": True},
        {"destino": ImagenDeSeccion.PREVENTAS, "con_etiqueta": True},
        {"imagen": ""},
    ],
)
def test_la_base_rechaza_una_imagen_incoherente(shonen, datos):
    seccion = SeccionPortada.objects.create(tipo=SeccionPortada.CINTA)
    datos = {"imagen": "secciones/x.webp", **datos}
    if datos.pop("con_etiqueta", False):
        datos["etiqueta"] = shonen
    with pytest.raises(IntegrityError), transaction.atomic():
        ImagenDeSeccion.objects.create(seccion=seccion, **datos)


# ---------------------------------------------------------------------------
# El gestor por tarjetas (B-07-010)
# ---------------------------------------------------------------------------


def test_reordenar_las_tarjetas_cambia_el_orden_y_se_audita(client_admin, shonen):
    seinen = EtiquetaFactory(nombre="Seinen", grupo=shonen.grupo)
    primera = SeccionPortada.objects.create(etiqueta=shonen, orden=3)
    segunda = SeccionPortada.objects.create(etiqueta=seinen, orden=4)

    client_admin.post(
        URL_CONFIGURAR,
        formset(
            {"id": str(primera.pk), "origen": f"e:{shonen.pk}", "orden": "4", "activa": "on"},
            {"id": str(segunda.pk), "origen": f"e:{seinen.pk}", "orden": "3", "activa": "on"},
            existentes=2,
        ),
    )

    titulos = [s.titulo_visible for s in SeccionPortada.objects.filter(tipo="productos")]
    assert titulos == ["Seinen", "Shonen"]
    assert auditoria().detalle == (
        f"{FIJAS} · Shonen (productos) · Seinen (productos) → "
        f"{FIJAS} · Seinen (productos) · Shonen (productos)"
    )


def test_la_imagen_de_la_fila_se_guarda_procesada_y_se_audita(client_admin, shonen):
    seccion = SeccionPortada.objects.create(etiqueta=shonen, orden=3)

    client_admin.post(
        URL_CONFIGURAR,
        {
            **formset(
                {"id": str(seccion.pk), "origen": f"e:{shonen.pk}", "orden": "3", "activa": "on"},
                existentes=1,
            ),
            "form-0-imagen": imagen(),
        },
    )

    seccion.refresh_from_db()
    assert seccion.imagen.name.startswith("filas/") and seccion.imagen.name.endswith(".webp")
    assert max(Image.open(seccion.imagen.path).size) <= 800  # RNF-05
    assert auditoria().detalle.endswith("; imagen cambiada en Shonen")


def test_un_archivo_que_no_es_imagen_se_rechaza_y_no_se_guarda_nada(client_admin, shonen):
    respuesta = client_admin.post(
        URL_CONFIGURAR,
        {
            **formset({"origen": f"e:{shonen.pk}", "activa": "on"}),
            "form-0-imagen": SimpleUploadedFile("a.png", b"no es una imagen"),
        },
    )

    assert respuesta.status_code == 200
    assert respuesta.context["formularios"].forms[0].errors["imagen"]
    assert not SeccionPortada.objects.filter(tipo=SeccionPortada.PRODUCTOS).exists()


def test_quitar_la_imagen_de_una_fila(client_admin, shonen):
    seccion = SeccionPortada.objects.create(etiqueta=shonen, orden=3, imagen="filas/vieja.webp")

    client_admin.post(
        URL_CONFIGURAR,
        formset(
            {
                "id": str(seccion.pk),
                "origen": f"e:{shonen.pk}",
                "orden": "3",
                "activa": "on",
                "quitar_imagen": "on",
            },
            existentes=1,
        ),
    )

    seccion.refresh_from_db()
    assert not seccion.imagen


def test_el_gestor_trae_una_plantilla_por_tipo_y_los_mandos(client_admin, shonen):
    SeccionPortada.objects.create(etiqueta=shonen, orden=3)

    contenido = client_admin.get(URL_CONFIGURAR).content.decode()

    for tipo in ("productos", "accesos", "pagina", "cinta", "panel"):
        assert f'data-plantilla-fila="{tipo}"' in contenido
        assert f'data-agregar-fila="{tipo}"' in contenido
    # Las fijas no se agregan.
    assert 'data-agregar-fila="recien_llegados"' not in contenido
    assert 'name="form-__prefix__-origen"' in contenido
    assert 'name="form-__prefix__-img-__imagen__-lleva_a"' in contenido
    # Las tres guardadas y las cinco plantillas.
    assert contenido.count('<li class="tarjeta-fila tarjeta-seccion') == 8
    assert "data-subir" in contenido and "data-bajar" in contenido and "data-asa" in contenido
    assert 'enctype="multipart/form-data"' in contenido


def test_las_fijas_no_ofrecen_eliminar(client_admin):
    contenido = client_admin.get(URL_CONFIGURAR).content.decode()

    assert 'name="form-0-DELETE"' not in contenido
    assert 'name="form-1-DELETE"' not in contenido


# ---------------------------------------------------------------------------
# La portada (CU-TDA-POR)
# ---------------------------------------------------------------------------


def test_la_portada_muestra_las_secciones_en_su_orden_con_sus_productos(client, cliente, shonen):
    seinen = EtiquetaFactory(nombre="Seinen", grupo=shonen.grupo)
    con_etiqueta(shonen, titulo="Dragon Ball")
    con_etiqueta(seinen, titulo="Berserk")
    SeccionPortada.objects.create(grupo=shonen.grupo, titulo="Todas las demografías", orden=4)
    SeccionPortada.objects.create(etiqueta=shonen, orden=3)

    respuesta = portada(client, cliente)

    secciones = nuevas(respuesta)
    assert [s.titulo_visible for s in secciones] == ["Shonen", "Todas las demografías"]
    assert [p.titulo for p in secciones[0].productos] == ["Dragon Ball"]
    assert {p.titulo for p in secciones[1].productos} == {"Dragon Ball", "Berserk"}
    contenido = respuesta.content.decode()
    assert f"etiqueta={shonen.pk}&amp;estado=todos" in contenido
    assert f"grupo={shonen.grupo_id}&amp;estado=todos" in contenido


def test_las_secciones_se_numeran_y_alternan_noche_y_papel(client, cliente, shonen):
    con_etiqueta(shonen)
    SeccionPortada.objects.create(etiqueta=shonen, orden=3)
    SeccionPortada.objects.create(etiqueta=shonen, titulo="Otra", orden=4)

    secciones = portada(client, cliente).context["secciones"]

    # Sin pre-ventas, «Lo que se viene» no se dibuja y no consume número.
    assert [(s.numero, s.superficie, s.titulo_visible) for s in secciones] == [
        ("01", "noche", "Recién llegados"),
        ("02", "papel", "Shonen"),
        ("03", "noche", "Otra"),
    ]


def test_la_fila_trae_hasta_doce_y_sin_lo_que_la_tienda_no_muestra(client, cliente, shonen):
    for indice in range(PRODUCTOS_POR_FILA + 3):
        con_etiqueta(shonen, titulo=f"Tomo {indice:02d}")
    con_etiqueta(shonen, titulo="Descatalogado", estado=Producto.DESCATALOGADO)
    con_etiqueta(shonen, titulo="Para adultos", solo_adultos=True)
    SeccionPortada.objects.create(etiqueta=shonen, orden=3)

    productos = nuevas(portada(client, cliente))[0].productos

    titulos = [p.titulo for p in productos]
    assert len(titulos) == PRODUCTOS_POR_FILA
    assert titulos[0] == f"Tomo {PRODUCTOS_POR_FILA + 2:02d}"  # lo más nuevo primero
    assert "Descatalogado" not in titulos
    assert "Para adultos" not in titulos


def test_no_se_dibujan_las_secciones_vacias_inactivas_o_de_etiquetas_dadas_de_baja(
    client, cliente, shonen
):
    vacia = EtiquetaFactory(nombre="Josei", grupo=shonen.grupo)
    de_baja = EtiquetaFactory(nombre="Kodomo", grupo=shonen.grupo, activa=False)
    con_etiqueta(shonen)
    con_etiqueta(de_baja)
    SeccionPortada.objects.create(etiqueta=vacia, orden=3)
    SeccionPortada.objects.create(etiqueta=de_baja, orden=4)
    SeccionPortada.objects.create(etiqueta=shonen, orden=5, activa=False)
    SeccionPortada.objects.create(tipo=SeccionPortada.CINTA, orden=6)  # sin imágenes

    assert nuevas(portada(client, cliente)) == []


def test_el_catalogo_filtra_por_grupo_para_el_ver_todo(client, shonen):
    otro_grupo = EtiquetaFactory(
        nombre="Universo DC", grupo=GrupoEtiquetaFactory(nombre="Franquicia")
    )
    con_etiqueta(shonen, titulo="Naruto")
    con_etiqueta(otro_grupo, titulo="Batman")

    respuesta = client.get(URL_CATALOGO, {"grupo": shonen.grupo_id, "estado": "todos"})

    assert [p.titulo for p in respuesta.context["productos"]] == ["Naruto"]


def test_la_fila_abre_con_su_imagen_o_con_el_abanico_de_portadas(client, cliente, shonen):
    seinen = EtiquetaFactory(nombre="Seinen", grupo=shonen.grupo)
    con_etiqueta(shonen, titulo="Dragon Ball")
    con_etiqueta(seinen, titulo="Berserk")
    SeccionPortada.objects.create(etiqueta=shonen, orden=3, imagen="filas/shonen.webp")
    SeccionPortada.objects.create(etiqueta=seinen, orden=4)

    contenido = portada(client, cliente).content.decode()

    assert 'src="/media/filas/shonen.webp"' in contenido
    assert contenido.count("fila-portada__titular--sin-imagen") == 1
    assert "fila-portada__abanico" in contenido


def test_los_accesos_llevan_a_su_destino_con_cuantos_productos_hay(client, cliente, shonen):
    con_etiqueta(shonen, titulo="Naruto")
    con_etiqueta(shonen, titulo="Bleach")
    preventa = ProductoFactory(titulo="Kaiju", estado=Producto.PRE_VENTA)
    tipo = TipoFactory(nombre="Figura")
    vacia = EtiquetaFactory(nombre="Josei", grupo=shonen.grupo)
    de_baja = EtiquetaFactory(nombre="Kodomo", grupo=shonen.grupo, activa=False)
    con_etiqueta(de_baja)
    oculto = ProductoFactory(titulo="Descatalogado", estado=Producto.DESCATALOGADO)
    accesos(
        ("Shonen", {"destino": ImagenDeSeccion.ETIQUETA, "etiqueta": shonen}),
        ("Pre-ventas", {"destino": ImagenDeSeccion.PREVENTAS}),
        ("Kaiju", {"destino": ImagenDeSeccion.PRODUCTO, "producto": preventa}),
        ("Sin productos", {"destino": ImagenDeSeccion.ETIQUETA, "etiqueta": vacia}),
        ("De baja", {"destino": ImagenDeSeccion.ETIQUETA, "etiqueta": de_baja}),
        ("Oculto", {"destino": ImagenDeSeccion.PRODUCTO, "producto": oculto}),
        ("Sin enlace", {}),
        ("Figuras", {"destino": ImagenDeSeccion.TIPO, "tipo_producto": tipo}),
        titulo="Atajos",
    )

    respuesta = portada(client, cliente)

    seccion = nuevas(respuesta)[0]
    assert [(i.titulo, getattr(i, "cantidad", None)) for i in seccion.lista] == [
        ("Shonen", 2),
        ("Pre-ventas", 1),
        ("Kaiju", None),
    ]
    contenido = respuesta.content.decode()
    assert f'href="{URL_CATALOGO}?etiqueta={shonen.pk}&amp;estado=todos"' in contenido
    assert f'href="{reverse("core:tienda_producto", args=[preventa.pk])}"' in contenido
    assert "2 productos" in contenido and "1 producto<" in contenido


def test_la_pagina_muestra_la_vineta_sin_enlace_si_su_destino_cayo(client, cliente, shonen):
    de_baja = EtiquetaFactory(nombre="Kodomo", grupo=shonen.grupo, activa=False)
    seccion = SeccionPortada.objects.create(tipo=SeccionPortada.PAGINA, titulo="Del local", orden=3)
    con_imagen(seccion, 1, texto="Viernes de pre-ventas")
    con_imagen(
        seccion,
        2,
        imagen="",
        texto="¡KRAK!",
        forma_texto=ImagenDeSeccion.GRITO,
        destino=ImagenDeSeccion.PREVENTAS,
    )
    con_imagen(
        seccion,
        3,
        texto="¡Volvió!",
        forma_texto=ImagenDeSeccion.GLOBO,
        destino=ImagenDeSeccion.ETIQUETA,
        etiqueta=de_baja,
    )

    contenido = portada(client, cliente).content.decode()

    assert 'class="vineta__recuadro">Viernes de pre-ventas<' in contenido
    assert "vineta--color" in contenido and 'class="vineta__grito">¡KRAK!' in contenido
    # La primera no tiene destino y la tercera lo perdió: las dos van sin enlace.
    assert contenido.count('<div class="vineta"') == 2
    pagina = contenido.partition('class="pagina-historieta"')[2]
    assert '&amp;orden=llegada" class="vineta vineta--color"' in pagina
    assert 'class="vineta__globo">¡Volvió!<' in contenido


def test_el_panel_lleva_su_boton_o_se_queda_sin_el(client, cliente):
    panel = SeccionPortada.objects.create(
        tipo=SeccionPortada.PANEL,
        titulo="Reservá lo que se viene",
        texto="Asegurá tu ejemplar.",
        texto_boton="Ver las pre-ventas",
        orden=3,
    )
    foto = con_imagen(panel, destino=ImagenDeSeccion.PREVENTAS)

    contenido = portada(client, cliente).content.decode()
    assert 'id="titulo-seccion-02">Reservá lo que se viene<' in contenido
    assert ">Ver las pre-ventas</a>" in contenido

    foto.destino = ImagenDeSeccion.SIN_ENLACE
    foto.save()
    assert ">Ver las pre-ventas</a>" not in portada(client, cliente).content.decode()


def test_la_cinta_de_fotos_repite_sus_fotos_sin_anunciar_la_segunda_vuelta(client, cliente):
    cinta = SeccionPortada.objects.create(tipo=SeccionPortada.CINTA, titulo="Vitrinas", orden=3)
    for numero in range(4):
        con_imagen(cinta, numero, titulo=f"Foto {numero}")

    contenido = portada(client, cliente).content.decode()

    # Cuatro fotos no llenan una vuelta: se repiten tres veces, y la cinta lleva
    # dos vueltas. Sólo las cuatro primeras se anuncian.
    assert contenido.count('<figure class="foto"') == 24
    assert contenido.count('<figure class="foto" aria-hidden="true">') == 20
    assert "data-cinta-pausa" in contenido


def test_recien_llegados_arma_la_vitrina_y_la_grilla_sin_repetir(client, cliente):
    con_portada = [
        ProductoFactory(titulo=f"Con portada {n}", stock=2, portada=f"portadas/{n}.webp")
        for n in range(VITRINA + 2)
    ]
    sin_portada = ProductoFactory(titulo="Sin portada", stock=2)

    respuesta = portada(client, cliente)

    recien = respuesta.context["secciones"][0]
    assert recien.tipo == SeccionPortada.RECIEN_LLEGADOS
    assert len(recien.vitrina) == VITRINA
    assert all(p.portada for p in recien.vitrina)
    assert {p.pk for p in recien.vitrina}.isdisjoint({p.pk for p in recien.grilla})
    assert {p.pk for p in recien.vitrina} | {p.pk for p in recien.grilla} == {
        p.pk for p in [*con_portada, sin_portada]
    }
    contenido = respuesta.content.decode()
    assert contenido.count("data-vitrina-diapositiva>") == 1
    assert contenido.count("data-vitrina-diapositiva hidden>") == VITRINA - 1
    assert contenido.count('data-vitrina-elegir="') == VITRINA


def test_la_vitrina_agrega_al_carrito_como_la_tarjeta(client, cliente, cajero):
    producto = ProductoFactory(titulo="Berserk", stock=2, portada="portadas/b.webp")

    contenido = portada(client, cliente).content.decode()
    vitrina = contenido.partition("data-vitrina")[2].partition("data-vitrina-controles")[0]
    assert f'action="{reverse("tienda:agregar", args=[producto.pk])}"' in vitrina
    assert "data-agregar-rapido" in vitrina

    # El personal no tiene carrito: ni en la tarjeta ni en la vitrina.
    client.force_login(cajero)
    assert "data-agregar-rapido>" not in client.get(URL_PORTADA).content.decode()


def test_una_vitrina_de_productos_muestra_uno_por_vez(client, cliente, shonen):
    for numero in range(3):
        con_etiqueta(shonen, titulo=f"Tomo {numero}", portada=f"portadas/{numero}.webp")
    SeccionPortada.objects.create(etiqueta=shonen, presentacion=SeccionPortada.VITRINA, orden=3)

    contenido = portada(client, cliente).content.decode()

    seccion = contenido.partition('data-tipo="productos"')[2].partition("</section>")[0]
    assert seccion.count("data-vitrina-diapositiva>") == 1
    assert seccion.count("data-vitrina-diapositiva hidden>") == 2


def test_el_hero_pone_el_carrusel_en_el_televisor_o_la_portada_destacada(client, cliente):
    ProductoFactory(titulo="Berserk", stock=2, portada="portadas/b.webp")

    sin_banners = portada(client, cliente).content.decode()
    assert "tele--fija" in sin_banners and 'alt="Portada de Berserk"' in sin_banners

    Banner.objects.create(imagen="banners/a.webp", posicion=0)
    Banner.objects.create(imagen="banners/b.webp", posicion=1)
    con_banners = portada(client, cliente).content.decode()
    assert 'class="carrusel tele"' in con_banners
    assert con_banners.count('class="canal" data-indicador') == 2
    for control in ("data-anterior", "data-siguiente", "data-pausar"):
        assert control in con_banners


def test_la_portada_no_dispara_una_consulta_por_seccion_de_mas(
    client, cliente, shonen, django_assert_max_num_queries
):
    for numero in range(4):
        con_etiqueta(shonen, titulo=f"Tomo {numero}")
    for orden in range(3, 7):
        SeccionPortada.objects.create(etiqueta=shonen, orden=orden)
    accesos(*[(f"A{n}", {"destino": "etiqueta", "etiqueta": shonen}) for n in range(4)])
    client.force_login(cliente)

    with django_assert_max_num_queries(90):
        client.get(URL_PORTADA)


# ---------------------------------------------------------------------------
# La cáscara de la tienda (B-07-011, B-07-012; novena parte)
# ---------------------------------------------------------------------------


def test_el_pie_lleva_las_secciones_de_productos_activas_al_catalogo(client, shonen):
    """La cinta de accesos se quitó (B-07-021): los accesos quedan en el pie."""
    otra = EtiquetaFactory(nombre="Kodomo", grupo=shonen.grupo, activa=False)
    SeccionPortada.objects.create(etiqueta=shonen, orden=3)
    SeccionPortada.objects.create(grupo=shonen.grupo, titulo="Por demografía", orden=4)
    SeccionPortada.objects.create(etiqueta=otra, orden=5)
    SeccionPortada.objects.create(etiqueta=shonen, titulo="Apagada", orden=6, activa=False)
    SeccionPortada.objects.create(tipo=SeccionPortada.CINTA, titulo="Fotos", orden=7)

    respuesta = client.get(URL_CATALOGO, {"etiqueta": shonen.pk, "estado": "todos"})

    accesos_del_pie = [(a["texto"], a["actual"]) for a in respuesta.context["accesos_tienda"]]
    assert accesos_del_pie == [
        ("Novedades", False),
        ("Pre-ventas", False),
        ("Shonen", True),
        ("Por demografía", False),
    ]
    pie = respuesta.content.decode().partition('<footer class="pie-publico')[2]
    assert f"etiqueta={shonen.pk}&amp;estado=todos" in pie
    assert "Botón de arrepentimiento" in pie  # Res. 424/2020
    assert "Rebobinar" in pie


def test_la_botonera_nombra_cada_destino_y_marca_el_actual(client, cliente):
    client.force_login(cliente)

    contenido = client.get(URL_CATALOGO, {"estado": "pre_venta"}).content.decode()

    encabezado = contenido.partition("</header>")[0]
    for nombre in ("Inicio", "Catálogo", "Pre-ventas", "Carrito", "Mi cuenta"):
        assert f'<span class="boton-aparato__nombre">{nombre}</span>' in encabezado
    actual = encabezado.partition('aria-current="page"')[2][:300]
    assert "Pre-ventas" in actual


def test_el_invitado_ve_ingresar_y_el_personal_no_ve_el_carrito(client, cajero):
    invitado = client.get(URL_PORTADA).content.decode().partition("</header>")[0]
    assert "botonera__ingresar" in invitado

    client.force_login(cajero)
    personal = client.get(URL_PORTADA).content.decode().partition("</header>")[0]
    assert "encabezado-publico__carrito" not in personal


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


def test_los_aparatos_van_en_lima_salvo_que_la_identidad_elija_otro_color(client):
    """Plan 07, novena parte, ambigüedad 3: el rol «Aparatos encendidos»."""
    from apps.core.models import IdentidadVisual

    hoja = client.get(reverse("core:tienda_css")).content.decode()
    assert "--rol-encendido: var(--ok);" in hoja
    assert "--rol-encendido-sobre: #0A0A0C;" in hoja

    identidad = IdentidadVisual.obtener()
    identidad.color_rol_encendido = "acento"
    identidad.save()

    hoja = client.get(reverse("core:tienda_css")).content.decode()
    assert "--rol-encendido: var(--tienda-acento);" in hoja


def test_cada_destino_lleva_a_su_filtro_y_cae_si_se_da_de_baja(shonen):
    """Las ramas de `destino_de`: cada destino arma su filtro del catálogo, y uno
    dado de baja deja de ser enlace (ambigüedad 5)."""
    from apps.core.views_tienda import destino_de

    editorial = EditorialFactory(nombre="Panini")
    tipo = TipoFactory(nombre="Artbook")
    producto = con_etiqueta(shonen, titulo="Naruto", editorial=editorial, tipo=tipo)
    seccion = SeccionPortada.objects.create(tipo=SeccionPortada.CINTA)
    casos = {
        "grupo": (ImagenDeSeccion.GRUPO, {"grupo": shonen.grupo}, f"grupo={shonen.grupo_id}"),
        "editorial": (
            ImagenDeSeccion.EDITORIAL,
            {"editorial": editorial},
            f"editorial={editorial.pk}",
        ),
        "tipo": (ImagenDeSeccion.TIPO, {"tipo_producto": tipo}, f"tipo={tipo.pk}"),
        "etiqueta": (ImagenDeSeccion.ETIQUETA, {"etiqueta": shonen}, f"etiqueta={shonen.pk}"),
    }
    for nombre, (destino, dato, filtro) in casos.items():
        foto = con_imagen(seccion, destino=destino, **dato)
        url, productos = destino_de(foto)
        assert url == f"{URL_CATALOGO}?{filtro}&estado=todos", nombre
        assert list(productos) == [producto.producto_ptr], nombre

    editorial.activa = False
    editorial.save()
    tipo.activo = False
    tipo.save()
    shonen.grupo.activo = False
    shonen.grupo.save()
    for foto in ImagenDeSeccion.objects.select_related(
        "grupo", "editorial", "tipo_producto", "etiqueta__grupo"
    ):
        assert destino_de(foto) is None, foto.destino


def test_en_recien_llegados_novedad_sobra_pero_en_el_catalogo_sigue(client, cliente, shonen):
    """Pedido del responsable (2026-11-11): en «Recién llegados» todo es nuevo."""
    con_etiqueta(shonen, titulo="Berserk", volumen=5, portada="portadas/b.webp")
    SeccionPortada.objects.create(etiqueta=shonen, orden=3)

    contenido = portada(client, cliente).content.decode()
    recien = contenido.partition('data-tipo="recien_llegados"')[2].partition("</section>")[0]
    fila = contenido.partition('data-tipo="productos"')[2].partition("</section>")[0]

    assert "¡NOVEDAD!" not in recien
    assert "¡NOVEDAD!" in fila
    assert "¡NOVEDAD!" in client.get(URL_CATALOGO).content.decode()


def test_el_casete_de_la_vitrina_lleva_la_pista_sin_el_titulo(client, cliente):
    """El título ya está al lado: el casete lleva la tienda, el lado y la pista."""
    ProductoFactory(titulo="Berserk", volumen=5, stock=2, portada="portadas/b.webp")

    contenido = portada(client, cliente).content.decode()
    casete = contenido.partition('class="casete casete--recortado"')[2].partition("</div>")[0]

    assert '<b class="casete__pista">01</b>' in casete
    assert "Pista 01 / 01" in casete
    assert "Berserk" not in casete


def test_el_carnet_es_la_credencial_del_socio(client):
    from apps.accounts.tests.factories import UsuarioFactory

    socio = UsuarioFactory(rol="cliente", first_name="Camila", last_name="Márquez")
    client.force_login(socio)

    contenido = client.get(reverse("cuenta:panel")).content.decode()

    assert '<div class="carnet__retrato" aria-hidden="true"><span>CM</span></div>' in contenido
    assert f'Socio desde <span class="datos">{socio.date_joined:%Y}</span>' in contenido
    assert f"Nº {socio.codigo_cliente}" in contenido


def test_las_iniciales_salen_del_correo_si_no_hay_nombre():
    from types import SimpleNamespace

    from apps.accounts.templatetags.cuenta import _iniciales

    assert _iniciales(SimpleNamespace(first_name="", last_name=" ", email="zeta@x.com")) == "Z"


def test_el_catalogo_lleva_el_lomo_y_la_cinta_con_los_tipos(client):
    ProductoFactory(titulo="Berserk", stock=2, tipo=TipoFactory(nombre="Manga"))

    contenido = client.get(URL_CATALOGO).content.decode()

    assert '<h1 id="titulo-catalogo">Toda la tienda</h1>' in contenido
    cinta = contenido.partition('class="cinta-marcha"')[2].partition("</div></div>")[0]
    assert "<span>Manga</span>" in cinta
    # Es decorativa: no se anuncia.
    assert '<div class="cinta-marcha" aria-hidden="true">' in contenido


def test_entre_papel_y_noche_va_la_cinta_con_el_nombre_de_la_seccion(client, cliente, shonen):
    con_etiqueta(shonen)
    SeccionPortada.objects.create(etiqueta=shonen, orden=3)
    SeccionPortada.objects.create(etiqueta=shonen, titulo="Lo más leído", orden=4)

    contenido = portada(client, cliente).content.decode()

    # Recién llegados (noche), Shonen (papel), Lo más leído (noche): una cinta.
    assert contenido.count('<div class="cinta-marcha"') == 1
    assert "<span>Lo más leído</span>" in contenido


def test_la_tienda_trae_el_telon_y_apaga_la_transicion_nativa(client):
    """El barrido en negro no depende de la transición del navegador (B-07-055)."""
    from pathlib import Path

    from django.conf import settings

    contenido = client.get(URL_CATALOGO).content.decode()
    assert '<div class="telon" data-telon aria-hidden="true">' in contenido
    hoja = (Path(settings.BASE_DIR) / "static/css/escaparate.css").read_text(encoding="utf-8")
    assert "@view-transition { navigation: none; }" in hoja
    assert "prefers-reduced-motion: reduce" in hoja.partition(".telon {")[2]


def test_la_ficha_es_un_expediente_con_el_sello_del_estado(client):
    disponible = ProductoFactory(titulo="Berserk", volumen=7, stock=2)
    preventa = ProductoFactory(titulo="Kaiju", estado=Producto.PRE_VENTA)

    ficha = client.get(reverse("core:tienda_producto", args=[disponible.pk])).content.decode()
    assert f"Expediente Nº {disponible.codigo}" in ficha
    assert "hoja-expediente__sello--disponible" in ficha and ">En stock<" in ficha
    assert "Tomo<b>07</b>" in ficha

    ficha = client.get(reverse("core:tienda_producto", args=[preventa.pk])).content.decode()
    assert "hoja-expediente__sello--pre_venta" in ficha


def test_la_ficha_avisa_cuando_no_se_pueden_agregar_mas_unidades(client, cliente):
    """Pedido del responsable (2026-11-11): el «+» de la ficha dice por qué no sube."""
    producto = ProductoFactory(titulo="Berserk", stock=3)
    client.force_login(cliente)
    url = reverse("core:tienda_producto", args=[producto.pk])

    ficha = client.get(url).content.decode()
    assert 'max="3"' in ficha
    assert "no hay más unidades: hay 3 en stock." in ficha

    client.post(reverse("tienda:agregar", args=[producto.pk]), {"cantidad": "2"})
    ficha = client.get(url).content.decode()
    # El tope descuenta lo que ya está en el carrito.
    assert 'max="1"' in ficha
    assert "Hay 3 en stock y ya tenés 2 en el carrito." in ficha

    client.post(reverse("tienda:agregar", args=[producto.pk]), {"cantidad": "1"})
    ficha = client.get(url).content.decode()
    assert "Ya tenés en el carrito todo el stock" in ficha
    assert (
        'name="cantidad"'
        not in ficha.partition("ficha-publica__compra")[2].partition("</div>\n        </div>")[0]
    )


def test_CO253_cambiar_la_imagen_de_una_seccion_registra_la_anterior(client_admin, shonen):
    """Plan 16, segunda parte: el log dice qué imagen tenía antes (B-16-005)."""
    seccion = SeccionPortada.objects.create(etiqueta=shonen, orden=3, imagen="filas/vieja.webp")

    client_admin.post(
        URL_CONFIGURAR,
        {
            **formset(
                {"id": str(seccion.pk), "origen": f"e:{shonen.pk}", "orden": "3", "activa": "on"},
                existentes=1,
            ),
            "form-0-imagen": imagen(),
        },
    )

    seccion.refresh_from_db()
    assert {
        "campo": "imagen de Shonen",
        "antes": "filas/vieja.webp",
        "despues": seccion.imagen.name,
        "imagen": True,
    } in auditoria().cambios
