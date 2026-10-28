"""Vuelve `longbox_demo` al punto de partida en un comando (plan 00, apartado 2).

    python scripts/demo/restaurar.py --guardar     # una vez, con la base ya poblada
    python scripts/demo/restaurar.py               # antes de la demostración y entre actos

La instantánea es una **base plantilla** dentro del mismo contenedor,
`longbox_demo_base`. Restaurar es borrar `longbox_demo` y crearla de nuevo
`TEMPLATE longbox_demo_base`: PostgreSQL copia los archivos de la base, sin
volver a ejecutar ningún INSERT, y por eso tarda segundos y no minutos.

Los archivos subidos (portadas, correos archivados, banners) se copian aparte,
de `datos/media` a `datos/media_base` y de vuelta.

Antes de restaurar hay que detener `servir`: PostgreSQL no copia una base con
conexiones abiertas. Las que queden se cortan.
"""

import argparse
import shutil
import sys
import time
from pathlib import Path

import psycopg2
from entorno import ENTORNO, preparar

RAIZ_DATOS = Path(__file__).resolve().parent / "datos"
MEDIA = RAIZ_DATOS / "media"
MEDIA_BASE = RAIZ_DATOS / "media_base"
BASE = ENTORNO["DB_NAME"]
PLANTILLA = f"{BASE}_base"


def conectar():
    """A la base `postgres` del contenedor: no se borra la base a la que uno está conectado."""
    conexion = psycopg2.connect(
        dbname="postgres",
        user=ENTORNO["DB_USER"],
        password=ENTORNO["DB_PASSWORD"],
        host=ENTORNO["DB_HOST"],
        port=ENTORNO["DB_PORT"],
    )
    conexion.autocommit = True
    return conexion


def cortar_conexiones(cursor, base):
    cursor.execute(
        "SELECT pg_terminate_backend(pid) FROM pg_stat_activity "
        "WHERE datname = %s AND pid <> pg_backend_pid()",
        [base],
    )


def copiar(cursor, *, desde, hacia):
    cortar_conexiones(cursor, desde)
    cortar_conexiones(cursor, hacia)
    cursor.execute(f'DROP DATABASE IF EXISTS "{hacia}"')  # nosec B608 - nombres fijos
    cursor.execute(f'CREATE DATABASE "{hacia}" TEMPLATE "{desde}"')  # nosec B608 - nombres fijos


def main():
    argumentos = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    argumentos.add_argument("--guardar", action="store_true", help="Tomar la instantánea.")
    argumentos.add_argument(
        "--vaciar", action="store_true", help="Recrear longbox_demo vacía (después: migrate)."
    )
    opciones = argumentos.parse_args()

    # Verifica que el entorno apunte a la base de la demostración.
    preparar(django_setup=False)
    if BASE != "longbox_demo":
        raise SystemExit("Sólo se restaura longbox_demo.")

    inicio = time.perf_counter()
    # Sin `with` sobre la conexión: abriría una transacción, y CREATE DATABASE
    # no corre dentro de una.
    conexion = conectar()
    try:
        cursor = conexion.cursor()
        if opciones.vaciar:
            cortar_conexiones(cursor, BASE)
            cursor.execute(f'DROP DATABASE IF EXISTS "{BASE}"')  # nosec B608 - nombre fijo
            cursor.execute(f'CREATE DATABASE "{BASE}"')  # nosec B608 - nombre fijo
            shutil.rmtree(MEDIA, ignore_errors=True)
            accion = "Base vaciada"
        elif opciones.guardar:
            copiar(cursor, desde=BASE, hacia=PLANTILLA)
            if MEDIA.exists():
                shutil.rmtree(MEDIA_BASE, ignore_errors=True)
                shutil.copytree(MEDIA, MEDIA_BASE)
            accion = "Instantánea guardada"
        else:
            cursor.execute("SELECT 1 FROM pg_database WHERE datname = %s", [PLANTILLA])
            if cursor.fetchone() is None:
                raise SystemExit("No hay instantánea. Corré primero: restaurar.py --guardar")
            copiar(cursor, desde=PLANTILLA, hacia=BASE)
            shutil.rmtree(MEDIA, ignore_errors=True)
            if MEDIA_BASE.exists():
                shutil.copytree(MEDIA_BASE, MEDIA)
            accion = "Base restaurada"
    finally:
        conexion.close()
    print(f"{accion} en {time.perf_counter() - inicio:.1f} s")


if __name__ == "__main__":
    sys.exit(main())
