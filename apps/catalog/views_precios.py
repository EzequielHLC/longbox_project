"""Las pantallas del módulo 03: tabla de precios de referencia y margen global.

- `CU-PVP-TBC` consulta la tabla con filtros por editorial, tipo y formato.
- `CU-PVP-TBA` da de alta una combinación.
- `CU-PVP-TBM` cambia un precio en dos tiempos: el informe de alcance y la
  confirmación, que propaga.
- `CU-PVP-TBB` quita una combinación en dos tiempos.
- `CU-PVP-MAR` cambia el margen en dos tiempos: la simulación y la confirmación.
- `CO-031` restaura el precio calculado de un producto, mostrándolo antes.

Volver sin confirmar es `cancelarOperacion` (`CO-156`): no cambia ni se audita.
Exclusivas del Administrador, validado en el servidor (RNF-03).
"""

from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views import View
from django.views.generic import CreateView, ListView

from apps.catalog import tabla_de_precios
from apps.catalog.forms import MargenForm, PrecioModificacionForm, PrecioReferenciaForm
from apps.catalog.models import Editorial, Formato, ProductoEditorial, TablaPrecioReferencia, Tipo
from apps.catalog.views import CatalogoAdminMixin, _entero
from apps.core import cotizaciones
from apps.core.models import ConfiguracionSistema
from apps.core.utils import obtener_ip


class PrecioListaView(CatalogoAdminMixin, ListView):
    """`CO-166`: las combinaciones con su precio, con filtros combinables."""

    template_name = "catalog/precio_lista.html"
    context_object_name = "precios"
    FILTROS = (("editorial", Editorial), ("tipo", Tipo), ("formato", Formato))  # noqa: RUF012

    def filtros(self):
        return {campo: _entero(self.request.GET.get(campo)) for campo, _ in self.FILTROS}

    def get_queryset(self):
        filas = TablaPrecioReferencia.objects.select_related("editorial", "tipo", "formato")
        for campo, valor in self.filtros().items():
            if valor:
                filas = filas.filter(**{f"{campo}_id": valor})
        return filas

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        filtros = self.filtros()
        contexto.update(
            {
                "filtros": filtros,
                "hay_filtros": any(filtros.values()),
                "total": TablaPrecioReferencia.objects.count(),
                "editoriales": Editorial.objects.all(),
                "tipos": Tipo.objects.filter(usa_formato=True),
                "formatos": Formato.objects.all(),
                "cotizaciones": cotizaciones.resumen_para_pantalla(),
            }
        )
        # B-03-006: el PVP en otras monedas, a la cotización de referencia.
        valores = contexto["cotizaciones"]["valores"]
        for precio in contexto["precios"]:
            precio.equivalencias = cotizaciones.equivalencias(precio.pvp, valores)
        return contexto


class PrecioCrearView(CatalogoAdminMixin, CreateView):
    """`CU-PVP-TBA` — `CO-049`."""

    model = TablaPrecioReferencia
    form_class = PrecioReferenciaForm
    template_name = "catalog/precio_formulario.html"

    def form_valid(self, form):
        fila = tabla_de_precios.registrar(
            form, actor=self.request.user, ip=obtener_ip(self.request)
        )
        messages.success(
            self.request,
            f"Se agregó {tabla_de_precios.combinacion(fila)} a ${fila.pvp}.",
        )
        return redirect("catalog:precio_lista")


class PrecioModificarView(CatalogoAdminMixin, View):
    """`CU-PVP-TBM`: el precio nuevo, el informe de alcance y la confirmación.

    Un `POST` sin `confirmar` es la solicitud (`CO-047`): valida y muestra a
    cuántos productos llega. Con `confirmar` es `CO-048`, que vuelve a validar
    el precio: lo que se confirma es lo que viaja, no lo que se informó.
    """

    def dispatch(self, request, *args, **kwargs):
        self.fila = get_object_or_404(
            TablaPrecioReferencia.objects.select_related("editorial", "tipo", "formato"),
            pk=kwargs["pk"],
        )
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, pk):
        formulario = PrecioModificacionForm(initial={"pvp": self.fila.pvp})
        return self._pantalla(request, formulario)

    def post(self, request, pk):
        formulario = PrecioModificacionForm(request.POST)
        if not formulario.is_valid():
            return self._pantalla(request, formulario)

        nuevo = formulario.cleaned_data["pvp"]
        if "confirmar" not in request.POST:
            return self._pantalla(
                request,
                formulario,
                informe=tabla_de_precios.solicitar_modificacion(self.fila),
                nuevo=nuevo,
            )

        resumen = tabla_de_precios.confirmar_modificacion(
            self.fila, nuevo, actor=request.user, ip=obtener_ip(request)
        )
        messages.success(
            request,
            f"{resumen.combinacion}: ${resumen.anterior} → ${resumen.nuevo}. "
            f"{resumen.actualizados} producto{'s' if resumen.actualizados != 1 else ''} "
            "actualizado" + ("s." if resumen.actualizados != 1 else "."),
        )
        return redirect("catalog:precio_lista")

    def _pantalla(self, request, formulario, informe=None, nuevo=None):
        return render(
            request,
            "catalog/precio_modificar.html",
            {"fila": self.fila, "form": formulario, "informe": informe, "nuevo": nuevo},
        )


class PrecioEliminarView(CatalogoAdminMixin, View):
    """`CU-PVP-TBB`: el informe de vinculados (`CO-050`) y la baja (`CO-051`)."""

    def get(self, request, pk):
        fila = get_object_or_404(TablaPrecioReferencia, pk=pk)
        return render(
            request,
            "catalog/precio_eliminar.html",
            {"precio": fila, "vinculados": tabla_de_precios.solicitar_baja(fila)},
        )

    def post(self, request, pk):
        fila = get_object_or_404(TablaPrecioReferencia, pk=pk)
        descripcion = tabla_de_precios.combinacion(fila)
        desvinculados = tabla_de_precios.confirmar_baja(
            fila, actor=request.user, ip=obtener_ip(request)
        )
        if desvinculados is not None:
            messages.success(
                request,
                f"Se quitó {descripcion} de la tabla. {desvinculados} producto"
                f"{'s' if desvinculados != 1 else ''} conserva"
                f"{'n' if desvinculados != 1 else ''} su precio sin vínculo.",
            )
        return redirect("catalog:precio_lista")


class RestaurarPrecioView(CatalogoAdminMixin, View):
    """`CO-031`: el precio recalculado a la vista antes de guardar.

    Se llega desde la ficha y desde la edición del producto (`CU-CAT-EDI` A2).
    """

    def get(self, request, pk):
        producto = get_object_or_404(ProductoEditorial, pk=pk)
        return render(
            request,
            "catalog/producto_restaurar_precio.html",
            {"producto": producto, "restauracion": tabla_de_precios.restauracion_de(producto)},
        )

    def post(self, request, pk):
        producto = get_object_or_404(ProductoEditorial, pk=pk)
        restauracion = tabla_de_precios.restaurar_precio_calculado(
            producto, actor=request.user, ip=obtener_ip(request)
        )
        if restauracion.aplica:
            messages.success(
                request,
                f"El precio volvió al calculado: ${restauracion.precio_actual} → "
                f"${restauracion.precio_recalculado}.",
            )
        else:
            messages.info(request, restauracion.motivo)
        return redirect(reverse("catalog:producto_detalle", args=[pk]))


class MargenView(CatalogoAdminMixin, View):
    """`CU-PVP-MAR`: el valor vigente, la simulación y la confirmación.

    Sale de la pantalla de parámetros porque cambiarlo propaga precios
    (`CU-CFG-PAR` A1). Un `POST` sin `confirmar` es la simulación (`CO-052`);
    con `confirmar`, el cambio (`CO-053`).
    """

    template_name = "catalog/margen.html"

    def get(self, request):
        return self._pantalla(
            request, MargenForm(initial={"margen": self._vigente_en_porcentaje()})
        )

    def post(self, request):
        formulario = MargenForm(request.POST)
        if not tabla_de_precios.hay_importados():
            # La precondición de `CO-052`: sin importados no hay cambio posible
            # (C-11, mandan los contratos; C-19 sigue abierta).
            return self._pantalla(request, formulario)
        if not formulario.is_valid():
            return self._pantalla(request, formulario)

        nuevo = formulario.proporcion()
        if "confirmar" not in request.POST:
            return self._pantalla(request, formulario, nuevo=nuevo, a_confirmar=True)

        resumen = tabla_de_precios.confirmar_cambio_de_margen(
            nuevo, actor=request.user, ip=obtener_ip(request)
        )
        messages.success(
            request,
            f"Margen global: {tabla_de_precios.porcentaje(resumen.anterior)} → "
            f"{tabla_de_precios.porcentaje(resumen.nuevo)}. {resumen.recalculados} productos "
            f"recalculados y {resumen.excluidos_por_precio_manual} excluidos por precio a mano.",
        )
        return redirect("catalog:margen")

    def _vigente_en_porcentaje(self):
        return ConfiguracionSistema.obtener().margen_ganancia * 100

    def _pantalla(self, request, formulario, nuevo=None, a_confirmar=False):
        configuracion = ConfiguracionSistema.obtener()
        return render(
            request,
            self.template_name,
            {
                "form": formulario,
                "vigente": tabla_de_precios.porcentaje(configuracion.margen_ganancia),
                "configuracion": configuracion,
                "hay_importados": tabla_de_precios.hay_importados(),
                "simulacion": tabla_de_precios.simular_cambio_de_margen(),
                "nuevo": tabla_de_precios.porcentaje(nuevo) if nuevo is not None else "",
                "a_confirmar": a_confirmar,
            },
        )
