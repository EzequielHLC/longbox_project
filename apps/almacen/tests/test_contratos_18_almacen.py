"""Contratos del stock almacenado en local (plan 18).

`CO-215`, `CO-216`, `CO-087`, `CO-151`, `CO-089`, `CO-217`, `CO-218`, `CO-152`,
`CO-227`, `CO-153`, `CO-154`, y la opción 2 de `CO-095` que ahora se completa.
"""

from datetime import timedelta
from decimal import Decimal
from io import StringIO

import pytest
from django.contrib.contenttypes.models import ContentType
from django.urls import reverse
from django.utils import timezone

from apps.accounts.tests.factories import UsuarioFactory
from apps.almacen import servicios
from apps.almacen.models import ArticuloRetenido, SolicitudDespacho
from apps.almacen.tests.util import retenido, solicitud_de
from apps.catalog.models import Producto
from apps.catalog.tests.factories import ProductoFactory
from apps.core.models import RegistroAuditoria
from apps.pedidos import demora, preventa
from apps.pedidos.models import LineaPedido, Pedido, TransaccionPago
from apps.pedidos.tests.util import demorar
from apps.puntos.models import LotePuntos
from apps.tienda.models import CobroEnCurso
from apps.tienda.tests.compra_util import (
    DIRECCION_PERFIL,
    OTRA_DIRECCION,
    avisar,
    cliente_con_direccion,
    fijar_parametros,
)

URL_STOCK = reverse("cuenta:stock")
URL_DESPACHO = reverse("cuenta:despacho")
URL_LISTA = reverse("almacen:lista")


def _acciones(accion):
    return RegistroAuditoria.objects.filter(accion=accion)


@pytest.fixture
def titular(db):
    fijar_parametros()
    return cliente_con_direccion(first_name="Ana", last_name="Lectora")


@pytest.fixture
def navegador(client, titular):
    client.force_login(titular)
    return client


def _pedir(navegador, *articulos):
    return navegador.post(
        URL_DESPACHO, {"accion": "seleccionar", "articulo": [a.pk for a in articulos]}
    )


# ---------------------------------------------------------------------------
# CO-095 opción 2: el artículo diferido queda retenido cuando llega
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_CO095_el_articulo_diferido_queda_retenido_uno_por_unidad(
    administrador, titular, mailoutbox, django_capture_on_commit_callbacks
):
    fijar_parametros(plazo_retencion_meses=3)
    producto, pedido, linea = demorar(titular)
    LineaPedido.objects.filter(pk=linea.pk).update(cantidad=2)
    demora.confirmar_opcion(pedido, linea.pk, titular, LineaPedido.DESPACHO_DIFERIDO)

    with django_capture_on_commit_callbacks(execute=True):
        preventa.confirmar_ingreso({producto.pk: 2}, administrador, origen="http://testserver")

    articulos = list(ArticuloRetenido.objects.filter(linea_pedido=linea))
    hoy = timezone.localdate()
    assert len(articulos) == 2
    for articulo in articulos:
        assert articulo.usuario == titular
        assert articulo.estado == ArticuloRetenido.DISPONIBLE
        assert articulo.valor == linea.precio_unitario
        assert articulo.fecha_ingreso == hoy
        assert articulo.fecha_vencimiento == servicios.vencimiento_desde(hoy, 3)
    linea.refresh_from_db()
    assert linea.estado == LineaPedido.DISPONIBLE  # B-18-003
    assert _acciones(RegistroAuditoria.INGRESO_STOCK_ALMACENADO).get().actor == administrador
    assert reverse("cuenta:stock") in mailoutbox[-1].body


@pytest.mark.django_db
def test_CO095_el_pedido_muestra_el_articulo_en_el_local_y_deja_de_contar_como_demorado(
    administrador, titular, navegador
):
    from django.test import Client

    client_admin = Client()
    client_admin.force_login(administrador)
    producto, pedido, linea = demorar(titular)
    demora.confirmar_opcion(pedido, linea.pk, titular, LineaPedido.DESPACHO_DIFERIDO)
    preventa.confirmar_ingreso({producto.pk: 1}, administrador)

    detalle = navegador.get(reverse("cuenta:pedido", args=[pedido.numero]))
    listado = client_admin.get(reverse("pedidos:lista") + "?demorados=1")

    assert "En el local a tu nombre" in detalle.content.decode()
    assert pedido not in listado.context["pedidos"]


# ---------------------------------------------------------------------------
# CO-215 consultarStockAlmacenadoPropio
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_CO215_lista_lo_propio_con_lo_proximo_a_vencer_y_lo_pendiente_en_solo_lectura(
    navegador, titular
):
    fijar_parametros(dias_aviso_retencion=7)
    lejos = retenido(titular, vence_en=60)
    cerca = retenido(titular, vence_en=5)
    pendiente = retenido(titular, estado=ArticuloRetenido.PENDIENTE_DESPACHO)
    retenido(titular, estado=ArticuloRetenido.RETIRADO)
    retenido(UsuarioFactory(rol="cliente"))
    registros = RegistroAuditoria.objects.count()

    respuesta = navegador.get(URL_STOCK)

    articulos = {a.pk: a for a in respuesta.context["articulos"]}
    assert set(articulos) == {lejos.pk, cerca.pk, pendiente.pk}
    assert articulos[cerca.pk].proximo and not articulos[lejos.pk].proximo
    contenido = respuesta.content.decode()
    assert f'value="{lejos.pk}"' in contenido
    assert f'value="{pendiente.pk}"' not in contenido  # A3
    assert "Próximo a vencer" in contenido
    assert RegistroAuditoria.objects.count() == registros


@pytest.mark.django_db
def test_CO215_A1_sin_articulos_lo_dice(navegador):
    respuesta = navegador.get(URL_STOCK)

    assert "No tenés artículos guardados" in respuesta.content.decode()


# ---------------------------------------------------------------------------
# CO-216 solicitarDespachoDeStockAlmacenado · CO-087 declararDireccionDeEnvio
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_CO216_resume_valor_costo_y_direccion_sin_registrar_nada(navegador, titular):
    uno = retenido(titular, valor="10000")
    otro = retenido(titular, valor="5000")

    _pedir(navegador, uno, otro)
    respuesta = navegador.get(URL_DESPACHO)

    resumen = respuesta.context["resumen"]
    assert resumen.valor == Decimal("15000")
    assert resumen.costo_envio == Decimal("1500")  # menos que el mínimo de 50.000
    assert resumen.envio["direccion"] == DIRECCION_PERFIL["direccion"]
    assert ArticuloRetenido.objects.filter(estado=ArticuloRetenido.DISPONIBLE).count() == 2
    assert not SolicitudDespacho.objects.exists()


@pytest.mark.django_db
def test_CO216_desde_el_monto_minimo_el_envio_es_gratis(navegador, titular):
    articulo = retenido(titular, valor="50000")  # B-18-007: desde, no «supera»

    _pedir(navegador, articulo)
    respuesta = navegador.get(URL_DESPACHO)

    assert respuesta.context["resumen"].gratis


@pytest.mark.django_db
def test_CO216_no_se_puede_pedir_lo_de_otro_ni_lo_que_no_esta_disponible(navegador, titular):
    ajeno = retenido(UsuarioFactory(rol="cliente"))
    pendiente = retenido(titular, estado=ArticuloRetenido.PENDIENTE_DESPACHO)

    for articulo in (ajeno, pendiente):
        _pedir(navegador, articulo)
        respuesta = navegador.get(URL_DESPACHO, follow=True)
        assert respuesta.redirect_chain[-1][0] == URL_STOCK


@pytest.mark.django_db
def test_CO087_la_direccion_del_envio_no_toca_el_perfil(navegador, titular):
    articulo = retenido(titular, valor="60000")
    _pedir(navegador, articulo)

    navegador.post(URL_DESPACHO, {"accion": "direccion", **OTRA_DIRECCION})
    navegador.post(URL_DESPACHO, {"accion": "confirmar"})

    titular.refresh_from_db()
    solicitud = SolicitudDespacho.objects.get()
    assert solicitud.envio_localidad == "Posadas"
    assert titular.localidad == DIRECCION_PERFIL["localidad"]


@pytest.mark.django_db
def test_CO151_E1_sin_direccion_no_se_confirma(client):
    fijar_parametros()
    sin_direccion = UsuarioFactory(rol="cliente")
    client.force_login(sin_direccion)
    articulo = retenido(sin_direccion, valor="60000")
    _pedir(client, articulo)

    pantalla = client.get(URL_DESPACHO)
    client.post(URL_DESPACHO, {"accion": "confirmar"})

    articulo.refresh_from_db()
    assert pantalla.context["editar_direccion"]
    assert articulo.estado == ArticuloRetenido.DISPONIBLE
    assert not SolicitudDespacho.objects.exists()


# ---------------------------------------------------------------------------
# CO-151 confirmarDespachoDeStockAlmacenado · CO-089 registrarResultadoDePago
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_CO151_gratis_genera_la_solicitud_y_avisa_al_administrador(
    navegador, titular, administrador, mailoutbox, django_capture_on_commit_callbacks
):
    uno = retenido(titular, valor="30000")
    otro = retenido(titular, valor="30000")
    _pedir(navegador, uno, otro)

    with django_capture_on_commit_callbacks(execute=True):
        respuesta = navegador.post(URL_DESPACHO, {"accion": "confirmar"})

    solicitud = SolicitudDespacho.objects.get()
    assert respuesta.url == URL_STOCK
    assert solicitud.costo_envio == 0
    assert solicitud.envio_direccion == DIRECCION_PERFIL["direccion"]
    assert set(solicitud.articulos.values_list("estado", flat=True)) == {
        ArticuloRetenido.PENDIENTE_DESPACHO
    }
    assert not TransaccionPago.objects.exists()
    assert _acciones(RegistroAuditoria.SOLICITUD_DESPACHO).get().actor == titular
    assert mailoutbox[-1].to == [administrador.email]
    assert solicitud.numero in mailoutbox[-1].subject


@pytest.mark.django_db
def test_CO151_A1_pago_aprobado_genera_la_solicitud_con_su_transaccion(navegador, titular):
    articulo = retenido(titular, valor="10000")
    _pedir(navegador, articulo)

    pasarela = navegador.post(URL_DESPACHO, {"accion": "confirmar"})
    cobro = CobroEnCurso.objects.get()
    articulo.refresh_from_db()
    pendiente_mientras_paga = articulo.estado
    avisar(navegador, cobro)
    resultado = navegador.get(reverse("compra:resultado", args=[cobro.referencia]))

    articulo.refresh_from_db()
    cobro.refresh_from_db()
    transaccion = TransaccionPago.objects.get()
    assert pasarela.url == reverse("compra:pasarela_prueba", args=[cobro.referencia])
    assert (cobro.tipo, cobro.monto) == (CobroEnCurso.DESPACHO, Decimal("1500"))
    assert pendiente_mientras_paga == ArticuloRetenido.DISPONIBLE
    assert articulo.estado == ArticuloRetenido.PENDIENTE_DESPACHO
    assert (transaccion.solicitud, transaccion.pedido) == (articulo.solicitud, None)
    assert (transaccion.monto, transaccion.estado) == (Decimal("1500"), TransaccionPago.APROBADO)
    assert resultado.url == URL_STOCK


@pytest.mark.django_db
def test_CO151_A1_pago_rechazado_no_genera_nada(navegador, titular):
    articulo = retenido(titular, valor="10000")
    _pedir(navegador, articulo)
    navegador.post(URL_DESPACHO, {"accion": "confirmar"})
    cobro = CobroEnCurso.objects.get()

    avisar(navegador, cobro, aprobado=False, mensaje="Fondos insuficientes.")
    resultado = navegador.get(reverse("compra:resultado", args=[cobro.referencia]))

    articulo.refresh_from_db()
    assert articulo.estado == ArticuloRetenido.DISPONIBLE
    assert not SolicitudDespacho.objects.exists()
    assert resultado.url == URL_DESPACHO


@pytest.mark.django_db
def test_CO089_E3_si_el_articulo_vencio_mientras_pagaba_se_reembolsa(
    navegador, titular, mailoutbox, django_capture_on_commit_callbacks
):
    articulo = retenido(titular, valor="10000")
    _pedir(navegador, articulo)
    navegador.post(URL_DESPACHO, {"accion": "confirmar"})
    cobro = CobroEnCurso.objects.get()
    ArticuloRetenido.objects.filter(pk=articulo.pk).update(estado=ArticuloRetenido.VENCIDO)

    avisar(navegador, cobro)

    cobro.refresh_from_db()
    assert cobro.estado == CobroEnCurso.REEMBOLSADO
    assert not SolicitudDespacho.objects.exists()
    assert not TransaccionPago.objects.exists()
    assert "envío" in mailoutbox[-1].subject


@pytest.mark.django_db
def test_CO156_volver_sin_confirmar_el_envio_no_registra_nada(navegador, titular):
    articulo = retenido(titular)
    _pedir(navegador, articulo)
    navegador.get(URL_DESPACHO)

    navegador.get(URL_STOCK)

    articulo.refresh_from_db()
    assert articulo.estado == ArticuloRetenido.DISPONIBLE
    assert not SolicitudDespacho.objects.exists()


@pytest.mark.django_db
def test_CO151_el_cierre_de_caja_cuenta_el_envio_como_online(client_admin, titular):
    from apps.caja import servicios as caja

    solicitud = solicitud_de(titular, costo="1500")
    TransaccionPago.objects.create(
        solicitud=solicitud,
        medio=TransaccionPago.PASARELA,
        monto=Decimal("1500"),
        estado=TransaccionPago.APROBADO,
        referencia="envio-1",
    )

    resumen = caja.resumen_previo()

    assert resumen.total_online == Decimal("1500")
    assert resumen.total_presencial == 0


# ---------------------------------------------------------------------------
# CO-217 consultarStockAlmacenado · CO-218 consultarFichaDeArticuloRetenido
# ---------------------------------------------------------------------------


@pytest.mark.django_db
@pytest.mark.parametrize("rol", ["administrador", "cajero"])
def test_CO217_lista_todos_los_clientes_con_filtros(client, request, titular, rol):
    otro = UsuarioFactory(rol="cliente", first_name="Beto")
    del_titular = retenido(titular, vence_en=3, producto=ProductoFactory(titulo="Akira"))
    del_otro = retenido(otro, vence_en=40, estado=ArticuloRetenido.PENDIENTE_DESPACHO)
    client.force_login(request.getfixturevalue(rol))

    todos = client.get(URL_LISTA)
    por_cliente = client.get(URL_LISTA, {"cliente": titular.codigo_cliente})
    por_producto = client.get(URL_LISTA, {"producto": "akira"})
    por_estado = client.get(URL_LISTA, {"estado": ArticuloRetenido.PENDIENTE_DESPACHO})
    hasta = (timezone.localdate() + timedelta(days=10)).isoformat()
    por_fecha = client.get(URL_LISTA, {"hasta": hasta})
    vacio = client.get(URL_LISTA, {"cliente": "nadie@nada"})

    assert {a.pk for a in todos.context["articulos"]} == {del_titular.pk, del_otro.pk}
    for respuesta in (por_cliente, por_producto, por_fecha):
        assert [a.pk for a in respuesta.context["articulos"]] == [del_titular.pk]
    assert [a.pk for a in por_estado.context["articulos"]] == [del_otro.pk]
    assert todos.context["articulos"][0].proximo
    assert "Ningún artículo coincide" in vacio.content.decode()  # A1


@pytest.mark.django_db
def test_CO218_la_ficha_muestra_origen_fechas_valor_e_historial(
    client_admin, administrador, titular
):
    producto, pedido, linea = demorar(titular)
    demora.confirmar_opcion(pedido, linea.pk, titular, LineaPedido.DESPACHO_DIFERIDO)
    preventa.confirmar_ingreso({producto.pk: 1}, administrador)
    articulo = ArticuloRetenido.objects.get()
    nueva = timezone.localdate() + timedelta(days=200)
    servicios.modificar_plazo(articulo.pk, administrador, nueva, "Viaja por trabajo")

    respuesta = client_admin.get(reverse("almacen:ficha", args=[articulo.pk]))

    contenido = respuesta.content.decode()
    assert f"Pedido {pedido.numero}" in contenido
    assert nueva.strftime("%d/%m/%Y") in contenido
    assert "Viaja por trabajo" in contenido
    assert reverse("almacen:retiro", args=[articulo.pk]) in contenido
    assert reverse("almacen:plazo", args=[articulo.pk]) in contenido


@pytest.mark.django_db
def test_CO218_el_cajero_no_ve_la_accion_del_plazo(client, cajero, titular):
    articulo = retenido(titular)
    client.force_login(cajero)

    respuesta = client.get(reverse("almacen:ficha", args=[articulo.pk]))

    assert reverse("almacen:plazo", args=[articulo.pk]) not in respuesta.content.decode()


# ---------------------------------------------------------------------------
# CO-152 confirmarDespachoFisico · CO-227 confirmarRetiroEnLocal
# ---------------------------------------------------------------------------


@pytest.mark.django_db
@pytest.mark.parametrize("rol", ["administrador", "cajero"])
def test_CO152_despachar_la_solicitud_registra_cada_articulo_y_avisa(
    client, request, titular, rol, mailoutbox, django_capture_on_commit_callbacks
):
    solicitud = solicitud_de(titular)
    uno = retenido(titular, estado=ArticuloRetenido.PENDIENTE_DESPACHO, solicitud=solicitud)
    otro = retenido(titular, estado=ArticuloRetenido.PENDIENTE_DESPACHO, solicitud=solicitud)
    actor = request.getfixturevalue(rol)
    client.force_login(actor)
    url = reverse("almacen:solicitud", args=[solicitud.pk])

    with django_capture_on_commit_callbacks(execute=True):
        client.post(url, {"articulo": [uno.pk, otro.pk]})

    uno.refresh_from_db()
    otro.refresh_from_db()
    assert (uno.estado, otro.estado) == (ArticuloRetenido.DESPACHADO, ArticuloRetenido.DESPACHADO)
    entradas = _acciones(RegistroAuditoria.DESPACHO_STOCK_ALMACENADO)
    assert entradas.count() == 2
    assert {e.actor for e in entradas} == {actor}
    assert mailoutbox[-1].to == [titular.email]


@pytest.mark.django_db
def test_CO152_E1_si_un_articulo_cambio_no_se_registra_nada(client_admin, titular):
    solicitud = solicitud_de(titular)
    uno = retenido(titular, estado=ArticuloRetenido.PENDIENTE_DESPACHO, solicitud=solicitud)
    otro = retenido(titular, estado=ArticuloRetenido.PENDIENTE_DESPACHO, solicitud=solicitud)
    ArticuloRetenido.objects.filter(pk=otro.pk).update(estado=ArticuloRetenido.DESPACHADO)

    respuesta = client_admin.post(
        reverse("almacen:solicitud", args=[solicitud.pk]),
        {"articulo": [uno.pk, otro.pk]},
        follow=True,
    )

    uno.refresh_from_db()
    assert uno.estado == ArticuloRetenido.PENDIENTE_DESPACHO
    assert "no se registró nada" in respuesta.content.decode()
    assert not _acciones(RegistroAuditoria.DESPACHO_STOCK_ALMACENADO).exists()


@pytest.mark.django_db
@pytest.mark.parametrize("rol", ["administrador", "cajero"])
def test_CO227_el_retiro_registra_al_titular_sin_avisarle(
    client, request, titular, rol, mailoutbox, django_capture_on_commit_callbacks
):
    articulo = retenido(titular)
    client.force_login(request.getfixturevalue(rol))
    url = reverse("almacen:retiro", args=[articulo.pk])

    verificacion = client.get(url)
    with django_capture_on_commit_callbacks(execute=True):
        client.post(url)

    articulo.refresh_from_db()
    assert titular.codigo_cliente in verificacion.content.decode()
    assert articulo.estado == ArticuloRetenido.RETIRADO
    entrada = _acciones(RegistroAuditoria.RETIRO_EN_LOCAL).get()
    assert "Lectora" in entrada.detalle
    assert mailoutbox == []


@pytest.mark.django_db
def test_CO227_E1_lo_pendiente_de_despacho_no_se_retira(client_admin, titular):
    articulo = retenido(titular, estado=ArticuloRetenido.PENDIENTE_DESPACHO)

    client_admin.post(reverse("almacen:retiro", args=[articulo.pk]))

    articulo.refresh_from_db()
    assert articulo.estado == ArticuloRetenido.PENDIENTE_DESPACHO
    assert not _acciones(RegistroAuditoria.RETIRO_EN_LOCAL).exists()


# ---------------------------------------------------------------------------
# CO-153 modificarPlazoDeRetencion
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_CO153_cambia_la_fecha_con_motivo_y_avisa_al_cliente(
    client_admin, administrador, titular, mailoutbox, django_capture_on_commit_callbacks
):
    articulo = retenido(titular, vence_en=10)
    anterior = articulo.fecha_vencimiento
    nueva = timezone.localdate() + timedelta(days=5)  # también se puede acortar

    with django_capture_on_commit_callbacks(execute=True):
        respuesta = client_admin.post(
            reverse("almacen:plazo", args=[articulo.pk]),
            {"fecha": nueva.isoformat(), "motivo": "Pidió más tiempo"},
        )

    articulo.refresh_from_db()
    assert respuesta.url == reverse("almacen:ficha", args=[articulo.pk])
    assert articulo.fecha_vencimiento == nueva
    entrada = _acciones(RegistroAuditoria.PLAZO_RETENCION).get()
    assert entrada.actor == administrador
    assert anterior.strftime("%d/%m/%Y") in entrada.detalle
    assert nueva.strftime("%d/%m/%Y") in entrada.detalle
    assert "Pidió más tiempo" in entrada.detalle
    assert entrada.objetivo_tipo == ContentType.objects.get_for_model(ArticuloRetenido)
    assert mailoutbox[-1].to == [titular.email]


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("dias", "motivo", "error"),
    [(0, "Motivo", "posterior a hoy"), (-3, "Motivo", "posterior a hoy"), (5, "  ", "obligatorio")],
)
def test_CO153_E1_E2_fecha_no_futura_o_motivo_vacio_se_rechazan(
    client_admin, titular, dias, motivo, error
):
    articulo = retenido(titular, vence_en=10)
    anterior = articulo.fecha_vencimiento
    fecha = (timezone.localdate() + timedelta(days=dias)).isoformat()

    respuesta = client_admin.post(
        reverse("almacen:plazo", args=[articulo.pk]), {"fecha": fecha, "motivo": motivo}
    )

    articulo.refresh_from_db()
    assert articulo.fecha_vencimiento == anterior
    assert error in respuesta.content.decode()
    assert not _acciones(RegistroAuditoria.PLAZO_RETENCION).exists()


@pytest.mark.django_db
def test_CO153_un_articulo_en_estado_final_no_tiene_plazo(administrador, titular):
    articulo = retenido(titular, estado=ArticuloRetenido.RETIRADO)

    with pytest.raises(servicios.OperacionRechazada):
        servicios.modificar_plazo(
            articulo.pk, administrador, timezone.localdate() + timedelta(days=9), "Motivo"
        )


# ---------------------------------------------------------------------------
# CO-154 ejecutarCicloDeVencimientoDeRetencion
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_CO154_avisa_una_vez_por_fecha_lo_que_vence_en_los_dias_de_aviso(
    titular, mailoutbox, administrador, django_capture_on_commit_callbacks
):
    fijar_parametros(dias_aviso_retencion=7)
    dentro = retenido(titular, vence_en=6)  # B-18-006: «o menos»
    fuera = retenido(titular, vence_en=8)
    pendiente = retenido(titular, vence_en=5, estado=ArticuloRetenido.PENDIENTE_DESPACHO)
    antes = list(ArticuloRetenido.objects.values_list("pk", "estado", "fecha_vencimiento"))

    with django_capture_on_commit_callbacks(execute=True):
        primera = servicios.ciclo_de_vencimiento()
        segunda = servicios.ciclo_de_vencimiento()

    assert primera.avisados == [dentro]  # E1: lo pendiente no se avisa
    assert segunda.avisados == []
    assert list(ArticuloRetenido.objects.values_list("pk", "estado", "fecha_vencimiento")) == antes
    assert len(mailoutbox) == 1
    assert dentro.fecha_vencimiento.strftime("%d/%m/%Y") in mailoutbox[0].subject
    del fuera, pendiente

    nueva = timezone.localdate() + timedelta(days=4)
    servicios.modificar_plazo(dentro.pk, administrador, nueva, "Ajuste")
    tercera = servicios.ciclo_de_vencimiento()
    assert [a.pk for a in tercera.avisados] == [dentro.pk]


@pytest.mark.django_db
def test_CO154_lo_vencido_disponible_vuelve_al_stock_con_su_valor_en_puntos(
    titular, mailoutbox, django_capture_on_commit_callbacks
):
    producto = ProductoFactory(stock=0, estado=Producto.AGOTADO)
    articulo = retenido(titular, vence_en=0, producto=producto)

    with django_capture_on_commit_callbacks(execute=True):
        resumen = servicios.ciclo_de_vencimiento()
        repetido = servicios.ciclo_de_vencimiento()

    articulo.refresh_from_db()
    producto.refresh_from_db()
    assert resumen.reintegrados == [articulo]
    assert repetido.reintegrados == []
    assert articulo.estado == ArticuloRetenido.VENCIDO
    assert (producto.stock, producto.estado) == (1, Producto.ACTIVO)
    # Plan 00, C2: todas las procedencias vuelven con su valor (antes, sin reembolso).
    assert LotePuntos.objects.get(origen=LotePuntos.REEMBOLSO).cantidad_acreditada == 1000
    entrada = _acciones(RegistroAuditoria.VENCIMIENTO_RETENCION).get()
    assert titular.email in entrada.detalle and str(producto) in entrada.detalle
    assert mailoutbox[-1].to == [titular.email]


@pytest.mark.django_db
def test_CO154_A1_lo_vencido_con_envio_pendiente_se_extiende_tres_dias_cada_vez(
    titular, administrador, mailoutbox
):
    producto = ProductoFactory(stock=0)
    articulo = retenido(
        titular, vence_en=0, producto=producto, estado=ArticuloRetenido.PENDIENTE_DESPACHO
    )
    vence = articulo.fecha_vencimiento

    resumen = servicios.ciclo_de_vencimiento()
    articulo.refresh_from_db()
    primera = articulo.fecha_vencimiento
    with pytest.MonkeyPatch.context() as parche:
        parche.setattr(timezone, "localdate", lambda *a: vence + timedelta(days=3))
        servicios.ciclo_de_vencimiento()

    articulo.refresh_from_db()
    producto.refresh_from_db()
    assert resumen.extendidos == [articulo]
    assert primera == vence + timedelta(days=3)
    assert articulo.fecha_vencimiento == vence + timedelta(days=6)  # B-18-005
    assert articulo.estado == ArticuloRetenido.PENDIENTE_DESPACHO
    assert producto.stock == 0
    assert any(administrador.email in m.to for m in mailoutbox)
    assert _acciones(RegistroAuditoria.VENCIMIENTO_RETENCION).count() == 2


@pytest.mark.django_db
def test_CO154_E2_sin_articulos_elegibles_no_hace_nada(titular, mailoutbox):
    retenido(titular, vence_en=90)
    registros = RegistroAuditoria.objects.count()

    resumen = servicios.ciclo_de_vencimiento()

    assert (resumen.avisados, resumen.reintegrados, resumen.extendidos) == ([], [], [])
    assert mailoutbox == []
    assert RegistroAuditoria.objects.count() == registros


@pytest.mark.django_db
def test_CO154_el_temporizador_corre_el_ciclo(titular):
    from django.core.management import call_command

    salida = StringIO()
    call_command("ejecutar_temporizador", stdout=salida)

    assert "stock en local:" in salida.getvalue()
    assert "restock:" in salida.getvalue()


@pytest.mark.django_db
def test_CO154_en_estado_final_no_se_toca(titular):
    articulo = retenido(titular, vence_en=-5, estado=ArticuloRetenido.RETIRADO)
    del articulo

    resumen = servicios.ciclo_de_vencimiento()

    assert resumen.reintegrados == [] and resumen.extendidos == []
    assert not Pedido.objects.exists()
