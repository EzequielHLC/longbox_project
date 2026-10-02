from django.urls import path

from apps.core import views
from apps.core import views_auditoria as auditoria
from apps.core import views_contenido as contenido

app_name = "core"

urlpatterns = [
    # El documento que CO-107 hace aceptar en el alta pública (CU-CLI-ALT).
    path(
        "politica-de-privacidad/",
        views.PoliticaPrivacidadView.as_view(),
        name="politica_privacidad",
    ),
    # Datos geográficos para el autocompletado del registro (CU-CLI-ALT).
    path("datos/localidades/", views.localidades, name="localidades"),
    path("tienda/", views.TiendaView.as_view(), name="tienda"),
    path("tienda/preguntas-frecuentes/", contenido.FaqPublicaView.as_view(), name="faq"),
    path("tienda/identidad.css", contenido.TiendaCssView.as_view(), name="tienda_css"),
    # El contenido de la tienda (CU-CFG-FAQ, BN*, VIS).
    path("configuracion/faq/", contenido.FaqView.as_view(), name="faq_editor"),
    path("configuracion/banners/", contenido.BannerListaView.as_view(), name="banner_lista"),
    path("configuracion/banners/nuevo/", contenido.BannerCrearView.as_view(), name="banner_crear"),
    path(
        "configuracion/banners/<int:pk>/",
        contenido.BannerEditarView.as_view(),
        name="banner_editar",
    ),
    path(
        "configuracion/banners/<int:pk>/baja/",
        contenido.BannerBajaView.as_view(),
        name="banner_baja",
    ),
    path(
        "configuracion/identidad-visual/",
        contenido.IdentidadVisualView.as_view(),
        name="identidad_visual",
    ),
    path("mostrador/", views.MostradorView.as_view(), name="mostrador"),
    path("panel/", views.PanelAdministracionView.as_view(), name="panel"),
    # CU-AUD-CON — el log se consulta y se exporta; no se escribe desde acá.
    path("auditoria/", auditoria.LogListaView.as_view(), name="auditoria"),
    path("auditoria/exportar/", auditoria.LogExportarView.as_view(), name="auditoria_exportar"),
    path("auditoria/<int:pk>/", auditoria.LogDetalleView.as_view(), name="auditoria_detalle"),
]
