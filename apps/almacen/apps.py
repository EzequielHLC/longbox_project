from django.apps import AppConfig


class AlmacenConfig(AppConfig):
    """Módulo 18 · Stock Almacenado en Local: lo que el local guarda a nombre de un Cliente."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.almacen"
    verbose_name = "stock almacenado"
