"""La configuración del modelo de lenguaje, y el diagnóstico de sus fallos.

Todo esto salió de una restricción del proyecto que no es técnica: **el sistema
se demuestra desplegado**, y el modelo local corre en una máquina de escritorio
que no viaja. Sin poder apuntar a un proveedor remoto desde una pantalla, la
mitad del sistema no se puede mostrar fuera de esa máquina.

Y apuntar a un proveedor remoto trajo un problema que con el modelo local no
existía: **los modos de falla dejan de ser uno solo**. Contra LM Studio, o está
corriendo o no está. Contra un proveedor pago hay clave vencida, cuota agotada,
límite de pedidos y modelo inexistente, y cada uno se arregla en un lugar
distinto. Un `None` para todos manda a buscar el problema donde no está — que es
exactamente lo que la pantalla de diagnóstico existe para evitar.

Los mensajes de abajo no son inventados: **son los que devolvió OpenRouter** al
probar el sistema contra él.
"""

import io
import json
from unittest.mock import patch
from urllib.error import HTTPError, URLError

import pytest

from apps.core import integraciones, llm
from apps.core.models import ConfiguracionSistema

pytestmark = pytest.mark.django_db

# **La función real, capturada antes de que la fixture la parchee.** `sin_red` es
# autouse y reemplaza `integraciones.pedir` en cada test, que es exactamente lo
# que queremos en todos lados menos acá: estos tests prueban `pedir` misma, así
# que necesitan la de verdad con `urlopen` parcheado un nivel más abajo.
#
# Se captura al importar el módulo, que ocurre en la recolección y por lo tanto
# antes de que corra ninguna fixture.
PEDIR_REAL = integraciones.pedir


def fallo_http(codigo, cuerpo=None):
    """Un rechazo del servidor, como lo levanta `urlopen`."""
    contenido = json.dumps(cuerpo).encode() if cuerpo is not None else b""
    return HTTPError(
        "https://proveedor.test/v1/chat/completions",
        codigo,
        "Error",
        {},
        io.BytesIO(contenido),
    )


def respondiendo(valor):
    """Parchea `urlopen`, que es lo único que la puerta HTTP toca de la red."""
    if isinstance(valor, Exception):
        return patch("apps.core.integraciones.urlopen", side_effect=valor)

    class Falsa(io.BytesIO):
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

    return patch(
        "apps.core.integraciones.urlopen",
        return_value=Falsa(json.dumps(valor).encode()),
    )


# ---------------------------------------------------------------------------
# La puerta HTTP distingue los modos de falla
# ---------------------------------------------------------------------------


def test_una_respuesta_buena_trae_los_datos():
    with respondiendo({"ok": True}):
        respuesta = PEDIR_REAL("https://x.test/v1/models", timeout=4)

    assert respuesta
    assert respuesta.datos == {"ok": True}


def test_sin_conexion_se_distingue_de_un_rechazo():
    with respondiendo(URLError("sin ruta al host")):
        respuesta = PEDIR_REAL("https://x.test/v1/models", timeout=4)

    assert not respuesta
    assert respuesta.motivo == integraciones.SIN_CONEXION
    assert respuesta.estado_http is None


def test_un_rechazo_conserva_el_codigo():
    """Es lo que antes se perdía: el servidor **contestó**, y contestó que no."""
    with respondiendo(fallo_http(401)):
        respuesta = PEDIR_REAL("https://x.test/v1/models", timeout=4)

    assert not respuesta
    assert respuesta.motivo == integraciones.RECHAZADO
    assert respuesta.estado_http == 401
    assert respuesta.no_autorizado


def test_el_cuerpo_del_error_se_conserva():
    """Los proveedores explican ahí por qué rechazaron, y sin leerlo el
    diagnóstico se queda en el número."""
    with respondiendo(fallo_http(404, {"error": {"message": "No endpoints found for x."}})):
        respuesta = PEDIR_REAL("https://x.test/v1/chat/completions", timeout=4)

    assert "No endpoints found" in respuesta.detalle


def test_una_respuesta_que_no_es_json_se_distingue():
    """Pasa cuando la dirección apunta a algo que no es la API que se cree: es
    un problema de configuración, no de red."""

    class Falsa(io.BytesIO):
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

    with patch("apps.core.integraciones.urlopen", return_value=Falsa(b"<html>error</html>")):
        respuesta = PEDIR_REAL("https://x.test/v1/models", timeout=4)

    assert respuesta.motivo == integraciones.ILEGIBLE


def _pedir_json_real(url, timeout):
    """`pedir_json` con la puerta de verdad, por el mismo motivo que `PEDIR_REAL`."""
    respuesta = PEDIR_REAL(url, timeout=timeout)
    return respuesta.datos if respuesta else None


def test_los_catalogos_siguen_recibiendo_json_o_nada():
    """`pedir_json` descarta el diagnóstico a propósito: un catálogo tiene
    respaldo local y hace lo mismo sea cual sea el motivo."""
    with respondiendo(URLError("sin red")):
        assert _pedir_json_real("https://x.test/algo", 4) is None

    with respondiendo({"data": [1]}):
        assert _pedir_json_real("https://x.test/algo", 4) == {"data": [1]}


# ---------------------------------------------------------------------------
# La configuración sale de la base, no de `settings`
# ---------------------------------------------------------------------------


def test_el_pedido_usa_la_configuracion_guardada(settings):
    """Cambiar de proveedor desde la pantalla tiene que surtir efecto sin
    reiniciar el servidor: para eso existe la pantalla."""
    settings.LLM_URL = "http://no-se-usa.test/v1/chat/completions"
    configuracion = ConfiguracionSistema.obtener()
    configuracion.llm_url = "https://proveedor.test/v1/chat/completions"
    configuracion.llm_modelo = "un/modelo"
    configuracion.llm_api_key = "clave-secreta"
    configuracion.save()

    with patch("apps.core.integraciones.pedir") as pedir:
        pedir.return_value = integraciones.Respuesta(motivo=integraciones.SIN_CONEXION)
        llm.pedir_json("sistema", "usuario")

    assert pedir.call_args.args[0] == "https://proveedor.test/v1/chat/completions"
    assert pedir.call_args.kwargs["cuerpo"]["model"] == "un/modelo"
    assert pedir.call_args.kwargs["cabeceras"]["Authorization"] == "Bearer clave-secreta"


def test_sin_clave_no_se_manda_la_cabecera():
    """Un servidor local no la pide, y algunos rechazan el pedido si llega
    vacía."""
    configuracion = ConfiguracionSistema.obtener()
    configuracion.llm_api_key = ""
    configuracion.save()

    with patch("apps.core.integraciones.pedir") as pedir:
        pedir.return_value = integraciones.Respuesta(motivo=integraciones.SIN_CONEXION)
        llm.pedir_json("sistema", "usuario")

    assert pedir.call_args.kwargs["cabeceras"] == {}


def test_el_chequeo_de_estado_manda_la_credencial():
    """Antes iba sin ella, y contra un proveedor que la exige en el catálogo de
    modelos la pantalla informaba "caído" con el servicio vivo."""
    configuracion = ConfiguracionSistema.obtener()
    configuracion.llm_api_key = "clave-secreta"
    configuracion.save()

    with patch("apps.core.integraciones.pedir") as pedir:
        pedir.return_value = integraciones.Respuesta(datos={"data": []})
        llm.estado()

    assert pedir.call_args.kwargs["cabeceras"]["Authorization"] == "Bearer clave-secreta"


# ---------------------------------------------------------------------------
# Los fallos se traducen a algo accionable
# ---------------------------------------------------------------------------


def test_una_clave_vencida_no_se_reporta_como_servicio_caido():
    """Es el fallo más probable con un proveedor remoto, y el que peor se
    diagnostica desde un mensaje genérico."""
    with patch("apps.core.integraciones.pedir") as pedir:
        pedir.return_value = integraciones.Respuesta(
            motivo=integraciones.RECHAZADO, estado_http=401, detalle="No auth credentials"
        )
        estado = llm.estado()

    assert estado.disponible is False
    assert estado.rechazado is True
    assert estado.estado_http == 401
    assert "credencial" in estado.detalle.lower()


def test_sin_credito_se_dice_con_todas_las_letras():
    with patch("apps.core.integraciones.pedir") as pedir:
        pedir.return_value = integraciones.Respuesta(
            motivo=integraciones.RECHAZADO, estado_http=402
        )
        estado = llm.estado()

    assert "crédito" in estado.detalle


def test_el_limite_de_pedidos_se_explica():
    """429 es lo habitual con los modelos gratuitos, y sin traducirlo la
    pantalla muestra un número."""
    with patch("apps.core.integraciones.pedir") as pedir:
        pedir.return_value = integraciones.Respuesta(
            motivo=integraciones.RECHAZADO, estado_http=429
        )
        estado = llm.estado()

    assert "limitando los pedidos" in estado.detalle


def test_un_modelo_inexistente_muestra_el_motivo_del_proveedor():
    """Mensaje real de OpenRouter al pedirle un identificador que no existe."""
    with patch("apps.core.integraciones.pedir") as pedir:
        pedir.return_value = integraciones.Respuesta(
            motivo=integraciones.RECHAZADO,
            estado_http=404,
            detalle="No endpoints found for google/gemini-2.0-flash-exp:free.",
        )
        estado = llm.estado()

    assert "No endpoints found" in estado.detalle


def test_una_extraccion_rechazada_no_se_confunde_con_el_servicio_caido():
    with patch("apps.core.integraciones.pedir") as pedir:
        pedir.return_value = integraciones.Respuesta(
            motivo=integraciones.RECHAZADO, estado_http=401, detalle="clave inválida"
        )
        respuesta = llm.pedir_json("sistema", "usuario")

    assert respuesta.error == llm.RECHAZADO
    assert respuesta.error != llm.SIN_SERVICIO


def test_un_error_del_proveedor_con_codigo_200_se_reconoce():
    """Pasa con los modelos gratuitos hospedados: la pasarela contesta bien y el
    fallo es del modelo de arriba. Mensaje real de OpenRouter."""
    with patch("apps.core.integraciones.pedir") as pedir:
        pedir.return_value = integraciones.Respuesta(
            datos={"error": {"message": "Upstream error from Nvidia: Service overloaded"}}
        )
        respuesta = llm.pedir_json("sistema", "usuario")

    assert respuesta.error == llm.RECHAZADO
    assert "Upstream error" in respuesta.crudo


# ---------------------------------------------------------------------------
# La clave es una credencial, no un parámetro
# ---------------------------------------------------------------------------


def test_la_clave_se_muestra_enmascarada():
    configuracion = ConfiguracionSistema.obtener()
    configuracion.llm_api_key = "sk-or-v1-0123456789abcdef"

    assert configuracion.clave_enmascarada == "…cdef"
    assert "0123456789" not in configuracion.clave_enmascarada


def test_sin_clave_no_hay_nada_que_enmascarar():
    configuracion = ConfiguracionSistema.obtener()
    configuracion.llm_api_key = ""

    assert configuracion.clave_enmascarada == ""


def test_la_direccion_del_catalogo_se_deduce_de_la_del_chat():
    """Funciona igual con LM Studio que con un proveedor remoto, porque `/v1/`
    es parte de la convención de la API que los dos implementan."""
    configuracion = ConfiguracionSistema.obtener()
    configuracion.llm_url = "https://openrouter.ai/api/v1/chat/completions"
    configuracion.save()

    with patch("apps.core.integraciones.pedir") as pedir:
        pedir.return_value = integraciones.Respuesta(datos={"data": []})
        estado = llm.estado()

    assert estado.url == "https://openrouter.ai/api/v1/models"
