"""La respuesta del proveedor a un pedido (plan 00 de la respuesta del proveedor).

Sin código de contrato todavía: el caso de uso y sus operaciones esperan el que
asigne el responsable. Las reglas del plan, cada una con su prueba:

- lo que se espera es lo confirmado, y con eso el cupo de la pre-venta;
- confirmar menos que lo reservado se acepta y se avisa, sin cancelar nada;
- lo que no puede abastecer se cierra sin recibir, con motivo;
- mover la fecha de una pre-venta con reservas es una demora, y no toca la fecha del Cliente;
- la propuesta despachada espera la respuesta y se cierra cuando respondieron todos.
"""

from datetime import date, timedelta
from unittest.mock import patch

import pytest
from django.urls import reverse
from django.utils import timezone

from apps.accounts.models import Usuario
from apps.accounts.tests.factories import UsuarioFactory
from apps.avisos import bot, telegram
from apps.avisos.models import PreferenciaAviso, VinculoTelegram
from apps.avisos.tests.telegram_falso import TOKEN, telegram_falso
from apps.catalog.models import Producto, ProductoEditorial
from apps.catalog.tests.factories import EditorialFactory, ProductoFactory
from apps.core.models import RegistroAuditoria
from apps.core.tests.concurrencia import a_la_vez
from apps.pedidos.models import LineaPedido
from apps.pedidos.tests.util import reservar
from apps.restock import servicios as restock
from apps.restock.models import PropuestaRestock
from apps.suppliers import llegadas, respuestas
from apps.suppliers.llegadas import OperacionRechazada
from apps.suppliers.models import LineaPedidoProveedor, PedidoProveedor
from apps.suppliers.tests.factories import ProveedorFactory
from apps.tienda.tests.compra_util import fijar_parametros

pytestmark = pytest.mark.django_db

CHAT = 4242
DENTRO_DE_UN_MES = timezone.localdate() + timedelta(days=30)


@pytest.fixture
def ivrea(db):
    return ProveedorFactory(razon_social="Distribuidora Ivrea", editorial=EditorialFactory())


def agotado(ivrea, titulo="Akira"):
    return ProductoFactory(
        titulo=titulo, stock=0, estado=Producto.AGOTADO, editorial=ivrea.editorial
    )


@pytest.fixture
def pedido(ivrea):
    return llegadas.registrar(
        ivrea,
        PedidoProveedor.MANUAL,
        [(agotado(ivrea, "Akira"), 6), (agotado(ivrea, "Berserk"), 4)],
        fecha_estimada=DENTRO_DE_UN_MES,
    )


def lineas(pedido):
    return {linea.producto.titulo: linea for linea in pedido.lineas.select_related("producto")}


# ---------------------------------------------------------------------------
# Las respuestas, una por una
# ---------------------------------------------------------------------------


def test_confirmar_todo_deja_cada_línea_confirmada_y_lo_audita(pedido, administrador):
    respuestas.confirmar_todo(pedido, administrador)

    pedido.refresh_from_db()
    assert pedido.respondido
    assert {linea.respuesta for linea in pedido.lineas.all()} == {LineaPedidoProveedor.CONFIRMADA}
    assert RegistroAuditoria.objects.filter(
        accion=RegistroAuditoria.RESPUESTA_PROVEEDOR, actor=administrador
    ).exists()


def test_otra_cantidad_cambia_lo_que_se_espera(pedido, administrador):
    akira = lineas(pedido)["Akira"]

    respuestas.responder(pedido, {akira.pk: (LineaPedidoProveedor.OTRA_CANTIDAD, 2)}, administrador)

    akira.refresh_from_db()
    assert (akira.respuesta, akira.cantidad_confirmada, akira.esperada) == ("otra_cantidad", 2, 2)
    assert akira.pendiente == 2 and llegadas.pendiente(akira.producto) == 2


def test_la_misma_cantidad_que_lo_pedido_es_una_confirmación(pedido, administrador):
    akira = lineas(pedido)["Akira"]

    respuestas.responder(pedido, {akira.pk: (LineaPedidoProveedor.OTRA_CANTIDAD, 6)}, administrador)

    akira.refresh_from_db()
    assert akira.respuesta == LineaPedidoProveedor.CONFIRMADA and akira.cantidad_confirmada is None


@pytest.mark.parametrize("cantidad", [0, None, -1])
def test_confirmar_cero_no_se_puede(pedido, administrador, cantidad):
    akira = lineas(pedido)["Akira"]

    with pytest.raises(OperacionRechazada, match="mayor que cero"):
        respuestas.responder(
            pedido, {akira.pk: (LineaPedidoProveedor.OTRA_CANTIDAD, cantidad)}, administrador
        )


def test_confirmar_menos_de_lo_que_ya_llegó_cierra_la_línea(pedido, administrador):
    akira = lineas(pedido)["Akira"]
    llegadas.registrar_llegada(pedido, {akira.pk: 3}, administrador)

    respuestas.responder(pedido, {akira.pk: (LineaPedidoProveedor.OTRA_CANTIDAD, 3)}, administrador)

    akira.refresh_from_db()
    assert akira.estado == LineaPedidoProveedor.RECIBIDA


def test_la_llegada_se_mide_contra_lo_confirmado(pedido, administrador):
    akira = lineas(pedido)["Akira"]
    respuestas.responder(pedido, {akira.pk: (LineaPedidoProveedor.OTRA_CANTIDAD, 2)}, administrador)

    llegadas.registrar_llegada(pedido, {akira.pk: 2}, administrador)

    akira.refresh_from_db()
    assert akira.estado == LineaPedidoProveedor.RECIBIDA


def test_no_disponible_pide_motivo_y_cierra_sin_recibir(pedido, administrador):
    akira = lineas(pedido)["Akira"]
    no = {akira.pk: (LineaPedidoProveedor.NO_DISPONIBLE, None)}

    with pytest.raises(OperacionRechazada, match="motivo es obligatorio"):
        respuestas.responder(pedido, no, administrador)
    respuestas.responder(pedido, no, administrador, motivo="No tiene stock")

    akira.refresh_from_db()
    assert akira.estado == LineaPedidoProveedor.SIN_RECIBIR
    assert akira.respuesta == LineaPedidoProveedor.NO_DISPONIBLE
    assert akira.motivo_cierre == "No tiene stock"


def test_no_puede_cierra_el_pedido_entero(pedido, administrador):
    respuestas.no_puede(pedido, "Discontinuado", administrador)

    pedido.refresh_from_db()
    assert pedido.estado == PedidoProveedor.CERRADO
    assert {linea.estado for linea in pedido.lineas.all()} == {LineaPedidoProveedor.SIN_RECIBIR}


def test_un_pedido_cerrado_no_admite_respuesta(pedido, administrador):
    respuestas.no_puede(pedido, "Discontinuado", administrador)

    with pytest.raises(OperacionRechazada, match="cerrado"):
        respuestas.poner_fecha(pedido, date(2027, 1, 1), administrador)


def test_sin_nada_para_anotar_lo_dice(pedido, administrador):
    with pytest.raises(OperacionRechazada, match="nada para anotar"):
        respuestas.responder(pedido, {}, administrador)


def test_la_línea_de_otro_pedido_no_se_toca(pedido, ivrea, administrador):
    otro = llegadas.registrar(ivrea, PedidoProveedor.MANUAL, [(agotado(ivrea, "Otro"), 1)])

    with pytest.raises(OperacionRechazada, match="no es de este pedido"):
        respuestas.responder(
            pedido, {otro.lineas.get().pk: (LineaPedidoProveedor.CONFIRMADA, None)}, administrador
        )


# ---------------------------------------------------------------------------
# Las pre-ventas: el cupo y la fecha (ambigüedades 3 y 4)
# ---------------------------------------------------------------------------


@pytest.fixture
def con_reservas(pedido, cliente):
    fijar_parametros(margen_cupo_preventa=0)
    akira = lineas(pedido)["Akira"]
    reservar(cliente, akira.producto, cantidad=4)
    return akira


def test_confirmar_menos_de_lo_reservado_se_acepta_y_avisa_sin_cancelar(
    con_reservas, pedido, administrador
):
    resultado = respuestas.responder(
        pedido, {con_reservas.pk: (LineaPedidoProveedor.OTRA_CANTIDAD, 2)}, administrador
    )

    ((producto, reservado, esperado),) = resultado.sin_cubrir
    assert (producto.pk, reservado, esperado) == (con_reservas.producto_id, 4, 2)
    assert LineaPedido.objects.get(producto=con_reservas.producto).estado == LineaPedido.RESERVADO


def test_atrasar_una_preventa_con_reservas_es_una_demora(con_reservas, pedido, administrador):
    antes = ProductoEditorial.objects.get(pk=con_reservas.producto_id).llegada_vigente

    resultado = respuestas.poner_fecha(pedido, DENTRO_DE_UN_MES + timedelta(days=20), administrador)

    assert [p.pk for p in resultado.para_demorar] == [con_reservas.producto_id]
    assert ProductoEditorial.objects.get(pk=con_reservas.producto_id).llegada_vigente == antes
    pedido.refresh_from_db()
    assert pedido.fecha_estimada == DENTRO_DE_UN_MES + timedelta(days=20)


def test_adelantar_una_preventa_con_reservas_no_es_demora(con_reservas, pedido, administrador):
    resultado = respuestas.poner_fecha(pedido, DENTRO_DE_UN_MES - timedelta(days=5), administrador)

    assert resultado.para_demorar == []


def test_una_preventa_sin_reservas_toma_la_fecha_nueva(pedido, administrador):
    berserk = lineas(pedido)["Berserk"]
    nueva = DENTRO_DE_UN_MES + timedelta(days=10)

    respuestas.poner_fecha(pedido, nueva, administrador)

    assert ProductoEditorial.objects.get(pk=berserk.producto_id).fecha_llegada == nueva


# ---------------------------------------------------------------------------
# La propuesta espera la respuesta (desvío de DME-13, aprobado)
# ---------------------------------------------------------------------------


@pytest.fixture
def despachada(administrador, mailoutbox):
    fijar_parametros(cantidad_minima_restock=3, margen_stock_restock=2)
    proveedores = []
    for nombre in ("Ivrea", "Panini"):
        editorial = EditorialFactory(nombre=nombre)
        proveedores.append(ProveedorFactory(editorial=editorial))
        ProductoFactory(editorial=editorial, stock=0, estado=Producto.AGOTADO)
    propuesta = restock.ciclo_semanal().propuesta
    for proveedor in proveedores:
        restock.despachar(propuesta, proveedor.pk, administrador)
    propuesta.refresh_from_db()
    return propuesta


def test_la_despachada_espera_la_respuesta(despachada):
    assert despachada.estado == PropuestaRestock.ESPERANDO
    assert despachada.pedidos.count() == 2


def test_se_cierra_cuando_respondió_el_último(despachada, administrador):
    primero, segundo = despachada.pedidos.order_by("pk")

    respuestas.confirmar_todo(primero, administrador)
    despachada.refresh_from_db()
    assert despachada.estado == PropuestaRestock.ESPERANDO

    resultado = respuestas.no_puede(segundo, "Sin stock", administrador)
    despachada.refresh_from_db()
    assert resultado.propuesta_cerrada and despachada.estado == PropuestaRestock.CERRADA


def test_la_llegada_sin_respuesta_también_cuenta(despachada, administrador):
    for pedido in despachada.pedidos.all():
        linea = pedido.lineas.get()
        llegadas.registrar_llegada(pedido, {linea.pk: linea.cantidad_pedida}, administrador)

    despachada.refresh_from_db()
    assert despachada.estado == PropuestaRestock.CERRADA


def test_mientras_espera_se_puede_generar_la_próxima(despachada, administrador):
    assert restock.armar_a_mano(administrador).estado == PropuestaRestock.PENDIENTE


@pytest.mark.django_db(transaction=True)
def test_la_web_y_el_chat_a_la_vez_cierran_la_propuesta_una_vez(despachada, administrador):
    for pedido in despachada.pedidos.order_by("pk")[:1]:
        respuestas.confirmar_todo(pedido, administrador)
    ultimo = despachada.pedidos.order_by("pk").last()

    def responder():
        try:
            respuestas.confirmar_todo(ultimo, administrador)
        except OperacionRechazada:
            return "ya estaba"
        return "respondió"

    a_la_vez(responder, responder)

    despachada.refresh_from_db()
    assert despachada.estado == PropuestaRestock.CERRADA
    assert (
        RegistroAuditoria.objects.filter(
            accion=RegistroAuditoria.CIERRE_PROPUESTA_RESTOCK, objetivo_pk=despachada.pk
        ).count()
        == 1
    )


# ---------------------------------------------------------------------------
# La pantalla
# ---------------------------------------------------------------------------


def test_la_ficha_del_pedido_pregunta_y_la_de_la_propuesta_enlaza(client_admin, despachada):
    """Plan 00 de la respuesta simple: la respuesta se anota sólo en la ficha del pedido."""
    pedido = despachada.pedidos.first()

    ficha = client_admin.get(reverse("suppliers:pedido_detalle", args=[pedido.pk])).content.decode()
    assert f"¿Qué contestó {pedido.nombre_proveedor}?" in ficha
    assert reverse("suppliers:pedido_responder", args=[pedido.pk, "todo"]) in ficha

    propuesta = client_admin.get(
        reverse("restock:propuesta_detalle", args=[despachada.pk])
    ).content.decode()
    assert "Anotar la respuesta" in propuesta
    assert "Guardar la respuesta" not in propuesta


def test_guardar_desde_la_ficha_anota_cada_línea_y_la_fecha(client_admin, pedido):
    akira, berserk = lineas(pedido)["Akira"], lineas(pedido)["Berserk"]
    volver = reverse("suppliers:pedido_detalle", args=[pedido.pk])

    respuesta = client_admin.post(
        reverse("suppliers:pedido_respuesta", args=[pedido.pk]),
        {
            "accion": "guardar",
            f"respuesta-{akira.pk}": "otra_cantidad",
            f"cantidad-{akira.pk}": "3",
            f"respuesta-{berserk.pk}": "confirmada",
            "fecha": "2027-01-15",
            "volver": volver,
        },
    )

    assert respuesta.url == f"{volver}#respuesta-{pedido.pk}"
    akira.refresh_from_db()
    berserk.refresh_from_db()
    pedido.refresh_from_db()
    assert (akira.cantidad_confirmada, berserk.respuesta) == (3, "confirmada")
    assert pedido.fecha_estimada == date(2027, 1, 15)


def test_no_puede_sin_motivo_lo_pide_y_no_cierra(client_admin, pedido):
    respuesta = client_admin.post(
        reverse("suppliers:pedido_respuesta", args=[pedido.pk]), {"accion": "nada"}, follow=True
    )

    assert "obligatorio" in respuesta.content.decode()
    pedido.refresh_from_db()
    assert pedido.estado == PedidoProveedor.ABIERTO


def test_volver_a_otro_sitio_no_se_sigue(client_admin, pedido):
    respuesta = client_admin.post(
        reverse("suppliers:pedido_respuesta", args=[pedido.pk]),
        {"accion": "todo", "volver": "https://otro.test/"},
    )

    assert respuesta.url.startswith(reverse("suppliers:pedido_detalle", args=[pedido.pk]))


# Foco reforzado: control de acceso por la dirección real.


@pytest.mark.parametrize("rol", [Usuario.CAJERO, Usuario.CLIENTE])
def test_el_rol_equivocado_no_responde(client, pedido, rol):
    client.force_login(UsuarioFactory(rol=rol))

    respuesta = client.post(
        reverse("suppliers:pedido_respuesta", args=[pedido.pk]), {"accion": "todo"}
    )

    assert respuesta.status_code in (403, 302)
    pedido.refresh_from_db()
    assert not pedido.respondido


# ---------------------------------------------------------------------------
# Telegram
# ---------------------------------------------------------------------------


@pytest.fixture
def falso(settings):
    settings.TELEGRAM_BOT_TOKEN = TOKEN
    settings.URL_PUBLICA = "https://longbox.test"
    falso, parche = telegram_falso()
    with parche:
        yield falso


@pytest.fixture
def vinculado(administrador):
    VinculoTelegram.objects.create(usuario=administrador, chat_id=CHAT, nombre_en_telegram="Eze")
    PreferenciaAviso.objects.create(
        usuario=administrador, tipo="restock", por_correo=False, por_telegram=True
    )
    return administrador


def boton(accion, pk, extra="", chat=CHAT, firma=None):
    datos = f"{accion}:{pk}:{extra}"
    return {
        "update_id": 2,
        "callback_query": {
            "id": "c",
            "data": f"{datos}:{firma or telegram.firmar(datos, chat)}",
            "message": {"message_id": 9, "chat": {"id": chat, "type": "private"}},
        },
    }


def respuesta_a(pregunta, texto):
    return {
        "update_id": 3,
        "message": {
            "chat": {"id": CHAT, "type": "private"},
            "text": texto,
            "reply_to_message": {"text": pregunta},
        },
    }


def test_el_pedido_que_sale_llega_al_chat_con_sus_botones(
    vinculado, falso, ivrea, django_capture_on_commit_callbacks
):
    from apps.suppliers import pedidos as correo_de_pedido
    from apps.suppliers.pedidos import LineaDePedido

    producto = agotado(ivrea)
    with django_capture_on_commit_callbacks(execute=True):
        resultado = correo_de_pedido.enviar_y_registrar(
            ivrea,
            [LineaDePedido(titulo="Akira", volumen=1, isbn="", cantidad=3, producto=producto)],
            vinculado,
            origen=PedidoProveedor.MANUAL,
        )

    mensaje = falso.mensajes(CHAT)[-1]
    assert f"Salió el pedido #{resultado.pedido.pk}" in mensaje["text"]
    botones = [b for fila in mensaje["reply_markup"]["inline_keyboard"] for b in fila]
    acciones = [b["callback_data"].split(":")[0] for b in botones if "callback_data" in b]
    assert acciones == ["pc", "pf", "pn"]
    # Plan 00 de la respuesta simple: «Con cambios» abre la pantalla de la web.
    (con_cambios,) = [b for b in botones if "url" in b]
    assert con_cambios["url"].endswith(
        reverse("suppliers:pedido_responder", args=[resultado.pedido.pk, "cambios"])
    )


def test_confirmó_todo_desde_el_chat(vinculado, falso, pedido):
    bot.procesar(boton("pc", pedido.pk))

    pedido.refresh_from_db()
    assert pedido.respondido
    assert "confirmó todo" in falso.textos(CHAT)[-1]
    assert RegistroAuditoria.objects.filter(
        accion=RegistroAuditoria.RESPUESTA_PROVEEDOR, detalle__endswith="(desde Telegram)"
    ).exists()


def test_la_fecha_se_escribe_respondiendo(vinculado, falso, pedido):
    bot.procesar(boton("pf", pedido.pk))
    pregunta = falso.textos(CHAT)[-1]
    assert "fecha de llegada del pedido" in pregunta

    bot.procesar(respuesta_a(pregunta, "15/01/2027"))

    pedido.refresh_from_db()
    assert pedido.fecha_estimada == date(2027, 1, 15)
    assert "llega el 15/01/2027" in falso.textos(CHAT)[-1]


def test_una_fecha_sin_año_es_la_próxima(vinculado, falso, pedido):
    hoy = timezone.localdate()
    manana = hoy + timedelta(days=1)

    bot.procesar(respuesta_a(f"la fecha de llegada del pedido #{pedido.pk}", f"{manana:%d/%m}"))

    pedido.refresh_from_db()
    assert pedido.fecha_estimada == manana


def test_una_fecha_que_no_se_entiende_lo_dice(vinculado, falso, pedido):
    bot.procesar(respuesta_a(f"la fecha de llegada del pedido #{pedido.pk}", "el martes"))

    pedido.refresh_from_db()
    assert pedido.fecha_estimada == DENTRO_DE_UN_MES
    assert "No entendí la fecha" in falso.textos(CHAT)[-1]


def test_no_puede_con_un_motivo_rápido(vinculado, falso, pedido):
    bot.procesar(boton("pn", pedido.pk))
    assert "¿Por qué no puede abastecer" in falso.textos(CHAT)[-1]

    bot.procesar(boton("pm", pedido.pk, extra="1"))

    pedido.refresh_from_db()
    assert pedido.estado == PedidoProveedor.CERRADO
    assert pedido.lineas.first().motivo_cierre == respuestas.MOTIVOS_NO_PUEDE[1]


def test_no_puede_con_otro_motivo_escrito(vinculado, falso, pedido):
    bot.procesar(boton("po", pedido.pk))
    pregunta = falso.textos(CHAT)[-1]

    bot.procesar(respuesta_a(pregunta, "Cerró la editorial"))

    pedido.refresh_from_db()
    assert pedido.lineas.first().motivo_cierre == "Cerró la editorial"


def test_un_botón_de_pedido_armado_a_mano_no_hace_nada(vinculado, falso, pedido):
    bot.procesar(boton("pc", pedido.pk, firma="000000000000"))

    pedido.refresh_from_db()
    assert not pedido.respondido


def test_un_administrador_dado_de_baja_no_responde(vinculado, falso, pedido):
    UsuarioFactory(rol=Usuario.ADMINISTRADOR)
    Usuario.objects.filter(pk=vinculado.pk).update(estado=Usuario.INACTIVO)

    bot.procesar(boton("pc", pedido.pk))
    bot.procesar(respuesta_a(f"fecha de llegada del pedido #{pedido.pk}", "15/01/2027"))

    pedido.refresh_from_db()
    assert not pedido.respondido and pedido.fecha_estimada == DENTRO_DE_UN_MES


def test_el_recordatorio_sale_a_los_tres_días_una_vez(vinculado, falso, pedido):
    assert respuestas.recordar() == []

    tarde = timezone.now() + timedelta(days=respuestas.DIAS_PARA_RECORDAR, minutes=1)
    assert respuestas.recordar(tarde) == [pedido]
    assert "todavía no respondió" in falso.textos(CHAT)[-1]
    assert respuestas.recordar(tarde + timedelta(days=1)) == []


def test_lo_respondido_no_se_recuerda(vinculado, falso, pedido, administrador):
    respuestas.confirmar_todo(pedido, administrador)

    assert respuestas.recordar(timezone.now() + timedelta(days=5)) == []


def test_el_resumen_cuenta_los_pedidos_sin_respuesta(pedido):
    from apps.avisos import resumen

    filas = dict(resumen.armar(timezone.localdate())["filas"])

    assert filas["🤝 Pedidos sin respuesta del proveedor"] == 1


# ---------------------------------------------------------------------------
# Reintentar un correo que falló, desde el chat (CO-019)
# ---------------------------------------------------------------------------


def test_un_correo_que_falla_ofrece_reintentar_y_reintentar_reprocesa(vinculado, falso):
    from types import SimpleNamespace

    from apps.suppliers import services
    from apps.suppliers.models import CorreoProveedor
    from apps.suppliers.tests import correos_de_ejemplo as ejemplo

    ProveedorFactory(correo_comercial="novedades@ivrea.test")
    correo = services.ingerir(ejemplo.correo_de_novedades()).correo

    def falla(pk, *, actor):
        CorreoProveedor.objects.filter(pk=pk).update(
            estado=CorreoProveedor.FALLIDO, motivo="El modelo no respondió."
        )
        return SimpleNamespace(generacion=None)

    with patch.object(services, "aprobar_correo", side_effect=falla):
        bot.procesar(boton("ap", correo.pk))

    mensaje = falso.mensajes(CHAT)[-1]
    assert "No pude procesar" in mensaje["text"]
    acciones = [
        b["callback_data"].split(":")[0]
        for fila in mensaje["reply_markup"]["inline_keyboard"]
        for b in fila
    ]
    assert acciones == ["rp", "de"]

    with patch.object(services, "reprocesar_correo", side_effect=falla) as reprocesar:
        bot.procesar(boton("rp", correo.pk))

    reprocesar.assert_called_once_with(correo.pk, actor=vinculado)
