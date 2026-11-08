"""El pedido a mano busca por nombre y no le pide a un proveedor lo que trae otro (B-05-018).

Por la dirección real. Nadie recuerda trescientos códigos: cada renglón acepta el
código, el ISBN o el título con su número, y la lista ofrece «código — título #tomo».
"""

import pytest
from django.urls import reverse

from apps.accounts.tests.factories import UsuarioFactory
from apps.catalog.busqueda import SEPARADOR
from apps.catalog.models import Producto
from apps.catalog.tests.factories import EditorialFactory, ProductoFactory
from apps.suppliers.models import PedidoProveedor
from apps.suppliers.tests.factories import ProveedorFactory

pytestmark = pytest.mark.django_db

URL = reverse("suppliers:pedido_nuevo")


@pytest.fixture
def ivrea(db):
    return ProveedorFactory(razon_social="Distribuidora Ivrea", editorial=EditorialFactory())


@pytest.fixture
def panini(db):
    return ProveedorFactory(razon_social="Panini Argentina", editorial=EditorialFactory())


def tomo(de, titulo, volumen, **extra):
    """Un tomo agotado de la editorial habitual de `de` (salvo que `extra` diga otra)."""
    extra.setdefault("editorial", de.editorial)
    return ProductoFactory(
        titulo=titulo, volumen=volumen, stock=0, estado=Producto.AGOTADO, **extra
    )


def pedir(client, proveedor, *renglones):
    datos = {
        "proveedor": proveedor.pk,
        "renglon-TOTAL_FORMS": str(len(renglones)),
        "renglon-INITIAL_FORMS": "0",
    }
    for indice, (texto, cantidad) in enumerate(renglones):
        datos[f"renglon-{indice}-producto"] = texto
        datos[f"renglon-{indice}-cantidad"] = str(cantidad)
    return client.post(URL, datos)


def test_se_pide_por_el_titulo_con_su_numero(client_admin, ivrea, mailoutbox):
    frieren = tomo(ivrea, "Frieren", 9)
    tomo(ivrea, "Frieren", 10)

    pedir(client_admin, ivrea, ("frieren 9", 4))

    linea = PedidoProveedor.objects.get().lineas.get()
    assert (linea.producto_id, linea.cantidad_pedida) == (frieren.pk, 4)
    assert mailoutbox[-1].to == [ivrea.correo_comercial]


def test_se_pide_por_la_opcion_de_la_lista_con_codigo_y_nombre(client_admin, ivrea):
    frieren = tomo(ivrea, "Frieren", 9)

    pedir(client_admin, ivrea, (f"{frieren.codigo}{SEPARADOR}Frieren #9", 2))

    assert PedidoProveedor.objects.get().lineas.get().producto_id == frieren.pk


def test_la_pantalla_ofrece_el_catalogo_y_quitar_renglones(client_admin, ivrea):
    frieren = tomo(ivrea, "Frieren", 9)

    contenido = client_admin.get(URL).content.decode()

    assert f'<option value="{frieren.codigo}{SEPARADOR}Frieren #9">' in contenido
    assert 'data-autocompletado="productos-para-pedir"' in contenido
    assert "data-quitar-renglon" in contenido


def test_un_titulo_que_coincide_con_varios_pide_elegir(client_admin, ivrea, mailoutbox):
    tomo(ivrea, "Dragon Ball", 3)
    tomo(ivrea, "Dragon Ball Super", 3)

    respuesta = pedir(client_admin, ivrea, ("Dragon 3", 1))

    assert "coincide con más de un producto" in respuesta.content.decode()
    assert not PedidoProveedor.objects.exists()
    assert mailoutbox == []


# ---------------------------------------------------------------------------
# El proveedor que corresponde
# ---------------------------------------------------------------------------


def test_no_se_le_pide_a_un_proveedor_lo_que_trae_otro(client_admin, ivrea, panini, mailoutbox):
    naruto = tomo(panini, "Naruto", 72)

    respuesta = pedir(client_admin, ivrea, (naruto.codigo, 3))

    contenido = respuesta.content.decode()
    assert "lo trae Panini Argentina, no Distribuidora Ivrea" in contenido
    assert not PedidoProveedor.objects.exists()
    assert mailoutbox == []


def test_manda_el_proveedor_propio_del_producto_antes_que_el_de_su_editorial(
    client_admin, ivrea, panini, mailoutbox
):
    # Un tomo de la editorial de Panini que, según su ficha, trae Ivrea.
    importado = tomo(panini, "Akira", 1, proveedor=ivrea)

    pedir(client_admin, ivrea, (importado.codigo, 1))

    assert PedidoProveedor.objects.get().proveedor == ivrea


def test_si_no_se_sabe_quien_lo_trae_no_se_pide(client_admin, ivrea, mailoutbox):
    """B-05-021: sin proveedor identificable no hay cómo saber si este lo tiene."""
    sin_dueno = tomo(ivrea, "Sin dueño", 1, editorial=EditorialFactory())

    respuesta = pedir(client_admin, ivrea, (sin_dueno.codigo, 1))

    assert "No se sabe qué proveedor trae" in respuesta.content.decode()
    assert not PedidoProveedor.objects.exists()
    assert not mailoutbox


def test_un_renglon_de_otro_proveedor_frena_todo_el_pedido(client_admin, ivrea, panini):
    propio, ajeno = tomo(ivrea, "Frieren", 9), tomo(panini, "Naruto", 72)

    pedir(client_admin, ivrea, (propio.codigo, 1), (ajeno.codigo, 1))

    assert not PedidoProveedor.objects.exists()


@pytest.mark.parametrize("rol", ["cajero", "cliente"])
def test_el_rol_equivocado_no_pide_por_la_direccion_real(client, ivrea, rol, mailoutbox):
    frieren = tomo(ivrea, "Frieren", 9)
    client.force_login(UsuarioFactory(rol=rol))

    assert client.get(URL).status_code == 403
    assert pedir(client, ivrea, (frieren.codigo, 1)).status_code == 403
    assert not PedidoProveedor.objects.exists()
