"""Las tarjetas ilustradas que acompañan algunos avisos de Telegram (B-19-020).

Se dibujan en el momento con Pillow, con los colores de `tokens.css` y las fuentes
de `static/fuentes`, en el lenguaje del escaparate (plan 07, novena parte): noche
con líneas de barrido, la palabra calada de fondo, el título en Archivo itálica
apretada con su sombra dura, las cifras como aparatos redondeados con su luz lima
y Long-bot asomando de un televisor con los rótulos de pantalla de un VHS.
**Long-bot es propio**: una caja de historietas (un longbox) con orejas de conejo
y la cara en una pantalla, en el espíritu de los bangboo de Zenless Zone Zero
pero sin copiar a ninguno.

Una tarjeta nunca reemplaza al texto: sale antes del mensaje, y si no se puede
dibujar o mandar, el mensaje sale igual. No lleva nada que el texto no diga.
"""

import logging
from functools import lru_cache
from io import BytesIO
from pathlib import Path

from django.conf import settings
from PIL import Image, ImageChops, ImageDraw, ImageFont

logger = logging.getLogger(__name__)

ANCHO, ALTO = 1280, 640
S = 2  # se dibuja al doble y se achica: Pillow no suaviza los bordes

# tokens.css, primitivos de color.
NOCHE = (10, 10, 12)
ASFALTO = (20, 20, 24)
HORMIGON = (29, 29, 35)
CABLE = (47, 47, 55)
HUMO = (154, 154, 165)
TIZA = (212, 212, 218)
HUESO = (242, 239, 232)
BLANCO = (255, 255, 255)
SENAL = (255, 106, 19)
SENAL_VIVO = (255, 138, 61)
SENAL_HONDO = (178, 62, 0)
ALARMA = (255, 77, 94)
ALARMA_HONDO = (196, 22, 42)
OK = (182, 242, 60)
DATO = (92, 200, 255)

# El tono pinta el panel de Long-bot: el acento, o la alarma para lo urgente.
TONOS = {"senal": (SENAL, SENAL_HONDO), "alarma": (ALARMA, ALARMA_HONDO)}

# Los gestos de Long-bot.
CONTENTO = "contento"
FESTEJO = "festejo"
GUINO = "guino"
ALERTA = "alerta"
TRISTE = "triste"

FUENTES = Path(settings.BASE_DIR) / "static" / "fuentes"
MARGEN = 64
ANCHO_TEXTO = 600

# El televisor de Long-bot: el aparato y, adentro, la pantalla.
TELE = (724, 58, 1232, 598)
PANTALLA = (748, 82, 1208, 520)
# Long-bot se dibuja a su tamaño y entra en la pantalla achicado, debajo de los rótulos.
ESCALA_BOT = 0.78
CENTRO_BOT_Y = 384


@lru_cache(maxsize=32)
def _fuente(archivo, tamano, peso=None):
    fuente = ImageFont.truetype(str(FUENTES / archivo), int(tamano * S))
    if peso:
        fuente.set_variation_by_name(peso)
    return fuente


@lru_cache(maxsize=32)
def _titular(tamano, ancho=72):
    """Archivo itálica negra y apretada: la voz de los títulos del escaparate."""
    fuente = ImageFont.truetype(str(FUENTES / "archivo-italic-variable.woff2"), int(tamano * S))
    fuente.set_variation_by_axes([900, ancho])
    return fuente


def _interfaz(tamano, peso="SemiBold"):
    return _fuente("archivo-variable.woff2", tamano, peso)


def _datos(tamano, peso="Bold"):
    return _fuente("jetbrains-mono-variable.woff2", tamano, peso)


class _Lienzo:
    """Coordenadas en píxeles de la tarjeta final; el doble de resolución queda acá adentro."""

    def __init__(self, transparente=False):
        if transparente:
            self.imagen = Image.new("RGBA", (ANCHO * S, ALTO * S), (0, 0, 0, 0))
        else:
            self.imagen = Image.new("RGB", (ANCHO * S, ALTO * S), NOCHE)
        self.dibujo = ImageDraw.Draw(self.imagen)

    @staticmethod
    def _e(*valores):
        return [round(v * S) for v in valores]

    def caja(self, x0, y0, x1, y1, *, radio=0, relleno=None, borde=None, grosor=0):
        self.dibujo.rounded_rectangle(
            self._e(x0, y0, x1, y1),
            radius=radio * S,
            fill=relleno,
            outline=borde,
            width=round(grosor * S),
        )

    def poligono(self, puntos, relleno, borde=None, grosor=0):
        self.dibujo.polygon(
            [tuple(self._e(x, y)) for x, y in puntos],
            fill=relleno,
            outline=borde,
            width=round(grosor * S),
        )

    def elipse(self, x0, y0, x1, y1, relleno=None, borde=None, grosor=0):
        self.dibujo.ellipse(
            self._e(x0, y0, x1, y1), fill=relleno, outline=borde, width=round(grosor * S)
        )

    def arco(self, cx, cy, radio, desde, hasta, color, grosor):
        self.dibujo.arc(
            self._e(cx - radio, cy - radio, cx + radio, cy + radio),
            desde,
            hasta,
            fill=color,
            width=round(grosor * S),
        )

    def linea(self, puntos, color, grosor):
        self.dibujo.line(
            [tuple(self._e(x, y)) for x, y in puntos],
            fill=color,
            width=round(grosor * S),
            joint="curve",
        )

    def texto(self, x, y, texto, fuente, color, *, ancla="la", borde=None, grosor=0):
        self.dibujo.text(
            tuple(self._e(x, y)),
            texto,
            font=fuente,
            fill=color,
            anchor=ancla,
            stroke_width=round(grosor * S),
            stroke_fill=borde,
        )

    @staticmethod
    def largo(texto, fuente):
        return fuente.getlength(texto) / S

    def jpeg(self):
        final = self.imagen.resize((ANCHO, ALTO), Image.Resampling.LANCZOS)
        salida = BytesIO()
        final.save(salida, "JPEG", quality=90, optimize=True)
        return salida.getvalue()


def _cortar(texto, fuente, ancho, lineas_maximas):
    """Parte el texto en renglones que entran en `ancho`; el último lleva «…» si sobra."""
    palabras, renglones, actual = texto.split(), [], ""
    for palabra in palabras:
        prueba = f"{actual} {palabra}".strip()
        if _Lienzo.largo(prueba, fuente) <= ancho or not actual:
            actual = prueba
        else:
            renglones.append(actual)
            actual = palabra
    if actual:
        renglones.append(actual)
    if len(renglones) > lineas_maximas:
        renglones = renglones[:lineas_maximas]
        ultimo = renglones[-1]
        while ultimo and _Lienzo.largo(ultimo + "…", fuente) > ancho:
            ultimo = ultimo[:-1]
        renglones[-1] = ultimo.rstrip() + "…"
    return renglones


def _ajustar(texto, ancho, tamanos, fuente_de, lineas_maximas):
    """El tamaño más grande con el que el texto entra en las líneas permitidas."""
    for tamano in tamanos:
        fuente = fuente_de(tamano)
        renglones = _cortar(texto, fuente, ancho, lineas_maximas)
        if not renglones[-1].endswith("…"):
            return fuente, tamano, renglones
    return fuente, tamano, renglones


# ---------------------------------------------------------------------------
# El fondo
# ---------------------------------------------------------------------------


def _barrido(lienzo, x0, y0, x1, y1, color, *, paso=4, alfa=70):
    """Las líneas de barrido de un monitor viejo, translúcidas."""
    capa = Image.new("RGBA", lienzo.imagen.size, (0, 0, 0, 0))
    dibujo = ImageDraw.Draw(capa)
    for y in range(round(y0 * S), round(y1 * S), round(paso * S)):
        dibujo.rectangle((round(x0 * S), y, round(x1 * S), y + S - 1), fill=(*color, alfa))
    lienzo.imagen.paste(capa, (0, 0), capa)


def _cinta(lienzo, y0, y1, color):
    """La cinta de peligro del sistema: bandas en diagonal, el acento y la noche."""
    lienzo.caja(0, y0, ANCHO, y1, relleno=NOCHE)
    alto, banda = y1 - y0, 14
    x = -alto
    while x < ANCHO:
        lienzo.poligono([(x, y1), (x + alto, y0), (x + alto + banda, y0), (x + banda, y1)], color)
        x += banda * 2


def _fondo(lienzo, tono):
    vivo, _ = TONOS[tono]
    # La palabra calada de fondo, como las del escaparate: sólo el contorno.
    lienzo.texto(
        MARGEN - 30,
        ALTO - 20,
        "LONGBOX",
        _titular(230, 62),
        NOCHE,
        ancla="ls",
        borde=CABLE,
        grosor=2,
    )
    _barrido(lienzo, 0, 0, ANCHO, ALTO, ASFALTO, paso=4, alfa=255)
    # La cinta de abajo, con el acento del tono.
    _cinta(lienzo, ALTO - 14, ALTO, vivo)


def _pantalla(lienzo, tono, gesto):
    """El televisor: el aparato redondeado, su sombra dura y la pantalla encendida."""
    vivo, hondo = TONOS[tono]
    x0, y0, x1, y1 = TELE
    lienzo.caja(x0 + 10, y0 + 10, x1 + 10, y1 + 10, radio=40, relleno=vivo)  # sombra dura
    lienzo.caja(x0, y0, x1, y1, radio=40, relleno=HORMIGON, borde=NOCHE, grosor=6)
    lienzo.caja(x0 + 10, y0 + 8, x1 - 10, y0 + 12, radio=2, relleno=CABLE)  # el brillo del borde
    px0, py0, px1, py1 = PANTALLA
    # La pantalla: el tono, más hondo hacia abajo, con su barrido y una banda de tracking.
    pantalla = Image.new("RGB", (round((px1 - px0) * S), round((py1 - py0) * S)), vivo)
    dibujo = ImageDraw.Draw(pantalla)
    alto = pantalla.height
    for y in range(alto):
        mezcla = max(0.0, (y / alto - 0.35) / 0.65)
        color = tuple(round(a + (b - a) * mezcla) for a, b in zip(vivo, hondo, strict=True))
        dibujo.line((0, y, pantalla.width, y), fill=color)
    mascara = Image.new("L", pantalla.size, 0)
    ImageDraw.Draw(mascara).rounded_rectangle((0, 0, *pantalla.size), radius=26 * S, fill=255)
    lienzo.imagen.paste(pantalla, (round(px0 * S), round(py0 * S)), mascara)
    _barrido(lienzo, px0, py0, px1, py1, hondo, paso=5, alfa=90)
    banda = py0 + (py1 - py0) * (0.78 if gesto != TRISTE else 0.3)
    for corrimiento, ancho, color in ((0, 7, BLANCO), (10, 3, TIZA), (-8, 2, BLANCO)):
        lienzo.caja(
            px0 + 6, banda + corrimiento, px1 - 6, banda + corrimiento + ancho, relleno=color
        )
    lienzo.caja(px0, py0, px1, py1, radio=26, borde=NOCHE, grosor=5)
    # Los rótulos de pantalla, como el OSD de una videocasetera.
    osd = _datos(20, "ExtraBold")
    if tono == "alarma":
        lienzo.elipse(px0 + 24, py0 + 24, px0 + 42, py0 + 42, relleno=BLANCO)
        lienzo.texto(px0 + 52, py0 + 33, "REC", osd, BLANCO, ancla="lm", borde=hondo, grosor=2)
    else:
        lienzo.poligono([(px0 + 24, py0 + 22), (px0 + 44, py0 + 33), (px0 + 24, py0 + 44)], BLANCO)
        lienzo.texto(px0 + 54, py0 + 33, "PLAY", osd, BLANCO, ancla="lm", borde=hondo, grosor=2)
    lienzo.texto(px1 - 24, py0 + 33, "SP  CH 03", osd, BLANCO, ancla="rm", borde=hondo, grosor=2)
    # El frente del aparato: la luz de encendido lima y la marca.
    luz_y = (py1 + y1) / 2
    lienzo.elipse(x0 + 34, luz_y - 9, x0 + 52, luz_y + 9, relleno=OK, borde=NOCHE, grosor=3)
    lienzo.texto(x0 + 64, luz_y, "POWER", _datos(14), HUMO, ancla="lm")
    lienzo.texto(x1 - 34, luz_y, "LONGBOX", _titular(26, 80), TIZA, ancla="rm")
    for indice in range(5):
        x = x1 - 236 + indice * 12
        lienzo.caja(x, luz_y - 10, x + 5, luz_y + 10, radio=2, relleno=CABLE)


# ---------------------------------------------------------------------------
# Long-bot
# ---------------------------------------------------------------------------


def _chispa(lienzo, cx, cy, radio, color):
    """Una estrellita de cuatro puntas."""
    fino = radio * 0.28
    lienzo.poligono(
        [
            (cx, cy - radio),
            (cx + fino, cy - fino),
            (cx + radio, cy),
            (cx + fino, cy + fino),
            (cx, cy + radio),
            (cx - fino, cy + fino),
            (cx - radio, cy),
            (cx - fino, cy - fino),
        ],
        color,
        NOCHE,
        3,
    )


def _oreja(lienzo, base_x, base_y, alto, angulo, acento):
    """Una oreja parada sobre (base_x, base_y), girada `angulo` grados (positivo, a la derecha).

    Se dibuja derecha en una capa aparte y se gira desde su base: Pillow no gira
    las figuras que dibuja.
    """
    ancho, tinta = 66, 8
    # Una capa cuadrada con la base de la oreja en el centro: gire para donde
    # gire, la oreja entra entera.
    lado = round(2 * (alto + 2 * tinta) * S)
    capa = Image.new("RGBA", (lado, lado), (0, 0, 0, 0))
    dibujo = ImageDraw.Draw(capa)
    centro = lado / 2
    x0, y0 = centro - ancho / 2 * S, centro - alto * S
    dibujo.rounded_rectangle(
        (x0, y0, x0 + ancho * S, centro),
        radius=ancho // 2 * S,
        fill=HUESO,
        outline=NOCHE,
        width=tinta * S,
    )
    dibujo.rounded_rectangle(
        (x0 + 19 * S, y0 + 26 * S, x0 + 47 * S, centro - 60 * S), radius=14 * S, fill=acento
    )
    girada = capa.rotate(-angulo, resample=Image.Resampling.BICUBIC)
    lienzo.imagen.paste(girada, (round(base_x * S - centro), round(base_y * S - centro)), girada)


def _orejas(lienzo, cx, cy, gesto, acento):
    base = cy - 80
    if gesto == TRISTE:
        angulos, alto = (-118, 118), 150
    elif gesto == ALERTA:
        angulos, alto = (-4, 4), 236
    else:
        # Una derecha y la otra ladeada: tiene onda.
        angulos, alto = (-6, 18), 214
    for lado, angulo in zip((-1, 1), angulos, strict=True):
        _oreja(lienzo, cx + lado * 80, base, alto, angulo, acento)


def _cara(lienzo, cx, cy, gesto):
    """La pantalla con los ojos de luz."""
    lienzo.caja(
        cx - 118, cy - 44, cx + 118, cy + 96, radio=28, relleno=NOCHE, borde=CABLE, grosor=5
    )
    lienzo.linea([(cx - 92, cy - 22), (cx - 62, cy - 30)], HORMIGON, 6)  # el brillo del vidrio
    luz = {ALERTA: ALARMA, TRISTE: DATO}.get(gesto, SENAL_VIVO)
    ojo_y = cy + 20
    izquierda, derecha = cx - 50, cx + 50
    if gesto in (CONTENTO, FESTEJO):
        for x in (izquierda, derecha):
            lienzo.arco(x, ojo_y + 10, 24, 200, 340, luz, 11)
    elif gesto == GUINO:
        lienzo.arco(izquierda, ojo_y + 10, 24, 200, 340, luz, 11)
        lienzo.caja(derecha - 15, ojo_y - 24, derecha + 15, ojo_y + 18, radio=15, relleno=luz)
    elif gesto == ALERTA:
        for x in (izquierda, derecha):
            lienzo.elipse(x - 22, ojo_y - 26, x + 22, ojo_y + 22, relleno=luz)
            lienzo.elipse(x - 10, ojo_y - 16, x + 2, ojo_y - 4, relleno=BLANCO)
    elif gesto == TRISTE:
        for x, lado in ((izquierda, -1), (derecha, 1)):
            lienzo.elipse(x - 13, ojo_y - 6, x + 13, ojo_y + 20, relleno=luz)
            # Cejas caídas hacia afuera.
            lienzo.linea([(x + lado * 30, ojo_y - 14), (x - lado * 12, ojo_y - 30)], luz, 6)
        # Una lágrima.
        lienzo.poligono(
            [
                (izquierda - 6, ojo_y + 30),
                (izquierda - 14, ojo_y + 48),
                (izquierda + 2, ojo_y + 48),
            ],
            luz,
        )
        lienzo.elipse(izquierda - 15, ojo_y + 40, izquierda + 3, ojo_y + 58, relleno=luz)
    # La boca.
    boca_y = cy + 72
    if gesto == FESTEJO:
        lienzo.dibujo.pieslice(
            lienzo._e(cx - 20, boca_y - 22, cx + 20, boca_y + 14), 0, 180, fill=luz
        )
    elif gesto == ALERTA:
        lienzo.elipse(cx - 9, boca_y - 12, cx + 9, boca_y + 6, borde=luz, grosor=5)
    elif gesto == TRISTE:
        lienzo.arco(cx, boca_y + 8, 14, 205, 335, luz, 5)
    else:
        lienzo.arco(cx, boca_y - 14, 16, 25, 155, luz, 5)


def long_bot(lienzo, cx, cy, gesto, tono="senal"):
    """Long-bot con el centro del cuerpo en (cx, cy)."""
    vivo, hondo = TONOS[tono]
    tinta = 8
    lienzo.elipse(cx - 175, cy + 150, cx + 175, cy + 190, relleno=hondo)  # sombra
    if gesto == FESTEJO:
        for x, y, r, c in (
            (-230, -210, 26, BLANCO),
            (215, -250, 20, OK),
            (250, -120, 14, BLANCO),
            (-260, -60, 16, DATO),
        ):
            _chispa(lienzo, cx + x, cy + y, r, c)
    _orejas(lienzo, cx, cy, gesto, vivo)
    # Las patas.
    for lado in (-1, 1):
        x = cx + lado * 70
        lienzo.caja(
            x - 28, cy + 100, x + 28, cy + 168, radio=14, relleno=CABLE, borde=NOCHE, grosor=tinta
        )
    # Los brazos: en el festejo y el guiño, uno arriba.
    lienzo.caja(
        cx - 196, cy + 6, cx - 146, cy + 86, radio=22, relleno=TIZA, borde=NOCHE, grosor=tinta
    )
    if gesto in (FESTEJO, GUINO):
        lienzo.caja(
            cx + 150, cy - 112, cx + 200, cy - 10, radio=22, relleno=TIZA, borde=NOCHE, grosor=tinta
        )
    else:
        lienzo.caja(
            cx + 146, cy + 6, cx + 196, cy + 86, radio=22, relleno=TIZA, borde=NOCHE, grosor=tinta
        )
    # El cuerpo es la caja; la tapa, con la etiqueta.
    lienzo.caja(
        cx - 158, cy - 96, cx + 158, cy + 128, radio=30, relleno=HUESO, borde=NOCHE, grosor=tinta
    )
    lienzo.caja(
        cx - 172, cy - 124, cx + 172, cy - 66, radio=20, relleno=TIZA, borde=NOCHE, grosor=tinta
    )
    lienzo.caja(cx - 40, cy - 112, cx + 40, cy - 78, radio=4, relleno=vivo, borde=NOCHE, grosor=4)
    lienzo.texto(cx, cy - 95, "LB", _titular(26, 80), NOCHE, ancla="mm")
    _cara(lienzo, cx, cy, gesto)
    if gesto == ALERTA:
        # El globo con el signo.
        lienzo.caja(
            cx + 150, cy - 300, cx + 236, cy - 206, radio=18, relleno=BLANCO, borde=NOCHE, grosor=6
        )
        lienzo.poligono(
            [(cx + 166, cy - 214), (cx + 150, cy - 180), (cx + 196, cy - 210)], BLANCO, NOCHE, 6
        )
        lienzo.caja(cx + 158, cy - 218, cx + 228, cy - 208, relleno=BLANCO)
        lienzo.texto(cx + 193, cy - 254, "!", _titular(72, 100), ALARMA_HONDO, ancla="mm")


# ---------------------------------------------------------------------------
# La tarjeta
# ---------------------------------------------------------------------------


def _cifras(lienzo, cifras, y, tono):
    """Las cifras como aparatos: paneles redondeados, la sombra dura y la luz lima en la primera."""
    vivo, _ = TONOS[tono]
    cifras = list(cifras)[:4]
    hueco = 16
    ancho = (ANCHO_TEXTO - hueco * (len(cifras) - 1)) / len(cifras)
    alto = 112
    for i, (rotulo, valor) in enumerate(cifras):
        x0 = MARGEN + i * (ancho + hueco)
        x1 = x0 + ancho
        lienzo.caja(x0 + 6, y + 6, x1 + 6, y + alto + 6, radio=16, relleno=vivo)
        lienzo.caja(x0, y, x1, y + alto, radio=16, relleno=ASFALTO, borde=CABLE, grosor=3)
        rotulo_fuente = _datos(15)
        sangria = 20
        if i == 0:
            lienzo.elipse(x0 + 20, y + 22, x0 + 30, y + 32, relleno=OK)
            sangria = 38
        renglon = _cortar(str(rotulo).upper(), rotulo_fuente, ancho - sangria - 16, 1)[0]
        lienzo.texto(
            x0 + sangria, y + 27, renglon, rotulo_fuente, OK if i == 0 else HUMO, ancla="lm"
        )
        valor = str(valor)
        fuente = next(
            (
                _datos(t, "ExtraBold")
                for t in (46, 40, 34, 28, 24, 20, 17)
                if lienzo.largo(valor, _datos(t, "ExtraBold")) <= ancho - 36
            ),
            _datos(20, "ExtraBold"),
        )
        valor = _cortar(valor, fuente, ancho - 36, 1)[0]
        lienzo.texto(x0 + 20, y + alto - 20, valor, fuente, BLANCO, ancla="ls")


def dibujar(titulo, *, bajada="", cifras=(), gesto=CONTENTO, tono="senal", rotulo="Long-bot"):
    """Los bytes JPEG de la tarjeta (1280 × 640)."""
    vivo, _ = TONOS[tono]
    bajada = str(bajada)
    lienzo = _Lienzo()
    _fondo(lienzo, tono)
    _pantalla(lienzo, tono, gesto)
    # Long-bot, adentro de la tele: se dibuja aparte, se achica y se recorta a la pantalla.
    bot = _Lienzo(transparente=True)
    long_bot(bot, ANCHO / 2, ALTO / 2, gesto, tono)
    chico = bot.imagen.resize(
        (round(bot.imagen.width * ESCALA_BOT), round(bot.imagen.height * ESCALA_BOT)),
        Image.Resampling.LANCZOS,
    )
    capa = Image.new("RGBA", bot.imagen.size, (0, 0, 0, 0))
    centro_x = (PANTALLA[0] + PANTALLA[2]) / 2
    capa.paste(
        chico,
        (
            round((centro_x - ANCHO / 2 * ESCALA_BOT) * S),
            round((CENTRO_BOT_Y - ALTO / 2 * ESCALA_BOT) * S),
        ),
    )
    pantalla = Image.new("L", capa.size, 0)
    ImageDraw.Draw(pantalla).rounded_rectangle(
        [round(v * S) for v in (*PANTALLA[:3], PANTALLA[3] - 3)], radius=26 * S, fill=255
    )
    lienzo.imagen.paste(capa, (0, 0), ImageChops.darker(capa.getchannel("A"), pantalla))

    # El rótulo de arriba, como el de las secciones: la luz lima y el texto de datos.
    lienzo.elipse(MARGEN, 56, MARGEN + 14, 70, relleno=OK if tono == "senal" else vivo)
    lienzo.texto(MARGEN + 26, 63, f"LONGBOX · {rotulo}".upper(), _datos(18), HUMO, ancla="lm")

    hay_cifras = bool(cifras)
    fuente, tamano, renglones = _ajustar(
        titulo.upper(), ANCHO_TEXTO, (104, 92, 80, 70, 62, 54), _titular, 2
    )
    y = 104
    interlineado = tamano * 0.92
    for renglon in renglones:
        # La sombra dura del sistema, corrida hacia abajo y a la derecha.
        lienzo.texto(MARGEN + 5, y + 5, renglon, fuente, vivo)
        lienzo.texto(MARGEN, y, renglon, fuente, BLANCO)
        y += interlineado
    if bajada:
        tamano_bajada = 28 if hay_cifras else 34
        fuente_bajada = _interfaz(tamano_bajada, "Medium")
        y += 18
        for renglon in _cortar(bajada, fuente_bajada, ANCHO_TEXTO, 2 if hay_cifras else 3):
            lienzo.texto(MARGEN, y, renglon, fuente_bajada, TIZA)
            y += tamano_bajada * 1.3
    if hay_cifras:
        _cifras(lienzo, cifras, ALTO - 168, tono)
    return lienzo.jpeg()


def mandar(chat_id, titulo, **detalles):
    """Dibuja la tarjeta y la manda sola, sin epígrafe. `None` si no salió."""
    from apps.avisos import telegram

    imagen = tarjeta(titulo, **detalles)
    return telegram.enviar_foto(chat_id, imagen, "") if imagen else None


def tarjeta(titulo, **detalles):
    """Como `dibujar`, pero `None` si algo falla: la tarjeta acompaña, nunca frena un aviso."""
    try:
        return dibujar(str(titulo), **detalles)
    except Exception:  # cualquier cosa: sin tarjeta, el aviso sale igual
        logger.exception("No se pudo dibujar la tarjeta de Telegram «%s».", titulo)
        return None
