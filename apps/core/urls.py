from django.urls import path

from apps.core import views

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
    path("mostrador/", views.MostradorView.as_view(), name="mostrador"),
    path("panel/", views.PanelAdministracionView.as_view(), name="panel"),
]
