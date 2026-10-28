"""La demora de varios tomos a la vez (B-01-022, desvío consultado de CU-ALT-DEM).

Cada tomo es un `CO-015` propio, con sus postcondiciones y su auditoría; lo que
no admite la demora queda afuera con su motivo y no frena a los demás; y el
Cliente recibe un solo correo con todos sus tomos demorados.
"""

from datetime import timedelta

import pytest
from django.urls import reverse
from django.utils import timezone

from apps.accounts.tests.factories import UsuarioFactory
from apps.catalog.models import Producto, ProductoEditorial
from apps.core.models import RegistroAuditoria
from apps.pedidos import preventa
from apps.pedidos.models import LineaPedido, Pedido
from apps.pedidos.tests.util import crear_preventa, reservar

pytestmark = pytest.mark.django_db

URL = reverse("pedidos:demora_lote")


def en_dias(dias):
    return timezone.localdate() + timedelta(days=dias)


def _correos_a(mailoutbox, direccion):
    return [m for m in mailoutbox if direccion in m.to]


# ---------------------------------------------------------------------------
# El servicio
# ---------------------------------------------------------------------------


def test_CO015_varios_tomos_cada_uno_con_su_fecha_y_su_auditoria(
    administrador, cliente, django_capture_on_commit_callbacks
):
    uno, dos = crear_preventa(dias=5), crear_preventa(dias=6)
    _, linea_uno = reservar(cliente, uno)
    _, linea_dos = reservar(cliente, dos)

    with django_capture_on_commit_callbacks(execute=True):
        resumen = preventa.registrar_demoras(
            {uno: en_dias(30), dos: None}, administrador, nota="Imprenta"
        )

    assert len(resumen.demorados) == 2
    assert resumen.excluidos == []
    uno, dos = (ProductoEditorial.objects.get(pk=p.pk) for p in (uno, dos))
    assert (uno.demorado, uno.fecha_estimada, uno.nota_demora) == (True, en_dias(30), "Imprenta")
    assert (dos.demorado, dos.fecha_estimada) == (True, None)
    assert {uno.estado, dos.estado} == {Producto.PRE_VENTA}  # la demora no es un estado
    for linea in (linea_uno, linea_dos):
        linea.refresh_from_db()
        assert linea.estado == LineaPedido.ESPERANDO_DEMORADO
        assert linea.pedido.estado == Pedido.ESPERANDO_DEMORADO
    assert RegistroAuditoria.objects.filter(accion=RegistroAuditoria.REGISTRO_DEMORA).count() == 2


def test_CO015_el_que_ya_no_admite_la_demora_queda_afuera_y_los_demas_siguen(administrador):
    ya_demorado = crear_preventa(dias=5, demorado=True)
    vencido = crear_preventa(dias=-2)
    sano = crear_preventa(dias=8)

    resumen = preventa.registrar_demoras(
        {ya_demorado: None, vencido: None, sano: None}, administrador
    )

    assert [r.producto.pk for r in resumen.demorados] == [sano.pk]
    motivos = dict((p.pk, m) for p, m in resumen.excluidos)
    assert "ya tiene una demora" in motivos[ya_demorado.pk]
    assert "ya pasó" in motivos[vencido.pk]
    vencido.refresh_from_db()
    assert vencido.demorado is False  # postcondición negativa: lo excluido no cambia


def test_una_fecha_pasada_excluye_sólo_ese_tomo(administrador):
    uno, dos = crear_preventa(dias=5), crear_preventa(dias=5)

    resumen = preventa.registrar_demoras({uno: en_dias(-1), dos: en_dias(10)}, administrador)

    assert [r.producto.pk for r in resumen.demorados] == [dos.pk]
    assert "posterior a hoy" in resumen.excluidos[0][1]


def test_un_solo_correo_por_cliente_con_todos_sus_tomos(
    administrador, cliente, mailoutbox, django_capture_on_commit_callbacks
):
    otro = UsuarioFactory(rol="cliente")
    uno, dos, tres = (crear_preventa(dias=5) for _ in range(3))
    for producto in (uno, dos, tres):
        reservar(cliente, producto)
    reservar(otro, uno)

    with django_capture_on_commit_callbacks(execute=True):
        preventa.registrar_demoras(
            {uno: en_dias(20), dos: en_dias(20), tres: None},
            administrador,
            origen="https://longbox.test",
        )

    propios = _correos_a(mailoutbox, cliente.email)
    assert len(propios) == 1
    cuerpo = propios[0].body
    for producto in (uno, dos, tres):
        assert preventa.nombre(producto) in cuerpo
    assert "Ver mis pedidos" in cuerpo  # tres pedidos: el acceso a todos
    assert reverse("cuenta:pedidos") in cuerpo
    # El que tenía un solo tomo recibe el aviso de siempre.
    del_otro = _correos_a(mailoutbox, otro.email)
    assert len(del_otro) == 1
    assert "un artículo se demora" in del_otro[0].subject


def test_varios_tomos_del_mismo_pedido_llevan_a_ese_pedido(
    administrador, cliente, mailoutbox, django_capture_on_commit_callbacks
):
    uno, dos = crear_preventa(dias=5), crear_preventa(dias=5)
    pedido, _ = reservar(cliente, uno)
    LineaPedido.objects.create(
        pedido=pedido,
        producto=dos,
        cantidad=1,
        precio_unitario=dos.precio,
        estado=LineaPedido.RESERVADO,
    )

    with django_capture_on_commit_callbacks(execute=True):
        preventa.registrar_demoras(
            {uno: None, dos: None}, administrador, origen="https://longbox.test"
        )

    propios = _correos_a(mailoutbox, cliente.email)
    assert len(propios) == 1
    assert pedido.numero in propios[0].subject
    assert reverse("cuenta:pedido", args=[pedido.numero]) in propios[0].body


# ---------------------------------------------------------------------------
# La pantalla, por su dirección real
# ---------------------------------------------------------------------------


def test_la_pantalla_va_en_tres_tiempos_y_sólo_confirma_al_final(
    client_admin, cliente, django_capture_on_commit_callbacks
):
    uno, dos = crear_preventa(dias=5), crear_preventa(dias=5)
    reservar(cliente, uno)
    fecha = en_dias(25).isoformat()

    formulario = client_admin.get(URL, {"producto": [uno.pk, dos.pk]})
    datos = {
        "producto": [uno.pk, dos.pk],
        "incluir": [uno.pk, dos.pk],
        f"fecha_{uno.pk}": fecha,
        f"fecha_{dos.pk}": "",
        "nota": "Aviso",
    }
    revision = client_admin.post(URL, datos)

    assert formulario.status_code == 200
    assert len(formulario.context["filas"]) == 2
    assert revision.context["revision"] is True
    assert (revision.context["total_pedidos"], revision.context["total_clientes"]) == (1, 1)
    uno.refresh_from_db()
    assert uno.demorado is False  # revisar no registra nada

    with django_capture_on_commit_callbacks(execute=True):
        respuesta = client_admin.post(URL, {**datos, "confirmar": "1"})

    assert respuesta.url == reverse("pedidos:preventas")
    uno, dos = (ProductoEditorial.objects.get(pk=p.pk) for p in (uno, dos))
    assert (uno.demorado, uno.fecha_estimada.isoformat()) == (True, fecha)
    assert dos.demorado is True


def test_lo_destildado_no_se_demora(client_admin):
    uno, dos = crear_preventa(dias=5), crear_preventa(dias=5)

    client_admin.post(
        URL,
        {"producto": [uno.pk, dos.pk], "incluir": [uno.pk], "confirmar": "1"},
    )

    uno, dos = (ProductoEditorial.objects.get(pk=p.pk) for p in (uno, dos))
    assert (uno.demorado, dos.demorado) == (True, False)


def test_una_fecha_pasada_se_marca_en_su_fila_y_no_registra(client_admin):
    uno = crear_preventa(dias=5)

    respuesta = client_admin.post(
        URL,
        {"producto": [uno.pk], "incluir": [uno.pk], f"fecha_{uno.pk}": en_dias(-1).isoformat()},
    )

    assert respuesta.context["filas"][0]["error"]
    assert "revision" not in respuesta.context
    uno.refresh_from_db()
    assert uno.demorado is False


def test_lo_que_no_admite_la_demora_se_muestra_sin_casilla(client_admin):
    vencido = crear_preventa(dias=-2)

    respuesta = client_admin.get(URL, {"producto": [vencido.pk]})

    fila = respuesta.context["filas"][0]
    assert fila["no_admite"] and not fila["incluido"]
    assert f'name="incluir" value="{vencido.pk}"' not in respuesta.content.decode()


def test_sin_tomos_elegidos_vuelve_con_el_aviso(client_admin):
    respuesta = client_admin.get(URL, follow=True)

    assert "Elegí al menos una pre-venta" in respuesta.content.decode()


def test_el_grupo_de_preventas_ofrece_demorarlo_entero(client_admin):
    uno = crear_preventa(dias=5)

    html = client_admin.get(reverse("pedidos:preventas")).content.decode()

    assert f"{URL}?producto={uno.pk}" in html
    assert "Demorar este grupo" in html


def test_el_cajero_no_registra_demoras_por_la_direccion_real(client, cajero):
    uno = crear_preventa(dias=5)
    client.force_login(cajero)

    respuesta = client.post(URL, {"producto": [uno.pk], "incluir": [uno.pk], "confirmar": "1"})

    assert respuesta.status_code == 403
    uno.refresh_from_db()
    assert uno.demorado is False
