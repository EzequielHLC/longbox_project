"""URL configuration for config project.

Rutas raíz del proyecto. Cada app expone las suyas en su propio `urls.py`.

**No hay admin de Django.** Se retiró junto con los cuatro `admin.py` de las
apps, por dos reglas del sistema que no admite:

- Ninguna escritura del sistema ocurre fuera de una operación contratada. El
  admin es una puerta de escritura sobre cualquier tabla, sin contrato, sin
  informe de impacto y sin entrada de auditoría.
- No existe ninguna cuenta fuera de los tres roles. Un superusuario es
  exactamente eso: una cuenta que el modelo de dominio no declara.

El alta de la primera cuenta Administrador en una instalación nueva es el
comando `manage.py crear_administrador_inicial`, declarado como tarea de
consola y fuera del modelo de casos de uso (ver `bitacora/01-alta-editorial.md`,
R-01-002).
"""

from django.conf import settings
from django.conf.urls.static import static
from django.urls import include, path
from django.views.generic import RedirectView

urlpatterns = [
    path("cuentas/", include("apps.accounts.urls")),
    path("cuenta/", include("apps.accounts.urls_cuenta")),
    path("catalogo/", include("apps.catalog.urls")),
    path("proveedores/", include("apps.suppliers.urls")),
    path("pedidos/", include("apps.pedidos.urls")),
    path("mostrador/", include("apps.ventas.urls")),
    path("caja/", include("apps.caja.urls")),
    path("stock-local/", include("apps.almacen.urls")),
    path("restock/", include("apps.restock.urls")),
    path("devoluciones/", include("apps.devoluciones.urls")),
    path("tienda/arrepentimiento/", include("apps.devoluciones.urls_tienda")),
    path("tienda/carrito/", include("apps.tienda.urls")),
    path("tienda/compra/", include("apps.tienda.urls_compra")),
    path("", include("apps.core.urls")),
    # La raíz es la tienda: pública desde que se resolvió C-20 (2026-10-05).
    path("", RedirectView.as_view(pattern_name="core:tienda"), name="inicio"),
]

# Las portadas subidas por el personal las sirve el runserver solo en
# desarrollo. En producción las sirve el servidor web, nunca Django: `static()`
# devuelve una lista vacía cuando DEBUG es False, así que esto no es un agujero
# que se pueda dejar puesto sin querer.
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
