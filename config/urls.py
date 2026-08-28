"""URL configuration for config project.

Rutas raíz del proyecto. Cada app expone las suyas en su propio `urls.py`.
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("cuentas/", include("apps.accounts.urls")),
    path("catalogo/", include("apps.catalog.urls")),
    path("proveedores/", include("apps.suppliers.urls")),
    path("", include("apps.core.urls")),
    path("", RedirectView.as_view(pattern_name="accounts:login"), name="inicio"),
]

# Las portadas subidas por el personal las sirve el runserver solo en
# desarrollo. En producción las sirve el servidor web, nunca Django: `static()`
# devuelve una lista vacía cuando DEBUG es False, así que esto no es un agujero
# que se pueda dejar puesto sin querer.
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
