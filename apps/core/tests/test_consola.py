"""La salida de consola en ASCII.

Existe por un modo de falla concreto en Windows: la consola corre en cp1252, y
un comando que imprima un carácter fuera de ese juego muere con
`UnicodeEncodeError` **después** de haber hecho el trabajo — la base quedó
escrita y la salida no alcanzó a decir cuánto se procesó.

Los textos propios del proyecto ya se escriben en ASCII. El problema son los
ajenos: el asunto de un correo, el título de un manga, la razón social que cargó
una persona. Eso no se puede pedir que venga en ASCII.
"""

import pytest

from apps.core.consola import ascii_seguro

# Este archivo no toca la base ni la red.


@pytest.mark.parametrize(
    ("original", "esperado"),
    [
        # El caso que lo destapó: el nombre de un formato de manga.
        ("Tank\u014dbon", "Tankobon"),
        # Y el más frecuente: cualquier texto en castellano.
        ("Reprogramaci\u00f3n de Berserk", "Reprogramacion de Berserk"),
        ("Editorial \u00d1and\u00fa S.A.", "Editorial Nandu S.A."),
        # Lo que ya es ASCII pasa intacto.
        ("Editorial Ivrea S.A.", "Editorial Ivrea S.A."),
    ],
)
def test_los_diacriticos_se_sacan_conservando_la_lectura(original, esperado):
    """Se descompone y se quitan las tildes en vez de reemplazar la letra
    entera: "Tankobon" se lee, "T?nk?bon" no."""
    assert ascii_seguro(original) == esperado


def test_lo_que_no_tiene_equivalente_se_reemplaza_sin_romper():
    """Un kanji no se puede transcribir. Perder ese carácter es peor que el
    original pero infinitamente mejor que perder el resto de la salida."""
    resultado = ascii_seguro("Vol. 3 de \u9032\u6483\u306e\u5de8\u4eba")

    assert resultado.startswith("Vol. 3 de ")
    assert resultado.isascii()


def test_el_resultado_siempre_se_puede_escribir_en_la_consola():
    """La garantía que el módulo entero existe para dar."""
    for texto in ["Tank\u014dbon", "\u9032\u6483", "caf\u00e9", "\u2192 flecha"]:
        ascii_seguro(texto).encode("cp1252")


@pytest.mark.parametrize("vacio", ["", None])
def test_un_valor_vacio_no_rompe(vacio):
    """Un asunto ausente es normal; que el comando explote por eso, no."""
    assert ascii_seguro(vacio) == ""
