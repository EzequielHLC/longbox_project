#!/usr/bin/env python3
"""
Genera `.contexto-ia/ESTRUCTURA.md` desde el árbol del repositorio.

    python scripts/generar_estructura.py

Es el mapa con el que alguien se orienta sin abrir ningún archivo: qué carpetas hay, qué contiene
cada app, y para qué sirve cada archivo que no se explica solo por su nombre.

De dónde saca las descripciones
-------------------------------
**No las inventa.** Cada descripción sale del propio archivo:

    *.py      el docstring del módulo, primer párrafo
    *.html    el primer bloque `{% comment %}` de la plantilla, primer párrafo

Cuando un archivo no tiene ni una cosa ni la otra, se cae a una tabla de roles fijos para los
nombres canónicos de Django (`models.py`, `views.py`, `urls.py`, …), que son justamente los que
no hace falta explicar. Si no es ninguno de los dos casos, la celda queda en `—`: preferible a
una descripción plausible y equivocada.

Qué escribe y qué NO toca
-------------------------
Escribe un solo archivo, y lo pisa entero en cada corrida:

    .contexto-ia/ESTRUCTURA.md

Todo lo demás bajo `.contexto-ia/` es de `generar_contexto.py` o del responsable. Este script no
lo lee para generar, no lo modifica, y no depende de su contenido.

Qué deliberadamente no lleva
----------------------------
**Nada de estado ni de avance.** Ni cuántos casos de uso hay construidos, ni qué módulo falta, ni
porcentajes de cobertura. Eso vive en `docs/ESTADO.md` y en `docs/DEUDA.md`, que son su domicilio
único. Un mapa que además informa avance se desactualiza por el lado del avance y arrastra al
mapa con él.

Los conteos de archivos y de líneas que sí aparecen son estructura, no progreso: dicen dónde está
el peso del código, no cuánto se hizo.

Verificación
------------
Al terminar informa lo que no pudo describir: archivos sin docstring y sin comentario, y carpetas
que encontró y no tenía previstas. Si el repositorio cambia de forma, aparece ahí.
"""

from __future__ import annotations

import argparse
import ast
import re
import sys
from datetime import date
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent

# --------------------------------------------------------------------------- #
# Qué se recorre y qué no
# --------------------------------------------------------------------------- #

# Carpetas que no entran al mapa, y por qué. El motivo se publica en el archivo: un mapa que
# omite algo en silencio se lee como si eso no existiera.
EXCLUIDAS = {
    "venv": "entorno virtual",
    "__pycache__": "artefactos de compilación",
    ".git": "metadatos de git",
    ".ruff_cache": "caché del análisis estático",
    ".pytest_cache": "caché de la suite",
    ".mypy_cache": "caché de tipos",
    "htmlcov": "informe de cobertura, se regenera",
    "staticfiles": "estáticos recolectados, se regeneran",
    "node_modules": "dependencias de front, si llegaran a existir",
    ".vscode": "preferencias del editor",
    ".claude": "configuración del asistente",
    "media": "archivos subidos en desarrollo (portadas, correos)",
    "respaldos": "volcados de la base, fuera del repositorio",
    ".idea": "preferencias del editor",
}

# Extensiones que se listan archivo por archivo dentro de una app.
CODIGO = {".py", ".html"}

# Las migraciones se cuentan pero no se enumeran: son decenas, el nombre ya dice qué hacen y
# ninguna necesita descripción propia.
NO_ENUMERAR = {"migrations"}

# --------------------------------------------------------------------------- #
# Roles fijos: los nombres canónicos que no hace falta explicar
# --------------------------------------------------------------------------- #

ROLES = {
    "__init__.py": "Marca el paquete.",
    "apps.py": "Configuración de la app.",
    "models.py": "Modelos de datos de la app.",
    "views.py": "Vistas de la app.",
    "urls.py": "Rutas de la app.",
    "forms.py": "Formularios de la app.",
    "tests.py": "Pruebas de la app.",
    "signals.py": "Señales de la app.",
    "backends.py": "Backends de autenticación.",
    "mixins.py": "Mixins compartidos.",
    "utils.py": "Utilidades sueltas.",
    "factories.py": "Constructores de objetos para las pruebas.",
    "conftest.py": "Fixtures y configuración de la suite.",
    "manage.py": "Punto de entrada de Django.",
    "asgi.py": "Punto de entrada ASGI.",
    "wsgi.py": "Punto de entrada WSGI.",
    "context_processors.py": "Variables que se inyectan en toda plantilla.",
    # Configuración de la raíz. No son código de la aplicación pero orientan igual.
    "pyproject.toml": "Configuración de black, ruff y coverage.",
    "pytest.ini": "Configuración de la suite: settings de Django y opciones por defecto.",
    ".pre-commit-config.yaml": "Los hooks que corren antes de cada commit.",
    ".python-version": "La versión de Python del proyecto.",
    ".gitignore": "Qué no entra al repositorio.",
    ".env.example": "Plantilla de las variables de entorno, sin valores reales.",
    "requirements.txt": "Dependencias de ejecución.",
    "requirements-dev.txt": "Dependencias de desarrollo: formato, lint, seguridad y pruebas.",
    "README.md": "Puesta en marcha del proyecto.",
    "CLAUDE.md": "Reglas de trabajo sobre el repositorio. Normativo.",
}

# Archivos de la raíz que existen en el disco y no orientan a nadie: artefactos regenerables o
# material con secretos, que se nombra en «lo que no cubre» y no en la tabla.
RAIZ_EXCLUIDOS = {".coverage", "coverage.xml", "db.sqlite3", ".env"}

# Descripción de las carpetas del esqueleto. Es estructura del proyecto, no interpretación.
CARPETAS = {
    "apps": "Las cuatro aplicaciones Django del sistema.",
    "config": "Configuración del proyecto: settings por entorno, rutas raíz, puntos de entrada.",
    "templates": "Plantillas compartidas: las cáscaras de los dos modos y los parciales reusables.",
    "static": "Hojas de estilo, scripts e imágenes servidos tal cual.",
    "docs": "Estado, deuda, planes, método de pruebas y despliegue. Se escribe a mano.",
    "bitacora": "Lo que se decidió construyendo, por módulo. Se anexa, no se reescribe.",
    ".contexto-ia": "La especificación volcada del documento de análisis, más este mapa.",
    "scripts": "Los generadores: contexto, estructura, cobertura y DSS. Viajan con el repositorio.",
    ".github": "Definición de las puertas de calidad que corren en cada push.",
}

CABECERA = (
    "> **Tipo: Fotografía.** Tomada el **{fecha}**, del árbol del repositorio y no de memoria.\n"
    "> **Generado por `scripts/generar_estructura.py`.** No lo edites: la próxima corrida lo "
    "pisa.\n"
    "> Si algo está mal acá, anotalo en la bitácora del módulo.\n\n"
)

# --------------------------------------------------------------------------- #
# Lectura de descripciones
# --------------------------------------------------------------------------- #

RE_COMMENT = re.compile(r"\{%\s*comment\s*%\}(.*?)\{%\s*endcomment\s*%\}", re.S)
RE_HTML_COMMENT = re.compile(r"<!--(.*?)-->", re.S)


def _primer_parrafo(texto: str) -> str:
    """El primer párrafo de un bloque, en una sola línea y sin marcas de énfasis."""
    texto = texto.strip()
    if not texto:
        return ""
    parrafo = texto.split("\n\n")[0]
    parrafo = " ".join(linea.strip() for linea in parrafo.splitlines() if linea.strip())
    # El énfasis de Markdown dentro de una celda de tabla no aporta y a veces rompe la fila.
    parrafo = parrafo.replace("**", "").replace("`", "").replace("|", "/")
    return parrafo.strip()


def _recortar(texto: str, tope: int = 200) -> str:
    """Hasta la primera oración, o hasta el tope si la oración es larga."""
    if not texto:
        return ""
    # Un punto seguido de espacio y mayúscula corta oración; uno dentro de `RF-10.` o de un
    # nombre de archivo, no.
    m = re.search(r"(?<=[a-z0-9)»”\"])\.\s+(?=[A-ZÁÉÍÓÚÑ¿¡«])", texto)
    if m and m.start() < tope:
        return texto[: m.start() + 1]
    if len(texto) <= tope:
        return texto
    corte = texto.rfind(" ", 0, tope)
    return texto[: corte if corte > 0 else tope].rstrip(",;:") + "…"


def describir_py(ruta: Path) -> str:
    try:
        arbol = ast.parse(ruta.read_text(encoding="utf-8"))
    except (SyntaxError, UnicodeDecodeError):
        return ""
    return _recortar(_primer_parrafo(ast.get_docstring(arbol) or ""))


def describir_html(ruta: Path) -> str:
    try:
        texto = ruta.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return ""
    m = RE_COMMENT.search(texto) or RE_HTML_COMMENT.search(texto)
    if not m:
        return ""
    return _recortar(_primer_parrafo(m.group(1)))


def describir(ruta: Path) -> tuple[str, bool]:
    """La descripción del archivo, y si salió del archivo mismo o de la tabla de roles."""
    if ruta.suffix == ".py":
        d = describir_py(ruta)
    elif ruta.suffix == ".html":
        d = describir_html(ruta)
    else:
        d = ""
    if d:
        return d, True
    return ROLES.get(ruta.name, ""), False


def lineas(ruta: Path) -> int:
    try:
        return sum(1 for _ in ruta.open(encoding="utf-8", errors="replace"))
    except OSError:
        return 0


# --------------------------------------------------------------------------- #
# Recorrido
# --------------------------------------------------------------------------- #


def subdirectorios(base: Path) -> list[Path]:
    return sorted(
        (d for d in base.iterdir() if d.is_dir() and d.name not in EXCLUIDAS),
        key=lambda d: d.name,
    )


def archivos(base: Path, extensiones: set[str] | None = None) -> list[Path]:
    return sorted(
        (
            f
            for f in base.iterdir()
            if f.is_file() and (extensiones is None or f.suffix in extensiones)
        ),
        key=lambda f: f.name,
    )


def contar(base: Path) -> int:
    """Archivos bajo una carpeta, recursivo, sin contar lo excluido."""
    total = 0
    for hijo in base.iterdir():
        if hijo.is_dir():
            if hijo.name not in EXCLUIDAS:
                total += contar(hijo)
        else:
            total += 1
    return total


def arbol(base: Path, prefijo: str = "", profundidad: int = 3) -> list[str]:
    """El árbol de carpetas, sin archivos. Cada rama dice cuántos archivos cuelgan de ella."""
    if profundidad <= 0:
        return []
    hijos = subdirectorios(base)
    salida: list[str] = []
    for i, d in enumerate(hijos):
        ultimo = i == len(hijos) - 1
        rama = "└── " if ultimo else "├── "
        n = contar(d)
        nota = f"  ({n} archivo{'s' if n != 1 else ''})" if n else ""
        salida.append(f"{prefijo}{rama}{d.name}/{nota}")
        if d.name not in NO_ENUMERAR:
            salida += arbol(d, prefijo + ("    " if ultimo else "│   "), profundidad - 1)
    return salida


# --------------------------------------------------------------------------- #
# Escritura
# --------------------------------------------------------------------------- #


def tabla(filas: list[tuple[str, str, str]]) -> list[str]:
    if not filas:
        return ["*(vacío)*", ""]
    out = ["| Archivo | Líneas | Para qué sirve |", "| --- | --- | --- |"]
    out += [f"| `{a}` | {n} | {d or '—'} |" for a, n, d in filas]
    out.append("")
    return out


def filas_de(base: Path, prefijo: str = "", sin_describir: list[str] | None = None):
    filas = []
    for f in archivos(base, CODIGO):
        d, propia = describir(f)
        if not propia and not d and sin_describir is not None:
            sin_describir.append(str(f.relative_to(RAIZ)).replace("\\", "/"))
        filas.append((prefijo + f.name, str(lineas(f)), d))
    return filas


def seccion_app(app: Path, sin_describir: list[str]) -> list[str]:
    nombre = app.name
    out = [f"### `apps/{nombre}`", ""]

    # El propósito de la app: el docstring de su `__init__.py` si lo tiene, si no el de `apps.py`.
    proposito = describir_py(app / "__init__.py") or describir_py(app / "apps.py")
    if proposito:
        out += [proposito, ""]

    out += ["**Módulos**", ""]
    out += tabla(filas_de(app, sin_describir=sin_describir))

    # Plantillas de la app, que viven en templates/<app>/.
    plantillas = app / "templates" / nombre
    if plantillas.is_dir():
        out += ["**Plantillas**", ""]
        out += tabla(filas_de(plantillas, sin_describir=sin_describir))

    # Comandos de gestión.
    comandos = app / "management" / "commands"
    if comandos.is_dir():
        out += ["**Comandos de gestión**", ""]
        out += tabla(filas_de(comandos, sin_describir=sin_describir))

    # Etiquetas y filtros de plantilla.
    tags = app / "templatetags"
    if tags.is_dir():
        out += ["**Etiquetas de plantilla**", ""]
        out += tabla(filas_de(tags, sin_describir=sin_describir))

    # Pruebas: se enumeran porque el nombre del archivo dice qué cubre.
    pruebas = app / "tests"
    if pruebas.is_dir():
        out += ["**Pruebas**", ""]
        out += tabla(filas_de(pruebas, sin_describir=sin_describir))

    migraciones = app / "migrations"
    if migraciones.is_dir():
        n = len([f for f in archivos(migraciones, {".py"}) if f.name != "__init__.py"])
        out += [
            f"**Migraciones** — {n} en `apps/{nombre}/migrations/`. No se enumeran: el nombre de "
            "cada una dice qué hace.",
            "",
        ]

    # Todo lo que la app tenga y no sea una de las carpetas canónicas de arriba. Sin esto, una
    # carpeta con datos o con muestras desaparece del mapa sin que nadie lo note.
    canonicas = {"migrations", "templates", "tests", "management", "templatetags"}
    for extra in subdirectorios(app):
        if extra.name in canonicas:
            continue
        n = contar(extra)
        out += [
            f"**`{extra.name}/`** — {n} archivo{'s' if n != 1 else ''}.",
            "",
        ]
        filas = [
            (str(f.relative_to(extra)).replace("\\", "/"), str(lineas(f)), describir(f)[0])
            for f in sorted(extra.rglob("*"))
            if f.is_file() and "__pycache__" not in f.parts
        ]
        out += tabla(filas)
    return out


def generar(salida: Path) -> tuple[str, list[str], list[str]]:
    sin_describir: list[str] = []
    imprevistas: list[str] = []

    out: list[str] = [CABECERA.format(fecha=date.today().isoformat())]
    out += [
        "# Estructura del repositorio",
        "",
        "El mapa del repositorio: qué carpetas hay, qué contiene cada app y para qué sirve cada "
        "archivo que no se explica por su nombre.",
        "",
        "**No informa avance.** Qué caso de uso está construido vive en `docs/ESTADO.md`; qué "
        "separa el código de la especificación, en `docs/DEUDA.md`.",
        "",
        "---",
        "",
        "## El árbol",
        "",
        "```",
        f"{RAIZ.name}/",
    ]
    out += arbol(RAIZ)
    out += ["```", ""]

    # Qué es cada carpeta de primer nivel.
    out += ["| Carpeta | Qué contiene |", "| --- | --- |"]
    for d in subdirectorios(RAIZ):
        descripcion = CARPETAS.get(d.name, "")
        if not descripcion:
            imprevistas.append(d.name)
            descripcion = "—"
        out.append(f"| `{d.name}/` | {descripcion} |")
    out += ["", "---", ""]

    # --- las apps ---
    apps_dir = RAIZ / "apps"
    out += [
        "## Las apps",
        "",
        "Cuatro aplicaciones Django. Cada una lleva sus modelos, sus vistas, sus plantillas y sus "
        "pruebas adentro.",
        "",
    ]
    for app in subdirectorios(apps_dir):
        out += seccion_app(app, sin_describir)
        out += ["---", ""]

    # --- configuración ---
    config = RAIZ / "config"
    out += ["## `config/` — configuración del proyecto", ""]
    out += tabla(filas_de(config, sin_describir=sin_describir))
    ajustes = config / "settings"
    if ajustes.is_dir():
        out += ["**Ajustes por entorno**", ""]
        out += tabla(filas_de(ajustes, prefijo="settings/", sin_describir=sin_describir))
    out += ["---", ""]

    # --- plantillas compartidas ---
    plantillas = RAIZ / "templates"
    out += [
        "## `templates/` — plantillas compartidas",
        "",
        "Las cáscaras de los dos modos del sistema visual y los parciales que reusan todas las "
        "apps. Las plantillas propias de cada app viven dentro de la app.",
        "",
    ]
    out += tabla(filas_de(plantillas, sin_describir=sin_describir))
    out += ["---", ""]

    # --- estáticos ---
    estaticos = RAIZ / "static"
    if estaticos.is_dir():
        out += ["## `static/`", ""]
        filas = []
        for f in sorted(estaticos.rglob("*")):
            if f.is_file() and "__pycache__" not in f.parts:
                filas.append((str(f.relative_to(estaticos)).replace("\\", "/"), str(lineas(f)), ""))
        out += tabla(filas)
        out += ["---", ""]

    # --- scripts ---
    scripts = RAIZ / "scripts"
    if scripts.is_dir():
        out += [
            "## `scripts/` — los generadores",
            "",
            "No forman parte de la aplicación: producen documentación desde el documento de "
            "análisis y desde el repositorio.",
            "",
        ]
        out += tabla(filas_de(scripts, sin_describir=sin_describir))
        out += ["---", ""]

    # --- raíz ---
    out += ["## Archivos de la raíz", ""]
    filas = []
    omitidos = []
    for f in archivos(RAIZ):
        if f.name in RAIZ_EXCLUIDOS:
            omitidos.append(f.name)
            continue
        d, _ = describir(f)
        filas.append((f.name, str(lineas(f)), d))
    out += tabla(filas)
    if omitidos:
        out += [
            "No se listan, por ser artefactos regenerables o llevar secretos: "
            + ", ".join(f"`{n}`" for n in omitidos)
            + ".",
            "",
        ]
    out += ["---", ""]

    # --- lo que no aparece ---
    out += [
        "## Lo que este mapa no cubre",
        "",
        "Carpetas que existen en el disco y no entran al recorrido:",
        "",
        "| Carpeta | Por qué no está |",
        "| --- | --- |",
    ]
    for nombre, motivo in sorted(EXCLUIDAS.items()):
        if (RAIZ / nombre).exists() or any(RAIZ.rglob(nombre)):
            out.append(f"| `{nombre}/` | {motivo} |")
    out += [
        "",
        "Tampoco cubre el contenido de `.contexto-ia/`, que es la especificación volcada: su "
        "punto de entrada es `.contexto-ia/INDICE.md`.",
        "",
    ]
    if sin_describir:
        out += [
            "Archivos sin docstring ni comentario de cabecera, que quedaron con la celda en `—`:",
            "",
        ]
        out += [f"- `{r}`" for r in sin_describir]
        out += [""]

    return "\n".join(out).rstrip() + "\n", sin_describir, imprevistas


def main() -> int:
    p = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    p.add_argument("--salida", type=Path, default=RAIZ / ".contexto-ia" / "ESTRUCTURA.md")
    p.add_argument("--dry-run", action="store_true", help="informa sin escribir nada")
    args = p.parse_args()

    contenido, sin_describir, imprevistas = generar(args.salida)

    print(f"Repositorio: {RAIZ}")
    print(f"Salida     : {args.salida}")
    if args.dry_run:
        print("Modo       : dry-run, no se escribe nada")
    else:
        args.salida.parent.mkdir(parents=True, exist_ok=True)
        args.salida.write_text(contenido, encoding="utf-8")

    print("\nVerificación")
    problemas = 0
    if sin_describir:
        problemas += len(sin_describir)
        print(f"  · {len(sin_describir)} archivo(s) sin docstring ni comentario de cabecera:")
        for r in sin_describir:
            print(f"      {r}")
    if imprevistas:
        problemas += len(imprevistas)
        print(
            f"  · {len(imprevistas)} carpeta(s) de primer nivel sin descripción prevista: "
            f"{', '.join(imprevistas)}"
        )
    if not problemas:
        print("  Sin observaciones.")

    print("\nNo se tocó: todo lo demás bajo .contexto-ia/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
