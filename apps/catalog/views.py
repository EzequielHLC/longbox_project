"""Pantallas del catálogo: alta de lotes editoriales e inventario.

Todas son de backoffice y exclusivas del Administrador, validado del lado del
servidor (RNF-03). El sistema visual que les corresponde es el **modo
operativo**: ninguna pantalla de este módulo es pública.
"""

import csv
from decimal import Decimal

from django.contrib import messages
from django.contrib.contenttypes.models import ContentType
from django.db import IntegrityError, transaction
from django.db.models import Count, Q, Sum
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views import View
from django.views.generic import CreateView, DetailView, ListView, UpdateView

from apps.accounts.models import Usuario
from apps.catalog import catalogos, galeria, revisiones, services, tabla_de_precios
from apps.catalog.forms import (
    BorradorForm,
    CabeceraLoteForm,
    CabeceraLoteImportadoForm,
    CompraOnlineForm,
    ConfiguracionForm,
    EditorialForm,
    FormatoForm,
    ModeloDeLenguajeForm,
    ProductoEditorialForm,
    ProductoNoEditorialForm,
    RechazoDeBorradorForm,
    SeguridadForm,
    TipoForm,
    formatos_para,
    formset_de_items,
)
from apps.catalog.models import (
    EDITORIAL,
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
from apps.core import cambios, cotizaciones
from apps.core.mixins import RolRequeridoMixin
from apps.core.models import ConfiguracionSistema, RegistroAuditoria
from apps.core.utils import celda_csv, obtener_ip
from apps.pedidos import preventa
from apps.puntos.servicios import puntos_por_monto
from apps.restock import servicios as restock
from apps.restock.models import SuscripcionReposicion
from apps.suppliers.models import Proveedor

MENSAJE_BORRADOR_YA_RESUELTO = "Este borrador ya fue confirmado o rechazado."
MENSAJE_SIN_SESION = "No hay ninguna sesión de revisión en curso."
MENSAJE_CONFIANZA_SIN_REVISAR = (
    "Antes de confirmar hay que revisar los campos de confianza baja: {}."
)


class InventarioMixin(RolRequeridoMixin):
    """CU-CAT-INV — Consultar Inventario, el primer CU del proyecto con **dos actores**.

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


def choque_tras_validar(form, *, alta, portada_guardada=""):
    """¿El guardado chocó con otro producto que se confirmó mientras éste se validaba?

    Entre la validación y el INSERT otro pedido se quedó con el código, el ISBN o
    la edición (plan 00 de cierre de deuda, D1). Se vuelve a validar: la segunda
    pasada ya ve la fila ganadora y deja el mismo aviso —con el enlace y el
    criterio— que si hubiera llegado antes. Si vuelve a pasar, el error de
    integridad es otro y no se disfraza de duplicado: devuelve `False`.

    La portada de este envío se escribe al almacenamiento antes del INSERT; si no
    es la que el producto ya tenía, nadie la referencia y se borra. En un alta, la
    fila del padre pudo llegar a insertarse antes de que chocara la de la hija: la
    transacción la deshizo, pero la instancia se quedó con su clave y tiene que
    volver a ser nueva para que la segunda validación no se excluya a sí misma.
    """
    portada = form.instance.portada
    if portada and portada.name and portada.name != portada_guardada:
        portada.storage.delete(portada.name)
    if alta:
        form.instance.pk = None
        form.instance.id = None
        form.instance._state.adding = True
    form.full_clean()
    return bool(form.errors)


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
    """CU-CAT-ALT — Registrar Alta de Producto No Editorial.

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
        contexto["conflicto"] = getattr(contexto["form"], "conflicto", None)
        contexto["hay_categorias"] = Tipo.objects.filter(activo=True, clase=NO_EDITORIAL).exists()
        return contexto

    def form_valid(self, form):
        try:
            with transaction.atomic():
                producto = form.save()
                agregadas, _ = galeria.actualizar(
                    producto, nuevas=form.cleaned_data.get("imagenes_nuevas") or []
                )
                detalle = (
                    f"«{producto.titulo}» ({producto.tipo}) · código {producto.codigo} · "
                    f"${producto.precio} · stock inicial {producto.stock}"
                )
                if agregadas:
                    detalle += f" · {galeria.describir(agregadas, 0)}"
                RegistroAuditoria.registrar(
                    RegistroAuditoria.ALTA_PRODUCTO_NO_EDITORIAL,
                    actor=self.request.user,
                    ip=obtener_ip(self.request),
                    objetivo=producto,
                    detalle=detalle,
                )
        except IntegrityError:
            # `CO-028` E3 cuando otra alta ganó el código después de validarlo.
            if not choque_tras_validar(form, alta=True):
                raise
            return self.form_invalid(form)

        self.object = producto
        messages.success(self.request, f"«{producto.titulo}» se agregó al catálogo.")
        # El paso 8 pide terminar mostrando la ficha del producto creado.
        return redirect("catalog:producto_detalle", pk=producto.pk)


class DuplicadosNoEditorialesView(CatalogoAdminMixin, View):
    """Lo que ya existe con un nombre parecido, mientras se escribe (CU-CAT-ALT E2).

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
    catalogo = None

    def datos(self, request):
        """Lo que se le pasa al formulario. Algunos catálogos completan algo."""
        return request.POST

    def post(self, request):
        formulario = self.form_class(self.datos(request))
        if not formulario.is_valid():
            return JsonResponse({"errores": formulario.errors.get("nombre", [])}, status=400)

        # El mismo alta que la pantalla del catálogo, con su misma auditoría
        # (A1 de `CU-CFG-EDA`): no hay dos caminos con reglas distintas.
        creado = catalogos.registrar(
            formulario, catalogo=self.catalogo, actor=request.user, ip=obtener_ip(request)
        )
        return JsonResponse({"id": creado.pk, "nombre": creado.nombre})


class EditorialRapidaView(CatalogoRapidoView):
    form_class = EditorialForm
    catalogo = catalogos.EDITORIALES


class TipoRapidaView(CatalogoRapidoView):
    """A1 de `CU-CFG-TPA`. La carga de un lote es de material editorial, así
    que el rubro no se pregunta: es el de la pantalla."""

    form_class = TipoForm
    catalogo = catalogos.TIPOS

    def datos(self, request):
        datos = request.POST.copy()
        datos["clase"] = EDITORIAL
        return datos


class FormatoRapidaView(CatalogoRapidoView):
    """A1 de `CU-CFG-FMA`: el formato nuevo queda declarado para el tipo
    elegido en la carga, salvo que se indique que aplica a todos."""

    form_class = FormatoForm
    catalogo = catalogos.FORMATOS


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

    def get(
        self, request, formulario=None, form_modelo=None, form_compra=None, form_seguridad=None
    ):
        contexto = self._contexto(request, formulario, form_modelo)
        configuracion = ConfiguracionSistema.obtener()
        contexto["form_compra"] = form_compra or CompraOnlineForm(instance=configuracion)
        contexto["form_seguridad"] = form_seguridad or SeguridadForm(instance=configuracion)
        # Para que el Administrador vea qué significan los dos números juntos.
        ejemplo = Decimal("10000")
        puntos_del_ejemplo = puntos_por_monto(ejemplo)
        contexto["ejemplo_puntos"] = {
            "compra": ejemplo,
            "puntos": puntos_del_ejemplo,
            "valen": puntos_del_ejemplo * configuracion.equivalencia_puntos,
        }
        return render(request, self.template_name, contexto)

    def post(self, request):
        # Dos formularios en la misma pantalla, distinguidos por el botón que
        # los envía. Están separados porque se tocan por motivos distintos: el
        # margen lo cambia el negocio, el modelo de lenguaje lo cambia quien
        # despliega — y un error en uno no tiene por qué borrar lo escrito en
        # el otro.
        if "guardar_modelo" in request.POST:
            return self._guardar_modelo(request)
        if "guardar_compra" in request.POST:
            return self._guardar_parametros(request, CompraOnlineForm)
        if "guardar_seguridad" in request.POST:
            return self._guardar_parametros(request, SeguridadForm)
        return self._guardar_parametros(request, ConfiguracionForm)

    # Cómo se nombra cada parámetro en el detalle de la auditoría; los demás,
    # por el nombre de su campo.
    NOMBRES = {  # noqa: RUF012
        "stock_inicial_por_defecto": "stock por defecto",
        "intervalo_carrusel": "intervalo del carrusel (s)",
        "dias_aviso_preventa": "aviso previo de pre-venta (días)",
        "ventana_decision_horas": "ventana de decisión (h)",
        "equivalencia_puntos": "valor del punto ($)",
        "porcentaje_puntos": "reintegro en puntos (%)",
        "plazo_devolucion_dias": "plazo de arrepentimiento (días)",
        "plazo_garantia_dias": "plazo de garantía (días)",
        "maximo_reserva_preventa": "máximo por reserva (unidades)",
        "margen_cupo_preventa": "margen del cupo de pre-venta (%)",
        "expiracion_sesion_minutos": "expiración de la sesión (min)",
        "bloqueo_intentos_minutos": "bloqueo tras intentos fallidos (min)",
    }

    def _guardar_parametros(self, request, formulario_de):
        configuracion = ConfiguracionSistema.obtener()
        campos = formulario_de.Meta.fields
        anterior = {campo: self._legible(configuracion, campo) for campo in campos}
        formulario = formulario_de(request.POST, instance=configuracion)

        rechazado = None
        if not formulario.is_valid():
            if formulario_de is SeguridadForm:
                return self.get(request, form_seguridad=formulario)
            if formulario_de is not CompraOnlineForm:
                return self.get(request, formulario=formulario)
            if not formulario.solo_falla_el_plazo_de_devolucion():
                return self.get(request, form_compra=formulario)
            # CO-130 E1: el plazo por debajo del piso legal se rechaza solo; los
            # demás valores válidos se guardan, y el plazo conserva el vigente.
            rechazado = formulario
            datos = request.POST.copy()
            datos["plazo_devolucion_dias"] = configuracion.plazo_devolucion_dias
            formulario = formulario_de(datos, instance=ConfiguracionSistema.obtener())
            if not formulario.is_valid():
                return self.get(request, form_compra=rechazado)

        with transaction.atomic():
            configuracion = formulario.save(commit=False)
            configuracion.actualizado_por = request.user
            configuracion.save()
            # CO-130: una entrada por cada parámetro efectivamente modificado, con
            # su valor anterior y el nuevo. Guardar sin cambios no deja ninguna.
            for campo in campos:
                nuevo = self._legible(configuracion, campo)
                if anterior[campo] == nuevo:
                    continue
                RegistroAuditoria.registrar(
                    accion=RegistroAuditoria.PARAMETRO_MODIFICADO,
                    actor=request.user,
                    objetivo=configuracion,
                    ip=obtener_ip(request),
                    detalle=f"{self._nombre(campo)}: {anterior[campo]} → {nuevo}",
                )

        if rechazado is not None:
            messages.warning(
                request,
                "Se guardaron los demás parámetros. El plazo de arrepentimiento no cambió: "
                + CompraOnlineForm.PISO_LEGAL,
            )
            return self.get(request, form_compra=rechazado)
        messages.success(request, "Se actualizaron los parámetros.")
        return redirect("catalog:parametros")

    def _nombre(self, campo):
        return self.NOMBRES.get(campo) or ConfiguracionSistema._meta.get_field(campo).verbose_name

    @staticmethod
    def _legible(configuracion, campo):
        if campo == "pasarela":
            return configuracion.get_pasarela_display()
        valor = getattr(configuracion, campo)
        if isinstance(valor, Decimal):
            # «8000.00» de la base y «8000» del formulario son el mismo importe.
            return format(valor.normalize(), "f")
        return valor

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

            detalles = [
                f"modo: {anterior[0]} → {configuracion.get_llm_modo_display()}",
                f"dirección: {anterior[1]} → {configuracion.llm_url}",
                f"modelo: {anterior[2]} → "
                f"{configuracion.llm_modelo or 'el que tenga cargado el servidor'}",
            ]
            if formulario.cleaned_data.get("api_key"):
                detalles.append("se reemplazó la clave de la API")

            RegistroAuditoria.registrar(
                accion=RegistroAuditoria.PARAMETRO_MODIFICADO,
                actor=request.user,
                objetivo=configuracion,
                ip=obtener_ip(request),
                detalle="; ".join(detalles),
            )

        messages.success(
            request,
            "Se actualizó la configuración del modelo. Verifíquela en Diagnóstico del modelo.",
        )
        return redirect("catalog:parametros")

    def _contexto(self, request, formulario, form_modelo=None):
        return {
            "configuracion": ConfiguracionSistema.obtener(),
            "form": formulario or ConfiguracionForm(instance=ConfiguracionSistema.obtener()),
            "form_modelo": form_modelo
            or ModeloDeLenguajeForm(instance=ConfiguracionSistema.obtener()),
            "editoriales": Editorial.objects.all(),
            # Una editorial activa sin ninguna fila no tiene de dónde sacar el
            # precio de un alta nacional: sus productos van con precio a mano.
            "editoriales_sin_precios": Editorial.objects.filter(
                activa=True, precios_de_referencia__isnull=True
            ),
            # Los catálogos tienen pantalla propia (`CU-CFG-EDC`, `TPC`, `FMC`,
            # `CU-CAT-GRC`); acá queda el acceso con lo que hay en cada uno.
            "catalogos": [
                (
                    catalogos.TIPOS,
                    "tipo",
                    Tipo.objects.filter(activo=True).count(),
                    Tipo.objects.count(),
                ),
                (
                    catalogos.FORMATOS,
                    "formato",
                    Formato.objects.filter(activo=True).count(),
                    Formato.objects.count(),
                ),
                (
                    catalogos.EDITORIALES,
                    "editorial",
                    Editorial.objects.filter(activa=True).count(),
                    Editorial.objects.count(),
                ),
                (
                    catalogos.GRUPOS,
                    "etiqueta",
                    GrupoEtiqueta.objects.filter(activo=True).count(),
                    GrupoEtiqueta.objects.count(),
                ),
            ],
            "cantidad_de_precios": TablaPrecioReferencia.objects.count(),
            "margen_vigente": tabla_de_precios.porcentaje(
                ConfiguracionSistema.obtener().margen_ganancia
            ),
        }


class LoteResumenView(CatalogoAdminMixin, DetailView):
    """El resumen del alta (CU-ALT-NAC paso 9, CU-ALT-IMP paso 11).

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
    """CU-CAT-INV — Consultar Inventario.

    Nació como contraparte de lectura del alta en lote (A7 de
    `alta_editorial.md`), antes de que el Módulo 02 se abordara, y por eso
    heredaba dos cosas que su propio CU contradice: **estaba restringida al
    Administrador** —el Cajero es actor declarado— y **ordenaba por fecha de
    alta**, que es lo que sirve después de cargar un lote y no lo que pide el
    paso 2.

    Las dos quedaron resueltas sin perder el uso viejo: el orden es un parámetro
    con alfabético por defecto, así que quien viene de cargar un lote pide
    `?orden=recientes` y ve lo suyo.

    Editar y dar de baja son CU-CAT-EDI y CU-CAT-BAJ, todavía sin implementar.
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

        editorial = _entero(self.request.GET.get("editorial"))
        if editorial:
            productos = productos.filter(productoeditorial__editorial_id=editorial)

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
        contexto["editorial_elegida"] = _entero(self.request.GET.get("editorial")) or ""
        contexto["editoriales"] = Editorial.objects.all()
        # A1: la exportación lleva los mismos filtros que la pantalla.
        contexto["filtros_aplicados"] = self.request.GET.urlencode()
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


class ProductoExportarView(CatalogoAdminMixin, ProductoListaView):
    """CU-CAT-INV A1 — `CO-037 exportarInventario`.

    Hereda la consulta del listado y no la reescribe: el archivo tiene que
    traer exactamente las filas que la pantalla muestra con esos filtros, y dos
    consultas escritas por separado terminan filtrando distinto.

    Exclusiva del Administrador, validado en el servidor: el mixin del catálogo
    va primero y le gana al del inventario, que también deja entrar al Cajero.

    CSV porque es el formato de la otra exportación del sistema (`CO-129`). Con
    BOM, para que la planilla de cálculo lea bien los acentos.
    """

    COLUMNAS = (  # noqa: RUF012
        "Código",
        "Título",
        "Volumen",
        "Tipo",
        "Editorial",
        "Formato",
        "Origen",
        "Estado",
        "Stock",
        "Precio",
    )

    def get(self, request, *args, **kwargs):
        productos = self.get_queryset()

        respuesta = HttpResponse(content_type="text/csv; charset=utf-8")
        respuesta["Content-Disposition"] = (
            f'attachment; filename="inventario-{timezone.localdate():%Y-%m-%d}.csv"'
        )
        respuesta.write("\ufeff")
        escritor = csv.writer(respuesta)
        escritor.writerow(self.COLUMNAS)
        cantidad = 0
        for producto in productos.iterator(chunk_size=500):
            editorial = getattr(producto, "productoeditorial", None)
            escritor.writerow(
                celda_csv(valor)
                for valor in [
                    producto.codigo,
                    producto.titulo,
                    editorial.volumen if editorial and editorial.volumen else "",
                    producto.tipo.nombre,
                    editorial.editorial.nombre if editorial else "",
                    editorial.formato.nombre if editorial and editorial.formato else "",
                    editorial.get_origen_display() if editorial else "",
                    producto.get_estado_display(),
                    producto.stock,
                    producto.precio,
                ]
            )
            cantidad += 1

        RegistroAuditoria.registrar(
            accion=RegistroAuditoria.EXPORTACION_INVENTARIO,
            actor=request.user,
            ip=obtener_ip(request),
            detalle=f"{cantidad} productos; filtros: {self._filtros_legibles()}",
        )
        return respuesta

    def _filtros_legibles(self):
        """Los filtros tal como se aplicaron, para el registro de auditoría."""
        parametros = {
            clave: valor
            for clave, valor in self.request.GET.items()
            if clave in ("q", "estado", "stock", "origen", "tipo", "editorial", "etiqueta", "orden")
        }
        parametros.setdefault("estado", self.ESTADO_POR_DEFECTO)
        return ", ".join(f"{clave}={valor or 'todos'}" for clave, valor in parametros.items())


class ProductoDetalleView(InventarioMixin, DetailView):
    """CU-CAT-INV paso 6 — la ficha, con **campos distintos según quién mire**.

    Es el destino del enlace que CU-ALT-NAC E1 exige al informar un duplicado, y
    ahora también el paso 6 del CU de consulta. Lo que cambia por rol:

    - El **Administrador** ve todo, incluido el historial de modificaciones.
    - El **Cajero** ve nombre, imagen, categoría, estado, stock y precio, y la
      ficha es de solo lectura sin acciones.

    Los otros dos campos que el paso 6 le reserva al Administrador —stock
    reservado en pedidos y suscriptores de reposición activos— se calculan desde
    que existen Pedidos y Restock.
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
            contexto["restauracion"] = tabla_de_precios.restauracion_de(self.object)
            contexto["reservadas"] = (
                preventa.reservas_pendientes(self.object).aggregate(total=Sum("cantidad"))["total"]
                or 0
            )
            contexto["suscriptores"] = SuscripcionReposicion.objects.filter(
                producto=self.object, estado__in=SuscripcionReposicion.EN_ESPERA
            ).count()
            contexto["puede_demorar"] = self._puede_demorar()
        return contexto

    def _puede_demorar(self):
        """Las precondiciones de `CO-014`, para ofrecer la acción sólo cuando aplica."""
        try:
            preventa.validar_demora(self.object)
        except (preventa.OperacionRechazada, AttributeError):
            return False
        return True

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
        del_producto = Q(objetivo_tipo__in=tipos, objetivo_pk=self.object.pk)

        # **El alta por lote se audita sobre el lote**, una entrada por lote y no
        # por ítem (CU-ALT-NAC paso 8). Sin sumarla, el historial de un tomo
        # cargado por lote empezaba en su primera modificación, como si hubiera
        # aparecido solo.
        lote = getattr(self.object, "lote_id", None)
        if lote:
            del_producto |= Q(
                objetivo_tipo=ContentType.objects.get_for_model(LoteAlta), objetivo_pk=lote
            )
        return RegistroAuditoria.objects.filter(del_producto).select_related("actor")[:25]


class BorradorListaView(CatalogoAdminMixin, ListView):
    """CU-ALT-REV paso 1 — la cola de borradores pendientes.

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
    """CU-ALT-REV pasos 2 y 3 — revisar un borrador, editarlo y resolverlo.

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
            # cortesía que CU-ALT-NAC E1 le da a los duplicados del alta en lote,
            # enlace a la ficha existente incluido.
            "duplicado": self._duplicado_de(borrador),
            # B-01-020: la serie, si ya está en el catálogo, con lo que difiere.
            "serie": (serie := services.serie_de(borrador.titulo, borrador.editorial)),
            "serie_datos": serie
            and {
                "tipo": serie.tipo.pk,
                "formato": serie.formato.pk if serie.formato else "",
                "autor": serie.autor,
                "sinopsis": serie.sinopsis,
                "solo_adultos": serie.solo_adultos,
                "etiquetas": [etiqueta.pk for etiqueta in serie.etiquetas],
            },
            # B-01-018: la fila de la tabla para lo que el borrador tiene guardado.
            # La pantalla la vuelve a consultar si se cambia la combinación.
            "precio_de_la_tabla": borrador.precio_de_la_tabla,
            "precio_es_el_de_la_tabla": borrador.precio_es_el_de_la_tabla
            or (borrador.precio is None and borrador.precio_de_la_tabla is not None),
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
        formulario = BorradorForm(
            request.POST,
            request.FILES,
            instance=borrador,
            confirmando="confirmar" in request.POST,
        )
        if not formulario.is_valid():
            return render(request, self.template_name, self._contexto(borrador, form=formulario))

        borrador = formulario.save()
        revisiones.completar(borrador)
        self._marcar_revisadas(request, borrador)

        if "confirmar" not in request.POST:
            messages.success(request, "Cambios guardados. El borrador sigue pendiente.")
            return redirect("catalog:borrador_detalle", pk=borrador.pk)

        # Se relee la confianza después de haberla marcado: si el Administrador
        # tildó las casillas en este mismo envío, tienen que contar.
        sin_revisar = [c.campo for c in borrador.confianzas_bajas_sin_revisar]
        if sin_revisar:
            messages.error(request, MENSAJE_CONFIANZA_SIN_REVISAR.format(", ".join(sin_revisar)))
            return redirect("catalog:borrador_detalle", pk=borrador.pk)

        confirmacion = revisiones.confirmar(
            borrador,
            actor=request.user,
            ip=obtener_ip(request),
            confirma_precio_manual=formulario.cleaned_data.get("confirma_precio_manual", False),
        )
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
    """CU-ALT-REV paso 4 — confirmar una selección con una sola acción.

    **Excluye, no bloquea.** Un borrador con confianza baja o con un bloqueante
    vacío se saltea informando por qué y queda en cola para revisión individual;
    los demás se confirman igual. Es la misma distinción de CU-ALT-NAC entre una
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
                f"«{excluida.borrador}» quedó en la cola: {excluida.motivo_legible.lower()}.",
            )
        return redirect("catalog:borrador_lista")


class CerrarSesionRevisionView(CatalogoAdminMixin, View):
    """CU-ALT-REV pasos 5 y 6 — cerrar la tanda y mandar los pedidos.

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


# ---------------------------------------------------------------------------
# CU-CAT-EDI y CU-CAT-BAJ — editar, dar de baja y reactivar un producto
# ---------------------------------------------------------------------------


def _estado_por_stock(producto):
    if producto.estado == Producto.AGOTADO and producto.stock > 0:
        return Producto.ACTIVO
    return producto.estado


class ProductoEdicionView(CatalogoAdminMixin, UpdateView):
    """CU-CAT-EDI — Editar Producto, de los dos rubros.

    **Una vista y dos formularios**, elegidos por el rubro del producto. La
    alternativa era un formulario que supiera de los dos, y sería peor: los
    campos no se solapan casi en nada —volumen, ISBN y editorial contra marca— y
    un formulario condicional termina siendo dos formularios con `if` de por
    medio, más difícil de leer que dos declarados.

    El del rubro no editorial es **el mismo que usa el alta**, no uno parecido.
    Es la misma regla que gobierna los catálogos: dos caminos con la regla
    escrita dos veces es la forma más segura de que uno quede más laxo.

    **La precondición del CU es amplia y conviene respetarla:** el producto se
    edita en cualquier estado, descatalogado incluido. A diferencia de una cuenta
    de usuario, que se congela al darse de baja, un producto de baja no habilita
    nada mientras lo esté, y mantener sus datos al día es lo que permite
    reactivarlo.
    """

    model = Producto
    template_name = "catalog/producto_formulario.html"
    context_object_name = "producto"

    def get_queryset(self):
        return Producto.objects.select_related("tipo")

    def get_object(self, queryset=None):
        """La instancia de la hija: es sobre la que trabaja su formulario."""
        return super().get_object(queryset).especifico

    def get_form_class(self):
        if self.object.clase == Producto.EDITORIAL:
            return ProductoEditorialForm
        return ProductoNoEditorialForm

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        contexto["duplicado"] = getattr(contexto["form"], "duplicado", None)
        contexto["conflicto"] = getattr(contexto["form"], "conflicto", None)
        contexto["es_editorial"] = self.object.clase == Producto.EDITORIAL
        if contexto["es_editorial"]:
            contexto["restauracion"] = tabla_de_precios.restauracion_de(self.object)
        return contexto

    def form_valid(self, form):
        # El «antes» se lee de la base y **antes** de guardar. Leerlo después
        # —como se hacía— daba lo mismo para los campos simples, pero no para
        # las etiquetas: la relación se consulta en vivo, así que el «antes»
        # ya traía las nuevas y el cambio no se registraba nunca.
        campos = self._campos_auditados(self.object)
        anterior = type(self.object).objects.get(pk=self.object.pk)
        antes = {etiqueta: leer(anterior) for etiqueta, leer in campos.items()}

        try:
            producto, partes = self._guardar(form, campos, anterior, antes)
        except IntegrityError:
            # `CO-030` E2 cuando otro producto ganó el código de barras, el ISBN o
            # la edición después de validarlos.
            if not choque_tras_validar(
                form, alta=False, portada_guardada=anterior.portada.name or ""
            ):
                raise
            return self.form_invalid(form)

        self.object = producto
        if partes:
            messages.success(self.request, f"Se actualizó «{producto.titulo}».")
        else:
            # Guardar sin haber tocado nada no es un error, pero decir "se
            # actualizó" sería afirmar algo que el historial de la ficha
            # desmiente: no va a mostrar ninguna entrada nueva.
            messages.info(self.request, "No había cambios para guardar.")
        return redirect("catalog:producto_detalle", pk=producto.pk)

    def _guardar(self, form, campos, anterior, antes):
        """El guardado de la edición con su historial, en una transacción."""
        with transaction.atomic():
            producto = form.save()
            # Antes de medir los cambios: «Usar como portada» cambia la portada.
            orden_y_portada = galeria.ordenar(
                producto,
                orden=form.cleaned_data.get("orden_imagenes") or [],
                portada_desde=form.cleaned_data.get("nueva_portada"),
            )
            agregadas, quitadas = galeria.actualizar(
                producto,
                nuevas=form.cleaned_data.get("imagenes_nuevas") or [],
                quitar=form.cleaned_data.get("quitar_imagenes") or [],
            )
            lo_que_cambio = {
                etiqueta: (antes[etiqueta], leer(producto))
                for etiqueta, leer in campos.items()
                if antes[etiqueta] != leer(producto)
            }
            partes = [cambios.describir(lo_que_cambio)] if lo_que_cambio else []
            # B-05-006: el stock decide si está Agotado. Reponer lo vuelve a la venta.
            estado = _estado_por_stock(producto)
            if estado != producto.estado:
                nuevo = dict(Producto.ESTADO_CHOICES)[estado]
                partes.append(f"estado: «{producto.get_estado_display()}» → «{nuevo}»")
                Producto.objects.filter(pk=producto.pk).update(estado=estado)
                producto.estado = estado
            restock.al_subir_stock(
                producto,
                anterior.stock,
                producto.stock,
                origen=self.request.build_absolute_uri("/").rstrip("/"),
            )
            if agregadas or quitadas:
                partes.append(galeria.describir(agregadas, quitadas))
            partes.extend(orden_y_portada)
            if partes:
                RegistroAuditoria.registrar(
                    RegistroAuditoria.MODIFICACION_PRODUCTO,
                    actor=self.request.user,
                    ip=obtener_ip(self.request),
                    objetivo=producto,
                    detalle=f"{producto.codigo} · " + "; ".join(partes),
                )
        return producto, partes

    @staticmethod
    def _campos_auditados(producto):
        """Qué se registra en el log, con su par anterior → nuevo.

        Los comunes primero y los del rubro después. La sinopsis no entra
        entera —un log con párrafos adentro deja de poder leerse—: se dice
        cuántos caracteres tiene, y el texto completo se compara aparte para
        no perder un cambio que no altere el largo.
        """
        auditados = {
            "título": lambda p: p.titulo,
            "tipo": lambda p: str(p.tipo),
            "precio": lambda p: f"${p.precio}",
            "stock": lambda p: str(p.stock),
            "código de barras": lambda p: p.codigo_barras or "sin declarar",
            "solo adultos": lambda p: "sí" if p.solo_adultos else "no",
            "etiquetas": lambda p: (
                ", ".join(e.nombre for e in p.etiquetas.order_by("nombre")) or "ninguna"
            ),
            "portada": lambda p: p.portada.name.rsplit("/", 1)[-1] if p.portada else "pendiente",
            "descripción": _sinopsis,
        }
        if producto.clase == Producto.EDITORIAL:
            auditados.update(
                {
                    "volumen": lambda p: str(p.volumen),
                    "ISBN": lambda p: p.isbn or "sin declarar",
                    "editorial": lambda p: str(p.editorial),
                    "formato": lambda p: str(p.formato) if p.formato else "sin formato",
                    "autor": lambda p: p.autor or "sin declarar",
                    "fecha de llegada": lambda p: (
                        f"{p.fecha_llegada:%d/%m/%Y}" if p.fecha_llegada else "sin fecha"
                    ),
                    "precio fijado a mano": lambda p: "sí" if p.precio_manual else "no",
                }
            )
        else:
            auditados["marca"] = lambda p: p.marca or "sin marca"
        return auditados


class _Sinopsis(str):
    """El texto de la sinopsis que se compara entero y se muestra resumido."""

    def __new__(cls, texto):
        objeto = super().__new__(cls, f"{len(texto)} caracteres" if texto else "vacía")
        objeto.texto = texto
        return objeto

    def __eq__(self, otro):
        return isinstance(otro, _Sinopsis) and self.texto == otro.texto

    def __ne__(self, otro):
        return not self == otro

    __hash__ = str.__hash__


def _sinopsis(producto):
    return _Sinopsis(producto.descripcion or "")


class ProductoBajaView(CatalogoAdminMixin, DetailView):
    """CU-CAT-BAJ — Dar de Baja Producto.

    El GET **no** es un trámite de confirmación: es el informe de impacto que el
    Administrador tiene que leer antes de decidir, y por eso la baja es una
    pantalla propia y no un botón con un cartel del navegador. Es el mismo
    criterio con el que se construyó la baja de proveedor de CU-PRV-BAJ.

    **La baja es lógica, nunca un `DELETE`.** Lo pide la postcondición del CU:
    el producto se conserva en el inventario interno y en el historial de ventas.

    Los pasos 7 a 9 —resolver las referencias y avisar a los clientes— los hace
    `services.confirmar_baja_de_producto` (B-02-006).
    """

    model = Producto
    template_name = "catalog/producto_baja.html"
    context_object_name = "producto"

    def get_object(self, queryset=None):
        return super().get_object(queryset).especifico

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        contexto["impacto"] = services.calcular_impacto_de_baja(self.object)
        return contexto

    def post(self, request, *args, **kwargs):
        producto = self.get_object()

        # Se vuelve a chequear acá y no solo escondiendo el botón: un doble envío
        # no debe registrar dos bajas del mismo producto.
        if producto.estado == Producto.DESCATALOGADO:
            messages.info(request, f"«{producto.titulo}» ya estaba fuera del catálogo.")
            return redirect("catalog:producto_detalle", pk=producto.pk)

        # Un título cancelado por la editorial no llega nunca y no se reactiva.
        # Descatalogarlo lo movería a un estado del que sí se vuelve, borrando la
        # única marca de que ese tomo no existe.
        if producto.estado in Producto.ESTADOS_TERMINALES:
            messages.error(
                request,
                f"«{producto.titulo}» está {producto.get_estado_display().lower()} "
                "y no admite otra baja.",
            )
            return redirect("catalog:producto_detalle", pk=producto.pk)

        hecho = services.confirmar_baja_de_producto(
            producto, actor=request.user, ip=obtener_ip(request)
        )
        resuelto = [
            f"{hecho.suscripciones} aviso(s) de stock cancelado(s)" if hecho.suscripciones else "",
            (
                f"{len(hecho.ofertas_dadas_de_baja)} oferta(s) dada(s) de baja"
                if hecho.ofertas_dadas_de_baja
                else ""
            ),
            f"{hecho.carritos} carrito(s) avisado(s)" if hecho.carritos else "",
        ]
        resuelto = ", ".join(parte for parte in resuelto if parte)
        messages.success(
            request,
            f"«{producto.titulo}» salió del catálogo. Sigue en el inventario interno."
            + (f" Se resolvió: {resuelto}." if resuelto else ""),
        )
        return redirect("catalog:producto_detalle", pk=producto.pk)


class ProductoReactivarView(CatalogoAdminMixin, DetailView):
    """La vuelta de la baja de CU-CAT-BAJ. La describe **CU-CAT-REA**.

    Reactivar Producto Descatalogado, con el par solicitar/confirmar de CO-035 y
    CO-036. Existe porque sin ella la baja es un camino de ida, y el propio
    CU-CAT-EDI quedaría sin sentido en su parte más explícita: su precondición
    dice que un producto se edita estando de baja, y mantener al día los datos de
    algo que no puede volver no sirve para nada.

    Volver a cargarlo tampoco sería equivalente: el código es único e inmutable,
    así que el producto reingresaría con otra identidad y perdería su historial
    de auditoría, que es justo lo que la baja lógica se propuso conservar.

    Vuelve a **Activo** y no al estado que tenía antes. Un producto que estaba en
    Pre-venta cuando se lo dio de baja lleva meses fuera del catálogo, y su fecha
    de llegada ya no describe nada.
    """

    model = Producto
    template_name = "catalog/producto_reactivar.html"
    context_object_name = "producto"

    def get_object(self, queryset=None):
        return super().get_object(queryset).especifico

    def _fecha_vencida(self, producto):
        """`CO-036` E2: la fecha de llegada programada ya pasó."""
        llegada = getattr(producto, "fecha_llegada", None)
        return llegada is not None and llegada < timezone.localdate()

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        contexto["fecha_vencida"] = self._fecha_vencida(self.object)
        return contexto

    def post(self, request, *args, **kwargs):
        producto = self.get_object()

        # CO-035 E1: el cancelado por editorial es terminal; no "ya está en el catálogo".
        if producto.estado in Producto.ESTADOS_TERMINALES:
            messages.error(
                request,
                f"«{producto.titulo}» está {producto.get_estado_display().lower()}: "
                "es un estado terminal y no se reactiva.",
            )
            return redirect("catalog:producto_detalle", pk=producto.pk)
        if producto.estado != Producto.DESCATALOGADO:
            messages.info(request, f"«{producto.titulo}» ya está en el catálogo.")
            return redirect("catalog:producto_detalle", pk=producto.pk)
        fecha_vencida = self._fecha_vencida(producto)

        with transaction.atomic():
            anterior = producto.get_estado_display()
            producto.estado = Producto.ACTIVO
            producto.save(update_fields=["estado"])
            # CO-036 pide el estado anterior y el nuevo en la entrada.
            RegistroAuditoria.registrar(
                RegistroAuditoria.REACTIVACION_PRODUCTO,
                actor=request.user,
                ip=obtener_ip(request),
                objetivo=producto,
                detalle=(
                    f"{producto.codigo} · «{producto.titulo}» · estado anterior: {anterior} → "
                    f"{producto.get_estado_display()}"
                    + (" · la fecha de llegada quedó sin efecto" if fecha_vencida else "")
                ),
            )

        messages.success(
            request,
            f"«{producto.titulo}» volvió al catálogo."
            + (
                " Su fecha de llegada programada ya pasó y quedó sin efecto."
                if fecha_vencida
                else ""
            ),
        )
        return redirect("catalog:producto_detalle", pk=producto.pk)
