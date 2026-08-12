"""Los enlaces con token tienen que llegar enteros al correo.

Estos tests miran el mensaje MIME que sale, no el cuerpo que armamos nosotros.
La diferencia es exactamente el agujero por el que se coló el bug: `correo.body`
siempre está entero, pero el enlace se partía en dos al codificar el mensaje,
y el destinatario recibía un token incompleto que el sistema rechazaba.
"""

import re

import pytest
from django.core import mail
from django.test import Client
from django.urls import reverse

from apps.accounts.tests.helpers_usuarios import DATOS_DE_ALTA, URL_ALTA

# Un host que hace que la línea del enlace pase los 78 caracteres: es la
# condición que disparaba el corte. Con un host corto el bug no se reproduce.
HOST_LARGO = "127.0.0.1:8000"

pytestmark = pytest.mark.django_db


def mensaje_enviado(correo):
    """El MIME tal como sale, ya codificado."""
    return correo.message().as_bytes().decode()


def enlace_del_mensaje(correo):
    encontrado = re.search(r"https?://\S+", mensaje_enviado(correo))
    assert encontrado, "El correo no trae ningún enlace"
    return encontrado.group()


def ruta(enlace):
    return enlace.replace(f"http://{HOST_LARGO}", "")


def test_el_enlace_de_activacion_llega_entero(client_admin):
    client_admin.post(URL_ALTA, DATOS_DE_ALTA, HTTP_HOST=HOST_LARGO)

    enlace = enlace_del_mensaje(mail.outbox[0])

    # Un enlace cortado termina en el `=` de continuación, no en la barra.
    assert enlace.endswith("/")
    assert "=" not in enlace
    # Y, sobre todo, sirve: el token está completo.
    assert Client().get(ruta(enlace)).status_code == 302


def test_el_enlace_de_recuperacion_llega_entero(client, cliente):
    client.post(reverse("accounts:password_reset"), {"email": cliente.email}, HTTP_HOST=HOST_LARGO)

    enlace = enlace_del_mensaje(mail.outbox[0])

    assert enlace.endswith("/")
    assert "=" not in enlace
    assert Client().get(ruta(enlace)).status_code == 302


def test_los_acentos_llegan_legibles(client_admin):
    """Sin codificar, el cuerpo se lee tal cual: importa porque en desarrollo
    el correo se lee crudo en la consola del `runserver`."""
    client_admin.post(URL_ALTA, DATOS_DE_ALTA, HTTP_HOST=HOST_LARGO)

    assert "comuníquelo al administrador del sistema" in mensaje_enviado(mail.outbox[0])


def test_ninguna_linea_del_cuerpo_queda_partida(client_admin):
    client_admin.post(URL_ALTA, DATOS_DE_ALTA, HTTP_HOST=HOST_LARGO)

    lineas = mensaje_enviado(mail.outbox[0]).splitlines()
    assert not [linea for linea in lineas if linea.endswith("=")]
