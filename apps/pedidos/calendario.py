"""El calendario de las pre-ventas por llegar (plan 00 de interfaz, 22).

Se arma con los mismos grupos de `preventa.por_llegar()` —fecha de llegada
vigente y editorial—, así que el calendario no puede decir otra cosa que la
lista de abajo. Un mes empieza en lunes y trae los días de los meses vecinos
que completan sus semanas.
"""

import calendar
from dataclasses import dataclass, field
from datetime import date, timedelta

from django.utils import timezone

DIAS_DE_LA_SEMANA = ("Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom")
MESES = (
    "enero",
    "febrero",
    "marzo",
    "abril",
    "mayo",
    "junio",
    "julio",
    "agosto",
    "septiembre",
    "octubre",
    "noviembre",
    "diciembre",
)


@dataclass
class Dia:
    fecha: date
    del_mes: bool
    es_hoy: bool
    grupos: list = field(default_factory=list)

    @property
    def atrasado(self):
        return any(grupo.vencido for grupo in self.grupos)


@dataclass
class Mes:
    primero: date
    semanas: list

    @property
    def nombre(self):
        return f"{MESES[self.primero.month - 1].capitalize()} {self.primero.year}"

    @property
    def anterior(self):
        return (self.primero - timedelta(days=1)).replace(day=1)

    @property
    def siguiente(self):
        return (self.primero + timedelta(days=31)).replace(day=1)

    @property
    def dias_con_llegadas(self):
        return [dia for semana in self.semanas for dia in semana if dia.del_mes and dia.grupos]


def mes_pedido(texto):
    """`2026-11` → el primer día de ese mes; lo que no se entiende, el mes actual."""
    try:
        anio, mes = (int(parte) for parte in str(texto).split("-"))
        return date(anio, mes, 1)
    except (TypeError, ValueError):
        return timezone.localdate().replace(day=1)


def mes_de(primero, grupos):
    hoy = timezone.localdate()
    por_fecha = {}
    for grupo in grupos:
        if grupo.llegada is not None:
            por_fecha.setdefault(grupo.llegada, []).append(grupo)
    semanas = [
        [
            Dia(
                fecha=fecha,
                del_mes=fecha.month == primero.month,
                es_hoy=fecha == hoy,
                grupos=por_fecha.get(fecha, []),
            )
            for fecha in semana
        ]
        for semana in calendar.Calendar(firstweekday=0).monthdatescalendar(
            primero.year, primero.month
        )
    ]
    return Mes(primero=primero, semanas=semanas)


def resumen(grupos):
    """Las cifras de arriba: el tamaño de lo que viene antes de recorrerlo."""
    hoy = timezone.localdate()
    filas = [fila for grupo in grupos for fila in grupo.filas]
    return {
        "productos": len(filas),
        "reservadas": sum(fila.reservadas for fila in filas),
        "esta_semana": sum(
            1 for fila in filas if fila.llegada and hoy <= fila.llegada <= hoy + timedelta(days=7)
        ),
        "atrasados": sum(1 for fila in filas if fila.llegada and fila.llegada < hoy),
    }
