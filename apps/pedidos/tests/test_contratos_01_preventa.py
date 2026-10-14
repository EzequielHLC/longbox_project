"""Contratos del ciclo de la pre-venta (plan 01): `CO-011` a `CO-015`, `CO-026`, `CO-027`.

Cada prueba lleva en el nombre el contrato cuyas postcondiciones verifica.
"""

from datetime import timedelta
from decimal import Decimal
from io import StringIO
from unittest import mock

import pytest
from django.core.management import call_command
from django.urls import reverse
from django.utils import timezone
from freezegun import freeze_time

from apps.catalog.models import Producto, ProductoEditorial
from apps.catalog.tests.factories import EditorialFactory
from apps.core.models import RegistroAuditoria
from apps.pedidos import preventa
from apps.pedidos.models import AvisoDePreVenta, LineaPedido, Pedido
from apps.pedidos.tests.util import crear_preventa, demorar, reservar
from apps.puntos.models import LotePuntos, MovimientoPuntos
from apps.tienda.tests.compra_util import fijar_parametros

# El valor del punto que fija `fijar_parametros`: 1 punto = $10.


def _foto():
    """Productos, pedidos y líneas, para verificar que algo no cambió nada."""
    return (
        list(Producto.objects.order_by("pk").values_list("pk", "estado", "stock")),
        list(Pedido.objects.order_by("pk").values_list("pk", "estado")),
        list(LineaPedido.objects.order_by("pk").values_list("pk", "estado", "decision_demora")),
    )


def _acciones(accion):
    return RegistroAuditoria.objects.filter(accion=accion)


# ---------------------------------------------------------------------------
# CO-011 ejecutarCicloVigilanciaPreventa
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_CO011_avisa_las_proximas_y_las_de_hoy_sin_cambiar_nada(administrador, cliente, mailoutbox):
    fijar_parametros(dias_aviso_preventa=2)
    proxima = crear_preventa(dias=2, titulo="Akira")
    de_hoy = crear_preventa(dias=0, titulo="Berserk")
    reservar(cliente, proxima)
    antes = _foto()

    resumen = preventa.ciclo_de_vigilancia()

    assert [f.producto for f in resumen.proximas] == [proxima]
    assert [f.producto for f in resumen.de_hoy] == [de_hoy]
    assert _foto() == antes
    assert len(mailoutbox) == 1
    correo = mailoutbox[0]
    assert correo.to == [administrador.email]
    assert "Akira" in correo.body and "Berserk" in correo.body
    assert "1 pedido(s)" in correo.body


@pytest.mark.django_db
def test_CO011_correr_dos_veces_el_mismo_dia_no_repite_avisos(administrador, mailoutbox):
    fijar_parametros(dias_aviso_preventa=2)
    crear_preventa(dias=1)

    preventa.ciclo_de_vigilancia()
    segunda = preventa.ciclo_de_vigilancia()

    assert not segunda.proximas
    assert len(mailoutbox) == 1
    assert AvisoDePreVenta.objects.count() == 1


@pytest.mark.django_db
def test_CO011_fuera_del_horizonte_o_sin_preventas_no_avisa(administrador, mailoutbox):
    fijar_parametros(dias_aviso_preventa=2)
    crear_preventa(dias=3)

    resumen = preventa.ciclo_de_vigilancia()

    assert (resumen.proximas, resumen.de_hoy, resumen.escaladas) == ([], [], [])
    assert mailoutbox == []


@pytest.mark.django_db
def test_CO011_una_demorada_cuya_fecha_estimada_paso_se_recuerda_una_vez(administrador, mailoutbox):
    producto = crear_preventa(dias=3)
    preventa.registrar_demora(producto, administrador, fecha_estimada=producto.fecha_llegada)

    with freeze_time(timezone.now() + timedelta(days=5)):
        primera = preventa.ciclo_de_vigilancia()
        segunda = preventa.ciclo_de_vigilancia()

    assert [f.producto for f in primera.de_hoy] == [producto]
    assert not primera.escaladas
    assert not segunda.de_hoy


@pytest.mark.django_db
def test_CO011_el_temporizador_corre_los_ciclos_de_la_preventa_y_la_demora(administrador):
    salida = StringIO()

    call_command("ejecutar_temporizador", stdout=salida)

    texto = salida.getvalue()
    assert "pre-venta:" in texto
    assert "ventanas de decision:" in texto
    assert "compensacion por demora:" in texto


# ---------------------------------------------------------------------------
# CO-012 ejecutarCicloEscaladoPorInaccion
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_CO012_escala_lo_vencido_sin_ingreso_ni_demora_y_lo_audita(
    administrador, cliente, mailoutbox
):
    vencida = crear_preventa(dias=-1, titulo="Vagabond")
    reservar(cliente, vencida)
    antes = _foto()

    resumen = preventa.ciclo_de_vigilancia()

    assert [f.producto for f in resumen.escaladas] == [vencida]
    assert _foto() == antes
    entrada = _acciones(RegistroAuditoria.ESCALADO_PREVENTA).get()
    assert entrada.actor is None
    assert "Vagabond" in entrada.detalle
    assert any("sin resolver" in m.subject.lower() for m in mailoutbox)


@pytest.mark.django_db
def test_CO012_escala_una_vez_por_dia_mientras_siga_sin_resolver(administrador):
    crear_preventa(dias=-1)

    preventa.ciclo_de_vigilancia()
    preventa.ciclo_de_vigilancia()
    with freeze_time(timezone.now() + timedelta(days=1)):
        preventa.ciclo_de_vigilancia()

    assert _acciones(RegistroAuditoria.ESCALADO_PREVENTA).count() == 2


@pytest.mark.django_db
def test_CO012_no_escala_lo_que_tiene_demora_registrada(administrador):
    producto = crear_preventa(dias=1)
    preventa.registrar_demora(producto, administrador)

    with freeze_time(timezone.now() + timedelta(days=3)):
        resumen = preventa.ciclo_de_vigilancia()

    assert not resumen.escaladas
    assert not _acciones(RegistroAuditoria.ESCALADO_PREVENTA).exists()


# ---------------------------------------------------------------------------
# CO-013 confirmarIngresoDeLote
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_CO013_confirmar_ingreso_activa_productos_y_pasa_pedidos_a_pendiente_de_armado(
    administrador, cliente, mailoutbox, django_capture_on_commit_callbacks
):
    producto = crear_preventa(dias=0)
    pedido, linea = reservar(cliente, producto, cantidad=2)

    with django_capture_on_commit_callbacks(execute=True):
        resumen = preventa.confirmar_ingreso({producto.pk: 10}, administrador)

    producto.refresh_from_db()
    pedido.refresh_from_db()
    linea.refresh_from_db()
    assert resumen.activados == [producto]
    assert (producto.estado, producto.stock) == (Producto.ACTIVO, 8)
    assert linea.estado == LineaPedido.DISPONIBLE
    assert pedido.estado == Pedido.PENDIENTE_ARMADO
    transicion = pedido.transiciones.last()
    assert (transicion.estado_anterior, transicion.estado_nuevo, transicion.actor) == (
        Pedido.ESPERANDO_PRE_VENTA,
        Pedido.PENDIENTE_ARMADO,
        administrador,
    )
    assert _acciones(RegistroAuditoria.CONFIRMACION_INGRESO).get().actor == administrador
    assert _acciones(RegistroAuditoria.TRANSICION_PEDIDO).get().actor == administrador
    assert mailoutbox[0].to == [cliente.email]


@pytest.mark.django_db
def test_CO013_lo_recibido_cubre_las_reservas_en_orden_de_compra(administrador, cliente):
    producto = crear_preventa(dias=0)
    primero, linea_1 = reservar(cliente, producto, hace_minutos=30)
    segundo, linea_2 = reservar(cliente, producto, hace_minutos=20)
    tercero, linea_3 = reservar(cliente, producto, hace_minutos=10)

    resumen = preventa.confirmar_ingreso({producto.pk: 2}, administrador)

    for objeto in (producto, linea_1, linea_2, linea_3, primero, tercero):
        objeto.refresh_from_db()
    assert resumen.parciales == [producto]
    assert (producto.estado, producto.stock, producto.demorado) == (Producto.PRE_VENTA, 0, True)
    assert [linea_1.estado, linea_2.estado, linea_3.estado] == [
        LineaPedido.DISPONIBLE,
        LineaPedido.DISPONIBLE,
        LineaPedido.ESPERANDO_DEMORADO,
    ]
    assert (primero.estado, tercero.estado) == (Pedido.PENDIENTE_ARMADO, Pedido.ESPERANDO_DEMORADO)
    assert linea_3.fecha_llegada_original == timezone.localdate()


@pytest.mark.django_db
def test_CO013_no_saltea_una_reserva_que_no_alcanza(administrador, cliente):
    producto = crear_preventa(dias=0)
    _, grande = reservar(cliente, producto, cantidad=3, hace_minutos=20)
    _, chica = reservar(cliente, producto, cantidad=1, hace_minutos=10)

    preventa.confirmar_ingreso({producto.pk: 2}, administrador)

    for objeto in (producto, grande, chica):
        objeto.refresh_from_db()
    assert (grande.estado, chica.estado) == (
        LineaPedido.ESPERANDO_DEMORADO,
        LineaPedido.ESPERANDO_DEMORADO,
    )
    # Las dos unidades quedan en el local para la próxima llegada.
    assert (producto.estado, producto.stock) == (Producto.PRE_VENTA, 2)

    preventa.confirmar_ingreso({producto.pk: 2}, administrador)

    for objeto in (producto, grande, chica):
        objeto.refresh_from_db()
    assert (grande.estado, chica.estado) == (LineaPedido.DISPONIBLE, LineaPedido.DISPONIBLE)
    assert (producto.estado, producto.stock, producto.demorado) == (Producto.AGOTADO, 0, False)


@pytest.mark.django_db
def test_CO013_un_pedido_con_otra_preventa_sigue_esperando(administrador, cliente):
    llega = crear_preventa(dias=0)
    no_llega = crear_preventa(dias=10)
    pedido, _ = reservar(cliente, llega)
    LineaPedido.objects.create(
        pedido=pedido,
        producto=no_llega,
        cantidad=1,
        precio_unitario=no_llega.precio,
        estado=LineaPedido.RESERVADO,
    )

    preventa.confirmar_ingreso({llega.pk: 1}, administrador)

    pedido.refresh_from_db()
    assert pedido.estado == Pedido.ESPERANDO_PRE_VENTA
    assert not _acciones(RegistroAuditoria.TRANSICION_PEDIDO).exists()


@pytest.mark.django_db
def test_CO013_A1_un_faltante_vencido_se_demora_con_la_cascada_de_CO015(administrador, cliente):
    fijar_parametros(ventana_decision_horas=48)
    producto = crear_preventa(dias=0)
    pedido, linea = reservar(cliente, producto)

    resumen = preventa.confirmar_ingreso({producto.pk: 0}, administrador)

    for objeto in (producto, pedido, linea):
        objeto.refresh_from_db()
    assert resumen.demorados == [producto]
    assert (producto.estado, producto.demorado) == (Producto.PRE_VENTA, True)
    assert linea.estado == LineaPedido.ESPERANDO_DEMORADO
    assert pedido.estado == Pedido.ESPERANDO_DEMORADO
    assert linea.decision_vence_en > timezone.now() + timedelta(hours=47)
    assert _acciones(RegistroAuditoria.REGISTRO_DEMORA).get().actor == administrador


@pytest.mark.django_db
def test_CO013_un_faltante_que_todavia_no_vence_no_cambia(administrador, cliente):
    producto = crear_preventa(dias=4)
    reservar(cliente, producto)
    antes = _foto()

    resumen = preventa.confirmar_ingreso({producto.pk: 0}, administrador)

    assert resumen.sin_cambios == [producto]
    assert _foto() == antes


@pytest.mark.django_db
def test_CO013_E3_un_producto_que_falla_queda_en_preventa_y_los_demas_siguen(
    administrador, cliente, mailoutbox, django_capture_on_commit_callbacks
):
    falla = crear_preventa(dias=0, titulo="Falla")
    sigue = crear_preventa(dias=0, titulo="Sigue")
    _, linea_falla = reservar(cliente, falla)
    original = preventa._ingresar

    def ingresar(pk, *args):
        if pk == falla.pk:
            original(pk, *args)
            raise RuntimeError("fallo técnico")
        return original(pk, *args)

    with mock.patch.object(preventa, "_ingresar", ingresar):
        with django_capture_on_commit_callbacks(execute=True):
            resumen = preventa.confirmar_ingreso({falla.pk: 5, sigue.pk: 5}, administrador)

    for objeto in (falla, sigue, linea_falla):
        objeto.refresh_from_db()
    assert (falla.estado, falla.stock) == (Producto.PRE_VENTA, 0)
    assert linea_falla.estado == LineaPedido.RESERVADO
    assert sigue.estado == Producto.ACTIVO
    assert resumen.errores == [str(falla)]
    assert _acciones(RegistroAuditoria.INCIDENTE_PREVENTA).get().actor == administrador
    assert any(administrador.email in m.to for m in mailoutbox)


@pytest.mark.django_db
def test_CO013_rechaza_unidades_negativas(administrador):
    producto = crear_preventa(dias=0)

    with pytest.raises(preventa.OperacionRechazada):
        preventa.confirmar_ingreso({producto.pk: -1}, administrador)


@pytest.mark.django_db
def test_CO013_el_articulo_de_despacho_diferido_llega_disponible_y_cierra_la_compensacion(
    administrador, cliente, mailoutbox, django_capture_on_commit_callbacks
):
    from apps.pedidos import demora

    producto, pedido, linea = demorar(cliente)
    demora.confirmar_opcion(pedido, linea.pk, cliente, LineaPedido.DESPACHO_DIFERIDO)
    mailoutbox.clear()

    with django_capture_on_commit_callbacks(execute=True):
        preventa.confirmar_ingreso({producto.pk: 1}, administrador)

    pedido.refresh_from_db()
    linea.refresh_from_db()
    assert pedido.estado == Pedido.EMPAQUETADO
    assert (linea.estado, linea.decision_demora, linea.compensacion_cerrada) == (
        LineaPedido.DISPONIBLE,
        LineaPedido.DESPACHO_DIFERIDO,
        True,
    )
    assert "llegó" in mailoutbox[0].subject.lower()


@pytest.mark.django_db
def test_CO013_por_la_pantalla_se_revisa_y_despues_se_confirma(client_admin, cliente):
    producto = crear_preventa(dias=0)
    reservar(cliente, producto)
    datos = {"producto": [producto.pk], f"unidades_{producto.pk}": "3"}
    antes = _foto()

    revision = client_admin.post(reverse("pedidos:ingreso"), datos)

    assert revision.status_code == 200
    assert "Pasa a la venta" in revision.content.decode()
    assert _foto() == antes

    respuesta = client_admin.post(reverse("pedidos:ingreso"), {**datos, "confirmar": "1"})

    producto.refresh_from_db()
    assert respuesta.url == reverse("pedidos:preventas")
    assert (producto.estado, producto.stock) == (Producto.ACTIVO, 2)


@pytest.mark.django_db
@pytest.mark.parametrize("valor", ["dos", "-3", "10000"])
def test_CO013_la_pantalla_rechaza_unidades_invalidas(client_admin, valor):
    producto = crear_preventa(dias=0)

    respuesta = client_admin.post(
        reverse("pedidos:ingreso"),
        {"producto": [producto.pk], f"unidades_{producto.pk}": valor, "confirmar": "1"},
        follow=True,
    )

    producto.refresh_from_db()
    assert producto.estado == Producto.PRE_VENTA
    assert "Revise las unidades" in respuesta.content.decode()


@pytest.mark.django_db
def test_CO013_la_pantalla_agrupa_por_fecha_y_editorial(client_admin):
    ivrea, panini = EditorialFactory(nombre="Ivrea"), EditorialFactory(nombre="Panini")
    crear_preventa(dias=1, editorial=ivrea, titulo="Uno")
    crear_preventa(dias=1, editorial=ivrea, titulo="Dos")
    crear_preventa(dias=1, editorial=panini, titulo="Tres")
    crear_preventa(dias=-2, editorial=panini, titulo="Cuatro")

    respuesta = client_admin.get(reverse("pedidos:preventas"))

    grupos = respuesta.context["grupos"]
    assert [(g.editorial.nombre, len(g.filas)) for g in grupos] == [
        ("Panini", 1),
        ("Ivrea", 2),
        ("Panini", 1),
    ]
    assert grupos[0].vencido
    assert "Atrasado" in respuesta.content.decode()


@pytest.mark.django_db
def test_CO013_un_producto_que_ya_no_esta_en_preventa_se_informa(client_admin):
    producto = crear_preventa(dias=0)
    Producto.objects.filter(pk=producto.pk).update(estado=Producto.ACTIVO)

    respuesta = client_admin.post(
        reverse("pedidos:ingreso"),
        {"producto": [producto.pk], f"unidades_{producto.pk}": "3"},
        follow=True,
    )

    assert "Ninguno de esos productos sigue en pre-venta" in respuesta.content.decode()


# ---------------------------------------------------------------------------
# CO-014 solicitarRegistroDeDemora · CO-015 confirmarRegistroDeDemora
# ---------------------------------------------------------------------------


def _url_demora(producto):
    return reverse("pedidos:demora", args=[producto.pk])


@pytest.mark.django_db
def test_CO014_informa_pedidos_y_clientes_sin_registrar_nada(client_admin, cliente):
    producto = crear_preventa(dias=5)
    reservar(cliente, producto)
    reservar(cliente, producto)
    antes = _foto()

    respuesta = client_admin.post(_url_demora(producto), {"fecha_estimada": "", "nota": ""})

    informe = respuesta.context["informe"]
    assert (informe.pedidos, informe.clientes) == (2, 1)
    assert _foto() == antes
    assert not _acciones(RegistroAuditoria.REGISTRO_DEMORA).exists()


@pytest.mark.django_db
def test_CO014_A3_sin_pedidos_lo_dice(client_admin):
    producto = crear_preventa(dias=5)

    respuesta = client_admin.post(_url_demora(producto), {"fecha_estimada": "", "nota": ""})

    assert respuesta.context["informe"].pedidos == 0
    assert "Sin pedidos activos" in respuesta.content.decode()


@pytest.mark.django_db
@pytest.mark.parametrize("dias", [0, -1])
def test_CO014_E1_la_fecha_estimada_debe_ser_posterior_a_hoy(client_admin, dias):
    producto = crear_preventa(dias=5)
    fecha = (timezone.localdate() + timedelta(days=dias)).isoformat()

    respuesta = client_admin.post(
        _url_demora(producto), {"fecha_estimada": fecha, "nota": "Imprenta", "confirmar": "1"}
    )

    producto.refresh_from_db()
    assert respuesta.status_code == 200
    assert "posterior a hoy" in respuesta.content.decode()
    assert respuesta.context["form"].data["nota"] == "Imprenta"
    assert not producto.demorado


@pytest.mark.django_db
def test_CO014_rechaza_lo_ya_demorado_lo_vencido_y_lo_que_no_es_preventa(
    client_admin, administrador
):
    demorado = crear_preventa(dias=5)
    preventa.registrar_demora(demorado, administrador)
    vencido = crear_preventa(dias=-1)
    activo = crear_preventa(dias=5)
    Producto.objects.filter(pk=activo.pk).update(estado=Producto.ACTIVO)

    for producto in (demorado, vencido, activo):
        respuesta = client_admin.get(_url_demora(producto))
        assert respuesta.url == reverse("catalog:producto_detalle", args=[producto.pk])
    assert _acciones(RegistroAuditoria.REGISTRO_DEMORA).count() == 1


@pytest.mark.django_db
def test_CO015_confirmar_demora_marca_el_producto_y_transiciona_los_pedidos(
    client_admin, administrador, cliente, mailoutbox, django_capture_on_commit_callbacks
):
    fijar_parametros(ventana_decision_horas=72)
    producto = crear_preventa(dias=5)
    llegada_original = producto.fecha_llegada
    pedido, linea = reservar(cliente, producto, otros=(("5000", 1),))
    nueva = timezone.localdate() + timedelta(days=30)

    with django_capture_on_commit_callbacks(execute=True):
        respuesta = client_admin.post(
            _url_demora(producto),
            {"fecha_estimada": nueva.isoformat(), "nota": "Imprenta", "confirmar": "1"},
        )

    producto = ProductoEditorial.objects.get(pk=producto.pk)
    pedido.refresh_from_db()
    linea.refresh_from_db()
    assert respuesta.url == reverse("catalog:producto_detalle", args=[producto.pk])
    assert (producto.estado, producto.demorado) == (Producto.PRE_VENTA, True)
    assert (producto.fecha_estimada, producto.nota_demora) == (nueva, "Imprenta")
    assert linea.estado == LineaPedido.ESPERANDO_DEMORADO
    assert linea.fecha_llegada_original == llegada_original
    assert linea.compensacion_acumulada == Decimal("0")
    assert not linea.decision_demora
    assert timedelta(hours=71) < linea.decision_vence_en - timezone.now() <= timedelta(hours=72)
    assert pedido.estado == Pedido.ESPERANDO_DEMORADO
    assert pedido.lineas.get(estado=LineaPedido.DISPONIBLE)
    entrada = _acciones(RegistroAuditoria.REGISTRO_DEMORA).get()
    assert entrada.actor == administrador
    correo = mailoutbox[0]
    assert correo.to == [cliente.email]
    assert reverse("cuenta:pedido", args=[pedido.numero]) in correo.body
    assert nueva.strftime("%d/%m/%Y") in correo.body


@pytest.mark.django_db
def test_CO015_A1_sin_fecha_estimada_el_aviso_la_omite(
    administrador, cliente, mailoutbox, django_capture_on_commit_callbacks
):
    producto = crear_preventa(dias=5)
    reservar(cliente, producto)

    with django_capture_on_commit_callbacks(execute=True):
        preventa.registrar_demora(producto, administrador)

    producto.refresh_from_db()
    assert producto.fecha_estimada is None
    assert "Nueva fecha estimada" not in mailoutbox[0].body


@pytest.mark.django_db
def test_CO015_A3_sin_pedidos_registra_la_demora_sin_avisos(administrador, mailoutbox):
    producto = crear_preventa(dias=5)

    resumen = preventa.registrar_demora(producto, administrador)

    producto.refresh_from_db()
    assert producto.demorado
    assert resumen.pedidos == []
    assert mailoutbox == []
    assert _acciones(RegistroAuditoria.REGISTRO_DEMORA).exists()


@pytest.mark.django_db
def test_CO015_E2_un_pedido_que_falla_no_frena_a_los_demas(
    administrador, cliente, mailoutbox, django_capture_on_commit_callbacks
):
    producto = crear_preventa(dias=5)
    falla, linea_falla = reservar(cliente, producto, hace_minutos=10)
    sigue, linea_sigue = reservar(cliente, producto)
    original = preventa._demorar_pedido

    def demorar_pedido(pedido, *args):
        original(pedido, *args)
        if pedido.pk == falla.pk:
            raise RuntimeError("fallo técnico")

    with mock.patch.object(preventa, "_demorar_pedido", demorar_pedido):
        with django_capture_on_commit_callbacks(execute=True):
            resumen = preventa.registrar_demora(producto, administrador)

    for objeto in (producto, falla, sigue, linea_falla, linea_sigue):
        objeto.refresh_from_db()
    assert producto.demorado
    assert resumen.errores == [falla.numero]
    assert (falla.estado, linea_falla.estado) == (Pedido.ESPERANDO_PRE_VENTA, LineaPedido.RESERVADO)
    assert (sigue.estado, linea_sigue.estado) == (
        Pedido.ESPERANDO_DEMORADO,
        LineaPedido.ESPERANDO_DEMORADO,
    )
    assert falla.numero in _acciones(RegistroAuditoria.INCIDENTE_PREVENTA).get().detalle
    assert any(administrador.email in m.to for m in mailoutbox)


@pytest.mark.django_db
def test_CO156_volver_desde_el_informe_de_demora_no_registra_nada(client_admin, cliente):
    producto = crear_preventa(dias=5)
    reservar(cliente, producto)
    antes = _foto()

    client_admin.get(_url_demora(producto))
    client_admin.post(_url_demora(producto), {"fecha_estimada": "", "nota": "x"})
    client_admin.get(reverse("catalog:producto_detalle", args=[producto.pk]))

    assert _foto() == antes
    assert not _acciones(RegistroAuditoria.REGISTRO_DEMORA).exists()


# ---------------------------------------------------------------------------
# CO-026 solicitarCancelacionDePreventaEnLote · CO-027 confirmarCancelacionDePreventaEnLote
# ---------------------------------------------------------------------------


def _url_cancelar(producto):
    return reverse("pedidos:cancelar_preventa", args=[producto.pk])


@pytest.mark.django_db
def test_CO026_informa_reservas_por_cliente_y_los_puntos_a_reembolsar(client_admin, cliente):
    fijar_parametros()
    producto = crear_preventa(dias=5, precio="10005")
    # $10.005 en dinero: 1001 puntos, hacia arriba (B-01-010); más el envío de
    # un pedido que se queda vacío: $1.500, 150 puntos (B-08-008).
    reservar(cliente, producto)
    # Pagada con 900 puntos, en un pedido que sigue con otro artículo.
    reservar(cliente, producto, puntos=900, otros=(("5000", 1),))
    antes = _foto()

    respuesta = client_admin.get(_url_cancelar(producto))

    informe = respuesta.context["informe"]
    assert (informe.reservas, informe.total_puntos) == (2, 1001 + 150 + 900)
    assert [c.usuario for c in informe.clientes] == [cliente]
    assert _foto() == antes


@pytest.mark.django_db
def test_CO026_sin_reservas_lo_dice_con_cero(client_admin):
    producto = crear_preventa(dias=5)

    respuesta = client_admin.get(_url_cancelar(producto))

    assert (respuesta.context["informe"].reservas, respuesta.context["informe"].total_puntos) == (
        0,
        0,
    )
    assert "Sin reservas activas" in respuesta.content.decode()


@pytest.mark.django_db
def test_CO027_cancela_reservas_reembolsa_en_puntos_y_cancela_el_producto(
    client_admin, administrador, cliente, mailoutbox, django_capture_on_commit_callbacks
):
    fijar_parametros(caducidad_puntos_meses=12)
    producto = crear_preventa(dias=5, precio="10000")
    solo, linea_solo = reservar(cliente, producto)
    con_otro, linea_con_otro = reservar(cliente, producto, puntos=1000, otros=(("5000", 1),))
    stock_antes = producto.stock

    with django_capture_on_commit_callbacks(execute=True):
        respuesta = client_admin.post(_url_cancelar(producto))

    for objeto in (producto, solo, con_otro, linea_solo, linea_con_otro):
        objeto.refresh_from_db()
    assert respuesta.url == reverse("catalog:producto_detalle", args=[producto.pk])
    assert producto.estado == Producto.CANCELADO_EDITORIAL
    assert producto.stock == stock_antes
    assert {linea_solo.estado, linea_con_otro.estado} == {LineaPedido.CANCELADO_REEMBOLSO}
    assert solo.estado == Pedido.CANCELADO
    assert con_otro.estado == Pedido.PENDIENTE_ARMADO
    # Un lote por cliente: 1000 + 150 del envío del pedido vacío + 1000 en puntos.
    lote = LotePuntos.objects.get(usuario=cliente)
    assert (lote.origen, lote.cantidad_acreditada, lote.disponible) == (
        LotePuntos.REEMBOLSO,
        2150,
        2150,
    )
    assert lote.caduca_el.year == timezone.localdate().year + 1
    movimiento = MovimientoPuntos.objects.get(usuario=cliente)
    assert (movimiento.tipo, movimiento.saldo_resultante) == (MovimientoPuntos.ACREDITACION, 2150)
    assert list(movimiento.lotes.all()) == [lote]
    entrada = _acciones(RegistroAuditoria.CANCELACION_PREVENTA_LOTE).get()
    assert entrada.actor == administrador
    assert "2 reserva(s)" in entrada.detalle and "2150 pts" in entrada.detalle
    assert mailoutbox[0].to == [cliente.email]
    assert solo.numero in mailoutbox[0].body


@pytest.mark.django_db
def test_CO027_sin_reservas_solo_cambia_el_estado(client_admin):
    producto = crear_preventa(dias=5)

    client_admin.post(_url_cancelar(producto))

    producto.refresh_from_db()
    assert producto.estado == Producto.CANCELADO_EDITORIAL
    assert not LotePuntos.objects.exists()
    assert "0 reserva(s)" in _acciones(RegistroAuditoria.CANCELACION_PREVENTA_LOTE).get().detalle


@pytest.mark.django_db
def test_CO027_incluye_las_reservas_ya_demoradas(client_admin, cliente):
    producto, pedido, linea = demorar(cliente)

    client_admin.post(_url_cancelar(producto))

    linea.refresh_from_db()
    pedido.refresh_from_db()
    assert linea.estado == LineaPedido.CANCELADO_REEMBOLSO
    assert linea.compensacion_cerrada
    assert pedido.estado == Pedido.PENDIENTE_ARMADO


@pytest.mark.django_db
def test_CO027_E1_si_falla_un_reembolso_no_queda_nada(client_admin, cliente):
    producto = crear_preventa(dias=5)
    _, linea = reservar(cliente, producto)
    antes = _foto()

    with mock.patch("apps.puntos.servicios.acreditar", side_effect=RuntimeError("fallo técnico")):
        respuesta = client_admin.post(_url_cancelar(producto), follow=True)

    assert _foto() == antes
    assert not LotePuntos.objects.exists()
    assert not _acciones(RegistroAuditoria.CANCELACION_PREVENTA_LOTE).exists()
    assert "No quedó ningún cambio" in respuesta.content.decode()


@pytest.mark.django_db
def test_CO027_no_se_cancela_lo_que_no_esta_en_preventa(client_admin):
    producto = crear_preventa(dias=5)
    Producto.objects.filter(pk=producto.pk).update(estado=Producto.ACTIVO)

    lectura = client_admin.get(_url_cancelar(producto))
    escritura = client_admin.post(_url_cancelar(producto))

    producto.refresh_from_db()
    assert producto.estado == Producto.ACTIVO
    assert lectura.url == escritura.url == reverse("catalog:producto_detalle", args=[producto.pk])


@pytest.mark.django_db
def test_CO156_volver_desde_la_cancelacion_no_cambia_nada(client_admin, cliente):
    producto = crear_preventa(dias=5)
    reservar(cliente, producto)
    antes = _foto()

    client_admin.get(_url_cancelar(producto))
    client_admin.get(reverse("catalog:producto_detalle", args=[producto.pk]))

    assert _foto() == antes
    assert not LotePuntos.objects.exists()


@pytest.mark.django_db
def test_CO013_la_revision_dice_que_faltante_se_demora_y_cual_no_cambia(client_admin, cliente):
    vencido = crear_preventa(dias=0, titulo="Vencido")
    futuro = crear_preventa(dias=4, titulo="Futuro")
    reservar(cliente, vencido)
    datos = {"producto": [vencido.pk, futuro.pk]}

    respuesta = client_admin.post(reverse("pedidos:ingreso"), datos)

    filas = {fila.producto.pk: fila for fila in respuesta.context["filas"]}
    assert filas[vencido.pk].se_demora and not filas[futuro.pk].se_demora
    contenido = respuesta.content.decode()
    assert "Se demora" in contenido and "Sin cambios" in contenido


@pytest.mark.django_db
def test_CO015_el_servicio_rechaza_una_fecha_estimada_que_no_es_futura(administrador):
    producto = crear_preventa(dias=5)

    with pytest.raises(preventa.OperacionRechazada):
        preventa.registrar_demora(producto, administrador, fecha_estimada=timezone.localdate())

    producto.refresh_from_db()
    assert not producto.demorado
