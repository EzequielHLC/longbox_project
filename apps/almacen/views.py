"""El stock almacenado en el panel de gestión (plan 18).

`CU-STK-ADC` (consulta y ficha), `CU-STK-FIS` (despacho y retiro) para el
Administrador y el Cajero; `CU-STK-PLA` sólo para el Administrador. La
restricción vive en el servidor: el rol equivocado recibe 403 por la dirección.
"""

from datetime import datetime

from django import forms
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View

from apps.accounts.models import Usuario
from apps.almacen import servicios
from apps.almacen.models import ArticuloRetenido, SolicitudDespacho
from apps.core.mixins import RolRequeridoMixin


class AlmacenMixin(RolRequeridoMixin):
    roles_permitidos = (Usuario.ADMINISTRADOR, Usuario.CAJERO)


class AdministradorMixin(RolRequeridoMixin):
    roles_permitidos = (Usuario.ADMINISTRADOR,)


def _origen(request):
    return request.build_absolute_uri("/").rstrip("/")


def _fecha(texto):
    try:
        return datetime.strptime(texto, "%Y-%m-%d").date()
    except (TypeError, ValueError):
        return None


class ListaView(AlmacenMixin, View):
    """`CO-217`: todos los artículos, con filtros; A1, la vista vacía."""

    def get(self, request):
        datos = request.GET
        estado = datos.get("estado", "")
        filtros = servicios.Filtros(
            cliente=datos.get("cliente", "").strip(),
            producto=datos.get("producto", "").strip(),
            estado=estado if estado in dict(ArticuloRetenido.ESTADO_CHOICES) else "",
            desde=_fecha(datos.get("desde")),
            hasta=_fecha(datos.get("hasta")),
        )
        dias = servicios.dias_de_aviso()
        articulos = list(servicios.consultar(filtros)[:200])
        for articulo in articulos:
            articulo.proximo = articulo.proximo_a_vencer(dias)
        return render(
            request,
            "almacen/lista.html",
            {
                "articulos": articulos,
                "filtros": filtros,
                "estados": ArticuloRetenido.ESTADO_CHOICES,
                "dias_aviso": dias,
            },
        )


def _articulo(pk):
    return get_object_or_404(
        ArticuloRetenido.objects.select_related(
            "usuario",
            "producto",
            "producto__productoeditorial",
            "solicitud",
            "linea_pedido__pedido",
        ),
        pk=pk,
    )


class FichaView(AlmacenMixin, View):
    """`CO-218`: la ficha, con el historial de plazo y las acciones que admite."""

    def get(self, request, pk):
        articulo = _articulo(pk)
        return render(
            request,
            "almacen/ficha.html",
            {
                "articulo": articulo,
                "historial": servicios.historial_de_plazo(articulo),
                "proximo": articulo.proximo_a_vencer(servicios.dias_de_aviso()),
                "es_administrador": request.user.rol == Usuario.ADMINISTRADOR,
            },
        )


class RetiroView(AlmacenMixin, View):
    """`CO-227`. GET pide verificar al titular; POST registra. Volver no registra (A2)."""

    def get(self, request, pk):
        articulo = _articulo(pk)
        if articulo.estado != ArticuloRetenido.DISPONIBLE:
            messages.error(request, "Sólo se retira un artículo disponible.")
            return redirect("almacen:ficha", pk=pk)
        return render(request, "almacen/retiro.html", {"articulo": articulo})

    def post(self, request, pk):
        try:
            servicios.retirar(pk, request.user)
        except servicios.OperacionRechazada as rechazo:
            messages.error(request, str(rechazo))
            return redirect("almacen:ficha", pk=pk)
        messages.success(request, "Retiro registrado.")
        return redirect("almacen:ficha", pk=pk)


class SolicitudView(AlmacenMixin, View):
    """La solicitud de despacho: sus artículos, la dirección y el pago (B-18-004).

    Confirmar el despacho registra `CO-152` sobre cada artículo pendiente de una
    vez (B-18-007).
    """

    def _solicitud(self, pk):
        return get_object_or_404(SolicitudDespacho.objects.select_related("usuario"), pk=pk)

    def get(self, request, pk):
        solicitud = self._solicitud(pk)
        articulos = list(
            solicitud.articulos.select_related("producto", "producto__productoeditorial")
        )
        return render(
            request,
            "almacen/solicitud.html",
            {
                "solicitud": solicitud,
                "articulos": articulos,
                "pendientes": [
                    a for a in articulos if a.estado == ArticuloRetenido.PENDIENTE_DESPACHO
                ],
                "transaccion": getattr(solicitud, "transaccion", None),
            },
        )

    def post(self, request, pk):
        solicitud = self._solicitud(pk)
        ids = [int(v) for v in request.POST.getlist("articulo") if v.isdigit()]
        if not ids or not solicitud.articulos.filter(pk__in=ids).count() == len(set(ids)):
            messages.error(request, "Elegí los artículos de esta solicitud.")
            return redirect("almacen:solicitud", pk=pk)
        try:
            despachados = servicios.despachar(ids, request.user, origen=_origen(request))
        except servicios.OperacionRechazada as rechazo:
            messages.error(request, str(rechazo))
            return redirect("almacen:solicitud", pk=pk)
        messages.success(
            request, f"Despacho confirmado: {len(despachados)} artículo(s). Se avisó al cliente."
        )
        return redirect("almacen:solicitud", pk=pk)


class RetiroPedidoView(AlmacenMixin, View):
    """«Entregar todo» (plan 07, octava parte, ambigüedad 5): `CO-227` sobre cada
    artículo disponible del pedido, verificando al titular una sola vez."""

    def _pedido(self, pk):
        from apps.pedidos.models import Pedido

        return get_object_or_404(Pedido.objects.select_related("usuario"), pk=pk)

    def get(self, request, pk):
        pedido = self._pedido(pk)
        articulos = list(servicios.disponibles_del_pedido(pk))
        if not articulos:
            messages.error(request, "Este pedido no tiene artículos para entregar.")
            return redirect("almacen:lista")
        return render(
            request,
            "almacen/retiro_pedido.html",
            {"pedido": pedido, "articulos": articulos, "titular": articulos[0].usuario},
        )

    def post(self, request, pk):
        ids = [int(v) for v in request.POST.getlist("articulo") if v.isdigit()]
        try:
            entregados = servicios.retirar_pedido(pk, request.user, ids)
        except servicios.OperacionRechazada as rechazo:
            messages.error(request, str(rechazo))
            return redirect("almacen:lista")
        messages.success(request, f"Retiro registrado: {len(entregados)} artículo(s).")
        return redirect("almacen:lista")


class PlazoForm(forms.Form):
    fecha = forms.DateField(
        label="Nueva fecha de vencimiento",
        widget=forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
    )
    motivo = forms.CharField(
        label="Motivo", max_length=500, widget=forms.Textarea(attrs={"rows": 3})
    )


class PlazoView(AdministradorMixin, View):
    """`CO-153`: sólo el Administrador. Cancelar no registra nada (A1)."""

    template_name = "almacen/plazo.html"

    def _render(self, request, articulo, formulario):
        return render(
            request,
            self.template_name,
            {
                "articulo": articulo,
                "form": formulario,
                "historial": servicios.historial_de_plazo(articulo),
            },
        )

    def get(self, request, pk):
        articulo = _articulo(pk)
        if not articulo.corre_plazo:
            messages.error(request, "Este artículo no tiene un plazo vigente.")
            return redirect("almacen:ficha", pk=pk)
        return self._render(
            request, articulo, PlazoForm(initial={"fecha": articulo.fecha_vencimiento})
        )

    def post(self, request, pk):
        articulo = _articulo(pk)
        formulario = PlazoForm(request.POST)
        if not formulario.is_valid():
            return self._render(request, articulo, formulario)
        try:
            servicios.modificar_plazo(
                pk,
                request.user,
                formulario.cleaned_data["fecha"],
                formulario.cleaned_data["motivo"],
                origen=_origen(request),
            )
        except servicios.OperacionRechazada as rechazo:
            formulario.add_error(None, str(rechazo))
            return self._render(request, articulo, formulario)
        messages.success(request, "Plazo actualizado. Se avisó al cliente.")
        return redirect("almacen:ficha", pk=pk)
