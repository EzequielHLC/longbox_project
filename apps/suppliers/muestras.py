"""Contenido de muestra para el banco de pruebas del modelo.

**Esto fabrica datos de mentira. No es un módulo de ISBN.** El nombre importa:
`apps/catalog/isbn.py` solo *verifica*, nunca inventa, y esa línea no se cruza.
Un generador de ISBN al alcance del código de catálogo es un arma cargada —
tarde o temprano alguien lo usa para completar un ISBN que falta en un borrador,
y un ISBN inventado es matemáticamente válido y no identifica nada. Acá los
números existen para dárselos al modelo y ver qué hace con ellos, no para
guardarlos.

**El dígito de control se calcula por una vía distinta a la de `isbn.py`.** No es
capricho: si lo calculara con la misma función, un test que genere un ISBN y
después le pregunte a `es_valido` si está bien estaría probando que la función
coincide consigo misma —pasaría igual con las ponderaciones al revés—. Con dos
formulaciones escritas distinto, que coincidan sobre cientos de valores sí dice
algo. La equivalencia es aritmética: `1×pares + 3×impares` es lo mismo que
`total + 2×impares`.

**Por qué la muestra se genera en vez de estar fija.** Mostrar siempre los mismos
tres tomos deja la duda de si el modelo los está reconociendo en vez de leerlos.
Con una muestra distinta en cada carga, lo que se ve es que lee.
"""

import random
from dataclasses import dataclass

# Títulos y tamaños plausibles del rubro. No son los de ningún catálogo real:
# son para que la muestra se lea como un correo de verdad y no como `foo bar`.
TITULOS = [
    "Berserk Deluxe",
    "Blue Period",
    "Vinland Saga",
    "Chainsaw Man",
    "Vagabond",
    "Monster",
    "Dorohedoro",
    "Oyasumi Punpun",
]
FORMATOS = ["Tapa dura", "B6", "Tankōbon", "A5", "Rústica"]

# Prefijo de un ISBN-13 argentino: 978 (Bookland) + 987 (Argentina). Que la
# muestra empiece bien hace que se parezca a lo que llega de verdad.
PREFIJO = "978987"


@dataclass(frozen=True)
class Muestra:
    """Un contenido de prueba y lo que hace falta para evaluarlo.

    `cids` son los identificadores de portada que la muestra "trae": sin
    declararlos, la comprobación de portada inexistente no tendría contra qué
    comparar y la demostración mostraría una validación que no valida.

    `isbn_roto` es el que se corrompió a propósito, para poder afirmar en un test
    que el sistema efectivamente lo detecta.
    """

    contenido: str
    cids: frozenset
    isbn_roto: str


def digito_de_control(cuerpo):
    """El dígito que cierra un ISBN-13, por la vía de la suma total.

    `1×pares + 3×impares` es lo mismo que `total + 2×impares`, y se calcula así
    a propósito: es la formulación que **no** comparte código con la de
    `isbn.py`, que es lo que vuelve significativo cruzarlas.
    """
    digitos = [int(caracter) for caracter in cuerpo]
    impares = sum(digitos[1::2])
    return str((10 - (sum(digitos) + 2 * impares) % 10) % 10)


def isbn_de_prueba(numero):
    """Un ISBN-13 válido y distinto para cada número."""
    cuerpo = f"{PREFIJO}{numero % 1_000_000:06d}"
    return cuerpo + digito_de_control(cuerpo)


def isbn_roto(numero):
    """El mismo, con el dígito de control corrido en uno.

    Un solo dígito de diferencia: es exactamente el error que se comete al
    transcribir, y el que la verificación tiene que atrapar.
    """
    valido = isbn_de_prueba(numero)
    return valido[:-1] + str((int(valido[-1]) + 1) % 10)


def armar(cantidad=3, semilla=None):
    """Arma una muestra como la que produce la extracción de un correo real.

    Trae las trampas puestas, porque probar contra un correo ideal no prueba
    nada: una fila de logo que no es un producto, una fila de encabezado, prosa
    alrededor de la tabla, y **un ISBN con un dígito cambiado**. Ese último es la
    mitad interesante de la demostración — muestra que el sistema le desconfía al
    modelo, no solo que el modelo copia bien.
    """
    azar = random.Random(semilla)  # noqa: S311
    base = azar.randrange(1, 999_000)

    # Cuál sale roto se sortea también: si fuera siempre el último, alcanzaría
    # con mirar la última fila para saber qué va a pasar.
    roto_en = azar.randrange(cantidad)
    titulos = azar.sample(TITULOS, k=min(cantidad, len(TITULOS)))

    filas, cids, isbn_del_roto = [], {"logo@editorial.test"}, ""
    for posicion in range(cantidad):
        isbn = (
            isbn_roto(base + posicion) if posicion == roto_en else isbn_de_prueba(base + posicion)
        )
        if posicion == roto_en:
            isbn_del_roto = isbn

        cid = f"tapa{posicion + 1:03d}@editorial.test"
        cids.add(cid)
        filas.append(
            f"| {isbn} | [imagen:{cid}] | {titulos[posicion % len(titulos)]} | "
            f"{azar.randrange(1, 30)} | {azar.choice(FORMATOS)} | "
            f"${azar.randrange(8, 40) * 500} |"
        )

    contenido = "\n".join(
        [
            "[imagen:logo@editorial.test]",
            "Novedades de marzo 2026",
            "| ISBN | Tapa | Título | Vol. | Formato | PVP |",
            *filas,
            "Los pedidos se reciben hasta el 20 de marzo.",
        ]
    )
    return Muestra(contenido=contenido, cids=frozenset(cids), isbn_roto=isbn_del_roto)
