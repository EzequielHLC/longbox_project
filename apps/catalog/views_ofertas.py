"""Gestión de Ofertas (`CU-PVP-CON`, `ALT`, `EDI`, `BAJ`). Sólo el Administrador.

Las pantallas no deciden nada de lo que el contrato declara: lo valida
`apps.catalog.ofertas`. Acá se traduce cada rechazo a su campo o a un mensaje.
"""

from datetime import date

from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View

from apps.catalog import ofertas
from apps.catalog.forms_ofertas import OfertaForm, opcion_de, productos_elegibles
from apps.catalog.models import Oferta
from apps.catalog.precio_visible import hoy_local
from apps.catalog.views import CatalogoAdminMixin
from apps.core.utils import obtener_ip

POR_PAGINA = 25


def _fecha(texto):
    try:
        return date.fromisoformat(texto) if texto else None
    except ValueError:
        return None


def _ofertas():
    return Oferta.objects.select_related("producto", "tipo")


class FiltrosDeOfertas:
    """Paso 3 de `CU-PVP-CON`: estado, rango de fechas de inicio o de vencimiento, y texto."""

    CAMPOS_DE_FECHA = (("inicio", "fecha_inicio"), ("vencimiento", "fecha_vencimiento"))

    def __init__(self, parametros):
        self.estado = parametros.get("estado", "")
        if self.estado not in dict(Oferta.ESTADOS):
            self.estado = ""
        self.fecha = parametros.get("fecha", "inicio")
        if self.fecha not in dict(self.CAMPOS_DE_FECHA):
            self.fecha = "inicio"
        self.desde = _fecha(parametros.get("desde"))
        self.hasta = _fecha(parametros.get("hasta"))
        self.texto = parametros.get("q", "").strip()

    @property
    def activos(self):
        return bool(self.estado or self.desde or self.hasta or self.texto)

    def aplicar(self, consulta, hoy):
        if self.estado:
            consulta = consulta.filter(ofertas.filtro_de_estado(self.estado, hoy))
        campo = dict(self.CAMPOS_DE_FECHA)[self.fecha]
        if self.desde:
            consulta = consulta.filter(**{f"{campo}__gte": self.desde})
        if self.hasta:
            consulta = consulta.filter(**{f"{campo}__lte": self.hasta})
        if self.texto:
            consulta = consulta.filter(
                Q(descripcion__icontains=self.texto)
                | Q(producto__titulo__icontains=self.texto)
                | Q(tipo__nombre__icontains=self.texto)
            )
        return consulta


class OfertaListaView(CatalogoAdminMixin, View):
    """`CO-169`: de la fecha de inicio más reciente a la más vieja."""

    def get(self, request):
        hoy = hoy_local()
        filtros = FiltrosDeOfertas(request.GET)
        todas = Oferta.objects.select_related("producto", "tipo")
        encontradas = filtros.aplicar(todas, hoy).order_by("-fecha_inicio", "-pk")
        pagina = Paginator(encontradas, POR_PAGINA).get_page(request.GET.get("page"))
        for oferta in pagina.object_list:
            oferta.estado_hoy = oferta.estado_en(hoy)
        parametros = request.GET.copy()
        parametros.pop("page", None)
        return render(
            request,
            "catalog/oferta_lista.html",
            {
                "pagina": pagina,
                "ofertas": pagina.object_list,
                "filtros": filtros,
                "estados": Oferta.ESTADOS,
                "hay_ofertas": todas.exists(),
                "parametros": parametros.urlencode(),
            },
        )


class OfertaFichaView(CatalogoAdminMixin, View):
    """`CO-170`: los parámetros, los productos con sus dos precios y las acciones del estado."""

    def get(self, request, pk):
        oferta = get_object_or_404(_ofertas(), pk=pk)
        hoy = hoy_local()
        estado = oferta.estado_en(hoy)
        return render(
            request,
            "catalog/oferta_ficha.html",
            {
                "oferta": oferta,
                "estado": estado,
                "descuento": ofertas.describir_descuento(oferta.tipo_descuento, oferta.valor),
                "alcance": ofertas.describir_alcance(oferta.alcance, oferta.producto, oferta.tipo),
                "productos": ofertas.productos_afectados(oferta, hoy=hoy),
                "editable": estado not in Oferta.TERMINALES,
            },
        )


class _FormularioDeOferta(CatalogoAdminMixin, View):
    """Lo común al alta y a la edición: el formulario, el tope (E3) y los rechazos."""

    template_name = "catalog/oferta_formulario.html"

    def pantalla(self, request, formulario, oferta=None, afectados=None):
        return render(
            request,
            self.template_name,
            {
                "form": formulario,
                "oferta": oferta,
                "afectados": afectados or [],
                "productos": [opcion_de(producto) for producto in productos_elegibles()],
            },
        )

    def procesar(self, request, formulario, ejecutar, oferta=None):
        if not formulario.is_valid():
            return None, self.pantalla(request, formulario, oferta)
        datos = formulario.datos()
        try:
            resultado = ejecutar(datos, aceptar_tope="aceptar_tope" in request.POST)
        except ofertas.TopeRequerido as tope:
            return None, self.pantalla(request, formulario, oferta, afectados=tope.afectados)
        except ofertas.OfertaRechazada as rechazo:
            formulario.add_error(rechazo.campo, str(rechazo))
            return None, self.pantalla(request, formulario, oferta)
        return (resultado, datos), None


class OfertaAltaView(_FormularioDeOferta):
    """`CO-054`, o `CO-055` si se confirma con el tope de $1."""

    def get(self, request):
        return self.pantalla(request, OfertaForm())

    def post(self, request):
        formulario = OfertaForm(request.POST)

        def ejecutar(datos, aceptar_tope):
            return ofertas.registrar(
                datos, actor=request.user, ip=obtener_ip(request), aceptar_tope=aceptar_tope
            )

        hecho, respuesta = self.procesar(request, formulario, ejecutar)
        if respuesta is not None:
            return respuesta
        oferta, datos = hecho
        messages.success(
            request, f"Oferta «{oferta.descripcion}» registrada: {oferta.get_estado_display()}."
        )
        if ofertas.tipo_sin_productos(datos):
            messages.warning(
                request,
                "El tipo de material seleccionado no tiene productos activos en este momento. "
                "La oferta quedó registrada y se aplicará automáticamente cuando los haya.",
            )
        return redirect("catalog:oferta_ficha", oferta.pk)


class OfertaEdicionView(_FormularioDeOferta):
    """`CO-168` abre, `CO-056` guarda. Vencida o Dada de baja no se editan (E2)."""

    def _abrir(self, request, pk):
        """`CO-168`. Se llama después del control de rol del mixin, nunca antes."""
        self.oferta = get_object_or_404(_ofertas(), pk=pk)
        if ofertas.se_puede_editar(self.oferta):
            return None
        messages.error(
            request,
            "Una oferta vencida o dada de baja no se puede modificar. "
            "Para volver a aplicar el descuento, creá una oferta nueva.",
        )
        return redirect("catalog:oferta_ficha", pk)

    def get(self, request, pk):
        if (bloqueo := self._abrir(request, pk)) is not None:
            return bloqueo
        return self.pantalla(request, OfertaForm(oferta=self.oferta), self.oferta)

    def post(self, request, pk):
        if (bloqueo := self._abrir(request, pk)) is not None:
            return bloqueo
        formulario = OfertaForm(request.POST, oferta=self.oferta)

        def ejecutar(datos, aceptar_tope):
            return ofertas.editar(
                self.oferta,
                datos,
                actor=request.user,
                ip=obtener_ip(request),
                aceptar_tope=aceptar_tope,
            )

        hecho, respuesta = self.procesar(request, formulario, ejecutar, self.oferta)
        if respuesta is not None:
            return respuesta
        cambios, _ = hecho
        if cambios:
            messages.success(request, f"Oferta actualizada: {'; '.join(cambios)}.")
        else:
            messages.info(request, "No hubo cambios que guardar.")
        return redirect("catalog:oferta_ficha", self.oferta.pk)


class OfertaBajaView(CatalogoAdminMixin, View):
    """`CO-057` es esta pantalla; el botón es `CO-058`. Cancelar es volver (`CO-156`)."""

    def get(self, request, pk):
        try:
            informe = ofertas.solicitar_baja(get_object_or_404(_ofertas(), pk=pk))
        except ofertas.OfertaRechazada as rechazo:
            messages.info(request, str(rechazo))
            return redirect("catalog:oferta_ficha", pk)
        return render(request, "catalog/oferta_baja.html", {"informe": informe})

    def post(self, request, pk):
        try:
            resumen = ofertas.confirmar_baja(
                get_object_or_404(_ofertas(), pk=pk), actor=request.user, ip=obtener_ip(request)
            )
        except ofertas.OfertaRechazada as rechazo:
            messages.info(request, str(rechazo))
            return redirect("catalog:oferta_ficha", pk)
        messages.success(
            request,
            f"Oferta «{resumen.oferta.descripcion}» dada de baja: {resumen.productos} productos "
            f"volvieron a su precio y {resumen.carritos} carritos se actualizaron.",
        )
        return redirect("catalog:oferta_ficha", pk)
