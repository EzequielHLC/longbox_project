"""Pantallas de proveedores editoriales (CU-18 a CU-21).

Todas son de backoffice y exclusivas del Administrador, validado del lado del
servidor (RNF-03). Sistema visual: **modo operativo**; ninguna es pública.

El orden en que conviene leerlas es el del ciclo de vida de un proveedor:
listado (CU-21) → alta (CU-18) → ficha (CU-21 paso 4) → edición (CU-19) → baja
(CU-20) y su vuelta.

Al final va la **cola de correos**, que no es de ningún CU: es la antesala del
pipeline de CU-04, donde cada correo espera una decisión antes de que se gaste
un solo ciclo en procesarlo.
"""

from django.conf import settings
from django.contrib import messages
from django.db import transaction
from django.db.models import Count, Q
from django.shortcuts import redirect, render
from django.views.generic import CreateView, DetailView, ListView, TemplateView, UpdateView

from apps.accounts.models import Usuario
from apps.core import llm
from apps.core.mixins import RolRequeridoMixin
from apps.core.models import RegistroAuditoria
from apps.core.utils import obtener_ip
from apps.suppliers import extraccion, services
from apps.suppliers.forms import (
    DescarteDeCorreoForm,
    ProveedorForm,
    PruebaDelModeloForm,
)
from apps.suppliers.models import CorreoProveedor, Proveedor

MENSAJE_YA_ESTA_ACTIVO = "El proveedor ya está activo."
MENSAJE_YA_ESTA_INACTIVO = "El proveedor ya está dado de baja."
MENSAJE_CORREO_YA_RESUELTO = "Este correo ya fue resuelto."


class ProveedoresMixin(RolRequeridoMixin):
    """Los cuatro CU del módulo son exclusivos del Administrador."""

    roles_permitidos = (Usuario.ADMINISTRADOR,)


def _conflicto_de(formulario):
    """El proveedor con el que chocó un alta o una edición, si hubo choque.

    E2 de CU-18 pide informar el conflicto **con enlace a la ficha del proveedor
    existente**: no alcanza con saber que hay choque, hace falta contra quién.
    El formulario lo encontró al validar y lo deja anotado; acá se elige cuál
    mostrar cuando chocan los dos campos a la vez.
    """
    return getattr(formulario, "conflicto_razon_social", None) or getattr(
        formulario, "conflicto_correo", None
    )


class ProveedorListaView(ProveedoresMixin, ListView):
    """CU-21 — Consultar Proveedores.

    Es el punto de entrada del módulo: desde acá se llega al alta, a la ficha y,
    por la ficha, a la edición y a la baja. Solo lectura, y el CU es explícito en
    que **no genera entrada de auditoría**: consultar no es operar.
    """

    context_object_name = "proveedores"
    paginate_by = 25

    def get_template_names(self):
        # El buscador refresca la tabla mientras se escribe pidiendo la misma
        # URL con `?parcial=1`. Sin JavaScript el formulario se envía normal y
        # cae en la plantilla completa: la pantalla funciona igual.
        if self.request.GET.get("parcial"):
            return ["suppliers/_tabla_proveedores.html"]
        return ["suppliers/proveedor_lista.html"]

    def get_queryset(self):
        # CU-21 paso 2 pide mostrar la cantidad de productos vinculados en cada
        # fila. Se anota en la consulta y no se cuenta por fila: con veinte
        # proveedores serían veinte consultas más.
        proveedores = Proveedor.objects.select_related("editorial", "tipo_por_defecto").annotate(
            cantidad_productos=Count("productos")
        )

        busqueda = self.request.GET.get("q", "").strip()
        if busqueda:
            proveedores = proveedores.filter(
                Q(razon_social__icontains=busqueda)
                | Q(correo_comercial__icontains=busqueda)
                | Q(nombre_contacto__icontains=busqueda)
            )

        # Un valor inventado en la query string se ignora: no rompe ni filtra de
        # más.
        estado = self.request.GET.get("estado", "")
        if estado in dict(Proveedor.ESTADO_CHOICES):
            proveedores = proveedores.filter(estado=estado)

        # El orden alfabético del paso 2 se repite acá aunque el modelo ya lo
        # declare: Django **no** aplica el `ordering` del `Meta` a una consulta
        # con `annotate`, porque esa agrupa, y sin esta línea el listado sale en
        # el orden en que la base tenga ganas de devolver las filas.
        return proveedores.order_by("razon_social")

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        estado = self.request.GET.get("estado", "")
        contexto["busqueda"] = self.request.GET.get("q", "").strip()
        contexto["estado_elegido"] = estado if estado in dict(Proveedor.ESTADO_CHOICES) else ""
        contexto["estados"] = Proveedor.ESTADO_CHOICES
        # Las cifras se calculan sobre el padrón completo y no sobre el recorte
        # filtrado: son el estado del módulo, no del filtro que se está mirando.
        #
        # "Activos" y "alimentan el pipeline" son dos cifras distintas a
        # propósito: la diferencia entre las dos son los proveedores activos con
        # el procesamiento apagado, que es justo el grupo que de otro modo
        # quedaría invisible y que explica por qué de alguien no llega nada.
        contexto["resumen"] = Proveedor.objects.aggregate(
            total=Count("pk"),
            activos=Count("pk", filter=Q(estado=Proveedor.ACTIVO)),
            alimentan=Count("pk", filter=Q(estado=Proveedor.ACTIVO, procesa_novedades=True)),
            inactivos=Count("pk", filter=Q(estado=Proveedor.INACTIVO)),
        )
        return contexto


class ProveedorDetalleView(ProveedoresMixin, DetailView):
    """CU-21 paso 4 — la ficha completa.

    Es también el destino del enlace que E2 del CU-18 exige al informar un
    conflicto de alta, y desde donde arrancan CU-19 y CU-20.
    """

    model = Proveedor
    template_name = "suppliers/proveedor_detalle.html"
    context_object_name = "proveedor"

    def get_queryset(self):
        return Proveedor.objects.select_related("editorial", "tipo_por_defecto")

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        # Los primeros productos alcanzan para reconocer al proveedor; el
        # inventario completo tiene su propia pantalla y su propio buscador.
        contexto["productos"] = self.object.productos.select_related(
            "editorial", "tipo", "formato"
        )[:25]
        contexto["cantidad_productos"] = self.object.productos.count()
        return contexto


class ProveedorAltaView(ProveedoresMixin, CreateView):
    """CU-18 — Registrar Proveedor Editorial."""

    model = Proveedor
    form_class = ProveedorForm
    template_name = "suppliers/proveedor_formulario.html"

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        contexto["titulo"] = "Nuevo proveedor"
        contexto["descripcion"] = (
            "El correo comercial habilita el procesamiento automático de las novedades "
            "que envíe este proveedor."
        )
        contexto["conflicto"] = _conflicto_de(contexto["form"])
        return contexto

    def form_valid(self, form):
        with transaction.atomic():
            proveedor = form.save()
            RegistroAuditoria.registrar(
                accion=RegistroAuditoria.ALTA_PROVEEDOR,
                actor=self.request.user,
                objetivo=proveedor,
                objetivo_email=proveedor.correo_comercial,
                ip=obtener_ip(self.request),
                detalle=f"«{proveedor.razon_social}» · {proveedor.correo_comercial}",
            )

        self.object = proveedor
        messages.success(
            self.request,
            f"Se registró «{proveedor.razon_social}». Su correo comercial ya está "
            "habilitado como remitente válido.",
        )
        # CU-18 paso 6: el alta termina mostrando la ficha del proveedor creado.
        return redirect("suppliers:proveedor_detalle", pk=proveedor.pk)


class ProveedorEdicionView(ProveedoresMixin, UpdateView):
    """CU-19 — Editar Proveedor Editorial.

    A diferencia de la edición de un usuario del sistema, un proveedor
    **inactivo sí se puede editar**: la precondición del CU dice "cualquier
    estado" y acá no hay nada que congelar. Una cuenta dada de baja guarda
    permisos que reviven solos al reactivarla; un proveedor inactivo no habilita
    nada mientras esté de baja, porque el filtro de remitentes mira el estado
    antes que el correo.
    """

    model = Proveedor
    form_class = ProveedorForm
    template_name = "suppliers/proveedor_formulario.html"
    context_object_name = "proveedor"

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        contexto["titulo"] = "Editar proveedor"
        contexto["descripcion"] = (
            "Cambiar el correo comercial redirige el pipeline de novedades: el anterior "
            "deja de reconocerse en cuanto se confirma."
        )
        contexto["conflicto"] = _conflicto_de(contexto["form"])
        return contexto

    def form_valid(self, form):
        # Copia del estado previo *antes* de que el formulario toque la
        # instancia: el CU pide auditar valores anteriores y nuevos, y con el
        # objeto ya modificado los anteriores se pierden.
        anterior = Proveedor.objects.get(pk=self.object.pk)

        with transaction.atomic():
            proveedor = form.save()
            cambios = services.cambios_entre(anterior, proveedor)
            if cambios:
                RegistroAuditoria.registrar(
                    accion=RegistroAuditoria.MODIFICACION_PROVEEDOR,
                    actor=self.request.user,
                    objetivo=proveedor,
                    objetivo_email=proveedor.correo_comercial,
                    ip=obtener_ip(self.request),
                    detalle=services.describir_cambios(cambios),
                )

        self.object = proveedor
        if anterior.correo_comercial != proveedor.correo_comercial:
            messages.success(
                self.request,
                f"Se actualizó «{proveedor.razon_social}». Desde ahora solo se procesan "
                f"los mensajes que lleguen desde {proveedor.correo_comercial}.",
            )
        else:
            messages.success(self.request, f"Se actualizó «{proveedor.razon_social}».")
        return redirect("suppliers:proveedor_detalle", pk=proveedor.pk)


class ProveedorBajaView(ProveedoresMixin, DetailView):
    """CU-20 — Dar de Baja Proveedor Editorial.

    El GET **no** es un trámite de confirmación: es el paso 3 del CU, el informe
    de impacto que el Administrador tiene que leer antes de decidir. Por eso la
    baja es una pantalla propia y no un botón con un cartel del navegador.
    """

    model = Proveedor
    template_name = "suppliers/proveedor_baja.html"
    context_object_name = "proveedor"

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        contexto["impacto"] = services.calcular_impacto_de_baja(self.object)
        return contexto

    def post(self, request, *args, **kwargs):
        proveedor = self.get_object()
        # La precondición del CU es estado Activo. Se vuelve a chequear acá y no
        # solo escondiendo el botón: un POST repetido —el clásico doble envío—
        # no debe registrar dos bajas del mismo proveedor.
        if not proveedor.esta_activo:
            messages.info(request, MENSAJE_YA_ESTA_INACTIVO)
            return redirect("suppliers:proveedor_detalle", pk=proveedor.pk)

        impacto = services.calcular_impacto_de_baja(proveedor)
        with transaction.atomic():
            proveedor.estado = Proveedor.INACTIVO
            proveedor.save(update_fields=["estado", "actualizado_en"])
            RegistroAuditoria.registrar(
                accion=RegistroAuditoria.BAJA_PROVEEDOR,
                actor=request.user,
                objetivo=proveedor,
                objetivo_email=proveedor.correo_comercial,
                ip=obtener_ip(request),
                detalle=(
                    f"«{proveedor.razon_social}» · productos vinculados: "
                    f"{impacto.productos_vinculados}"
                ),
            )

        messages.success(
            request,
            f"Se dio de baja «{proveedor.razon_social}». Su correo dejó de reconocerse "
            "como remitente válido; sus productos y su historial se conservan.",
        )
        return redirect("suppliers:proveedor_detalle", pk=proveedor.pk)


class ProveedorReactivarView(ProveedoresMixin, DetailView):
    """La vuelta de la baja de CU-20. **Ningún CU la describe.**

    Se agrega porque sin ella la baja es una trampa: la razón social y el correo
    son únicos a nivel de base *en cualquier estado*, así que un proveedor
    inactivo bloquea sus propios datos para siempre y retomar la relación
    comercial obligaría a inventarle una razón social distinta. Y el motivo que
    el propio CU-20 le da a la baja —"cambio de distribuidor o cese de relación
    comercial"— describe justamente situaciones que se revierten.

    A diferencia de la reactivación de una cuenta de personal, acá no hay
    credencial que renovar: un proveedor no inicia sesión. Vuelve directo a
    Activo, y con eso su correo vuelve al filtro de remitentes de CU-04.
    """

    model = Proveedor
    template_name = "suppliers/proveedor_reactivar.html"
    context_object_name = "proveedor"

    def post(self, request, *args, **kwargs):
        proveedor = self.get_object()
        if proveedor.esta_activo:
            messages.info(request, MENSAJE_YA_ESTA_ACTIVO)
            return redirect("suppliers:proveedor_detalle", pk=proveedor.pk)

        with transaction.atomic():
            proveedor.estado = Proveedor.ACTIVO
            proveedor.save(update_fields=["estado", "actualizado_en"])
            RegistroAuditoria.registrar(
                accion=RegistroAuditoria.REACTIVACION_PROVEEDOR,
                actor=request.user,
                objetivo=proveedor,
                objetivo_email=proveedor.correo_comercial,
                ip=obtener_ip(request),
                detalle=f"«{proveedor.razon_social}» vuelve al filtro de remitentes",
            )

        messages.success(
            request,
            f"Se reactivó «{proveedor.razon_social}». Sus mensajes vuelven a procesarse "
            f"desde {proveedor.correo_comercial}.",
        )
        return redirect("suppliers:proveedor_detalle", pk=proveedor.pk)


# ---------------------------------------------------------------------------
# Cola de correos — la antesala del pipeline de CU-04
# ---------------------------------------------------------------------------


class CorreoListaView(ProveedoresMixin, ListView):
    """Los correos recibidos, esperando una decisión.

    No sale de ningún caso de uso: la fuente da por sentado que todo correo de
    un remitente registrado se procesa solo. Esta pantalla es la contraparte de
    la aprobación explícita, y también el camino de respaldo — la notificación
    al celular puede fallar, y en ese caso la cola tiene que seguir estando y
    poder resolverse desde acá.
    """

    context_object_name = "correos"
    paginate_by = 25

    def get_template_names(self):
        if self.request.GET.get("parcial"):
            return ["suppliers/_tabla_correos.html"]
        return ["suppliers/correo_lista.html"]

    def get_queryset(self):
        consulta = CorreoProveedor.objects.select_related("proveedor")

        busqueda = self.request.GET.get("q", "").strip()
        if busqueda:
            consulta = consulta.filter(
                Q(asunto__icontains=busqueda)
                | Q(remitente__icontains=busqueda)
                | Q(proveedor__razon_social__icontains=busqueda)
            )

        estado = self.request.GET.get("estado", "")
        if estado in dict(CorreoProveedor.ESTADO_CHOICES):
            consulta = consulta.filter(estado=estado)

        return consulta

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        estado = self.request.GET.get("estado", "")
        contexto["busqueda"] = self.request.GET.get("q", "").strip()
        contexto["estado_elegido"] = (
            estado if estado in dict(CorreoProveedor.ESTADO_CHOICES) else ""
        )
        contexto["estados"] = CorreoProveedor.ESTADO_CHOICES
        contexto["pendientes"] = CorreoProveedor.objects.pendientes().count()
        return contexto


class CorreoDetalleView(ProveedoresMixin, DetailView):
    """El correo archivado, lo que se extrajo de él, y la decisión.

    Muestra el **contenido extraído** y no el HTML original a propósito: es
    exactamente lo que se le va a mandar al modelo, y poder leerlo antes de
    aprobar es lo que permite darse cuenta de que la extracción salió mal
    —columnas corridas, una tabla que no se reconoció— sin haber gastado nada.

    El descarte se resuelve acá, en el `POST` de esta misma vista, y no en una
    pantalla aparte: la decisión se toma mirando el contenido, así que el
    formulario tiene que estar donde está el contenido.
    """

    model = CorreoProveedor
    template_name = "suppliers/correo_detalle.html"
    context_object_name = "correo"

    def get_queryset(self):
        return CorreoProveedor.objects.select_related("proveedor", "resuelto_por")

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        contexto.setdefault("form", DescarteDeCorreoForm())
        # Las líneas que son filas de una tabla de datos se distinguen de la
        # prosa: es lo primero que hay que mirar para saber si la extracción
        # entendió la estructura o la aplanó.
        contexto["lineas"] = [
            {"texto": linea, "es_fila": linea.startswith("|")}
            for linea in self.object.contenido.splitlines()
        ]
        return contexto

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()

        # Se vuelve a chequear acá y no solo escondiendo el botón: un correo ya
        # resuelto no puede volver a resolverse por un doble envío ni por un
        # POST directo (RNF-03).
        if not self.object.esta_abierto:
            messages.info(request, MENSAJE_CORREO_YA_RESUELTO)
            return redirect("suppliers:correo_detalle", pk=self.object.pk)

        formulario = DescarteDeCorreoForm(request.POST)
        if not formulario.is_valid():
            contexto = self.get_context_data(object=self.object, form=formulario)
            return render(request, self.template_name, contexto)

        motivo = formulario.cleaned_data["motivo"]
        asunto = self.object.asunto or "sin asunto"
        with transaction.atomic():
            services.descartar(self.object, request.user, motivo)
            RegistroAuditoria.registrar(
                accion=RegistroAuditoria.CORREO_DESCARTADO,
                actor=request.user,
                objetivo=self.object,
                ip=obtener_ip(request),
                detalle=f"«{asunto}» de {self.object.proveedor}: {motivo}",
            )

        messages.success(request, "Se descartó el correo. No va a procesarse.")
        return redirect("suppliers:correo_detalle", pk=self.object.pk)


# ---------------------------------------------------------------------------
# Diagnóstico del modelo de lenguaje
# ---------------------------------------------------------------------------


class DiagnosticoLLMView(ProveedoresMixin, TemplateView):
    """Si el modelo está vivo, y qué entiende cuando se le manda algo.

    No es de ningún caso de uso: es una herramienta de operación. Existe porque
    el pipeline de CU-04 depende de un servicio que corre **afuera de Django** y
    que se apaga sin avisar, y sin esta pantalla la única forma de descubrirlo
    es que un correo quede en estado fallido con un mensaje genérico.

    Separa los dos motivos por los que una extracción puede fallar, que se
    arreglan en lugares distintos:

    - **El servicio no está.** Se responde con un `GET` barato al catálogo de
      modelos, que contesta en milisegundos.
    - **El servicio está y la respuesta no sirve.** Eso solo se ve mandándole
      algo de verdad, y por eso el banco de pruebas muestra lo que se envió, lo
      que volvió en crudo y lo que el sistema logró interpretar.

    Ese último punto es también lo que la vuelve útil para mostrar el sistema:
    el prompt, la respuesta y las validaciones dejan de ser algo que hay que
    creer y pasan a verse en pantalla.
    """

    template_name = "suppliers/diagnostico_llm.html"

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        # El estado se consulta en cada carga: es barato y es justamente lo que
        # se viene a mirar. Si el `post` ya lo consultó, se reusa — preguntarlo
        # dos veces en el mismo pedido no aporta nada.
        if "estado" not in contexto:
            contexto["estado"] = llm.estado()
        contexto["configuracion"] = {
            "url": settings.LLM_URL,
            "modelo": settings.LLM_MODELO or "el que esté cargado en el servidor",
            "timeout": settings.LLM_TIMEOUT,
            "temperatura": settings.LLM_TEMPERATURA,
        }
        contexto.setdefault("form", PruebaDelModeloForm())
        contexto["prompt"] = extraccion.SISTEMA
        contexto["version_prompt"] = extraccion.VERSION_PROMPT
        return contexto

    def post(self, request, *args, **kwargs):
        formulario = PruebaDelModeloForm(request.POST)

        # El estado se consulta **antes** de intentar la extracción, y no es un
        # detalle de orden: con el servicio caído, llamar al modelo esperaría el
        # timeout largo entero —minutos— para terminar fallando por lo mismo que
        # este chequeo de cuatro segundos ya sabe. La pantalla que existe para
        # avisar que el servicio no está no puede ser la que más tarda cuando no
        # está.
        estado = llm.estado()
        if not formulario.is_valid():
            return self.render_to_response(self.get_context_data(form=formulario, estado=estado))

        if estado.disponible:
            # Se usa **la misma función que el pipeline**, no una copia
            # simplificada: una prueba que ejercite otro camino puede pasar
            # mientras el camino real está roto, que es la peor clase de
            # diagnóstico.
            resultado = extraccion.extraer(
                formulario.cleaned_data["contenido"], cids=formulario.cids
            )
        else:
            resultado = extraccion.Extraccion(error=llm.SIN_SERVICIO)

        return self.render_to_response(
            self.get_context_data(form=formulario, estado=estado, resultado=resultado)
        )
