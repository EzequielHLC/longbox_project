"""Los pedidos en el panel de gestión (plan 08). Se monta en `pedidos/`."""

from django.urls import path

from apps.pedidos import views, views_preventa

app_name = "pedidos"

urlpatterns = [
    path("", views.PedidoListaView.as_view(), name="lista"),
    path("<int:pk>/", views.PedidoDetalleView.as_view(), name="detalle"),
    path("<int:pk>/avanzar/", views.AvanzarView.as_view(), name="avanzar"),
    path("preventas/", views_preventa.PreVentasView.as_view(), name="preventas"),
    path("preventas/ingreso/", views_preventa.IngresoView.as_view(), name="ingreso"),
    path("preventas/<int:pk>/demora/", views_preventa.DemoraView.as_view(), name="demora"),
    path("preventas/demora/", views_preventa.DemoraLoteView.as_view(), name="demora_lote"),
    path(
        "preventas/<int:pk>/cancelar/",
        views_preventa.CancelarPreVentaView.as_view(),
        name="cancelar_preventa",
    ),
]
