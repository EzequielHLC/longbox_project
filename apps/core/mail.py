"""Envío de correo del proyecto.

Existe por un motivo puntual: los correos que mandamos llevan enlaces con token
(activación de cuenta y recuperación de contraseña) que superan los 78
caracteres de línea. Ante una línea así, Python elige `quoted-printable` para el
cuerpo, y ese formato parte las líneas a los 76 caracteres metiendo un `=` de
continuación:

    http://127.0.0.1:8000/cuentas/activar/Mg/dd06qf-1c387ea3adb11cab445619c6a942c=
    e1c/

Un cliente de correo vuelve a unir las dos mitades y el enlace funciona. Una
terminal no: linkea hasta el fin de la línea, y el token queda cortado y el
enlace se rechaza. Como en desarrollo el "cliente de correo" es la consola del
`runserver`, el enlace resultaba inusable.

La solución es una política de correo que permite líneas largas (RFC 5322 las
admite hasta 998) y acepta el cuerpo en 8 bits, de modo que el texto viaja tal
cual, sin cortes y sin los `=C3=A1` de los acentos.

Contrapartida a tener en cuenta cuando se configure un SMTP real: el cuerpo en 8
bits requiere que el servidor anuncie la extensión 8BITMIME. Los servidores
actuales la soportan; si alguno no lo hiciera, `smtplib` reconvierte el mensaje
antes de enviarlo.
"""

import email.policy

from django.core.mail import EmailMessage

# Límite de largo de línea de RFC 5322.
LARGO_MAXIMO_DE_LINEA = 998

POLITICA_SIN_CORTES = email.policy.default.clone(
    cte_type="8bit",
    max_line_length=LARGO_MAXIMO_DE_LINEA,
)


class CorreoSinCortes(EmailMessage):
    """Correo de texto plano que no parte las líneas largas."""

    def message(self, *, policy=POLITICA_SIN_CORTES):
        return super().message(policy=policy)


def enviar_correo(asunto, cuerpo, destinatarios, remitente=None):
    """Punto de entrada único para mandar correo desde el sistema.

    Sin `remitente`, Django usa `DEFAULT_FROM_EMAIL`.
    """
    CorreoSinCortes(
        subject=asunto,
        body=cuerpo,
        from_email=remitente,
        to=destinatarios,
    ).send()
