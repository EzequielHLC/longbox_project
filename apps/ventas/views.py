"""El mostrador (`CU-VTA-REG`). Cajero y Administrador; el Cliente recibe 403."""

from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views import View

from apps.accounts.models import Usuario
from apps.catalog.models import Producto
from apps.core.mixins import RolRequeridoMixin
from apps.pedidos.models import Pedido, TransaccionPago
from apps.ventas import ticket as servicio


class MostradorMixin(RolRequeridoMixin):
    roles_permitidos = (Usuario.CAJERO, Usuario.ADMINISTRADOR)


def _al_mostrador(request, error=None, busqueda=""):
    if error:
        messages.error(request, str(error))
    url = reverse("core:mostrador")
    return redirect(f"{url}?q={busqueda}" if busqueda else url)


class MostradorView(MostradorMixin, View):
    """El ticket en curso y la búsqueda de productos."""

    def get(self, request):
        busqueda = request.GET.get("q", "").strip()
        return render(
            request,
            "ventas/mostrador.html",
            {
                "ticket": servicio.consultar(request.session),
                "busqueda": busqueda,
                "resultados": servicio.buscar(busqueda) if busqueda else [],
                "medios": [
                    (valor, etiqueta)
                    for valor, etiqueta in TransaccionPago.MEDIO_CHOICES
                    if valor in servicio.MEDIOS
                ],
            },
        )


class NuevaVentaView(MostradorMixin, View):
    """`CO-078`: descarta el ticket en curso y abre uno en blanco."""

    def post(self, request):
        try:
            servicio.abrir(request.session)
        except servicio.VentaRechazada as error:
            return _al_mostrador(request, error)
        return _al_mostrador(request)


class AgregarView(MostradorMixin, View):
    """`CO-079`. Con un producto elegido, o con un texto: si coincide exacto con un
    código, se agrega; si no, se buscan coincidencias por título (B-06-003)."""

    def post(self, request):
        cantidad_texto = request.POST.get("cantidad", "1").strip() or "1"
        if not cantidad_texto.isdigit():
            return _al_mostrador(request, "Escribí la cantidad con números.")
        cantidad = int(cantidad_texto)
        if request.POST.get("producto"):
            producto = get_object_or_404(Producto, pk=request.POST["producto"])
        else:
            texto = request.POST.get("q", "").strip()
            producto = servicio.buscar_exacto(texto)
            if producto is None:
                return _al_mostrador(request, busqueda=texto)
        try:
            servicio.agregar(request.session, producto, cantidad)
        except servicio.VentaRechazada as error:
            return _al_mostrador(request, error)
        return _al_mostrador(request)


class QuitarView(MostradorMixin, View):
    """`CO-080`."""

    def post(self, request, pk):
        servicio.quitar(request.session, pk)
        return _al_mostrador(request)


class ClienteView(MostradorMixin, View):
    """`CO-081` (vincular) y quitar la cuenta vinculada por error."""

    def post(self, request):
        if request.POST.get("accion") == "quitar":
            servicio.desvincular(request.session)
            return _al_mostrador(request)
        try:
            cliente = servicio.vincular(request.session, request.POST.get("cliente", ""))
        except servicio.VentaRechazada as error:
            return _al_mostrador(request, error)
        messages.success(request, f"Cliente: {cliente.get_full_name() or cliente.email}.")
        return _al_mostrador(request)


class CanjeView(MostradorMixin, View):
    """`CO-103` y `CO-104` sobre un ítem del ticket."""

    def post(self, request, pk):
        if request.POST.get("accion") == "revertir":
            servicio.revertir_canje(request.session, pk)
            return _al_mostrador(request)
        try:
            servicio.aplicar_canje(request.session, pk)
        except servicio.VentaRechazada as error:
            return _al_mostrador(request, error)
        return _al_mostrador(request)


class ConfirmarView(MostradorMixin, View):
    """`CO-082`."""

    def post(self, request):
        try:
            pedido = servicio.confirmar(
                request.session, request.POST.get("medio", ""), request.user
            )
        except servicio.VentaRechazada as error:
            return _al_mostrador(request, error)
        return redirect("ventas:comprobante", numero=pedido.numero)


class ComprobanteView(MostradorMixin, View):
    """La salida de `CO-082`: el detalle de la venta, imprimible (B-06-004)."""

    def get(self, request, numero):
        pedido = get_object_or_404(
            Pedido.objects.select_related("usuario", "transaccion"),
            numero=numero,
            canal=Pedido.PRESENCIAL,
        )
        lineas = list(pedido.lineas.select_related("producto"))
        acreditacion = pedido.movimientos_puntos.filter(tipo="acreditacion").first()
        return render(
            request,
            "ventas/comprobante.html",
            {
                "pedido": pedido,
                "lineas": lineas,
                "transaccion": pedido.transaccion,
                "puntos_acreditados": acreditacion.cantidad if acreditacion else 0,
                "puntos_canjeados": sum(linea.puntos_canjeados for linea in lineas),
            },
        )
