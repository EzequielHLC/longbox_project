from django.urls import path

from apps.tienda import views

app_name = "tienda"

urlpatterns = [
    path("", views.CarritoView.as_view(), name="carrito"),
    path("agregar/<int:pk>/", views.AgregarView.as_view(), name="agregar"),
    path("linea/<int:pk>/cantidad/", views.CantidadView.as_view(), name="cantidad"),
    path("linea/<int:pk>/quitar/", views.QuitarView.as_view(), name="quitar"),
]
