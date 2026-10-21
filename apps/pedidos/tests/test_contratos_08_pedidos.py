"""Pruebas de contrato de la gestión de pedidos (plan 08, primera parte).

`CO-182` consultarPedidos, `CO-183` consultarDetalleDePedido, `CO-092`
avanzarEstadoDePedido y `CO-093` confirmarAvancePeseADecisionPendiente. Todas
por la dirección real, como las usa el Administrador.
"""

from decimal import Decimal

import pytest
from django.core import mail
from django.urls import reverse

from apps.core.models import RegistroAuditoria
from apps.pedidos import servicios
from apps.pedidos.models import LineaPedido, Pedido, TransicionDePedido
from apps.pedidos.tests.util import crear_pedido

pytestmark = pytest.mark.django_db

URL_LISTA = reverse("pedidos:lista")


def avanzar(client, pedido, **extra):
    datos = {"estado_visto": pedido.estado, **extra}
    return client.post(reverse("pedidos:avanzar", args=[pedido.pk]), datos)


def foto(pedido):
    pedido.refresh_from_db()
    return (
        pedido.estado,
        list(pedido.lineas.values_list("estado", flat=True)),
        pedido.transiciones.count(),
    )


# ===========================================================================
# CO-182 · consultarPedidos
# ===========================================================================


def test_CO182_lista_los_pedidos_del_mas_reciente_al_mas_viejo(client_admin, cliente):
    viejo = crear_pedido(cliente, hace_dias=3)
    nuevo = crear_pedido(cliente)

    respuesta = client_admin.get(URL_LISTA)

    assert list(respuesta.context["pedidos"]) == [nuevo, viejo]


def test_CO182_cada_fila_trae_cliente_o_invitado_canal_estado_y_total(client_admin, cliente):
    crear_pedido(cliente, lineas=(("10000", 2), ("5000", 1, 500)), costo_envio="1500")
    crear_pedido(correo_invitado="lector@correo.test")

    contenido = client_admin.get(URL_LISTA).content.decode()
    pedidos = {p.usuario_id: p for p in client_admin.get(URL_LISTA).context["pedidos"]}

    assert pedidos[cliente.pk].cobrado == Decimal("21500")
    assert "Invitado" in contenido
    assert "lector@correo.test" in contenido
    assert "Pendiente de armado" in contenido
    assert "Online" in contenido


@pytest.mark.parametrize(
    ("filtro", "esperados"),
    [
        ({"estado": Pedido.ARMADO}, {"armado"}),
        ({"q": "lector@"}, {"invitado"}),
        ({"canal": Pedido.PRESENCIAL}, set()),
        ({"demorados": "1"}, {"demorado"}),
    ],
)
def test_CO182_filtra_por_estado_cliente_canal_y_demorados(
    client_admin, cliente, filtro, esperados
):
    nombres = {
        "pendiente": crear_pedido(cliente),
        "armado": crear_pedido(cliente, estado=Pedido.ARMADO),
        "invitado": crear_pedido(correo_invitado="lector@correo.test"),
        "demorado": crear_pedido(cliente, estado=Pedido.ARMADO),
    }
    nombres["demorado"].lineas.update(estado=LineaPedido.ESPERANDO_DEMORADO)
    if filtro.get("estado"):
        esperados = {"armado", "demorado"}

    respuesta = client_admin.get(URL_LISTA, filtro)

    por_pk = {p.pk: n for n, p in nombres.items()}
    assert {por_pk[p.pk] for p in respuesta.context["pedidos"]} == esperados


def test_CO182_filtra_por_rango_de_fechas(client_admin, cliente):
    crear_pedido(cliente, hace_dias=10)
    reciente = crear_pedido(cliente, hace_dias=1)
    from django.utils import timezone

    desde = (timezone.localdate() - timezone.timedelta(days=2)).isoformat()

    respuesta = client_admin.get(URL_LISTA, {"desde": desde})

    assert list(respuesta.context["pedidos"]) == [reciente]


def test_CO182_E1_sin_resultados_informa_y_ofrece_limpiar(client_admin, cliente):
    crear_pedido(cliente)

    contenido = client_admin.get(URL_LISTA, {"q": "nadie"}).content.decode()

    assert "Ningún pedido coincide con los filtros." in contenido
    assert "Limpiar filtros" in contenido


def test_CO182_un_filtro_invalido_se_ignora(client_admin, cliente):
    crear_pedido(cliente)

    respuesta = client_admin.get(URL_LISTA, {"estado": "inventado", "desde": "ayer"})

    assert len(respuesta.context["pedidos"]) == 1


def test_CO182_hace_las_mismas_consultas_con_pocos_o_muchos_pedidos(
    client_admin, cliente, django_assert_max_num_queries
):
    for _ in range(3):
        crear_pedido(cliente)
    client_admin.get(URL_LISTA)
    for _ in range(20):
        crear_pedido(cliente, lineas=(("1000", 1), ("2000", 2)))

    # 12 de la lista, más 4 fijas del plan 00 de interfaz: los contadores del menú
    # (U5) y las transiciones del riel de cada fila, precargadas en una (P7).
    with django_assert_max_num_queries(16):
        client_admin.get(URL_LISTA)


def test_CO182_no_modifica_el_estado_del_sistema(client_admin, cliente):
    pedido = crear_pedido(cliente)
    antes = foto(pedido)
    registros = RegistroAuditoria.objects.count()

    client_admin.get(URL_LISTA)

    assert foto(pedido) == antes
    assert RegistroAuditoria.objects.count() == registros


# ===========================================================================
# CO-183 · consultarDetalleDePedido
# ===========================================================================


def test_CO183_muestra_cliente_items_puntos_pago_y_linea_de_tiempo(client_admin, cliente):
    pedido = crear_pedido(cliente, lineas=(("10000", 1), ("5000", 1, 500)))

    respuesta = client_admin.get(reverse("pedidos:detalle", args=[pedido.pk]))

    contenido = respuesta.content.decode()
    assert respuesta.context["puntos_canjeados"] == 500
    assert respuesta.context["cobrado"] == Decimal("11500")
    assert "Pasarela" in contenido
    assert "500 pts" in contenido
    assert len(respuesta.context["transiciones"]) == 1
    assert "Avanzar a armado" in contenido


def test_CO183_en_un_estado_automatico_no_ofrece_avanzar(client_admin, cliente):
    pedido = crear_pedido(cliente, estado=Pedido.ESPERANDO_PRE_VENTA)

    contenido = client_admin.get(reverse("pedidos:detalle", args=[pedido.pk])).content.decode()

    assert "Avanzar a" not in contenido
    assert "Esperando stock de pre-venta para el armado." in contenido


def test_CO183_un_pedido_pagado_sólo_con_puntos_lo_dice(client_admin, cliente):
    pedido = crear_pedido(cliente, lineas=(("5000", 1, 500),), costo_envio="0", con_pago=False)

    contenido = client_admin.get(reverse("pedidos:detalle", args=[pedido.pk])).content.decode()

    assert "Sólo puntos" in contenido


def test_CO183_no_modifica_el_estado_del_sistema(client_admin, cliente):
    pedido = crear_pedido(cliente)
    antes = foto(pedido)

    client_admin.get(reverse("pedidos:detalle", args=[pedido.pk]))

    assert foto(pedido) == antes


# ===========================================================================
# CO-092 · avanzarEstadoDePedido
# ===========================================================================


@pytest.mark.parametrize(
    ("desde", "hasta"),
    [
        (Pedido.PENDIENTE_ARMADO, Pedido.ARMADO),
        (Pedido.ARMADO, Pedido.EMPAQUETADO),
        (Pedido.EMPAQUETADO, Pedido.DESPACHADO),
    ],
)
def test_CO092_c_el_estado_pasa_al_unico_siguiente(client_admin, cliente, desde, hasta):
    pedido = crear_pedido(cliente, estado=desde)
    assert pedido.estado == desde

    avanzar(client_admin, pedido)

    pedido.refresh_from_db()
    assert pedido.estado == hasta


def test_CO092_c_armado_no_toca_las_lineas(client_admin, cliente):
    pedido = crear_pedido(cliente)

    avanzar(client_admin, pedido)

    assert set(pedido.lineas.values_list("estado", flat=True)) == {LineaPedido.DISPONIBLE}


def test_CO092_c_empaquetado_y_despachado_avanzan_las_lineas_disponibles(client_admin, cliente):
    pedido = crear_pedido(cliente, estado=Pedido.ARMADO, lineas=(("1000", 1), ("2000", 1)))

    avanzar(client_admin, pedido)
    assert set(pedido.lineas.values_list("estado", flat=True)) == {LineaPedido.EMPAQUETADO}
    pedido.refresh_from_db()
    avanzar(client_admin, pedido)

    assert set(pedido.lineas.values_list("estado", flat=True)) == {LineaPedido.DESPACHADO}


def test_CO092_c_las_lineas_demoradas_no_avanzan(client_admin, cliente):
    pedido = crear_pedido(cliente, estado=Pedido.ARMADO, lineas=(("1000", 1), ("2000", 1)))
    demorada = pedido.lineas.first()
    demorada.estado = LineaPedido.ESPERANDO_DEMORADO
    demorada.decision_demora = LineaPedido.PAUSAR
    demorada.save()

    avanzar(client_admin, pedido)

    demorada.refresh_from_db()
    assert demorada.estado == LineaPedido.ESPERANDO_DEMORADO


def test_CO092_queda_una_transicion_en_la_linea_de_tiempo(client_admin, cliente, administrador):
    pedido = crear_pedido(cliente)

    avanzar(client_admin, pedido)

    transicion = pedido.transiciones.last()
    assert (transicion.estado_anterior, transicion.estado_nuevo) == (
        Pedido.PENDIENTE_ARMADO,
        Pedido.ARMADO,
    )
    assert transicion.actor == administrador


def test_CO092_queda_en_la_auditoria_con_el_estado_anterior_y_el_nuevo(
    client_admin, cliente, administrador
):
    pedido = crear_pedido(cliente)

    avanzar(client_admin, pedido)

    registro = RegistroAuditoria.objects.get(accion=RegistroAuditoria.AVANCE_ESTADO_PEDIDO)
    assert registro.actor == administrador
    assert registro.objetivo == pedido
    assert "Pendiente de armado → Armado" in registro.detalle


def test_CO092_el_cliente_recibe_la_notificacion(
    client_admin, cliente, django_capture_on_commit_callbacks
):
    pedido = crear_pedido(cliente)

    with django_capture_on_commit_callbacks(execute=True):
        avanzar(client_admin, pedido)

    assert mail.outbox[-1].to == [cliente.email]
    assert "armado" in mail.outbox[-1].subject


def test_CO092_el_invitado_recibe_la_notificacion_en_su_correo(
    client_admin, django_capture_on_commit_callbacks
):
    pedido = crear_pedido(correo_invitado="lector@correo.test")

    with django_capture_on_commit_callbacks(execute=True):
        avanzar(client_admin, pedido)

    assert mail.outbox[-1].to == ["lector@correo.test"]
    assert "a este correo" in mail.outbox[-1].body


def test_CO092_un_correo_caido_no_deshace_el_avance(
    client_admin, cliente, django_capture_on_commit_callbacks, monkeypatch
):
    def caido(**kwargs):
        raise OSError("SMTP caído")

    monkeypatch.setattr(servicios, "enviar_correo", caido)
    pedido = crear_pedido(cliente)

    with django_capture_on_commit_callbacks(execute=True):
        avanzar(client_admin, pedido)

    pedido.refresh_from_db()
    assert pedido.estado == Pedido.ARMADO


@pytest.mark.parametrize("estado", [Pedido.ESPERANDO_PRE_VENTA, Pedido.ESPERANDO_DEMORADO])
def test_CO092_E1_un_estado_automatico_no_se_avanza_a_mano(client_admin, cliente, estado):
    pedido = crear_pedido(cliente, estado=estado)
    antes = foto(pedido)

    respuesta = avanzar(client_admin, pedido)

    assert foto(pedido) == antes
    texto = client_admin.get(respuesta.url).content.decode()
    assert "avanza sólo cuando el sistema" in texto
    assert not RegistroAuditoria.objects.filter(
        accion=RegistroAuditoria.AVANCE_ESTADO_PEDIDO
    ).exists()


def test_CO092_un_pedido_despachado_no_tiene_siguiente(client_admin, cliente):
    pedido = crear_pedido(cliente, estado=Pedido.DESPACHADO)
    antes = foto(pedido)

    avanzar(client_admin, pedido)

    assert foto(pedido) == antes


def test_CO092_no_se_saltea_un_paso_si_el_pedido_cambio_en_otra_pantalla(client_admin, cliente):
    pedido = crear_pedido(cliente)
    visto = pedido.estado
    Pedido.objects.filter(pk=pedido.pk).update(estado=Pedido.ARMADO)

    client_admin.post(reverse("pedidos:avanzar", args=[pedido.pk]), {"estado_visto": visto})

    pedido.refresh_from_db()
    assert pedido.estado == Pedido.ARMADO


def test_CO092_E2_con_decision_pendiente_advierte_y_no_avanza(client_admin, cliente):
    pedido = crear_pedido(cliente, estado=Pedido.ARMADO, lineas=(("1000", 1), ("2000", 1)))
    pedido.lineas.filter(pk=pedido.lineas.first().pk).update(estado=LineaPedido.ESPERANDO_DEMORADO)
    antes = foto(pedido)

    respuesta = avanzar(client_admin, pedido)

    assert respuesta.status_code == 200
    assert "Artículos demorados sin decisión del cliente." in respuesta.content.decode()
    assert foto(pedido) == antes


def test_CO092_la_confirmacion_muestra_el_estado_actual_y_el_siguiente(client_admin, cliente):
    pedido = crear_pedido(cliente)

    contenido = client_admin.get(reverse("pedidos:avanzar", args=[pedido.pk])).content.decode()

    assert "De <strong>Pendiente de armado</strong> a <strong>Armado</strong>" in contenido


# ===========================================================================
# CO-093 · confirmarAvancePeseADecisionPendiente
# ===========================================================================


def test_CO093_avanza_y_los_pendientes_conservan_su_estado(client_admin, cliente):
    pedido = crear_pedido(cliente, estado=Pedido.ARMADO, lineas=(("1000", 1), ("2000", 1)))
    demorada, disponible = pedido.lineas.order_by("pk")
    LineaPedido.objects.filter(pk=demorada.pk).update(estado=LineaPedido.ESPERANDO_DEMORADO)

    avanzar(client_admin, pedido, confirmado="1")

    pedido.refresh_from_db()
    demorada.refresh_from_db()
    disponible.refresh_from_db()
    assert pedido.estado == Pedido.EMPAQUETADO
    assert demorada.estado == LineaPedido.ESPERANDO_DEMORADO
    assert demorada.decision_demora == ""
    assert disponible.estado == LineaPedido.EMPAQUETADO
    registro = RegistroAuditoria.objects.get(accion=RegistroAuditoria.AVANCE_ESTADO_PEDIDO)
    assert "1 artículo(s) con decisión pendiente" in registro.detalle


# ===========================================================================
# La línea de tiempo arranca con la compra (B-08-001)
# ===========================================================================


def test_la_primera_transicion_es_la_del_estado_inicial(cliente):
    pedido = crear_pedido(cliente)

    transicion = TransicionDePedido.objects.get(pedido=pedido)

    assert transicion.estado_anterior == ""
    assert transicion.estado_nuevo == Pedido.PENDIENTE_ARMADO
