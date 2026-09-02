"""El comando `extraer_novedades`: la puerta por la que hoy corre el pipeline.

Mientras no exista el ejecutor en segundo plano, esta es la **única** forma de
procesar un correo de la cola, así que romperlo deja el pipeline sin entrada. Y
es además el lugar donde se ve si funcionó: la diferencia entre "entendió cinco"
y "generó tres" es lo que dice si el modelo está leyendo bien o si el catálogo
ya tenía todo.

Se prueba también que **la salida sea ASCII**. La consola de Windows corre en
cp1252 y un título en japonés o un motivo con tilde la harían reventar con el
trabajo ya hecho y sin saber cuánto se procesó.
"""

import json
from io import StringIO
from unittest.mock import patch

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError

from apps.catalog.models import BorradorProducto
from apps.catalog.tests.factories import EditorialFactory, ProductoFactory, TipoFactory
from apps.core import integraciones
from apps.suppliers import extraccion, services
from apps.suppliers.models import CorreoProveedor
from apps.suppliers.tests import correos_de_ejemplo as ejemplo
from apps.suppliers.tests.factories import ProveedorFactory

BERSERK = "9789878271583"


def producto_extraido(**cambios):
    base = {
        "isbn": BERSERK,
        "titulo": "Berserk Deluxe",
        "volumen": "5",
        "formato": "Tapa dura",
        "precio": "24900",
        "fecha": "",
        "imagen": "tapa001@ivrea.test",
        "confianza": {
            campo: "alta" for campo in ("isbn", "titulo", "volumen", "formato", "precio", "fecha")
        },
    }
    base.update(cambios)
    return base


def respuesta(intencion=extraccion.NOVEDADES, productos=None, periodo=""):
    contenido = {"intencion": intencion, "periodo": periodo, "productos": productos or []}
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


def correr(*args):
    salida = StringIO()
    call_command("extraer_novedades", *args, stdout=salida, stderr=salida)
    return salida.getvalue()


@pytest.fixture
def editorial(db):
    return EditorialFactory(nombre="Ivrea")


@pytest.fixture
def tipo(db):
    return TipoFactory(nombre="Manga", usa_formato=True)


@pytest.fixture
def correo(db, editorial, tipo):
    ProveedorFactory(
        correo_comercial="novedades@ivrea.test",
        editorial=editorial,
        tipo_por_defecto=tipo,
    )
    return services.ingerir(ejemplo.correo_de_novedades()).correo


# ---------------------------------------------------------------------------
# Qué procesa y qué no
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_sin_argumentos_no_procesa_nada(correo):
    """El modelo corre local y cada pasada son minutos de GPU: un comando que
    procese todo por omisión es la forma más rápida de gastar una tarde."""
    with pytest.raises(CommandError):
        correr()

    assert BorradorProducto.objects.count() == 0


@pytest.mark.django_db
def test_un_correo_inexistente_lo_dice_en_vez_de_callarse(db):
    with pytest.raises(CommandError):
        correr("--correo", "9999")


@pytest.mark.django_db
def test_procesa_el_correo_que_se_le_nombra(correo):
    with contestando(respuesta(productos=[producto_extraido()])):
        salida = correr("--correo", str(correo.pk))

    assert BorradorProducto.objects.count() == 1
    assert "1 borrador(es)" in salida


@pytest.mark.django_db
def test_con_pendientes_recorre_la_cola(correo):
    with contestando(respuesta(productos=[producto_extraido()])):
        correr("--pendientes")

    assert BorradorProducto.objects.count() == 1


@pytest.mark.django_db
def test_una_cola_vacia_lo_informa(db):
    salida = correr("--pendientes")

    assert "No hay correos que procesar" in salida


# ---------------------------------------------------------------------------
# El reporte
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_informa_por_separado_lo_entendido_y_lo_generado(correo, editorial, tipo):
    """Es la diferencia que dice si el pipeline está funcionando o si el
    catálogo ya tenía todo."""
    ProductoFactory(isbn=BERSERK, editorial=editorial, tipo=tipo)

    with contestando(respuesta(productos=[producto_extraido()])):
        salida = correr("--correo", str(correo.pk))

    assert "1 productos" in salida
    assert "0 borrador(es)" in salida
    assert "1 ya en el catalogo" in salida


@pytest.mark.django_db
def test_enumera_lo_omitido_con_su_motivo(correo, editorial, tipo):
    ProductoFactory(isbn=BERSERK, editorial=editorial, tipo=tipo)

    with contestando(respuesta(productos=[producto_extraido()])):
        salida = correr("--correo", str(correo.pk))

    assert "Ya esta en el catalogo" in salida


@pytest.mark.django_db
def test_informa_los_reparos_del_modelo(correo):
    with contestando(respuesta(productos=[producto_extraido(imagen="inventada@x.test")])):
        salida = correr("--correo", str(correo.pk))

    assert "Portada inexistente" in salida


@pytest.mark.django_db
def test_un_correo_que_no_era_de_novedades_lo_aclara(correo):
    """Sin esta línea, cero borradores se leería como un fallo del pipeline."""
    with contestando(respuesta(intencion=extraccion.OTRO)):
        salida = correr("--correo", str(correo.pk))

    assert "no era un correo de novedades" in salida


@pytest.mark.django_db
def test_si_el_modelo_esta_caido_lo_dice_y_no_genera_nada(correo):
    with contestando(None):
        salida = correr("--correo", str(correo.pk))

    assert "modelo de lenguaje" in salida
    assert BorradorProducto.objects.count() == 0
    correo.refresh_from_db()
    assert correo.estado == CorreoProveedor.FALLIDO


# ---------------------------------------------------------------------------
# La salida sobrevive a la consola de Windows
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_la_salida_es_ascii_aunque_el_correo_traiga_de_todo(correo):
    """El asunto, el título y los motivos vienen del proveedor y del modelo:
    pueden traer kanji, tildes o comillas angulares. La consola corre en cp1252
    y reventaría con el trabajo ya hecho."""
    correo.asunto = "Novedades marzo — 進撃の巨人"
    correo.save(update_fields=["asunto"])

    with contestando(respuesta(productos=[producto_extraido(titulo="進撃の巨人", precio="")])):
        salida = correr("--correo", str(correo.pk))

    salida.encode("ascii")
