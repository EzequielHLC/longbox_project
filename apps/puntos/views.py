"""«Mis puntos» (`CU-PTS-CON`): `CO-188` y `CO-189`. Sólo lee.

La consulta es siempre de quien pide: no recibe un identificador de cliente,
así que no hay forma de pedir los puntos de otro.
"""

from datetime import datetime, timedelta

from django.core.paginator import Paginator
from django.shortcuts import render
from django.utils import timezone
from django.views import View

from apps.accounts.views_cuenta import ClienteMixin
from apps.core.models import ConfiguracionSistema
from apps.puntos import servicios
from apps.puntos.models import LotePuntos, MovimientoPuntos

DIAS_PROXIMO_A_VENCER = 30  # CU-PTS-CON paso 2 (b)


def _fecha(texto):
    try:
        return datetime.strptime(texto, "%Y-%m-%d").date()
    except (TypeError, ValueError):
        return None


class PuntosView(ClienteMixin, View):
    def get(self, request):
        usuario = request.user
        saldo = servicios.saldo(usuario)
        configuracion = ConfiguracionSistema.obtener()
        equivalencia = configuracion.equivalencia_puntos
        hoy = timezone.localdate()

        # (b) Los lotes con algo disponible, el que vence antes primero.
        lotes = list(
            LotePuntos.objects.filter(usuario=usuario, estado=LotePuntos.ACTIVO).order_by(
                "caduca_el", "pk"
            )
        )
        for lote in lotes:
            lote.proximo_a_vencer = lote.caduca_el <= hoy + timedelta(days=DIAS_PROXIMO_A_VENCER)

        # (c) El historial, con el filtro de CO-189: tipo y rango de fechas.
        tipo = request.GET.get("tipo", "")
        tipo = tipo if tipo in dict(MovimientoPuntos.TIPO_CHOICES) else ""
        desde, hasta = _fecha(request.GET.get("desde")), _fecha(request.GET.get("hasta"))
        movimientos = MovimientoPuntos.objects.filter(usuario=usuario).select_related("pedido")
        if tipo:
            movimientos = movimientos.filter(tipo=tipo)
        if desde:
            movimientos = movimientos.filter(ocurrido_en__date__gte=desde)
        if hasta:
            movimientos = movimientos.filter(ocurrido_en__date__lte=hasta)
        pagina = Paginator(movimientos.order_by("-ocurrido_en", "-pk"), 50).get_page(
            request.GET.get("page")
        )
        consulta = request.GET.copy()
        consulta.pop("page", None)

        return render(
            request,
            "cuenta/puntos.html",
            {
                "seccion": "puntos",
                "saldo": saldo,
                "saldo_en_pesos": saldo * equivalencia,
                "equivalencia": equivalencia,
                "porcentaje": configuracion.porcentaje_puntos,
                "lotes": lotes,
                "pagina": pagina,
                "movimientos": pagina.object_list,
                "filtros": {"tipo": tipo, "desde": desde, "hasta": hasta},
                "hay_filtro": bool(tipo or desde or hasta),
                "tipos": MovimientoPuntos.TIPO_CHOICES,
                "consulta": consulta,
                "dias_proximo": DIAS_PROXIMO_A_VENCER,
            },
        )
