"""CU-PRV-CON — Consultar Proveedores: el listado y la ficha.

Es solo lectura y el CU es explícito en que **no genera entrada de auditoría**.
Ese último punto también se prueba: consultar no es operar, y un log que
registrara cada consulta enterraría las operaciones reales.
"""

import pytest
from django.urls import reverse

from apps.accounts.tests.factories import UsuarioFactory
from apps.catalog.tests.factories import ProductoFactory
from apps.core.models import RegistroAuditoria
from apps.suppliers.models import Proveedor
from apps.suppliers.tests.factories import ProveedorFactory

pytestmark = pytest.mark.django_db

URL_LISTA = reverse("suppliers:proveedor_lista")


def url_ficha(proveedor):
    return reverse("suppliers:proveedor_detalle", args=[proveedor.pk])


# ---------------------------------------------------------------------------
# El listado
# ---------------------------------------------------------------------------


def test_el_listado_muestra_los_proveedores(client_admin):
    ProveedorFactory(razon_social="Editorial Ivrea")

    respuesta = client_admin.get(URL_LISTA)

    assert respuesta.status_code == 200
    assert "Editorial Ivrea" in respuesta.content.decode()


def test_el_listado_sale_ordenado_alfabeticamente(client_admin):
    """CU-PRV-CON paso 2: la vista por defecto es alfabética."""
    ProveedorFactory(razon_social="Ovni Press")
    ProveedorFactory(razon_social="Editorial Ivrea")
    ProveedorFactory(razon_social="Panini")

    razones = [p.razon_social for p in client_admin.get(URL_LISTA).context["proveedores"]]

    assert razones == ["Editorial Ivrea", "Ovni Press", "Panini"]


def test_cada_fila_trae_la_cantidad_de_productos_vinculados(client_admin):
    """Lo pide el paso 2, y se anota en la consulta: contarlo por fila serían
    tantas consultas extra como proveedores haya."""
    proveedor = ProveedorFactory()
    ProductoFactory(proveedor=proveedor)
    ProductoFactory(proveedor=proveedor)

    fila = client_admin.get(URL_LISTA).context["proveedores"][0]

    assert fila.cantidad_productos == 2


@pytest.mark.parametrize("campo", ["razon_social", "correo_comercial", "nombre_contacto"])
def test_el_buscador_encuentra_por_los_tres_campos(client_admin, campo):
    """Paso 3: búsqueda por texto libre. El nombre de contacto se suma a los dos
    que nombra el CU porque es por donde se busca cuando lo que se recuerda es
    con quién se habló, no cómo se llama la empresa."""
    ProveedorFactory(
        **{campo: "Buscame"} if campo != "correo_comercial" else {campo: "buscame@x.test"}
    )
    ProveedorFactory(razon_social="Otra cosa", correo_comercial="otra@x.test")

    respuesta = client_admin.get(URL_LISTA, {"q": "buscame"})

    assert respuesta.context["proveedores"].count() == 1


def test_el_filtro_de_estado_funciona(client_admin):
    ProveedorFactory(razon_social="Activa")
    ProveedorFactory(razon_social="De baja", estado=Proveedor.INACTIVO)

    contenido = client_admin.get(URL_LISTA, {"estado": Proveedor.INACTIVO}).content.decode()

    assert "De baja" in contenido
    assert "Activa" not in contenido


def test_un_estado_inventado_se_ignora(client_admin):
    """Un valor arbitrario en la query string no rompe ni filtra de más."""
    ProveedorFactory(razon_social="Editorial Ivrea")

    respuesta = client_admin.get(URL_LISTA, {"estado": "inventado"})

    assert respuesta.status_code == 200
    assert "Editorial Ivrea" in respuesta.content.decode()


def test_el_parcial_devuelve_solo_el_fragmento_de_la_tabla(client_admin):
    ProveedorFactory(razon_social="Editorial Ivrea")

    contenido = client_admin.get(URL_LISTA, {"parcial": "1"}).content.decode()

    assert "Editorial Ivrea" in contenido
    assert "<html" not in contenido


def test_sin_proveedores_ofrece_el_acceso_directo_al_alta(client_admin):
    """E2 del CU: la vista vacía informa y ofrece el camino a CU-PRV-ALT."""
    contenido = client_admin.get(URL_LISTA).content.decode()

    assert "No hay proveedores registrados" in contenido
    assert reverse("suppliers:proveedor_alta") in contenido


def test_un_filtro_sin_resultados_ofrece_limpiarlo(client_admin):
    """E1 del CU. Es un mensaje distinto del de "no hay ninguno" porque es un
    problema distinto: acá sí hay proveedores, solo que no estos."""
    ProveedorFactory(razon_social="Editorial Ivrea")

    contenido = client_admin.get(URL_LISTA, {"q": "no existe"}).content.decode()

    assert "Ningún proveedor coincide" in contenido
    assert "Limpiar filtros" in contenido


def test_consultar_no_genera_entrada_de_auditoria(client_admin):
    """Postcondición explícita del CU: solo lectura.

    Se miran las acciones del módulo y no el log entero porque abrir la sesión
    del Administrador ya deja su propia entrada, que no tiene nada que ver con
    esto.
    """
    proveedor = ProveedorFactory()

    client_admin.get(URL_LISTA)
    client_admin.get(url_ficha(proveedor))

    acciones_del_modulo = [
        RegistroAuditoria.ALTA_PROVEEDOR,
        RegistroAuditoria.MODIFICACION_PROVEEDOR,
        RegistroAuditoria.BAJA_PROVEEDOR,
        RegistroAuditoria.REACTIVACION_PROVEEDOR,
    ]
    assert not RegistroAuditoria.objects.filter(accion__in=acciones_del_modulo).exists()


# ---------------------------------------------------------------------------
# La ficha
# ---------------------------------------------------------------------------


def test_la_ficha_muestra_los_datos_de_contacto(client_admin):
    proveedor = ProveedorFactory(
        razon_social="Editorial Ivrea",
        correo_comercial="novedades@ivrea.test",
        nombre_contacto="Laura Gómez",
        telefono="376400000",
        notas="Paga a 30 días.",
    )

    contenido = client_admin.get(url_ficha(proveedor)).content.decode()

    assert "Editorial Ivrea" in contenido
    assert "novedades@ivrea.test" in contenido
    assert "Laura Gómez" in contenido
    assert "376400000" in contenido
    assert "Paga a 30 días." in contenido


def test_la_ficha_lista_los_productos_vinculados(client_admin):
    proveedor = ProveedorFactory()
    ProductoFactory(titulo="Akira", proveedor=proveedor)

    respuesta = client_admin.get(url_ficha(proveedor))

    assert respuesta.context["cantidad_productos"] == 1
    assert "Akira" in respuesta.content.decode()


def test_la_ficha_dice_si_el_correo_se_reconoce_como_remitente(client_admin):
    """Es la consecuencia práctica del estado, y no se deduce sola de la palabra
    "Inactivo"."""
    activo = ProveedorFactory()
    inactivo = ProveedorFactory(estado=Proveedor.INACTIVO)

    assert (
        "Reconocido como remitente válido" in client_admin.get(url_ficha(activo)).content.decode()
    )
    assert "No se reconoce como remitente" in client_admin.get(url_ficha(inactivo)).content.decode()


def test_la_ficha_encadena_las_acciones_del_modulo(client_admin):
    """CU-PRV-CON paso 5: desde la ficha se inician CU-PRV-EDI y CU-PRV-BAJ."""
    proveedor = ProveedorFactory()

    contenido = client_admin.get(url_ficha(proveedor)).content.decode()

    assert reverse("suppliers:proveedor_edicion", args=[proveedor.pk]) in contenido
    assert reverse("suppliers:proveedor_baja", args=[proveedor.pk]) in contenido


def test_la_ficha_de_un_inactivo_ofrece_reactivar_y_no_dar_de_baja(client_admin):
    proveedor = ProveedorFactory(estado=Proveedor.INACTIVO)

    contenido = client_admin.get(url_ficha(proveedor)).content.decode()

    assert reverse("suppliers:proveedor_reactivar", args=[proveedor.pk]) in contenido
    assert reverse("suppliers:proveedor_baja", args=[proveedor.pk]) not in contenido


def test_la_ficha_sin_pedidos_lo_dice(client_admin):
    """El paso 4 del CU pide el historial de pedidos (B-04-008). Sin pedidos se
    dice, en vez de una lista vacía."""
    proveedor = ProveedorFactory()

    contenido = client_admin.get(url_ficha(proveedor)).content.decode()

    assert "Todavía no se le hizo ningún pedido." in contenido


# ---------------------------------------------------------------------------
# Permisos y menú
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("rol_sin_permiso", ["cliente", "cajero"])
def test_el_listado_no_filtra_datos_a_otros_roles(client, rol_sin_permiso):
    proveedor = ProveedorFactory(razon_social="Editorial Ivrea")
    client.force_login(UsuarioFactory(rol=rol_sin_permiso))

    assert client.get(URL_LISTA).status_code == 403
    assert client.get(url_ficha(proveedor)).status_code == 403


def test_el_menu_del_administrador_enlaza_proveedores(client_admin):
    contenido = client_admin.get(URL_LISTA).content.decode()

    assert URL_LISTA in contenido
    assert "menu-enlace--actual" in contenido
