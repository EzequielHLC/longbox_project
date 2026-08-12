from django.conf import settings
from django.db import models


class RegistroAuditoriaError(Exception):
    """Se intentó modificar o borrar una entrada del log de auditoría."""


class RegistroAuditoria(models.Model):
    """Bitácora de operaciones sensibles del sistema.

    Versión mínima para el Módulo 12 (autenticación). El CU-55 del módulo de
    Auditoría la va a ampliar con más acciones y con la vista de consulta.

    El log es *inmutable*: ningún rol, ni siquiera Administrador, puede editar
    o borrar una entrada. Eso se garantiza acá abajo, en el modelo, para que
    valga aunque alguien lo intente desde el admin o desde un shell.
    """

    INICIO_SESION = "inicio_sesion"
    CIERRE_SESION = "cierre_sesion"
    BLOQUEO_POR_INTENTOS = "bloqueo_por_intentos"
    CAMBIO_CONTRASENA = "cambio_contrasena"
    ALTA_USUARIO = "alta_usuario"
    MODIFICACION_USUARIO = "modificacion_usuario"
    BAJA_USUARIO = "baja_usuario"
    REACTIVACION_USUARIO = "reactivacion_usuario"
    REENVIO_ACTIVACION = "reenvio_activacion"
    ACTIVACION_CUENTA = "activacion_cuenta"
    ELIMINACION_PENDIENTE = "eliminacion_pendiente"
    REGISTRO_CLIENTE = "registro_cliente"

    ACCION_CHOICES = [  # noqa: RUF012
        (INICIO_SESION, "Inicio de sesión"),
        (CIERRE_SESION, "Cierre de sesión"),
        (BLOQUEO_POR_INTENTOS, "Bloqueo por intentos fallidos"),
        (CAMBIO_CONTRASENA, "Cambio de contraseña"),
        (ALTA_USUARIO, "Alta de usuario del sistema"),
        (MODIFICACION_USUARIO, "Modificación de usuario del sistema"),
        (BAJA_USUARIO, "Baja de usuario del sistema"),
        (REACTIVACION_USUARIO, "Reactivación de usuario del sistema"),
        (REENVIO_ACTIVACION, "Reenvío del enlace de activación"),
        (ACTIVACION_CUENTA, "Activación de cuenta"),
        (ELIMINACION_PENDIENTE, "Eliminación de cuenta pendiente de activación"),
        (REGISTRO_CLIENTE, "Registro de cuenta de cliente"),
    ]

    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="registros_auditoria",
    )
    # Se guarda desnormalizado para que la traza sobreviva a la baja del
    # usuario, y para poder registrar intentos con correos inexistentes.
    actor_email = models.CharField(max_length=254, blank=True)

    # Usuario *sobre el que* se ejecutó la acción, cuando no es el mismo que la
    # ejecuta: en el Módulo 13 el Administrador opera sobre cuentas ajenas, y
    # el historial tiene que poder consultarse por cuenta afectada.
    objetivo = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="registros_auditoria_recibidos",
    )
    objetivo_email = models.CharField(max_length=254, blank=True)

    accion = models.CharField(max_length=40, choices=ACCION_CHOICES)
    ip = models.GenericIPAddressField(null=True, blank=True)
    # Texto libre: en las modificaciones (CU-51) guarda los valores anteriores
    # y los nuevos de cada campo, así que no entra en un largo fijo corto.
    detalle = models.TextField(blank=True)
    ocurrido_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "registro de auditoría"
        verbose_name_plural = "registros de auditoría"
        ordering = ["-ocurrido_en"]

    def __str__(self):
        return f"{self.ocurrido_en:%Y-%m-%d %H:%M} · {self.accion} · {self.actor_email}"

    def save(self, *args, **kwargs):
        if self.pk is not None:
            raise RegistroAuditoriaError("El log de auditoría es inmutable: no se puede modificar.")
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise RegistroAuditoriaError("El log de auditoría es inmutable: no se puede borrar.")

    @classmethod
    def registrar(
        cls,
        accion,
        actor=None,
        actor_email="",
        ip=None,
        detalle="",
        objetivo=None,
        objetivo_email="",
    ):
        """Punto de entrada único para escribir en el log."""
        return cls.objects.create(
            accion=accion,
            actor=actor,
            actor_email=actor_email or (actor.email if actor else ""),
            objetivo=objetivo,
            objetivo_email=objetivo_email or (objetivo.email if objetivo else ""),
            ip=ip,
            detalle=detalle,
        )
