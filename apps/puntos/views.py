"""«Mis puntos» (`CU-PTS-CON`): `CO-188` y `CO-189`. Sólo lee.

Y el panel del Administrador sobre los puntos de un Cliente (`CU-PTS-ADM`), al final.

La consulta es siempre de quien pide: no recibe un identificador de cliente,
así que no hay forma de pedir los puntos de otro.
"""

from datetime import datetime, timedelta

from django.contrib import messages
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views import View

from apps.accounts.models import Usuario
from apps.accounts.views_cuenta import ClienteMixin
from apps.core.mixins import RolRequeridoMixin
from apps.core.models import ConfiguracionSistema
from apps.puntos import ajuste, servicios
from apps.puntos.caducidad import usable_hasta
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
            # Ambigüedad 3 (plan 10, segunda parte): vence al empezar su día.
            lote.hasta = usable_hasta(lote)

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


# ---------------------------------------------------------------------------
# CU-PTS-ADM — CO-191 consultarPuntosDeCliente · CO-106 registrarAjusteManualDePuntos
# ---------------------------------------------------------------------------


class AjustePuntosView(RolRequeridoMixin, View):
    """Los puntos de un Cliente y su ajuste manual. Sólo el Administrador (RNF-03).

    GET es `CO-191`; POST, `CO-106`. Volver sin confirmar no registra nada (A1).
    """

    roles_permitidos = (Usuario.ADMINISTRADOR,)
    template_name = "puntos/ajuste.html"

    def _cliente(self, pk):
        return get_object_or_404(Usuario, pk=pk, rol=Usuario.CLIENTE)

    def get(self, request, pk, datos=None, error="", maximo=None):
        cliente = self._cliente(pk)
        try:
            panel = ajuste.consultar(cliente)
        except ajuste.AjusteRechazado as rechazo:
            messages.error(request, str(rechazo))
            return redirect("accounts:cliente_ficha", pk=pk)
        return render(
            request,
            self.template_name,
            {
                "panel": panel,
                "cliente": cliente,
                "datos": datos or {"tipo": MovimientoPuntos.ACREDITACION},
                "error": error,
                "maximo": maximo,
                "tipos": MovimientoPuntos.TIPO_CHOICES,
            },
        )

    def post(self, request, pk):
        cliente = self._cliente(pk)
        datos = {
            "tipo": request.POST.get("tipo", ""),
            "cantidad": request.POST.get("cantidad", "").strip(),
            "motivo": request.POST.get("motivo", ""),
        }
        cantidad = int(datos["cantidad"]) if datos["cantidad"].isdigit() else 0
        try:
            hecho = ajuste.ajustar(cliente, request.user, datos["tipo"], cantidad, datos["motivo"])
        except ajuste.AjusteRechazado as rechazo:  # E1, E2: se conserva lo ingresado
            return self.get(request, pk, datos=datos, error=str(rechazo), maximo=rechazo.maximo)
        messages.success(
            request,
            f"Ajuste registrado: {hecho.cantidad} pts. El saldo pasó de {hecho.anterior} a "
            f"{hecho.saldo} pts.",
        )
        return redirect("accounts:cliente_puntos", pk=pk)
