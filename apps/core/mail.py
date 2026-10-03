"""Envío de correo del proyecto.

Tres piezas, y las tres pasan por acá:

1. **El mensaje no parte las líneas largas.** Los correos llevan enlaces con
   token (activación de cuenta y recuperación de contraseña) que superan los 78
   caracteres de línea. Ante una línea así, Python elige `quoted-printable` para
   el cuerpo, y ese formato parte las líneas a los 76 caracteres metiendo un `=`
   de continuación:

       http://127.0.0.1:8000/cuentas/activar/Mg/dd06qf-1c387ea3adb11cab445619c6a942c=
       e1c/

   Un cliente de correo vuelve a unir las dos mitades; una terminal no, y el
   enlace copiado desde la consola queda cortado. La política de abajo permite
   líneas de hasta 998 caracteres (RFC 5322) y cuerpo en 8 bits, de modo que el
   texto viaja tal cual. El servidor tiene que anunciar 8BITMIME; si alguno no lo
   hiciera, `smtplib` reconvierte el mensaje antes de enviarlo.

2. **Cada correo lleva dos versiones** (B-00-008): el texto plano de siempre y
   una alternativa HTML con el estilo del sistema. El cliente de correo elige la
   que puede mostrar; el texto plano sigue siendo la fuente de verdad del
   contenido y el que queda en la consola.

3. **El envío deja una copia en la consola** (`CorreoConCopia`). Antes el
   correo sólo se imprimía; ahora sale por SMTP de verdad y la copia se sigue
   viendo en la ventana del servidor, que en una demostración es donde se mira.
"""

import email.policy
import sys
import threading

from django.core.mail import EmailMultiAlternatives
from django.core.mail.backends.smtp import EmailBackend as BackendSMTP
from django.template.loader import render_to_string

# Límite de largo de línea de RFC 5322.
LARGO_MAXIMO_DE_LINEA = 998

POLITICA_SIN_CORTES = email.policy.default.clone(
    cte_type="8bit",
    max_line_length=LARGO_MAXIMO_DE_LINEA,
)

SEPARADOR = "-" * 79


class CorreoSinCortes(EmailMultiAlternatives):
    """Correo que no parte las líneas largas. Admite una alternativa HTML."""

    def message(self, *, policy=POLITICA_SIN_CORTES):
        return super().message(policy=policy)


def cuerpo_html(plantilla, contexto=None):
    """La versión HTML de un correo, con el nombre de la tienda en la cabecera.

    Las plantillas viven en `templates/correo/` y extienden `correo/base.html`.
    """
    from apps.core.models import IdentidadVisual

    identidad = IdentidadVisual.obtener()
    return render_to_string(plantilla, {"tienda": identidad, **(contexto or {})})


def enviar_correo(asunto, cuerpo, destinatarios, remitente=None, html=None):
    """Punto de entrada único para mandar correo desde el sistema.

    Sin `remitente`, Django usa `DEFAULT_FROM_EMAIL`. `html` es la alternativa
    con estilo; `cuerpo` va siempre, en texto plano.
    """
    correo = CorreoSinCortes(
        subject=asunto,
        body=cuerpo,
        from_email=remitente,
        to=destinatarios,
    )
    if html:
        correo.attach_alternative(html, "text/html")
    correo.send()


class CorreoConCopia(BackendSMTP):
    """Manda por SMTP y deja una copia legible en la consola.

    La copia muestra las cabeceras y el texto plano, que es donde están los
    enlaces; de la versión HTML sólo informa que va adjunta. Se imprime **antes**
    de intentar el envío: si el servidor falla, el enlace igual quedó a la vista.

    Sin `EMAIL_HOST` configurado no hay a dónde mandar, y el correo queda sólo
    en la consola, con una línea que lo dice. Un fallo del servidor **levanta**:
    quien llama decide si reintenta (el pedido a proveedor lo hace) o si el error
    llega a la pantalla.
    """

    def __init__(self, *args, stream=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.stream = stream or sys.stdout
        self._candado_de_copia = threading.RLock()

    @property
    def configurado(self):
        return bool(self.host)

    def send_messages(self, email_messages):
        if not email_messages:
            return 0
        for mensaje in email_messages:
            self._copiar(mensaje)
        if not self.configurado:
            self._anotar(
                "[correo] Sin EMAIL_HOST configurado: el correo quedó sólo en esta consola."
            )
            return len(email_messages)
        try:
            enviados = super().send_messages(email_messages)
        except Exception as fallo:
            self._anotar(f"[correo] Falló el envío por {self.host}: {fallo}")
            raise
        destinos = ", ".join(d for m in email_messages for d in m.recipients())
        self._anotar(f"[correo] Enviado por {self.host} a {destinos}.")
        return enviados

    def _copiar(self, mensaje):
        lineas = [
            SEPARADOR,
            f"De: {mensaje.from_email}",
            f"Para: {', '.join(mensaje.recipients())}",
            f"Asunto: {mensaje.subject}",
        ]
        for contenido, tipo in getattr(mensaje, "alternatives", []):
            if tipo == "text/html":
                lineas.append(f"Versión HTML adjunta ({len(contenido)} caracteres).")
        lineas += ["", mensaje.body.rstrip(), SEPARADOR]
        self._anotar("\n".join(lineas))

    def _anotar(self, texto):
        with self._candado_de_copia:
            self.stream.write(texto + "\n")
            self.stream.flush()
