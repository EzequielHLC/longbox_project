"""El carrito en la tienda (`CU-TDA-CRC`, `CRA`, `CRM`, `CRB`).

Invitados y Clientes. Al personal, cualquier dirección del carrito le responde
403 (plan 07, segunda parte, ambigüedad 3): la restricción vive acá, en el
servidor, y no sólo en el botón que la ficha no le muestra.

Una línea se busca siempre **dentro** del carrito de quien pide: la de otro
carrito responde 404, como si no existiera.
"""

from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.views import View

from apps.core.templatetags.moneda import pesos
from apps.core.views_tienda import visibles
from apps.tienda import carrito as servicio
from apps.tienda.models import LineaCarrito


def _cantidad(request):
    texto = request.POST.get("cantidad", "1").strip()
    if not texto.lstrip("-").isdigit():
        raise servicio.OperacionRechazada("Escribí la cantidad con números.")
    return int(texto)


class CarritoMixin:
    def dispatch(self, request, *args, **kwargs):
        if not servicio.puede_tener_carrito(request.user):
            raise PermissionDenied("El carrito es de las cuentas de cliente.")
        return super().dispatch(request, *args, **kwargs)

    def linea(self, request, pk):
        carrito = servicio.carrito_de(request)
        if carrito is None:
            raise Http404("La línea no está en tu carrito.")
        return get_object_or_404(
            LineaCarrito.objects.select_related("producto"), pk=pk, carrito=carrito
        )


class CarritoView(CarritoMixin, View):
    """`CO-178`: sólo lee."""

    def get(self, request):
        consultado = servicio.consultar(servicio.carrito_de(request))
        return render(request, "tienda/carrito.html", {"carrito": consultado})


class AgregarView(CarritoMixin, View):
    """`CO-083`, desde la ficha pública (`CU-TDA-CAT` paso 6)."""

    def post(self, request, pk):
        producto = get_object_or_404(visibles(), pk=pk)
        volver = request.POST.get("volver", "")
        if not url_has_allowed_host_and_scheme(volver, allowed_hosts={request.get_host()}):
            volver = ""
        try:
            resultado = servicio.agregar(
                servicio.carrito_de(request, crear=True), producto, _cantidad(request)
            )
        except servicio.OperacionRechazada as rechazo:
            messages.error(request, str(rechazo))
        else:
            if resultado.tope is not None:
                messages.warning(
                    request,
                    f"Hay {resultado.tope} disponibles de «{producto.titulo}»: "
                    f"el carrito quedó con {resultado.tope}.",
                )
            else:
                accion = "reservó" if resultado.linea.producto.estado == "pre_venta" else "agregó"
                messages.success(request, f"Se {accion} «{producto.titulo}» en el carrito.")
        return redirect(volver or "tienda:carrito")


class CantidadView(CarritoMixin, View):
    """`CO-084`."""

    def post(self, request, pk):
        linea = self.linea(request, pk)
        try:
            resultado = servicio.modificar_cantidad(linea, _cantidad(request))
        except servicio.OperacionRechazada as rechazo:
            messages.error(request, str(rechazo))
        else:
            if resultado.tope is not None:
                messages.warning(
                    request,
                    f"Hay {resultado.tope} disponibles de «{linea.producto.titulo}»: "
                    f"la línea quedó con {resultado.tope}.",
                )
            else:
                subtotal = pesos(resultado.linea.precio_vigente * resultado.linea.cantidad)
                messages.success(
                    request,
                    f"«{linea.producto.titulo}»: {resultado.linea.cantidad} "
                    f"unidad(es), {subtotal}.",
                )
        return redirect("tienda:carrito")


class QuitarView(CarritoMixin, View):
    """`CO-085`. Sin confirmación: se deshace volviendo a agregar."""

    def post(self, request, pk):
        linea = self.linea(request, pk)
        titulo = linea.producto.titulo
        servicio.quitar(linea)
        messages.success(request, f"Se quitó «{titulo}» del carrito.")
        return redirect("tienda:carrito")
