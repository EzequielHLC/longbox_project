"""`CasoDevolucion` y su evidencia (modelo de dominio, área 5; plan 00, C1).

Un caso es un reclamo sobre una línea de un pedido entregado, de uno de dos tipos:

- **Arrepentimiento**: la revocación de una compra online (Ley 24.240, art. 34;
  botón de arrepentimiento). Cubre la línea entera, no pide fotos y se reembolsa
  por el medio de pago cuando el local recibe el artículo, que vuelve al stock.
- **Garantía**: un defecto de fabricación o un error de imprenta. Cubre una
  unidad, pide fotos y se resuelve con un cambio, puntos o el medio de pago.

Lo que no es registrar (la prueba de destrucción, la devolución del artículo) se
coordina por fuera del sistema. Su ciclo es DME-15: Pendiente y uno de dos
finales, Resuelto o Rechazado. **Existe a lo sumo uno por línea, en cualquier
estado** (I-19): es la identidad del caso, y vive en la base como unicidad.
"""

from django.conf import settings
from django.db import models
from django.db.models import Q
from django.utils import timezone

from apps.catalog.models import Producto
from apps.devoluciones.almacenamiento import evidencias


class CasoDevolucion(models.Model):
    DEFECTO = "defecto"
    ERROR_IMPRENTA = "error_imprenta"
    ARREPENTIMIENTO = "arrepentimiento"
    MOTIVO_CHOICES = [  # noqa: RUF012
        (DEFECTO, "Defecto de fabricación"),
        (ERROR_IMPRENTA, "Error de imprenta"),
        (ARREPENTIMIENTO, "Arrepentimiento"),
    ]
    MOTIVOS_DE_GARANTIA = (DEFECTO, ERROR_IMPRENTA)

    PENDIENTE = "pendiente"
    RESUELTO = "resuelto"
    RECHAZADO = "rechazado"
    ESTADO_CHOICES = [  # noqa: RUF012
        (PENDIENTE, "Pendiente"),
        (RESUELTO, "Resuelto"),
        (RECHAZADO, "Rechazado"),
    ]

    CAMBIO = "cambio"
    REEMBOLSO = "reembolso"
    REEMBOLSO_MEDIO = "reembolso_medio"
    RESOLUCION_CHOICES = [  # noqa: RUF012
        (CAMBIO, "Cambio"),
        (REEMBOLSO, "Reembolso en puntos"),
        (REEMBOLSO_MEDIO, "Reembolso por el medio de pago"),
    ]

    # I-19: un caso por línea, en cualquier estado.
    linea = models.OneToOneField(
        "pedidos.LineaPedido",
        on_delete=models.PROTECT,
        related_name="caso_devolucion",
        verbose_name="línea del pedido",
    )
    # El invitado no tiene cuenta: el arrepentimiento no pide registración
    # (Res. 424/2020). El correo de contacto es el de la compra.
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="casos_devolucion",
        verbose_name="cliente",
    )
    correo = models.EmailField("correo de contacto")
    motivo = models.CharField("motivo", max_length=20, choices=MOTIVO_CHOICES)
    # Garantía: una unidad (el ejemplar fallado). Arrepentimiento: la línea entera.
    unidades = models.PositiveIntegerField("unidades", default=1)
    descripcion = models.TextField("descripción", blank=True)
    estado = models.CharField("estado", max_length=12, choices=ESTADO_CHOICES, default=PENDIENTE)
    resolucion = models.CharField(
        "resolución", max_length=20, choices=RESOLUCION_CHOICES, blank=True
    )
    motivo_rechazo = models.TextField("motivo del rechazo", blank=True)
    producto_reemplazo = models.ForeignKey(
        Producto,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="casos_de_cambio",
        verbose_name="producto de reemplazo",
    )
    # Lo que el local devuelve desde el panel de la pasarela: el sistema lo
    # registra, no mueve el dinero (plan 00, C1).
    monto_reembolsado = models.DecimalField(
        "monto a reembolsar", max_digits=12, decimal_places=2, null=True, blank=True
    )
    abierto_en = models.DateTimeField("abierto el", default=timezone.now)
    resuelto_en = models.DateTimeField("resuelto el", null=True, blank=True)
    resuelto_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="casos_resueltos",
    )

    class Meta:
        verbose_name = "caso de devolución"
        verbose_name_plural = "casos de devolución"
        ordering = ["abierto_en", "pk"]  # noqa: RUF012
        constraints = [  # noqa: RUF012
            # DME-15: la resolución existe sólo en Resuelto; el motivo del
            # rechazo, sólo en Rechazado, y nunca vacío.
            models.CheckConstraint(
                condition=Q(estado="pendiente", resolucion="", motivo_rechazo="")
                | (Q(estado="resuelto", motivo_rechazo="") & ~Q(resolucion=""))
                | (Q(estado="rechazado", resolucion="") & ~Q(motivo_rechazo="")),
                name="caso_estado_coherente_con_resolucion",
            ),
            models.CheckConstraint(
                condition=Q(resolucion="cambio", producto_reemplazo__isnull=False)
                | (~Q(resolucion="cambio") & Q(producto_reemplazo__isnull=True)),
                name="caso_cambio_tiene_reemplazo",
            ),
            # El arrepentimiento devuelve lo pagado: nunca se resuelve con un cambio.
            models.CheckConstraint(
                condition=~Q(motivo="arrepentimiento", resolucion="cambio"),
                name="caso_arrepentimiento_sin_cambio",
            ),
            models.CheckConstraint(
                condition=Q(resolucion="reembolso_medio", monto_reembolsado__gt=0)
                | (~Q(resolucion="reembolso_medio") & Q(monto_reembolsado__isnull=True)),
                name="caso_reembolso_medio_con_monto",
            ),
            models.CheckConstraint(condition=Q(unidades__gte=1), name="caso_al_menos_una_unidad"),
        ]

    def __str__(self):
        return f"Caso {self.numero}"

    @property
    def numero(self):
        return f"DV-{self.pk:05d}" if self.pk else ""

    @property
    def abierto(self):
        return self.estado == self.PENDIENTE

    @property
    def es_arrepentimiento(self):
        return self.motivo == self.ARREPENTIMIENTO

    @property
    def telefono(self):
        return getattr(self.usuario, "telefono", "") if self.usuario_id else ""


class EvidenciaDevolucion(models.Model):
    """Una foto del artículo reclamado, ya convertida a WebP (RNF-05)."""

    caso = models.ForeignKey(CasoDevolucion, on_delete=models.CASCADE, related_name="evidencias")
    imagen = models.ImageField("imagen", storage=evidencias, upload_to="devoluciones/%Y/%m/")

    class Meta:
        verbose_name = "evidencia de devolución"
        verbose_name_plural = "evidencias de devolución"
        ordering = ["pk"]  # noqa: RUF012

    def __str__(self):
        return f"Evidencia {self.pk} del {self.caso}"
