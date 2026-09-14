from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from apps.accounts.models import IntentoFallido, Usuario


@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    list_display = ("email", "username", "rol", "estado", "actualizado_en")
    # El rol y el estado se pueden cambiar desde la propia lista, sin entrar a
    # cada usuario. (El alta, la modificación y la baja formales de usuarios de
    # personal son CU-USR-ALT, CU-USR-MOD y CU-USR-BAJ, con su propia pantalla
    # de backoffice; esto es solo la herramienta de administración de Django.)
    list_editable = ("rol", "estado")
    list_display_links = ("email",)
    list_filter = ("rol", "estado")
    search_fields = ("email", "username")
    ordering = ("email",)
    # `is_active` se deriva de `estado` en `Usuario.save()`: mostrarlo editable
    # sería mentira, porque cualquier cambio se pisaría al guardar.
    readonly_fields = ("is_active", "actualizado_en")
    fieldsets = UserAdmin.fieldsets + (("Longbox", {"fields": ("rol", "estado")}),)
    add_fieldsets = UserAdmin.add_fieldsets + (("Longbox", {"fields": ("email", "rol", "estado")}),)


@admin.register(IntentoFallido)
class IntentoFallidoAdmin(admin.ModelAdmin):
    list_display = ("email", "ip", "ocurrido_en")
    search_fields = ("email", "ip")
    readonly_fields = ("email", "ip", "ocurrido_en")
