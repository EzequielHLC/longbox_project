"""Los correos salen de verdad, dejan copia en la consola y llevan el estilo del sistema.

B-00-008. Tres cosas que se rompen por separado:

- **El envío.** `CorreoConCopia` imprime la copia y después manda por SMTP. El
  servidor se reemplaza por un doble: ninguna prueba sale a la red.
- **Las dos versiones.** Cada correo lleva el texto plano de siempre y una
  alternativa HTML con el mismo enlace.
- **El estilo.** Los correos son la única parte con estilos en línea, así que la
  regla de `test_estilo_vineta.py` no los cubre: acá se verifica que los colores
  sigan siendo los de `tokens.css` y que no carguen nada de afuera.
"""

import io
import re
from pathlib import Path
from unittest.mock import patch

import pytest
from django.conf import settings
from django.core import mail
from django.test import RequestFactory
from django.urls import reverse

from apps.accounts import services
from apps.accounts.tests.helpers_usuarios import DATOS_DE_ALTA, URL_ALTA
from apps.core.mail import CorreoConCopia, CorreoSinCortes, cuerpo_html
from apps.core.models import IdentidadVisual
from apps.core.templatetags.correo import ESTILOS, PALETA
from apps.suppliers.pedidos import INTENTOS, LineaDePedido, enviar_pedido
from apps.suppliers.tests.factories import ProveedorFactory

pytestmark = pytest.mark.django_db

RAIZ = Path(settings.BASE_DIR)
CORREOS = RAIZ / "templates" / "correo"
TOKENS = (RAIZ / "static" / "css" / "tokens.css").read_text(encoding="utf-8")
SMTP = "django.core.mail.backends.smtp.smtplib.SMTP"
LARGO_MAXIMO_DE_LINEA = 998


def html_de(correo):
    ((contenido, tipo),) = correo.alternatives
    assert tipo == "text/html"
    return contenido


def enlace_del_texto(correo):
    encontrado = re.search(r"https?://\S+", correo.body)
    assert encontrado, correo.body
    return encontrado.group()


def un_correo(**cambios):
    datos = {
        "subject": "Prueba",
        "body": "Hola, este es el texto plano.",
        "from_email": "tienda@longbox.test",
        "to": ["ana@longbox.test"],
        **cambios,
    }
    correo = CorreoSinCortes(**datos)
    correo.attach_alternative("<p>Hola</p>", "text/html")
    return correo


# ---------------------------------------------------------------------------
# El estilo
# ---------------------------------------------------------------------------


def test_la_paleta_de_los_correos_es_la_de_los_tokens():
    for nombre, valor in PALETA.items():
        assert re.search(rf"--{nombre}:\s*{valor};", TOKENS, re.IGNORECASE), nombre


def test_los_estilos_solo_usan_colores_de_la_paleta():
    permitidos = {valor.upper() for valor in PALETA.values()}
    for nombre, estilo in ESTILOS.items():
        for color in re.findall(r"#[0-9A-Fa-f]{3,8}\b", estilo):
            assert color.upper() in permitidos, (nombre, color)
        # Lo que un cliente de correo no entiende, o lo que Viñeta Nocturna prohíbe.
        for prohibido in ("var(", "gradient", "radius", "clip-path", "box-shadow", '"'):
            assert prohibido not in estilo, (nombre, prohibido)


@pytest.mark.parametrize("ruta", sorted(CORREOS.glob("*.html")), ids=lambda ruta: ruta.name)
def test_la_plantilla_de_correo_no_escribe_colores_ni_carga_recursos(ruta):
    texto = ruta.read_text(encoding="utf-8")

    assert not re.search(r"#[0-9a-fA-F]{6}\b|\brgba?\(", texto)
    assert not re.search(r"<style[\s>]|<link|<script|<img|\sclass=", texto)
    assert not re.search(r"(?:src|href)=\"https?://", texto)


def test_el_nombre_y_el_contacto_de_la_tienda_firman_el_correo(cliente):
    identidad = IdentidadVisual.obtener()
    identidad.nombre_tienda = "Akiba"
    identidad.correo_contacto = "hola@akiba.test"
    identidad.save()

    html = cuerpo_html("correo/bloqueo.html", {"usuario": cliente, "minutos": 15})

    assert "&nbsp;Akiba</td>" in html
    assert "Akiba &middot; hola@akiba.test" in html


# ---------------------------------------------------------------------------
# Las dos versiones de cada correo
# ---------------------------------------------------------------------------


def test_la_activacion_lleva_la_version_con_estilo_y_el_mismo_enlace(client_admin):
    client_admin.post(URL_ALTA, DATOS_DE_ALTA)

    correo = mail.outbox[0]
    html = html_de(correo)

    assert f'href="{enlace_del_texto(correo)}"' in html
    assert "Establecer contraseña" in html
    assert "Ana María Pérez" in html
    assert PALETA["senal"] in html


def test_la_recuperacion_lleva_la_version_con_estilo_y_el_mismo_enlace(client, cliente):
    client.post(reverse("accounts:password_reset"), {"email": cliente.email})

    correo = mail.outbox[0]

    assert f'href="{enlace_del_texto(correo)}"' in html_de(correo)


def test_la_bienvenida_lleva_la_version_con_estilo(cliente):
    services.enviar_bienvenida(cliente, RequestFactory().get("/"))

    correo = mail.outbox[0]

    assert enlace_del_texto(correo).endswith(reverse("accounts:login"))
    assert f'href="{enlace_del_texto(correo)}"' in html_de(correo)


def test_el_aviso_de_bloqueo_lleva_la_version_con_estilo(cliente):
    services._notificar_bloqueo(cliente.email, "10.0.0.1")

    html = html_de(mail.outbox[0])

    assert f"Pausa de {settings.LOGIN_BLOQUEO_MINUTOS} minutos" in html
    assert "Bloqueo:" in html


def test_el_pedido_va_en_tabla_y_escapa_lo_que_escribe_el_usuario():
    proveedor = ProveedorFactory(razon_social="Ivrea", nombre_contacto="Laura")
    lineas = [
        LineaDePedido(titulo="Akira <edición>", volumen=3, isbn="9789878000001", cantidad=2),
        LineaDePedido(titulo="Sin código", volumen=None, isbn="", cantidad=1),
    ]

    assert enviar_pedido(proveedor, lineas)

    correo = mail.outbox[0]
    html = html_de(correo)
    assert "Akira &lt;edición&gt; &middot; vol. 3" in html
    assert "9789878000001" in html
    assert "Total: 2 título(s) &middot; 3 unidad(es)" in html
    # El texto plano sigue siendo el de siempre.
    assert "9789878000001 — Akira <edición> vol. 3: 2 unidad(es)" in correo.body


def test_ninguna_linea_del_correo_pasa_el_limite_del_protocolo(client_admin):
    """Una línea de más de 998 caracteres obliga a recodificar la parte entera."""
    client_admin.post(URL_ALTA, DATOS_DE_ALTA)

    # `as_bytes`, como lo manda el SMTP: `as_string` recodifica las partes en 8 bits.
    mensaje = mail.outbox[0].message().as_bytes().decode()

    assert max(len(linea) for linea in mensaje.splitlines()) <= LARGO_MAXIMO_DE_LINEA
    assert "base64" not in mensaje
    assert "quoted-printable" not in mensaje


# ---------------------------------------------------------------------------
# El envío con copia en la consola
# ---------------------------------------------------------------------------


def test_sin_servidor_el_correo_queda_solo_en_la_consola(settings):
    settings.EMAIL_HOST = ""
    consola = io.StringIO()

    with patch(SMTP) as smtp:
        enviados = CorreoConCopia(stream=consola).send_messages([un_correo()])

    assert enviados == 1
    smtp.assert_not_called()
    copia = consola.getvalue()
    for texto in (
        "Para: ana@longbox.test",
        "Asunto: Prueba",
        "Hola, este es el texto plano.",
        "Versión HTML adjunta",
        "Sin EMAIL_HOST configurado",
    ):
        assert texto in copia, texto


def test_con_servidor_sale_por_smtp_y_deja_la_copia(settings):
    settings.EMAIL_HOST = "smtp.longbox.test"
    settings.EMAIL_USE_TLS = False
    consola = io.StringIO()

    with patch(SMTP) as smtp:
        enviados = CorreoConCopia(stream=consola).send_messages([un_correo()])

    assert enviados == 1
    remitente, destinatarios, mensaje = smtp.return_value.sendmail.call_args.args
    assert destinatarios == ["ana@longbox.test"]
    assert b"text/html" in mensaje
    copia = consola.getvalue()
    assert "Hola, este es el texto plano." in copia
    assert "Enviado por smtp.longbox.test a ana@longbox.test." in copia


def test_una_consola_que_no_escribe_un_caracter_no_frena_el_envio(settings):
    """La copia va antes del envío: en una consola cp1252 un carácter raro del
    asunto dejaba el correo sin salir."""
    settings.EMAIL_HOST = "smtp.longbox.test"
    settings.EMAIL_USE_TLS = False
    crudo = io.BytesIO()
    consola = io.TextIOWrapper(crudo, encoding="cp1252")
    correo = un_correo()
    correo.subject = "Reprogramación � ☃"

    with patch(SMTP) as smtp:
        enviados = CorreoConCopia(stream=consola).send_messages([correo])

    assert enviados == 1
    smtp.return_value.sendmail.assert_called_once()
    assert b"Asunto: Reprogramacion ? ?" in crudo.getvalue()


def test_un_fallo_del_servidor_levanta_y_la_copia_igual_queda(settings):
    settings.EMAIL_HOST = "smtp.longbox.test"
    consola = io.StringIO()

    with patch(SMTP, side_effect=ConnectionRefusedError("conexión rechazada")):
        with pytest.raises(ConnectionRefusedError):
            CorreoConCopia(stream=consola).send_messages([un_correo()])

    copia = consola.getvalue()
    assert "Hola, este es el texto plano." in copia
    assert "Falló el envío por smtp.longbox.test: conexión rechazada" in copia


def test_sin_mensajes_no_hace_nada(settings):
    consola = io.StringIO()

    assert CorreoConCopia(stream=consola).send_messages([]) == 0
    assert consola.getvalue() == ""


def test_el_pedido_reintenta_cuando_el_servidor_real_falla(settings, capsys):
    settings.EMAIL_BACKEND = "apps.core.mail.CorreoConCopia"
    settings.EMAIL_HOST = "smtp.longbox.test"
    proveedor = ProveedorFactory()
    linea = LineaDePedido(titulo="Akira", volumen=1, isbn="", cantidad=1)

    with patch(SMTP, side_effect=ConnectionRefusedError("conexión rechazada")):
        resultado = enviar_pedido(proveedor, [linea])

    assert not resultado
    assert resultado.intentos == INTENTOS
    assert capsys.readouterr().out.count("Falló el envío") == INTENTOS
