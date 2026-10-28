#!/usr/bin/env python3
"""
Genera `docs/pruebas/CATALOGO.md`: qué pruebas hay, qué hace cada una y si pasa.

    python scripts/generar_catalogo.py                     # corre la suite y escribe el catálogo
    python scripts/generar_catalogo.py --junit informe.xml  # usa una corrida ya hecha

Qué hace cada prueba sale de su docstring (la primera oración) o, si no tiene, de su nombre, que
en este repositorio ya describe el efecto esperado. Si pasa sale de una corrida real de pytest,
leída de su informe JUnit: el catálogo nunca dice «pasa» de memoria.

También lista los scripts de `scripts/demo/`, con lo que hace cada uno según su docstring. Qué
caso de prueba ejecuta cada archivo, de la suite o de la demo, sale de la línea «Se ejecuta con»
de `docs/pruebas/CASOS_DE_PRUEBA.md`. Un caso que cita un archivo que no existe se informa.

Se lee el árbol sintáctico y no el texto, por el mismo motivo que en `generar_cobertura.py`: una
cadena que mencione `def test_…` dentro de un docstring no es una prueba.

La salida por consola va en ASCII: la consola de Windows corre en cp1252 y un acento la hace
reventar con `UnicodeEncodeError`.
"""

from __future__ import annotations

import argparse
import ast
import re
import subprocess  # nosec B404 - pytest con argumentos fijos
import sys
import tempfile
import xml.etree.ElementTree as ET  # nosec B405 - el informe lo escribe pytest en esta corrida
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import date
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent

NOMBRE_DE_APP = {
    "accounts": "Cuentas y acceso",
    "catalog": "Catálogo",
    "core": "Núcleo",
    "suppliers": "Proveedores",
    "tienda": "Tienda",
}

RE_CASO = re.compile(r"^### (CP-\d+) ", re.M)
RE_ARCHIVO_CITADO = re.compile(r"(scripts/demo/\w+\.py|apps/\w+/tests/test_\w+\.py)")

PASA, FALLA, OMITIDA, SIN_CORRER = "Pasa", "**Falla**", "Omitida", "No corrió"

CABECERA = """> **Tipo: Fotografía.** Tomada el {fecha} de una corrida real de la suite.
> **Generado por `scripts/generar_catalogo.py`.** No lo edites: la próxima corrida lo pisa.

# Catálogo de pruebas

Qué pruebas hay, qué hace cada una y si pasa. Cómo se escriben está en
[`ESPECIFICACION.md`](ESPECIFICACION.md); qué contratos cubren, en [`COBERTURA.md`](COBERTURA.md);
qué casos de prueba verifican, en [`CASOS_DE_PRUEBA.md`](CASOS_DE_PRUEBA.md).
"""


@dataclass
class Prueba:
    nombre: str
    que_hace: str
    casos: int
    resultado: str = SIN_CORRER


# --------------------------------------------------------------------------- #
# Las pruebas, del código
# --------------------------------------------------------------------------- #


def primera_oracion(texto: str | None) -> str:
    if not texto:
        return ""
    parrafo = " ".join(texto.strip().split("\n\n")[0].split())
    corte = parrafo.find(". ")
    return parrafo if corte == -1 else parrafo[: corte + 1]


def de_nombre(nombre: str) -> str:
    """`test_la_baja_es_logica` → «La baja es logica»."""
    texto = nombre.removeprefix("test_").replace("_", " ")
    return texto[:1].upper() + texto[1:]


def casos_de(funcion: ast.FunctionDef) -> int:
    """Cuántos casos genera `parametrize`, si los valores están escritos como lista literal."""
    total = 1
    for deco in funcion.decorator_list:
        if not (isinstance(deco, ast.Call) and getattr(deco.func, "attr", "") == "parametrize"):
            continue
        if len(deco.args) > 1 and isinstance(deco.args[1], (ast.List, ast.Tuple)):
            total *= max(len(deco.args[1].elts), 1)
    return total


def leer_archivo(ruta: Path) -> tuple[str, list[Prueba]]:
    arbol = ast.parse(ruta.read_text(encoding="utf-8"))
    pruebas = []
    for nodo in arbol.body:
        funciones = [nodo]
        if isinstance(nodo, ast.ClassDef) and nodo.name.startswith("Test"):
            funciones = nodo.body
        for f in funciones:
            if isinstance(f, (ast.FunctionDef, ast.AsyncFunctionDef)) and f.name.startswith(
                "test_"
            ):
                que_hace = primera_oracion(ast.get_docstring(f)) or de_nombre(f.name)
                pruebas.append(Prueba(f.name, que_hace.replace("|", "\\|"), casos_de(f)))
    return primera_oracion(ast.get_docstring(arbol)), pruebas


def leer_scripts(carpeta: Path) -> list[tuple[str, str]]:
    """`(nombre, qué hace)` de cada script de la demo, del primer párrafo de su docstring."""
    scripts = []
    for ruta in sorted(carpeta.glob("*.py")):
        doc = ast.get_docstring(ast.parse(ruta.read_text(encoding="utf-8"))) or ""
        primero = " ".join(doc.strip().split("\n\n")[0].split())
        scripts.append((ruta.name, primero.replace("|", "\\|")))
    return scripts


def leer_casos(ruta: Path) -> dict[str, list[str]]:
    """`{archivo relativo: [CP-NN, …]}`, de la línea «Se ejecuta con» de cada caso de prueba."""
    por_archivo: dict[str, list[str]] = defaultdict(list)
    if not ruta.is_file():
        return por_archivo
    texto = ruta.read_text(encoding="utf-8")
    marcas = list(RE_CASO.finditer(texto))
    for i, marca in enumerate(marcas):
        fin = marcas[i + 1].start() if i + 1 < len(marcas) else len(texto)
        bloque = texto[marca.end() : fin]
        inicio = bloque.find("**Se ejecuta con:**")
        if inicio == -1:
            continue
        linea = bloque[inicio:].split("\n- **")[0]
        for archivo in dict.fromkeys(RE_ARCHIVO_CITADO.findall(linea)):
            por_archivo[archivo].append(marca.group(1))
    return por_archivo


# --------------------------------------------------------------------------- #
# Los resultados, de una corrida
# --------------------------------------------------------------------------- #


def correr_suite(informe: Path) -> None:
    orden = [sys.executable, "-m", "pytest", "-q", "-n", "auto", "--no-cov"]
    orden += ["-p", "no:randomly", f"--junitxml={informe}"]
    subprocess.call(orden, cwd=RAIZ)  # nosec B603 - pytest con argumentos fijos


def leer_resultados(informe: Path) -> tuple[dict[tuple[str, str], str], float]:
    """`{(archivo relativo, función): resultado}` y la duración de la corrida.

    Una función parametrizada tiene un `testcase` por caso; falla si falla cualquiera.
    """
    raiz = ET.parse(informe).getroot()  # nosec B314 - archivo propio, recién escrito por pytest
    suites = [raiz] if raiz.tag == "testsuite" else list(raiz)
    duracion = sum(float(s.get("time", 0)) for s in suites)
    resultados: dict[tuple[str, str], str] = {}
    for caso in raiz.iter("testcase"):
        archivo = caso.get("classname", "").split(".")
        # `apps.accounts.tests.test_login` o, si está en una clase, `….test_login.TestAlgo`
        while archivo and not archivo[-1].startswith("test_"):
            archivo.pop()
        clave = ("/".join(archivo) + ".py", caso.get("name", "").split("[")[0])
        if caso.find("failure") is not None or caso.find("error") is not None:
            estado = FALLA
        elif caso.find("skipped") is not None:
            estado = OMITIDA
        else:
            estado = PASA
        previo = resultados.get(clave)
        if previo != FALLA and not (previo == PASA and estado == OMITIDA):
            resultados[clave] = estado
    return resultados, duracion


# --------------------------------------------------------------------------- #
# El documento
# --------------------------------------------------------------------------- #


def armar(archivos, resultados, duracion, casos, scripts) -> tuple[str, Counter]:
    cuenta: Counter = Counter()
    cuerpo: list[str] = []
    app_actual = None
    for ruta, cubre, pruebas in archivos:
        app = ruta.parts[-3]
        if app != app_actual:
            app_actual = app
            cuerpo += ["---", "", f"## {NOMBRE_DE_APP.get(app, app)} — `apps/{app}`", ""]
        rel = ruta.relative_to(RAIZ).as_posix()
        cuerpo += [f"### `{ruta.name}`", ""]
        if cubre:
            cuerpo += [cubre.replace("|", "\\|"), ""]
        if casos.get(rel):
            cuerpo += [f"**Casos de prueba que ejecuta:** {', '.join(casos[rel])}.", ""]
        cuerpo += ["| Prueba | Qué hace | Casos | Resultado |", "| --- | --- | ---: | --- |"]
        for p in pruebas:
            p.resultado = resultados.get((rel, p.nombre), SIN_CORRER)
            cuenta[p.resultado] += 1
            cuenta["casos"] += p.casos
            cuerpo.append(f"| `{p.nombre}` | {p.que_hace} | {p.casos} | {p.resultado} |")
        cuerpo.append("")

    cuerpo += [
        "---",
        "",
        "## Scripts de `scripts/demo/`",
        "",
        "Las pruebas de resistencia que no entran en la suite. Corren sobre la base de la "
        "demostración; cómo se preparan está en [`CASOS_DE_PRUEBA.md`](CASOS_DE_PRUEBA.md).",
        "",
        "| Script | Qué hace | Casos de prueba |",
        "| --- | --- | --- |",
    ]
    for nombre, que_hace in scripts:
        propios = ", ".join(casos.get(f"scripts/demo/{nombre}", [])) or "—"
        cuerpo.append(f"| `{nombre}` | {que_hace} | {propios} |")
    cuerpo.append("")

    existentes = {r.relative_to(RAIZ).as_posix() for r, _, _ in archivos}
    existentes |= {f"scripts/demo/{nombre}" for nombre, _ in scripts}
    perdidos = sorted(a for a in casos if a not in existentes)
    cuenta["perdidos"] = len(perdidos)

    total = sum(len(p) for _, _, p in archivos)
    resumen = [
        "## Resumen",
        "",
        "| | |",
        "| --- | ---: |",
        f"| Archivos de prueba | {len(archivos)} |",
        f"| Funciones de prueba | {total} |",
        f"| Casos, contando cada valor de `parametrize` | {cuenta['casos']} |",
        f"| Pasan | {cuenta[PASA]} |",
        f"| Fallan | {cuenta[FALLA]} |",
        f"| Omitidas | {cuenta[OMITIDA]} |",
        f"| No corrieron | {cuenta[SIN_CORRER]} |",
        f"| Duración de la corrida | {duracion:.0f} s |",
        f"| Scripts de resistencia en `scripts/demo/` | {len(scripts)} |",
        "",
    ]
    if perdidos:
        resumen += ["**Casos de prueba que citan un archivo que no existe:**", ""]
        resumen += [f"- `{a}` ({', '.join(casos[a])})" for a in perdidos]
        resumen.append("")
    if cuenta[FALLA]:
        resumen += ["**Fallan:**", ""]
        for ruta, _, pruebas in archivos:
            for p in pruebas:
                if p.resultado == FALLA:
                    resumen.append(f"- `{ruta.relative_to(RAIZ).as_posix()}::{p.nombre}`")
        resumen.append("")
    documento = [CABECERA.format(fecha=date.today().isoformat()), *resumen, *cuerpo]
    return "\n".join(documento), cuenta


def main() -> int:
    p = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    p.add_argument("--junit", type=Path, help="informe JUnit de una corrida ya hecha")
    p.add_argument("--apps", type=Path, default=RAIZ / "apps")
    p.add_argument("--demo", type=Path, default=RAIZ / "scripts" / "demo")
    p.add_argument("--casos", type=Path, default=RAIZ / "docs" / "pruebas" / "CASOS_DE_PRUEBA.md")
    p.add_argument("--salida", type=Path, default=RAIZ / "docs" / "pruebas" / "CATALOGO.md")
    args = p.parse_args()

    archivos = []
    for ruta in sorted(args.apps.glob("*/tests/test_*.py")):
        cubre, pruebas = leer_archivo(ruta)
        if pruebas:
            archivos.append((ruta, cubre, pruebas))

    if args.junit:
        informe = args.junit
    else:
        informe = Path(tempfile.mkdtemp()) / "junit.xml"
        print("Corriendo la suite...")
        correr_suite(informe)
    if not informe.is_file():
        print(f"error: no hay informe de la corrida en {informe}", file=sys.stderr)
        return 1

    resultados, duracion = leer_resultados(informe)
    casos = leer_casos(args.casos)
    documento, cuenta = armar(archivos, resultados, duracion, casos, leer_scripts(args.demo))
    args.salida.write_text(documento.rstrip() + "\n", encoding="utf-8")

    print(f"Escrito    : {args.salida.relative_to(RAIZ)}")
    print(f"Pasan      : {cuenta[PASA]}")
    print(f"Fallan     : {cuenta[FALLA]}")
    print(f"Omitidas   : {cuenta[OMITIDA]}")
    print(f"No corrieron: {cuenta[SIN_CORRER]}")
    if cuenta["perdidos"]:
        print(f"AVISO: {cuenta['perdidos']} archivo(s) citado(s) en los casos que no existen.")
    return 1 if cuenta[FALLA] or cuenta[SIN_CORRER] or cuenta["perdidos"] else 0


if __name__ == "__main__":
    sys.exit(main())
