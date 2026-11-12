from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied


def plantilla_del_rol(request, sobria, del_cajero):
    """La plantilla de una pantalla según quién la mira (plan 06, segunda parte).

    El Cajero ve el mostrador encendido; el Administrador, la versión sobria. Las
    dos plantillas ofrecen las mismas operaciones: cambia la forma, no lo que se
    puede hacer.
    """
    return del_cajero if getattr(request.user, "rol", "") == "cajero" else sobria


class RolRequeridoMixin(LoginRequiredMixin):
    """Restringe una vista a uno o más roles, validando del lado del servidor.

    RNF-03: nunca alcanza con esconder el enlace en el frontend. Un request
    directo con un rol que no corresponde tiene que morir en 403 antes de que
    la vista toque dato alguno — por eso el chequeo va en `dispatch()`.
    """

    roles_permitidos = ()

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            # LoginRequiredMixin redirige al login conservando el `next`.
            return super().dispatch(request, *args, **kwargs)
        if self.roles_permitidos and request.user.rol not in self.roles_permitidos:
            raise PermissionDenied("Tu rol no tiene acceso a esta sección.")
        return super().dispatch(request, *args, **kwargs)
