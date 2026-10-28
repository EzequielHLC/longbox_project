"""La propuesta de restock en el panel de gestión (plan 05). Se monta en `restock/`."""

from django.urls import path

from apps.restock import views

app_name = "restock"

urlpatterns = [
    path("", views.PropuestaView.as_view(), name="propuesta"),
    path("generar/", views.GenerarView.as_view(), name="generar"),
    # Plan 00 del circuito: las propuestas pasadas, sólo para leer.
    path("propuestas/", views.PropuestaListaView.as_view(), name="propuesta_lista"),
    path("propuestas/<int:pk>/", views.PropuestaDetalleView.as_view(), name="propuesta_detalle"),
    path("agregar/", views.AgregarView.as_view(), name="agregar"),
    path(
        "proveedores/<int:clave>/cantidades/",
        views.CantidadesView.as_view(),
        name="cantidades",
    ),
    path("lineas/<int:pk>/", views.LineaView.as_view(), name="linea"),
    path("proveedores/<int:clave>/", views.ProveedorView.as_view(), name="proveedor"),
    # El aviso de reposición del Cliente, desde la ficha pública (CU-RST-SUS).
    path("aviso/<int:pk>/", views.AvisoView.as_view(), name="aviso"),
]
