"""Deja una base de desarrollo limpia para una presentación, con el catálogo real de Ivrea.

    python scripts/demo/presentacion.py --confirmar

**No borra la base actual.** Crea una nueva, `longbox_presentacion`, y apunta el
`.env` a ella. La vieja queda intacta: volver atrás es cambiar `DB_NAME` en el
`.env`. Pasos:

1. Exporta de la base actual lo que se conserva: las cuentas `admin@correo.com`,
   `cajero@correo.com` y `cliente@correo.com` (con sus contraseñas de siempre),
   la identidad visual y los parámetros.
2. Respalda la base actual con `manage.py respaldar_base` en `respaldos/`.
3. Crea la base nueva, cambia `DB_NAME` en el `.env` y la migra.
4. Mueve `media/` a `respaldos/presentacion-<fecha>/media`: la base nueva arranca
   sin los archivos de la vieja.
5. Carga lo conservado y el catálogo de Ivrea (`presentacion_carga.py`).

Requiere el Excel y las portadas de `raspar_ivrea.py` en `scripts/demo/datos/`.
"""

import argparse
import re
import shutil
import subprocess  # nosec B404 - manage.py y el cargador, con argumentos fijos
import sys
from datetime import datetime
from pathlib import Path

import psycopg2
from decouple import Config, RepositoryEnv

RAIZ = Path(__file__).resolve().parents[2]
AQUI = Path(__file__).resolve().parent
ENV = RAIZ / ".env"
NUEVA = "longbox_presentacion"


def correr(*argumentos, base):
    """Corre un comando de Python con la base indicada, sin tocar el resto del entorno."""
    import os

    entorno = {
        **os.environ,
        "DB_NAME": base,
        "DJANGO_SETTINGS_MODULE": "config.settings.development",
        "PYTHONIOENCODING": "utf-8",
    }
    subprocess.run(  # nosec B603 - manage.py y el cargador, sin shell
        [sys.executable, *map(str, argumentos)], cwd=RAIZ, env=entorno, check=True
    )


def main():
    opciones = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    opciones.add_argument("--confirmar", action="store_true", help="Hace falta para correr.")
    opciones.add_argument(
        "--reemplazar", action="store_true", help="Recrear la base nueva si ya existe."
    )
    argumentos = opciones.parse_args()
    if not argumentos.confirmar:
        raise SystemExit(
            "Revisá lo que hace (python scripts/demo/presentacion.py -h) y agregá --confirmar."
        )

    config = Config(RepositoryEnv(str(ENV)))
    vieja = config("DB_NAME")
    if vieja == NUEVA and not argumentos.reemplazar:
        raise SystemExit(f"El .env ya apunta a {NUEVA}. Para rehacerla: --reemplazar")
    origen = vieja if vieja != NUEVA else config("DB_NAME_ANTERIOR", default="longbox_db")

    carpeta = RAIZ / "respaldos" / f"presentacion-{datetime.now():%Y%m%d-%H%M}"
    carpeta.mkdir(parents=True, exist_ok=True)
    conservado = carpeta / "conservado.json"

    print(f"1. Exportando lo que se conserva de {origen}…")
    correr(AQUI / "presentacion_carga.py", "exportar", conservado, base=origen)

    print(f"2. Respaldando {origen}…")
    correr(
        RAIZ / "manage.py", "respaldar_base", "--destino", carpeta, "--conservar", "0", base=origen
    )

    print(f"3. Creando {NUEVA} y migrándola…")
    conexion = psycopg2.connect(
        dbname="postgres",
        user=config("DB_USER"),
        password=config("DB_PASSWORD"),
        host=config("DB_HOST"),
        port=config("DB_PORT"),
    )
    conexion.autocommit = True
    cursor = conexion.cursor()
    cursor.execute("SELECT 1 FROM pg_database WHERE datname = %s", [NUEVA])
    if cursor.fetchone():
        if not argumentos.reemplazar:
            raise SystemExit(f"{NUEVA} ya existe. Para rehacerla: --reemplazar")
        cursor.execute(
            "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = %s", [NUEVA]
        )
        cursor.execute(f'DROP DATABASE "{NUEVA}"')  # nosec B608 - nombre fijo
    cursor.execute(f'CREATE DATABASE "{NUEVA}"')  # nosec B608 - nombre fijo
    conexion.close()

    texto = ENV.read_text(encoding="utf-8")
    texto = re.sub(r"(?m)^DB_NAME=.*$", f"DB_NAME={NUEVA}", texto, count=1)
    if "DB_NAME_ANTERIOR" not in texto:
        texto = texto.replace(
            f"DB_NAME={NUEVA}",
            f"DB_NAME={NUEVA}\n"
            f"# La base de antes de la limpieza (presentacion.py). Volver: DB_NAME={origen}\n"
            f"DB_NAME_ANTERIOR={origen}",
            1,
        )
    ENV.write_text(texto, encoding="utf-8")
    correr(RAIZ / "manage.py", "migrate", "--verbosity", "0", base=NUEVA)

    print("4. Guardando media/ aparte…")
    if (RAIZ / "media").exists():
        shutil.move(str(RAIZ / "media"), str(carpeta / "media"))

    print("5. Cargando el catálogo de Ivrea…")
    correr(AQUI / "presentacion_carga.py", "cargar", conservado, base=NUEVA)
    print(f"Listo. Respaldo de lo anterior en {carpeta}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
