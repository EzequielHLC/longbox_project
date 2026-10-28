"""Pruebas de contrato del carrito (módulo 07, plan 07 segunda parte).

`CO-083` agregar, `CO-084` modificar, `CO-085` quitar, `CO-178` consultar y
`CO-086` fusionar, más la parte de `CO-048` y `CO-053` que llega a las líneas.
Todas por la dirección real, como las usa el Cliente o el invitado.

Postcondiciones negativas que se miran: la consulta no cambia nada, el carrito
no toca el stock ni el precio del producto, y nada de esto se audita.
"""

from datetime import timedelta
from decimal import Decimal

import pytest
from django.urls import reverse
from django.utils import timezone
from freezegun import freeze_time

from apps.accounts.tests.factories import PASSWORD_DE_PRUEBA
from apps.catalog import tabla_de_precios
from apps.catalog.models import Producto
from apps.catalog.tests.factories import PrecioReferenciaFactory, ProductoFactory
from apps.catalog.tests.test_contratos_03_pricing import fijar_margen, importado, vinculado
from apps.core.models import ConfiguracionSistema, RegistroAuditoria
from apps.tienda.carrito import CLAVE_DE_SESION
from apps.tienda.models import Carrito, LineaCarrito

pytestmark = pytest.mark.django_db

URL_CARRITO = reverse("tienda:carrito")
# Relativo a la hora real, nunca una fecha fija: la sesión que se abre con el reloj
# congelado vence a los 30 minutos (SESSION_COOKIE_AGE) y se lee después con el
# reloj real. Con una fecha fija la prueba empezaba a fallar al día siguiente.
MOMENTO = timezone.now().replace(microsecond=0) - timedelta(minutes=5)
# La operación ocurre un minuto después de armar el carrito. El reloj se congela
# desde el principio: congelarlo a mitad de la prueba dejaría vencida la sesión
# que se abrió con el reloj real.
DESPUES = MOMENTO + timedelta(minutes=1)


def agregar(client, producto, cantidad=1, **extra):
    return client.post(
        reverse("tienda:agregar", args=[producto.pk]), {"cantidad": cantidad, **extra}
    )


def cambiar(client, linea, cantidad):
    return client.post(reverse("tienda:cantidad", args=[linea.pk]), {"cantidad": cantidad})


def quitar(client, linea):
    return client.post(reverse("tienda:quitar", args=[linea.pk]))


def mensajes(respuesta):
    return [str(m) for m in respuesta.context["messages"]] if respuesta.context else []


@pytest.fixture
def disponible(db):
    return ProductoFactory(titulo="Akira", stock=5, precio=Decimal("18500"))


@pytest.fixture
def en_pre_venta(db):
    return ProductoFactory(titulo="Berserk 42", estado=Producto.PRE_VENTA, stock=0)


@pytest.fixture
def client_cliente(client, cliente):
    client.force_login(cliente)
    return client


# ===========================================================================
# CO-083 · agregarProductoAlCarrito
# ===========================================================================


def test_CO083_el_invitado_crea_un_carrito_de_sesion_con_la_linea(client, disponible):
    with freeze_time(MOMENTO):
        respuesta = agregar(client, disponible, 2)

    assert respuesta.status_code == 302
    carrito = Carrito.objects.get()
    assert carrito.persistencia == Carrito.DE_SESION
    assert carrito.usuario is None
    assert client.session[CLAVE_DE_SESION] == carrito.pk
    assert carrito.actualizado_en == MOMENTO
    linea = carrito.lineas.get()
    assert linea.producto_id == disponible.pk
    assert linea.cantidad == 2
    assert linea.precio_vigente == Decimal("18500")


def test_CO083_el_cliente_crea_un_carrito_persistente_asociado_a_su_cuenta(
    client_cliente, cliente, disponible
):
    agregar(client_cliente, disponible)

    carrito = Carrito.objects.get()
    assert carrito.persistencia == Carrito.PERSISTENTE
    assert carrito.usuario == cliente


def test_CO083_si_ya_estaba_suma_a_la_misma_linea(client, disponible):
    agregar(client, disponible, 1)
    agregar(client, disponible, 2)

    assert LineaCarrito.objects.get().cantidad == 3


def test_CO083_E1_la_cantidad_no_pasa_del_stock_y_se_informa_el_maximo(client, disponible):
    agregar(client, disponible, 4)
    respuesta = agregar(client, disponible, 4, volver="")
    respuesta = client.get(respuesta.url)

    assert LineaCarrito.objects.get().cantidad == 5
    assert "Hay 5 disponibles de «Akira»: el carrito quedó con 5." in mensajes(respuesta)


def test_CO083_A1_la_pre_venta_se_reserva_sin_mirar_el_stock(client, en_pre_venta):
    """Sin stock (cero) y hasta el máximo por reserva: el stock no la limita."""
    agregar(client, en_pre_venta, 4)

    assert LineaCarrito.objects.get().cantidad == 4


def test_CO083_A1_la_reserva_queda_en_el_maximo_por_cliente_y_se_avisa(client, en_pre_venta):
    """Plan 00 de tope de reservas: el máximo por reserva de Parámetros (5)."""
    respuesta = agregar(client, en_pre_venta, 30)

    assert LineaCarrito.objects.get().cantidad == 5
    assert "hasta 5 unidades" in mensajes(client.get(respuesta.url))[0]


@pytest.mark.parametrize("cantidad", ["0", "-2", "dos"])
def test_CO083_rechaza_una_cantidad_que_no_es_al_menos_uno(client, disponible, cantidad):
    agregar(client, disponible, cantidad)

    assert not LineaCarrito.objects.exists()


def test_CO083_un_producto_sin_stock_no_se_agrega(client):
    sin_stock = ProductoFactory(stock=0)
    agotado = ProductoFactory(estado=Producto.AGOTADO, stock=0)

    agregar(client, sin_stock)
    agregar(client, agotado)

    assert not LineaCarrito.objects.exists()


def test_CO083_un_producto_fuera_de_la_tienda_responde_404(client):
    descatalogado = ProductoFactory(estado=Producto.DESCATALOGADO, stock=3)

    assert agregar(client, descatalogado).status_code == 404


def test_CO083_no_toca_el_producto_ni_se_audita(client, disponible):
    agregar(client, disponible, 3)

    disponible.refresh_from_db()
    assert disponible.stock == 5
    assert disponible.precio == Decimal("18500")
    assert not RegistroAuditoria.objects.exists()


def test_CO083_volver_a_una_direccion_externa_se_ignora(client, disponible):
    respuesta = agregar(client, disponible, volver="https://otro.test/robo")

    assert respuesta.url == URL_CARRITO


# ===========================================================================
# CO-084 · modificarCantidadDeLinea
# ===========================================================================


def test_CO084_la_linea_queda_con_la_cantidad_declarada(client, disponible):
    with freeze_time(MOMENTO) as reloj:
        agregar(client, disponible, 1)
        linea = LineaCarrito.objects.get()
        reloj.move_to(DESPUES)

        cambiar(client, linea, 4)

    linea.refresh_from_db()
    assert linea.cantidad == 4
    assert linea.carrito.actualizado_en == DESPUES


def test_CO084_E1_no_pasa_del_stock(client, disponible):
    agregar(client, disponible, 1)
    linea = LineaCarrito.objects.get()

    respuesta = client.get(cambiar(client, linea, 9).url)

    linea.refresh_from_db()
    assert linea.cantidad == 5
    assert "Hay 5 disponibles de «Akira»: la línea quedó con 5." in mensajes(respuesta)


def test_CO084_E2_menos_de_uno_se_rechaza_y_la_linea_no_cambia(client, disponible):
    agregar(client, disponible, 2)
    linea = LineaCarrito.objects.get()

    cambiar(client, linea, 0)

    linea.refresh_from_db()
    assert linea.cantidad == 2


def test_CO084_A1_en_pre_venta_el_tope_es_el_maximo_por_reserva(client, en_pre_venta):
    agregar(client, en_pre_venta, 1)

    cambiar(client, LineaCarrito.objects.get(), 12)

    assert LineaCarrito.objects.get().cantidad == 5


def test_CO084_A1_el_maximo_sale_de_parametros(client, en_pre_venta):
    configuracion = ConfiguracionSistema.obtener()
    configuracion.maximo_reserva_preventa = 12
    configuracion.save()
    agregar(client, en_pre_venta, 1)

    cambiar(client, LineaCarrito.objects.get(), 12)

    assert LineaCarrito.objects.get().cantidad == 12


def test_CO084_la_linea_de_otro_carrito_responde_404(client, disponible, django_user_model):
    ajeno = Carrito.objects.create()
    linea_ajena = LineaCarrito.objects.create(
        carrito=ajeno, producto=disponible, cantidad=1, precio_vigente=1, precio_visto=1
    )
    agregar(client, disponible)

    assert cambiar(client, linea_ajena, 3).status_code == 404
    linea_ajena.refresh_from_db()
    assert linea_ajena.cantidad == 1


# ===========================================================================
# CO-085 · eliminarLineaDelCarrito
# ===========================================================================


def test_CO085_la_linea_deja_de_existir_y_el_producto_sigue_igual(client, disponible):
    with freeze_time(MOMENTO) as reloj:
        agregar(client, disponible, 2)
        linea = LineaCarrito.objects.get()
        reloj.move_to(DESPUES)

        quitar(client, linea)

    assert not LineaCarrito.objects.exists()
    assert Carrito.objects.get().actualizado_en == DESPUES
    disponible.refresh_from_db()
    assert disponible.stock == 5


def test_CO085_la_linea_de_otro_carrito_responde_404(client, disponible):
    ajeno = Carrito.objects.create()
    linea_ajena = LineaCarrito.objects.create(
        carrito=ajeno, producto=disponible, cantidad=1, precio_vigente=1, precio_visto=1
    )

    assert quitar(client, linea_ajena).status_code == 404
    assert LineaCarrito.objects.filter(pk=linea_ajena.pk).exists()


# ===========================================================================
# CO-178 · consultarCarrito
# ===========================================================================


def test_CO178_presenta_las_lineas_con_precio_subtotal_y_total(client, disponible, en_pre_venta):
    agregar(client, disponible, 2)
    agregar(client, en_pre_venta, 1)

    contenido = client.get(URL_CARRITO).content.decode()

    assert "Akira" in contenido
    assert "Berserk 42" in contenido
    assert "$ 37.000" in contenido
    assert "Pre-venta" in contenido


def test_CO178_A1_el_carrito_vacio_ofrece_el_catalogo(client):
    contenido = client.get(URL_CARRITO).content.decode()

    assert "Tu carrito está vacío." in contenido
    assert reverse("core:tienda_catalogo") in contenido


def test_CO178_A3_y_A4_la_disponibilidad_se_deriva_del_producto(client, disponible):
    otro = ProductoFactory(titulo="Monster", stock=4)
    agregar(client, disponible, 3)
    agregar(client, otro, 2)
    Producto.objects.filter(pk=disponible.pk).update(stock=1)
    Producto.objects.filter(pk=otro.pk).update(estado=Producto.DESCATALOGADO)

    respuesta = client.get(URL_CARRITO)
    contenido = respuesta.content.decode()

    assert "Stock insuficiente · máximo 1" in contenido
    assert "Producto no disponible" in contenido
    assert not respuesta.context["carrito"].se_puede_pagar


def test_CO178_A4_la_pre_venta_figura_siempre_disponible(client, en_pre_venta):
    agregar(client, en_pre_venta, 40)

    assert client.get(URL_CARRITO).context["carrito"].se_puede_pagar


def test_CO178_la_consulta_no_modifica_nada(client, disponible):
    agregar(client, disponible, 2)
    Producto.objects.filter(pk=disponible.pk).update(precio=Decimal("20000"))
    antes = list(LineaCarrito.objects.values())
    carrito_antes = list(Carrito.objects.values())

    client.get(URL_CARRITO)

    assert list(LineaCarrito.objects.values()) == antes
    assert list(Carrito.objects.values()) == carrito_antes


# ===========================================================================
# CO-048 y CO-053 · la propagación llega a las líneas (B-03-001)
# ===========================================================================


def test_CO048_confirmar_modificacion_actualiza_las_lineas_y_el_carrito_avisa(
    client, administrador
):
    fila = PrecioReferenciaFactory(pvp=Decimal("10000"))
    producto = vinculado(fila, stock=3)
    agregar(client, producto)

    tabla_de_precios.confirmar_modificacion(fila, Decimal("12000"), actor=administrador)

    linea = LineaCarrito.objects.get()
    assert linea.precio_vigente == Decimal("12000")
    assert linea.precio_visto == Decimal("10000")
    contenido = client.get(URL_CARRITO).content.decode()
    assert "El precio de este producto ha cambiado" in contenido
    assert "antes $ 10.000" in contenido


def test_CO048_no_toca_las_lineas_de_otros_productos(client, administrador, disponible):
    fila = PrecioReferenciaFactory(pvp=Decimal("10000"))
    agregar(client, disponible)

    tabla_de_precios.confirmar_modificacion(fila, Decimal("12000"), actor=administrador)

    assert LineaCarrito.objects.get().precio_vigente == Decimal("18500")


def test_CO053_confirmar_cambio_de_margen_actualiza_las_lineas(client, administrador):
    fijar_margen("0.40")
    producto = importado("10000", stock=2)
    agregar(client, producto)

    tabla_de_precios.confirmar_cambio_de_margen(Decimal("0.50"), actor=administrador)

    assert LineaCarrito.objects.get().precio_vigente == Decimal("15000")


def test_cambiar_la_cantidad_apaga_el_aviso_de_precio(client, administrador):
    fila = PrecioReferenciaFactory(pvp=Decimal("10000"))
    producto = vinculado(fila, stock=3)
    agregar(client, producto)
    tabla_de_precios.confirmar_modificacion(fila, Decimal("12000"), actor=administrador)

    cambiar(client, LineaCarrito.objects.get(), 2)

    assert LineaCarrito.objects.get().precio_visto == Decimal("12000")
    assert "ha cambiado" not in client.get(URL_CARRITO).content.decode()


# ===========================================================================
# CO-086 · fusionarCarritoDeSesion
# ===========================================================================


def iniciar_sesion(client, usuario):
    return client.post(
        reverse("accounts:login"), {"username": usuario.email, "password": PASSWORD_DE_PRUEBA}
    )


def test_CO086_sin_carrito_propio_el_de_sesion_pasa_a_la_cuenta(client, cliente, disponible):
    with freeze_time(MOMENTO) as reloj:
        agregar(client, disponible, 2)
        de_sesion = Carrito.objects.get()
        reloj.move_to(DESPUES)

        iniciar_sesion(client, cliente)

    de_sesion.refresh_from_db()
    assert de_sesion.usuario == cliente
    assert de_sesion.persistencia == Carrito.PERSISTENTE
    assert de_sesion.actualizado_en == DESPUES
    assert de_sesion.lineas.get().cantidad == 2
    assert CLAVE_DE_SESION not in client.session


def test_CO086_con_carrito_propio_suma_con_tope_y_elimina_el_de_sesion(
    client, cliente, disponible, en_pre_venta
):
    solo_en_sesion = ProductoFactory(titulo="Monster", stock=9)
    persistido = Carrito.objects.create(usuario=cliente, persistencia=Carrito.PERSISTENTE)
    LineaCarrito.objects.create(
        carrito=persistido, producto=disponible, cantidad=4, precio_vigente=1, precio_visto=1
    )
    LineaCarrito.objects.create(
        carrito=persistido, producto=en_pre_venta, cantidad=3, precio_vigente=1, precio_visto=1
    )
    agregar(client, disponible, 3)
    agregar(client, en_pre_venta, 5)
    agregar(client, solo_en_sesion, 1)
    de_sesion = Carrito.objects.get(usuario__isnull=True)

    iniciar_sesion(client, cliente)

    assert not Carrito.objects.filter(pk=de_sesion.pk).exists()
    cantidades = dict(persistido.lineas.values_list("producto__titulo", "cantidad"))
    # 4 + 3 = 7 con tope en el stock de 5; la pre-venta, 3 + 5 = 8 con tope en el
    # máximo por reserva (5).
    assert cantidades == {"Akira": 5, "Berserk 42": 5, "Monster": 1}


def test_CO086_el_personal_que_inicia_sesion_descarta_el_carrito_de_invitado(
    client, cajero, disponible
):
    agregar(client, disponible)

    iniciar_sesion(client, cajero)

    assert not Carrito.objects.exists()


# ===========================================================================
# Control de acceso — por la dirección real, con el rol equivocado
# ===========================================================================


@pytest.mark.parametrize("rol", ["cajero", "administrador"])
def test_el_personal_no_tiene_carrito(client, request, rol, disponible):
    client.force_login(request.getfixturevalue(rol))
    linea = LineaCarrito.objects.create(
        carrito=Carrito.objects.create(),
        producto=disponible,
        cantidad=1,
        precio_vigente=1,
        precio_visto=1,
    )

    assert client.get(URL_CARRITO).status_code == 403
    assert agregar(client, disponible).status_code == 403
    assert cambiar(client, linea, 2).status_code == 403
    assert quitar(client, linea).status_code == 403
    ficha = client.get(reverse("core:tienda_producto", args=[disponible.pk])).content.decode()
    assert "La compra es para cuentas de cliente." in ficha


def test_la_ficha_ofrece_agregar_y_el_encabezado_cuenta_las_unidades(client, disponible):
    ficha = reverse("core:tienda_producto", args=[disponible.pk])
    assert reverse("tienda:agregar", args=[disponible.pk]) in client.get(ficha).content.decode()

    agregar(client, disponible, 3)
    contenido = client.get(ficha).content.decode()

    assert 'aria-label="3 unidades"' in contenido
    assert 'Tenés <span class="datos">3</span> en el carrito' in contenido
