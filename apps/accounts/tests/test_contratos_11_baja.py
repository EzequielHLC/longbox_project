"""Pruebas de contrato de CU-CLI-BAJ: `CO-112`, `CO-113` y `CO-156` (plan 11, tercera parte).

Cada postcondición por la dirección real, con el Cliente. Las tres negativas
explícitas de `CO-113` —los pedidos activos, el historial y el correo— tienen su
propia prueba, porque son las que se rompen sin que nadie lo note.
"""

from datetime import timedelta
from unittest.mock import patch

import pytest
from django.db import DatabaseError
from django.urls import reverse
from django.utils import timezone

from apps.accounts import baja_cliente
from apps.accounts.models import Usuario
from apps.accounts.tests.factories import PASSWORD_DE_PRUEBA, UsuarioFactory
from apps.almacen.models import ArticuloRetenido
from apps.almacen.tests.util import retenido
from apps.catalog.models import Producto
from apps.catalog.tests.factories import ProductoFactory
from apps.core.models import RegistroAuditoria
from apps.pedidos import servicios as pedidos
from apps.pedidos.models import LineaPedido, Pedido
from apps.pedidos.tests.util import crear_pedido
from apps.puntos import servicios as puntos
from apps.puntos.models import LotePuntos, MovimientoPuntos
from apps.restock.models import SuscripcionReposicion
from apps.tienda.models import Carrito, LineaCarrito

pytestmark = pytest.mark.django_db

URL = reverse("cuenta:baja")


@pytest.fixture
def lector(client):
    usuario = UsuarioFactory(rol="cliente", email="lector@correo.test")
    client.force_login(usuario)
    return usuario


def lote(usuario, cantidad):
    return LotePuntos.objects.create(
        usuario=usuario,
        cantidad_acreditada=cantidad,
        disponible=cantidad,
        origen=LotePuntos.COMPRA,
        caduca_el=timezone.localdate() + timedelta(days=200),
    )


def confirmar(client, contrasena=PASSWORD_DE_PRUEBA):
    return client.post(URL, {"contrasena": contrasena})


def auditorias():
    return RegistroAuditoria.objects.filter(accion=RegistroAuditoria.BAJA_CUENTA_CLIENTE)


@pytest.fixture
def con_todo(lector):
    """Algo en cada una de las cuatro categorías del informe."""
    lote(lector, 120)
    lote(lector, 30)
    agotado = ProductoFactory(stock=0, estado=Producto.AGOTADO)
    SuscripcionReposicion.objects.create(usuario=lector, producto=agotado)
    carrito = Carrito.objects.create(usuario=lector, persistencia=Carrito.PERSISTENTE)
    producto = ProductoFactory(stock=3)
    LineaCarrito.objects.create(
        carrito=carrito,
        producto=producto,
        cantidad=1,
        precio_vigente=producto.precio,
        precio_visto=producto.precio,
    )
    pedido = crear_pedido(lector, estado=Pedido.PENDIENTE_ARMADO)
    return {"pedido": pedido, "carrito": carrito}


# ---------------------------------------------------------------------------
# CO-112 · solicitarBajaDeCuentaPropia
# ---------------------------------------------------------------------------


def test_CO112_el_informe_trae_las_cuatro_categorias_y_el_aviso(client, lector, con_todo):
    respuesta = client.get(URL)

    implicaciones = respuesta.context["implicaciones"]
    assert implicaciones.puntos == 150
    assert implicaciones.equivalencia > 0
    assert implicaciones.pedidos_activos == 1
    assert implicaciones.suscripciones == 1
    assert implicaciones.lineas_carrito == 1
    contenido = respuesta.content.decode()
    assert "Es permanente" in contenido
    assert 'name="contrasena"' in contenido


def test_CO112_pedir_el_informe_no_modifica_nada(client, lector, con_todo):
    client.get(URL)

    lector.refresh_from_db()
    assert lector.estado == Usuario.ACTIVO
    assert puntos.saldo(lector) == 150
    assert LineaCarrito.objects.count() == 1
    assert not auditorias().exists()


@pytest.mark.parametrize(
    "estado", [ArticuloRetenido.DISPONIBLE, ArticuloRetenido.PENDIENTE_DESPACHO]
)
def test_CO112_E1_un_retenido_bloquea_y_dice_que_hacer(client, lector, estado):
    retenido(lector, estado=estado)

    respuesta = client.get(URL)

    contenido = respuesta.content.decode()
    assert baja_cliente.MENSAJE_RETENIDOS in contenido
    assert reverse("cuenta:stock") in contenido
    assert 'name="contrasena"' not in contenido


def test_CO112_E2_una_decision_de_demora_pendiente_bloquea(client, lector):
    pedido = crear_pedido(lector, estado=Pedido.ESPERANDO_DEMORADO)
    pedido.lineas.update(estado=LineaPedido.ESPERANDO_DEMORADO, decision_demora="")

    contenido = client.get(URL).content.decode()

    assert baja_cliente.MENSAJE_DEMORADOS in contenido
    assert 'name="contrasena"' not in contenido


def test_CO112_E1_E2_tambien_los_exige_la_confirmacion(client, lector):
    """El bloqueo vive en el servidor: un POST armado a mano no lo saltea."""
    retenido(lector)

    confirmar(client)

    lector.refresh_from_db()
    assert lector.estado == Usuario.ACTIVO
    assert not auditorias().exists()


# ---------------------------------------------------------------------------
# CO-113 · confirmarBajaDeCuentaPropia
# ---------------------------------------------------------------------------


def test_CO113_la_cuenta_pasa_a_inactiva_y_vuelve_al_ingreso(client, lector):
    respuesta = confirmar(client, PASSWORD_DE_PRUEBA)

    lector.refresh_from_db()
    assert lector.estado == Usuario.INACTIVO
    assert lector.is_active is False
    assert respuesta.url == reverse("accounts:login")
    seguida = client.get(respuesta.url)
    assert baja_cliente.MENSAJE_DESACTIVADA in seguida.content.decode()


def test_CO113_se_cierran_las_sesiones_en_todos_los_dispositivos(client, lector):
    from django.test import Client

    otro_dispositivo = Client()
    otro_dispositivo.force_login(lector)

    confirmar(client)

    assert "_auth_user_id" not in client.session
    assert otro_dispositivo.get(reverse("cuenta:panel")).status_code == 302


def test_CO113_los_puntos_quedan_en_cero_y_vencidos_con_su_debito(client, lector, con_todo):
    confirmar(client)

    lotes = LotePuntos.objects.filter(usuario=lector)
    assert all(x.disponible == 0 and x.estado == LotePuntos.VENCIDO for x in lotes)
    assert puntos.saldo(lector) == 0
    debitos = MovimientoPuntos.objects.filter(
        usuario=lector, tipo=MovimientoPuntos.DEBITO, motivo=baja_cliente.MOTIVO_PUNTOS
    )
    assert sorted(d.cantidad for d in debitos) == [30, 120]


def test_CO113_se_eliminan_las_suscripciones_y_las_lineas_del_carrito(client, lector, con_todo):
    confirmar(client)

    assert not SuscripcionReposicion.objects.filter(usuario=lector).exists()
    assert not LineaCarrito.objects.filter(carrito=con_todo["carrito"]).exists()


def test_CO113_los_pedidos_activos_no_se_modifican_y_siguen_avisando(
    client, lector, con_todo, administrador, mailoutbox, django_capture_on_commit_callbacks
):
    """Postcondición negativa: el pedido sigue su ciclo y se notifica al correo
    que se conserva."""
    pedido = con_todo["pedido"]
    antes = (pedido.estado, list(pedido.lineas.values_list("estado", "cantidad")))

    confirmar(client)

    pedido.refresh_from_db()
    assert (pedido.estado, list(pedido.lineas.values_list("estado", "cantidad"))) == antes
    mailoutbox.clear()
    with django_capture_on_commit_callbacks(execute=True):
        pedidos.avanzar(pedido, administrador, estado_visto=pedido.estado)
    assert any("lector@correo.test" in correo.to for correo in mailoutbox)


def test_CO113_el_historial_y_el_correo_se_conservan(client, lector, con_todo):
    """Las otras dos negativas: nada se borra del historial y el correo queda."""
    acreditaciones = MovimientoPuntos.objects.filter(usuario=lector).count()

    confirmar(client)

    lector.refresh_from_db()
    assert lector.email == "lector@correo.test"
    assert Pedido.objects.filter(usuario=lector).count() == 1
    assert LotePuntos.objects.filter(usuario=lector).count() == 2
    assert MovimientoPuntos.objects.filter(usuario=lector).count() == acreditaciones + 2


def test_CO113_la_entrada_trae_puntos_suscripciones_y_pedidos(client, lector, con_todo):
    confirmar(client)

    registro = auditorias().get()
    assert registro.actor == lector
    assert "puntos invalidados: 150" in registro.detalle
    assert "suscripciones canceladas: 1" in registro.detalle
    assert "Administrador: 1" in registro.detalle


def test_CO113_manda_la_confirmacion_al_correo(
    client, lector, con_todo, mailoutbox, django_capture_on_commit_callbacks
):
    with django_capture_on_commit_callbacks(execute=True):
        confirmar(client)

    correo = next(c for c in mailoutbox if "desactivada" in c.subject)
    assert correo.to == ["lector@correo.test"]
    assert "siguen su camino" in correo.body


def test_CO113_el_correo_no_se_puede_volver_a_registrar(client, lector):
    confirmar(client)

    client.post(
        reverse("accounts:registro_cliente"),
        {
            "nombre_completo": "Otra Persona",
            "email": "lector@correo.test",
            "password1": "ComicRojo2026",
            "password2": "ComicRojo2026",
            "acepta_politica": "on",
        },
    )

    assert Usuario.objects.filter(email__iexact="lector@correo.test").count() == 1


def test_CO113_E3_una_contrasena_equivocada_no_avanza_y_no_revela_nada(client, lector):
    respuesta = confirmar(client, "otra-cosa")

    lector.refresh_from_db()
    assert lector.estado == Usuario.ACTIVO
    assert respuesta.context["form"].errors["contrasena"] == [baja_cliente.MENSAJE_CONTRASENA]


def test_CO113_E3_tres_intentos_bloquean_la_baja_y_no_el_ingreso(client, lector):
    for _ in range(3):
        confirmar(client, "otra-cosa")

    respuesta = confirmar(client, PASSWORD_DE_PRUEBA)

    lector.refresh_from_db()
    assert lector.estado == Usuario.ACTIVO
    assert "tres intentos fallidos" in respuesta.content.decode()
    # El inicio de sesión no comparte el contador.
    client.logout()
    ingreso = client.post(
        reverse("accounts:login"),
        {"username": lector.email, "password": PASSWORD_DE_PRUEBA},
    )
    assert ingreso.status_code == 302


def test_CO113_E4_un_fallo_tecnico_revierte_todo(client, lector, con_todo):
    with patch(
        "apps.accounts.baja_cliente.LineaCarrito.objects.filter",
        side_effect=DatabaseError("caída"),
    ):
        respuesta = confirmar(client)

    lector.refresh_from_db()
    assert respuesta.status_code == 302
    assert lector.estado == Usuario.ACTIVO
    assert puntos.saldo(lector) == 150
    assert SuscripcionReposicion.objects.filter(usuario=lector).exists()
    assert not auditorias().exists()


# ---------------------------------------------------------------------------
# CO-156 · cancelarOperacion, y el acceso
# ---------------------------------------------------------------------------


def test_CO156_abandonar_la_baja_no_cambia_nada(client, lector, con_todo):
    contenido = client.get(URL).content.decode()

    assert reverse("cuenta:datos") in contenido
    client.get(reverse("cuenta:datos"))
    lector.refresh_from_db()
    assert lector.estado == Usuario.ACTIVO
    assert puntos.saldo(lector) == 150


@pytest.mark.parametrize("rol", ["cajero", "administrador"])
def test_CO112_CO113_el_personal_no_entra(client, rol):
    usuario = UsuarioFactory(rol=rol)
    client.force_login(usuario)

    assert client.get(URL).status_code == 403
    assert confirmar(client).status_code == 403
    usuario.refresh_from_db()
    assert usuario.estado == Usuario.ACTIVO


def test_CO112_sin_sesion_va_al_ingreso(client):
    assert client.get(URL).status_code == 302


# ---------------------------------------------------------------------------
# CO-124 · la vuelta de la baja: el Administrador reactiva al Cliente (B-11-009)
# ---------------------------------------------------------------------------


def url_reactivar(cliente):
    return reverse("accounts:cliente_reactivar", args=[cliente.pk])


@pytest.fixture
def dado_de_baja(db):
    """Un Cliente que se dio de baja con puntos y un pedido. Se arma por el
    servicio y no por el navegador: `client_admin` usa el mismo."""
    cliente = UsuarioFactory(rol="cliente", email="lector@correo.test")
    lote(cliente, 120)
    lote(cliente, 30)
    crear_pedido(cliente, estado=Pedido.PENDIENTE_ARMADO)
    baja_cliente.confirmar(cliente)
    cliente.refresh_from_db()
    return cliente


def test_CO124_el_cliente_vuelve_a_pendiente_con_un_enlace_nuevo(
    client_admin, administrador, dado_de_baja, mailoutbox
):
    from apps.accounts.models import EnlaceActivacion

    mailoutbox.clear()

    client_admin.post(url_reactivar(dado_de_baja))

    dado_de_baja.refresh_from_db()
    assert dado_de_baja.estado == Usuario.PENDIENTE_ACTIVACION
    assert dado_de_baja.rol == Usuario.CLIENTE
    assert not dado_de_baja.has_usable_password()
    assert EnlaceActivacion.objects.filter(
        usuario=dado_de_baja, estado=EnlaceActivacion.VIGENTE
    ).exists()
    assert [correo.to for correo in mailoutbox] == [["lector@correo.test"]]
    assert "reactivada" in mailoutbox[0].body
    registro = RegistroAuditoria.objects.get(
        accion=RegistroAuditoria.REACTIVACION_USUARIO, objetivo_pk=dado_de_baja.pk
    )
    assert registro.actor == administrador


def test_CO124_los_puntos_y_el_historial_no_vuelven_ni_se_pierden(client_admin, dado_de_baja):
    """CO-113: los puntos se perdieron sin recuperación; los datos nunca se eliminan."""
    client_admin.post(url_reactivar(dado_de_baja))

    assert puntos.saldo(dado_de_baja) == 0
    assert Pedido.objects.filter(usuario=dado_de_baja).count() == 1
    assert MovimientoPuntos.objects.filter(usuario=dado_de_baja).count() == 2


def test_CO124_la_ficha_ofrece_reactivar_solo_si_esta_dado_de_baja(client_admin, dado_de_baja):
    otro = UsuarioFactory(rol="cliente")

    con_baja = client_admin.get(reverse("accounts:cliente_ficha", args=[dado_de_baja.pk]))
    activo = client_admin.get(reverse("accounts:cliente_ficha", args=[otro.pk]))

    assert url_reactivar(dado_de_baja) in con_baja.content.decode()
    assert url_reactivar(otro) not in activo.content.decode()


def test_CO124_un_cliente_activo_no_se_reactiva(client_admin):
    activo = UsuarioFactory(rol="cliente")

    client_admin.post(url_reactivar(activo))

    activo.refresh_from_db()
    assert activo.estado == Usuario.ACTIVO
    assert not RegistroAuditoria.objects.filter(
        accion=RegistroAuditoria.REACTIVACION_USUARIO
    ).exists()


@pytest.mark.parametrize("rol", ["cajero", "cliente"])
def test_CO124_otro_rol_no_reactiva_un_cliente(client, rol):
    cliente = UsuarioFactory(rol="cliente", estado=Usuario.INACTIVO)
    client.force_login(UsuarioFactory(rol=rol))

    assert client.post(url_reactivar(cliente)).status_code == 403
    cliente.refresh_from_db()
    assert cliente.estado == Usuario.INACTIVO


# ---------------------------------------------------------------------------
# CO-123 · la baja lógica de un Cliente desde la administración (B-11-010)
# ---------------------------------------------------------------------------


def url_baja_admin(cliente):
    return reverse("accounts:cliente_baja", args=[cliente.pk])


def test_CO123_el_administrador_da_de_baja_un_cliente_sin_quitarle_nada(
    client_admin, administrador
):
    cliente = UsuarioFactory(rol="cliente")
    lote(cliente, 120)
    crear_pedido(cliente, estado=Pedido.PENDIENTE_ARMADO)
    SuscripcionReposicion.objects.create(
        usuario=cliente, producto=ProductoFactory(stock=0, estado=Producto.AGOTADO)
    )

    client_admin.post(url_baja_admin(cliente))

    cliente.refresh_from_db()
    assert cliente.estado == Usuario.INACTIVO
    assert puntos.saldo(cliente) == 120
    assert SuscripcionReposicion.objects.filter(usuario=cliente).exists()
    assert Pedido.objects.get(usuario=cliente).estado == Pedido.PENDIENTE_ARMADO
    registro = RegistroAuditoria.objects.get(
        accion=RegistroAuditoria.BAJA_USUARIO, objetivo_pk=cliente.pk
    )
    assert registro.actor == administrador


def test_CO123_la_baja_cierra_las_sesiones_del_cliente(client_admin):
    from django.test import Client

    cliente = UsuarioFactory(rol="cliente")
    navegador = Client()
    navegador.force_login(cliente)

    client_admin.post(url_baja_admin(cliente))

    assert navegador.get(reverse("cuenta:panel")).status_code == 302


def test_CO123_la_ficha_ofrece_dar_de_baja_y_despues_reactivar(client_admin):
    cliente = UsuarioFactory(rol="cliente")
    ficha = reverse("accounts:cliente_ficha", args=[cliente.pk])

    assert url_baja_admin(cliente) in client_admin.get(ficha).content.decode()
    client_admin.post(url_baja_admin(cliente))
    contenido = client_admin.get(ficha).content.decode()

    assert url_baja_admin(cliente) not in contenido
    assert reverse("accounts:cliente_reactivar", args=[cliente.pk]) in contenido


def test_CO123_reactivar_tras_la_baja_del_administrador_devuelve_sus_puntos(client_admin):
    cliente = UsuarioFactory(rol="cliente")
    lote(cliente, 120)
    client_admin.post(url_baja_admin(cliente))

    client_admin.post(reverse("accounts:cliente_reactivar", args=[cliente.pk]))

    cliente.refresh_from_db()
    assert cliente.estado == Usuario.PENDIENTE_ACTIVACION
    assert puntos.saldo(cliente) == 120


@pytest.mark.parametrize("rol", ["cajero", "cliente"])
def test_CO123_otro_rol_no_da_de_baja_un_cliente(client, rol):
    cliente = UsuarioFactory(rol="cliente")
    client.force_login(UsuarioFactory(rol=rol))

    assert client.post(url_baja_admin(cliente)).status_code == 403
    cliente.refresh_from_db()
    assert cliente.estado == Usuario.ACTIVO
