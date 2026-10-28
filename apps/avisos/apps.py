from django.apps import AppConfig


class AvisosConfig(AppConfig):
    """Módulo 19 · Perfil y avisos: el perfil del Administrador, los canales de aviso y Telegram."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.avisos"
    verbose_name = "perfil y avisos"

    def ready(self):
        # Las alertas de seguridad escuchan el registro de auditoría (B-19-012).
        from apps.avisos import seguridad  # noqa: F401
