"""Contratos del Cliente ante una demora (plan 08, segunda parte).

`CO-184`, `CO-094`, `CO-095`, `CO-098`, `CO-096`, `CO-097` y `CO-156`. Las
operaciones del Cliente se ejercen por su dirección real en «Mi cuenta».
"""

from datetime import timedelta
from decimal import Decimal
from unittest import mock

import pytest
from django.urls import reverse
from django.utils import timezone
from freezegun import freeze_time

from apps.catalog.models import Producto
from apps.core.models import RegistroAuditoria
from apps.pedidos import demora, preventa
from apps.pedidos.models import LineaPedido, Pedido
from apps.pedidos.tests.util import crear_preventa, demorar
from apps.puntos.models import LotePuntos, MovimientoPuntos
from apps.tienda.tests.compra_util import fijar_parametros


def _url(pedido, linea):
    return reverse("cuenta:demora", args=[pedido.numero, linea.pk])


def _foto(pedido):
    return (
        Pedido.objects.get(pk=pedido.pk).estado,
        list(
            pedido.lineas.order_by("pk").values_list(
                "estado", "decision_demora", "ventana_cerrada", "compensacion_acumulada"
            )
        ),
        LotePuntos.objects.count(),
    )


def _acciones(accion):
    return RegistroAuditoria.objects.filter(accion=accion)


@pytest.fixture
def con_demora(cliente):
    fijar_parametros()
    return demorar(cliente)


# ---------------------------------------------------------------------------
# CO-184 consultarOpcionesAnteDemora
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_CO184_muestra_el_articulo_sus_fechas_y_las_tres_opciones(client, cliente, con_demora):
    producto, pedido, linea = con_demora
    client.force_login(cliente)
    antes = _foto(pedido)

    respuesta = client.get(_url(pedido, linea))

    contenido = respuesta.content.decode()
    assert respuesta.status_code == 200
    assert str(producto) in contenido
    assert linea.fecha_llegada_original.strftime("%d/%m/%Y") in contenido
    situacion = respuesta.context["situacion"]
    assert [o.clave for o in situacion.opciones] == [
        LineaPedido.PAUSAR,
        LineaPedido.DESPACHO_DIFERIDO,
        LineaPedido.CANCELAR,
    ]
    for opcion in situacion.opciones:
        assert opcion.titulo in contenido
    assert _foto(pedido) == antes


@pytest.mark.django_db
def test_CO184_el_detalle_del_pedido_ofrece_elegir_que_hacer(client, cliente, con_demora):
    _, pedido, linea = con_demora
    client.force_login(cliente)

    respuesta = client.get(reverse("cuenta:pedido", args=[pedido.numero]))

    assert _url(pedido, linea) in respuesta.content.decode()


@pytest.mark.django_db
def test_CO184_E1_con_la_ventana_vencida_no_hay_opciones(client, cliente, con_demora):
    _, pedido, linea = con_demora

    with freeze_time(timezone.now() + timedelta(hours=73)):
        client.force_login(cliente)
        respuesta = client.get(_url(pedido, linea), follow=True)
        detalle = client.get(reverse("cuenta:pedido", args=[pedido.numero]))

    assert "Venció el plazo para elegir" in respuesta.content.decode()
    assert _url(pedido, linea) not in detalle.content.decode()


@pytest.mark.django_db
def test_CO184_sin_nada_para_despachar_no_ofrece_recibir_lo_disponible(client, cliente):
    fijar_parametros()
    _, pedido, linea = demorar(cliente, otros=())
    client.force_login(cliente)

    respuesta = client.get(_url(pedido, linea))

    assert [o.clave for o in respuesta.context["situacion"].opciones] == [
        LineaPedido.PAUSAR,
        LineaPedido.CANCELAR,
    ]


@pytest.mark.django_db
def test_CO184_con_otra_preventa_esperando_no_ofrece_recibir_lo_disponible(cliente):
    fijar_parametros()
    _, pedido, linea = demorar(cliente)
    otra = crear_preventa(dias=20)
    LineaPedido.objects.create(
        pedido=pedido,
        producto=otra,
        cantidad=1,
        precio_unitario=otra.precio,
        estado=LineaPedido.RESERVADO,
    )
    linea.pedido = pedido

    claves = [o.clave for o in demora.opciones_de(linea)]

    assert LineaPedido.DESPACHO_DIFERIDO not in claves


# ---------------------------------------------------------------------------
# CO-094 seleccionarOpcionAnteDemora
# ---------------------------------------------------------------------------


@pytest.mark.django_db
@pytest.mark.parametrize("clave", [LineaPedido.PAUSAR, LineaPedido.CANCELAR])
def test_CO094_pide_confirmar_con_la_consecuencia_sin_registrar(client, cliente, con_demora, clave):
    _, pedido, linea = con_demora
    client.force_login(cliente)
    antes = _foto(pedido)

    respuesta = client.post(_url(pedido, linea), {"opcion": clave})

    elegida = respuesta.context["elegida"]
    assert elegida.clave == clave
    assert elegida.consecuencia in respuesta.content.decode()
    if clave == LineaPedido.CANCELAR:
        assert "No se puede deshacer" in elegida.consecuencia
        assert "1000 pts" in respuesta.content.decode()
    assert _foto(pedido) == antes
    assert not _acciones(RegistroAuditoria.DECISION_DEMORA).exists()


@pytest.mark.django_db
def test_CO094_una_opcion_que_no_corresponde_se_rechaza(client, cliente):
    fijar_parametros()
    _, pedido, linea = demorar(cliente, otros=())
    client.force_login(cliente)

    for datos in (
        {"opcion": LineaPedido.DESPACHO_DIFERIDO},
        {"opcion": LineaPedido.DESPACHO_DIFERIDO, "confirmar": "1"},
        {"opcion": "inventada", "confirmar": "1"},
    ):
        respuesta = client.post(_url(pedido, linea), datos, follow=True)
        assert "no está disponible" in respuesta.content.decode()

    linea.refresh_from_db()
    assert not linea.decision_demora


# ---------------------------------------------------------------------------
# CO-095 confirmarOpcionAnteDemora
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_CO095_pausar_registra_la_decision_y_el_pedido_sigue_esperando(
    client, cliente, con_demora, mailoutbox, django_capture_on_commit_callbacks
):
    _, pedido, linea = con_demora
    client.force_login(cliente)

    with django_capture_on_commit_callbacks(execute=True):
        respuesta = client.post(
            _url(pedido, linea), {"opcion": LineaPedido.PAUSAR, "confirmar": "1"}
        )

    pedido.refresh_from_db()
    linea.refresh_from_db()
    assert respuesta.url == reverse("cuenta:pedido", args=[pedido.numero])
    assert linea.decision_demora == LineaPedido.PAUSAR
    assert linea.estado == LineaPedido.ESPERANDO_DEMORADO
    assert pedido.estado == Pedido.ESPERANDO_DEMORADO
    assert pedido.lineas.filter(estado=LineaPedido.DISPONIBLE).count() == 1
    entrada = _acciones(RegistroAuditoria.DECISION_DEMORA).get()
    assert entrada.actor == cliente and pedido.numero in entrada.detalle
    assert mailoutbox[0].to == [cliente.email]


@pytest.mark.django_db
def test_CO095_al_llegar_el_articulo_pausado_el_pedido_pasa_a_pendiente_de_armado(
    administrador, cliente, con_demora
):
    producto, pedido, linea = con_demora
    demora.confirmar_opcion(pedido, linea.pk, cliente, LineaPedido.PAUSAR)

    preventa.confirmar_ingreso({producto.pk: 1}, administrador)

    pedido.refresh_from_db()
    assert pedido.estado == Pedido.PENDIENTE_ARMADO


@pytest.mark.django_db
def test_CO095_despacho_diferido_empaqueta_lo_disponible_y_el_pedido(client, cliente, con_demora):
    _, pedido, linea = con_demora
    client.force_login(cliente)

    client.post(_url(pedido, linea), {"opcion": LineaPedido.DESPACHO_DIFERIDO, "confirmar": "1"})

    pedido.refresh_from_db()
    linea.refresh_from_db()
    otra = pedido.lineas.exclude(pk=linea.pk).get()
    assert linea.decision_demora == LineaPedido.DESPACHO_DIFERIDO
    assert linea.estado == LineaPedido.ESPERANDO_DEMORADO
    assert not linea.compensacion_cerrada
    assert otra.estado == LineaPedido.EMPAQUETADO
    assert pedido.estado == Pedido.EMPAQUETADO
    transicion = pedido.transiciones.last()
    assert (transicion.estado_nuevo, transicion.actor) == (Pedido.EMPAQUETADO, cliente)


@pytest.mark.django_db
def test_CO095_el_despacho_no_arrastra_al_articulo_diferido(administrador, cliente, con_demora):
    from apps.pedidos import servicios

    producto, pedido, linea = con_demora
    demora.confirmar_opcion(pedido, linea.pk, cliente, LineaPedido.DESPACHO_DIFERIDO)
    preventa.confirmar_ingreso({producto.pk: 1}, administrador)

    servicios.avanzar(pedido, administrador, estado_visto=Pedido.EMPAQUETADO)

    linea.refresh_from_db()
    assert linea.estado == LineaPedido.DISPONIBLE
    assert pedido.lineas.exclude(pk=linea.pk).get().estado == LineaPedido.DESPACHADO


@pytest.mark.django_db
def test_CO095_no_se_decide_dos_veces(client, cliente, con_demora):
    _, pedido, linea = con_demora
    client.force_login(cliente)
    client.post(_url(pedido, linea), {"opcion": LineaPedido.PAUSAR, "confirmar": "1"})

    respuesta = client.post(
        _url(pedido, linea), {"opcion": LineaPedido.CANCELAR, "confirmar": "1"}, follow=True
    )

    linea.refresh_from_db()
    assert linea.decision_demora == LineaPedido.PAUSAR
    assert "Ya elegiste" in respuesta.content.decode()
    assert not LotePuntos.objects.filter(origen=LotePuntos.REEMBOLSO).exists()


@pytest.mark.django_db
def test_CO095_con_la_ventana_vencida_se_rechaza_en_el_servidor(client, cliente, con_demora):
    _, pedido, linea = con_demora
    antes = _foto(pedido)

    with freeze_time(timezone.now() + timedelta(hours=73)):
        client.force_login(cliente)
        client.post(_url(pedido, linea), {"opcion": LineaPedido.PAUSAR, "confirmar": "1"})

    assert _foto(pedido) == antes


@pytest.mark.django_db
def test_CO156_volver_desde_la_confirmacion_no_registra_nada(client, cliente, con_demora):
    _, pedido, linea = con_demora
    client.force_login(cliente)
    antes = _foto(pedido)

    client.post(_url(pedido, linea), {"opcion": LineaPedido.CANCELAR})
    respuesta = client.get(_url(pedido, linea))

    assert respuesta.status_code == 200
    assert _foto(pedido) == antes
    assert not _acciones(RegistroAuditoria.DECISION_DEMORA).exists()


# ---------------------------------------------------------------------------
# CO-098 confirmarCancelacionDeArticuloDemorado
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_CO098_cancelar_reembolsa_el_valor_en_puntos_y_no_toca_el_stock(
    client, cliente, con_demora, mailoutbox, django_capture_on_commit_callbacks
):
    producto, pedido, linea = con_demora
    stock = Producto.objects.get(pk=producto.pk).stock
    client.force_login(cliente)

    with django_capture_on_commit_callbacks(execute=True):
        respuesta = client.post(
            _url(pedido, linea), {"opcion": LineaPedido.CANCELAR, "confirmar": "1"}, follow=True
        )

    pedido.refresh_from_db()
    linea.refresh_from_db()
    assert linea.estado == LineaPedido.CANCELADO_REEMBOLSO
    assert linea.decision_demora == LineaPedido.CANCELAR
    assert linea.compensacion_cerrada
    # B-08-005: la pre-venta nunca llegó, así que el stock no cambia.
    assert Producto.objects.get(pk=producto.pk).stock == stock
    lote = LotePuntos.objects.get(usuario=cliente)
    assert (lote.origen, lote.cantidad_acreditada) == (LotePuntos.REEMBOLSO, 1000)
    movimiento = MovimientoPuntos.objects.get(usuario=cliente)
    assert (movimiento.linea_pedido, movimiento.saldo_resultante) == (linea, 1000)
    # El pedido sigue con su otro artículo.
    assert pedido.estado == Pedido.PENDIENTE_ARMADO
    entrada = _acciones(RegistroAuditoria.CANCELACION_ARTICULO_DEMORADO).get()
    assert entrada.actor == cliente and "1000 pts" in entrada.detalle
    assert "tu saldo es de 1000 pts" in respuesta.content.decode()
    assert any("cancelado" in m.subject for m in mailoutbox)


@pytest.mark.django_db
def test_CO098_pagado_con_puntos_devuelve_los_mismos_puntos(cliente):
    fijar_parametros()
    _, pedido, linea = demorar(cliente, puntos=777)

    confirmacion = demora.confirmar_opcion(pedido, linea.pk, cliente, LineaPedido.CANCELAR)

    assert confirmacion.puntos == 777
    assert LotePuntos.objects.get(usuario=cliente).cantidad_acreditada == 777


@pytest.mark.django_db
def test_CO098_un_pedido_sin_otros_articulos_se_cancela_y_devuelve_el_envio(cliente):
    fijar_parametros()
    _, pedido, linea = demorar(cliente, otros=(), costo_envio="1500")

    confirmacion = demora.confirmar_opcion(pedido, linea.pk, cliente, LineaPedido.CANCELAR)

    pedido.refresh_from_db()
    assert pedido.estado == Pedido.CANCELADO
    assert confirmacion.puntos == 1000 + 150
    assert pedido.transiciones.last().estado_nuevo == Pedido.CANCELADO


@pytest.mark.django_db
def test_CO098_E1_si_falla_no_queda_nada_y_avisa_al_administrador(
    client, administrador, cliente, con_demora, mailoutbox
):
    _, pedido, linea = con_demora
    client.force_login(cliente)
    antes = _foto(pedido)

    with mock.patch("apps.puntos.servicios.acreditar", side_effect=RuntimeError("fallo")):
        respuesta = client.post(
            _url(pedido, linea), {"opcion": LineaPedido.CANCELAR, "confirmar": "1"}, follow=True
        )

    assert _foto(pedido) == antes
    assert not _acciones(RegistroAuditoria.CANCELACION_ARTICULO_DEMORADO).exists()
    assert "No quedó ningún cambio" in respuesta.content.decode()
    assert any(administrador.email in m.to and pedido.numero in m.body for m in mailoutbox)


@pytest.mark.django_db
def test_CO098_cancelado_el_articulo_sale_del_historial_activo(client, cliente):
    fijar_parametros()
    _, pedido, linea = demorar(cliente, otros=())
    demora.confirmar_opcion(pedido, linea.pk, cliente, LineaPedido.CANCELAR)
    client.force_login(cliente)

    activos = client.get(reverse("cuenta:panel"))
    historial = client.get(reverse("cuenta:historial"))

    assert pedido not in activos.context["pedidos"]
    assert pedido in historial.context["pedidos"]


# ---------------------------------------------------------------------------
# CO-096 ejecutarCicloDeVencimientoDeVentanaDeDecision
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_CO096_cierra_las_ventanas_vencidas_y_avisa_al_administrador(
    administrador, cliente, con_demora, mailoutbox
):
    _, pedido, linea = con_demora

    with freeze_time(timezone.now() + timedelta(hours=73)):
        cerradas = demora.ciclo_de_ventanas()

    pedido.refresh_from_db()
    linea.refresh_from_db()
    assert cerradas == [linea]
    assert linea.ventana_cerrada
    assert (linea.estado, linea.decision_demora) == (LineaPedido.ESPERANDO_DEMORADO, "")
    assert pedido.estado == Pedido.ESPERANDO_DEMORADO
    entrada = _acciones(RegistroAuditoria.VENCIMIENTO_VENTANA).get()
    assert entrada.actor is None and pedido.numero in entrada.detalle
    assert mailoutbox[-1].to == [administrador.email]


@pytest.mark.django_db
def test_CO096_mira_la_decision_y_no_el_estado(administrador, cliente, con_demora):
    _, pedido, linea = con_demora
    demora.confirmar_opcion(pedido, linea.pk, cliente, LineaPedido.PAUSAR)

    with freeze_time(timezone.now() + timedelta(hours=73)):
        cerradas = demora.ciclo_de_ventanas()

    linea.refresh_from_db()
    assert cerradas == []
    assert not linea.ventana_cerrada


@pytest.mark.django_db
def test_CO096_no_repite_ni_toca_las_vigentes(administrador, cliente, con_demora):
    _, pedido, linea = con_demora

    vigentes = demora.ciclo_de_ventanas()
    with freeze_time(timezone.now() + timedelta(hours=73)):
        demora.ciclo_de_ventanas()
        segunda = demora.ciclo_de_ventanas()

    assert (vigentes, segunda) == ([], [])
    assert _acciones(RegistroAuditoria.VENCIMIENTO_VENTANA).count() == 1


# ---------------------------------------------------------------------------
# CO-097 ejecutarCicloDeCompensacionPorRetraso
# ---------------------------------------------------------------------------


def _diferido(cliente, *, semanas_atras=0, precio="10000"):
    fijar_parametros()
    producto, pedido, linea = demorar(cliente, precio=precio)
    demora.confirmar_opcion(pedido, linea.pk, cliente, LineaPedido.DESPACHO_DIFERIDO)
    LineaPedido.objects.filter(pk=linea.pk).update(
        fecha_llegada_original=timezone.localdate() - timedelta(weeks=semanas_atras)
    )
    linea.refresh_from_db()
    return producto, pedido, linea


@pytest.mark.django_db
def test_CO097_acredita_el_5_por_ciento_por_semana_cumplida(
    cliente, mailoutbox, django_capture_on_commit_callbacks
):
    _, pedido, linea = _diferido(cliente, semanas_atras=1, precio="10010")

    with django_capture_on_commit_callbacks(execute=True):
        acreditadas = demora.ciclo_de_compensacion()

    linea.refresh_from_db()
    # 5 % de $10.010 son $500,50: 51 puntos, hacia arriba.
    assert [c.puntos for c in acreditadas] == [51]
    assert linea.compensacion_acumulada == Decimal("500.50")
    assert not linea.compensacion_cerrada
    lote = LotePuntos.objects.get(usuario=cliente)
    assert (lote.origen, lote.cantidad_acreditada) == (LotePuntos.COMPENSACION, 51)
    movimiento = MovimientoPuntos.objects.get(usuario=cliente)
    assert (movimiento.tipo, movimiento.linea_pedido) == (MovimientoPuntos.ACREDITACION, linea)
    entrada = _acciones(RegistroAuditoria.COMPENSACION_RETRASO).get()
    assert "51 pts" in entrada.detalle and "5 %" in entrada.detalle
    assert mailoutbox[-1].to == [cliente.email]
    assert "51 pts" in mailoutbox[-1].body


@pytest.mark.django_db
def test_CO097_correr_dos_veces_o_antes_de_la_semana_no_acredita_de_mas(cliente):
    _, _, linea = _diferido(cliente, semanas_atras=0)

    antes_de_la_semana = demora.ciclo_de_compensacion()
    with freeze_time(timezone.now() + timedelta(days=7)):
        primera = demora.ciclo_de_compensacion()
        segunda = demora.ciclo_de_compensacion()

    assert antes_de_la_semana == [] and segunda == []
    assert len(primera) == 1
    linea.refresh_from_db()
    assert linea.compensacion_acumulada == Decimal("500.00")


@pytest.mark.django_db
def test_CO097_el_tope_del_25_por_ciento_cierra_el_acumulador(cliente):
    _, _, linea = _diferido(cliente, semanas_atras=10)

    acreditadas = demora.ciclo_de_compensacion()
    with freeze_time(timezone.now() + timedelta(weeks=2)):
        despues = demora.ciclo_de_compensacion()

    linea.refresh_from_db()
    assert [c.puntos for c in acreditadas] == [250]
    assert linea.compensacion_acumulada == Decimal("2500.00")
    assert linea.compensacion_cerrada
    assert despues == []


@pytest.mark.django_db
def test_CO097_E1_un_articulo_que_llego_o_se_cancelo_no_acredita(administrador, cliente):
    producto, _, linea = _diferido(cliente, semanas_atras=2)
    preventa.confirmar_ingreso({producto.pk: 1}, administrador)

    acreditadas = demora.ciclo_de_compensacion()

    assert acreditadas == []
    assert not LotePuntos.objects.filter(origen=LotePuntos.COMPENSACION).exists()


@pytest.mark.django_db
def test_CO097_E2_un_acumulador_en_el_tope_y_abierto_se_cierra_sin_acreditar(cliente):
    _, _, linea = _diferido(cliente, semanas_atras=8)
    LineaPedido.objects.filter(pk=linea.pk).update(compensacion_acumulada=Decimal("2500"))

    acreditadas = demora.ciclo_de_compensacion()

    linea.refresh_from_db()
    assert acreditadas == []
    assert linea.compensacion_cerrada
    assert not LotePuntos.objects.filter(origen=LotePuntos.COMPENSACION).exists()
    assert (
        "se cerró sin acreditar" in _acciones(RegistroAuditoria.COMPENSACION_RETRASO).get().detalle
    )


@pytest.mark.django_db
def test_CO097_E3_sin_acumuladores_no_hace_nada(cliente):
    fijar_parametros()
    _, pedido, linea = demorar(cliente)
    demora.confirmar_opcion(pedido, linea.pk, cliente, LineaPedido.PAUSAR)
    LineaPedido.objects.filter(pk=linea.pk).update(
        fecha_llegada_original=timezone.localdate() - timedelta(weeks=3)
    )

    acreditadas = demora.ciclo_de_compensacion()

    assert acreditadas == []
    assert not _acciones(RegistroAuditoria.COMPENSACION_RETRASO).exists()


@pytest.mark.django_db
def test_CO098_con_envio_gratis_el_pedido_cancelado_solo_devuelve_el_articulo(cliente):
    fijar_parametros()
    _, pedido, linea = demorar(cliente, otros=(), costo_envio="0")

    confirmacion = demora.confirmar_opcion(pedido, linea.pk, cliente, LineaPedido.CANCELAR)

    pedido.refresh_from_db()
    assert pedido.estado == Pedido.CANCELADO
    assert confirmacion.puntos == 1000
