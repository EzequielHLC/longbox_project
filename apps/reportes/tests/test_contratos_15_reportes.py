"""Pruebas de contrato de CU-REP-GEN: `CO-204` y `CO-128` (plan 15).

Cada reporte se arma con pedidos que lo pueden confundir: uno cancelado, uno de
varias líneas, una línea pagada con puntos y otra cancelada con reembolso. La
postcondición de `CO-204` es negativa —no modifica nada— y la de `CO-128`, la
entrada en el log con el tipo, el rango y el actor.
"""

from datetime import timedelta
from decimal import Decimal

import pytest
from django.urls import reverse
from django.utils import timezone

from apps.accounts.tests.factories import UsuarioFactory
from apps.catalog.models import Producto
from apps.catalog.tests.factories import (
    ProductoFactory,
    ProductoNoEditorialFactory,
    TipoFactory,
)
from apps.core.models import RegistroAuditoria
from apps.pedidos.models import LineaPedido, Pedido
from apps.pedidos.tests.util import crear_pedido
from apps.puntos.models import MovimientoPuntos
from apps.reportes import servicios
from apps.reportes.forms import MENSAJE_FUTURO, MENSAJE_RANGO_INVERTIDO
from apps.restock.models import SuscripcionReposicion

pytestmark = pytest.mark.django_db

URL = reverse("reportes:generar")
EXPORTAR = reverse("reportes:exportar")


def hoy():
    return timezone.localdate()


def rango(tipo, *, desde=None, hasta=None, **extra):
    return {
        "tipo": tipo,
        "desde": (desde or hoy() - timedelta(days=7)).isoformat(),
        "hasta": (hasta or hoy()).isoformat(),
        **extra,
    }


def linea(pedido, producto, cantidad, precio, **extra):
    return LineaPedido.objects.create(
        pedido=pedido,
        producto=producto,
        cantidad=cantidad,
        precio_unitario=Decimal(precio),
        **{"estado": LineaPedido.DISPONIBLE, **extra},
    )


@pytest.fixture
def ventas(db):
    """Dos ventas que cuentan y una que no.

    - Online: Akira ×2 a $10.000, Berserk ×1 pagado con puntos, y una línea
      cancelada con reembolso que no cuenta. Envío $1.500.
    - Mostrador: Akira ×1 a $10.000.
    - Cancelado: no cuenta.
    """
    akira = ProductoFactory(titulo="Akira", codigo="AKI-1")
    berserk = ProductoFactory(titulo="Berserk", codigo="BER-1")
    online = crear_pedido(UsuarioFactory(), lineas=(), costo_envio="1500")
    linea(online, akira, 2, "10000")
    linea(online, berserk, 1, "8000", cubierta_con_puntos=True, puntos_canjeados=800)
    linea(online, berserk, 1, "8000", estado=LineaPedido.CANCELADO_REEMBOLSO)
    mostrador = crear_pedido(UsuarioFactory(), lineas=(), costo_envio="0")
    mostrador.canal = Pedido.PRESENCIAL
    mostrador.modalidad = Pedido.MOSTRADOR
    mostrador.estado = Pedido.VENDIDO_EN_LOCAL
    mostrador.save(update_fields=["canal", "modalidad", "estado"])
    linea(mostrador, akira, 1, "10000")
    cancelado = crear_pedido(UsuarioFactory(), lineas=(), estado=Pedido.CANCELADO)
    linea(cancelado, akira, 5, "10000")
    return {"akira": akira, "berserk": berserk}


def generar(client, tipo, **extra):
    return client.get(URL, rango(tipo, **extra)).context["reporte"]


# ---------------------------------------------------------------------------
# CO-204 · generarReporteOperativo
# ---------------------------------------------------------------------------


def test_CO204_ventas_totales_consolida_por_dia(client_admin, ventas):
    reporte = generar(client_admin, servicios.VENTAS_TOTALES)

    assert reporte.columnas == ["Día", "Ventas", "Unidades", "Importe", "Envío", "Reembolsos"]
    assert reporte.filas == [[hoy(), 2, 4, Decimal("30000"), Decimal("1500"), 0]]
    assert reporte.totales[1:5] == [2, 4, Decimal("30000"), Decimal("1500")]


def test_CO204_ventas_totales_filtra_por_canal(client_admin, ventas):
    reporte = generar(client_admin, servicios.VENTAS_TOTALES, canal=Pedido.PRESENCIAL)

    assert reporte.filas == [[hoy(), 1, 1, Decimal("10000"), Decimal("0"), 0]]


def test_CO204_ventas_por_canal_separa_fisico_y_online(client_admin, ventas):
    reporte = generar(client_admin, servicios.VENTAS_POR_CANAL)

    assert reporte.filas == [
        ["Físico (mostrador)", 1, 1, Decimal("10000"), Decimal("0")],
        ["Online", 1, 3, Decimal("20000"), Decimal("1500")],
    ]


def test_CO204_mas_vendidos_ordena_por_unidades_y_el_canje_no_suma(client_admin, ventas):
    reporte = generar(client_admin, servicios.MAS_VENDIDOS)

    assert reporte.filas == [
        ["AKI-1", "Akira", 3, Decimal("30000")],
        ["BER-1", "Berserk", 1, Decimal("0")],
    ]


def test_CO204_mas_vendidos_filtra_por_categoria(client_admin, ventas):
    reporte = generar(client_admin, servicios.MAS_VENDIDOS, categoria=ventas["akira"].tipo_id)

    assert [fila[1] for fila in reporte.filas] == ["Akira"]


def test_CO204_movimientos_de_puntos_por_tipo_y_motivo(client_admin):
    cliente = UsuarioFactory()
    for tipo, cantidad, motivo in [
        (MovimientoPuntos.ACREDITACION, 100, "Compra"),
        (MovimientoPuntos.ACREDITACION, 50, "Compra"),
        (MovimientoPuntos.DEBITO, 30, "Canje"),
    ]:
        MovimientoPuntos.objects.create(
            usuario=cliente, tipo=tipo, cantidad=cantidad, saldo_resultante=0, motivo=motivo
        )

    reporte = generar(client_admin, servicios.MOVIMIENTOS_DE_PUNTOS)
    solo_debitos = generar(
        client_admin, servicios.MOVIMIENTOS_DE_PUNTOS, tipo_movimiento=MovimientoPuntos.DEBITO
    )

    assert ["Acreditación", "Compra", 2, 150] in reporte.filas
    assert ["Débito", "Canje", 1, 30] in reporte.filas
    assert reporte.totales[-1] == 120
    assert solo_debitos.filas == [["Débito", "Canje", 1, 30]]


def test_CO204_solicitudes_de_reposicion_en_espera_del_rango(client_admin):
    manga, figura = TipoFactory(nombre="Manga"), TipoFactory(nombre="Figura")
    agotado = ProductoFactory(
        titulo="Akira", codigo="AKI-1", tipo=manga, stock=0, estado=Producto.AGOTADO
    )
    # «Figura» es la categoría no editorial que siembra la migración: su producto
    # es del mismo rubro (I-05, en la base desde el plan 00 de cierre de deuda).
    otro = ProductoNoEditorialFactory(
        titulo="Gojo", codigo="GOJ-1", tipo=figura, stock=0, estado=Producto.AGOTADO
    )
    for _ in range(2):
        SuscripcionReposicion.objects.create(usuario=UsuarioFactory(), producto=agotado)
    SuscripcionReposicion.objects.create(usuario=UsuarioFactory(), producto=otro)
    SuscripcionReposicion.objects.create(
        usuario=UsuarioFactory(), producto=otro, estado=SuscripcionReposicion.NOTIFICADA
    )
    SuscripcionReposicion.objects.create(
        usuario=UsuarioFactory(), producto=otro, creada_en=timezone.now() - timedelta(days=90)
    )

    reporte = generar(client_admin, servicios.REPOSICION)
    solo_manga = generar(client_admin, servicios.REPOSICION, categoria=manga.pk)

    assert [fila[:3] for fila in reporte.filas] == [["AKI-1", "Akira", 2], ["GOJ-1", "Gojo", 1]]
    assert [fila[1] for fila in solo_manga.filas] == ["Akira"]


def test_CO204_no_modifica_nada(client_admin, ventas):
    pedidos = list(Pedido.objects.values_list("pk", "estado"))
    entradas = RegistroAuditoria.objects.count()

    for tipo, _ in servicios.TIPOS:
        client_admin.get(URL, rango(tipo))

    assert list(Pedido.objects.values_list("pk", "estado")) == pedidos
    assert RegistroAuditoria.objects.count() == entradas


@pytest.mark.parametrize(
    "desde, hasta, mensaje",
    [
        (1, 5, MENSAJE_RANGO_INVERTIDO),
        (0, -3, MENSAJE_FUTURO),
    ],
)
def test_CO204_E1_un_rango_invalido_no_procede(client_admin, desde, hasta, mensaje):
    respuesta = client_admin.get(
        URL,
        rango(
            servicios.VENTAS_TOTALES,
            desde=hoy() - timedelta(days=desde),
            hasta=hoy() - timedelta(days=hasta),
        ),
    )

    assert respuesta.context["reporte"] is None
    assert mensaje in respuesta.content.decode()


def test_CO204_E1_el_rango_es_obligatorio(client_admin):
    respuesta = client_admin.get(URL, {"tipo": servicios.VENTAS_TOTALES, "desde": "", "hasta": ""})

    assert respuesta.context["reporte"] is None


@pytest.mark.parametrize("tipo", [clave for clave, _ in servicios.TIPOS])
def test_CO204_E2_sin_datos_el_reporte_vacio_lo_dice(client_admin, tipo):
    respuesta = client_admin.get(URL, rango(tipo))

    assert respuesta.status_code == 200
    assert respuesta.context["reporte"].vacio
    assert "No hay datos para este reporte" in respuesta.content.decode()


# ---------------------------------------------------------------------------
# CO-128 · exportarReporte
# ---------------------------------------------------------------------------


def test_CO128_el_csv_dice_lo_mismo_que_la_pantalla(client_admin, ventas):
    pantalla = generar(client_admin, servicios.MAS_VENDIDOS)

    respuesta = client_admin.get(EXPORTAR, rango(servicios.MAS_VENDIDOS))

    texto = respuesta.content.decode("utf-8-sig")
    assert respuesta["Content-Type"].startswith("text/csv")
    renglones = texto.strip().splitlines()
    assert renglones[0] == ",".join(pantalla.columnas)
    assert renglones[1] == "AKI-1,Akira,3,30000.00"
    assert len(renglones) == 1 + len(pantalla.filas) + 1


def test_CO128_queda_en_el_log_con_tipo_rango_y_actor(client_admin, administrador, ventas):
    desde = hoy() - timedelta(days=7)

    client_admin.get(EXPORTAR, rango(servicios.VENTAS_TOTALES, desde=desde, canal="online"))

    registro = RegistroAuditoria.objects.get(accion=RegistroAuditoria.EXPORTACION_REPORTE)
    assert registro.actor == administrador
    assert "Ventas totales" in registro.detalle
    assert desde.strftime("%d/%m/%Y") in registro.detalle
    assert hoy().strftime("%d/%m/%Y") in registro.detalle
    assert "canal Online" in registro.detalle


def test_CO128_precondicion_sin_reporte_valido_no_exporta(client_admin):
    respuesta = client_admin.get(
        EXPORTAR, rango(servicios.VENTAS_TOTALES, desde=hoy(), hasta=hoy() - timedelta(days=2))
    )

    assert respuesta.status_code == 302
    assert not RegistroAuditoria.objects.filter(
        accion=RegistroAuditoria.EXPORTACION_REPORTE
    ).exists()


# ---------------------------------------------------------------------------
# Control de acceso: por la dirección real, con el rol equivocado
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("rol", ["cajero", "cliente"])
def test_CO204_CO128_otro_rol_no_entra(client, rol):
    client.force_login(UsuarioFactory(rol=rol))

    assert client.get(URL, rango(servicios.VENTAS_TOTALES)).status_code == 403
    assert client.get(EXPORTAR, rango(servicios.VENTAS_TOTALES)).status_code == 403
    assert not RegistroAuditoria.objects.filter(
        accion=RegistroAuditoria.EXPORTACION_REPORTE
    ).exists()


def test_el_menu_del_administrador_enlaza_los_reportes(client_admin):
    assert URL in client_admin.get(reverse("core:panel")).content.decode()
