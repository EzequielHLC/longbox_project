"""Administración de respaldo del catálogo.

Los parámetros del negocio —editoriales, etiquetas, tipos, formatos y la tabla
de precios— tienen su propia pantalla en el backoffice, que es la que usa el
personal. Estos registros quedan igual en el admin de Django como herramienta de
desarrollo y soporte: para revisar datos en crudo, corregir a mano una carga rara
o mirar un producto sin pasar por la pantalla.
"""

from django.contrib import admin

from apps.catalog.models import (
    Editorial,
    Etiqueta,
    Formato,
    GrupoEtiqueta,
    LoteAlta,
    Producto,
    ProductoEditorial,
    ProductoNoEditorial,
    TablaPrecioReferencia,
    Tipo,
)


@admin.register(Editorial)
class EditorialAdmin(admin.ModelAdmin):
    list_display = ("nombre", "activa")
    list_filter = ("activa",)
    search_fields = ("nombre",)


@admin.register(GrupoEtiqueta)
class GrupoEtiquetaAdmin(admin.ModelAdmin):
    list_display = ("nombre", "activo", "orden")
    list_filter = ("activo",)
    search_fields = ("nombre",)


@admin.register(Etiqueta)
class EtiquetaAdmin(admin.ModelAdmin):
    list_display = ("nombre", "grupo", "activa")
    list_filter = ("grupo", "activa")
    search_fields = ("nombre",)


@admin.register(Tipo)
class TipoAdmin(admin.ModelAdmin):
    list_display = ("nombre", "usa_formato", "activo", "orden")
    list_filter = ("usa_formato", "activo")
    search_fields = ("nombre",)


@admin.register(Formato)
class FormatoAdmin(admin.ModelAdmin):
    list_display = ("nombre", "descripcion", "activo", "orden")
    list_filter = ("activo", "tipos")
    filter_horizontal = ("tipos",)
    search_fields = ("nombre",)


@admin.register(TablaPrecioReferencia)
class TablaPrecioReferenciaAdmin(admin.ModelAdmin):
    list_display = ("editorial", "tipo", "formato", "pvp", "actualizado_en")
    list_filter = ("editorial", "tipo", "formato")
    search_fields = ("editorial__nombre",)


@admin.register(LoteAlta)
class LoteAltaAdmin(admin.ModelAdmin):
    list_display = ("__str__", "origen", "editorial", "tipo", "cre", "creado_por", "creado_en")
    list_filter = ("origen",)
    readonly_fields = ("creado_en",)


@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    """El padre de la jerarquía: solo lo común a los dos rubros.

    Los campos propios de cada especialización se ven en su propio admin —
    `ProductoEditorialAdmin` y `ProductoNoEditorialAdmin`—, que es lo que la
    herencia con tabla por hijo permite y una tabla única con columnas nulas no.
    """

    list_display = ("titulo", "clase", "tipo", "estado", "stock", "precio")
    list_filter = ("clase", "estado", "tipo", "solo_adultos")
    search_fields = ("titulo",)
    filter_horizontal = ("etiquetas",)
    readonly_fields = ("clase", "creado_en", "actualizado_en")


@admin.register(ProductoEditorial)
class ProductoEditorialAdmin(admin.ModelAdmin):
    list_display = ("titulo", "volumen", "editorial", "tipo", "formato", "origen", "precio")
    list_filter = ("origen", "estado", "tipo", "formato", "precio_manual", "demorado")
    search_fields = ("titulo", "autor", "isbn")
    filter_horizontal = ("etiquetas",)
    readonly_fields = ("clase", "creado_en", "actualizado_en")


@admin.register(ProductoNoEditorial)
class ProductoNoEditorialAdmin(admin.ModelAdmin):
    list_display = ("titulo", "tipo", "marca", "estado", "stock", "precio")
    list_filter = ("estado", "tipo", "solo_adultos")
    search_fields = ("titulo", "marca", "codigo_interno")
    filter_horizontal = ("etiquetas",)
    readonly_fields = ("clase", "creado_en", "actualizado_en")
