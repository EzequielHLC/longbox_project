"""Las devoluciones reformuladas (plan 00, C1).

El arrepentimiento por el botón, sin registración (`CO-185`, `CO-099`), su
reembolso por el medio de pago o en puntos (`CO-101`), y la garantía con su
propio plazo y el cambio por un tomo de la misma editorial y formato (`CO-100`).
"""

from decimal import Decimal

import pytest
from django.db import IntegrityError, transaction
from django.test import Client
from django.urls import reverse

from apps.accounts.tests.factories import UsuarioFactory
from apps.catalog.tests.factories import ProductoFactory
from apps.core.models import RegistroAuditoria
from apps.devoluciones import servicios
from apps.devoluciones.models import CasoDevolucion
from apps.devoluciones.tests.util import caso_de, pedido_despachado
from apps.pedidos.models import Pedido
from apps.pedidos.tests.util import como_venta_de_mostrador, crear_pedido
from apps.puntos import servicios as puntos
from apps.puntos.models import LotePuntos, MovimientoPuntos
from apps.tienda.tests.compra_util import cliente_con_direccion, fijar_parametros

URL_BOTON = reverse("devoluciones_tienda:inicio")


def _url_pedido(pedido):
    return reverse("devoluciones_tienda:pedido", args=[pedido.numero])


@pytest.fixture
def titular(db):
    fijar_parametros()
    return cliente_con_direccion(first_name="Ana", last_name="Lectora")


@pytest.fixture
def panel(db):
    sesion = Client()
    sesion.force_login(UsuarioFactory(rol="administrador"))
    return sesion


def _pedido_de_invitado(*, hace_dias=1, lineas=(("10000", 1),)):
    pedido = crear_pedido(
        None, estado=Pedido.DESPACHADO, lineas=lineas, hace_dias=hace_dias, costo_envio="1500"
    )
    pedido.lineas.update(estado="despachado")
    return pedido


# ---------------------------------------------------------------------------
# El botón de arrepentimiento, sin registración
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_el_boton_esta_destacado_en_el_pie_de_toda_la_tienda(client):
    """Res. 424/2020: visible y de fácil acceso. Va en el pie, que está en todas
    las páginas, como un botón propio y no como un enlace más (B-09-009)."""
    for url in (reverse("core:tienda"), reverse("core:tienda_catalogo")):
        contenido = client.get(url).content.decode()
        pie = contenido[contenido.index("<footer") :]

        assert f'href="{URL_BOTON}" class="boton-seccion boton-arrepentimiento"' in pie
        assert "Botón de arrepentimiento" in pie


@pytest.mark.django_db
def test_CO185_sin_sesion_el_numero_y_el_correo_de_la_compra_abren_el_pedido(client):
    pedido = _pedido_de_invitado(lineas=(("10000", 2), ("8000", 1)))

    respuesta = client.post(
        URL_BOTON, {"numero": pedido.numero, "correo": "INVITADO@correo.test"}, follow=True
    )

    assert respuesta.redirect_chain[-1][0] == _url_pedido(pedido)
    assert len(respuesta.context["solicitud"].lineas) == 2


@pytest.mark.django_db
def test_CO185_un_correo_que_no_coincide_no_revela_el_pedido(client):
    pedido = _pedido_de_invitado()

    respuesta = client.post(URL_BOTON, {"numero": pedido.numero, "correo": "otro@correo.test"})
    directo = client.get(_url_pedido(pedido))

    assert "No encontramos" in respuesta.context["error"]
    assert directo.status_code == 404


@pytest.mark.django_db
def test_CO185_con_sesion_el_cliente_ve_sus_compras_dentro_del_plazo(client, titular):
    vigente = pedido_despachado(titular, hace_dias=2)
    vencido = pedido_despachado(titular, hace_dias=30)
    client.force_login(titular)

    respuesta = client.get(URL_BOTON)

    assert respuesta.context["pedidos"] == [vigente]
    assert vencido not in respuesta.context["pedidos"]


@pytest.mark.django_db
def test_CO099_arrepentirse_abre_un_caso_por_linea_con_la_linea_entera_y_sin_fotos(
    client, mailoutbox, django_capture_on_commit_callbacks
):
    pedido = _pedido_de_invitado(lineas=(("10000", 2), ("8000", 1)))
    client.post(URL_BOTON, {"numero": pedido.numero, "correo": "invitado@correo.test"})
    lineas = list(pedido.lineas.order_by("pk"))

    with django_capture_on_commit_callbacks(execute=True):
        respuesta = client.post(_url_pedido(pedido), {"linea": [linea.pk for linea in lineas]})

    casos = list(CasoDevolucion.objects.order_by("pk"))
    assert [c.linea for c in casos] == lineas
    assert [c.unidades for c in casos] == [2, 1]
    assert {c.motivo for c in casos} == {CasoDevolucion.ARREPENTIMIENTO}
    assert {c.correo for c in casos} == {"invitado@correo.test"}
    assert all(c.usuario is None for c in casos)
    assert not any(c.evidencias.exists() for c in casos)
    # Res. 424/2020: el código, en la pantalla y por correo.
    contenido = respuesta.content.decode()
    assert all(c.numero in contenido for c in casos)
    assert any(casos[0].numero in m.body and m.to == ["invitado@correo.test"] for m in mailoutbox)


@pytest.mark.django_db
def test_CO099_el_arrepentimiento_es_solo_para_compras_online(titular):
    pedido = pedido_despachado(titular)
    como_venta_de_mostrador(pedido)

    with pytest.raises(servicios.OperacionRechazada, match="compras online"):
        servicios.iniciar_solicitud(pedido, servicios.ARREPENTIMIENTO)


@pytest.mark.django_db
def test_CO099_E1_los_dos_plazos_son_independientes(titular):
    fijar_parametros(plazo_devolucion_dias=10, plazo_garantia_dias=90)
    pedido = pedido_despachado(titular, hace_dias=30)

    with pytest.raises(servicios.PlazoVencido, match="arrepentirte"):
        servicios.iniciar_solicitud(pedido, servicios.ARREPENTIMIENTO)
    solicitud = servicios.iniciar_solicitud(pedido, servicios.GARANTIA)

    assert solicitud.lineas == list(pedido.lineas.all())


@pytest.mark.django_db
def test_CO099_un_arrepentimiento_y_una_garantia_no_conviven_en_la_misma_linea(titular):
    caso = caso_de(titular, motivo=CasoDevolucion.ARREPENTIMIENTO)

    with pytest.raises(servicios.CasoExistente):
        servicios.registrar_caso(
            caso.linea.pedido, caso.linea.pk, titular, CasoDevolucion.DEFECTO, "", []
        )


# ---------------------------------------------------------------------------
# CO-101 y el reembolso por el medio de pago
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_CO101_el_arrepentimiento_se_reembolsa_por_el_medio_de_pago_y_vuelve_al_stock(
    titular, administrador, mailoutbox, django_capture_on_commit_callbacks
):
    pedido = pedido_despachado(titular, lineas=(("10000", 2), ("8000", 1)))
    caso = caso_de(titular, pedido=pedido, motivo=CasoDevolucion.ARREPENTIMIENTO)
    producto = caso.linea.producto
    antes = producto.stock

    with django_capture_on_commit_callbacks(execute=True):
        hecho = servicios.resolver_con_reembolso_por_el_medio(caso.pk, administrador)

    caso.refresh_from_db()
    producto.refresh_from_db()
    assert caso.resolucion == CasoDevolucion.REEMBOLSO_MEDIO
    assert caso.monto_reembolsado == hecho.monto == Decimal("20000")  # las dos unidades
    assert producto.stock == antes + 2
    registro = RegistroAuditoria.objects.get(accion=RegistroAuditoria.DEVOLUCION_REEMBOLSO_MEDIO)
    assert "20000" in registro.detalle
    assert "$ 20000" in mailoutbox[-1].body
    assert not LotePuntos.objects.filter(origen=LotePuntos.REEMBOLSO).exists()


@pytest.mark.django_db
def test_CO101_arrepentirse_del_pedido_entero_reintegra_tambien_el_envio(titular, administrador):
    pedido = pedido_despachado(titular, lineas=(("10000", 1),))

    caso = caso_de(titular, pedido=pedido, motivo=CasoDevolucion.ARREPENTIMIENTO)
    hecho = servicios.resolver_con_reembolso_por_el_medio(caso.pk, administrador)

    assert hecho.monto == Decimal("10000") + pedido.costo_envio


@pytest.mark.django_db
def test_CO101_el_reembolso_por_el_medio_descuenta_los_puntos_ganados(titular, administrador):
    pedido = pedido_despachado(titular, lineas=(("10000", 1),))
    puntos.acreditar(titular, 100, origen=LotePuntos.COMPRA, pedido=pedido)
    caso = caso_de(titular, pedido=pedido, motivo=CasoDevolucion.ARREPENTIMIENTO)

    servicios.resolver_con_reembolso_por_el_medio(caso.pk, administrador)

    assert puntos.saldo(titular) == 0
    assert MovimientoPuntos.objects.get(tipo=MovimientoPuntos.DEBITO).cantidad == 100


@pytest.mark.django_db
def test_CO101_lo_pagado_con_puntos_vuelve_en_puntos_y_no_por_el_medio(titular, administrador):
    pedido = pedido_despachado(titular, lineas=(("10000", 1, 1000),))
    caso = caso_de(titular, pedido=pedido, motivo=CasoDevolucion.ARREPENTIMIENTO)

    opciones = servicios.opciones(caso)
    with pytest.raises(servicios.OperacionRechazada):
        servicios.resolver_con_reembolso_por_el_medio(caso.pk, administrador)
    servicios.resolver_con_reembolso(caso.pk, administrador)

    assert (opciones.medio, opciones.puntos, opciones.cambio) == (False, True, False)
    assert LotePuntos.objects.get(origen=LotePuntos.REEMBOLSO).cantidad_acreditada >= 1000


@pytest.mark.django_db
def test_CO101_en_el_mostrador_no_hay_reembolso_por_el_medio(titular, administrador):
    pedido = pedido_despachado(titular)
    como_venta_de_mostrador(pedido)
    caso = caso_de(titular, pedido=pedido)

    assert servicios.opciones(caso).medio is False
    with pytest.raises(servicios.OperacionRechazada, match="pasarela"):
        servicios.resolver_con_reembolso_por_el_medio(caso.pk, administrador)


@pytest.mark.django_db
def test_CO100_el_arrepentimiento_no_admite_cambio_ni_en_el_servicio_ni_en_la_base(
    titular, administrador
):
    reemplazo = ProductoFactory(stock=3, precio=Decimal("10000"))
    caso = caso_de(titular, motivo=CasoDevolucion.ARREPENTIMIENTO, como=reemplazo)

    with pytest.raises(servicios.OperacionRechazada, match="no se resuelve con un cambio"):
        servicios.resolver_con_cambio(caso.pk, reemplazo.pk, administrador)
    with pytest.raises(IntegrityError), transaction.atomic():
        CasoDevolucion.objects.filter(pk=caso.pk).update(
            estado=CasoDevolucion.RESUELTO,
            resolucion=CasoDevolucion.CAMBIO,
            producto_reemplazo=reemplazo,
        )


@pytest.mark.django_db
def test_CO100_el_reemplazo_tiene_que_ser_de_la_misma_editorial_y_formato(titular, administrador):
    caso = caso_de(titular)
    otro = ProductoFactory(stock=3, precio=Decimal("10000"))

    with pytest.raises(servicios.OperacionRechazada, match="misma editorial"):
        servicios.resolver_con_cambio(caso.pk, otro.pk, administrador)

    otro.refresh_from_db()
    assert otro.stock == 3


@pytest.mark.django_db
def test_la_ficha_del_caso_muestra_el_contacto_y_solo_las_resoluciones_que_admite(titular, panel):
    titular.telefono_numero = "3517000000"
    titular.save(update_fields=["telefono_numero"])
    caso = caso_de(titular, motivo=CasoDevolucion.ARREPENTIMIENTO)

    contenido = panel.get(reverse("devoluciones:detalle", args=[caso.pk])).content.decode()

    assert titular.email in contenido
    assert "3517000000" in contenido
    assert reverse("devoluciones:reembolso_medio", args=[caso.pk]) in contenido
    assert reverse("devoluciones:cambio", args=[caso.pk]) not in contenido


@pytest.mark.django_db
def test_acceso_el_cajero_no_registra_un_reembolso_por_el_medio(client, cajero, titular):
    caso = caso_de(titular, motivo=CasoDevolucion.ARREPENTIMIENTO)
    client.force_login(cajero)

    respuesta = client.post(reverse("devoluciones:reembolso_medio", args=[caso.pk]))

    caso.refresh_from_db()
    assert respuesta.status_code == 403
    assert caso.estado == CasoDevolucion.PENDIENTE


@pytest.mark.django_db
def test_flujo_el_invitado_se_arrepiente_y_el_local_reembolsa(client, panel):
    pedido = _pedido_de_invitado(lineas=(("10000", 1),))
    linea = pedido.lineas.get()
    client.post(URL_BOTON, {"numero": pedido.numero, "correo": "invitado@correo.test"})
    client.post(_url_pedido(pedido), {"linea": [linea.pk]})
    caso = CasoDevolucion.objects.get()

    confirmacion = panel.get(reverse("devoluciones:reembolso_medio", args=[caso.pk]))
    panel.post(reverse("devoluciones:reembolso_medio", args=[caso.pk]))

    caso.refresh_from_db()
    assert confirmacion.context["monto"] == Decimal("11500")  # el tomo y el envío
    assert caso.estado == CasoDevolucion.RESUELTO
    assert caso.monto_reembolsado == Decimal("11500")


@pytest.mark.django_db
def test_el_plazo_de_garantia_se_configura_en_parametros(client_admin):
    from apps.core.models import ConfiguracionSistema

    fijar_parametros()
    datos = {
        "guardar_compra": "1",
        "costo_envio": "1500",
        "monto_minimo_envio_gratuito": "50000",
        "ventana_decision_horas": "72",
        "plazo_retencion_meses": "3",
        "dias_aviso_retencion": "7",
        "plazo_devolucion_dias": "10",
        "plazo_garantia_dias": "180",
        "equivalencia_puntos": "10",
        "porcentaje_puntos": "10",
        "caducidad_puntos_meses": "12",
        "dias_aviso_caducidad_puntos": "3",
        "pasarela": ConfiguracionSistema.PASARELA_PRUEBA,
    }

    client_admin.post(reverse("catalog:parametros"), datos)

    assert ConfiguracionSistema.obtener().plazo_garantia_dias == 180
