"""Una vuelta del reloj por minuto (`core.reloj`): la casilla, el resumen y la salud.

Lo corre `longbox-reloj.timer` en la VM. Correrlo de más no hace daño: cada tarea
mira si le toca.

La salida va en ASCII por la consola de Windows (ver `respaldar_base`).
"""

from django.core.management.base import BaseCommand

from apps.core import reloj
from apps.core.consola import ascii_seguro


class Command(BaseCommand):
    help = "Una vuelta del reloj por minuto: casilla, resumen de la manana y salud."

    def handle(self, *args, **opciones):
        for linea in reloj.tic():
            self.stdout.write(ascii_seguro(linea))
