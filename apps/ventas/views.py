"""El mostrador (`CU-VTA-REG`). Cajero y Administrador; el Cliente recibe 403."""

from decimal import Decimal, InvalidOperation

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


ULTIMO_AGREGADO = "mostrador_ultimo_agregado"
VENTA_REGISTRADA = "mostrador_venta_registrada"


def _importe(texto):
    """Lo recibido en efectivo, escrito por el cajero; vacío o ilegible, nada."""
    try:
        valor = Decimal(str(texto).replace(".", "").replace(",", ".").strip())
    except (InvalidOperation, ValueError):
        return None
    return valor if valor > 0 else None


class MostradorView(MostradorMixin, View):
    """El ticket en curso y la búsqueda de productos."""

    def get(self, request):
        busqueda = request.GET.get("q", "").strip()
        return render(
            request,
            "ventas/mostrador.html",
            {
                "ticket": servicio.consultar(request.session),
                # Plan 00 de interfaz, segunda parte, 13.3: la fila recién agregada destella.
                "ultimo_agregado": request.session.pop(ULTIMO_AGREGADO, None),
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
        request.session[ULTIMO_AGREGADO] = producto.pk
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
        # 13.1 y 13.6: el vuelto se calcula para mostrarlo; no se guarda en ningún lado.
        recibido = _importe(request.POST.get("recibido", ""))
        # Una venta pagada sólo con puntos no tiene transacción de dinero.
        transaccion = TransaccionPago.objects.filter(pedido=pedido).first()
        vuelto = None
        if (
            transaccion
            and transaccion.medio == TransaccionPago.EFECTIVO
            and recibido
            and recibido >= transaccion.monto
        ):
            vuelto = str(recibido - transaccion.monto)
        request.session[VENTA_REGISTRADA] = {
            "numero": pedido.numero,
            "recibido": str(recibido) if vuelto is not None else None,
            "vuelto": vuelto,
        }
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
        registrada = request.session.get(VENTA_REGISTRADA) or {}
        if registrada.get("numero") == pedido.numero:
            request.session.pop(VENTA_REGISTRADA)
        else:
            registrada = {}
        return render(
            request,
            "ventas/comprobante.html",
            {
                "pedido": pedido,
                "lineas": lineas,
                "transaccion": getattr(pedido, "transaccion", None),
                "puntos_acreditados": acreditacion.cantidad if acreditacion else 0,
                "puntos_canjeados": sum(linea.puntos_canjeados for linea in lineas),
                # 13.6: recién confirmada, la pantalla lo dice y ofrece la siguiente.
                "recien_registrada": bool(registrada),
                "recibido": Decimal(registrada["recibido"]) if registrada.get("recibido") else None,
                "vuelto": Decimal(registrada["vuelto"]) if registrada.get("vuelto") else None,
            },
        )
