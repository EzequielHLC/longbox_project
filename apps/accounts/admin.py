from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from apps.accounts.models import IntentoFallido, Usuario


@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    list_display = ("email", "username", "rol", "is_active")
    # El rol se puede cambiar desde la propia lista, sin entrar a cada usuario.
    # (El alta y la baja formal de usuarios de personal son CU-50/51/52, con su
    # propia pantalla; esto es solo la herramienta de administración de Django.)
    list_editable = ("rol", "is_active")
    list_display_links = ("email",)
    list_filter = ("rol", "is_active")
    search_fields = ("email", "username")
    ordering = ("email",)
    fieldsets = UserAdmin.fieldsets + (("Longbox", {"fields": ("rol",)}),)
    add_fieldsets = UserAdmin.add_fieldsets + (("Longbox", {"fields": ("email", "rol")}),)


@admin.register(IntentoFallido)
class IntentoFallidoAdmin(admin.ModelAdmin):
    list_display = ("email", "ip", "ocurrido_en")
    search_fields = ("email", "ip")
    readonly_fields = ("email", "ip", "ocurrido_en")
