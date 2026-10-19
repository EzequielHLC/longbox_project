"""Las devoluciones en el panel de gestión (plan 09). Se montan en `devoluciones/`."""

from django.urls import path

from apps.devoluciones import views

app_name = "devoluciones"

urlpatterns = [
    path("", views.ListaView.as_view(), name="lista"),
    path("<int:pk>/", views.DetalleView.as_view(), name="detalle"),
    path("<int:pk>/cambio/", views.CambioView.as_view(), name="cambio"),
    path("<int:pk>/reembolso/", views.ReembolsoView.as_view(), name="reembolso"),
    path("<int:pk>/reembolso-medio/", views.ReembolsoMedioView.as_view(), name="reembolso_medio"),
    path("<int:pk>/rechazo/", views.RechazoView.as_view(), name="rechazo"),
    path("<int:pk>/fotos/<int:foto>/", views.EvidenciaView.as_view(), name="evidencia"),
]
