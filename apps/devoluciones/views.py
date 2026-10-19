"""Las devoluciones en el panel de gestión (plan 09). Se montan en `devoluciones/`.

`CU-DEV-RES` es del Administrador: el Cajero recibe 403 por la dirección real.
La única excepción es la foto de un caso, que también ve el Cliente que la subió
(y nadie más: el caso de otro responde 404).
"""

from django.contrib import messages
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View

from apps.accounts.models import Usuario
from apps.core.mixins import RolRequeridoMixin
from apps.devoluciones import servicios
from apps.devoluciones.models import CasoDevolucion, EvidenciaDevolucion


class AdministradorMixin(RolRequeridoMixin):
    roles_permitidos = (Usuario.ADMINISTRADOR,)


def _origen(request):
    return request.build_absolute_uri("/").rstrip("/")


def _caso(pk):
    try:
        return servicios.detalle(pk)
    except CasoDevolucion.DoesNotExist as error:
        raise Http404("No existe ese caso.") from error


# ---------------------------------------------------------------------------
# CO-186 consultarCasosDeDevolucion · CO-187 consultarDetalleDeCasoDeDevolucion
# ---------------------------------------------------------------------------


class ListaView(AdministradorMixin, View):
    """`CO-186`: los pendientes, más antiguos primero. E2: vacío, con el historial a mano."""

    FILTROS = (  # noqa: RUF012
        ("pendientes", "Pendientes"),
        ("historial", "Resueltos y rechazados"),
        ("resueltos", "Resueltos"),
        ("rechazados", "Rechazados"),
    )

    def get(self, request):
        filtro = request.GET.get("filtro", "pendientes")
        if filtro not in servicios.FILTROS:
            filtro = "pendientes"
        return render(
            request,
            "devoluciones/lista.html",
            {
                "casos": list(servicios.consultar_casos(filtro)[:200]),
                "filtro": filtro,
                "filtros": self.FILTROS,
            },
        )


class DetalleView(AdministradorMixin, View):
    """`CO-187`: el caso completo, con el contacto para coordinar por fuera del
    sistema, las fotos y las resoluciones que admite (plan 00, C1)."""

    def get(self, request, pk):
        caso = _caso(pk)
        return render(
            request,
            "devoluciones/detalle.html",
            {
                "caso": caso,
                "linea": caso.linea,
                "pedido": caso.linea.pedido,
                "opciones": servicios.opciones(caso),
            },
        )


# ---------------------------------------------------------------------------
# CO-100 resolverCasoConCambio
# ---------------------------------------------------------------------------


class CambioView(AdministradorMixin, View):
    """Paso 5, opción A. GET busca el reemplazo y, elegido, muestra los dos precios
    (ambigüedad 8); POST confirma. Sin stock (E1), no se puede confirmar."""

    def _pendiente(self, request, pk):
        caso = _caso(pk)
        if not caso.abierto:
            messages.error(request, "El caso ya no está pendiente.")
            return caso, redirect("devoluciones:detalle", pk=pk)
        return caso, None

    def get(self, request, pk):
        caso, salida = self._pendiente(request, pk)
        if salida:
            return salida
        if not servicios.opciones(caso).cambio:
            messages.error(request, "Este reclamo no se resuelve con un cambio.")
            return redirect("devoluciones:detalle", pk=pk)
        buscar = request.GET.get("buscar", "").strip()
        elegido = None
        if request.GET.get("producto", "").isdigit():
            elegido = (
                servicios._reemplazos_de(caso)
                .select_related("productoeditorial")
                .filter(pk=request.GET["producto"])
                .first()
            )
            if elegido is not None:
                elegido.con_stock = servicios.con_stock(elegido)
        return render(
            request,
            "devoluciones/cambio.html",
            {
                "caso": caso,
                "linea": caso.linea,
                "buscar": buscar,
                "resultados": servicios.buscar_reemplazos(caso, buscar),
                "elegido": elegido,
            },
        )

    def post(self, request, pk):
        get_object_or_404(CasoDevolucion, pk=pk)
        producto = request.POST.get("producto", "")
        try:
            servicios.resolver_con_cambio(
                pk,
                int(producto) if producto.isdigit() else 0,
                request.user,
                origen=_origen(request),
            )
        except CasoDevolucion.DoesNotExist as error:
            raise Http404("No existe ese caso.") from error
        except servicios.SinStock as rechazo:
            messages.error(request, str(rechazo))
            return redirect("devoluciones:cambio", pk=pk)
        except servicios.OperacionRechazada as rechazo:
            messages.error(request, str(rechazo))
            return redirect("devoluciones:detalle", pk=pk)
        messages.success(request, "Cambio autorizado. Le avisamos al cliente.")
        return redirect("devoluciones:detalle", pk=pk)


# ---------------------------------------------------------------------------
# CO-101 resolverCasoConReembolsoEnPuntos
# ---------------------------------------------------------------------------


class ReembolsoView(AdministradorMixin, View):
    """Paso 5, opción B. GET muestra cuántos puntos se acreditan; POST confirma."""

    def get(self, request, pk):
        caso = _caso(pk)
        if not caso.abierto or not servicios.opciones(caso).puntos:
            messages.error(request, "Este reclamo no se reembolsa en puntos.")
            return redirect("devoluciones:detalle", pk=pk)
        return render(
            request,
            "devoluciones/reembolso.html",
            {
                "caso": caso,
                "linea": caso.linea,
                "puntos": servicios.puntos_de_reembolso(caso.linea) * caso.unidades,
            },
        )

    def post(self, request, pk):
        try:
            hecho = servicios.resolver_con_reembolso(pk, request.user, origen=_origen(request))
        except CasoDevolucion.DoesNotExist as error:
            raise Http404("No existe ese caso.") from error
        except servicios.OperacionRechazada as rechazo:
            messages.error(request, str(rechazo))
            return redirect("devoluciones:detalle", pk=pk)
        messages.success(
            request,
            f"Reembolso acreditado: {hecho.puntos} pts. El saldo del cliente es de "
            f"{hecho.saldo} pts.",
        )
        return redirect("devoluciones:detalle", pk=pk)


class ReembolsoMedioView(AdministradorMixin, View):
    """El reembolso por el medio de pago (plan 00, C1): se registra lo que el local
    devuelve desde el panel de la pasarela. GET muestra el monto; POST registra."""

    def get(self, request, pk):
        caso = _caso(pk)
        if not caso.abierto or not servicios.opciones(caso).medio:
            messages.error(request, "Este reclamo no se reembolsa por el medio de pago.")
            return redirect("devoluciones:detalle", pk=pk)
        return render(
            request,
            "devoluciones/reembolso_medio.html",
            {
                "caso": caso,
                "linea": caso.linea,
                "monto": servicios.monto_por_el_medio(caso),
                "incluye_envio": servicios._completa_el_pedido(caso)
                and bool(caso.linea.pedido.costo_envio),
                "pago": servicios._pagos_por_la_pasarela(caso.linea.pedido).first(),
            },
        )

    def post(self, request, pk):
        try:
            hecho = servicios.resolver_con_reembolso_por_el_medio(
                pk, request.user, origen=_origen(request)
            )
        except CasoDevolucion.DoesNotExist as error:
            raise Http404("No existe ese caso.") from error
        except servicios.OperacionRechazada as rechazo:
            messages.error(request, str(rechazo))
            return redirect("devoluciones:detalle", pk=pk)
        messages.success(request, f"Reembolso registrado: $ {hecho.monto}. Le avisamos al cliente.")
        return redirect("devoluciones:detalle", pk=pk)


# ---------------------------------------------------------------------------
# CO-102 rechazarCasoDeDevolucion
# ---------------------------------------------------------------------------


class RechazoView(AdministradorMixin, View):
    """A1. El motivo es obligatorio; volver no registra nada."""

    def get(self, request, pk, error="", motivo=""):
        caso = _caso(pk)
        if not caso.abierto:
            messages.error(request, "El caso ya no está pendiente.")
            return redirect("devoluciones:detalle", pk=pk)
        return render(
            request,
            "devoluciones/rechazo.html",
            {"caso": caso, "linea": caso.linea, "error": error, "motivo": motivo},
        )

    def post(self, request, pk):
        motivo = request.POST.get("motivo", "")
        if not motivo.strip():
            return self.get(request, pk, error="El motivo del rechazo es obligatorio.")
        try:
            servicios.rechazar(pk, request.user, motivo, origen=_origen(request))
        except CasoDevolucion.DoesNotExist as error:
            raise Http404("No existe ese caso.") from error
        except servicios.OperacionRechazada as rechazo:
            messages.error(request, str(rechazo))
            return redirect("devoluciones:detalle", pk=pk)
        messages.success(request, "Caso rechazado. Le avisamos al cliente con el motivo.")
        return redirect("devoluciones:detalle", pk=pk)


# ---------------------------------------------------------------------------
# Las fotos del caso (ambigüedad 10)
# ---------------------------------------------------------------------------


class EvidenciaView(RolRequeridoMixin, View):
    """Una foto, para el Administrador o para el Cliente que la subió."""

    roles_permitidos = (Usuario.ADMINISTRADOR, Usuario.CLIENTE)

    def get(self, request, pk, foto):
        evidencia = get_object_or_404(
            EvidenciaDevolucion.objects.select_related("caso"), pk=foto, caso_id=pk
        )
        if request.user.rol == Usuario.CLIENTE and evidencia.caso.usuario_id != request.user.pk:
            raise Http404("No existe esa foto.")
        try:
            archivo = evidencia.imagen.open("rb")
        except FileNotFoundError as error:
            raise Http404("La foto no está en el almacenamiento.") from error
        respuesta = FileResponse(archivo, content_type="image/webp")
        respuesta["Cache-Control"] = "private, no-store"
        return respuesta
