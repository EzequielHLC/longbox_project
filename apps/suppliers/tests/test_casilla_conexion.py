"""Cómo se conecta la casilla de novedades: SSL siempre, salvo el correo de prueba local.

El `conftest` corta `casilla.abrir` en todas las pruebas; acá se prueba la función
de verdad, guardada al importar, con `imaplib` reemplazado.
"""

from unittest.mock import patch

import pytest

from apps.suppliers import casilla
from apps.suppliers.casilla import abrir as abrir_de_verdad


@pytest.fixture
def casilla_configurada(settings):
    settings.CASILLA_PUERTO = 1143
    settings.CASILLA_USUARIO = "casilla"
    settings.CASILLA_CLAVE = "prueba"
    settings.CASILLA_CARPETA = "INBOX"
    return settings


def test_con_ssl_abre_imap_con_ssl(casilla_configurada):
    casilla_configurada.CASILLA_HOST = "imap.gmail.com"
    casilla_configurada.CASILLA_SSL = True

    with patch.object(casilla.imaplib, "IMAP4_SSL") as con_ssl:
        abrir_de_verdad()

    con_ssl.assert_called_once_with("imap.gmail.com", 1143, timeout=casilla.TIEMPO_DE_ESPERA)
    con_ssl.return_value.login.assert_called_once_with("casilla", "prueba")


@pytest.mark.parametrize("host", ["127.0.0.1", "localhost"])
def test_sin_ssl_abre_imap_plano_con_el_correo_de_prueba_local(casilla_configurada, host):
    casilla_configurada.CASILLA_HOST = host
    casilla_configurada.CASILLA_SSL = False

    with (
        patch.object(casilla.imaplib, "IMAP4") as plano,
        patch.object(casilla.imaplib, "IMAP4_SSL") as con_ssl,
    ):
        abrir_de_verdad()

    plano.assert_called_once()
    con_ssl.assert_not_called()


def test_sin_ssl_con_una_casilla_de_afuera_se_rechaza_sin_conectar(casilla_configurada):
    """La clave viajaría en claro por internet."""
    casilla_configurada.CASILLA_HOST = "imap.gmail.com"
    casilla_configurada.CASILLA_SSL = False

    with (
        patch.object(casilla.imaplib, "IMAP4") as plano,
        pytest.raises(casilla.CasillaSinCifrar),
    ):
        abrir_de_verdad()

    plano.assert_not_called()
