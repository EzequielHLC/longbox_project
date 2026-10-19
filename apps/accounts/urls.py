from django.urls import path

from apps.accounts import views
from apps.puntos.views import AjustePuntosView

app_name = "accounts"

urlpatterns = [
    path("login/", views.LoginUsuarioView.as_view(), name="login"),
    # Módulo 11 — alta pública de cuenta de Cliente (CU-CLI-ALT).
    path("registro/", views.RegistroClienteView.as_view(), name="registro_cliente"),
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
    # Módulo 13 — Gestión de Usuarios (backoffice, solo Administrador).
    path("usuarios/", views.UsuarioListaView.as_view(), name="usuario_lista"),
    # Consulta de cuentas de Cliente: solo lectura (ver `ClienteListaView`).
    path("clientes/", views.ClienteListaView.as_view(), name="cliente_lista"),
    path("clientes/<int:pk>/", views.ClienteFichaView.as_view(), name="cliente_ficha"),
    # CU-PTS-ADM: los puntos del Cliente y su ajuste manual (plan 10, segunda parte).
    path("clientes/<int:pk>/puntos/", AjustePuntosView.as_view(), name="cliente_puntos"),
    path("usuarios/nuevo/", views.UsuarioAltaView.as_view(), name="usuario_alta"),
    path("usuarios/<int:pk>/", views.UsuarioFichaView.as_view(), name="usuario_ficha"),
    path("usuarios/<int:pk>/editar/", views.UsuarioEdicionView.as_view(), name="usuario_edicion"),
    path(
        "usuarios/<int:pk>/reenviar-activacion/",
        views.ReenviarActivacionView.as_view(),
        name="usuario_reenviar_activacion",
    ),
    path("usuarios/<int:pk>/baja/", views.UsuarioBajaView.as_view(), name="usuario_baja"),
    path(
        "usuarios/<int:pk>/reactivar/",
        views.UsuarioReactivarView.as_view(),
        name="usuario_reactivar",
    ),
    path(
        "usuarios/<int:pk>/eliminar/",
        views.UsuarioEliminarPendienteView.as_view(),
        name="usuario_eliminar",
    ),
    # Activación de la cuenta nueva: la abre el destinatario del correo, sin
    # sesión iniciada.
    path("activar/listo/", views.ActivacionCompletaView.as_view(), name="activacion_completa"),
    path("activar/<uidb64>/<token>/", views.ActivarCuentaView.as_view(), name="activar_cuenta"),
]
