"""Acceso a la propuesta de restock por la dirección real, y escrituras a la vez."""

import pytest
from django.urls import reverse

from apps.accounts.tests.factories import UsuarioFactory
from apps.catalog.models import Producto
from apps.catalog.tests.factories import EditorialFactory, ProductoFactory
from apps.core.tests.concurrencia import a_la_vez, errores_internos, sesion_de
from apps.restock import servicios
from apps.restock.models import LineaPropuestaRestock, PropuestaRestock, SuscripcionReposicion
from apps.suppliers.tests.factories import ProveedorFactory
from apps.tienda.tests.compra_util import fijar_parametros


@pytest.mark.django_db
@pytest.mark.parametrize("rol", ["cajero", "cliente"])
def test_acceso_solo_el_administrador_opera_el_restock(client, request, rol):
    fijar_parametros()
    ProductoFactory(stock=0, estado=Producto.AGOTADO)
    propuesta = servicios.ciclo_semanal().propuesta
    linea = propuesta.lineas.get()
    client.force_login(request.getfixturevalue(rol))

    respuestas = [
        client.get(reverse("restock:propuesta")),
        client.post(reverse("restock:generar")),
        client.post(reverse("restock:linea", args=[linea.pk]), {"cantidad": "50"}),
        client.post(reverse("restock:agregar"), {"producto": "P-1", "cantidad": "1"}),
        client.get(reverse("restock:proveedor", args=[0])),
        client.post(reverse("restock:proveedor", args=[0]), {"accion": "descartar", "motivo": "x"}),
    ]

    linea.refresh_from_db()
    assert {r.status_code for r in respuestas} == {403}
    assert linea.estado_despacho == LineaPropuestaRestock.PENDIENTE
    assert linea.cantidad_sugerida != 50


@pytest.mark.django_db
def test_acceso_el_menu_del_administrador_lleva_al_restock(client_admin):
    respuesta = client_admin.get(reverse("restock:propuesta"))

    assert reverse("restock:propuesta") in respuesta.content.decode()


@pytest.mark.django_db(transaction=True)
def test_concurrencia_dos_clics_en_avisarme_dejan_una_suscripcion():
    cliente = UsuarioFactory(rol="cliente")
    producto = ProductoFactory(stock=0, estado=Producto.AGOTADO)
    una, otra = sesion_de(cliente), sesion_de(cliente)
    url = reverse("restock:aviso", args=[producto.pk])

    respuestas = a_la_vez(lambda: una.post(url), lambda: otra.post(url))

    assert errores_internos(respuestas) == []
    assert SuscripcionReposicion.objects.count() == 1


@pytest.mark.django_db(transaction=True)
def test_concurrencia_el_ciclo_y_el_boton_dejan_una_sola_propuesta_pendiente():
    fijar_parametros()
    administrador = UsuarioFactory(rol="administrador")
    ProductoFactory(stock=0, estado=Producto.AGOTADO)
    panel = sesion_de(administrador)

    respuestas = a_la_vez(
        lambda: panel.post(reverse("restock:generar")),
        servicios.ciclo_semanal,
    )

    assert errores_internos(respuestas[:1]) == []
    assert PropuestaRestock.objects.filter(estado=PropuestaRestock.PENDIENTE).count() == 1


@pytest.mark.django_db(transaction=True)
def test_concurrencia_dos_administradores_despachan_al_mismo_proveedor_una_vez(mailoutbox):
    fijar_parametros()
    editorial = EditorialFactory()
    proveedor = ProveedorFactory(editorial=editorial)
    ProductoFactory(stock=0, estado=Producto.AGOTADO, editorial=editorial)
    servicios.ciclo_semanal()
    uno = sesion_de(UsuarioFactory(rol="administrador"))
    otro = sesion_de(UsuarioFactory(rol="administrador"))
    url = reverse("restock:proveedor", args=[proveedor.pk])

    respuestas = a_la_vez(lambda: uno.post(url), lambda: otro.post(url))

    assert errores_internos(respuestas) == []
    assert sum(1 for m in mailoutbox if m.to == [proveedor.correo_comercial]) == 1
