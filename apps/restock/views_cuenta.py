"""«Avisos de stock» en «Mi cuenta» (plan 00 de interfaz, segunda parte, 15).

El Cliente ve los productos que pidió que le avisen y cancela el que ya no
quiere: es el A1 de `CU-RST-SUS` (`CO-076`) desde otro lugar, el mismo servicio
que usa la ficha. Lo ya avisado se muestra, sin acción, los últimos 90 días.
"""

from datetime import timedelta

from django.contrib import messages
from django.db.models import Count, OuterRef, Q, Subquery
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views import View

from apps.accounts.views_cuenta import ClienteMixin
from apps.catalog.models import Producto
from apps.restock import servicios
from apps.restock.models import SuscripcionReposicion

DIAS_DE_AVISADOS = 90


def _turno():
    """Cuántos esperan el mismo producto desde antes, más uno: el lugar en la fila."""
    return Subquery(
        SuscripcionReposicion.objects.filter(
            producto=OuterRef("producto"),
            estado__in=SuscripcionReposicion.EN_ESPERA,
            creada_en__lte=OuterRef("creada_en"),
        )
        .values("producto")
        .annotate(n=Count("pk"))
        .values("n")[:1]
    )


class AvisosView(ClienteMixin, View):
    def get(self, request):
        propias = SuscripcionReposicion.objects.filter(usuario=request.user).select_related(
            "producto", "producto__productoeditorial"
        )
        desde = timezone.now() - timedelta(days=DIAS_DE_AVISADOS)
        return render(
            request,
            "restock/cuenta_avisos.html",
            {
                "seccion": "avisos",
                "esperando": propias.filter(estado__in=SuscripcionReposicion.EN_ESPERA)
                .annotate(turno=_turno())
                .order_by("creada_en", "pk"),
                "avisados": propias.filter(
                    Q(estado=SuscripcionReposicion.NOTIFICADA), notificada_en__gte=desde
                ).order_by("-notificada_en", "-pk"),
            },
        )

    def post(self, request):
        producto = get_object_or_404(Producto, pk=request.POST.get("producto"))
        if servicios.cancelar_suscripcion(request.user, producto):
            messages.success(request, f"Cancelaste el aviso de «{producto.titulo}».")
        return redirect("cuenta:avisos")
