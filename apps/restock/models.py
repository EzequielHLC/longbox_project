"""`SuscripcionReposicion`, `PropuestaRestock` y su línea (módulo 05; áreas 3 y 4).

La suscripción es la demanda que no se ve: alguien quiso comprar algo agotado.
Su momento de creación es su turno (P-13). La propuesta es un borrador que el
Administrador revisa y despacha proveedor por proveedor (P-07).
"""

from django.conf import settings
from django.db import models
from django.db.models import Q
from django.utils import timezone

from apps.catalog.models import Producto, ProductoEditorial


class SuscripcionReposicion(models.Model):
    ACTIVA = "activa"
    NOTIFICADA = "notificada"
    FALLIDA = "fallida"
    ESTADO_CHOICES = [  # noqa: RUF012
        (ACTIVA, "Activa"),
        (NOTIFICADA, "Notificada"),
        (FALLIDA, "Notificación fallida"),
    ]
    # La lista de espera: la fallida conserva su turno (B-05-005).
    EN_ESPERA = (ACTIVA, FALLIDA)

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="suscripciones_reposicion"
    )
    producto = models.ForeignKey(
        Producto, on_delete=models.CASCADE, related_name="suscripciones_reposicion"
    )
    creada_en = models.DateTimeField("creada en", default=timezone.now)
    estado = models.CharField("estado", max_length=12, choices=ESTADO_CHOICES, default=ACTIVA)
    notificada_en = models.DateTimeField("notificada en", null=True, blank=True)

    class Meta:
        verbose_name = "suscripción de reposición"
        verbose_name_plural = "suscripciones de reposición"
        ordering = ["creada_en", "pk"]  # noqa: RUF012
        constraints = [  # noqa: RUF012
            # I-22: a lo sumo una en espera por cliente y producto.
            models.UniqueConstraint(
                fields=["usuario", "producto"],
                condition=Q(estado__in=["activa", "fallida"]),
                name="suscripcion_en_espera_unica",
            ),
        ]

    def __str__(self):
        return f"{self.usuario} espera {self.producto}"


class PropuestaRestock(models.Model):
    PENDIENTE = "pendiente"
    # Plan 00 de la respuesta del proveedor (desvío de DME-13, aprobado): despachada,
    # queda abierta hasta que cada proveedor contesta qué manda y cuándo.
    ESPERANDO = "esperando"
    CERRADA = "cerrada"
    ESTADO_CHOICES = [  # noqa: RUF012
        (PENDIENTE, "Pendiente de aprobación"),
        (ESPERANDO, "Esperando respuesta"),
        (CERRADA, "Cerrada"),
    ]
    AUTOMATICO = "automatico"
    MANUAL = "manual"
    # B-05-012: armada a mano por el Administrador, vacía, sin mirar la demanda.
    A_MANO = "a_mano"
    DISPARO_CHOICES = [  # noqa: RUF012
        (AUTOMATICO, "Automático"),
        (MANUAL, "Manual"),
        (A_MANO, "Armada a mano"),
    ]

    fecha_generacion = models.DateTimeField("fecha de generación", default=timezone.now)
    tipo_disparo = models.CharField("tipo de disparo", max_length=12, choices=DISPARO_CHOICES)
    estado = models.CharField("estado", max_length=12, choices=ESTADO_CHOICES, default=PENDIENTE)
    cerrada_en = models.DateTimeField("cerrada en", null=True, blank=True)

    class Meta:
        verbose_name = "propuesta de restock"
        verbose_name_plural = "propuestas de restock"
        ordering = ["-fecha_generacion", "-pk"]  # noqa: RUF012
        constraints = [  # noqa: RUF012
            # I-21: a lo sumo una pendiente de aprobación.
            models.UniqueConstraint(
                fields=["estado"],
                condition=Q(estado="pendiente"),
                name="propuesta_pendiente_unica",
            ),
        ]

    def __str__(self):
        return f"Propuesta del {timezone.localtime(self.fecha_generacion):%d/%m/%Y}"

    @property
    def espera(self):
        """Qué espera la propuesta y desde cuándo (plan 00 de la respuesta simple, R5 y
        R6). Vacío si no está esperando. Lee los pedidos ya traídos, sin sus líneas."""
        if self.estado != self.ESPERANDO:
            return ""
        pedidos = list(self.pedidos.all())
        if any(pedido.estado == "sin_enviar" for pedido in pedidos):
            return "Esperando un reintento de envío"
        desde = min((pedido.creado_en for pedido in pedidos), default=None)
        if desde is None:
            return "Esperando respuesta"
        dias = (timezone.localdate() - timezone.localdate(desde)).days
        if dias <= 0:
            return "Esperando respuesta desde hoy"
        return f"Esperando respuesta hace {dias} día{'s' if dias != 1 else ''}"


class LineaPropuestaRestock(models.Model):
    PENDIENTE = "pendiente"
    DESPACHADO = "despachado"
    DESCARTADO = "descartado"
    ESTADO_CHOICES = [  # noqa: RUF012
        (PENDIENTE, "Pendiente"),
        (DESPACHADO, "Despachado"),
        (DESCARTADO, "Descartado"),
    ]

    propuesta = models.ForeignKey(PropuestaRestock, on_delete=models.CASCADE, related_name="lineas")
    producto = models.ForeignKey(
        ProductoEditorial, on_delete=models.PROTECT, related_name="lineas_de_restock"
    )
    cantidad_sugerida = models.PositiveIntegerField("cantidad")
    # Congelado al generar (PD-09): es lo que justificó la cantidad.
    suscriptores_activos = models.PositiveIntegerField("suscriptores", default=0)
    estado_despacho = models.CharField(
        "estado de despacho", max_length=12, choices=ESTADO_CHOICES, default=PENDIENTE
    )
    anadida_a_mano = models.BooleanField("añadida a mano", default=False)
    motivo_descarte = models.TextField("motivo del descarte", blank=True)

    class Meta:
        verbose_name = "línea de propuesta de restock"
        verbose_name_plural = "líneas de propuesta de restock"
        ordering = ["-suscriptores_activos", "pk"]  # noqa: RUF012
        constraints = [  # noqa: RUF012
            models.UniqueConstraint(
                fields=["propuesta", "producto"], name="linea_restock_producto_unico"
            ),
        ]

    def __str__(self):
        return f"{self.cantidad_sugerida} × {self.producto}"
