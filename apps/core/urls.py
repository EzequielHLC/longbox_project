from django.urls import path

from apps.core import views

app_name = "core"

urlpatterns = [
    path("tienda/", views.TiendaView.as_view(), name="tienda"),
    path("mostrador/", views.MostradorView.as_view(), name="mostrador"),
    path("panel/", views.PanelAdministracionView.as_view(), name="panel"),
]
