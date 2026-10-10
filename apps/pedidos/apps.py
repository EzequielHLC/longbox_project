from django.apps import AppConfig


class PedidosConfig(AppConfig):
    """Área 5 del modelo: el pedido, sus líneas y su cobro.

    Lo crea la compra online (módulo 07) y lo gestionan los módulos 08, 09, 14 y
    18. Vive en su propia app para que ninguno de ellos dependa de la tienda.
    """

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.pedidos"
    verbose_name = "pedidos"
