"""«Mi cuenta»: el panel del Cliente (plan 11, segunda parte).

`CU-CLI-HIS` (`CO-192`, `CO-193`) y `CU-CLI-DAT` (`CO-108` a `CO-111`). La
sección Puntos es `CU-PTS-CON` y vive en `apps/puntos/views.py`.

Todo es del Cliente: el personal recibe 403 y un invitado va al ingreso. Un
pedido se busca siempre **entre los del Cliente**: el de otro responde 404.
La única excepción es la confirmación del correo nuevo (`CO-110`), que se abre
desde el enlace del correo y se autentica por su token, no por la sesión.
"""

from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.sites.shortcuts import get_current_site
from django.db import IntegrityError, transaction
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.views import View

from apps.accounts.forms import CambioDeCorreoForm, DatosPersonalesForm
from apps.accounts.models import TokenCambioCorreo, Usuario
from apps.accounts.tokens import token_de_cambio_de_correo
from apps.core.mail import cuerpo_html, enviar_correo
from apps.core.mixins import RolRequeridoMixin
from apps.core.models import RegistroAuditoria
from apps.core.utils import obtener_ip
from apps.pedidos.models import Pedido
from apps.pedidos.servicios import ACTIVOS
from apps.pedidos.views import con_totales


class ClienteMixin(RolRequeridoMixin):
    roles_permitidos = (Usuario.CLIENTE,)


def _pedidos_de(usuario):
    return con_totales(Pedido.objects.filter(usuario=usuario)).order_by("-fecha", "-pk")


# ---------------------------------------------------------------------------
# CU-CLI-HIS — CO-192 consultarPanelDeCuenta · CO-193 consultarDetalleDePedidoPropio
# ---------------------------------------------------------------------------


class PanelView(ClienteMixin, View):
    """`CO-192`: la puerta del panel, con los pedidos activos (E1: sin pedidos, un mensaje)."""

    def get(self, request):
        return render(
            request,
            "cuenta/panel.html",
            {
                "seccion": "activos",
                "pedidos": _pedidos_de(request.user).filter(estado__in=ACTIVOS),
            },
        )


class HistorialView(ClienteMixin, View):
    """Los pedidos despachados (B-11-004)."""

    def get(self, request):
        return render(
            request,
            "cuenta/historial.html",
            {
                "seccion": "historial",
                "pedidos": _pedidos_de(request.user).filter(estado=Pedido.DESPACHADO),
            },
        )


class PedidoPropioView(ClienteMixin, View):
    """`CO-193`: ítems, precios efectivos, estados alcanzados y fecha de cada uno.

    Un pedido activo vuelve a pedirse cada 30 segundos (RF-18; B-08-002).
    """

    def get(self, request, numero):
        pedido = get_object_or_404(Pedido, numero=numero, usuario=request.user)
        lineas = list(pedido.lineas.select_related("producto", "producto__productoeditorial"))
        return render(
            request,
            "cuenta/pedido.html",
            {
                "seccion": "activos" if pedido.estado in ACTIVOS else "historial",
                "pedido": pedido,
                "lineas": lineas,
                "transiciones": list(pedido.transiciones.all()),
                "cobrado": sum((linea.subtotal for linea in lineas), pedido.costo_envio),
                "activo": pedido.estado in ACTIVOS,
            },
        )


# ---------------------------------------------------------------------------
# CU-CLI-DAT — CO-108 actualizarDatosPersonales
# ---------------------------------------------------------------------------


class DatosView(ClienteMixin, View):
    template_name = "cuenta/datos.html"

    def get(self, request, formulario=None):
        return render(
            request,
            self.template_name,
            {
                "seccion": "datos",
                "form": formulario or DatosPersonalesForm(instance=request.user),
            },
        )

    def post(self, request):
        usuario = Usuario.objects.get(pk=request.user.pk)
        campos = ["first_name", "last_name", *DatosPersonalesForm.CAMPOS]
        antes = {campo: getattr(usuario, campo) for campo in campos}
        formulario = DatosPersonalesForm(request.POST, instance=usuario)
        if not formulario.is_valid():
            return self.get(request, formulario)
        with transaction.atomic():
            usuario = formulario.save()
            cambios = [
                f"{Usuario._meta.get_field(campo).verbose_name}: "
                f"«{antes[campo]}» → «{getattr(usuario, campo)}»"
                for campo in campos
                if antes[campo] != getattr(usuario, campo)
            ]
            if cambios:
                RegistroAuditoria.registrar(
                    accion=RegistroAuditoria.MODIFICACION_DATOS_CLIENTE,
                    actor=usuario,
                    objetivo=usuario,
                    ip=obtener_ip(request),
                    detalle="; ".join(cambios),
                )
        if cambios:
            messages.success(request, "Tus datos quedaron actualizados.")
        else:
            messages.info(request, "No había nada que cambiar.")
        return redirect("cuenta:datos")


# ---------------------------------------------------------------------------
# CU-CLI-DAT A2 — CO-111 cambiarContrasena
# ---------------------------------------------------------------------------


class ContrasenaView(ClienteMixin, View):
    """`CO-111`: con la contraseña actual. Las demás sesiones se cierran; ésta sigue.

    Cambiar la contraseña cambia el hash, y con él la firma de todas las sesiones
    abiertas: Django las invalida solo. `update_session_auth_hash` vuelve a
    firmar la sesión actual, que es la que el contrato conserva.
    """

    template_name = "cuenta/contrasena.html"

    def get(self, request):
        return render(
            request,
            self.template_name,
            {"seccion": "datos", "form": PasswordChangeForm(request.user)},
        )

    def post(self, request):
        formulario = PasswordChangeForm(request.user, request.POST)
        if not formulario.is_valid():
            return render(request, self.template_name, {"seccion": "datos", "form": formulario})
        with transaction.atomic():
            usuario = formulario.save()
            RegistroAuditoria.registrar(
                accion=RegistroAuditoria.CAMBIO_CONTRASENA,
                actor=usuario,
                objetivo=usuario,
                ip=obtener_ip(request),
                detalle="Desde «Mi cuenta»: se cerraron las sesiones en otros dispositivos.",
            )
        update_session_auth_hash(request, usuario)
        messages.success(
            request, "Tu contraseña cambió. Cerramos tu sesión en los demás dispositivos."
        )
        return redirect("cuenta:datos")


# ---------------------------------------------------------------------------
# CU-CLI-DAT A1 — CO-109 solicitarCambioDeCorreo · CO-110 confirmarCambioDeCorreo
# ---------------------------------------------------------------------------


class CorreoView(ClienteMixin, View):
    """`CO-109`: emite el token y manda el enlace **al correo nuevo**. La cuenta no cambia."""

    template_name = "cuenta/correo.html"

    def get(self, request):
        return render(
            request,
            self.template_name,
            {"seccion": "datos", "form": CambioDeCorreoForm(request.user)},
        )

    def post(self, request):
        formulario = CambioDeCorreoForm(request.user, request.POST)
        if not formulario.is_valid():
            return render(request, self.template_name, {"seccion": "datos", "form": formulario})
        correo = formulario.cleaned_data["correo_nuevo"]
        TokenCambioCorreo.emitir(request.user, correo)
        sitio = get_current_site(request)
        protocolo = "https" if request.is_secure() else "http"
        ruta = reverse(
            "cuenta:confirmar_correo",
            kwargs={
                "uidb64": urlsafe_base64_encode(force_bytes(request.user.pk)),
                "token": token_de_cambio_de_correo.make_token(request.user),
            },
        )
        contexto = {
            "usuario": request.user,
            "correo_nuevo": correo,
            "enlace": f"{protocolo}://{sitio.domain}{ruta}",
            "vigencia_horas": TokenCambioCorreo.VIGENCIA.total_seconds() // 3600,
        }
        enviar_correo(
            asunto="Confirmá tu correo nuevo",
            cuerpo=render_to_string("cuenta/correo_confirmar.txt", contexto),
            destinatarios=[correo],
            html=cuerpo_html("correo/cambio_de_correo.html", contexto),
        )
        messages.success(
            request,
            f"Te mandamos un enlace a {correo}. Hasta que lo abras, tu correo sigue siendo "
            f"{request.user.email}.",
        )
        return redirect("cuenta:datos")


class ConfirmarCorreoView(View):
    """`CO-110`. El GET muestra qué se va a confirmar; el POST lo hace.

    No cambia nada en el GET a propósito: muchos servicios de correo abren los
    enlaces solos para revisarlos, y un enlace que cambiara el correo al abrirse
    se consumiría sin que el titular lo hubiera tocado.
    """

    template_name = "cuenta/correo_confirmar.html"

    def _resolver(self, uidb64, token):
        try:
            usuario = Usuario.objects.get(pk=force_str(urlsafe_base64_decode(uidb64)))
        except (Usuario.DoesNotExist, ValueError, TypeError, OverflowError):
            raise Http404("El enlace no es válido.") from None
        pendiente = TokenCambioCorreo.vigente_de(usuario)
        valido = pendiente is not None and token_de_cambio_de_correo.check_token(usuario, token)
        return usuario, (pendiente if valido else None)

    def get(self, request, uidb64, token):
        usuario, pendiente = self._resolver(uidb64, token)
        return render(request, self.template_name, {"pendiente": pendiente, "usuario": usuario})

    def post(self, request, uidb64, token):
        usuario, pendiente = self._resolver(uidb64, token)
        if pendiente is None:
            return render(request, self.template_name, {"pendiente": None, "usuario": usuario})
        anterior = usuario.email
        try:
            with transaction.atomic():
                if not pendiente.consumir():
                    raise Http404("El enlace ya se usó.")
                usuario.email = pendiente.correo_nuevo
                usuario.save(update_fields=["email", "actualizado_en"])
                RegistroAuditoria.registrar(
                    accion=RegistroAuditoria.CAMBIO_CORREO,
                    actor=usuario,
                    objetivo=usuario,
                    ip=obtener_ip(request),
                    detalle=f"{anterior} → {usuario.email}",
                )
        except IntegrityError:
            # Otra cuenta tomó ese correo entre el pedido y la confirmación (I-10).
            messages.error(request, "Ese correo ya tiene una cuenta asociada.")
            return render(request, self.template_name, {"pendiente": None, "usuario": usuario})
        _avisar_al_correo_anterior(anterior, usuario.email)
        if request.user.is_authenticated and request.user.pk == usuario.pk:
            messages.success(request, f"Listo: tu correo ahora es {usuario.email}.")
            return redirect("cuenta:datos")
        messages.success(request, f"Listo: tu correo ahora es {usuario.email}. Ya podés ingresar.")
        return redirect("accounts:login")


def _enmascarar(correo):
    nombre, _, dominio = correo.partition("@")
    return f"{nombre[:2]}{'•' * max(len(nombre) - 2, 1)}@{dominio}"


def _avisar_al_correo_anterior(anterior, nuevo):
    """B-11-005: el titular se entera aunque el cambio no lo haya hecho él."""
    contexto = {"correo_nuevo": _enmascarar(nuevo)}
    enviar_correo(
        asunto="El correo de tu cuenta cambió",
        cuerpo=render_to_string("cuenta/correo_cambiado.txt", contexto),
        destinatarios=[anterior],
        html=cuerpo_html("correo/correo_cambiado.html", contexto),
    )
