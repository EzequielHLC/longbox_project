"""Pruebas de contrato de la compra como invitado (`CU-TDA-INV`, plan 07 sexta parte).

`CO-181` iniciarCompraComoInvitado, `CO-090` declararDatosDeInvitado, `CO-091`
confirmarPedidoDeInvitado y la rama de invitado de `CO-089`.
"""

from decimal import Decimal

import pytest
from django.core import mail
from django.urls import reverse

from apps.catalog.models import Producto
from apps.core.models import RegistroAuditoria
from apps.pedidos.models import Pedido, TransaccionPago
from apps.puntos.models import LotePuntos, MovimientoPuntos
from apps.tienda import compra
from apps.tienda.models import CobroEnCurso, LineaCarrito
from apps.tienda.tests.compra_util import (
    COSTO_ENVIO,
    OTRA_DIRECCION,
    URL_INVITADO,
    URL_INVITADO_CONFIRMAR,
    URL_INVITADO_RESUMEN,
    agregar,
    avisar,
    cliente_con_direccion,
    fijar_parametros,
    producto,
)

pytestmark = pytest.mark.django_db

DATOS = {"correo": "Lector@Correo.test", **OTRA_DIRECCION}


@pytest.fixture(autouse=True)
def parametros(db):
    return fijar_parametros()


def declarar(client, **cambios):
    return client.post(URL_INVITADO, {**DATOS, **cambios})


def comprar_como_invitado(client, *, aprobado=True):
    declarar(client)
    client.post(URL_INVITADO_CONFIRMAR)
    cobro = CobroEnCurso.objects.get()
    avisar(client, cobro, aprobado=aprobado)
    cobro.refresh_from_db()
    return cobro


# ===========================================================================
# CO-181 · iniciarCompraComoInvitado
# ===========================================================================


def test_CO181_presenta_el_formulario_de_datos_del_invitado(client):
    agregar(client, producto())

    respuesta = client.get(URL_INVITADO)

    assert respuesta.status_code == 200
    assert set(respuesta.context["form"].fields) >= {
        "correo",
        "direccion",
        "localidad",
        "provincia",
        "codigo_postal",
    }


def test_CO181_A1_ofrece_iniciar_sesion(client):
    agregar(client, producto())

    contenido = client.get(URL_INVITADO).content.decode()

    assert reverse("accounts:login") in contenido


def test_CO181_un_carrito_con_pre_venta_no_se_compra_como_invitado(client):
    agregar(client, producto(stock=0, estado=Producto.PRE_VENTA))

    respuesta = client.get(URL_INVITADO, follow=True)

    assert respuesta.redirect_chain[-1][0] == reverse("tienda:carrito")
    assert "Reservar una pre-venta requiere una cuenta" in respuesta.content.decode()


def test_CO181_no_modifica_el_estado_del_sistema(client):
    prod = producto()
    agregar(client, prod)

    client.get(URL_INVITADO)

    assert Producto.objects.get(pk=prod.pk).stock == 5
    assert not CobroEnCurso.objects.exists()


def test_CO181_un_cliente_con_sesion_va_a_su_checkout(client):
    client.force_login(cliente_con_direccion())

    respuesta = client.get(URL_INVITADO)

    assert respuesta.url == reverse("compra:checkout")


# ===========================================================================
# CO-090 · declararDatosDeInvitado
# ===========================================================================


def test_CO090_c_los_datos_quedan_asociados_al_checkout_sin_cambios_persistentes(client):
    prod = producto()
    agregar(client, prod)

    respuesta = declarar(client)

    assert respuesta.url == URL_INVITADO_RESUMEN
    assert client.session[compra.CLAVE_INVITADO]["correo"] == "lector@correo.test"
    assert not CobroEnCurso.objects.exists()
    assert not Pedido.objects.exists()
    assert Producto.objects.get(pk=prod.pk).stock == 5


def test_CO090_salida_el_resumen_con_envio_y_total_sin_canje(client):
    agregar(client, producto(precio="10000"), 2)
    declarar(client)

    respuesta = client.get(URL_INVITADO_RESUMEN)

    resumen = respuesta.context["resumen"]
    assert resumen.total == Decimal("20000") + COSTO_ENVIO
    assert resumen.saldo == 0
    assert "Cubrir con" not in respuesta.content.decode()


@pytest.mark.parametrize(
    "cambio",
    [{"correo": "no-es-un-correo"}, {"direccion": ""}, {"codigo_postal": ""}, {"provincia": ""}],
)
def test_CO090_E1_un_dato_ausente_o_invalido_se_resalta_y_se_conserva_lo_escrito(client, cambio):
    agregar(client, producto())

    respuesta = declarar(client, **cambio)

    formulario = respuesta.context["form"]
    campo = next(iter(cambio))
    assert respuesta.status_code == 200
    assert formulario.errors[campo]
    assert formulario.data["localidad"] == DATOS["localidad"]
    assert compra.CLAVE_INVITADO not in client.session


def test_CO090_E2_un_producto_sin_stock_vuelve_al_carrito(client):
    prod = producto(stock=1)
    agregar(client, prod)
    Producto.objects.filter(pk=prod.pk).update(stock=0, estado=Producto.AGOTADO)

    respuesta = declarar(client)

    assert respuesta.url == reverse("tienda:carrito")
    assert compra.CLAVE_INVITADO not in client.session


def test_CO090_A1_si_el_correo_es_de_una_cuenta_sugiere_iniciar_sesion(client):
    cliente_con_direccion(email="lector@correo.test")
    agregar(client, producto())
    declarar(client)

    respuesta = client.get(URL_INVITADO_RESUMEN)

    assert respuesta.context["tiene_cuenta"] is True
    assert "ya tiene una cuenta" in respuesta.content.decode()


# ===========================================================================
# CO-091 · confirmarPedidoDeInvitado
# ===========================================================================


def test_CO091_emite_la_solicitud_de_cobro_sin_cambios_en_el_dominio(client):
    prod = producto()
    agregar(client, prod)
    declarar(client)

    respuesta = client.post(URL_INVITADO_CONFIRMAR)

    cobro = CobroEnCurso.objects.get()
    assert respuesta.url == reverse("compra:pasarela_prueba", args=[cobro.referencia])
    assert cobro.correo_invitado == "lector@correo.test"
    assert cobro.usuario is None
    assert cobro.puntos_a_debitar == 0
    assert not Pedido.objects.exists()
    assert Producto.objects.get(pk=prod.pk).stock == 5


def test_CO091_sin_datos_declarados_vuelve_al_formulario(client):
    agregar(client, producto())

    respuesta = client.post(URL_INVITADO_CONFIRMAR)

    assert respuesta.url == URL_INVITADO
    assert not CobroEnCurso.objects.exists()


# ===========================================================================
# CO-089 · rama de invitado
# ===========================================================================


def test_CO089_invitado_el_pedido_queda_asociado_al_correo_y_no_a_un_usuario(client):
    agregar(client, producto())

    comprar_como_invitado(client)

    pedido = Pedido.objects.get()
    assert pedido.usuario is None
    assert pedido.correo_invitado == "lector@correo.test"
    assert pedido.estado == Pedido.PENDIENTE_ARMADO
    assert pedido.envio_localidad == "Posadas"
    assert TransaccionPago.objects.get().pedido == pedido


def test_CO089_invitado_no_se_acreditan_ni_debitan_puntos(client):
    agregar(client, producto())

    comprar_como_invitado(client)

    assert not LotePuntos.objects.exists()
    assert not MovimientoPuntos.objects.exists()


def test_CO089_invitado_el_stock_baja_y_el_carrito_de_sesion_se_vacia(client):
    prod = producto(stock=2)
    agregar(client, prod, 2)

    comprar_como_invitado(client)

    assert Producto.objects.get(pk=prod.pk).estado == Producto.AGOTADO
    assert not LineaCarrito.objects.exists()


def test_CO089_invitado_la_confirmacion_va_al_correo_declarado(
    client, django_capture_on_commit_callbacks
):
    agregar(client, producto())

    with django_capture_on_commit_callbacks(execute=True):
        comprar_como_invitado(client)

    assert mail.outbox[0].to == ["lector@correo.test"]
    assert "te vamos a avisar a este correo" in mail.outbox[0].body


def test_CO089_invitado_queda_en_la_auditoria_con_su_correo(client):
    agregar(client, producto())

    comprar_como_invitado(client)

    registro = RegistroAuditoria.objects.get(accion=RegistroAuditoria.COMPRA_ONLINE)
    assert registro.actor is None
    assert registro.actor_email == "lector@correo.test"


def test_CO089_invitado_E3_rechazo_conserva_los_datos_del_formulario(client):
    prod = producto()
    agregar(client, prod)

    cobro = comprar_como_invitado(client, aprobado=False)

    assert cobro.estado == CobroEnCurso.RECHAZADO
    assert Producto.objects.get(pk=prod.pk).stock == 5
    assert not Pedido.objects.exists()
    respuesta = client.get(reverse("compra:resultado", args=[cobro.referencia]))
    assert URL_INVITADO_RESUMEN in respuesta.content.decode()
    assert client.session[compra.CLAVE_INVITADO]["correo"] == "lector@correo.test"
