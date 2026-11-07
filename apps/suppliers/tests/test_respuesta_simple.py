"""La respuesta del proveedor, simple (plan 00 de la respuesta simple, B-05-015).

Sin código de contrato todavía, como el resto del caso de uso. Cada regla con su
prueba, incluidas las postcondiciones negativas:

- R1: lo que llega es una respuesta, y ya no se recuerda como «sin respuesta»;
- R2: no se confirma más de lo pedido;
- R3: lo que no cambió no se vuelve a anotar ni a auditar;
- R4: el motivo es de cada línea;
- R5 y R6: la propuesta dice qué espera y desde cuándo;
- R7: las advertencias enlazan el producto;
- la fecha se puede borrar, y «No puede» dice qué pasa antes de confirmar.
"""

from datetime import timedelta

import pytest
from django.urls import reverse
from django.utils import timezone

from apps.accounts.models import Usuario
from apps.accounts.tests.factories import UsuarioFactory
from apps.catalog.models import Producto
from apps.catalog.tests.factories import EditorialFactory, ProductoFactory
from apps.core.models import RegistroAuditoria
from apps.pedidos.tests.util import reservar
from apps.restock.models import PropuestaRestock
from apps.suppliers import llegadas, respuestas
from apps.suppliers.llegadas import OperacionRechazada
from apps.suppliers.models import LineaPedidoProveedor, PedidoProveedor
from apps.suppliers.tests.factories import ProveedorFactory
from apps.tienda.tests.compra_util import fijar_parametros

pytestmark = pytest.mark.django_db

DENTRO_DE_UN_MES = timezone.localdate() + timedelta(days=30)
CONFIRMADA = LineaPedidoProveedor.CONFIRMADA
OTRA = LineaPedidoProveedor.OTRA_CANTIDAD
NO = LineaPedidoProveedor.NO_DISPONIBLE


@pytest.fixture
def ivrea(db):
    return ProveedorFactory(razon_social="Distribuidora Ivrea", editorial=EditorialFactory())


@pytest.fixture
def pedido(ivrea):
    return llegadas.registrar(
        ivrea,
        PedidoProveedor.MANUAL,
        [
            (
                ProductoFactory(
                    titulo=t, stock=0, estado=Producto.AGOTADO, editorial=ivrea.editorial
                ),
                n,
            )
            for t, n in (("Akira", 6), ("Berserk", 4))
        ],
        fecha_estimada=DENTRO_DE_UN_MES,
    )


def lineas(pedido):
    return {linea.producto.titulo: linea for linea in pedido.lineas.select_related("producto")}


def respuestas_auditadas(pedido):
    return RegistroAuditoria.objects.filter(
        accion=RegistroAuditoria.RESPUESTA_PROVEEDOR, objetivo_pk=pedido.pk
    )


# ---------------------------------------------------------------------------
# R1 · lo que llega es una respuesta
# ---------------------------------------------------------------------------


def test_una_llegada_parcial_sin_respuesta_confirma_la_línea(pedido, administrador):
    akira = lineas(pedido)["Akira"]

    llegadas.registrar_llegada(pedido, {akira.pk: 2}, administrador)

    akira.refresh_from_db()
    assert (akira.estado, akira.respuesta) == (LineaPedidoProveedor.PARCIAL, CONFIRMADA)
    assert akira.respondida_en is not None
    # La línea entera queda confirmada: se sigue esperando lo que falta.
    assert akira.pendiente == 4


def test_lo_que_llegó_no_se_recuerda_como_sin_respuesta(pedido, administrador):
    akira, berserk = lineas(pedido)["Akira"], lineas(pedido)["Berserk"]
    llegadas.registrar_llegada(pedido, {akira.pk: 1, berserk.pk: 1}, administrador)

    assert respuestas.recordar(timezone.now() + timedelta(days=5)) == []


def test_la_llegada_no_pisa_una_respuesta_ya_anotada(pedido, administrador):
    akira = lineas(pedido)["Akira"]
    respuestas.responder(pedido, {akira.pk: (OTRA, 3)}, administrador)

    llegadas.registrar_llegada(pedido, {akira.pk: 1}, administrador)

    akira.refresh_from_db()
    assert (akira.respuesta, akira.cantidad_confirmada) == (OTRA, 3)


def test_lo_que_confirma_la_pantalla_de_preventas_también_responde(pedido):
    akira = lineas(pedido)["Akira"]

    llegadas.descontar(akira.producto, 2)

    akira.refresh_from_db()
    assert akira.respuesta == CONFIRMADA


# ---------------------------------------------------------------------------
# R2 · no más de lo pedido
# ---------------------------------------------------------------------------


def test_no_se_confirma_más_de_lo_pedido(pedido, administrador):
    akira = lineas(pedido)["Akira"]

    with pytest.raises(OperacionRechazada, match="más de lo pedido"):
        respuestas.responder(pedido, {akira.pk: (OTRA, 7)}, administrador)

    akira.refresh_from_db()
    assert akira.respuesta == LineaPedidoProveedor.SIN_RESPUESTA
    assert llegadas.pendiente(akira.producto) == 6


# ---------------------------------------------------------------------------
# R3 · sólo lo que cambió
# ---------------------------------------------------------------------------


def test_confirmar_otra_vez_no_anota_ni_audita(pedido, administrador):
    akira = lineas(pedido)["Akira"]
    respuestas.responder(pedido, {akira.pk: (CONFIRMADA, None)}, administrador)
    akira.refresh_from_db()
    antes = akira.respondida_en

    resultado = respuestas.responder(pedido, {akira.pk: (CONFIRMADA, None)}, administrador)

    akira.refresh_from_db()
    assert resultado.respondidas == 0
    assert akira.respondida_en == antes
    assert respuestas_auditadas(pedido).count() == 1


def test_la_misma_cantidad_otra_vez_no_anota(pedido, administrador):
    akira = lineas(pedido)["Akira"]
    respuestas.responder(pedido, {akira.pk: (OTRA, 3)}, administrador)

    resultado = respuestas.responder(pedido, {akira.pk: (OTRA, 3)}, administrador)

    assert resultado.respondidas == 0
    assert respuestas_auditadas(pedido).count() == 1


def test_cambiar_la_cantidad_sí_anota(pedido, administrador):
    akira = lineas(pedido)["Akira"]
    respuestas.responder(pedido, {akira.pk: (OTRA, 3)}, administrador)

    resultado = respuestas.responder(pedido, {akira.pk: (CONFIRMADA, None)}, administrador)

    akira.refresh_from_db()
    assert resultado.respondidas == 1
    assert (akira.respuesta, akira.cantidad_confirmada) == (CONFIRMADA, None)


# ---------------------------------------------------------------------------
# R4 · el motivo es de cada línea
# ---------------------------------------------------------------------------


def test_cada_línea_no_disponible_guarda_su_motivo(pedido, administrador):
    akira, berserk = lineas(pedido)["Akira"], lineas(pedido)["Berserk"]

    respuestas.responder(
        pedido,
        {
            akira.pk: (NO, None, "Está discontinuado"),
            berserk.pk: (NO, None, "Sin stock hasta marzo"),
        },
        administrador,
    )

    akira.refresh_from_db()
    berserk.refresh_from_db()
    assert akira.motivo_cierre == "Está discontinuado"
    assert berserk.motivo_cierre == "Sin stock hasta marzo"
    detalle = respuestas_auditadas(pedido).get().detalle
    assert "Está discontinuado" in detalle and "Sin stock hasta marzo" in detalle


def test_sin_motivo_propio_ni_general_no_se_cierra(pedido, administrador):
    akira = lineas(pedido)["Akira"]

    with pytest.raises(OperacionRechazada, match="obligatorio"):
        respuestas.responder(pedido, {akira.pk: (NO, None, "  ")}, administrador)

    akira.refresh_from_db()
    assert akira.estado == LineaPedidoProveedor.PENDIENTE


def test_el_motivo_general_sirve_a_las_que_no_traen(pedido, administrador):
    akira = lineas(pedido)["Akira"]

    respuestas.responder(pedido, {akira.pk: (NO, None)}, administrador, motivo="No tiene stock")

    akira.refresh_from_db()
    assert akira.motivo_cierre == "No tiene stock"


# ---------------------------------------------------------------------------
# La fecha y las consecuencias
# ---------------------------------------------------------------------------


def test_la_fecha_se_puede_borrar(pedido, administrador):
    respuestas.quitar_fecha(pedido, administrador)

    pedido.refresh_from_db()
    assert pedido.fecha_estimada is None
    assert "sin fecha" in respuestas_auditadas(pedido).get().detalle


def test_borrar_una_fecha_que_no_hay_lo_dice(pedido, administrador):
    respuestas.quitar_fecha(pedido, administrador)

    with pytest.raises(OperacionRechazada, match="ya no tiene fecha"):
        respuestas.quitar_fecha(pedido, administrador)


def test_confirmar_todo_con_la_fecha(pedido, administrador):
    nueva = DENTRO_DE_UN_MES + timedelta(days=3)

    respuestas.confirmar_todo(pedido, administrador, fecha=nueva)

    pedido.refresh_from_db()
    assert pedido.respondido and pedido.fecha_estimada == nueva


def test_no_puede_dice_qué_preventas_pierden_lo_que_esperaban(pedido, cliente):
    fijar_parametros(margen_cupo_preventa=0)
    akira = lineas(pedido)["Akira"]
    reservar(cliente, akira.producto, cantidad=2)

    consecuencias = respuestas.consecuencias_de_no_puede(pedido)

    assert consecuencias["lineas"] == 2
    ((fila),) = consecuencias["preventas"]
    assert (fila["producto"].pk, fila["reservas"], fila["quedan"]) == (akira.producto_id, 2, 0)


def test_mirar_las_consecuencias_no_cambia_nada(pedido):
    respuestas.consecuencias_de_no_puede(pedido)

    pedido.refresh_from_db()
    assert pedido.estado == PedidoProveedor.ABIERTO
    assert not respuestas_auditadas(pedido).exists()


# ---------------------------------------------------------------------------
# El resumen de la respuesta (ficha y propuesta)
# ---------------------------------------------------------------------------


def test_el_resumen_dice_hace_cuánto_espera(pedido):
    PedidoProveedor.objects.filter(pk=pedido.pk).update(
        creado_en=timezone.now() - timedelta(days=4)
    )
    pedido.refresh_from_db()

    resumen = pedido.respuesta_resumida

    assert resumen["clave"] == "esperando"
    assert resumen["texto"] == "Esperando respuesta hace 4 días"
    assert resumen["esperando"] == 2


@pytest.mark.parametrize(
    ("respuestas_de", "clave", "texto"),
    [
        ({"Akira": (CONFIRMADA, None), "Berserk": (CONFIRMADA, None)}, "todo", "Confirmó todo"),
        ({"Akira": (OTRA, 2), "Berserk": (CONFIRMADA, None)}, "cambios", "Confirmó con cambios"),
        ({"Akira": (NO, None, "x"), "Berserk": (NO, None, "y")}, "no_puede", "No puede abastecer"),
    ],
)
def test_el_resumen_de_lo_que_contestó(pedido, administrador, respuestas_de, clave, texto):
    por_titulo = lineas(pedido)
    respuestas.responder(
        pedido, {por_titulo[t].pk: v for t, v in respuestas_de.items()}, administrador
    )
    pedido.refresh_from_db()

    assert (pedido.respuesta_resumida["clave"], pedido.respuesta_resumida["texto"]) == (
        clave,
        texto,
    )


def test_un_pedido_sin_enviar_espera_un_reintento(ivrea):
    sin_enviar = llegadas.registrar(
        ivrea,
        PedidoProveedor.MANUAL,
        [(ProductoFactory(editorial=ivrea.editorial, stock=0, estado=Producto.AGOTADO), 2)],
        error_de_envio="Connection unexpectedly closed",
    )

    assert sin_enviar.respuesta_resumida["texto"] == "Esperando un reintento de envío"


def test_la_propuesta_dice_qué_espera(administrador, ivrea, mailoutbox):
    from apps.restock import servicios as restock

    fijar_parametros(cantidad_minima_restock=3, margen_stock_restock=2)
    ProductoFactory(editorial=ivrea.editorial, stock=0, estado=Producto.AGOTADO)
    propuesta = restock.ciclo_semanal().propuesta
    restock.despachar(propuesta, ivrea.pk, administrador)
    propuesta.refresh_from_db()

    assert propuesta.estado == PropuestaRestock.ESPERANDO
    assert propuesta.espera == "Esperando respuesta desde hoy"
    propuesta.pedidos.update(creado_en=timezone.now() - timedelta(days=2))
    assert PropuestaRestock.objects.get(pk=propuesta.pk).espera == "Esperando respuesta hace 2 días"
    propuesta.pedidos.update(estado=PedidoProveedor.SIN_ENVIAR)
    assert PropuestaRestock.objects.get(pk=propuesta.pk).espera == "Esperando un reintento de envío"


def test_una_propuesta_que_no_espera_no_dice_nada():
    assert PropuestaRestock(estado=PropuestaRestock.CERRADA).espera == ""


# ---------------------------------------------------------------------------
# Las pantallas
# ---------------------------------------------------------------------------


def url_responder(pedido, tipo):
    return reverse("suppliers:pedido_responder", args=[pedido.pk, tipo])


@pytest.mark.parametrize("tipo", ["todo", "cambios", "no-puede", "fecha"])
def test_cada_respuesta_tiene_su_pantalla_que_se_abre_como_diálogo(client_admin, pedido, tipo):
    respuesta = client_admin.get(url_responder(pedido, tipo))

    assert respuesta.status_code == 200
    assert "data-dialogo-contenido" in respuesta.content.decode()


def test_una_respuesta_que_no_existe_no_tiene_pantalla(client_admin, pedido):
    assert client_admin.get(url_responder(pedido, "cualquiera")).status_code == 404


def test_un_pedido_cerrado_no_abre_la_pantalla(client_admin, pedido, administrador):
    respuestas.no_puede(pedido, "No tiene stock", administrador)

    respuesta = client_admin.get(url_responder(pedido, "todo"))

    assert respuesta.status_code == 302


def test_con_cambios_muestra_cada_línea_con_sus_tres_opciones(client_admin, pedido):
    html = client_admin.get(url_responder(pedido, "cambios")).content.decode()

    for linea in pedido.lineas.all():
        assert f'name="respuesta-{linea.pk}" value="otra_cantidad"' in html
        assert f'name="motivo-{linea.pk}"' in html
        assert f'max="{linea.cantidad_pedida}"' in html


def test_no_puede_muestra_las_consecuencias(client_admin, pedido, cliente):
    fijar_parametros(margen_cupo_preventa=0)
    akira = lineas(pedido)["Akira"]
    reservar(cliente, akira.producto, cantidad=2)

    html = client_admin.get(url_responder(pedido, "no-puede")).content.decode()

    assert "Se cierran 2 productos sin recibir" in html
    assert str(akira.producto.especifico) in html
    assert 'data-dialogo-contenido="critico"' in html


def test_con_cambios_desde_la_web_con_un_motivo_por_línea(client_admin, pedido):
    akira, berserk = lineas(pedido)["Akira"], lineas(pedido)["Berserk"]

    client_admin.post(
        reverse("suppliers:pedido_respuesta", args=[pedido.pk]),
        {
            "accion": "cambios",
            f"respuesta-{akira.pk}": "otra_cantidad",
            f"cantidad-{akira.pk}": "2",
            f"respuesta-{berserk.pk}": "no_disponible",
            f"motivo-{berserk.pk}": "Está discontinuado",
        },
    )

    akira.refresh_from_db()
    berserk.refresh_from_db()
    assert (akira.respuesta, akira.cantidad_confirmada) == (OTRA, 2)
    assert (berserk.estado, berserk.motivo_cierre) == (
        LineaPedidoProveedor.SIN_RECIBIR,
        "Está discontinuado",
    )


def test_un_error_vuelve_a_la_misma_pantalla_con_la_ficha_de_origen(client_admin, pedido):
    akira = lineas(pedido)["Akira"]
    volver = reverse("suppliers:pedido_detalle", args=[pedido.pk])

    respuesta = client_admin.post(
        reverse("suppliers:pedido_respuesta", args=[pedido.pk]),
        {
            "accion": "cambios",
            f"respuesta-{akira.pk}": "otra_cantidad",
            f"cantidad-{akira.pk}": "99",
            "volver": volver,
        },
    )

    assert respuesta.url.startswith(url_responder(pedido, "cambios"))
    assert "volver=" in respuesta.url


def test_no_puede_con_otro_motivo_escrito(client_admin, pedido):
    client_admin.post(
        reverse("suppliers:pedido_respuesta", args=[pedido.pk]),
        {"accion": "nada", "motivo": "otro", "motivo_otro": "Cierra el local"},
    )

    assert set(pedido.lineas.values_list("motivo_cierre", flat=True)) == {"Cierra el local"}


def test_sin_fecha_desde_la_web(client_admin, pedido):
    client_admin.post(
        reverse("suppliers:pedido_respuesta", args=[pedido.pk]),
        {"accion": "fecha", "sin_fecha": "1"},
    )

    pedido.refresh_from_db()
    assert pedido.fecha_estimada is None


def test_la_fecha_vacía_sin_marcar_sin_fecha_lo_pide(client_admin, pedido):
    respuesta = client_admin.post(
        reverse("suppliers:pedido_respuesta", args=[pedido.pk]),
        {"accion": "fecha", "fecha": ""},
        follow=True,
    )

    assert "Sin fecha" in respuesta.content.decode()
    pedido.refresh_from_db()
    assert pedido.fecha_estimada == DENTRO_DE_UN_MES


def test_repetir_la_misma_respuesta_lo_dice(client_admin, pedido, administrador):
    respuestas.confirmar_todo(pedido, administrador)
    akira = lineas(pedido)["Akira"]

    respuesta = client_admin.post(
        reverse("suppliers:pedido_respuesta", args=[pedido.pk]),
        {"accion": "cambios", f"respuesta-{akira.pk}": "confirmada"},
        follow=True,
    )

    assert "No cambió nada" in respuesta.content.decode()


def test_la_advertencia_de_reservas_enlaza_la_demora(client_admin, pedido, cliente):
    fijar_parametros(margen_cupo_preventa=0)
    akira = lineas(pedido)["Akira"]
    reservar(cliente, akira.producto, cantidad=4)

    respuesta = client_admin.post(
        reverse("suppliers:pedido_respuesta", args=[pedido.pk]),
        {
            "accion": "cambios",
            f"respuesta-{akira.pk}": "otra_cantidad",
            f"cantidad-{akira.pk}": "2",
        },
        follow=True,
    )

    assert (
        f'href="{reverse("pedidos:demora", args=[akira.producto_id])}"'
        in respuesta.content.decode()
    )


def test_la_ficha_ya_no_tiene_campos_y_enlaza_la_llegada(client_admin, pedido):
    html = client_admin.get(reverse("suppliers:pedido_detalle", args=[pedido.pk])).content.decode()

    assert "llegaron_" not in html
    assert reverse("suppliers:pedido_llegada", args=[pedido.pk]) in html
    assert html.count("Akira") >= 1


def test_respondido_todo_la_ficha_se_achica_a_una_línea(client_admin, pedido, administrador):
    respuestas.confirmar_todo(pedido, administrador)

    html = client_admin.get(reverse("suppliers:pedido_detalle", args=[pedido.pk])).content.decode()

    assert "¿Qué contestó" not in html
    assert "2 confirmados" in html
    assert "Cambiar la fecha" in html


def test_la_llegada_se_carga_en_por_llegar_abierta_en_el_grupo_del_pedido(client_admin, pedido):
    # B-05-017: la ficha del pedido lleva a «Por llegar», al grupo de sus líneas.
    respuesta = client_admin.get(reverse("suppliers:pedido_llegada", args=[pedido.pk]))

    assert respuesta.url.startswith(reverse("suppliers:por_llegar") + "#grupo-")
    html = client_admin.get(reverse("suppliers:por_llegar")).content.decode()
    for linea in pedido.lineas.all():
        assert f'name="llegaron_l{linea.pk}"' in html


def test_una_llegada_vacía_vuelve_a_la_carga(client_admin, pedido):
    respuesta = client_admin.post(reverse("suppliers:pedido_llegada", args=[pedido.pk]), {})

    assert respuesta.url == reverse("suppliers:pedido_llegada", args=[pedido.pk])


# Foco reforzado: control de acceso por la dirección real.


@pytest.mark.parametrize("rol", [Usuario.CAJERO, Usuario.CLIENTE])
@pytest.mark.parametrize("tipo", ["todo", "no-puede"])
def test_el_rol_equivocado_no_ve_las_pantallas_de_respuesta(client, pedido, rol, tipo):
    client.force_login(UsuarioFactory(rol=rol))

    assert client.get(url_responder(pedido, tipo)).status_code in (403, 302)


@pytest.mark.parametrize("rol", [Usuario.CAJERO, Usuario.CLIENTE])
def test_el_rol_equivocado_no_carga_la_llegada(client, pedido, rol):
    client.force_login(UsuarioFactory(rol=rol))

    assert client.get(reverse("suppliers:pedido_llegada", args=[pedido.pk])).status_code in (
        403,
        302,
    )
