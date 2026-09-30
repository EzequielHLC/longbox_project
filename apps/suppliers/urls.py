from django.urls import path

from apps.suppliers import views

app_name = "suppliers"

urlpatterns = [
    # CU-PRV-CON — consulta. Es el punto de entrada del módulo.
    path("", views.ProveedorListaView.as_view(), name="proveedor_lista"),
    path("<int:pk>/", views.ProveedorDetalleView.as_view(), name="proveedor_detalle"),
    # CU-PRV-ALT — alta.
    path("nuevo/", views.ProveedorAltaView.as_view(), name="proveedor_alta"),
    # CU-PRV-EDI — edición.
    path("<int:pk>/editar/", views.ProveedorEdicionView.as_view(), name="proveedor_edicion"),
    # CU-PRV-BAJ — baja. CU-PRV-REA — la vuelta (ver la vista).
    path("<int:pk>/baja/", views.ProveedorBajaView.as_view(), name="proveedor_baja"),
    path(
        "<int:pk>/reactivar/",
        views.ProveedorReactivarView.as_view(),
        name="proveedor_reactivar",
    ),
    # CU-PRV-COL — la cola de correos: la antesala del pipeline de CU-ALT-NOV,
    # donde cada mensaje espera la aprobación explícita.
    path("correos/", views.CorreoListaView.as_view(), name="correo_lista"),
    path("correos/<int:pk>/", views.CorreoDetalleView.as_view(), name="correo_detalle"),
    path("correos/<int:pk>/aprobar/", views.AprobarCorreoView.as_view(), name="correo_aprobar"),
    path(
        "correos/<int:pk>/reprocesar/",
        views.ReprocesarCorreoView.as_view(),
        name="correo_reprocesar",
    ),
    # CU-CFG-LLM — diagnóstico: si el modelo está vivo y qué entiende cuando se
    # le manda algo.
    path("modelo/", views.DiagnosticoLLMView.as_view(), name="diagnostico_llm"),
]
