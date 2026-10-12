"""La caja (plan 14). Se monta en `caja/`."""

from django.urls import path

from apps.caja import views

app_name = "caja"

urlpatterns = [
    path("", views.CajaView.as_view(), name="caja"),
    path("cerrar/", views.CerrarView.as_view(), name="cerrar"),
    path("cierres/", views.CierreListaView.as_view(), name="cierres"),
    path("cierres/<int:pk>/", views.CierreView.as_view(), name="cierre"),
    path("cierres/<int:pk>/exportar/", views.ExportarView.as_view(), name="exportar"),
]
