"""D6-06 · Respaldo y restauración, según `docs/despliegue/RESPALDOS.md`.

    python scripts/demo/respaldo.py

1. `manage.py respaldar_base` sobre `longbox_demo` (el comando del sistema, que
   verifica el archivo con `pg_restore --list` antes de darlo por bueno).
2. Se crea una base vacía, `longbox_restaurada`, en el mismo contenedor.
3. Se restaura el respaldo en ella con `pg_restore`.
4. Se compara el número de filas de **cada tabla** entre las dos bases.

Éxito: todas las tablas con el mismo recuento. La base restaurada se borra al
terminar.
"""

import subprocess  # nosec B404 - pg_restore y manage.py con argumentos fijos
import sys
import time

import psycopg2
from entorno import ENTORNO, RAIZ, SALIDA, entorno_para_subproceso, preparar

RESTAURADA = "longbox_restaurada"
DESTINO = SALIDA / "respaldos"


def conectar(base):
    conexion = psycopg2.connect(
        dbname=base,
        user=ENTORNO["DB_USER"],
        password=ENTORNO["DB_PASSWORD"],
        host=ENTORNO["DB_HOST"],
        port=ENTORNO["DB_PORT"],
    )
    conexion.autocommit = True
    return conexion


def recuentos(base):
    conexion = conectar(base)
    try:
        cursor = conexion.cursor()
        cursor.execute(
            "SELECT tablename FROM pg_tables WHERE schemaname = 'public' ORDER BY tablename"
        )
        tablas = [fila[0] for fila in cursor.fetchall()]
        salida = {}
        for tabla in tablas:
            cursor.execute(f'SELECT count(*) FROM "{tabla}"')  # nosec B608 - nombres del catálogo
            salida[tabla] = cursor.fetchone()[0]
        return salida
    finally:
        conexion.close()


def main():
    preparar()
    from apps.core.management.commands.respaldar_base import ubicar

    DESTINO.mkdir(parents=True, exist_ok=True)
    inicio = time.perf_counter()
    subprocess.run(  # nosec B603
        [
            sys.executable,
            str(RAIZ / "manage.py"),
            "respaldar_base",
            "--destino",
            str(DESTINO),
            "--conservar",
            "0",
        ],
        env=entorno_para_subproceso(),
        cwd=RAIZ,
        check=True,
    )
    respaldo = max(DESTINO.glob("*.dump"), key=lambda archivo: archivo.stat().st_mtime)
    megas = respaldo.stat().st_size / 1024 / 1024
    print(f"1. Respaldo: {respaldo.name} ({megas:.1f} MB) en {time.perf_counter() - inicio:.1f} s")

    administracion = conectar("postgres")
    cursor = administracion.cursor()
    cursor.execute(f'DROP DATABASE IF EXISTS "{RESTAURADA}"')  # nosec B608 - nombre fijo
    cursor.execute(f'CREATE DATABASE "{RESTAURADA}"')  # nosec B608
    print(f"2. Base vacía creada: {RESTAURADA}")

    inicio = time.perf_counter()
    pg_restore = ubicar("pg_restore")
    subprocess.run(  # nosec B603
        [
            str(pg_restore),
            "--no-owner",
            "--dbname",
            RESTAURADA,
            "--host",
            ENTORNO["DB_HOST"],
            "--port",
            ENTORNO["DB_PORT"],
            "--username",
            ENTORNO["DB_USER"],
            str(respaldo),
        ],
        env={**entorno_para_subproceso(), "PGPASSWORD": ENTORNO["DB_PASSWORD"]},
        check=True,
    )
    print(f"3. Restaurado en {time.perf_counter() - inicio:.1f} s")

    original, restaurada = recuentos(ENTORNO["DB_NAME"]), recuentos(RESTAURADA)
    distintas = {
        tabla: (original.get(tabla), restaurada.get(tabla))
        for tabla in set(original) | set(restaurada)
        if original.get(tabla) != restaurada.get(tabla)
    }
    filas = sum(original.values())
    print(f"4. {len(original)} tablas, {filas} filas en total; distintas: {distintas or 'ninguna'}")
    for tabla in (
        "catalog_producto",
        "accounts_usuario",
        "core_registroauditoria",
        "suppliers_correoproveedor",
    ):
        print(f"   {tabla}: {original.get(tabla)} → {restaurada.get(tabla)}")

    cursor.execute(f'DROP DATABASE IF EXISTS "{RESTAURADA}"')  # nosec B608
    administracion.close()
    print("Resultado:", "OK" if not distintas else "FALLA")
    return 0 if not distintas else 1


if __name__ == "__main__":
    sys.exit(main())
