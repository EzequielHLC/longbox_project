"""Módulo 19 · Perfil y avisos (plan 00 de Telegram).

Tres conceptos que el modelo de dominio todavía no tiene (B-19-001):

- **El vínculo con Telegram**: qué chat es de qué Administrador. Es un dato
  personal: se borra al desvincular, y la autorización se mira en el momento de
  cada acción —un Administrador dado de baja no hace nada desde su chat—.
- **El código de vinculación**: un solo uso, vence a los 15 minutos. Es lo que
  viaja en el enlace `t.me/<bot>?start=<código>`, como `EnlaceActivacion`.
- **La preferencia de aviso**: por tipo, correo sí o no y Telegram sí o no. Sin
  fila, el aviso sale por el canal por defecto de su tipo: por correo, como
  siempre (decisión 3 del plan), salvo los de la etapa 3 (B-19-011).
"""

import secrets
from dataclasses import dataclass
from datetime import timedelta

from django.conf import settings
from django.db import models
from django.utils import timezone

# Los tipos de aviso al Administrador, sacados de los lugares donde hoy se avisa.
CORREOS = "correos"
PREVENTAS = "preventas"
PEDIDOS = "pedidos"
RESTOCK = "restock"
DEVOLUCIONES = "devoluciones"
STOCK_LOCAL = "stock_local"
# Etapa 3 (plan 00 del bot, etapa 3).
VENTAS = "ventas"
SEGURIDAD = "seguridad"
SISTEMA = "sistema"
RESUMEN = "resumen"


@dataclass(frozen=True)
class TipoDeAviso:
    """Un tipo de aviso al Administrador y su canal cuando no eligió ninguno."""

    clave: str
    nombre: str
    descripcion: str
    por_correo: bool = True
    por_telegram: bool = False

    @property
    def opcional(self):
        """Si puede quedar sin canal (ambigüedad 1 del plan de la etapa 3).

        Los que por defecto no van por correo son un extra: sin Telegram no se
        mandan, y si Telegram falla no caen al correo, que serían decenas por día.
        Los demás nunca se pierden por el canal (decisión 4 del plan anterior).
        """
        return not self.por_correo


TIPOS = [
    TipoDeAviso(CORREOS, "Correos de proveedores", "Correo nuevo en la cola, casilla sin conexión"),
    TipoDeAviso(
        PREVENTAS,
        "Pre-ventas",
        "Las que llegan pronto o hoy, las atrasadas, demoras e ingresos con errores",
    ),
    TipoDeAviso(
        PEDIDOS, "Pedidos de clientes", "Demoras sin respuesta, cancelaciones que fallaron"
    ),
    TipoDeAviso(RESTOCK, "Restock", "Propuesta nueva o pendiente, pedido que no salió"),
    TipoDeAviso(DEVOLUCIONES, "Devoluciones", "Reclamo nuevo, con sus fotos por Telegram"),
    TipoDeAviso(STOCK_LOCAL, "Stock en local", "Solicitud de envío, envíos vencidos"),
    TipoDeAviso(
        VENTAS,
        "Ventas online",
        "Cada pago aprobado, con sus reservas; pre-ventas que agotaron el cupo",
        por_correo=False,
        por_telegram=True,
    ),
    TipoDeAviso(
        RESUMEN,
        "Resumen de la mañana",
        "Lo pendiente y lo que llega, una vez por día a la hora de Parámetros",
        por_correo=False,
        por_telegram=True,
    ),
    TipoDeAviso(
        SEGURIDAD,
        "Seguridad",
        "Bloqueos por intentos, ingresos desde una IP nueva, Administradores nuevos, "
        "cambios masivos de precios",
        por_telegram=True,
    ),
    TipoDeAviso(
        SISTEMA,
        "Estado del sistema",
        "Respaldo que falta, disco casi lleno",
        por_correo=False,
        por_telegram=True,
    ),
]
TIPO_POR_CLAVE = {tipo.clave: tipo for tipo in TIPOS}


def tipo_de_aviso(clave):
    """El tipo de esa clave; uno sin clave conocida sale por correo, como siempre."""
    return TIPO_POR_CLAVE.get(clave) or TipoDeAviso(clave, "", "")


TIPO_CHOICES = [(tipo.clave, tipo.nombre) for tipo in TIPOS]

VIGENCIA_DEL_CODIGO = timedelta(minutes=15)
INTENTOS_DE_CONFIRMACION = 5


class VinculoTelegram(models.Model):
    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="vinculo_telegram",
        verbose_name="usuario",
    )
    # El chat privado con el bot. Un chat es de una sola cuenta.
    chat_id = models.BigIntegerField("chat", unique=True)
    nombre_en_telegram = models.CharField("nombre en Telegram", max_length=200, blank=True)
    vinculado_en = models.DateTimeField("vinculado el", auto_now_add=True)

    class Meta:
        verbose_name = "vínculo con Telegram"
        verbose_name_plural = "vínculos con Telegram"

    def __str__(self):
        return f"{self.usuario} · {self.nombre_en_telegram or self.chat_id}"


class CodigoVinculacion(models.Model):
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="codigos_telegram",
        verbose_name="usuario",
    )
    codigo = models.CharField("código", max_length=40, unique=True)
    creado_en = models.DateTimeField("creado el", auto_now_add=True)
    vence_en = models.DateTimeField("vence el")
    usado_en = models.DateTimeField("usado el", null=True, blank=True)
    # B-19-005: abrir el enlace no vincula. El bot anota qué chat lo abrió y le da
    # un número de confirmación, que se escribe en el perfil, donde sólo entra el
    # dueño de la cuenta: un enlace filtrado no alcanza para tomarla.
    chat_pendiente = models.BigIntegerField("chat que lo abrió", null=True, blank=True)
    nombre_pendiente = models.CharField("nombre en Telegram", max_length=200, blank=True)
    confirmacion = models.CharField("número de confirmación", max_length=6, blank=True)
    intentos = models.PositiveSmallIntegerField("intentos de confirmación", default=0)

    class Meta:
        verbose_name = "código de vinculación"
        verbose_name_plural = "códigos de vinculación"

    def __str__(self):
        return f"{self.usuario} · vence {self.vence_en:%d/%m/%Y %H:%M}"

    @classmethod
    def nuevo(cls, usuario):
        # Uno por vez: pedir otro anula los que no se usaron.
        cls.objects.filter(usuario=usuario, usado_en__isnull=True).delete()
        return cls.objects.create(
            usuario=usuario,
            codigo=secrets.token_urlsafe(24),
            vence_en=timezone.now() + VIGENCIA_DEL_CODIGO,
        )

    @property
    def vigente(self):
        return self.usado_en is None and timezone.now() < self.vence_en

    @property
    def espera_confirmacion(self):
        return self.vigente and self.chat_pendiente is not None


class PreferenciaAviso(models.Model):
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="preferencias_de_aviso",
        verbose_name="usuario",
    )
    tipo = models.CharField("tipo de aviso", max_length=20, choices=TIPO_CHOICES)
    por_correo = models.BooleanField("por correo", default=True)
    por_telegram = models.BooleanField("por Telegram", default=False)

    class Meta:
        verbose_name = "preferencia de aviso"
        verbose_name_plural = "preferencias de aviso"
        constraints = [  # noqa: RUF012
            models.UniqueConstraint(fields=["usuario", "tipo"], name="preferencia_aviso_unica"),
        ]

    def __str__(self):
        return f"{self.usuario} · {self.get_tipo_display()}"
