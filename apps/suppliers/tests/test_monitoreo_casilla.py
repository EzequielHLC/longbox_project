"""`CO-016 ejecutarCicloMonitoreoCasilla` (plan 00, A1).

La casilla se reemplaza por una conexión de mentira: `casilla.abrir` es la única
salida, y el `conftest` la corta para todas las pruebas.
"""

from datetime import timedelta
from io import StringIO
from unittest.mock import patch

import pytest
from django.core.management import call_command
from django.utils import timezone

from apps.catalog.tests.factories import EditorialFactory
from apps.core.models import ConfiguracionSistema
from apps.suppliers import casilla
from apps.suppliers.models import CorreoProveedor
from apps.suppliers.tests import correos_de_ejemplo as ejemplo
from apps.suppliers.tests.factories import ProveedorFactory

pytestmark = pytest.mark.django_db


class CasillaDeMentira:
    """Lo que `imaplib` contesta, con los mensajes que se le den."""

    def __init__(self, *mensajes):
        self.mensajes = {str(i + 1).encode(): m for i, m in enumerate(mensajes)}
        self.leidos = []
        self.cerrada = False

    def search(self, charset, criterio):
        return "OK", [b" ".join(n for n in self.mensajes if n not in self.leidos)]

    def fetch(self, numero, partes):
        return "OK", [(b"1 (BODY[] {10}", self.mensajes[numero]), b")"]

    def store(self, numero, operacion, bandera):
        self.leidos.append(numero)
        return "OK", []

    def logout(self):
        self.cerrada = True


@pytest.fixture
def ivrea():
    return ProveedorFactory(
        razon_social="Editorial Ivrea",
        correo_comercial="novedades@ivrea.test",
        editorial=EditorialFactory(nombre="Ivrea"),
    )


@pytest.fixture
def configurada(settings):
    settings.CASILLA_HOST = "imap.prueba.test"
    settings.CASILLA_USUARIO = "novedades@longbox.test"
    return settings


def _con(*mensajes):
    falsa = CasillaDeMentira(*mensajes)
    return falsa, patch.object(casilla, "abrir", return_value=falsa)


def test_CO016_encola_lo_de_un_proveedor_habilitado_sin_procesarlo(
    ivrea, configurada, administrador, mailoutbox
):
    falsa, parche = _con(ejemplo.correo_de_novedades())

    with parche:
        resumen = casilla.ciclo()

    correo = CorreoProveedor.objects.get()
    assert resumen.ingresados == [correo]
    assert correo.proveedor == ivrea
    assert correo.estado == CorreoProveedor.PENDIENTE
    assert falsa.leidos == [b"1"]
    assert falsa.cerrada is True
    assert any(m.to == [administrador.email] and "cola" in m.subject for m in mailoutbox)


def test_CO016_E1_un_remitente_no_registrado_no_se_encola_y_el_ciclo_sigue(ivrea, configurada):
    _, parche = _con(
        ejemplo.correo_de_novedades(remitente="spam@cualquiera.test", message_id="<a@x.test>"),
        ejemplo.correo_de_novedades(),
    )

    with parche:
        resumen = casilla.ciclo()

    assert resumen.descartados == 1
    assert len(resumen.ingresados) == 1


def test_CO016_I16_correr_dos_veces_no_encola_dos_veces(ivrea, configurada):
    mensaje = ejemplo.correo_de_novedades()
    for _ in range(2):
        ConfiguracionSistema.objects.update(casilla_revisada_en=None)
        _, parche = _con(mensaje)
        with parche:
            casilla.ciclo()

    assert CorreoProveedor.objects.count() == 1


def test_CO016_E3_sin_conexion_avisa_al_administrador_y_no_encola(
    ivrea, configurada, administrador, mailoutbox
):
    resumen = casilla.ciclo()  # el conftest corta la casilla

    assert resumen.estado == "sin conexión"
    assert not CorreoProveedor.objects.exists()
    assert any("No se pudo leer la casilla" in m.subject for m in mailoutbox)
    assert ConfiguracionSistema.obtener().casilla_revisada_en is None  # se reintenta


def test_CO016_respeta_la_frecuencia_configurada(ivrea, configurada):
    ConfiguracionSistema.obtener()
    ConfiguracionSistema.objects.update(
        frecuencia_casilla_horas=24, casilla_revisada_en=timezone.now() - timedelta(hours=2)
    )
    falsa, parche = _con(ejemplo.correo_de_novedades())

    with parche:
        resumen = casilla.ciclo()

    assert resumen.estado == "no corresponde todavía"
    assert not CorreoProveedor.objects.exists()
    assert falsa.leidos == []


def test_CO016_sin_casilla_configurada_no_hace_nada(ivrea):
    assert casilla.ciclo().estado == "sin configurar"


def test_CO016_corre_en_el_temporizador(ivrea, configurada):
    _, parche = _con(ejemplo.correo_de_novedades())
    salida = StringIO()

    with parche:
        call_command("ejecutar_temporizador", stdout=salida)

    assert "casilla: 1 a la cola" in salida.getvalue()
    assert CorreoProveedor.objects.count() == 1
