"""URL configuration for config project.

Rutas raíz del proyecto. Cada app expone las suyas en su propio `urls.py`.
"""

from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("cuentas/", include("apps.accounts.urls")),
    path("", include("apps.core.urls")),
    path("", RedirectView.as_view(pattern_name="accounts:login"), name="inicio"),
]
