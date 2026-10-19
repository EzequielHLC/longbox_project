"""Acceso al stock almacenado por la dirección real, y escrituras a la vez."""

from datetime import timedelta

import pytest
from django.urls import reverse
from django.utils import timezone

from apps.accounts.tests.factories import UsuarioFactory
from apps.almacen.models import ArticuloRetenido, SolicitudDespacho
from apps.almacen.tests.util import retenido, solicitud_de
from apps.core.models import RegistroAuditoria
from apps.core.tests.concurrencia import a_la_vez, errores_internos, sesion_de
from apps.tienda.tests.compra_util import cliente_con_direccion, fijar_parametros


@pytest.mark.django_db
def test_acceso_el_cliente_no_entra_al_panel_del_stock(client, cliente):
    articulo = retenido(cliente, estado=ArticuloRetenido.PENDIENTE_DESPACHO)
    client.force_login(cliente)

    respuestas = [
        client.get(reverse("almacen:lista")),
        client.get(reverse("almacen:ficha", args=[articulo.pk])),
        client.post(reverse("almacen:retiro", args=[articulo.pk])),
        client.post(
            reverse("almacen:solicitud", args=[articulo.solicitud.pk]),
            {"articulo": [articulo.pk]},
        ),
        client.post(reverse("almacen:plazo", args=[articulo.pk]), {"fecha": "2099-01-01"}),
    ]

    articulo.refresh_from_db()
    assert {r.status_code for r in respuestas} == {403}
    assert articulo.estado == ArticuloRetenido.PENDIENTE_DESPACHO


@pytest.mark.django_db
def test_acceso_el_cajero_no_modifica_el_plazo(client, cajero, cliente):
    articulo = retenido(cliente, vence_en=10)
    anterior = articulo.fecha_vencimiento
    client.force_login(cajero)

    respuesta = client.post(
        reverse("almacen:plazo", args=[articulo.pk]),
        {"fecha": (timezone.localdate() + timedelta(days=90)).isoformat(), "motivo": "x"},
    )

    articulo.refresh_from_db()
    assert respuesta.status_code == 403
    assert articulo.fecha_vencimiento == anterior


@pytest.mark.django_db
@pytest.mark.parametrize("rol", ["cajero", "administrador"])
def test_acceso_el_personal_no_usa_el_stock_de_mi_cuenta(client, request, rol):
    client.force_login(request.getfixturevalue(rol))

    respuestas = [
        client.get(reverse("cuenta:stock")),
        client.post(reverse("cuenta:despacho"), {"accion": "confirmar"}),
    ]

    assert {r.status_code for r in respuestas} == {403}


@pytest.mark.django_db
def test_acceso_un_cliente_no_pide_el_envio_de_lo_ajeno(client, cliente):
    fijar_parametros()
    ajeno = retenido(UsuarioFactory(rol="cliente"), valor="60000")
    client.force_login(cliente)

    client.post(reverse("cuenta:despacho"), {"accion": "seleccionar", "articulo": [ajeno.pk]})
    client.post(reverse("cuenta:despacho"), {"accion": "confirmar"})

    ajeno.refresh_from_db()
    assert ajeno.estado == ArticuloRetenido.DISPONIBLE
    assert not SolicitudDespacho.objects.exists()


@pytest.mark.django_db
def test_acceso_el_menu_lleva_al_stock_en_local(client, cajero):
    client.force_login(cajero)

    respuesta = client.get(reverse("almacen:lista"))

    assert reverse("almacen:lista") in respuesta.content.decode()


@pytest.mark.django_db(transaction=True)
def test_concurrencia_dos_pestanas_que_piden_el_envio_generan_una_sola_solicitud():
    fijar_parametros()
    titular = cliente_con_direccion()
    articulo = retenido(titular, valor="60000")
    una, otra = sesion_de(titular), sesion_de(titular)
    for sesion in (una, otra):
        sesion.post(
            reverse("cuenta:despacho"), {"accion": "seleccionar", "articulo": [articulo.pk]}
        )

    respuestas = a_la_vez(
        lambda: una.post(reverse("cuenta:despacho"), {"accion": "confirmar"}),
        lambda: otra.post(reverse("cuenta:despacho"), {"accion": "confirmar"}),
    )

    articulo.refresh_from_db()
    assert errores_internos(respuestas) == []
    assert SolicitudDespacho.objects.count() == 1
    assert articulo.solicitud == SolicitudDespacho.objects.get()


@pytest.mark.django_db(transaction=True)
def test_concurrencia_el_despacho_y_el_retiro_del_mismo_articulo_registran_uno():
    titular = UsuarioFactory(rol="cliente")
    administrador = UsuarioFactory(rol="administrador")
    cajero = UsuarioFactory(rol="cajero")
    solicitud = solicitud_de(titular)
    articulo = retenido(titular, estado=ArticuloRetenido.PENDIENTE_DESPACHO, solicitud=solicitud)
    ArticuloRetenido.objects.filter(pk=articulo.pk).update(estado=ArticuloRetenido.DISPONIBLE)
    articulo.refresh_from_db()
    panel, mostrador = sesion_de(administrador), sesion_de(cajero)

    respuestas = a_la_vez(
        lambda: panel.post(
            reverse("almacen:solicitud", args=[solicitud.pk]), {"articulo": [articulo.pk]}
        ),
        lambda: mostrador.post(reverse("almacen:retiro", args=[articulo.pk])),
    )

    articulo.refresh_from_db()
    assert errores_internos(respuestas) == []
    assert articulo.estado == ArticuloRetenido.RETIRADO
    assert RegistroAuditoria.objects.filter(accion=RegistroAuditoria.RETIRO_EN_LOCAL).count() == 1


@pytest.mark.django_db(transaction=True)
def test_concurrencia_el_vencimiento_y_el_pedido_de_envio_no_se_pisan():
    from apps.almacen import servicios

    fijar_parametros()
    titular = cliente_con_direccion()
    articulo = retenido(titular, valor="60000", vence_en=0)
    navegador = sesion_de(titular)
    navegador.post(reverse("cuenta:despacho"), {"accion": "seleccionar", "articulo": [articulo.pk]})

    respuestas = a_la_vez(
        lambda: navegador.post(reverse("cuenta:despacho"), {"accion": "confirmar"}),
        servicios.ciclo_de_vencimiento,
    )

    articulo.refresh_from_db()
    assert errores_internos(respuestas[:1]) == []
    producto = articulo.producto
    producto.refresh_from_db()
    if articulo.estado == ArticuloRetenido.VENCIDO:
        assert not SolicitudDespacho.objects.exists()
        assert producto.stock == 1
    else:
        # Pidió el envío primero: vence con el envío pendiente y se extiende.
        assert articulo.estado == ArticuloRetenido.PENDIENTE_DESPACHO
        assert producto.stock == 0
