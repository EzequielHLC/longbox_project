"""Contratos de restock (plan 05): `CO-067` a `CO-077`, `CO-174`, `CO-175`."""

from datetime import timedelta
from unittest import mock

import pytest
from django.urls import reverse
from django.utils import timezone

from apps.accounts.tests.factories import UsuarioFactory
from apps.catalog.models import Producto
from apps.catalog.tests.factories import EditorialFactory, ProductoFactory
from apps.catalog.tests.test_edicion_producto import datos_editoriales
from apps.core.models import RegistroAuditoria
from apps.restock import servicios
from apps.restock.models import LineaPropuestaRestock, PropuestaRestock, SuscripcionReposicion
from apps.suppliers.tests.factories import ProveedorFactory
from apps.tienda.tests.compra_util import fijar_parametros


def _acciones(accion):
    return RegistroAuditoria.objects.filter(accion=accion)


def _agotado(**extra):
    return ProductoFactory(stock=0, estado=Producto.AGOTADO, **extra)


def _ficha(producto):
    return reverse("core:tienda_producto", args=[producto.pk])


def _aviso(producto):
    return reverse("restock:aviso", args=[producto.pk])


def _suscriptos(producto, cantidad):
    """`cantidad` clientes en espera, en orden de llegada."""
    ahora = timezone.now()
    return [
        SuscripcionReposicion.objects.create(
            usuario=UsuarioFactory(rol="cliente"),
            producto=producto,
            creada_en=ahora - timedelta(minutes=cantidad - i),
        )
        for i in range(cantidad)
    ]


# ---------------------------------------------------------------------------
# CO-075 suscribirseAReposicion · CO-076 cancelarSuscripcionDeReposicion
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_CO075_suscribirse_desde_la_ficha_de_un_agotado(client, cliente):
    producto = _agotado()
    client.force_login(cliente)
    registros = RegistroAuditoria.objects.count()

    antes = client.get(_ficha(producto))
    respuesta = client.post(_aviso(producto), follow=True)

    suscripcion = SuscripcionReposicion.objects.get()
    assert "Avisarme cuando haya stock" in antes.content.decode()
    assert (suscripcion.usuario, suscripcion.producto_id) == (cliente, producto.pk)
    assert suscripcion.estado == SuscripcionReposicion.ACTIVA
    assert servicios.en_espera(producto) == 1
    contenido = respuesta.content.decode()
    assert "Te avisaremos cuando este producto vuelva a estar disponible." in contenido
    assert "Suscripto" in contenido and "Cancelar aviso" in contenido
    assert "1 persona espera" in contenido
    assert RegistroAuditoria.objects.count() == registros  # sin auditoría


@pytest.mark.django_db
def test_CO075_E1_no_registra_un_duplicado(client, cliente):
    producto = _agotado()
    client.force_login(cliente)

    client.post(_aviso(producto))
    client.post(_aviso(producto))

    assert SuscripcionReposicion.objects.count() == 1


@pytest.mark.django_db
def test_CO075_E2_si_ya_hay_stock_no_se_suscribe(client, cliente):
    producto = ProductoFactory(stock=2, estado=Producto.ACTIVO)
    client.force_login(cliente)

    respuesta = client.post(_aviso(producto), follow=True)

    assert not SuscripcionReposicion.objects.exists()
    assert "ya tiene unidades disponibles" in respuesta.content.decode()


@pytest.mark.django_db
def test_CO075_el_invitado_va_al_ingreso_y_el_personal_no_puede(client, cajero):
    producto = _agotado()

    invitado = client.post(_aviso(producto))
    client.force_login(cajero)
    personal = client.post(_aviso(producto))

    assert invitado.url.startswith(reverse("accounts:login"))
    assert personal.status_code == 403
    assert not SuscripcionReposicion.objects.exists()


@pytest.mark.django_db
def test_CO076_cancelar_elimina_la_suscripcion_sin_auditar(client, cliente):
    producto = _agotado()
    client.force_login(cliente)
    client.post(_aviso(producto))
    registros = RegistroAuditoria.objects.count()

    respuesta = client.post(_aviso(producto), {"accion": "cancelar"}, follow=True)

    assert not SuscripcionReposicion.objects.exists()
    assert servicios.en_espera(producto) == 0
    assert "Avisarme cuando haya stock" in respuesta.content.decode()
    assert RegistroAuditoria.objects.count() == registros


# ---------------------------------------------------------------------------
# CO-077 notificarReposicionASuscriptores
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_CO077_reponer_por_la_edicion_avisa_a_los_primeros_n(
    client_admin, mailoutbox, django_capture_on_commit_callbacks
):
    producto = _agotado()
    suscripciones = _suscriptos(producto, 5)

    with django_capture_on_commit_callbacks(execute=True):
        client_admin.post(
            reverse("catalog:producto_editar", args=[producto.pk]),
            datos_editoriales(producto, stock=3),
        )

    producto.refresh_from_db()
    estados = [SuscripcionReposicion.objects.get(pk=s.pk).estado for s in suscripciones]
    assert producto.estado == Producto.ACTIVO  # B-05-006
    assert estados == [SuscripcionReposicion.NOTIFICADA] * 3 + [SuscripcionReposicion.ACTIVA] * 2
    assert {m.to[0] for m in mailoutbox} == {s.usuario.email for s in suscripciones[:3]}
    assert _ficha(producto) in mailoutbox[0].body
    assert servicios.en_espera(producto) == 2
    entrada = _acciones(RegistroAuditoria.NOTIFICACION_REPOSICION).get()
    assert "ingresaron 3" in entrada.detalle
    assert "3 suscriptor(es) notificado(s), 2 en espera" in entrada.detalle


@pytest.mark.django_db
def test_CO077_con_mas_unidades_que_suscriptores_avisa_a_todos(mailoutbox):
    producto = _agotado()
    _suscriptos(producto, 2)

    resultado = servicios.reposicion(producto, 10)

    assert len(resultado.notificadas) == 2
    assert servicios.en_espera(producto) == 0


@pytest.mark.django_db
def test_CO077_A1_sin_suscriptores_no_registra_nada(mailoutbox):
    producto = _agotado()
    registros = RegistroAuditoria.objects.count()

    servicios.reposicion(producto, 4)

    assert mailoutbox == []
    assert RegistroAuditoria.objects.count() == registros


@pytest.mark.django_db
def test_CO077_E1_un_envio_que_falla_tres_veces_conserva_el_turno(mailoutbox):
    producto = _agotado()
    primero, segundo = _suscriptos(producto, 2)
    destinatarios = []

    def enviar(**kwargs):
        destinatarios.append(kwargs["destinatarios"][0])
        if kwargs["destinatarios"] == [primero.usuario.email]:
            raise OSError("servidor caído")

    with mock.patch("apps.restock.servicios.enviar_correo", side_effect=enviar):
        resultado = servicios.reposicion(producto, 1)
    primero.refresh_from_db()

    assert destinatarios.count(primero.usuario.email) == 3
    assert resultado.fallidas == [primero]
    assert primero.estado == SuscripcionReposicion.FALLIDA
    assert _acciones(RegistroAuditoria.NOTIFICACION_FALLIDA).exists()
    # La ronda siguiente lo vuelve a tomar primero (B-05-005).
    siguiente = servicios.reposicion(producto, 1)
    assert [s.pk for s in siguiente.notificadas] == [primero.pk]
    segundo.refresh_from_db()
    assert segundo.estado == SuscripcionReposicion.ACTIVA


@pytest.mark.django_db
def test_CO077_E2_quien_cancela_no_cede_su_cupo(mailoutbox):
    producto = _agotado()
    uno, dos, tres = _suscriptos(producto, 3)
    original = servicios._avisar_reposicion

    def avisar(suscripcion, enlace):
        if suscripcion.pk == uno.pk:
            SuscripcionReposicion.objects.filter(pk=dos.pk).delete()
        return original(suscripcion, enlace)

    with mock.patch.object(servicios, "_avisar_reposicion", avisar):
        resultado = servicios.reposicion(producto, 2)

    tres.refresh_from_db()
    assert [s.pk for s in resultado.notificadas] == [uno.pk]
    assert tres.estado == SuscripcionReposicion.ACTIVA


@pytest.mark.django_db
def test_CO077_el_articulo_que_vuelve_por_vencimiento_tambien_avisa(
    cliente, mailoutbox, django_capture_on_commit_callbacks
):
    from apps.almacen import servicios as almacen
    from apps.almacen.tests.util import retenido

    producto = _agotado()
    retenido(cliente, vence_en=0, producto=producto)
    (espera,) = _suscriptos(producto, 1)

    with django_capture_on_commit_callbacks(execute=True):
        almacen.ciclo_de_vencimiento()

    espera.refresh_from_db()
    assert espera.estado == SuscripcionReposicion.NOTIFICADA


@pytest.mark.django_db
def test_CO077_bajar_el_stock_no_avisa(
    client_admin, mailoutbox, django_capture_on_commit_callbacks
):
    producto = ProductoFactory(stock=5, estado=Producto.ACTIVO)
    _suscriptos(producto, 1)

    with django_capture_on_commit_callbacks(execute=True):
        client_admin.post(
            reverse("catalog:producto_editar", args=[producto.pk]),
            datos_editoriales(producto, stock=2),
        )

    assert not _acciones(RegistroAuditoria.NOTIFICACION_REPOSICION).exists()


# ---------------------------------------------------------------------------
# CO-067 ejecutarCicloDePropuestaDeRestock · CO-068 generarPropuestaDeRestock
# ---------------------------------------------------------------------------


@pytest.fixture
def parametros(db):
    return fijar_parametros(cantidad_minima_restock=3, margen_stock_restock=2)


@pytest.mark.django_db
def test_CO067_arma_la_propuesta_por_proveedor_con_la_cantidad_sugerida(
    parametros, administrador, mailoutbox, django_capture_on_commit_callbacks
):
    ivrea = EditorialFactory(nombre="Ivrea")
    proveedor = ProveedorFactory(razon_social="Distribuidora Ivrea", editorial=ivrea)
    con_demanda = _agotado(editorial=ivrea, titulo="Akira")
    _suscriptos(con_demanda, 4)
    sin_demanda = ProductoFactory(stock=1, estado=Producto.ACTIVO, editorial=ivrea)
    huerfano = _agotado()  # su editorial no tiene proveedor
    ProductoFactory(stock=2, estado=Producto.ACTIVO)  # no está bajo el margen
    ProductoFactory(stock=0, estado=Producto.PRE_VENTA)  # no se repone

    with django_capture_on_commit_callbacks(execute=True):
        resultado = servicios.ciclo_semanal()

    propuesta = resultado.propuesta
    assert (propuesta.estado, propuesta.tipo_disparo) == (
        PropuestaRestock.PENDIENTE,
        PropuestaRestock.AUTOMATICO,
    )
    grupos = servicios.agrupar(propuesta)
    assert [g.nombre for g in grupos] == ["Distribuidora Ivrea", "Sin proveedor"]
    assert grupos[0].proveedor == proveedor
    assert [linea.producto for linea in grupos[0].lineas] == [con_demanda, sin_demanda]
    lineas = {linea.producto_id: linea for linea in propuesta.lineas.all()}
    assert lineas[con_demanda.pk].cantidad_sugerida == 6  # 4 suscriptores + margen 2
    assert lineas[sin_demanda.pk].cantidad_sugerida == 3  # la mínima
    assert lineas[con_demanda.pk].suscriptores_activos == 4
    assert lineas[huerfano.pk].estado_despacho == LineaPropuestaRestock.PENDIENTE
    assert not any(linea.anadida_a_mano for linea in lineas.values())
    entrada = _acciones(RegistroAuditoria.PROPUESTA_RESTOCK).get()
    assert (
        "automático" in entrada.detalle and "Distribuidora Ivrea: 2 producto(s)" in entrada.detalle
    )
    assert mailoutbox[-1].to == [administrador.email]


@pytest.mark.django_db
def test_CO067_E1_sin_elegibles_no_genera_y_lo_registra_una_vez_por_semana(parametros):
    ProductoFactory(stock=10, estado=Producto.ACTIVO)

    primero = servicios.ciclo_semanal()
    segundo = servicios.ciclo_semanal()

    assert primero.motivo == segundo.motivo == "sin_elegibles"
    assert not PropuestaRestock.objects.exists()
    assert _acciones(RegistroAuditoria.PROPUESTA_RESTOCK).count() == 1


@pytest.mark.django_db
def test_CO067_E3_con_una_pendiente_no_genera_otra_y_avisa(parametros, administrador, mailoutbox):
    _agotado()
    PropuestaRestock.objects.create(
        tipo_disparo=PropuestaRestock.MANUAL,
        fecha_generacion=timezone.now() - timedelta(days=10),
    )

    resultado = servicios.ciclo_semanal()

    assert resultado.motivo == "pendiente"
    assert PropuestaRestock.objects.count() == 1
    assert any("pendiente" in m.subject.lower() for m in mailoutbox)


@pytest.mark.django_db
def test_CO067_E4_se_abstiene_si_hubo_una_propuesta_en_la_semana(parametros):
    _agotado()
    PropuestaRestock.objects.create(
        tipo_disparo=PropuestaRestock.MANUAL,
        estado=PropuestaRestock.CERRADA,
        fecha_generacion=timezone.now() - timedelta(days=3),
    )

    resultado = servicios.ciclo_semanal()

    assert resultado.motivo == "reciente"
    assert PropuestaRestock.objects.count() == 1


@pytest.mark.django_db
def test_CO068_el_disparo_manual_genera_aunque_haya_una_reciente_y_omite_el_ciclo(
    parametros, client_admin, administrador
):
    _agotado()
    PropuestaRestock.objects.create(
        tipo_disparo=PropuestaRestock.AUTOMATICO,
        estado=PropuestaRestock.CERRADA,
        fecha_generacion=timezone.now() - timedelta(days=2),
    )

    client_admin.post(reverse("restock:generar"))
    automatico = servicios.ciclo_semanal()

    nueva = PropuestaRestock.objects.get(estado=PropuestaRestock.PENDIENTE)
    assert nueva.tipo_disparo == PropuestaRestock.MANUAL
    assert automatico.motivo == "reciente"
    entrada = _acciones(RegistroAuditoria.PROPUESTA_RESTOCK).get()
    assert entrada.actor == administrador and "Se omite el ciclo" in entrada.detalle


@pytest.mark.django_db
def test_CO068_E1_sin_elegibles_igual_omite_el_ciclo_de_la_semana(parametros, administrador):
    resultado = servicios.generar_manual(administrador)
    automatico = servicios.ciclo_semanal()

    assert resultado.propuesta.estado == PropuestaRestock.CERRADA
    assert automatico.motivo == "reciente"


@pytest.mark.django_db
def test_CO068_E3_con_una_pendiente_se_rechaza(parametros, client_admin):
    _agotado()
    PropuestaRestock.objects.create(tipo_disparo=PropuestaRestock.MANUAL)

    respuesta = client_admin.post(reverse("restock:generar"), follow=True)

    assert PropuestaRestock.objects.count() == 1
    assert "Ya hay una propuesta pendiente" in respuesta.content.decode()


# ---------------------------------------------------------------------------
# CO-174, CO-175 y los ajustes: CO-069, CO-070, CO-071
# ---------------------------------------------------------------------------


@pytest.fixture
def propuesta(parametros):
    editorial = EditorialFactory()
    proveedor = ProveedorFactory(editorial=editorial)
    _agotado(editorial=editorial)
    _agotado(editorial=editorial)
    resultado = servicios.ciclo_semanal()
    resultado.propuesta.proveedor_de_prueba = proveedor
    return resultado.propuesta


@pytest.mark.django_db
def test_CO174_muestra_la_propuesta_por_proveedor(client_admin, propuesta):
    respuesta = client_admin.get(reverse("restock:propuesta"))

    grupos = respuesta.context["grupos"]
    assert [g.proveedor for g in grupos] == [propuesta.proveedor_de_prueba]
    assert propuesta.proveedor_de_prueba.razon_social in respuesta.content.decode()


@pytest.mark.django_db
def test_CO174_E1_sin_propuesta_lo_dice(client_admin):
    respuesta = client_admin.get(reverse("restock:propuesta"))

    assert respuesta.context["propuesta"] is None
    assert "No hay una propuesta pendiente" in respuesta.content.decode()


@pytest.mark.django_db
def test_CO175_lista_las_lineas_del_proveedor(client_admin, propuesta):
    clave = propuesta.proveedor_de_prueba.pk

    respuesta = client_admin.get(reverse("restock:proveedor", args=[clave]))

    assert len(respuesta.context["grupo"].lineas) == 2


@pytest.mark.django_db
def test_CO069_ajustar_la_cantidad_conserva_los_suscriptores(client_admin, propuesta):
    linea = propuesta.lineas.first()
    suscriptores = linea.suscriptores_activos

    client_admin.post(reverse("restock:linea", args=[linea.pk]), {"cantidad": "12"})
    client_admin.post(reverse("restock:linea", args=[linea.pk]), {"cantidad": "0"})

    linea.refresh_from_db()
    assert (linea.cantidad_sugerida, linea.suscriptores_activos) == (12, suscriptores)


@pytest.mark.django_db
def test_CO070_quitar_elimina_la_linea(client_admin, propuesta):
    linea = propuesta.lineas.first()

    client_admin.post(reverse("restock:linea", args=[linea.pk]), {"accion": "quitar"})

    assert not LineaPropuestaRestock.objects.filter(pk=linea.pk).exists()
    assert propuesta.lineas.count() == 1


@pytest.mark.django_db
def test_CO071_agregar_va_al_grupo_de_su_proveedor(client_admin, propuesta):
    otra_editorial = EditorialFactory()
    otro = ProveedorFactory(editorial=otra_editorial)
    producto = ProductoFactory(stock=20, editorial=otra_editorial)
    _suscriptos(producto, 2)

    client_admin.post(reverse("restock:agregar"), {"producto": producto.codigo, "cantidad": "4"})
    repetido = client_admin.post(
        reverse("restock:agregar"), {"producto": producto.codigo, "cantidad": "4"}, follow=True
    )

    linea = propuesta.lineas.get(producto=producto)
    assert (linea.cantidad_sugerida, linea.anadida_a_mano, linea.suscriptores_activos) == (
        4,
        True,
        2,
    )
    assert linea in servicios.grupo_de(propuesta, otro.pk).lineas
    assert "ya está en la propuesta" in repetido.content.decode()


# ---------------------------------------------------------------------------
# CO-072 despacharPedidoAProveedor · CO-073 descartarProveedorDePropuesta · CO-074
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_CO072_despachar_envia_el_correo_y_marca_las_lineas(
    client_admin, administrador, propuesta, mailoutbox
):
    proveedor = propuesta.proveedor_de_prueba

    client_admin.post(reverse("restock:proveedor", args=[proveedor.pk]))

    propuesta.refresh_from_db()
    assert set(propuesta.lineas.values_list("estado_despacho", flat=True)) == {
        LineaPropuestaRestock.DESPACHADO
    }
    assert mailoutbox[-1].to == [proveedor.correo_comercial]
    assert _acciones(RegistroAuditoria.DESPACHO_RESTOCK).get().actor == administrador
    assert "Enviado" in _acciones(RegistroAuditoria.PEDIDO_A_PROVEEDOR).get().detalle
    # Era el único proveedor: la propuesta se cierra sola.
    assert propuesta.estado == PropuestaRestock.CERRADA
    assert _acciones(RegistroAuditoria.CIERRE_PROPUESTA_RESTOCK).exists()


@pytest.mark.django_db
def test_CO072_E2_si_el_correo_falla_el_proveedor_sigue_pendiente(
    client_admin, administrador, propuesta, mailoutbox, django_capture_on_commit_callbacks
):
    proveedor = propuesta.proveedor_de_prueba

    with mock.patch("apps.suppliers.pedidos.enviar_correo", side_effect=OSError("servidor caído")):
        with django_capture_on_commit_callbacks(execute=True):
            client_admin.post(reverse("restock:proveedor", args=[proveedor.pk]))

    propuesta.refresh_from_db()
    assert propuesta.estado == PropuestaRestock.PENDIENTE
    assert set(propuesta.lineas.values_list("estado_despacho", flat=True)) == {
        LineaPropuestaRestock.PENDIENTE
    }
    assert "No se envió" in _acciones(RegistroAuditoria.PEDIDO_A_PROVEEDOR).get().detalle
    assert mailoutbox[-1].to == [administrador.email]


@pytest.mark.django_db
def test_CO072_el_grupo_sin_proveedor_no_se_despacha(client_admin, parametros):
    _agotado()
    servicios.ciclo_semanal()

    client_admin.post(reverse("restock:proveedor", args=[0]))

    assert not LineaPropuestaRestock.objects.filter(
        estado_despacho=LineaPropuestaRestock.DESPACHADO
    ).exists()


@pytest.mark.django_db
def test_CO073_descartar_exige_motivo_y_cierra_si_era_el_ultimo(
    client_admin, administrador, propuesta
):
    clave = propuesta.proveedor_de_prueba.pk
    url = reverse("restock:proveedor", args=[clave])

    client_admin.post(url, {"accion": "descartar", "motivo": "  "})
    sin_motivo = set(propuesta.lineas.values_list("estado_despacho", flat=True))
    client_admin.post(url, {"accion": "descartar", "motivo": "Sin cupo este mes"})

    propuesta.refresh_from_db()
    assert sin_motivo == {LineaPropuestaRestock.PENDIENTE}
    assert set(propuesta.lineas.values_list("motivo_descarte", flat=True)) == {"Sin cupo este mes"}
    assert propuesta.estado == PropuestaRestock.CERRADA
    assert _acciones(RegistroAuditoria.DESCARTE_RESTOCK).get().actor == administrador


@pytest.mark.django_db
def test_CO073_descartar_un_proveedor_no_afecta_a_los_demas(client_admin, parametros):
    uno, otro = EditorialFactory(), EditorialFactory()
    proveedor_uno = ProveedorFactory(editorial=uno)
    ProveedorFactory(editorial=otro)
    _agotado(editorial=uno)
    queda = _agotado(editorial=otro)
    propuesta = servicios.ciclo_semanal().propuesta

    client_admin.post(
        reverse("restock:proveedor", args=[proveedor_uno.pk]),
        {"accion": "descartar", "motivo": "No trabaja más"},
    )

    propuesta.refresh_from_db()
    assert propuesta.estado == PropuestaRestock.PENDIENTE
    assert propuesta.lineas.get(producto=queda).estado_despacho == LineaPropuestaRestock.PENDIENTE


@pytest.mark.django_db
def test_CO074_E2_sin_correo_no_se_envia_y_se_registra(mailoutbox):
    from apps.suppliers import pedidos

    proveedor = ProveedorFactory()
    proveedor.correo_comercial = ""

    resultado = pedidos.enviar_y_registrar(
        proveedor, [pedidos.LineaDePedido(titulo="Akira", volumen=1, isbn="", cantidad=2)]
    )

    assert not resultado.enviado
    assert mailoutbox == []
    assert "sin correo" in _acciones(RegistroAuditoria.PEDIDO_A_PROVEEDOR).get().detalle.lower()


@pytest.mark.django_db
def test_CO013_lo_que_sobra_al_llegar_una_preventa_avisa_a_los_suscriptores(
    administrador, cliente, mailoutbox, django_capture_on_commit_callbacks
):
    from apps.pedidos import preventa
    from apps.pedidos.tests.util import crear_preventa, reservar

    producto = crear_preventa(dias=0)
    reservar(cliente, producto)
    suscripciones = _suscriptos(producto, 3)

    with django_capture_on_commit_callbacks(execute=True):
        preventa.confirmar_ingreso({producto.pk: 3}, administrador)

    estados = [SuscripcionReposicion.objects.get(pk=s.pk).estado for s in suscripciones]
    # Llegaron 3, una cubre la reserva: quedan 2 a la venta (B-05-001).
    assert estados == [SuscripcionReposicion.NOTIFICADA] * 2 + [SuscripcionReposicion.ACTIVA]
