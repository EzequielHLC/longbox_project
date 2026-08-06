from django.contrib.auth.models import AbstractUser
from django.db import models


class Usuario(AbstractUser):
    ROL_CHOICES = [  # noqa: RUF012
        ("cliente", "Cliente"),
        ("cajero", "Cajero"),
        ("administrador", "Administrador"),
    ]
    rol = models.CharField(max_length=20, choices=ROL_CHOICES, default="cliente")

    # El login del sistema es por correo (CU-46), así que el email tiene que
    # ser único e identificar a una sola cuenta. `username` se conserva como
    # identificador interno heredado de AbstractUser.
    email = models.EmailField("correo electrónico", unique=True)

    def save(self, *args, **kwargs):
        # Se normaliza a minúsculas para que "Ana@x.com" y "ana@x.com" no
        # puedan convivir como dos cuentas distintas.
        self.email = self.email.strip().lower()
        return super().save(*args, **kwargs)


class IntentoFallido(models.Model):
    """Un intento de inicio de sesión rechazado por credenciales inválidas.

    Se guarda el correo tal como se tipeó (puede no corresponder a ninguna
    cuenta: si solo contáramos los intentos contra cuentas existentes, la
    diferencia de comportamiento delataría qué correos están registrados).
    """

    email = models.CharField(max_length=254, db_index=True)
    ip = models.GenericIPAddressField(null=True, blank=True)
    ocurrido_en = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        verbose_name = "intento fallido"
        verbose_name_plural = "intentos fallidos"
        ordering = ["-ocurrido_en"]

    def __str__(self):
        return f"{self.email} desde {self.ip} el {self.ocurrido_en:%Y-%m-%d %H:%M}"
