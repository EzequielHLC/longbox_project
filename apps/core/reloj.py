"""El reloj por minuto: lo que no puede esperar al Temporizador diario (B-19-011).

Cada minuto, cada tarea mira primero si le toca y, si no, sale sin hacer nada:

- la casilla de novedades, según la frecuencia de Parámetros (`CO-016`, B-04-015);
- el resumen de la mañana, si ya es la hora y hoy no salió (`CU-AVI-RES`);
- los controles de salud, un aviso por día y por problema (`CU-AVI-EST`).

En la VM lo dispara `longbox-reloj.timer` con `manage.py cada_minuto`; en esta PC,
`manage.py telegram escuchar` entre una consulta y otra. **Una tarea que falla no
frena a las demás.**
"""

import logging

logger = logging.getLogger(__name__)


def _casilla():
    from apps.suppliers import casilla

    resumen = casilla.ciclo()
    if resumen.estado != "revisada":
        return f"casilla: {resumen.estado}"
    return f"casilla: {len(resumen.ingresados)} correo(s) nuevo(s)"


def _resumen():
    from apps.avisos import resumen

    return f"resumen: {resumen.si_corresponde().estado}"


def _salud():
    from apps.avisos import salud

    avisados = salud.controlar()
    return f"salud: {', '.join(avisados) if avisados else 'sin avisos'}"


TAREAS = (("casilla", _casilla), ("resumen", _resumen), ("salud", _salud))


def tic():
    """Una vuelta. Devuelve una línea por tarea, para la consola."""
    lineas = []
    for nombre, tarea in TAREAS:
        try:
            lineas.append(tarea())
        except Exception:  # noqa: BLE001 - una tarea caída no frena a las demás
            logger.exception("Falló la tarea «%s» del reloj por minuto.", nombre)
            lineas.append(f"{nombre}: falló")
    return lineas
