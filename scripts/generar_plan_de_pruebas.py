"""Rellena las tablas medidas del plan de pruebas leyendo el codigo.

Se genera y no se escribe a mano por un motivo practico: una tabla de
trazabilidad copiada queda desactualizada en la primera tanda, y una que dice que
algo esta probado cuando ya no lo esta es peor que no tener ninguna.

El script **no toca la prosa**. Busca las marcas `<!-- TABLA:X -->` y reemplaza
solo el bloque que va detras de cada una, hasta el proximo titulo o la proxima
marca. Lo que se escribe a mano se queda; lo que se mide, se mide.

    pytest                                 # deja .coverage al dia
    python scripts\\generar_plan_de_pruebas.py

La salida va en ASCII: la consola de Windows corre en cp1252 y un acento la hace
reventar con `UnicodeEncodeError`. El documento que escribe si lleva acentos,
porque sale por un archivo UTF-8 y no por la consola.
"""

import ast
import io
import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
DOCUMENTO = RAIZ / "docs" / "pruebas" / "plan-de-pruebas.md"
TESTS = RAIZ / "apps"

# Nombre legible de cada app, para el titulo de su tabla.
APPS = {
    "core": "Nucleo, integraciones y configuracion",
    "accounts": "Usuarios, autenticacion y roles",
    "catalog": "Catalogo, productos y borradores",
    "suppliers": "Proveedores y pipeline de novedades",
}


def _titulo_y_cus(ruta):
    """Del docstring del archivo: su primera linea y los CU que menciona."""
    arbol = ast.parse(io.open(ruta, encoding="utf-8").read())
    doc = (ast.get_docstring(arbol) or "").strip()
    primera = doc.split("\n")[0].strip() if doc else ""
    # El titulo suele ser "CU-08 - Registrar Alta de ...": el codigo va en su
    # propia columna, asi que se le quita del texto.
    titulo = re.sub(r"^CU-\d+\s*[—-]\s*", "", primera).rstrip(".")
    funciones = sum(
        1
        for n in ast.walk(arbol)
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name.startswith("test_")
    )
    cus = sorted(set(re.findall(r"CU-\d+", doc)), key=lambda c: int(c[3:]))
    return titulo, funciones, cus


def tabla_trazabilidad():
    por_app = {}
    for ruta in sorted(TESTS.glob("*/tests/test_*.py")):
        por_app.setdefault(ruta.parts[-3], []).append(ruta)

    lineas = []
    sin_titulo = []
    total = 0

    for app in sorted(por_app, key=lambda a: list(APPS).index(a) if a in APPS else 99):
        filas = []
        subtotal = 0
        for ruta in por_app[app]:
            titulo, funciones, cus = _titulo_y_cus(ruta)
            if not titulo:
                sin_titulo.append(f"apps/{app}/tests/{ruta.name}")
                titulo = "_(sin docstring de modulo)_"
            filas.append(f"| `{ruta.name}` | {', '.join(cus) or '--'} | {titulo} | {funciones} |")
            subtotal += funciones
        total += subtotal
        lineas.append(f"\n#### `apps/{app}` -- {APPS.get(app, app)}")
        lineas.append(f"\n{len(por_app[app])} archivos, {subtotal} funciones de prueba.\n")
        lineas.append("| Archivo | CU | Que cubre | Funciones |")
        lineas.append("|---|---|---|---:|")
        lineas.extend(filas)

    archivos = sum(len(v) for v in por_app.values())
    lineas.append(f"\n**Total: {total} funciones de prueba en {archivos} archivos.**")
    lineas.append(
        "\n> Las funciones no son los casos ejecutados: `pytest` reporta mas, "
        "porque una funcion con `@pytest.mark.parametrize` corre una vez por "
        "juego de datos."
    )
    return "\n".join(lineas), sin_titulo


def tabla_cobertura():
    """Lee `.coverage` con la API de coverage, que es la fuente de verdad."""
    try:
        from coverage import Coverage
    except ImportError:  # pragma: no cover - solo si falta la dependencia
        return None

    datos = Coverage(data_file=str(RAIZ / ".coverage"))
    datos.load()
    medida = datos.get_data()
    if not medida.measured_files():
        return None

    por_app = {}
    for archivo in medida.measured_files():
        partes = Path(archivo).parts
        if "apps" not in partes:
            continue
        app = partes[partes.index("apps") + 1]
        analisis = datos._analyze(archivo)
        acumulado = por_app.setdefault(app, [0, 0])
        acumulado[0] += len(analisis.statements)
        acumulado[1] += len(analisis.missing)

    lineas = ["| App | Sentencias | Sin cubrir | Cobertura |", "|---|---:|---:|---:|"]
    totales = [0, 0]
    for app in sorted(por_app, key=lambda a: list(APPS).index(a) if a in APPS else 99):
        sentencias, sin_cubrir = por_app[app]
        totales[0] += sentencias
        totales[1] += sin_cubrir
        pct = round(100 * (sentencias - sin_cubrir) / sentencias)
        lineas.append(f"| `apps/{app}` | {sentencias} | {sin_cubrir} | {pct} % |")
    pct = round(100 * (totales[0] - totales[1]) / totales[0])
    lineas.append(f"| **Total** | **{totales[0]}** | **{totales[1]}** | **{pct} %** |")
    return "\n".join(lineas)


def reemplazar(texto, marca, contenido):
    """Cambia lo que sigue a una marca, sin tocar lo que la rodea.

    El bloque termina en el proximo titulo (`---` o una linea que empiece con
    `#`) o en la proxima marca, lo que venga primero.
    """
    patron = re.compile(
        rf"(<!-- TABLA:{marca} -->\n).*?(?=\n(?:#|---|<!-- TABLA:))",
        re.DOTALL,
    )
    if not patron.search(texto):
        raise SystemExit(f"No se encontro la marca TABLA:{marca} en el documento.")
    return patron.sub(lambda m: m.group(1) + contenido + "\n", texto)


def main():
    if not DOCUMENTO.exists():
        raise SystemExit(f"No existe {DOCUMENTO}")

    texto = io.open(DOCUMENTO, encoding="utf-8").read()

    trazabilidad, sin_titulo = tabla_trazabilidad()
    texto = reemplazar(texto, "TRAZABILIDAD", trazabilidad)

    cobertura = tabla_cobertura()
    if cobertura is None:
        print("AVISO: no hay datos de cobertura. Corra `pytest` y repita.")
        print("       La tabla de cobertura quedo como estaba.")
    else:
        texto = reemplazar(texto, "COBERTURA", cobertura)

    io.open(DOCUMENTO, "w", encoding="utf-8", newline="\n").write(texto)
    print(f"Actualizado {DOCUMENTO.relative_to(RAIZ)}")

    if sin_titulo:
        print("\nArchivos de test sin docstring de modulo (quedan sin fila util):")
        for ruta in sin_titulo:
            print(f"  {ruta}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
