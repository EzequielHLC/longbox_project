"""`/refresh` en el bot y «Revisar la casilla» en la cola (B-19-016).

Los dos son `CO-016` en el momento: traen lo nuevo a la cola sin procesarlo, y
**reinician el reloj de la lectura automática**, porque la frecuencia cuenta desde
la última revisión, sea a pedido o automática.
"""

from datetime import timedelta

import pytest
from django.urls import reverse
from django.utils import timezone

from apps.avisos import bot
from apps.avisos.models import PreferenciaAviso, VinculoTelegram
from apps.avisos.tests.telegram_falso import TOKEN, telegram_falso
from apps.catalog.tests.factories import EditorialFactory
from apps.core.models import ConfiguracionSistema
from apps.suppliers import casilla
from apps.suppliers.models import CorreoProveedor
from apps.suppliers.tests import correos_de_ejemplo as ejemplo
from apps.suppliers.tests.factories import ProveedorFactory
from apps.suppliers.tests.test_monitoreo_casilla import _con

pytestmark = pytest.mark.django_db

CHAT = 4242


@pytest.fixture(autouse=True)
def con_telegram(settings):
    settings.TELEGRAM_BOT_TOKEN = TOKEN
    settings.URL_PUBLICA = "https://longbox.test"


@pytest.fixture
def falso():
    falso, parche = telegram_falso()
    with parche:
        yield falso


@pytest.fixture
def vinculado(administrador):
    VinculoTelegram.objects.create(usuario=administrador, chat_id=CHAT, nombre_en_telegram="Eze")
    return administrador


@pytest.fixture
def configurada(settings):
    settings.CASILLA_HOST = "imap.prueba.test"
    settings.CASILLA_USUARIO = "novedades@longbox.test"
    ProveedorFactory(
        razon_social="Editorial Ivrea",
        correo_comercial="novedades@ivrea.test",
        editorial=EditorialFactory(nombre="Ivrea"),
    )
    ConfiguracionSistema.obtener()
    # Revisada hace un minuto, cada cinco: a la lectura automática todavía no le toca.
    ConfiguracionSistema.objects.update(
        frecuencia_casilla_minutos=5, casilla_revisada_en=timezone.now() - timedelta(minutes=1)
    )
    return settings


def refresh():
    bot.procesar(
        {"update_id": 1, "message": {"chat": {"id": CHAT, "type": "private"}, "text": "/refresh"}}
    )


def test_refresh_trae_lo_nuevo_aunque_no_le_toque_y_reinicia_el_reloj(
    vinculado, configurada, falso
):
    antes = ConfiguracionSistema.obtener().casilla_revisada_en
    _, parche = _con(ejemplo.correo_de_novedades())

    with parche:
        refresh()

    assert CorreoProveedor.objects.get().estado == CorreoProveedor.PENDIENTE
    revisada = ConfiguracionSistema.obtener().casilla_revisada_en
    assert revisada > antes
    texto = falso.textos(CHAT)[-1]
    assert "1 correo(s) nuevo(s)" in texto
    proxima = timezone.localtime(revisada + timedelta(minutes=5))
    assert f"La próxima revisión automática es a las {proxima:%H:%M}" in texto
    # Reiniciado: la lectura automática ahora espera la frecuencia entera.
    with parche:
        assert casilla.ciclo().estado == "no corresponde todavía"


def test_refresh_sin_novedades_lo_dice(vinculado, configurada, falso):
    _, parche = _con()

    with parche:
        refresh()

    assert falso.textos(CHAT)[0] == "Revisando la casilla…"
    assert "no hay correos nuevos" in falso.textos(CHAT)[-1]


def test_si_los_correos_llegan_por_telegram_no_los_repite(vinculado, configurada, falso):
    PreferenciaAviso.objects.create(
        usuario=vinculado, tipo="correos", por_correo=False, por_telegram=True
    )
    _, parche = _con(ejemplo.correo_de_novedades())

    with parche:
        refresh()

    assert "Te los mandé arriba" in falso.textos(CHAT)[-1]
    assert any("Aprobar y procesar" in str(m.get("reply_markup")) for m in falso.mensajes(CHAT))


def test_si_no_llegan_por_telegram_los_lista_con_la_cola(vinculado, configurada, falso):
    _, parche = _con(ejemplo.correo_de_novedades())

    with parche:
        refresh()

    texto = falso.textos(CHAT)[-1]
    assert "✉ Editorial Ivrea" in texto and "Abrir la cola" in texto


def test_refresh_sin_casilla_configurada(vinculado, falso):
    refresh()

    assert "no está configurada" in falso.textos(CHAT)[-1]


def test_refresh_con_la_casilla_caída_lo_dice_y_no_reinicia(vinculado, configurada, falso):
    antes = ConfiguracionSistema.obtener().casilla_revisada_en

    refresh()  # la fixture de red corta `casilla.abrir`

    assert "No se pudo conectar" in falso.textos(CHAT)[-1]
    assert ConfiguracionSistema.obtener().casilla_revisada_en == antes


def test_refresh_desde_un_chat_sin_vínculo_no_revisa(configurada, falso):
    _, parche = _con(ejemplo.correo_de_novedades())

    with parche:
        refresh()

    assert "no está vinculado" in falso.textos(CHAT)[-1]
    assert not CorreoProveedor.objects.exists()


def test_refresh_está_en_el_menú_y_en_la_ayuda(vinculado, falso):
    from apps.avisos import telegram

    assert "refresh" in dict(telegram.COMANDOS)
    bot.procesar(
        {"update_id": 1, "message": {"chat": {"id": CHAT, "type": "private"}, "text": "/ayuda"}}
    )
    assert "/refresh" in falso.textos(CHAT)[-1]


def test_el_botón_de_la_cola_también_reinicia_el_reloj(client_admin, configurada):
    _, parche = _con()

    with parche:
        client_admin.post(reverse("suppliers:correo_revisar"))
        assert casilla.ciclo().estado == "no corresponde todavía"


def test_la_cola_dice_cuándo_es_la_próxima_revisión(client_admin, configurada):
    revisada = ConfiguracionSistema.obtener().casilla_revisada_en
    proxima = timezone.localtime(revisada + timedelta(minutes=5))

    html = client_admin.get(reverse("suppliers:correo_lista")).content.decode()

    assert f'La próxima, automática, a las <span class="datos">{proxima:%H:%M}</span>' in html
    assert "revisar ahora reinicia la cuenta" in html


def test_la_cola_con_la_revisión_vencida_dice_el_próximo_minuto(client_admin, configurada):
    ConfiguracionSistema.objects.update(casilla_revisada_en=timezone.now() - timedelta(hours=1))

    html = client_admin.get(reverse("suppliers:correo_lista")).content.decode()

    assert "en el próximo minuto" in html
