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
    with patch.object(integraciones, "pedir", return_value=sin_conexion):
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
