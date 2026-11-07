"""Las tarjetas de Long-bot que acompañan algunos avisos de Telegram (B-19-020).

La tarjeta sale antes del texto y nunca lo reemplaza: si no se puede dibujar, el
aviso sale igual. Telegram es el de mentira detrás de la única puerta.
"""

from io import BytesIO
from types import SimpleNamespace
from unittest.mock import patch

import pytest
from django.utils import timezone
from PIL import Image

from apps.avisos import bot, resumen, tarjetas
from apps.avisos.canales import avisar_administradores
from apps.avisos.models import RESUMEN, SISTEMA, VinculoTelegram
from apps.avisos.tests.telegram_falso import TOKEN, telegram_falso

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
    administrador.first_name = "Ezequiel Hernán"
    administrador.save(update_fields=["first_name"])
    VinculoTelegram.objects.create(usuario=administrador, chat_id=CHAT, nombre_en_telegram="Eze")
    return administrador


def _imagen(foto):
    _nombre, contenido, tipo = foto["photo"]
    assert tipo == "image/jpeg"
    return Image.open(BytesIO(contenido))


@pytest.mark.parametrize(
    "gesto", [tarjetas.CONTENTO, tarjetas.FESTEJO, tarjetas.GUINO, tarjetas.ALERTA, tarjetas.TRISTE]
)
@pytest.mark.parametrize("tono", ["senal", "alarma"])
def test_cada_gesto_y_tono_da_un_jpeg_apaisado(gesto, tono):
    imagen = Image.open(BytesIO(tarjetas.dibujar("Prueba", gesto=gesto, tono=tono)))

    assert imagen.format == "JPEG"
    assert imagen.size == (tarjetas.ANCHO, tarjetas.ALTO)


def test_un_titulo_largo_y_cifras_largas_se_achican_y_no_rompen():
    contenido = tarjetas.dibujar(
        "Un título larguísimo que no entra ni en dos renglones de ninguna manera posible",
        bajada="Una bajada " * 30,
        cifras=[("Un rótulo muy largo", "$ 123.456.789"), ("B", 2), ("C", 3), ("D", 4), ("E", 5)],
    )

    assert Image.open(BytesIO(contenido)).size == (tarjetas.ANCHO, tarjetas.ALTO)


def test_el_texto_se_corta_con_puntos_suspensivos_cuando_sobra():
    fuente = tarjetas._interfaz(30)

    renglones = tarjetas._cortar("palabra " * 80, fuente, 300, 2)

    assert len(renglones) == 2
    assert renglones[-1].endswith("…")


def test_si_no_se_puede_dibujar_no_hay_tarjeta_y_no_explota():
    with patch.object(tarjetas, "dibujar", side_effect=RuntimeError("sin fuentes")):
        assert tarjetas.tarjeta("Hola") is None


def test_la_tarjeta_sale_antes_del_texto_con_el_nombre_de_pila(vinculado, falso):
    with patch.object(tarjetas, "tarjeta", wraps=tarjetas.tarjeta) as dibujo:
        avisar_administradores(
            SISTEMA,
            asunto="a",
            titulo="Hay algo para mirar",
            parrafos=["El disco está lleno."],
            tarjeta={"titulo": "¡Hola, {nombre}!", "gesto": tarjetas.ALERTA, "tono": "alarma"},
        )

    metodos = [metodo for metodo, cuerpo in falso.llamadas if cuerpo.get("chat_id") == CHAT]
    assert metodos == ["sendPhoto", "sendMessage"]
    assert dibujo.call_args.kwargs["titulo"] == "¡Hola, Ezequiel!"
    assert _imagen(falso.fotos(CHAT)[0]).size == (tarjetas.ANCHO, tarjetas.ALTO)
    assert falso.fotos(CHAT)[0]["caption"] == ""


def test_sin_nombre_de_pila_el_titulo_pierde_la_coma(vinculado, falso):
    vinculado.first_name = ""
    vinculado.save(update_fields=["first_name"])

    with patch.object(tarjetas, "tarjeta", wraps=tarjetas.tarjeta) as dibujo:
        avisar_administradores(
            SISTEMA, asunto="a", titulo="t", parrafos=[], tarjeta={"titulo": "¡Hola, {nombre}!"}
        )

    assert dibujo.call_args.kwargs["titulo"] == "¡Hola!"


def test_si_la_tarjeta_falla_el_aviso_sale_igual_sin_foto(vinculado, falso):
    with patch.object(tarjetas, "dibujar", side_effect=RuntimeError("roto")):
        avisar_administradores(
            SISTEMA, asunto="a", titulo="El aviso", parrafos=[], tarjeta={"titulo": "x"}
        )

    assert not falso.fotos(CHAT)
    assert "El aviso" in falso.textos(CHAT)[0]


def test_un_aviso_sin_tarjeta_no_manda_fotos(vinculado, falso):
    avisar_administradores(SISTEMA, asunto="a", titulo="Sólo texto", parrafos=[])

    assert not falso.fotos(CHAT)
    assert len(falso.textos(CHAT)) == 1


def test_el_resumen_de_la_manana_lleva_su_tarjeta(vinculado, falso):
    aviso = resumen.armar(timezone.localdate())

    assert aviso["tarjeta"]["titulo"] == "¡Buen día, {nombre}!"
    assert [rotulo for rotulo, _ in aviso["tarjeta"]["cifras"]] == [
        "Por armar",
        "Correos",
        "Borradores",
        "Ventas ayer",
    ]
    # Sin nada pendiente, Long-bot festeja.
    assert aviso["tarjeta"]["gesto"] == tarjetas.FESTEJO

    avisar_administradores(RESUMEN, **aviso)

    assert len(falso.fotos(CHAT)) == 1
    assert falso.textos(CHAT)


def test_la_ayuda_presenta_a_long_bot_con_su_tarjeta(vinculado, falso):
    bot.procesar(
        {
            "update_id": 1,
            "message": {"message_id": 1, "chat": {"id": CHAT, "type": "private"}, "text": "/ayuda"},
        }
    )

    metodos = [metodo for metodo, cuerpo in falso.llamadas if cuerpo.get("chat_id") == CHAT]
    assert metodos == ["sendPhoto", "sendMessage"]


def test_el_pedido_que_no_salio_lleva_la_tarjeta_triste(vinculado, falso):
    pedido = SimpleNamespace(pk=7, nombre_proveedor="Ivrea", error_de_envio="Rebotó")

    with patch.object(tarjetas, "tarjeta", wraps=tarjetas.tarjeta) as dibujo:
        bot.mandar_pedido_sin_enviar(CHAT, pedido)

    assert dibujo.call_args.kwargs["gesto"] == tarjetas.TRISTE
    assert dibujo.call_args.args[0] == "No salió el pedido #7"
    assert "Reintentar el envío" in str(falso.mensajes(CHAT)[-1]["reply_markup"])
