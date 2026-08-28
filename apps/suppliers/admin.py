"""Administración de respaldo de proveedores.

Los proveedores tienen su propia pantalla en el backoffice, que es la que usa el
personal y la única que audita. Este registro queda como herramienta de
desarrollo y soporte: revisar datos en crudo o corregir a mano una carga rara.
"""

from django.contrib import admin

from apps.suppliers.models import CorreoProveedor, Proveedor


@admin.register(Proveedor)
class ProveedorAdmin(admin.ModelAdmin):
    list_display = (
        "razon_social",
        "correo_comercial",
        "estado",
        "procesa_novedades",
        "editorial",
        "tipo_por_defecto",
    )
    list_filter = ("estado", "procesa_novedades", "editorial")
    search_fields = ("razon_social", "correo_comercial", "nombre_contacto")
    readonly_fields = ("creado_en", "actualizado_en")


@admin.register(CorreoProveedor)
class CorreoProveedorAdmin(admin.ModelAdmin):
    list_display = ("asunto", "proveedor", "estado", "fecha", "recibido_en")
    list_filter = ("estado", "proveedor")
    search_fields = ("asunto", "remitente", "message_id")
    readonly_fields = ("recibido_en", "message_id", "contenido", "imagenes")
