"""El generador de contenido de muestra para el banco de pruebas.

**Lo que de verdad prueba este archivo** es que dos implementaciones del dígito
de control del ISBN, escritas por vías distintas, coinciden. `isbn.py` recorre
con pesos alternados; `muestras.py` suma el total y le agrega dos veces los
impares. Que coincidan sobre cientos de valores es evidencia; si el generador
usara la misma función, un test así solo probaría que coincide consigo misma —
pasaría igual con las ponderaciones al revés.
"""

from datetime import date

import pytest

from apps.catalog import isbn as isbn_util
from apps.suppliers import extraccion, muestras

# No toca la base: son cadenas entrando y saliendo.

CUANTOS = 500


# ---------------------------------------------------------------------------
# El cruce entre las dos implementaciones
# ---------------------------------------------------------------------------


def test_todo_isbn_generado_lo_acepta_la_verificacion():
    """Quinientos valores, dos implementaciones independientes. Una diferencia
    en las ponderaciones aparecería acá aunque los cuatro ISBN reales de
    `test_isbn.py` sigan pasando."""
    invalidos = [
        numero
        for numero in range(CUANTOS)
        if not isbn_util.es_valido(muestras.isbn_de_prueba(numero))
    ]

    assert invalidos == []


def test_todo_isbn_roto_lo_rechaza_la_verificacion():
    """La otra mitad: que el generador de rotos genere rotos de verdad. Sin
    esto, la demostración podría estar mostrando un ISBN válido y diciendo que
    lo detectó."""
    aceptados = [
        numero for numero in range(CUANTOS) if isbn_util.es_valido(muestras.isbn_roto(numero))
    ]

    assert aceptados == []


def test_el_roto_difiere_del_valido_en_un_solo_digito():
    """Es el error que se comete al transcribir, y el que la verificación tiene
    que atrapar. Un número completamente distinto no probaría lo mismo."""
    valido = muestras.isbn_de_prueba(42)
    roto = muestras.isbn_roto(42)

    assert len(valido) == len(roto)
    assert sum(1 for a, b in zip(valido, roto, strict=True) if a != b) == 1


def test_numeros_distintos_dan_isbn_distintos():
    """Si se repitieran, una muestra con varios productos chocaría contra la
    restricción de unicidad al confirmarlos."""
    generados = {muestras.isbn_de_prueba(numero) for numero in range(CUANTOS)}

    assert len(generados) == CUANTOS


def test_los_isbn_empiezan_como_uno_argentino():
    """978 de Bookland más 987 de Argentina: que la muestra arranque bien hace
    que se parezca a lo que llega de verdad."""
    assert muestras.isbn_de_prueba(1).startswith("978987")


# ---------------------------------------------------------------------------
# La muestra armada
# ---------------------------------------------------------------------------


def test_la_muestra_tiene_la_forma_de_un_correo_extraido():
    muestra = muestras.armar(semilla=1)
    lineas = muestra.contenido.splitlines()
    filas = [linea for linea in lineas if linea.startswith("|")]

    # El encabezado más los tres productos.
    assert len(filas) == 4
    # Y la prosa de alrededor, que es de donde sale el período del envío.
    assert f"Novedades de {muestra.periodo_texto}" in muestra.contenido
    assert "Los pedidos se reciben" in muestra.contenido


def test_trae_las_trampas_de_un_correo_real():
    """Probar contra un correo ideal no prueba nada: el logo no es un producto y
    la fila de encabezado tampoco."""
    muestra = muestras.armar(semilla=1)

    logo = next(linea for linea in muestra.contenido.splitlines() if "logo@" in linea)
    assert not logo.startswith("|")
    assert "| ISBN | Tapa |" in muestra.contenido


def test_exactamente_un_producto_trae_el_isbn_roto():
    """Ni ninguno —no se vería la validación— ni todos, que haría parecer que el
    modelo lee mal siempre."""
    muestra = muestras.armar(cantidad=5, semilla=2)
    isbns = [
        fila.split("|")[1].strip()
        for fila in muestra.contenido.splitlines()
        if fila.startswith("| 978")
    ]

    rotos = [valor for valor in isbns if not isbn_util.es_valido(valor)]
    assert rotos == [muestra.isbn_roto]


def test_cual_sale_roto_no_es_siempre_el_mismo():
    """Si fuera siempre el último, alcanzaría con mirar la última fila para
    saber qué va a pasar antes de correr la prueba."""
    posiciones = set()
    for semilla in range(30):
        muestra = muestras.armar(cantidad=4, semilla=semilla)
        filas = [f for f in muestra.contenido.splitlines() if f.startswith("| 978")]
        posiciones.add(next(i for i, f in enumerate(filas) if muestra.isbn_roto in f))

    assert len(posiciones) > 1


def test_declara_los_identificadores_de_portada_que_trae():
    """Sin ellos, la comprobación de portada inexistente no tendría contra qué
    comparar y la demostración mostraría una validación que no valida."""
    muestra = muestras.armar(semilla=1)

    marcados = {
        linea.split("[imagen:")[1].split("]")[0]
        for linea in muestra.contenido.splitlines()
        if "[imagen:" in linea
    }
    assert marcados == set(muestra.cids)


def test_la_misma_semilla_da_la_misma_muestra():
    """Un test que necesite una muestra conocida tiene que poder pedirla."""
    assert muestras.armar(semilla=9).contenido == muestras.armar(semilla=9).contenido


def test_sin_semilla_las_muestras_difieren():
    assert muestras.armar().contenido != muestras.armar().contenido


@pytest.mark.parametrize("cantidad", [1, 3, 8])
def test_se_puede_pedir_la_cantidad_de_productos(cantidad):
    muestra = muestras.armar(cantidad=cantidad, semilla=1)
    filas = [f for f in muestra.contenido.splitlines() if f.startswith("| 978")]

    assert len(filas) == cantidad


# ---------------------------------------------------------------------------
# El período
# ---------------------------------------------------------------------------


def test_el_periodo_anunciado_es_futuro():
    """Con una fecha ya pasada, todos los borradores nacen Activos y el banco de
    pruebas nunca ejercita la rama de Pre-venta — que es la que tiene
    consecuencias: un producto que no llegó figurando disponible no da ningún
    síntoma hasta que alguien lo compra."""
    for semilla in range(30):
        muestra = muestras.armar(semilla=semilla)
        assert muestra.periodo > date.today()


def test_el_periodo_se_declara_y_coincide_con_el_texto():
    """La muestra dice qué debería salir de ella, para que verificarlo no
    obligue a volver a interpretar el texto acá — eso compararía la muestra
    consigo misma."""
    muestra = muestras.armar(semilla=3)

    assert extraccion.interpretar_fecha(muestra.periodo_texto) == muestra.periodo


def test_el_periodo_varia_entre_muestras():
    """Mismo motivo que los títulos y los ISBN: un valor fijo deja la duda de si
    el modelo lo lee o lo reconoce de verlo siempre igual."""
    periodos = {muestras.armar(semilla=semilla).periodo for semilla in range(30)}

    assert len(periodos) > 1


def test_el_vencimiento_de_pedidos_es_un_señuelo_sin_año():
    """Es una segunda fecha en la misma prosa, y el modelo tiene que copiar el
    período y no el vencimiento. Va sin año a propósito: si el modelo la
    eligiera igual, el intérprete la descarta y el reparo lo dice en pantalla en
    vez de quedar en silencio."""
    muestra = muestras.armar(semilla=5)

    vencimiento = next(
        linea for linea in muestra.contenido.splitlines() if "Los pedidos se reciben" in linea
    )
    assert extraccion.interpretar_fecha(vencimiento) is None
