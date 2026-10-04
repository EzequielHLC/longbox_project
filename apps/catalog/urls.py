from django.urls import path

from apps.catalog import views
from apps.catalog import views_catalogos as vc
from apps.catalog import views_ofertas as vo
from apps.catalog import views_precios as vp

app_name = "catalog"

urlpatterns = [
    # Inventario interno, solo lectura: el alta es por lote y la edición
    # pertenece al módulo de Catálogo, todavía no implementado.
    path("productos/", views.ProductoListaView.as_view(), name="producto_lista"),
    path("productos/exportar/", views.ProductoExportarView.as_view(), name="producto_exportar"),
    path("productos/<int:pk>/", views.ProductoDetalleView.as_view(), name="producto_detalle"),
    # CU-CAT-EDI y CU-CAT-BAJ le agregan las acciones a la ficha que ya existe, en vez de
    # duplicar la pantalla: el listado y el detalle de CU-CAT-INV son el punto de
    # entrada de las tres.
    path(
        "productos/<int:pk>/editar/",
        views.ProductoEdicionView.as_view(),
        name="producto_editar",
    ),
    path("productos/<int:pk>/baja/", views.ProductoBajaView.as_view(), name="producto_baja"),
    path(
        "productos/<int:pk>/reactivar/",
        views.ProductoReactivarView.as_view(),
        name="producto_reactivar",
    ),
    # CU-ALT-REV — revisión de los borradores que genera el pipeline de novedades.
    path("borradores/", views.BorradorListaView.as_view(), name="borrador_lista"),
    path("borradores/<int:pk>/", views.BorradorDetalleView.as_view(), name="borrador_detalle"),
    path(
        "borradores/confirmar-en-lote/",
        views.ConfirmarEnLoteView.as_view(),
        name="borrador_confirmar_lote",
    ),
    path(
        "borradores/cerrar-sesion/",
        views.CerrarSesionRevisionView.as_view(),
        name="cerrar_sesion_revision",
    ),
    # CU-CAT-ALT — alta de producto no editorial. De a uno, no por lote.
    path(
        "productos/no-editorial/nuevo/",
        views.ProductoNoEditorialAltaView.as_view(),
        name="producto_no_editorial_alta",
    ),
    path(
        "productos/no-editorial/duplicados/",
        views.DuplicadosNoEditorialesView.as_view(),
        name="duplicados_no_editoriales",
    ),
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
    path("tipos/rapido/", views.TipoRapidaView.as_view(), name="tipo_rapido"),
    path("formatos/rapido/", views.FormatoRapidaView.as_view(), name="formato_rapido"),
    path("etiquetas/rapida/", vc.EtiquetaRapidaView.as_view(), name="etiqueta_rapida"),
    # Parámetros globales.
    path("parametros/", views.ParametrosView.as_view(), name="parametros"),
    # Los catálogos de clasificación: listado, alta, modificación y baja con
    # informe, iguales para los cinco (`views_catalogos`).
    path("parametros/editoriales/", vc.EditorialListaView.as_view(), name="editorial_lista"),
    path("parametros/editoriales/nueva/", vc.EditorialCrearView.as_view(), name="editorial_crear"),
    path(
        "parametros/editoriales/<int:pk>/",
        vc.EditorialEditarView.as_view(),
        name="editorial_editar",
    ),
    path(
        "parametros/editoriales/<int:pk>/baja/",
        vc.EditorialBajaView.as_view(),
        name="editorial_baja",
    ),
    path("parametros/tipos/", vc.TipoListaView.as_view(), name="tipo_lista"),
    path("parametros/tipos/nuevo/", vc.TipoCrearView.as_view(), name="tipo_crear"),
    path(
        "parametros/tipos/<int:pk>/",
        vc.TipoEditarView.as_view(),
        name="tipo_editar",
    ),
    path(
        "parametros/tipos/<int:pk>/baja/",
        vc.TipoBajaView.as_view(),
        name="tipo_baja",
    ),
    path("parametros/formatos/", vc.FormatoListaView.as_view(), name="formato_lista"),
    path("parametros/formatos/nuevo/", vc.FormatoCrearView.as_view(), name="formato_crear"),
    path(
        "parametros/formatos/<int:pk>/",
        vc.FormatoEditarView.as_view(),
        name="formato_editar",
    ),
    path(
        "parametros/formatos/<int:pk>/baja/",
        vc.FormatoBajaView.as_view(),
        name="formato_baja",
    ),
    # Las etiquetas se operan por grupo (`CO-165`): la lista de grupos es la
    # entrada, y cada grupo tiene la de sus etiquetas.
    path("parametros/etiquetas/", vc.GrupoListaView.as_view(), name="etiquetas"),
    path(
        "parametros/grupos-de-etiqueta/nuevo/",
        vc.GrupoCrearView.as_view(),
        name="grupo_etiqueta_crear",
    ),
    path(
        "parametros/grupos-de-etiqueta/<int:pk>/",
        vc.GrupoEditarView.as_view(),
        name="grupo_etiqueta_editar",
    ),
    path(
        "parametros/grupos-de-etiqueta/<int:pk>/baja/",
        vc.GrupoBajaView.as_view(),
        name="grupo_etiqueta_baja",
    ),
    path(
        "parametros/grupos-de-etiqueta/<int:pk>/etiquetas/",
        vc.EtiquetasDeGrupoView.as_view(),
        name="grupo_etiquetas",
    ),
    path("parametros/etiquetas/nueva/", vc.EtiquetaCrearView.as_view(), name="etiqueta_crear"),
    path(
        "parametros/etiquetas/<int:pk>/",
        vc.EtiquetaEditarView.as_view(),
        name="etiqueta_editar",
    ),
    path(
        "parametros/etiquetas/<int:pk>/baja/",
        vc.EtiquetaBajaView.as_view(),
        name="etiqueta_baja",
    ),
    # La tabla de precios de referencia y el margen global (módulo 03).
    path("parametros/precios/", vp.PrecioListaView.as_view(), name="precio_lista"),
    path("parametros/precios/nuevo/", vp.PrecioCrearView.as_view(), name="precio_crear"),
    path("parametros/precios/<int:pk>/", vp.PrecioModificarView.as_view(), name="precio_editar"),
    path(
        "parametros/precios/<int:pk>/eliminar/",
        vp.PrecioEliminarView.as_view(),
        name="precio_eliminar",
    ),
    path("parametros/margen/", vp.MargenView.as_view(), name="margen"),
    path("ofertas/", vo.OfertaListaView.as_view(), name="oferta_lista"),
    path("ofertas/nueva/", vo.OfertaAltaView.as_view(), name="oferta_alta"),
    path("ofertas/<int:pk>/", vo.OfertaFichaView.as_view(), name="oferta_ficha"),
    path("ofertas/<int:pk>/editar/", vo.OfertaEdicionView.as_view(), name="oferta_editar"),
    path("ofertas/<int:pk>/baja/", vo.OfertaBajaView.as_view(), name="oferta_baja"),
    path(
        "productos/<int:pk>/restaurar-precio/",
        vp.RestaurarPrecioView.as_view(),
        name="producto_restaurar_precio",
    ),
]
