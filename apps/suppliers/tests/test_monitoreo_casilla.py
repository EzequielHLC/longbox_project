"""`CO-016 ejecutarCicloMonitoreoCasilla` (plan 00, A1).

La casilla se reemplaza por una conexión de mentira: `casilla.abrir` es la única
salida, y el `conftest` la corta para todas las pruebas.
"""

from datetime import timedelta
from io import StringIO
from unittest.mock import patch

import pytest
from django.core.management import call_command
from django.urls import reverse
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
        frecuencia_casilla_minutos=60, casilla_revisada_en=timezone.now() - timedelta(minutes=20)
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


# ---------------------------------------------------------------------------
# `manage.py revisar_casilla` (plan 00 del circuito, H)
# ---------------------------------------------------------------------------


def test_CO016_revisar_casilla_saltea_la_frecuencia(ivrea, configurada):
    ConfiguracionSistema.obtener()
    ConfiguracionSistema.objects.update(
        frecuencia_casilla_minutos=60, casilla_revisada_en=timezone.now() - timedelta(minutes=20)
    )
    _, parche = _con(ejemplo.correo_de_novedades())
    salida = StringIO()

    with parche:
        call_command("revisar_casilla", stdout=salida)

    assert "1 a la cola" in salida.getvalue()
    correo = CorreoProveedor.objects.get()
    # Sólo encola: el procesamiento lo dispara una persona (CO-017).
    assert correo.estado == CorreoProveedor.PENDIENTE


def test_CO016_revisar_casilla_si_corresponde_respeta_la_frecuencia(ivrea, configurada):
    """B-04-015: respeta la frecuencia, como el reloj por minuto de la VM."""
    ConfiguracionSistema.obtener()
    ConfiguracionSistema.objects.update(
        frecuencia_casilla_minutos=5, casilla_revisada_en=timezone.now() - timedelta(minutes=2)
    )
    falsa, parche = _con(ejemplo.correo_de_novedades())
    salida = StringIO()

    with parche:
        call_command("revisar_casilla", "--si-corresponde", stdout=salida)

    assert "no corresponde" in salida.getvalue()
    assert falsa.leidos == [] and not CorreoProveedor.objects.exists()

    ConfiguracionSistema.objects.update(casilla_revisada_en=timezone.now() - timedelta(minutes=6))
    with parche:
        call_command("revisar_casilla", "--si-corresponde", stdout=salida)

    assert CorreoProveedor.objects.count() == 1


def test_CO016_escuchar_al_bot_vigila_la_casilla(ivrea, configurada, settings):
    """B-04-015: en esta PC, `telegram escuchar` revisa la casilla entre consulta y consulta."""
    from apps.avisos.tests.telegram_falso import TOKEN, telegram_falso

    settings.TELEGRAM_BOT_TOKEN = TOKEN
    _, casilla_falsa = _con(ejemplo.correo_de_novedades())
    falso, red = telegram_falso()
    salida = StringIO()

    with casilla_falsa, red:
        call_command("telegram", "escuchar", "--una-vez", stdout=salida)

    assert "1 correo(s) nuevo(s)" in salida.getvalue()
    assert CorreoProveedor.objects.get().estado == CorreoProveedor.PENDIENTE


def test_escuchar_sigue_aunque_la_casilla_falle(ivrea, configurada, settings):
    from apps.avisos.tests.telegram_falso import TOKEN, telegram_falso

    settings.TELEGRAM_BOT_TOKEN = TOKEN
    falso, red = telegram_falso()
    salida = StringIO()

    with red, patch.object(casilla, "ciclo", side_effect=RuntimeError("rota")):
        call_command("telegram", "escuchar", "--una-vez", stdout=salida)

    # El reloj sigue con las otras tareas: el resumen y la salud corren igual.
    assert "casilla: fall" in salida.getvalue()


def test_revisar_casilla_sin_configurar_lo_dice(ivrea):
    salida = StringIO()

    call_command("revisar_casilla", stdout=salida)

    assert "sin configurar" in salida.getvalue()


# ---------------------------------------------------------------------------
# «Revisar la casilla» desde la cola (B-04-013)
# ---------------------------------------------------------------------------

URL_REVISAR = "/proveedores/correos/revisar/"


def test_CO016_el_boton_de_la_cola_encola_sin_esperar_la_frecuencia(
    client_admin, ivrea, configurada
):
    ConfiguracionSistema.obtener()
    ConfiguracionSistema.objects.update(
        frecuencia_casilla_minutos=60, casilla_revisada_en=timezone.now() - timedelta(minutes=20)
    )
    _, parche = _con(ejemplo.correo_de_novedades())

    with parche:
        respuesta = client_admin.post(reverse("suppliers:correo_revisar"), follow=True)

    correo = CorreoProveedor.objects.get()
    assert correo.estado == CorreoProveedor.PENDIENTE  # sólo encola (CO-017 lo decide una persona)
    assert "1 correo nuevo en la cola" in respuesta.content.decode()
    assert ConfiguracionSistema.obtener().casilla_revisada_en > timezone.now() - timedelta(
        minutes=1
    )


def test_el_boton_sin_correos_nuevos_lo_dice(client_admin, ivrea, configurada):
    _, parche = _con()

    with parche:
        respuesta = client_admin.post(reverse("suppliers:correo_revisar"), follow=True)

    assert "no hay correos nuevos" in respuesta.content.decode()


def test_el_boton_sin_conexion_avisa_y_no_encola(client_admin, ivrea, configurada):
    respuesta = client_admin.post(reverse("suppliers:correo_revisar"), follow=True)

    assert "No se pudo conectar a la casilla" in respuesta.content.decode()
    assert not CorreoProveedor.objects.exists()


def test_sin_casilla_configurada_la_cola_no_ofrece_el_boton(client_admin, ivrea):
    html = client_admin.get(reverse("suppliers:correo_lista")).content.decode()
    respuesta = client_admin.post(reverse("suppliers:correo_revisar"), follow=True)

    assert reverse("suppliers:correo_revisar") not in html
    assert "no está configurada" in respuesta.content.decode()


def test_con_casilla_configurada_la_cola_ofrece_el_boton(client_admin, ivrea, configurada):
    html = client_admin.get(reverse("suppliers:correo_lista")).content.decode()

    assert reverse("suppliers:correo_revisar") in html
    assert "Revisar la casilla" in html


def test_el_cajero_no_revisa_la_casilla_por_la_direccion_real(client, cajero, ivrea, configurada):
    client.force_login(cajero)
    falsa, parche = _con(ejemplo.correo_de_novedades())

    with parche:
        respuesta = client.post(URL_REVISAR)

    assert respuesta.status_code == 403
    assert falsa.leidos == []
    assert not CorreoProveedor.objects.exists()


def test_revisar_la_casilla_no_se_hace_con_get(client_admin, ivrea, configurada):
    falsa, parche = _con(ejemplo.correo_de_novedades())

    with parche:
        respuesta = client_admin.get(reverse("suppliers:correo_revisar"))

    assert respuesta.status_code == 405
    assert falsa.leidos == []
