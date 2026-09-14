"""El pipeline entero: de un `.eml` en la cola a borradores con su portada.

Los tests de `apps/catalog/tests/test_borradores.py` prueban las reglas sobre una
extracción escrita a mano. Estos prueban lo otro: que el correo real —con su
tabla de maquetado, su logo embebido y sus portadas con `Content-ID`— llegue
hasta el borrador sin perder nada en el camino.

Es el paso 7 de CU-ALT-NOV y es donde más fácil se rompe algo en silencio: si el
identificador de una portada no se normaliza igual de los dos lados, el borrador
queda con la imagen pendiente y nadie entiende por qué.

**Sigue sin llamarse al modelo:** se parchea la puerta HTTP, igual que en el
resto de la app.
"""

import json
from unittest.mock import patch

import pytest

from apps.catalog.models import BorradorProducto
from apps.core import integraciones
from apps.core.models import RegistroAuditoria
from apps.suppliers import extraccion, services
from apps.suppliers.models import CorreoProveedor
from apps.suppliers.tests import correos_de_ejemplo as ejemplo
from apps.suppliers.tests.factories import ProveedorFactory

# Los tres tomos del correo de ejemplo, con el identificador de su portada.
TAPA_BERSERK = "tapa001@ivrea.test"


def producto_extraido(**cambios):
    """Lo que el modelo devolvería para el primer tomo del correo de ejemplo."""
    base = {
        "isbn": "9789878271583",
        "titulo": "Berserk Deluxe",
        "volumen": "5",
        "formato": "Tapa dura",
        "precio": "24900",
        "fecha": "",
        "imagen": TAPA_BERSERK,
        "confianza": {
            campo: "alta" for campo in ("isbn", "titulo", "volumen", "formato", "precio", "fecha")
        },
    }
    base.update(cambios)
    return base


def respuesta(intencion=extraccion.NOVEDADES, productos=None, periodo=""):
    contenido = {
        "intencion": intencion,
        "periodo": periodo,
        "productos": productos or [],
    }
    return {"choices": [{"message": {"content": json.dumps(contenido)}}]}


def _como_respuesta(valor):
    """Envuelve lo que el servidor devolvería en el tipo que usa la puerta HTTP.

    Desde que `integraciones.pedir` distingue los modos de falla, devuelve una
    `Respuesta` y no un diccionario pelado. Los tests siguen escribiendo el JSON
    del servidor, que es lo legible, y esto lo lleva al contrato real — un test
    que parchea con la forma vieja probaría un camino que ya no existe.

    `None` se traduce a un fallo de conexión, que es lo que significaba antes.
    """
    if valor is None:
        return integraciones.Respuesta(motivo=integraciones.SIN_CONEXION)
    if isinstance(valor, integraciones.Respuesta):
        return valor
    return integraciones.Respuesta(datos=valor)


def contestando(valor):
    return patch("apps.core.integraciones.pedir", return_value=_como_respuesta(valor))


@pytest.fixture
def proveedor(db):
    """Con la cabecera cargada, que es lo normal en un proveedor operativo."""
    from apps.catalog.tests.factories import EditorialFactory, TipoFactory

    return ProveedorFactory(
        correo_comercial="novedades@ivrea.test",
        editorial=EditorialFactory(nombre="Ivrea"),
        tipo_por_defecto=TipoFactory(nombre="Manga", usa_formato=True),
    )


@pytest.fixture
def correo(db, proveedor):
    """Un correo de verdad, archivado, tal como lo dejaría la ingesta."""
    return services.ingerir(ejemplo.correo_de_novedades()).correo


# ---------------------------------------------------------------------------
# De la cola al borrador
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_procesar_un_correo_de_la_cola_deja_sus_borradores(correo):
    with contestando(respuesta(productos=[producto_extraido()])):
        services.extraer_novedades(correo)

    borrador = BorradorProducto.objects.get()
    assert borrador.titulo == "Berserk Deluxe"
    assert borrador.correo == correo
    assert borrador.estado == BorradorProducto.PENDIENTE


@pytest.mark.django_db
def test_un_correo_que_no_es_de_novedades_no_genera_borradores(correo):
    """Es lo que justifica que la cola exista: por la casilla del proveedor
    llegan facturas y saludos, y ninguno tiene que ensuciar la revisión."""
    with contestando(respuesta(intencion=extraccion.OTRO)):
        services.extraer_novedades(correo)

    assert BorradorProducto.objects.count() == 0
    correo.refresh_from_db()
    assert correo.estado == CorreoProveedor.PROCESADO


@pytest.mark.django_db
def test_si_el_modelo_no_contesta_no_se_genera_ningun_borrador(correo):
    """Un fallo del servicio no puede dejar medio borrador cargado."""
    with contestando(None):
        services.extraer_novedades(correo)

    assert BorradorProducto.objects.count() == 0
    correo.refresh_from_db()
    assert correo.estado == CorreoProveedor.FALLIDO
    # Y tampoco se audita una generación que no ocurrió.
    assert not RegistroAuditoria.objects.filter(
        accion=RegistroAuditoria.BORRADORES_GENERADOS
    ).exists()


# ---------------------------------------------------------------------------
# Paso 7 — la portada sale del propio correo
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_la_portada_embebida_termina_como_archivo_del_borrador(correo):
    """No se descarga de ninguna URL: ya vino adentro del correo (corrección 16)."""
    with contestando(respuesta(productos=[producto_extraido()])):
        services.extraer_novedades(correo)

    borrador = BorradorProducto.objects.get()
    assert borrador.portada
    assert not borrador.portada_pendiente
    # Y es la imagen de verdad, no un archivo vacío.
    assert borrador.portada.size > 0


@pytest.mark.django_db
def test_el_borrador_conserva_el_identificador_de_su_portada(correo):
    """Es lo que permite volver a sacarla del archivo original si algo sale mal,
    sin tener que adivinar cuál era."""
    with contestando(respuesta(productos=[producto_extraido()])):
        services.extraer_novedades(correo)

    assert BorradorProducto.objects.get().cid_portada == TAPA_BERSERK


@pytest.mark.django_db
def test_una_portada_inventada_deja_el_borrador_sin_imagen_y_con_su_reparo(correo):
    """La extracción ya descarta el identificador que no existe entre las partes
    del correo; acá se verifica que eso llegue hasta el borrador."""
    with contestando(respuesta(productos=[producto_extraido(imagen="inventada@x.test")])):
        services.extraer_novedades(correo)

    borrador = BorradorProducto.objects.get()
    assert borrador.portada_pendiente
    assert any("Portada inexistente" in reparo for reparo in borrador.reparos)


@pytest.mark.django_db
def test_un_producto_sin_portada_no_interrumpe_al_resto(correo):
    """CU-ALT-NOV: la portada que falta no corta el procesamiento del correo."""
    with contestando(
        respuesta(
            productos=[
                producto_extraido(imagen=""),
                producto_extraido(isbn="9789878271590", volumen="6"),
            ]
        )
    ):
        services.extraer_novedades(correo)

    borradores = list(BorradorProducto.objects.all())
    assert len(borradores) == 2
    assert borradores[0].portada_pendiente
    assert not borradores[1].portada_pendiente


@pytest.mark.django_db
def test_el_logo_del_encabezado_no_se_confunde_con_una_portada(correo):
    """El correo de ejemplo trae un logo embebido que **no** es tapa de nada. Si
    las portadas se correlacionaran por orden, correría todo un lugar."""
    with contestando(respuesta(productos=[producto_extraido()])):
        services.extraer_novedades(correo)

    borrador = BorradorProducto.objects.get()
    # La que quedó es la que el marcador de su fila nombraba, no la primera
    # imagen del correo.
    assert borrador.cid_portada == TAPA_BERSERK


@pytest.mark.django_db
def test_sin_archivo_guardado_los_borradores_salen_igual_sin_portada(correo):
    """El archivo es el respaldo, no una precondición: si faltara, la revisión
    sigue siendo posible y la portada se adjunta a mano."""
    correo.archivo.delete(save=True)

    with contestando(respuesta(productos=[producto_extraido()])):
        services.extraer_novedades(correo)

    borrador = BorradorProducto.objects.get()
    assert borrador.portada_pendiente
    assert borrador.titulo == "Berserk Deluxe"


# ---------------------------------------------------------------------------
# El período, de punta a punta
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_el_periodo_anunciado_llega_hasta_la_fecha_del_borrador(correo):
    from datetime import timedelta

    from django.utils import timezone

    futuro = timezone.localdate() + timedelta(days=45)

    with contestando(
        respuesta(productos=[producto_extraido()], periodo=f"Novedades de {futuro.isoformat()}")
    ):
        services.extraer_novedades(correo)

    borrador = BorradorProducto.objects.get()
    assert borrador.fecha_llegada == futuro
    assert borrador.nace_en_pre_venta


@pytest.mark.django_db
def test_reprocesar_un_correo_no_duplica_sus_borradores(correo):
    """Ajustar el prompt y volver a correr es el caso normal, no el raro."""
    with contestando(respuesta(productos=[producto_extraido()])):
        services.extraer_novedades(correo)
        services.extraer_novedades(correo)

    assert BorradorProducto.objects.count() == 1


# ---------------------------------------------------------------------------
# La ficha del correo
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_la_ficha_muestra_los_borradores_generados(client_admin, correo):
    """Van junto al contenido del que salieron: un borrador con el precio del
    tomo siguiente solo se nota teniendo las dos cosas a la vista."""
    from django.urls import reverse

    with contestando(respuesta(productos=[producto_extraido()])):
        services.extraer_novedades(correo)

    contenido = client_admin.get(
        reverse("suppliers:correo_detalle", args=[correo.pk])
    ).content.decode()

    assert "Borradores generados" in contenido
    assert "Berserk Deluxe" in contenido


@pytest.mark.django_db
def test_la_ficha_marca_los_borradores_incompletos(client_admin, correo):
    from django.urls import reverse

    with contestando(respuesta(productos=[producto_extraido(precio="")])):
        services.extraer_novedades(correo)

    contenido = client_admin.get(
        reverse("suppliers:correo_detalle", args=[correo.pk])
    ).content.decode()

    assert "Extracción incompleta" in contenido


@pytest.mark.django_db
def test_la_ficha_ya_no_dice_que_falta_el_extractor(client_admin, correo):
    """Decía que el procesamiento se habilitaba "cuando esté el extractor
    conectado", y el extractor existe desde que el pipeline genera borradores.
    Lo que falta es el botón, y falta por RNF-02, que es otra cosa."""
    from django.urls import reverse

    contenido = client_admin.get(
        reverse("suppliers:correo_detalle", args=[correo.pk])
    ).content.decode()

    assert "cuando esté el extractor conectado" not in contenido
    assert "extraer_novedades --correo" in contenido


@pytest.mark.django_db
def test_un_correo_sin_procesar_no_muestra_la_seccion_de_borradores(client_admin, correo):
    """Una sección vacía se leería como "no generó nada", que es distinto de
    "todavía no se procesó"."""
    from django.urls import reverse

    contenido = client_admin.get(
        reverse("suppliers:correo_detalle", args=[correo.pk])
    ).content.decode()

    assert "Borradores generados" not in contenido
