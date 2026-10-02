"""El contenido de la tienda: FAQ, banners e identidad visual (CU-CFG-FAQ, BN*, VIS).

Las pantallas de edición son del Administrador (RNF-03). Lo que publican se ve
en la tienda: la portada con el carrusel, la página de preguntas frecuentes y
la hoja de estilo con las variables `--tienda-*` (C-06, C-07).
"""

from django.contrib import messages
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.views import View
from django.views.generic import TemplateView

from apps.core import contenido
from apps.core.forms import BannerEdicionForm, BannerForm, FaqForm, IdentidadVisualForm
from apps.core.mixins import RolRequeridoMixin
from apps.core.models import Banner, ConfiguracionSistema, ContenidoFAQ, IdentidadVisual
from apps.core.utils import obtener_ip


class ContenidoAdminMixin(RolRequeridoMixin):
    roles_permitidos = ("administrador",)


# ---------------------------------------------------------------------------
# FAQ — CU-CFG-FAQ (CO-210, CO-135, CO-136)
# ---------------------------------------------------------------------------


class FaqView(ContenidoAdminMixin, View):
    """El editor Markdown con su vista previa, y la publicación.

    La vista previa es un envío que no guarda nada: pertenece al editor y no
    publica (comentario de la ficha). «Descartar cambios» vuelve a cargar lo
    publicado (A1). Un contenido vacío pide confirmación explícita (A2).
    """

    template_name = "core/faq_editor.html"

    def get(self, request):
        faq = ContenidoFAQ.obtener()
        return self._pantalla(request, FaqForm(initial={"contenido": faq.contenido}))

    def post(self, request):
        formulario = FaqForm(request.POST)
        formulario.is_valid()
        texto = formulario.cleaned_data.get("contenido", "")

        if "vista_previa" in request.POST:
            return self._pantalla(
                request, formulario, vista_previa=contenido.markdown_a_html(texto)
            )

        publicado = contenido.publicar_faq(
            texto,
            actor=request.user,
            ip=obtener_ip(request),
            confirma_vacia="confirmar_vacia" in request.POST,
        )
        if not publicado:
            return self._pantalla(request, formulario, advertir_vacia=True)

        messages.success(request, "Se publicó la FAQ. Ya se ve así en la tienda.")
        return redirect("core:faq_editor")

    def _pantalla(self, request, formulario, vista_previa=None, advertir_vacia=False):
        return render(
            request,
            self.template_name,
            {
                "form": formulario,
                "faq": ContenidoFAQ.obtener(),
                "vista_previa": vista_previa,
                "advertir_vacia": advertir_vacia,
            },
        )


class FaqPublicaView(TemplateView):
    """Las preguntas frecuentes en la tienda, tal como se publicaron (`CO-135`)."""

    template_name = "core/faq.html"

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        faq = ContenidoFAQ.obtener()
        contexto["faq_html"] = contenido.markdown_a_html(faq.contenido)
        contexto["faq"] = faq
        return contexto


# ---------------------------------------------------------------------------
# Banners — CU-CFG-BNC, BNA, BNM, BNB (CO-209, CO-132, CO-133, CO-134)
# ---------------------------------------------------------------------------


class BannerListaView(ContenidoAdminMixin, TemplateView):
    """`CO-209`: la galería en orden, con la vista previa del carrusel."""

    template_name = "core/banner_lista.html"

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        contexto["banners"] = Banner.objects.all()
        contexto["intervalo"] = ConfiguracionSistema.obtener().intervalo_carrusel
        return contexto


class BannerCrearView(ContenidoAdminMixin, View):
    template_name = "core/banner_formulario.html"

    def get(self, request):
        return render(request, self.template_name, {"form": BannerForm(), "titulo": "Nuevo banner"})

    def post(self, request):
        formulario = BannerForm(request.POST, request.FILES)
        if not formulario.is_valid():
            contexto = {"form": formulario, "titulo": "Nuevo banner"}
            return render(request, self.template_name, contexto)
        banner = contenido.agregar_banner(
            formulario.cleaned_data["imagen"], actor=request.user, ip=obtener_ip(request)
        )
        messages.success(
            request, f"Se agregó el banner en la posición {banner.numero}. Ya está en la tienda."
        )
        return redirect("core:banner_lista")


class BannerEditarView(ContenidoAdminMixin, View):
    template_name = "core/banner_formulario.html"

    def _contexto(self, banner, formulario):
        return {"form": formulario, "banner": banner, "titulo": f"Modificar {banner}"}

    def get(self, request, pk):
        banner = get_object_or_404(Banner, pk=pk)
        return render(
            request, self.template_name, self._contexto(banner, BannerEdicionForm(banner=banner))
        )

    def post(self, request, pk):
        banner = get_object_or_404(Banner, pk=pk)
        formulario = BannerEdicionForm(request.POST, request.FILES, banner=banner)
        if not formulario.is_valid():
            # E1: una imagen inválida no deja registrar nada, tampoco la posición.
            return render(request, self.template_name, self._contexto(banner, formulario))
        contenido.editar_banner(
            banner,
            actor=request.user,
            ip=obtener_ip(request),
            imagen_procesada=formulario.cleaned_data.get("imagen"),
            numero=formulario.cleaned_data.get("numero"),
        )
        messages.success(request, "Se guardaron los cambios del banner. Ya se ven en la tienda.")
        return redirect("core:banner_lista")


class BannerBajaView(ContenidoAdminMixin, View):
    """`CO-134`: la confirmación y la baja. Volver sin confirmar no cambia nada."""

    def get(self, request, pk):
        banner = get_object_or_404(Banner, pk=pk)
        return render(request, "core/banner_baja.html", {"banner": banner})

    def post(self, request, pk):
        banner = get_object_or_404(Banner, pk=pk)
        contenido.eliminar_banner(banner, actor=request.user, ip=obtener_ip(request))
        messages.success(request, "Se eliminó el banner y se reordenó la galería.")
        return redirect("core:banner_lista")


# ---------------------------------------------------------------------------
# Identidad visual — CU-CFG-VIS (CO-208, CO-131)
# ---------------------------------------------------------------------------


class IdentidadVisualView(ContenidoAdminMixin, View):
    template_name = "core/identidad_visual.html"

    def get(self, request):
        identidad = IdentidadVisual.obtener()
        return self._pantalla(request, IdentidadVisualForm(instance=identidad), identidad)

    def post(self, request):
        identidad = IdentidadVisual.obtener()
        formulario = IdentidadVisualForm(request.POST, request.FILES, instance=identidad)
        if not formulario.is_valid():
            # E1 y E2: no se aplica ningún cambio hasta corregir.
            return self._pantalla(request, formulario, IdentidadVisual.obtener())
        contenido.actualizar_identidad(
            formulario,
            actor=request.user,
            ip=obtener_ip(request),
            logo=formulario.cleaned_data.get("logo_nuevo"),
            imagen_fondo=formulario.cleaned_data.get("fondo_nuevo"),
        )
        messages.success(request, "Se guardó la identidad visual. Ya se ve en la tienda.")
        return redirect("core:identidad_visual")

    def _pantalla(self, request, formulario, identidad):
        return render(request, self.template_name, {"form": formulario, "identidad": identidad})


class TiendaCssView(View):
    """La hoja con las cuatro variables `--tienda-*` y el fondo, sin sesión.

    Los colores ya están validados como `#RRGGBB`, y la dirección de la imagen
    sale del almacenamiento: nada de lo que se escribe acá lo tipea alguien.
    """

    def get(self, request):
        identidad = IdentidadVisual.obtener()
        hoja = render_to_string("core/tienda.css", {"identidad": identidad})
        respuesta = HttpResponse(hoja, content_type="text/css; charset=utf-8")
        respuesta["Cache-Control"] = "public, max-age=86400"
        return respuesta
