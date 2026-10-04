"""Las pantallas de los catálogos de clasificación.

Cuatro pantallas por catálogo, iguales para los cinco (R-17-002):

- **El listado** (`CO-211`, `CO-212`, `CO-213`, `CO-164`, `CO-165`), con los
  activos y los dados de baja y filtro por estado. Es el punto de partida de
  las otras tres.
- **El alta**, que nace activa.
- **La modificación**, que corrige y reactiva, y nunca da de baja.
- **La baja**: el `GET` es la solicitud con su informe y el `POST` es la
  confirmación. Volver sin confirmar es `cancelarOperacion` (`CO-156`): no
  cambia nada ni se audita.

Exclusivas del Administrador, validado del lado del servidor (RNF-03).
"""

from django.contrib import messages
from django.db import IntegrityError, transaction
from django.db.models import Count
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views import View
from django.views.generic import CreateView, DetailView, ListView, UpdateView

from apps.catalog import catalogos
from apps.catalog.forms import (
    EditorialForm,
    EtiquetaForm,
    FormatoForm,
    GrupoEtiquetaForm,
    TipoForm,
)
from apps.catalog.models import Etiqueta, GrupoEtiqueta
from apps.catalog.views import CatalogoAdminMixin
from apps.core.utils import obtener_ip

ACTIVOS = "activos"
INACTIVOS = "inactivos"
ESTADOS = [("", "Todos"), (ACTIVOS, "Activos"), (INACTIVOS, "Dados de baja")]

# `CO-165` dice «paginado» sin decir cuánto: se toma el de `CO-205`.
ETIQUETAS_POR_PAGINA = 50


class CatalogoMixin(CatalogoAdminMixin):
    """Lo que las cuatro pantallas de un catálogo comparten."""

    catalogo = None

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        contexto["catalogo"] = self.catalogo
        return contexto


def _filtrar_por_estado(consulta, catalogo, estado):
    if estado == ACTIVOS:
        return consulta.filter(**{catalogo.campo_estado: True})
    if estado == INACTIVOS:
        return consulta.filter(**{catalogo.campo_estado: False})
    return consulta


class CatalogoListaView(CatalogoMixin, ListView):
    """La consulta: activos e inactivos, con filtro por estado."""

    template_name = "catalog/catalogo_lista.html"
    context_object_name = "registros"
    descripcion = ""

    @property
    def estado(self):
        estado = self.request.GET.get("estado", "")
        return estado if estado in (ACTIVOS, INACTIVOS) else ""

    def get_queryset(self):
        return _filtrar_por_estado(self.catalogo.listado(), self.catalogo, self.estado)

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        contexto.update(
            {
                "estado": self.estado,
                "estados": ESTADOS,
                "total": self.catalogo.modelo.objects.count(),
                "descripcion": self.descripcion,
                "plantilla_filas": f"catalog/_filas_{self.catalogo.clave}.html",
            }
        )
        return contexto


class CatalogoFormularioMixin(CatalogoMixin):
    """Alta y modificación: guardar con su auditoría y volver al listado."""

    template_name = "catalog/catalogo_formulario.html"
    titulo = ""
    descripcion = ""
    campos_auditados = (("nombre", "nombre"),)
    relaciones = ()

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        formulario = contexto["form"]
        contexto.update(
            {
                "titulo": self.titulo,
                "descripcion": self.descripcion,
                "volver_a": self.url_de_vuelta(),
                "colision": formulario.colision,
                "colision_activa": (
                    self.catalogo.esta_activo(formulario.colision) if formulario.colision else False
                ),
                "colision_url": (
                    self.catalogo.url_editar(formulario.colision) if formulario.colision else ""
                ),
            }
        )
        return contexto

    def url_de_vuelta(self):
        return self.catalogo.url_lista(getattr(self, "object", None))

    def despues_de_guardar(self, formulario, objeto):
        """Lo que alguna pantalla guarda además del registro. Casi siempre nada."""

    def form_valid(self, form):
        try:
            with transaction.atomic():
                self.object = self.guardar(form)
                self.despues_de_guardar(form, self.object)
        except IntegrityError:
            # Dos envíos del mismo nombre a la vez (un doble clic): los dos pasan
            # la validación del formulario y el segundo choca contra la unicidad
            # de la base. Se le avisa lo mismo que habría dicho el formulario un
            # instante después, en vez de un error 500 (B-17-016).
            if "nombre" not in form.cleaned_data or not hasattr(form, "mensaje_repetido"):
                raise
            nombre = form.cleaned_data["nombre"]
            # La misma pantalla que la validación normal: el aviso con el enlace al
            # registro que ganó la carrera.
            form.colision = self.catalogo.modelo.objects.filter(nombre__iexact=nombre).first()
            form.add_error("nombre", form.mensaje_repetido.format(nombre=nombre))
            return self.form_invalid(form)
        messages.success(self.request, self.mensaje(self.object))
        return redirect(self.catalogo.url_lista(self.object))


class CatalogoAltaView(CatalogoFormularioMixin, CreateView):
    def guardar(self, formulario):
        return catalogos.registrar(
            formulario,
            catalogo=self.catalogo,
            actor=self.request.user,
            ip=obtener_ip(self.request),
            campos_auditados=self.campos_auditados[1:],
            relaciones=self.relaciones,
        )

    def mensaje(self, objeto):
        return f"Se dio de alta {self.catalogo.articulo} {self.catalogo.singular} «{objeto}»."


class CatalogoEdicionView(CatalogoFormularioMixin, UpdateView):
    def guardar(self, formulario):
        self.reactivado = bool(formulario.cleaned_data.get("reactivar"))
        return catalogos.editar(
            formulario,
            catalogo=self.catalogo,
            actor=self.request.user,
            ip=obtener_ip(self.request),
            campos_auditados=self.campos_auditados,
            relaciones=self.relaciones,
        )

    def mensaje(self, objeto):
        if self.reactivado:
            return f"Se reactivó «{objeto}»: vuelve a ofrecerse en los formularios."
        return f"Se guardaron los cambios de «{objeto}»."

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        contexto["puede_dar_de_baja"] = self.catalogo.esta_activo(self.object)
        return contexto


class CatalogoBajaView(CatalogoMixin, DetailView):
    """La baja en dos tiempos: el informe primero, la confirmación después."""

    template_name = "catalog/catalogo_baja.html"
    context_object_name = "registro"
    consecuencia = ""

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        if not self.catalogo.esta_activo(self.object):
            # La precondición de la solicitud: ya está dado de baja.
            messages.info(request, f"«{self.object}» ya estaba dado de baja.")
            return redirect(self.catalogo.url_lista(self.object))
        return self.render_to_response(self.get_context_data(object=self.object))

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        contexto["informe"] = self.catalogo.informe(self.object)
        contexto["consecuencia"] = self.consecuencia
        contexto["volver_a"] = self.catalogo.url_lista(self.object)
        return contexto

    def post(self, request, *args, **kwargs):
        registro = self.get_object()
        dado_de_baja = catalogos.confirmar_baja(
            registro, catalogo=self.catalogo, actor=request.user, ip=obtener_ip(request)
        )
        if dado_de_baja:
            messages.success(
                request,
                f"Se dio de baja «{registro}». Deja de ofrecerse en los formularios y "
                "conserva lo que ya lo usa.",
            )
        else:
            messages.info(request, f"«{registro}» ya estaba dado de baja.")
        return redirect(self.catalogo.url_lista(registro))


# ---------------------------------------------------------------------------
# Editoriales — CU-CFG-EDC, EDA, EDM, EDB
# ---------------------------------------------------------------------------


class EditorialListaView(CatalogoListaView):
    catalogo = catalogos.EDITORIALES
    descripcion = (
        "Quién publica el material editorial. La editorial entra en la identidad del "
        "producto y en la tabla de precios de referencia."
    )


class EditorialCrearView(CatalogoAltaView):
    catalogo = catalogos.EDITORIALES
    form_class = EditorialForm
    titulo = "Nueva editorial"
    descripcion = (
        "Nace activa y queda disponible en el alta de productos, de proveedores y en la "
        "tabla de precios."
    )


class EditorialEditarView(CatalogoEdicionView):
    catalogo = catalogos.EDITORIALES
    model = catalogos.EDITORIALES.modelo
    form_class = EditorialForm
    titulo = "Modificar editorial"
    descripcion = "Los productos, proveedores y precios que la usan muestran el nombre corregido."


class EditorialBajaView(CatalogoBajaView):
    catalogo = catalogos.EDITORIALES
    model = catalogos.EDITORIALES.modelo
    consecuencia = (
        "Deja de ofrecerse en los formularios. Los productos, los proveedores y las filas "
        "de precio que la usan la conservan. Un borrador que la herede de su proveedor no "
        "se podrá confirmar hasta cambiarla o reactivarla."
    )


# ---------------------------------------------------------------------------
# Tipos de material — CU-CFG-TPC, TPA, TPM, TPB
# ---------------------------------------------------------------------------


class TipoFormularioMixin:
    """El tipo guarda además sus formatos declarados (`CO-146`)."""

    campos_auditados = (
        ("nombre", "nombre"),
        ("clase", "rubro"),
        ("usa_formato", "se clasifica por formato"),
    )

    def despues_de_guardar(self, formulario, tipo):
        catalogos.declarar_formatos(
            tipo,
            formulario.formatos_elegidos(),
            actor=self.request.user,
            ip=obtener_ip(self.request),
        )


class TipoListaView(CatalogoListaView):
    catalogo = catalogos.TIPOS
    descripcion = (
        "Qué clase de material es. Un solo catálogo para los dos rubros: lo que distingue "
        "un tipo editorial de uno no editorial es el rubro."
    )


class TipoCrearView(TipoFormularioMixin, CatalogoAltaView):
    catalogo = catalogos.TIPOS
    form_class = TipoForm
    titulo = "Nuevo tipo de material"
    descripcion = (
        "Un tipo que se clasifica por formato pide el tamaño del tomo y toma su precio de "
        "la tabla de referencia. Uno que no, lleva el precio en el alta."
    )


class TipoEditarView(TipoFormularioMixin, CatalogoEdicionView):
    catalogo = catalogos.TIPOS
    model = catalogos.TIPOS.modelo
    form_class = TipoForm
    titulo = "Modificar tipo de material"
    descripcion = (
        "Ningún cambio puede dejar un producto o una fila de precio con una clasificación "
        "que el tipo ya no admite."
    )


class TipoBajaView(CatalogoBajaView):
    catalogo = catalogos.TIPOS
    model = catalogos.TIPOS.modelo
    consecuencia = (
        "Deja de ofrecerse en los formularios de alta. Los productos, las filas de precio, "
        "los formatos y los proveedores que lo usan lo conservan. Un borrador que lo herede "
        "de su proveedor no se podrá confirmar hasta cambiarlo o reactivarlo."
    )


# ---------------------------------------------------------------------------
# Formatos — CU-CFG-FMC, FMA, FMM, FMB
# ---------------------------------------------------------------------------


class FormatoFormularioMixin:
    campos_auditados = (
        ("nombre", "nombre"),
        ("descripcion", "medidas"),
        ("aplica_a_todos", "aplica a todos los tipos"),
    )
    relaciones = (("tipos", "tipos"),)


class FormatoListaView(CatalogoListaView):
    catalogo = catalogos.FORMATOS
    descripcion = (
        "El tamaño físico del tomo. El catálogo es compartido entre editoriales: lo que "
        "varía por editorial es el precio."
    )


class FormatoCrearView(FormatoFormularioMixin, CatalogoAltaView):
    catalogo = catalogos.FORMATOS
    form_class = FormatoForm
    titulo = "Nuevo formato"
    descripcion = (
        "Se ofrece en todos los tipos que se clasifican por formato, o sólo en los que se declaren."
    )


class FormatoEditarView(FormatoFormularioMixin, CatalogoEdicionView):
    catalogo = catalogos.FORMATOS
    model = catalogos.FORMATOS.modelo
    form_class = FormatoForm
    titulo = "Modificar formato"
    descripcion = "Ninguna combinación de tipo y formato en uso puede quedar sin declarar."


class FormatoBajaView(CatalogoBajaView):
    catalogo = catalogos.FORMATOS
    model = catalogos.FORMATOS.modelo
    consecuencia = (
        "Deja de ofrecerse en los formularios. Los productos, las filas de precio y los "
        "tipos que lo declaran lo conservan. Un borrador con este formato no se podrá "
        "confirmar hasta cambiarlo o reactivarlo."
    )


# ---------------------------------------------------------------------------
# Grupos de etiquetas — CU-CAT-GRC, GRA, GRM, GRB
# ---------------------------------------------------------------------------


class GrupoListaView(CatalogoListaView):
    catalogo = catalogos.GRUPOS
    descripcion = (
        "Cada grupo es una faceta de búsqueda —franquicia, género, colección— y sus "
        "etiquetas son los valores. Un producto puede tener varias etiquetas."
    )


class GrupoCrearView(CatalogoAltaView):
    catalogo = catalogos.GRUPOS
    form_class = GrupoEtiquetaForm
    titulo = "Nuevo grupo de etiquetas"
    descripcion = (
        "El eje en el que describe una etiqueta. Cada grupo es un filtro aparte: sin ellos, "
        "franquicias y géneros quedarían mezclados en una sola caja."
    )


class GrupoEditarView(CatalogoEdicionView):
    catalogo = catalogos.GRUPOS
    model = catalogos.GRUPOS.modelo
    form_class = GrupoEtiquetaForm
    titulo = "Modificar grupo de etiquetas"
    descripcion = (
        "Reactivar el grupo no reactiva sus etiquetas: cada una conserva su propio estado."
    )


class GrupoBajaView(CatalogoBajaView):
    catalogo = catalogos.GRUPOS
    model = catalogos.GRUPOS.modelo
    consecuencia = (
        "El grupo y todas sus etiquetas dejan de ofrecerse en los formularios. Los productos "
        "conservan sus etiquetas. Reactivar el grupo después no reactiva las etiquetas."
    )


# ---------------------------------------------------------------------------
# Etiquetas — CU-CAT-ETC, ETA, ETM, ETB
# ---------------------------------------------------------------------------


class EtiquetasDeGrupoView(CatalogoMixin, ListView):
    """`CO-165`: las etiquetas de un grupo, paginadas, con búsqueda y estado.

    Las etiquetas son el único catálogo abierto: crecen sin techo y se operan
    buscando, no recorriendo.
    """

    catalogo = catalogos.ETIQUETAS
    template_name = "catalog/etiqueta_lista.html"
    context_object_name = "registros"
    paginate_by = ETIQUETAS_POR_PAGINA

    def dispatch(self, request, *args, **kwargs):
        self.grupo = get_object_or_404(GrupoEtiqueta, pk=kwargs["pk"])
        return super().dispatch(request, *args, **kwargs)

    @property
    def estado(self):
        estado = self.request.GET.get("estado", "")
        return estado if estado in (ACTIVOS, INACTIVOS) else ""

    @property
    def busqueda(self):
        return self.request.GET.get("q", "").strip()

    def get_queryset(self):
        etiquetas = Etiqueta.objects.filter(grupo=self.grupo).annotate(
            cantidad_productos=Count("productos")
        )
        if self.busqueda:
            etiquetas = etiquetas.filter(nombre__icontains=self.busqueda)
        return _filtrar_por_estado(etiquetas, self.catalogo, self.estado).order_by("nombre")

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        contexto.update(
            {
                "grupo": self.grupo,
                "estado": self.estado,
                "estados": ESTADOS,
                "busqueda": self.busqueda,
                "total": self.grupo.etiquetas.count(),
            }
        )
        return contexto


class EtiquetaCrearView(CatalogoAltaView):
    catalogo = catalogos.ETIQUETAS
    form_class = EtiquetaForm
    titulo = "Nueva etiqueta"
    descripcion = (
        "Describe el producto pero no lo identifica ni fija su precio: si algo decide algo, "
        "es un campo, no una etiqueta."
    )
    campos_auditados = (("nombre", "nombre"), ("grupo__nombre", "grupo"))

    def get_initial(self):
        inicial = super().get_initial()
        grupo = self.request.GET.get("grupo")
        if grupo and grupo.isdigit():
            inicial["grupo"] = int(grupo)
        return inicial

    def url_de_vuelta(self):
        grupo = self.get_initial().get("grupo")
        if grupo:
            return reverse("catalog:grupo_etiquetas", args=[grupo])
        return self.catalogo.url_lista()


class EtiquetaEditarView(CatalogoEdicionView):
    catalogo = catalogos.ETIQUETAS
    model = catalogos.ETIQUETAS.modelo
    form_class = EtiquetaForm
    titulo = "Modificar etiqueta"
    descripcion = (
        "Los productos que la tienen la conservan. Moverla a otro grupo cambia el filtro "
        "bajo el cual se ofrece."
    )
    campos_auditados = (("nombre", "nombre"), ("grupo__nombre", "grupo"))


class EtiquetaBajaView(CatalogoBajaView):
    catalogo = catalogos.ETIQUETAS
    model = catalogos.ETIQUETAS.modelo
    consecuencia = (
        "Deja de ofrecerse en los formularios de producto. Los productos que la tienen la "
        "conservan, y en su edición aparece marcada para poder quitarla."
    )


class EtiquetaRapidaView(CatalogoAdminMixin, View):
    """Alta de una etiqueta —y de su grupo, si es nuevo— sin salir del alta (B-02-005).

    `GET` devuelve los grupos activos para el diálogo. `POST` crea con los
    mismos formularios y la misma auditoría que las pantallas de grupos y
    etiquetas (`CO-038`, `CO-042`): el atajo no puede ser más laxo que ellas.
    Si la etiqueta no se puede crear, tampoco queda creado el grupo.
    """

    def get(self, request):
        grupos = GrupoEtiqueta.objects.filter(activo=True).order_by("nombre")
        return JsonResponse({"grupos": [{"id": g.pk, "nombre": g.nombre} for g in grupos]})

    def post(self, request):
        ip = obtener_ip(request)
        with transaction.atomic():
            datos = request.POST.copy()
            if datos.get("grupo") == "nuevo":
                grupo_form = GrupoEtiquetaForm({"nombre": datos.get("grupo_nuevo", "")})
                if not grupo_form.is_valid():
                    return JsonResponse(
                        {"errores": {"grupo_nuevo": grupo_form.errors.get("nombre", [])}},
                        status=400,
                    )
                grupo = catalogos.registrar(
                    grupo_form, catalogo=catalogos.GRUPOS, actor=request.user, ip=ip
                )
                datos["grupo"] = str(grupo.pk)

            formulario = EtiquetaForm(datos)
            if not formulario.is_valid():
                transaction.set_rollback(True)
                return JsonResponse({"errores": formulario.errors}, status=400)
            etiqueta = catalogos.registrar(
                formulario,
                catalogo=catalogos.ETIQUETAS,
                actor=request.user,
                ip=ip,
                campos_auditados=(("grupo__nombre", "grupo"),),
            )
        return JsonResponse(
            {
                "id": etiqueta.pk,
                "nombre": etiqueta.nombre,
                "grupo": etiqueta.grupo.nombre,
                "texto": str(etiqueta),
            }
        )
