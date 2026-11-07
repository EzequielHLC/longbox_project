"""Por dónde sale cada aviso al Administrador (plan 00 de Telegram, 1).

El aviso dice **qué** y **de qué tipo**; acá se decide **por dónde**, según lo que
eligió cada Administrador en su perfil (`CU-AVI-CAM`). Sin preferencia cargada,
por el canal por defecto del tipo: por correo, como siempre (decisión 3), salvo
los de la etapa 3 que son sólo por Telegram (B-19-011). Si el Administrador eligió
Telegram y no se puede —el bot no está configurado, desvinculó el chat, Telegram
no contestó—, el aviso le llega por correo (decisión 4): un aviso no se pierde por
el canal. Los opcionales sí (`TipoDeAviso.opcional`).
"""

import html
import logging

from django.conf import settings

from apps.accounts.models import Usuario
from apps.avisos import telegram
from apps.avisos.models import VinculoTelegram, tipo_de_aviso

logger = logging.getLogger(__name__)


def _administradores():
    return (
        Usuario.objects.filter(rol=Usuario.ADMINISTRADOR, estado=Usuario.ACTIVO)
        .prefetch_related("preferencias_de_aviso")
        .order_by("pk")
    )


def _chat_de(usuario):
    try:
        return usuario.vinculo_telegram.chat_id
    except VinculoTelegram.DoesNotExist:
        return None


def destinatarios(tipo):
    """`(correos, chats)` de los Administradores activos para un tipo de aviso.

    `chats` son `(usuario, chat_id)`. Quien eligió Telegram y no tiene cómo
    recibirlo va a `correos`, aunque haya apagado el correo, salvo en un tipo
    opcional.
    """
    definicion = tipo_de_aviso(tipo)
    correos, chats = [], []
    for usuario in _administradores():
        preferencia = next((p for p in usuario.preferencias_de_aviso.all() if p.tipo == tipo), None)
        por_correo = preferencia.por_correo if preferencia else definicion.por_correo
        por_telegram = preferencia.por_telegram if preferencia else definicion.por_telegram
        chat = _chat_de(usuario) if por_telegram and telegram.configurado() else None
        if chat:
            chats.append((usuario, chat))
        if por_correo or (por_telegram and not chat and not definicion.opcional):
            correos.append(usuario.email)
    return correos, chats


def _cae_al_correo(tipo, usuario, correos):
    """Telegram no contestó: le llega por correo (decisión 4), si el tipo no es opcional."""
    if not tipo_de_aviso(tipo).opcional and usuario.email not in correos:
        correos.append(usuario.email)


def texto_para_telegram(
    *,
    titulo,
    parrafos,
    antetitulo="",
    filas=(),
    enlace="",
    texto_enlace="",
    tipo="",
    nombre="",
    voz=None,
    **_,
):
    """El mismo aviso que el correo, en el HTML que entiende Telegram y con la voz
    de Long-bot (B-19-017): el emoji del tipo, el título, la línea, el dato y un
    remate. `voz` trae lo que sólo usa Telegram (el día y lo pendiente del resumen).
    """
    from apps.avisos import voz as long_bot
    from apps.avisos.models import RESUMEN

    voz = voz or {}
    if tipo == RESUMEN and "hoy" in voz:
        titulo = long_bot.saludo_del_dia(nombre, voz["hoy"])
    cabeza = long_bot.encabezado(long_bot.EMOJI.get(tipo, "🔔"), html.escape(titulo))
    partes = [f"<i>{html.escape(antetitulo)}</i>\n{cabeza}" if antetitulo else cabeza]
    partes.extend(html.escape(parrafo) for parrafo in parrafos)
    if filas:
        partes.append(
            "\n".join(
                f"• {html.escape(str(izquierda))}: {html.escape(str(derecha))}"
                for izquierda, derecha in filas
            )
        )
    if tipo == RESUMEN and "pendientes" in voz:
        partes.append(f"<i>{long_bot.cierre_del_resumen(voz['pendientes'])}</i>")
    elif remate := long_bot.remate(tipo):
        partes.append(f"<i>{remate}</i>")
    if enlace:
        partes.append(
            f'👉 <a href="{html.escape(enlace)}">{html.escape(texto_enlace or "Abrir")}</a>'
        )
    return "\n\n".join(partes)


def avisar_administradores(tipo, *, fotos=(), voz=None, tarjeta=None, **aviso):
    """El aviso a los Administradores, por el canal de cada uno.

    `fotos` son imágenes (`ImageField`) que por Telegram van debajo del aviso,
    achicadas; por correo no van (B-19-014). `voz`, lo que Long-bot usa para
    hablar y el correo no (B-19-017). `tarjeta`, la ilustración que va antes del
    texto por Telegram (B-19-020): los datos de `tarjetas.dibujar`; un `{nombre}`
    en su título se completa con el de cada Administrador.
    """
    from apps.avisos import tarjetas
    from apps.avisos import voz as long_bot
    from apps.avisos.miniaturas import miniatura
    from apps.pedidos import avisos

    correos, chats = destinatarios(tipo)
    if chats:
        album = [m for m in (miniatura(foto) for foto in fotos) if m] if fotos else []
        dibujadas = {}
        for usuario, chat in chats:
            if tarjeta:
                titulo = _titulo_de_la_tarjeta(tarjeta["titulo"], long_bot.nombre_de(usuario))
                if titulo not in dibujadas:
                    dibujadas[titulo] = tarjetas.tarjeta(**{**tarjeta, "titulo": titulo})
                if dibujadas[titulo]:
                    # Si la foto no sale, el texto sale igual: la tarjeta sólo acompaña.
                    telegram.enviar_foto(chat, dibujadas[titulo], "")
            texto = texto_para_telegram(
                **aviso, tipo=tipo, nombre=long_bot.nombre_de(usuario), voz=voz
            )
            if telegram.enviar(chat, texto) is None:
                _cae_al_correo(tipo, usuario, correos)
            elif album:
                telegram.enviar_album(chat, album)
    if correos:
        avisos.avisar(correos, **aviso)


def _titulo_de_la_tarjeta(titulo, nombre):
    """El título con el nombre de pila, o sin la coma si no hay nombre."""
    if "{nombre}" not in titulo:
        return titulo
    return titulo.replace(", {nombre}", f", {nombre}" if nombre else "").replace("{nombre}", nombre)


def avisar_pedido(pedido, *, recordatorio=False):
    """El pedido a proveedor que salió (o que no respondió), con sus botones, a quien
    recibe los avisos de restock por Telegram. Por correo no hay nada nuevo: la
    respuesta se anota en la web (plan 00 de la respuesta del proveedor)."""
    from apps.avisos import bot

    _, chats = destinatarios("restock")
    for _usuario, chat in chats:
        bot.mandar_pedido(chat, pedido, recordatorio=recordatorio)


def avisar_pedido_sin_enviar(pedido):
    """B-05-014: el pedido que no salió, con «Reintentar el envío»."""
    from apps.avisos import bot

    _, chats = destinatarios("restock")
    for _usuario, chat in chats:
        bot.mandar_pedido_sin_enviar(chat, pedido)


def avisar_correos_nuevos(correos_nuevos, **aviso):
    """`CO-016`: el resumen por correo y, por Telegram, cada correo con sus botones."""
    from apps.avisos import bot
    from apps.pedidos import avisos

    correos, chats = destinatarios("correos")
    for usuario, chat in chats:
        llegaron = [bot.mandar_correo(chat, correo) is not None for correo in correos_nuevos]
        if not all(llegaron) and usuario.email not in correos:
            correos.append(usuario.email)
    avisos.avisar(correos, **aviso)


def enlace(nombre_url, *args):
    """La dirección pública de una pantalla, o vacío si el sistema no la conoce."""
    from django.urls import reverse

    return settings.URL_PUBLICA + reverse(nombre_url, args=args) if settings.URL_PUBLICA else ""
