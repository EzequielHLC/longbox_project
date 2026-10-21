"""El reclamo del Cliente (`CU-DEV-SOL`; plan 00, C1).

- **Garantía**, desde «Mi cuenta» (`cuenta/`): GET es `CO-185` (el formulario, o
  E1 y E2 si no corresponde); POST es `CO-099`. El pedido se busca entre los del
  Cliente: el de otro responde 404.
- **Arrepentimiento**, desde el botón de arrepentimiento (`tienda/arrepentimiento/`):
  **sin registración** (Res. 424/2020). Con sesión, el pedido es del Cliente; sin
  sesión, el número de pedido y el correo de la compra tienen que coincidir. La
  respuesta es la misma si no coinciden o si el pedido no existe.
"""

from django.contrib import messages
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View

from apps.accounts.models import Usuario
from apps.accounts.views_cuenta import ClienteMixin
from apps.devoluciones import servicios
from apps.pedidos.models import Pedido

CLAVE_PEDIDO = "arrepentimiento_pedido"


def _origen(request):
    return request.build_absolute_uri("/").rstrip("/")


def _avisar_rechazo(request, rechazo):
    if isinstance(rechazo, servicios.CasoExistente):  # E2: el caso existente y su estado
        for caso in rechazo.casos:
            messages.info(
                request,
                f"Reclamo {caso.numero} por {servicios.nombre(caso.linea.producto)}: "
                f"{caso.get_estado_display().lower()}.",
            )
    messages.error(request, str(rechazo))


class SolicitudView(ClienteMixin, View):
    """La garantía: defecto de fabricación o error de imprenta, con fotos."""

    template_name = "devoluciones/cuenta_solicitud.html"

    def _pedido(self, request, numero):
        return get_object_or_404(Pedido, numero=numero, usuario=request.user)

    def get(self, request, numero, datos=None, errores=None):
        pedido = self._pedido(request, numero)
        try:
            solicitud = servicios.iniciar_solicitud(pedido, servicios.GARANTIA)
        except servicios.OperacionRechazada as rechazo:  # E1, E2, o sin despachar
            _avisar_rechazo(request, rechazo)
            return redirect("cuenta:pedido", numero=pedido.numero)
        return render(
            request,
            self.template_name,
            {
                "seccion": "pedidos",
                "pedido": pedido,
                "solicitud": solicitud,
                "datos": datos or {},
                "errores": errores or {},
                "maximo_fotos": servicios.MAXIMO_IMAGENES,
            },
        )

    def post(self, request, numero):
        pedido = self._pedido(request, numero)
        datos = {
            "linea": request.POST.get("linea", ""),
            "motivo": request.POST.get("motivo", ""),
            "descripcion": request.POST.get("descripcion", ""),
        }
        linea = datos["linea"]
        try:
            apertura = servicios.registrar_caso(
                pedido,
                int(linea) if linea.isdigit() else 0,
                request.user,
                datos["motivo"],
                datos["descripcion"],
                request.FILES.getlist("fotos"),
                origen=_origen(request),
            )
        except servicios.EvidenciaInvalida as rechazo:  # E3, E4: el formulario sigue abierto
            return self.get(request, numero, datos=datos, errores={"fotos": str(rechazo)})
        except (servicios.PlazoVencido, servicios.CasoExistente):
            return self.get(request, numero)
        except servicios.OperacionRechazada as rechazo:
            return self.get(request, numero, datos=datos, errores={"general": str(rechazo)})
        messages.success(
            request,
            f"Registramos tu reclamo {apertura.caso.numero}. Te escribimos para coordinar "
            "el cambio o el reintegro.",
        )
        return redirect("cuenta:pedido", numero=numero)


# ---------------------------------------------------------------------------
# El botón de arrepentimiento (Res. 424/2020)
# ---------------------------------------------------------------------------


def _es_cliente(usuario):
    return usuario.is_authenticated and usuario.rol == Usuario.CLIENTE


class ArrepentimientoView(View):
    """La puerta del botón: con sesión, los pedidos del Cliente; sin sesión, el
    número de pedido y el correo de la compra."""

    template_name = "devoluciones/arrepentimiento.html"

    def get(self, request, error=""):
        pedidos = []
        if _es_cliente(request.user):
            pedidos = [
                pedido
                for pedido in Pedido.objects.filter(
                    usuario=request.user, canal=Pedido.ONLINE
                ).order_by("-fecha", "-pk")[:20]
                if servicios.admite_reclamos(pedido, servicios.ARREPENTIMIENTO)
            ]
        return render(
            request,
            self.template_name,
            {
                "pedidos": pedidos,
                "error": error,
                "dias": servicios.plazo_dias(servicios.ARREPENTIMIENTO),
            },
        )

    def post(self, request):
        pedido = servicios.pedido_por_numero_y_correo(
            request.POST.get("numero"), request.POST.get("correo")
        )
        if pedido is None:
            return self.get(
                request, error="No encontramos una compra online con ese número y ese correo."
            )
        request.session[CLAVE_PEDIDO] = pedido.pk
        return redirect("devoluciones_tienda:pedido", numero=pedido.numero)


class ArrepentimientoPedidoView(View):
    """`CO-185` y `CO-099` del arrepentimiento: qué artículos devuelve."""

    template_name = "devoluciones/arrepentimiento_pedido.html"

    def _pedido(self, request, numero):
        pedido = Pedido.objects.filter(numero=numero, canal=Pedido.ONLINE).first()
        if pedido is None:
            raise Http404("No existe ese pedido.")
        propio = _es_cliente(request.user) and pedido.usuario_id == request.user.pk
        if not propio and request.session.get(CLAVE_PEDIDO) != pedido.pk:
            raise Http404("No existe ese pedido.")
        return pedido

    def get(self, request, numero, error=""):
        pedido = self._pedido(request, numero)
        try:
            solicitud = servicios.iniciar_solicitud(pedido, servicios.ARREPENTIMIENTO)
        except servicios.OperacionRechazada as rechazo:
            _avisar_rechazo(request, rechazo)
            return redirect("devoluciones_tienda:inicio")
        return render(
            request,
            self.template_name,
            {"pedido": pedido, "solicitud": solicitud, "error": error},
        )

    def post(self, request, numero):
        pedido = self._pedido(request, numero)
        lineas = [int(v) for v in request.POST.getlist("linea") if v.isdigit()]
        try:
            apertura = servicios.registrar_arrepentimiento(
                pedido,
                lineas,
                usuario=request.user if _es_cliente(request.user) else None,
                descripcion=request.POST.get("descripcion", ""),
                origen=_origen(request),
            )
        except (servicios.PlazoVencido, servicios.CasoExistente) as rechazo:
            _avisar_rechazo(request, rechazo)
            return redirect("devoluciones_tienda:inicio")
        except servicios.OperacionRechazada as rechazo:
            return self.get(request, numero, error=str(rechazo))
        request.session.pop(CLAVE_PEDIDO, None)
        return render(
            request,
            "devoluciones/arrepentimiento_listo.html",
            {"pedido": pedido, "casos": apertura.casos},
        )
