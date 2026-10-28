"""La API de Telegram, por la única puerta HTTP del proyecto (plan 00 de Telegram, 3).

Todo sale por `integraciones.pedir`: las pruebas cortan la red ahí, así que este
canal queda cubierto desde el primer día sin que nadie se acuerde de cortarlo.
**El token viaja en la dirección** (`/bot<token>/…`): la puerta lo tapa antes de
escribirla en el log (`integraciones.para_el_log`).

Sin `TELEGRAM_BOT_TOKEN` el canal no existe: `configurado()` es falso, nadie
intenta mandar nada y todos los avisos salen por correo.
"""

import hashlib
import hmac
import logging

from django.conf import settings
from django.core.cache import cache

from apps.core import integraciones

logger = logging.getLogger(__name__)

API = "https://api.telegram.org"
TIEMPO_DE_ESPERA = 15
# La consulta larga de `getUpdates` espera hasta esto en el servidor de Telegram.
ESPERA_DE_NOVEDADES = 25
# Lo que el bot recibe: mensajes, botones y búsquedas en línea (B-19-015).
ACTUALIZACIONES = ["message", "callback_query", "inline_query"]


def configurado():
    return bool(settings.TELEGRAM_BOT_TOKEN)


def _llamar(metodo, *, espera=TIEMPO_DE_ESPERA, archivos=None, **parametros):
    """Un método de la API. Devuelve el `result` o `None` si no salió.

    `espera` es la de la conexión; `timeout`, si viene, es el parámetro de Telegram.
    `archivos` sube bytes (una foto) en un formulario multiparte.
    """
    if not configurado():
        return None
    pedido = {
        "timeout": espera,
        "metodo": "POST",
        "cuerpo": {clave: valor for clave, valor in parametros.items() if valor is not None},
    }
    if archivos:
        pedido["archivos"] = archivos
    respuesta = integraciones.pedir(f"{API}/bot{settings.TELEGRAM_BOT_TOKEN}/{metodo}", **pedido)
    if not respuesta or not isinstance(respuesta.datos, dict) or not respuesta.datos.get("ok"):
        logger.warning("Telegram no aceptó «%s»: %s", metodo, getattr(respuesta, "detalle", ""))
        return None
    return respuesta.datos.get("result")


def enviar(chat_id, texto, *, botones=None, responder_a=None, forzar_respuesta=False):
    """Un mensaje con HTML de Telegram. Devuelve el mensaje mandado o `None`."""
    marcado = None
    if botones:
        marcado = {"inline_keyboard": botones}
    elif forzar_respuesta:
        marcado = {"force_reply": True, "input_field_placeholder": "Escribí el motivo"}
    return _llamar(
        "sendMessage",
        chat_id=chat_id,
        text=texto[:4096],
        parse_mode="HTML",
        disable_web_page_preview=True,
        reply_markup=marcado,
        reply_to_message_id=responder_a,
    )


def enviar_foto(chat_id, foto, texto, *, botones=None):
    """Una foto (bytes JPEG) con su epígrafe en HTML. Devuelve el mensaje o `None`."""
    return _llamar(
        "sendPhoto",
        archivos={"photo": ("portada.jpg", foto, "image/jpeg")},
        chat_id=chat_id,
        caption=texto[:TOPE_DE_EPIGRAFE],
        parse_mode="HTML",
        reply_markup={"inline_keyboard": botones} if botones else None,
    )


def enviar_album(chat_id, fotos, texto=""):
    """Hasta diez fotos (bytes JPEG) juntas, con el epígrafe en la primera."""
    fotos = list(fotos)[:10]
    if not fotos:
        return None
    medios = [
        {"type": "photo", "media": f"attach://foto{i}"}
        | ({"caption": texto[:TOPE_DE_EPIGRAFE], "parse_mode": "HTML"} if i == 0 and texto else {})
        for i in range(len(fotos))
    ]
    return _llamar(
        "sendMediaGroup",
        archivos={f"foto{i}": (f"foto{i}.jpg", foto, "image/jpeg") for i, foto in enumerate(fotos)},
        chat_id=chat_id,
        media=medios,
    )


def responder_inline(id_de_la_consulta, resultados):
    """La respuesta a `@bot texto`: personal y de vida corta, porque mira quién pregunta."""
    return _llamar(
        "answerInlineQuery",
        inline_query_id=id_de_la_consulta,
        results=resultados,
        cache_time=10,
        is_personal=True,
    )


def quitar_botones(chat_id, mensaje_id):
    return _llamar(
        "editMessageReplyMarkup",
        chat_id=chat_id,
        message_id=mensaje_id,
        reply_markup={"inline_keyboard": []},
    )


def responder_boton(id_de_la_consulta, texto=""):
    """El aviso breve arriba del chat al tocar un botón. Telegram lo exige enseguida."""
    return _llamar("answerCallbackQuery", callback_query_id=id_de_la_consulta, text=texto[:200])


def novedades(desde=None):
    """`getUpdates`: lo que llegó desde la última novedad procesada (esta PC)."""
    return (
        _llamar(
            "getUpdates",
            espera=ESPERA_DE_NOVEDADES + 10,
            offset=desde,
            timeout=ESPERA_DE_NOVEDADES,
            allowed_updates=ACTUALIZACIONES,
        )
        or []
    )


def usuario_del_bot():
    """El `@usuario` del bot, para armar el enlace de vinculación. Se guarda un día."""
    guardado = cache.get("telegram:usuario")
    if guardado:
        return guardado
    datos = _llamar("getMe")
    usuario = (datos or {}).get("username", "")
    if usuario:
        cache.set("telegram:usuario", usuario, 60 * 60 * 24)
    return usuario


# El menú de comandos del bot, el que Telegram muestra al tocar «/» (B-19-007).
COMANDOS = [
    ("ayuda", "Qué puedo hacer y cómo"),
    ("stock", "El stock de un producto: /stock Chainsaw Man 12"),
    ("llega", "Lo que llega esta semana y lo atrasado"),
    ("pendientes", "Lo que espera una decisión"),
    ("caja", "Lo cobrado hoy, sin cerrar"),
    ("estado", "Disco, memoria, base y el último respaldo"),
    ("refresh", "Revisar la casilla de novedades ahora"),
    ("cargar", "Un borrador: /cargar Berserk Deluxe 5, Ivrea, 24900"),
    ("borradores", "Los borradores por revisar; se pueden rechazar"),
    ("salir", "Desvincular este chat"),
]
TOPE_DE_FOTO = 10 * 1024 * 1024
# Telegram corta el epígrafe de una foto en 1024 caracteres.
TOPE_DE_EPIGRAFE = 1024


def poner_comandos():
    return _llamar(
        "setMyCommands",
        commands=[{"command": nombre, "description": texto} for nombre, texto in COMANDOS],
    )


def descargar_archivo(file_id):
    """Los bytes de una foto que mandaron al bot, o `None`. Por la única puerta."""
    datos = _llamar("getFile", file_id=file_id)
    ruta = datos.get("file_path") if isinstance(datos, dict) else None
    if not ruta:
        return None
    return integraciones.descargar(
        f"{API}/file/bot{settings.TELEGRAM_BOT_TOKEN}/{ruta}",
        timeout=TIEMPO_DE_ESPERA,
        tope=TOPE_DE_FOTO,
    )


def poner_webhook(url):
    return _llamar(
        "setWebhook",
        url=url,
        secret_token=secreto_del_webhook(),
        allowed_updates=ACTUALIZACIONES,
        drop_pending_updates=False,
    )


def sacar_webhook():
    return _llamar("deleteWebhook", drop_pending_updates=False)


def secreto_del_webhook():
    """Lo que Telegram manda en cada llamada al webhook, para saber que es él.

    Se deriva del token y de la `SECRET_KEY` en vez de pedir otra variable: sin
    las dos no se puede adivinar, y no hay una tercera cosa que configurar.
    """
    return hmac.new(
        settings.SECRET_KEY.encode(),
        f"webhook:{settings.TELEGRAM_BOT_TOKEN}".encode(),
        hashlib.sha256,
    ).hexdigest()[:48]


def firmar(*partes):
    """Una firma corta para los datos de un botón: nadie arma uno a mano."""
    texto = ":".join(str(parte) for parte in partes)
    return hmac.new(settings.SECRET_KEY.encode(), texto.encode(), hashlib.sha256).hexdigest()[:12]
