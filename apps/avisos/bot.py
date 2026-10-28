"""Lo que el bot entiende (plan 00 de Telegram).

- `/start <código>` — `CU-AVI-TGA`: pide vincular el chat; se confirma en el perfil.
- `/salir` — `CU-AVI-TGB`: desvincula el chat.
- Los botones de un correo nuevo — `CU-AVI-COR`: «Aprobar y procesar» es
  `CO-017` y «Descartar» es `CO-018`, con un motivo rápido o escrito.
- `/stock`, `/llega`, `/pendientes`, `/caja` o una pregunta con palabras —
  `CU-AVI-CON`: consultas fijas, de sólo lectura.
- `/cargar` o una foto con epígrafe — `CU-AVI-BOR`: un borrador para revisar.
- `/borradores` — `CU-AVI-REB`: la vista previa de los abiertos, con «Rechazar…».
  **Nunca con «Confirmar»**: el producto nace en la web.
- `/ayuda` (o `/help`): la lista de comandos.

**La autorización se mira en el momento de cada acción**, no al mandar el aviso:
el chat tiene que estar vinculado a un Administrador **activo**. Cada botón lleva
una firma con el chat y la acción, así que nadie arma uno a mano. Lo que se
resuelve desde acá se audita como desde la web, con el canal en el detalle.
"""

import hmac
import html
import logging
import re
import secrets
from functools import partial

from django.db import transaction
from django.utils import timezone

from apps.accounts.models import Usuario
from apps.avisos import telegram
from apps.avisos.canales import enlace
from apps.avisos.miniaturas import miniatura
from apps.avisos.models import INTENTOS_DE_CONFIRMACION, CodigoVinculacion, VinculoTelegram
from apps.core.models import RegistroAuditoria
from apps.core.segundo_plano import lanzar
from apps.core.templatetags.moneda import pesos
from apps.suppliers import services
from apps.suppliers.models import CorreoProveedor

logger = logging.getLogger(__name__)

# Decisión 5: los motivos frecuentes de descarte, y «Otro motivo…» para escribirlo.
MOTIVOS = (
    "No es de novedades",
    "Repetido",
    "Promoción o publicidad",
    "Factura o resumen de cuenta",
)
_CORREO_EN_LA_PREGUNTA = re.compile(r"correo #(\d+)")

AYUDA = (
    "<b>Soy el bot de Longbox.</b> Te aviso lo que elegiste en tu perfil y, cuando llega un "
    "correo de un proveedor, lo podés aprobar o descartar desde acá.\n\n"
    "<b>Consultas</b>\n"
    "/stock <i>título, código o ISBN</i> — stock, precio y estado\n"
    "/llega — lo que llega esta semana y lo atrasado\n"
    "/pendientes — lo que espera una decisión\n"
    "/caja — lo cobrado hoy, sin cerrar\n"
    "/estado — disco, memoria, base y el último respaldo\n"
    "/refresh — revisar la casilla de novedades ahora, sin esperar\n"
    "También podés preguntar con tus palabras: «¿cuántos Chainsaw Man 12 hay?».\n\n"
    "<b>Cargar un borrador</b>\n"
    "/cargar <i>Berserk Deluxe 5, Ivrea, B6, 24900</i> — o mandá la foto de la tapa con ese "
    "texto. Queda para revisar en la web; nada entra al catálogo sin tu confirmación. "
    "Es para material editorial: lo demás se da de alta en la web.\n"
    "/borradores <i>título (opcional)</i> — los que esperan revisión, con su portada. "
    "Desde acá se pueden rechazar; se confirman sólo en la web.\n\n"
    "<b>Compartir un producto</b>\n"
    "En cualquier chat, escribí <code>@{bot} berserk</code> y elegí el tomo: se comparte su "
    "ficha de la tienda, con el precio y el enlace, sin el stock.\n\n"
    "/salir — desvincular este chat de tu cuenta."
)
NO_VINCULADO = "Este chat no está vinculado a un Administrador activo. Vinculalo desde tu perfil."
_COMANDO = re.compile(r"^/(?P<nombre>[a-z]+)(?:@\w+)?(?:\s+(?P<resto>.*))?$", re.S | re.I)


# ---------------------------------------------------------------------------
# La entrada: una novedad de Telegram, por el webhook o por `escuchar`
# ---------------------------------------------------------------------------


def procesar(novedad):
    """Una novedad de Telegram. Nunca levanta: una novedad rara no frena las demás."""
    try:
        if "callback_query" in novedad:
            _boton(novedad["callback_query"])
        elif "inline_query" in novedad:
            _inline(novedad["inline_query"])
        elif "message" in novedad:
            _mensaje(novedad["message"])
    except Exception:  # noqa: BLE001 - el bot sigue atendiendo aunque una novedad falle
        logger.exception("No se pudo procesar una novedad de Telegram.")


def _mensaje(mensaje):
    chat = mensaje.get("chat", {})
    if chat.get("type") != "private":
        return
    chat_id = chat["id"]
    texto = (mensaje.get("text") or mensaje.get("caption") or "").strip()
    comando = _COMANDO.match(texto)
    nombre, resto = (
        (comando.group("nombre").lower(), (comando.group("resto") or "").strip())
        if comando
        else ("", "")
    )
    if nombre == "start":
        _vincular(chat_id, resto, _nombre(mensaje.get("from", {})))
    elif nombre == "salir":
        _desvincular_desde_el_chat(chat_id)
    elif nombre in ("ayuda", "help"):
        telegram.enviar(chat_id, _ayuda())
    elif (pregunta := (mensaje.get("reply_to_message") or {}).get("text", "")) and (
        encontrado := _CORREO_EN_LA_PREGUNTA.search(pregunta)
    ):
        _descartar(chat_id, int(encontrado.group(1)), texto)
    elif pregunta and (encontrado := _BORRADOR_EN_LA_PREGUNTA.search(pregunta)):
        _rechazar(chat_id, int(encontrado.group(1)), texto)
    elif administrador_del_chat(chat_id) is None:
        telegram.enviar(chat_id, NO_VINCULADO)
    elif mensaje.get("photo"):
        # La foto más grande que mandó Telegram; el epígrafe son los datos.
        foto = max(mensaje["photo"], key=lambda f: f.get("file_size") or 0)["file_id"]
        datos = resto if nombre == "cargar" else texto
        lanzar(partial(_cargar, chat_id, datos, foto))
    elif nombre == "cargar":
        lanzar(partial(_cargar, chat_id, resto, None))
    elif nombre == "borradores":
        lanzar(partial(_borradores, chat_id, resto))
    elif nombre in ("refresh", "revisar"):
        telegram.enviar(chat_id, "Revisando la casilla…")
        lanzar(partial(_refrescar, chat_id))
    elif nombre in ("stock", "llega", "pendientes", "caja", "estado"):
        telegram.enviar(chat_id, _consultar(nombre, resto))
    elif nombre:
        telegram.enviar(chat_id, f"No conozco /{html.escape(nombre)}. Mandá /ayuda.")
    elif texto:
        lanzar(partial(_pregunta_libre, chat_id, texto))
    else:
        telegram.enviar(chat_id, _ayuda())


def _ayuda():
    return AYUDA.replace("{bot}", html.escape(telegram.usuario_del_bot() or "el_bot"))


def _nombre(remitente):
    nombre = " ".join(p for p in (remitente.get("first_name"), remitente.get("last_name")) if p)
    usuario = remitente.get("username")
    return nombre or (f"@{usuario}" if usuario else "")


def administrador_del_chat(chat_id):
    """El Administrador **activo** de ese chat, o `None`. Se mira en cada acción."""
    vinculo = VinculoTelegram.objects.select_related("usuario").filter(chat_id=chat_id).first()
    if vinculo is None:
        return None
    usuario = vinculo.usuario
    if usuario.rol != Usuario.ADMINISTRADOR or usuario.estado != Usuario.ACTIVO:
        return None
    return usuario


# ---------------------------------------------------------------------------
# CU-AVI-TGA · CU-AVI-TGB
# ---------------------------------------------------------------------------


def _vincular(chat_id, codigo, nombre):
    """`CU-AVI-TGA`, segunda mitad: el chat que abrió el enlace pide vincularse.

    **No vincula todavía** (B-19-005): anota el chat y le da un número de seis
    cifras, que el Administrador escribe en su perfil. Si el enlace se filtró y
    lo abrió otro, ese otro no tiene la sesión para confirmarlo. Abrirlo de nuevo
    pisa el pedido anterior con un número nuevo.
    """
    with transaction.atomic():
        pedido = (
            CodigoVinculacion.objects.select_for_update()
            .select_related("usuario")
            .filter(codigo=codigo)
            .first()
            if codigo
            else None
        )
        if pedido is None or not pedido.vigente:
            telegram.enviar(
                chat_id,
                "Ese enlace no sirve: venció o ya se usó. "
                "Pedí uno nuevo desde tu perfil en Longbox.",
            )
            return
        usuario = pedido.usuario
        if usuario.rol != Usuario.ADMINISTRADOR or usuario.estado != Usuario.ACTIVO:
            telegram.enviar(chat_id, "Esta cuenta no puede usar el bot.")
            return
        pedido.chat_pendiente = chat_id
        pedido.nombre_pendiente = nombre[:200]
        pedido.confirmacion = f"{secrets.randbelow(10**6):06d}"
        pedido.intentos = 0
        pedido.save(
            update_fields=["chat_pendiente", "nombre_pendiente", "confirmacion", "intentos"]
        )
    telegram.enviar(
        chat_id,
        "Para terminar, escribí este número en tu perfil de Longbox:\n\n"
        f"<b>{pedido.confirmacion[:3]} {pedido.confirmacion[3:]}</b>\n\n"
        f"Vence a las {timezone.localtime(pedido.vence_en):%H:%M}. "
        "Si no pediste vincular una cuenta, ignorá este mensaje.",
    )


def confirmar_vinculo(usuario, numero):
    """`CU-AVI-TGA`, desde el perfil: el número que dio el bot. Devuelve `(ok, mensaje)`."""
    numero = "".join(c for c in (numero or "") if c.isdigit())
    with transaction.atomic():
        pedido = (
            CodigoVinculacion.objects.select_for_update()
            .filter(usuario=usuario, usado_en__isnull=True, chat_pendiente__isnull=False)
            .order_by("-creado_en")
            .first()
        )
        if pedido is None or not pedido.espera_confirmacion:
            return False, "No hay una vinculación esperando: pedí un enlace nuevo."
        if not hmac.compare_digest(numero, pedido.confirmacion):
            pedido.intentos += 1
            if pedido.intentos >= INTENTOS_DE_CONFIRMACION:
                pedido.delete()
                return False, "Demasiados intentos: se anuló el enlace. Pedí uno nuevo."
            pedido.save(update_fields=["intentos"])
            quedan = INTENTOS_DE_CONFIRMACION - pedido.intentos
            return False, f"Ese no es el número. Te quedan {quedan} intento(s)."
        chat_id, nombre = pedido.chat_pendiente, pedido.nombre_pendiente
        # Un chat es de una sola cuenta, y una cuenta tiene un solo chat.
        VinculoTelegram.objects.filter(chat_id=chat_id).exclude(usuario=usuario).delete()
        VinculoTelegram.objects.update_or_create(
            usuario=usuario, defaults={"chat_id": chat_id, "nombre_en_telegram": nombre}
        )
        pedido.usado_en = timezone.now()
        pedido.save(update_fields=["usado_en"])
        RegistroAuditoria.registrar(
            accion=RegistroAuditoria.VINCULO_TELEGRAM,
            actor=usuario,
            objetivo=usuario,
            detalle=(
                f"Telegram vinculado con {nombre or 'un chat sin nombre'}, "
                "confirmado desde el perfil."
            ),
        )
    saludo = f", {html.escape(nombre.split()[0])}" if nombre else ""
    telegram.enviar(
        chat_id,
        f"Listo{saludo}: este chat quedó vinculado a tu cuenta de Longbox. "
        "Elegí qué avisos recibir acá desde tu perfil. Mandá /ayuda para ver lo que podés hacer.",
    )
    return True, "Telegram quedó vinculado. Elegí abajo qué avisos querés recibir ahí."


def desvincular(usuario, *, desde="el perfil"):
    """`CU-AVI-TGB`. Devuelve si había vínculo. Los avisos vuelven al correo solos."""
    with transaction.atomic():
        borrados, _ = VinculoTelegram.objects.filter(usuario=usuario).delete()
        if borrados:
            RegistroAuditoria.registrar(
                accion=RegistroAuditoria.DESVINCULO_TELEGRAM,
                actor=usuario,
                objetivo=usuario,
                detalle=f"Telegram desvinculado desde {desde}.",
            )
    return bool(borrados)


def _desvincular_desde_el_chat(chat_id):
    vinculo = VinculoTelegram.objects.select_related("usuario").filter(chat_id=chat_id).first()
    if vinculo is None:
        telegram.enviar(chat_id, "Este chat no está vinculado a ninguna cuenta.")
        return
    desvincular(vinculo.usuario, desde="el chat")
    telegram.enviar(chat_id, "Listo: este chat ya no recibe avisos. Te llegan por correo.")


# ---------------------------------------------------------------------------
# CU-AVI-COR · el correo nuevo con sus botones
# ---------------------------------------------------------------------------


def _boton_de(accion, correo_pk, chat_id, extra=""):
    datos = f"{accion}:{correo_pk}:{extra}"
    return f"{datos}:{telegram.firmar(datos, chat_id)}"


def mandar_correo(chat_id, correo):
    """El aviso de un correo nuevo, con «Aprobar y procesar» y «Descartar»."""
    primeras = " ".join((correo.contenido or "").split())[:300]
    ficha = enlace("suppliers:correo_detalle", correo.pk)
    texto = (
        f"<i>Correo nuevo · {html.escape(str(correo.proveedor))}</i>\n"
        f"<b>{html.escape(correo.asunto or 'Sin asunto')}</b>\n"
        f"{html.escape(correo.remitente)}"
        + (f"\n\n{html.escape(primeras)}…" if primeras else "")
        + (f'\n\n<a href="{html.escape(ficha)}">Verlo en Longbox</a>' if ficha else "")
    )
    botones = [
        [{"text": "Aprobar y procesar", "callback_data": _boton_de("ap", correo.pk, chat_id)}],
        [{"text": "Descartar", "callback_data": _boton_de("de", correo.pk, chat_id)}],
    ]
    return telegram.enviar(chat_id, texto, botones=botones)


def _boton(consulta):
    mensaje = consulta.get("message") or {}
    chat_id = (mensaje.get("chat") or {}).get("id")
    partes = (consulta.get("data") or "").split(":")
    if chat_id is None or len(partes) != 4:
        telegram.responder_boton(consulta["id"], "Botón inválido.")
        return
    accion, pk, extra, firma = partes
    if firma != telegram.firmar(f"{accion}:{pk}:{extra}", chat_id):
        telegram.responder_boton(consulta["id"], "Botón inválido.")
        return
    if administrador_del_chat(chat_id) is None:
        telegram.responder_boton(
            consulta["id"], "Este chat no está vinculado a un Administrador activo."
        )
        return
    pk = int(pk)
    mensaje_id = mensaje.get("message_id")
    if accion == "ap":
        telegram.responder_boton(consulta["id"], "Procesando…")
        telegram.quitar_botones(chat_id, mensaje_id)
        # El modelo puede tardar minutos y Telegram espera la respuesta del botón:
        # se procesa aparte y el resultado llega como otro mensaje.
        lanzar(partial(_aprobar, chat_id, pk))
    elif accion == "de":
        telegram.responder_boton(consulta["id"])
        botones = [
            [{"text": motivo, "callback_data": _boton_de("dm", pk, chat_id, str(i))}]
            for i, motivo in enumerate(MOTIVOS)
        ]
        botones.append([{"text": "Otro motivo…", "callback_data": _boton_de("do", pk, chat_id)}])
        telegram.enviar(chat_id, f"¿Por qué se descarta el correo #{pk}?", botones=botones)
    elif accion == "dm" and extra.isdigit() and int(extra) < len(MOTIVOS):
        telegram.responder_boton(consulta["id"])
        telegram.quitar_botones(chat_id, mensaje_id)
        _descartar(chat_id, pk, MOTIVOS[int(extra)])
    elif accion == "do":
        telegram.responder_boton(consulta["id"])
        telegram.quitar_botones(chat_id, mensaje_id)
        telegram.enviar(
            chat_id,
            f"Escribí el motivo para descartar el correo #{pk}, " "respondiendo a este mensaje.",
            forzar_respuesta=True,
        )
    elif accion == "rb":
        telegram.responder_boton(consulta["id"])
        _preguntar_motivo_de_rechazo(chat_id, pk)
    elif accion == "rm" and extra.isdigit() and int(extra) < len(MOTIVOS_DE_RECHAZO):
        telegram.responder_boton(consulta["id"])
        telegram.quitar_botones(chat_id, mensaje_id)
        _rechazar(chat_id, pk, MOTIVOS_DE_RECHAZO[int(extra)])
    elif accion == "ro":
        telegram.responder_boton(consulta["id"])
        telegram.quitar_botones(chat_id, mensaje_id)
        telegram.enviar(
            chat_id,
            f"Escribí el motivo para rechazar el borrador #{pk}, respondiendo a este mensaje.",
            forzar_respuesta=True,
        )
    else:
        telegram.responder_boton(consulta["id"], "Botón inválido.")


def _aprobar(chat_id, correo_pk):
    """`CO-017` desde el chat. Lo que pasa después es lo mismo que desde la web."""
    usuario = administrador_del_chat(chat_id)
    if usuario is None:
        return
    try:
        resultado = services.aprobar_correo(correo_pk, actor=usuario)
    except CorreoProveedor.DoesNotExist:
        telegram.enviar(chat_id, f"El correo #{correo_pk} ya no existe.")
        return
    except services.CorreoYaResuelto as error:
        telegram.enviar(chat_id, f"Otro Administrador ya resolvió el correo #{correo_pk}: {error}.")
        return
    correo = CorreoProveedor.objects.get(pk=correo_pk)
    ficha = enlace("suppliers:correo_detalle", correo.pk)
    if correo.estado == CorreoProveedor.FALLIDO:
        texto = f"Falló el procesamiento del correo #{correo.pk}. {correo.motivo}"
    elif resultado.generacion is not None:
        cuenta = resultado.generacion.resumen
        borradores = enlace("catalog:borrador_lista")
        texto = (
            f"Se procesó el correo #{correo.pk}: {cuenta['generados']} borrador(es) para revisar "
            f"y {cuenta['duplicados']} omitido(s) por existir ya."
            + (
                f'\n\n<a href="{html.escape(borradores)}">Revisar los borradores</a>'
                if borradores
                else ""
            )
        )
    else:
        texto = f"Se procesó el correo #{correo.pk}. {correo.motivo}"
        if ficha:
            texto += f'\n\n<a href="{html.escape(ficha)}">Verlo en Longbox</a>'
    telegram.enviar(chat_id, texto)


def _descartar(chat_id, correo_pk, motivo):
    """`CO-018` desde el chat, con el motivo obligatorio y la misma auditoría."""
    usuario = administrador_del_chat(chat_id)
    motivo = " ".join((motivo or "").split())[:500]
    if usuario is None:
        telegram.enviar(chat_id, "Este chat no está vinculado a un Administrador activo.")
        return
    if not motivo:
        telegram.enviar(chat_id, "El motivo es obligatorio.")
        return
    with transaction.atomic():
        correo = CorreoProveedor.objects.select_for_update().filter(pk=correo_pk).first()
        if correo is None:
            telegram.enviar(chat_id, f"El correo #{correo_pk} ya no existe.")
            return
        if not correo.puede_descartarse:
            telegram.enviar(
                chat_id,
                f"El correo #{correo_pk} ya no se puede descartar: {correo.get_estado_display()}.",
            )
            return
        services.descartar(correo, usuario, motivo)
        RegistroAuditoria.registrar(
            accion=RegistroAuditoria.CORREO_DESCARTADO,
            actor=usuario,
            objetivo=correo,
            detalle=(
                f"«{correo.asunto or 'sin asunto'}» de {correo.proveedor}: {motivo} "
                "(desde Telegram)"
            ),
        )
    telegram.enviar(chat_id, f"Se descartó el correo #{correo_pk}: {html.escape(motivo)}.")


# ---------------------------------------------------------------------------
# CO-016 desde el chat: /refresh (B-19-016)
# ---------------------------------------------------------------------------


def _refrescar(chat_id):
    """Lo mismo que «Revisar la casilla» de la cola: trae lo nuevo, no procesa nada,
    y reinicia el reloj de la lectura automática."""
    from apps.avisos.canales import destinatarios
    from apps.suppliers import casilla

    if administrador_del_chat(chat_id) is None:
        return
    resumen = casilla.ciclo(forzar=True)
    if resumen.estado == "sin configurar":
        telegram.enviar(chat_id, "La casilla de novedades no está configurada en este sistema.")
        return
    if resumen.estado != "revisada":
        telegram.enviar(
            chat_id,
            "No se pudo conectar a la casilla de novedades. Se avisó a los administradores; "
            "probá de nuevo en un rato.",
        )
        return
    nuevos = resumen.ingresados
    lineas = [
        (
            f"<b>Revisé la casilla: {len(nuevos)} correo(s) nuevo(s) en la cola.</b>"
            if nuevos
            else "<b>Revisé la casilla: no hay correos nuevos.</b>"
        )
    ]
    if nuevos:
        llegan_aca = any(chat == chat_id for _, chat in destinatarios("correos")[1])
        if llegan_aca:
            lineas.append("Te los mandé arriba, cada uno con sus botones.")
        else:
            lineas.extend(
                f"✉ {html.escape(str(c.proveedor))}: {html.escape(c.asunto or 'sin asunto')}"
                for c in nuevos
            )
            cola = enlace("suppliers:correo_lista")
            if cola:
                lineas.append(f'<a href="{html.escape(cola)}">Abrir la cola</a>')
    proxima = casilla.proxima_revision()
    if proxima:
        lineas.append(
            f"La próxima revisión automática es a las {timezone.localtime(proxima):%H:%M}."
        )
    telegram.enviar(chat_id, "\n".join(lineas))


# ---------------------------------------------------------------------------
# CU-AVI-CON · las consultas, por comando o con palabras
# ---------------------------------------------------------------------------


def _consultar(consulta, texto=""):
    """El texto de una consulta fija. Ninguna escribe (decisión 10)."""
    from apps.avisos import consultas

    if consulta == "stock":
        return consultas.stock(texto)
    if consulta == "estado":
        from apps.avisos import salud

        return salud.texto_del_estado()
    return getattr(consultas, consulta)()


def _pregunta_libre(chat_id, texto):
    """El modelo elige la consulta; el sistema consulta y responde (regla 4)."""
    from apps.avisos import asistente

    if administrador_del_chat(chat_id) is None:
        return
    elegida = asistente.elegir_consulta(texto)
    if elegida is None:
        telegram.enviar(
            chat_id,
            "No pude entender la pregunta ahora: el modelo no contestó. "
            "Probá con un comando, como /stock o /pendientes.",
        )
        return
    consulta, argumento = elegida
    if consulta == "cargar":
        _cargar(chat_id, texto, None)
    elif consulta == "borradores":
        _borradores(chat_id, argumento)
    elif consulta == "ninguna":
        telegram.enviar(
            chat_id, "Eso no lo sé responder. Mandá /ayuda para ver lo que puedo hacer."
        )
    else:
        telegram.enviar(chat_id, _consultar(consulta, argumento or texto))


# ---------------------------------------------------------------------------
# CU-AVI-BOR · un borrador desde el chat
# ---------------------------------------------------------------------------


def _tipo_por_nombre(nombre):
    from apps.catalog.models import Tipo
    from apps.catalog.services import por_nombre

    return por_nombre(Tipo.objects.filter(activo=True), nombre)


def _editorial_por_nombre(nombre):
    from apps.catalog.models import Editorial
    from apps.catalog.services import por_nombre

    return por_nombre(Editorial.objects.filter(activa=True), nombre)


def _cargar(chat_id, texto, foto):
    """El texto (y la foto, que es la portada: decisión 9) a un **borrador** para
    revisar en la web. Nunca un producto: lo confirma una persona (regla 4)."""
    from apps.avisos import asistente
    from apps.catalog import borradores
    from apps.catalog import services as catalogo

    usuario = administrador_del_chat(chat_id)
    if usuario is None:
        return
    texto = " ".join((texto or "").split())
    if not texto:
        telegram.enviar(
            chat_id,
            "Contame qué cargar: <code>/cargar Berserk Deluxe 5, Ivrea, B6, 24900</code>, "
            "o mandá la foto de la tapa con ese texto.",
        )
        return
    lectura = asistente.leer_producto(texto, hoy=timezone.localdate())
    if lectura is None:
        telegram.enviar(chat_id, "No pude leer el producto ahora: el modelo no contestó.")
        return
    if not lectura.crudo["titulo"]:
        telegram.enviar(
            chat_id, "No encontré un título en el mensaje. Probá de nuevo con más datos."
        )
        return
    tipo = _tipo_por_nombre(lectura.tipo)
    if lectura.no_editorial or (tipo is not None and not tipo.es_editorial):
        _no_editorial(chat_id, lectura, tipo)
        return
    reparos = []
    editorial = _editorial_por_nombre(lectura.editorial)
    if editorial is None:
        # B-19-010: si la serie ya está en una sola editorial, es esa.
        de_la_serie = catalogo.editoriales_de_la_serie(lectura.crudo["titulo"])
        if len(de_la_serie) == 1:
            editorial = de_la_serie[0]
            if lectura.editorial:
                reparos.append(
                    f"La editorial «{lectura.editorial}» no está cargada: "
                    f"se tomó {editorial}, la de la serie."
                )
        elif lectura.editorial:
            reparos.append(
                f"La editorial «{lectura.editorial}» no está cargada: elegila al revisar."
            )
    if lectura.tipo and tipo is None:
        reparos.append(f"El tipo «{lectura.tipo}» no está cargado: elegilo al revisar.")
    portada = telegram.descargar_archivo(foto) if foto else None
    if foto and portada is None:
        reparos.append("La foto que llegó por Telegram no se pudo descargar.")
    borrador = borradores.desde_telegram(
        lectura.crudo,
        editorial=editorial,
        usuario=usuario,
        portada=portada,
        reparos=reparos,
        tipo=tipo,
    )
    mostrar_borrador(chat_id, borrador, encabezado="Quedó este borrador para revisar en la web.")


def _no_editorial(chat_id, lectura, tipo):
    """B-19-009: el borrador es de material editorial. Lo otro no se carga a medias."""
    clase = f" ({html.escape(str(tipo))})" if tipo else ""
    alta = enlace("catalog:producto_no_editorial_alta")
    telegram.enviar(
        chat_id,
        f"«{html.escape(lectura.crudo['titulo'])}» parece material no editorial{clase}. "
        "Los borradores son sólo de material editorial, así que no cargué nada: "
        "dalo de alta desde la web."
        + (f'\n\n<a href="{html.escape(alta)}">Alta no editorial</a>' if alta else ""),
    )


# ---------------------------------------------------------------------------
# CU-AVI-REB · ver los borradores y rechazarlos, nunca confirmarlos
# ---------------------------------------------------------------------------

# Los motivos frecuentes de rechazo, y «Otro motivo…» para escribirlo.
MOTIVOS_DE_RECHAZO = (
    "Ya está en el catálogo",
    "No lo vamos a traer",
    "Los datos están mal",
    "Lo cargué por error",
)
BORRADORES_POR_CONSULTA = 5
_BORRADOR_EN_LA_PREGUNTA = re.compile(r"rechazar el borrador #(\d+)")


def _e(valor):
    return html.escape(str(valor))


def _texto_del_borrador(borrador, encabezado=""):
    """La ficha corta de un borrador, para el chat: lo que hace falta para decidir
    si se rechaza ahí mismo o se abre en la web."""
    from apps.catalog import services as catalogo

    lineas = [encabezado] if encabezado else []
    lineas.append(f"<b>{_e(borrador)}</b> · borrador #{borrador.pk}")
    clasificacion = [
        str(borrador.editorial or "sin editorial"),
        str(borrador.tipo or "sin tipo"),
    ]
    if borrador.formato:
        clasificacion.append(str(borrador.formato))
    elif borrador.tipo and borrador.tipo.usa_formato:
        clasificacion.append("sin formato")
    lineas.append(_e(" · ".join(clasificacion)))
    precio = pesos(borrador.precio) if borrador.precio else "sin precio"
    estado = (
        f"Pre-venta, llega el {borrador.fecha_llegada:%d/%m/%Y}"
        if borrador.nace_en_pre_venta and borrador.fecha_llegada
        else borrador.get_estado_sugerido_display()
    )
    lineas.append(f"{_e(precio)} · {_e(estado)}")
    if borrador.origen == borrador.TELEGRAM:
        quien = borrador.cargado_por.get_full_name() if borrador.cargado_por else ""
        lineas.append(f"<i>Cargado por Telegram{_e(f' por {quien}') if quien else ''}</i>")
    elif borrador.proveedor:
        lineas.append(f"<i>De un correo de {_e(borrador.proveedor)}</i>")
    parecidos = catalogo.parecidos_al_borrador(borrador)
    if parecidos.producto:
        lineas.append(
            f"⚠ <b>Ya está en el catálogo</b>: {_e(parecidos.producto)} "
            f"(<code>{_e(parecidos.producto.codigo)}</code>)"
        )
    for producto in parecidos.productos:
        lineas.append(
            f"≈ Parecido en el catálogo: {_e(producto)} · {_e(producto.editorial)}"
            + (f" · {_e(producto.formato)}" if producto.formato else "")
        )
    for otro in parecidos.borradores:
        lineas.append(f"≈ Otro borrador abierto: {_e(otro)} · borrador #{otro.pk}")
    if borrador.reparos:
        reparos = "; ".join(borrador.reparos)
        lineas.append("Para mirar: " + _e(reparos if len(reparos) < 300 else reparos[:297] + "…"))
    ficha = enlace("catalog:borrador_detalle", borrador.pk)
    if ficha:
        lineas.append(f'<a href="{_e(ficha)}">Revisarlo en Longbox</a>')
    return "\n".join(lineas)


def mostrar_borrador(chat_id, borrador, *, encabezado=""):
    """La vista previa de un borrador: la portada con su ficha, o la ficha sola.
    Si está abierto, con «Rechazar…». **Nunca con un botón de confirmar**: el
    producto nace en la web, con la revisión entera a la vista (regla 4)."""
    texto = _texto_del_borrador(borrador, encabezado)
    botones = (
        [[{"text": "Rechazar…", "callback_data": _boton_de("rb", borrador.pk, chat_id)}]]
        if borrador.esta_abierto
        else None
    )
    foto = miniatura(borrador.portada)
    if foto and len(texto) <= telegram.TOPE_DE_EPIGRAFE:
        if telegram.enviar_foto(chat_id, foto, texto, botones=botones) is not None:
            return
    telegram.enviar(chat_id, texto, botones=botones)


def _borradores(chat_id, texto=""):
    """`/borradores [título]`: los abiertos, los más nuevos primero, con su vista previa."""
    from apps.catalog.models import BorradorProducto
    from apps.catalog.services import titulo_comparable

    if administrador_del_chat(chat_id) is None:
        return
    abiertos = BorradorProducto.objects.pendientes().select_related(
        "editorial", "tipo", "formato", "proveedor", "cargado_por"
    )
    abiertos = abiertos.order_by("-creado_en", "-pk")
    buscado = titulo_comparable(texto)
    if buscado:
        abiertos = [b for b in abiertos if buscado in titulo_comparable(b.titulo)]
    abiertos = list(abiertos)
    filtro = f" con «{_e(texto)}»" if buscado else ""
    if not abiertos:
        telegram.enviar(chat_id, f"No hay borradores para revisar{filtro}.")
        return
    lista = enlace("catalog:borrador_lista")
    cabecera = f"<b>{len(abiertos)} borrador(es) para revisar{filtro}.</b>"
    if len(abiertos) > BORRADORES_POR_CONSULTA:
        cabecera += f" Te muestro los {BORRADORES_POR_CONSULTA} más nuevos."
    cabecera += " Desde acá se rechazan; se confirman en la web."
    if lista:
        cabecera += f'\n\n<a href="{_e(lista)}">Todos los borradores</a>'
    telegram.enviar(chat_id, cabecera)
    for borrador in abiertos[:BORRADORES_POR_CONSULTA]:
        mostrar_borrador(chat_id, borrador)


def _preguntar_motivo_de_rechazo(chat_id, borrador_pk):
    from apps.catalog.models import BorradorProducto

    borrador = BorradorProducto.objects.filter(pk=borrador_pk).first()
    nombre = f" «{_e(borrador)}»" if borrador else ""
    botones = [
        [{"text": motivo, "callback_data": _boton_de("rm", borrador_pk, chat_id, str(i))}]
        for i, motivo in enumerate(MOTIVOS_DE_RECHAZO)
    ]
    botones.append(
        [{"text": "Otro motivo…", "callback_data": _boton_de("ro", borrador_pk, chat_id)}]
    )
    telegram.enviar(
        chat_id, f"¿Por qué se rechaza el borrador #{borrador_pk}{nombre}?", botones=botones
    )


def _rechazar(chat_id, borrador_pk, motivo):
    """El rechazo de `CU-ALT-REV`, con el motivo obligatorio y la misma auditoría."""
    from apps.catalog import revisiones
    from apps.catalog.models import BorradorProducto

    usuario = administrador_del_chat(chat_id)
    motivo = " ".join((motivo or "").split())[:500]
    if usuario is None:
        telegram.enviar(chat_id, NO_VINCULADO)
        return
    if not motivo:
        telegram.enviar(chat_id, "El motivo es obligatorio.")
        return
    borrador = BorradorProducto.objects.filter(pk=borrador_pk).first()
    if borrador is None:
        telegram.enviar(chat_id, f"El borrador #{borrador_pk} ya no existe.")
        return
    if revisiones.rechazar(borrador, actor=usuario, motivo=motivo, desde="Telegram") is None:
        borrador.refresh_from_db()
        telegram.enviar(
            chat_id,
            f"El borrador #{borrador_pk} ya no está abierto: {_e(borrador.get_estado_display())}.",
        )
        return
    telegram.enviar(chat_id, f"Se rechazó el borrador «{_e(borrador)}»: {_e(motivo)}.")


# ---------------------------------------------------------------------------
# CU-AVI-INL · compartir un producto desde cualquier chat
# ---------------------------------------------------------------------------

RESULTADOS_INLINE = 10


def _inline(consulta):
    """`@bot berserk` en cualquier chat: los productos de la tienda que coinciden.

    **Sólo para Administradores vinculados y activos** (ambigüedad 5): Telegram dice
    quién pregunta, y el id de un usuario es el de su chat privado con el bot. A
    cualquier otro se le contesta vacío. Lo que se comparte es **lo que muestra la
    tienda** (ambigüedad 4); el stock exacto aparece sólo en la lista, que ve
    únicamente quien elige.
    """
    from apps.avisos import consultas
    from apps.core.views_tienda import visibles

    quien = (consulta.get("from") or {}).get("id")
    texto = " ".join((consulta.get("query") or "").split())
    resultados = []
    if quien is not None and administrador_del_chat(quien) is not None and len(texto) >= 2:
        encontrados = [p.pk for p in consultas.buscar(texto, limite=RESULTADOS_INLINE)]
        productos = {p.pk: p for p in visibles().filter(pk__in=encontrados)}
        resultados = [_resultado_inline(productos[pk]) for pk in encontrados if pk in productos]
    telegram.responder_inline(consulta["id"], resultados)


def _resultado_inline(producto):
    from django.conf import settings
    from django.urls import reverse

    from apps.catalog.precio_visible import precio_visible
    from apps.core.views_tienda import AGOTADO, PRE_VENTA, estado_publico

    especifico = producto.especifico
    precio = pesos(precio_visible(producto))
    estado = estado_publico(producto)
    if estado == PRE_VENTA:
        llegada = getattr(especifico, "llegada_vigente", None)
        disponibilidad = f"En pre-venta{f', llega el {llegada:%d/%m/%Y}' if llegada else ''}"
    elif estado == AGOTADO:
        disponibilidad = "Agotado por ahora"
    else:
        disponibilidad = "Disponible"
    origen = getattr(especifico, "editorial", None) or getattr(especifico, "marca", "")
    lineas = [f"<b>{_e(especifico)}</b>"]
    if origen:
        lineas.append(_e(origen))
    lineas.append(f"{_e(precio)} · {_e(disponibilidad)}")
    if settings.URL_PUBLICA:
        ficha = settings.URL_PUBLICA + reverse("core:tienda_producto", args=[producto.pk])
        lineas.append(f'<a href="{_e(ficha)}">Verlo en la tienda</a>')
    resultado = {
        "type": "article",
        "id": str(producto.pk),
        "title": str(especifico),
        # Lo ve sólo el Administrador, en la lista: ahí sí va el stock.
        "description": f"{precio} · {disponibilidad} · stock {producto.stock}",
        "input_message_content": {
            "message_text": "\n".join(lineas),
            "parse_mode": "HTML",
            "link_preview_options": {"is_disabled": True},
        },
    }
    if settings.URL_PUBLICA.startswith("https://") and producto.portada:
        resultado["thumbnail_url"] = settings.URL_PUBLICA + producto.portada.url
    return resultado
