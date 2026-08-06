from django.views.generic import TemplateView

from apps.core.mixins import RolRequeridoMixin

# Vistas placeholder: son el destino de la redirección por rol del CU-46.
# Cada una se va a reemplazar por el módulo real (Tienda Online, Ventas
# Presenciales, panel de administración) cuando se aborde ese CU. Lo que sí
# es definitivo es el control de acceso por rol.


class TiendaView(RolRequeridoMixin, TemplateView):
    template_name = "core/tienda.html"
    roles_permitidos = ("cliente",)


class MostradorView(RolRequeridoMixin, TemplateView):
    template_name = "core/mostrador.html"
    roles_permitidos = ("cajero",)


class PanelAdministracionView(RolRequeridoMixin, TemplateView):
    template_name = "core/panel.html"
    roles_permitidos = ("administrador",)
