"""Fixtures compartidas por los tests de todas las apps.

Vive en la raíz —y no dentro de `apps/accounts/tests/`— porque las cuentas son
transversales: los tests de `core` (panel, permisos por rol) necesitan las
mismas tres cuentas de ejemplo que los de `accounts`.
"""

from unittest.mock import patch

import pytest
from django.core.cache import cache

from apps.accounts.tests.factories import UsuarioFactory


@pytest.fixture(autouse=True)
def archivos_aparte(settings, tmp_path):
    """Lo que un test guarda en disco va a su carpeta temporal, no a `media/`.

    Sin esto, cada corrida de la suite dejaba en el `media/` de desarrollo unas
    160 portadas de borradores y correos de prueba que nadie referenciaba (plan 00
    de cierre de deuda). Un test que necesita una carpeta propia la sigue
    pisando con la suya; las fotos de devoluciones ya tenían la suya.
    """
    settings.MEDIA_ROOT = tmp_path / "media"
    settings.EVIDENCIA_ROOT = tmp_path / "privado"


@pytest.fixture(autouse=True)
def casilla_sin_configurar(settings):
    """La casilla del `.env` de quien corre las pruebas no entra en ellas.

    Con el correo de prueba levantado (`config/correo-de-prueba/`), el `.env` la
    tiene configurada, y cada prueba que corre el Temporizador intentaba leerla.
    Las que prueban la casilla la configuran con su propia fixture.
    """
    settings.CASILLA_HOST = ""
    settings.CASILLA_USUARIO = ""
    settings.CASILLA_SSL = True


@pytest.fixture(autouse=True)
def telegram_sin_configurar(settings):
    """El token del bot del `.env` de quien corre las pruebas no entra en ellas.

    Sin token el canal no existe y todo aviso sale por correo. Las pruebas del
    módulo 19 lo configuran con su propia fixture; la red sigue cortada igual.
    """
    settings.TELEGRAM_BOT_TOKEN = ""  # nosec B105 - vacío a propósito: en las pruebas no hay bot


@pytest.fixture(autouse=True)
def avisos_en_el_acto(settings):
    """Los avisos corren en el acto: el buzón de prueba se lee apenas vuelve la
    operación, sin esperar a un hilo (`apps/core/segundo_plano.py`)."""
    settings.AVISOS_EN_SEGUNDO_PLANO = False


@pytest.fixture(autouse=True)
def sin_red(request):
    """Ningún test sale a internet, ni siquiera sin querer.

    El formulario de registro pide las provincias a georef-ar-api y los códigos
    de país a otro servicio. Si los tests los consultaran de verdad, la batería
    sería lenta, fallaría cuando alguno esté caído y no correría en el CI, que
    no tiene salida. Acá se corta la llamada y todo cae al respaldo local, que
    es justamente el camino que tiene que funcionar siempre.

    Se parchea `pedir`, que es la **única** puerta de salida HTTP del proyecto:
    una integración nueva queda cubierta sin tocar este archivo. Los tests de
    cada integración vuelven a parchear por su cuenta para simular respuestas
    concretas; el parche de adentro gana.

    Corta también `localhost`, y eso no es exceso de celo: el modelo de lenguaje
    corre en la máquina del desarrollador, así que un test que lo llamara de
    verdad andaría acá —dando una falsa sensación de estar cubierto— y en el CI,
    donde ese servicio no existe, se colgaría hasta el timeout.
    """
    from apps.core import integraciones

    # La caché es global al proceso: sin limpiarla, las provincias que cachea
    # un test aparecen en el siguiente y los resultados dejan de ser fiables.
    cache.clear()
    # Se devuelve un fallo **con su motivo**, no `None`: desde que la puerta HTTP
    # distingue los modos de falla, `None` dejó de ser lo que produce una red
    # cortada. Una fixture que simula algo que el sistema ya no genera prueba un
    # camino que no existe.
    sin_conexion = integraciones.Respuesta(
        motivo=integraciones.SIN_CONEXION, detalle="Red cortada por la fixture de tests."
    )
    # La casilla de novedades no es HTTP y tiene su propia puerta (plan 00, A1).
    from apps.suppliers import casilla

    def casilla_cortada():
        raise ConnectionError("Casilla cortada por la fixture de tests.")

    with (
        patch.object(integraciones, "pedir", return_value=sin_conexion),
        # La descarga binaria (la foto de un borrador desde Telegram) es la otra
        # mitad de la misma puerta, y se corta igual.
        patch.object(integraciones, "descargar", return_value=None),
        patch.object(casilla, "abrir", side_effect=casilla_cortada),
    ):
        yield
    cache.clear()


@pytest.fixture
def cliente(db):
    return UsuarioFactory(rol="cliente")


@pytest.fixture
def cajero(db):
    return UsuarioFactory(rol="cajero")


@pytest.fixture
def administrador(db):
    return UsuarioFactory(rol="administrador")


@pytest.fixture
def client_admin(client, administrador):
    """Navegador con sesión de Administrador: el actor de todo el Módulo 13."""
    client.force_login(administrador)
    return client
