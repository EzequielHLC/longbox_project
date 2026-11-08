"""B-19-021: una caída del servidor de correo se reintenta (revisión integral, R-07)."""

import smtplib
from unittest.mock import patch

import pytest
from django.core.cache import cache

from apps.avisos.models import VinculoTelegram
from apps.core import mail

pytestmark = pytest.mark.django_db

CAIDA = smtplib.SMTPServerDisconnected("Connection unexpectedly closed")


@pytest.fixture(autouse=True)
def sin_esperas():
    cache.clear()
    with patch.object(mail.time, "sleep") as dormir:
        yield dormir
    cache.clear()


@pytest.fixture
def con_telegram(administrador):
    VinculoTelegram.objects.create(usuario=administrador, chat_id=777, nombre_en_telegram="Admin")
    with (
        patch("apps.avisos.telegram.configurado", return_value=True),
        patch("apps.avisos.telegram.enviar", return_value={"message_id": 1}) as enviar,
    ):
        yield enviar


def enviar():
    mail.enviar_correo("Tu pedido A-1", "Hola", ["cliente@correo.test"])


def test_una_caida_pasajera_se_reintenta_y_sale(sin_esperas):
    with patch.object(mail.CorreoSinCortes, "send", side_effect=[CAIDA, CAIDA, 1]) as send:
        enviar()

    assert send.call_count == 3
    assert [llamada.args[0] for llamada in sin_esperas.call_args_list] == [2, 8]


def test_un_rechazo_temporal_4xx_tambien_se_reintenta():
    temporal = smtplib.SMTPDataError(451, b"Try again later")
    with patch.object(mail.CorreoSinCortes, "send", side_effect=[temporal, 1]) as send:
        enviar()

    assert send.call_count == 2


def test_un_rechazo_definitivo_no_se_reintenta(con_telegram):
    definitivo = smtplib.SMTPRecipientsRefused({"cliente@correo.test": (550, b"No such user")})
    with (
        patch.object(mail.CorreoSinCortes, "send", side_effect=definitivo) as send,
        pytest.raises(smtplib.SMTPRecipientsRefused),
    ):
        enviar()

    assert send.call_count == 1
    con_telegram.assert_not_called()


def test_tres_fallas_avisan_por_telegram_y_el_error_sigue(con_telegram):
    with (
        patch.object(mail.CorreoSinCortes, "send", side_effect=CAIDA) as send,
        pytest.raises(smtplib.SMTPServerDisconnected),
    ):
        enviar()

    assert send.call_count == 3
    (chat, texto), _ = con_telegram.call_args
    assert chat == 777
    assert "No sale el correo" in texto
    assert "Tu pedido A-1" in texto and "cliente@correo.test" in texto


def test_durante_la_misma_caida_se_avisa_una_sola_vez(con_telegram):
    with patch.object(mail.CorreoSinCortes, "send", side_effect=CAIDA):
        for _ in range(3):
            with pytest.raises(smtplib.SMTPServerDisconnected):
                enviar()

    assert con_telegram.call_count == 1
