from django.urls import path

from apps.suppliers import views

app_name = "suppliers"

urlpatterns = [
    # CU-21 — consulta. Es el punto de entrada del módulo.
    path("", views.ProveedorListaView.as_view(), name="proveedor_lista"),
    path("<int:pk>/", views.ProveedorDetalleView.as_view(), name="proveedor_detalle"),
    # CU-18 — alta.
    path("nuevo/", views.ProveedorAltaView.as_view(), name="proveedor_alta"),
    # CU-19 — edición.
    path("<int:pk>/editar/", views.ProveedorEdicionView.as_view(), name="proveedor_edicion"),
    # CU-20 — baja, y la vuelta que ningún CU describe (ver la vista).
    path("<int:pk>/baja/", views.ProveedorBajaView.as_view(), name="proveedor_baja"),
    path(
        "<int:pk>/reactivar/",
        views.ProveedorReactivarView.as_view(),
        name="proveedor_reactivar",
    ),
    # La cola de correos. No es de ningún CU: es la antesala del pipeline de
    # CU-04, donde cada mensaje espera la aprobación explícita.
    path("correos/", views.CorreoListaView.as_view(), name="correo_lista"),
    path("correos/<int:pk>/", views.CorreoDetalleView.as_view(), name="correo_detalle"),
    # Herramienta de operación, no de ningún CU: si el modelo está vivo y qué
    # entiende cuando se le manda algo.
    path("modelo/", views.DiagnosticoLLMView.as_view(), name="diagnostico_llm"),
]
