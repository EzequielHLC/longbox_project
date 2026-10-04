from datetime import timedelta

from django.contrib.auth import get_user_model
from django.db.models import Count, Q
from django.http import JsonResponse
from django.utils import timezone
from django.views.generic import TemplateView

from apps.core import georef, views_tienda
from apps.core.mixins import RolRequeridoMixin
from apps.core.models import Banner, ConfiguracionSistema, ContenidoFAQ, RegistroAuditoria


def localidades(request):
    """Localidades de una provincia, para el autocompletado del registro.

    El navegador consulta *esta* vista y no directamente a georef: así la
    caché del servidor sirve a todos los visitantes en lugar de que cada uno
    golpee la API pública por su cuenta, y si el servicio se cae el problema se
    resuelve en un solo lugar.

    Sin sesión, porque el registro es público (CU-CLI-ALT). No expone nada: son
    datos abiertos del INDEC.
    """
    provincia = request.GET.get("provincia", "").strip()
    return JsonResponse({"localidades": georef.obtener_localidades(provincia)})


class PoliticaPrivacidadView(TemplateView):
    """La política de privacidad.

    Es el documento que CU-CLI-ALT y CO-107 hacen aceptar, y el que el campo
    `fecha_aceptacion_politica` fecha. Pública y sin sesión: la enlaza el
    checkbox de consentimiento del registro, y de nada serviría un
    consentimiento "informado" si para leer lo que se acepta hubiera que tener
    cuenta antes.
    """

    template_name = "core/politica_privacidad.html"


# Vistas placeholder: son el destino de la redirección por rol del CU-AUT-INI.
# Cada una se va a reemplazar por el módulo real (Tienda Online, Ventas
# Presenciales, panel de administración) cuando se aborde ese CU. Lo que sí
# es definitivo es el control de acceso por rol.


class TiendaView(RolRequeridoMixin, TemplateView):
    """La portada de la tienda: el carrusel de banners (CU-CFG-BNC, C-06).

    El catálogo público es `CU-TDA-CAT`, de la etapa B.
    """

    template_name = "core/tienda.html"
    roles_permitidos = ("cliente",)

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        contexto["banners"] = Banner.objects.all()
        contexto["intervalo"] = ConfiguracionSistema.obtener().intervalo_carrusel
        contexto["hay_faq"] = bool(ContenidoFAQ.obtener().contenido)
        llegados = views_tienda.recien_llegados()
        contexto["recien_llegados"] = llegados
        contexto["destacado"] = next((p for p in llegados if p.portada), None)
        contexto["filas"] = views_tienda.filas_de_portada()
        return contexto


class MostradorView(RolRequeridoMixin, TemplateView):
    template_name = "core/mostrador.html"
    roles_permitidos = ("cajero",)


class PanelAdministracionView(RolRequeridoMixin, TemplateView):
    """Tablero de entrada del Administrador.

    Las cifras que muestra salen todas de datos que el sistema ya tiene hoy
    —cuentas y log de auditoría—; no hay ninguna métrica inventada esperando un
    módulo futuro. A medida que entren Catálogo, Ventas y Reportes, cada uno
    suma acá lo suyo.
    """

    template_name = "core/panel.html"
    roles_permitidos = ("administrador",)

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        Usuario = get_user_model()

        cuentas = Usuario.objects.aggregate(
            personal_activo=Count(
                "pk",
                filter=Q(rol__in=Usuario.ROLES_DE_PERSONAL, estado=Usuario.ACTIVO),
            ),
            pendientes=Count(
                "pk",
                filter=Q(
                    rol__in=Usuario.ROLES_DE_PERSONAL,
                    estado=Usuario.PENDIENTE_ACTIVACION,
                ),
            ),
            dados_de_baja=Count(
                "pk",
                filter=Q(rol__in=Usuario.ROLES_DE_PERSONAL, estado=Usuario.INACTIVO),
            ),
            clientes=Count("pk", filter=Q(rol=Usuario.CLIENTE)),
        )

        ultimo_dia = timezone.now() - timedelta(days=1)
        contexto["cuentas"] = cuentas
        contexto["clientes_nuevos"] = Usuario.objects.filter(
            rol=Usuario.CLIENTE, date_joined__gte=ultimo_dia
        ).count()
        contexto["bloqueos_del_dia"] = RegistroAuditoria.objects.filter(
            accion=RegistroAuditoria.BLOQUEO_POR_INTENTOS, ocurrido_en__gte=ultimo_dia
        ).count()
        # `select_related` evita una consulta por fila al mostrar el actor.
        contexto["actividad"] = RegistroAuditoria.objects.select_related("actor")[:12]
        return contexto
