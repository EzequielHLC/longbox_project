"""Viñeta Nocturna no se degrada sin que nadie lo note.

Las reglas son las de `.contexto-ia/TOKENS_VISUALES.md` y
`.contexto-ia/identidad_visual.md`, que reemplazaron al estilo preliminar plano
el 2026-10-02 (B-00-005). La prueba recorre `tokens.css`, la hoja de componentes y
todas las plantillas, y falla con la lista completa de lo que encuentra.

Lo que mira es el texto fuente, sin los comentarios. No renderiza nada.
"""

import re
from pathlib import Path

import pytest
from django.conf import settings

RAIZ = Path(settings.BASE_DIR)
TOKENS = RAIZ / "static" / "css" / "tokens.css"
TOKENS_DEL_RESPONSABLE = RAIZ / ".contexto-ia" / "tokens.css"
HOJA = RAIZ / "static" / "css" / "longbox.css"
FUENTES = RAIZ / "static" / "fuentes"

# El catálogo cerrado de `identidad_visual.md`: «No se crean animaciones fuera
# de esta lista».
ANIMACIONES = {
    "titulo-glitch",
    "portada-entra",
    "aparece",
    "sticker-pega",
    "barra-crece",
    "barrido-diagonal",
    "ticker",
    "ficha-entra",
    "sacudon",
    "destello-fila",
    "marcador-entra",
    "rebote-numero",
    "aviso-entra",
    "dialogo-entra",
    "latido",
    "barras-carga",
    "cinta-corre",
    # Plan 00 de interfaz, ambigüedad 3: el riel de estados del pedido.
    "riel-llena",
    "camion-avanza",
    "sello",
}

# Las del modo público pueden leer las variables de la tienda; las del
# operativo, nunca. La vista previa de la identidad visual es una miniatura de
# la tienda con `modo-publico`: su guion le cambia las variables.
PLANTILLAS_CON_VARIABLES_DE_TIENDA = {"base_publico.html", "tienda.css", "identidad_visual.html"}

NOMBRES_DE_COLOR = (
    "black|white|red|green|blue|yellow|orange|purple|pink|brown|gray|grey|cyan|magenta|"
    "navy|teal|silver|maroon|olive|lime|aqua|fuchsia|gold|indigo|violet|crimson"
)
COLOR_LITERAL = re.compile(
    rf"#[0-9a-fA-F]{{3,8}}\b|\b(?:rgba?|hsla?)\(|(?<![\w-])(?:{NOMBRES_DE_COLOR})(?![\w-])"
)

PROHIBIDO_EN_COMPONENTES = [
    (
        re.compile(r"border(?:-[\w-]+)?-radius\s*:(?!\s*(?:0\s*[;}]|var\(--radio\)))"),
        "border-radius ≠ 0",
    ),
    (re.compile(r"@import|fonts\.googleapis|fonts\.gstatic"), "fuente externa"),
    # `filter` sólo para la sombra dura del corte (patrón 1 de la identidad).
    (re.compile(r"(?<![\w-])filter\s*:(?!\s*(?:none|drop-shadow\(\d+px \d+px 0 ))"), "filtro"),
    (re.compile(r"font-weight\s*:\s*(?:100|200|300|600)\b"), "peso fuera de la escala"),
]


def _sin_comentarios(texto):
    texto = re.sub(r"\{%\s*comment\s*%\}.*?\{%\s*endcomment\s*%\}", "", texto, flags=re.S)
    texto = re.sub(r"\{#.*?#\}", "", texto, flags=re.S)
    texto = re.sub(r"<!--.*?-->", "", texto, flags=re.S)
    return re.sub(r"/\*.*?\*/", "", texto, flags=re.S)


# Los correos son la excepción documentada (B-00-008): un cliente de correo no
# lee hojas ni variables, y el estilo tiene que ir en línea. Sus reglas propias
# están en `test_correo.py`.
CORREOS = RAIZ / "templates" / "correo"


def _plantillas():
    carpetas = [RAIZ / "templates", *sorted((RAIZ / "apps").glob("*/templates"))]
    return sorted(
        ruta
        for carpeta in carpetas
        for ruta in carpeta.rglob("*")
        if ruta.suffix in {".html", ".css"} and CORREOS not in ruta.parents
    )


def _relativa(ruta):
    return ruta.relative_to(RAIZ).as_posix()


def test_los_tokens_del_sistema_son_los_del_responsable():
    """`TOKENS_VISUALES.md`: «Este documento y ese archivo dicen lo mismo»."""
    assert TOKENS.read_text(encoding="utf-8") == TOKENS_DEL_RESPONSABLE.read_text(encoding="utf-8")


def test_las_fuentes_estan_autoalojadas():
    for nombre in re.findall(r'url\("\.\./fuentes/([^"]+)"\)', TOKENS.read_text(encoding="utf-8")):
        assert (FUENTES / nombre).exists(), nombre


def test_la_hoja_de_componentes_no_escribe_colores():
    """Los componentes leen semánticos; los valores viven en `tokens.css`."""
    css = _sin_comentarios(HOJA.read_text(encoding="utf-8"))
    valores = re.findall(r":\s*([^;{}]+);", css)
    hallazgos = sorted({m.group(0) for v in valores for m in COLOR_LITERAL.finditer(v)})
    assert not hallazgos, hallazgos


def test_la_hoja_de_componentes_no_usa_nada_de_lo_prohibido():
    css = _sin_comentarios(HOJA.read_text(encoding="utf-8"))
    hallazgos = [nombre for patron, nombre in PROHIBIDO_EN_COMPONENTES if patron.search(css)]
    assert not hallazgos, hallazgos


def test_el_desenfoque_solo_va_en_el_telon_del_dialogo():
    """Plan 00 de interfaz, ambigüedad 2: `backdrop-filter` sólo en el `::backdrop`
    de un `<dialog>`, a 4px. En cualquier otro lado sigue prohibido."""
    css = _sin_comentarios(HOJA.read_text(encoding="utf-8"))
    for selector, cuerpo in re.findall(r"([^{}]+)\{([^{}]*backdrop-filter[^{}]*)\}", css):
        assert selector.strip().endswith("::backdrop"), selector.strip()
        assert re.findall(r"backdrop-filter\s*:\s*([^;]+);", cuerpo) == ["blur(4px)"], cuerpo


def test_las_sombras_son_duras():
    """Sin desenfoque: el tercer largo de toda sombra es 0, o es un token."""
    css = _sin_comentarios(HOJA.read_text(encoding="utf-8"))
    for valor in re.findall(r"box-shadow\s*:\s*([^;]+);", css):
        if valor.strip() in ("none",) or valor.strip().startswith("var(--sombra-golpe-"):
            continue
        largos = re.findall(r"-?\d+(?:\.\d+)?px|(?<![\w.])0(?![\w.%])", valor)
        assert len(largos) < 3 or largos[2] in ("0", "0px"), valor


def test_solo_hay_animaciones_del_catalogo():
    css = _sin_comentarios(HOJA.read_text(encoding="utf-8"))
    definidas = set(re.findall(r"@keyframes\s+([\w-]+)", css))
    usadas = {
        nombre
        for valor in re.findall(r"animation(?:-name)?\s*:\s*([^;]+);", css)
        for nombre in re.findall(r"[a-z][\w-]*", valor)
        if nombre in definidas or "-" in nombre and not nombre.startswith(("var", "curva"))
    }
    assert definidas <= ANIMACIONES, definidas - ANIMACIONES
    assert {n for n in usadas if n in definidas} <= ANIMACIONES


def test_el_movimiento_reducido_esta_declarado():
    assert "prefers-reduced-motion: reduce" in TOKENS.read_text(encoding="utf-8")
    assert "prefers-reduced-motion: reduce" in HOJA.read_text(encoding="utf-8")


def test_el_modo_operativo_no_lee_las_variables_de_la_tienda():
    css = _sin_comentarios(HOJA.read_text(encoding="utf-8"))
    for bloque in re.finditer(r"([^{}]+)\{([^{}]*)\}", css):
        selector, cuerpo = bloque.groups()
        if "--tienda-" in cuerpo:
            assert "modo-publico" in selector or "encabezado-publico" in selector, selector


@pytest.mark.parametrize("ruta", _plantillas(), ids=_relativa)
def test_la_plantilla_no_trae_estilo_propio(ruta):
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
            hallazgos.append("Tailwind o fuente externa")
        if re.search(r"#[0-9a-fA-F]{6}\b|\brgba?\(", texto):
            hallazgos.append("color literal")

    if "--tienda-" in texto and ruta.name not in PLANTILLAS_CON_VARIABLES_DE_TIENDA:
        hallazgos.append("lee las variables --tienda-*")

    assert not hallazgos, hallazgos


def test_el_sticker_no_aparece_en_el_mostrador():
    """Bangers, «nunca en el operativo»."""
    operativas = [
        ruta
        for ruta in _plantillas()
        if ruta.suffix == ".html" and "base_operativo.html" in ruta.read_text(encoding="utf-8")
    ]
    assert operativas
    for ruta in operativas:
        assert 'class="sticker' not in ruta.read_text(encoding="utf-8"), _relativa(ruta)


def test_los_archivos_del_sistema_anterior_ya_no_estan():
    assert not (RAIZ / "templates" / "_desplegable.html").exists()
    assert not (RAIZ / "static" / "img" / "login-akihabara.jpg").exists()
