"""Respaldo de la base de datos, pensado para correr solo.

Tres decisiones que conviene tener a la vista, porque son las que separan un
respaldo de un archivo que parece un respaldo:

1. **Se verifica antes de darlo por bueno.** `pg_dump` puede terminar con codigo
   0 y dejar un archivo truncado si se corta el disco o la conexion. Cada
   respaldo se relee con `pg_restore --list` antes de contarlo, y si no se puede
   leer se descarta. Un respaldo que nadie abrio hasta el dia que hace falta no
   es un respaldo, es una esperanza.

2. **La contrasena viaja por el entorno, no por la linea de comandos.** Los
   argumentos de un proceso los ve cualquiera que liste procesos en la maquina.

3. **`pg_dump` tiene que ser de la misma version mayor que el servidor, o mas
   nueva.** Uno viejo se niega a volcar una base nueva, y es el error que
   aparece justo cuando hace falta el respaldo. En esta maquina la variable PATH
   apunta a PostgreSQL 16 y el servidor es 18, asi que la busqueda del
   ejecutable no es un lujo: sin ella el comando no corre.

La salida va en ASCII a proposito: la consola de Windows corre en cp1252 y una
flecha o un acento la hacen reventar con `UnicodeEncodeError`, con el trabajo ya
hecho y sin saber cuanto se proceso.
"""

import os
import re
import shutil
import subprocess  # nosec B404 - se invoca pg_dump con lista de argumentos, sin shell
from datetime import datetime
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import connection

# Donde Windows instala PostgreSQL. Se recorren de mayor a menor version para
# quedarse con el pg_dump mas nuevo, que es el que sirve para cualquier servidor
# igual o mas viejo.
CARPETAS_WINDOWS = Path("C:/Program Files/PostgreSQL")

# El nombre ordena alfabeticamente igual que cronologicamente, que es lo que
# hace que la limpieza por antiguedad sea un `sorted()` y no una fecha extraida
# del nombre del archivo.
PATRON = "longbox-%Y%m%d-%H%M%S.dump"
RECONOCE = re.compile(r"^longbox-\d{8}-\d{6}\.dump$")


def ubicar(programa):
    """Donde esta `pg_dump` o `pg_restore`, o `None`.

    Primero el PATH, que es lo correcto en un servidor. Si ahi no esta, se
    recorren las instalaciones de Windows de mayor a menor version.
    """
    hallado = shutil.which(programa)
    if hallado:
        return Path(hallado)

    if not CARPETAS_WINDOWS.is_dir():
        return None

    versiones = sorted(
        (c for c in CARPETAS_WINDOWS.iterdir() if c.name.isdigit()),
        key=lambda c: int(c.name),
        reverse=True,
    )
    for carpeta in versiones:
        candidato = carpeta / "bin" / f"{programa}.exe"
        if candidato.is_file():
            return candidato
    return None


def version_mayor(ejecutable):
    """La version mayor que declara el ejecutable, o `None` si no se entiende."""
    try:
        salida = subprocess.run(  # nosec B603 - ruta resuelta por `ubicar`, sin shell
            [str(ejecutable), "--version"],
            capture_output=True,
            text=True,
            timeout=30,
            check=True,
        ).stdout
    except (subprocess.SubprocessError, OSError):
        return None
    encontrado = re.search(r"(\d+)\.", salida)
    return int(encontrado.group(1)) if encontrado else None


def _correr(orden, entorno=None):
    """Un proceso externo del que interesan codigo, salida y error."""
    return subprocess.run(  # nosec B603 - rutas resueltas por `ubicar`, sin shell
        [str(parte) for parte in orden],
        capture_output=True,
        text=True,
        env=entorno,
        check=False,
    )


class Command(BaseCommand):
    help = "Genera un respaldo comprimido de la base y borra los mas viejos."

    def add_arguments(self, parser):
        parser.add_argument(
            "--destino",
            default=None,
            help="Carpeta donde dejar los respaldos. Por defecto, RESPALDOS_DIR.",
        )
        parser.add_argument(
            "--conservar",
            type=int,
            default=7,
            help="Cuantos respaldos dejar. Los mas viejos se borran. 0 no borra ninguno.",
        )
        parser.add_argument(
            "--verificar-solo",
            action="store_true",
            help="No respalda: revisa que los respaldos existentes se puedan leer.",
        )

    def handle(self, *opciones, **argumentos):
        destino = Path(argumentos["destino"] or settings.RESPALDOS_DIR)
        destino.mkdir(parents=True, exist_ok=True)

        restaurador = ubicar("pg_restore")
        if restaurador is None:
            raise CommandError("No se encontro pg_restore. Sin el no se puede verificar nada.")

        if argumentos["verificar_solo"]:
            self._revisar_los_existentes(destino, restaurador)
            return

        archivo = self._volcar(destino)
        self._verificar(archivo, restaurador)
        self.stdout.write(f"OK  {archivo.name}  ({archivo.stat().st_size // 1024} KB)")
        self._limpiar(destino, argumentos["conservar"])

    # -- el volcado ---------------------------------------------------------

    def _volcar(self, destino):
        volcador = ubicar("pg_dump")
        if volcador is None:
            raise CommandError(
                "No se encontro pg_dump. Agregue la carpeta bin de PostgreSQL al PATH."
            )

        del_servidor = connection.cursor().connection.info.server_version // 10000
        de_la_herramienta = version_mayor(volcador)
        if de_la_herramienta is not None and de_la_herramienta < del_servidor:
            raise CommandError(
                f"pg_dump es version {de_la_herramienta} y el servidor es {del_servidor}. "
                "Uno mas viejo que el servidor se niega a volcar la base."
            )

        base = settings.DATABASES["default"]
        archivo = destino / datetime.now().strftime(PATRON)

        # `--format=custom` es el formato propio de PostgreSQL: viene comprimido
        # y permite restaurar una sola tabla, cosa que un `.sql` plano no
        # permite. `--no-password` evita que el proceso se quede esperando una
        # contrasena por teclado que en una tarea programada no va a llegar
        # nunca: sin eso, un respaldo mal configurado no falla, se cuelga.
        orden = [
            volcador,
            "--format=custom",
            "--no-password",
            f"--host={base['HOST']}",
            f"--port={base['PORT']}",
            f"--username={base['USER']}",
            f"--file={archivo}",
            base["NAME"],
        ]

        # La contrasena por entorno: los argumentos de un proceso los lee
        # cualquiera que liste procesos en la maquina.
        resultado = _correr(orden, entorno={**os.environ, "PGPASSWORD": base["PASSWORD"]})
        if resultado.returncode != 0:
            archivo.unlink(missing_ok=True)
            raise CommandError(f"pg_dump fallo: {resultado.stderr.strip()}")
        return archivo

    # -- la verificacion ----------------------------------------------------

    def _legible(self, archivo, restaurador):
        resultado = _correr([restaurador, "--list", archivo])
        return resultado.returncode == 0 and bool(resultado.stdout.strip()), resultado.stderr

    def _verificar(self, archivo, restaurador):
        """Relee el respaldo recien hecho. Es lo que lo distingue de un archivo."""
        anduvo, error = self._legible(archivo, restaurador)
        if not anduvo:
            archivo.unlink(missing_ok=True)
            raise CommandError(f"El respaldo no se puede leer y se descarto: {error.strip()}")

    def _revisar_los_existentes(self, destino, restaurador):
        respaldos = self._listar(destino)
        if not respaldos:
            self.stdout.write("No hay respaldos en la carpeta.")
            return

        rotos = 0
        for archivo in respaldos:
            anduvo, _ = self._legible(archivo, restaurador)
            self.stdout.write(f"{'OK  ' if anduvo else 'ROTO'}  {archivo.name}")
            rotos += 0 if anduvo else 1
        if rotos:
            raise CommandError(f"{rotos} respaldo(s) ilegibles.")

    # -- la limpieza --------------------------------------------------------

    def _listar(self, destino):
        """Los respaldos de la carpeta, del mas viejo al mas nuevo.

        Se filtra por el patron del nombre y no por la extension: la carpeta
        puede tener cualquier otra cosa, y borrar por antiguedad algo que uno no
        genero es la peor forma de fallar que tiene un limpiador.
        """
        return sorted(a for a in destino.iterdir() if a.is_file() and RECONOCE.match(a.name))

    def _limpiar(self, destino, conservar):
        if conservar <= 0:
            return
        for archivo in self._listar(destino)[:-conservar]:
            archivo.unlink()
            self.stdout.write(f"Borrado por antiguedad: {archivo.name}")
