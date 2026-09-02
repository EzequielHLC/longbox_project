"""Pantallas del catálogo: alta de lotes editoriales e inventario.

Todas son de backoffice y exclusivas del Administrador, validado del lado del
servidor (RNF-03). El sistema visual que les corresponde es el **modo
operativo**: ninguna pantalla de este módulo es pública.
"""

from django.contrib import messages
from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from django.db.models import Count, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.views import View
from django.views.generic import CreateView, DetailView, ListView, UpdateView

from apps.accounts.models import Usuario
from apps.catalog import revisiones, services
from apps.catalog.forms import (
    BorradorForm,
    CabeceraLoteForm,
    CabeceraLoteImportadoForm,
    ConfiguracionForm,
    EditorialForm,
    EtiquetaForm,
    FormatoForm,
    GrupoEtiquetaForm,
    ModeloDeLenguajeForm,
    PrecioReferenciaForm,
    ProductoNoEditorialForm,
    RechazoDeBorradorForm,
    TipoForm,
    formatos_para,
    formset_de_items,
)
from apps.catalog.models import (
    NO_EDITORIAL,
    BorradorProducto,
    Editorial,
    Etiqueta,
    Formato,
    GrupoEtiqueta,
    LoteAlta,
    Producto,
    ProductoEditorial,
    ProductoNoEditorial,
    TablaPrecioReferencia,
    Tipo,
)
from apps.core import cotizaciones
from apps.core.mixins import RolRequeridoMixin
from apps.core.models import ConfiguracionSistema, RegistroAuditoria
from apps.core.utils import obtener_ip
from apps.suppliers.models import Proveedor

MENSAJE_BORRADOR_YA_RESUELTO = "Este borrador ya fue confirmado o rechazado."
MENSAJE_SIN_SESION = "No hay ninguna sesión de revisión en curso."
MENSAJE_CONFIANZA_SIN_REVISAR = (
    "Antes de confirmar hay que revisar los campos de confianza baja: {}."
)


class InventarioMixin(RolRequeridoMixin):
    """CU-11 — Consultar Inventario, el primer CU del proyecto con **dos actores**.

    El Administrador toma decisiones operativas y el Cajero responde consultas de
    mostrador; los dos necesitan ver el stock, y por eso la consulta no es
    exclusiva del Administrador como todo el resto de este archivo.

    Que sean dos actores no significa que vean lo mismo: el paso 6 del CU pide
    campos distintos según el rol, y eso se resuelve en la ficha, no acá. Este
    mixin decide **quién entra**; qué ve cada uno lo decide la vista.
    """

    roles_permitidos = (Usuario.ADMINISTRADOR, Usuario.CAJERO)


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


class ProductoNoEditorialAltaView(CatalogoAdminMixin, CreateView):
    """CU-08 — Registrar Alta de Producto No Editorial.

    Es de a uno y no por lote, a diferencia del alta editorial: cinco artículos
    no editoriales no comparten nada entre sí, mientras que veinte tomos de una
    serie comparten editorial, tipo y precio.

    **El duplicado avisa dos veces, y las dos hacen falta.** La pantalla consulta
    mientras se escribe el nombre —para no enterarse recién al guardar, con el
    formulario entero cargado— y el servidor exige la confirmación al guardar.
    La primera es comodidad; la segunda es el control. Es el mismo reparto que
    la confirmación del precio manual (A6 de `alta_editorial.md`).
    """

    model = ProductoNoEditorial
    form_class = ProductoNoEditorialForm
    template_name = "catalog/producto_no_editorial_formulario.html"

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        # El choque exacto, para poder enlazar la ficha existente al volver del
        # error. E2 del CU pide el enlace, no solo el aviso.
        contexto["duplicado"] = getattr(contexto["form"], "duplicado", None)
        contexto["hay_categorias"] = Tipo.objects.filter(activo=True, clase=NO_EDITORIAL).exists()
        return contexto

    def form_valid(self, form):
        with transaction.atomic():
            producto = form.save()
            RegistroAuditoria.registrar(
                RegistroAuditoria.ALTA_PRODUCTO_NO_EDITORIAL,
                actor=self.request.user,
                ip=obtener_ip(self.request),
                objetivo=producto,
                detalle=(
                    f"«{producto.titulo}» ({producto.tipo}) · código {producto.codigo} · "
                    f"${producto.precio} · stock inicial {producto.stock}"
                ),
            )

        self.object = producto
        messages.success(self.request, f"«{producto.titulo}» se agregó al catálogo.")
        # El paso 8 pide terminar mostrando la ficha del producto creado.
        return redirect("catalog:producto_detalle", pk=producto.pk)


class DuplicadosNoEditorialesView(CatalogoAdminMixin, View):
    """Lo que ya existe con un nombre parecido, mientras se escribe (CU-08 E2).

    Es la mitad cómoda de la advertencia de duplicado. Sin esto, el Administrador
    se entera de que estaba cargando algo repetido recién al apretar guardar, con
    el formulario entero escrito — el mismo problema que la consulta de precio de
    referencia ya resuelve del otro lado del módulo.

    **No valida nada.** Quien decide si el alta procede es el formulario, del
    lado del servidor: esta vista se puede esquivar, ignorar o no llegar nunca, y
    el duplicado se sigue informando igual al guardar.
    """

    def get(self, request):
        tipo = Tipo.objects.filter(pk=_entero(request.GET.get("tipo"))).first()
        titulo = request.GET.get("titulo", "")

        exacto = services.buscar_duplicado_no_editorial(titulo, tipo)
        parecidos = services.buscar_parecidos_no_editoriales(titulo, tipo)

        return JsonResponse(
            {
                "exacto": _resumen_de_producto(exacto) if exacto else None,
                "parecidos": [_resumen_de_producto(p) for p in parecidos],
            }
        )


def _resumen_de_producto(producto):
    """Lo mínimo para reconocerlo y poder ir a su ficha."""
    return {
        "titulo": producto.titulo,
        "categoria": str(producto.tipo),
        "codigo": producto.codigo,
        "url": reverse("catalog:producto_detalle", args=[producto.pk]),
    }


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

    def get(self, request, formulario=None, form_modelo=None):
        return render(request, self.template_name, self._contexto(request, formulario, form_modelo))

    def post(self, request):
        # Dos formularios en la misma pantalla, distinguidos por el botón que
        # los envía. Están separados porque se tocan por motivos distintos: el
        # margen lo cambia el negocio, el modelo de lenguaje lo cambia quien
        # despliega — y un error en uno no tiene por qué borrar lo escrito en
        # el otro.
        if "guardar_modelo" in request.POST:
            return self._guardar_modelo(request)
        return self._guardar_parametros(request)

    def _guardar_parametros(self, request):
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

    def _guardar_modelo(self, request):
        """A qué modelo de lenguaje le habla el sistema.

        **La clave no entra en la auditoría**, ni siquiera enmascarada: el log es
        inmutable y consultable, y un secreto que pasa por ahí queda ahí para
        siempre. Se registra **que** cambió, que es lo que hace falta saber
        cuando el pipeline deja de funcionar.
        """
        configuracion = ConfiguracionSistema.obtener()
        anterior = (
            configuracion.get_llm_modo_display(),
            configuracion.llm_url,
            configuracion.llm_modelo or "el que tenga cargado el servidor",
        )
        formulario = ModeloDeLenguajeForm(request.POST, instance=configuracion)

        if not formulario.is_valid():
            return self.get(request, form_modelo=formulario)

        with transaction.atomic():
            configuracion = formulario.save(commit=False)
            configuracion.actualizado_por = request.user
            configuracion.save()

            cambios = [
                f"modo: {anterior[0]} → {configuracion.get_llm_modo_display()}",
                f"dirección: {anterior[1]} → {configuracion.llm_url}",
                f"modelo: {anterior[2]} → "
                f"{configuracion.llm_modelo or 'el que tenga cargado el servidor'}",
            ]
            if formulario.cleaned_data.get("api_key"):
                cambios.append("se reemplazó la clave de la API")

            RegistroAuditoria.registrar(
                accion=RegistroAuditoria.PARAMETRO_MODIFICADO,
                actor=request.user,
                objetivo=configuracion,
                ip=obtener_ip(request),
                detalle="; ".join(cambios),
            )

        messages.success(
            request,
            "Se actualizó la configuración del modelo. Conviene verificarla en "
            "Proveedores → Diagnóstico del modelo antes de procesar un correo.",
        )
        return redirect("catalog:parametros")

    def _contexto(self, request, formulario, form_modelo=None):
        precios_de_referencia = TablaPrecioReferencia.objects.select_related(
            "editorial", "tipo", "formato"
        )

        editorial = _entero(request.GET.get("editorial"))
        if editorial:
            precios_de_referencia = precios_de_referencia.filter(editorial_id=editorial)

        return {
            "configuracion": ConfiguracionSistema.obtener(),
            "form": formulario or ConfiguracionForm(instance=ConfiguracionSistema.obtener()),
            "form_modelo": form_modelo
            or ModeloDeLenguajeForm(instance=ConfiguracionSistema.obtener()),
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

        contexto["creados"] = lote.productos.select_related("editorial", "tipo").prefetch_related(
            "etiquetas__grupo"
        )
        contexto["rechazados"] = [
            {**rechazado, "existente": existentes.get(rechazado.get("producto_existente"))}
            for rechazado in lote.rechazados
        ]
        contexto["con_precio_manual"] = lote.productos.filter(precio_manual=True)
        return contexto


class ProductoListaView(InventarioMixin, ListView):
    """CU-11 — Consultar Inventario.

    Nació como contraparte de lectura del alta en lote (A7 de
    `alta_editorial.md`), antes de que el Módulo 02 se abordara, y por eso
    heredaba dos cosas que su propio CU contradice: **estaba restringida al
    Administrador** —el Cajero es actor declarado— y **ordenaba por fecha de
    alta**, que es lo que sirve después de cargar un lote y no lo que pide el
    paso 2.

    Las dos quedaron resueltas sin perder el uso viejo: el orden es un parámetro
    con alfabético por defecto, así que quien viene de cargar un lote pide
    `?orden=recientes` y ve lo suyo.

    Editar y dar de baja son CU-09 y CU-10, todavía sin implementar.
    """

    # El paso 3 del CU: "disponibilidad de stock (Con stock / Sin stock /
    # Todos)". Van como constantes porque la vista y la plantilla tienen que
    # ofrecer exactamente los mismos valores.
    CON_STOCK = "con"
    SIN_STOCK = "sin"
    DISPONIBILIDADES = (  # noqa: RUF012
        (CON_STOCK, "Con stock"),
        (SIN_STOCK, "Sin stock"),
    )

    # El paso 2 pide orden alfabético; el uso que le da Alta Editorial pide lo
    # último cargado. Es un parámetro, con el del CU por defecto.
    ORDENES = {  # noqa: RUF012
        # Por título y, dentro de la serie, por volumen. El volumen vive en
        # la hija editorial, así que el orden lo atraviesa; en los no
        # editoriales queda nulo y ordena parejo entre ellos.
        "alfabetico": ("titulo", "productoeditorial__volumen"),
        "recientes": ("-creado_en",),
    }
    ORDEN_POR_DEFECTO = "alfabetico"

    # El paso 2: "todos los productos en estado Activo". Se guarda como
    # constante y no escrito en dos lugares porque la vista lo usa para filtrar
    # y el contexto para marcar el desplegable: si se separan, la pantalla
    # mostraría un filtro distinto del que aplicó.
    ESTADO_POR_DEFECTO = Producto.ACTIVO

    context_object_name = "productos"
    paginate_by = 25

    def get_template_names(self):
        if self.request.GET.get("parcial"):
            return ["catalog/_tabla_productos.html"]
        return ["catalog/producto_lista.html"]

    def get_queryset(self):
        # Las dos hijas vienen en la misma consulta: `Producto.especifico`
        # las necesita y sin esto habría una consulta por fila (N+1).
        productos = Producto.objects.select_related(
            "tipo",
            "productoeditorial",
            "productoeditorial__editorial",
            "productoeditorial__formato",
            "productonoeditorial",
        )

        busqueda = self.request.GET.get("q", "").strip()
        if busqueda:
            productos = productos.filter(
                Q(titulo__icontains=busqueda)
                | Q(codigo__icontains=busqueda)
                | Q(productoeditorial__autor__icontains=busqueda)
                | Q(productoeditorial__editorial__nombre__icontains=busqueda)
                | Q(productonoeditorial__marca__icontains=busqueda)
            )

        # Los filtros se validan contra las opciones reales: un valor inventado
        # en la query string se ignora, no rompe ni filtra de más.
        #
        # **La vista por defecto es "los Activos", no "todos"** (paso 2 del CU).
        # Un inventario que abre mostrando también lo descatalogado y lo
        # cancelado por editorial obliga a filtrar antes de poder leerlo, y el
        # Cajero que atiende a alguien en el mostrador no está para eso. Se
        # distingue el parámetro ausente del vacío: `?estado=` explícito
        # significa "todos", que es como el enlace de limpiar filtros pide verlos.
        estado = self.request.GET.get("estado", self.ESTADO_POR_DEFECTO)
        if estado in dict(Producto.ESTADO_CHOICES):
            productos = productos.filter(estado=estado)

        disponibilidad = self.request.GET.get("stock", "")
        if disponibilidad == self.CON_STOCK:
            productos = productos.filter(stock__gt=0)
        elif disponibilidad == self.SIN_STOCK:
            productos = productos.filter(stock=0)

        origen = self.request.GET.get("origen", "")
        if origen in dict(ProductoEditorial.ORIGEN_CHOICES):
            # Atraviesa a la hija: `origen` dejó de vivir en el padre, y con
            # eso el filtro descarta solos a los no editoriales, que es lo
            # correcto — un insumo no es ni nacional ni importado.
            productos = productos.filter(productoeditorial__origen=origen)

        tipo = _entero(self.request.GET.get("tipo"))
        if tipo:
            productos = productos.filter(tipo_id=tipo)

        # Las etiquetas no identifican un producto, pero son la forma natural de
        # recortar el catálogo: "todo lo de Marvel" cruza editoriales y tipos, y
        # ninguno de los otros filtros junta eso.
        etiqueta = _entero(self.request.GET.get("etiqueta"))
        if etiqueta:
            productos = productos.filter(etiquetas=etiqueta)

        orden = self.request.GET.get("orden", self.ORDEN_POR_DEFECTO)
        return productos.order_by(*self.ORDENES.get(orden, self.ORDENES[self.ORDEN_POR_DEFECTO]))

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        estado = self.request.GET.get("estado", self.ESTADO_POR_DEFECTO)
        origen = self.request.GET.get("origen", "")
        disponibilidad = self.request.GET.get("stock", "")
        orden = self.request.GET.get("orden", self.ORDEN_POR_DEFECTO)
        contexto["busqueda"] = self.request.GET.get("q", "").strip()
        contexto["estado_elegido"] = estado if estado in dict(Producto.ESTADO_CHOICES) else ""
        contexto["disponibilidades"] = self.DISPONIBILIDADES
        contexto["disponibilidad_elegida"] = (
            disponibilidad if disponibilidad in dict(self.DISPONIBILIDADES) else ""
        )
        contexto["orden_elegido"] = orden if orden in self.ORDENES else self.ORDEN_POR_DEFECTO
        contexto["origen_elegido"] = (
            origen if origen in dict(ProductoEditorial.ORIGEN_CHOICES) else ""
        )
        contexto["tipo_elegido"] = _entero(self.request.GET.get("tipo")) or ""
        contexto["etiqueta_elegida"] = _entero(self.request.GET.get("etiqueta")) or ""
        contexto["estados"] = Producto.ESTADO_CHOICES
        contexto["origenes"] = ProductoEditorial.ORIGEN_CHOICES
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


class ProductoDetalleView(InventarioMixin, DetailView):
    """CU-11 paso 6 — la ficha, con **campos distintos según quién mire**.

    Es el destino del enlace que CU-01 E1 exige al informar un duplicado, y
    ahora también el paso 6 del CU de consulta. Lo que cambia por rol:

    - El **Administrador** ve todo, incluido el historial de modificaciones.
    - El **Cajero** ve nombre, imagen, categoría, estado, stock y precio, y la
      ficha es de solo lectura sin acciones.

    Los otros dos campos que el paso 6 le reserva al Administrador —stock
    reservado en pedidos y suscriptores de reposición activos— pertenecen a
    Pedidos y a Restock, que no existen. La ficha lo dice en vez de mostrar un
    cero, por el mismo criterio con el que la baja de proveedor no inventa la
    cifra de propuestas de restock que no puede calcular.
    """

    model = Producto
    template_name = "catalog/producto_detalle.html"
    context_object_name = "producto"

    def get_queryset(self):
        return Producto.objects.select_related(
            "tipo",
            "productoeditorial",
            "productoeditorial__editorial",
            "productoeditorial__formato",
            "productoeditorial__lote",
            "productonoeditorial",
        ).prefetch_related("etiquetas__grupo")

    def get_object(self, queryset=None):
        """Devuelve **la instancia de la hija**, no la del padre.

        Así la plantilla lee `producto.volumen` y `producto.marca` sin saber de
        la jerarquía: la hija hereda todos los campos del padre, con lo cual
        sirve para las dos mitades de la ficha. Bajar acá y no en la plantilla
        deja el descenso en un solo lugar.
        """
        return super().get_object(queryset).especifico

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        contexto["es_administrador"] = self.request.user.rol == Usuario.ADMINISTRADOR
        if contexto["es_administrador"]:
            contexto["historial"] = self._historial()
        return contexto

    def _historial(self):
        """Lo que se hizo sobre este producto, de lo más nuevo a lo más viejo.

        Sale del log genérico de auditoría, que desde A8 de `alta_editorial.md`
        tiene objetivo genérico y un índice sobre `(objetivo_tipo, objetivo_pk)`
        puesto exactamente para esta consulta.
        """
        # **Los tres tipos de contenido, y no solo el del padre.** Con herencia
        # por tabla el objetivo genérico se vuelve ambiguo: quien audita pasando
        # una instancia de la hija deja registrado `productoeditorial`, y quien
        # pasa una del padre deja `producto`. Las dos se refieren a la misma
        # fila —la clave primaria es compartida— así que el historial tiene que
        # buscar por las tres o se le pierde la mitad de su propio pasado.
        tipos = [
            ContentType.objects.get_for_model(modelo)
            for modelo in (Producto, ProductoEditorial, ProductoNoEditorial)
        ]
        return RegistroAuditoria.objects.filter(
            objetivo_tipo__in=tipos, objetivo_pk=self.object.pk
        ).select_related("actor")[:25]


class BorradorListaView(CatalogoAdminMixin, ListView):
    """CU-05 paso 1 — la cola de borradores pendientes.

    Muestra los dos grupos que el CU pide diferenciar visualmente: los
    **incompletos** (les falta un campo bloqueante) y los de **confianza baja**
    (el modelo dudó de algún dato). No son lo mismo y no se arreglan igual: al
    incompleto le falta un dato, al dudoso hay que mirarle uno que ya está.

    Desde acá salen las dos acciones de lote: confirmar una selección y cerrar
    la sesión de revisión.
    """

    context_object_name = "borradores"
    paginate_by = 25

    def get_template_names(self):
        if self.request.GET.get("parcial"):
            return ["catalog/_tabla_borradores.html"]
        return ["catalog/borrador_lista.html"]

    def get_queryset(self):
        borradores = (
            BorradorProducto.objects.pendientes()
            .select_related("editorial", "tipo", "formato", "proveedor", "correo")
            .prefetch_related("confianzas")
        )

        busqueda = self.request.GET.get("q", "").strip()
        if busqueda:
            borradores = borradores.filter(
                Q(titulo__icontains=busqueda)
                | Q(isbn__icontains=busqueda)
                | Q(proveedor__razon_social__icontains=busqueda)
            )

        proveedor = _entero(self.request.GET.get("proveedor"))
        if proveedor:
            borradores = borradores.filter(proveedor_id=proveedor)

        return borradores

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        contexto["busqueda"] = self.request.GET.get("q", "").strip()
        contexto["proveedor_elegido"] = _entero(self.request.GET.get("proveedor")) or ""
        # Solo los proveedores que tienen algo en la cola: ofrecer los treinta
        # del padrón para filtrar entre dos sería ruido.
        contexto["proveedores"] = Proveedor.objects.filter(
            borradores__estado__in=BorradorProducto.ESTADOS_ABIERTOS
        ).distinct()

        pendientes = BorradorProducto.objects.pendientes()
        contexto["resumen"] = {
            "total": pendientes.count(),
            "incompletos": pendientes.filter(estado=BorradorProducto.INCOMPLETO).count(),
        }
        contexto["sesion"] = revisiones.sesion_abierta_de(self.request.user)
        return contexto


class BorradorDetalleView(CatalogoAdminMixin, View):
    """CU-05 pasos 2 y 3 — revisar un borrador, editarlo y resolverlo.

    Las tres acciones (guardar, confirmar, rechazar) llegan al mismo `POST` y se
    distinguen por el botón que se apretó. Están juntas a propósito: las tres se
    deciden mirando los mismos datos, y separarlas en tres pantallas obligaría a
    ir y volver con el borrador a medio editar.

    **La acción afirmativa sobre cada campo de confianza baja se valida acá, del
    lado del servidor.** Es lo que pide el paso 3, y esconder el botón no sería
    validarlo: un `POST` armado a mano confirmaría igual un dato que nadie miró.
    """

    template_name = "catalog/borrador_detalle.html"

    def get(self, request, pk):
        borrador = self._obtener(pk)
        return render(request, self.template_name, self._contexto(borrador))

    def post(self, request, pk):
        borrador = self._obtener(pk)

        if not borrador.esta_abierto:
            # Se vuelve a chequear en el POST y no solo escondiendo los botones:
            # el doble envío del formulario es el caso normal, no el raro.
            messages.info(request, MENSAJE_BORRADOR_YA_RESUELTO)
            return redirect("catalog:borrador_detalle", pk=borrador.pk)

        if "rechazar" in request.POST:
            return self._rechazar(request, borrador)
        return self._guardar_o_confirmar(request, borrador)

    # ------------------------------------------------------------------

    def _obtener(self, pk):
        return get_object_or_404(
            BorradorProducto.objects.select_related(
                "editorial", "tipo", "formato", "proveedor", "correo", "producto"
            ).prefetch_related("confianzas"),
            pk=pk,
        )

    def _contexto(self, borrador, **extra):
        contexto = {
            "borrador": borrador,
            "form": BorradorForm(instance=borrador),
            "form_rechazo": RechazoDeBorradorForm(),
            # La confianza se muestra junto al campo que califica, no en una
            # lista aparte: separada, revisar sería ir y volver entre dos zonas
            # de la pantalla buscando a qué campo corresponde cada marca.
            "confianzas": {c.campo: c for c in borrador.confianzas.all()},
            "sesion": revisiones.sesion_abierta_de(self.request.user),
            # Si el producto ya está en el catálogo, se dice **antes** de
            # intentar confirmar. Salió de correr el pipeline sobre dos correos
            # que anunciaban los mismos tomos: los borradores del segundo
            # quedaban en la cola sin ninguna marca, y la única forma de
            # enterarse era apretar el botón y recibir el rechazo. Es la misma
            # cortesía que CU-01 E1 le da a los duplicados del alta en lote,
            # enlace a la ficha existente incluido.
            "duplicado": self._duplicado_de(borrador),
        }
        contexto.update(extra)
        return contexto

    def _duplicado_de(self, borrador):
        """El producto que ya ocupa esa identidad, o `None`.

        Solo tiene sentido sobre un borrador abierto: en uno confirmado el
        "duplicado" sería el producto que él mismo creó.
        """
        if not borrador.esta_abierto:
            return None
        return services.buscar_duplicado(
            borrador.titulo,
            borrador.volumen,
            borrador.tipo,
            borrador.formato,
            borrador.editorial,
            borrador.isbn,
        )

    def _rechazar(self, request, borrador):
        formulario = RechazoDeBorradorForm(request.POST)
        if not formulario.is_valid():
            return render(
                request,
                self.template_name,
                self._contexto(borrador, form_rechazo=formulario, mostrar_rechazo=True),
            )

        revisiones.rechazar(
            borrador,
            actor=request.user,
            motivo=formulario.cleaned_data["motivo"],
            ip=obtener_ip(request),
        )
        messages.success(request, f"Borrador «{borrador}» rechazado.")
        return redirect("catalog:borrador_lista")

    def _guardar_o_confirmar(self, request, borrador):
        formulario = BorradorForm(request.POST, request.FILES, instance=borrador)
        if not formulario.is_valid():
            return render(request, self.template_name, self._contexto(borrador, form=formulario))

        borrador = formulario.save()
        self._marcar_revisadas(request, borrador)

        if "confirmar" not in request.POST:
            messages.success(request, "Cambios guardados. El borrador sigue pendiente.")
            return redirect("catalog:borrador_detalle", pk=borrador.pk)

        # Se relee la confianza después de haberla marcado: si el Administrador
        # tildó las casillas en este mismo envío, tienen que contar.
        sin_revisar = [c.campo for c in borrador.confianzas.all() if c.exige_revision]
        if sin_revisar:
            messages.error(request, MENSAJE_CONFIANZA_SIN_REVISAR.format(", ".join(sin_revisar)))
            return redirect("catalog:borrador_detalle", pk=borrador.pk)

        confirmacion = revisiones.confirmar(borrador, actor=request.user, ip=obtener_ip(request))
        if not confirmacion:
            messages.error(request, f"No se pudo confirmar: {confirmacion.motivo_legible.lower()}.")
            return redirect("catalog:borrador_detalle", pk=borrador.pk)

        messages.success(request, f"«{confirmacion.producto}» se agregó al catálogo.")
        return redirect("catalog:borrador_lista")

    def _marcar_revisadas(self, request, borrador):
        """La acción afirmativa del paso 3, campo por campo.

        Se guarda lo que el Administrador tildó **y también lo que destildó**: la
        revisión de un campo se puede retirar, y dejar la marca puesta haría que
        un dato vuelto a poner en duda siguiera contando como mirado.
        """
        marcados = set(request.POST.getlist("revisado"))
        for confianza in borrador.confianzas.all():
            revisado = confianza.campo in marcados
            if confianza.revisado != revisado:
                confianza.revisado = revisado
                confianza.save(update_fields=["revisado"])


class ConfirmarEnLoteView(CatalogoAdminMixin, View):
    """CU-05 paso 4 — confirmar una selección con una sola acción.

    **Excluye, no bloquea.** Un borrador con confianza baja o con un bloqueante
    vacío se saltea informando por qué y queda en cola para revisión individual;
    los demás se confirman igual. Es la misma distinción de CU-01 entre una
    exclusión esperada y un fallo transaccional.
    """

    def post(self, request):
        elegidos = [_entero(valor) for valor in request.POST.getlist("borrador")]
        borradores = list(
            BorradorProducto.objects.pendientes()
            .filter(pk__in=[pk for pk in elegidos if pk])
            .prefetch_related("confianzas")
        )
        if not borradores:
            messages.info(request, "No se seleccionó ningún borrador pendiente.")
            return redirect("catalog:borrador_lista")

        resultado = revisiones.confirmar_en_lote(
            borradores, actor=request.user, ip=obtener_ip(request)
        )
        if resultado.confirmadas:
            messages.success(
                request, f"{len(resultado.confirmadas)} producto(s) agregado(s) al catálogo."
            )
        for excluida in resultado.excluidas:
            messages.warning(
                request,
                f"«{excluida.borrador}» quedó en la cola: " f"{excluida.motivo_legible.lower()}.",
            )
        return redirect("catalog:borrador_lista")


class CerrarSesionRevisionView(CatalogoAdminMixin, View):
    """CU-05 pasos 5 y 6 — cerrar la tanda y mandar los pedidos.

    Un correo por proveedor con los productos **de esta sesión**. El cierre no se
    hace solo al salir de la pantalla: es una decisión explícita, porque es la
    que dispara los pedidos al proveedor.
    """

    def post(self, request):
        sesion = revisiones.sesion_abierta_de(request.user)
        if sesion is None:
            messages.info(request, MENSAJE_SIN_SESION)
            return redirect("catalog:borrador_lista")

        envios = revisiones.cerrar(sesion, actor=request.user, ip=obtener_ip(request))
        enviados = [envio for envio in envios if envio]
        if enviados:
            messages.success(
                request, f"Sesión cerrada. Se enviaron {len(enviados)} pedido(s) de reposición."
            )
        else:
            messages.info(request, "Sesión cerrada sin confirmaciones: no se envió ningún pedido.")

        for envio in envios:
            if not envio:
                # El CU pide notificar **cuál** proveedor falló: sin el nombre el
                # aviso no sirve para ir a mandarlo a mano.
                messages.error(
                    request,
                    f"No se pudo enviar el pedido a {envio.proveedor} "
                    f"({envio.proveedor.correo_comercial}) después de "
                    f"{envio.intentos} intentos. Los productos quedaron cargados igual.",
                )
        return redirect("catalog:borrador_lista")
