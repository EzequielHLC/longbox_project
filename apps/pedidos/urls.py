"""Los pedidos en el panel de gestión (plan 08). Se monta en `pedidos/`."""

from django.urls import path

from apps.pedidos import views

app_name = "pedidos"

urlpatterns = [
    path("", views.PedidoListaView.as_view(), name="lista"),
    path("<int:pk>/", views.PedidoDetalleView.as_view(), name="detalle"),
    path("<int:pk>/avanzar/", views.AvanzarView.as_view(), name="avanzar"),
]
