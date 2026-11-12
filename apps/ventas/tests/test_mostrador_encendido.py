"""El mostrador encendido (plan 06, segunda parte): el Cajero ve el estilo de la
tienda y el Administrador sigue sobrio.

Lo que se verifica es que **cambie la forma y no lo que se puede hacer**: las
dos versiones ofrecen las mismas operaciones, contra las mismas direcciones.
"""

from decimal import Decimal

import pytest
from django.urls import reverse

from apps.caja.views import SEGMENTOS, _medidores
from apps.catalog.tests.factories import ProductoFactory
from apps.tienda.tests.compra_util import fijar_parametros

pytestmark = pytest.mark.django_db

MOSTRADOR = reverse("core:mostrador")
HOJA = "css/mostrador.css"


@pytest.fixture(autouse=True)
def parametros(db):
    return fijar_parametros()


@pytest.fixture
def caja(client, cajero):
    client.force_login(cajero)
    return client


def _plantillas(respuesta):
    return {plantilla.name for plantilla in respuesta.templates}


# ===========================================================================
# Por rol
# ===========================================================================


@pytest.mark.parametrize(
    "url, del_cajero, sobria",
    [
        (MOSTRADOR, "ventas/cajero/mostrador.html", "ventas/mostrador.html"),
        (reverse("caja:caja"), "caja/cajero/caja.html", "caja/caja.html"),
    ],
)
def test_el_cajero_ve_su_version_y_el_administrador_la_sobria(
    client, cajero, administrador, url, del_cajero, sobria
):
    client.force_login(cajero)
    del_cajero_resp = client.get(url)
    client.force_login(administrador)
    sobria_resp = client.get(url)

    assert del_cajero in _plantillas(del_cajero_resp)
    assert sobria not in _plantillas(del_cajero_resp)
    assert sobria in _plantillas(sobria_resp)
    assert del_cajero not in _plantillas(sobria_resp)


def test_la_hoja_y_la_barra_del_cajero_no_llegan_al_administrador(client, cajero, administrador):
    client.force_login(cajero)
    del_cajero = client.get(reverse("catalog:producto_lista")).content.decode()
    client.force_login(administrador)
    sobria = client.get(reverse("catalog:producto_lista")).content.decode()

    assert HOJA in del_cajero and "modo-cajero" in del_cajero and "caj-barra" in del_cajero
    assert 'id="menu-lateral"' not in del_cajero
    assert HOJA not in sobria and "modo-cajero" not in sobria and "caj-barra" not in sobria
    assert 'id="menu-lateral"' in sobria


@pytest.mark.parametrize(
    "url, destino",
    [
        (MOSTRADOR, "Mostrador"),
        (reverse("caja:caja"), "Caja"),
        (reverse("almacen:lista"), "Stock en local"),
        (reverse("catalog:producto_lista"), "Inventario"),
    ],
)
def test_la_barra_enciende_el_destino_actual(caja, url, destino):
    contenido = caja.get(url).content.decode()
    barra = contenido[contenido.index('class="caj-botonera"') :]
    barra = barra[: barra.index("</nav>")]

    encendido = barra[barra.index('aria-current="page"') :]
    assert f"<span>{destino}</span>" in encendido[: encendido.index("</a>")]
    assert barra.count('aria-current="page"') == 1


# ===========================================================================
# Las mismas operaciones
# ===========================================================================


def test_el_mostrador_del_cajero_ofrece_todas_las_operaciones(caja, cajero):
    producto = ProductoFactory(stock=5, precio=Decimal("10000"))
    caja.post(reverse("ventas:agregar"), {"producto": producto.pk, "cantidad": 1})

    contenido = caja.get(MOSTRADOR).content.decode()

    for accion in (
        reverse("ventas:agregar"),
        reverse("ventas:quitar", args=[producto.pk]),
        reverse("ventas:cliente"),
        reverse("ventas:confirmar"),
        reverse("ventas:nueva"),
    ):
        assert f'action="{accion}"' in contenido, accion
    # El lector de código de barras escribe donde está el foco.
    assert 'name="q"' in contenido and "autofocus" in contenido
    for medio in ("efectivo", "transferencia", "tarjeta"):
        assert f'name="medio" value="{medio}"' in contenido
    assert 'name="recibido"' in contenido and "data-total" in contenido
    assert "Cobrar $ 10.000" in contenido


def test_con_cliente_el_ticket_ofrece_el_canje(caja, cliente):
    producto = ProductoFactory(stock=5, precio=Decimal("10000"))
    caja.post(reverse("ventas:agregar"), {"producto": producto.pk, "cantidad": 1})
    caja.post(reverse("ventas:cliente"), {"cliente": cliente.codigo_cliente})

    contenido = caja.get(MOSTRADOR).content.decode()

    assert f'action="{reverse("ventas:canje", args=[producto.pk])}"' in contenido
    assert "caj-carnet" in contenido
    assert "Quitar cliente" in contenido


def test_el_ticket_vacio_no_deja_cobrar(caja):
    contenido = caja.get(MOSTRADOR).content.decode()

    assert "Todavía no hay productos en el ticket" in contenido
    assert 'class="caj-accion caj-accion--ancha" disabled' in contenido


def test_cobrar_desde_el_mostrador_del_cajero_registra_y_anuncia_el_vuelto(caja):
    producto = ProductoFactory(stock=5, precio=Decimal("8500"))
    caja.post(reverse("ventas:agregar"), {"producto": producto.pk, "cantidad": 1})

    respuesta = caja.post(
        reverse("ventas:confirmar"), {"medio": "efectivo", "recibido": "10.000"}, follow=True
    )
    contenido = respuesta.content.decode()

    assert "ventas/cajero/comprobante.html" in _plantillas(respuesta)
    assert "¡Listo," in contenido
    assert "$ 1.500" in contenido  # el vuelto, en el visor
    assert "Nueva venta" in contenido


# ===========================================================================
# Los medidores de la caja
# ===========================================================================


def test_el_medio_que_mas_recaudo_llena_el_medidor_y_termina_en_pico():
    filas = _medidores([("Efectivo", Decimal("300")), ("Tarjeta", Decimal("100")), ("Pasarela", 0)])

    efectivo, tarjeta, pasarela = (segmentos for _, _, segmentos in filas)
    assert len(efectivo) == SEGMENTOS
    assert efectivo[-2:] == ["pico", "pico"]
    assert all(efectivo)
    assert sum(1 for s in tarjeta if s) == 4
    assert "pico" not in tarjeta
    assert not any(pasarela)


def test_sin_recaudacion_los_medidores_quedan_apagados():
    filas = _medidores([("Efectivo", 0), ("Tarjeta", 0)])

    assert all(not any(segmentos) for _, _, segmentos in filas)
