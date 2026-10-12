"""`CierreDeCaja` (modelo de dominio, área 5).

Consolida las transacciones aprobadas que todavía no entraron en un cierre, por
canal y por medio de pago. Uno por fecha de jornada (I-23): lo cobrado después
del cierre del día va al siguiente (B-14-001). Un cierre confirmado no cambia.
"""

from decimal import Decimal

from django.conf import settings
from django.db import models
from django.db.models import Q
from django.utils import timezone

CERO = Decimal("0")


def _importe(nombre):
    return models.DecimalField(nombre, max_digits=14, decimal_places=2, default=CERO)


class CierreDeCaja(models.Model):
    fecha_jornada = models.DateField("fecha de la jornada", unique=True)
    # Totales por canal y por medio: importes, no texto, para poder sumarlos.
    total_presencial = _importe("total presencial")
    total_online = _importe("total online")
    total_efectivo = _importe("total en efectivo")
    total_transferencia = _importe("total por transferencia")
    total_tarjeta = _importe("total con tarjeta")
    total_pasarela = _importe("total por pasarela")
    total_global = _importe("total global")
    transacciones_incluidas = models.PositiveIntegerField("transacciones incluidas", default=0)
    transacciones_excluidas = models.PositiveIntegerField("transacciones excluidas", default=0)
    realizado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="cierres_de_caja",
    )
    realizado_en = models.DateTimeField("realizado en", default=timezone.now)

    class Meta:
        verbose_name = "cierre de caja"
        verbose_name_plural = "cierres de caja"
        ordering = ["-fecha_jornada"]  # noqa: RUF012
        constraints = [  # noqa: RUF012
            models.CheckConstraint(
                condition=Q(total_global__gte=0)
                & Q(total_presencial__gte=0)
                & Q(total_online__gte=0),
                name="cierre_totales_no_negativos",
            ),
        ]

    def __str__(self):
        return f"Cierre del {self.fecha_jornada:%d/%m/%Y}"

    @property
    def por_canal(self):
        return [("Físico", self.total_presencial), ("Online", self.total_online)]

    @property
    def por_medio(self):
        return [
            ("Efectivo", self.total_efectivo),
            ("Transferencia", self.total_transferencia),
            ("Tarjeta", self.total_tarjeta),
            ("Pasarela", self.total_pasarela),
        ]
