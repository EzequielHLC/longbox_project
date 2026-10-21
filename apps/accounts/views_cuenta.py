"""«Mi cuenta»: el panel del Cliente (plan 11, segunda parte).

`CU-CLI-HIS` (`CO-192`, `CO-193`) y `CU-CLI-DAT` (`CO-108` a `CO-111`). La
sección Puntos es `CU-PTS-CON` y vive en `apps/puntos/views.py`.

Todo es del Cliente: el personal recibe 403 y un invitado va al ingreso. Un
pedido se busca siempre **entre los del Cliente**: el de otro responde 404.
La única excepción es la confirmación del correo nuevo (`CO-110`), que se abre
desde el enlace del correo y se autentica por su token, no por la sesión.
"""

import logging

from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.sites.shortcuts import get_current_site
from django.db import IntegrityError, transaction
from django.db.models import Exists, OuterRef, Q
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
from apps.almacen.models import ArticuloRetenido
from apps.core.mail import cuerpo_html, enviar_correo
from apps.core.mixins import RolRequeridoMixin
from apps.core.models import RegistroAuditoria
from apps.core.utils import obtener_ip
from apps.devoluciones import servicios as devoluciones
from apps.pedidos import demora
from apps.pedidos.models import LineaPedido, Pedido
from apps.pedidos.riel import riel_de
from apps.pedidos.servicios import ACTIVOS
from apps.pedidos.views import con_totales

logger = logging.getLogger(__name__)


class ClienteMixin(RolRequeridoMixin):
    roles_permitidos = (Usuario.CLIENTE,)


def _pedidos_de(usuario):
    return con_totales(Pedido.objects.filter(usuario=usuario)).order_by("-fecha", "-pk")


def _por_retirar():
    """Si el pedido para retirar tiene algo esperando en el mostrador."""
    return Exists(
        ArticuloRetenido.objects.filter(
            linea_pedido__pedido=OuterRef("pk"),
            procedencia=ArticuloRetenido.PARA_RETIRAR,
            estado__in=ArticuloRetenido.CON_PLAZO,
        )
    )


# Plan 00 de interfaz, ambigüedad 1: un pedido «En el local» sigue en curso
# mientras quede algo por retirar; después pasa al historial (B-11-006).
EN_CURSO = Q(estado__in=ACTIVOS) | Q(estado=Pedido.EN_LOCAL, por_retirar=True)
TERMINADOS = Q(estado__in=(Pedido.DESPACHADO, Pedido.CANCELADO, Pedido.VENDIDO_EN_LOCAL)) | Q(
    estado=Pedido.EN_LOCAL, por_retirar=False
)


def en_curso(usuario):
    return _pedidos_de(usuario).annotate(por_retirar=_por_retirar()).filter(EN_CURSO)


def terminados(usuario):
    return _pedidos_de(usuario).annotate(por_retirar=_por_retirar()).filter(TERMINADOS)


# ---------------------------------------------------------------------------
# CU-CLI-HIS — CO-192 consultarPanelDeCuenta · CO-193 consultarDetalleDePedidoPropio
# ---------------------------------------------------------------------------


def _con_riel(pedidos):
    """Cada pedido con su riel reducido y hasta tres portadas (plan 00 de interfaz, 4.3)."""
    pedidos = list(pedidos.prefetch_related("transiciones", "lineas__producto"))
    for pedido in pedidos:
        # Una compra en el mostrador no recorre nada (B-06-005).
        pedido.riel = (
            None
            if pedido.canal == Pedido.PRESENCIAL
            else riel_de(pedido, list(pedido.transiciones.all()))
        )
        lineas = list(pedido.lineas.all())
        pedido.portadas = [linea.producto for linea in lineas[:3]]
        pedido.mas_productos = max(len(lineas) - 3, 0)
    return pedidos


class PanelView(ClienteMixin, View):
    """`CO-192`: la puerta del panel, el resumen de la cuenta con los pedidos en
    curso (E1: sin pedidos, un mensaje)."""

    def get(self, request):
        return render(
            request,
            "cuenta/panel.html",
            {
                "seccion": "resumen",
                "pedidos": _con_riel(en_curso(request.user)),
            },
        )


class PedidosView(ClienteMixin, View):
    """Los pedidos en curso y, debajo, el historial: los despachados (B-11-004),
    los cancelados (B-08-008) y los retirados del local (B-11-006)."""

    def get(self, request):
        return render(
            request,
            "cuenta/pedidos.html",
            {
                "seccion": "pedidos",
                "en_curso": _con_riel(en_curso(request.user)),
                "historial": _con_riel(terminados(request.user)),
            },
        )


class HistorialView(ClienteMixin, View):
    """La dirección del historial anterior al plan 00 de interfaz: la usan los
    enlaces ya enviados por correo. Lleva al grupo del historial."""

    def get(self, request):
        return redirect(reverse("cuenta:pedidos") + "#historial")


class PedidoPropioView(ClienteMixin, View):
    """`CO-193`: ítems, precios efectivos, estados alcanzados y fecha de cada uno.

    Un pedido activo vuelve a pedirse cada 30 segundos (RF-18; B-08-002).
    """

    def get(self, request, numero):
        pedido = get_object_or_404(Pedido, numero=numero, usuario=request.user)
        lineas = list(
            pedido.lineas.select_related(
                "producto", "producto__productoeditorial", "caso_devolucion"
            )
        )
        for linea in lineas:
            linea.pedido = pedido
            linea.puede_decidir = demora.puede_decidir(linea)
            # Plan 09, ambigüedad 11: el reclamo se sigue al lado de su línea.
            linea.caso = getattr(linea, "caso_devolucion", None)
        # Plan 00, C1: la garantía desde acá; el arrepentimiento, por su botón.
        transiciones = list(pedido.transiciones.all())
        reclamo = devoluciones.estado_de_reclamo(pedido, devoluciones.GARANTIA)
        arrepentimiento = devoluciones.estado_de_reclamo(pedido, devoluciones.ARREPENTIMIENTO)
        return render(
            request,
            "cuenta/pedido.html",
            {
                "seccion": "pedidos",
                "pedido": pedido,
                "lineas": lineas,
                "transiciones": transiciones,
                "riel": (
                    None if pedido.canal == Pedido.PRESENCIAL else riel_de(pedido, transiciones)
                ),
                "cobrado": sum((linea.subtotal for linea in lineas), pedido.costo_envio),
                "activo": pedido.estado in ACTIVOS,
                "puede_reclamar": bool(reclamo and reclamo.puede),
                "reclamo_vencido": bool(reclamo and not reclamo.puede),
                "reclamo_hasta": reclamo.hasta if reclamo else None,
                "puede_arrepentirse": bool(arrepentimiento and arrepentimiento.puede),
                "arrepentimiento_hasta": arrepentimiento.hasta if arrepentimiento else None,
            },
        )


# ---------------------------------------------------------------------------
# CU-PED-OPC — CO-184, CO-094, CO-095 · CU-PED-CAN — CO-098
# ---------------------------------------------------------------------------


class DemoraView(ClienteMixin, View):
    """El Cliente elige qué hacer con un artículo demorado de su pedido.

    GET es `CO-184`; el primer POST, `CO-094` (la confirmación con su
    consecuencia); el segundo, `CO-095` o, si cancela, `CO-098`. Volver sin
    confirmar es `CO-156`: no queda nada registrado.
    """

    template_name = "cuenta/demora.html"

    def _linea(self, request, numero, linea):
        pedido = get_object_or_404(Pedido, numero=numero, usuario=request.user)
        linea = get_object_or_404(pedido.lineas.select_related("producto"), pk=linea)
        linea.pedido = pedido
        return pedido, linea

    def _situacion(self, request, linea):
        try:
            return demora.consultar_opciones(linea)
        except demora.DecisionRechazada as rechazo:
            messages.error(request, str(rechazo))
            return None

    def get(self, request, numero, linea):
        pedido, linea = self._linea(request, numero, linea)
        situacion = self._situacion(request, linea)
        if situacion is None:
            return redirect("cuenta:pedido", numero=numero)
        return render(
            request,
            self.template_name,
            {"seccion": "pedidos", "pedido": pedido, "situacion": situacion},
        )

    def post(self, request, numero, linea):
        pedido, linea = self._linea(request, numero, linea)
        clave = request.POST.get("opcion", "")
        if "confirmar" not in request.POST:
            situacion = self._situacion(request, linea)
            if situacion is None:
                return redirect("cuenta:pedido", numero=numero)
            try:
                elegida = demora.seleccionar_opcion(linea, clave)
            except demora.DecisionRechazada as rechazo:
                messages.error(request, str(rechazo))
                return redirect("cuenta:demora", numero=numero, linea=linea.pk)
            return render(
                request,
                self.template_name,
                {
                    "seccion": "pedidos",
                    "pedido": pedido,
                    "situacion": situacion,
                    "elegida": elegida,
                },
            )
        try:
            confirmacion = demora.confirmar_opcion(pedido, linea.pk, request.user, clave)
        except demora.DecisionRechazada as rechazo:
            messages.error(request, str(rechazo))
            return redirect("cuenta:pedido", numero=numero)
        except Exception:  # noqa: BLE001 - E1 de CO-098: la transacción se deshizo entera
            logger.exception("Falló la decisión sobre la línea %s.", linea.pk)
            if clave == LineaPedido.CANCELAR:
                demora.avisar_fallo_de_cancelacion(pedido, linea)
            messages.error(
                request, "No se pudo completar. No quedó ningún cambio: intentá de nuevo."
            )
            return redirect("cuenta:demora", numero=numero, linea=linea.pk)
        if confirmacion.opcion is demora.CANCELAR:
            messages.success(
                request,
                f"Artículo cancelado. Te acreditamos {confirmacion.puntos} pts; "
                f"tu saldo es de {confirmacion.saldo} pts.",
            )
        else:
            messages.success(request, confirmacion.opcion.consecuencia)
        return redirect("cuenta:pedido", numero=numero)


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
