"""Revisa la casilla de novedades ahora, sin esperar la frecuencia (`CO-016`).

Es el mismo ciclo del Temporizador —`casilla.ciclo`—, con la frecuencia de
Parámetros salteada: deja en la cola lo que haya llegado y no procesa nada.
Sirve para la demostración, después de mandar un correo con
`scripts/demo/redactar_correo.py` (plan 00 del circuito con los proveedores, H).

Con `--si-corresponde` respeta la frecuencia, como la casilla dentro del reloj por
minuto (`cada_minuto`; B-04-015, B-19-011): no conecta si no pasó el tiempo.
"""

from django.core.management.base import BaseCommand

from apps.core.consola import ascii_seguro
from apps.suppliers import casilla


class Command(BaseCommand):
    help = "Revisa la casilla de novedades ahora y deja lo nuevo en la cola (CO-016)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--si-corresponde",
            action="store_true",
            help="Respetar la frecuencia de Parámetros (lo que corre la VM cada minuto).",
        )

    def handle(self, *args, si_corresponde=False, **opciones):
        resumen = casilla.ciclo(forzar=not si_corresponde)
        if resumen.estado != "revisada":
            self.stdout.write(ascii_seguro(f"Casilla {resumen.estado}."))
            return
        self.stdout.write(
            ascii_seguro(
                f"Casilla revisada: {len(resumen.ingresados)} a la cola, "
                f"{resumen.repetidos} repetidos, {resumen.descartados} sin ingresar."
            )
        )
        for correo in resumen.ingresados:
            self.stdout.write(ascii_seguro(f"  - {correo.proveedor}: {correo.asunto}"))
