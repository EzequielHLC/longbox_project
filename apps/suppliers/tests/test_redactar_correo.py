"""Lo que arma `scripts/demo/redactar_correo.py` lo lee el sistema (plan 00 del circuito, H).

La herramienta no es parte del sistema, pero si su correo no se pudiera leer la
demostración probaría otra cosa. Se arma un correo con tabla y portada y se lo
pasa por la misma ingesta que usa la casilla.
"""

import importlib.util
from pathlib import Path

import pytest

from apps.catalog.tests.factories import EditorialFactory
from apps.suppliers import correos, services
from apps.suppliers.models import CorreoProveedor
from apps.suppliers.tests.factories import ProveedorFactory

RUTA = Path(__file__).resolve().parents[3] / "scripts" / "demo" / "redactar_correo.py"
PNG = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00"
    b"\x1f\x15\xc4\x89\x00\x00\x00\rIDATx\x9cc\xf8\x0f\x00\x00\x01\x01\x00\x05\x18\xd8N\x00"
    b"\x00\x00\x00IEND\xaeB`\x82"
)


@pytest.fixture(scope="module")
def redactor():
    especificacion = importlib.util.spec_from_file_location("redactar_correo", RUTA)
    modulo = importlib.util.module_from_spec(especificacion)
    especificacion.loader.exec_module(modulo)
    return modulo


def _datos(**cambios):
    datos = {
        "de": "novedades@ivrea.test",
        "asunto": "Novedades de marzo 2027",
        "cuerpo": "Estimados,\n\nLas novedades de marzo 2027.",
        "con_tabla": "1",
        "titulo_0": "Berserk Deluxe",
        "tomo_0": "5",
        "precio_0": "24900",
        "titulo_1": "Vagabond",
        "tomo_1": "2",
    }
    datos.update(cambios)
    return datos


def test_el_correo_redactado_conserva_la_tabla_y_la_portada(redactor):
    correo = redactor.armar(_datos(), {0: (PNG, "image/png")}, para="casilla@longbox.demo")

    leido = correos.leer(bytes(correo))

    filas = [linea for linea in leido.contenido.splitlines() if linea.startswith("|")]
    assert any("Berserk Deluxe" in fila and "[imagen:" in fila for fila in filas)
    assert any("Vagabond" in fila for fila in filas)
    assert len(leido.imagenes) == 1
    assert "marzo 2027" in leido.contenido


def test_sin_tabla_sale_sólo_el_texto(redactor):
    correo = redactor.armar(
        _datos(con_tabla=""), {0: (PNG, "image/png")}, para="casilla@longbox.demo"
    )

    leido = correos.leer(bytes(correo))

    assert not any(linea.startswith("|") for linea in leido.contenido.splitlines())
    assert leido.imagenes == []


@pytest.mark.django_db
def test_el_correo_redactado_entra_a_la_cola_del_proveedor(redactor):
    proveedor = ProveedorFactory(
        correo_comercial="novedades@ivrea.test", editorial=EditorialFactory(nombre="Ivrea")
    )
    correo = redactor.armar(_datos(), {}, para="casilla@longbox.demo")

    resultado = services.ingerir(bytes(correo))

    assert resultado.ingresado
    assert resultado.correo.proveedor == proveedor
    assert resultado.correo.estado == CorreoProveedor.PENDIENTE


def test_el_formulario_se_lee_sin_el_modulo_cgi(redactor):
    limite = "----limite"
    cuerpo = (
        (
            f'--{limite}\r\nContent-Disposition: form-data; name="asunto"\r\n\r\nReprogramación\r\n'
            f'--{limite}\r\nContent-Disposition: form-data; name="portada_0"; '
            'filename="tapa.png"\r\nContent-Type: image/png\r\n\r\n'
        ).encode()
        + PNG
        + f"\r\n--{limite}--\r\n".encode()
    )

    datos, portadas = redactor.leer_formulario(f"multipart/form-data; boundary={limite}", cuerpo)

    # Sin `charset` declarado, como lo manda el navegador: es UTF-8.
    assert datos["asunto"] == "Reprogramación"
    assert portadas[0] == (PNG, "image/png")
