"""El Temporizador del Sistema: la puerta unica de los procesos periodicos (P-05).

Corre el ciclo de vigencia de ofertas (`CO-059`), la vigilancia de la pre-venta
(`CO-011`, `CO-012`), el vencimiento de las ventanas de decision (`CO-096`) y la
compensacion por demora (`CO-097`). Los otros que declara la especificacion
(`CO-016`, `CO-155`, `CU-PTS-CAD` y los demas de P-05) se suman aca a medida que
existan, cada uno como una funcion mas en `PROCESOS`.

Correrlo dos veces el mismo dia no hace dano: cada proceso mira el estado
guardado y solo toca lo que todavia no se actualizo.

Se ejecuta al arrancar `demostracion.bat`, y en una instalacion que queda
encendida se programa una vez por dia en el Programador de tareas de Windows
(`docs/despliegue/DEMOSTRACION.md`). Aunque no corra, una oferta empieza y
termina a tiempo: el precio visible se calcula con las fechas. Lo que espera al
Temporizador es el estado guardado y la entrada de auditoria del vencimiento.

La salida va en ASCII por la consola de Windows (ver `respaldar_base`).
"""

from django.core.management.base import BaseCommand

from apps.catalog import ofertas
from apps.pedidos import demora, preventa


def ciclo_de_ofertas():
    resultado = ofertas.ejecutar_ciclo()
    return f"ofertas: {len(resultado.activadas)} activadas, {len(resultado.vencidas)} vencidas"


def ciclo_de_preventa():
    resultado = preventa.ciclo_de_vigilancia()
    return (
        f"pre-venta: {len(resultado.proximas)} proximas, {len(resultado.de_hoy)} para hoy, "
        f"{len(resultado.escaladas)} escaladas"
    )


def ciclo_de_ventanas():
    return f"ventanas de decision: {len(demora.ciclo_de_ventanas())} vencidas"


def ciclo_de_compensacion():
    return f"compensacion por demora: {len(demora.ciclo_de_compensacion())} acreditadas"


PROCESOS = (ciclo_de_ofertas, ciclo_de_preventa, ciclo_de_ventanas, ciclo_de_compensacion)


class Command(BaseCommand):
    help = "Corre los procesos periodicos del sistema (Temporizador, P-05)."

    def handle(self, *args, **opciones):
        for proceso in PROCESOS:
            self.stdout.write(proceso().encode("ascii", "replace").decode("ascii"))
