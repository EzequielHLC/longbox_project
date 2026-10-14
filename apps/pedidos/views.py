"""Los pedidos en el panel de gestión (plan 08): `CU-PED-CON` y `CU-PED-EST`.

Sólo el Administrador (plan 08, amb. 5). El Cajero y el Cliente reciben 403 en
cualquiera de estas direcciones: la restricción vive en el servidor.
"""

from datetime import datetime

from django.contrib import messages
from django.db.models import (
    Case,
    DecimalField,
    Exists,
    F,
    OuterRef,
    Q,
    Sum,
    Value,
    When,
)
from django.db.models.functions import Coalesce
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View
from django.views.generic import ListView

from apps.accounts.models import Usuario
from apps.core.mixins import RolRequeridoMixin
from apps.pedidos import servicios
from apps.pedidos.models import LineaPedido, Pedido

CERO = Value(0, output_field=DecimalField(max_digits=12, decimal_places=2))


def con_totales(pedidos):
    """El total cobrado de cada pedido, en la misma consulta (B-08-003).

    Lo pagado en dinero (las líneas no cubiertas con puntos) más el envío, y si
    tiene artículos demorados. Sin esto el listado haría una consulta por fila.
    """
    importe = Case(
        When(
            lineas__cubierta_con_puntos=False,
            then=F("lineas__precio_unitario") * F("lineas__cantidad"),
        ),
        default=CERO,
        output_field=DecimalField(max_digits=12, decimal_places=2),
    )
    # También el artículo que llegó para el despacho diferido (B-08-007).
    demorados = LineaPedido.objects.filter(pedido=OuterRef("pk")).filter(
        Q(estado=LineaPedido.ESPERANDO_DEMORADO)
        | Q(estado=LineaPedido.DISPONIBLE, decision_demora=LineaPedido.DESPACHO_DIFERIDO)
    )
    return pedidos.annotate(
        cobrado_productos=Coalesce(Sum(importe), CERO),
        tiene_demorados=Exists(demorados),
    ).annotate(cobrado=F("cobrado_productos") + F("costo_envio"))


def _fecha(texto):
    try:
        return datetime.strptime(texto, "%Y-%m-%d").date()
    except (TypeError, ValueError):
        return None


class PedidosMixin(RolRequeridoMixin):
    roles_permitidos = (Usuario.ADMINISTRADOR,)


class PedidoListaView(PedidosMixin, ListView):
    """`CO-182`: todos los pedidos, los más recientes primero, de a 50."""

    context_object_name = "pedidos"
    paginate_by = 50

    def get_template_names(self):
        if self.request.GET.get("parcial"):
            return ["pedidos/_tabla_pedidos.html"]
        return ["pedidos/pedido_lista.html"]

    def filtros(self):
        datos = self.request.GET
        estado = datos.get("estado", "")
        canal = datos.get("canal", "")
        return {
            "q": datos.get("q", "").strip(),
            "estado": estado if estado in dict(Pedido.ESTADO_CHOICES) else "",
            "canal": canal if canal in dict(Pedido.CANAL_CHOICES) else "",
            "desde": _fecha(datos.get("desde")),
            "hasta": _fecha(datos.get("hasta")),
            "demorados": datos.get("demorados") == "1",
        }

    def get_queryset(self):
        filtros = self.filtros()
        pedidos = Pedido.objects.select_related("usuario")
        if filtros["q"]:
            q = filtros["q"]
            pedidos = pedidos.filter(
                Q(numero__icontains=q)
                | Q(usuario__email__icontains=q)
                | Q(usuario__first_name__icontains=q)
                | Q(usuario__last_name__icontains=q)
                | Q(correo_invitado__icontains=q)
            )
        if filtros["estado"]:
            pedidos = pedidos.filter(estado=filtros["estado"])
        if filtros["canal"]:
            pedidos = pedidos.filter(canal=filtros["canal"])
        if filtros["desde"]:
            pedidos = pedidos.filter(fecha__date__gte=filtros["desde"])
        if filtros["hasta"]:
            pedidos = pedidos.filter(fecha__date__lte=filtros["hasta"])
        pedidos = con_totales(pedidos)
        if filtros["demorados"]:
            pedidos = pedidos.filter(tiene_demorados=True)
        return pedidos.order_by("-fecha", "-pk")

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        filtros = self.filtros()
        contexto["filtros"] = filtros
        contexto["hay_filtro"] = any(filtros.values())
        contexto["estados"] = Pedido.ESTADO_CHOICES
        contexto["canales"] = Pedido.CANAL_CHOICES
        contexto["consulta"] = self.request.GET.copy()
        contexto["consulta"].pop("page", None)
        contexto["consulta"].pop("parcial", None)
        return contexto


def _detalle(pedido):
    lineas = list(pedido.lineas.select_related("producto"))
    return {
        "pedido": pedido,
        "lineas": lineas,
        "transiciones": list(pedido.transiciones.select_related("actor")),
        "transaccion": getattr(pedido, "transaccion", None),
        "puntos_canjeados": sum(linea.puntos_canjeados for linea in lineas),
        "cobrado": sum((linea.subtotal for linea in lineas), pedido.costo_envio),
        "siguiente": servicios.siguiente_estado(pedido),
        "automatico": pedido.estado in servicios.AUTOMATICOS,
        "siguiente_display": dict(Pedido.ESTADO_CHOICES).get(servicios.siguiente_estado(pedido)),
    }


class PedidoDetalleView(PedidosMixin, View):
    """`CO-183`: el pedido entero, con su línea de tiempo y la acción que admite."""

    def get(self, request, pk):
        pedido = get_object_or_404(Pedido.objects.select_related("usuario"), pk=pk)
        return render(request, "pedidos/pedido_detalle.html", _detalle(pedido))


class AvanzarView(PedidosMixin, View):
    """`CO-092` y `CO-093`. GET pide confirmar; POST avanza.

    La confirmación muestra la advertencia de E2 si hay artículos demorados con
    la decisión pendiente; confirmarla es `CO-093`.
    """

    template_name = "pedidos/pedido_avanzar.html"

    def _contexto(self, pedido, pendientes=None):
        contexto = _detalle(pedido)
        if pendientes is None and contexto["siguiente"] == Pedido.EMPAQUETADO:
            pendientes = servicios.pendientes_de_decision(pedido)
        contexto["pendientes"] = pendientes or []
        return contexto

    def get(self, request, pk):
        pedido = get_object_or_404(Pedido, pk=pk)
        if pedido.estado in servicios.AUTOMATICOS or not servicios.siguiente_estado(pedido):
            return redirect("pedidos:detalle", pk=pk)
        return render(request, self.template_name, self._contexto(pedido))

    def post(self, request, pk):
        pedido = get_object_or_404(Pedido, pk=pk)
        try:
            avance = servicios.avanzar(
                pedido,
                request.user,
                estado_visto=request.POST.get("estado_visto", ""),
                confirmado=request.POST.get("confirmado") == "1",
            )
        except servicios.DecisionPendiente as advertencia:
            return render(request, self.template_name, self._contexto(pedido, advertencia.lineas))
        except servicios.AvanceRechazado as rechazo:
            messages.error(request, str(rechazo))
            return redirect("pedidos:detalle", pk=pk)
        messages.success(
            request,
            f"El pedido {avance.pedido.numero} pasó a «{avance.pedido.get_estado_display()}». "
            "Se avisó al cliente por correo.",
        )
        return redirect("pedidos:detalle", pk=pk)
