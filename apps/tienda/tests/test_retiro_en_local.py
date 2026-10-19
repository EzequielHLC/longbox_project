"""Retiro en el local (plan 07, octava parte).

Las enmiendas de `CO-087`, `CO-088`, `CO-089`, `CO-092`, `CO-154`, `CO-217` y
`CO-227` para el pedido que se retira en el local, y las devoluciones de lo
retirado (ambigüedad 4).
"""

from datetime import timedelta
from decimal import Decimal

import pytest
from django.db import IntegrityError, transaction
from django.test import Client
from django.urls import reverse
from django.utils import timezone

from apps.accounts.tests.factories import UsuarioFactory
from apps.almacen import servicios as almacen
from apps.almacen.models import ArticuloRetenido
from apps.core.models import RegistroAuditoria
from apps.devoluciones import servicios as devoluciones
from apps.pedidos import demora, preventa
from apps.pedidos import servicios as pedidos
from apps.pedidos.models import LineaPedido, Pedido
from apps.pedidos.tests.util import demorar
from apps.puntos import servicios as puntos
from apps.puntos.models import LotePuntos
from apps.tienda import compra
from apps.tienda.models import CobroEnCurso
from apps.tienda.tests.compra_util import (
    DIRECCION_PERFIL,
    URL_CHECKOUT,
    agregar,
    avisar,
    cliente_con_direccion,
    confirmar,
    dar_puntos,
    fijar_parametros,
    producto,
)


@pytest.fixture
def titular(db):
    fijar_parametros()
    return cliente_con_direccion(first_name="Ana", last_name="Lectora")


@pytest.fixture
def navegador(client, titular):
    client.force_login(titular)
    return client


@pytest.fixture
def panel(db):
    sesion = Client()
    sesion.force_login(UsuarioFactory(rol="administrador"))
    return sesion


def _elegir_retiro(navegador):
    return navegador.post(URL_CHECKOUT, {"modalidad": "retiro"})


def _comprar_para_retirar(navegador, *productos):
    for prod, cantidad in productos:
        agregar(navegador, prod, cantidad)
    _elegir_retiro(navegador)
    _, cobro = confirmar(navegador)
    avisar(navegador, cobro)
    cobro.refresh_from_db()
    return cobro.pedido


def _armar(panel, pedido):
    for _ in range(2):
        pedido.refresh_from_db()
        panel.post(reverse("pedidos:avanzar", args=[pedido.pk]), {"estado_visto": pedido.estado})
    pedido.refresh_from_db()
    return pedido


def _retiro(pedido):
    Pedido.objects.filter(pk=pedido.pk).update(
        modalidad=Pedido.RETIRO,
        costo_envio=0,
        envio_direccion="",
        envio_localidad="",
        envio_provincia="",
        envio_codigo_postal="",
    )
    pedido.refresh_from_db()
    return pedido


# ---------------------------------------------------------------------------
# CO-087 · CO-180: la modalidad en el checkout
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_CO087_con_retiro_el_envio_cuesta_cero_y_no_se_pide_direccion(titular, navegador):
    agregar(navegador, producto(precio="10000"))

    _elegir_retiro(navegador)
    respuesta = navegador.get(URL_CHECKOUT)

    resumen = respuesta.context["resumen"]
    assert resumen.retiro is True
    assert resumen.costo_envio == 0
    assert resumen.direccion_completa is True
    assert resumen.total == Decimal("10000")
    contenido = respuesta.content.decode()
    assert "Lo retirás en el local" in contenido
    assert 'role="progressbar"' not in contenido  # sin la barra del envío gratis


@pytest.mark.django_db
def test_CO087_la_modalidad_no_toca_el_perfil(titular, navegador):
    agregar(navegador, producto())

    _elegir_retiro(navegador)

    titular.refresh_from_db()
    assert titular.direccion == DIRECCION_PERFIL["direccion"]


@pytest.mark.django_db
def test_CO087_se_puede_volver_a_envio_a_domicilio_antes_de_confirmar(titular, navegador):
    agregar(navegador, producto(precio="10000"))
    _elegir_retiro(navegador)

    navegador.post(URL_CHECKOUT, {"modalidad": "envio"})

    resumen = navegador.get(URL_CHECKOUT).context["resumen"]
    assert resumen.retiro is False
    assert resumen.costo_envio == Decimal("1500")


@pytest.mark.django_db
def test_CO090_D4_el_invitado_no_puede_retirar():
    from django.contrib.auth.models import AnonymousUser

    from apps.tienda.models import Carrito

    carrito = Carrito.objects.create()
    resumen = compra.resumen(carrito, usuario=AnonymousUser(), envio={}, retiro=True)

    assert resumen.retiro is False
    assert resumen.direccion_completa is False


# ---------------------------------------------------------------------------
# CO-088 · CO-089: el pedido nace para retirar
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_CO088_el_cobro_congela_el_retiro_sin_envio(titular, navegador):
    agregar(navegador, producto(precio="10000"))
    _elegir_retiro(navegador)

    _, cobro = confirmar(navegador)

    assert cobro.retiro is True
    assert cobro.costo_envio == 0
    assert not any(cobro.envio.values())
    assert cobro.monto == Decimal("10000")


@pytest.mark.django_db
def test_CO089_el_pedido_nace_para_retirar_sin_direccion_ni_envio(titular, navegador):
    prod = producto(stock=3, precio="10000")

    pedido = _comprar_para_retirar(navegador, (prod, 1))

    prod.refresh_from_db()
    assert pedido.modalidad == Pedido.RETIRO
    assert pedido.estado == Pedido.PENDIENTE_ARMADO
    assert pedido.costo_envio == 0
    assert pedido.direccion_de_envio == ""
    assert prod.stock == 2
    assert puntos.saldo(titular) == 100  # 10 % de $ 10.000 a $ 10 el punto
    assert (
        "retiro en el local"
        in RegistroAuditoria.objects.get(accion=RegistroAuditoria.COMPRA_ONLINE).detalle
    )


@pytest.mark.django_db
def test_CO089_D4_un_cobro_de_retiro_sin_cuenta_no_genera_pedido(db):
    fijar_parametros()
    prod = producto(stock=2)
    cobro = CobroEnCurso.objects.create(
        referencia="retiro-invitado",
        pasarela="prueba",
        correo_invitado="invitado@correo.test",
        lineas=[{"producto": prod.pk, "cantidad": 1, "precio": "10000", "puntos": 0}],
        costo_envio=0,
        monto=Decimal("10000"),
        retiro=True,
    )

    compra.registrar_resultado(cobro.referencia, referencia_pago="p-1", monto=Decimal("10000"))

    cobro.refresh_from_db()
    assert cobro.estado == CobroEnCurso.REEMBOLSADO
    assert not Pedido.objects.exists()


@pytest.mark.django_db
def test_D4_la_base_no_admite_un_pedido_para_retirar_sin_cuenta_o_con_envio(titular):
    with pytest.raises(IntegrityError), transaction.atomic():
        Pedido.objects.create(
            canal=Pedido.ONLINE,
            estado=Pedido.PENDIENTE_ARMADO,
            modalidad=Pedido.RETIRO,
            correo_invitado="invitado@correo.test",
        )
    with pytest.raises(IntegrityError), transaction.atomic():
        Pedido.objects.create(
            canal=Pedido.ONLINE,
            estado=Pedido.PENDIENTE_ARMADO,
            modalidad=Pedido.RETIRO,
            usuario=titular,
            costo_envio=Decimal("1500"),
        )


# ---------------------------------------------------------------------------
# CO-092: de Armado a En el local
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_CO092_el_pedido_armado_pasa_a_en_el_local_y_nunca_a_empaquetado(titular, navegador, panel):
    pedido = _comprar_para_retirar(navegador, (producto(), 1))

    pedido = _armar(panel, pedido)

    estados = list(pedido.transiciones.values_list("estado_nuevo", flat=True))
    assert pedido.estado == Pedido.EN_LOCAL
    assert Pedido.EMPAQUETADO not in estados
    assert Pedido.DESPACHADO not in estados
    assert pedidos.siguiente_estado(pedido) is None


@pytest.mark.django_db
def test_CO092_cada_unidad_entra_al_stock_en_local_como_pedido_para_retirar(
    titular, navegador, panel
):
    fijar_parametros(plazo_retencion_meses=3)
    pedido = _comprar_para_retirar(
        navegador, (producto(precio="10000"), 2), (producto(precio="8000"), 1)
    )
    assert not ArticuloRetenido.objects.exists()

    _armar(panel, pedido)

    articulos = list(ArticuloRetenido.objects.order_by("valor", "pk"))
    hoy = timezone.localdate()
    assert len(articulos) == 3
    assert [a.valor for a in articulos] == [Decimal("8000"), Decimal("10000"), Decimal("10000")]
    for articulo in articulos:
        assert articulo.usuario == titular
        assert articulo.procedencia == ArticuloRetenido.PARA_RETIRAR
        assert articulo.estado == ArticuloRetenido.DISPONIBLE
        assert articulo.fecha_vencimiento == almacen.vencimiento_desde(hoy, 3)
        assert articulo.linea_pedido.pedido == pedido


@pytest.mark.django_db
def test_CO092_avisa_que_esta_listo_para_retirar(
    titular, navegador, panel, mailoutbox, django_capture_on_commit_callbacks
):
    pedido = _comprar_para_retirar(navegador, (producto(), 1))
    pedido.refresh_from_db()
    panel.post(reverse("pedidos:avanzar", args=[pedido.pk]), {"estado_visto": pedido.estado})

    with django_capture_on_commit_callbacks(execute=True):
        panel.post(reverse("pedidos:avanzar", args=[pedido.pk]), {"estado_visto": Pedido.ARMADO})

    aviso = mailoutbox[-1]
    assert aviso.to == [titular.email]
    assert "en el local" in aviso.subject
    assert "listo para retirar" in aviso.body


@pytest.mark.django_db
def test_CO092_avanzar_dos_veces_no_duplica_los_articulos(titular, navegador, panel):
    pedido = _comprar_para_retirar(navegador, (producto(), 1))
    _armar(panel, pedido)

    panel.post(reverse("pedidos:avanzar", args=[pedido.pk]), {"estado_visto": Pedido.ARMADO})

    assert ArticuloRetenido.objects.count() == 1


@pytest.mark.django_db
def test_CO092_las_lineas_no_cambian_al_pasar_a_en_el_local(titular, navegador, panel):
    pedido = _comprar_para_retirar(navegador, (producto(), 1))

    _armar(panel, pedido)

    assert list(pedido.lineas.values_list("estado", flat=True)) == [LineaPedido.DISPONIBLE]


@pytest.mark.django_db
def test_el_pedido_para_retirar_muestra_su_modalidad_al_cliente_y_al_administrador(
    titular, navegador, panel
):
    pedido = _comprar_para_retirar(navegador, (producto(), 1))
    _armar(panel, pedido)

    del_cliente = navegador.get(reverse("cuenta:pedido", args=[pedido.numero])).content.decode()
    del_panel = panel.get(reverse("pedidos:detalle", args=[pedido.pk])).content.decode()

    assert "Retiro en el local" in del_cliente
    assert reverse("cuenta:stock") in del_cliente
    assert reverse("almacen:retiro_pedido", args=[pedido.pk]) in del_panel


# ---------------------------------------------------------------------------
# Ambigüedad 3: una pre-venta demorada en un pedido para retirar
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_la_opcion_2_en_un_pedido_para_retirar_lo_devuelve_al_armado(titular):
    _, pedido, linea = demorar(titular)
    pedido = _retiro(pedido)

    opciones = demora.consultar_opciones(linea).opciones
    demora.confirmar_opcion(pedido, linea.pk, titular, LineaPedido.DESPACHO_DIFERIDO)

    pedido.refresh_from_db()
    assert demora.DIFERIR_RETIRO in opciones
    assert demora.DIFERIR not in opciones
    assert pedido.estado == Pedido.PENDIENTE_ARMADO
    assert set(pedido.lineas.exclude(pk=linea.pk).values_list("estado", flat=True)) == {
        LineaPedido.DISPONIBLE
    }


@pytest.mark.django_db
def test_el_demorado_de_un_pedido_para_retirar_entra_como_para_retirar(titular, administrador):
    producto_demorado, pedido, linea = demorar(titular)
    pedido = _retiro(pedido)
    demora.confirmar_opcion(pedido, linea.pk, titular, LineaPedido.DESPACHO_DIFERIDO)
    pedidos.avanzar(pedido, administrador, estado_visto=Pedido.PENDIENTE_ARMADO)
    pedido.refresh_from_db()
    pedidos.avanzar(pedido, administrador, estado_visto=Pedido.ARMADO)

    preventa.confirmar_ingreso({producto_demorado.pk: 1}, administrador)

    diferido = ArticuloRetenido.objects.get(linea_pedido=linea)
    disponibles = ArticuloRetenido.objects.exclude(linea_pedido=linea)
    assert diferido.procedencia == ArticuloRetenido.PARA_RETIRAR
    assert disponibles.count() == 1  # lo que se armó antes, sin la línea diferida


# ---------------------------------------------------------------------------
# Ambigüedad 5: entregar todo en el mostrador (CO-227)
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_CO227_entregar_todo_retira_cada_articulo_disponible_del_pedido(
    titular, navegador, panel, cajero
):
    pedido = _comprar_para_retirar(navegador, (producto(), 2), (producto(), 1))
    _armar(panel, pedido)
    mostrador = Client()
    mostrador.force_login(cajero)
    url = reverse("almacen:retiro_pedido", args=[pedido.pk])

    verificacion = mostrador.get(url)
    ids = [a.pk for a in verificacion.context["articulos"]]
    mostrador.post(url, {"articulo": ids})

    assert verificacion.context["titular"] == titular
    assert len(ids) == 3
    assert set(ArticuloRetenido.objects.values_list("estado", flat=True)) == {
        ArticuloRetenido.RETIRADO
    }
    assert RegistroAuditoria.objects.filter(accion=RegistroAuditoria.RETIRO_EN_LOCAL).count() == 3


@pytest.mark.django_db
def test_CO227_E1_si_un_articulo_cambio_no_se_entrega_ninguno(titular, navegador, panel, cajero):
    pedido = _comprar_para_retirar(navegador, (producto(), 2))
    _armar(panel, pedido)
    uno, otro = ArticuloRetenido.objects.order_by("pk")
    almacen.retirar(uno.pk, cajero)

    with pytest.raises(almacen.OperacionRechazada):
        almacen.retirar_pedido(pedido.pk, cajero, [uno.pk, otro.pk])

    otro.refresh_from_db()
    assert otro.estado == ArticuloRetenido.DISPONIBLE


@pytest.mark.django_db
def test_acceso_el_cliente_no_entrega_su_propio_pedido(titular, navegador, panel):
    pedido = _comprar_para_retirar(navegador, (producto(), 1))
    _armar(panel, pedido)
    articulo = ArticuloRetenido.objects.get()

    respuesta = navegador.post(
        reverse("almacen:retiro_pedido", args=[pedido.pk]), {"articulo": [articulo.pk]}
    )

    articulo.refresh_from_db()
    assert respuesta.status_code == 403
    assert articulo.estado == ArticuloRetenido.DISPONIBLE


# ---------------------------------------------------------------------------
# CO-217 · CO-218: el origen nuevo
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_CO218_la_ficha_muestra_el_origen_y_el_acceso_a_entregar_todo(titular, navegador, panel):
    pedido = _comprar_para_retirar(navegador, (producto(), 1))
    _armar(panel, pedido)
    articulo = ArticuloRetenido.objects.get()

    contenido = panel.get(reverse("almacen:ficha", args=[articulo.pk])).content.decode()

    assert f"Pedido {pedido.numero} · pedido para retirar" in contenido
    assert reverse("almacen:retiro_pedido", args=[pedido.pk]) in contenido


# ---------------------------------------------------------------------------
# CO-154: el vencimiento devuelve su valor en puntos (D3)
# ---------------------------------------------------------------------------


def _vencer(articulo):
    ArticuloRetenido.objects.filter(pk=articulo.pk).update(fecha_vencimiento=timezone.localdate())


@pytest.mark.django_db
def test_CO154_D3_lo_no_retirado_vuelve_al_stock_con_su_valor_en_puntos(titular, navegador, panel):
    prod = producto(stock=2, precio="10000")
    pedido = _comprar_para_retirar(navegador, (prod, 1))
    _armar(panel, pedido)
    articulo = ArticuloRetenido.objects.get()
    _vencer(articulo)
    antes = puntos.saldo(titular)

    almacen.ciclo_de_vencimiento()

    articulo.refresh_from_db()
    prod.refresh_from_db()
    assert articulo.estado == ArticuloRetenido.VENCIDO
    assert prod.stock == 2
    lote = LotePuntos.objects.get(origen=LotePuntos.REEMBOLSO)
    assert lote.cantidad_acreditada == 1000  # $ 10.000 a $ 10 el punto
    # Plan 00, C2: menos los 100 puntos que esa unidad había sumado con la compra.
    assert puntos.saldo(titular) == antes + 1000 - 100
    registro = RegistroAuditoria.objects.filter(
        accion=RegistroAuditoria.VENCIMIENTO_RETENCION
    ).get()
    assert "Reembolso de 1000 pts" in registro.detalle


@pytest.mark.django_db
def test_CO154_D3_una_unidad_pagada_con_puntos_devuelve_sus_puntos(titular, navegador, panel):
    dar_puntos(titular, 5000)
    prod = producto(stock=2, precio="10000")
    agregar(navegador, prod, 1)
    linea = navegador.get(URL_CHECKOUT).context["resumen"].lineas[0].linea
    navegador.post(reverse("compra:canje", args=[linea.pk]))
    _elegir_retiro(navegador)
    _, cobro = confirmar(navegador)
    cobro.refresh_from_db()
    _armar(panel, cobro.pedido)
    articulo = ArticuloRetenido.objects.get()
    _vencer(articulo)

    almacen.ciclo_de_vencimiento()

    assert LotePuntos.objects.get(origen=LotePuntos.REEMBOLSO).cantidad_acreditada == 1000


@pytest.mark.django_db
def test_CO154_el_despacho_diferido_tambien_vuelve_con_reembolso(titular):
    from apps.almacen.tests.util import retenido

    articulo = retenido(titular, vence_en=0)

    almacen.ciclo_de_vencimiento()

    articulo.refresh_from_db()
    assert articulo.estado == ArticuloRetenido.VENCIDO
    assert LotePuntos.objects.filter(origen=LotePuntos.REEMBOLSO).exists()  # plan 00, C2


@pytest.mark.django_db
def test_CO154_correr_dos_veces_no_reembolsa_dos_veces(titular, navegador, panel):
    pedido = _comprar_para_retirar(navegador, (producto(precio="10000"), 1))
    _armar(panel, pedido)
    _vencer(ArticuloRetenido.objects.get())

    almacen.ciclo_de_vencimiento()
    almacen.ciclo_de_vencimiento()

    assert LotePuntos.objects.filter(origen=LotePuntos.REEMBOLSO).count() == 1


@pytest.mark.django_db
def test_CO154_el_aviso_previo_dice_que_vuelve_con_reembolso(
    titular, navegador, panel, mailoutbox, django_capture_on_commit_callbacks
):
    pedido = _comprar_para_retirar(navegador, (producto(), 1))
    _armar(panel, pedido)
    ArticuloRetenido.objects.update(fecha_vencimiento=timezone.localdate() + timedelta(days=3))

    with django_capture_on_commit_callbacks(execute=True):
        almacen.ciclo_de_vencimiento()

    assert "te devolvemos su valor en puntos" in mailoutbox[-1].body


# ---------------------------------------------------------------------------
# Ambigüedad 4: las devoluciones de lo retirado
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_CO185_lo_retirado_se_puede_reclamar_desde_el_retiro(titular, navegador, panel, cajero):
    pedido = _comprar_para_retirar(navegador, (producto(), 1))
    _armar(panel, pedido)
    url = reverse("cuenta:devolucion", args=[pedido.numero])
    antes = navegador.get(url, follow=True)
    almacen.retirar(ArticuloRetenido.objects.get().pk, cajero)

    despues = navegador.get(url)

    assert "solicitud" not in antes.context
    assert "Todavía no retiraste nada" in antes.content.decode()
    assert [linea.pk for linea in despues.context["solicitud"].lineas] == [pedido.lineas.get().pk]


@pytest.mark.django_db
def test_CO099_el_plazo_de_lo_retirado_corre_desde_el_retiro(titular, navegador, panel, cajero):
    fijar_parametros(plazo_garantia_dias=10)  # plan 00, C1: la garantía tiene su plazo
    pedido = _comprar_para_retirar(navegador, (producto(), 1))
    _armar(panel, pedido)
    articulo = ArticuloRetenido.objects.get()
    almacen.retirar(articulo.pk, cajero)
    ArticuloRetenido.objects.filter(pk=articulo.pk).update(
        actualizado_en=timezone.now() - timedelta(days=11)
    )
    linea = pedido.lineas.get()

    with pytest.raises(devoluciones.PlazoVencido):
        devoluciones.registrar_caso(pedido, linea.pk, titular, "defecto", "", [])

    assert devoluciones.estado_de_reclamo(pedido).puede is False


@pytest.mark.django_db
def test_el_estado_de_reclamo_ofrece_el_boton_en_el_pedido_retirado(
    titular, navegador, panel, cajero
):
    pedido = _comprar_para_retirar(navegador, (producto(), 1))
    _armar(panel, pedido)
    almacen.retirar(ArticuloRetenido.objects.get().pk, cajero)

    contenido = navegador.get(reverse("cuenta:pedido", args=[pedido.numero])).content.decode()

    assert reverse("cuenta:devolucion", args=[pedido.numero]) in contenido


@pytest.mark.django_db(transaction=True)
def test_concurrencia_dos_mostradores_que_entregan_el_mismo_pedido_registran_una_vez():
    from apps.core.tests.concurrencia import a_la_vez, errores_internos, sesion_de

    fijar_parametros()
    titular = cliente_con_direccion()
    administrador = UsuarioFactory(rol="administrador")
    pedido = Pedido.objects.create(
        canal=Pedido.ONLINE,
        estado=Pedido.ARMADO,
        modalidad=Pedido.RETIRO,
        usuario=titular,
    )
    pedido.asignar_numero()
    LineaPedido.objects.create(
        pedido=pedido,
        producto=producto(),
        cantidad=2,
        precio_unitario=Decimal("10000"),
        estado=LineaPedido.DISPONIBLE,
    )
    pedidos.avanzar(pedido, administrador, estado_visto=Pedido.ARMADO)
    ids = list(ArticuloRetenido.objects.values_list("pk", flat=True))
    url = reverse("almacen:retiro_pedido", args=[pedido.pk])
    una = sesion_de(UsuarioFactory(rol="cajero"))
    otra = sesion_de(UsuarioFactory(rol="cajero"))

    respuestas = a_la_vez(
        lambda: una.post(url, {"articulo": ids}), lambda: otra.post(url, {"articulo": ids})
    )

    assert errores_internos(respuestas) == []
    assert RegistroAuditoria.objects.filter(accion=RegistroAuditoria.RETIRO_EN_LOCAL).count() == 2
