"""`Carrito` y `LineaCarrito` (modelo de dominio, área 5).

El carrito es una selección sin compromiso: no reserva stock y sus operaciones
no se auditan (`CU-TDA-CRC`, Comentarios).
"""

from django.conf import settings
from django.db import models
from django.utils import timezone

from apps.catalog.models import POSITIVO, Producto


class Carrito(models.Model):
    """La selección de un Cliente, o la de un invitado mientras dura su sesión.

    El de invitado no tiene usuario: se ubica por el identificador que guarda su
    sesión (`apps.tienda.carrito.CLAVE_DE_SESION`), y muere con ella (plan 07,
    segunda parte, ambigüedad 4).
    """

    DE_SESION = "de_sesion"
    PERSISTENTE = "persistente"
    PERSISTENCIA_CHOICES = [  # noqa: RUF012
        (DE_SESION, "De sesión"),
        (PERSISTENTE, "Persistente"),
    ]

    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="carrito",
    )
    persistencia = models.CharField(
        "persistencia", max_length=12, choices=PERSISTENCIA_CHOICES, default=DE_SESION
    )
    actualizado_en = models.DateTimeField("actualizado en", default=timezone.now)
    creado_en = models.DateTimeField("creado en", auto_now_add=True)

    class Meta:
        verbose_name = "carrito"
        verbose_name_plural = "carritos"
        constraints = [  # noqa: RUF012
            # Persistente si y sólo si tiene dueño: un carrito de invitado con
            # usuario, o uno persistente sin él, no lo produce ningún contrato.
            models.CheckConstraint(
                condition=(
                    models.Q(persistencia="persistente", usuario__isnull=False)
                    | models.Q(persistencia="de_sesion", usuario__isnull=True)
                ),
                name="carrito_persistente_si_tiene_usuario",
            ),
        ]

    def __str__(self):
        return f"Carrito de {self.usuario}" if self.usuario_id else f"Carrito de sesión {self.pk}"


class LineaCarrito(models.Model):
    """Un producto del carrito, con su cantidad y dos importes (B-07-003).

    `precio_vigente` es el del contrato: la propagación de precios lo actualiza
    (`CO-048`, `CO-053` y las ofertas). `precio_visto` es el que el Cliente tenía
    a la vista la última vez que tocó la línea; cuando difiere del precio actual,
    la consulta avisa que el precio cambió (`CU-TDA-CRC` A2).
    """

    carrito = models.ForeignKey(Carrito, on_delete=models.CASCADE, related_name="lineas")
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, related_name="lineas_carrito")
    cantidad = models.PositiveIntegerField("cantidad")
    precio_vigente = models.DecimalField(
        "precio vigente", max_digits=12, decimal_places=2, validators=[POSITIVO]
    )
    precio_visto = models.DecimalField(
        "precio visto", max_digits=12, decimal_places=2, validators=[POSITIVO]
    )
    agregada_en = models.DateTimeField("agregada en", auto_now_add=True)

    class Meta:
        verbose_name = "línea de carrito"
        verbose_name_plural = "líneas de carrito"
        ordering = ["agregada_en", "pk"]  # noqa: RUF012
        constraints = [  # noqa: RUF012
            models.UniqueConstraint(
                fields=["carrito", "producto"], name="linea_unica_por_producto"
            ),
            models.CheckConstraint(
                condition=models.Q(cantidad__gte=1), name="linea_cantidad_minima"
            ),
        ]

    def __str__(self):
        return f"{self.cantidad} × {self.producto}"
