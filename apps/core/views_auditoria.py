"""CU-AUD-CON — Consultar el Log de Auditoría (`CO-205`, `CO-206`, `CO-129`).

La consulta no se audita, deliberadamente: auditar la lectura del log llenaría
el log de su propia lectura. La exportación sí, porque saca datos del sistema.

**El log no se escribe desde acá.** Lo escriben todos los casos de uso como
parte de sus postcondiciones, y es inmutable en el modelo (I-13). Estas
direcciones responden 403 a cualquier método de escritura, también para el
Administrador (comentario de la ficha), antes de tocar nada.
"""

import csv
import re

from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import PermissionDenied
from django.core.files.storage import default_storage
from django.http import StreamingHttpResponse
from django.utils import timezone
from django.utils.dateparse import parse_date
from django.views import View
from django.views.generic import DetailView, ListView

from apps.core.mixins import RolRequeridoMixin
from apps.core.models import RegistroAuditoria
from apps.core.utils import celda_csv, obtener_ip

Usuario = get_user_model()

POR_PAGINA = 50

# C-15 (a): el filtro ofrece las acciones del enumerado, agrupadas para
# encontrarlas. Las nueve categorías de la ficha no están mapeadas a las
# acciones en ninguna parte, y el mapeo no se inventa (B-16-001).
GRUPOS_DE_ACCIONES = (
    (
        "Sesiones y contraseñas",
        ("inicio_sesion", "cierre_sesion", "bloqueo_por_intentos", "cambio_contrasena"),
    ),
    (
        "Cuentas",
        (
            "alta_administrador_inicial",
            "alta_usuario",
            "modificacion_usuario",
            "baja_usuario",
            "reactivacion_usuario",
            "reenvio_activacion",
            "activacion_cuenta",
            "eliminacion_pendiente",
            "registro_cliente",
            "baja_cuenta_cliente",
        ),
    ),
    (
        "Productos",
        (
            "alta_lote_editorial",
            "alta_producto_no_editorial",
            "modificacion_producto",
            "baja_producto",
            "reactivacion_producto",
        ),
    ),
    ("Catálogos", ("alta_catalogo", "modificacion_catalogo", "baja_catalogo")),
    (
        "Precios y parámetros",
        (
            "alta_precio_referencia",
            "modificacion_precio_referencia",
            "baja_precio_referencia",
            "parametro_modificado",
        ),
    ),
    (
        "Proveedores y correos",
        (
            "alta_proveedor",
            "modificacion_proveedor",
            "baja_proveedor",
            "reactivacion_proveedor",
            "correo_descartado",
            "borradores_generados",
            "borrador_confirmado",
            "borrador_rechazado",
            "sesion_revision_cerrada",
            "diagnostico_llm",
            "disponibilidad_llm",
            "cambio_modelo_propuesto",
            "cambio_modelo",
        ),
    ),
    (
        "Contenido de la tienda",
        (
            "publicacion_faq",
            "modificacion_identidad_visual",
            "alta_banner",
            "modificacion_banner",
            "baja_banner",
        ),
    ),
    (
        "Exportaciones",
        ("exportacion_inventario", "exportacion_auditoria", "exportacion_reporte"),
    ),
    (
        "Restock y pedidos a proveedores",
        (
            "propuesta_restock",
            "despacho_restock",
            "descarte_restock",
            "cierre_propuesta_restock",
            "pedido_a_proveedor",
            "llegada_pedido",
            "respuesta_proveedor",
            "cierre_sin_recibir",
        ),
    ),
    (
        "Perfil y avisos",
        ("vinculo_telegram", "desvinculo_telegram", "canales_de_aviso"),
    ),
)


def acciones_agrupadas():
    nombres = dict(RegistroAuditoria.ACCION_CHOICES)
    return [
        (grupo, [(accion, nombres[accion]) for accion in acciones if accion in nombres])
        for grupo, acciones in GRUPOS_DE_ACCIONES
    ]


class SoloLecturaMixin(RolRequeridoMixin):
    """Sólo el Administrador, y sólo para leer.

    Cualquier otro método recibe 403 y no 405: la ficha lo pide así, y lo que
    se comunica es «no se puede escribir el log», no «este verbo no existe».
    """

    roles_permitidos = (Usuario.ADMINISTRADOR,)
    metodos_de_lectura = ("get", "head", "options")

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and request.method.lower() not in self.metodos_de_lectura:
            raise PermissionDenied("El log de auditoría no admite escritura.")
        return super().dispatch(request, *args, **kwargs)


class FiltrosDelLog:
    """Los filtros del paso 3, leídos una sola vez para el listado y el archivo.

    Un valor inválido en la dirección se ignora: no rompe ni filtra de más.
    """

    def __init__(self, parametros):
        self.actor = parametros.get("actor", "").strip()
        rol = parametros.get("rol", "")
        self.rol = rol if rol in dict(Usuario.ROL_CHOICES) else ""
        accion = parametros.get("accion", "")
        self.accion = accion if accion in dict(RegistroAuditoria.ACCION_CHOICES) else ""
        entidad = parametros.get("entidad", "")
        self.entidad = int(entidad) if entidad.isdigit() else None
        self.desde = (
            parse_date(parametros.get("desde", "") or "") if parametros.get("desde") else None
        )
        self.hasta = (
            parse_date(parametros.get("hasta", "") or "") if parametros.get("hasta") else None
        )

    @property
    def activos(self):
        return any([self.actor, self.rol, self.accion, self.entidad, self.desde, self.hasta])

    def aplicar(self, entradas):
        if self.actor:
            entradas = entradas.filter(actor_email__icontains=self.actor)
        if self.rol:
            # C-15 (a): el rol **actual** de la cuenta. Una cuenta eliminada no
            # entra en ningún rol; la pantalla lo dice.
            entradas = entradas.filter(actor__rol=self.rol)
        if self.accion:
            entradas = entradas.filter(accion=self.accion)
        if self.entidad:
            entradas = entradas.filter(objetivo_tipo_id=self.entidad)
        if self.desde:
            entradas = entradas.filter(ocurrido_en__date__gte=self.desde)
        if self.hasta:
            entradas = entradas.filter(ocurrido_en__date__lte=self.hasta)
        return entradas

    def legibles(self):
        """Los filtros tal como se aplicaron, para el registro de la exportación."""
        partes = []
        if self.actor:
            partes.append(f"actor contiene «{self.actor}»")
        if self.rol:
            partes.append(f"rol {dict(Usuario.ROL_CHOICES)[self.rol]}")
        if self.accion:
            partes.append(f"acción {dict(RegistroAuditoria.ACCION_CHOICES)[self.accion]}")
        if self.entidad:
            tipo = ContentType.objects.filter(pk=self.entidad).first()
            partes.append(f"entidad {tipo.name if tipo else self.entidad}")
        if self.desde:
            partes.append(f"desde {self.desde:%d/%m/%Y}")
        if self.hasta:
            partes.append(f"hasta {self.hasta:%d/%m/%Y}")
        return "; ".join(partes) or "sin filtros"


def _entradas():
    return RegistroAuditoria.objects.select_related("objetivo_tipo").order_by("-ocurrido_en", "-pk")


class LogListaView(SoloLecturaMixin, ListView):
    """`CO-205`: de la más reciente a la más antigua, de a 50."""

    template_name = "core/auditoria_lista.html"
    context_object_name = "entradas"
    paginate_by = POR_PAGINA

    def get_queryset(self):
        self.filtros = FiltrosDelLog(self.request.GET)
        return self.filtros.aplicar(_entradas())

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        parametros = self.request.GET.copy()
        parametros.pop("page", None)
        contexto.update(
            {
                "filtros": self.filtros,
                "acciones": acciones_agrupadas(),
                "roles": Usuario.ROL_CHOICES,
                "entidades": ContentType.objects.filter(
                    pk__in=RegistroAuditoria.objects.exclude(objetivo_tipo=None)
                    .values("objetivo_tipo")
                    .distinct()
                ).order_by("model"),
                "parametros": parametros.urlencode(),
            }
        )
        return contexto


class LogDetalleView(SoloLecturaMixin, DetailView):
    """`CO-206`: la entrada completa, con el valor anterior y el nuevo.

    Desde la segunda parte del plan 16 cada modificación guarda, campo por
    campo, qué se cambió y cómo estaba antes, y se presenta en una tabla; si el
    valor es una imagen, se muestra la imagen. Las entradas anteriores no tienen
    esa lista y se presentan por su detalle, tal como se registró.
    """

    model = RegistroAuditoria
    template_name = "core/auditoria_detalle.html"
    context_object_name = "entrada"

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        cambios = self.object.cambios or []
        # Una entrada anterior a la lista estructurada: sus reemplazos se leen del
        # detalle sólo para mostrarlos en la tabla. La entrada no se toca.
        contexto["cambios_leidos"] = not cambios
        if not cambios:
            cambios = reemplazos_del_detalle(self.object.accion, self.object.detalle)
        contexto["cambios"] = [{**cambio, **_urls_de_imagen(cambio)} for cambio in cambios]
        return contexto


# Lo que el sistema escribió siempre igual: «campo: «antes» → «después»».
_REEMPLAZO_CITADO = re.compile(
    r"(?:^|(?<=[;·:] ))(?P<campo>[^:;·«»\n]+?): «(?P<antes>.*?)» → «(?P<despues>.*?)»", re.S
)
# Sin comillas («margen global: 40 % → 45 %»): sólo en las acciones que modifican,
# un reemplazo por tramo y sin otra oración en el medio.
_REEMPLAZO_SIMPLE = re.compile(r"^(?P<campo>[^:«»]+): (?P<antes>[^→«»]+?) → (?P<despues>[^→«»]+)$")
_ACCIONES_QUE_MODIFICAN = {
    RegistroAuditoria.MODIFICACION_USUARIO,
    RegistroAuditoria.MODIFICACION_DATOS_CLIENTE,
    RegistroAuditoria.MODIFICACION_PRODUCTO,
    RegistroAuditoria.PARAMETRO_MODIFICADO,
    RegistroAuditoria.MODIFICACION_PROVEEDOR,
    RegistroAuditoria.MODIFICACION_CATALOGO,
    RegistroAuditoria.MODIFICACION_PRECIO_REFERENCIA,
    RegistroAuditoria.MODIFICACION_IDENTIDAD_VISUAL,
    RegistroAuditoria.MODIFICACION_BANNER,
    RegistroAuditoria.MODIFICACION_OFERTA,
    RegistroAuditoria.AVANCE_ESTADO_PEDIDO,
    RegistroAuditoria.BAJA_USUARIO,
}


def reemplazos_del_detalle(accion, detalle):
    """Los reemplazos «antes → después» que dice el texto de una entrada vieja.

    Sólo para presentarlos: lo que no tiene una de las dos formas que el sistema
    escribió se queda en el detalle, y la tabla nunca dice algo que el texto no diga.
    """
    if not detalle:
        return []
    citados = [
        {"campo": m["campo"].strip(), "antes": m["antes"], "despues": m["despues"]}
        for m in _REEMPLAZO_CITADO.finditer(detalle)
    ]
    if citados or accion not in _ACCIONES_QUE_MODIFICAN:
        return citados
    simples = []
    for tramo in detalle.split("; "):
        coincide = _REEMPLAZO_SIMPLE.match(tramo.strip().rstrip("."))
        if coincide:
            simples.append(
                {
                    "campo": coincide["campo"].strip(),
                    "antes": coincide["antes"].strip().strip("'"),
                    "despues": coincide["despues"].strip().strip("'"),
                }
            )
    return simples


def _urls_de_imagen(cambio):
    """La dirección de cada versión de una imagen, si el archivo sigue estando."""
    if not cambio.get("imagen"):
        return {}
    return {
        f"url_{momento}": default_storage.url(cambio[momento])
        for momento in ("antes", "despues")
        if cambio.get(momento) and default_storage.exists(cambio[momento])
    }


class _Eco:
    """Un archivo de mentira que devuelve lo que se le escribe, para el flujo."""

    def write(self, valor):
        return valor


class LogExportarView(RolRequeridoMixin, View):
    """`CO-129`: todas las entradas del filtro activo, no sólo la página.

    Se genera en flujo: el log crece sin techo y no hace falta tenerlo entero
    en memoria para escribirlo. La entrada de la exportación se registra antes
    de empezar, con los filtros aplicados, y por eso no aparece en su propio
    archivo.
    """

    roles_permitidos = (Usuario.ADMINISTRADOR,)
    COLUMNAS = (  # noqa: RUF012
        "Momento",
        "Actor",
        "Acción",
        "Entidad",
        "Identificador",
        "Afectado",
        "IP",
        "Detalle",
    )

    def get(self, request):
        filtros = FiltrosDelLog(request.GET)
        entradas = filtros.aplicar(_entradas())
        cantidad = entradas.count()

        RegistroAuditoria.registrar(
            accion=RegistroAuditoria.EXPORTACION_AUDITORIA,
            actor=request.user,
            ip=obtener_ip(request),
            detalle=f"{cantidad} entradas; filtros: {filtros.legibles()}",
        )

        escritor = csv.writer(_Eco())

        def filas():
            # La marca de orden de bytes: sin ella la planilla lee mal los acentos.
            yield "\ufeff"
            yield escritor.writerow(self.COLUMNAS)
            for entrada in entradas.iterator(chunk_size=1000):
                yield escritor.writerow(
                    [
                        celda_csv(
                            timezone.localtime(entrada.ocurrido_en).strftime("%d/%m/%Y %H:%M:%S")
                        ),
                        celda_csv(entrada.actor_email),
                        celda_csv(entrada.get_accion_display()),
                        celda_csv(entrada.objetivo_tipo.name if entrada.objetivo_tipo else ""),
                        celda_csv(entrada.objetivo_pk or ""),
                        celda_csv(entrada.objetivo_email),
                        celda_csv(entrada.ip or ""),
                        celda_csv(entrada.detalle),
                    ]
                )

        respuesta = StreamingHttpResponse(filas(), content_type="text/csv; charset=utf-8")
        respuesta["Content-Disposition"] = (
            f'attachment; filename="auditoria-{timezone.localdate():%Y-%m-%d}.csv"'
        )
        return respuesta
