"""D5-01 · Línea base: tiempos de respuesta con un solo usuario (RNF-02).

    python scripts/demo/linea_base.py [--veces 20]

Contra el servidor de la demostración (`https://127.0.0.1:8443`), con la base
poblada. Mide cinco operaciones, cada una `--veces` seguidas, y guarda la mediana
y el percentil 95 en `salida/linea_base.json`: es la referencia contra la que se
calcula la degradación de D5-02.
"""

import argparse
import json
import re
import statistics
import sys
import time

import requests
from entorno import AUTORIDAD_LOCAL, DIRECCION, SALIDA

OPERACIONES = {
    "inventario: búsqueda": "/catalogo/productos/?q=one",
    "inventario: ficha": "/catalogo/productos/{producto}/",
    "correos: cola": "/proveedores/correos/",
    "cuentas: clientes": "/cuentas/clientes/",
    "auditoría: página": "/auditoria/?page=50",
}


def iniciar_sesion(sesion, correo):
    sesion.verify = AUTORIDAD_LOCAL
    sesion.get(f"{DIRECCION}/cuentas/login/")
    inicio = time.perf_counter()
    respuesta = sesion.post(
        f"{DIRECCION}/cuentas/login/",
        {
            "username": correo,
            "password": "Demo-2026!",  # nosec B105 - cuenta de demostración
            "csrfmiddlewaretoken": sesion.cookies.get("csrftoken"),
        },
        headers={"Referer": f"{DIRECCION}/cuentas/login/"},
    )
    if "sessionid" not in sesion.cookies:
        raise SystemExit(f"No se pudo iniciar sesión como {correo} ({respuesta.status_code}).")
    return time.perf_counter() - inicio


def percentil(valores, p):
    ordenados = sorted(valores)
    return ordenados[min(len(ordenados) - 1, round(p / 100 * (len(ordenados) - 1)))]


def main():
    argumentos = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    argumentos.add_argument("--veces", type=int, default=20)
    opciones = argumentos.parse_args()

    tiempos = {"inicio de sesión (POST)": []}
    for _ in range(min(opciones.veces, 10)):
        tiempos["inicio de sesión (POST)"].append(
            iniciar_sesion(requests.Session(), "admin1@longbox.demo")
        )

    sesion = requests.Session()
    iniciar_sesion(sesion, "admin1@longbox.demo")
    pagina = sesion.get(f"{DIRECCION}/catalogo/productos/").text
    producto = re.search(r"/catalogo/productos/(\d+)/", pagina).group(1)
    for nombre, ruta in OPERACIONES.items():
        url = DIRECCION + ruta.format(producto=producto)
        sesion.get(url)  # calentamiento
        tiempos[nombre] = []
        for _ in range(opciones.veces):
            inicio = time.perf_counter()
            respuesta = sesion.get(url)
            tiempos[nombre].append(time.perf_counter() - inicio)
            if respuesta.status_code != 200:
                raise SystemExit(f"{nombre}: respuesta {respuesta.status_code}")

    resumen = {
        nombre: {
            "mediana_ms": round(statistics.median(valores) * 1000),
            "p95_ms": round(percentil(valores, 95) * 1000),
            "muestras": len(valores),
        }
        for nombre, valores in tiempos.items()
    }
    (SALIDA / "linea_base.json").write_text(
        json.dumps(resumen, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"{'Operación':<26} {'mediana':>9} {'p95':>9}")
    for nombre, datos in resumen.items():
        print(f"{nombre:<26} {datos['mediana_ms']:>7} ms {datos['p95_ms']:>7} ms")
    return 0


if __name__ == "__main__":
    sys.exit(main())
