"""Alta de lote de material editorial nacional."""

from datetime import date
from decimal import Decimal
from unittest.mock import patch

import pytest

from apps.accounts.tests.factories import UsuarioFactory
from apps.catalog.forms import MENSAJE_LOTE_VACIO
from apps.catalog.models import LoteAlta, Producto
from apps.catalog.tests.factories import (
    PVP_DE_PRUEBA,
    EditorialFactory,
    EtiquetaFactory,
    FormatoFactory,
    PrecioReferenciaFactory,
    ProductoFactory,
    TipoFactory,
)
from apps.catalog.tests.helpers_lote import URL_NACIONAL, item, lote_nacional, payload, url_ficha
from apps.core.models import RegistroAuditoria

pytestmark = pytest.mark.django_db


@pytest.fixture
def referencia():
    """La precondición del alta: la tabla tiene una combinación cargada."""
    return PrecioReferenciaFactory()


# ---------------------------------------------------------------------------
# Cabecera y herencia
# ---------------------------------------------------------------------------


def test_los_items_heredan_la_clasificacion_y_el_precio_de_la_cabecera(client_admin, referencia):
    datos = lote_nacional([item("Akira", 1), item("Akira", 2)], referencia)

    respuesta = client_admin.post(URL_NACIONAL, datos)

    assert respuesta.status_code == 302
    productos = Producto.objects.order_by("volumen")
    assert productos.count() == 2
    for producto in productos:
        assert producto.editorial == referencia.editorial
        assert producto.tipo == referencia.tipo
        assert producto.formato == referencia.formato
        assert producto.precio == PVP_DE_PRUEBA
        assert producto.origen == Producto.NACIONAL


def test_con_la_cabecera_puesta_manda_la_cabecera_aunque_el_item_declare_otra_cosa(
    client_admin, referencia
):
    """El ítem llega bloqueado en la pantalla, y el servidor sostiene la regla.

    Un `select` deshabilitado no se envía, pero nada impide mandar el campo a
    mano: si el servidor no ignorara ese valor, el bloqueo de la pantalla sería
    decorativo.
    """
    otra = EditorialFactory(nombre="Ovni Press")
    datos = lote_nacional([item("Akira", 1, editorial=otra.pk)], referencia)

    client_admin.post(URL_NACIONAL, datos)

    assert Producto.objects.get().editorial == referencia.editorial


def test_un_item_desbloqueado_declara_su_propia_clasificacion(client_admin, referencia):
    otra = EditorialFactory(nombre="Ovni Press")
    datos = lote_nacional(
        [
            item("Akira", 1),
            item(
                "Dune",
                1,
                desbloqueado="1",
                editorial=otra.pk,
                tipo=referencia.tipo.pk,
                formato=referencia.formato.pk,
                precio="12000",
            ),
        ],
        referencia,
    )

    respuesta = client_admin.post(URL_NACIONAL, datos)

    assert respuesta.status_code == 302
    assert Producto.objects.get(titulo="Akira").editorial == referencia.editorial
    assert Producto.objects.get(titulo="Dune").editorial == otra


def test_desbloquear_un_item_convierte_el_lote_en_mixto(client_admin, referencia):
    """La cabecera deja de describir al lote, así que se la vacía.

    Dejarla puesta haría que el resumen y la auditoría dijeran que todo el lote
    es de una editorial cuando no lo es.
    """
    otra = EditorialFactory(nombre="Ovni Press")
    datos = lote_nacional(
        [
            item("Akira", 1),
            item(
                "Dune",
                1,
                desbloqueado="1",
                editorial=otra.pk,
                tipo=referencia.tipo.pk,
                formato=referencia.formato.pk,
                precio="12000",
            ),
        ],
        referencia,
    )

    client_admin.post(URL_NACIONAL, datos)

    lote = LoteAlta.objects.get()
    assert lote.es_mixto is True
    assert lote.editorial is None


def test_un_item_puede_sobrescribir_el_precio_sin_desbloquear_nada(client_admin, referencia):
    """El precio y el estado siempre se pueden pisar por ítem: lo que el bloqueo
    protege es la clasificación, no los valores del alta."""
    datos = lote_nacional([item("Akira", 1), item("Akira", 2, precio="9900")], referencia)

    client_admin.post(URL_NACIONAL, datos)

    assert Producto.objects.get(volumen=1).precio == PVP_DE_PRUEBA
    assert Producto.objects.get(volumen=2).precio == Decimal("9900")


def test_el_precio_editado_a_mano_queda_excluido_de_la_propagacion(client_admin, referencia):
    """Sin la marca, un cambio de la tabla de precios le pisaría después una
    decisión que alguien tomó a propósito."""
    datos = lote_nacional([item("Akira", 1), item("Akira", 2, precio="9900")], referencia)

    client_admin.post(URL_NACIONAL, datos)

    assert Producto.objects.get(volumen=1).precio_manual is False
    assert Producto.objects.get(volumen=2).precio_manual is True


def test_el_producto_queda_vinculado_a_su_combinacion_de_la_tabla(client_admin, referencia):
    """El precio de un nacional es un vínculo, no una foto (RF-11)."""
    datos = lote_nacional([item("Akira", 1)], referencia)

    client_admin.post(URL_NACIONAL, datos)

    assert Producto.objects.get().precio_referencia == referencia


def test_en_un_lote_mixto_cada_item_declara_sus_propios_datos(client_admin):
    una = PrecioReferenciaFactory(editorial=EditorialFactory(nombre="Ovni Press"))
    otra = PrecioReferenciaFactory(editorial=EditorialFactory(nombre="Ivrea"))

    datos = payload(
        [
            item("Akira", 1, editorial=una.editorial.pk, tipo=una.tipo.pk, formato=una.formato.pk),
            item(
                "Dune",
                1,
                editorial=otra.editorial.pk,
                tipo=otra.tipo.pk,
                formato=otra.formato.pk,
                precio="12000",
            ),
        ]
    )

    respuesta = client_admin.post(URL_NACIONAL, datos)

    assert respuesta.status_code == 302
    assert Producto.objects.get(titulo="Akira").editorial == una.editorial
    assert Producto.objects.get(titulo="Dune").precio == Decimal("12000")
    assert LoteAlta.objects.get().es_mixto is True


def test_en_un_lote_mixto_falta_la_editorial_del_item(client_admin):
    tipo = TipoFactory()
    datos = payload([item("Akira", 1, tipo=tipo.pk, precio="7000")])

    respuesta = client_admin.post(URL_NACIONAL, datos)

    assert respuesta.status_code == 200
    assert respuesta.context["formset"].errors[0]["editorial"]
    assert not Producto.objects.exists()


def test_en_un_lote_mixto_falta_el_tipo_del_item(client_admin):
    editorial = EditorialFactory()
    datos = payload([item("Akira", 1, editorial=editorial.pk, precio="7000")])

    respuesta = client_admin.post(URL_NACIONAL, datos)

    assert respuesta.status_code == 200
    assert respuesta.context["formset"].errors[0]["tipo"]


def test_sin_precio_de_referencia_el_alta_pide_el_precio_a_mano(client_admin):
    """Que la combinación no esté en la tabla no bloquea el alta: solo obliga a
    escribir el precio."""
    editorial = EditorialFactory()
    tipo = TipoFactory()
    formato = FormatoFactory()
    base = {"editorial": editorial.pk, "tipo": tipo.pk, "formato": formato.pk}

    respuesta = client_admin.post(URL_NACIONAL, payload([item("Akira", 1)], **base))

    assert respuesta.status_code == 200
    assert respuesta.context["formset"].errors[0]["precio"]

    datos = payload([item("Akira", 1, precio="7000")], **base)
    assert client_admin.post(URL_NACIONAL, datos).status_code == 302
    assert Producto.objects.get().precio == Decimal("7000")


# ---------------------------------------------------------------------------
# Tipo, formato y franquicia
# ---------------------------------------------------------------------------


def test_el_formato_es_obligatorio_para_un_tipo_que_lo_usa(client_admin):
    editorial = EditorialFactory()
    tipo = TipoFactory(nombre="Manga", usa_formato=True)
    datos = payload([item("Akira", 1, precio="7000")], editorial=editorial.pk, tipo=tipo.pk)

    respuesta = client_admin.post(URL_NACIONAL, datos)

    assert respuesta.status_code == 200
    assert respuesta.context["formset"].errors[0]["formato"]


def test_un_tipo_que_no_usa_formato_no_lo_pide_ni_lo_guarda(client_admin):
    """Un artbook no se clasifica por tamaño: si viene un formato, se descarta.

    Se descarta y no se rechaza porque la pantalla esconde el campo al cambiar
    de tipo y el valor puede haber quedado de la selección anterior.
    """
    editorial = EditorialFactory()
    tipo = TipoFactory(nombre="Artbook", usa_formato=False)
    formato = FormatoFactory()
    datos = payload(
        [item("Akira Club", 1, formato=formato.pk, precio="30000")],
        editorial=editorial.pk,
        tipo=tipo.pk,
    )

    respuesta = client_admin.post(URL_NACIONAL, datos)

    assert respuesta.status_code == 302
    assert Producto.objects.get().formato is None


def test_un_comic_se_da_de_alta_sin_declarar_ninguna_etiqueta(client_admin):
    """Las etiquetas describen, no identifican: un tomo sin ninguna es un
    producto completo, solo más difícil de encontrar."""
    editorial = EditorialFactory()
    tipo = TipoFactory(nombre="Cómic", usa_formato=True)
    formato = FormatoFactory(nombre="Grapa")
    PrecioReferenciaFactory(editorial=editorial, tipo=tipo, formato=formato, pvp="8000")
    datos = payload([item("Batman", 1)], editorial=editorial.pk, tipo=tipo.pk, formato=formato.pk)

    assert client_admin.post(URL_NACIONAL, datos).status_code == 302
    producto = Producto.objects.get()
    assert not producto.etiquetas.exists()
    assert producto.precio == Decimal("8000")


def test_las_etiquetas_de_la_cabecera_las_heredan_todos_los_items(client_admin, referencia):
    """Es el motivo por el que viven en la cabecera: veinte tomos de la misma
    serie comparten franquicia y género igual que comparten editorial."""
    marvel = EtiquetaFactory(nombre="Marvel")
    datos = lote_nacional(
        [item("Civil War", 1), item("Civil War", 2)], referencia, etiquetas=marvel.pk
    )

    assert client_admin.post(URL_NACIONAL, datos).status_code == 302
    assert Producto.objects.count() == 2
    for producto in Producto.objects.all():
        assert list(producto.etiquetas.all()) == [marvel]


def test_la_cabecera_dibuja_las_etiquetas_agrupadas(client_admin):
    """Si el campo no llega a la pantalla, el formulario lo acepta igual pero
    nadie puede usarlo: es el tipo de hueco que solo se ve mirando el HTML."""
    EditorialFactory()
    EtiquetaFactory(nombre="Marvel")

    contenido = client_admin.get(URL_NACIONAL).content.decode()

    assert "Etiquetas del lote" in contenido
    assert "Franquicia" in contenido
    assert "Marvel" in contenido


def test_un_item_puede_sumar_etiquetas_propias(client_admin, referencia):
    marvel = EtiquetaFactory(nombre="Marvel")
    limitada = EtiquetaFactory(nombre="Edición limitada")
    datos = lote_nacional(
        [item("Civil War", 1, etiquetas=limitada.pk), item("Civil War", 2)],
        referencia,
        etiquetas=marvel.pk,
    )

    assert client_admin.post(URL_NACIONAL, datos).status_code == 302
    primero = Producto.objects.get(volumen=1)
    segundo = Producto.objects.get(volumen=2)
    assert set(primero.etiquetas.all()) == {marvel, limitada}
    assert set(segundo.etiquetas.all()) == {marvel}


def test_declarar_la_misma_etiqueta_arriba_y_abajo_no_la_duplica(client_admin, referencia):
    marvel = EtiquetaFactory(nombre="Marvel")
    datos = lote_nacional(
        [item("Civil War", 1, etiquetas=marvel.pk)], referencia, etiquetas=marvel.pk
    )

    assert client_admin.post(URL_NACIONAL, datos).status_code == 302
    assert Producto.objects.get().etiquetas.count() == 1


def test_una_etiqueta_desactivada_no_se_puede_elegir(client_admin, referencia):
    etiqueta = EtiquetaFactory(nombre="Universo retirado", activa=False)
    datos = lote_nacional([item("Akira", 1, etiquetas=etiqueta.pk)], referencia)

    respuesta = client_admin.post(URL_NACIONAL, datos)

    assert respuesta.status_code == 200
    assert respuesta.context["formset"].errors[0]["etiquetas"]
    assert not Producto.objects.exists()


def test_un_item_se_puede_marcar_como_solo_para_adultos(client_admin, referencia):
    """No es una etiqueta: cambia lo que el sistema hace con el producto, así
    que es un campo y la tienda va a preguntar por él, no por una cadena."""
    datos = lote_nacional([item("Akira", 1, solo_adultos="on")], referencia)

    assert client_admin.post(URL_NACIONAL, datos).status_code == 302
    assert Producto.objects.get().solo_adultos is True


def test_por_defecto_un_producto_no_es_solo_para_adultos(client_admin, referencia):
    datos = lote_nacional([item("Akira", 1)], referencia)

    assert client_admin.post(URL_NACIONAL, datos).status_code == 302
    assert Producto.objects.get().solo_adultos is False


def test_el_precio_depende_de_los_tres_campos(client_admin):
    """La misma editorial y el mismo tipo, en dos tamaños, valen distinto."""
    editorial = EditorialFactory()
    tipo = TipoFactory(nombre="Manga")
    b6 = FormatoFactory(nombre="B6")
    deluxe = FormatoFactory(nombre="Deluxe")
    PrecioReferenciaFactory(editorial=editorial, tipo=tipo, formato=b6, pvp="12500")
    PrecioReferenciaFactory(editorial=editorial, tipo=tipo, formato=deluxe, pvp="28000")

    for formato, esperado in [(b6, "12500"), (deluxe, "28000")]:
        datos = payload(
            [item("Berserk", 1)], editorial=editorial.pk, tipo=tipo.pk, formato=formato.pk
        )
        client_admin.post(URL_NACIONAL, datos)
        assert Producto.objects.get(formato=formato).precio == Decimal(esperado)


# ---------------------------------------------------------------------------
# Estado derivado de la fecha de llegada
# ---------------------------------------------------------------------------


def test_con_fecha_de_llegada_el_producto_nace_en_pre_venta(client_admin, referencia):
    datos = lote_nacional([item("Akira", 1)], referencia, fecha_llegada="2026-12-01")

    client_admin.post(URL_NACIONAL, datos)

    producto = Producto.objects.get()
    assert producto.estado == Producto.PRE_VENTA
    assert producto.fecha_llegada == date(2026, 12, 1)


def test_sin_fecha_de_llegada_el_producto_nace_activo(client_admin, referencia):
    datos = lote_nacional([item("Akira", 1)], referencia)

    client_admin.post(URL_NACIONAL, datos)

    producto = Producto.objects.get()
    assert producto.estado == Producto.ACTIVO
    assert producto.fecha_llegada is None


def test_el_item_puede_sobrescribir_el_estado_de_la_cabecera(client_admin, referencia):
    datos = lote_nacional(
        [item("Akira", 1), item("Akira", 2, estado=Producto.ACTIVO)],
        referencia,
        fecha_llegada="2026-12-01",
    )

    client_admin.post(URL_NACIONAL, datos)

    assert Producto.objects.get(volumen=1).estado == Producto.PRE_VENTA
    assert Producto.objects.get(volumen=2).estado == Producto.ACTIVO


# ---------------------------------------------------------------------------
# Duplicados contra el catálogo
# ---------------------------------------------------------------------------


def test_un_item_duplicado_se_excluye_y_los_demas_se_crean(client_admin, referencia):
    """Un duplicado no es un fallo del lote, es una exclusión esperada."""
    ProductoFactory(
        titulo="Akira",
        volumen=1,
        editorial=referencia.editorial,
        tipo=referencia.tipo,
        formato=referencia.formato,
    )
    datos = lote_nacional([item("Akira", 1), item("Akira", 2), item("Akira", 3)], referencia)

    respuesta = client_admin.post(URL_NACIONAL, datos)

    assert respuesta.status_code == 302
    assert Producto.objects.count() == 3  # el que ya existía más los dos nuevos
    assert set(Producto.objects.values_list("volumen", flat=True)) == {1, 2, 3}
    assert len(LoteAlta.objects.get().rechazados) == 1


def test_el_duplicado_se_detecta_sin_distinguir_mayusculas(client_admin, referencia):
    ProductoFactory(
        titulo="Akira",
        volumen=1,
        editorial=referencia.editorial,
        tipo=referencia.tipo,
        formato=referencia.formato,
    )
    datos = lote_nacional([item("  aKiRa  ", 1)], referencia)

    client_admin.post(URL_NACIONAL, datos)

    assert Producto.objects.count() == 1


def test_el_mismo_tomo_en_otro_formato_no_es_duplicado(client_admin):
    """Dos ediciones del mismo tomo son dos productos: distinto precio, distinto
    stock y las dos pueden estar en la góndola al mismo tiempo."""
    editorial = EditorialFactory()
    tipo = TipoFactory()
    b6 = FormatoFactory(nombre="B6")
    deluxe = FormatoFactory(nombre="Deluxe")
    PrecioReferenciaFactory(editorial=editorial, tipo=tipo, formato=deluxe, pvp="28000")
    ProductoFactory(titulo="Berserk", volumen=1, editorial=editorial, tipo=tipo, formato=b6)

    datos = payload([item("Berserk", 1)], editorial=editorial.pk, tipo=tipo.pk, formato=deluxe.pk)
    client_admin.post(URL_NACIONAL, datos)

    assert Producto.objects.count() == 2


def test_una_editorial_distinta_no_es_duplicado(client_admin):
    editorial = EditorialFactory()
    otra = PrecioReferenciaFactory(editorial=EditorialFactory())
    ProductoFactory(
        titulo="Akira", volumen=1, editorial=editorial, tipo=otra.tipo, formato=otra.formato
    )

    client_admin.post(URL_NACIONAL, lote_nacional([item("Akira", 1)], otra))

    assert Producto.objects.count() == 2


def test_el_resumen_informa_la_colision_con_enlace_a_la_ficha(client_admin, referencia):
    existente = ProductoFactory(
        titulo="Akira",
        volumen=1,
        editorial=referencia.editorial,
        tipo=referencia.tipo,
        formato=referencia.formato,
    )
    datos = lote_nacional([item("Akira", 1), item("Akira", 2)], referencia)

    respuesta = client_admin.post(URL_NACIONAL, datos, follow=True)

    contenido = respuesta.content.decode()
    assert "Excluidos del alta" in contenido
    assert url_ficha(existente) in contenido


# ---------------------------------------------------------------------------
# Auditoría y atomicidad
# ---------------------------------------------------------------------------


def test_la_confirmacion_genera_una_unica_entrada_de_auditoria(
    client_admin, administrador, referencia
):
    """Una entrada consolidada por lote, no una por ítem."""
    datos = lote_nacional([item("Akira", 1), item("Akira", 2), item("Akira", 3)], referencia)

    client_admin.post(URL_NACIONAL, datos)

    registros = RegistroAuditoria.objects.filter(accion=RegistroAuditoria.ALTA_LOTE_EDITORIAL)
    assert registros.count() == 1
    assert registros.get().actor == administrador


def test_la_auditoria_apunta_al_lote_y_no_a_una_cuenta(client_admin, referencia):
    datos = lote_nacional([item("Akira", 1)], referencia)

    client_admin.post(URL_NACIONAL, datos)

    registro = RegistroAuditoria.objects.get(accion=RegistroAuditoria.ALTA_LOTE_EDITORIAL)
    assert registro.objetivo == LoteAlta.objects.get()
    assert registro.objetivo_email == ""


def test_un_fallo_tecnico_no_deja_productos_a_medio_crear(client_admin, referencia):
    """RNF-06: la creación del lote es atómica."""
    datos = lote_nacional([item("Akira", 1), item("Akira", 2)], referencia)

    with patch(
        "apps.catalog.services.RegistroAuditoria.registrar", side_effect=RuntimeError("caída")
    ):
        with pytest.raises(RuntimeError):
            client_admin.post(URL_NACIONAL, datos)

    assert not Producto.objects.exists()
    assert not LoteAlta.objects.exists()


# ---------------------------------------------------------------------------
# Campos opcionales y validaciones sueltas
# ---------------------------------------------------------------------------


def test_un_item_sin_stock_declarado_nace_en_cero(client_admin, referencia):
    """El sistema no inventa unidades que nadie contó."""
    client_admin.post(URL_NACIONAL, lote_nacional([item("Akira", 1)], referencia))

    assert Producto.objects.get().stock == 0


def test_el_stock_declarado_se_respeta(client_admin, referencia):
    client_admin.post(URL_NACIONAL, lote_nacional([item("Akira", 1, stock="12")], referencia))

    assert Producto.objects.get().stock == 12


def test_sin_portada_el_producto_queda_marcado_como_imagen_pendiente(client_admin, referencia):
    client_admin.post(URL_NACIONAL, lote_nacional([item("Akira", 1)], referencia))

    assert Producto.objects.get().portada_pendiente is True


def test_un_item_sin_titulo_no_se_registra(client_admin, referencia):
    datos = lote_nacional([item("", 1, precio="7000")], referencia)

    respuesta = client_admin.post(URL_NACIONAL, datos)

    assert respuesta.status_code == 200
    assert respuesta.context["formset"].errors[0]["titulo"]
    assert not Producto.objects.exists()


def test_un_lote_sin_ningun_item_no_se_guarda(client_admin, referencia):
    respuesta = client_admin.post(URL_NACIONAL, lote_nacional([item("", "")], referencia))

    assert respuesta.status_code == 200
    assert MENSAJE_LOTE_VACIO in respuesta.content.decode()
    assert not LoteAlta.objects.exists()


def test_un_lote_de_un_solo_item_es_valido(client_admin, referencia):
    assert (
        client_admin.post(URL_NACIONAL, lote_nacional([item("Akira", 1)], referencia)).status_code
        == 302
    )
    assert Producto.objects.count() == 1


# ---------------------------------------------------------------------------
# RNF-03 — autorización del lado del servidor
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("rol_sin_permiso", ["cliente", "cajero"])
def test_solo_el_administrador_da_de_alta_lotes(client, rol_sin_permiso, referencia):
    client.force_login(UsuarioFactory(rol=rol_sin_permiso))
    datos = lote_nacional([item("Akira", 1)], referencia)

    assert client.get(URL_NACIONAL).status_code == 403
    assert client.post(URL_NACIONAL, datos).status_code == 403
    assert not Producto.objects.exists()


def test_sin_sesion_el_alta_redirige_al_login(client):
    respuesta = client.get(URL_NACIONAL)

    assert respuesta.status_code == 302
    assert "/cuentas/login/" in respuesta.url
