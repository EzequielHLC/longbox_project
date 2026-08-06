from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import (
    LoginView,
    LogoutView,
    PasswordResetCompleteView,
    PasswordResetConfirmView,
    PasswordResetDoneView,
    PasswordResetView,
)
from django.http import JsonResponse
from django.shortcuts import resolve_url
from django.urls import reverse_lazy
from django.views.decorators.http import require_POST

from apps.accounts.forms import FormularioLogin
from apps.core.models import RegistroAuditoria
from apps.core.utils import obtener_ip

# CU-46 paso 4: cada rol aterriza en su propio módulo.
DESTINOS_POR_ROL = {
    "cliente": "core:tienda",
    "cajero": "core:mostrador",
    "administrador": "core:panel",
}

MENSAJE_SESION_EXPIRADA = "Tu sesión expiró por inactividad."


class LoginUsuarioView(LoginView):
    """CU-46 — Iniciar Sesión."""

    template_name = "accounts/login.html"
    form_class = FormularioLogin
    # Precondición del CU: no tiene una sesión activa vigente en el dispositivo.
    redirect_authenticated_user = True

    def get(self, request, *args, **kwargs):
        # La pantalla de login avisa cuando se llegó acá por vencimiento de la
        # sesión; el aviso previo con opción de extenderla lo maneja el JS de
        # `base.html`, que redirige con este parámetro.
        if request.GET.get("expirada") == "1":
            messages.info(request, MENSAJE_SESION_EXPIRADA)
        return super().get(request, *args, **kwargs)

    def get_success_url(self):
        # `get_redirect_url()` valida el ?next= contra hosts externos.
        destino = self.get_redirect_url()
        if destino:
            return destino
        return resolve_url(DESTINOS_POR_ROL.get(self.request.user.rol, settings.LOGIN_REDIRECT_URL))


class LogoutUsuarioView(LogoutView):
    """CU-47 — Cerrar Sesión.

    `LogoutView` invalida únicamente la sesión del dispositivo actual: las
    sesiones abiertas en otros dispositivos siguen vigentes, como pide el CU.
    Solo acepta POST, así un enlace de terceros no puede desloguear al usuario.
    """

    next_page = reverse_lazy("accounts:login")


class RecuperarContrasenaView(PasswordResetView):
    """CU-48 pasos 1 a 3 — pedir el enlace de recuperación."""

    template_name = "accounts/password_reset_form.html"
    email_template_name = "accounts/password_reset_email.txt"
    subject_template_name = "accounts/password_reset_subject.txt"
    success_url = reverse_lazy("accounts:password_reset_done")
    # `PasswordResetForm` solo le manda el correo a cuentas activas y siempre
    # termina en la misma pantalla, exista o no el correo: eso es lo que evita
    # la enumeración de cuentas.


class RecuperarContrasenaEnviadaView(PasswordResetDoneView):
    template_name = "accounts/password_reset_done.html"


class RestablecerContrasenaView(PasswordResetConfirmView):
    """CU-48 pasos 4 y 5 — validar el token y fijar la nueva contraseña.

    El token es de un solo uso sin código extra: `PasswordResetTokenGenerator`
    lo deriva del hash de la contraseña actual, así que al cambiarla el enlace
    anterior deja de validar. Por el mismo motivo cambia el HMAC de sesión y
    todas las sesiones abiertas del usuario quedan invalidadas.
    """

    template_name = "accounts/password_reset_confirm.html"
    success_url = reverse_lazy("accounts:password_reset_complete")

    def form_valid(self, form):
        respuesta = super().form_valid(form)
        RegistroAuditoria.registrar(
            accion=RegistroAuditoria.CAMBIO_CONTRASENA,
            actor=self.user,
            ip=obtener_ip(self.request),
            detalle="restablecimiento por correo",
        )
        return respuesta


class RestablecerContrasenaCompletaView(PasswordResetCompleteView):
    template_name = "accounts/password_reset_complete.html"


@require_POST
@login_required
def renovar_sesion(request):
    """Extiende la sesión un período completo más.

    La llama el botón "Seguir conectado" del aviso previo al vencimiento. Con
    `SESSION_SAVE_EVERY_REQUEST = True` alcanza con que el request llegue
    autenticado para que Django reinicie el contador de inactividad.
    """
    return JsonResponse({"segundos_restantes": settings.SESSION_COOKIE_AGE})
