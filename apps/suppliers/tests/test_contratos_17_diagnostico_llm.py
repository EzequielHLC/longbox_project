"""Pruebas de contrato de CU-CFG-LLM: `CO-214`, `CO-149` y `CO-150`.

El comportamiento de la pantalla está en `test_diagnostico_llm.py`. Acá, lo que
los contratos declaran: qué se consulta sin modificar nada, qué queda en el log
—con la configuración vigente y **sin la credencial**— y, sobre todo, la
postcondición negativa central de `CO-149`: el diagnóstico no toca el catálogo
ni genera borradores. La red está cortada: se parchea la puerta HTTP.
"""

import pytest

from apps.accounts.tests.factories import UsuarioFactory
from apps.catalog.models import BorradorProducto, Producto
from apps.catalog.tests.factories import ProductoFactory
from apps.core import integraciones
from apps.core.models import ConfiguracionSistema, RegistroAuditoria
from apps.suppliers.tests.test_diagnostico_llm import (
    CATALOGO,
    CONTENIDO,
    URL,
    contestando,
    extraccion_valida,
    producto,
)

pytestmark = pytest.mark.django_db

CLAVE = "sk-secreta-0123456789"


@pytest.fixture
def configurado(db):
    configuracion = ConfiguracionSistema.obtener()
    configuracion.llm_modo = configuracion.REMOTO
    configuracion.llm_url = "https://modelos.test/v1/chat/completions"
    configuracion.llm_modelo = "qwen/qwen3.5-9b"
    configuracion.llm_api_key = CLAVE
    configuracion.save()
    return configuracion


def auditorias(accion):
    return RegistroAuditoria.objects.filter(accion=accion)


def rechazo(codigo):
    return integraciones.Respuesta(motivo=integraciones.RECHAZADO, estado_http=codigo)


# ---------------------------------------------------------------------------
# CO-214 · consultarConfiguracionDeDiagnostico
# ---------------------------------------------------------------------------


def test_CO214_presenta_la_configuracion_con_la_credencial_enmascarada(client_admin, configurado):
    with contestando(CATALOGO):
        respuesta = client_admin.get(URL)

    contenido = respuesta.content.decode()
    assert "modelos.test" in contenido
    assert CLAVE not in contenido
    assert CLAVE[-4:] in contenido
    assert respuesta.context["form"]["contenido"].value()


def test_CO214_no_modifica_nada(client_admin, configurado):
    with contestando(CATALOGO):
        client_admin.get(URL)

    assert not auditorias(RegistroAuditoria.DIAGNOSTICO_LLM).exists()
    assert not auditorias(RegistroAuditoria.DISPONIBILIDAD_LLM).exists()


# ---------------------------------------------------------------------------
# CO-149 · ejecutarDiagnosticoDelModelo
# ---------------------------------------------------------------------------


def test_CO149_no_modifica_el_catalogo_ni_genera_borradores(client_admin, configurado):
    """Postcondición negativa explícita y central del contrato."""
    existente = ProductoFactory(titulo="Berserk Deluxe", volumen=5)
    productos_antes = Producto.objects.count()

    with contestando(CATALOGO, extraccion_valida([producto(), producto(volumen="6")])):
        client_admin.post(URL, {"contenido": CONTENIDO})

    existente.refresh_from_db()
    assert Producto.objects.count() == productos_antes
    assert existente.titulo == "Berserk Deluxe"
    assert not BorradorProducto.objects.exists()


def test_CO149_la_salida_trae_prompt_crudo_validacion_tiempo_y_version(client_admin, configurado):
    with contestando(CATALOGO, extraccion_valida()):
        respuesta = client_admin.post(URL, {"contenido": CONTENIDO})

    resultado = respuesta.context["resultado"]
    assert respuesta.context["prompt"]
    assert resultado.crudo
    assert resultado.productos
    assert resultado.version_prompt in respuesta.content.decode()
    assert resultado.milisegundos >= 0


def test_CO149_queda_en_el_log_con_la_configuracion_y_sin_la_credencial(
    client_admin, configurado, administrador
):
    with contestando(CATALOGO, extraccion_valida()):
        client_admin.post(URL, {"contenido": CONTENIDO})

    registro = auditorias(RegistroAuditoria.DIAGNOSTICO_LLM).get()
    assert registro.actor == administrador
    assert "Remoto" in registro.detalle or "remoto" in registro.detalle
    assert "https://modelos.test/v1/chat/completions" in registro.detalle
    assert "qwen/qwen3.5-9b" in registro.detalle
    assert "1 producto(s)" in registro.detalle
    assert CLAVE not in registro.detalle
    assert CLAVE[-4:] not in registro.detalle


def test_CO149_E1_sin_respuesta_tambien_queda_registrado(client_admin, configurado):
    with contestando(None):
        respuesta = client_admin.post(URL, {"contenido": CONTENIDO})

    assert "verifique que el servidor" in respuesta.content.decode()
    assert "Sin respuesta" in auditorias(RegistroAuditoria.DIAGNOSTICO_LLM).get().detalle


@pytest.mark.parametrize(
    "codigo, texto",
    [
        (401, "rechazó la credencial"),
        (402, "no tiene crédito"),
        (429, "limitando los pedidos"),
    ],
)
def test_CO149_E2_E3_rechazos_distinguidos(client_admin, configurado, codigo, texto):
    with contestando(rechazo(codigo)):
        respuesta = client_admin.post(URL, {"contenido": CONTENIDO})

    assert texto in respuesta.content.decode()
    detalle = auditorias(RegistroAuditoria.DIAGNOSTICO_LLM).get().detalle
    assert f"HTTP {codigo}" in detalle


def test_CO149_E4_el_modelo_configurado_no_existe(client_admin, configurado):
    with contestando({"data": [{"id": "otro/modelo"}]}):
        respuesta = client_admin.post(URL, {"accion": "disponibilidad"})

    assert respuesta.context["estado"].modelo_disponible is False
    assert "otro/modelo" in respuesta.content.decode()


def test_CO149_E5_contenido_invalido_se_informa_como_reparo(client_admin, configurado):
    with contestando(CATALOGO, extraccion_valida([producto(isbn="9789878271580")])):
        respuesta = client_admin.post(URL, {"contenido": CONTENIDO})

    assert respuesta.context["resultado"].productos[0].reparos
    assert "1 con reparos" in auditorias(RegistroAuditoria.DIAGNOSTICO_LLM).get().detalle


def test_CO149_E6_formato_ininterpretable_muestra_el_crudo(client_admin, configurado):
    ilegible = {"choices": [{"message": {"content": "esto no es JSON"}}]}

    with contestando(CATALOGO, ilegible):
        respuesta = client_admin.post(URL, {"contenido": CONTENIDO})

    assert "esto no es JSON" in respuesta.content.decode()
    assert "ininterpretable" in auditorias(RegistroAuditoria.DIAGNOSTICO_LLM).get().detalle


# ---------------------------------------------------------------------------
# CO-150 · verificarDisponibilidadDelModelo
# ---------------------------------------------------------------------------


def test_CO150_comprueba_sin_extraccion_y_queda_en_el_log(client_admin, configurado):
    with contestando(CATALOGO) as pedir:
        respuesta = client_admin.post(URL, {"accion": "disponibilidad"})

    assert pedir.call_count == 1
    assert "resultado" not in respuesta.context
    registro = auditorias(RegistroAuditoria.DISPONIBILIDAD_LLM).get()
    assert "En línea" in registro.detalle
    assert CLAVE not in registro.detalle
    assert not auditorias(RegistroAuditoria.DIAGNOSTICO_LLM).exists()


@pytest.mark.parametrize(
    "respuesta_http, texto",
    [(None, "Sin respuesta"), (rechazo(401), "HTTP 401"), (rechazo(429), "HTTP 429")],
)
def test_CO150_E1_a_E3_quedan_registrados(client_admin, configurado, respuesta_http, texto):
    with contestando(respuesta_http):
        client_admin.post(URL, {"accion": "disponibilidad"})

    assert texto in auditorias(RegistroAuditoria.DISPONIBILIDAD_LLM).get().detalle


def test_CO150_no_modifica_el_dominio(client_admin, configurado):
    with contestando(CATALOGO):
        client_admin.post(URL, {"accion": "disponibilidad"})

    assert not BorradorProducto.objects.exists()


# ---------------------------------------------------------------------------
# Control de acceso
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("rol", ["cajero", "cliente"])
def test_CO149_CO150_otro_rol_no_diagnostica(client, configurado, rol):
    client.force_login(UsuarioFactory(rol=rol))

    with contestando(CATALOGO, extraccion_valida()) as pedir:
        client.post(URL, {"contenido": CONTENIDO})
        client.post(URL, {"accion": "disponibilidad"})

    assert pedir.call_count == 0
    assert not auditorias(RegistroAuditoria.DIAGNOSTICO_LLM).exists()
    assert not auditorias(RegistroAuditoria.DISPONIBILIDAD_LLM).exists()
