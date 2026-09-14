"""CU-CAT-ALT — Registrar Alta de Producto No Editorial.

Es el alta del rubro secundario del negocio: TCG, figuras, merchandising e
insumos. De a uno y no por lote, a diferencia del alta editorial — cinco
artículos no editoriales no comparten nada entre sí.

Lo que más se prueba acá es el duplicado, porque es donde este CU se aparta de la
fuente. CU-CAT-ALT E2 lo trata como **bloqueo**: "el producto no es registrado". El
catálogo real no lo tolera —hay merch genérico, sin marca y no oficial— así que
pasa a ser una advertencia que el Administrador confirma (corrección 21).

El aviso llega dos veces y las dos hacen falta, con roles distintos:

- **Mientras se escribe**, por consulta a `duplicados_no_editoriales`. Es
  comodidad: sin eso el choque aparece con el formulario entero ya cargado.
- **Al guardar**, exigido por el servidor. Ese es el control, y es el que estos
  tests tratan como obligatorio: la consulta en vivo se puede esquivar.
"""

from decimal import Decimal

import pytest
from django.urls import reverse

from apps.accounts.tests.factories import UsuarioFactory
from apps.catalog.models import NO_EDITORIAL, Producto, ProductoNoEditorial, Tipo
from apps.catalog.tests.factories import (
    EtiquetaFactory,
    ProductoNoEditorialFactory,
    TipoFactory,
    TipoNoEditorialFactory,
)
from apps.core.models import RegistroAuditoria

pytestmark = pytest.mark.django_db

URL_ALTA = reverse("catalog:producto_no_editorial_alta")
URL_DUPLICADOS = reverse("catalog:duplicados_no_editoriales")


@pytest.fixture
def categoria(db):
    return TipoNoEditorialFactory(nombre="Figura")


def datos(categoria, **cambios):
    """Un alta válida, salvo por lo que el test cambie."""
    base = {
        "titulo": "Figura Nendoroid Gojo",
        "tipo": categoria.pk,
        "precio": "45000",
        "stock": "3",
        "codigo": "",
        "codigo_barras": "",
        "marca": "",
        "descripcion": "",
    }
    base.update(cambios)
    return base


# ---------------------------------------------------------------------------
# El camino feliz
# ---------------------------------------------------------------------------


def test_el_alta_crea_el_producto(client_admin, categoria):
    respuesta = client_admin.post(URL_ALTA, datos(categoria))

    producto = ProductoNoEditorial.objects.get()
    assert producto.titulo == "Figura Nendoroid Gojo"
    assert producto.tipo == categoria
    assert producto.precio == Decimal("45000")
    assert producto.stock == 3
    # El paso 8 pide terminar mostrando la ficha del producto creado.
    assert respuesta.status_code == 302
    assert respuesta.url == reverse("catalog:producto_detalle", args=[producto.pk])


def test_nace_activo_y_con_su_codigo(client_admin, categoria):
    """CU-CAT-ALT asigna exclusivamente Activo, y todo producto nace identificado."""
    client_admin.post(URL_ALTA, datos(categoria))

    producto = ProductoNoEditorial.objects.get()
    assert producto.estado == Producto.ACTIVO
    assert producto.codigo.startswith("N-")


def test_el_codigo_escrito_a_mano_se_respeta(client_admin, categoria):
    """CU-CAT-ALT paso 3 lista el "código de producto interno" entre los opcionales.
    Nuestro campo es el mismo, híbrido: se escribe o se genera."""
    client_admin.post(URL_ALTA, datos(categoria, codigo="FIG-0007"))

    assert ProductoNoEditorial.objects.get().codigo == "FIG-0007"


def test_los_opcionales_se_guardan(client_admin, categoria):
    etiqueta = EtiquetaFactory(nombre="Jujutsu Kaisen")

    client_admin.post(
        URL_ALTA,
        datos(
            categoria,
            marca="Good Smile Company",
            descripcion="Escala 1/7, edición limitada.",
            etiquetas=[etiqueta.pk],
        ),
    )

    producto = ProductoNoEditorial.objects.get()
    assert producto.marca == "Good Smile Company"
    assert producto.descripcion.startswith("Escala")
    assert list(producto.etiquetas.all()) == [etiqueta]


def test_la_marca_es_opcional(client_admin, categoria):
    """Es el caso que reescribió el modelo: hay merch genérico y no oficial."""
    client_admin.post(URL_ALTA, datos(categoria, marca=""))

    assert ProductoNoEditorial.objects.get().marca == ""


def test_la_imagen_no_bloquea_el_alta(client_admin, categoria):
    """CU-CAT-ALT paso 2 la lista entre los obligatorios; se unifica con A5 de
    `alta_editorial.md`, donde la portada tampoco bloquea. Es el mismo campo del
    mismo modelo y la misma pantalla de inventario."""
    client_admin.post(URL_ALTA, datos(categoria))

    producto = ProductoNoEditorial.objects.get()
    assert producto.portada_pendiente


# ---------------------------------------------------------------------------
# Lo que sí bloquea
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("faltante", ["titulo", "tipo", "precio", "stock"])
def test_los_obligatorios_bloquean_el_alta(client_admin, categoria, faltante):
    """E1: se resaltan, el formulario permanece abierto y no se registra nada."""
    respuesta = client_admin.post(URL_ALTA, datos(categoria, **{faltante: ""}))

    assert respuesta.status_code == 200
    assert ProductoNoEditorial.objects.count() == 0
    assert faltante in respuesta.context["form"].errors


def test_el_formulario_conserva_lo_ya_escrito(client_admin, categoria):
    """E1 lo pide explícitamente: no se reinicia vacío."""
    respuesta = client_admin.post(URL_ALTA, datos(categoria, precio=""))

    assert "Figura Nendoroid Gojo" in respuesta.content.decode()


def test_una_categoria_editorial_se_rechaza(client_admin):
    """El recorte del desplegable es comodidad; la validación es del servidor."""
    editorial = TipoFactory(nombre="Manga")

    respuesta = client_admin.post(URL_ALTA, datos(editorial, tipo=editorial.pk))

    assert respuesta.status_code == 200
    assert ProductoNoEditorial.objects.count() == 0


def test_el_formulario_no_ofrece_el_estado(client_admin, categoria):
    """No hay campo que mandar: el sistema asigna Activo."""
    contenido = client_admin.get(URL_ALTA).content.decode()

    assert 'name="estado"' not in contenido
    # El texto se parte en dos líneas del HTML, así que se busca el tramo que
    # no cruza el corte: comparar contra la frase entera haría fallar el test
    # por un salto de línea de la plantilla.
    assert "admite Pre-venta" in contenido


def test_un_precio_desmesurado_se_rechaza(client_admin, categoria):
    respuesta = client_admin.post(URL_ALTA, datos(categoria, precio="99999999"))

    assert respuesta.status_code == 200
    assert ProductoNoEditorial.objects.count() == 0


# ---------------------------------------------------------------------------
# El duplicado: advertencia, no bloqueo (corrección 21)
# ---------------------------------------------------------------------------


def test_el_duplicado_no_se_registra_sin_confirmar(client_admin, categoria):
    ProductoNoEditorialFactory(titulo="Llavero Naruto", tipo=categoria)

    respuesta = client_admin.post(URL_ALTA, datos(categoria, titulo="Llavero Naruto"))

    assert respuesta.status_code == 200
    assert ProductoNoEditorial.objects.count() == 1


def test_el_duplicado_se_informa_con_enlace_a_la_ficha_existente(client_admin, categoria):
    """E2 pide el enlace, no solo el aviso: sin él hay que ir a buscarlo a mano."""
    existente = ProductoNoEditorialFactory(titulo="Llavero Naruto", tipo=categoria)

    respuesta = client_admin.post(URL_ALTA, datos(categoria, titulo="Llavero Naruto"))

    contenido = respuesta.content.decode()
    assert reverse("catalog:producto_detalle", args=[existente.pk]) in contenido
    assert existente.codigo in contenido


def test_confirmando_el_duplicado_el_alta_procede(client_admin, categoria):
    """Dos llaveros de Naruto de proveedores distintos son dos productos. Con la
    clave dura, el Administrador tendría que inventarle un nombre al segundo."""
    ProductoNoEditorialFactory(titulo="Llavero Naruto", tipo=categoria)

    client_admin.post(
        URL_ALTA,
        datos(categoria, titulo="Llavero Naruto", confirma_duplicado="1"),
    )

    assert ProductoNoEditorial.objects.filter(titulo="Llavero Naruto").count() == 2


def test_los_dos_duplicados_tienen_códigos_distintos(client_admin, categoria):
    """Es lo que hace posible convivir: la identidad nunca fue el nombre."""
    primero = ProductoNoEditorialFactory(titulo="Llavero Naruto", tipo=categoria)

    client_admin.post(URL_ALTA, datos(categoria, titulo="Llavero Naruto", confirma_duplicado="1"))

    segundo = ProductoNoEditorial.objects.exclude(pk=primero.pk).get()
    assert primero.codigo != segundo.codigo


def test_el_mismo_nombre_en_otra_categoria_no_es_duplicado(client_admin, categoria):
    """La clave del CU es nombre **+ categoría**: un llavero y una carta con el
    mismo nombre no chocan."""
    otra = TipoNoEditorialFactory(nombre="TCG")
    ProductoNoEditorialFactory(titulo="Naruto", tipo=otra)

    client_admin.post(URL_ALTA, datos(categoria, titulo="Naruto"))

    assert ProductoNoEditorial.objects.count() == 2


def test_la_confirmacion_no_se_ofrece_cuando_no_hay_choque(client_admin, categoria):
    """Ofrecerla siempre la volvería un clic automático, que es lo mismo que no
    tenerla — el mismo motivo por el que la confirmación de cambio de correo no
    aparece en el alta de proveedor."""
    contenido = client_admin.get(URL_ALTA).content.decode()

    assert "Es un producto distinto" not in contenido


def test_el_duplicado_ignora_mayusculas_y_espacios(client_admin, categoria):
    ProductoNoEditorialFactory(titulo="Llavero Naruto", tipo=categoria)

    respuesta = client_admin.post(URL_ALTA, datos(categoria, titulo="  llavero   naruto "))

    assert respuesta.status_code == 200
    assert ProductoNoEditorial.objects.count() == 1


# ---------------------------------------------------------------------------
# El aviso temprano: comodidad, no control
# ---------------------------------------------------------------------------


def test_la_consulta_encuentra_el_choque_exacto(client_admin, categoria):
    existente = ProductoNoEditorialFactory(titulo="Llavero Naruto", tipo=categoria)

    datos_json = client_admin.get(
        URL_DUPLICADOS, {"titulo": "Llavero Naruto", "tipo": categoria.pk}
    ).json()

    assert datos_json["exacto"]["codigo"] == existente.codigo
    assert datos_json["exacto"]["url"].endswith(f"/{existente.pk}/")


def test_la_consulta_avisa_de_parecidos_en_otras_categorias(client_admin, categoria):
    """Que exista en Merchandising es información útil aunque se lo esté
    cargando en TCG: puede ser el aviso de que la categoría es la equivocada."""
    otra = TipoNoEditorialFactory(nombre="TCG")
    ProductoNoEditorialFactory(titulo="Llavero Naruto", tipo=otra)

    datos_json = client_admin.get(
        URL_DUPLICADOS, {"titulo": "Llavero Naruto", "tipo": categoria.pk}
    ).json()

    assert datos_json["exacto"] is None
    assert len(datos_json["parecidos"]) == 1


def test_la_consulta_no_devuelve_nada_con_un_nombre_muy_corto(client_admin, categoria):
    """Con una letra, todo el catálogo es un parecido."""
    ProductoNoEditorialFactory(titulo="Llavero Naruto", tipo=categoria)

    datos_json = client_admin.get(URL_DUPLICADOS, {"titulo": "L"}).json()

    assert datos_json["parecidos"] == []


def test_la_consulta_no_valida_nada(client_admin, categoria):
    """Se puede esquivar, ignorar o no llegar nunca: el duplicado se informa
    igual al guardar. Por eso el control vive en el formulario."""
    ProductoNoEditorialFactory(titulo="Llavero Naruto", tipo=categoria)

    respuesta = client_admin.post(URL_ALTA, datos(categoria, titulo="Llavero Naruto"))

    assert respuesta.status_code == 200
    assert ProductoNoEditorial.objects.count() == 1


# ---------------------------------------------------------------------------
# Auditoría y permisos
# ---------------------------------------------------------------------------


def test_el_alta_queda_auditada(client_admin, categoria, administrador):
    """La postcondición pide fecha, hora y datos del producto creado."""
    client_admin.post(URL_ALTA, datos(categoria))

    producto = ProductoNoEditorial.objects.get()
    registro = RegistroAuditoria.objects.get(accion=RegistroAuditoria.ALTA_PRODUCTO_NO_EDITORIAL)
    assert registro.actor == administrador
    assert producto.codigo in registro.detalle
    assert "stock inicial 3" in registro.detalle


@pytest.mark.parametrize("rol", ["cliente", "cajero"])
def test_el_alta_es_exclusiva_del_administrador(client, categoria, rol):
    """El Cajero consulta el inventario (CU-CAT-INV) pero no da de alta nada."""
    client.force_login(UsuarioFactory(rol=rol))

    assert client.get(URL_ALTA).status_code == 403
    assert client.post(URL_ALTA, datos(categoria)).status_code == 403
    assert client.get(URL_DUPLICADOS).status_code == 403
    assert ProductoNoEditorial.objects.count() == 0


def test_el_inventario_enlaza_el_alta(client_admin):
    contenido = client_admin.get(reverse("catalog:producto_lista")).content.decode()

    assert URL_ALTA in contenido


def test_sin_categorias_activas_la_pantalla_lo_dice(client_admin):
    """Sin ninguna, el desplegable aparecería vacío y sin explicar por qué.

    Las cuatro categorías de CU-CAT-ALT vienen sembradas por la migración, así que
    para llegar a este caso hay que desactivarlas — que es exactamente lo que
    podría pasar en una instalación real.
    """
    Tipo.objects.filter(clase=NO_EDITORIAL).update(activo=False)

    contenido = client_admin.get(URL_ALTA).content.decode()

    assert "Todavía no hay categorías no editoriales" in contenido
