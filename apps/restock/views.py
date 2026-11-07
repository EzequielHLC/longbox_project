"""Restock (plan 05).

El aviso de reposición es del Cliente, desde la ficha pública (`CO-075`,
`CO-076`). La propuesta es del Administrador (`CO-067` a `CO-073`, `CO-174`,
`CO-175`). La restricción vive en el servidor: el rol equivocado recibe 403.
"""

from django.contrib import messages
from django.contrib.auth.views import redirect_to_login
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django.views import View

from apps.accounts.models import Usuario
from apps.catalog import busqueda
from apps.catalog.models import Producto
from apps.core.mixins import RolRequeridoMixin
from apps.restock import servicios
from apps.restock.models import LineaPropuestaRestock, PropuestaRestock
from apps.suppliers.views_pedidos import fecha_o_nada

# ---------------------------------------------------------------------------
# CU-RST-SUS — CO-075, CO-076, desde la ficha pública
# ---------------------------------------------------------------------------


class AvisoView(View):
    """POST: pedir el aviso o cancelarlo. Invitado al ingreso, personal 403 (B-05-002)."""

    def post(self, request, pk):
        ficha = reverse("core:tienda_producto", args=[pk])
        if not request.user.is_authenticated:
            return redirect_to_login(ficha)
        if request.user.rol != Usuario.CLIENTE:
            raise PermissionDenied("El aviso de reposición es de los clientes.")
        producto = get_object_or_404(Producto, pk=pk)
        if request.POST.get("accion") == "cancelar":
            servicios.cancelar_suscripcion(request.user, producto)
            messages.success(request, "Cancelaste el aviso.")
            return redirect(ficha)
        try:
            servicios.suscribir(request.user, producto)
        except servicios.YaHayStock:
            messages.info(request, "Este producto ya tiene unidades disponibles.")  # E2
            return redirect(ficha)
        messages.success(request, "Te avisaremos cuando este producto vuelva a estar disponible.")
        return redirect(ficha)


# ---------------------------------------------------------------------------
# CU-RST-PRO A1 y CU-RST-APR — la propuesta en el panel
# ---------------------------------------------------------------------------


class RestockMixin(RolRequeridoMixin):
    roles_permitidos = (Usuario.ADMINISTRADOR,)


def _volver(request, ancla=""):
    """Adonde vuelve un formulario de la propuesta: a la ficha si vino de ahí, o a
    «Restock» (B-05-011). Sólo a una dirección de este sitio."""
    destino = request.POST.get("volver", "")
    if not url_has_allowed_host_and_scheme(
        destino, allowed_hosts={request.get_host()}, require_https=request.is_secure()
    ):
        destino = reverse("restock:propuesta")
    return redirect(destino + ancla)


def _contexto_de(propuesta, grupos):
    """Lo que muestran «Restock» y la ficha de una propuesta pendiente."""
    return {
        "propuesta": propuesta,
        "grupos": grupos,
        "opciones_para_agregar": (
            busqueda.opciones_para_pedir() if propuesta and propuesta.estado == "pendiente" else []
        ),
        # Plan 00 de interfaz, segunda parte, 14.1.
        "resumen": {
            "productos": sum(len(g.lineas) for g in grupos),
            "unidades": sum(g.unidades for g in grupos),
            "pendientes": sum(1 for g in grupos if g.pendiente),
            "suscriptores": sum(g.suscriptores for g in grupos),
            "descartados": sum(1 for g in grupos if g.estado == "descartado"),
        },
    }


def _pendiente_o_volver(request):
    propuesta = servicios.pendiente()
    if propuesta is None:
        messages.error(request, "No hay una propuesta pendiente.")
    return propuesta


class PropuestaView(RestockMixin, View):
    """`CO-174`: la propuesta pendiente por proveedor. E1: no hay ninguna."""

    def get(self, request):
        propuesta = servicios.pendiente()
        grupos = servicios.agrupar(propuesta) if propuesta else []
        return render(
            request,
            "restock/propuesta.html",
            {
                **_contexto_de(propuesta, grupos),
                "volver": request.path,
                "ultima": PropuestaRestock.objects.filter(estado=PropuestaRestock.CERRADA).first(),
            },
        )


class PropuestaListaView(RestockMixin, View):
    """Todas las propuestas, abiertas y cerradas (plan 00 del circuito, B-05-009).

    Sólo lee. La pendiente sigue trabajándose en «Restock»; desde acá se ve qué
    se pidió antes, a quién, qué se descartó y qué llegó.
    """

    def get(self, request):
        propuestas = PropuestaRestock.objects.prefetch_related("lineas", "pedidos").order_by(
            "-fecha_generacion", "-pk"
        )
        pagina = Paginator(propuestas, 30).get_page(request.GET.get("pagina"))
        return render(request, "restock/propuesta_lista.html", {"pagina": pagina})


class PropuestaDetalleView(RestockMixin, View):
    """La ficha de una propuesta: sus líneas por proveedor y los pedidos que salieron.

    Si está pendiente, se trabaja desde acá también (B-05-011): las mismas
    operaciones de `CU-RST-APR` que en «Restock», y cada formulario vuelve a la ficha.
    """

    def get(self, request, pk):
        propuesta = get_object_or_404(PropuestaRestock, pk=pk)
        grupos = servicios.agrupar(propuesta)
        return render(
            request,
            "restock/propuesta_detalle.html",
            {
                **_contexto_de(propuesta, grupos),
                "volver": request.path,
                "pedidos": propuesta.pedidos.select_related("proveedor").prefetch_related(
                    "lineas__producto__productoeditorial",
                    "lineas__producto__productonoeditorial",
                ),
            },
        )


class AManoView(RestockMixin, View):
    """B-05-012: una propuesta vacía, para cargarla producto por producto."""

    def post(self, request):
        try:
            servicios.armar_a_mano(request.user)
        except servicios.OperacionRechazada as rechazo:
            messages.error(request, str(rechazo))
        else:
            messages.success(
                request, "Propuesta armada: agregue los productos con su código o su título."
            )
        return redirect("restock:propuesta")


class CerrarVaciaView(RestockMixin, View):
    """B-05-012: cerrar la propuesta pendiente que quedó sin productos."""

    def post(self, request):
        propuesta = _pendiente_o_volver(request)
        if propuesta is None:
            return redirect("restock:propuesta")
        try:
            servicios.cerrar_vacia(propuesta, request.user)
        except servicios.OperacionRechazada as rechazo:
            messages.error(request, str(rechazo))
        else:
            messages.success(request, "Se cerró la propuesta vacía.")
        return redirect("restock:propuesta")


class GenerarView(RestockMixin, View):
    """`CO-068`: el disparo manual. Omite el ciclo automático de la semana."""

    def post(self, request):
        resultado = servicios.generar_manual(request.user)
        if resultado.motivo == "pendiente":
            messages.error(
                request, "Ya hay una propuesta pendiente: resuélvala antes de generar otra."
            )
        elif resultado.propuesta and resultado.propuesta.estado == PropuestaRestock.CERRADA:
            messages.info(request, "No hay productos para reponer.")
        else:
            messages.success(request, "Propuesta generada.")
        return redirect("restock:propuesta")


def _entero(texto):
    try:
        return int(texto)
    except (TypeError, ValueError):
        return None


class LineaView(RestockMixin, View):
    """`CO-069` (cantidad) y `CO-070` (quitar)."""

    def post(self, request, pk):
        get_object_or_404(LineaPropuestaRestock, pk=pk)
        try:
            if request.POST.get("accion") == "quitar":
                linea = servicios.eliminar_linea(pk)
                messages.success(request, f"Se quitó «{linea.producto}».")
            else:
                linea = servicios.ajustar_cantidad(pk, _entero(request.POST.get("cantidad")))
                messages.success(
                    request, f"«{linea.producto}»: {linea.cantidad_sugerida} unidad(es)."
                )
        except servicios.OperacionRechazada as rechazo:
            messages.error(request, str(rechazo))
        return _volver(request)


class CantidadesView(RestockMixin, View):
    """`CO-069` de todas las líneas de un proveedor con un solo «Guardar» (14.3)."""

    def post(self, request, clave):
        propuesta = _pendiente_o_volver(request)
        if propuesta is None:
            return redirect("restock:propuesta")
        cantidades = {
            int(nombre.removeprefix("cantidad-")): _entero(valor)
            for nombre, valor in request.POST.items()
            if nombre.startswith("cantidad-") and nombre.removeprefix("cantidad-").isdigit()
        }
        try:
            cambiadas = servicios.ajustar_cantidades(propuesta, clave, cantidades)
        except servicios.OperacionRechazada as rechazo:
            messages.error(request, str(rechazo))
        else:
            if cambiadas:
                messages.success(request, f"Se guardaron {cambiadas} cantidad(es).")
            else:
                messages.info(request, "No cambió ninguna cantidad.")
        return _volver(request, f"#grupo-{clave}")


class AgregarView(RestockMixin, View):
    """`CO-071`: por código, ISBN, código de barras o título con su número (B-05-016)."""

    def post(self, request):
        propuesta = _pendiente_o_volver(request)
        if propuesta is None:
            return redirect("restock:propuesta")
        producto, problema = busqueda.buscar_para_pedir(request.POST.get("producto", ""))
        if producto is None:
            messages.error(request, problema)
            return _volver(request)
        try:
            servicios.agregar_producto(propuesta, producto, _entero(request.POST.get("cantidad")))
        except servicios.OperacionRechazada as rechazo:
            messages.error(request, str(rechazo))
            return _volver(request)
        messages.success(request, f"Se agregó «{producto}».")
        return _volver(request)


class ProveedorView(RestockMixin, View):
    """`CO-175` y la confirmación de `CO-072` o `CO-073`. Volver no registra nada."""

    def _grupo(self, request, clave):
        propuesta = _pendiente_o_volver(request)
        if propuesta is None:
            return None, None
        try:
            return propuesta, servicios.grupo_de(propuesta, clave)
        except servicios.OperacionRechazada as rechazo:
            messages.error(request, str(rechazo))
            return None, None

    def get(self, request, clave):
        propuesta, grupo = self._grupo(request, clave)
        if grupo is None:
            return redirect("restock:propuesta")
        return render(request, "restock/proveedor.html", {"propuesta": propuesta, "grupo": grupo})

    def post(self, request, clave):
        propuesta, grupo = self._grupo(request, clave)
        if grupo is None:
            return redirect("restock:propuesta")
        try:
            if request.POST.get("accion") == "descartar":
                servicios.descartar(propuesta, clave, request.POST.get("motivo"), request.user)
                messages.success(request, f"Se descartó el pedido a {grupo.nombre}.")
                return redirect("restock:propuesta")
            envio = servicios.despachar(
                propuesta,
                clave,
                request.user,
                fecha_estimada=fecha_o_nada(request.POST.get("fecha_estimada")),
            )
        except servicios.OperacionRechazada as rechazo:
            messages.error(request, str(rechazo))
            return redirect("restock:proveedor", clave=clave)
        if envio.enviado:
            messages.success(request, f"Pedido enviado a {grupo.nombre}.")
        else:
            messages.error(
                request,
                f"No salió el pedido a {grupo.nombre}: sigue pendiente para reintentar.",
            )
        return redirect("restock:propuesta")
