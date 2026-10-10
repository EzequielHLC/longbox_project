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
    # `CO-103`: la línea entera se paga con puntos (B-07-033). Marcarla no debita
    # nada; el débito ocurre en `CO-089`.
    cubierta_con_puntos = models.BooleanField("cubierta con puntos", default=False)

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


class CobroEnCurso(models.Model):
    """Lo que se cobra, congelado al confirmar el pedido (B-07-034).

    **No es un concepto del dominio**, como no lo es la sesión: es lo que
    recuerda el checkout mientras el Cliente está en la pasarela, porque el aviso
    del pago llega de servidor a servidor y no trae su sesión. `CO-088` lo crea y
    `CO-089` lo materializa en un `Pedido`.

    El pedido es lo que se cobró: las líneas se copian acá con su precio y su
    canje, y un cambio posterior del carrito no las alcanza.
    """

    PENDIENTE = "pendiente"
    PROCESADO = "procesado"
    RECHAZADO = "rechazado"
    REEMBOLSADO = "reembolsado"
    ESTADO_CHOICES = [  # noqa: RUF012
        (PENDIENTE, "Esperando el pago"),
        (PROCESADO, "Pedido generado"),
        (RECHAZADO, "Pago rechazado"),
        (REEMBOLSADO, "Pago reembolsado"),
    ]

    referencia = models.CharField("referencia", max_length=64, unique=True)
    pasarela = models.CharField("pasarela", max_length=15)
    estado = models.CharField("estado", max_length=12, choices=ESTADO_CHOICES, default=PENDIENTE)
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="cobros_en_curso",
    )
    correo_invitado = models.EmailField("correo del invitado", blank=True)
    carrito = models.ForeignKey(
        Carrito, on_delete=models.SET_NULL, null=True, blank=True, related_name="cobros"
    )
    envio = models.JSONField("dirección de envío", default=dict)
    # Por línea: producto, cantidad, precio unitario y puntos del canje (0 si no).
    lineas = models.JSONField("líneas", default=list)
    costo_envio = models.DecimalField("costo de envío", max_digits=12, decimal_places=2)
    monto = models.DecimalField("monto a cobrar", max_digits=12, decimal_places=2)
    puntos_a_debitar = models.PositiveIntegerField("puntos a debitar", default=0)
    # Lo que la pasarela devuelve al iniciar el cobro (en MercadoPago, la preferencia).
    id_externo = models.CharField("identificador en la pasarela", max_length=100, blank=True)
    mensaje = models.CharField("mensaje de la pasarela", max_length=300, blank=True)
    # La dirección de la tienda desde la que se compró: el aviso de la pasarela
    # no trae la petición del Cliente, y el correo necesita el enlace al pedido.
    origen = models.CharField("dirección de la tienda", max_length=200, blank=True)
    pedido = models.OneToOneField(
        "pedidos.Pedido", on_delete=models.PROTECT, null=True, blank=True, related_name="cobro"
    )
    creado_en = models.DateTimeField("creado en", auto_now_add=True)
    resuelto_en = models.DateTimeField("resuelto en", null=True, blank=True)

    class Meta:
        verbose_name = "cobro en curso"
        verbose_name_plural = "cobros en curso"
        constraints = [  # noqa: RUF012
            models.CheckConstraint(
                condition=models.Q(monto__gte=0, costo_envio__gte=0),
                name="cobro_importes_no_negativos",
            ),
        ]

    def __str__(self):
        return f"Cobro {self.referencia} ({self.get_estado_display()})"

    @property
    def correo_de_contacto(self):
        return self.usuario.email if self.usuario_id else self.correo_invitado
