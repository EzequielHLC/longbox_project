"""El botón de arrepentimiento, en la tienda pública (plan 00, C1).

Se monta en `tienda/arrepentimiento/`.
"""

from django.urls import path

from apps.devoluciones import views_cuenta as views

app_name = "devoluciones_tienda"

urlpatterns = [
    path("", views.ArrepentimientoView.as_view(), name="inicio"),
    path("<str:numero>/", views.ArrepentimientoPedidoView.as_view(), name="pedido"),
]
