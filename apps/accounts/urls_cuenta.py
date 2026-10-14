"""«Mi cuenta», el panel del Cliente (plan 11, segunda parte; plan 10). Se monta en `cuenta/`."""

from django.urls import path

from apps.accounts import views_cuenta as views
from apps.puntos.views import PuntosView

app_name = "cuenta"

urlpatterns = [
    path("", views.PanelView.as_view(), name="panel"),
    path("historial/", views.HistorialView.as_view(), name="historial"),
    path("pedidos/<str:numero>/", views.PedidoPropioView.as_view(), name="pedido"),
    path("pedidos/<str:numero>/demora/<int:linea>/", views.DemoraView.as_view(), name="demora"),
    path("puntos/", PuntosView.as_view(), name="puntos"),
    path("datos/", views.DatosView.as_view(), name="datos"),
    path("contrasena/", views.ContrasenaView.as_view(), name="contrasena"),
    path("correo/", views.CorreoView.as_view(), name="correo"),
    path(
        "correo/confirmar/<uidb64>/<token>/",
        views.ConfirmarCorreoView.as_view(),
        name="confirmar_correo",
    ),
]
