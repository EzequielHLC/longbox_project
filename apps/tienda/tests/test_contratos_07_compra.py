"""Pruebas de contrato de la compra con cuenta (`CU-TDA-CMP`, plan 07 sexta parte).

`CO-179` procederAlPago, `CO-180` iniciarCheckout, `CO-087` declararDireccionDeEnvio,
`CO-103`/`CO-104`/`CO-190` del canje, `CO-088` confirmarPedido y `CO-089`
registrarResultadoDePago. Todas por la dirección real, como las usa el Cliente
o como avisa la pasarela.

Postcondiciones negativas que se miran: nada antes del pago cambia el dominio;
`CO-087` no toca el perfil; el canje no toca ningún lote; un rechazo o un fallo
no deja nada.
"""

from decimal import Decimal

import pytest
from django.core import mail
from django.test import Client
from django.urls import reverse

from apps.catalog.models import Producto
from apps.core.models import RegistroAuditoria
from apps.pedidos.models import LineaPedido, Pedido, TransaccionPago
from apps.puntos import servicios as puntos
from apps.puntos.models import LotePuntos, MovimientoPuntos
from apps.tienda import compra
from apps.tienda.models import CobroEnCurso, LineaCarrito
from apps.tienda.tests.compra_util import (
    COSTO_ENVIO,
    DIRECCION_PERFIL,
    OTRA_DIRECCION,
    URL_CANJE_LISTO,
    URL_CHECKOUT,
    URL_PAGAR,
    agregar,
    avisar,
    cliente_con_direccion,
    confirmar,
    dar_puntos,
    fijar_parametros,
    producto,
)

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def parametros(db):
    return fijar_parametros()


@pytest.fixture
def comprador(db):
    return cliente_con_direccion()


@pytest.fixture
def navegador(client, comprador):
    client.force_login(comprador)
    return client


def foto(*productos):
    """Lo que nada antes del pago puede cambiar: stock, pedidos, lotes, carrito."""
    return {
        "stock": [Producto.objects.get(pk=p.pk).stock for p in productos],
        "pedidos": Pedido.objects.count(),
        "lineas_pedido": LineaPedido.objects.count(),
        "transacciones": TransaccionPago.objects.count(),
        "lotes": list(LotePuntos.objects.values_list("pk", "disponible", "estado")),
        "movimientos": MovimientoPuntos.objects.count(),
        "carrito": list(
            LineaCarrito.objects.values_list("producto_id", "cantidad", "cubierta_con_puntos")
        ),
    }


def comprar(navegador, *, aprobado=True, **kwargs):
    """Confirmar y que la pasarela avise. Devuelve el cobro, ya resuelto."""
    _, cobro = confirmar(navegador)
    avisar(navegador, cobro, aprobado=aprobado, **kwargs)
    cobro.refresh_from_db()
    return cobro


# ===========================================================================
# CO-179 · procederAlPago
# ===========================================================================


def test_CO179_con_todas_las_lineas_disponibles_transfiere_al_checkout(navegador):
    agregar(navegador, producto())

    respuesta = navegador.post(URL_PAGAR)

    assert respuesta.status_code == 302
    assert respuesta.url == URL_CHECKOUT


def test_CO179_una_linea_no_disponible_bloquea_y_vuelve_al_carrito(navegador):
    prod = producto()
    agregar(navegador, prod)
    Producto.objects.filter(pk=prod.pk).update(estado=Producto.DESCATALOGADO)

    respuesta = navegador.post(URL_PAGAR, follow=True)

    assert respuesta.redirect_chain[-1][0] == reverse("tienda:carrito")
    assert "quitá los productos no disponibles" in respuesta.content.decode()


def test_CO179_stock_insuficiente_bloquea(navegador):
    prod = producto(stock=3)
    agregar(navegador, prod, 3)
    Producto.objects.filter(pk=prod.pk).update(stock=2)

    respuesta = navegador.post(URL_PAGAR)

    assert respuesta.url == reverse("tienda:carrito")


def test_CO179_no_modifica_el_estado_del_sistema(navegador):
    prod = producto()
    agregar(navegador, prod)
    antes = foto(prod)

    navegador.post(URL_PAGAR)

    assert foto(prod) == antes


def test_CO179_el_invitado_que_elige_comprar_como_invitado_va_al_formulario(client):
    agregar(client, producto())

    respuesta = client.post(URL_PAGAR, {"modo": "invitado"})

    assert respuesta.url == reverse("compra:invitado")


def test_CO179_el_invitado_sin_elegir_va_a_iniciar_sesion_y_vuelve_al_checkout(client):
    agregar(client, producto())

    respuesta = client.post(URL_PAGAR)

    assert respuesta.url.startswith(reverse("accounts:login"))
    assert respuesta.url.endswith("next=" + URL_CHECKOUT)


# ===========================================================================
# CO-180 · iniciarCheckout
# ===========================================================================


def test_CO180_presenta_lineas_direccion_del_perfil_envio_y_subtotal(navegador):
    agregar(navegador, producto(precio="12000"), 2)

    respuesta = navegador.get(URL_CHECKOUT)

    resumen = respuesta.context["resumen"]
    assert respuesta.status_code == 200
    assert len(resumen.lineas) == 1
    assert resumen.subtotal_productos == Decimal("24000")
    assert resumen.costo_envio == COSTO_ENVIO
    assert resumen.total == Decimal("25500")
    assert resumen.envio == DIRECCION_PERFIL


def test_CO180_desde_el_monto_minimo_el_envio_es_gratis(navegador):
    agregar(navegador, producto(precio="50000"))

    resumen = navegador.get(URL_CHECKOUT).context["resumen"]

    assert resumen.costo_envio == 0
    assert resumen.total == Decimal("50000")


def test_CO180_E1_stock_perdido_por_compra_concurrente_vuelve_al_carrito(navegador):
    prod = producto(stock=1)
    agregar(navegador, prod)
    Producto.objects.filter(pk=prod.pk).update(stock=0, estado=Producto.AGOTADO)

    respuesta = navegador.get(URL_CHECKOUT, follow=True)

    assert respuesta.redirect_chain[-1][0] == reverse("tienda:carrito")
    contenido = respuesta.content.decode()
    assert f"«{prod.titulo}»" in contenido
    assert "Producto no disponible" in contenido


def test_CO180_no_modifica_el_estado_del_sistema(navegador):
    prod = producto()
    agregar(navegador, prod)
    antes = foto(prod)

    navegador.get(URL_CHECKOUT)

    assert foto(prod) == antes
    assert CobroEnCurso.objects.count() == 0


# ===========================================================================
# CO-087 · declararDireccionDeEnvio
# ===========================================================================


def test_CO087_la_direccion_del_checkout_pasa_a_la_declarada(navegador):
    agregar(navegador, producto())
    assert navegador.get(URL_CHECKOUT).context["resumen"].envio == DIRECCION_PERFIL

    navegador.post(URL_CHECKOUT, OTRA_DIRECCION)

    assert navegador.get(URL_CHECKOUT).context["resumen"].envio == OTRA_DIRECCION


def test_CO087_la_direccion_del_perfil_no_se_modifica(navegador, comprador):
    agregar(navegador, producto())

    navegador.post(URL_CHECKOUT, OTRA_DIRECCION)

    comprador.refresh_from_db()
    assert {campo: getattr(comprador, campo) for campo in DIRECCION_PERFIL} == DIRECCION_PERFIL


def test_CO087_devuelve_el_costo_de_envio(navegador):
    agregar(navegador, producto())

    respuesta = navegador.post(URL_CHECKOUT, OTRA_DIRECCION, follow=True)

    assert "Envío: $" in respuesta.content.decode()


def test_CO087_una_direccion_incoherente_no_se_declara(navegador):
    agregar(navegador, producto())

    respuesta = navegador.post(URL_CHECKOUT, {**OTRA_DIRECCION, "provincia": "Córdoba"})

    assert respuesta.status_code == 200
    assert respuesta.context["form"].errors["codigo_postal"]
    assert compra.CLAVE_ENVIO not in navegador.session


def test_CO087_sin_numero_de_calle_no_se_declara(navegador):
    agregar(navegador, producto())

    respuesta = navegador.post(URL_CHECKOUT, {**OTRA_DIRECCION, "direccion": "San Martín"})

    assert respuesta.context["form"].errors["direccion"]


# ===========================================================================
# CO-103 · aplicarCanjeDePuntosAItem · CO-104 · CO-190
# ===========================================================================


def canjear(navegador, linea, accion=None):
    datos = {"accion": accion} if accion else {}
    return navegador.post(reverse("compra:canje", args=[linea.pk]), datos)


def test_CO103_la_linea_queda_cubierta_y_el_total_baja_su_precio(navegador, comprador):
    dar_puntos(comprador, 500)
    agregar(navegador, producto(precio="3000"))
    agregar(navegador, producto(precio="8000"))
    linea = LineaCarrito.objects.get(producto__precio=Decimal("3000"))
    antes = navegador.get(URL_CHECKOUT).context["resumen"].total
    assert linea.cubierta_con_puntos is False

    canjear(navegador, linea)

    linea.refresh_from_db()
    assert linea.cubierta_con_puntos is True
    resumen = navegador.get(URL_CHECKOUT).context["resumen"]
    assert resumen.total == antes - Decimal("3000")
    assert resumen.puntos_aplicados == 300
    assert resumen.saldo_restante == 200


def test_CO103_ningun_lote_de_puntos_se_modifica_ni_se_audita(navegador, comprador):
    dar_puntos(comprador, 500)
    agregar(navegador, producto(precio="3000"))
    antes = list(LotePuntos.objects.values_list("pk", "disponible", "estado"))
    registros = RegistroAuditoria.objects.count()

    canjear(navegador, LineaCarrito.objects.get())

    assert list(LotePuntos.objects.values_list("pk", "disponible", "estado")) == antes
    assert MovimientoPuntos.objects.count() == 0
    assert RegistroAuditoria.objects.count() == registros


def test_CO103_E1_saldo_insuficiente_no_cubre_y_lo_informa(navegador, comprador):
    dar_puntos(comprador, 299)
    agregar(navegador, producto(precio="3000"))
    linea = LineaCarrito.objects.get()

    respuesta = canjear(navegador, linea)

    linea.refresh_from_db()
    assert linea.cubierta_con_puntos is False
    texto = navegador.get(respuesta.url).content.decode()
    assert "hacen falta 300 puntos y te quedan 299" in texto


def test_CO103_E1_no_hay_canje_parcial_entre_dos_lineas(navegador, comprador):
    dar_puntos(comprador, 500)
    agregar(navegador, producto(precio="3000"))
    agregar(navegador, producto(precio="2500"))
    primera, segunda = LineaCarrito.objects.order_by("pk")

    canjear(navegador, primera)
    canjear(navegador, segunda)

    segunda.refresh_from_db()
    assert segunda.cubierta_con_puntos is False


def test_CO103_E2_se_verifica_con_el_precio_de_hoy(navegador, comprador):
    dar_puntos(comprador, 300)
    prod = producto(precio="3000")
    agregar(navegador, prod)
    navegador.get(URL_CHECKOUT)
    Producto.objects.filter(pk=prod.pk).update(precio=Decimal("3010"))

    canjear(navegador, LineaCarrito.objects.get())

    assert LineaCarrito.objects.get().cubierta_con_puntos is False


def test_CO103_sin_saldo_no_hay_canje(navegador):
    agregar(navegador, producto(precio="3000"))

    canjear(navegador, LineaCarrito.objects.get())

    assert LineaCarrito.objects.get().cubierta_con_puntos is False


def test_CO103_los_puntos_requeridos_redondean_hacia_arriba(navegador, comprador):
    dar_puntos(comprador, 301)
    agregar(navegador, producto(precio="3001"))

    canjear(navegador, LineaCarrito.objects.get())

    assert navegador.get(URL_CHECKOUT).context["resumen"].puntos_aplicados == 301


def test_CO103_la_linea_de_otro_carrito_responde_404(navegador, comprador):
    dar_puntos(comprador, 500)
    ajeno = cliente_con_direccion()
    otro_navegador = Client()
    otro_navegador.force_login(ajeno)
    agregar(otro_navegador, producto())
    linea_ajena = LineaCarrito.objects.get(carrito__usuario=ajeno)
    agregar(navegador, producto())

    respuesta = canjear(navegador, linea_ajena)

    assert respuesta.status_code == 404
    linea_ajena.refresh_from_db()
    assert linea_ajena.cubierta_con_puntos is False


def test_CO104_la_linea_vuelve_a_su_precio_sin_tocar_lotes(navegador, comprador):
    dar_puntos(comprador, 500)
    agregar(navegador, producto(precio="3000"))
    linea = LineaCarrito.objects.get()
    canjear(navegador, linea)
    cubierto = navegador.get(URL_CHECKOUT).context["resumen"].total
    lotes = list(LotePuntos.objects.values_list("pk", "disponible", "estado"))

    canjear(navegador, linea, "revertir")

    linea.refresh_from_db()
    assert linea.cubierta_con_puntos is False
    assert navegador.get(URL_CHECKOUT).context["resumen"].total == cubierto + Decimal("3000")
    assert list(LotePuntos.objects.values_list("pk", "disponible", "estado")) == lotes


def test_CO190_A2_si_el_total_queda_en_cero_lo_informa_sin_cambiar_nada(navegador, comprador):
    dar_puntos(comprador, 10000)
    prod = producto(precio="60000")
    agregar(navegador, prod)
    canjear(navegador, LineaCarrito.objects.get())
    antes = foto(prod)

    respuesta = navegador.post(URL_CANJE_LISTO, follow=True)

    assert "se completa íntegramente con puntos" in respuesta.content.decode()
    assert foto(prod) == antes


# ===========================================================================
# CO-088 · confirmarPedido
# ===========================================================================


def test_CO088_con_total_mayor_que_cero_emite_la_solicitud_de_cobro_con_su_referencia(navegador):
    agregar(navegador, producto())

    respuesta, cobro = confirmar(navegador)

    assert cobro is not None
    assert len(cobro.referencia) == 32
    assert cobro.estado == CobroEnCurso.PENDIENTE
    assert cobro.monto == Decimal("11500")
    assert respuesta.url == reverse("compra:pasarela_prueba", args=[cobro.referencia])


def test_CO088_con_total_mayor_que_cero_no_cambia_el_dominio(navegador):
    prod = producto()
    agregar(navegador, prod)
    antes = foto(prod)

    confirmar(navegador)

    assert foto(prod) == antes


def test_CO088_congela_lineas_precios_direccion_y_canje(navegador, comprador):
    dar_puntos(comprador, 500)
    prod = producto(precio="3000")
    otro = producto(precio="7000")
    agregar(navegador, prod, 1)
    agregar(navegador, otro, 2)
    canjear(navegador, LineaCarrito.objects.get(producto=prod))
    navegador.post(URL_CHECKOUT, OTRA_DIRECCION)

    _, cobro = confirmar(navegador)

    assert cobro.lineas == [
        {"producto": prod.pk, "cantidad": 1, "precio": "3000.00", "puntos": 300},
        {"producto": otro.pk, "cantidad": 2, "precio": "7000.00", "puntos": 0},
    ]
    assert cobro.envio == OTRA_DIRECCION
    assert cobro.puntos_a_debitar == 300
    assert cobro.monto == Decimal("14000") + COSTO_ENVIO


def test_CO088_sin_direccion_completa_no_confirma(client):
    sin_direccion = cliente_con_direccion(direccion="", localidad="")
    client.force_login(sin_direccion)
    agregar(client, producto())

    respuesta = client.post(reverse("compra:confirmar"))

    assert respuesta.url == reverse("tienda:carrito")
    assert CobroEnCurso.objects.count() == 0


def test_CO088_A2_con_todo_cubierto_y_envio_gratis_confirma_sin_pasarela(navegador, comprador):
    dar_puntos(comprador, 6000)
    prod = producto(precio="60000")
    agregar(navegador, prod)
    canjear(navegador, LineaCarrito.objects.get())

    respuesta, cobro = confirmar(navegador)

    pedido = Pedido.objects.get()
    assert respuesta.url == reverse("compra:resultado", args=[cobro.referencia])
    assert cobro.monto == 0
    assert not TransaccionPago.objects.exists()
    assert pedido.lineas.get().cubierta_con_puntos is True
    assert puntos.saldo(comprador) == 0


def test_CO088_A2_no_ocurre_si_hay_que_pagar_el_envio(navegador, comprador):
    dar_puntos(comprador, 1000)
    agregar(navegador, producto(precio="3000"))
    canjear(navegador, LineaCarrito.objects.get())

    respuesta, cobro = confirmar(navegador)

    assert cobro.monto == COSTO_ENVIO
    assert respuesta.url == reverse("compra:pasarela_prueba", args=[cobro.referencia])
    assert not Pedido.objects.exists()


def test_CO088_un_canje_que_el_saldo_ya_no_cubre_pide_revisar(navegador, comprador):
    lote = dar_puntos(comprador, 300)
    agregar(navegador, producto(precio="3000"))
    canjear(navegador, LineaCarrito.objects.get())
    LotePuntos.objects.filter(pk=lote.pk).update(disponible=100)

    respuesta, cobro = confirmar(navegador)

    assert respuesta.url == URL_CHECKOUT
    assert cobro is None


# ===========================================================================
# CO-089 · registrarResultadoDePago — pago aprobado
# ===========================================================================


@pytest.fixture
def compra_aprobada(navegador, comprador):
    """Una compra de dos productos, uno cubierto con puntos, aprobada por la pasarela."""
    dar_puntos(comprador, 400, dias=30)
    dar_puntos(comprador, 400, dias=90)
    cubierto = producto(stock=4, precio="5000")
    pagado = producto(stock=2, precio="9000")
    agregar(navegador, cubierto, 1)
    agregar(navegador, pagado, 2)
    navegador.get(URL_CHECKOUT)
    navegador.post(reverse("compra:canje", args=[LineaCarrito.objects.get(producto=cubierto).pk]))
    cobro = comprar(navegador)
    return {"cobro": cobro, "cubierto": cubierto, "pagado": pagado}


def test_CO089_a_crea_el_pedido_con_una_linea_por_linea_del_carrito_y_la_transaccion(
    compra_aprobada,
):
    pedido = Pedido.objects.get()

    assert pedido.lineas.count() == 2
    assert TransaccionPago.objects.get().pedido == pedido


def test_CO089_b_asociaciones_del_pedido(compra_aprobada, comprador):
    pedido = Pedido.objects.get()

    assert pedido.usuario == comprador
    assert pedido.correo_invitado == ""
    assert {linea.producto_id for linea in pedido.lineas.all()} == {
        compra_aprobada["cubierto"].pk,
        compra_aprobada["pagado"].pk,
    }
    assert pedido.transaccion.pk == TransaccionPago.objects.get().pk
    assert compra_aprobada["cobro"].pedido == pedido


def test_CO089_c_numero_unico_canal_online_y_pendiente_de_armado(compra_aprobada):
    pedido = Pedido.objects.get()

    assert pedido.numero == f"{pedido.pk:06d}"
    assert pedido.canal == Pedido.ONLINE
    assert pedido.estado == Pedido.PENDIENTE_ARMADO
    assert pedido.costo_envio == COSTO_ENVIO


def test_CO089_c_la_direccion_queda_copiada_y_no_sigue_al_perfil(compra_aprobada, comprador):
    comprador.direccion = "Otra calle 999"
    comprador.save()

    pedido = Pedido.objects.get()
    assert pedido.envio_direccion == DIRECCION_PERFIL["direccion"]
    assert pedido.envio_codigo_postal == DIRECCION_PERFIL["codigo_postal"]


def test_CO089_c_el_precio_unitario_queda_congelado(compra_aprobada):
    pagado = compra_aprobada["pagado"]
    Producto.objects.filter(pk=pagado.pk).update(precio=Decimal("99999"))

    linea = LineaPedido.objects.get(producto=pagado)
    assert linea.precio_unitario == Decimal("9000")
    assert linea.estado == LineaPedido.DISPONIBLE


def test_CO089_c_la_linea_cubierta_guarda_el_valor_de_su_canje(compra_aprobada):
    cubierta = LineaPedido.objects.get(producto=compra_aprobada["cubierto"])
    pagada = LineaPedido.objects.get(producto=compra_aprobada["pagado"])

    assert (cubierta.cubierta_con_puntos, cubierta.puntos_canjeados) == (True, 500)
    assert (pagada.cubierta_con_puntos, pagada.puntos_canjeados) == (False, 0)


def test_CO089_c_la_transaccion_queda_aprobada_con_referencia_y_monto(compra_aprobada):
    cobro = compra_aprobada["cobro"]
    transaccion = TransaccionPago.objects.get()

    assert transaccion.referencia == f"prueba-{cobro.referencia}"
    assert transaccion.monto == Decimal("18000") + COSTO_ENVIO
    assert transaccion.estado == TransaccionPago.APROBADO
    assert transaccion.medio == TransaccionPago.PASARELA
    assert transaccion.incluida_en_cierre is False


def test_CO089_c_el_stock_baja_y_el_que_llega_a_cero_pasa_a_agotado(compra_aprobada):
    cubierto = Producto.objects.get(pk=compra_aprobada["cubierto"].pk)
    pagado = Producto.objects.get(pk=compra_aprobada["pagado"].pk)

    assert (cubierto.stock, cubierto.estado) == (3, Producto.ACTIVO)
    assert (pagado.stock, pagado.estado) == (0, Producto.AGOTADO)


def test_CO089_c_debita_los_lotes_de_caducidad_mas_proxima_primero(compra_aprobada):
    proximo, lejano = LotePuntos.objects.filter(origen=LotePuntos.AJUSTE_MANUAL).order_by(
        "caduca_el"
    )

    assert (proximo.disponible, proximo.estado) == (0, LotePuntos.AGOTADO)
    assert (lejano.disponible, lejano.estado) == (300, LotePuntos.ACTIVO)
    debito = MovimientoPuntos.objects.get(tipo=MovimientoPuntos.DEBITO)
    assert debito.cantidad == 500
    assert set(debito.lotes.all()) == {proximo, lejano}


def test_CO089_c_acredita_los_puntos_de_lo_pagado_en_dinero_sin_el_envio(
    compra_aprobada, comprador
):
    lote = LotePuntos.objects.get(origen=LotePuntos.COMPRA)
    acreditacion = MovimientoPuntos.objects.get(tipo=MovimientoPuntos.ACREDITACION)

    assert lote.cantidad_acreditada == 180  # 10 % de 18000 = $1800, a $10 el punto; sin envío
    assert lote.estado == LotePuntos.ACTIVO
    assert lote.caduca_el.year == lote.acreditado_en.year + 1
    assert acreditacion.cantidad == 180
    assert acreditacion.pedido == Pedido.objects.get()
    assert puntos.saldo(comprador) == 300 + 180


def test_CO089_a_el_carrito_queda_vaciado(compra_aprobada, comprador):
    assert not LineaCarrito.objects.filter(carrito__usuario=comprador).exists()


def test_CO089_queda_registrado_en_la_auditoria_con_el_actor(compra_aprobada, comprador):
    registro = RegistroAuditoria.objects.get(accion=RegistroAuditoria.COMPRA_ONLINE)

    assert registro.actor == comprador
    assert registro.objetivo == Pedido.objects.get()
    assert "canjeó 500 pts" in registro.detalle


def test_CO089_con_pre_venta_nace_esperando_stock_y_la_linea_reservada(navegador):
    reserva = producto(stock=0, estado=Producto.PRE_VENTA)
    inmediato = producto(stock=3)
    agregar(navegador, reserva)
    agregar(navegador, inmediato)

    comprar(navegador)

    pedido = Pedido.objects.get()
    assert pedido.estado == Pedido.ESPERANDO_PRE_VENTA
    assert pedido.lineas.get(producto=reserva).estado == LineaPedido.RESERVADO
    assert pedido.lineas.get(producto=inmediato).estado == LineaPedido.DISPONIBLE
    assert Producto.objects.get(pk=reserva.pk).stock == 0
    assert Producto.objects.get(pk=inmediato.pk).stock == 2


def test_CO089_los_puntos_acreditados_redondean_hacia_abajo(navegador, comprador):
    agregar(navegador, producto(precio="10009"))

    comprar(navegador)

    # 10 % de $10009 = $1000,90, a $10 el punto: 100,09 → 100.
    assert LotePuntos.objects.get(origen=LotePuntos.COMPRA).cantidad_acreditada == 100


def test_CO089_envia_la_confirmacion_despues_del_commit(
    navegador, comprador, django_capture_on_commit_callbacks
):
    agregar(navegador, producto())

    with django_capture_on_commit_callbacks(execute=True):
        comprar(navegador)

    pedido = Pedido.objects.get()
    assert len(mail.outbox) == 1
    assert mail.outbox[0].to == [comprador.email]
    assert pedido.numero in mail.outbox[0].subject
    assert pedido.numero in mail.outbox[0].body


def test_CO089_un_correo_caido_no_deshace_el_pedido(
    navegador, django_capture_on_commit_callbacks, monkeypatch
):
    def caido(**kwargs):
        raise OSError("SMTP caído")

    monkeypatch.setattr(compra, "enviar_correo", caido)
    agregar(navegador, producto())

    with django_capture_on_commit_callbacks(execute=True):
        comprar(navegador)

    assert Pedido.objects.count() == 1


def test_CO089_la_pantalla_de_resultado_muestra_el_numero_y_el_estado(navegador):
    agregar(navegador, producto())
    cobro = comprar(navegador)

    respuesta = navegador.get(reverse("compra:resultado", args=[cobro.referencia]))

    contenido = respuesta.content.decode()
    assert Pedido.objects.get().numero in contenido
    assert "Pendiente de armado" in contenido


# ===========================================================================
# CO-089 — idempotencia, rechazo (E2) y fallo después del pago (E3)
# ===========================================================================


def test_CO089_un_aviso_repetido_no_genera_un_segundo_pedido(navegador):
    prod = producto(stock=5)
    agregar(navegador, prod, 2)
    cobro = comprar(navegador)
    despues_del_primero = foto(prod)

    respuesta = avisar(navegador, cobro)

    assert respuesta.status_code == 200
    assert foto(prod) == despues_del_primero
    assert Pedido.objects.count() == 1


def test_CO089_E2_un_pago_rechazado_no_modifica_nada(navegador, comprador):
    dar_puntos(comprador, 500)
    prod = producto(precio="3000")
    agregar(navegador, prod)
    canjear(navegador, LineaCarrito.objects.get())
    antes = foto(prod)

    cobro = comprar(navegador, aprobado=False, mensaje="Fondos insuficientes.")

    assert foto(prod) == antes
    assert cobro.estado == CobroEnCurso.RECHAZADO


def test_CO089_E2_el_rechazo_se_informa_con_el_mensaje_de_la_pasarela(navegador):
    agregar(navegador, producto())
    cobro = comprar(navegador, aprobado=False, mensaje="Fondos insuficientes.")

    respuesta = navegador.get(reverse("compra:resultado", args=[cobro.referencia]))

    contenido = respuesta.content.decode()
    assert "Fondos insuficientes." in contenido
    assert URL_CHECKOUT in contenido


def test_CO089_E2_el_rechazo_queda_en_la_auditoria(navegador, comprador):
    agregar(navegador, producto())

    comprar(navegador, aprobado=False, mensaje="Fondos insuficientes.")

    registro = RegistroAuditoria.objects.get(accion=RegistroAuditoria.PAGO_RECHAZADO)
    assert registro.actor == comprador
    assert "Fondos insuficientes." in registro.detalle


def test_CO089_E3_stock_perdido_mientras_se_pagaba_no_deja_nada_y_reembolsa(
    navegador, comprador, monkeypatch
):
    reembolsos = []
    monkeypatch.setattr(
        "apps.tienda.pasarelas.PasarelaDePrueba.reembolsar",
        lambda self, cobro, referencia: reembolsos.append(referencia) or True,
    )
    prod = producto(stock=1)
    agregar(navegador, prod)
    _, cobro = confirmar(navegador)
    Producto.objects.filter(pk=prod.pk).update(stock=0, estado=Producto.AGOTADO)
    antes = foto(prod)

    avisar(navegador, cobro)

    cobro.refresh_from_db()
    assert foto(prod) == antes
    assert cobro.estado == CobroEnCurso.REEMBOLSADO
    assert reembolsos == [f"prueba-{cobro.referencia}"]


def test_CO089_E3_un_fallo_tecnico_a_mitad_de_camino_no_deja_datos_parciales(
    navegador, comprador, monkeypatch
):
    def falla(*args, **kwargs):
        raise RuntimeError("la base se cayó")

    monkeypatch.setattr(puntos, "acreditar", falla)
    prod = producto(stock=3)
    agregar(navegador, prod, 2)
    antes = foto(prod)

    cobro = comprar(navegador)

    assert foto(prod) == antes
    assert not CobroEnCurso.objects.filter(pk=cobro.pk, pedido__isnull=False).exists()
    registro = RegistroAuditoria.objects.get(accion=RegistroAuditoria.INCIDENTE_COMPRA)
    assert "Se inició el reembolso." in registro.detalle


def test_CO089_E3_avisa_al_cliente_que_el_cargo_se_revierte(navegador, comprador):
    prod = producto(stock=1)
    agregar(navegador, prod)
    _, cobro = confirmar(navegador)
    Producto.objects.filter(pk=prod.pk).update(stock=0)

    avisar(navegador, cobro)

    assert mail.outbox[-1].to == [comprador.email]
    assert "revierte" in mail.outbox[-1].subject
    respuesta = navegador.get(reverse("compra:resultado", args=[cobro.referencia]))
    assert "El cargo se revierte" in respuesta.content.decode()


def test_CO089_E3_el_saldo_que_ya_no_alcanza_tambien_reembolsa(navegador, comprador):
    lote = dar_puntos(comprador, 300)
    prod = producto(precio="3000")
    agregar(navegador, prod)
    canjear(navegador, LineaCarrito.objects.get())
    _, cobro = confirmar(navegador)
    LotePuntos.objects.filter(pk=lote.pk).update(disponible=100)

    avisar(navegador, cobro)

    cobro.refresh_from_db()
    assert cobro.estado == CobroEnCurso.REEMBOLSADO
    assert not Pedido.objects.exists()
    assert LotePuntos.objects.get(pk=lote.pk).disponible == 100


def test_CO089_un_monto_distinto_del_cobrado_no_genera_pedido(navegador):
    agregar(navegador, producto())
    _, cobro = confirmar(navegador)

    avisar(navegador, cobro, monto="1.00")

    cobro.refresh_from_db()
    assert not Pedido.objects.exists()
    assert cobro.estado == CobroEnCurso.REEMBOLSADO


def test_CO089_otro_carrito_cambiado_despues_de_confirmar_no_entra_al_pedido(navegador):
    comprado = producto()
    agregar(navegador, comprado)
    _, cobro = confirmar(navegador)
    agregado_despues = producto()
    agregar(navegador, agregado_despues)

    avisar(navegador, cobro)

    pedido = Pedido.objects.get()
    assert [linea.producto_id for linea in pedido.lineas.all()] == [comprado.pk]
    assert list(LineaCarrito.objects.values_list("producto_id", flat=True)) == [agregado_despues.pk]
