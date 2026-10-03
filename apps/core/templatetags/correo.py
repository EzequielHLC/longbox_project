"""Los estilos de los correos HTML (B-00-008).

Un cliente de correo no lee hojas externas, ni variables CSS, ni `clip-path`, ni
degradés: lo que no va en línea, en cada etiqueta, no llega. Por eso los correos
son la única parte del sistema con `style=`, y por eso los estilos salen todos
de acá y no de cada plantilla: los colores son los de `tokens.css` copiados por
nombre, y una prueba verifica que sigan siéndolo.

Las familias van sin comillas para que el atributo no necesite escaparlas. Las
fuentes del sistema no viajan en el correo: Archivo y JetBrains Mono se usan si
el lector las tiene, y si no, sus equivalentes más cercanos.
"""

from django import template

register = template.Library()

# Primitivos de `tokens.css` que usan los correos, con su nombre de token.
PALETA = {
    "noche": "#0A0A0C",
    "asfalto": "#141418",
    "hormigon": "#1D1D23",
    "cable": "#2F2F37",
    "humo": "#9A9AA5",
    "tiza": "#D4D4DA",
    "hueso": "#F2EFE8",
    "senal": "#FF6A13",
    "senal-vivo": "#FF8A3D",
    "senal-hondo": "#B23E00",
    "alarma": "#FF4D5E",
}

TEXTO = "font-family:Archivo,Arial Narrow,Helvetica Neue,Arial,sans-serif"
MONO = "font-family:JetBrains Mono,Consolas,Courier New,monospace"
P = PALETA

ESTILOS = {
    "cuerpo": f"margin:0;padding:0;background-color:{P['noche']}",
    "fondo": f"background-color:{P['noche']}",
    "preencabezado": (
        f"display:none;max-height:0;overflow:hidden;opacity:0;color:{P['noche']};font-size:1px"
    ),
    "marco": "padding:32px 16px",
    "columna": "width:100%;max-width:600px",
    "celda-marca": "padding:0 4px 14px",
    "marca": (
        f"{TEXTO};font-size:22px;font-weight:900;letter-spacing:0.04em;"
        f"text-transform:uppercase;color:{P['hueso']}"
    ),
    "rombo": f"color:{P['senal']}",
    "rotulo": (
        f"{MONO};font-size:11px;letter-spacing:0.12em;text-transform:uppercase;"
        f"color:{P['humo']};text-align:right"
    ),
    "cinta-senal": f"background-color:{P['senal']};height:8px;font-size:0;line-height:0",
    "cinta-noche": f"background-color:{P['noche']};height:8px;font-size:0;line-height:0",
    "panel": (
        f"background-color:{P['asfalto']};border-left:1px solid {P['cable']};"
        f"border-right:6px solid {P['senal']};border-bottom:6px solid {P['senal']};"
        "padding:32px 32px 36px"
    ),
    "antetitulo": (
        f"margin:0 0 8px;{MONO};font-size:12px;font-weight:700;letter-spacing:0.12em;"
        f"text-transform:uppercase;color:{P['senal']}"
    ),
    "titulo": (
        f"margin:0 0 24px;{TEXTO};font-size:30px;font-weight:900;line-height:1.05;"
        f"letter-spacing:-0.01em;text-transform:uppercase;color:{P['hueso']}"
    ),
    "parrafo": f"margin:0 0 16px;{TEXTO};font-size:16px;line-height:1.6;color:{P['tiza']}",
    "secundario": f"margin:0 0 16px;{TEXTO};font-size:14px;line-height:1.6;color:{P['humo']}",
    "destacado": f"color:{P['hueso']};font-weight:700",
    "acciones": "padding:8px 0 24px",
    "boton-celda": f"background-color:{P['senal']};border-bottom:3px solid {P['senal-hondo']}",
    "boton": (
        f"display:inline-block;padding:14px 28px;{TEXTO};font-size:15px;font-weight:900;"
        f"letter-spacing:0.04em;text-transform:uppercase;color:{P['noche']};"
        "text-decoration:none"
    ),
    "enlace-caja": (
        f"margin:0 0 24px;padding:12px 14px;border:1px dashed {P['cable']};{MONO};"
        f"font-size:12px;line-height:1.5;word-break:break-all;color:{P['tiza']}"
    ),
    "enlace": f"color:{P['senal-vivo']};text-decoration:underline",
    "aviso": (
        f"margin:0 0 24px;padding:14px 16px;border-left:4px solid {P['alarma']};"
        f"background-color:{P['hormigon']};{TEXTO};font-size:15px;line-height:1.5;"
        f"color:{P['tiza']}"
    ),
    "aviso-prefijo": f"{MONO};font-weight:700;text-transform:uppercase;color:{P['alarma']}",
    "tabla": "width:100%;border-collapse:collapse;margin:0 0 24px",
    "th": (
        f"{MONO};font-size:11px;font-weight:700;letter-spacing:0.12em;text-transform:uppercase;"
        f"color:{P['humo']};text-align:left;padding:0 8px 8px;"
        f"border-bottom:2px solid {P['senal']}"
    ),
    "th-cifra": (
        f"{MONO};font-size:11px;font-weight:700;letter-spacing:0.12em;text-transform:uppercase;"
        f"color:{P['humo']};text-align:right;padding:0 8px 8px;"
        f"border-bottom:2px solid {P['senal']}"
    ),
    "td": (
        f"{TEXTO};font-size:15px;line-height:1.4;color:{P['tiza']};padding:10px 8px;"
        f"border-bottom:1px solid {P['cable']};vertical-align:top"
    ),
    "td-dato": (
        f"{MONO};font-size:13px;line-height:1.4;color:{P['tiza']};padding:10px 8px;"
        f"border-bottom:1px solid {P['cable']};vertical-align:top;white-space:nowrap"
    ),
    "td-cifra": (
        f"{MONO};font-size:15px;font-weight:700;color:{P['hueso']};padding:10px 8px;"
        f"border-bottom:1px solid {P['cable']};vertical-align:top;text-align:right"
    ),
    "total": (
        f"{MONO};font-size:12px;font-weight:700;letter-spacing:0.08em;"
        f"text-transform:uppercase;color:{P['hueso']};padding:14px 8px 0;text-align:right"
    ),
    "pie": f"padding:24px 4px 0;{MONO};font-size:11px;line-height:1.7;color:{P['humo']}",
}


@register.simple_tag
def estilo(nombre):
    """El estilo en línea de una pieza del correo: `style="{% estilo 'parrafo' %}"`."""
    return ESTILOS[nombre]


@register.simple_tag
def color(nombre):
    """Un color de la paleta, para atributos como `bgcolor`."""
    return PALETA[nombre]
