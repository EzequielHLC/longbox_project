"""El estilo preliminar plano no se degrada sin que nadie lo note.

Las reglas son las de `.contexto-ia/TOKENS_VISUALES.md` («Bordes, formas y
movimiento» y «Color») y las de `.contexto-ia/identidad_visual.md` («Cinco
reglas» y «Qué se retira»). Esta prueba recorre la hoja de estilo y todas las
plantillas, y falla con la lista completa de lo que encuentra, archivo por
archivo, para que el arreglo no sea adivinar dónde está el problema.

Lo que mira es el texto fuente, sin los comentarios. No renderiza nada: una
regla de estilo que aparece en una plantilla aparece siempre, se dibuje o no.
"""

import re
from pathlib import Path

import pytest
from django.conf import settings

RAIZ = Path(settings.BASE_DIR)
HOJA = RAIZ / "static" / "css" / "longbox.css"

TOKENS_DE_COLOR = {
    "--papel": "#FFFFFF",
    "--tinta": "#111111",
    "--grafito": "#555555",
    "--gris-control": "#767676",
    "--gris-linea": "#D6D6D6",
    "--gris-fondo": "#F2F2F2",
}

# Las plantillas del modo público pueden leer las variables de la tienda; las
# del operativo, nunca (`TOKENS_VISUALES.md`, «El modo operativo no lee nunca
# estas variables»).
PLANTILLAS_CON_VARIABLES_DE_TIENDA = {"base_publico.html", "tienda.css"}

NOMBRES_DE_COLOR = (
    "black|white|red|green|blue|yellow|orange|purple|pink|brown|gray|grey|cyan|magenta|"
    "navy|teal|silver|maroon|olive|lime|aqua|fuchsia|gold|indigo|violet|crimson"
)

# La paleta retirada y la de Tailwind, usadas como clase: `bg-signal`,
# `text-slate-500`, `border-azure`.
CLASE_DE_COLOR = re.compile(
    r"\b(?:bg|text|border(?:-[lrtbxy])?|ring|fill|stroke|from|to|via|outline|decoration|"
    r"placeholder|accent|divide)-"
    r"(?:void|ash|panel|line|static|screen|signal2?|azure|slate|gray|zinc|neutral|stone|"
    r"red|orange|amber|yellow|lime|green|emerald|teal|cyan|sky|blue|indigo|violet|purple|"
    r"fuchsia|pink|rose|white|black)\b"
)
# Clases de Tailwind que traen tamaño, espaciado, peso o tipografía literales.
CLASE_LITERAL = re.compile(
    r"(?<![\w-])(?:-?(?:m|p)[trblxy]?-(?:\d|\[)|gap(?:-[xy])?-\d|space-[xy]-\d|"
    r"text-(?:xs|sm|base|lg|[2-9]?xl|\[)|font-(?:display|body|mono|medium|semibold|bold|"
    r"extrabold|light)|tracking-|leading-|uppercase|italic|rounded|shadow|"
    r"[wh]-(?:\d|\[)|max-w-|min-w-\[|tabular-nums)(?![\w-])"
)

PROHIBIDO_EN_CSS = [
    (re.compile(r"(?<![\w-])animation(?:-[\w-]+)?\s*:"), "animation"),
    (re.compile(r"(?<![\w-])transition(?:-[\w-]+)?\s*:"), "transition"),
    (re.compile(r"@keyframes"), "@keyframes"),
    (re.compile(r"clip-path\s*:"), "clip-path"),
    # El espacio va dentro de la negación: afuera, `\s*` retrocede y deja
    # pasar justamente el valor permitido.
    (
        re.compile(r"border(?:-[\w-]+)?-radius\s*:(?!\s*(?:0\s*[;}]|var\(--radio\)))"),
        "border-radius ≠ 0",
    ),
    (re.compile(r"(?:box|text)-shadow\s*:(?!\s*(?:none\s*[;}]|var\(--sombra\)))"), "sombra"),
    (re.compile(r"(?:linear|radial|conic|repeating-\w+)-gradient"), "gradiente"),
    (re.compile(r"@import|@font-face|fonts\.googleapis|fonts\.gstatic"), "fuente web"),
    (re.compile(r"(?<![\w-])(?:backdrop-)?filter\s*:"), "filtro"),
    (re.compile(r"(?<![\w-])transform\s*:"), "transform"),
    (re.compile(r"url\("), "imagen de fondo literal"),
    (re.compile(r"(?<![\w-])opacity\s*:(?!\s*[01]\s*[;}])"), "opacidad parcial"),
    (re.compile(r"letter-spacing\s*:"), "espaciado de letras"),
    (re.compile(r"font-variant\s*:\s*small-caps|text-transform\s*:\s*uppercase"), "versalitas"),
    (re.compile(r"font-style\s*:\s*italic"), "cursiva"),
    (re.compile(r"font-weight\s*:(?!\s*(?:400|600|normal)\s*[;}!])"), "peso fuera de 400/600"),
]

COLOR_LITERAL = re.compile(
    rf"#[0-9a-fA-F]{{3,8}}\b|\b(?:rgba?|hsla?)\(|(?<![\w-])(?:{NOMBRES_DE_COLOR})(?![\w-])"
)


def _sin_comentarios(texto):
    texto = re.sub(r"\{%\s*comment\s*%\}.*?\{%\s*endcomment\s*%\}", "", texto, flags=re.S)
    texto = re.sub(r"\{#.*?#\}", "", texto, flags=re.S)
    texto = re.sub(r"<!--.*?-->", "", texto, flags=re.S)
    texto = re.sub(r"/\*.*?\*/", "", texto, flags=re.S)
    return texto


def _plantillas():
    carpetas = [RAIZ / "templates", *sorted((RAIZ / "apps").glob("*/templates"))]
    return sorted(
        ruta
        for carpeta in carpetas
        for ruta in carpeta.rglob("*")
        if ruta.suffix in {".html", ".css"}
    )


def _relativa(ruta):
    return ruta.relative_to(RAIZ).as_posix()


def _fuera_del_bloque_de_tokens(css):
    """La hoja sin el bloque `:root`, que es el único lugar donde viven los colores."""
    return re.sub(r":root\s*\{.*?\}", "", css, count=1, flags=re.S)


def test_hay_hoja_y_plantillas_para_revisar():
    assert HOJA.exists()
    assert len(_plantillas()) > 40


def test_los_seis_colores_se_declaran_una_sola_vez_con_su_valor():
    css = _sin_comentarios(HOJA.read_text(encoding="utf-8"))
    bloque = re.search(r":root\s*\{(.*?)\}", css, flags=re.S).group(1)
    for token, valor in TOKENS_DE_COLOR.items():
        declaraciones = re.findall(rf"{re.escape(token)}\s*:\s*([^;]+);", css)
        assert declaraciones == [valor], f"{token}: {declaraciones}"
        assert f"{token}: {valor}" in bloque


def test_la_hoja_no_usa_nada_de_lo_prohibido():
    css = _sin_comentarios(HOJA.read_text(encoding="utf-8"))
    hallazgos = [nombre for patron, nombre in PROHIBIDO_EN_CSS if patron.search(css)]
    assert not hallazgos, hallazgos


def test_la_hoja_no_escribe_colores_fuera_de_los_tokens():
    css = _fuera_del_bloque_de_tokens(_sin_comentarios(HOJA.read_text(encoding="utf-8")))
    # `url(...)` y los nombres de propiedad (`color:`) no son colores.
    valores = re.findall(r":\s*([^;{}]+);", css)
    hallazgos = sorted({m.group(0) for v in valores for m in COLOR_LITERAL.finditer(v)})
    assert not hallazgos, hallazgos


@pytest.mark.parametrize("ruta", _plantillas(), ids=_relativa)
def test_la_plantilla_no_trae_estilo_propio_ni_efectos(ruta):
    texto = _sin_comentarios(ruta.read_text(encoding="utf-8"))
    hallazgos = []

    if ruta.suffix == ".html":
        if re.search(r"<style[\s>]", texto):
            hallazgos.append("bloque <style>")
        if re.search(r"\sstyle\s*=", texto):
            hallazgos.append("atributo style")
        if re.search(r"<(?:script|link)[^>]+(?:src|href)=\"https?://", texto):
            hallazgos.append("recurso externo")
        if re.search(r"fonts\.googleapis|cdn\.tailwindcss|tailwind\.config", texto):
            hallazgos.append("Tailwind o fuente web")
        hallazgos += sorted({f"clase de color «{m}»" for m in CLASE_DE_COLOR.findall(texto)})
        hallazgos += sorted({f"clase literal «{m}»" for m in CLASE_LITERAL.findall(texto)})
        if re.search(r"#[0-9a-fA-F]{6}\b|\brgba?\(", texto):
            hallazgos.append("color literal")
        if "data-texto" in texto:
            hallazgos.append("copia del barrido (data-texto)")

    if "--tienda-" in texto and ruta.name not in PLANTILLAS_CON_VARIABLES_DE_TIENDA:
        hallazgos.append("lee las variables --tienda-*")

    assert not hallazgos, hallazgos


def test_el_modo_operativo_no_lee_las_variables_de_la_tienda():
    css = _sin_comentarios(HOJA.read_text(encoding="utf-8"))
    for bloque in re.finditer(r"([^{}]+)\{([^{}]*)\}", css):
        selector, cuerpo = bloque.groups()
        if "--tienda-" in cuerpo:
            assert "modo-publico" in selector or "encabezado-publico" in selector, selector


def test_los_archivos_del_sistema_anterior_ya_no_estan():
    assert not (RAIZ / "templates" / "_desplegable.html").exists()
    assert not (RAIZ / "static" / "img" / "login-akihabara.jpg").exists()
