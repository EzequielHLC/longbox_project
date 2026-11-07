"""La voz de Long-bot (B-19-017): un compañero de trabajo animado, no un sistema.

El responsable lo pidió como un Jarvis «pero no tan formal»: te habla de vos y por
tu nombre, festeja una venta, te pone las pilas a la mañana. Tres reglas para que
la personalidad no tape el dato:

- **El dato va primero y no cambia**: la cifra, el título, el enlace. Lo que varía
  es la frase de alrededor, para que no suene a máquina repitiendo lo mismo.
- **Un emoji al frente de cada aviso**, que dice de qué es; adentro, con criterio.
- **Nunca inventa ni promete**: la charla del modelo no da cifras ni hace nada
  (`asistente.elegir_consulta`); lo que pasa en el sistema lo dicen estas frases.

Todo es HTML de Telegram: quien arma un texto con datos los escapa antes.
"""

import random

NOMBRE = "Long-bot"
LINEA = "━━━━━━━━━━━━━━"

# El emoji de cada tipo de aviso (`avisos.models.TIPOS`).
EMOJI = {
    "correos": "📬",
    "preventas": "📦",
    "pedidos": "🧾",
    "restock": "🔁",
    "devoluciones": "↩️",
    "stock_local": "🏪",
    "ventas": "💸",
    "resumen": "☀️",
    "seguridad": "🛡️",
    "sistema": "🩺",
    "modelo": "🤖",
}

# Lo que cierra cada aviso, si el tipo tiene algo que decir.
REMATES = {
    "ventas": ("¡Bien ahí! 🔥", "¡Otra más! 🙌", "Eso es lo que me gusta ver 💪", "¡Vamos! 🚀"),
    "seguridad": (
        "Si no te suena, mejor mirarlo ahora 👀",
        "Te lo marco por las dudas 🛡️",
        "Ojo con esto: si no fuiste vos, revisalo ya.",
    ),
    "sistema": ("Cuando puedas, le echás un ojo 🔧", "Mejor resolverlo antes de que moleste 🔧"),
    "preventas": ("Te lo dejo anotado 📌", "Para que no se escape 📌"),
    "pedidos": ("Esto espera una mano tuya 🙏", "Te lo dejo para cuando puedas 🙏"),
    "restock": ("Cuando quieras lo miramos 📋",),
    "devoluciones": ("Te lo dejo listo para resolver 👇",),
    "stock_local": ("Para el mostrador 👇",),
}

FRASES = {
    "presentacion": (
        "🤖 <b>¡Hola{coma}! Soy {bot}</b>, tu compañero en la comiquería.",
        "🤖 <b>Acá {bot}{coma}</b>, listo para darte una mano.",
    ),
    "no_vinculado": (
        "🤔 Mmm, este chat no está vinculado a un Administrador activo. Vinculalo desde tu "
        "perfil en Longbox y arrancamos.",
        "🔒 Todavía no nos conocemos: este chat no está vinculado a un Administrador activo. "
        "Se vincula desde tu perfil en Longbox.",
    ),
    "vinculado": (
        "🤝 <b>¡Listo{coma}! Ya somos equipo.</b>\nEste chat quedó vinculado a tu cuenta de "
        "Longbox. Elegí en tu perfil qué avisos querés por acá y mandá /ayuda para ver todo lo "
        "que hago.",
        "🎉 <b>¡Bienvenido a bordo{coma}!</b>\nEste chat quedó vinculado a tu cuenta de Longbox. "
        "Desde tu perfil elegís qué te aviso por acá; con /ayuda te muestro lo que sé hacer.",
    ),
    "desvinculado": (
        "👋 Listo, me desconecto: este chat ya no recibe avisos. Te llegan por correo. "
        "¡Cuando quieras volvés!",
        "👋 Hecho: este chat ya no recibe avisos y te llegan por correo. Acá voy a estar.",
    ),
    "comando_desconocido": (
        "🤷 No conozco /{comando}. Mandá /ayuda y te muestro lo que sé hacer.",
        "🤷 /{comando} no me suena. Probá con /ayuda.",
    ),
    "sin_modelo": (
        "😵 Ahora no puedo pensar: el modelo no contestó. Mientras tanto, los comandos andan: "
        "probá /stock o /pendientes.",
        "😵 Me quedé sin cerebro un momento: el modelo no contestó. Con comandos sigo: "
        "/stock, /llega o /pendientes.",
    ),
    "charla_sin_modelo": (
        "🙂 ¡Acá estoy! Eso no lo sé responder, pero mandá /ayuda y te muestro lo que hago.",
        "🙂 Eso no lo sé responder todavía. Con /ayuda ves todo lo que puedo hacer.",
    ),
    "procesando": ("🧠 Dale, lo leo y te cuento…", "🧠 Ahí voy, dame un toque…"),
    "revisando": ("🔄 Revisando la casilla…", "🔄 Me fijo si llegó algo…"),
    "motivo_obligatorio": ("✋ El motivo es obligatorio: contame por qué y lo hago.",),
}


def elegir(opciones):
    return random.choice(opciones)  # nosec B311 - varía una frase, no es seguridad


def nombre_de(usuario):
    """El nombre de pila para hablarle, o vacío."""
    return ((usuario.first_name if usuario else "") or "").strip().split(" ")[0]


def frase(clave, *, nombre="", **datos):
    """Una de las frases de `clave`, con `{coma}` (`, Ezequiel`) y los datos ya escapados."""
    coma = f", {nombre}" if nombre else ""
    return elegir(FRASES[clave]).format(coma=coma, bot=NOMBRE, **datos)


def remate(tipo):
    opciones = REMATES.get(tipo)
    return elegir(opciones) if opciones else ""


def encabezado(emoji, titulo):
    """La primera línea de un aviso: el emoji y el título en negrita, y la línea."""
    return f"{emoji} <b>{titulo}</b>\n{LINEA}"


DIAS = ("lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo")


def saludo_del_dia(nombre, hoy):
    dia = DIAS[hoy.weekday()]
    quien = f", {nombre}" if nombre else ""
    return elegir(
        (
            f"¡Buen día{quien}! Arrancamos el {dia} {hoy:%d/%m}",
            f"¡Buenas{quien}! Así viene el {dia} {hoy:%d/%m}",
            f"¡Arriba{quien}! Este es el {dia} {hoy:%d/%m}",
        )
    )


def cierre_del_resumen(pendientes):
    """La última línea del resumen de la mañana, según cuánto hay para hacer."""
    if pendientes == 0:
        return elegir(("Está todo al día. ¡Un lujo! ☕", "Nada urgente: día tranqui ☕"))
    if pendientes <= 3:
        return elegir(("Pinta un día tranqui. ¿Arrancamos? 💪", "Poquito para hoy. ¡A darle! 💪"))
    return elegir(("Hay bastante: café en mano y a darle ☕💪", "Día cargado, pero lo sacamos 💪"))
