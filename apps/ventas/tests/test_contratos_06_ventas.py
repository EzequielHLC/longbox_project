"""Pruebas de contrato del mostrador (`CU-VTA-REG`, plan 06).

`CO-078` a `CO-082`, y `CO-103`/`CO-104` desde el ticket. Por la dirección real,
como las usa el Cajero. Postcondiciones negativas: nada antes de confirmar toca
el stock, los puntos ni los pedidos.
"""

from decimal import Decimal

import pytest
from django.test import Client
from django.urls import reverse

from apps.accounts.models import Usuario
from apps.accounts.tests.factories import UsuarioFactory
from apps.catalog.models import Producto
from apps.catalog.tests.factories import ProductoFactory
from apps.core.models import RegistroAuditoria
from apps.pedidos.models import LineaPedido, Pedido, TransaccionPago
from apps.puntos import servicios as puntos
from apps.puntos.models import LotePuntos, MovimientoPuntos
from apps.tienda.tests.compra_util import dar_puntos, fijar_parametros
from apps.ventas import ticket as servicio

pytestmark = pytest.mark.django_db

URL = reverse("core:mostrador")


@pytest.fixture(autouse=True)
def parametros(db):
    return fijar_parametros()


@pytest.fixture
def caja(client, cajero):
    client.force_login(cajero)
    return client


@pytest.fixture
def lector(db):
    return UsuarioFactory(rol=Usuario.CLIENTE, first_name="Ana")


def producto(stock=5, precio="10000", **extra):
    return ProductoFactory(stock=stock, precio=Decimal(precio), **extra)


def agregar(caja, prod=None, q=None, cantidad=1):
    datos = {"cantidad": cantidad}
    if prod is not None:
        datos["producto"] = prod.pk
    if q is not None:
        datos["q"] = q
    return caja.post(reverse("ventas:agregar"), datos)


def vincular(caja, texto):
    return caja.post(reverse("ventas:cliente"), {"cliente": texto})


def canjear(caja, prod, accion=None):
    datos = {"accion": accion} if accion else {}
    return caja.post(reverse("ventas:canje", args=[prod.pk]), datos)


def confirmar(caja, medio=TransaccionPago.EFECTIVO):
    return caja.post(reverse("ventas:confirmar"), {"medio": medio})


def foto(*productos):
    return {
        "stock": [Producto.objects.get(pk=p.pk).stock for p in productos],
        "pedidos": Pedido.objects.count(),
        "transacciones": TransaccionPago.objects.count(),
        "lotes": list(LotePuntos.objects.values_list("pk", "disponible", "estado")),
        "movimientos": MovimientoPuntos.objects.count(),
    }


def mensajes(respuesta):
    return [str(m) for m in respuesta.context["messages"]]


# ===========================================================================
# CO-078 · abrirVentaPresencial
# ===========================================================================


def test_CO078_abre_un_ticket_en_blanco_sin_tocar_el_dominio(caja):
    prod = producto()
    agregar(caja, prod)
    antes = foto(prod)

    caja.post(reverse("ventas:nueva"))

    assert caja.session[servicio.CLAVE] == {"items": [], "cliente": None}
    assert foto(prod) == antes


def test_CO078_sin_productos_con_stock_no_se_abre(caja):
    producto(stock=0)

    respuesta = caja.post(reverse("ventas:nueva"), follow=True)

    assert "No hay productos con stock para vender." in mensajes(respuesta)


# ===========================================================================
# CO-079 · agregarItemAlTicket
# ===========================================================================


def test_CO079_a_agrega_el_item_y_el_stock_no_cambia(caja):
    prod = producto(stock=5)

    agregar(caja, prod, cantidad=2)

    ticket = caja.get(URL).context["ticket"]
    assert [(i.producto.pk, i.cantidad) for i in ticket.items] == [(prod.pk, 2)]
    assert ticket.total == Decimal("20000")
    assert Producto.objects.get(pk=prod.pk).stock == 5


@pytest.mark.parametrize("campo", ["codigo", "codigo_barras", "isbn"])
def test_CO079_un_codigo_exacto_agrega_directo(caja, campo):
    valores = {"codigo": None, "codigo_barras": "7791234567890", "isbn": "9789878271583"}
    prod = producto(**({campo: valores[campo]} if valores[campo] else {}))
    texto = prod.codigo if campo == "codigo" else valores[campo]
    if campo == "isbn":
        texto = "978-987-827-158-3"

    agregar(caja, q=texto)

    assert [i.producto.pk for i in caja.get(URL).context["ticket"].items] == [prod.pk]


def test_CO079_un_texto_que_no_es_codigo_lista_coincidencias_sin_agregar(caja):
    prod = producto(titulo="Akira")
    producto(titulo="Berserk")

    respuesta = agregar(caja, q="aki")
    pantalla = caja.get(respuesta.url)

    assert [p.pk for p in pantalla.context["resultados"]] == [prod.pk]
    assert pantalla.context["ticket"].vacio


def test_CO079_repetir_un_producto_suma_la_cantidad(caja):
    prod = producto(stock=5)

    agregar(caja, prod, cantidad=2)
    agregar(caja, prod, cantidad=1)

    assert caja.get(URL).context["ticket"].items[0].cantidad == 3


def test_CO079_E1_un_producto_sin_stock_no_se_agrega(caja):
    prod = producto(stock=0, estado=Producto.AGOTADO)

    respuesta = agregar(caja, prod)

    pantalla = caja.get(respuesta.url)
    assert pantalla.context["ticket"].vacio
    assert f"«{prod.titulo}» no tiene unidades disponibles." in mensajes(pantalla)


def test_CO079_no_se_agrega_mas_que_el_stock(caja):
    prod = producto(stock=2)
    agregar(caja, prod, cantidad=2)

    respuesta = agregar(caja, prod, cantidad=1)

    pantalla = caja.get(respuesta.url)
    assert pantalla.context["ticket"].items[0].cantidad == 2
    assert f"De «{prod.titulo}» hay 2 unidad(es)." in mensajes(pantalla)


def test_CO079_una_pre_venta_no_se_vende_en_el_local(caja):
    prod = producto(stock=0, estado=Producto.PRE_VENTA)

    agregar(caja, prod)

    assert caja.get(URL).context["ticket"].vacio


# ===========================================================================
# CO-080 · quitarItemDelTicket
# ===========================================================================


def test_CO080_a_se_retira_el_item(caja):
    prod, otro = producto(), producto()
    agregar(caja, prod)
    agregar(caja, otro)

    caja.post(reverse("ventas:quitar", args=[prod.pk]))

    assert [i.producto.pk for i in caja.get(URL).context["ticket"].items] == [otro.pk]


def test_CO080_si_estaba_cubierto_el_canje_se_va_sin_tocar_lotes(caja, lector):
    dar_puntos(lector, 2000)
    prod = producto()
    agregar(caja, prod)
    vincular(caja, lector.codigo_cliente)
    canjear(caja, prod)
    lotes = list(LotePuntos.objects.values_list("pk", "disponible"))

    caja.post(reverse("ventas:quitar", args=[prod.pk]))

    ticket = caja.get(URL).context["ticket"]
    assert ticket.puntos_aplicados == 0
    assert list(LotePuntos.objects.values_list("pk", "disponible")) == lotes


# ===========================================================================
# CO-081 · vincularCuentaDeCliente
# ===========================================================================


def test_CO081_b_se_asocia_el_cliente_por_su_codigo(caja, lector):
    dar_puntos(lector, 150)

    vincular(caja, lector.codigo_cliente)

    ticket = caja.get(URL).context["ticket"]
    assert ticket.cliente == lector
    assert ticket.saldo == 150


def test_CO081_tambien_por_correo(caja, lector):
    vincular(caja, lector.email.upper())

    assert caja.get(URL).context["ticket"].cliente == lector


@pytest.mark.parametrize("caso", ["inexistente", "inactivo", "personal"])
def test_CO081_sin_un_cliente_activo_no_se_vincula(caja, cajero, caso):
    if caso == "inactivo":
        texto = UsuarioFactory(rol=Usuario.CLIENTE, estado=Usuario.INACTIVO).codigo_cliente
    elif caso == "personal":
        texto = cajero.email
    else:
        texto = "000000"

    respuesta = vincular(caja, texto)

    pantalla = caja.get(respuesta.url)
    assert pantalla.context["ticket"].cliente is None
    assert "No hay un cliente activo con ese código o correo." in mensajes(pantalla)


def test_CO081_no_hay_cambios_persistentes(caja, lector):
    prod = producto()
    antes = foto(prod)

    vincular(caja, lector.codigo_cliente)

    assert foto(prod) == antes


# ===========================================================================
# CO-103 / CO-104 · canje desde el ticket (CU-PTS-CJE, rama de mostrador)
# ===========================================================================


def test_CO103_mostrador_el_item_queda_cubierto_y_el_total_baja(caja, lector):
    dar_puntos(lector, 1500)
    prod, otro = producto(precio="10000"), producto(precio="4000")
    agregar(caja, prod)
    agregar(caja, otro)
    vincular(caja, lector.codigo_cliente)

    canjear(caja, prod)

    ticket = caja.get(URL).context["ticket"]
    assert ticket.total == Decimal("4000")
    assert ticket.puntos_aplicados == 1000
    assert ticket.saldo_restante == 500


def test_CO103_mostrador_ningun_lote_cambia(caja, lector):
    dar_puntos(lector, 1500)
    prod = producto()
    agregar(caja, prod)
    vincular(caja, lector.codigo_cliente)
    antes = foto(prod)

    canjear(caja, prod)

    assert foto(prod) == antes


def test_CO103_mostrador_E2_saldo_insuficiente_no_cubre(caja, lector):
    dar_puntos(lector, 999)
    prod = producto(precio="10000")
    agregar(caja, prod)
    vincular(caja, lector.codigo_cliente)

    respuesta = canjear(caja, prod)

    pantalla = caja.get(respuesta.url)
    assert pantalla.context["ticket"].puntos_aplicados == 0
    assert any("hacen falta 1000 puntos y quedan 999" in m for m in mensajes(pantalla))


def test_CO103_mostrador_sin_cliente_no_hay_canje(caja):
    prod = producto()
    agregar(caja, prod)

    canjear(caja, prod)

    assert caja.get(URL).context["ticket"].puntos_aplicados == 0


def test_CO104_mostrador_el_item_vuelve_a_su_precio(caja, lector):
    dar_puntos(lector, 1500)
    prod = producto()
    agregar(caja, prod)
    vincular(caja, lector.codigo_cliente)
    canjear(caja, prod)

    canjear(caja, prod, "revertir")

    ticket = caja.get(URL).context["ticket"]
    assert ticket.total == Decimal("10000")
    assert ticket.puntos_aplicados == 0


# ===========================================================================
# CO-082 · confirmarVentaPresencial
# ===========================================================================


@pytest.fixture
def venta(caja, lector):
    """Dos productos, uno cubierto con puntos, cobrado con tarjeta a un cliente vinculado."""
    dar_puntos(lector, 600, dias=30)
    dar_puntos(lector, 600, dias=90)
    cubierto = producto(stock=3, precio="10000")
    pagado = producto(stock=2, precio="6000")
    agregar(caja, cubierto)
    agregar(caja, pagado, cantidad=2)
    vincular(caja, lector.codigo_cliente)
    canjear(caja, cubierto)
    respuesta = confirmar(caja, TransaccionPago.TARJETA)
    return {"respuesta": respuesta, "cubierto": cubierto, "pagado": pagado}


def test_CO082_a_crea_el_pedido_con_sus_lineas_y_la_transaccion(venta):
    pedido = Pedido.objects.get()

    assert pedido.lineas.count() == 2
    assert pedido.transaccion is not None


def test_CO082_b_el_pedido_queda_asociado_al_cliente(venta, lector):
    assert Pedido.objects.get().usuario == lector


def test_CO082_c_canal_presencial_y_nace_vendido_en_el_local(venta):
    """B-06-005: la postcondición decía «Despachado»; la venta de mostrador tiene
    estado, modalidad y estado de ítem propios."""
    pedido = Pedido.objects.get()

    assert pedido.canal == Pedido.PRESENCIAL
    assert pedido.estado == Pedido.VENDIDO_EN_LOCAL
    assert pedido.modalidad == Pedido.MOSTRADOR
    assert set(pedido.lineas.values_list("estado", flat=True)) == {LineaPedido.ENTREGADO_EN_LOCAL}
    assert pedido.transiciones.get().estado_nuevo == Pedido.VENDIDO_EN_LOCAL


def test_CO082_c_precio_congelado_y_canje_registrado(venta):
    cubierta = LineaPedido.objects.get(producto=venta["cubierto"])
    pagada = LineaPedido.objects.get(producto=venta["pagado"])
    Producto.objects.filter(pk=venta["pagado"].pk).update(precio=Decimal("99999"))

    pagada.refresh_from_db()
    assert pagada.precio_unitario == Decimal("6000")
    assert (cubierta.cubierta_con_puntos, cubierta.puntos_canjeados) == (True, 1000)


def test_CO082_c_la_transaccion_tiene_el_medio_el_subtotal_monetario_y_aprobado(venta):
    transaccion = TransaccionPago.objects.get()

    assert transaccion.medio == TransaccionPago.TARJETA
    assert transaccion.monto == Decimal("12000")
    assert transaccion.estado == TransaccionPago.APROBADO
    assert transaccion.incluida_en_cierre is False


def test_CO082_c_el_stock_baja_y_el_que_llega_a_cero_pasa_a_agotado(venta):
    cubierto = Producto.objects.get(pk=venta["cubierto"].pk)
    pagado = Producto.objects.get(pk=venta["pagado"].pk)

    assert (cubierto.stock, cubierto.estado) == (2, Producto.ACTIVO)
    assert (pagado.stock, pagado.estado) == (0, Producto.AGOTADO)


def test_CO082_c_debita_los_lotes_que_vencen_antes(venta):
    proximo, lejano = LotePuntos.objects.filter(origen=LotePuntos.AJUSTE_MANUAL).order_by(
        "caduca_el"
    )

    assert (proximo.disponible, proximo.estado) == (0, LotePuntos.AGOTADO)
    assert (lejano.disponible, lejano.estado) == (200, LotePuntos.ACTIVO)
    assert MovimientoPuntos.objects.get(tipo=MovimientoPuntos.DEBITO).cantidad == 1000


def test_CO082_c_acredita_el_reintegro_de_lo_pagado_en_dinero(venta, lector):
    lote = LotePuntos.objects.get(origen=LotePuntos.COMPRA)

    # 10 % de $12.000 = $1.200, a $10 el punto: 120 puntos.
    assert lote.cantidad_acreditada == 120
    assert MovimientoPuntos.objects.get(tipo=MovimientoPuntos.ACREDITACION).cantidad == 120
    assert puntos.saldo(lector) == 200 + 120


def test_CO082_queda_en_la_auditoria_con_el_detalle(venta, cajero):
    registro = RegistroAuditoria.objects.get(accion=RegistroAuditoria.VENTA_PRESENCIAL)

    assert registro.actor == cajero
    assert registro.objetivo == Pedido.objects.get()
    assert "canjeó 1000 pts" in registro.detalle
    assert "acreditó 120 pts" in registro.detalle


def test_CO082_el_ticket_queda_vacio_y_se_muestra_el_comprobante(venta, caja):
    pedido = Pedido.objects.get()

    assert venta["respuesta"].url == reverse("ventas:comprobante", args=[pedido.numero])
    contenido = caja.get(venta["respuesta"].url).content.decode()
    assert pedido.numero in contenido
    assert "Puntos sumados" in contenido
    assert caja.get(URL).context["ticket"].vacio


def test_CO082_sin_cliente_no_hay_puntos_ni_asociacion(caja):
    agregar(caja, producto())

    confirmar(caja)

    pedido = Pedido.objects.get()
    assert pedido.usuario is None
    assert not LotePuntos.objects.exists()


def test_CO082_todo_cubierto_con_puntos_registra_la_transaccion_en_cero(caja, lector):
    dar_puntos(lector, 2000)
    prod = producto()
    agregar(caja, prod)
    vincular(caja, lector.codigo_cliente)
    canjear(caja, prod)

    caja.post(reverse("ventas:confirmar"), {})

    transaccion = TransaccionPago.objects.get()
    assert transaccion.monto == 0
    assert not LotePuntos.objects.filter(origen=LotePuntos.COMPRA).exists()


def test_CO082_con_importe_hay_que_elegir_el_medio_de_pago(caja):
    prod = producto()
    agregar(caja, prod)
    antes = foto(prod)

    caja.post(reverse("ventas:confirmar"), {"medio": "cheque"})

    assert foto(prod) == antes


def test_CO082_si_el_stock_se_perdio_no_se_vende_nada(caja):
    prod = producto(stock=2)
    agregar(caja, prod, cantidad=2)
    Producto.objects.filter(pk=prod.pk).update(stock=1)
    antes = foto(prod)

    respuesta = confirmar(caja)

    assert foto(prod) == antes
    assert f"De «{prod.titulo}» quedan 1 unidad(es). Corregí el ticket." in mensajes(
        caja.get(respuesta.url)
    )


def test_CO082_si_el_saldo_cambio_no_se_confirma(caja, lector):
    lote = dar_puntos(lector, 1000)
    prod = producto()
    agregar(caja, prod)
    vincular(caja, lector.codigo_cliente)
    canjear(caja, prod)
    LotePuntos.objects.filter(pk=lote.pk).update(disponible=10)

    confirmar(caja)

    assert not Pedido.objects.exists()


# ===========================================================================
# Acceso
# ===========================================================================


@pytest.mark.parametrize(
    ("metodo", "nombre"),
    [
        ("get", "core:mostrador"),
        ("post", "ventas:nueva"),
        ("post", "ventas:agregar"),
        ("post", "ventas:cliente"),
        ("post", "ventas:confirmar"),
    ],
)
def test_acceso_el_cliente_recibe_403_en_el_mostrador(client, cliente, metodo, nombre):
    client.force_login(cliente)

    assert getattr(client, metodo)(reverse(nombre)).status_code == 403


def test_acceso_el_administrador_tambien_vende(client_admin):
    agregar(client_admin, producto())

    confirmar(client_admin)

    assert Pedido.objects.get().canal == Pedido.PRESENCIAL


def test_acceso_sin_sesion_va_al_ingreso():
    assert Client().get(URL).url.startswith(reverse("accounts:login"))


# ---------------------------------------------------------------------------
# B-06-005: la venta de mostrador no se mezcla con los envíos
# ---------------------------------------------------------------------------


def test_B06005_la_base_no_admite_un_presencial_despachado_ni_un_online_de_mostrador():
    from django.db import IntegrityError, transaction

    from apps.pedidos.tests.util import crear_pedido

    pedido = crear_pedido(correo_invitado="x@correo.test")
    for cambios in (
        {"canal": Pedido.PRESENCIAL},
        {"modalidad": Pedido.MOSTRADOR},
        {"estado": Pedido.VENDIDO_EN_LOCAL},
    ):
        with pytest.raises(IntegrityError), transaction.atomic():
            Pedido.objects.filter(pk=pedido.pk).update(**cambios)


def test_B06005_la_compra_en_el_local_va_al_historial_de_la_cuenta_sin_riel(client):
    from apps.pedidos.tests.util import como_venta_de_mostrador, crear_pedido

    lector = UsuarioFactory(rol="cliente")
    pedido = como_venta_de_mostrador(crear_pedido(lector, estado=Pedido.DESPACHADO))
    client.force_login(lector)

    pedidos = client.get(reverse("cuenta:pedidos"))
    propio = client.get(reverse("cuenta:pedido", args=[pedido.numero])).content.decode()

    assert [p.pk for p in pedidos.context["historial"]] == [pedido.pk]
    assert pedidos.context["historial"][0].riel is None
    assert "Compra en el local" in propio
    assert "data-riel=" not in propio
