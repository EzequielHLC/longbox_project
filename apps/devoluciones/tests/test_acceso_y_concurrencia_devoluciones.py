"""Acceso a las devoluciones por la dirección real, y resoluciones a la vez."""

from decimal import Decimal

import pytest
from django.urls import reverse

from apps.accounts.tests.factories import UsuarioFactory
from apps.almacen.models import ArticuloRetenido
from apps.catalog.models import Producto
from apps.catalog.tests.factories import ProductoFactory
from apps.core.models import RegistroAuditoria
from apps.core.tests.concurrencia import a_la_vez, errores_internos, sesion_de
from apps.devoluciones.models import CasoDevolucion, EvidenciaDevolucion
from apps.devoluciones.tests.util import caso_de, foto, pedido_despachado
from apps.puntos.models import LotePuntos
from apps.tienda.tests.compra_util import fijar_parametros


def _con_foto(caso):
    evidencia = EvidenciaDevolucion(caso=caso)
    evidencia.imagen.save("foto.png", foto(), save=True)
    return evidencia


def _escrituras(client, caso, producto):
    return [
        client.post(reverse("devoluciones:cambio", args=[caso.pk]), {"producto": producto.pk}),
        client.post(reverse("devoluciones:reembolso", args=[caso.pk])),
        client.post(reverse("devoluciones:rechazo", args=[caso.pk]), {"motivo": "No."}),
    ]


@pytest.mark.django_db
@pytest.mark.parametrize("rol", ["cajero", "cliente"])
def test_acceso_solo_el_administrador_consulta_y_resuelve_casos(client, request, rol):
    caso = caso_de(UsuarioFactory(rol="cliente"))
    producto = ProductoFactory(stock=3, precio=Decimal("10000"))
    client.force_login(request.getfixturevalue(rol))

    respuestas = [
        client.get(reverse("devoluciones:lista")),
        client.get(reverse("devoluciones:detalle", args=[caso.pk])),
        client.get(reverse("devoluciones:cambio", args=[caso.pk])),
        *_escrituras(client, caso, producto),
    ]

    caso.refresh_from_db()
    producto.refresh_from_db()
    assert {r.status_code for r in respuestas} == {403}
    assert caso.estado == CasoDevolucion.PENDIENTE
    assert producto.stock == 3
    assert not LotePuntos.objects.exists()


@pytest.mark.django_db
def test_acceso_sin_sesion_las_devoluciones_llevan_al_ingreso(client):
    caso = caso_de(UsuarioFactory(rol="cliente"))

    respuesta = client.post(reverse("devoluciones:reembolso", args=[caso.pk]))

    caso.refresh_from_db()
    assert respuesta.status_code == 302
    assert reverse("accounts:login") in respuesta.url
    assert caso.estado == CasoDevolucion.PENDIENTE


@pytest.mark.django_db
@pytest.mark.parametrize("rol", ["cajero", "administrador"])
def test_acceso_el_personal_no_abre_reclamos_desde_mi_cuenta(client, request, rol):
    pedido = pedido_despachado(UsuarioFactory(rol="cliente"))
    client.force_login(request.getfixturevalue(rol))
    url = reverse("cuenta:devolucion", args=[pedido.numero])

    respuestas = [client.get(url), client.post(url, {"motivo": CasoDevolucion.DEFECTO})]

    assert {r.status_code for r in respuestas} == {403}
    assert not CasoDevolucion.objects.exists()


@pytest.mark.django_db
def test_acceso_la_foto_la_ven_el_administrador_y_su_cliente_y_nadie_mas(
    client, administrador, cajero
):
    titular = UsuarioFactory(rol="cliente")
    caso = caso_de(titular)
    url = reverse("devoluciones:evidencia", args=[caso.pk, _con_foto(caso).pk])

    vistas = {}
    for nombre, usuario in (
        ("titular", titular),
        ("administrador", administrador),
        ("otro cliente", UsuarioFactory(rol="cliente")),
        ("cajero", cajero),
    ):
        client.force_login(usuario)
        vistas[nombre] = client.get(url).status_code
    client.logout()
    vistas["sin sesión"] = client.get(url).status_code

    assert vistas == {
        "titular": 200,
        "administrador": 200,
        "otro cliente": 404,
        "cajero": 403,
        "sin sesión": 302,
    }


@pytest.mark.django_db
def test_acceso_la_foto_no_tiene_direccion_publica(client):
    caso = caso_de(UsuarioFactory(rol="cliente"))
    evidencia = _con_foto(caso)

    with pytest.raises(ValueError, match="no tiene dirección pública"):
        evidencia.imagen.url  # noqa: B018


@pytest.mark.django_db
def test_acceso_el_menu_del_administrador_lleva_a_devoluciones(client, administrador):
    client.force_login(administrador)

    respuesta = client.get(reverse("devoluciones:lista"))

    assert f'href="{reverse("devoluciones:lista")}"' in respuesta.content.decode()


# ---------------------------------------------------------------------------
# Concurrencia
# ---------------------------------------------------------------------------


@pytest.mark.django_db(transaction=True)
def test_concurrencia_dos_administradores_que_resuelven_el_mismo_caso_registran_uno():
    fijar_parametros()
    caso = caso_de(UsuarioFactory(rol="cliente"))
    una = sesion_de(UsuarioFactory(rol="administrador"))
    otra = sesion_de(UsuarioFactory(rol="administrador"))

    respuestas = a_la_vez(
        lambda: una.post(reverse("devoluciones:reembolso", args=[caso.pk])),
        lambda: otra.post(reverse("devoluciones:rechazo", args=[caso.pk]), {"motivo": "No."}),
    )

    caso.refresh_from_db()
    assert errores_internos(respuestas) == []
    assert caso.estado in (CasoDevolucion.RESUELTO, CasoDevolucion.RECHAZADO)
    resoluciones = RegistroAuditoria.objects.filter(
        accion__in=(
            RegistroAuditoria.DEVOLUCION_CON_REEMBOLSO,
            RegistroAuditoria.RECHAZO_DEVOLUCION,
        )
    )
    assert resoluciones.count() == 1
    assert LotePuntos.objects.count() == (1 if caso.estado == CasoDevolucion.RESUELTO else 0)


@pytest.mark.django_db(transaction=True)
def test_concurrencia_dos_cambios_por_la_ultima_unidad_autorizan_uno():
    ultimo = ProductoFactory(stock=1, precio=Decimal("10000"))
    uno = caso_de(UsuarioFactory(rol="cliente"), como=ultimo)
    otro = caso_de(UsuarioFactory(rol="cliente"), como=ultimo)
    una = sesion_de(UsuarioFactory(rol="administrador"))
    otra = sesion_de(UsuarioFactory(rol="administrador"))

    respuestas = a_la_vez(
        lambda: una.post(reverse("devoluciones:cambio", args=[uno.pk]), {"producto": ultimo.pk}),
        lambda: otra.post(reverse("devoluciones:cambio", args=[otro.pk]), {"producto": ultimo.pk}),
    )

    ultimo.refresh_from_db()
    assert errores_internos(respuestas) == []
    assert ultimo.stock == 0
    assert ultimo.estado == Producto.AGOTADO
    assert ArticuloRetenido.objects.count() == 1
    assert CasoDevolucion.objects.filter(estado=CasoDevolucion.PENDIENTE).count() == 1


@pytest.mark.django_db(transaction=True)
def test_concurrencia_dos_pestanas_que_reclaman_el_mismo_articulo_abren_un_caso(settings, tmp_path):
    settings.EVIDENCIA_ROOT = tmp_path
    fijar_parametros()
    titular = UsuarioFactory(rol="cliente")
    pedido = pedido_despachado(titular)
    linea = pedido.lineas.get()
    una, otra = sesion_de(titular), sesion_de(titular)
    url = reverse("cuenta:devolucion", args=[pedido.numero])

    def reclamar(sesion):
        return lambda: sesion.post(
            url, {"linea": linea.pk, "motivo": CasoDevolucion.DEFECTO, "fotos": [foto()]}
        )

    respuestas = a_la_vez(reclamar(una), reclamar(otra))

    assert errores_internos(respuestas) == []
    assert CasoDevolucion.objects.filter(linea=linea).count() == 1
    assert (
        RegistroAuditoria.objects.filter(accion=RegistroAuditoria.APERTURA_DEVOLUCION).count() == 1
    )


# ---------------------------------------------------------------------------
# Las ramas de error de las pantallas
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_un_caso_inexistente_responde_404_en_todas_sus_pantallas(client, administrador):
    client.force_login(administrador)

    respuestas = [
        client.get(reverse(nombre, args=[999]))
        for nombre in (
            "devoluciones:detalle",
            "devoluciones:cambio",
            "devoluciones:reembolso",
            "devoluciones:rechazo",
        )
    ] + [
        client.post(reverse("devoluciones:cambio", args=[999]), {"producto": "1"}),
        client.post(reverse("devoluciones:reembolso", args=[999])),
        client.post(reverse("devoluciones:rechazo", args=[999]), {"motivo": "No."}),
    ]

    assert {r.status_code for r in respuestas} == {404}


@pytest.mark.django_db
def test_un_caso_ya_resuelto_no_ofrece_ni_admite_otra_resolucion(client, administrador):
    fijar_parametros()
    caso = caso_de(UsuarioFactory(rol="cliente"))
    producto = ProductoFactory(stock=3, precio=Decimal("10000"))
    client.force_login(administrador)
    client.post(reverse("devoluciones:reembolso", args=[caso.pk]))

    pantallas = [
        client.get(reverse(nombre, args=[caso.pk]))
        for nombre in ("devoluciones:cambio", "devoluciones:reembolso", "devoluciones:rechazo")
    ]
    escrituras = _escrituras(client, caso, producto)

    producto.refresh_from_db()
    destino = reverse("devoluciones:detalle", args=[caso.pk])
    assert {r.url for r in pantallas + escrituras} == {destino}
    assert producto.stock == 3
    assert LotePuntos.objects.count() == 1
    assert "Autorizar cambio" not in client.get(destino).content.decode()


@pytest.mark.django_db
def test_el_cambio_sin_producto_elegido_no_registra_nada(client, administrador):
    caso = caso_de(UsuarioFactory(rol="cliente"))
    client.force_login(administrador)

    respuesta = client.post(reverse("devoluciones:cambio", args=[caso.pk]), {"producto": ""})

    caso.refresh_from_db()
    assert respuesta.url == reverse("devoluciones:detalle", args=[caso.pk])
    assert caso.estado == CasoDevolucion.PENDIENTE


@pytest.mark.django_db
def test_el_cambio_por_un_producto_sin_stock_vuelve_a_la_busqueda(client, administrador):
    agotado = ProductoFactory(stock=0, precio=Decimal("10000"), estado=Producto.AGOTADO)
    caso = caso_de(UsuarioFactory(rol="cliente"), como=agotado)
    client.force_login(administrador)

    respuesta = client.post(
        reverse("devoluciones:cambio", args=[caso.pk]), {"producto": agotado.pk}, follow=True
    )

    assert respuesta.redirect_chain[-1][0] == reverse("devoluciones:cambio", args=[caso.pk])
    assert "no tiene stock disponible" in respuesta.content.decode()


@pytest.mark.django_db
def test_el_rechazo_desde_la_pantalla_avisa_y_vuelve_a_la_ficha(client, administrador):
    caso = caso_de(UsuarioFactory(rol="cliente"))
    client.force_login(administrador)

    formulario = client.get(reverse("devoluciones:rechazo", args=[caso.pk]))
    respuesta = client.post(
        reverse("devoluciones:rechazo", args=[caso.pk]), {"motivo": "No corresponde."}
    )

    caso.refresh_from_db()
    assert formulario.status_code == 200
    assert respuesta.url == reverse("devoluciones:detalle", args=[caso.pk])
    assert caso.estado == CasoDevolucion.RECHAZADO


@pytest.mark.django_db
def test_una_foto_que_falta_en_el_almacenamiento_responde_404(client, administrador):
    caso = caso_de(UsuarioFactory(rol="cliente"))
    evidencia = _con_foto(caso)
    evidencia.imagen.storage.delete(evidencia.imagen.name)
    client.force_login(administrador)

    respuesta = client.get(reverse("devoluciones:evidencia", args=[caso.pk, evidencia.pk]))

    assert respuesta.status_code == 404


@pytest.mark.django_db
def test_un_filtro_desconocido_muestra_los_pendientes(client, administrador):
    pendiente = caso_de(UsuarioFactory(rol="cliente"))
    client.force_login(administrador)

    respuesta = client.get(reverse("devoluciones:lista") + "?filtro=cualquiera")

    assert respuesta.context["filtro"] == "pendientes"
    assert respuesta.context["casos"] == [pendiente]
