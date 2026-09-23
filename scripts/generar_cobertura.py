#!/usr/bin/env python3
"""
Genera `docs/pruebas/COBERTURA.md`: qué prueba lleva el código de qué contrato.

    python scripts/generar_cobertura.py

**Es la única fuente de «qué contrato cubre qué prueba».** Ningún otro archivo del proyecto
informa esa correspondencia; los que la necesitan enlazan acá.

Se genera y no se escribe a mano por un motivo práctico: una tabla de trazabilidad copiada queda
desactualizada en la primera tanda, y una que dice que algo está probado cuando ya no lo está es
peor que no tener ninguna.

De dónde sale cada mitad
------------------------
    los contratos      `.contexto-ia/contratos/*.md`, que vuelca `generar_contexto.py`
    las pruebas        los nombres de función `test_CO###_...` bajo `apps/*/tests/`

La convención de nombres es lo que hace posible medirlo sin leer código, y está en
`docs/pruebas/ESPECIFICACION.md`, apartado 2: *«prueba de contrato: empieza por el código del
contrato. Con eso, "qué contratos no tienen prueba" es una búsqueda de texto y no una auditoría».*

Qué mide y qué NO mide
----------------------
Mide **que existe una prueba que dice verificar el contrato**. No mide que la verifique entera.

La diferencia no es menor y es la razón por la que este archivo no dice «verificado»: un contrato
con tres postcondiciones y una sola prueba figura acá igual que uno con todas cubiertas. Decidir
si un contrato está verificado exige leer sus postcondiciones al lado de sus pruebas, que es
trabajo de persona; el estado resultante vive en `docs/ESTADO.md`.

Tampoco mide cobertura de líneas. Esa es otra puerta, se mide con `coverage` y su número vive en
`docs/ESTADO.md`. Las dos se pueden cumplir por separado y sólo la de contratos es la que el
documento de análisis promete.

La salida por consola va en ASCII: la consola de Windows corre en cp1252 y un acento la hace
reventar con `UnicodeEncodeError`. El archivo que escribe sí lleva acentos, porque sale por un
archivo UTF-8 y no por la consola.
"""

from __future__ import annotations

import argparse
import ast
import re
import sys
from collections import defaultdict
from datetime import date
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent

RE_CONTRATO_EN_ARCHIVO = re.compile(r"^## (CO-\d{3}) · (.+)$", re.M)
RE_PRUEBA_DE_CONTRATO = re.compile(r"^test_CO(\d{3})_")
RE_MODULO_EN_ARCHIVO = re.compile(r"^# (?:Módulo (\d+) · (.+)|(Contratos transversales))$", re.M)

CABECERA = """> **Tipo: Fotografía.** Tomada el {fecha}, del repositorio y no de memoria.
> **Generado por `scripts/generar_cobertura.py`.** No lo edites: la próxima corrida lo pisa.
> Se reemplaza entero. Si algo está mal acá, anotalo en la bitácora del módulo.

# Cobertura de contratos

Qué prueba lleva el código de qué contrato. **Es la única fuente de esta correspondencia**: los
demás documentos enlazan acá en vez de repetirla.

Sale de cruzar los contratos de `.contexto-ia/contratos/` con los nombres de función
`test_CO###_…` de la suite. La convención que lo hace posible está en
[`ESPECIFICACION.md`](ESPECIFICACION.md), apartado 2.

**Qué mide y qué no.** Mide que existe una prueba que *dice* verificar el contrato. No mide que
lo verifique entero: un contrato con tres postcondiciones y una sola prueba figura acá igual que
uno con todas cubiertas. Decidir si un contrato está verificado exige leer sus postcondiciones al
lado de sus pruebas, y ese juicio vive en [`../ESTADO.md`](../ESTADO.md). La cobertura de líneas
es otra puerta y su número también vive ahí.
"""


# --------------------------------------------------------------------------- #
# Las dos fuentes
# --------------------------------------------------------------------------- #


def leer_contratos(carpeta: Path) -> list[tuple[str, str, str, str]]:
    """`(CO-###, operación, archivo, título del archivo)` de cada contrato volcado."""
    contratos = []
    for ruta in sorted(carpeta.glob("*.md")):
        texto = ruta.read_text(encoding="utf-8")
        m = RE_MODULO_EN_ARCHIVO.search(texto)
        if m and m.group(3):
            titulo = "Transversales"
        elif m:
            titulo = f"{m.group(1)} {m.group(2)}"
        else:
            titulo = ruta.stem
        for codigo, operacion in RE_CONTRATO_EN_ARCHIVO.findall(texto):
            contratos.append((codigo, operacion.strip(), ruta.name, titulo))
    return contratos


def leer_pruebas(raiz_apps: Path) -> dict[str, list[tuple[str, str]]]:
    """`{CO-###: [(nombre de la prueba, archivo), …]}` de toda la suite.

    Se lee el árbol sintáctico y no el texto: una cadena que mencione `test_CO013_` dentro de un
    docstring no es una prueba, y contarla haría figurar como cubierto un contrato que no lo
    está. El nombre de la función es el único dato que la convención promete.
    """
    por_contrato: dict[str, list[tuple[str, str]]] = defaultdict(list)
    for ruta in sorted(raiz_apps.glob("*/tests/test_*.py")):
        arbol = ast.parse(ruta.read_text(encoding="utf-8"))
        rel = ruta.relative_to(RAIZ).as_posix()
        for nodo in ast.walk(arbol):
            if not isinstance(nodo, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            m = RE_PRUEBA_DE_CONTRATO.match(nodo.name)
            if m:
                por_contrato[f"CO-{m.group(1)}"].append((nodo.name, rel))
    return por_contrato


# --------------------------------------------------------------------------- #
# El documento
# --------------------------------------------------------------------------- #


def armar(contratos, pruebas) -> tuple[str, dict[str, int]]:
    con_prueba = [c for c in contratos if pruebas.get(c[0])]
    sin_prueba = [c for c in contratos if not pruebas.get(c[0])]

    partes = [CABECERA.format(fecha=date.today().isoformat()), "---", "", "## Resumen", ""]
    partes += [
        "| | |",
        "| --- | ---: |",
        f"| Contratos especificados | {len(contratos)} |",
        f"| Con al menos una prueba que lleva su código | {len(con_prueba)} |",
        f"| Sin ninguna | {len(sin_prueba)} |",
        f"| Pruebas de contrato en la suite | {sum(len(v) for v in pruebas.values())} |",
        "",
    ]

    # Códigos de prueba que no corresponden a ningún contrato: una prueba nombrada por un
    # contrato inexistente es un error de tipeo que, sin este aviso, se lee como cobertura.
    huerfanos = sorted(set(pruebas) - {c[0] for c in contratos})
    if huerfanos:
        partes += [
            "**Pruebas que nombran un contrato inexistente.** Un tipeo en el código del contrato "
            "produce una prueba que parece cubrir algo y no cubre nada:",
            "",
        ]
        for codigo in huerfanos:
            nombres = ", ".join(f"`{n}`" for n, _ in pruebas[codigo])
            partes.append(f"- `{codigo}` — {nombres}")
        partes.append("")

    partes += ["---", "", "## Por archivo de contratos", ""]

    por_archivo: dict[tuple[str, str], list] = defaultdict(list)
    for codigo, operacion, archivo, titulo in contratos:
        por_archivo[(archivo, titulo)].append((codigo, operacion))

    for (archivo, titulo), propios in sorted(por_archivo.items()):
        cubiertos = sum(1 for codigo, _ in propios if pruebas.get(codigo))
        partes += [
            f"### `{archivo}` — {titulo}",
            "",
            f"{len(propios)} contratos · {cubiertos} con prueba · {len(propios) - cubiertos} sin.",
            "",
            "| Contrato | Operación | Pruebas | Dónde |",
            "| --- | --- | ---: | --- |",
        ]
        for codigo, operacion in sorted(propios):
            encontradas = pruebas.get(codigo, [])
            if not encontradas:
                partes.append(f"| `{codigo}` | {operacion} | — | — |")
                continue
            archivos = sorted({a for _, a in encontradas})
            partes.append(
                f"| `{codigo}` | {operacion} | {len(encontradas)} | "
                + ", ".join(f"`{a}`" for a in archivos)
                + " |"
            )
        partes.append("")

    partes += ["---", "", "## Prueba por prueba", ""]
    partes.append(
        "Cada contrato con sus pruebas, por nombre. El nombre dice qué postcondición verifica "
        "cada una, que es lo que hace consultable la trazabilidad sin abrir un archivo."
    )
    partes.append("")
    for codigo, operacion, _, _ in sorted(contratos):
        encontradas = pruebas.get(codigo)
        if not encontradas:
            continue
        partes.append(f"**`{codigo}` · {operacion}**")
        partes.append("")
        for nombre, archivo in sorted(encontradas):
            partes.append(f"- `{nombre}` — `{archivo}`")
        partes.append("")

    partes += [
        "---",
        "",
        "## Lo que esta fotografía no cubre",
        "",
        "- **No dice que un contrato esté verificado**, sólo que alguna prueba lleva su código. "
        "Una postcondición sin prueba no se distingue desde acá de una cubierta.",
        "- **No mira las pruebas que no son de contrato.** Las de acceso, flujo, unidad y "
        "frontera no llevan código de contrato en el nombre, a propósito, y no entran en este "
        "recuento.",
        "- **No mide cobertura de líneas.** Es otra puerta y su número vive en "
        "[`../ESTADO.md`](../ESTADO.md).",
        "",
    ]

    resumen = {
        "contratos": len(contratos),
        "con_prueba": len(con_prueba),
        "sin_prueba": len(sin_prueba),
        "pruebas": sum(len(v) for v in pruebas.values()),
        "huerfanos": len(huerfanos),
    }
    return "\n".join(partes), resumen


def main() -> int:
    p = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    p.add_argument("--contratos", type=Path, default=RAIZ / ".contexto-ia" / "contratos")
    p.add_argument("--apps", type=Path, default=RAIZ / "apps")
    p.add_argument("--salida", type=Path, default=RAIZ / "docs" / "pruebas" / "COBERTURA.md")
    args = p.parse_args()

    if not args.contratos.is_dir():
        print(f"error: no existe {args.contratos}", file=sys.stderr)
        print("       corre antes scripts/generar_contexto.py", file=sys.stderr)
        return 1

    contratos = leer_contratos(args.contratos)
    if not contratos:
        print(f"error: no se encontro ningun contrato en {args.contratos}", file=sys.stderr)
        return 1

    pruebas = leer_pruebas(args.apps)
    documento, resumen = armar(contratos, pruebas)

    args.salida.parent.mkdir(parents=True, exist_ok=True)
    args.salida.write_text(documento.rstrip() + "\n", encoding="utf-8")

    print(f"Escrito    : {args.salida.relative_to(RAIZ)}")
    print(f"Contratos  : {resumen['contratos']}")
    print(f"Con prueba : {resumen['con_prueba']}")
    print(f"Sin prueba : {resumen['sin_prueba']}")
    print(f"Pruebas de contrato: {resumen['pruebas']}")
    if resumen["huerfanos"]:
        print(f"AVISO: {resumen['huerfanos']} codigo(s) de prueba sin contrato que los respalde.")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
