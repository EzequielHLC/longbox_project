from django.urls import path

from apps.avisos import views

app_name = "avisos"

urlpatterns = [
    # Módulo 19 · Perfil y avisos.
    path("perfil/", views.PerfilView.as_view(), name="perfil"),
    path("perfil/avisos/", views.CanalesView.as_view(), name="canales"),
    path("perfil/telegram/vincular/", views.VincularView.as_view(), name="vincular"),
    path("perfil/telegram/confirmar/", views.ConfirmarVinculoView.as_view(), name="confirmar"),
    path("perfil/telegram/cancelar/", views.CancelarVinculoView.as_view(), name="cancelar"),
    path("perfil/telegram/desvincular/", views.DesvincularView.as_view(), name="desvincular"),
    path("perfil/contrasena/", views.ContrasenaView.as_view(), name="contrasena"),
    path("telegram/webhook/", views.WebhookView.as_view(), name="webhook"),
]
