"""Stock en local en «Mi cuenta» (plan 18): `CU-STK-CON` y `CU-STK-DES`.

Todo es del Cliente: el personal recibe 403 y un artículo de otro no aparece ni
se puede pedir. La selección y la dirección del envío viven en la sesión hasta
confirmar: cancelar (A2) es simplemente volver, y no queda nada registrado.
"""

from django.contrib import messages
from django.shortcuts import redirect, render
from django.views import View

from apps.accounts.models import Usuario
from apps.almacen import servicios
from apps.almacen.models import ArticuloRetenido
from apps.core.mixins import RolRequeridoMixin
from apps.tienda.forms import DireccionDeEnvioForm

CLAVE_SELECCION = "despacho_articulos"
CLAVE_ENVIO = "despacho_envio"


class ClienteMixin(RolRequeridoMixin):
    roles_permitidos = (Usuario.CLIENTE,)


class StockView(ClienteMixin, View):
    """`CO-215`: lo guardado a su nombre, con el destacado de lo próximo a vencer."""

    def get(self, request):
        dias = servicios.dias_de_aviso()
        articulos = list(servicios.del_cliente(request.user))
        for articulo in articulos:
            articulo.proximo = articulo.proximo_a_vencer(dias)
        return render(
            request,
            "almacen/cuenta_stock.html",
            {
                "seccion": "stock",
                "articulos": articulos,
                "hay_disponibles": any(a.estado == ArticuloRetenido.DISPONIBLE for a in articulos),
            },
        )


class DespachoView(ClienteMixin, View):
    """`CO-216` (resumen), `CO-087` (la dirección) y `CO-151` (confirmar)."""

    template_name = "almacen/cuenta_despacho.html"

    def _envio(self, request):
        return request.session.get(CLAVE_ENVIO) or servicios.direccion_predeterminada(request.user)

    def _render(self, request, formulario=None):
        ids = request.session.get(CLAVE_SELECCION, [])
        try:
            resumen = servicios.resumen_de_despacho(request.user, ids, self._envio(request))
        except servicios.OperacionRechazada as rechazo:
            request.session.pop(CLAVE_SELECCION, None)
            messages.error(request, str(rechazo))
            return redirect("cuenta:stock")
        return render(
            request,
            self.template_name,
            {
                "seccion": "stock",
                "resumen": resumen,
                "form": formulario or DireccionDeEnvioForm(initial=resumen.envio),
                # E1: sin dirección completa, se pide antes de confirmar.
                "editar_direccion": formulario is not None or not resumen.direccion_completa,
            },
        )

    def get(self, request):
        return self._render(request)

    def post(self, request):
        accion = request.POST.get("accion", "")
        if accion == "seleccionar":
            request.session[CLAVE_SELECCION] = [
                int(v) for v in request.POST.getlist("articulo") if v.isdigit()
            ]
            request.session.pop(CLAVE_ENVIO, None)
            return redirect("cuenta:despacho")
        if accion == "direccion":
            formulario = DireccionDeEnvioForm(request.POST)
            if not formulario.is_valid():
                return self._render(request, formulario)
            request.session[CLAVE_ENVIO] = {
                campo: formulario.cleaned_data.get(campo, "") for campo in servicios.CAMPOS_DE_ENVIO
            }
            return redirect("cuenta:despacho")
        return self._confirmar(request)

    def _confirmar(self, request):
        from apps.tienda.mercadopago import SinCredencial
        from apps.tienda.pasarelas import pasarela

        try:
            despacho = servicios.confirmar_despacho(
                request.user,
                request.session.get(CLAVE_SELECCION, []),
                self._envio(request),
                request=request,
                pasarela=pasarela(),
            )
        except servicios.OperacionRechazada as rechazo:
            messages.error(request, str(rechazo))
            return redirect("cuenta:despacho")
        except SinCredencial:
            messages.error(request, "El pago online no está disponible en este momento.")
            return redirect("cuenta:despacho")
        if despacho.solicitud is not None:
            _terminar(request)
            messages.success(
                request,
                f"Pediste el envío ({despacho.solicitud.numero}). Te avisamos cuando salga.",
            )
            return redirect("cuenta:stock")
        if despacho.redireccion:
            return redirect(despacho.redireccion)
        messages.error(request, "No pudimos conectar con la pasarela de pago. Probá de nuevo.")
        return redirect("cuenta:despacho")


def _terminar(request):
    request.session.pop(CLAVE_SELECCION, None)
    request.session.pop(CLAVE_ENVIO, None)


def resultado_de_pago(request, cobro):
    """Cómo terminó el pago del envío (A1), desde la pantalla de resultado de la compra."""
    if cobro.estado == cobro.PROCESADO:
        _terminar(request)
        messages.success(
            request,
            f"Pago aprobado: pediste el envío ({cobro.solicitud.numero}). "
            "Te avisamos cuando salga.",
        )
        return redirect("cuenta:stock")
    if cobro.estado == cobro.RECHAZADO:
        messages.error(
            request,
            (cobro.mensaje or "La pasarela rechazó el pago.")
            + " Tus artículos siguen disponibles.",
        )
        return redirect("cuenta:despacho")
    _terminar(request)
    messages.error(
        request,
        "El pago se aprobó pero uno de los artículos ya no estaba disponible. "
        "El cargo se revierte.",
    )
    return redirect("cuenta:stock")
