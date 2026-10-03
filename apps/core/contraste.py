"""Contraste entre dos colores, según WCAG 2.2.

Lo usa la identidad visual de la tienda (CU-CFG-VIS): `identidad_visual.md` pide
rechazar combinaciones con menos de 4,5:1 contra el fondo y elegir solo el texto
que va sobre el color primario.
"""

MINIMO_TEXTO = 4.5


def _canal(valor):
    valor = valor / 255
    return valor / 12.92 if valor <= 0.03928 else ((valor + 0.055) / 1.055) ** 2.4


def luminancia(hex_color):
    texto = hex_color.lstrip("#")
    rojo, verde, azul = (int(texto[i : i + 2], 16) for i in (0, 2, 4))
    return 0.2126 * _canal(rojo) + 0.7152 * _canal(verde) + 0.0722 * _canal(azul)


def contraste(uno, otro):
    claro, oscuro = sorted((luminancia(uno), luminancia(otro)), reverse=True)
    return (claro + 0.05) / (oscuro + 0.05)


def mas_legible(fondo, candidatos):
    """De los colores candidatos, el de mayor contraste sobre `fondo`."""
    return max(candidatos, key=lambda color: contraste(fondo, color))
