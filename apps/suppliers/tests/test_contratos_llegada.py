"""`CO-232` confirmarLlegadaDeMercaderia: «Por llegar», una sola pantalla (B-05-017).

Por la dirección real. Cada postcondición tiene su prueba, también las negativas:
revisar no registra nada, lo que no es pre-venta en cero sigue abierto, y la misma
caja confirmada dos veces se cuenta una.
"""

from datetime import timedelta

import pytest
from django.urls import reverse
from django.utils import timezone

from apps.accounts.tests.factories import UsuarioFactory
from apps.catalog.models import Producto, ProductoEditorial
from apps.catalog.tests.factories import EditorialFactory, ProductoFactory
from apps.core.models import RegistroAuditoria
from apps.pedidos.models import LineaPedido, Pedido
from apps.pedidos.tests.util import reservar
from apps.restock.models import SuscripcionReposicion
from apps.suppliers import llegadas
from apps.suppliers.models import LineaPedidoProveedor, PedidoProveedor
from apps.suppliers.tests.factories import ProveedorFactory

pytestmark = pytest.mark.django_db

URL = reverse("suppliers:por_llegar")
REVISAR = reverse("suppliers:llegada_revisar")


@pytest.fixture
def ivrea(db):
    return ProveedorFactory(razon_social="Distribuidora Ivrea", editorial=EditorialFactory())


def pedir(proveedor, *renglones, dias=0):
    """Un pedido enviado con sus líneas. Lo agotado sin stock pasa a Pre-venta."""
    return llegadas.registrar(
        proveedor,
        PedidoProveedor.MANUAL,
        list(renglones),
        fecha_estimada=timezone.localdate() + timedelta(days=dias),
    )


def agotado(proveedor, titulo, **extra):
    return ProductoFactory(
        titulo=titulo, stock=0, estado=Producto.AGOTADO, editorial=proveedor.editorial, **extra
    )


def formulario(*filas, confirmar=False):
    """El grupo enviado: `(linea, unidades)` o `(producto, unidades)` sin pedido."""
    datos = {"fila": []}
    for objeto, valor in filas:
        if isinstance(objeto, LineaPedidoProveedor):
            campo = f"l{objeto.pk}"
            datos[f"vista_{campo}"] = str(objeto.cantidad_recibida)
        else:
            campo = f"p{objeto.pk}"
        datos["fila"].append(campo)
        datos[f"llegaron_{campo}"] = str(valor)
    if confirmar:
        datos["confirmar"] = "1"
    return datos


def foto():
    return (
        list(Producto.objects.order_by("pk").values_list("estado", "stock")),
        list(
            LineaPedidoProveedor.objects.order_by("pk").values_list("cantidad_recibida", "estado")
        ),
        list(LineaPedido.objects.order_by("pk").values_list("estado")),
        RegistroAuditoria.objects.count(),
    )


# ---------------------------------------------------------------------------
# La pantalla
# ---------------------------------------------------------------------------


def test_CO240_agrupa_por_proveedor_y_fecha_con_lo_de_los_dos_paneles(client_admin, ivrea, cliente):
    otro = ProveedorFactory(razon_social="Panini Argentina", editorial=EditorialFactory())
    akira = agotado(ivrea, "Akira")
    pedido = pedir(ivrea, (akira, 6), (agotado(ivrea, "Berserk"), 4), dias=2)
    pedir(otro, (agotado(otro, "Naruto"), 3), dias=2)
    reservar(cliente, akira, cantidad=2)

    respuesta = client_admin.get(URL)

    grupos = respuesta.context["grupos"]
    assert [(g.nombre, len(g.filas)) for g in grupos] == [
        ("Distribuidora Ivrea", 2),
        ("Panini Argentina", 1),
    ]
    fila = next(f for f in grupos[0].filas if f.producto.pk == akira.pk)
    assert (fila.linea.pedido, fila.esperadas, fila.reservadas) == (pedido, 6, 2)
    contenido = respuesta.content.decode()
    assert f'name="llegaron_l{fila.linea.pk}"' in contenido
    assert f"#{pedido.pk}" in contenido


def test_CO240_la_preventa_sin_pedido_aparece_marcada(client_admin):
    suelta = ProductoFactory(estado=Producto.PRE_VENTA, stock=0, fecha_llegada=timezone.localdate())
    LineaPedidoProveedor.objects.filter(producto=suelta).delete()

    contenido = client_admin.get(URL).content.decode()

    assert f'name="llegaron_p{suelta.pk}"' in contenido
    assert "Sin pedido registrado" in contenido


def test_CO240_un_pedido_sin_enviar_no_se_espera_y_se_avisa(client_admin, ivrea):
    akira = agotado(ivrea, "Akira")
    pedido = pedir(ivrea, (akira, 6))
    # Como lo deja un correo que falló (B-05-014): sin pedido en camino, no hay pre-venta.
    PedidoProveedor.objects.filter(pk=pedido.pk).update(estado=PedidoProveedor.SIN_ENVIAR)
    Producto.objects.filter(pk=akira.pk).update(estado=Producto.AGOTADO)

    respuesta = client_admin.get(URL)

    assert respuesta.context["grupos"] == []
    assert "1 pedido sin enviar" in respuesta.content.decode()


# ---------------------------------------------------------------------------
# Revisar y confirmar
# ---------------------------------------------------------------------------


def test_CO244_revisar_no_registra_nada(client_admin, ivrea, cliente):
    akira = agotado(ivrea, "Akira")
    pedido = pedir(ivrea, (akira, 6))
    reservar(cliente, akira, cantidad=2)
    antes = foto()

    respuesta = client_admin.post(REVISAR, formulario((pedido.lineas.get(), 4)))

    assert respuesta.status_code == 200
    assert "Confirmar la llegada" in respuesta.content.decode()
    assert foto() == antes


def test_CO232_cada_linea_suma_lo_recibido_a_su_pedido(client_admin, ivrea):
    pedido = pedir(ivrea, (agotado(ivrea, "Akira"), 6), (agotado(ivrea, "Berserk"), 4))
    akira, berserk = pedido.lineas.order_by("pk")

    client_admin.post(REVISAR, formulario((akira, 2), (berserk, 4), confirmar=True))

    akira.refresh_from_db()
    berserk.refresh_from_db()
    assert (akira.cantidad_recibida, akira.estado) == (2, LineaPedidoProveedor.PARCIAL)
    assert (berserk.cantidad_recibida, berserk.estado) == (4, LineaPedidoProveedor.RECIBIDA)
    assert RegistroAuditoria.objects.filter(
        accion=RegistroAuditoria.LLEGADA_PEDIDO, objetivo_pk=str(pedido.pk)
    ).exists()


def test_CO232_lo_que_llega_de_mas_se_acepta_y_queda_en_la_auditoria(client_admin, ivrea):
    pedido = pedir(ivrea, (agotado(ivrea, "Akira"), 6))

    client_admin.post(REVISAR, formulario((pedido.lineas.get(), 8), confirmar=True))

    linea = pedido.lineas.get()
    assert (linea.cantidad_recibida, linea.estado) == (8, LineaPedidoProveedor.RECIBIDA)
    detalle = RegistroAuditoria.objects.get(accion=RegistroAuditoria.LLEGADA_PEDIDO).detalle
    assert "de más" in detalle


def test_CO232_la_preventa_cubre_sus_reservas_por_CO013(client_admin, ivrea, cliente):
    akira = agotado(ivrea, "Akira")
    pedido = pedir(ivrea, (akira, 6))
    compra, reserva = reservar(cliente, akira, cantidad=2)

    client_admin.post(REVISAR, formulario((pedido.lineas.get(), 6), confirmar=True))

    akira.refresh_from_db()
    reserva.refresh_from_db()
    compra.refresh_from_db()
    assert (akira.estado, akira.stock) == (Producto.ACTIVO, 4)
    assert reserva.estado == LineaPedido.DISPONIBLE
    assert compra.estado == Pedido.PENDIENTE_ARMADO
    assert RegistroAuditoria.objects.filter(
        accion=RegistroAuditoria.CONFIRMACION_INGRESO, objetivo_pk=str(akira.pk)
    ).exists()


def test_CO232_lo_que_no_es_preventa_suma_al_stock_y_avisa_a_los_suscriptores(
    client_admin, ivrea, cliente, django_capture_on_commit_callbacks
):
    akira = ProductoFactory(titulo="Akira", stock=0, estado=Producto.AGOTADO)
    SuscripcionReposicion.objects.create(usuario=cliente, producto=akira)
    pedido = llegadas.registrar(ivrea, PedidoProveedor.MANUAL, [(akira, 3)])
    Producto.objects.filter(pk=akira.pk).update(estado=Producto.AGOTADO)

    with django_capture_on_commit_callbacks(execute=True):
        client_admin.post(REVISAR, formulario((pedido.lineas.get(), 3), confirmar=True))

    akira.refresh_from_db()
    assert (akira.estado, akira.stock) == (Producto.ACTIVO, 3)
    assert (
        SuscripcionReposicion.objects.get(producto=akira).estado == SuscripcionReposicion.NOTIFICADA
    )


def test_CO232_la_preventa_sin_pedido_se_carga_por_CO013(client_admin, cliente):
    suelta = ProductoFactory(estado=Producto.PRE_VENTA, stock=0, fecha_llegada=timezone.localdate())
    LineaPedidoProveedor.objects.filter(producto=suelta).delete()
    reservar(cliente, suelta, cantidad=1)

    client_admin.post(REVISAR, formulario((suelta, 3), confirmar=True))

    suelta.refresh_from_db()
    assert (suelta.estado, suelta.stock) == (Producto.ACTIVO, 2)


def test_CO232_un_faltante_con_la_fecha_cumplida_se_demora_y_uno_futuro_no_cambia(
    client_admin, ivrea, cliente
):
    hoy = agotado(ivrea, "Hoy", fecha_llegada=timezone.localdate())
    pedido_hoy = pedir(ivrea, (hoy, 2), dias=0)
    futuro = agotado(ivrea, "Futuro", fecha_llegada=timezone.localdate() + timedelta(days=5))
    pedido_futuro = pedir(ivrea, (futuro, 2), dias=5)
    reservar(cliente, hoy)
    reservar(cliente, futuro)

    client_admin.post(
        REVISAR,
        formulario((pedido_hoy.lineas.get(), 0), (pedido_futuro.lineas.get(), 0), confirmar=True),
    )

    assert ProductoEditorial.objects.get(pk=hoy.pk).demorado is True
    assert ProductoEditorial.objects.get(pk=futuro.pk).demorado is False
    # Postcondición negativa: un faltante no toca lo recibido de las líneas.
    assert set(LineaPedidoProveedor.objects.values_list("cantidad_recibida", flat=True)) == {0}


def test_CO232_lo_que_no_es_preventa_en_cero_sigue_esperando(client_admin, ivrea):
    akira = ProductoFactory(titulo="Akira", stock=2, estado=Producto.ACTIVO)
    pedido = llegadas.registrar(ivrea, PedidoProveedor.MANUAL, [(akira, 3)])
    antes = foto()

    respuesta = client_admin.post(
        REVISAR, formulario((pedido.lineas.get(), 0), confirmar=True), follow=True
    )

    assert foto() == antes
    assert "No cambió nada" in respuesta.content.decode()


def test_CO232_confirmar_sin_haber_revisado_no_registra(client_admin, ivrea):
    pedido = pedir(ivrea, (agotado(ivrea, "Akira"), 6))
    linea = pedido.lineas.get()
    antes = foto()

    respuesta = client_admin.post(
        REVISAR,
        {"fila": [f"l{linea.pk}"], f"llegaron_l{linea.pk}": "6", "confirmar": "1"},
        follow=True,
    )

    assert foto() == antes
    assert "Revisá la llegada antes de confirmarla" in respuesta.content.decode()


def test_CO232_si_otro_se_adelanto_ese_pedido_no_suma_y_los_demas_siguen(client_admin, ivrea):
    uno = pedir(ivrea, (agotado(ivrea, "Akira"), 6))
    otro = pedir(ivrea, (agotado(ivrea, "Berserk"), 4))
    vieja = formulario((uno.lineas.get(), 4), (otro.lineas.get(), 4), confirmar=True)
    # Otra persona registró 2 de Akira entre la revisión y la confirmación.
    llegadas.registrar_llegada(uno, {uno.lineas.get().pk: 2}, UsuarioFactory(rol="administrador"))

    respuesta = client_admin.post(REVISAR, vieja, follow=True)

    assert uno.lineas.get().cantidad_recibida == 2  # lo de la revisión vieja no se sumó
    assert otro.lineas.get().cantidad_recibida == 4  # el otro pedido siguió (como CO-013 E3)
    assert "mientras revisabas" in respuesta.content.decode()


def test_CO232_si_una_linea_se_cerro_mientras_tanto_no_se_registra_nada(client_admin, ivrea):
    uno = pedir(ivrea, (agotado(ivrea, "Akira"), 6))
    otro = pedir(ivrea, (agotado(ivrea, "Berserk"), 4))
    vieja = formulario((uno.lineas.get(), 6), (otro.lineas.get(), 4), confirmar=True)
    llegadas.registrar_llegada(uno, {uno.lineas.get().pk: 6}, UsuarioFactory(rol="administrador"))

    respuesta = client_admin.post(REVISAR, vieja, follow=True)

    assert otro.lineas.get().cantidad_recibida == 0
    assert "ya no está esperando" in respuesta.content.decode()


# ---------------------------------------------------------------------------
# Control de acceso por la dirección real, y las direcciones viejas
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("rol", ["cajero", "cliente"])
def test_CO232_el_rol_equivocado_no_ve_ni_carga_la_llegada(client, ivrea, rol):
    pedido = pedir(ivrea, (agotado(ivrea, "Akira"), 6))
    client.force_login(UsuarioFactory(rol=rol))

    assert client.get(URL).status_code == 403
    respuesta = client.post(REVISAR, formulario((pedido.lineas.get(), 6), confirmar=True))

    assert respuesta.status_code == 403
    assert pedido.lineas.get().cantidad_recibida == 0


def test_las_direcciones_viejas_llevan_a_por_llegar_sin_registrar_nada(client_admin, ivrea):
    pedido = pedir(ivrea, (agotado(ivrea, "Akira"), 6))
    antes = foto()

    vista = client_admin.get(reverse("pedidos:preventas"), {"mes": "2026-12"})
    envio = client_admin.post(
        reverse("pedidos:ingreso"), {"producto": [pedido.lineas.get().producto_id]}
    )

    assert vista.url == f"{URL}?mes=2026-12"
    assert envio.url == URL
    assert foto() == antes


# ---------------------------------------------------------------------------
# B-05-019: lo que ya no se vende (revisión integral, R-03)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("estado", [Producto.DESCATALOGADO, Producto.CANCELADO_EDITORIAL])
def test_CO232_la_llegada_no_reactiva_un_producto_que_no_se_vende(
    client_admin, ivrea, cliente, estado, django_capture_on_commit_callbacks
):
    akira = ProductoFactory(titulo="Akira", stock=0, estado=Producto.AGOTADO)
    pedido = llegadas.registrar(ivrea, PedidoProveedor.MANUAL, [(akira, 3)])
    SuscripcionReposicion.objects.create(usuario=cliente, producto=akira)
    Producto.objects.filter(pk=akira.pk).update(estado=estado)
    linea = pedido.lineas.get()

    revision = client_admin.post(REVISAR, formulario((linea, 3))).content.decode()
    with django_capture_on_commit_callbacks(execute=True):
        client_admin.post(REVISAR, formulario((linea, 3), confirmar=True))

    akira.refresh_from_db()
    assert "No vuelve a la venta" in revision
    # Postcondición negativa: el estado no cambia y nadie recibe el aviso de reposición.
    assert (akira.estado, akira.stock) == (estado, 3)
    assert SuscripcionReposicion.objects.get(producto=akira).estado != (
        SuscripcionReposicion.NOTIFICADA
    )


def test_CO027_cancelar_la_preventa_cierra_lo_pedido_al_proveedor(
    client_admin, ivrea, administrador
):
    from apps.pedidos import preventa

    akira = agotado(ivrea, "Akira")
    pedido = pedir(ivrea, (akira, 6))
    akira.refresh_from_db()
    assert akira.estado == Producto.PRE_VENTA

    preventa.cancelar_preventa(akira.especifico, administrador)

    linea = pedido.lineas.get()
    pedido.refresh_from_db()
    assert (linea.estado, linea.motivo_cierre) == (
        LineaPedidoProveedor.SIN_RECIBIR,
        "La editorial canceló el título.",
    )
    assert pedido.estado == PedidoProveedor.CERRADO
    assert "Akira" not in client_admin.get(URL).content.decode()
    assert "1 línea(s) de pedido al proveedor" in (
        RegistroAuditoria.objects.get(accion=RegistroAuditoria.CANCELACION_PREVENTA_LOTE).detalle
    )


def test_CO034_descatalogar_cierra_lo_pedido_al_proveedor(ivrea, administrador):
    from apps.catalog.services import confirmar_baja_de_producto

    akira = ProductoFactory(titulo="Akira", stock=2, estado=Producto.ACTIVO)
    otro = ProductoFactory(titulo="Berserk", stock=2, estado=Producto.ACTIVO)
    pedido = llegadas.registrar(ivrea, PedidoProveedor.MANUAL, [(akira, 3), (otro, 3)])

    hecho = confirmar_baja_de_producto(akira, actor=administrador)

    pedido.refresh_from_db()
    estados = dict(pedido.lineas.values_list("producto_id", "estado"))
    assert hecho.lineas_cerradas == 1
    assert estados == {
        akira.pk: LineaPedidoProveedor.SIN_RECIBIR,
        otro.pk: LineaPedidoProveedor.PENDIENTE,
    }
    # Lo demás del pedido se sigue esperando.
    assert pedido.estado == PedidoProveedor.ABIERTO
