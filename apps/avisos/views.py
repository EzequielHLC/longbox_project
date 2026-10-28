"""Módulo 19 · Perfil y avisos: las pantallas del Administrador y el webhook del bot.

- `CU-AVI-PEC` Consultar mi perfil: sus datos, sus avisos y Telegram. Los datos se
  corrigen por `CU-USR-MOD`; la contraseña propia, acá, como `CO-111`.
- `CU-AVI-CAM` Modificar los canales de aviso: por tipo, correo y Telegram.
- `CU-AVI-TGA` y `CU-AVI-TGB`: pedir el enlace de vinculación y desvincular.

Sólo el Administrador (decisión 1 del plan).
"""

import hmac
import json
import logging

from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.db import transaction
from django.http import HttpResponse, HttpResponseForbidden
from django.shortcuts import redirect, render
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt

from apps.accounts.models import Usuario
from apps.avisos import bot, telegram
from apps.avisos.models import TIPOS, CodigoVinculacion, PreferenciaAviso, VinculoTelegram
from apps.core.mixins import RolRequeridoMixin
from apps.core.models import RegistroAuditoria
from apps.core.utils import obtener_ip

logger = logging.getLogger(__name__)


class PerfilMixin(RolRequeridoMixin):
    roles_permitidos = (Usuario.ADMINISTRADOR,)


def _preferencias(usuario):
    """Cada tipo de aviso con su canal: lo guardado, o el de su tipo si no hay fila."""
    guardadas = {p.tipo: p for p in usuario.preferencias_de_aviso.all()}
    filas = []
    for tipo in TIPOS:
        preferencia = guardadas.get(tipo.clave)
        filas.append(
            {
                "clave": tipo.clave,
                "nombre": tipo.nombre,
                "descripcion": tipo.descripcion,
                "por_correo": preferencia.por_correo if preferencia else tipo.por_correo,
                "por_telegram": preferencia.por_telegram if preferencia else tipo.por_telegram,
            }
        )
    return filas


def _enlace_de(codigo):
    usuario_del_bot = telegram.usuario_del_bot()
    return f"https://t.me/{usuario_del_bot}?start={codigo.codigo}" if usuario_del_bot else ""


class PerfilView(PerfilMixin, View):
    """`CU-AVI-PEC`."""

    def get(self, request):
        usuario = request.user
        vinculo = VinculoTelegram.objects.filter(usuario=usuario).first()
        codigo = (
            CodigoVinculacion.objects.filter(usuario=usuario, usado_en__isnull=True)
            .order_by("-creado_en")
            .first()
        )
        codigo = codigo if codigo and codigo.vigente and vinculo is None else None
        return render(
            request,
            "avisos/perfil.html",
            {
                "vinculo": vinculo,
                "codigo": codigo,
                "enlace_telegram": _enlace_de(codigo) if codigo else "",
                "telegram_configurado": telegram.configurado(),
                "preferencias": _preferencias(usuario),
            },
        )


class CanalesView(PerfilMixin, View):
    """`CU-AVI-CAM`: lo que se marcó, por tipo. «Todo por Telegram» es el atajo."""

    http_method_names = ["post"]  # noqa: RUF012

    def post(self, request):
        usuario = request.user
        vinculado = VinculoTelegram.objects.filter(usuario=usuario).exists()
        todo_por_telegram = request.POST.get("atajo") == "telegram"
        cambios = []
        with transaction.atomic():
            for tipo in TIPOS:
                clave, nombre = tipo.clave, tipo.nombre
                if todo_por_telegram:
                    por_correo, por_telegram = False, True
                else:
                    por_correo = f"correo_{clave}" in request.POST
                    por_telegram = f"telegram_{clave}" in request.POST
                if por_telegram and not vinculado:
                    # Sin chat no hay a dónde mandarlo: el aviso no puede quedar sin
                    # canal, salvo uno opcional, que sin Telegram no se manda.
                    por_telegram = False
                    por_correo = por_correo or not tipo.opcional
                PreferenciaAviso.objects.update_or_create(
                    usuario=usuario,
                    tipo=clave,
                    defaults={"por_correo": por_correo, "por_telegram": por_telegram},
                )
                canales = [
                    n for n, si in (("correo", por_correo), ("Telegram", por_telegram)) if si
                ]
                cambios.append(f"{nombre}: {' y '.join(canales) or 'ninguno'}")
            RegistroAuditoria.registrar(
                accion=RegistroAuditoria.CANALES_DE_AVISO,
                actor=usuario,
                objetivo=usuario,
                ip=obtener_ip(request),
                detalle="; ".join(cambios),
            )
        messages.success(request, "Se guardaron tus avisos.")
        return redirect("avisos:perfil")


class VincularView(PerfilMixin, View):
    """`CU-AVI-TGA`, primera mitad: el enlace de un solo uso. La otra mitad es `/start`."""

    http_method_names = ["post"]  # noqa: RUF012

    def post(self, request):
        if not telegram.configurado():
            messages.error(request, "El bot de Telegram no está configurado (TELEGRAM_BOT_TOKEN).")
            return redirect("avisos:perfil")
        CodigoVinculacion.nuevo(request.user)
        messages.info(request, "Abrí el enlace desde tu teléfono: vence en 15 minutos.")
        return redirect("avisos:perfil")


class ConfirmarVinculoView(PerfilMixin, View):
    """`CU-AVI-TGA`, el cierre: el número que el bot le dio al chat (B-19-005)."""

    http_method_names = ["post"]  # noqa: RUF012

    def post(self, request):
        ok, mensaje = bot.confirmar_vinculo(request.user, request.POST.get("numero", ""))
        (messages.success if ok else messages.error)(request, mensaje)
        return redirect("avisos:perfil")


class CancelarVinculoView(PerfilMixin, View):
    """«No fui yo»: anula el enlace y el pedido del chat que lo abrió."""

    http_method_names = ["post"]  # noqa: RUF012

    def post(self, request):
        CodigoVinculacion.objects.filter(usuario=request.user, usado_en__isnull=True).delete()
        messages.info(request, "Se anuló el enlace. Si querés vincular Telegram, pedí uno nuevo.")
        return redirect("avisos:perfil")


class DesvincularView(PerfilMixin, View):
    """`CU-AVI-TGB` desde el perfil."""

    http_method_names = ["post"]  # noqa: RUF012

    def post(self, request):
        if bot.desvincular(request.user):
            messages.success(request, "Se desvinculó Telegram. Los avisos te llegan por correo.")
        return redirect("avisos:perfil")


class ContrasenaView(PerfilMixin, View):
    """La contraseña propia del Administrador, como `CO-111` para el Cliente."""

    template_name = "avisos/contrasena.html"

    def get(self, request):
        return render(request, self.template_name, {"form": PasswordChangeForm(request.user)})

    def post(self, request):
        formulario = PasswordChangeForm(request.user, request.POST)
        if not formulario.is_valid():
            return render(request, self.template_name, {"form": formulario})
        with transaction.atomic():
            usuario = formulario.save()
            RegistroAuditoria.registrar(
                accion=RegistroAuditoria.CAMBIO_CONTRASENA,
                actor=usuario,
                objetivo=usuario,
                ip=obtener_ip(request),
                detalle="Desde «Mi perfil»: se cerraron las sesiones en otros dispositivos.",
            )
        update_session_auth_hash(request, usuario)
        messages.success(
            request, "Tu contraseña cambió. Cerramos tu sesión en los demás dispositivos."
        )
        return redirect("avisos:perfil")


@method_decorator(csrf_exempt, name="dispatch")
class WebhookView(View):
    """Donde Telegram entrega las novedades (decisión 7: webhook en la VM).

    No lleva sesión ni CSRF: lo llama Telegram. Lo que lo protege es el secreto
    que Telegram manda en la cabecera, derivado del token y de la `SECRET_KEY`.
    Se contesta siempre enseguida: lo que tarda —procesar un correo— va aparte.
    """

    http_method_names = ["post"]  # noqa: RUF012

    def post(self, request):
        recibido = request.headers.get("X-Telegram-Bot-Api-Secret-Token", "")
        if not telegram.configurado() or not hmac.compare_digest(
            recibido, telegram.secreto_del_webhook()
        ):
            return HttpResponseForbidden()
        try:
            novedad = json.loads(request.body)
        except ValueError:
            return HttpResponse(status=400)
        bot.procesar(novedad)
        return HttpResponse("ok")
