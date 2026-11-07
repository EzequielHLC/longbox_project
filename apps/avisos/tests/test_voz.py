"""La voz de Long-bot (B-19-017): personalidad sin tapar el dato.

Las frases varían; lo que estas pruebas fijan es lo que no puede variar: el dato,
el nombre de quien lee, el emoji del tipo y que la charla del modelo sea sólo
texto escapado, que no hace nada.
"""

import string
from datetime import date
from unittest.mock import patch

import pytest

from apps.accounts.models import Usuario
from apps.accounts.tests.factories import UsuarioFactory
from apps.avisos import asistente, bot, canales, voz
from apps.avisos.models import VinculoTelegram
from apps.avisos.tests.telegram_falso import TOKEN, telegram_falso
from apps.catalog.models import BorradorProducto
from apps.core import llm
from apps.suppliers import services
from apps.suppliers.tests import correos_de_ejemplo as ejemplo
from apps.suppliers.tests.factories import ProveedorFactory

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
    Usuario.objects.filter(pk=administrador.pk).update(first_name="Ezequiel")
    administrador.refresh_from_db()
    VinculoTelegram.objects.create(usuario=administrador, chat_id=CHAT, nombre_en_telegram="Eze")
    return administrador


def mensaje(texto):
    return {"update_id": 1, "message": {"chat": {"id": CHAT, "type": "private"}, "text": texto}}


# ---------------------------------------------------------------------------
# Las frases
# ---------------------------------------------------------------------------


def _campos(plantilla):
    return {campo for _, campo, _, _ in string.Formatter().parse(plantilla) if campo}


@pytest.mark.parametrize("clave", list(voz.FRASES))
def test_todas_las_variantes_se_arman_sin_error(clave):
    for variante in voz.FRASES[clave]:
        datos = {campo: "x" for campo in _campos(variante) - {"coma", "bot"}}
        with patch.object(voz, "elegir", return_value=variante):
            assert voz.frase(clave, nombre="Ezequiel", **datos)


def test_la_frase_lleva_el_nombre_y_sin_nombre_no_deja_la_coma():
    for variante in voz.FRASES["vinculado"]:
        with patch.object(voz, "elegir", return_value=variante):
            assert ", Ezequiel" in voz.frase("vinculado", nombre="Ezequiel")
            assert ", !" not in voz.frase("vinculado") and ",!" not in voz.frase("vinculado")


@pytest.mark.parametrize("clave", ["no_vinculado"])
def test_las_variantes_conservan_el_dato(clave):
    assert all("no está vinculado" in v for v in voz.FRASES[clave])


def test_cada_tipo_de_aviso_tiene_su_emoji():
    from apps.avisos.models import TIPOS

    assert {tipo.clave for tipo in TIPOS} <= set(voz.EMOJI)


def test_el_saludo_del_día_dice_el_día_y_el_nombre():
    saludo = voz.saludo_del_dia("Ezequiel", date(2026, 10, 28))

    assert "Ezequiel" in saludo and "miércoles 28/10" in saludo


@pytest.mark.parametrize(("pendientes", "pista"), [(0, "☕"), (2, "💪"), (9, "💪")])
def test_el_cierre_del_resumen_sigue_a_lo_pendiente(pendientes, pista):
    assert pista in voz.cierre_del_resumen(pendientes)


def test_el_nombre_de_pila_sale_del_usuario():
    assert voz.nombre_de(Usuario(first_name="Ana María")) == "Ana"
    assert voz.nombre_de(None) == ""


# ---------------------------------------------------------------------------
# Los avisos
# ---------------------------------------------------------------------------


def test_un_aviso_lleva_el_emoji_del_tipo_la_línea_y_el_remate():
    texto = canales.texto_para_telegram(
        tipo="ventas", titulo="¡Venta! Pedido 1", parrafos=["Ana"], filas=[("Total", "$ 1")]
    )

    assert texto.startswith("💸 <b>¡Venta! Pedido 1</b>\n" + voz.LINEA)
    assert "• Total: $ 1" in texto
    assert any(remate in texto for remate in voz.REMATES["ventas"])


def test_el_resumen_saluda_por_el_nombre_y_cierra_según_lo_pendiente():
    texto = canales.texto_para_telegram(
        tipo="resumen",
        titulo="Buen día",
        parrafos=[],
        nombre="Ezequiel",
        voz={"hoy": date(2026, 10, 28), "pendientes": 0},
    )

    assert texto.startswith("☀️ <b>") and "Ezequiel" in texto and "28/10" in texto
    assert "☕" in texto


def test_un_tipo_sin_emoji_propio_usa_la_campana():
    assert canales.texto_para_telegram(titulo="Algo", parrafos=[]).startswith("🔔")


@pytest.mark.django_db
def test_cada_administrador_recibe_el_aviso_con_su_nombre(vinculado, falso):
    otra = UsuarioFactory(rol=Usuario.ADMINISTRADOR, first_name="Ana")
    VinculoTelegram.objects.create(usuario=otra, chat_id=99, nombre_en_telegram="Ana")

    canales.avisar_administradores(
        "resumen",
        asunto="Resumen",
        titulo="Buen día",
        parrafos=[],
        voz={"hoy": date(2026, 10, 28), "pendientes": 0},
    )

    assert "Ezequiel" in falso.textos(CHAT)[-1]
    assert "Ana" in falso.textos(99)[-1]


@pytest.mark.django_db
def test_el_correo_nuevo_llega_con_la_cita_y_los_botones_con_emoji(vinculado, falso):
    ProveedorFactory(correo_comercial="novedades@ivrea.test")
    correo = services.ingerir(ejemplo.correo_de_novedades()).correo

    bot.mandar_correo(CHAT, correo)

    mensaje_ = falso.mensajes(CHAT)[-1]
    assert mensaje_["text"].startswith("📬 <b>")
    assert "<blockquote>" in mensaje_["text"]
    botones = [b["text"] for fila in mensaje_["reply_markup"]["inline_keyboard"] for b in fila]
    assert botones == ["✅ Aprobar y procesar", "🗑 Descartar"]


@pytest.mark.django_db
def test_la_ayuda_presenta_a_long_bot_y_saluda_por_el_nombre(vinculado, falso):
    bot.procesar(mensaje("/ayuda"))

    texto = falso.textos(CHAT)[-1]
    assert "Long-bot" in texto and "Ezequiel" in texto and "/refresh" in texto


# ---------------------------------------------------------------------------
# La charla: el modelo habla, no hace
# ---------------------------------------------------------------------------


def _modelo(datos):
    return patch.object(llm, "pedir_json", return_value=llm.RespuestaDelModelo(datos=datos))


@pytest.mark.django_db
def test_un_saludo_lo_contesta_el_modelo_en_personaje(vinculado, falso):
    with _modelo(
        {"consulta": "ninguna", "texto": "", "respuesta": "¡Buenas, Ezequiel! 😄"}
    ) as pedir:
        bot.procesar(mensaje("buen día"))

    assert falso.textos(CHAT)[-1] == "¡Buenas, Ezequiel! 😄"
    # Le dice al modelo con quién habla y quién es.
    sistema = pedir.call_args.args[0]
    assert "Long-bot" in sistema and "Ezequiel" in sistema


@pytest.mark.django_db
def test_la_charla_del_modelo_se_escapa_y_no_hace_nada(vinculado, falso):
    respuesta = '<a href="https://otro.test">Cargué</a> el tomo /cargar Berserk 5'
    with _modelo({"consulta": "ninguna", "texto": "", "respuesta": respuesta}):
        bot.procesar(mensaje("cargá algo"))

    texto = falso.textos(CHAT)[-1]
    assert "<a href" not in texto and "&lt;a href" in texto
    assert not BorradorProducto.objects.exists()


@pytest.mark.django_db
def test_sin_charla_del_modelo_contesta_una_frase_fija(vinculado, falso):
    with _modelo({"consulta": "ninguna", "texto": "", "respuesta": ""}):
        bot.procesar(mensaje("hola"))

    assert "no lo sé responder" in falso.textos(CHAT)[-1]


def test_la_charla_se_corta_si_se_alarga():
    with _modelo({"consulta": "ninguna", "texto": "", "respuesta": "bla " * 500}):
        _, _, charla = asistente.elegir_consulta("contame algo", nombre="Eze")

    assert len(charla) <= asistente.TOPE_DE_LA_CHARLA


def test_para_una_consulta_la_charla_no_se_usa():
    with _modelo({"consulta": "caja", "texto": "", "respuesta": "¡Te cuento la caja!"}):
        consulta, _, _ = asistente.elegir_consulta("¿cómo va la caja?")

    assert consulta == "caja"
