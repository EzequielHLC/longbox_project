"""CU-REP-GEN (plan 15). Se monta en `reportes/`."""

from django.urls import path

from apps.reportes import views

app_name = "reportes"

urlpatterns = [
    path("", views.ReportesView.as_view(), name="generar"),
    path("exportar/", views.ExportarView.as_view(), name="exportar"),
]
