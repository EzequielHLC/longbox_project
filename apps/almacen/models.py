"""`ArticuloRetenido` y `SolicitudDespacho` (módulo 18; modelo de dominio, área 5).

Un artículo retenido es **una unidad** de un producto que el local guarda a
nombre de un Cliente (B-18-002). Su ciclo es DME-12: Disponible, Pendiente de
despacho, y uno de tres finales (Despachado, Retirado en local, Vencido y
devuelto al stock).

Tiene tres procedencias: el artículo de despacho diferido, la unidad de un
pedido para retirar (plan 07, octava parte) y el reemplazo de un cambio por
garantía (plan 00, C1), que se envía sin costo. Las tres vencen con su valor
en puntos (plan 00, C2).

La solicitud de despacho agrupa los artículos que el Cliente pidió juntos, con
la dirección copiada y, si el envío fue pago, su transacción (B-18-004).
"""

from datetime import timedelta
from decimal import Decimal

from django.conf import settings
from django.db import models
from django.db.models import Q
from django.utils import timezone

from apps.catalog.models import Producto


class SolicitudDespacho(models.Model):
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="solicitudes_de_despacho",
    )
    envio_direccion = models.CharField("dirección", max_length=150)
    envio_depto = models.CharField("piso / depto.", max_length=20, blank=True)
    envio_localidad = models.CharField("localidad", max_length=120)
    envio_provincia = models.CharField("provincia", max_length=60)
    envio_codigo_postal = models.CharField("código postal", max_length=10)
    costo_envio = models.DecimalField(
        "costo de envío", max_digits=12, decimal_places=2, default=Decimal("0")
    )
    creada_en = models.DateTimeField("creada en", default=timezone.now)

    class Meta:
        verbose_name = "solicitud de despacho"
        verbose_name_plural = "solicitudes de despacho"
        ordering = ["-creada_en", "-pk"]  # noqa: RUF012
        constraints = [  # noqa: RUF012
            models.CheckConstraint(
                condition=Q(costo_envio__gte=0), name="solicitud_costo_envio_no_negativo"
            ),
        ]

    def __str__(self):
        return f"Solicitud {self.numero}"

    @property
    def numero(self):
        return f"D-{self.pk:06d}" if self.pk else ""

    @property
    def direccion_de_envio(self):
        partes = [self.envio_direccion, self.envio_depto, self.envio_localidad]
        provincia = " ".join(p for p in (self.envio_provincia, self.envio_codigo_postal) if p)
        return ", ".join(p for p in [*partes, provincia] if p)

    @property
    def envio_gratis(self):
        return not self.costo_envio


class ArticuloRetenido(models.Model):
    DISPONIBLE = "disponible"
    PENDIENTE_DESPACHO = "pendiente_despacho"
    DESPACHADO = "despachado"
    RETIRADO = "retirado"
    VENCIDO = "vencido"
    ESTADO_CHOICES = [  # noqa: RUF012
        (DISPONIBLE, "Disponible"),
        (PENDIENTE_DESPACHO, "Pendiente de despacho"),
        (DESPACHADO, "Despachado"),
        (RETIRADO, "Retirado en local"),
        (VENCIDO, "Vencido y devuelto al stock"),
    ]
    # Los que corren plazo (CO-153): los demás no tienen vencimiento vigente.
    CON_PLAZO = (DISPONIBLE, PENDIENTE_DESPACHO)
    FINALES = (DESPACHADO, RETIRADO, VENCIDO)

    DESPACHO_DIFERIDO = "despacho_diferido"
    PARA_RETIRAR = "para_retirar"
    CAMBIO = "cambio"
    PROCEDENCIA_CHOICES = [  # noqa: RUF012
        (DESPACHO_DIFERIDO, "Despacho diferido"),
        (PARA_RETIRAR, "Pedido para retirar"),
        (CAMBIO, "Cambio por garantía"),
    ]

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="articulos_retenidos",
        verbose_name="cliente",
    )
    producto = models.ForeignKey(
        Producto, on_delete=models.PROTECT, related_name="articulos_retenidos"
    )
    linea_pedido = models.ForeignKey(
        "pedidos.LineaPedido",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="articulos_retenidos",
    )
    solicitud = models.ForeignKey(
        SolicitudDespacho,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="articulos",
    )
    valor = models.DecimalField("valor", max_digits=12, decimal_places=2)
    fecha_ingreso = models.DateField("fecha de ingreso", default=timezone.localdate)
    fecha_vencimiento = models.DateField("fecha de vencimiento", null=True, blank=True)
    estado = models.CharField("estado", max_length=20, choices=ESTADO_CHOICES, default=DISPONIBLE)
    procedencia = models.CharField(
        "procedencia", max_length=20, choices=PROCEDENCIA_CHOICES, default=DESPACHO_DIFERIDO
    )
    # B-18-006: la fecha de vencimiento para la que ya se avisó al Cliente.
    aviso_para = models.DateField("aviso enviado para", null=True, blank=True)
    actualizado_en = models.DateTimeField("última modificación", auto_now=True)

    class Meta:
        verbose_name = "artículo retenido"
        verbose_name_plural = "artículos retenidos"
        ordering = ["fecha_vencimiento", "pk"]  # noqa: RUF012
        constraints = [  # noqa: RUF012
            models.CheckConstraint(condition=Q(valor__gt=0), name="articulo_valor_positivo"),
            # Lo que corre plazo tiene fecha de vencimiento.
            models.CheckConstraint(
                condition=~Q(estado__in=["disponible", "pendiente_despacho"])
                | Q(fecha_vencimiento__isnull=False),
                name="articulo_con_plazo_tiene_vencimiento",
            ),
            # Un artículo pendiente de despacho pertenece a una solicitud.
            models.CheckConstraint(
                condition=~Q(estado="pendiente_despacho") | Q(solicitud__isnull=False),
                name="articulo_pendiente_tiene_solicitud",
            ),
        ]
        indexes = [models.Index(fields=["estado", "fecha_vencimiento"])]  # noqa: RUF012

    def __str__(self):
        return f"{self.producto} · {self.usuario}"

    @property
    def origen(self):
        if self.linea_pedido_id:
            return (
                f"Pedido {self.linea_pedido.pedido.numero} · "
                f"{self.get_procedencia_display().lower()}"
            )
        return "Cambio"

    @property
    def para_retirar(self):
        return self.procedencia == self.PARA_RETIRAR

    @property
    def de_cambio(self):
        return self.procedencia == self.CAMBIO

    @property
    def corre_plazo(self):
        return self.estado in self.CON_PLAZO

    def dias_para_vencer(self, hoy=None):
        if not self.corre_plazo or self.fecha_vencimiento is None:
            return None
        return (self.fecha_vencimiento - (hoy or timezone.localdate())).days

    def proximo_a_vencer(self, dias_aviso, hoy=None):
        """El destacado de `CO-215` y `CO-217`: no es un estado, se deriva de la fecha."""
        if self.estado != self.DISPONIBLE:
            return False
        restan = self.dias_para_vencer(hoy)
        return restan is not None and restan <= dias_aviso


def vencimiento_desde(dia, meses):
    """`dia` más `meses` meses; el 31 de un mes corto cae en su último día."""
    from apps.puntos.servicios import _sumar_meses

    return _sumar_meses(dia, meses)


EXTENSION_AUTOMATICA = timedelta(days=3)
