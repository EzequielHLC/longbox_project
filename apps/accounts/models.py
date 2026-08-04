from django.contrib.auth.models import AbstractUser
from django.db import models


class Usuario(AbstractUser):
    ROL_CHOICES = [  # noqa: RUF012
        ("cliente", "Cliente"),
        ("cajero", "Cajero"),
        ("administrador", "Administrador"),
    ]
    rol = models.CharField(max_length=20, choices=ROL_CHOICES, default="cliente")