"""Carga correos de proveedor desde archivos `.eml` de una carpeta.

Es la puerta de entrada a la cola mientras no exista la lectura de la casilla.
No es un andamio descartable: cuando el ciclo de IMAP exista va a invocar el
**mismo** `services.ingerir`, y este comando va a seguir sirviendo para cargar
un correo puntual que hubo que rescatar a mano, o para reproducir con un mensaje
real un problema que apareció en producción.
"""

from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from apps.core.consola import ascii_seguro
from apps.suppliers import services

# La consola de Windows corre en cp1252 y revienta con una flecha o un punto
# medio: `UnicodeEncodeError` al escribir, con el trabajo ya hecho y sin forma
# de saber cuánto se alcanzó a procesar. La salida de un comando de consola se
# mantiene en ASCII a propósito — el resto de la interfaz, que sale por HTTP en
# UTF-8, no tiene esta restricción.
FLECHA = "->"


class Command(BaseCommand):
    help = "Ingiere los archivos .eml de una carpeta y los deja en la cola de aprobación."

    def add_arguments(self, parser):
        parser.add_argument("carpeta", help="Carpeta con los archivos .eml a leer.")

    def handle(self, *args, **opciones):
        carpeta = Path(opciones["carpeta"])
        if not carpeta.is_dir():
            raise CommandError(f"No existe la carpeta «{carpeta}».")

        archivos = sorted(carpeta.glob("*.eml"))
        if not archivos:
            # No es un error: es el resultado normal de un ciclo sin novedades
            # (E6 de CU-04). Se informa y se termina sin generar nada.
            self.stdout.write("No hay archivos .eml en la carpeta. Nada que ingerir.")
            return

        conteo = {"ingresados": 0, "repetidos": 0, "descartados": 0}

        for archivo in archivos:
            resultado = services.ingerir(archivo.read_bytes(), nombre_archivo=archivo.name)

            if resultado.ingresado:
                conteo["ingresados"] += 1
                self.stdout.write(
                    # La razón social viene de una ficha que carga una persona:
                    # puede tener tildes, y el nombre del archivo también.
                    self.style.SUCCESS(
                        f"  + {ascii_seguro(archivo.name)} {FLECHA} "
                        f"{ascii_seguro(resultado.correo.proveedor)}"
                    )
                )
            elif resultado.motivo == services.MotivoDeDescarte.REPETIDO:
                conteo["repetidos"] += 1
                self.stdout.write(f"  = {ascii_seguro(archivo.name)} (ya estaba en la cola)")
            else:
                conteo["descartados"] += 1
                self.stdout.write(
                    self.style.WARNING(f"  - {ascii_seguro(archivo.name)} ({resultado.motivo})")
                )

        self.stdout.write("")
        self.stdout.write(
            f"{conteo['ingresados']} ingresados, {conteo['repetidos']} repetidos, "
            f"{conteo['descartados']} sin ingresar"
        )
