from django.apps import AppConfig


class TiendaConfig(AppConfig):
    """Módulo 07 · Tienda Online: el carrito, y más adelante la compra."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.tienda"
    verbose_name = "tienda online"

    def ready(self):
        # `CO-086`: la fusión del carrito la dispara el inicio de sesión.
        from apps.tienda import senales  # noqa: F401
