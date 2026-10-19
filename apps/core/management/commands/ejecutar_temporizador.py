"""El Temporizador del Sistema: la puerta unica de los procesos periodicos (P-05).

Corre el ciclo de vigencia de ofertas (`CO-059`), la vigilancia de la pre-venta
(`CO-011`, `CO-012`), el vencimiento de las ventanas de decision (`CO-096`), la
compensacion por demora (`CO-097`), el vencimiento del stock en local (`CO-154`)
la propuesta semanal de restock (`CO-067`), la caducidad de puntos (`CO-105`)
con su aviso previo, la sincronizacion de cotizaciones (`CO-155`) y el descarte
de los cobros abandonados (plan 00, C3), y el monitoreo de la casilla de
novedades (`CO-016`). Los otros que declara la especificacion
(los demas de P-05) se suman aca a medida que
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

from apps.almacen import servicios as almacen
from apps.catalog import ofertas
from apps.core import cotizaciones
from apps.pedidos import demora, preventa
from apps.puntos import caducidad
from apps.restock import servicios as restock
from apps.suppliers import casilla
from apps.tienda import compra


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


def ciclo_de_retencion():
    resultado = almacen.ciclo_de_vencimiento()
    return (
        f"stock en local: {len(resultado.avisados)} avisados, "
        f"{len(resultado.reintegrados)} devueltos al stock, {len(resultado.extendidos)} extendidos"
    )


def ciclo_de_restock():
    resultado = restock.ciclo_semanal()
    if resultado.propuesta:
        return "restock: propuesta generada"
    return f"restock: sin propuesta ({resultado.motivo})"


def ciclo_de_puntos():
    resultado = caducidad.ciclo()
    return (
        f"puntos: {len(resultado.vencidos)} lotes vencidos, {len(resultado.diferidos)} diferidos "
        f"por un canje, {len(resultado.incidentes)} con fallo, {len(resultado.avisados)} avisados"
    )


def ciclo_de_cotizaciones():
    catalogo = cotizaciones.sincronizar()
    if catalogo is None:
        return "cotizaciones: la API no respondio, queda el respaldo anterior"
    return f"cotizaciones: respaldo al {catalogo['fecha']}"


def ciclo_de_cobros():
    return f"cobros abandonados: {compra.descartar_abandonados()} descartados"


def ciclo_de_casilla():
    resultado = casilla.ciclo()
    if resultado.estado != "revisada":
        return f"casilla: {resultado.estado}"
    return (
        f"casilla: {len(resultado.ingresados)} a la cola, {resultado.repetidos} repetidos, "
        f"{resultado.descartados} sin ingresar"
    )


PROCESOS = (
    ciclo_de_ofertas,
    ciclo_de_preventa,
    ciclo_de_ventanas,
    ciclo_de_compensacion,
    ciclo_de_retencion,
    ciclo_de_restock,
    ciclo_de_puntos,
    ciclo_de_cotizaciones,
    ciclo_de_cobros,
    ciclo_de_casilla,
)


class Command(BaseCommand):
    help = "Corre los procesos periodicos del sistema (Temporizador, P-05)."

    def handle(self, *args, **opciones):
        for proceso in PROCESOS:
            self.stdout.write(proceso().encode("ascii", "replace").decode("ascii"))
