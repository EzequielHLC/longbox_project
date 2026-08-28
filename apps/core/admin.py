from django.contrib import admin

from apps.core.models import ConfiguracionSistema, RegistroAuditoria


@admin.register(ConfiguracionSistema)
class ConfiguracionSistemaAdmin(admin.ModelAdmin):
    """Respaldo del panel de parámetros globales del backoffice."""

    list_display = ("__str__", "margen_ganancia", "stock_inicial_por_defecto", "actualizado_en")
    readonly_fields = ("actualizado_en", "actualizado_por")

    def has_add_permission(self, request):
        # Es una tabla de una sola fila y ya existe: el botón de "agregar"
        # solo podría crear confusión sobre cuál rige.
        return not ConfiguracionSistema.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(RegistroAuditoria)
class RegistroAuditoriaAdmin(admin.ModelAdmin):
    """Solo lectura: el log de auditoría no se edita ni se borra desde ningún lado."""

    list_display = ("ocurrido_en", "accion", "actor_email", "objetivo", "ip", "detalle")
    list_filter = ("accion",)
    search_fields = ("actor_email", "objetivo_email", "ip")
    readonly_fields = (
        "actor",
        "actor_email",
        "objetivo_tipo",
        "objetivo_pk",
        "objetivo_email",
        "accion",
        "ip",
        "detalle",
        "ocurrido_en",
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
