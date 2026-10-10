"""El ensayo completo de la demostración, o la verificación rápida de la mañana.

    python scripts/demo/ensayo.py            # todos los escenarios, con la carga de 10 minutos
    python scripts/demo/ensayo.py --rapido   # uno corto de cada acto (unos 3 minutos)
    python scripts/demo/ensayo.py --solo D3-01 D6-04   # sólo esos

Requiere el servidor de la demostración levantado (`manejar.py servir` y Caddy con
`Caddyfile.demo`). Corre cada herramienta, guarda su salida en
`salida/ensayo-<fecha>/` con el tiempo y el código de salida, y restaura la base
después de cada escenario que escribe datos. Al final imprime la tabla de
resultados.
"""

import argparse
import os
import subprocess  # nosec B404 - herramientas de la demostración con argumentos fijos
import sys
import time
from datetime import datetime
from pathlib import Path

from entorno import RAIZ, SALIDA

AQUI = Path(__file__).resolve().parent
PY = sys.executable

# (código, comando, ¿escribe en la base?, en qué modo: «ambos», «completo» o «rapido»)
ESCENARIOS = [
    ("D1-02", [PY, AQUI / "sabotaje.py", "todos"], False, "completo"),
    ("D1-02 rápido", [PY, AQUI / "sabotaje.py", "acceso"], False, "rapido"),
    ("D3-01", [PY, AQUI / "rutas_protegidas.py"], False, "ambos"),
    ("D3-02..09", [PY, AQUI / "ataques.py"], True, "ambos"),
    ("D4-02..06", [PY, AQUI / "carreras.py", "--veces", "20"], True, "completo"),
    ("D4-02..06 rápido", [PY, AQUI / "carreras.py", "--veces", "3"], True, "rapido"),
    ("D5-01", [PY, AQUI / "linea_base.py"], False, "ambos"),
    (
        "D5-02",
        [
            "locust",
            "-f",
            AQUI / "locustfile.py",
            "--headless",
            "-u",
            "50",
            "-r",
            "5",
            "-t",
            "10m",
            "--host",
            "https://127.0.0.1:8443",
            "--csv",
            SALIDA / "carga_50",
            "--only-summary",
        ],
        True,
        False,
    ),
    (
        "D5-02 rápido",
        [
            "locust",
            "-f",
            AQUI / "locustfile.py",
            "--headless",
            "-u",
            "50",
            "-r",
            "10",
            "-t",
            "1m",
            "--host",
            "https://127.0.0.1:8443",
            "--csv",
            SALIDA / "carga_50_corta",
            "--only-summary",
        ],
        True,
        True,
    ),
    ("D5-03", [PY, AQUI / "escalones.py"], True, "completo"),
    ("D6-01..02", [PY, AQUI / "modelo_caido.py"], True, "ambos"),
    ("D6-04", [PY, AQUI / "caida_base.py"], False, "ambos"),
    ("D6-06", [PY, AQUI / "respaldo.py"], False, "completo"),
]


def correr(comando, destino):
    inicio = time.perf_counter()
    with open(destino, "w", encoding="utf-8") as archivo:
        codigo = subprocess.call(  # nosec B603
            [str(parte) for parte in comando],
            cwd=RAIZ,
            stdout=archivo,
            stderr=subprocess.STDOUT,
            env={**os.environ, "PYTHONIOENCODING": "utf-8"},
        )
    return codigo, time.perf_counter() - inicio


def main():
    argumentos = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    argumentos.add_argument("--rapido", action="store_true")
    argumentos.add_argument("--solo", nargs="+", help="Sólo estos escenarios, por su código.")
    opciones = argumentos.parse_args()
    carpeta = SALIDA / f"ensayo-{datetime.now():%Y%m%d-%H%M}"
    carpeta.mkdir(parents=True, exist_ok=True)
    filas = []
    modo = "rapido" if opciones.rapido else "completo"
    for codigo_escenario, comando, escribe, cuando in ESCENARIOS:
        if opciones.solo:
            if codigo_escenario not in opciones.solo:
                continue
        elif cuando not in ("ambos", modo):
            continue
        print(f"→ {codigo_escenario} …", flush=True)
        destino = carpeta / f"{codigo_escenario.replace(' ', '_')}.txt"
        codigo, segundos = correr(comando, destino)
        restaurado = ""
        if escribe:
            _, segundos_restaurar = correr([PY, AQUI / "restaurar.py"], carpeta / "restaurar.txt")
            restaurado = f"restaurada en {segundos_restaurar:.1f} s"
        resultado = "OK" if codigo == 0 else f"FALLA ({codigo})"
        filas.append((codigo_escenario, resultado, segundos, restaurado, destino.name))
        print(f"  {resultado} en {segundos:.0f} s {restaurado}", flush=True)
    resumen = [
        "| Escenario | Resultado | Tiempo | Base | Salida |",
        "| --- | --- | --- | --- | --- |",
    ]
    for escenario, resultado, segundos, restaurado, archivo in filas:
        resumen.append(
            f"| {escenario} | {resultado} | {segundos:.0f} s | {restaurado} | `{archivo}` |"
        )
    (carpeta / "resumen.md").write_text("\n".join(resumen) + "\n", encoding="utf-8")
    print("\n".join(resumen))
    return 0 if all(fila[1] == "OK" for fila in filas) else 1


if __name__ == "__main__":
    sys.exit(main())
