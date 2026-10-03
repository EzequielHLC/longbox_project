"""Pruebas de contrato del módulo 07 · Tienda online (CU-TDA-CAT).

Se escriben desde el contrato, según `docs/pruebas/ESPECIFICACION.md` apartado 3.
El catálogo es público y de sólo lectura: ninguna consulta modifica nada ni se
audita. Plan: `docs/planes/07-tienda-online.md`.
"""

from datetime import timedelta
from decimal import Decimal

import pytest
from django.urls import reverse
from django.utils import timezone

from apps.catalog.models import Producto
from apps.catalog.tests.factories import (
    EditorialFactory,
    EtiquetaFactory,
    GrupoEtiquetaFactory,
    ProductoFactory,
    TipoFactory,
)
from apps.core.models import IdentidadVisual, RegistroAuditoria

pytestmark = pytest.mark.django_db

URL = reverse("core:tienda_catalogo")


def titulos(respuesta):
    return [p.titulo for p in respuesta.context["productos"]]


def test_CO176_por_defecto_activos_con_stock_de_lo_mas_nuevo_a_lo_mas_viejo(client):
    viejo = ProductoFactory(titulo="Viejo", stock=2)
    nuevo = ProductoFactory(titulo="Nuevo", stock=2)
    Producto.objects.filter(pk=viejo.pk).update(creado_en=timezone.now() - timedelta(days=3))
    ProductoFactory(titulo="Sin stock", stock=0)
    ProductoFactory(titulo="En pre-venta", estado=Producto.PRE_VENTA)
    registros = RegistroAuditoria.objects.count()

    respuesta = client.get(URL)

    assert respuesta.status_code == 200
    assert titulos(respuesta) == [nuevo.titulo, viejo.titulo]
    assert RegistroAuditoria.objects.count() == registros


@pytest.mark.parametrize("estado", ["disponible", "agotado", "pre_venta", "todos"])
def test_CO176_descatalogados_cancelados_y_para_adultos_no_se_ven_bajo_ningun_filtro(
    client, estado
):
    for oculto in (Producto.DESCATALOGADO, Producto.CANCELADO_EDITORIAL):
        ProductoFactory(titulo=f"Oculto {oculto}", estado=oculto, stock=3)
    ProductoFactory(titulo="Para adultos", stock=3, solo_adultos=True)

    visibles = titulos(client.get(URL, {"estado": estado}))

    assert not [t for t in visibles if t.startswith("Oculto") or t == "Para adultos"]


def test_CO176_los_filtros_de_estado(client):
    ProductoFactory(titulo="Con stock", stock=4)
    ProductoFactory(titulo="Activo sin stock", stock=0)
    ProductoFactory(titulo="Agotado", estado=Producto.AGOTADO, stock=0)
    ProductoFactory(titulo="Reserva", estado=Producto.PRE_VENTA, stock=0)

    assert set(titulos(client.get(URL, {"estado": "agotado"}))) == {"Activo sin stock", "Agotado"}
    assert titulos(client.get(URL, {"estado": "pre_venta"})) == ["Reserva"]
    assert len(titulos(client.get(URL, {"estado": "todos"}))) == 4


def test_CO176_busqueda_tipo_editorial_etiqueta_y_precio(client):
    ivrea = EditorialFactory(nombre="Ivrea de prueba")
    manga = TipoFactory(nombre="Manga de prueba")
    franquicia = EtiquetaFactory(nombre="Berserk", grupo=GrupoEtiquetaFactory(nombre="Franq."))
    buscado = ProductoFactory(
        titulo="Berserk Deluxe", editorial=ivrea, tipo=manga, precio=Decimal("24900"), stock=1
    )
    buscado.etiquetas.add(franquicia)
    ProductoFactory(titulo="Otro", precio=Decimal("5000"), stock=1)

    for parametros in (
        {"q": "deluxe"},
        {"q": "ivrea de"},
        {"tipo": manga.pk},
        {"editorial": ivrea.pk},
        {"etiqueta": franquicia.pk},
        {"desde": "20000", "hasta": "30000"},
    ):
        assert titulos(client.get(URL, parametros)) == ["Berserk Deluxe"], parametros


def test_CO176_E1_sin_resultados_ofrece_limpiar_los_filtros(client):
    ProductoFactory(stock=1)

    contenido = client.get(URL, {"q": "no existe nada así"}).content.decode()

    assert "Ningún producto coincide con los filtros" in contenido
    assert "Limpiar filtros" in contenido


def test_CO176_se_pagina_de_a_24(client):
    for numero in range(26):
        ProductoFactory(titulo=f"Tomo {numero}", volumen=numero + 1, stock=1)

    assert len(client.get(URL).context["productos"]) == 24
    assert len(client.get(URL, {"page": 2}).context["productos"]) == 2


@pytest.mark.parametrize(
    ("estado", "stock", "accion"),
    [
        (Producto.ACTIVO, 3, "Agregar al carrito"),
        (Producto.ACTIVO, 0, "Avisarme cuando haya stock"),
        (Producto.AGOTADO, 0, "Avisarme cuando haya stock"),
        (Producto.PRE_VENTA, 0, "Reservar"),
    ],
)
def test_CO177_la_ficha_ofrece_la_accion_de_su_estado(client, estado, stock, accion):
    producto = ProductoFactory(
        estado=estado, stock=stock, fecha_llegada=timezone.localdate() + timedelta(days=9)
    )

    contenido = client.get(reverse("core:tienda_producto", args=[producto.pk])).content.decode()

    assert accion in contenido
    if estado == Producto.PRE_VENTA:
        assert "Llegada estimada" in contenido


def test_CO177_un_producto_no_visible_responde_404(client):
    producto = ProductoFactory(estado=Producto.DESCATALOGADO)

    assert client.get(reverse("core:tienda_producto", args=[producto.pk])).status_code == 404


def test_CO177_volver_conserva_los_filtros(client):
    producto = ProductoFactory(stock=1)

    contenido = client.get(
        reverse("core:tienda_producto", args=[producto.pk]), {"volver": "q=berserk&tipo=3"}
    ).content.decode()

    assert f"{URL}?q=berserk&amp;tipo=3" in contenido


def test_el_catalogo_es_publico_y_la_portada_sigue_siendo_del_cliente(client):
    """Precondición de `CO-176`; la portada espera la respuesta a C-20."""
    assert client.get(URL).status_code == 200
    assert client.get(reverse("core:tienda")).status_code == 302


# ===========================================================================
# CU-CFG-VIS con Viñeta Nocturna: contraste mínimo contra el fondo
# ===========================================================================


DATOS = {
    "nombre_tienda": "Akiba",
    "correo_contacto": "hola@akiba.test",
    "color_primario": "#FF6A13",
    "color_secundario": "#9A9AA5",
    "color_acento": "#FF6A13",
    "tipo_fondo": "color",
    "color_fondo": "#0A0A0C",
}


def test_la_identidad_nace_con_los_valores_de_vineta_nocturna():
    identidad = IdentidadVisual.obtener()

    assert (identidad.color_primario, identidad.color_fondo) == ("#FF6A13", "#0A0A0C")
    assert identidad.sobre_primario == "#0A0A0C"


def test_un_secundario_ilegible_sobre_el_fondo_se_rechaza(client_admin):
    respuesta = client_admin.post(
        reverse("core:identidad_visual"), {**DATOS, "color_secundario": "#1D1D23"}
    )

    assert "el mínimo es 4,5:1" in respuesta.context["form"].errors["color_secundario"][0]
    assert not RegistroAuditoria.objects.filter(
        accion=RegistroAuditoria.MODIFICACION_IDENTIDAD_VISUAL
    ).exists()


def test_el_texto_sobre_el_primario_lo_elige_el_sistema(client_admin, client):
    client_admin.post(reverse("core:identidad_visual"), {**DATOS, "color_primario": "#222266"})

    hoja = client.get(reverse("core:tienda_css")).content.decode()

    assert "--tienda-sobre-primario: #FFFFFF;" in hoja
