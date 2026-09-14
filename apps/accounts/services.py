"""Reglas de negocio de las cuentas que no son ni de la vista ni del modelo.

Agrupa lo que comparten los módulos de Autenticación (12) y Gestión de
Usuarios (13): el bloqueo por intentos fallidos, la invalidación de sesiones
ajenas y el envío del enlace de activación.
"""

from datetime import timedelta

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.sessions.models import Session
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from apps.accounts.models import IntentoFallido
from apps.accounts.tokens import token_de_activacion
from apps.core import cambios
from apps.core.mail import enviar_correo
from apps.core.models import RegistroAuditoria

Usuario = get_user_model()


# ---------------------------------------------------------------------------
# CU-AUT-INI — bloqueo por intentos fallidos
#
# Se cuentan los rechazos del par (correo, IP) —"el mismo dispositivo" del CU—
# dentro de una ventana de tiempo. Si en esa ventana hay
# `LOGIN_INTENTOS_MAXIMOS` intentos, el acceso queda bloqueado.
#
# No hace falta guardar un campo "bloqueado_hasta": mientras dura el bloqueo no
# se registran intentos nuevos, así que el bloqueo se levanta solo cuando el
# último intento sale de la ventana.
# ---------------------------------------------------------------------------


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

    enviar_correo(
        asunto="Longbox — acceso bloqueado temporalmente",
        cuerpo=(
            f"Estimado/a {usuario.get_full_name() or usuario.email}:\n\n"
            "Se han detectado varios intentos fallidos de inicio de sesión en su cuenta, "
            "por lo que el acceso quedó bloqueado durante "
            f"{settings.LOGIN_BLOQUEO_MINUTOS} minutos.\n\n"
            "Si los intentos fueron suyos, aguarde ese lapso y vuelva a ingresar. En caso "
            "de no reconocer esta actividad, se recomienda cambiar la contraseña apenas "
            "recupere el acceso.\n\n"
            "Longbox"
        ),
        destinatarios=[usuario.email],
    )


# ---------------------------------------------------------------------------
# Sesiones ajenas (CU-USR-MOD, CU-USR-BAJ; también la necesitan CU-AUT-REC y CU-CLI-BAJ)
# ---------------------------------------------------------------------------


def invalidar_sesiones_de(usuario):
    """Cierra todas las sesiones abiertas de ese usuario, en cualquier dispositivo.

    No es un logout propio: el Administrador tiene que poder cortarle la sesión
    a *otro* usuario. Con el backend de sesiones por defecto de Django la
    sesión vive en la tabla `django_session` y el usuario logueado está adentro
    del `session_data` cifrado, así que no hay forma de filtrar por SQL: hay
    que decodificar cada sesión vigente y comparar.

    Son pocas filas (solo las no vencidas) y la operación es puntual —un cambio
    de rol o una baja—, así que el recorrido no es un problema de rendimiento.

    CU-AUT-REC no la usa: al cambiar la contraseña cambia el hash y, con él, el HMAC
    de sesión, y Django invalida todo solo.
    """
    id_usuario = str(usuario.pk)
    sesiones_vigentes = Session.objects.filter(expire_date__gte=timezone.now())
    cerradas = 0
    for sesion in sesiones_vigentes:
        if sesion.get_decoded().get("_auth_user_id") == id_usuario:
            sesion.delete()
            cerradas += 1
    return cerradas


# ---------------------------------------------------------------------------
# CU-USR-ALT / CU-USR-MOD — alta y activación de cuentas de personal
# ---------------------------------------------------------------------------


def username_disponible_para(email):
    """`username` interno de una cuenta nueva, derivado del correo.

    `AbstractUser` exige un `username` único aunque el login del sistema sea
    por correo. Se usa el correo mismo (los caracteres de un email son válidos
    para el validador de Django) recortado al largo del campo, y se agrega un
    sufijo solo en el caso de borde de dos correos largos que compartan los
    primeros 150 caracteres.
    """
    largo_maximo = Usuario._meta.get_field("username").max_length
    candidato = email.strip().lower()[:largo_maximo]
    sufijo = 2
    while Usuario.objects.filter(username=candidato).exists():
        cola = f"-{sufijo}"
        candidato = f"{candidato[: largo_maximo - len(cola)]}{cola}"
        sufijo += 1
    return candidato


def preparar_para_activacion(usuario):
    """Deja la cuenta pendiente y sin contraseña utilizable.

    `set_unusable_password()` guarda un hash aleatorio distinto en cada
    llamada. Como el token se deriva de ese hash, llamarla de nuevo invalida
    cualquier enlace de activación emitido antes (CU-USR-MOD, flujo alternativo:
    "el enlace anterior queda invalidado"), sin necesidad de una tabla de
    tokens propia.
    """
    usuario.estado = Usuario.PENDIENTE_ACTIVACION
    usuario.set_unusable_password()


def enviar_enlace_de_activacion(usuario, request):
    """Manda el correo con el enlace para que el usuario elija su contraseña."""
    sitio = get_current_site(request)
    contexto = {
        "usuario": usuario,
        "uid": urlsafe_base64_encode(force_bytes(usuario.pk)),
        "token": token_de_activacion.make_token(usuario),
        "protocol": "https" if request.is_secure() else "http",
        "domain": sitio.domain,
        "vigencia_horas": settings.VIGENCIA_ENLACE_ACTIVACION // 3600,
    }
    enviar_correo(
        asunto=render_to_string("accounts/activacion_subject.txt", contexto).strip(),
        cuerpo=render_to_string("accounts/activacion_email.txt", contexto),
        destinatarios=[usuario.email],
    )


# ---------------------------------------------------------------------------
# CU-CLI-ALT — registro de Cliente
# ---------------------------------------------------------------------------


def enviar_bienvenida(usuario, request):
    """Correo de bienvenida del paso 5 del CU-CLI-ALT.

    No lleva enlace de activación, a diferencia del alta de personal: la cuenta
    de Cliente nace Activa y el propio registro ya la autentica. Es un aviso de
    que la cuenta existe —evidencia para el titular si alguien registrara su
    correo sin su consentimiento— y la puerta de entrada a la tienda.
    """
    sitio = get_current_site(request)
    contexto = {
        "usuario": usuario,
        "protocol": "https" if request.is_secure() else "http",
        "domain": sitio.domain,
    }
    enviar_correo(
        asunto=render_to_string("accounts/bienvenida_subject.txt", contexto).strip(),
        cuerpo=render_to_string("accounts/bienvenida_email.txt", contexto),
        destinatarios=[usuario.email],
    )


# ---------------------------------------------------------------------------
# CU-USR-MOD / CU-USR-BAJ — resguardo del último Administrador
# ---------------------------------------------------------------------------


def es_el_unico_administrador_activo(usuario):
    """¿Sacarle el rol o darlo de baja dejaría al sistema sin Administrador?

    Se llama siempre dentro de una transacción: `select_for_update()` bloquea
    las filas de los demás Administradores activos hasta el commit, así dos
    Administradores editando al mismo tiempo no pueden quitarse el rol
    mutuamente y dejar el sistema sin ninguno.
    """
    if not usuario.es_administrador_activo:
        return False
    otros_administradores = list(
        Usuario.objects.select_for_update()
        .filter(rol=Usuario.ADMINISTRADOR, estado=Usuario.ACTIVO)
        .exclude(pk=usuario.pk)
    )
    return not otros_administradores


# ---------------------------------------------------------------------------
# CU-USR-MOD — auditoría con valores anteriores y nuevos
# ---------------------------------------------------------------------------

CAMPOS_AUDITADOS = {  # noqa: RUF012
    "nombre": lambda usuario: usuario.get_full_name(),
    "correo": lambda usuario: usuario.email,
    "rol": lambda usuario: usuario.get_rol_display(),
}


def cambios_entre(anterior, nuevo):
    """`{campo: (valor_anterior, valor_nuevo)}` de los campos que cambiaron."""
    return cambios.entre(anterior, nuevo, CAMPOS_AUDITADOS)


def describir_cambios(lo_que_cambio):
    """Texto para el log: no alcanza con el estado final, va el par completo."""
    return cambios.describir(lo_que_cambio)
