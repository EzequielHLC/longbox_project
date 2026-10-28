"""Acceso al ciclo de la pre-venta y a la demora por la dirección real, y escrituras a la vez."""

import pytest
from django.urls import reverse

from apps.accounts.tests.factories import UsuarioFactory
from apps.catalog.models import Producto
from apps.core.models import RegistroAuditoria
from apps.core.tests.concurrencia import a_la_vez, errores_internos, sesion_de
from apps.pedidos.models import LineaPedido, Pedido
from apps.pedidos.tests.util import crear_preventa, demorar, reservar
from apps.puntos.models import LotePuntos
from apps.tienda.tests.compra_util import fijar_parametros

# ---------------------------------------------------------------------------
# Acceso: el ciclo de la pre-venta es del Administrador
# ---------------------------------------------------------------------------


@pytest.mark.django_db
@pytest.mark.parametrize("rol", ["cajero", "cliente"])
def test_acceso_solo_el_administrador_opera_la_preventa(client, request, rol):
    producto = crear_preventa(dias=0)
    reservar(request.getfixturevalue("cliente"), producto)
    client.force_login(request.getfixturevalue(rol))

    respuestas = [
        client.get(reverse("pedidos:preventas")),
        client.post(
            reverse("pedidos:ingreso"),
            {"producto": [producto.pk], f"unidades_{producto.pk}": "5", "confirmar": "1"},
        ),
        client.get(reverse("pedidos:demora", args=[producto.pk])),
        client.post(reverse("pedidos:demora", args=[producto.pk]), {"confirmar": "1"}),
        client.get(reverse("pedidos:cancelar_preventa", args=[producto.pk])),
        client.post(reverse("pedidos:cancelar_preventa", args=[producto.pk])),
    ]

    producto.refresh_from_db()
    assert {r.status_code for r in respuestas} == {403}
    assert (producto.estado, producto.stock, producto.productoeditorial.demorado) == (
        Producto.PRE_VENTA,
        0,
        False,
    )


@pytest.mark.django_db
def test_acceso_la_ficha_ofrece_las_acciones_de_preventa_solo_cuando_aplican(client_admin, cliente):
    producto = crear_preventa(dias=5)
    reservar(cliente, producto, cantidad=2)
    activo = crear_preventa(dias=5)
    Producto.objects.filter(pk=activo.pk).update(estado=Producto.ACTIVO)

    ficha = client_admin.get(reverse("catalog:producto_detalle", args=[producto.pk]))
    otra = client_admin.get(reverse("catalog:producto_detalle", args=[activo.pk]))

    assert ficha.context["reservadas"] == 2
    assert reverse("pedidos:demora", args=[producto.pk]) in ficha.content.decode()
    assert reverse("pedidos:cancelar_preventa", args=[producto.pk]) in ficha.content.decode()
    assert reverse("pedidos:demora", args=[activo.pk]) not in otra.content.decode()
    assert reverse("pedidos:cancelar_preventa", args=[activo.pk]) not in otra.content.decode()


@pytest.mark.django_db
def test_acceso_el_panel_muestra_las_preventas_por_llegar(client_admin):
    fijar_parametros(dias_aviso_preventa=2)
    crear_preventa(dias=-1)
    crear_preventa(dias=0)
    crear_preventa(dias=2)
    crear_preventa(dias=9)

    respuesta = client_admin.get(reverse("core:panel"))

    proximas = respuesta.context["preventas"]
    assert (len(proximas.vencidas), len(proximas.hoy), len(proximas.proximas)) == (1, 1, 1)
    assert reverse("pedidos:preventas") in respuesta.content.decode()


@pytest.mark.django_db
def test_acceso_los_parametros_de_la_preventa_se_guardan_y_se_auditan(client_admin):
    fijar_parametros()
    datos = {
        "stock_inicial_por_defecto": "0",
        "intervalo_carrusel": "10",
        "dias_aviso_preventa": "4",
        "cantidad_minima_restock": "3",
        "margen_stock_restock": "2",
        "frecuencia_casilla_minutos": "24",
    }

    client_admin.post(reverse("catalog:parametros"), datos)

    from apps.core.models import ConfiguracionSistema

    assert ConfiguracionSistema.obtener().dias_aviso_preventa == 4
    assert RegistroAuditoria.objects.filter(
        accion=RegistroAuditoria.PARAMETRO_MODIFICADO,
        detalle="aviso previo de pre-venta (días): 2 → 4",
    ).exists()


# ---------------------------------------------------------------------------
# Acceso: la decisión es del titular del pedido
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_acceso_un_cliente_no_decide_sobre_el_pedido_de_otro(client, cliente):
    fijar_parametros()
    _, pedido, linea = demorar(cliente)
    client.force_login(UsuarioFactory(rol="cliente"))
    url = reverse("cuenta:demora", args=[pedido.numero, linea.pk])

    lectura = client.get(url)
    escritura = client.post(url, {"opcion": LineaPedido.CANCELAR, "confirmar": "1"})

    linea.refresh_from_db()
    assert (lectura.status_code, escritura.status_code) == (404, 404)
    assert linea.estado == LineaPedido.ESPERANDO_DEMORADO


@pytest.mark.django_db
@pytest.mark.parametrize("rol", ["cajero", "administrador"])
def test_acceso_el_personal_no_decide_por_el_cliente(client, request, cliente, rol):
    fijar_parametros()
    _, pedido, linea = demorar(cliente)
    client.force_login(request.getfixturevalue(rol))

    respuesta = client.post(
        reverse("cuenta:demora", args=[pedido.numero, linea.pk]),
        {"opcion": LineaPedido.CANCELAR, "confirmar": "1"},
    )

    linea.refresh_from_db()
    assert respuesta.status_code == 403
    assert not linea.decision_demora


@pytest.mark.django_db
def test_acceso_sin_sesion_la_decision_va_al_ingreso(client, cliente):
    fijar_parametros()
    _, pedido, linea = demorar(cliente)

    respuesta = client.get(reverse("cuenta:demora", args=[pedido.numero, linea.pk]))

    assert respuesta.url.startswith(reverse("accounts:login"))


# ---------------------------------------------------------------------------
# Concurrencia
# ---------------------------------------------------------------------------


@pytest.mark.django_db(transaction=True)
def test_concurrencia_dos_pestanas_que_confirman_registran_una_sola_decision():
    fijar_parametros()
    cliente = UsuarioFactory(rol="cliente")
    _, pedido, linea = demorar(cliente)
    url = reverse("cuenta:demora", args=[pedido.numero, linea.pk])
    una, otra = sesion_de(cliente), sesion_de(cliente)

    respuestas = a_la_vez(
        lambda: una.post(url, {"opcion": LineaPedido.PAUSAR, "confirmar": "1"}),
        lambda: otra.post(url, {"opcion": LineaPedido.CANCELAR, "confirmar": "1"}),
    )

    linea.refresh_from_db()
    assert errores_internos(respuestas) == []
    assert linea.decision_demora in (LineaPedido.PAUSAR, LineaPedido.CANCELAR)
    assert (
        RegistroAuditoria.objects.filter(
            accion__in=(
                RegistroAuditoria.DECISION_DEMORA,
                RegistroAuditoria.CANCELACION_ARTICULO_DEMORADO,
            )
        ).count()
        == 1
    )
    reembolsos = LotePuntos.objects.filter(origen=LotePuntos.REEMBOLSO).count()
    assert reembolsos == (1 if linea.decision_demora == LineaPedido.CANCELAR else 0)


@pytest.mark.django_db(transaction=True)
def test_concurrencia_la_llegada_y_la_cancelacion_del_cliente_no_se_pisan():
    fijar_parametros()
    cliente = UsuarioFactory(rol="cliente")
    administrador = UsuarioFactory(rol="administrador")
    producto, pedido, linea = demorar(cliente)
    url = reverse("cuenta:demora", args=[pedido.numero, linea.pk])
    navegador, panel = sesion_de(cliente), sesion_de(administrador)

    respuestas = a_la_vez(
        lambda: navegador.post(url, {"opcion": LineaPedido.CANCELAR, "confirmar": "1"}),
        lambda: panel.post(
            reverse("pedidos:ingreso"),
            {"producto": [producto.pk], f"unidades_{producto.pk}": "1", "confirmar": "1"},
        ),
    )

    producto.refresh_from_db()
    linea.refresh_from_db()
    assert errores_internos(respuestas) == []
    if linea.estado == LineaPedido.CANCELADO_REEMBOLSO:
        # Canceló primero: la unidad que llegó queda a la venta.
        assert (producto.estado, producto.stock) == (Producto.ACTIVO, 1)
        assert LotePuntos.objects.filter(origen=LotePuntos.REEMBOLSO).count() == 1
    else:
        # Llegó primero: el artículo es suyo y la cancelación se rechazó.
        assert linea.estado == LineaPedido.DISPONIBLE
        assert (producto.estado, producto.stock) == (Producto.AGOTADO, 0)
        assert not LotePuntos.objects.filter(origen=LotePuntos.REEMBOLSO).exists()


@pytest.mark.django_db(transaction=True)
def test_concurrencia_dos_administradores_que_confirman_el_mismo_ingreso_lo_cuentan_una_vez():
    cliente = UsuarioFactory(rol="cliente")
    uno, otro = UsuarioFactory(rol="administrador"), UsuarioFactory(rol="administrador")
    producto = crear_preventa(dias=0)
    pedido, _ = reservar(cliente, producto)
    datos = {"producto": [producto.pk], f"unidades_{producto.pk}": "5", "confirmar": "1"}
    primero, segundo = sesion_de(uno), sesion_de(otro)

    respuestas = a_la_vez(
        lambda: primero.post(reverse("pedidos:ingreso"), datos),
        lambda: segundo.post(reverse("pedidos:ingreso"), datos),
    )

    producto.refresh_from_db()
    pedido.refresh_from_db()
    assert errores_internos(respuestas) == []
    assert (producto.estado, producto.stock) == (Producto.ACTIVO, 4)
    assert pedido.estado == Pedido.PENDIENTE_ARMADO
    assert (
        RegistroAuditoria.objects.filter(accion=RegistroAuditoria.CONFIRMACION_INGRESO).count() == 1
    )


@pytest.mark.django_db(transaction=True)
def test_concurrencia_la_cancelacion_por_la_editorial_y_la_compra_no_dejan_reservas_vivas():
    from apps.tienda.tests.compra_util import (
        agregar,
        avisar,
        cliente_con_direccion,
        confirmar,
    )

    fijar_parametros()
    comprador = cliente_con_direccion()
    administrador = UsuarioFactory(rol="administrador")
    producto = crear_preventa(dias=5)
    navegador, panel = sesion_de(comprador), sesion_de(administrador)
    agregar(navegador, producto)
    _, cobro = confirmar(navegador)

    respuestas = a_la_vez(
        lambda: avisar(navegador, cobro),
        lambda: panel.post(reverse("pedidos:cancelar_preventa", args=[producto.pk])),
    )

    producto.refresh_from_db()
    assert errores_internos(respuestas) == []
    assert producto.estado == Producto.CANCELADO_EDITORIAL
    assert not LineaPedido.objects.filter(producto=producto, estado=LineaPedido.RESERVADO).exists()
