"""Utilidades compartidas por los tests del Módulo 13 (Gestión de Usuarios)."""

import re

from django.core import mail
from django.urls import reverse

from apps.accounts.models import Usuario

URL_LISTA = reverse("accounts:usuario_lista")
URL_ALTA = reverse("accounts:usuario_alta")

DATOS_DE_ALTA = {
    "nombre_completo": "Ana María Pérez",
    "email": "ana@longbox.test",
    "rol": "cajero",
}


def url_edicion(usuario):
    return reverse("accounts:usuario_edicion", args=[usuario.pk])


def url_baja(usuario):
    return reverse("accounts:usuario_baja", args=[usuario.pk])


def url_reenviar_activacion(usuario):
    return reverse("accounts:usuario_reenviar_activacion", args=[usuario.pk])


def datos_de(usuario, **cambios):
    """El formulario completo tal como está hoy, con los cambios que se indiquen."""
    formulario = {
        "nombre_completo": usuario.get_full_name(),
        "email": usuario.email,
        "rol": usuario.rol,
    }
    formulario.update(cambios)
    return formulario


def enlace_de_activacion(correo):
    """Ruta del enlace de activación que viaja en el cuerpo del correo."""
    encontrado = re.search(r"/cuentas/activar/[\w\-]+/[\w\-]+/", correo.body)
    assert encontrado, f"El correo no trae un enlace de activación:\n{correo.body}"
    return encontrado.group()


def crear_usuario_pendiente(client_admin, **cambios):
    """Da de alta una cuenta por la vista real y devuelve (usuario, enlace)."""
    datos = {**DATOS_DE_ALTA, **cambios}
    client_admin.post(URL_ALTA, datos)
    usuario = Usuario.objects.get(email=datos["email"])
    return usuario, enlace_de_activacion(mail.outbox[-1])
