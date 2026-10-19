"""`LotePuntos` y `MovimientoPuntos` (modelo de dominio, área 6; P-06).

El saldo de un Cliente **no es un atributo**: es la suma de `disponible` de sus
lotes Activos (I-18). Cada acreditación crea un lote con su caducidad, y cada
débito consume lotes en orden de caducidad más próxima.
"""

from django.conf import settings
from django.db import models
from django.db.models import F, Q
from django.utils import timezone


class LotePuntos(models.Model):
    COMPRA = "compra"
    REEMBOLSO = "reembolso"
    COMPENSACION = "compensacion"
    AJUSTE_MANUAL = "ajuste_manual"
    ORIGEN_CHOICES = [  # noqa: RUF012
        (COMPRA, "Compra"),
        (REEMBOLSO, "Reembolso"),
        (COMPENSACION, "Compensación"),
        (AJUSTE_MANUAL, "Ajuste manual"),
    ]

    ACTIVO = "activo"
    AGOTADO = "agotado"
    VENCIDO = "vencido"
    ESTADO_CHOICES = [  # noqa: RUF012
        (ACTIVO, "Activo"),
        (AGOTADO, "Agotado"),
        (VENCIDO, "Vencido"),
    ]

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="lotes_puntos"
    )
    cantidad_acreditada = models.PositiveIntegerField("cantidad acreditada")
    disponible = models.PositiveIntegerField("disponible")
    origen = models.CharField("origen", max_length=15, choices=ORIGEN_CHOICES)
    acreditado_en = models.DateTimeField("fecha de acreditación", default=timezone.now)
    caduca_el = models.DateField("fecha de caducidad")
    estado = models.CharField("estado", max_length=10, choices=ESTADO_CHOICES, default=ACTIVO)
    comprometido_en_canje = models.BooleanField("comprometido en canje", default=False)
    # Plan 10, segunda parte: el aviso previo a la caducidad sale una sola vez.
    aviso_caducidad = models.BooleanField("aviso previo enviado", default=False)

    class Meta:
        verbose_name = "lote de puntos"
        verbose_name_plural = "lotes de puntos"
        ordering = ["caduca_el", "pk"]  # noqa: RUF012
        constraints = [  # noqa: RUF012
            models.CheckConstraint(
                condition=Q(disponible__lte=F("cantidad_acreditada")),
                name="lote_disponible_no_supera_lo_acreditado",
            ),
            # Agotado si y sólo si no le queda nada (salvo que haya vencido).
            models.CheckConstraint(
                condition=Q(estado="vencido")
                | Q(estado="agotado", disponible=0)
                | (Q(estado="activo") & Q(disponible__gt=0)),
                name="lote_estado_coherente_con_disponible",
            ),
        ]

    def __str__(self):
        return f"{self.disponible}/{self.cantidad_acreditada} pts ({self.get_estado_display()})"


class MovimientoPuntos(models.Model):
    ACREDITACION = "acreditacion"
    DEBITO = "debito"
    TIPO_CHOICES = [  # noqa: RUF012
        (ACREDITACION, "Acreditación"),
        (DEBITO, "Débito"),
    ]

    # Derivable de los lotes, pero el historial del Cliente (CU-PTS-CON) se
    # consulta por cuenta y un movimiento sin lotes no tendría dueño.
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="movimientos_puntos"
    )
    lotes = models.ManyToManyField(LotePuntos, related_name="movimientos", blank=True)
    tipo = models.CharField("tipo", max_length=15, choices=TIPO_CHOICES)
    cantidad = models.PositiveIntegerField("cantidad")
    saldo_resultante = models.PositiveIntegerField("saldo resultante")
    motivo = models.CharField("motivo", max_length=300, blank=True)
    ocurrido_en = models.DateTimeField("ocurrido en", default=timezone.now)
    pedido = models.ForeignKey(
        "pedidos.Pedido",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="movimientos_puntos",
    )
    linea_pedido = models.ForeignKey(
        "pedidos.LineaPedido",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="movimientos_puntos",
    )
    caso_devolucion = models.ForeignKey(
        "devoluciones.CasoDevolucion",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="movimientos_puntos",
    )

    class Meta:
        verbose_name = "movimiento de puntos"
        verbose_name_plural = "movimientos de puntos"
        ordering = ["-ocurrido_en", "-pk"]  # noqa: RUF012
        constraints = [  # noqa: RUF012
            models.CheckConstraint(
                condition=Q(cantidad__gt=0), name="movimiento_cantidad_positiva"
            ),
        ]

    def __str__(self):
        return f"{self.get_tipo_display()} de {self.cantidad} pts"
