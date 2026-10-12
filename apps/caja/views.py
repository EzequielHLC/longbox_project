"""La caja (`CU-CAJ-CIE`). Cajero y Administrador; el Cliente recibe 403."""

from django.contrib import messages
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View
from django.views.generic import ListView

from apps.accounts.models import Usuario
from apps.caja import servicios
from apps.caja.models import CierreDeCaja
from apps.core.mixins import RolRequeridoMixin


class CajaMixin(RolRequeridoMixin):
    roles_permitidos = (Usuario.CAJERO, Usuario.ADMINISTRADOR)


class CajaView(CajaMixin, View):
    """`CO-203`: el resumen previo, o el cierre de hoy (E1), o sin movimientos (E2)."""

    def get(self, request):
        return render(
            request,
            "caja/caja.html",
            {
                "resumen": servicios.resumen_previo(),
                "ultimos": CierreDeCaja.objects.select_related("realizado_por")[:10],
            },
        )


class CerrarView(CajaMixin, View):
    """`CO-126`."""

    def post(self, request):
        try:
            cierre = servicios.confirmar(request.user)
        except servicios.CierreRechazado as rechazo:
            messages.error(request, str(rechazo))
            return redirect("caja:caja")
        messages.success(request, "Caja cerrada.")
        return redirect("caja:cierre", pk=cierre.pk)


class CierreView(CajaMixin, View):
    """El resumen definitivo de un cierre."""

    def get(self, request, pk):
        cierre = get_object_or_404(CierreDeCaja.objects.select_related("realizado_por"), pk=pk)
        return render(
            request,
            "caja/cierre.html",
            {
                "cierre": cierre,
                "transacciones": cierre.transacciones.select_related("pedido").order_by(
                    "registrada_en", "pk"
                ),
            },
        )


class CierreListaView(CajaMixin, ListView):
    template_name = "caja/cierre_lista.html"
    context_object_name = "cierres"
    paginate_by = 30
    queryset = CierreDeCaja.objects.select_related("realizado_por")


class ExportarView(CajaMixin, View):
    """`CO-127`."""

    def get(self, request, pk):
        cierre = get_object_or_404(CierreDeCaja, pk=pk)
        respuesta = HttpResponse(content_type="text/csv; charset=utf-8")
        respuesta["Content-Disposition"] = (
            f'attachment; filename="cierre-{cierre.fecha_jornada:%Y-%m-%d}.csv"'
        )
        respuesta.write("﻿")  # BOM: que la planilla lea bien los acentos
        servicios.exportar(cierre, respuesta, request.user)
        return respuesta
