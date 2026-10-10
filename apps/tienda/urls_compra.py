"""La compra (plan 07, sexta parte). Se monta en `tienda/compra/`."""

from django.urls import path

from apps.tienda import views_compra as views

app_name = "compra"

urlpatterns = [
    path("pagar/", views.PagarView.as_view(), name="pagar"),
    path("checkout/", views.CheckoutView.as_view(), name="checkout"),
    path("checkout/puntos/<int:pk>/", views.CanjeView.as_view(), name="canje"),
    path("checkout/puntos/listo/", views.ConfirmarCanjeView.as_view(), name="canje_listo"),
    path("checkout/confirmar/", views.ConfirmarView.as_view(), name="confirmar"),
    path("invitado/", views.InvitadoView.as_view(), name="invitado"),
    path("invitado/resumen/", views.InvitadoResumenView.as_view(), name="invitado_resumen"),
    path("invitado/confirmar/", views.InvitadoConfirmarView.as_view(), name="invitado_confirmar"),
    path("resultado/<str:referencia>/", views.ResultadoView.as_view(), name="resultado"),
    path("aviso/<str:clave>/", views.AvisoView.as_view(), name="aviso"),
    path(
        "pasarela-de-prueba/<str:referencia>/",
        views.PasarelaDePruebaView.as_view(),
        name="pasarela_prueba",
    ),
]
