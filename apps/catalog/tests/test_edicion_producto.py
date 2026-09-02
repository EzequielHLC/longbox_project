"""CU-09 — Editar Producto (Editorial o No Editorial).

La fuente da solo la descripción resumida de este CU: no hay flujo numerado ni
excepciones. Lo que se prueba acá sale de ahí y de las decisiones que documenta
`catalogo.md`.

Tres cosas concentran casi todos los tests, porque son donde el CU se puede
romper en silencio:

- **El duplicado al editar.** Cambiar el título o el volumen puede chocar con un
  producto que ya existe. Y el caso inverso importa igual: guardar una ficha sin
  tocarle la identidad **no** puede chocar consigo misma, o ningún producto se
  podría editar dos veces.
- **El precio manual (A1).** Editarlo a mano rompe el vínculo con la tabla de
  referencia y con el margen global. La advertencia se muestra, pero el que
  exige la confirmación es el servidor.
- **Lo que no se ofrece.** El código es la identidad y no cambia; el estado lo
  gobiernan los CU que lo mueven, y ofrecerlo acá permitiría descatalogar sin
  pasar por el informe de impacto de CU-10.
"""

from decimal import Decimal

import pytest
from django.urls import reverse

from apps.accounts.tests.factories import UsuarioFactory
from apps.catalog.models import Producto, ProductoEditorial, ProductoNoEditorial
from apps.catalog.tests.factories import (
    EditorialFactory,
    EtiquetaFactory,
    FormatoFactory,
    ProductoFactory,
    ProductoNoEditorialFactory,
    TipoFactory,
    TipoNoEditorialFactory,
)
from apps.core.models import RegistroAuditoria

pytestmark = pytest.mark.django_db


def url(producto):
    return reverse("catalog:producto_editar", args=[producto.pk])


def datos_editoriales(producto, **cambios):
    """El formulario completo de un tomo, salvo por lo que el test cambie."""
    base = {
        "titulo": producto.titulo,
        "volumen": producto.volumen,
        "isbn": producto.isbn,
        "editorial": producto.editorial_id,
        "tipo": producto.tipo_id,
        "formato": producto.formato_id or "",
        "precio": str(producto.precio),
        "stock": producto.stock,
        "fecha_llegada": "",
        "autor": producto.autor,
        "descripcion": producto.descripcion,
        "codigo_barras": producto.codigo_barras,
    }
    base.update(cambios)
    return base


def datos_no_editoriales(producto, **cambios):
    base = {
        "titulo": producto.titulo,
        "tipo": producto.tipo_id,
        "precio": str(producto.precio),
        "stock": producto.stock,
        "marca": producto.marca,
        "descripcion": producto.descripcion,
        "codigo_barras": producto.codigo_barras,
    }
    base.update(cambios)
    return base


# ---------------------------------------------------------------------------
# El camino feliz, en los dos rubros
# ---------------------------------------------------------------------------


def test_se_edita_un_tomo(client_admin):
    producto = ProductoFactory(titulo="Berserk", stock=3)

    respuesta = client_admin.post(
        url(producto), datos_editoriales(producto, titulo="Berserk Deluxe")
    )

    producto.refresh_from_db()
    assert producto.titulo == "Berserk Deluxe"
    assert respuesta.status_code == 302
    assert respuesta.url == reverse("catalog:producto_detalle", args=[producto.pk])


def test_se_edita_un_articulo_no_editorial(client_admin):
    producto = ProductoNoEditorialFactory(titulo="Llavero Naruto", marca="")

    client_admin.post(url(producto), datos_no_editoriales(producto, marca="Banpresto"))

    producto.refresh_from_db()
    assert producto.marca == "Banpresto"


def test_la_pantalla_de_cada_rubro_ofrece_sus_campos(client_admin):
    """Una vista y dos formularios: el tomo pide volumen y el artículo, marca."""
    tomo = client_admin.get(url(ProductoFactory())).content.decode()
    articulo = client_admin.get(url(ProductoNoEditorialFactory())).content.decode()

    assert 'name="volumen"' in tomo
    assert 'name="marca"' not in tomo
    assert 'name="marca"' in articulo
    assert 'name="volumen"' not in articulo


def test_guardar_sin_cambios_no_registra_nada(client_admin):
    """No es un error, pero tampoco una modificación: el historial no miente."""
    producto = ProductoFactory()

    client_admin.post(url(producto), datos_editoriales(producto))

    assert not RegistroAuditoria.objects.filter(
        accion=RegistroAuditoria.MODIFICACION_PRODUCTO
    ).exists()


# ---------------------------------------------------------------------------
# Lo que el formulario no ofrece
# ---------------------------------------------------------------------------


def test_el_codigo_no_se_puede_cambiar(client_admin):
    """Es la identidad del producto y el modelo la declara inmutable."""
    producto = ProductoNoEditorialFactory()
    original = producto.codigo

    contenido = client_admin.get(url(producto)).content.decode()
    client_admin.post(url(producto), datos_no_editoriales(producto, codigo="OTRO-123"))

    producto.refresh_from_db()
    assert 'name="codigo"' not in contenido
    assert producto.codigo == original


def test_el_estado_no_se_puede_cambiar_desde_la_edicion(client_admin):
    """Descatalogar tiene que pasar por el informe de impacto de CU-10. Un
    `select` que no se dibuja no impide mandar el valor a mano, así que lo que
    cuenta es que el servidor lo ignore."""
    producto = ProductoFactory(estado=Producto.ACTIVO)

    contenido = client_admin.get(url(producto)).content.decode()
    client_admin.post(url(producto), datos_editoriales(producto, estado=Producto.DESCATALOGADO))

    producto.refresh_from_db()
    assert 'name="estado"' not in contenido
    assert producto.estado == Producto.ACTIVO


# ---------------------------------------------------------------------------
# El duplicado al editar
# ---------------------------------------------------------------------------


def test_editar_sin_tocar_la_identidad_no_es_un_duplicado(client_admin):
    """El caso que rompería una búsqueda que no se excluya a sí misma: sin esto
    ningún producto se podría guardar dos veces."""
    producto = ProductoFactory(titulo="Berserk", stock=1)

    client_admin.post(url(producto), datos_editoriales(producto, stock=9))

    producto.refresh_from_db()
    assert producto.stock == 9


def test_el_choque_con_otro_tomo_se_informa(client_admin):
    editorial, tipo, formato = EditorialFactory(), TipoFactory(), FormatoFactory()
    ProductoFactory(titulo="Berserk", volumen=1, editorial=editorial, tipo=tipo, formato=formato)
    otro = ProductoFactory(
        titulo="Vagabond", volumen=1, editorial=editorial, tipo=tipo, formato=formato
    )

    respuesta = client_admin.post(url(otro), datos_editoriales(otro, titulo="Berserk"))

    otro.refresh_from_db()
    assert respuesta.status_code == 200
    assert otro.titulo == "Vagabond"
    assert respuesta.context["duplicado"] is not None


def test_el_choque_editorial_no_se_puede_confirmar(client_admin):
    """Las dos políticas de duplicado son opuestas, y es correcto.

    En el rubro editorial la unicidad de una edición la sostiene la base
    (`producto_editorial_unico_por_clave`), así que **no hay confirmación
    posible**: la fila no entra de ninguna manera. Ofrecer la casilla prometería
    una salida que termina en un error de integridad.
    """
    editorial, tipo, formato = EditorialFactory(), TipoFactory(), FormatoFactory()
    ProductoFactory(titulo="Berserk", volumen=1, editorial=editorial, tipo=tipo, formato=formato)
    otro = ProductoFactory(
        titulo="Vagabond", volumen=1, editorial=editorial, tipo=tipo, formato=formato
    )

    respuesta = client_admin.post(
        url(otro), datos_editoriales(otro, titulo="Berserk", confirma_duplicado="on")
    )

    otro.refresh_from_db()
    assert respuesta.status_code == 200
    assert otro.titulo == "Vagabond"
    assert 'name="confirma_duplicado"' not in respuesta.content.decode()


def test_el_choque_no_editorial_si_se_puede_confirmar(client_admin):
    """El otro rubro no tiene restricción de base y su duplicado es una
    advertencia: dos llaveros de Naruto pueden ser dos productos (corrección 21)."""
    categoria = TipoNoEditorialFactory()
    ProductoNoEditorialFactory(titulo="Llavero Naruto", tipo=categoria)
    otro = ProductoNoEditorialFactory(titulo="Llavero Sasuke", tipo=categoria)

    client_admin.post(
        url(otro),
        datos_no_editoriales(otro, titulo="Llavero Naruto", confirma_duplicado="on"),
    )

    otro.refresh_from_db()
    assert otro.titulo == "Llavero Naruto"


def test_el_isbn_repetido_se_detecta(client_admin):
    """El ISBN identifica una edición: dos filas con el mismo son la misma."""
    ProductoFactory(isbn="9788467938661")
    otro = ProductoFactory(isbn="")

    respuesta = client_admin.post(url(otro), datos_editoriales(otro, isbn="9788467938661"))

    otro.refresh_from_db()
    assert respuesta.status_code == 200
    assert otro.isbn == ""


def test_un_isbn_con_el_digito_mal_se_rechaza(client_admin):
    """Se verifica la aritmética, no una consulta externa. Un dígito mal copiado
    no falla de forma ruidosa: pasa a identificar algo que no existe."""
    producto = ProductoFactory(isbn="")

    respuesta = client_admin.post(url(producto), datos_editoriales(producto, isbn="9788467938660"))

    producto.refresh_from_db()
    assert respuesta.status_code == 200
    assert producto.isbn == ""


def test_el_articulo_no_editorial_tambien_se_excluye_a_si_mismo(client_admin):
    producto = ProductoNoEditorialFactory(titulo="Llavero Naruto", stock=1)

    client_admin.post(url(producto), datos_no_editoriales(producto, stock=7))

    producto.refresh_from_db()
    assert producto.stock == 7


# ---------------------------------------------------------------------------
# A1 — el precio fijado a mano
# ---------------------------------------------------------------------------


def test_cambiar_el_precio_exige_confirmacion(client_admin):
    """El cartel avisa; el que exige es el servidor."""
    producto = ProductoFactory(precio=Decimal("5000.00"), precio_manual=False)

    respuesta = client_admin.post(url(producto), datos_editoriales(producto, precio="7000"))

    producto.refresh_from_db()
    assert respuesta.status_code == 200
    assert producto.precio == Decimal("5000.00")


def test_confirmado_el_precio_cambia_y_queda_marcado(client_admin):
    producto = ProductoFactory(precio=Decimal("5000.00"), precio_manual=False)

    client_admin.post(
        url(producto),
        datos_editoriales(producto, precio="7000", confirma_precio_manual="on"),
    )

    producto.refresh_from_db()
    assert producto.precio == Decimal("7000.00")
    assert producto.precio_manual


def test_sin_tocar_el_precio_no_se_pide_nada(client_admin):
    producto = ProductoFactory(precio=Decimal("5000.00"), precio_manual=False)

    client_admin.post(url(producto), datos_editoriales(producto, stock=4))

    producto.refresh_from_db()
    assert producto.stock == 4
    assert not producto.precio_manual


def test_un_precio_ya_manual_no_vuelve_a_pedir_confirmacion(client_admin):
    """No hay vínculo que romper. Volver a preguntar enseña a tildar sin leer."""
    producto = ProductoFactory(precio=Decimal("5000.00"), precio_manual=True)

    client_admin.post(url(producto), datos_editoriales(producto, precio="6000"))

    producto.refresh_from_db()
    assert producto.precio == Decimal("6000.00")


def test_el_precio_desmesurado_se_rechaza(client_admin):
    producto = ProductoFactory()

    respuesta = client_admin.post(
        url(producto), datos_editoriales(producto, precio="99999999", confirma_precio_manual="on")
    )

    assert respuesta.status_code == 200


# ---------------------------------------------------------------------------
# La auditoría, que la descripción del CU pide explícitamente
# ---------------------------------------------------------------------------


def test_la_modificacion_queda_registrada(client_admin, administrador):
    producto = ProductoFactory(titulo="Berserk")

    client_admin.post(url(producto), datos_editoriales(producto, titulo="Vagabond"))

    registro = RegistroAuditoria.objects.get(accion=RegistroAuditoria.MODIFICACION_PRODUCTO)
    assert registro.actor == administrador
    assert registro.objetivo_pk == producto.pk


def test_el_registro_guarda_el_par_anterior_y_nuevo(client_admin):
    """Solo el estado final no permite reconstruir nada."""
    producto = ProductoFactory(titulo="Berserk")

    client_admin.post(url(producto), datos_editoriales(producto, titulo="Vagabond"))

    detalle = RegistroAuditoria.objects.get(accion=RegistroAuditoria.MODIFICACION_PRODUCTO).detalle
    assert "Berserk" in detalle
    assert "Vagabond" in detalle
    assert producto.codigo in detalle


def test_el_registro_nombra_los_campos_del_rubro(client_admin):
    """La marca solo existe en un rubro y el volumen solo en el otro."""
    articulo = ProductoNoEditorialFactory(marca="Bandai")

    client_admin.post(url(articulo), datos_no_editoriales(articulo, marca="Good Smile"))

    detalle = RegistroAuditoria.objects.get(accion=RegistroAuditoria.MODIFICACION_PRODUCTO).detalle
    assert "marca" in detalle
    assert "Bandai" in detalle


# ---------------------------------------------------------------------------
# La precondición amplia: se edita en cualquier estado
# ---------------------------------------------------------------------------


def test_un_producto_descatalogado_se_edita(client_admin):
    """A diferencia de una cuenta de usuario, que se congela al darse de baja:
    un producto de baja no habilita nada, y mantener sus datos al día es lo que
    permite reactivarlo."""
    producto = ProductoFactory(estado=Producto.DESCATALOGADO, stock=0)

    respuesta = client_admin.post(url(producto), datos_editoriales(producto, stock=5))

    producto.refresh_from_db()
    assert respuesta.status_code == 302
    assert producto.stock == 5
    assert producto.estado == Producto.DESCATALOGADO


def test_la_pantalla_avisa_que_esta_fuera_del_catalogo(client_admin):
    producto = ProductoFactory(estado=Producto.DESCATALOGADO)

    contenido = client_admin.get(url(producto)).content.decode()

    assert "fuera del catálogo" in contenido


# ---------------------------------------------------------------------------
# Permisos (RNF-03)
# ---------------------------------------------------------------------------


def test_el_cajero_no_edita(client):
    """CU-11 le abre la consulta al Cajero; editar sigue siendo del Administrador."""
    client.force_login(UsuarioFactory(rol="cajero"))

    assert client.get(url(ProductoFactory())).status_code == 403


def test_sin_sesion_redirige_al_login(client):
    assert client.get(url(ProductoFactory())).status_code == 302


# ---------------------------------------------------------------------------
# Los desplegables ofrecen lo que corresponde
# ---------------------------------------------------------------------------


def test_el_tomo_no_ofrece_categorias_del_otro_rubro(client_admin):
    editorial_tipo = TipoFactory(nombre="Manga de prueba")
    TipoNoEditorialFactory(nombre="Figura de prueba")
    producto = ProductoFactory(tipo=editorial_tipo)

    contenido = client_admin.get(url(producto)).content.decode()

    assert "Manga de prueba" in contenido
    assert "Figura de prueba" not in contenido


def test_las_etiquetas_se_pueden_cambiar(client_admin):
    etiqueta = EtiquetaFactory(nombre="Seinen")
    producto = ProductoFactory()

    client_admin.post(url(producto), datos_editoriales(producto, etiquetas=[etiqueta.pk]))

    assert list(producto.etiquetas.all()) == [etiqueta]


def test_un_tipo_ajeno_al_rubro_se_rechaza(client_admin):
    """El recorte del desplegable es comodidad; la validación es del servidor."""
    producto = ProductoNoEditorialFactory()
    ajeno = TipoFactory(nombre="Manga ajeno")

    respuesta = client_admin.post(url(producto), datos_no_editoriales(producto, tipo=ajeno.pk))

    producto.refresh_from_db()
    assert respuesta.status_code == 200
    assert producto.tipo != ajeno


def test_los_dos_rubros_llegan_a_su_propia_ficha(client_admin):
    """La vista baja a la instancia de la hija, que es sobre la que trabaja su
    formulario. Sin eso, un artículo no editorial se editaría con el formulario
    del otro rubro."""
    tomo = ProductoFactory()
    articulo = ProductoNoEditorialFactory()

    assert isinstance(client_admin.get(url(tomo)).context["producto"], ProductoEditorial)
    assert isinstance(client_admin.get(url(articulo)).context["producto"], ProductoNoEditorial)
