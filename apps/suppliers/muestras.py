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
from datetime import date

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

# Para escribir el período como lo escribe un proveedor. Se arma acá y no se
# saca de `locale`: el idioma de los meses no puede depender de cómo esté
# configurada la máquina en la que corre.
MESES = [
    "enero",
    "febrero",
    "marzo",
    "abril",
    "mayo",
    "junio",
    "julio",
    "agosto",
    "septiembre",
    "octubre",
    "noviembre",
    "diciembre",
]

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
    # El período que la muestra anuncia, y la fecha que debería salir de él. Se
    # exponen para poder afirmar en un test que el modelo lo encontró: sin esto,
    # verificar el período obligaría a volver a interpretar el texto acá, con lo
    # cual el test compararía la muestra consigo misma.
    periodo_texto: str = ""
    periodo: date | None = None


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
    azar = random.Random(semilla)  # nosec B311 - datos de demostración, no criptografía
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

    periodo_texto, periodo, mes = _periodo(azar)
    contenido = "\n".join(
        [
            "[imagen:logo@editorial.test]",
            f"Novedades de {periodo_texto}",
            "| ISBN | Tapa | Título | Vol. | Formato | PVP |",
            *filas,
            f"Los pedidos se reciben hasta el 20 de {mes}.",
        ]
    )
    return Muestra(
        contenido=contenido,
        cids=frozenset(cids),
        isbn_roto=isbn_del_roto,
        periodo_texto=periodo_texto,
        periodo=periodo,
    )


def _periodo(azar):
    """Un período **futuro**, escrito como lo escribe un proveedor.

    Dos decisiones que no son de estilo:

    **Futuro, y no fijo en el pasado.** La muestra anunciaba "marzo 2026" escrito
    a mano, y eso rompía la demostración de dos maneras. Con una fecha ya pasada
    todos los borradores nacen Activos, así que la pantalla nunca ejercitaba la
    rama de Pre-venta — que es la que tiene consecuencias: un producto que no
    llegó figurando disponible no da ningún síntoma hasta que alguien lo compra.
    Anunciando un mes que todavía no llegó, el banco de pruebas prueba esa rama,
    que es de la que hay que desconfiar.

    **Y varía, como varía todo lo demás de la muestra.** Mismo motivo por el que
    los títulos y los ISBN se sortean: un valor fijo deja la duda de si el modelo
    lo está leyendo o lo reconoce de haberlo visto siempre igual.

    La línea de "los pedidos se reciben hasta el 20 de …" queda como **señuelo**:
    es una segunda fecha en la misma prosa, y el modelo tiene que copiar el
    período y no el vencimiento. Va sin año a propósito, así que aunque la
    eligiera, el intérprete la descartaría —un mes sin año no se adivina— y el
    reparo lo diría en la pantalla en vez de quedar en silencio.
    """
    hoy = date.today()
    # Entre uno y seis meses adelante: el horizonte con el que una editorial
    # anuncia de verdad.
    adelanto = azar.randrange(1, 7)
    corrido = hoy.month - 1 + adelanto
    anio, indice = hoy.year + corrido // 12, corrido % 12
    return f"{MESES[indice]} {anio}", date(anio, indice + 1, 1), MESES[indice]
