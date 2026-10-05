"""El carrito en la tienda (`CU-TDA-CRC`, `CRA`, `CRM`, `CRB`).

Invitados y Clientes. Al personal, cualquier dirección del carrito le responde
403 (plan 07, segunda parte, ambigüedad 3): la restricción vive acá, en el
servidor, y no sólo en el botón que la ficha no le muestra.

Una línea se busca siempre **dentro** del carrito de quien pide: la de otro
carrito responde 404, como si no existiera.
"""

from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
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
    """`CO-083`, desde la ficha pública (`CU-TDA-CAT` paso 6) o desde la tarjeta.

    La tarjeta del catálogo y de la portada agrega una unidad sin salir de la
    pantalla (B-07-014): su guion pide la respuesta en JSON, con el mensaje y
    las unidades para el encabezado. Sin guion, el formulario se envía y vuelve
    a la pantalla de origen con el mismo mensaje. La operación es la misma.
    """

    def post(self, request, pk):
        producto = get_object_or_404(visibles(), pk=pk)
        volver = request.POST.get("volver", "")
        if not url_has_allowed_host_and_scheme(volver, allowed_hosts={request.get_host()}):
            volver = ""
        carrito = servicio.carrito_de(request, crear=True)
        try:
            resultado = servicio.agregar(carrito, producto, _cantidad(request))
        except servicio.OperacionRechazada as rechazo:
            nivel, mensaje = "error", str(rechazo)
        else:
            if resultado.tope is not None:
                nivel = "atencion"
                mensaje = (
                    f"Hay {resultado.tope} disponibles de «{producto.titulo}»: "
                    f"el carrito quedó con {resultado.tope}."
                )
            else:
                accion = "reservó" if resultado.linea.producto.estado == "pre_venta" else "agregó"
                nivel, mensaje = "exito", f"Se {accion} «{producto.titulo}» en el carrito."
        if request.headers.get("X-Requested-With") == "fetch":
            return JsonResponse(
                {"nivel": nivel, "mensaje": mensaje, "unidades": servicio.unidades_en(carrito)},
                status=400 if nivel == "error" else 200,
            )
        {"error": messages.error, "atencion": messages.warning, "exito": messages.success}[nivel](
            request, mensaje
        )
        return redirect(volver or "tienda:carrito")


def _responder(request, nivel, mensaje):
    """La respuesta de CO-084 y CO-085: JSON con el carrito dibujado si la pidió el
    guion del carrito (B-07-028); si no, el mensaje y de vuelta al carrito."""
    if request.headers.get("X-Requested-With") == "fetch":
        carrito = servicio.carrito_de(request)
        html = render_to_string(
            "tienda/_carrito.html", {"carrito": servicio.consultar(carrito)}, request=request
        )
        return JsonResponse(
            {
                "nivel": nivel,
                "mensaje": mensaje,
                "unidades": servicio.unidades_en(carrito),
                "html": html,
            }
        )
    {"error": messages.error, "atencion": messages.warning, "exito": messages.success}[nivel](
        request, mensaje
    )
    return redirect("tienda:carrito")


class CantidadView(CarritoMixin, View):
    """`CO-084`. Con el guion del carrito, la cantidad se aplica al cambiarla."""

    def post(self, request, pk):
        linea = self.linea(request, pk)
        try:
            resultado = servicio.modificar_cantidad(linea, _cantidad(request))
        except servicio.OperacionRechazada as rechazo:
            return _responder(request, "error", str(rechazo))
        if resultado.tope is not None:
            return _responder(
                request,
                "atencion",
                f"Hay {resultado.tope} disponibles de «{linea.producto.titulo}»: "
                f"la línea quedó con {resultado.tope}.",
            )
        subtotal = pesos(resultado.linea.precio_vigente * resultado.linea.cantidad)
        return _responder(
            request,
            "exito",
            f"«{linea.producto.titulo}»: {resultado.linea.cantidad} unidad(es), {subtotal}.",
        )


class QuitarView(CarritoMixin, View):
    """`CO-085`. Sin confirmación: se deshace volviendo a agregar."""

    def post(self, request, pk):
        linea = self.linea(request, pk)
        titulo = linea.producto.titulo
        servicio.quitar(linea)
        return _responder(request, "exito", f"Se quitó «{titulo}» del carrito.")
