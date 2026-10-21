"""«Mi cuenta», el panel del Cliente (plan 11, segunda parte; plan 10). Se monta en `cuenta/`."""

from django.urls import path

from apps.accounts import views_cuenta as views
from apps.almacen import views_cuenta as almacen
from apps.devoluciones import views_cuenta as devoluciones
from apps.puntos.views import PuntosView
from apps.restock.views_cuenta import AvisosView

app_name = "cuenta"


urlpatterns = [
    path("", views.PanelView.as_view(), name="panel"),
    path("pedidos/", views.PedidosView.as_view(), name="pedidos"),
    path("historial/", views.HistorialView.as_view(), name="historial"),
    path("pedidos/<str:numero>/", views.PedidoPropioView.as_view(), name="pedido"),
    path("pedidos/<str:numero>/demora/<int:linea>/", views.DemoraView.as_view(), name="demora"),
    path(
        "pedidos/<str:numero>/devolucion/",
        devoluciones.SolicitudView.as_view(),
        name="devolucion",
    ),
    path("puntos/", PuntosView.as_view(), name="puntos"),
    path("avisos/", AvisosView.as_view(), name="avisos"),
    path("stock-en-local/", almacen.StockView.as_view(), name="stock"),
    path("stock-en-local/envio/", almacen.DespachoView.as_view(), name="despacho"),
    path("datos/", views.DatosView.as_view(), name="datos"),
    path("contrasena/", views.ContrasenaView.as_view(), name="contrasena"),
    path("correo/", views.CorreoView.as_view(), name="correo"),
    path(
        "correo/confirmar/<uidb64>/<token>/",
        views.ConfirmarCorreoView.as_view(),
        name="confirmar_correo",
    ),
]
