"""Normalización y verificación del ISBN.

Vive aparte y sin Django de por medio, igual que `precios.py`, para poder
probarlo con una tabla de casos sin levantar la base.

**Qué es y por qué importa acá.** El ISBN es el único identificador globalmente
único de una edición: distingue el B6 del Deluxe del mismo tomo, cosa que la
tupla título + volumen + tipo + formato + editorial resuelve con esfuerzo y sin
garantías. Los correos de novedades de los proveedores lo traen siempre, así que
es el criterio de duplicados que el pipeline automatizado va a usar primero.

**Y trae su propio dígito verificador**, que es lo que lo hace confiable: un
dígito mal transcripto —por un tipeo, o por un modelo de lenguaje leyendo una
tabla— se detecta con aritmética, sin consultar ningún servicio externo. Eso
importa porque un ISBN con un error no falla ruidosamente: pasa a identificar un
producto que no existe, y el chequeo de duplicados deja de encontrar el que sí.

Nada de esto contradice a RF-05, que excluye "integración con catálogos externos,
bases de datos de ISBN": acá no se consulta nada, el número viene en el correo
del proveedor y la verificación es una suma.
"""

# Los dos largos válidos. El ISBN-10 quedó obsoleto en 2007 pero sigue impreso
# en catálogos y en material de fondo, así que se acepta.
LARGO_ISBN_10 = 10
LARGO_ISBN_13 = 13

MENSAJE_LARGO = "Un ISBN tiene 10 o 13 dígitos."
MENSAJE_CARACTERES = "El ISBN solo puede tener dígitos, y una X final en los de 10."
MENSAJE_VERIFICADOR = (
    "El ISBN no es válido: su dígito verificador no coincide. Suele ser un dígito mal copiado."
)


def normalizar(valor):
    """Deja el ISBN en la forma en que se guarda: sin guiones ni espacios.

    Se normaliza al **guardar** y no solo al comparar. Guardarlo tal como vino
    haría que "978-987-827-158-3" y "9789878271583" fueran dos productos
    distintos para cualquier consulta que no se acuerde de normalizar — y la
    restricción de unicidad de la base es una de esas.

    La X final del ISBN-10 va en mayúscula por la misma razón: es un dígito, no
    una letra, y "х" minúscula rompería la comparación exacta.
    """
    if not valor:
        return ""
    return "".join(valor.split()).replace("-", "").replace("–", "").upper()


def _error(isbn):
    """El motivo por el que el ISBN no sirve, o `None` si está bien."""
    if len(isbn) not in (LARGO_ISBN_10, LARGO_ISBN_13):
        return MENSAJE_LARGO

    cuerpo, verificador = isbn[:-1], isbn[-1]
    if not cuerpo.isdigit():
        return MENSAJE_CARACTERES

    if len(isbn) == LARGO_ISBN_13:
        if not verificador.isdigit():
            return MENSAJE_CARACTERES
        return None if _verificador_13(cuerpo) == verificador else MENSAJE_VERIFICADOR

    # En el de 10, el último dígito vale 10 cuando es X.
    if not (verificador.isdigit() or verificador == "X"):
        return MENSAJE_CARACTERES
    return None if _verificador_10(cuerpo) == verificador else MENSAJE_VERIFICADOR


def _verificador_13(cuerpo):
    """Los doce primeros pesan 1 y 3 alternados; el dígito completa a múltiplo de 10."""
    pesos = (1 if posicion % 2 == 0 else 3 for posicion in range(len(cuerpo)))
    suma = sum(int(digito) * peso for digito, peso in zip(cuerpo, pesos, strict=True))
    return str((10 - suma % 10) % 10)


def _verificador_10(cuerpo):
    """Los nueve primeros pesan de 10 a 2; el resto módulo 11 se expresa como X si vale 10."""
    suma = sum(int(digito) * (LARGO_ISBN_10 - posicion) for posicion, digito in enumerate(cuerpo))
    resto = (11 - suma % 11) % 11
    return "X" if resto == 10 else str(resto)


def es_valido(valor):
    """Si el valor, ya normalizado, es un ISBN bien formado."""
    return _error(normalizar(valor)) is None


def motivo_de_rechazo(valor):
    """El texto del error, o `None` si el ISBN está bien. Lo consume el formulario."""
    return _error(normalizar(valor))
