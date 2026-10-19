"""La compra en la tienda (plan 07, sexta parte): `CU-TDA-CMP` y `CU-TDA-INV`.

Quién entra a qué:

- **El checkout con cuenta** es del Cliente. Un invitado va al inicio de sesión;
  el personal recibe 403, como en el carrito.
- **La compra como invitado** es de quien no tiene sesión. Un Cliente que entra
  ahí va a su checkout.
- **El resultado de un cobro** lo ve sólo quien lo inició: su cuenta, o la
  sesión del invitado que lo confirmó.
- **El aviso de la pasarela** no tiene sesión ni CSRF: viene de servidor a
  servidor y se autentica por su firma o por la API de la pasarela.
"""

import logging

from django.contrib import messages
from django.contrib.auth.views import redirect_to_login
from django.core.exceptions import PermissionDenied
from django.http import Http404, HttpResponse, HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt

from apps.accounts.models import Usuario
from apps.core.models import ConfiguracionSistema
from apps.core.templatetags.moneda import pesos
from apps.tienda import carrito as servicio_carrito
from apps.tienda import compra
from apps.tienda.forms import DatosDeInvitadoForm, DireccionDeEnvioForm
from apps.tienda.mercadopago import AvisoSinResultado, SinCredencial
from apps.tienda.models import CobroEnCurso, LineaCarrito
from apps.tienda.pasarelas import CABECERA_FIRMA, AvisoInvalido, PasarelaDePrueba, pasarela

logger = logging.getLogger(__name__)


def _es_cliente(usuario):
    return usuario.is_authenticated and usuario.rol == Usuario.CLIENTE


class CompraMixin:
    """Invitados y Clientes, como el carrito: el personal no compra con su cuenta."""

    def dispatch(self, request, *args, **kwargs):
        if not servicio_carrito.puede_tener_carrito(request.user):
            raise PermissionDenied("La compra es de las cuentas de cliente.")
        return super().dispatch(request, *args, **kwargs)


class ClienteMixin(CompraMixin):
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect_to_login(request.get_full_path())
        return super().dispatch(request, *args, **kwargs)


class InvitadoMixin(CompraMixin):
    def dispatch(self, request, *args, **kwargs):
        # El 403 del personal va antes que la redirección del Cliente.
        if not servicio_carrito.puede_tener_carrito(request.user):
            raise PermissionDenied("La compra es de las cuentas de cliente.")
        if request.user.is_authenticated:
            return redirect("compra:checkout")
        return super().dispatch(request, *args, **kwargs)


def _al_carrito(request, bloqueo):
    messages.error(request, str(bloqueo))
    return redirect("tienda:carrito")


def _recordar_cobro(request, cobro):
    """Para que el invitado pueda ver el resultado de su propio cobro, y nadie más."""
    propios = request.session.get(compra.CLAVE_COBROS, [])
    request.session[compra.CLAVE_COBROS] = [*propios[-9:], cobro.referencia]


# ---------------------------------------------------------------------------
# CO-179 procederAlPago — desde el carrito
# ---------------------------------------------------------------------------


class PagarView(CompraMixin, View):
    def post(self, request):
        try:
            compra.proceder_al_pago(servicio_carrito.carrito_de(request))
        except compra.BloqueoDeAvance as bloqueo:
            return _al_carrito(request, bloqueo)
        if request.user.is_authenticated:
            return redirect("compra:checkout")
        if request.POST.get("modo") == "invitado":
            return redirect("compra:invitado")
        # Iniciar sesión fusiona el carrito (CO-086) y vuelve al checkout.
        return redirect_to_login(reverse("compra:checkout"))


# ---------------------------------------------------------------------------
# CU-TDA-CMP — CO-180, CO-087, CO-103, CO-104, CO-190, CO-088
# ---------------------------------------------------------------------------


class CheckoutView(ClienteMixin, View):
    template_name = "tienda/checkout.html"

    def _contexto(self, request, formulario=None):
        envio = compra.envio_del_checkout(request.session, request.user)
        hecho = compra.iniciar_checkout(
            servicio_carrito.carrito_de(request),
            request.user,
            envio,
            retiro=compra.retiro_del_checkout(request.session),
        )
        return {
            "resumen": hecho,
            "form": formulario or DireccionDeEnvioForm(initial=envio),
            "editar_direccion": formulario is not None or not hecho.direccion_completa,
            "texto_direccion": compra.texto_de_direccion(envio),
        }

    def get(self, request):
        try:
            return render(request, self.template_name, self._contexto(request))
        except compra.BloqueoDeAvance as bloqueo:
            return _al_carrito(request, bloqueo)

    def post(self, request):
        """`CO-087`: la dirección de este checkout, o la modalidad. El perfil no cambia."""
        if "modalidad" in request.POST:
            retiro = request.POST["modalidad"] == "retiro"
            compra.declarar_modalidad(request.session, retiro)
            messages.success(
                request,
                (
                    "Lo retirás en el local, sin costo de envío."
                    if retiro
                    else "Te lo enviamos a domicilio."
                ),
            )
            return redirect("compra:checkout")
        formulario = DireccionDeEnvioForm(request.POST)
        try:
            if not formulario.is_valid():
                return render(request, self.template_name, self._contexto(request, formulario))
            hecho = compra.iniciar_checkout(servicio_carrito.carrito_de(request), request.user, {})
        except compra.BloqueoDeAvance as bloqueo:
            return _al_carrito(request, bloqueo)
        costo = compra.declarar_direccion_de_envio(
            request.session, formulario.cleaned_data, hecho.subtotal_productos
        )
        compra.declarar_modalidad(request.session, False)
        envio = "gratis" if costo == 0 else pesos(costo)
        messages.success(request, f"Se enviará a la dirección declarada. Envío: {envio}.")
        return redirect("compra:checkout")


class CanjeView(ClienteMixin, View):
    """`CO-103` (aplicar) y `CO-104` (revertir) sobre una línea del propio carrito."""

    def post(self, request, pk):
        carrito = servicio_carrito.carrito_de(request)
        if carrito is None:
            raise Http404("La línea no está en tu carrito.")
        linea = get_object_or_404(
            LineaCarrito.objects.select_related("producto", "carrito"), pk=pk, carrito=carrito
        )
        if request.POST.get("accion") == "revertir":
            compra.revertir_canje(linea, request.user)
            messages.success(request, f"«{linea.producto.titulo}» vuelve a pagarse en dinero.")
            return redirect("compra:checkout")
        try:
            compra.aplicar_canje(linea, request.user)
        except compra.CanjeRechazado as rechazo:
            messages.error(request, str(rechazo))
        else:
            messages.success(request, f"«{linea.producto.titulo}» queda cubierto con puntos.")
        return redirect("compra:checkout")


class ConfirmarCanjeView(ClienteMixin, View):
    """`CO-190`: vuelve al checkout. Si el total quedó en cero, lo informa (A2)."""

    def post(self, request):
        envio = compra.envio_del_checkout(request.session, request.user)
        try:
            hecho = compra.iniciar_checkout(
                servicio_carrito.carrito_de(request),
                request.user,
                envio,
                retiro=compra.retiro_del_checkout(request.session),
            )
        except compra.BloqueoDeAvance as bloqueo:
            return _al_carrito(request, bloqueo)
        if hecho.total == 0:
            messages.info(
                request, "Tu compra se completa íntegramente con puntos: no hace falta pagar."
            )
        return redirect("compra:checkout")


class ConfirmarView(ClienteMixin, View):
    """`CO-088`: congela el cobro y va a la pasarela, o confirma si el total es cero."""

    def post(self, request):
        envio = compra.envio_del_checkout(request.session, request.user)
        try:
            confirmacion = compra.confirmar_pedido(
                servicio_carrito.carrito_de(request),
                request.user,
                envio,
                request,
                pasarela(),
                retiro=compra.retiro_del_checkout(request.session),
            )
        except compra.BloqueoDeAvance as bloqueo:
            return _al_carrito(request, bloqueo)
        except compra.CanjeRechazado as rechazo:
            messages.error(request, str(rechazo))
            return redirect("compra:checkout")
        except SinCredencial:
            messages.error(request, "El pago online no está disponible en este momento.")
            return redirect("compra:checkout")
        return _ir_a_pagar(request, confirmacion)


def _ir_a_pagar(request, confirmacion):
    _recordar_cobro(request, confirmacion.cobro)
    if confirmacion.redireccion:
        return redirect(confirmacion.redireccion)
    if confirmacion.pedido is None and confirmacion.cobro.monto > 0:
        # La pasarela no aceptó iniciar el cobro: no se le cobró nada a nadie.
        messages.error(request, "No pudimos conectar con la pasarela de pago. Probá de nuevo.")
        return redirect("tienda:carrito")
    return redirect("compra:resultado", referencia=confirmacion.cobro.referencia)


# ---------------------------------------------------------------------------
# CU-TDA-INV — CO-181, CO-090, CO-091
# ---------------------------------------------------------------------------


class InvitadoView(InvitadoMixin, View):
    """`CO-181` (GET) y `CO-090` (POST): el formulario de datos del invitado."""

    template_name = "tienda/invitado.html"

    def get(self, request):
        try:
            compra.iniciar_compra_como_invitado(servicio_carrito.carrito_de(request))
        except compra.BloqueoDeAvance as bloqueo:
            return _al_carrito(request, bloqueo)
        datos = request.session.get(compra.CLAVE_INVITADO) or None
        return render(request, self.template_name, {"form": DatosDeInvitadoForm(initial=datos)})

    def post(self, request):
        formulario = DatosDeInvitadoForm(request.POST)
        carrito = servicio_carrito.carrito_de(request)
        try:
            compra.iniciar_compra_como_invitado(carrito)
            if not formulario.is_valid():
                # E1: los campos con error se resaltan y lo escrito se conserva.
                return render(request, self.template_name, {"form": formulario})
            # E2: el stock se verifica en el momento.
            compra.iniciar_checkout(carrito, None, formulario.cleaned_data)
        except compra.BloqueoDeAvance as bloqueo:
            return _al_carrito(request, bloqueo)
        request.session[compra.CLAVE_INVITADO] = formulario.cleaned_data
        return redirect("compra:invitado_resumen")


class InvitadoResumenView(InvitadoMixin, View):
    """La salida de `CO-090`: el resumen, sin canje de puntos."""

    def get(self, request):
        datos = request.session.get(compra.CLAVE_INVITADO)
        if not datos:
            return redirect("compra:invitado")
        carrito = servicio_carrito.carrito_de(request)
        try:
            compra.iniciar_compra_como_invitado(carrito)
            hecho = compra.iniciar_checkout(carrito, None, datos)
        except compra.BloqueoDeAvance as bloqueo:
            return _al_carrito(request, bloqueo)
        return render(
            request,
            "tienda/invitado_resumen.html",
            {
                "resumen": hecho,
                "datos": datos,
                "texto_direccion": compra.texto_de_direccion(datos),
                "tiene_cuenta": compra.cuenta_con_correo(datos["correo"]),
            },
        )


class InvitadoConfirmarView(InvitadoMixin, View):
    """`CO-091`: siempre a la pasarela."""

    def post(self, request):
        datos = request.session.get(compra.CLAVE_INVITADO)
        if not datos:
            return redirect("compra:invitado")
        try:
            confirmacion = compra.confirmar_pedido_de_invitado(
                servicio_carrito.carrito_de(request), datos, request, pasarela()
            )
        except compra.BloqueoDeAvance as bloqueo:
            return _al_carrito(request, bloqueo)
        except SinCredencial:
            messages.error(request, "El pago online no está disponible en este momento.")
            return redirect("compra:invitado_resumen")
        return _ir_a_pagar(request, confirmacion)


# ---------------------------------------------------------------------------
# El resultado: confirmación (paso 8), rechazo (E2) o fallo con reembolso (E3)
# ---------------------------------------------------------------------------


class ResultadoView(View):
    def get(self, request, referencia):
        cobro = get_object_or_404(
            CobroEnCurso.objects.select_related("pedido"), referencia=referencia
        )
        propio = (
            cobro.usuario_id == request.user.pk
            if cobro.usuario_id
            else referencia in request.session.get(compra.CLAVE_COBROS, [])
        )
        if not propio:
            raise Http404("No hay un pago con esa referencia.")
        if cobro.tipo == CobroEnCurso.DESPACHO and cobro.estado != CobroEnCurso.PENDIENTE:
            from apps.almacen.views_cuenta import resultado_de_pago

            return resultado_de_pago(request, cobro)
        if cobro.estado == CobroEnCurso.PROCESADO:
            # El checkout terminó: la próxima compra arranca de cero.
            request.session.pop(compra.CLAVE_ENVIO, None)
            request.session.pop(compra.CLAVE_RETIRO, None)
            request.session.pop(compra.CLAVE_INVITADO, None)
        volver = "compra:checkout" if cobro.usuario_id else "compra:invitado_resumen"
        return render(
            request,
            "tienda/resultado.html",
            {"cobro": cobro, "pedido": cobro.pedido, "volver": volver},
        )


# ---------------------------------------------------------------------------
# CO-089 registrarResultadoDePago — el aviso de la pasarela
# ---------------------------------------------------------------------------


@method_decorator(csrf_exempt, name="dispatch")
class AvisoView(View):
    """El webhook. Contesta 200 a todo aviso auténtico, aunque ya se haya procesado:
    una pasarela que recibe un error reintenta, y el reintento no debe hacer nada."""

    def post(self, request, clave):
        try:
            elegida = pasarela(clave)
            aviso = elegida.leer_aviso(
                request.body, request.headers, request.META.get("QUERY_STRING", "")
            )
        except AvisoSinResultado:
            return HttpResponse("Recibido.")
        except (AvisoInvalido, SinCredencial) as error:
            logger.warning("Aviso de pago descartado (%s): %s", clave, error)
            return HttpResponseBadRequest("Aviso inválido.")
        cobro = compra.registrar_resultado_de_pago(aviso, elegida)
        if cobro is None:
            raise Http404("No hay un cobro con esa referencia.")
        return HttpResponse("Recibido.")


class PasarelaDePruebaView(View):
    """La pantalla de la pasarela de prueba (B-07-031).

    Es la pasarela, no la tienda: no pide sesión. Avisa al sistema con el mismo
    aviso firmado que recibe `AvisoView`, y después devuelve al Cliente al
    resultado, como haría una pasarela real.
    """

    MOTIVOS = (  # noqa: RUF012
        "Fondos insuficientes.",
        "La tarjeta fue rechazada por el banco emisor.",
        "Los datos de la tarjeta no son válidos.",
    )

    def _cobro(self, referencia):
        cobro = get_object_or_404(
            CobroEnCurso, referencia=referencia, pasarela=ConfiguracionSistema.PASARELA_PRUEBA
        )
        return cobro

    def get(self, request, referencia):
        cobro = self._cobro(referencia)
        return render(
            request,
            "tienda/pasarela_prueba.html",
            {"cobro": cobro, "motivos": self.MOTIVOS},
        )

    def post(self, request, referencia):
        cobro = self._cobro(referencia)
        if cobro.estado == CobroEnCurso.PENDIENTE:
            prueba = PasarelaDePrueba()
            aprobado = request.POST.get("resultado") == "aprobar"
            motivo = request.POST.get("motivo", "")
            cuerpo, firma = prueba.armar_aviso(
                cobro,
                aprobado=aprobado,
                mensaje="" if aprobado else (motivo if motivo in self.MOTIVOS else self.MOTIVOS[0]),
            )
            aviso = prueba.leer_aviso(cuerpo, {CABECERA_FIRMA: firma})
            compra.registrar_resultado_de_pago(aviso, prueba)
        return redirect("compra:resultado", referencia=cobro.referencia)
