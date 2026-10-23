"""CU-REP-GEN — Generar Reporte Operativo (plan 15).

`ReportesView` es `CO-204`: los parámetros y, si son válidos, el reporte. Va por
GET porque no modifica nada y así el reporte se puede volver a abrir o
compartir con su dirección. `ExportarView` es `CO-128`: el mismo reporte, con
los mismos parámetros, en CSV, y su entrada en el log.
"""

import csv
import io

from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.utils import timezone
from django.views import View

from apps.accounts.models import Usuario
from apps.core.mixins import RolRequeridoMixin
from apps.core.models import RegistroAuditoria
from apps.core.utils import obtener_ip
from apps.reportes import servicios
from apps.reportes.forms import ReporteForm


class ReportesMixin(RolRequeridoMixin):
    roles_permitidos = (Usuario.ADMINISTRADOR,)


def _formulario(request):
    if "tipo" not in request.GET:
        hoy = timezone.localdate()
        return ReporteForm(
            initial={"tipo": servicios.VENTAS_TOTALES, "desde": hoy.replace(day=1), "hasta": hoy}
        )
    return ReporteForm(request.GET)


def _reporte(formulario):
    datos = formulario.cleaned_data
    return servicios.generar(
        datos["tipo"], datos["desde"], datos["hasta"], **formulario.parametros()
    )


class ReportesView(ReportesMixin, View):
    def get(self, request):
        formulario = _formulario(request)
        reporte = _reporte(formulario) if formulario.is_bound and formulario.is_valid() else None
        return render(
            request,
            "reportes/reportes.html",
            {"form": formulario, "reporte": reporte, "consulta": request.GET.urlencode()},
        )


class ExportarView(ReportesMixin, View):
    def get(self, request):
        formulario = ReporteForm(request.GET)
        if not formulario.is_valid():
            # Sin un reporte válido en pantalla no hay qué exportar (precondición de CO-128).
            return redirect("reportes:generar")
        datos = formulario.cleaned_data
        reporte = _reporte(formulario)
        RegistroAuditoria.registrar(
            accion=RegistroAuditoria.EXPORTACION_REPORTE,
            actor=request.user,
            ip=obtener_ip(request),
            detalle=(
                f"{reporte.titulo} · del {datos['desde']:%d/%m/%Y} al {datos['hasta']:%d/%m/%Y} · "
                f"{servicios.describir_filtros(**formulario.parametros())} · "
                f"{len(reporte.filas)} filas"
            ),
        )

        salida = io.StringIO()
        # La marca de orden de bytes: sin ella la planilla lee mal los acentos.
        salida.write("\ufeff")
        escritor = csv.writer(salida)
        escritor.writerow(reporte.columnas)
        for fila in reporte.filas:
            escritor.writerow(fila)
        if reporte.totales:
            escritor.writerow(reporte.totales)

        respuesta = HttpResponse(salida.getvalue(), content_type="text/csv; charset=utf-8")
        nombre = f"{reporte.tipo}_{datos['desde']:%Y%m%d}_{datos['hasta']:%Y%m%d}.csv"
        respuesta["Content-Disposition"] = f'attachment; filename="{nombre}"'
        return respuesta
