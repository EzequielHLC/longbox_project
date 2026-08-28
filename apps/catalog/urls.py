from django.urls import path

from apps.catalog import views

app_name = "catalog"

urlpatterns = [
    # Inventario interno, solo lectura: el alta es por lote y la edición
    # pertenece al módulo de Catálogo, todavía no implementado.
    path("productos/", views.ProductoListaView.as_view(), name="producto_lista"),
    path("productos/<int:pk>/", views.ProductoDetalleView.as_view(), name="producto_detalle"),
    # Alta de lotes.
    path("lotes/nacional/", views.AltaLoteNacionalView.as_view(), name="lote_nacional"),
    path("lotes/importado/", views.AltaLoteImportadoView.as_view(), name="lote_importado"),
    path("lotes/<int:pk>/resumen/", views.LoteResumenView.as_view(), name="lote_resumen"),
    # Consultas que usa la pantalla de alta sin recargar.
    path(
        "precio-de-referencia/",
        views.PrecioDeReferenciaView.as_view(),
        name="precio_referencia",
    ),
    path("editoriales/rapida/", views.EditorialRapidaView.as_view(), name="editorial_rapida"),
    # Parámetros globales.
    path("parametros/", views.ParametrosView.as_view(), name="parametros"),
    path(
        "parametros/editoriales/nueva/",
        views.EditorialCrearView.as_view(),
        name="editorial_crear",
    ),
    path(
        "parametros/editoriales/<int:pk>/",
        views.EditorialEditarView.as_view(),
        name="editorial_editar",
    ),
    path(
        "parametros/grupos-de-etiqueta/nuevo/",
        views.GrupoEtiquetaCrearView.as_view(),
        name="grupo_etiqueta_crear",
    ),
    path(
        "parametros/grupos-de-etiqueta/<int:pk>/",
        views.GrupoEtiquetaEditarView.as_view(),
        name="grupo_etiqueta_editar",
    ),
    path("parametros/etiquetas/nueva/", views.EtiquetaCrearView.as_view(), name="etiqueta_crear"),
    path(
        "parametros/etiquetas/<int:pk>/",
        views.EtiquetaEditarView.as_view(),
        name="etiqueta_editar",
    ),
    path("parametros/tipos/nuevo/", views.TipoCrearView.as_view(), name="tipo_crear"),
    path("parametros/tipos/<int:pk>/", views.TipoEditarView.as_view(), name="tipo_editar"),
    path("parametros/formatos/nuevo/", views.FormatoCrearView.as_view(), name="formato_crear"),
    path("parametros/formatos/<int:pk>/", views.FormatoEditarView.as_view(), name="formato_editar"),
    path("parametros/precios/nuevo/", views.PrecioCrearView.as_view(), name="precio_crear"),
    path("parametros/precios/<int:pk>/", views.PrecioEditarView.as_view(), name="precio_editar"),
    path(
        "parametros/precios/<int:pk>/eliminar/",
        views.PrecioEliminarView.as_view(),
        name="precio_eliminar",
    ),
]
