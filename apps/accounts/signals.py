from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.dispatch import receiver

from apps.core.models import RegistroAuditoria
from apps.core.utils import obtener_ip


@receiver(user_logged_in)
def auditar_inicio_de_sesion(sender, request, user, **kwargs):
    """CU-46 paso 3: todo inicio de sesión queda en el log de auditoría.

    Se engancha a la signal y no a la vista para que también quede registrado
    lo que entre por otra puerta (el admin de Django, por ejemplo).
    """
    RegistroAuditoria.registrar(
        accion=RegistroAuditoria.INICIO_SESION,
        actor=user,
        ip=obtener_ip(request),
        detalle=f"rol: {user.rol}",
    )


@receiver(user_logged_out)
def auditar_cierre_de_sesion(sender, request, user, **kwargs):
    """CU-47 paso 3."""
    if user is None:  # logout sin sesión activa
        return
    RegistroAuditoria.registrar(
        accion=RegistroAuditoria.CIERRE_SESION,
        actor=user,
        ip=obtener_ip(request),
    )
