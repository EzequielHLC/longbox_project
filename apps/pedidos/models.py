"""`Pedido`, `LineaPedido` y `TransaccionPago` (modelo de dominio, área 5).

Los crea `CO-089` al aprobarse el pago de una compra online, en una sola
transacción. Sus estados son los de DME-07 (pedido) y DME-08 (ítem); la compra
sólo usa los iniciales, y los demás son de la gestión de pedidos (módulo 08).

**Ningún importe es negativo y ningún precio es cero** (I-09): acá vive como
restricción de la base y no sólo como validador, porque la base es la única que
la hace valer para cualquier camino de escritura.
"""

from decimal import Decimal

from django.conf import settings
from django.db import models
from django.db.models import Q
from django.utils import timezone

from apps.catalog.models import Producto

ENVIO_CAMPOS = ("direccion", "depto", "localidad", "provincia", "codigo_postal")


class Pedido(models.Model):
    ONLINE = "online"
    PRESENCIAL = "presencial"
    CANAL_CHOICES = [  # noqa: RUF012
        (ONLINE, "Online"),
        (PRESENCIAL, "Presencial"),
    ]

    # DME-07. RF-18: dos secuencias, según haya o no pre-ventas al confirmar.
    ESPERANDO_PRE_VENTA = "esperando_pre_venta"
    PENDIENTE_ARMADO = "pendiente_armado"
    ARMADO = "armado"
    ESPERANDO_DEMORADO = "esperando_demorado"
    EMPAQUETADO = "empaquetado"
    DESPACHADO = "despachado"
    # B-08-008: un pedido que se queda sin artículos. Terminal.
    CANCELADO = "cancelado"
    ESTADO_CHOICES = [  # noqa: RUF012
        (ESPERANDO_PRE_VENTA, "Esperando stock de pre-venta"),
        (PENDIENTE_ARMADO, "Pendiente de armado"),
        (ARMADO, "Armado"),
        (ESPERANDO_DEMORADO, "Esperando artículo demorado"),
        (EMPAQUETADO, "Empaquetado"),
        (DESPACHADO, "Despachado"),
        (CANCELADO, "Cancelado"),
    ]

    # Se asigna dentro de la misma transacción que crea el pedido, a partir de
    # su clave: nulo sólo durante ese instante, nunca visible afuera.
    numero = models.CharField("número", max_length=20, unique=True, null=True, blank=True)
    canal = models.CharField("canal", max_length=12, choices=CANAL_CHOICES)
    estado = models.CharField("estado", max_length=25, choices=ESTADO_CHOICES)
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="pedidos",
    )
    correo_invitado = models.EmailField("correo del invitado", blank=True)

    # La dirección se **copia**, no se referencia (PD-09): cambiar el domicilio
    # del perfil no puede reescribir a dónde se despachó un pedido pasado.
    envio_direccion = models.CharField("dirección", max_length=150, blank=True)
    envio_depto = models.CharField("piso / depto.", max_length=20, blank=True)
    envio_localidad = models.CharField("localidad", max_length=120, blank=True)
    envio_provincia = models.CharField("provincia", max_length=60, blank=True)
    envio_codigo_postal = models.CharField("código postal", max_length=10, blank=True)

    costo_envio = models.DecimalField(
        "costo de envío", max_digits=12, decimal_places=2, default=Decimal("0")
    )
    fecha = models.DateTimeField("fecha", default=timezone.now)

    class Meta:
        verbose_name = "pedido"
        verbose_name_plural = "pedidos"
        ordering = ["-fecha", "-pk"]  # noqa: RUF012
        constraints = [  # noqa: RUF012
            models.CheckConstraint(
                condition=Q(costo_envio__gte=0), name="pedido_costo_envio_no_negativo"
            ),
            # Un pedido online es de una cuenta o de un correo de invitado, nunca
            # de los dos y nunca de ninguno (CO-089 b).
            models.CheckConstraint(
                condition=Q(canal="presencial")
                | (Q(usuario__isnull=False) & Q(correo_invitado=""))
                | (Q(usuario__isnull=True) & ~Q(correo_invitado="")),
                name="pedido_online_de_cuenta_o_invitado",
            ),
        ]

    def __str__(self):
        return f"Pedido {self.numero}"

    @property
    def direccion_de_envio(self):
        partes = [self.envio_direccion, self.envio_depto, self.envio_localidad]
        provincia = " ".join(p for p in (self.envio_provincia, self.envio_codigo_postal) if p)
        return ", ".join(p for p in [*partes, provincia] if p)

    @property
    def correo_de_contacto(self):
        return self.usuario.email if self.usuario_id else self.correo_invitado

    @property
    def subtotal(self):
        return sum((linea.subtotal for linea in self.lineas.all()), Decimal("0"))

    @property
    def total(self):
        return self.subtotal + self.costo_envio

    def asignar_numero(self):
        self.numero = f"{self.pk:06d}"
        self.save(update_fields=["numero"])


class LineaPedido(models.Model):
    # DME-08. La compra usa los dos primeros; los demás, la gestión de pedidos.
    DISPONIBLE = "disponible"
    RESERVADO = "reservado"
    ESPERANDO_DEMORADO = "esperando_demorado"
    EMPAQUETADO = "empaquetado"
    DESPACHADO = "despachado"
    CANCELADO_REEMBOLSO = "cancelado_reembolso"
    ESTADO_CHOICES = [  # noqa: RUF012
        (DISPONIBLE, "Disponible"),
        (RESERVADO, "Reservado"),
        (ESPERANDO_DEMORADO, "Esperando artículo demorado"),
        (EMPAQUETADO, "Empaquetado"),
        (DESPACHADO, "Despachado"),
        (CANCELADO_REEMBOLSO, "Cancelado con reembolso en puntos"),
    ]

    PAUSAR = "pausar"
    DESPACHO_DIFERIDO = "despacho_diferido"
    CANCELAR = "cancelar"
    DECISION_CHOICES = [  # noqa: RUF012
        (PAUSAR, "Pausar"),
        (DESPACHO_DIFERIDO, "Despacho diferido"),
        (CANCELAR, "Cancelar"),
    ]

    pedido = models.ForeignKey(Pedido, on_delete=models.CASCADE, related_name="lineas")
    producto = models.ForeignKey(Producto, on_delete=models.PROTECT, related_name="lineas_pedido")
    cantidad = models.PositiveIntegerField("cantidad")
    # Congelado al confirmar (P-09): un cambio de precio posterior no lo sigue.
    precio_unitario = models.DecimalField("precio unitario", max_digits=12, decimal_places=2)
    cubierta_con_puntos = models.BooleanField("cubierta con puntos", default=False)
    # «cubierta con puntos con el valor de su canje» (CO-089 c): cuántos costó.
    puntos_canjeados = models.PositiveIntegerField("puntos canjeados", default=0)
    estado = models.CharField("estado del ítem", max_length=25, choices=ESTADO_CHOICES)
    decision_demora = models.CharField(
        "decisión ante demora", max_length=20, choices=DECISION_CHOICES, blank=True
    )
    compensacion_acumulada = models.DecimalField(
        "compensación acumulada", max_digits=12, decimal_places=2, default=Decimal("0")
    )
    fecha_llegada_original = models.DateField("fecha de llegada original", null=True, blank=True)
    # B-08-004: la ventana se abre al registrarse la demora de la línea.
    decision_vence_en = models.DateTimeField("la decisión vence", null=True, blank=True)
    ventana_cerrada = models.BooleanField("ventana de decisión cerrada", default=False)
    compensacion_cerrada = models.BooleanField("compensación cerrada", default=False)

    class Meta:
        verbose_name = "línea de pedido"
        verbose_name_plural = "líneas de pedido"
        ordering = ["pk"]  # noqa: RUF012
        constraints = [  # noqa: RUF012
            models.CheckConstraint(
                condition=Q(cantidad__gte=1), name="linea_pedido_cantidad_minima"
            ),
            models.CheckConstraint(
                condition=Q(precio_unitario__gt=0), name="linea_pedido_precio_positivo"
            ),
            models.CheckConstraint(
                condition=Q(compensacion_acumulada__gte=0),
                name="linea_pedido_compensacion_no_negativa",
            ),
            models.CheckConstraint(
                condition=Q(cubierta_con_puntos=True, puntos_canjeados__gt=0)
                | Q(cubierta_con_puntos=False, puntos_canjeados=0),
                name="linea_pedido_canje_coherente",
            ),
        ]

    def __str__(self):
        return f"{self.cantidad} × {self.producto}"

    @property
    def valor(self):
        """El valor original del artículo, pagado como sea (`CO-097`, `CO-098`)."""
        return self.precio_unitario * self.cantidad

    @property
    def despacho_diferido(self):
        return self.decision_demora == self.DESPACHO_DIFERIDO

    @property
    def subtotal(self):
        """Lo que se paga en dinero: cero si la cubrieron los puntos."""
        if self.cubierta_con_puntos:
            return Decimal("0")
        return self.precio_unitario * self.cantidad


class TransaccionPago(models.Model):
    EFECTIVO = "efectivo"
    TRANSFERENCIA = "transferencia"
    TARJETA = "tarjeta"
    PASARELA = "pasarela"
    MEDIO_CHOICES = [  # noqa: RUF012
        (EFECTIVO, "Efectivo"),
        (TRANSFERENCIA, "Transferencia"),
        (TARJETA, "Tarjeta"),
        (PASARELA, "Pasarela"),
    ]

    APROBADO = "aprobado"
    RECHAZADO = "rechazado"
    PENDIENTE_VERIFICACION = "pendiente_verificacion"
    ESTADO_CHOICES = [  # noqa: RUF012
        (APROBADO, "Aprobado"),
        (RECHAZADO, "Rechazado"),
        (PENDIENTE_VERIFICACION, "Pendiente de verificación"),
    ]

    pedido = models.OneToOneField(Pedido, on_delete=models.PROTECT, related_name="transaccion")
    medio = models.CharField("medio de pago", max_length=15, choices=MEDIO_CHOICES)
    monto = models.DecimalField("monto", max_digits=12, decimal_places=2)
    estado = models.CharField("estado", max_length=25, choices=ESTADO_CHOICES)
    # Única: es lo que reconoce un aviso repetido de la pasarela y evita el
    # doble pedido por el mismo pago (CO-089, nota 1). Nula en efectivo.
    referencia = models.CharField(
        "referencia de la pasarela", max_length=100, unique=True, null=True, blank=True
    )
    incluida_en_cierre = models.BooleanField("incluida en cierre", default=False)
    # CierreDeCaja "0..1" -- "0..*" TransaccionPago (CO-126 b).
    cierre = models.ForeignKey(
        "caja.CierreDeCaja",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="transacciones",
    )
    registrada_en = models.DateTimeField("registrada en", default=timezone.now)

    class Meta:
        verbose_name = "transacción de pago"
        verbose_name_plural = "transacciones de pago"
        constraints = [  # noqa: RUF012
            models.CheckConstraint(condition=Q(monto__gte=0), name="transaccion_monto_no_negativo"),
        ]

    def __str__(self):
        return f"{self.get_medio_display()} {self.monto} ({self.get_estado_display()})"


class TransicionDePedido(models.Model):
    """Un paso de la línea de tiempo del pedido (B-08-001).

    `CO-183` y `CO-193` muestran «la línea de tiempo de estados con
    timestamps», y `Pedido` sólo guarda el estado en el que está. La primera la
    escribe la compra (sin estado anterior); las demás, quien avanza el pedido:
    el Administrador (`CO-092`) o, más adelante, un proceso del sistema
    (`actor` nulo).
    """

    pedido = models.ForeignKey(Pedido, on_delete=models.CASCADE, related_name="transiciones")
    estado_anterior = models.CharField(
        "estado anterior", max_length=25, choices=Pedido.ESTADO_CHOICES, blank=True
    )
    estado_nuevo = models.CharField("estado nuevo", max_length=25, choices=Pedido.ESTADO_CHOICES)
    ocurrida_en = models.DateTimeField("ocurrida en", default=timezone.now)
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="transiciones_de_pedido",
    )

    class Meta:
        verbose_name = "transición de pedido"
        verbose_name_plural = "transiciones de pedido"
        ordering = ["ocurrida_en", "pk"]  # noqa: RUF012

    def __str__(self):
        return f"{self.pedido} → {self.get_estado_nuevo_display()}"


class AvisoDePreVenta(models.Model):
    """Lo que el Temporizador ya avisó (`CO-011`, `CO-012`; B-01-009).

    Correr el ciclo dos veces el mismo día no repite un correo: cada aviso se
    anota con el producto, su tipo y la fecha a la que se refiere.
    """

    PROXIMIDAD = "proximidad"
    LLEGADA = "llegada"
    ESCALADO = "escalado"
    TIPO_CHOICES = [  # noqa: RUF012
        (PROXIMIDAD, "Llegada próxima"),
        (LLEGADA, "Llega hoy"),
        (ESCALADO, "Sin resolver"),
    ]

    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, related_name="avisos_preventa")
    tipo = models.CharField("tipo", max_length=12, choices=TIPO_CHOICES)
    fecha = models.DateField("fecha")
    enviado_en = models.DateTimeField("enviado en", default=timezone.now)

    class Meta:
        verbose_name = "aviso de pre-venta"
        verbose_name_plural = "avisos de pre-venta"
        constraints = [  # noqa: RUF012
            models.UniqueConstraint(
                fields=["producto", "tipo", "fecha"], name="aviso_preventa_unico"
            ),
        ]

    def __str__(self):
        return f"{self.get_tipo_display()} · {self.producto} · {self.fecha}"
