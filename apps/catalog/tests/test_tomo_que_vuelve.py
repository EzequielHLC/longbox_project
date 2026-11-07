"""El tomo cancelado por la editorial que vuelve a anunciarse (B-01-026).

`CU-ALT-CAN` deja al cancelado en un estado del que no se vuelve, y en el historial.
El que vuelve es **otra edición, con código nuevo**, enlazada a la cancelada. La
cancelación retira la edición y libera su ISBN y su clave; las restricciones de
unicidad valen sólo entre ediciones vivas. Postcondiciones negativas incluidas: el
cancelado no cambia, y dos ediciones vivas iguales siguen chocando.
"""

from decimal import Decimal

import pytest
from django.db import IntegrityError, transaction
from django.urls import reverse

from apps.catalog import revisiones, services
from apps.catalog.models import BorradorProducto, LoteAlta, Producto, ProductoEditorial
from apps.catalog.tests.factories import ProductoFactory
from apps.pedidos import preventa
from apps.pedidos.tests.util import crear_preventa
from apps.suppliers.models import CorreoProveedor
from apps.suppliers.tests.factories import ProveedorFactory

pytestmark = pytest.mark.django_db

ISBN = "9789870028550"


@pytest.fixture
def cancelado(administrador):
    tomo = crear_preventa(titulo="Sakamoto Days", volumen=24, isbn=ISBN)
    preventa.cancelar_preventa(tomo, administrador)
    return ProductoEditorial.objects.get(pk=tomo.pk)


def igual_a(tomo, **cambios):
    datos = {
        "titulo": tomo.titulo,
        "volumen": tomo.volumen,
        "isbn": tomo.isbn,
        "editorial": tomo.editorial,
        "tipo": tomo.tipo,
        "formato": tomo.formato,
        "precio": Decimal("12000"),
        "precio_base": Decimal("12000"),
        "stock": 0,
        "estado": Producto.ACTIVO,
    }
    datos.update(cambios)
    return ProductoEditorial.objects.create(**datos)


# ---------------------------------------------------------------------------
# CO-027 · la cancelación retira la edición
# ---------------------------------------------------------------------------


def test_CO027_cancelar_retira_la_edición(cancelado):
    assert cancelado.estado == Producto.CANCELADO_EDITORIAL
    assert cancelado.edicion_retirada is True


def test_CO027_cancelar_no_toca_el_isbn_ni_el_código(cancelado):
    """El cancelado queda en el historial tal cual: sólo se libera la identidad."""
    assert (cancelado.isbn, cancelado.codigo) == (ISBN, cancelado.codigo)
    assert cancelado.clave_edicion == cancelado.calcular_clave_edicion()


def test_una_preventa_viva_no_está_retirada():
    assert crear_preventa(titulo="Frieren", volumen=9).edicion_retirada is False


# ---------------------------------------------------------------------------
# La identidad liberada
# ---------------------------------------------------------------------------


def test_el_cancelado_ya_no_cuenta_como_duplicado(cancelado):
    duplicado = services.buscar_duplicado(
        cancelado.titulo,
        cancelado.volumen,
        cancelado.tipo,
        cancelado.formato,
        cancelado.editorial,
        cancelado.isbn,
    )

    assert duplicado is None


def test_pero_se_lo_encuentra_para_avisar(cancelado):
    retirada = services.buscar_retirada(
        cancelado.titulo,
        cancelado.volumen,
        cancelado.tipo,
        cancelado.formato,
        cancelado.editorial,
        cancelado.isbn,
    )

    assert retirada.pk == cancelado.pk


def test_el_que_vuelve_nace_con_código_nuevo_y_enlazado(cancelado):
    nuevo = igual_a(cancelado)

    assert nuevo.codigo != cancelado.codigo
    assert nuevo.reanuncia_a_id == cancelado.pk
    assert list(cancelado.reanunciada_como.all()) == [nuevo]


def test_sin_isbn_se_enlaza_por_la_clave(administrador):
    tomo = crear_preventa(titulo="Dandadan", volumen=3, isbn="")
    preventa.cancelar_preventa(tomo, administrador)

    nuevo = igual_a(ProductoEditorial.objects.get(pk=tomo.pk))

    assert nuevo.reanuncia_a_id == tomo.pk


def test_el_cancelado_no_cambia_cuando_vuelve(cancelado):
    """Postcondición negativa: el historial del cancelado queda intacto."""
    igual_a(cancelado)

    cancelado.refresh_from_db()
    assert cancelado.estado == Producto.CANCELADO_EDITORIAL
    assert cancelado.edicion_retirada and cancelado.isbn == ISBN


def test_un_tomo_distinto_no_se_enlaza(cancelado):
    otro = igual_a(cancelado, volumen=25, isbn="")

    assert otro.reanuncia_a is None


def test_si_vuelve_y_se_cancela_otra_vez_el_tercero_reanuncia_al_último(cancelado, administrador):
    segundo = igual_a(cancelado, estado=Producto.PRE_VENTA, stock=0)
    preventa.cancelar_preventa(segundo, administrador)

    tercero = igual_a(cancelado)

    assert tercero.reanuncia_a_id == segundo.pk


def test_dos_ediciones_vivas_iguales_siguen_chocando_en_la_base():
    """Postcondición negativa: la restricción sigue valiendo entre las vivas."""
    vivo = ProductoFactory(titulo="Akira", volumen=1, isbn="9789878271583")

    with pytest.raises(IntegrityError), transaction.atomic():
        igual_a(vivo)


def test_la_clave_viva_también_sigue_chocando():
    vivo = ProductoFactory(titulo="Akira", volumen=2, isbn="")

    with pytest.raises(IntegrityError), transaction.atomic():
        igual_a(vivo, isbn="")


# ---------------------------------------------------------------------------
# Los caminos de alta
# ---------------------------------------------------------------------------


def test_el_lote_lo_carga_en_vez_de_rechazarlo(cancelado, administrador):
    lote = LoteAlta(origen=LoteAlta.NACIONAL)
    item = {
        "titulo": cancelado.titulo,
        "volumen": cancelado.volumen,
        "isbn": cancelado.isbn,
        "editorial": cancelado.editorial,
        "tipo": cancelado.tipo,
        "formato": cancelado.formato,
        "origen": ProductoEditorial.NACIONAL,
        "estado": Producto.ACTIVO,
        "precio": Decimal("12000"),
        "precio_base": Decimal("12000"),
        "stock": 3,
    }

    resultado = services.registrar_lote(lote=lote, items=[item], actor=administrador)

    assert not resultado.rechazados
    (nuevo,) = resultado.creados
    assert nuevo.reanuncia_a_id == cancelado.pk


def test_el_borrador_del_correo_se_confirma_como_reanuncio(cancelado, administrador):
    proveedor = ProveedorFactory(editorial=cancelado.editorial, tipo_por_defecto=cancelado.tipo)
    correo = CorreoProveedor.objects.create(
        proveedor=proveedor,
        message_id="<vuelve@ivrea.test>",
        remitente=proveedor.correo_comercial,
        estado=CorreoProveedor.PROCESADO,
    )
    borrador = BorradorProducto.objects.create(
        correo=correo,
        proveedor=proveedor,
        titulo=cancelado.titulo,
        volumen=cancelado.volumen,
        isbn=cancelado.isbn,
        editorial=cancelado.editorial,
        tipo=cancelado.tipo,
        formato=cancelado.formato,
        precio=Decimal("12000"),
        stock_inicial=2,
        estado_sugerido=Producto.ACTIVO,
    )

    confirmacion = revisiones.confirmar(borrador, actor=administrador, confirma_precio_manual=True)

    assert confirmacion.motivo != revisiones.YA_EXISTE
    nuevo = ProductoEditorial.objects.exclude(pk=cancelado.pk).get(isbn=ISBN)
    assert nuevo.reanuncia_a_id == cancelado.pk


# ---------------------------------------------------------------------------
# Las pantallas
# ---------------------------------------------------------------------------


def test_la_ficha_del_cancelado_ofrece_volver_a_anunciar(client_admin, cancelado):
    html = client_admin.get(
        reverse("catalog:producto_detalle", args=[cancelado.pk])
    ).content.decode()

    assert "Volver a anunciar" in html
    assert f"{reverse('catalog:lote_nacional')}?reanuncia={cancelado.pk}" in html


def test_una_ficha_viva_no_ofrece_volver_a_anunciar(client_admin):
    vivo = ProductoFactory()

    html = client_admin.get(reverse("catalog:producto_detalle", args=[vivo.pk])).content.decode()

    assert "Volver a anunciar" not in html


def test_las_dos_fichas_se_enlazan(client_admin, cancelado):
    nuevo = igual_a(cancelado)

    del_nuevo = client_admin.get(
        reverse("catalog:producto_detalle", args=[nuevo.pk])
    ).content.decode()
    del_viejo = client_admin.get(
        reverse("catalog:producto_detalle", args=[cancelado.pk])
    ).content.decode()

    assert "Reanuncia a" in del_nuevo and cancelado.codigo in del_nuevo
    assert "Reanunciado como" in del_viejo and nuevo.codigo in del_viejo


def test_volver_a_anunciar_precarga_el_lote(client_admin, cancelado):
    respuesta = client_admin.get(f"{reverse('catalog:lote_nacional')}?reanuncia={cancelado.pk}")

    html = respuesta.content.decode()
    assert f'value="{cancelado.titulo}"' in html
    assert f'value="{cancelado.isbn}"' in html
    assert "edición nueva" in html


def test_volver_a_anunciar_algo_que_no_está_cancelado_no_precarga(client_admin):
    vivo = ProductoFactory(titulo="Vagabond")

    html = client_admin.get(
        f"{reverse('catalog:lote_nacional')}?reanuncia={vivo.pk}"
    ).content.decode()

    assert 'value="Vagabond"' not in html


def test_el_borrador_avisa_que_el_tomo_vuelve(client_admin, cancelado):
    proveedor = ProveedorFactory(editorial=cancelado.editorial, tipo_por_defecto=cancelado.tipo)
    correo = CorreoProveedor.objects.create(
        proveedor=proveedor,
        message_id="<aviso@ivrea.test>",
        remitente=proveedor.correo_comercial,
        estado=CorreoProveedor.PROCESADO,
    )
    borrador = BorradorProducto.objects.create(
        correo=correo,
        proveedor=proveedor,
        titulo=cancelado.titulo,
        volumen=cancelado.volumen,
        isbn=cancelado.isbn,
        editorial=cancelado.editorial,
        tipo=cancelado.tipo,
        formato=cancelado.formato,
        precio=Decimal("12000"),
        stock_inicial=1,
        estado_sugerido=Producto.ACTIVO,
    )

    html = client_admin.get(
        reverse("catalog:borrador_detalle", args=[borrador.pk])
    ).content.decode()

    assert "Este tomo vuelve a anunciarse" in html
    assert "Este producto ya está en el catálogo" not in html


def test_sigue_sin_poder_reactivarse(client_admin, cancelado):
    """`CU-CAT-REA` no admite un cancelado: volver es otra edición, no reactivarlo."""
    client_admin.post(reverse("catalog:producto_reactivar", args=[cancelado.pk]))

    cancelado.refresh_from_db()
    assert cancelado.estado == Producto.CANCELADO_EDITORIAL
