"""Los correos del ciclo de la pre-venta y de la demora (planes 01 y 08).

Todos tienen la misma forma —unos párrafos, a veces una tabla, a veces un
botón—, así que salen de una sola plantilla. Un correo caído no deshace la
operación que lo originó: se registra y se sigue.
"""

import logging

from apps.accounts.models import Usuario
from apps.core.mail import cuerpo_html, enviar_correo

logger = logging.getLogger(__name__)


def avisar(
    destinatarios,
    *,
    asunto,
    titulo,
    parrafos,
    antetitulo="",
    rotulo="Pedido",
    filas=(),
    enlace="",
    texto_enlace="",
):
    destinatarios = [d for d in destinatarios if d]
    if not destinatarios:
        return
    texto = "\n\n".join(parrafos)
    if filas:
        texto += "\n\n" + "\n".join(f"- {izquierda}: {derecha}" for izquierda, derecha in filas)
    if enlace:
        texto += f"\n\n{texto_enlace}: {enlace}"
    contexto = {
        "asunto": asunto,
        "titulo": titulo,
        "antetitulo": antetitulo,
        "rotulo": rotulo,
        "parrafos": parrafos,
        "filas": filas,
        "enlace": enlace,
        "texto_enlace": texto_enlace,
    }
    try:
        enviar_correo(
            asunto=asunto,
            cuerpo=texto + "\n",
            destinatarios=destinatarios,
            html=cuerpo_html("correo/aviso.html", contexto),
        )
    except Exception:  # noqa: BLE001 - la operación ya ocurrió: un correo caído no la deshace
        logger.exception("No se pudo enviar el aviso «%s».", asunto)


def correos_de_administradores():
    return list(
        Usuario.objects.filter(rol=Usuario.ADMINISTRADOR, estado=Usuario.ACTIVO)
        .order_by("pk")
        .values_list("email", flat=True)
    )


def avisar_administradores(**kwargs):
    kwargs.setdefault("rotulo", "Pre-venta")
    avisar(correos_de_administradores(), **kwargs)
