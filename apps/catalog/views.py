"""Pantallas del catálogo: alta de lotes editoriales e inventario.

Todas son de backoffice y exclusivas del Administrador, validado del lado del
servidor (RNF-03). El sistema visual que les corresponde es el **modo
operativo**: ninguna pantalla de este módulo es pública.
"""

from django.contrib import messages
from django.db import transaction
from django.db.models import Count, Q
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import CreateView, DetailView, ListView, UpdateView

from apps.accounts.models import Usuario
from apps.catalog import services
from apps.catalog.forms import (
    CabeceraLoteForm,
    CabeceraLoteImportadoForm,
    ConfiguracionForm,
    EditorialForm,
    EtiquetaForm,
    FormatoForm,
    GrupoEtiquetaForm,
    PrecioReferenciaForm,
    TipoForm,
    formatos_para,
    formset_de_items,
)
from apps.catalog.models import (
    Editorial,
    Etiqueta,
    Formato,
    GrupoEtiqueta,
    LoteAlta,
    Producto,
    TablaPrecioReferencia,
    Tipo,
)
from apps.core import cotizaciones
from apps.core.mixins import RolRequeridoMixin
from apps.core.models import ConfiguracionSistema, RegistroAuditoria
from apps.core.utils import obtener_ip


class CatalogoAdminMixin(RolRequeridoMixin):
    """El alta de productos es exclusiva del Administrador en los dos CU."""

    roles_permitidos = (Usuario.ADMINISTRADOR,)


class AltaLoteView(CatalogoAdminMixin, View):
    """Base compartida por el alta nacional y la importada.

    Las dos pantallas hacen lo mismo —cabecera opcional, formset de ítems,
    alta atómica y resumen— y se diferencian en qué cabecera piden y cómo sale
    el precio de cada ítem. Eso vive en los formularios; acá queda solo el
    orden en que se arman.

    El punto que importa es la secuencia del POST: la cabecera se valida
    **antes** de construir el formset, porque cada ítem necesita saber qué le
    aporta la cabecera para decidir qué campos son obligatorios en él.
    """

    origen = LoteAlta.NACIONAL
    cabecera_form_class = CabeceraLoteForm
    template_name = "catalog/lote_formulario.html"
    titulo = "Nuevo lote nacional"

    def get(self, request):
        self._avisar_si_falta_configuracion(request)
        cabecera = self.cabecera_form_class()
        return self._render(request, cabecera, self._formset(cabecera))

    def post(self, request):
        cabecera = self.cabecera_form_class(request.POST)
        # Puebla `cleaned_data` aunque haya errores: los ítems trabajan con lo
        # que la cabecera sí aportó y no reclaman de más.
        cabecera_valida = cabecera.is_valid()
        formset = self._formset(cabecera, request.POST, request.FILES)

        if not (cabecera_valida and formset.is_valid()):
            return self._render(request, cabecera, formset)

        lote = cabecera.lote()
        if formset.hay_items_desbloqueados:
            # Algún ítem se apartó de la clasificación de la cabecera, así que
            # la cabecera ya no describe al lote. Se la vacía en vez de dejarla
            # puesta: si no, el resumen y la auditoría dirían que todo el lote
            # es de una editorial cuando no lo es.
            lote.editorial = None
            lote.tipo = None
            lote.formato = None

        resultado = services.registrar_lote(
            lote=lote,
            items=formset.datos_de_los_productos(cabecera.etiquetas_del_lote()),
            actor=request.user,
            ip=obtener_ip(request),
        )
        return redirect("catalog:lote_resumen", pk=resultado.lote.pk)

    # ------------------------------------------------------------------

    def _formset(self, cabecera, *args):
        return formset_de_items(self.origen)(*args, form_kwargs=self._form_kwargs(cabecera))

    def _form_kwargs(self, cabecera):
        """Lo que cada ítem necesita saber del lote para validarse y calcularse."""
        return {"cabecera": getattr(cabecera, "cleaned_data", {})}

    def _contexto(self, cabecera, formset):
        return {
            "cabecera": cabecera,
            "formset": formset,
            "titulo": self.titulo,
            "origen": self.origen,
            "es_importado": self.origen == LoteAlta.IMPORTADO,
            # Qué muestra cada tipo viaja a la pantalla como dato: la misma
            # bandera y los mismos formatos que valida el servidor, así los dos
            # lados no pueden discrepar. `formatos` lista los que aplican —los
            # universales incluidos— para que el desplegable se recorte al
            # elegir el tipo en vez de ofrecer los quince del catálogo.
            "reglas_de_tipo": {
                str(tipo.pk): {
                    "nombre": tipo.nombre,
                    "usa_formato": tipo.usa_formato,
                    "formatos": [str(formato.pk) for formato in formatos_para(tipo)],
                }
                for tipo in Tipo.objects.filter(activo=True)
            },
        }

    def _render(self, request, cabecera, formset):
        return render(request, self.template_name, self._contexto(cabecera, formset))

    def _avisar_si_falta_configuracion(self, request):
        """Avisa cuando todavía no hay con qué dar de alta un producto.

        Sin editoriales ni tipos cargados la pantalla aparecería con los
        desplegables vacíos y sin explicar por qué, que es la peor forma de
        descubrir que falta configurar algo.
        """
        faltan = []
        if not Editorial.objects.filter(activa=True).exists():
            faltan.append("editoriales")
        if not Tipo.objects.filter(activo=True).exists():
            faltan.append("tipos de material")
        if not faltan:
            return
        messages.info(
            request,
            f"Todavía no hay {' ni '.join(faltan)} cargados. Se administran desde "
            "Parámetros globales.",
        )


class AltaLoteNacionalView(AltaLoteView):
    """Alta de lote de material editorial nacional."""


class AltaLoteImportadoView(AltaLoteView):
    """Alta de lote de material editorial importado."""

    origen = LoteAlta.IMPORTADO
    cabecera_form_class = CabeceraLoteImportadoForm
    titulo = "Nuevo lote importado"

    def _form_kwargs(self, cabecera):
        kwargs = super()._form_kwargs(cabecera)
        # El CRE sale de la calculadora de envío del lote y el margen de los
        # parámetros globales: ninguno de los dos es dato del ítem, pero los dos
        # entran en su cálculo. Se pasan como argumentos y no se leen desde el
        # formulario del ítem para que el precio de un ítem no dependa de otro.
        kwargs.update(
            cre=cabecera.cre_calculado,
            margen=ConfiguracionSistema.obtener().margen_ganancia,
            cotizacion=cabecera.cotizacion_aplicada,
        )
        return kwargs

    def _contexto(self, cabecera, formset):
        contexto = super()._contexto(cabecera, formset)
        # La pantalla muestra el margen vigente: el Administrador tiene que
        # poder ver con qué número se está calculando antes de confirmar.
        contexto["margen"] = ConfiguracionSistema.obtener().margen_ganancia
        contexto["cre"] = cabecera.cre_calculado
        contexto["cotizaciones"] = cabecera.referencia_de_cotizaciones
        contexto["moneda_local"] = cotizaciones.MONEDA_LOCAL
        return contexto


class PrecioDeReferenciaView(CatalogoAdminMixin, View):
    """El PVP de una combinación editorial + tipo + formato.

    La pantalla de alta pre-completa el precio al elegir esos tres campos. Sin
    esta consulta el pre-completado solo ocurriría al guardar, y el
    Administrador cargaría el lote entero sin ver un precio: cuando apareciera
    el error, ya habría escrito veinte ítems.

    Devuelve el precio como texto y no como número: en JSON un decimal viaja
    como coma flotante, y de este lado hay dinero.
    """

    def get(self, request):
        referencia = services.precio_de_referencia(
            Editorial.objects.filter(pk=_entero(request.GET.get("editorial"))).first(),
            Tipo.objects.filter(pk=_entero(request.GET.get("tipo"))).first(),
            Formato.objects.filter(pk=_entero(request.GET.get("formato"))).first(),
        )
        return JsonResponse({"pvp": str(referencia.pvp) if referencia else None})


class CatalogoRapidoView(CatalogoAdminMixin, View):
    """Alta de un catálogo de clasificación sin salir de la pantalla de carga.

    Existe porque el caso real es llegar con un tomo de una editorial —o de una
    franquicia— que todavía no está cargada: obligar a abandonar el lote a medio
    escribir para ir a otra pantalla es la clase de fricción que termina en un
    lote cargado con la editorial equivocada "para no perder lo escrito".

    La normalización y el chequeo de repetidos los hace el **mismo formulario**
    que usa la pantalla de parámetros: no hay dos caminos con reglas distintas
    para crear lo mismo. Si el atajo fuera más laxo, sería justamente la puerta
    de entrada de los duplicados que el formulario existe para evitar.

    **Las etiquetas no lo usan, y no es un olvido.** Este atajo agrega una
    opción a un `<select>`, y las etiquetas se dibujan como casillas agrupadas:
    hacerlo andar para las dos formas sería bastante más código del que ahorra.
    Además el caso es menos frecuente — un género se carga una vez y sirve para
    siempre, mientras que una editorial nueva aparece con cada lote.
    """

    form_class = None
    etiqueta = ""

    def post(self, request):
        formulario = self.form_class(request.POST)
        if not formulario.is_valid():
            return JsonResponse({"errores": formulario.errors.get("nombre", [])}, status=400)

        creado = formulario.save()
        RegistroAuditoria.registrar(
            accion=RegistroAuditoria.PARAMETRO_MODIFICADO,
            actor=request.user,
            objetivo=creado,
            ip=obtener_ip(request),
            detalle=(f"alta rápida de {self.etiqueta} «{creado.nombre}» desde la carga de un lote"),
        )
        return JsonResponse({"id": creado.pk, "nombre": creado.nombre})


class EditorialRapidaView(CatalogoRapidoView):
    form_class = EditorialForm
    etiqueta = "editorial"


def _entero(valor):
    """El parámetro convertido, o `None` si vino cualquier cosa."""
    try:
        return int(valor)
    except (TypeError, ValueError):
        return None


# ---------------------------------------------------------------------------
# Parámetros globales
# ---------------------------------------------------------------------------


class ParametrosView(CatalogoAdminMixin, View):
    """Todo lo que el negocio ajusta sin tocar código, en una sola pantalla.

    Están juntos porque se consultan juntos: para entender por qué un tomo
    salió a un precio hay que ver la tabla, el tipo, el formato y el margen, y
    tenerlos en cuatro pantallas distintas obliga a ir y volver.

    El alta y la edición de cada cosa van en pantallas aparte —y no en línea—
    porque cada una tiene sus propias validaciones y sus propios errores, y
    resolverlas todas en un mismo formulario haría que un error en el margen
    borrara lo que se estaba escribiendo en la tabla de precios.
    """

    template_name = "catalog/parametros.html"

    def get(self, request, formulario=None):
        return render(request, self.template_name, self._contexto(request, formulario))

    def post(self, request):
        configuracion = ConfiguracionSistema.obtener()
        anterior = (configuracion.margen_ganancia, configuracion.stock_inicial_por_defecto)
        formulario = ConfiguracionForm(request.POST, instance=configuracion)

        if not formulario.is_valid():
            return self.get(request, formulario=formulario)

        with transaction.atomic():
            configuracion = formulario.save(commit=False)
            configuracion.actualizado_por = request.user
            configuracion.save()
            RegistroAuditoria.registrar(
                accion=RegistroAuditoria.PARAMETRO_MODIFICADO,
                actor=request.user,
                objetivo=configuracion,
                ip=obtener_ip(request),
                detalle=(
                    f"margen: {anterior[0]} → {configuracion.margen_ganancia}; "
                    f"stock por defecto: {anterior[1]} → "
                    f"{configuracion.stock_inicial_por_defecto}"
                ),
            )

        messages.success(
            request,
            "Se actualizaron los parámetros. El margen nuevo rige para las altas de "
            "importados que se hagan de ahora en adelante; los productos ya cargados "
            "conservan el margen con el que se dieron de alta.",
        )
        return redirect("catalog:parametros")

    def _contexto(self, request, formulario):
        precios_de_referencia = TablaPrecioReferencia.objects.select_related(
            "editorial", "tipo", "formato"
        )

        editorial = _entero(request.GET.get("editorial"))
        if editorial:
            precios_de_referencia = precios_de_referencia.filter(editorial_id=editorial)

        return {
            "configuracion": ConfiguracionSistema.obtener(),
            "form": formulario or ConfiguracionForm(instance=ConfiguracionSistema.obtener()),
            "tipos": Tipo.objects.all(),
            "formatos": Formato.objects.all(),
            "editoriales": Editorial.objects.annotate(
                cantidad_precios=Count("precios_de_referencia")
            ),
            "grupos": GrupoEtiqueta.objects.annotate(cantidad_etiquetas=Count("etiquetas")),
            "etiquetas": Etiqueta.objects.select_related("grupo").annotate(
                cantidad_productos=Count("productos")
            ),
            "precios": precios_de_referencia,
            "editorial_elegida": editorial or "",
        }


class ParametroFormularioMixin(CatalogoAdminMixin):
    """Alta y edición de cualquiera de los catálogos de parámetros.

    Los cinco formularios se comportan igual —guardar, auditar y volver— así
    que comparten la vista y la plantilla. Lo único que cambia es el modelo, el
    formulario y el título, que es exactamente lo que declara cada subclase.
    """

    template_name = "catalog/parametro_formulario.html"
    success_url = reverse_lazy("catalog:parametros")
    titulo = ""
    descripcion = ""

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        contexto["titulo"] = self.titulo
        contexto["descripcion"] = self.descripcion
        return contexto

    def form_valid(self, form):
        with transaction.atomic():
            respuesta = super().form_valid(form)
            RegistroAuditoria.registrar(
                accion=RegistroAuditoria.PARAMETRO_MODIFICADO,
                actor=self.request.user,
                objetivo=self.object,
                ip=obtener_ip(self.request),
                detalle=f"{self.object._meta.verbose_name}: «{self.object}»",
            )
        messages.success(self.request, f"Se guardó «{self.object}».")
        return respuesta


class EditorialCrearView(ParametroFormularioMixin, CreateView):
    model = Editorial
    form_class = EditorialForm
    titulo = "Nueva editorial"
    descripcion = "Quién publica el material. Cada una tiene su propia tabla de precios."


class EditorialEditarView(ParametroFormularioMixin, UpdateView):
    model = Editorial
    form_class = EditorialForm
    titulo = "Editar editorial"
    descripcion = (
        "Desactivarla la saca de los desplegables de alta, pero conserva sus productos "
        "y su historial."
    )


class GrupoEtiquetaCrearView(ParametroFormularioMixin, CreateView):
    model = GrupoEtiqueta
    form_class = GrupoEtiquetaForm
    titulo = "Nuevo grupo de etiquetas"
    descripcion = (
        "El eje en el que describe una etiqueta. Cada grupo es un filtro aparte en la "
        "tienda: sin ellos, franquicias y géneros quedarían mezclados en una sola caja."
    )


class GrupoEtiquetaEditarView(ParametroFormularioMixin, UpdateView):
    model = GrupoEtiqueta
    form_class = GrupoEtiquetaForm
    titulo = "Editar grupo de etiquetas"
    descripcion = "Desactivarlo saca del alta a todas sus etiquetas, sin perder ninguna."


class EtiquetaCrearView(ParametroFormularioMixin, CreateView):
    model = Etiqueta
    form_class = EtiquetaForm
    titulo = "Nueva etiqueta"
    descripcion = (
        "Describe el producto pero no lo identifica ni fija su precio: si algo decide "
        "algo, es un campo, no una etiqueta."
    )


class EtiquetaEditarView(ParametroFormularioMixin, UpdateView):
    model = Etiqueta
    form_class = EtiquetaForm
    titulo = "Editar etiqueta"
    descripcion = (
        "Desactivarla la saca de los desplegables de alta, pero conserva sus productos "
        "y su historial."
    )


class TipoCrearView(ParametroFormularioMixin, CreateView):
    model = Tipo
    form_class = TipoForm
    titulo = "Nuevo tipo de material"
    descripcion = "Las dos banderas deciden qué campos muestra el alta de un producto de este tipo."


class TipoEditarView(ParametroFormularioMixin, UpdateView):
    model = Tipo
    form_class = TipoForm
    titulo = "Editar tipo de material"
    descripcion = (
        "Quitarle el formato lo saca de la tabla de precios: sus productos pasan a "
        "cargarse con precio a mano."
    )


class FormatoCrearView(ParametroFormularioMixin, CreateView):
    model = Formato
    form_class = FormatoForm
    titulo = "Nuevo formato"
    descripcion = "El tamaño del tomo. El nombre es compartido; el precio cambia por editorial."


class FormatoEditarView(ParametroFormularioMixin, UpdateView):
    model = Formato
    form_class = FormatoForm
    titulo = "Editar formato"


class PrecioCrearView(ParametroFormularioMixin, CreateView):
    model = TablaPrecioReferencia
    form_class = PrecioReferenciaForm
    titulo = "Nuevo precio de referencia"
    descripcion = (
        "El precio de venta de una combinación de editorial, tipo y formato. Es el que "
        "se pre-completa al cargar un lote nacional."
    )


class PrecioEditarView(ParametroFormularioMixin, UpdateView):
    model = TablaPrecioReferencia
    form_class = PrecioReferenciaForm
    titulo = "Editar precio de referencia"
    descripcion = (
        "Cambiarlo acá no toca los productos ya cargados: la propagación automática "
        "es parte del módulo de Precios, todavía no implementado."
    )


class PrecioEliminarView(CatalogoAdminMixin, DetailView):
    """Baja de una fila de la tabla de precios.

    Es de las pocas eliminaciones reales del sistema, y se justifica porque una
    fila de precios no tiene historial propio: los productos ya cargados
    guardan su precio, y los que la referencian lo hacen con `SET_NULL`, así
    que ninguno se rompe ni pierde su valor al desaparecer la fila.
    """

    model = TablaPrecioReferencia
    template_name = "catalog/precio_eliminar.html"
    context_object_name = "precio"

    def post(self, request, *args, **kwargs):
        precio = self.get_object()
        descripcion = str(precio)

        with transaction.atomic():
            RegistroAuditoria.registrar(
                accion=RegistroAuditoria.PARAMETRO_MODIFICADO,
                actor=request.user,
                ip=obtener_ip(request),
                detalle=f"baja del precio de referencia «{descripcion}»",
            )
            precio.delete()

        messages.success(request, f"Se eliminó el precio de referencia «{descripcion}».")
        return redirect("catalog:parametros")


class LoteResumenView(CatalogoAdminMixin, DetailView):
    """El resumen del alta (CU-01 paso 9, CU-02 paso 11).

    Es una pantalla propia y no un mensaje flash porque tiene que poder
    enumerar cada colisión con enlace a la ficha del producto existente (E1), y
    porque así se puede volver a mirar: los rechazados quedan guardados en el
    lote, no en la sesión.
    """

    model = LoteAlta
    template_name = "catalog/lote_resumen.html"
    context_object_name = "lote"

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        lote = self.object

        # Una sola consulta para todos los productos con los que se chocó, en
        # vez de una por fila de la tabla de rechazados.
        claves = [
            rechazado["producto_existente"]
            for rechazado in lote.rechazados
            if rechazado.get("producto_existente")
        ]
        existentes = Producto.objects.in_bulk(claves)

        contexto["creados"] = lote.productos.select_related("editorial").prefetch_related(
            "etiquetas__grupo"
        )
        contexto["rechazados"] = [
            {**rechazado, "existente": existentes.get(rechazado.get("producto_existente"))}
            for rechazado in lote.rechazados
        ]
        contexto["con_precio_manual"] = lote.productos.filter(precio_manual=True)
        return contexto


class ProductoListaView(CatalogoAdminMixin, ListView):
    """Inventario interno, **solo para consultar**.

    No es un CU: es la contraparte de lectura del alta, igual que la tabla de
    Clientes lo es del registro público. Existe porque CU-01 E1 exige enlazar a
    la ficha del producto con el que se chocó, y porque después de cargar un
    lote hay que poder ver que quedó cargado.

    Editar y dar de baja un producto son CU-09 y CU-10 (Módulo 02): esta
    pantalla no ofrece ninguna acción hasta que esos CU se aborden.
    """

    context_object_name = "productos"
    paginate_by = 25

    def get_template_names(self):
        if self.request.GET.get("parcial"):
            return ["catalog/_tabla_productos.html"]
        return ["catalog/producto_lista.html"]

    def get_queryset(self):
        productos = Producto.objects.select_related("editorial", "tipo", "formato")

        busqueda = self.request.GET.get("q", "").strip()
        if busqueda:
            productos = productos.filter(
                Q(titulo__icontains=busqueda)
                | Q(autor__icontains=busqueda)
                | Q(editorial__nombre__icontains=busqueda)
            )

        # Los filtros se validan contra las opciones reales: un valor inventado
        # en la query string se ignora, no rompe ni filtra de más.
        estado = self.request.GET.get("estado", "")
        if estado in dict(Producto.ESTADO_CHOICES):
            productos = productos.filter(estado=estado)

        origen = self.request.GET.get("origen", "")
        if origen in dict(Producto.ORIGEN_CHOICES):
            productos = productos.filter(origen=origen)

        tipo = _entero(self.request.GET.get("tipo"))
        if tipo:
            productos = productos.filter(tipo_id=tipo)

        # Las etiquetas no identifican un producto, pero son la forma natural de
        # recortar el catálogo: "todo lo de Marvel" cruza editoriales y tipos, y
        # ninguno de los otros filtros junta eso.
        etiqueta = _entero(self.request.GET.get("etiqueta"))
        if etiqueta:
            productos = productos.filter(etiquetas=etiqueta)

        return productos.order_by("-creado_en")

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        estado = self.request.GET.get("estado", "")
        origen = self.request.GET.get("origen", "")
        contexto["busqueda"] = self.request.GET.get("q", "").strip()
        contexto["estado_elegido"] = estado if estado in dict(Producto.ESTADO_CHOICES) else ""
        contexto["origen_elegido"] = origen if origen in dict(Producto.ORIGEN_CHOICES) else ""
        contexto["tipo_elegido"] = _entero(self.request.GET.get("tipo")) or ""
        contexto["etiqueta_elegida"] = _entero(self.request.GET.get("etiqueta")) or ""
        contexto["estados"] = Producto.ESTADO_CHOICES
        contexto["origenes"] = Producto.ORIGEN_CHOICES
        contexto["tipos"] = Tipo.objects.all()
        # Solo las que tienen algo cargado: un desplegable con cuarenta etiquetas
        # de las que treinta no filtran nada no ayuda a filtrar. Se traen con su
        # grupo porque el desplegable las muestra agrupadas.
        contexto["etiquetas"] = (
            Etiqueta.objects.filter(productos__isnull=False).select_related("grupo").distinct()
        )
        contexto["resumen"] = self._resumen()
        return contexto

    def _resumen(self):
        """Las cifras del encabezado. Se calculan sobre el catálogo entero.

        A propósito no se filtran junto con la tabla: son el estado del
        inventario, no del recorte que se está mirando. Un solo `aggregate`
        para las cuatro, en vez de cuatro consultas.
        """
        return Producto.objects.aggregate(
            total=Count("pk"),
            activos=Count("pk", filter=Q(estado=Producto.ACTIVO)),
            pre_venta=Count("pk", filter=Q(estado=Producto.PRE_VENTA)),
            sin_stock=Count("pk", filter=Q(estado=Producto.ACTIVO, stock=0)),
        )


class ProductoDetalleView(CatalogoAdminMixin, DetailView):
    """Ficha del producto, solo lectura. Es el destino del enlace de E1."""

    model = Producto
    template_name = "catalog/producto_detalle.html"
    context_object_name = "producto"

    def get_queryset(self):
        return Producto.objects.select_related(
            "editorial", "tipo", "formato", "lote"
        ).prefetch_related("etiquetas__grupo")
