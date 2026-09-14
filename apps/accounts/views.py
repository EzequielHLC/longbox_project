from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import (
    LoginView,
    LogoutView,
    PasswordResetCompleteView,
    PasswordResetConfirmView,
    PasswordResetDoneView,
    PasswordResetView,
)
from django.db import transaction
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, resolve_url
from django.urls import reverse_lazy
from django.utils import timezone
from django.views import View
from django.views.decorators.http import require_POST
from django.views.generic import CreateView, DetailView, ListView, TemplateView, UpdateView

from apps.accounts import services
from apps.accounts.forms import (
    MENSAJE_CUENTA_CON_HISTORIAL,
    MENSAJE_CUENTA_CONGELADA,
    MENSAJE_UNICO_ADMINISTRADOR,
    FormularioLogin,
    FormularioRecuperarContrasena,
    FormularioRegistroCliente,
    FormularioUsuarioPersonal,
)
from apps.accounts.models import Usuario
from apps.accounts.tokens import token_de_activacion, token_de_recuperacion
from apps.core import georef
from apps.core.mixins import RolRequeridoMixin
from apps.core.models import RegistroAuditoria
from apps.core.utils import obtener_ip

# CU-AUT-INI paso 4: cada rol aterriza en su propio módulo.
DESTINOS_POR_ROL = {
    "cliente": "core:tienda",
    "cajero": "core:mostrador",
    "administrador": "core:panel",
}

MENSAJE_SESION_EXPIRADA = "Tu sesión expiró por inactividad."


class LoginUsuarioView(LoginView):
    """CU-AUT-INI — Iniciar Sesión."""

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
    """CU-AUT-FIN — Cerrar Sesión.

    `LogoutView` invalida únicamente la sesión del dispositivo actual: las
    sesiones abiertas en otros dispositivos siguen vigentes, como pide el CU.
    Solo acepta POST, así un enlace de terceros no puede desloguear al usuario.
    """

    next_page = reverse_lazy("accounts:login")


class RecuperarContrasenaView(PasswordResetView):
    """CU-AUT-REC pasos 1 a 3 — pedir el enlace de recuperación."""

    template_name = "accounts/password_reset_form.html"
    email_template_name = "accounts/password_reset_email.txt"
    subject_template_name = "accounts/password_reset_subject.txt"
    success_url = reverse_lazy("accounts:password_reset_done")
    form_class = FormularioRecuperarContrasena
    # Vigencia de 30 minutos, más corta que el tope de `PASSWORD_RESET_TIMEOUT`.
    token_generator = token_de_recuperacion
    # `PasswordResetForm` solo le manda el correo a cuentas activas y siempre
    # termina en la misma pantalla, exista o no el correo: eso es lo que evita
    # la enumeración de cuentas.


class RecuperarContrasenaEnviadaView(PasswordResetDoneView):
    template_name = "accounts/password_reset_done.html"


class RestablecerContrasenaView(PasswordResetConfirmView):
    """CU-AUT-REC pasos 4 y 5 — validar el token y fijar la nueva contraseña.

    El token es de un solo uso sin código extra: `PasswordResetTokenGenerator`
    lo deriva del hash de la contraseña actual, así que al cambiarla el enlace
    anterior deja de validar. Por el mismo motivo cambia el HMAC de sesión y
    todas las sesiones abiertas del usuario quedan invalidadas.
    """

    template_name = "accounts/password_reset_confirm.html"
    success_url = reverse_lazy("accounts:password_reset_complete")
    token_generator = token_de_recuperacion

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


# ---------------------------------------------------------------------------
# Módulo 11 — Cuenta de Cliente (CU-CLI-ALT)
# ---------------------------------------------------------------------------


class RegistroClienteView(CreateView):
    """CU-CLI-ALT — Registrar Cuenta de Cliente.

    Es la única alta pública del sistema: no hereda de `RolRequeridoMixin`
    porque justamente la abre alguien que todavía no tiene cuenta. Lo que sí
    controla es lo contrario —quien ya tiene sesión no vuelve al registro— y
    que el rol nunca sea otro que `cliente`.
    """

    model = Usuario
    form_class = FormularioRegistroCliente
    template_name = "accounts/registro_cliente.html"

    def dispatch(self, request, *args, **kwargs):
        # Precondición del CU: el formulario es de acceso público, sin sesión
        # previa. A quien ya está adentro se lo manda a su módulo.
        if request.user.is_authenticated:
            destino = DESTINOS_POR_ROL.get(request.user.rol, settings.LOGIN_REDIRECT_URL)
            return redirect(destino)
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return resolve_url(DESTINOS_POR_ROL[Usuario.CLIENTE])

    def form_valid(self, form):
        # La cuenta, el correo de bienvenida y el registro de auditoría son una
        # sola unidad: si algo falla no queda una cuenta a medio crear ni un
        # registro de un alta que no ocurrió.
        with transaction.atomic():
            usuario = form.save(commit=False)
            usuario.username = services.username_disponible_para(usuario.email)
            # El rol y el estado no salen del formulario: los fija el sistema.
            # A diferencia del alta de personal (CU-USR-ALT), la cuenta nace Activa
            # porque el propio registro ya autentica al titular.
            usuario.rol = Usuario.CLIENTE
            usuario.estado = Usuario.ACTIVO
            # Evidencia del consentimiento informado (Ley 25.326): el checkbox
            # no se valida y se descarta, queda fechado junto con la cuenta.
            usuario.fecha_aceptacion_politica = timezone.now()
            usuario.save()

            # TODO(loyalty): cuando exista el módulo de Puntos, el saldo del
            # Cliente nuevo arranca en cero por defecto en ese módulo, no acá.
            # TODO(stock-local): ídem con el stock almacenado en local, que
            # nace vacío y es responsabilidad del Módulo 18.

            services.enviar_bienvenida(usuario, self.request)
            RegistroAuditoria.registrar(
                accion=RegistroAuditoria.REGISTRO_CLIENTE,
                actor=usuario,
                objetivo=usuario,
                ip=obtener_ip(self.request),
                detalle="alta pública de cuenta de cliente; política de privacidad aceptada",
            )

        self.object = usuario
        # Paso 5: inicia sesión automáticamente. `login()` dispara la signal
        # `user_logged_in`, así que el inicio de sesión se audita solo.
        login(self.request, usuario)
        messages.success(
            self.request,
            f"Se creó su cuenta con el correo {usuario.email}. ¡Bienvenido/a a Longbox!",
        )
        return redirect(self.get_success_url())


# ---------------------------------------------------------------------------
# Módulo 13 — Gestión de Usuarios (CU-USR-ALT, CU-USR-MOD, CU-USR-BAJ)
# ---------------------------------------------------------------------------


def cerrar_la_propia_sesion(request, usuario):
    """Si el Administrador se aplicó el cambio a sí mismo, cierra su sesión.

    Al invalidar las sesiones del usuario modificado se borró también la del
    Administrador que está ejecutando la acción, si son el mismo. Hay que
    cerrarla de forma ordenada: si no, el middleware de sesiones intenta
    guardar al final del request una sesión que ya no existe y la respuesta
    muere en un 400 en lugar de redirigir al login.

    Devuelve True si la sesión cerrada era la del propio request.
    """
    if request.user.is_authenticated and request.user.pk == usuario.pk:
        logout(request)
        return True
    return False


class GestionDeUsuariosMixin(RolRequeridoMixin):
    """Los tres CU son exclusivos del Administrador, validado server-side.

    RNF-03: el chequeo vive acá y no en el template. Que el menú no muestre el
    enlace no es una restricción de seguridad; un request directo a cualquiera
    de estas URLs con otro rol termina en 403 antes de tocar la base.
    """

    roles_permitidos = (Usuario.ADMINISTRADOR,)


class UsuarioListaView(GestionDeUsuariosMixin, ListView):
    """Tabla de cuentas de personal: el punto de entrada de los tres CU."""

    context_object_name = "usuarios"
    paginate_by = 25

    def get_template_names(self):
        # El buscador refresca la tabla mientras se escribe: para eso pide la
        # misma URL con `?parcial=1` y recibe solo el fragmento de la tabla, no
        # la pantalla entera. Sin JavaScript el formulario se envía normal y
        # cae en la plantilla completa, así que la pantalla funciona igual.
        if self.request.GET.get("parcial"):
            return ["accounts/_tabla_usuarios.html"]
        return ["accounts/usuario_lista.html"]

    def get_queryset(self):
        # Solo cuentas de personal: las de Cliente se gestionan en el Módulo 11.
        usuarios = Usuario.objects.filter(rol__in=Usuario.ROLES_DE_PERSONAL)

        busqueda = self.request.GET.get("q", "").strip()
        if busqueda:
            usuarios = usuarios.filter(
                Q(email__icontains=busqueda)
                | Q(first_name__icontains=busqueda)
                | Q(last_name__icontains=busqueda)
            )

        # Los filtros se validan contra las opciones reales: un valor inventado
        # en la query string se ignora, no rompe ni filtra de más.
        rol = self.request.GET.get("rol", "")
        if rol in Usuario.ROLES_DE_PERSONAL:
            usuarios = usuarios.filter(rol=rol)

        estado = self.request.GET.get("estado", "")
        if estado in dict(Usuario.ESTADO_CHOICES):
            usuarios = usuarios.filter(estado=estado)

        return usuarios.order_by("-actualizado_en")

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        rol = self.request.GET.get("rol", "")
        estado = self.request.GET.get("estado", "")
        contexto["busqueda"] = self.request.GET.get("q", "").strip()
        contexto["rol_elegido"] = rol if rol in Usuario.ROLES_DE_PERSONAL else ""
        contexto["estado_elegido"] = estado if estado in dict(Usuario.ESTADO_CHOICES) else ""
        contexto["roles"] = [
            (valor, etiqueta)
            for valor, etiqueta in Usuario.ROL_CHOICES
            if valor in Usuario.ROLES_DE_PERSONAL
        ]
        contexto["estados"] = Usuario.ESTADO_CHOICES
        return contexto


class ClienteListaView(GestionDeUsuariosMixin, ListView):
    """Cuentas de Cliente, **solo para consultar**.

    No es un CU: es la contraparte de lectura del registro público (CU-CLI-ALT). El
    Administrador necesita poder responder "¿esta persona tiene cuenta?, ¿desde
    cuándo?, ¿qué teléfono dejó?, ¿aceptó la política?" para dar soporte, y
    nada de eso requiere poder modificar la cuenta.

    Por eso la pantalla no tiene ninguna acción: dar de baja una cuenta de
    Cliente es el CU-CLI-BAJ, que todavía no está documentado y probablemente tenga
    reglas propias (pedidos en curso, puntos acumulados, stock guardado en el
    local). Cuando se aborde, se le agregan las acciones a esta misma tabla.
    """

    context_object_name = "clientes"
    paginate_by = 25

    def get_template_names(self):
        if self.request.GET.get("parcial"):
            return ["accounts/_tabla_clientes.html"]
        return ["accounts/cliente_lista.html"]

    def get_queryset(self):
        clientes = Usuario.objects.filter(rol=Usuario.CLIENTE)

        busqueda = self.request.GET.get("q", "").strip()
        if busqueda:
            clientes = clientes.filter(
                Q(email__icontains=busqueda)
                | Q(first_name__icontains=busqueda)
                | Q(last_name__icontains=busqueda)
                | Q(telefono_numero__icontains=busqueda)
            )

        estado = self.request.GET.get("estado", "")
        if estado in dict(Usuario.ESTADO_CHOICES):
            clientes = clientes.filter(estado=estado)

        provincia = self.request.GET.get("provincia", "")
        if provincia in georef.obtener_provincias():
            clientes = clientes.filter(provincia=provincia)

        # Por fecha de registro: lo primero que se quiere ver es quién se
        # anotó recién.
        return clientes.order_by("-date_joined")

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        estado = self.request.GET.get("estado", "")
        provincia = self.request.GET.get("provincia", "")
        provincias = georef.obtener_provincias()
        contexto["busqueda"] = self.request.GET.get("q", "").strip()
        contexto["estado_elegido"] = estado if estado in dict(Usuario.ESTADO_CHOICES) else ""
        contexto["provincia_elegida"] = provincia if provincia in provincias else ""
        contexto["estados"] = Usuario.ESTADO_CHOICES
        contexto["provincias"] = provincias
        return contexto


class UsuarioAltaView(GestionDeUsuariosMixin, CreateView):
    """CU-USR-ALT — Dar de Alta Usuario del Sistema."""

    model = Usuario
    form_class = FormularioUsuarioPersonal
    template_name = "accounts/usuario_formulario.html"
    success_url = reverse_lazy("accounts:usuario_lista")

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        contexto["titulo"] = "Nuevo usuario"
        return contexto

    def form_valid(self, form):
        # La cuenta, el enlace y el registro de auditoría son una sola unidad:
        # si falla el envío del correo no queda una cuenta a la que nadie pueda
        # entrar ni un registro de un alta que no ocurrió.
        with transaction.atomic():
            usuario = form.save(commit=False)
            usuario.username = services.username_disponible_para(usuario.email)
            services.preparar_para_activacion(usuario)
            usuario.save()
            services.enviar_enlace_de_activacion(usuario, self.request)
            RegistroAuditoria.registrar(
                accion=RegistroAuditoria.ALTA_USUARIO,
                actor=self.request.user,
                objetivo=usuario,
                ip=obtener_ip(self.request),
                detalle=f"rol asignado: {usuario.get_rol_display()}",
            )

        self.object = usuario
        messages.success(
            self.request,
            f"Se creó la cuenta de {usuario.email} y se envió el enlace de activación. "
            f"El enlace vence en {settings.VIGENCIA_ENLACE_ACTIVACION // 3600} horas.",
        )
        return redirect(self.get_success_url())


class UsuarioEdicionView(GestionDeUsuariosMixin, UpdateView):
    """CU-USR-MOD — Modificar Usuario del Sistema."""

    model = Usuario
    form_class = FormularioUsuarioPersonal
    template_name = "accounts/usuario_formulario.html"
    context_object_name = "usuario_objetivo"
    success_url = reverse_lazy("accounts:usuario_lista")

    def get_queryset(self):
        return Usuario.objects.filter(rol__in=Usuario.ROLES_DE_PERSONAL)

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        contexto["titulo"] = "Editar usuario"
        return contexto

    def get(self, request, *args, **kwargs):
        return self._rechazo_por_congelada() or super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        return self._rechazo_por_congelada() or super().post(request, *args, **kwargs)

    def _rechazo_por_congelada(self):
        """Bloquea la edición de una cuenta dada de baja, en GET y en POST.

        RNF-03: que la tabla ofrezca "Reactivar" en vez de "Editar" no es una
        restricción; el chequeo tiene que estar acá, contra un request directo.
        """
        if not self.get_object().esta_congelada:
            return None
        messages.error(self.request, MENSAJE_CUENTA_CONGELADA)
        return redirect("accounts:usuario_lista")

    def form_valid(self, form):
        # Copia del estado previo *antes* de que el formulario toque la
        # instancia: el CU pide auditar valores anteriores y nuevos, y con el
        # objeto ya modificado los anteriores se pierden.
        anterior = Usuario.objects.get(pk=self.object.pk)

        with transaction.atomic():
            cambia_el_rol = form.cleaned_data["rol"] != anterior.rol
            if cambia_el_rol and services.es_el_unico_administrador_activo(anterior):
                form.add_error("rol", MENSAJE_UNICO_ADMINISTRADOR)
                return self.form_invalid(form)

            usuario = form.save()
            cambios = services.cambios_entre(anterior, usuario)

            if cambios:
                RegistroAuditoria.registrar(
                    accion=RegistroAuditoria.MODIFICACION_USUARIO,
                    actor=self.request.user,
                    objetivo=usuario,
                    ip=obtener_ip(self.request),
                    detalle=services.describir_cambios(cambios),
                )
            if cambia_el_rol:
                # Los permisos viejos siguen vivos en la sesión abierta: hay
                # que forzar el re-login para que tome los nuevos.
                services.invalidar_sesiones_de(usuario)

        if not cambia_el_rol:
            messages.success(self.request, f"Se actualizó la cuenta de {usuario.email}.")
            return redirect(self.get_success_url())

        if cerrar_la_propia_sesion(self.request, usuario):
            messages.info(
                self.request,
                "Se modificó el rol de la cuenta propia, por lo que la sesión quedó "
                "cerrada. Vuelva a iniciar sesión con los permisos actualizados.",
            )
            return redirect("accounts:login")

        messages.success(
            self.request,
            f"Se actualizó la cuenta de {usuario.email}. Dado que se modificó el rol, se "
            "cerraron las sesiones activas de la cuenta y deberá volver a iniciar sesión.",
        )
        return redirect(self.get_success_url())


class ReenviarActivacionView(GestionDeUsuariosMixin, View):
    """CU-USR-MOD, flujo alternativo — regenerar el enlace de activación."""

    def post(self, request, pk):
        usuario = get_object_or_404(Usuario, pk=pk, rol__in=Usuario.ROLES_DE_PERSONAL)

        if not usuario.esta_pendiente_de_activacion:
            messages.error(
                request,
                "Solo se puede regenerar el enlace de una cuenta pendiente de activación.",
            )
            return redirect("accounts:usuario_edicion", pk=usuario.pk)

        with transaction.atomic():
            # Vuelve a rotar la contraseña inutilizable: eso mata el enlace
            # anterior antes de emitir el nuevo.
            services.preparar_para_activacion(usuario)
            usuario.save()
            services.enviar_enlace_de_activacion(usuario, request)
            RegistroAuditoria.registrar(
                accion=RegistroAuditoria.REENVIO_ACTIVACION,
                actor=request.user,
                objetivo=usuario,
                ip=obtener_ip(request),
                detalle="se emitió un enlace nuevo y quedó invalidado el anterior",
            )

        messages.success(
            request,
            f"Se envió un nuevo enlace de activación a {usuario.email}. "
            "El enlace anterior quedó invalidado.",
        )
        return redirect("accounts:usuario_edicion", pk=usuario.pk)


class UsuarioBajaView(GestionDeUsuariosMixin, DetailView):
    """CU-USR-BAJ — Dar de Baja Usuario del Sistema.

    El GET es la confirmación explícita que pide el paso 2; la baja se aplica
    únicamente por POST. Es una baja lógica: el usuario nunca se borra, así el
    historial de operaciones que registró queda intacto.
    """

    model = Usuario
    template_name = "accounts/usuario_baja.html"
    context_object_name = "usuario_objetivo"

    def get_queryset(self):
        return Usuario.objects.filter(rol__in=Usuario.ROLES_DE_PERSONAL)

    def post(self, request, *args, **kwargs):
        usuario = self.get_object()

        if usuario.estado != Usuario.ACTIVO:
            messages.error(request, "Solo se puede dar de baja una cuenta activa.")
            return redirect("accounts:usuario_lista")

        with transaction.atomic():
            if services.es_el_unico_administrador_activo(usuario):
                messages.error(request, MENSAJE_UNICO_ADMINISTRADOR)
                return redirect("accounts:usuario_baja", pk=usuario.pk)

            usuario.estado = Usuario.INACTIVO
            usuario.save()
            services.invalidar_sesiones_de(usuario)
            RegistroAuditoria.registrar(
                accion=RegistroAuditoria.BAJA_USUARIO,
                actor=request.user,
                objetivo=usuario,
                ip=obtener_ip(request),
                detalle=f"estado: '{Usuario.ACTIVO}' → '{Usuario.INACTIVO}'; sesiones cerradas",
            )

        if cerrar_la_propia_sesion(request, usuario):
            messages.info(
                request, "Se dio de baja la cuenta propia, por lo que la sesión quedó cerrada."
            )
            return redirect("accounts:login")

        messages.success(
            request,
            f"Se dio de baja la cuenta de {usuario.email} y se cerraron todas sus sesiones "
            "abiertas.",
        )
        return redirect("accounts:usuario_lista")


class UsuarioReactivarView(GestionDeUsuariosMixin, DetailView):
    """Devuelve al sistema una cuenta que había sido dada de baja.

    Agregado al CU (ver `/docs/modulos/gestion_usuarios.md`): sin esto, la baja
    del CU-USR-BAJ sería definitiva y alguien que vuelve al trabajo necesitaría una
    cuenta nueva, perdiendo la continuidad de su historial.

    La cuenta no vuelve directamente a Activa: vuelve a **Pendiente de
    activación** con un enlace nuevo. Se dio de baja por algún motivo, y
    devolverle el acceso con la contraseña que tenía —que pudo quedar anotada o
    compartida— sería reabrir una credencial vieja. Al pasar por el enlace, la
    persona elige una contraseña nueva y la anterior queda invalidada.
    """

    model = Usuario
    template_name = "accounts/usuario_reactivar.html"
    context_object_name = "usuario_objetivo"

    def get_queryset(self):
        return Usuario.objects.filter(rol__in=Usuario.ROLES_DE_PERSONAL)

    def post(self, request, *args, **kwargs):
        usuario = self.get_object()

        if not usuario.esta_congelada:
            messages.error(request, "Solo se puede reactivar una cuenta dada de baja.")
            return redirect("accounts:usuario_lista")

        with transaction.atomic():
            # Mismo camino que un alta: pendiente, sin contraseña utilizable y
            # con un enlace nuevo. Rotar el hash mata la contraseña anterior.
            services.preparar_para_activacion(usuario)
            usuario.save()
            services.enviar_enlace_de_activacion(usuario, request)
            RegistroAuditoria.registrar(
                accion=RegistroAuditoria.REACTIVACION_USUARIO,
                actor=request.user,
                objetivo=usuario,
                ip=obtener_ip(request),
                detalle=(
                    f"estado: '{Usuario.INACTIVO}' → '{Usuario.PENDIENTE_ACTIVACION}'; "
                    "se envió un enlace para elegir una contraseña nueva"
                ),
            )

        messages.success(
            request,
            f"Se reactivó la cuenta de {usuario.email} y se envió un enlace para establecer "
            "una nueva contraseña. Hasta entonces la cuenta no puede iniciar sesión.",
        )
        return redirect("accounts:usuario_lista")


class UsuarioEliminarPendienteView(GestionDeUsuariosMixin, DetailView):
    """Elimina una cuenta que nunca llegó a activarse.

    Agregado al CU (ver `/docs/modulos/gestion_usuarios.md`): el CU-USR-BAJ pide
    estado Activo para dar de baja, así que una cuenta cargada con el correo
    equivocado quedaría Pendiente para siempre, con ese correo bloqueado.

    Es la única eliminación física del sistema, y se justifica porque una
    cuenta que nunca se usó no pudo registrar ninguna operación: no hay
    historial que preservar. Todo lo que alguna vez estuvo Activo se da de baja
    lógicamente y nunca se borra.

    Ojo con la condición: no alcanza con que la cuenta esté Pendiente, porque
    una cuenta reactivada también lo está. Lo que la habilita es no haber
    iniciado sesión nunca (`Usuario.se_puede_eliminar`).
    """

    model = Usuario
    template_name = "accounts/usuario_eliminar.html"
    context_object_name = "usuario_objetivo"

    def get_queryset(self):
        return Usuario.objects.filter(rol__in=Usuario.ROLES_DE_PERSONAL)

    def post(self, request, *args, **kwargs):
        usuario = self.get_object()

        if not usuario.se_puede_eliminar:
            messages.error(request, MENSAJE_CUENTA_CON_HISTORIAL)
            return redirect("accounts:usuario_lista")

        correo = usuario.email
        with transaction.atomic():
            # El registro va *antes* del borrado para que quede el correo en
            # `objetivo_email`: al desaparecer la cuenta, la clave foránea se
            # pone en NULL pero el texto desnormalizado sobrevive.
            RegistroAuditoria.registrar(
                accion=RegistroAuditoria.ELIMINACION_PENDIENTE,
                actor=request.user,
                objetivo=usuario,
                ip=obtener_ip(request),
                detalle="cuenta nunca activada; se elimina y se libera el correo",
            )
            usuario.delete()

        messages.success(
            request,
            f"Se eliminó la cuenta pendiente de {correo}. La dirección de correo quedó "
            "nuevamente disponible.",
        )
        return redirect("accounts:usuario_lista")


class ActivarCuentaView(PasswordResetConfirmView):
    """CU-USR-ALT paso 3, del lado del usuario nuevo: elegir su primera contraseña.

    Reutiliza la vista de restablecimiento de Django porque el flujo es el
    mismo (validar el token, pedir contraseña y confirmación, guardarla
    hasheada); cambia la vigencia del token y el texto de la pantalla. Al
    terminar, la cuenta pasa de Pendiente a Activa.
    """

    template_name = "accounts/activar_cuenta.html"
    success_url = reverse_lazy("accounts:activacion_completa")
    token_generator = token_de_activacion

    def form_valid(self, form):
        respuesta = super().form_valid(form)
        usuario = self.user
        usuario.estado = Usuario.ACTIVO
        usuario.save()
        RegistroAuditoria.registrar(
            accion=RegistroAuditoria.ACTIVACION_CUENTA,
            actor=usuario,
            objetivo=usuario,
            ip=obtener_ip(self.request),
            detalle=f"estado: '{Usuario.PENDIENTE_ACTIVACION}' → '{Usuario.ACTIVO}'",
        )
        return respuesta


class ActivacionCompletaView(TemplateView):
    template_name = "accounts/activacion_completa.html"
