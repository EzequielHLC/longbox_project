"""El ciclo de la pre-venta en el panel de gestión (plan 01).

«Pre-ventas por llegar» (`CO-013`, B-01-006), la demora desde la ficha del
producto (`CO-014`, `CO-015`) y la cancelación por la editorial (`CO-026`,
`CO-027`). Sólo el Administrador.
"""

import logging

from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View

from apps.catalog.models import Producto, ProductoEditorial
from apps.pedidos import calendario, preventa
from apps.pedidos.forms import DemoraForm, leer_unidades
from apps.pedidos.views import PedidosMixin

logger = logging.getLogger(__name__)


def _origen(request):
    return request.build_absolute_uri("/").rstrip("/")


def _plural(cantidad, singular, plural):
    return f"{cantidad} {singular if cantidad == 1 else plural}"


class PreVentasView(PedidosMixin, View):
    """Las pre-ventas agrupadas por fecha de llegada y editorial."""

    def get(self, request):
        grupos = preventa.por_llegar()
        # Plan 00 de interfaz, 22: el calendario del mes y las cifras, de los mismos grupos.
        mes = calendario.mes_de(calendario.mes_pedido(request.GET.get("mes")), grupos)
        return render(
            request,
            "pedidos/preventas.html",
            {
                "grupos": grupos,
                "mes": mes,
                "dias_de_la_semana": calendario.DIAS_DE_LA_SEMANA,
                "resumen": calendario.resumen(grupos),
            },
        )


class IngresoView(PedidosMixin, View):
    """`CO-013`. El primer envío muestra qué va a pasar; el segundo lo confirma."""

    def post(self, request):
        ids = [int(pk) for pk in request.POST.getlist("producto") if pk.isdigit()]
        productos = list(
            ProductoEditorial.objects.filter(pk__in=ids, estado=Producto.PRE_VENTA)
            .select_related("editorial")
            .order_by("titulo", "volumen")
        )
        if not productos:
            messages.error(request, "Ninguno de esos productos sigue en pre-venta.")
            return redirect("pedidos:preventas")
        unidades, errores = leer_unidades(request.POST, productos)
        if errores:
            messages.error(request, "Revise las unidades: " + "; ".join(errores.values()))
            return redirect("pedidos:preventas")

        if "confirmar" not in request.POST:
            filas = [preventa.previsualizar_ingreso(p, unidades[p.pk]) for p in productos]
            return render(request, "pedidos/ingreso_confirmar.html", {"filas": filas})

        resumen = preventa.confirmar_ingreso(unidades, request.user, origen=_origen(request))
        partes = []
        if resumen.activados:
            partes.append(
                _plural(len(resumen.activados), "producto activado", "productos activados")
            )
        if resumen.parciales:
            partes.append(_plural(len(resumen.parciales), "ingreso parcial", "ingresos parciales"))
        if resumen.demorados:
            partes.append(
                _plural(len(resumen.demorados), "producto demorado", "productos demorados")
            )
        if resumen.pedidos:
            partes.append(
                _plural(len(resumen.pedidos), "pedido actualizado", "pedidos actualizados")
            )
        if partes:
            messages.success(request, "Ingreso confirmado: " + ", ".join(partes) + ".")
        elif not resumen.errores:
            messages.info(request, "No hubo cambios.")
        if resumen.errores:
            messages.error(
                request,
                "No se pudo confirmar " + ", ".join(resumen.errores) + ". Siguen en pre-venta.",
            )
        return redirect("pedidos:preventas")


def _producto(pk):
    return get_object_or_404(ProductoEditorial.objects.select_related("editorial"), pk=pk)


class DemoraView(PedidosMixin, View):
    """`CO-014` (informe de impacto) y `CO-015` (confirmación). Volver es `CO-156`."""

    template_name = "pedidos/demora.html"

    def _rechazar(self, request, producto, fecha=None):
        try:
            preventa.validar_demora(producto, fecha)
        except preventa.OperacionRechazada as rechazo:
            messages.error(request, str(rechazo))
            return redirect("catalog:producto_detalle", pk=producto.pk)
        return None

    def get(self, request, pk):
        producto = _producto(pk)
        return self._rechazar(request, producto) or render(
            request, self.template_name, {"producto": producto, "form": DemoraForm()}
        )

    def post(self, request, pk):
        producto = _producto(pk)
        rechazo = self._rechazar(request, producto)
        if rechazo:
            return rechazo
        formulario = DemoraForm(request.POST)
        if not formulario.is_valid():
            return render(request, self.template_name, {"producto": producto, "form": formulario})
        datos = formulario.cleaned_data
        if "confirmar" not in request.POST:
            return render(
                request,
                self.template_name,
                {
                    "producto": producto,
                    "form": formulario,
                    "informe": preventa.informe_de_demora(producto),
                },
            )
        try:
            resumen = preventa.registrar_demora(
                producto,
                request.user,
                fecha_estimada=datos["fecha_estimada"],
                nota=datos["nota"],
                origen=_origen(request),
            )
        except preventa.OperacionRechazada as rechazo:
            messages.error(request, str(rechazo))
            return redirect("catalog:producto_detalle", pk=pk)
        messages.success(
            request,
            "Demora registrada: "
            + _plural(len(resumen.pedidos), "pedido afectado", "pedidos afectados")
            + ", "
            + _plural(len(resumen.clientes), "cliente notificado", "clientes notificados")
            + ".",
        )
        if resumen.errores:
            messages.error(
                request, "No se pudieron actualizar los pedidos " + ", ".join(resumen.errores) + "."
            )
        return redirect("catalog:producto_detalle", pk=pk)


class CancelarPreVentaView(PedidosMixin, View):
    """`CO-026` (informe) y `CO-027` (confirmación). Volver es `CO-156`."""

    template_name = "pedidos/cancelar_preventa.html"

    def get(self, request, pk):
        producto = _producto(pk)
        if not producto.esta_en_pre_venta:
            messages.error(request, "El producto no está en pre-venta.")
            return redirect("catalog:producto_detalle", pk=pk)
        return render(
            request,
            self.template_name,
            {"producto": producto, "informe": preventa.informe_de_cancelacion(producto)},
        )

    def post(self, request, pk):
        producto = _producto(pk)
        try:
            informe = preventa.cancelar_preventa(producto, request.user)
        except preventa.OperacionRechazada as rechazo:
            messages.error(request, str(rechazo))
            return redirect("catalog:producto_detalle", pk=pk)
        except Exception:  # noqa: BLE001 - E1: la transacción se deshizo entera
            logger.exception("Falló la cancelación en lote de %s.", producto)
            messages.error(
                request,
                "No se pudo cancelar la pre-venta. No quedó ningún cambio: vuelva a intentarlo.",
            )
            return redirect("pedidos:cancelar_preventa", pk=pk)
        messages.success(
            request,
            "Pre-venta cancelada: "
            + _plural(informe.reservas, "reserva procesada", "reservas procesadas")
            + f", {informe.total_puntos} pts emitidos.",
        )
        return redirect("catalog:producto_detalle", pk=pk)
