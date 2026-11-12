"""La caja (`CU-CAJ-CIE`). Cajero y Administrador; el Cliente recibe 403."""

from django.contrib import messages
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View
from django.views.generic import ListView

from apps.accounts.models import Usuario
from apps.caja import servicios
from apps.caja.models import CierreDeCaja
from apps.core.mixins import RolRequeridoMixin, plantilla_del_rol
from apps.pedidos.models import TransaccionPago


class CajaMixin(RolRequeridoMixin):
    roles_permitidos = (Usuario.CAJERO, Usuario.ADMINISTRADOR)


class CajaView(CajaMixin, View):
    """`CO-203`: el resumen previo, o el cierre de hoy (E1), o sin movimientos (E2)."""

    def get(self, request):
        resumen = servicios.resumen_previo()
        medio = request.GET.get("medio", "")
        # Plan 00 de interfaz, segunda parte, 12: las ventas de la jornada, la más
        # reciente primero, con el filtro por medio. Sólo lee.
        ventas = sorted(
            resumen.incluidas + resumen.pendientes, key=lambda t: t.registrada_en, reverse=True
        )
        if medio in dict(TransaccionPago.MEDIO_CHOICES):
            ventas = [t for t in ventas if t.medio == medio]
        return render(
            request,
            plantilla_del_rol(request, "caja/caja.html", "caja/cajero/caja.html"),
            {
                "resumen": resumen,
                "medidores": _medidores(resumen.por_medio),
                "ventas": ventas,
                "medio": medio,
                "medios": TransaccionPago.MEDIO_CHOICES,
                "ultimos": CierreDeCaja.objects.select_related("realizado_por")[:10],
            },
        )


SEGMENTOS = 12


def _medidores(por_medio):
    """Lo recaudado por medio, con los segmentos encendidos de su medidor.

    El medio que más recaudó llena los doce; los dos últimos segmentos son el
    pico, en naranja. Es la misma proporción que la barra de la versión sobria.
    """
    maximo = max((total for _, total in por_medio), default=0)
    filas = []
    for etiqueta, total in por_medio:
        encendidos = round(total / maximo * SEGMENTOS) if maximo else 0
        segmentos = [
            ("pico" if i >= SEGMENTOS - 2 else True) if i < encendidos else False
            for i in range(SEGMENTOS)
        ]
        filas.append((etiqueta, total, segmentos))
    return filas


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
                "transacciones": cierre.transacciones.select_related(
                    "pedido", "pedido__usuario", "solicitud", "solicitud__usuario"
                ).order_by("-registrada_en", "-pk"),
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
