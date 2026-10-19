"""El stock almacenado en el panel de gestión (plan 18). Se monta en `stock-local/`."""

from django.urls import path

from apps.almacen import views

app_name = "almacen"

urlpatterns = [
    path("", views.ListaView.as_view(), name="lista"),
    path("<int:pk>/", views.FichaView.as_view(), name="ficha"),
    path("<int:pk>/retiro/", views.RetiroView.as_view(), name="retiro"),
    path("<int:pk>/plazo/", views.PlazoView.as_view(), name="plazo"),
    path("solicitudes/<int:pk>/", views.SolicitudView.as_view(), name="solicitud"),
    path("pedidos/<int:pk>/retiro/", views.RetiroPedidoView.as_view(), name="retiro_pedido"),
]
