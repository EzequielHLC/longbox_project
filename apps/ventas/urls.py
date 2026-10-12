"""El mostrador (plan 06). La pantalla principal es `core:mostrador`; las acciones, éstas."""

from django.urls import path

from apps.ventas import views

app_name = "ventas"

urlpatterns = [
    path("nueva/", views.NuevaVentaView.as_view(), name="nueva"),
    path("agregar/", views.AgregarView.as_view(), name="agregar"),
    path("quitar/<int:pk>/", views.QuitarView.as_view(), name="quitar"),
    path("cliente/", views.ClienteView.as_view(), name="cliente"),
    path("canje/<int:pk>/", views.CanjeView.as_view(), name="canje"),
    path("confirmar/", views.ConfirmarView.as_view(), name="confirmar"),
    path("comprobante/<str:numero>/", views.ComprobanteView.as_view(), name="comprobante"),
]
