"""La duración de la sesión según Parámetros (`CO-114`; B-12-001, plan 00, A3).

`SESSION_COOKIE_AGE` queda como el valor de arranque; el que rige es el de
`ConfiguracionSistema`, que el Administrador cambia sin tocar código.
"""


def segundos_de_sesion():
    from apps.core.models import ConfiguracionSistema

    return ConfiguracionSistema.obtener().expiracion_sesion_minutos * 60


class ExpiracionDeSesionMiddleware:
    """Cada request autenticado renueva la sesión por el tiempo configurado.

    Con `SESSION_SAVE_EVERY_REQUEST`, es expiración por inactividad: el contador
    vuelve a empezar con cada pedido.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if getattr(request, "user", None) is not None and request.user.is_authenticated:
            request.session.set_expiry(segundos_de_sesion())
        return self.get_response(request)
