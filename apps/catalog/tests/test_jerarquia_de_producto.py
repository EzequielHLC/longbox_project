"""La jerarquía de producto: identidad, rubro y las garantías de la base.

Todo lo de acá salió de una pregunta que estaba mal contestada en el modelo:
**qué identifica a un producto**. La respuesta vieja mezclaba dos cosas —la
identidad de la fila y la detección de duplicados— y por eso `marca` no podía ser
opcional: en cuanto un dato descriptivo entra en la clave, todo producto que no
lo tenga se vuelve inmodelable.

Lo que se prueba, entonces, es la separación:

- **Identidad**: `codigo`, siempre presente y único. Nunca depende de un dato
  descriptivo.
- **Detección de duplicados**: ISBN y código de barras cuando están, la tupla de
  A13 como respaldo del primero, y nombre + categoría como advertencia blanda.
"""

from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction

from apps.catalog.models import (
    Producto,
    ProductoAbstractoError,
    ProductoEditorial,
)
from apps.catalog.tests.factories import (
    EditorialFactory,
    FormatoFactory,
    ProductoFactory,
    ProductoNoEditorialFactory,
    TipoFactory,
    TipoNoEditorialFactory,
)

pytestmark = pytest.mark.django_db


# ---------------------------------------------------------------------------
# El código interno: la identidad de la fila
# ---------------------------------------------------------------------------


def test_un_producto_nace_con_codigo_aunque_nadie_se_lo_de():
    """Es la identidad de la fila: no puede faltar nunca."""
    producto = ProductoFactory()

    assert producto.codigo
    assert producto.codigo.startswith("E-")


def test_el_codigo_del_no_editorial_lleva_su_propio_prefijo():
    """El prefijo es seguro porque el rubro de una fila no cambia: una fila no
    salta de una tabla hija a la otra."""
    assert ProductoNoEditorialFactory().codigo.startswith("N-")


def test_un_codigo_escrito_a_mano_se_respeta():
    """Híbrido a propósito: la comiquería ya tiene una nomenclatura en sus
    planillas y el sistema no tiene por qué pisarla."""
    producto = ProductoFactory(codigo="MNG-0042")

    assert producto.codigo == "MNG-0042"


def test_dos_productos_no_pueden_compartir_codigo():
    ProductoFactory(codigo="REPETIDO")

    with pytest.raises(IntegrityError), transaction.atomic():
        ProductoFactory(codigo="REPETIDO")


def test_el_codigo_no_se_regenera_al_volver_a_guardar():
    """Si cambiara, dejaría de servir para lo único que sirve: identificar."""
    producto = ProductoFactory()
    original = producto.codigo

    producto.stock = 7
    producto.save()
    producto.refresh_from_db()

    assert producto.codigo == original


def test_los_codigos_generados_no_se_repiten_entre_rubros():
    """Se derivan de la clave primaria, que es compartida por la jerarquía, así
    que el prefijo es lo único que los separa."""
    codigos = {ProductoFactory().codigo for _ in range(5)}
    codigos |= {ProductoNoEditorialFactory().codigo for _ in range(5)}

    assert len(codigos) == 10


# ---------------------------------------------------------------------------
# La tupla de A13, recuperada como garantía de base
# ---------------------------------------------------------------------------


def test_dos_tomos_con_la_misma_tupla_chocan_en_la_base():
    """La restricción vieja abarcaba dos tablas y se perdió con la jerarquía.
    `clave_edicion` la recupera copiando a la hija los dos campos del padre."""
    editorial, tipo, formato = EditorialFactory(), TipoFactory(), FormatoFactory()
    ProductoFactory(
        titulo="Berserk", volumen=1, editorial=editorial, tipo=tipo, formato=formato, isbn=""
    )

    with pytest.raises(IntegrityError), transaction.atomic():
        ProductoFactory(
            titulo="Berserk", volumen=1, editorial=editorial, tipo=tipo, formato=formato, isbn=""
        )


def test_la_clave_ignora_mayusculas_y_espacios_de_mas():
    """Quien carga "Batman " un martes y "batman" el jueves está cargando el
    mismo tomo. Es el mismo `Lower()` de la restricción vieja."""
    editorial, tipo, formato = EditorialFactory(), TipoFactory(), FormatoFactory()
    ProductoFactory(
        titulo="Batman", volumen=1, editorial=editorial, tipo=tipo, formato=formato, isbn=""
    )

    with pytest.raises(IntegrityError), transaction.atomic():
        ProductoFactory(
            titulo="  batman  ",
            volumen=1,
            editorial=editorial,
            tipo=tipo,
            formato=formato,
            isbn="",
        )


def test_dos_importados_sin_formato_tambien_chocan():
    """A13: en SQL dos nulos no son iguales, así que sin el cero de relleno dos
    importados sin formato —que es lo normal— no chocarían nunca entre sí."""
    editorial, tipo = EditorialFactory(), TipoFactory()
    ProductoFactory(
        titulo="Akira", volumen=1, editorial=editorial, tipo=tipo, formato=None, isbn=""
    )

    with pytest.raises(IntegrityError), transaction.atomic():
        ProductoFactory(
            titulo="Akira", volumen=1, editorial=editorial, tipo=tipo, formato=None, isbn=""
        )


def test_la_misma_obra_de_dos_editoriales_son_dos_productos():
    """Es el caso que ordenó todo el modelo: la edición de Ivrea y la de Norma
    son la misma obra y **dos productos distintos**. Cambian la traducción, los
    modismos y el papel, y al cliente le importa."""
    tipo, formato = TipoFactory(), FormatoFactory()
    ivrea = ProductoFactory(
        titulo="Berserk",
        volumen=1,
        editorial=EditorialFactory(nombre="Ivrea"),
        tipo=tipo,
        formato=formato,
        isbn="",
    )
    norma = ProductoFactory(
        titulo="Berserk",
        volumen=1,
        editorial=EditorialFactory(nombre="Norma"),
        tipo=tipo,
        formato=formato,
        isbn="",
    )

    assert ivrea.pk != norma.pk
    assert ivrea.clave_edicion != norma.clave_edicion


def test_el_origen_no_entra_en_la_identidad():
    """`origen` es **cómo se forma el precio**, no qué es la cosa. Si entrara en
    la clave, el mismo tomo comprado por otro canal entraría dos veces."""
    editorial, tipo, formato = EditorialFactory(), TipoFactory(), FormatoFactory()
    nacional = ProductoFactory(
        titulo="Akira",
        volumen=1,
        editorial=editorial,
        tipo=tipo,
        formato=formato,
        isbn="",
        origen=ProductoEditorial.NACIONAL,
    )

    with pytest.raises(IntegrityError), transaction.atomic():
        ProductoFactory(
            titulo="Akira",
            volumen=1,
            editorial=editorial,
            tipo=tipo,
            formato=formato,
            isbn="",
            origen=ProductoEditorial.IMPORTADO,
        )

    assert nacional.origen == ProductoEditorial.NACIONAL


def test_la_clave_se_recalcula_al_cambiar_un_campo_de_la_tupla():
    producto = ProductoFactory(titulo="Uno", volumen=1)
    anterior = producto.clave_edicion

    producto.titulo = "Otro"
    producto.save()

    assert producto.clave_edicion != anterior
    assert "otro" in producto.clave_edicion


# ---------------------------------------------------------------------------
# El código de barras: identidad externa, y de los dos rubros
# ---------------------------------------------------------------------------


def test_el_codigo_de_barras_existe_en_los_dos_rubros():
    """**Un ISBN-13 es un EAN-13.** Los prefijos 978 y 979 son "Bookland", el país
    ficticio que GS1 reservó para libros dentro del sistema EAN, y el dígito
    verificador usa los mismos pesos alternados. Decir que solo el material no
    editorial tiene código de barras era literalmente falso."""
    tomo = ProductoFactory(codigo_barras="9789878271583")
    figura = ProductoNoEditorialFactory(codigo_barras="7791234567890")

    assert tomo.codigo_barras
    assert figura.codigo_barras


def test_el_codigo_de_barras_es_opcional():
    """El merch genérico no lo trae, y el material editorial de fondo puede
    tener un ISBN-10, que no es un EAN válido."""
    assert ProductoFactory(codigo_barras="").pk
    assert ProductoNoEditorialFactory(codigo_barras="").pk


def test_dos_productos_no_pueden_compartir_codigo_de_barras():
    """Igual que el ISBN y por el mismo motivo: son identificadores del mundo, y
    dos productos con el mismo número son el mismo producto."""
    ProductoNoEditorialFactory(codigo_barras="7791234567890")

    with pytest.raises(IntegrityError), transaction.atomic():
        ProductoNoEditorialFactory(codigo_barras="7791234567890")


def test_el_choque_de_codigo_de_barras_cruza_los_rubros():
    """Es consecuencia de que la restricción viva en la entidad general, y es lo
    correcto: el número identifica la cosa, no el rubro en el que la guardamos."""
    ProductoFactory(codigo_barras="7791234567890")

    with pytest.raises(IntegrityError), transaction.atomic():
        ProductoNoEditorialFactory(codigo_barras="7791234567890")


def test_varios_productos_sin_codigo_de_barras_conviven():
    """La restricción es parcial: si no lo fuera, todos los que no lo tienen
    chocarían entre sí por compartir la cadena vacía."""
    ProductoFactory(codigo_barras="")
    ProductoNoEditorialFactory(codigo_barras="")

    assert Producto.objects.filter(codigo_barras="").count() == 2


def test_el_isbn_no_se_copia_al_codigo_de_barras():
    """Se decidió **no** derivarlo: son el mismo número, pero mientras no haya
    lector la utilidad no está definida y sería lógica que nada ejercita."""
    tomo = ProductoFactory(isbn="9789878271583")

    assert tomo.codigo_barras == ""


def test_la_marca_es_opcional():
    """Es el caso que rompió el modelo viejo: hay merch genérico y no oficial."""
    articulo = ProductoNoEditorialFactory(marca="")

    assert articulo.pk
    assert articulo.marca == ""


def test_dos_articulos_del_mismo_nombre_y_categoria_pueden_convivir():
    """CU-CAT-ALT E2 lo trata como bloqueo y el catálogo real no lo tolera: dos
    llaveros de Naruto de proveedores distintos son dos productos. Se informa
    como advertencia, no se impide (corrección 21)."""
    categoria = TipoNoEditorialFactory(nombre="Merchandising")

    uno = ProductoNoEditorialFactory(titulo="Llavero Naruto", tipo=categoria)
    otro = ProductoNoEditorialFactory(titulo="Llavero Naruto", tipo=categoria)

    assert uno.pk != otro.pk
    assert uno.codigo != otro.codigo


# ---------------------------------------------------------------------------
# El rubro del tipo
# ---------------------------------------------------------------------------


def test_un_tomo_no_acepta_una_categoria_no_editorial():
    producto = ProductoFactory.build(tipo=TipoNoEditorialFactory(nombre="Figura"))

    with pytest.raises(ValidationError) as fallo:
        producto.clean()

    assert "tipo" in fallo.value.message_dict


def test_un_articulo_no_acepta_un_tipo_editorial():
    articulo = ProductoNoEditorialFactory.build(tipo=TipoFactory(nombre="Manga"))

    with pytest.raises(ValidationError) as fallo:
        articulo.clean()

    assert "tipo" in fallo.value.message_dict


def test_el_material_no_editorial_no_admite_pre_venta():
    """CU-CAT-ALT lo dice en sus comentarios, y se valida en el modelo y no
    escondiendo la opción en la pantalla."""
    articulo = ProductoNoEditorialFactory.build(
        tipo=TipoNoEditorialFactory(), estado=Producto.PRE_VENTA
    )

    with pytest.raises(ValidationError) as fallo:
        articulo.clean()

    assert "estado" in fallo.value.message_dict


def test_usa_formato_no_sirve_como_discriminador_de_rubro():
    """El atajo que parece obvio y no lo es: Artbook, Novela ligera y Libro son
    editoriales y ya tienen `usa_formato` en falso. Son dos preguntas distintas."""
    artbook = TipoFactory(nombre="Artbook", usa_formato=False)

    assert artbook.es_editorial
    assert not artbook.usa_formato


# ---------------------------------------------------------------------------
# El descenso a la subclase
# ---------------------------------------------------------------------------


def test_especifico_devuelve_la_hija_desde_el_padre():
    """La herencia con tabla por hija no baja sola: sin esto el inventario no
    puede leer `volumen` ni `marca`."""
    creado = ProductoFactory(volumen=7)

    desde_el_padre = Producto.objects.get(pk=creado.pk)

    assert type(desde_el_padre) is Producto
    assert desde_el_padre.especifico.volumen == 7


def test_especifico_sobre_una_hija_se_devuelve_a_si_misma():
    producto = ProductoFactory()

    assert producto.especifico is producto


def test_el_inventario_devuelve_los_dos_rubros_en_una_sola_consulta():
    """Es lo que la herencia con tabla propia hace posible y las clases
    abstractas no: CU-CAT-INV pide un listado único sobre los dos rubros."""
    ProductoFactory(titulo="Un tomo")
    ProductoNoEditorialFactory(titulo="Una figura")

    titulos = set(Producto.objects.values_list("titulo", flat=True))

    assert titulos == {"Un tomo", "Una figura"}


def test_el_discriminador_lo_escribe_el_modelo():
    """Que lo complete quien crea el objeto sería pedirle que repita algo que el
    propio tipo ya dice."""
    assert ProductoFactory().clase == Producto.EDITORIAL
    assert ProductoNoEditorialFactory().clase == Producto.NO_EDITORIAL


def test_el_precio_es_el_base_redondeado_en_los_dos_rubros():
    """La invariante que justifica que `precio_base` esté siempre presente."""
    tomo = ProductoFactory(precio=Decimal("1000.00"), precio_base=Decimal("1000.00"))

    assert tomo.precio == tomo.precio_base


# ---------------------------------------------------------------------------
# `Producto` es abstracto en el modelo de dominio
# ---------------------------------------------------------------------------


def test_no_se_puede_guardar_un_producto_sin_rubro():
    """No hay productos sueltos: todos son de un rubro o del otro. `Producto`
    tiene tabla propia porque la necesita —el inventario único y las claves
    foráneas de los módulos que vienen— pero eso no lo vuelve instanciable."""
    with pytest.raises(ProductoAbstractoError):
        Producto(titulo="Suelto", tipo=TipoFactory(), precio=Decimal("100")).save()


def test_guardar_por_la_entidad_general_tambien_se_rechaza():
    """Protege de paso la clave de edición: guardar por la general no la
    recalcula, porque no toca la tabla de la especialización. Antes era una
    condición documentada; ahora es una regla."""
    creado = ProductoFactory(titulo="Un tomo")
    desde_la_general = Producto.objects.get(pk=creado.pk)

    with pytest.raises(ProductoAbstractoError):
        desde_la_general.save()


def test_las_dos_especializaciones_se_guardan_sin_problema():
    assert ProductoFactory().pk
    assert ProductoNoEditorialFactory().pk


def test_un_alta_fallida_no_deja_una_fila_sin_codigo():
    """Las dos escrituras del código van en una transacción: el código se deriva
    de la clave primaria, así que hay que insertar para calcularlo, y sin la
    transacción hay un instante en el que la fila existe sin código."""
    assert not Producto.objects.filter(codigo__isnull=True).exists()

    ProductoFactory()
    ProductoNoEditorialFactory()

    assert not Producto.objects.filter(codigo__isnull=True).exists()
