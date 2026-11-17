"""El contenido de la tienda: FAQ, banners e identidad visual (CU-CFG-FAQ, BN*, VIS).

Las pantallas de edición son del Administrador (RNF-03). Lo que publican se ve
en la tienda: la portada con el carrusel, la página de preguntas frecuentes y
la hoja de estilo con las variables `--tienda-*` (C-06, C-07).
"""

from django.contrib import messages
from django.db import transaction
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.views import View
from django.views.generic import TemplateView

from apps.core import cambios, colores, contenido
from apps.core.forms import (
    BannerEdicionForm,
    BannerForm,
    FaqForm,
    IdentidadVisualForm,
    ImagenesDeSeccionFormSet,
    SeccionesPortadaFormSet,
)
from apps.core.mixins import RolRequeridoMixin
from apps.core.models import (
    Banner,
    ConfiguracionSistema,
    ContenidoFAQ,
    IdentidadVisual,
    ImagenDeSeccion,
    RegistroAuditoria,
    SeccionPortada,
)
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
        messages.success(request, f"Se agregó el banner en la posición {banner.numero}.")
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
        messages.success(request, "Se guardaron los cambios del banner.")
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
            imagen_acceso=formulario.cleaned_data.get("acceso_nueva"),
            quitar={
                campo
                for campo, casilla in (("logo", "quitar_logo"), ("imagen_acceso", "quitar_acceso"))
                if formulario.cleaned_data.get(casilla)
            },
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
        hoja = render_to_string(
            "core/tienda.css",
            {
                "identidad": identidad,
                "roles": colores.variables(identidad),
                "sobre_encabezado": colores.encabezado_con_color(identidad),
            },
        )
        respuesta = HttpResponse(hoja, content_type="text/css; charset=utf-8")
        respuesta["Cache-Control"] = "public, max-age=86400"
        return respuesta


def _lista(partes):
    return " · ".join(partes) or "ninguna"


def _formularios_con_imagen(secciones, imagenes):
    """Los formularios de sección y de tarjeta que reemplazan o quitan su imagen."""
    for formulario in secciones.forms:
        if formulario in secciones.deleted_forms:
            continue
        if formulario.has_changed() and formulario.cambio_la_imagen:
            yield formulario
        propias = imagenes[formulario.prefix]
        for f in propias.forms:
            if f not in propias.deleted_forms and f.has_changed() and f.cambio_la_imagen:
                yield f


def _resumen_de_secciones():
    """Cada sección en una línea, con lo que la auditoría tiene que poder comparar."""
    resumen = []
    secciones = SeccionPortada.objects.select_related("etiqueta", "grupo").prefetch_related(
        "imagenes"
    )
    for seccion in secciones:
        linea = f"{seccion.titulo_visible} ({seccion.get_tipo_display().lower()})"
        if not seccion.activa:
            linea += " (inactiva)"
        if seccion.imagen:
            linea += " (con imagen)"
        if seccion.presentacion == SeccionPortada.VITRINA:
            linea += " (vitrina)"
        if seccion.tipo in SeccionPortada.IMAGENES_POR_TIPO:
            imagenes = [
                f"{imagen}→{imagen.get_destino_display().lower()}"
                for imagen in seccion.imagenes.all()
            ]
            linea += f": {_lista(imagenes)}"
        resumen.append(linea)
    return resumen


class SeccionesPortadaView(ContenidoAdminMixin, View):
    """Las secciones de la portada de la tienda (`CU-CFG-SEC`; plan 07, novena parte).

    Una tarjeta por sección, que se reordena arrastrándola (B-07-010); «Agregar
    sección» suma una del tipo elegido. Las que llevan imágenes tienen adentro
    sus propias tarjetas, que también se reordenan. Todo se guarda junto y el
    cambio queda auditado con la lista anterior y la nueva; cambiar sólo una
    imagen también se audita, aunque la lista quede igual.

    Lo que pide cada tipo lo valida el servidor: cuántas imágenes lleva, el
    destino de cada una y que Recién llegados y Lo que se viene no se quiten.
    """

    template_name = "core/secciones_portada.html"

    def get(self, request):
        secciones = SeccionesPortadaFormSet(queryset=SeccionPortada.objects.all())
        return self._pantalla(request, secciones, self._imagenes(secciones))

    def post(self, request):
        secciones = SeccionesPortadaFormSet(
            request.POST, request.FILES, queryset=SeccionPortada.objects.all()
        )
        imagenes = self._imagenes(secciones, request)
        validas = secciones.is_valid()
        validas = all([imagen.is_valid() for imagen in imagenes.values()]) and validas
        if validas:
            validas = self._cantidades(secciones, imagenes)
        if not validas:
            return self._pantalla(request, secciones, imagenes)
        antes = _resumen_de_secciones()
        # Plan 16, segunda parte: el archivo que tenía cada imagen antes de
        # guardar. Los formularios todavía no la reemplazaron en la instancia.
        vieja = {
            id(f): f.instance.imagen.name
            for f in _formularios_con_imagen(secciones, imagenes)
            if f.instance.pk
        }
        with transaction.atomic():
            secciones.save()
            cambiadas = []
            registro_de_imagenes = []
            for formulario in secciones.forms:
                if formulario in secciones.deleted_forms:
                    continue
                if formulario.has_changed() and formulario.cambio_la_imagen:
                    cambiadas.append(formulario.instance.titulo_visible)
                    registro_de_imagenes.append(
                        cambios.imagen(
                            f"imagen de {formulario.instance.titulo_visible}",
                            vieja.get(id(formulario), ""),
                            formulario.instance.imagen.name,
                        )
                    )
                propias = imagenes[formulario.prefix]
                propias.instance = formulario.instance
                propias.save()
                for f in propias.forms:
                    if f not in propias.deleted_forms and f.has_changed() and f.cambio_la_imagen:
                        cambiadas.append(str(f.instance))
                        registro_de_imagenes.append(
                            cambios.imagen(
                                f"imagen de {f.instance}",
                                vieja.get(id(f), ""),
                                f.instance.imagen.name,
                            )
                        )
            despues = _resumen_de_secciones()
            if antes != despues or cambiadas:
                detalle = f"{_lista(antes)} → {_lista(despues)}"
                if cambiadas:
                    detalle += f"; imagen cambiada en {_lista(cambiadas)}"
                registro = []
                if antes != despues:
                    registro.append(("secciones", _lista(antes), _lista(despues)))
                RegistroAuditoria.registrar(
                    accion=RegistroAuditoria.MODIFICACION_SECCIONES_PORTADA,
                    actor=request.user,
                    ip=obtener_ip(request),
                    detalle=detalle,
                    cambios=registro + registro_de_imagenes,
                )
        messages.success(request, "Se guardaron las secciones de la portada.")
        return redirect("core:secciones_portada")

    @staticmethod
    def _imagenes(secciones, request=None):
        """Las imágenes de cada tarjeta, con el prefijo de su sección."""
        salida = {}
        for formulario in secciones.forms:
            argumentos = (request.POST, request.FILES) if request else ()
            salida[formulario.prefix] = ImagenesDeSeccionFormSet(
                *argumentos,
                instance=formulario.instance,
                prefix=f"{formulario.prefix}-img",
            )
        return salida

    @staticmethod
    def _cantidades(secciones, imagenes):
        """Cada tipo con imágenes, dentro de su mínimo y su máximo."""
        validas = True
        for formulario in secciones.forms:
            if formulario in secciones.deleted_forms:
                continue
            tipo = formulario.cleaned_data["tipo"]
            if tipo not in SeccionPortada.IMAGENES_POR_TIPO:
                continue
            minimo, maximo = SeccionPortada.IMAGENES_POR_TIPO[tipo]
            propias = imagenes[formulario.prefix]
            # La onomatopeya sin imagen es sólo de la página de historieta: en
            # las demás, la imagen es lo que se dibuja.
            if tipo != SeccionPortada.PAGINA:
                for imagen in propias.forms:
                    if imagen in propias.deleted_forms or not imagen.has_changed():
                        continue
                    if imagen.cleaned_data.get("forma_texto") == ImagenDeSeccion.GRITO:
                        imagen.add_error(
                            "imagen",
                            "Falta la imagen: la onomatopeya sin imagen es sólo de la "
                            "página de historieta.",
                        )
                        validas = False
            cantidad = propias.cantidad()
            if not minimo <= cantidad <= maximo:
                nombre = dict(SeccionPortada.TIPOS)[tipo]
                rango = f"{minimo}" if minimo == maximo else f"entre {minimo} y {maximo}"
                formulario.add_error(None, f"{nombre} lleva {rango} imágenes y tiene {cantidad}.")
                validas = False
        return validas

    def _pantalla(self, request, secciones, imagenes):
        tarjetas = [(f, imagenes[f.prefix]) for f in secciones.forms]
        for formulario, propias in tarjetas:
            propias.limite = SeccionPortada.IMAGENES_POR_TIPO.get(formulario.tipo_elegido)
        # Una tarjeta vacía por tipo: «Agregar sección» copia la del tipo elegido.
        plantillas = []
        for valor, nombre in SeccionPortada.TIPOS:
            if valor in SeccionPortada.FIJAS:
                continue
            vacia = secciones.form(
                prefix=secciones.add_prefix("__prefix__"),
                initial={"tipo": valor},
                empty_permitted=True,
                use_required_attribute=False,
            )
            propias = ImagenesDeSeccionFormSet(
                instance=SeccionPortada(tipo=valor), prefix=f"{vacia.prefix}-img"
            )
            propias.limite = SeccionPortada.IMAGENES_POR_TIPO.get(valor)
            plantillas.append((valor, nombre, vacia, propias))
        return render(
            request,
            self.template_name,
            {
                "formularios": secciones,
                "tarjetas": tarjetas,
                "plantillas": plantillas,
            },
        )
