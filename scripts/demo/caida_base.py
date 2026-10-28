"""D6-04 · La base de datos se cae con el servidor andando, y vuelve.

    python scripts/demo/caida_base.py

Contra el servidor de la demostración (`https://127.0.0.1:8443`) y el contenedor
`longbox-demo-db`. Pasos, con lo que tiene que pasar en cada uno:

1. Con la base arriba, el catálogo responde 200.
2. Se detiene el contenedor (`docker stop`). El catálogo responde **500 con la
   página genérica**: sin traza, sin nombres de tablas, sin la configuración.
3. Se vuelve a levantar el contenedor. **Sin reiniciar la aplicación**, el
   catálogo vuelve a responder 200 (la aplicación no reutiliza conexiones:
   `CONN_MAX_AGE` es 0, así que cada pedido abre una nueva).

Se mide cuánto tarda en volver después de levantar la base.
"""

import subprocess  # nosec B404 - docker con argumentos fijos
import sys
import time

import requests
from entorno import AUTORIDAD_LOCAL, CONTENEDOR, DIRECCION

URL = f"{DIRECCION}/tienda/catalogo/"
DELATORES = [
    "Traceback",
    "psycopg2",
    "OperationalError",
    "SELECT ",
    "DATABASES",
    "SECRET_KEY",
    "settings",
]


def docker(*argumentos):
    subprocess.run(  # nosec B603 B607 - docker con argumentos fijos, sin shell
        ["docker", *argumentos], check=True, capture_output=True
    )


def pedir():
    try:
        respuesta = requests.get(URL, verify=AUTORIDAD_LOCAL, timeout=20)
    except requests.RequestException as error:
        return None, f"sin respuesta: {type(error).__name__}"
    return respuesta.status_code, respuesta.text


def main():
    ok = True
    codigo, _ = pedir()
    print(f"1. Base arriba: catálogo {codigo}")
    ok &= codigo == 200

    print("2. Se detiene la base (docker stop)...")
    docker("stop", CONTENEDOR)
    codigo, cuerpo = pedir()
    delata = [palabra for palabra in DELATORES if cuerpo and palabra in cuerpo]
    print(f"   catálogo {codigo}, {len(cuerpo or '')} bytes, delata: {delata or 'nada'}")
    print(f"   cuerpo: {(cuerpo or '').strip()[:120]!r}")
    ok &= codigo == 500 and not delata

    print("3. Se levanta la base (docker start), sin tocar la aplicación...")
    docker("start", CONTENEDOR)
    inicio = time.perf_counter()
    codigo = None
    while time.perf_counter() - inicio < 60:
        codigo, _ = pedir()
        if codigo == 200:
            break
        time.sleep(0.5)
    print(f"   catálogo {codigo} a los {time.perf_counter() - inicio:.1f} s")
    ok &= codigo == 200

    print("Resultado:", "OK" if ok else "FALLA")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
