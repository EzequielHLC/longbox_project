from django.apps import AppConfig


class AccountsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.accounts"

    def ready(self):
        # Conecta las signals que registran login/logout en auditoría.
        from apps.accounts import signals  # noqa: F401
