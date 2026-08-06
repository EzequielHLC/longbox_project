"""Reglas del CU-46 que no son responsabilidad ni de la vista ni del modelo.

Bloqueo por intentos fallidos: se cuentan los rechazos del par (correo, IP)
—"el mismo dispositivo" del CU— dentro de una ventana de tiempo. Si en esa
ventana hay `LOGIN_INTENTOS_MAXIMOS` intentos, el acceso queda bloqueado.

No hace falta guardar un campo "bloqueado_hasta": mientras dura el bloqueo no
se registran intentos nuevos, así que el bloqueo se levanta solo cuando el
último intento sale de la ventana.
"""

from datetime import timedelta

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.utils import timezone

from apps.accounts.models import IntentoFallido
from apps.core.models import RegistroAuditoria

Usuario = get_user_model()


def _inicio_de_ventana():
    return timezone.now() - timedelta(minutes=settings.LOGIN_BLOQUEO_MINUTOS)


def intentos_recientes(email, ip):
    """Cantidad de intentos fallidos vigentes para ese correo desde esa IP."""
    return IntentoFallido.objects.filter(
        email__iexact=email,
        ip=ip,
        ocurrido_en__gte=_inicio_de_ventana(),
    ).count()


def esta_bloqueado(email, ip):
    return intentos_recientes(email, ip) >= settings.LOGIN_INTENTOS_MAXIMOS


def registrar_intento_fallido(email, ip):
    """Anota el intento y, si con este se alcanza el tope, dispara el bloqueo."""
    IntentoFallido.objects.create(email=email, ip=ip)
    if esta_bloqueado(email, ip):
        _notificar_bloqueo(email, ip)


def limpiar_intentos(email, ip):
    """Un login exitoso corta la racha: los intentos dejan de contar."""
    IntentoFallido.objects.filter(email__iexact=email, ip=ip).delete()


def _notificar_bloqueo(email, ip):
    usuario = Usuario.objects.filter(email__iexact=email).first()

    RegistroAuditoria.registrar(
        accion=RegistroAuditoria.BLOQUEO_POR_INTENTOS,
        actor=usuario,
        actor_email=email,
        ip=ip,
        detalle=f"{settings.LOGIN_INTENTOS_MAXIMOS} intentos fallidos consecutivos",
    )

    # Solo se avisa si el correo corresponde a una cuenta real: mandar un mail
    # a una dirección desconocida no aporta nada y confirmaría al atacante que
    # eligió una dirección válida de otra persona.
    if usuario is None:
        return

    send_mail(
        subject="Longbox — acceso bloqueado temporalmente",
        message=(
            f"Hola {usuario.first_name or usuario.email},\n\n"
            "Detectamos varios intentos fallidos de inicio de sesión en tu cuenta, "
            f"así que bloqueamos el acceso por {settings.LOGIN_BLOQUEO_MINUTOS} minutos.\n\n"
            "Si fuiste vos, esperá ese tiempo y volvé a intentar. Si no reconocés "
            "esta actividad, te recomendamos cambiar tu contraseña apenas puedas "
            "ingresar.\n\n"
            "Longbox"
        ),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[usuario.email],
        fail_silently=False,
    )
