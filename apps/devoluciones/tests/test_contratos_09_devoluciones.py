"""Contratos de devoluciones (plan 09).

`CO-185`, `CO-099`, `CO-186`, `CO-187`, `CO-100`, `CO-101`, `CO-102`, y el plazo
máximo de devolución de `CO-130`.
"""

from datetime import timedelta
from decimal import Decimal

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import IntegrityError, transaction
from django.urls import reverse
from django.utils import timezone

from apps.almacen.models import ArticuloRetenido
from apps.catalog.models import Producto
from apps.catalog.tests.factories import ProductoFactory
from apps.core.models import ConfiguracionSistema, RegistroAuditoria
from apps.devoluciones import servicios
from apps.devoluciones.models import CasoDevolucion, EvidenciaDevolucion
from apps.devoluciones.tests.util import caso_de, foto, no_imagen, pedido_despachado
from apps.pedidos.models import LineaPedido, Pedido
from apps.puntos import servicios as puntos
from apps.puntos.models import LotePuntos, MovimientoPuntos
from apps.tienda.tests.compra_util import cliente_con_direccion, dar_puntos, fijar_parametros

URL_LISTA = reverse("devoluciones:lista")


def _acciones(accion):
    return RegistroAuditoria.objects.filter(accion=accion)


def _url_solicitud(pedido):
    return reverse("cuenta:devolucion", args=[pedido.numero])


@pytest.fixture
def titular(db):
    fijar_parametros()
    return cliente_con_direccion(first_name="Ana", last_name="Lectora")


@pytest.fixture
def navegador(client, titular):
    client.force_login(titular)
    return client


def _reclamar(navegador, pedido, *, linea=None, motivo=CasoDevolucion.DEFECTO, fotos=None, **extra):
    linea = linea or pedido.lineas.order_by("pk").first()
    return navegador.post(
        _url_solicitud(pedido),
        {
            "linea": linea.pk,
            "motivo": motivo,
            "descripcion": extra.get("descripcion", "La tapa vino rota."),
            "fotos": [foto()] if fotos is None else fotos,
        },
    )


# ---------------------------------------------------------------------------
# CO-185 iniciarSolicitudDeDevolucion
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_CO185_presenta_los_articulos_sin_reclamo_y_los_motivos_sin_modificar_nada(
    titular, navegador
):
    pedido = pedido_despachado(titular, lineas=(("10000", 1), ("8000", 2)))
    reclamada, libre = pedido.lineas.order_by("pk")
    CasoDevolucion.objects.create(linea=reclamada, usuario=titular, motivo=CasoDevolucion.DEFECTO)
    casos, registros = CasoDevolucion.objects.count(), RegistroAuditoria.objects.count()

    respuesta = navegador.get(_url_solicitud(pedido))

    solicitud = respuesta.context["solicitud"]
    assert respuesta.status_code == 200
    assert solicitud.lineas == [libre]
    assert [c.linea for c in solicitud.existentes] == [reclamada]
    # Plan 00, C1: la disconformidad sale de la garantía y va por el arrepentimiento.
    assert dict(solicitud.motivos) == {
        "defecto": "Defecto de fabricación",
        "error_imprenta": "Error de imprenta",
    }
    assert 'type="file"' in respuesta.content.decode()
    assert CasoDevolucion.objects.count() == casos
    assert RegistroAuditoria.objects.count() == registros


@pytest.mark.django_db
def test_CO185_E1_vencido_el_plazo_informa_y_no_abre_el_formulario(titular, navegador):
    fijar_parametros(plazo_garantia_dias=10)
    pedido = pedido_despachado(titular, hace_dias=11)

    respuesta = navegador.get(_url_solicitud(pedido), follow=True)

    assert respuesta.redirect_chain[-1][0] == reverse("cuenta:pedido", args=[pedido.numero])
    assert "venció" in respuesta.content.decode()
    assert "solicitud" not in respuesta.context


@pytest.mark.django_db
def test_CO185_E2_con_todos_los_articulos_reclamados_informa_el_caso_y_su_estado(
    titular, navegador
):
    caso = caso_de(titular)
    CasoDevolucion.objects.filter(pk=caso.pk).update(
        estado=CasoDevolucion.RECHAZADO, motivo_rechazo="No se ve el defecto."
    )

    respuesta = navegador.get(_url_solicitud(caso.linea.pedido), follow=True)

    contenido = respuesta.content.decode()
    assert "solicitud" not in respuesta.context
    assert caso.numero in contenido
    assert "rechazado" in contenido


@pytest.mark.django_db
def test_CO185_no_ofrece_las_lineas_canceladas_ni_las_de_despacho_diferido(titular, navegador):
    pedido = pedido_despachado(titular, lineas=(("10000", 1), ("8000", 1), ("9000", 1)))
    salio, cancelada, diferida = pedido.lineas.order_by("pk")
    LineaPedido.objects.filter(pk=cancelada.pk).update(estado=LineaPedido.CANCELADO_REEMBOLSO)
    LineaPedido.objects.filter(pk=diferida.pk).update(
        estado=LineaPedido.DISPONIBLE, decision_demora=LineaPedido.DESPACHO_DIFERIDO
    )

    respuesta = navegador.get(_url_solicitud(pedido))

    assert respuesta.context["solicitud"].lineas == [salio]


@pytest.mark.django_db
def test_CO185_un_pedido_sin_despachar_no_admite_reclamo(titular, navegador):
    from apps.pedidos.tests.util import crear_pedido

    pedido = crear_pedido(titular, estado=Pedido.EMPAQUETADO)

    respuesta = navegador.get(_url_solicitud(pedido), follow=True)

    assert "solicitud" not in respuesta.context
    assert "despachado" in respuesta.content.decode()


# ---------------------------------------------------------------------------
# CO-099 registrarCasoDeDevolucion
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_CO099_crea_el_caso_pendiente_con_sus_datos(titular, navegador):
    pedido = pedido_despachado(titular)
    assert not CasoDevolucion.objects.exists()
    antes = timezone.now()

    _reclamar(
        navegador, pedido, motivo=CasoDevolucion.ERROR_IMPRENTA, descripcion="Faltan páginas."
    )

    caso = CasoDevolucion.objects.get()
    assert caso.estado == CasoDevolucion.PENDIENTE
    assert caso.motivo == CasoDevolucion.ERROR_IMPRENTA
    assert caso.descripcion == "Faltan páginas."
    assert caso.resolucion == ""
    assert antes <= caso.abierto_en <= timezone.now()


@pytest.mark.django_db
def test_CO099_el_caso_queda_asociado_a_la_linea_reclamada(titular, navegador):
    pedido = pedido_despachado(titular, lineas=(("10000", 1), ("8000", 1)))
    _, segunda = pedido.lineas.order_by("pk")

    _reclamar(navegador, pedido, linea=segunda)

    caso = CasoDevolucion.objects.get()
    assert caso.linea == segunda
    assert caso.usuario == titular


@pytest.mark.django_db
def test_CO099_guarda_cada_foto_convertida_a_webp_fuera_de_la_carpeta_publica(
    titular, navegador, settings, evidencias_en_carpeta_temporal
):
    pedido = pedido_despachado(titular)

    _reclamar(navegador, pedido, fotos=[foto(), foto("otra.jpg", "JPEG")])

    evidencias = list(EvidenciaDevolucion.objects.filter(caso=CasoDevolucion.objects.get()))
    assert len(evidencias) == 2
    for evidencia in evidencias:
        ruta = evidencia.imagen.path
        assert ruta.endswith(".webp")
        assert ruta.startswith(str(evidencias_en_carpeta_temporal))
        assert not ruta.startswith(str(settings.MEDIA_ROOT))


@pytest.mark.django_db
def test_CO099_confirma_al_cliente_la_apertura(titular, navegador):
    pedido = pedido_despachado(titular)

    respuesta = _reclamar(navegador, pedido)

    caso = CasoDevolucion.objects.get()
    assert respuesta.url == reverse("cuenta:pedido", args=[pedido.numero])
    detalle = navegador.get(respuesta.url).content.decode()
    assert f"Registramos tu reclamo {caso.numero}" in detalle


@pytest.mark.django_db
def test_CO099_avisa_al_administrador_del_caso_nuevo(
    titular, navegador, administrador, mailoutbox, django_capture_on_commit_callbacks
):
    pedido = pedido_despachado(titular)

    with django_capture_on_commit_callbacks(execute=True):
        _reclamar(navegador, pedido)

    caso = CasoDevolucion.objects.get()
    aviso = next(m for m in mailoutbox if m.to == [administrador.email])
    assert caso.numero in aviso.subject
    assert reverse("devoluciones:detalle", args=[caso.pk]) in aviso.body
    # Plan 00, C1: el Cliente recibe el código de su caso en el momento.
    al_cliente = next(m for m in mailoutbox if m.to == [titular.email])
    assert caso.numero in al_cliente.body


@pytest.mark.django_db
def test_CO099_registra_la_apertura_con_el_actor_y_el_momento(titular, navegador):
    pedido = pedido_despachado(titular)

    _reclamar(navegador, pedido)

    registro = _acciones(RegistroAuditoria.APERTURA_DEVOLUCION).get()
    caso = CasoDevolucion.objects.get()
    assert registro.actor == titular
    assert registro.objetivo == caso
    assert registro.ocurrido_en is not None
    assert caso.numero in registro.detalle


@pytest.mark.django_db
def test_CO099_E1_vencido_el_plazo_no_registra_nada(titular):
    fijar_parametros(plazo_garantia_dias=10)
    pedido = pedido_despachado(titular, hace_dias=11)

    with pytest.raises(servicios.PlazoVencido):
        servicios.registrar_caso(
            pedido, pedido.lineas.get().pk, titular, CasoDevolucion.DEFECTO, "", [foto()]
        )

    assert not CasoDevolucion.objects.exists()
    assert not EvidenciaDevolucion.objects.exists()
    assert not _acciones(RegistroAuditoria.APERTURA_DEVOLUCION).exists()


@pytest.mark.django_db
def test_CO099_el_plazo_corre_desde_el_despacho_con_el_parametro_vigente(titular):
    pedido = pedido_despachado(titular, hace_dias=60)
    # El pedido se creó hace 60 días, pero se despachó hace 12.
    pedido.transiciones.update(ocurrida_en=timezone.now() - timedelta(days=12))
    linea = pedido.lineas.get()

    fijar_parametros(plazo_garantia_dias=10)
    with pytest.raises(servicios.PlazoVencido):
        servicios.registrar_caso(pedido, linea.pk, titular, CasoDevolucion.DEFECTO, "", [foto()])
    fijar_parametros(plazo_garantia_dias=15)
    servicios.registrar_caso(pedido, linea.pk, titular, CasoDevolucion.DEFECTO, "", [foto()])

    assert CasoDevolucion.objects.filter(linea=linea).exists()


@pytest.mark.django_db
def test_CO099_E2_un_articulo_con_un_caso_rechazado_no_admite_otro(titular, navegador):
    caso = caso_de(titular)
    CasoDevolucion.objects.filter(pk=caso.pk).update(
        estado=CasoDevolucion.RECHAZADO, motivo_rechazo="No corresponde."
    )

    respuesta = _reclamar(navegador, caso.linea.pedido, linea=caso.linea)

    assert CasoDevolucion.objects.count() == 1
    assert caso.numero in navegador.get(respuesta.url).content.decode()


@pytest.mark.django_db
def test_CO099_I19_la_base_no_admite_dos_casos_sobre_la_misma_linea(titular):
    caso = caso_de(titular)

    with pytest.raises(IntegrityError), transaction.atomic():
        CasoDevolucion.objects.create(
            linea=caso.linea,
            usuario=titular,
            motivo=CasoDevolucion.ERROR_IMPRENTA,
            correo=titular.email,
        )

    assert CasoDevolucion.objects.count() == 1


@pytest.mark.django_db
def test_CO099_E3_sin_fotos_no_registra_y_el_formulario_sigue_abierto(titular, navegador):
    pedido = pedido_despachado(titular)

    respuesta = _reclamar(navegador, pedido, fotos=[], descripcion="Vino doblado.")

    assert respuesta.status_code == 200
    assert "obligatoria" in respuesta.context["errores"]["fotos"]
    assert respuesta.context["datos"]["descripcion"] == "Vino doblado."
    assert not CasoDevolucion.objects.exists()


@pytest.mark.django_db
def test_CO099_E4_un_archivo_que_no_es_imagen_se_descarta_con_el_problema_especifico(
    titular, navegador
):
    pedido = pedido_despachado(titular)

    respuesta = _reclamar(navegador, pedido, fotos=[foto(), no_imagen("roto.png")])

    error = respuesta.context["errores"]["fotos"]
    assert "roto.png" in error
    assert "no es una imagen" in error
    assert not CasoDevolucion.objects.exists()
    assert not EvidenciaDevolucion.objects.exists()


@pytest.mark.django_db
def test_CO099_E4_una_foto_que_excede_el_tamano_maximo_se_rechaza(titular, navegador):
    pedido = pedido_despachado(titular)
    pesada = SimpleUploadedFile("pesada.png", b"0" * (5 * 1024 * 1024 + 1), "image/png")

    respuesta = _reclamar(navegador, pedido, fotos=[pesada])

    assert "el máximo es 5 MB" in respuesta.context["errores"]["fotos"]
    assert not CasoDevolucion.objects.exists()


@pytest.mark.django_db
def test_CO099_E4_un_formato_no_aceptado_se_rechaza(titular, navegador):
    pedido = pedido_despachado(titular)

    respuesta = _reclamar(navegador, pedido, fotos=[_gif()])

    assert "GIF no se admite" in respuesta.context["errores"]["fotos"]
    assert not CasoDevolucion.objects.exists()


def _gif():
    from io import BytesIO

    from PIL import Image

    salida = BytesIO()
    Image.new("RGB", (10, 10)).save(salida, "GIF")
    return SimpleUploadedFile("foto.gif", salida.getvalue(), "image/gif")


@pytest.mark.django_db
def test_CO099_mas_de_cinco_fotos_no_se_admiten(titular, navegador):
    pedido = pedido_despachado(titular)

    respuesta = _reclamar(navegador, pedido, fotos=[foto(f"f{i}.png") for i in range(6)])

    assert "hasta 5 fotos" in respuesta.context["errores"]["fotos"]
    assert not CasoDevolucion.objects.exists()


@pytest.mark.django_db
def test_CO099_un_pedido_de_otro_cliente_responde_404(titular, navegador):
    otro = cliente_con_direccion()
    pedido = pedido_despachado(otro)

    respuesta = _reclamar(navegador, pedido)

    assert respuesta.status_code == 404
    assert not CasoDevolucion.objects.exists()


# ---------------------------------------------------------------------------
# CO-186 consultarCasosDeDevolucion · CO-187 consultarDetalleDeCasoDeDevolucion
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_CO186_lista_los_pendientes_mas_antiguos_primero_sin_modificar_nada(titular, client_admin):
    reciente = caso_de(titular, hace_dias=1)
    antiguo = caso_de(titular, hace_dias=5)
    resuelto = caso_de(titular, hace_dias=9)
    CasoDevolucion.objects.filter(pk=resuelto.pk).update(
        estado=CasoDevolucion.RECHAZADO, motivo_rechazo="No corresponde."
    )
    registros = RegistroAuditoria.objects.count()

    respuesta = client_admin.get(URL_LISTA)

    assert respuesta.context["casos"] == [antiguo, reciente]
    contenido = respuesta.content.decode()
    for dato in (
        antiguo.numero,
        "Ana Lectora",
        antiguo.linea.pedido.numero,
        "Defecto de fabricación",
    ):
        assert dato in contenido
    assert RegistroAuditoria.objects.count() == registros
    assert CasoDevolucion.objects.filter(estado=CasoDevolucion.PENDIENTE).count() == 2


@pytest.mark.django_db
def test_CO186_E2_sin_pendientes_muestra_el_panel_vacio_con_acceso_al_historial(client_admin):
    respuesta = client_admin.get(URL_LISTA)

    contenido = respuesta.content.decode()
    assert respuesta.context["casos"] == []
    assert "No hay casos pendientes" in contenido
    assert "?filtro=historial" in contenido


@pytest.mark.django_db
def test_CO186_el_historial_muestra_los_resueltos_y_los_rechazados(titular, client_admin):
    pendiente = caso_de(titular)
    rechazado = caso_de(titular)
    CasoDevolucion.objects.filter(pk=rechazado.pk).update(
        estado=CasoDevolucion.RECHAZADO, motivo_rechazo="No corresponde."
    )

    respuesta = client_admin.get(URL_LISTA + "?filtro=historial")

    assert respuesta.context["casos"] == [rechazado]
    assert pendiente not in respuesta.context["casos"]


@pytest.mark.django_db
def test_CO187_presenta_el_caso_con_sus_fotos_sin_modificar_nada(titular, navegador, client):
    pedido = pedido_despachado(titular)
    _reclamar(navegador, pedido, descripcion="Hojas pegadas.")
    caso = CasoDevolucion.objects.get()
    evidencia = caso.evidencias.get()
    from apps.accounts.tests.factories import UsuarioFactory

    client.force_login(UsuarioFactory(rol="administrador"))
    registros = RegistroAuditoria.objects.count()

    respuesta = client.get(reverse("devoluciones:detalle", args=[caso.pk]))
    imagen = client.get(reverse("devoluciones:evidencia", args=[caso.pk, evidencia.pk]))

    contenido = respuesta.content.decode()
    for dato in (titular.email, pedido.numero, "Defecto de fabricación", "Hojas pegadas."):
        assert dato in contenido
    assert reverse("devoluciones:evidencia", args=[caso.pk, evidencia.pk]) in contenido
    assert imagen.status_code == 200
    assert imagen["Content-Type"] == "image/webp"
    assert RegistroAuditoria.objects.count() == registros
    caso.refresh_from_db()
    assert caso.estado == CasoDevolucion.PENDIENTE


# ---------------------------------------------------------------------------
# CO-100 resolverCasoConCambio
# ---------------------------------------------------------------------------


@pytest.fixture
def reemplazo(db):
    return ProductoFactory(stock=3, precio=Decimal("10000"))


@pytest.mark.django_db
def test_CO100_el_caso_pasa_de_pendiente_a_resuelto_con_cambio(titular, administrador, reemplazo):
    caso = caso_de(titular, como=reemplazo)
    assert (caso.estado, caso.resolucion) == (CasoDevolucion.PENDIENTE, "")

    servicios.resolver_con_cambio(caso.pk, reemplazo.pk, administrador)

    caso.refresh_from_db()
    assert caso.estado == CasoDevolucion.RESUELTO
    assert caso.resolucion == CasoDevolucion.CAMBIO
    assert caso.resuelto_por == administrador


@pytest.mark.django_db
def test_CO100_el_caso_queda_asociado_al_producto_de_reemplazo(titular, administrador, reemplazo):
    caso = caso_de(titular, como=reemplazo)
    assert caso.producto_reemplazo is None

    servicios.resolver_con_cambio(caso.pk, reemplazo.pk, administrador)

    caso.refresh_from_db()
    assert caso.producto_reemplazo_id == reemplazo.pk


@pytest.mark.django_db
def test_CO100_el_stock_del_reemplazo_baja_una_unidad(titular, administrador, reemplazo):
    caso = caso_de(titular, como=reemplazo)
    assert reemplazo.stock == 3

    servicios.resolver_con_cambio(caso.pk, reemplazo.pk, administrador)

    reemplazo.refresh_from_db()
    assert reemplazo.stock == 2
    assert reemplazo.estado == Producto.ACTIVO


@pytest.mark.django_db
def test_CO100_el_reemplazo_que_llega_a_cero_pasa_a_agotado(titular, administrador):
    ultimo = ProductoFactory(stock=1, precio=Decimal("10000"))
    caso = caso_de(titular, como=ultimo)

    servicios.resolver_con_cambio(caso.pk, ultimo.pk, administrador)

    ultimo.refresh_from_db()
    assert ultimo.stock == 0
    assert ultimo.estado == Producto.AGOTADO


@pytest.mark.django_db
def test_CO100_el_reemplazo_queda_a_nombre_del_cliente_en_el_stock_en_local(
    titular, administrador, reemplazo
):
    # Plan 00, C1: sin devolución física; el reemplazo se retira o se envía sin costo.
    caso = caso_de(titular, como=reemplazo)
    assert not ArticuloRetenido.objects.exists()

    servicios.resolver_con_cambio(caso.pk, reemplazo.pk, administrador)

    articulo = ArticuloRetenido.objects.get()
    assert articulo.usuario == titular
    assert articulo.producto_id == reemplazo.pk
    assert articulo.procedencia == ArticuloRetenido.CAMBIO
    assert articulo.estado == ArticuloRetenido.DISPONIBLE
    from apps.almacen import servicios as almacen

    resumen = almacen.resumen_de_despacho(titular, [articulo.pk], {})
    assert resumen.costo_envio == 0


@pytest.mark.django_db
def test_CO100_registra_la_resolucion_con_el_tipo_el_administrador_y_el_momento(
    titular, administrador, reemplazo
):
    caso = caso_de(titular, como=reemplazo)

    servicios.resolver_con_cambio(caso.pk, reemplazo.pk, administrador)

    registro = _acciones(RegistroAuditoria.DEVOLUCION_CON_CAMBIO).get()
    assert registro.actor == administrador
    assert registro.objetivo == caso
    assert registro.ocurrido_en is not None
    assert "cambio" in registro.detalle


@pytest.mark.django_db
def test_CO100_avisa_al_cliente_con_el_reemplazo_y_las_instrucciones(
    titular, administrador, reemplazo, mailoutbox, django_capture_on_commit_callbacks
):
    caso = caso_de(titular, como=reemplazo)

    with django_capture_on_commit_callbacks(execute=True):
        servicios.resolver_con_cambio(caso.pk, reemplazo.pk, administrador)

    aviso = mailoutbox[-1]
    assert aviso.to == [titular.email]
    assert str(reemplazo.especifico) in aviso.body
    assert "sin costo" in aviso.body


@pytest.mark.django_db
def test_CO100_E1_sin_stock_no_registra_nada(titular, administrador):
    agotado = ProductoFactory(stock=0, precio=Decimal("10000"), estado=Producto.AGOTADO)
    caso = caso_de(titular, como=agotado)

    with pytest.raises(servicios.SinStock):
        servicios.resolver_con_cambio(caso.pk, agotado.pk, administrador)

    caso.refresh_from_db()
    agotado.refresh_from_db()
    assert caso.estado == CasoDevolucion.PENDIENTE
    assert caso.producto_reemplazo is None
    assert agotado.stock == 0
    assert not ArticuloRetenido.objects.exists()
    assert not _acciones(RegistroAuditoria.DEVOLUCION_CON_CAMBIO).exists()


@pytest.mark.django_db
def test_CO100_E1_la_pantalla_no_deja_elegir_un_producto_sin_stock(titular, client_admin):
    agotado = ProductoFactory(stock=0, precio=Decimal("10000"), titulo="Akira sin stock")
    caso = caso_de(titular, como=agotado)
    url = reverse("devoluciones:cambio", args=[caso.pk])

    busqueda = client_admin.get(url + "?buscar=Akira sin stock")
    elegido = client_admin.get(url + f"?producto={agotado.pk}")

    assert "Sin stock" in busqueda.content.decode()
    assert f"?producto={agotado.pk}" not in busqueda.content.decode()
    assert "Confirmar el cambio" not in elegido.content.decode()
    assert reverse("devoluciones:reembolso", args=[caso.pk]) in elegido.content.decode()


@pytest.mark.django_db
def test_CO100_no_toca_el_producto_reclamado_ni_los_puntos(titular, administrador, reemplazo):
    caso = caso_de(titular, como=reemplazo)
    reclamado = caso.linea.producto
    stock = reclamado.stock

    servicios.resolver_con_cambio(caso.pk, reemplazo.pk, administrador)

    reclamado.refresh_from_db()
    assert reclamado.stock == stock
    assert puntos.saldo(titular) == 0
    assert not MovimientoPuntos.objects.exists()


@pytest.mark.django_db
def test_CO100_un_caso_que_ya_no_esta_pendiente_no_se_vuelve_a_resolver(
    titular, administrador, reemplazo
):
    caso = caso_de(titular, como=reemplazo)
    servicios.rechazar(caso.pk, administrador, "No corresponde.")

    with pytest.raises(servicios.OperacionRechazada):
        servicios.resolver_con_cambio(caso.pk, reemplazo.pk, administrador)

    reemplazo.refresh_from_db()
    assert reemplazo.stock == 3
    assert not ArticuloRetenido.objects.exists()


# ---------------------------------------------------------------------------
# CO-101 resolverCasoConReembolsoEnPuntos
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_CO101_el_caso_pasa_de_pendiente_a_resuelto_con_reembolso(titular, administrador):
    caso = caso_de(titular)
    assert (caso.estado, caso.resolucion) == (CasoDevolucion.PENDIENTE, "")

    servicios.resolver_con_reembolso(caso.pk, administrador)

    caso.refresh_from_db()
    assert caso.estado == CasoDevolucion.RESUELTO
    assert caso.resolucion == CasoDevolucion.REEMBOLSO


@pytest.mark.django_db
def test_CO101_acredita_un_lote_de_reembolso_por_una_unidad_con_la_caducidad_estandar(
    titular, administrador
):
    fijar_parametros(caducidad_puntos_meses=12)
    # Dos unidades a $ 10.000 con 1 punto = $ 10: una unidad son 1000 puntos.
    caso = caso_de(titular, lineas=(("10000", 2),))
    assert not LotePuntos.objects.exists()

    servicios.resolver_con_reembolso(caso.pk, administrador)

    lote = LotePuntos.objects.get()
    assert lote.usuario == titular
    assert lote.origen == LotePuntos.REEMBOLSO
    assert lote.cantidad_acreditada == lote.disponible == 1000
    assert lote.caduca_el == puntos._sumar_meses(timezone.localdate(), 12)


@pytest.mark.django_db
def test_CO101_el_movimiento_de_acreditacion_queda_con_su_saldo_y_su_caso(titular, administrador):
    dar_puntos(titular, 50)
    caso = caso_de(titular)

    hecho = servicios.resolver_con_reembolso(caso.pk, administrador)

    movimiento = MovimientoPuntos.objects.get()
    assert movimiento.tipo == MovimientoPuntos.ACREDITACION
    assert movimiento.cantidad == 1000
    assert movimiento.saldo_resultante == 1050 == hecho.saldo
    assert movimiento.caso_devolucion == caso
    assert movimiento.linea_pedido == caso.linea


@pytest.mark.django_db
def test_CO101_una_unidad_pagada_con_puntos_devuelve_su_parte_hacia_arriba(titular, administrador):
    # Tres unidades canjeadas por 1001 puntos: una vale 333,67, se devuelven 334.
    caso = caso_de(titular, lineas=(("10000", 3, 1001),))

    hecho = servicios.resolver_con_reembolso(caso.pk, administrador)

    assert hecho.puntos == 334
    assert LotePuntos.objects.get().cantidad_acreditada == 334


@pytest.mark.django_db
def test_CO101_registra_la_resolucion_con_el_tipo_el_administrador_y_el_momento(
    titular, administrador
):
    caso = caso_de(titular)

    servicios.resolver_con_reembolso(caso.pk, administrador)

    registro = _acciones(RegistroAuditoria.DEVOLUCION_CON_REEMBOLSO).get()
    assert registro.actor == administrador
    assert registro.objetivo == caso
    assert "1000 pts" in registro.detalle


@pytest.mark.django_db
def test_CO101_avisa_al_cliente_con_el_saldo_actualizado(
    titular, administrador, mailoutbox, django_capture_on_commit_callbacks
):
    dar_puntos(titular, 50)
    caso = caso_de(titular)

    with django_capture_on_commit_callbacks(execute=True):
        servicios.resolver_con_reembolso(caso.pk, administrador)

    aviso = mailoutbox[-1]
    assert aviso.to == [titular.email]
    assert "1050 pts" in aviso.body


@pytest.mark.django_db
def test_CO101_descuenta_los_puntos_ganados_con_la_compra_y_no_toca_el_stock(
    titular, administrador
):
    # Plan 00, C2 (RF-19): la unidad que se reembolsa devuelve lo que ganó.
    caso = caso_de(titular)
    puntos.acreditar(titular, 100, origen=LotePuntos.COMPRA, pedido=caso.linea.pedido)
    producto = caso.linea.producto
    stock = producto.stock

    servicios.resolver_con_reembolso(caso.pk, administrador)

    producto.refresh_from_db()
    debito = MovimientoPuntos.objects.get(tipo=MovimientoPuntos.DEBITO)
    assert debito.cantidad == 100
    assert debito.linea_pedido == caso.linea
    assert puntos.saldo(titular) == 1000
    assert producto.stock == stock


@pytest.mark.django_db
def test_CO101_un_caso_ya_resuelto_no_acredita_dos_veces(titular, administrador):
    caso = caso_de(titular)
    servicios.resolver_con_reembolso(caso.pk, administrador)

    with pytest.raises(servicios.OperacionRechazada):
        servicios.resolver_con_reembolso(caso.pk, administrador)

    assert LotePuntos.objects.count() == 1


# ---------------------------------------------------------------------------
# CO-102 rechazarCasoDeDevolucion
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_CO102_el_caso_pasa_a_rechazado_con_el_motivo_declarado(titular, administrador):
    caso = caso_de(titular)
    assert (caso.estado, caso.motivo_rechazo) == (CasoDevolucion.PENDIENTE, "")

    servicios.rechazar(caso.pk, administrador, "  La foto no muestra el defecto.  ")

    caso.refresh_from_db()
    assert caso.estado == CasoDevolucion.RECHAZADO
    assert caso.motivo_rechazo == "La foto no muestra el defecto."


@pytest.mark.django_db
def test_CO102_registra_el_rechazo_con_el_actor_y_el_momento(titular, administrador):
    caso = caso_de(titular)

    servicios.rechazar(caso.pk, administrador, "No corresponde.")

    registro = _acciones(RegistroAuditoria.RECHAZO_DEVOLUCION).get()
    assert registro.actor == administrador
    assert registro.objetivo == caso
    assert "No corresponde." in registro.detalle


@pytest.mark.django_db
def test_CO102_avisa_al_cliente_con_el_motivo(
    titular, administrador, mailoutbox, django_capture_on_commit_callbacks
):
    caso = caso_de(titular)

    with django_capture_on_commit_callbacks(execute=True):
        servicios.rechazar(caso.pk, administrador, "La foto no muestra el defecto.")

    aviso = mailoutbox[-1]
    assert aviso.to == [titular.email]
    assert "La foto no muestra el defecto." in aviso.body


@pytest.mark.django_db
def test_CO102_sin_motivo_no_registra_nada(titular, client_admin):
    caso = caso_de(titular)

    respuesta = client_admin.post(reverse("devoluciones:rechazo", args=[caso.pk]), {"motivo": " "})

    caso.refresh_from_db()
    assert respuesta.status_code == 200
    assert "obligatorio" in respuesta.context["error"]
    assert caso.estado == CasoDevolucion.PENDIENTE
    assert not _acciones(RegistroAuditoria.RECHAZO_DEVOLUCION).exists()


@pytest.mark.django_db
def test_CO102_no_acredita_puntos_ni_toca_el_stock(titular, administrador):
    caso = caso_de(titular)
    producto = caso.linea.producto
    stock = producto.stock

    servicios.rechazar(caso.pk, administrador, "No corresponde.")

    producto.refresh_from_db()
    assert producto.stock == stock
    assert not MovimientoPuntos.objects.exists()
    assert not ArticuloRetenido.objects.exists()


# ---------------------------------------------------------------------------
# CO-130 configurarParametros: el plazo máximo de devolución (E1)
# ---------------------------------------------------------------------------

URL_PARAMETROS = reverse("catalog:parametros")


def _compra(**cambios):
    return {
        "guardar_compra": "1",
        "costo_envio": "1500",
        "monto_minimo_envio_gratuito": "50000",
        "ventana_decision_horas": "72",
        "plazo_retencion_meses": "3",
        "dias_aviso_retencion": "7",
        "plazo_devolucion_dias": "10",
        "plazo_garantia_dias": "90",
        "equivalencia_puntos": "10",
        "porcentaje_puntos": "10",
        "caducidad_puntos_meses": "12",
        "dias_aviso_caducidad_puntos": "3",
        "maximo_reserva_preventa": "5",
        "margen_cupo_preventa": "10",
        "pasarela": ConfiguracionSistema.PASARELA_PRUEBA,
        **cambios,
    }


@pytest.mark.django_db
def test_CO130_el_plazo_de_devolucion_pasa_al_declarado_y_queda_auditado(client_admin):
    fijar_parametros()
    assert ConfiguracionSistema.obtener().plazo_devolucion_dias == 10

    client_admin.post(URL_PARAMETROS, _compra(plazo_devolucion_dias="30"))

    assert ConfiguracionSistema.obtener().plazo_devolucion_dias == 30
    assert (
        _acciones(RegistroAuditoria.PARAMETRO_MODIFICADO).get().detalle
        == "plazo de arrepentimiento (días): 10 → 30"
    )


@pytest.mark.django_db
def test_CO130_E1_el_plazo_bajo_el_piso_legal_se_rechaza_solo_y_los_demas_se_guardan(
    client_admin,
):
    fijar_parametros()

    respuesta = client_admin.post(
        URL_PARAMETROS, _compra(plazo_devolucion_dias="7", costo_envio="2500")
    )

    configuracion = ConfiguracionSistema.obtener()
    assert configuracion.plazo_devolucion_dias == 10
    assert configuracion.costo_envio == Decimal("2500")
    error = respuesta.context["form_compra"].errors["plazo_devolucion_dias"][0]
    assert "Ley 24.240" in error
    detalles = set(
        _acciones(RegistroAuditoria.PARAMETRO_MODIFICADO).values_list("detalle", flat=True)
    )
    assert len(detalles) == 1
    assert detalles.pop().startswith("costo de envío: 1500")


@pytest.mark.django_db
def test_CO130_E2_otro_campo_invalido_no_guarda_nada_aunque_el_plazo_tambien_falle(client_admin):
    fijar_parametros()

    client_admin.post(URL_PARAMETROS, _compra(plazo_devolucion_dias="7", costo_envio="-1"))

    configuracion = ConfiguracionSistema.obtener()
    assert configuracion.costo_envio == Decimal("1500")
    assert configuracion.plazo_devolucion_dias == 10
    assert not _acciones(RegistroAuditoria.PARAMETRO_MODIFICADO).exists()


@pytest.mark.django_db
def test_CO130_la_base_no_admite_un_plazo_bajo_el_piso_legal():
    configuracion = ConfiguracionSistema.obtener()

    with pytest.raises(IntegrityError), transaction.atomic():
        ConfiguracionSistema.objects.filter(pk=configuracion.pk).update(plazo_devolucion_dias=9)


# ---------------------------------------------------------------------------
# Flujo
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_flujo_el_cliente_reclama_y_el_administrador_reembolsa_en_puntos(
    titular, navegador, administrador
):
    from django.test import Client

    client_admin = Client()
    client_admin.force_login(administrador)
    pedido = pedido_despachado(titular)
    detalle = navegador.get(reverse("cuenta:pedido", args=[pedido.numero])).content.decode()
    assert _url_solicitud(pedido) in detalle

    navegador.get(_url_solicitud(pedido))
    _reclamar(navegador, pedido)
    caso = CasoDevolucion.objects.get()

    lista = client_admin.get(URL_LISTA)
    assert caso in lista.context["casos"]
    client_admin.get(reverse("devoluciones:detalle", args=[caso.pk]))
    confirmacion = client_admin.get(reverse("devoluciones:reembolso", args=[caso.pk]))
    assert confirmacion.context["puntos"] == 1000
    client_admin.post(reverse("devoluciones:reembolso", args=[caso.pk]))

    caso.refresh_from_db()
    assert caso.estado == CasoDevolucion.RESUELTO
    assert puntos.saldo(titular) == 1000
    final = navegador.get(reverse("cuenta:pedido", args=[pedido.numero])).content.decode()
    assert caso.numero in final
    assert "reembolso en puntos" in final
    assert _url_solicitud(pedido) not in final


@pytest.mark.django_db
def test_flujo_el_administrador_busca_el_reemplazo_y_autoriza_el_cambio(titular, client_admin):
    reemplazo = ProductoFactory(stock=2, precio=Decimal("10000"), titulo="Monster deluxe")
    caso = caso_de(titular, como=reemplazo)
    url = reverse("devoluciones:cambio", args=[caso.pk])

    busqueda = client_admin.get(url + "?buscar=Monster")
    assert reemplazo.pk in [p.pk for p in busqueda.context["resultados"]]
    confirmacion = client_admin.get(url + f"?producto={reemplazo.pk}")
    assert "Confirmar el cambio" in confirmacion.content.decode()
    client_admin.post(url, {"producto": reemplazo.pk})

    caso.refresh_from_db()
    reemplazo.refresh_from_db()
    assert caso.producto_reemplazo_id == reemplazo.pk
    assert reemplazo.stock == 1
