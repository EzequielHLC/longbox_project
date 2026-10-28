# ruff: noqa: E501 - la plantilla SVG del gráfico se lee mejor sin cortar sus líneas
"""D5-03 · Hasta dónde llega: la carga sube por escalones hasta que el p95 pasa 2 s o hay errores.

    python scripts/demo/escalones.py [--duracion 90] [--escalones 50 100 200 400]

Cada escalón es una corrida de locust sin interfaz (`locustfile.py`) contra el
servidor de la demostración. Se detiene en el primer escalón donde el percentil 95
supera los 2 segundos de RNF-02 o aparecen errores: **no** se sigue subiendo sin
límite, porque cliente y servidor comparten la máquina y puede congelarse.

Deja la tabla en `salida/escalones.json` y el gráfico en
`salida/carga_escalones.svg`: percentiles por escalón, con la línea
horizontal de los 2 s del requisito.
"""

import argparse
import csv
import json
import subprocess  # nosec B404 - locust con argumentos fijos
import sys
from pathlib import Path

from entorno import DIRECCION, RAIZ, SALIDA

GRAFICOS = RAIZ / "scripts" / "demo" / "salida"
UMBRAL_MS = 2000


def correr(usuarios, duracion):
    prefijo = SALIDA / f"escalon_{usuarios}"
    subprocess.run(  # nosec B603 B607 - locust con argumentos fijos, sin shell
        [
            "locust",
            "-f",
            str(Path(__file__).with_name("locustfile.py")),
            "--headless",
            "-u",
            str(usuarios),
            "-r",
            str(max(5, usuarios // 10)),
            "-t",
            f"{duracion}s",
            "--host",
            DIRECCION,
            "--csv",
            str(prefijo),
            "--only-summary",
        ],
        cwd=RAIZ,
        capture_output=True,
    )
    with open(f"{prefijo}_stats.csv", encoding="utf-8") as archivo:
        total = next(fila for fila in csv.DictReader(archivo) if fila["Name"] == "Aggregated")
    pedidos = int(total["Request Count"])
    errores = int(total["Failure Count"])
    return {
        "usuarios": usuarios,
        "pedidos": pedidos,
        "errores": errores,
        "p50_ms": float(total["50%"]),
        "p95_ms": float(total["95%"]),
        "p99_ms": float(total["99%"]),
        "pedidos_por_s": round(float(total["Requests/s"]), 1),
    }


def grafico(filas, destino):
    """Un SVG simple: p50 y p95 por escalón, y la línea del requisito."""
    ancho, alto, margen = 640, 360, 60
    maximo = max(UMBRAL_MS * 1.2, *(f["p95_ms"] for f in filas))

    def x(indice):
        return margen + indice * (ancho - 2 * margen) / max(1, len(filas) - 1)

    def y(valor):
        return alto - margen - valor / maximo * (alto - 2 * margen)

    def linea(clave, color):
        puntos = " ".join(f"{x(i):.0f},{y(f[clave]):.0f}" for i, f in enumerate(filas))
        marcas = "".join(
            f'<circle cx="{x(i):.0f}" cy="{y(f[clave]):.0f}" r="4" fill="{color}"/>'
            f'<text x="{x(i):.0f}" y="{y(f[clave]) - 8:.0f}" font-size="11" text-anchor="middle" '
            f'fill="{color}">{f[clave]:.0f}</text>'
            for i, f in enumerate(filas)
        )
        return (
            f'<polyline points="{puntos}" fill="none" stroke="{color}" stroke-width="2"/>{marcas}'
        )

    ejes = "".join(
        f'<text x="{x(i):.0f}" y="{alto - margen + 18}" font-size="12" text-anchor="middle">'
        f'{f["usuarios"]}</text>'
        for i, f in enumerate(filas)
    )
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{ancho}" height="{alto}" font-family="sans-serif">
<rect width="100%" height="100%" fill="#0A0A0C"/>
<g fill="#D4D4DA">
<text x="{margen}" y="28" font-size="15" font-weight="bold">Tiempo de respuesta por escalón de carga (ms)</text>
<line x1="{margen}" y1="{y(UMBRAL_MS):.0f}" x2="{ancho - margen}" y2="{y(UMBRAL_MS):.0f}" stroke="#FF4D5E" stroke-dasharray="6 4"/>
<text x="{ancho - margen}" y="{y(UMBRAL_MS) - 6:.0f}" font-size="11" text-anchor="end" fill="#FF4D5E">RNF-02: 2000 ms</text>
<line x1="{margen}" y1="{alto - margen}" x2="{ancho - margen}" y2="{alto - margen}" stroke="#6E6E78"/>
{ejes}
<text x="{ancho / 2:.0f}" y="{alto - 18}" font-size="12" text-anchor="middle">sesiones concurrentes</text>
{linea("p50_ms", "#5CC8FF")}
{linea("p95_ms", "#FF6A13")}
<text x="{margen}" y="50" font-size="12" fill="#5CC8FF">p50</text>
<text x="{margen + 40}" y="50" font-size="12" fill="#FF6A13">p95</text>
</g>
</svg>
"""
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(svg, encoding="utf-8")


def main():
    argumentos = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    argumentos.add_argument("--duracion", type=int, default=90)
    argumentos.add_argument("--escalones", type=int, nargs="+", default=[50, 100, 200, 400])
    argumentos.add_argument("--nombre", default="carga_escalones")
    opciones = argumentos.parse_args()
    filas = []
    for usuarios in opciones.escalones:
        fila = correr(usuarios, opciones.duracion)
        filas.append(fila)
        print(
            f"{usuarios:>4} sesiones: {fila['pedidos']} pedidos, {fila['errores']} errores, "
            f"p50 {fila['p50_ms']:.0f} ms, p95 {fila['p95_ms']:.0f} ms, "
            f"{fila['pedidos_por_s']} pedidos/s",
            flush=True,
        )
        if fila["p95_ms"] > UMBRAL_MS or fila["errores"]:
            print("  → se degrada acá: se corta la subida.")
            break
    (SALIDA / f"{opciones.nombre}.json").write_text(json.dumps(filas, indent=2), encoding="utf-8")
    grafico(filas, GRAFICOS / f"{opciones.nombre}.svg")
    print(f"Gráfico: {GRAFICOS / (opciones.nombre + '.svg')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
