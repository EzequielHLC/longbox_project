"""Pruebas de contrato de CU-ALT-REV: `CO-159`, `CO-160`, `CO-020` a `CO-025`.

Las reglas están en `test_revision_borradores.py` y la pantalla en
`test_pantalla_revision.py`. Acá, cada postcondición de los contratos por la
dirección real, incluidas las negativas: lo que se consulta no abre sesión, y lo
que se excluye de un lote no se toca. La red está cortada: el envío de los
pedidos pasa por la puerta de correo de prueba.
"""

from unittest.mock import patch

import pytest
from django.urls import reverse
from django.utils import timezone

from apps.accounts.tests.factories import UsuarioFactory
from apps.catalog.models import BorradorProducto, ConfianzaCampo, Producto, SesionRevision
from apps.catalog.tests.factories import EditorialFactory, ProductoFactory, TipoFactory
from apps.catalog.tests.test_pantalla_revision import (
    CERRAR,
    EN_LOTE,
    LISTA,
    borrador_de,
    campos_de,
    ficha,
)
from apps.core.models import RegistroAuditoria
from apps.suppliers.models import CorreoProveedor
from apps.suppliers.tests.factories import ProveedorFactory

pytestmark = pytest.mark.django_db


@pytest.fixture
def proveedor(db):
    return ProveedorFactory(
        editorial=EditorialFactory(nombre="Ivrea"),
        tipo_por_defecto=TipoFactory(nombre="Manga", usa_formato=True),
    )


@pytest.fixture
def correo(db, proveedor):
    return CorreoProveedor.objects.create(
        proveedor=proveedor,
        message_id="<uno@ivrea.test>",
        remitente=proveedor.correo_comercial,
        estado=CorreoProveedor.PROCESADO,
    )


BERSERK = "9789878271583"


def auditorias(accion):
    return RegistroAuditoria.objects.filter(accion=accion)


def con_duda(borrador, campo="precio"):
    return ConfianzaCampo.objects.create(borrador=borrador, campo=campo, nivel=ConfianzaCampo.BAJA)


# ---------------------------------------------------------------------------
# CO-159 · consultarColaDeBorradores · CO-160 · abrirBorrador
# ---------------------------------------------------------------------------


def test_CO159_lista_los_pendientes_con_confianza_reparos_estado_y_stock(client_admin, correo):
    borrador = borrador_de(correo, reparos=["El ISBN no cierra"], stock_inicial=7)
    con_duda(borrador)
    borrador_de(correo, titulo="Ya rechazado", volumen=9, estado=BorradorProducto.RECHAZADO)

    respuesta = client_admin.get(LISTA)

    assert [b.pk for b in respuesta.context["borradores"]] == [borrador.pk]
    contenido = respuesta.content.decode()
    assert "Berserk Deluxe" in contenido
    assert "Ya rechazado" not in contenido


def test_CO159_E1_sin_pendientes_lo_informa(client_admin, correo):
    assert "No hay borradores pendientes" in client_admin.get(LISTA).content.decode()


def test_CO160_muestra_campos_confianzas_y_reparos(client_admin, correo):
    borrador = borrador_de(correo, reparos=["El ISBN no cierra"])
    con_duda(borrador)

    respuesta = client_admin.get(ficha(borrador))

    contenido = respuesta.content.decode()
    assert respuesta.context["confianzas"]["precio"].nivel == ConfianzaCampo.BAJA
    assert "El ISBN no cierra" in contenido
    assert 'name="revisado"' in contenido


def test_CO159_CO160_consultar_no_modifica_nada_ni_abre_sesion(client_admin, correo):
    borrador = borrador_de(correo)

    client_admin.get(LISTA)
    client_admin.get(ficha(borrador))

    borrador.refresh_from_db()
    assert borrador.estado == BorradorProducto.PENDIENTE
    assert not SesionRevision.objects.exists()


# ---------------------------------------------------------------------------
# CO-020 · editarBorrador · CO-021 · marcarCampoRevisado
# ---------------------------------------------------------------------------


def test_CO020_los_atributos_y_el_stock_inicial_pasan_a_lo_declarado(client_admin, correo):
    borrador = borrador_de(correo, stock_inicial=2)

    client_admin.post(
        ficha(borrador), campos_de(borrador, titulo="Berserk Maximum", stock_inicial=6)
    )

    borrador.refresh_from_db()
    assert borrador.titulo == "Berserk Maximum"
    assert borrador.stock_inicial == 6
    assert borrador.estado == BorradorProducto.PENDIENTE
    assert not Producto.objects.exists()


def test_CO020_completar_los_bloqueantes_lo_pasa_a_pendiente(client_admin, correo):
    borrador = borrador_de(correo, precio=None, estado=BorradorProducto.INCOMPLETO)

    client_admin.post(ficha(borrador), campos_de(borrador, precio="24900"))

    borrador.refresh_from_db()
    assert borrador.estado == BorradorProducto.PENDIENTE


def test_CO020_si_sigue_faltando_un_bloqueante_sigue_incompleto(client_admin, correo):
    borrador = borrador_de(correo, precio=None, titulo="", estado=BorradorProducto.INCOMPLETO)

    client_admin.post(ficha(borrador), campos_de(borrador, precio="24900"))

    borrador.refresh_from_db()
    assert borrador.estado == BorradorProducto.INCOMPLETO


def test_CO021_el_campo_pasa_a_revisado(client_admin, correo):
    borrador = borrador_de(correo)
    confianza = con_duda(borrador)

    client_admin.post(ficha(borrador), campos_de(borrador, revisado="precio"))

    confianza.refresh_from_db()
    assert confianza.revisado is True


# ---------------------------------------------------------------------------
# CO-022 · confirmarBorrador
# ---------------------------------------------------------------------------


def test_CO022_crea_el_producto_con_los_valores_del_borrador(
    client_admin, correo, proveedor, administrador
):
    borrador = borrador_de(correo, isbn=BERSERK, stock_inicial=4)
    antes = timezone.now()

    client_admin.post(ficha(borrador), campos_de(borrador, confirmar="1"))

    producto = Producto.objects.get().productoeditorial
    # (a) y (c) del producto
    assert producto.codigo
    assert producto.titulo == "Berserk Deluxe"
    assert producto.volumen == 5
    assert producto.isbn == BERSERK
    assert producto.precio == borrador.precio
    assert producto.stock == 4
    assert producto.estado == borrador.estado_sugerido
    # (b)
    assert producto.tipo == borrador.tipo
    assert producto.editorial == borrador.editorial
    assert producto.proveedor_id == proveedor.pk
    # El borrador y la sesión
    borrador.refresh_from_db()
    sesion = SesionRevision.objects.get()
    assert borrador.estado == BorradorProducto.CONFIRMADO
    assert borrador.sesion == sesion
    assert borrador.resuelto_por == administrador
    assert antes <= borrador.resuelto_en <= timezone.now()
    assert sesion.estado == SesionRevision.ABIERTA
    assert antes <= sesion.abierta_en <= timezone.now()
    registro = auditorias(RegistroAuditoria.BORRADOR_CONFIRMADO).get()
    assert registro.actor == administrador


def test_CO022_la_segunda_decision_sigue_en_la_misma_sesion(client_admin, correo):
    primero, segundo = borrador_de(correo), borrador_de(correo, titulo="Vagabond", volumen=1)

    client_admin.post(ficha(primero), campos_de(primero, confirmar="1"))
    client_admin.post(ficha(segundo), campos_de(segundo, confirmar="1"))

    assert SesionRevision.objects.count() == 1


def test_CO022_E3_un_bloqueante_vacio_bloquea(client_admin, correo):
    borrador = borrador_de(correo, precio=None, estado=BorradorProducto.INCOMPLETO)

    client_admin.post(ficha(borrador), campos_de(borrador, confirmar="1"))

    borrador.refresh_from_db()
    assert not Producto.objects.exists()
    assert borrador.esta_abierto
    assert not auditorias(RegistroAuditoria.BORRADOR_CONFIRMADO).exists()


def test_CO022_E7_la_colision_se_bloquea_antes_de_crear_y_enlaza_la_ficha(client_admin, correo):
    existente = ProductoFactory(isbn=BERSERK)
    borrador = borrador_de(correo, isbn=BERSERK)

    respuesta = client_admin.post(ficha(borrador), campos_de(borrador, confirmar="1"), follow=True)

    borrador.refresh_from_db()
    assert Producto.objects.count() == 1
    assert borrador.esta_abierto
    assert reverse("catalog:producto_detalle", args=[existente.pk]) in respuesta.content.decode()
    assert "por ISBN" in respuesta.content.decode()


def test_CO022_E7_por_combinacion_lo_dice(client_admin, correo):
    ProductoFactory(
        titulo="Berserk Deluxe",
        volumen=5,
        editorial=correo.proveedor.editorial,
        tipo=correo.proveedor.tipo_por_defecto,
        formato=None,
        isbn="",
    )
    borrador = borrador_de(correo)

    contenido = client_admin.get(ficha(borrador)).content.decode()

    assert "por título, volumen, tipo, formato y editorial" in contenido


def test_CO022_precondicion_confianza_baja_sin_revisar_bloquea(client_admin, correo):
    borrador = borrador_de(correo)
    con_duda(borrador)

    client_admin.post(ficha(borrador), campos_de(borrador, confirmar="1"))

    assert not Producto.objects.exists()


# ---------------------------------------------------------------------------
# CO-023 · confirmarBorradoresEnLote
# ---------------------------------------------------------------------------


def test_CO023_confirma_los_elegibles_y_no_toca_los_excluidos(client_admin, correo):
    elegible = borrador_de(correo)
    dudoso = borrador_de(correo, titulo="Vagabond", volumen=1)
    con_duda(dudoso)

    client_admin.post(EN_LOTE, {"borrador": [elegible.pk, dudoso.pk]})

    elegible.refresh_from_db()
    dudoso.refresh_from_db()
    assert elegible.estado == BorradorProducto.CONFIRMADO
    assert Producto.objects.count() == 1
    # Los excluidos no fueron modificados: siguen en la cola, sin sesión ni responsable.
    assert dudoso.estado == BorradorProducto.PENDIENTE
    assert dudoso.sesion is None
    assert dudoso.resuelto_por is None
    assert dudoso.resuelto_en is None
    assert auditorias(RegistroAuditoria.BORRADOR_CONFIRMADO).count() == 1


# ---------------------------------------------------------------------------
# CO-024 · rechazarBorrador
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("estado", [BorradorProducto.PENDIENTE, BorradorProducto.INCOMPLETO])
def test_CO024_pasa_a_rechazado_con_motivo_sesion_y_responsable(
    client_admin, correo, administrador, estado
):
    borrador = borrador_de(correo, estado=estado)

    client_admin.post(ficha(borrador), {"rechazar": "1", "motivo": "No lo vamos a traer."})

    borrador.refresh_from_db()
    assert borrador.estado == BorradorProducto.RECHAZADO
    assert borrador.motivo_rechazo == "No lo vamos a traer."
    assert borrador.sesion == SesionRevision.objects.get()
    assert borrador.resuelto_por == administrador
    assert borrador.resuelto_en is not None
    assert auditorias(RegistroAuditoria.BORRADOR_RECHAZADO).get().actor == administrador
    assert not Producto.objects.exists()


def test_CO024_precondicion_sin_motivo_no_rechaza(client_admin, correo):
    borrador = borrador_de(correo)

    client_admin.post(ficha(borrador), {"rechazar": "1", "motivo": ""})

    borrador.refresh_from_db()
    assert borrador.estado == BorradorProducto.PENDIENTE
    assert not SesionRevision.objects.exists()


# ---------------------------------------------------------------------------
# CO-025 · cerrarSesionDeRevision
# ---------------------------------------------------------------------------


def test_CO025_cierra_la_sesion_con_el_resultado_por_proveedor(
    client_admin, correo, proveedor, administrador, mailoutbox
):
    borrador = borrador_de(correo)
    client_admin.post(ficha(borrador), campos_de(borrador, confirmar="1"))
    antes = timezone.now()

    client_admin.post(CERRAR)

    sesion = SesionRevision.objects.get()
    assert sesion.estado == SesionRevision.CERRADA
    assert antes <= sesion.cerrada_en <= timezone.now()
    assert len(sesion.envios) == 1
    assert [correo.to for correo in mailoutbox] == [[proveedor.correo_comercial]]


def test_CO025_encadena_CO074_con_su_entrada_por_proveedor(client_admin, correo, proveedor):
    borrador = borrador_de(correo)
    client_admin.post(ficha(borrador), campos_de(borrador, confirmar="1"))

    client_admin.post(CERRAR)

    pedido = auditorias(RegistroAuditoria.PEDIDO_A_PROVEEDOR).get()
    assert pedido.objetivo_pk == proveedor.pk
    assert "Enviado" in pedido.detalle


def test_CO025_la_entrada_del_cierre_trae_el_resumen(client_admin, correo, administrador):
    confirmado = borrador_de(correo)
    rechazado = borrador_de(correo, titulo="Vagabond", volumen=1)
    borrador_de(correo, titulo="Pendiente", volumen=2)
    client_admin.post(ficha(confirmado), campos_de(confirmado, confirmar="1"))
    client_admin.post(ficha(rechazado), {"rechazar": "1", "motivo": "No va."})

    client_admin.post(CERRAR)

    registro = auditorias(RegistroAuditoria.SESION_REVISION_CERRADA).get()
    assert registro.actor == administrador
    for parte in (
        "1 confirmado(s)",
        "1 rechazado(s)",
        "1 pendiente(s)",
        "1 correo(s) de pedido enviado(s)",
    ):
        assert parte in registro.detalle


def test_CO025_E5_un_envio_fallido_no_revierte_los_productos(client_admin, correo, proveedor):
    borrador = borrador_de(correo)
    client_admin.post(ficha(borrador), campos_de(borrador, confirmar="1"))

    with patch("apps.suppliers.pedidos.enviar_correo", side_effect=OSError("caído")):
        respuesta = client_admin.post(CERRAR, follow=True)

    assert Producto.objects.count() == 1
    assert SesionRevision.objects.get().estado == SesionRevision.CERRADA
    assert proveedor.razon_social in respuesta.content.decode()
    assert "No se envió" in auditorias(RegistroAuditoria.PEDIDO_A_PROVEEDOR).get().detalle
    assert "1 fallido(s)" in auditorias(RegistroAuditoria.SESION_REVISION_CERRADA).get().detalle


def test_CO025_E6_sin_confirmaciones_no_se_envia_nada(client_admin, correo, mailoutbox):
    borrador = borrador_de(correo)
    client_admin.post(ficha(borrador), {"rechazar": "1", "motivo": "No va."})

    client_admin.post(CERRAR)

    assert SesionRevision.objects.get().estado == SesionRevision.CERRADA
    assert mailoutbox == []
    assert not auditorias(RegistroAuditoria.PEDIDO_A_PROVEEDOR).exists()
    assert "0 confirmado(s)" in auditorias(RegistroAuditoria.SESION_REVISION_CERRADA).get().detalle


def test_CO025_precondicion_sin_sesion_abierta_no_registra_cierre(client_admin, correo):
    client_admin.post(CERRAR)

    assert not auditorias(RegistroAuditoria.SESION_REVISION_CERRADA).exists()


# ---------------------------------------------------------------------------
# Control de acceso: por la dirección real, con el rol equivocado
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("rol", ["cajero", "cliente"])
def test_CO020_a_CO025_otro_rol_no_resuelve_borradores(client, correo, rol):
    client.force_login(UsuarioFactory(rol=rol))
    borrador = borrador_de(correo)

    client.post(ficha(borrador), campos_de(borrador, titulo="Otro", confirmar="1"))
    client.post(ficha(borrador), {"rechazar": "1", "motivo": "No va."})
    client.post(EN_LOTE, {"borrador": [borrador.pk]})
    client.post(CERRAR)

    borrador.refresh_from_db()
    assert borrador.titulo == "Berserk Deluxe"
    assert borrador.estado == BorradorProducto.PENDIENTE
    assert not Producto.objects.exists()
    assert not SesionRevision.objects.exists()
