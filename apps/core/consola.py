"""Salida de consola que no revienta en Windows.

La consola de Windows corre en cp1252. Un comando que imprima un carácter fuera
de ese juego —una tilde larga, un `→`, la `ō` de "Tankōbon"— muere con
`UnicodeEncodeError`, y muere **después** de haber hecho el trabajo: la base
quedó escrita y la salida no alcanzó a decir cuánto se procesó. Es el peor orden
posible para fallar.

Los textos propios del proyecto ya se escriben en ASCII a propósito. El problema
son los **ajenos**: el asunto de un correo, el título de un manga, la razón
social de un proveedor. Eso no se puede pedir que venga en ASCII, así que se
transcribe al imprimirlo.

Solo aplica a la consola. Lo que sale por HTTP va en UTF-8 y no tiene esta
restricción — los acentos y los kanji se muestran enteros en la pantalla.
"""

import unicodedata


def ascii_seguro(texto):
    """El texto en ASCII, conservando lo que se pueda leer.

    Se descompone y se sacan los diacríticos, así "Tankōbon" queda "Tankobon" y
    "Reprogramación" queda "Reprogramacion": legibles. Lo que no tiene
    equivalente —un kanji— se reemplaza por `?`, que es peor que el original
    pero infinitamente mejor que perder el resto de la salida.
    """
    if not texto:
        return ""
    sin_tildes = "".join(
        caracter
        for caracter in unicodedata.normalize("NFKD", str(texto))
        if not unicodedata.combining(caracter)
    )
    return sin_tildes.encode("ascii", errors="replace").decode("ascii")
