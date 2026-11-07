"""B-05-014: el pedido cuyo correo no salió queda «Sin enviar», a la vista.

Lo que pasó con Sakamoto #24 en la VM: el borrador se confirmó, nació en Pre-venta,
el correo del pedido falló al cerrar la revisión y, como el pedido sólo se
registraba si salía, el tomo quedó en Pre-venta sin nada en camino y sin ningún
lugar desde donde volver a pedirlo. Ahora:

- el pedido queda «Sin enviar», con su error, para reintentarlo o descartarlo;
- no da cupo hasta que sale, porque nadie lo está mandando;
- y una Pre-venta sin nada en camino entra en la propuesta de restock.
"""

from unittest.mock import patch

import pytest
from django.urls import reverse

from apps.accounts.models import Usuario
from apps.accounts.tests.factories import UsuarioFactory
from apps.avisos import bot, telegram
from apps.avisos.models import PreferenciaAviso, VinculoTelegram
from apps.avisos.tests.telegram_falso import TOKEN, telegram_falso
from apps.catalog.models import Producto
from apps.catalog.tests.factories import EditorialFactory, ProductoFactory
from apps.core.models import RegistroAuditoria
from apps.pedidos.tests.util import reservar
from apps.restock import servicios as restock
from apps.suppliers import llegadas, respuestas
from apps.suppliers import pedidos as correo_de_pedido
from apps.suppliers.models import PedidoProveedor
from apps.suppliers.tests.factories import ProveedorFactory
from apps.tienda.tests.compra_util import fijar_parametros

pytestmark = pytest.mark.django_db

CHAT = 4242


@pytest.fixture
def ivrea(db):
    return ProveedorFactory(
        razon_social="Editorial Ivrea", editorial=EditorialFactory(nombre="Ivrea")
    )


@pytest.fixture
def sakamoto(ivrea):
    """Como nace un tomo confirmado desde un borrador: en Pre-venta y sin stock."""
    return ProductoFactory(
        titulo="Sakamoto Days",
        volumen=24,
        stock=0,
        estado=Producto.PRE_VENTA,
        editorial=ivrea.editorial,
        pedido_en_camino=0,
    )


def falla(proveedor, lineas):
    return correo_de_pedido.ResultadoDeEnvio(
        proveedor=proveedor, lineas=list(lineas), intentos=3, error="Connection unexpectedly closed"
    )


def sale(proveedor, lineas):
    return correo_de_pedido.ResultadoDeEnvio(
        proveedor=proveedor, lineas=list(lineas), enviado=True, intentos=1
    )


def pedir(ivrea, producto, actor=None, **extra):
    linea = correo_de_pedido.LineaDePedido(
        titulo=producto.titulo, volumen=24, isbn="", cantidad=30, producto=producto
    )
    return correo_de_pedido.enviar_y_registrar(
        ivrea, [linea], actor, origen=PedidoProveedor.REVISION, **extra
    )


@pytest.fixture
def sin_enviar(ivrea, sakamoto):
    with patch.object(correo_de_pedido, "enviar_pedido", side_effect=falla):
        return pedir(ivrea, sakamoto, registrar_si_falla=True).pedido


# ---------------------------------------------------------------------------
# Lo que queda cuando el correo no sale
# ---------------------------------------------------------------------------


def test_si_el_correo_falla_el_pedido_queda_sin_enviar_con_su_error(sin_enviar, sakamoto):
    assert sin_enviar.estado == PedidoProveedor.SIN_ENVIAR
    assert sin_enviar.error_de_envio == "Connection unexpectedly closed"
    assert sin_enviar.lineas.get().producto_id == sakamoto.pk
    # No es mercadería en camino: no da cupo.
    assert llegadas.pendiente(sakamoto) == 0


def test_sin_registrar_si_falla_sigue_como_antes(ivrea, sakamoto):
    with patch.object(correo_de_pedido, "enviar_pedido", side_effect=falla):
        resultado = pedir(ivrea, sakamoto)

    assert resultado.pedido is None and not PedidoProveedor.objects.exists()


def test_el_cierre_de_una_revisión_registra_el_que_no_salió(ivrea, sakamoto, administrador):
    from apps.catalog import revisiones

    borrador = type(
        "Borrador",
        (),
        {
            "titulo": "Sakamoto Days",
            "volumen": 24,
            "isbn": "",
            "stock_inicial": 30,
            "producto": sakamoto,
            "fecha_llegada": None,
        },
    )()
    with patch.object(correo_de_pedido, "enviar_pedido", side_effect=falla):
        resultado = revisiones._pedir_a(ivrea, [borrador], administrador, None)

    assert resultado.pedido.estado == PedidoProveedor.SIN_ENVIAR


def test_una_preventa_sin_enviar_no_abre_preventas_nuevas(ivrea):
    agotado = ProductoFactory(stock=0, estado=Producto.AGOTADO, editorial=ivrea.editorial)

    with patch.object(correo_de_pedido, "enviar_pedido", side_effect=falla):
        pedir(ivrea, agotado, registrar_si_falla=True)

    agotado.refresh_from_db()
    assert agotado.estado == Producto.AGOTADO


# ---------------------------------------------------------------------------
# Reintentar y descartar
# ---------------------------------------------------------------------------


def test_reintentar_lo_manda_y_lo_deja_por_llegar(sin_enviar, sakamoto, administrador):
    with patch.object(correo_de_pedido, "enviar_pedido", side_effect=sale):
        envio = correo_de_pedido.reintentar(sin_enviar, administrador)

    sin_enviar.refresh_from_db()
    assert envio.enviado and sin_enviar.estado == PedidoProveedor.ABIERTO
    assert sin_enviar.error_de_envio == ""
    assert llegadas.pendiente(sakamoto) == 30
    assert RegistroAuditoria.objects.filter(
        accion=RegistroAuditoria.PEDIDO_A_PROVEEDOR,
        detalle__startswith="Reintento",
        actor=administrador,
    ).exists()


def test_si_vuelve_a_fallar_queda_sin_enviar_con_el_error_nuevo(sin_enviar, administrador):
    def otra_falla(proveedor, lineas):
        resultado = falla(proveedor, lineas)
        resultado.error = "timed out"
        return resultado

    with patch.object(correo_de_pedido, "enviar_pedido", side_effect=otra_falla):
        envio = correo_de_pedido.reintentar(sin_enviar, administrador)

    sin_enviar.refresh_from_db()
    assert not envio.enviado
    assert (sin_enviar.estado, sin_enviar.error_de_envio) == (
        PedidoProveedor.SIN_ENVIAR,
        "timed out",
    )


def test_reintentar_sin_correo_del_proveedor_lo_dice(sin_enviar, ivrea, administrador):
    type(ivrea).objects.filter(pk=ivrea.pk).update(correo_comercial="")

    envio = correo_de_pedido.reintentar(sin_enviar, administrador)

    assert envio.error == "sin correo registrado"


def test_lo_que_ya_salió_no_se_reintenta(sin_enviar, administrador):
    with patch.object(correo_de_pedido, "enviar_pedido", side_effect=sale):
        correo_de_pedido.reintentar(sin_enviar, administrador)

    with pytest.raises(llegadas.OperacionRechazada):
        correo_de_pedido.reintentar(sin_enviar, administrador)


def test_descartarlo_pide_motivo_y_saca_la_preventa_sin_reservas(
    sin_enviar, sakamoto, administrador
):
    with pytest.raises(llegadas.OperacionRechazada, match="obligatorio"):
        correo_de_pedido.descartar_sin_enviar(sin_enviar, "", administrador)

    correo_de_pedido.descartar_sin_enviar(sin_enviar, "Ya se pidió por teléfono", administrador)

    sin_enviar.refresh_from_db()
    sakamoto.refresh_from_db()
    assert sin_enviar.estado == PedidoProveedor.CERRADO
    assert sin_enviar.lineas.get().motivo_cierre == "Ya se pidió por teléfono"
    assert sakamoto.estado == Producto.AGOTADO


def test_un_pedido_sin_enviar_no_recibe_llegada_ni_respuesta(
    client_admin, sin_enviar, administrador
):
    linea = sin_enviar.lineas.get()

    client_admin.post(
        reverse("suppliers:llegada_revisar"),
        {
            "fila": [f"l{linea.pk}"],
            f"llegaron_l{linea.pk}": "5",
            f"vista_l{linea.pk}": "0",
            "confirmar": "1",
        },
    )
    linea.refresh_from_db()
    assert linea.cantidad_recibida == 0
    with pytest.raises(llegadas.OperacionRechazada, match="todavía no salió"):
        respuestas.confirmar_todo(sin_enviar, administrador)


# ---------------------------------------------------------------------------
# Las pantallas
# ---------------------------------------------------------------------------


def test_la_ficha_lo_dice_y_ofrece_reintentar_y_descartar(client_admin, sin_enviar):
    html = client_admin.get(
        reverse("suppliers:pedido_detalle", args=[sin_enviar.pk])
    ).content.decode()

    assert "El correo de este pedido no salió" in html
    assert "Connection unexpectedly closed" in html
    assert "Reintentar el envío" in html and "Descartar el pedido" in html


def test_la_lista_lo_muestra_primero_y_lo_cuenta(client_admin, sin_enviar):
    html = client_admin.get(reverse("suppliers:pedido_lista")).content.decode()

    assert "Sin enviar" in html
    assert client_admin.get(reverse("suppliers:pedido_lista")).context["sin_enviar"] == 1


def test_reintentar_desde_la_ficha(client_admin, sin_enviar):
    with patch.object(correo_de_pedido, "enviar_pedido", side_effect=sale):
        respuesta = client_admin.post(
            reverse("suppliers:pedido_reintentar", args=[sin_enviar.pk]), follow=True
        )

    assert "ya está por llegar" in respuesta.content.decode()
    sin_enviar.refresh_from_db()
    assert sin_enviar.estado == PedidoProveedor.ABIERTO


def test_descartar_desde_la_ficha(client_admin, sin_enviar):
    client_admin.post(
        reverse("suppliers:pedido_descartar", args=[sin_enviar.pk]), {"motivo": "No va más"}
    )

    sin_enviar.refresh_from_db()
    assert sin_enviar.estado == PedidoProveedor.CERRADO


# Foco reforzado: control de acceso por la dirección real.


@pytest.mark.parametrize("nombre", ["suppliers:pedido_reintentar", "suppliers:pedido_descartar"])
def test_el_cajero_no_reintenta_ni_descarta(client, sin_enviar, nombre):
    client.force_login(UsuarioFactory(rol=Usuario.CAJERO))

    with patch.object(correo_de_pedido, "enviar_pedido", side_effect=sale) as enviar:
        respuesta = client.post(reverse(nombre, args=[sin_enviar.pk]), {"motivo": "x"})

    assert respuesta.status_code == 403
    enviar.assert_not_called()
    sin_enviar.refresh_from_db()
    assert sin_enviar.estado == PedidoProveedor.SIN_ENVIAR


# ---------------------------------------------------------------------------
# Restock ve la Pre-venta sin nada en camino
# ---------------------------------------------------------------------------


def test_la_preventa_sin_nada_en_camino_entra_en_la_propuesta(sin_enviar, sakamoto, cliente):
    fijar_parametros(cantidad_minima_restock=3, margen_stock_restock=2)
    reservar(cliente, sakamoto, cantidad=5)

    propuesta = restock.ciclo_semanal().propuesta

    linea = propuesta.lineas.get(producto=sakamoto)
    assert linea.cantidad_sugerida == 5


def test_la_preventa_con_un_pedido_en_camino_no_entra(ivrea, sakamoto):
    fijar_parametros(cantidad_minima_restock=3, margen_stock_restock=2)
    with patch.object(correo_de_pedido, "enviar_pedido", side_effect=sale):
        pedir(ivrea, sakamoto)

    assert not restock.elegibles().filter(pk=sakamoto.pk).exists()


# ---------------------------------------------------------------------------
# Telegram
# ---------------------------------------------------------------------------


@pytest.fixture
def vinculado(administrador, settings):
    settings.TELEGRAM_BOT_TOKEN = TOKEN
    settings.URL_PUBLICA = "https://longbox.test"
    VinculoTelegram.objects.create(usuario=administrador, chat_id=CHAT, nombre_en_telegram="Eze")
    PreferenciaAviso.objects.create(
        usuario=administrador, tipo="restock", por_correo=False, por_telegram=True
    )
    return administrador


def boton(accion, pk):
    datos = f"{accion}:{pk}:"
    return {
        "update_id": 2,
        "callback_query": {
            "id": "c",
            "data": f"{datos}:{telegram.firmar(datos, CHAT)}",
            "message": {"message_id": 9, "chat": {"id": CHAT, "type": "private"}},
        },
    }


def test_el_pedido_que_no_salió_llega_al_chat_y_se_reintenta(
    vinculado, ivrea, sakamoto, django_capture_on_commit_callbacks
):
    falso, parche = telegram_falso()
    with parche:
        with (
            patch.object(correo_de_pedido, "enviar_pedido", side_effect=falla),
            django_capture_on_commit_callbacks(execute=True),
        ):
            pedido = pedir(ivrea, sakamoto, registrar_si_falla=True).pedido
        aviso = falso.mensajes(CHAT)[-1]
        assert f"No salió el pedido #{pedido.pk}" in aviso["text"]
        assert aviso["reply_markup"]["inline_keyboard"][0][0]["callback_data"].startswith("pe:")

        with patch.object(correo_de_pedido, "enviar_pedido", side_effect=sale):
            bot.procesar(boton("pe", pedido.pk))

    pedido.refresh_from_db()
    assert pedido.estado == PedidoProveedor.ABIERTO
    assert "¡Salió el pedido" in falso.textos(CHAT)[-1]
