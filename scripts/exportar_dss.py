#!/usr/bin/env python3
"""
Exporta los diagramas PlantUML embebidos en un documento Markdown a archivos SVG,
usando un servidor PlantUML dockerizado.

Uso típico (servidor en localhost:8080):

    docker run -d -p 8080:8080 plantuml/plantuml-server:jetty
    python export_dss.py

Opciones frecuentes:

    python export_dss.py --input 02_DSS.md --output svg/
    python export_dss.py --scale 3 --format png
    python export_dss.py --no-monochrome
    python export_dss.py --dry-run          # no contacta al servidor
    python export_dss.py --only DSS01 DSS42 # exporta sólo esos diagramas

Requisitos: sólo la librería estándar. `requests` se usa si está instalada, pero no hace falta.

**No escribe en `.contexto-ia/dss/`, y se niega si se le pide.** Esa carpeta la mantiene el
responsable a mano: contiene los diagramas en su forma fuente —el PlantUML dentro del Markdown—
y el inventario de operaciones. Lo que este script produce son imágenes *derivadas* de ese
material, y dejarlas ahí las mezclaría con la fuente. Van a una carpeta de salida propia.
"""

from __future__ import annotations

import argparse
import concurrent.futures as futures
import re
import string
import sys
import urllib.error
import urllib.request
import zlib
from dataclasses import dataclass
from pathlib import Path

# --------------------------------------------------------------------------- #
# Extracción de los bloques del Markdown
# --------------------------------------------------------------------------- #

FENCE_RE = re.compile(
    r"^[ \t]*```[ \t]*plantuml[ \t]*$(.*?)^[ \t]*```[ \t]*$", re.MULTILINE | re.DOTALL
)
STARTUML_RE = re.compile(r"^@startuml(?:[ \t]+(\S+))?[ \t]*$", re.MULTILINE)

# skinparams / directivas que el script controla y por lo tanto elimina del
# original antes de inyectar las suyas. Sin esto, un "skinparam shadowing false"
# ya presente en el diagrama ganaría por venir después.
OVERRIDDEN_RE = re.compile(
    r"^[ \t]*(?:skinparam[ \t]+(?:shadowing|monochrome)\b.*|scale[ \t]+.*)$",
    re.IGNORECASE | re.MULTILINE,
)


@dataclass
class Diagram:
    """Un bloque ```plantuml``` extraído del Markdown."""

    index: int  # orden de aparición, 1-based
    name: str  # nombre declarado en @startuml, o generado
    source: str  # código PlantUML tal como está en el Markdown
    line: int  # línea del Markdown donde arranca el bloque

    @property
    def filename_stem(self) -> str:
        safe = re.sub(r"[^A-Za-z0-9_.-]", "_", self.name)
        return safe or f"diagram_{self.index:03d}"


def extract_diagrams(markdown: str) -> list[Diagram]:
    """Devuelve todos los bloques ```plantuml``` del documento, en orden."""
    diagrams: list[Diagram] = []
    for i, match in enumerate(FENCE_RE.finditer(markdown), start=1):
        body = match.group(1).strip("\n")
        if not body.strip():
            continue
        line_no = markdown.count("\n", 0, match.start()) + 1

        name_match = STARTUML_RE.search(body)
        name = name_match.group(1) if name_match and name_match.group(1) else f"diagram_{i:03d}"

        diagrams.append(Diagram(index=i, name=name, source=body, line=line_no))
    return diagrams


# --------------------------------------------------------------------------- #
# Preparación del código fuente
# --------------------------------------------------------------------------- #


def prepare_source(source: str, *, scale: float, monochrome: bool, shadowing: bool) -> str:
    """
    Quita las directivas que este script controla e inyecta las propias
    inmediatamente después de @startuml, de modo que apliquen a todo el diagrama.
    """
    cleaned = OVERRIDDEN_RE.sub("", source)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)

    directives = [
        f"scale {scale:g}",
        f"skinparam monochrome {str(monochrome).lower()}",
        f"skinparam shadowing {str(shadowing).lower()}",
    ]
    injection = "\n".join(directives)

    match = STARTUML_RE.search(cleaned)
    if match:
        end = match.end()
        return cleaned[:end] + "\n" + injection + cleaned[end:]

    # Bloque sin @startuml: PlantUML lo acepta, pero hay que envolverlo para
    # poder inyectar las directivas en un lugar válido.
    return f"@startuml\n{injection}\n{cleaned.strip()}\n@enduml"


# --------------------------------------------------------------------------- #
# Codificación propia de PlantUML (deflate + alfabeto base64 alterado)
# --------------------------------------------------------------------------- #

_PLANTUML_ALPHABET = "0123456789" + string.ascii_uppercase + string.ascii_lowercase + "-_"
_B64_ALPHABET = string.ascii_uppercase + string.ascii_lowercase + "0123456789" + "+/"
_TRANSLATION = str.maketrans(_B64_ALPHABET, _PLANTUML_ALPHABET)


def plantuml_encode(text: str) -> str:
    """Codifica el diagrama para incrustarlo en la URL (modo GET del servidor)."""
    import base64

    compressor = zlib.compressobj(9, zlib.DEFLATED, -zlib.MAX_WBITS)
    compressed = compressor.compress(text.encode("utf-8")) + compressor.flush()
    b64 = base64.b64encode(compressed).decode("ascii").rstrip("=")
    return b64.translate(_TRANSLATION)


# --------------------------------------------------------------------------- #
# Comunicación con el servidor
# --------------------------------------------------------------------------- #


class RenderError(RuntimeError):
    pass


# Firmas para verificar que el servidor devolvió el formato que le pedimos.
# Sin esto un servidor que no soporte POST puede responder 200 con un PNG de
# error, y terminaríamos escribiendo un PNG dentro de un archivo .svg.
_MAGIC = {
    "svg": lambda d: d.lstrip()[:200].lower().startswith((b"<?xml", b"<svg")),
    "png": lambda d: d.startswith(b"\x89PNG\r\n\x1a\n"),
    "pdf": lambda d: d.startswith(b"%PDF"),
    "eps": lambda d: d.lstrip().startswith(b"%!PS"),
    "txt": lambda d: True,
}


def _check_format(data: bytes, fmt: str, via: str) -> None:
    if not data:
        raise RenderError(f"el servidor devolvió una respuesta vacía ({via})")
    validator = _MAGIC.get(fmt)
    if validator and not validator(data):
        kind = "PNG" if data.startswith(b"\x89PNG\r\n\x1a\n") else "desconocido"
        raise RenderError(
            f"el servidor devolvió contenido {kind} cuando se pidió {fmt} ({via}); "
            f"probablemente no soporta esa vía"
        )


ESQUEMAS_PERMITIDOS = ("http://", "https://")


def exigir_esquema_http(base: str) -> None:
    """El servidor tiene que ser http o https, y nada más.

    `urlopen` acepta también `file:` y esquemas propios, así que un `--server` mal escrito
    —o copiado de otro lado— podría terminar leyendo un archivo del disco y escribiéndolo como
    si fuera un diagrama renderizado. Se valida acá, una vez, y no en cada llamada.
    """
    if not base.startswith(ESQUEMAS_PERMITIDOS):
        raise RenderError(f"el servidor debe ser http o https, no '{base}'")


def _get(base: str, fmt: str, source: str, timeout: int) -> bytes:
    """Vía principal: GET /<fmt>/<encoded>. La soportan todos los servidores."""
    exigir_esquema_http(base)
    url = f"{base}/{fmt}/{plantuml_encode(source)}"
    if len(url) > 8000:
        raise RenderError("URL_TOO_LONG")
    try:
        # `exigir_esquema_http` de arriba acota el esquema a http/https.
        with urllib.request.urlopen(url, timeout=timeout) as response:  # nosec B310
            data = response.read()
    except urllib.error.HTTPError as exc:
        if exc.code in (413, 414):
            raise RenderError("URL_TOO_LONG") from exc
        raise RenderError(f"HTTP {exc.code} en GET: {exc.reason}") from exc
    except urllib.error.URLError as exc:
        raise RenderError(f"no se pudo contactar {base} ({exc.reason})") from exc
    _check_format(data, fmt, "GET")
    return data


def _post(base: str, fmt: str, source: str, timeout: int) -> bytes:
    """Reserva para diagramas cuya URL codificada excede el límite del servidor."""
    exigir_esquema_http(base)
    request = urllib.request.Request(
        f"{base}/{fmt}",
        data=source.encode("utf-8"),
        method="POST",
        headers={"Content-Type": "text/plain; charset=utf-8"},
    )
    try:
        # `exigir_esquema_http` de arriba acota el esquema a http/https.
        with urllib.request.urlopen(request, timeout=timeout) as response:  # nosec B310
            data = response.read()
    except urllib.error.HTTPError as exc:
        raise RenderError(f"HTTP {exc.code} en POST: {exc.reason}") from exc
    except urllib.error.URLError as exc:
        raise RenderError(f"no se pudo contactar {base} ({exc.reason})") from exc
    _check_format(data, fmt, "POST")
    return data


def render(source: str, *, server: str, fmt: str, timeout: int) -> bytes:
    """
    Renderiza un diagrama contra el servidor PlantUML.

    Usa GET con el diagrama codificado en la URL, que es la vía que todos los
    servidores implementan igual. Sólo recurre a POST cuando la URL resulta
    demasiado larga, porque no todos los servidores lo soportan y algunos
    responden 200 con una imagen de error en lugar de fallar.
    """
    base = server.rstrip("/")
    try:
        return _get(base, fmt, source, timeout)
    except RenderError as exc:
        if str(exc) != "URL_TOO_LONG":
            raise
    return _post(base, fmt, source, timeout)


def looks_like_error(data: bytes, fmt: str) -> str | None:
    """
    El servidor devuelve 200 con una imagen de error cuando el diagrama no compila.
    Para SVG podemos detectarlo mirando el contenido.
    """
    if fmt != "svg":
        return None
    head = data[:4000].decode("utf-8", errors="replace")
    if "@startuml" in head and "Syntax Error" in head:
        return "error de sintaxis reportado por PlantUML"
    for marker in ("Syntax Error?", "cannot be parsed", "Assumed diagram type"):
        if marker in head:
            return f"PlantUML reportó: {marker}"
    return None


# --------------------------------------------------------------------------- #
# Orquestación
# --------------------------------------------------------------------------- #

# Carpetas donde este script no escribe, cualquiera sea el `--output` que se le pase.
PROTEGIDAS = (Path(".contexto-ia") / "dss",)


def es_material_del_responsable(salida: Path) -> bool:
    """¿La carpeta de salida cae dentro de algo que mantiene el responsable?"""
    destino = salida.resolve()
    for protegida in PROTEGIDAS:
        candidata = protegida.resolve()
        if destino == candidata or candidata in destino.parents:
            return True
    return False


def check_server(server: str, timeout: int) -> None:
    probe = "@startuml\nBob -> Alice : ping\n@enduml"
    try:
        render(probe, server=server, fmt="svg", timeout=timeout)
    except RenderError as exc:
        raise SystemExit(
            f"No hay un servidor PlantUML respondiendo en {server}.\n"
            f"  Detalle: {exc}\n\n"
            f"  Levantalo con:\n"
            f"    docker run -d -p 8080:8080 plantuml/plantuml-server:jetty\n"
        ) from exc


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Exporta los diagramas PlantUML de un Markdown a SVG vía servidor PlantUML.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--input",
        "-i",
        type=Path,
        default=Path("02_DSS.md"),
        help="documento Markdown de entrada (default: 02_DSS.md)",
    )
    parser.add_argument(
        "--output", "-o", type=Path, default=Path("svg"), help="carpeta de salida (default: svg/)"
    )
    parser.add_argument(
        "--server",
        "-s",
        default="http://localhost:8080",
        help="URL base del servidor PlantUML (default: http://localhost:8080)",
    )
    parser.add_argument(
        "--format",
        "-f",
        default="svg",
        choices=["svg", "png", "eps", "pdf", "txt"],
        help="formato de salida (default: svg)",
    )
    parser.add_argument(
        "--scale", type=float, default=2.0, help="factor de escala; 2.0 = 200%% (default: 2.0)"
    )
    parser.add_argument(
        "--monochrome",
        dest="monochrome",
        action="store_true",
        default=True,
        help="renderizar en monocromo (default)",
    )
    parser.add_argument(
        "--no-monochrome",
        dest="monochrome",
        action="store_false",
        help="conservar los colores del diagrama",
    )
    parser.add_argument(
        "--shadowing",
        dest="shadowing",
        action="store_true",
        default=True,
        help="activar sombras (default)",
    )
    parser.add_argument(
        "--no-shadowing", dest="shadowing", action="store_false", help="desactivar sombras"
    )
    parser.add_argument(
        "--only",
        nargs="+",
        metavar="NOMBRE",
        help="exportar sólo los diagramas cuyo nombre contenga " "alguno de estos textos",
    )
    parser.add_argument(
        "--jobs", "-j", type=int, default=4, help="peticiones en paralelo (default: 4)"
    )
    parser.add_argument(
        "--timeout", type=int, default=30, help="timeout por diagrama, en segundos (default: 30)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="escribe el .puml preparado en vez de contactar al servidor",
    )
    args = parser.parse_args()

    if not args.input.is_file():
        print(f"error: no existe el archivo de entrada {args.input}", file=sys.stderr)
        return 1

    if es_material_del_responsable(args.output):
        print(
            f"error: {args.output} la mantiene el responsable a mano.\n"
            "       Este script produce imágenes derivadas; elegí otra carpeta de salida.",
            file=sys.stderr,
        )
        return 1

    markdown = args.input.read_text(encoding="utf-8")
    diagrams = extract_diagrams(markdown)

    if not diagrams:
        print(f"No se encontró ningún bloque ```plantuml``` en {args.input}.", file=sys.stderr)
        return 1

    if args.only:
        needles = [n.lower() for n in args.only]
        diagrams = [d for d in diagrams if any(n in d.name.lower() for n in needles)]
        if not diagrams:
            print(f"Ningún diagrama coincide con {args.only}.", file=sys.stderr)
            return 1

    # Nombres duplicados: se desambiguan con un sufijo, para no pisar archivos.
    seen: dict[str, int] = {}
    for diagram in diagrams:
        stem = diagram.filename_stem
        if stem in seen:
            seen[stem] += 1
            diagram.name = f"{diagram.name}__{seen[stem]}"
        else:
            seen[stem] = 1

    args.output.mkdir(parents=True, exist_ok=True)

    print(f"Entrada    : {args.input}")
    print(f"Diagramas  : {len(diagrams)}")
    print(f"Salida     : {args.output}/")
    print(
        f"Formato    : {args.format}  ·  escala {args.scale:g}x "
        f"({args.scale * 100:g}%)  ·  monochrome={str(args.monochrome).lower()}  "
        f"·  shadowing={str(args.shadowing).lower()}"
    )

    prepared = {
        d.name: prepare_source(
            d.source, scale=args.scale, monochrome=args.monochrome, shadowing=args.shadowing
        )
        for d in diagrams
    }

    if args.dry_run:
        print("Modo       : dry-run (no se contacta al servidor)\n")
        for diagram in diagrams:
            path = args.output / f"{diagram.filename_stem}.puml"
            path.write_text(prepared[diagram.name], encoding="utf-8")
            print(f"  · {path}")
        print(f"\n{len(diagrams)} archivos .puml escritos.")
        return 0

    print(f"Servidor   : {args.server}\n")
    check_server(args.server, args.timeout)

    ok: list[str] = []
    failed: list[tuple[str, str]] = []

    def work(diagram: Diagram) -> tuple[Diagram, bytes | None, str | None]:
        try:
            data = render(
                prepared[diagram.name], server=args.server, fmt=args.format, timeout=args.timeout
            )
        except RenderError as exc:
            return diagram, None, str(exc)
        problem = looks_like_error(data, args.format)
        return diagram, data, problem

    with futures.ThreadPoolExecutor(max_workers=max(1, args.jobs)) as pool:
        for diagram, data, problem in pool.map(work, diagrams):
            label = f"[{diagram.index:>3}/{len(diagrams)}] {diagram.name}"
            if data is None:
                failed.append((diagram.name, problem or "error desconocido"))
                print(f"  ✗ {label} — {problem}")
                continue
            path = args.output / f"{diagram.filename_stem}.{args.format}"
            path.write_bytes(data)
            if problem:
                failed.append((diagram.name, problem))
                print(f"  ! {label} — {problem} (archivo escrito igual)")
            else:
                ok.append(diagram.name)
                print(f"  ✓ {label} — {len(data):,} bytes")

    print(f"\nExportados sin problemas: {len(ok)}/{len(diagrams)}")
    if failed:
        print(f"Con problemas: {len(failed)}")
        for name, reason in failed:
            print(f"  · {name}: {reason}")
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
