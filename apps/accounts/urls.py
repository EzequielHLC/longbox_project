from django.urls import path

from apps.accounts import views

app_name = "accounts"

urlpatterns = [
    path("login/", views.LoginUsuarioView.as_view(), name="login"),
    path("logout/", views.LogoutUsuarioView.as_view(), name="logout"),
    path("sesion/renovar/", views.renovar_sesion, name="renovar_sesion"),
    path(
        "recuperar/",
        views.RecuperarContrasenaView.as_view(),
        name="password_reset",
    ),
    path(
        "recuperar/enviado/",
        views.RecuperarContrasenaEnviadaView.as_view(),
        name="password_reset_done",
    ),
    path(
        "recuperar/<uidb64>/<token>/",
        views.RestablecerContrasenaView.as_view(),
        name="password_reset_confirm",
    ),
    path(
        "recuperar/listo/",
        views.RestablecerContrasenaCompletaView.as_view(),
        name="password_reset_complete",
    ),
]
