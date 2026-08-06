from django.contrib import admin

from apps.core.models import RegistroAuditoria


@admin.register(RegistroAuditoria)
class RegistroAuditoriaAdmin(admin.ModelAdmin):
    """Solo lectura: el log de auditoría no se edita ni se borra desde ningún lado."""

    list_display = ("ocurrido_en", "accion", "actor_email", "ip", "detalle")
    list_filter = ("accion",)
    search_fields = ("actor_email", "ip")
    readonly_fields = ("actor", "actor_email", "accion", "ip", "detalle", "ocurrido_en")

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
