"""Inventario y ficha de producto: la contraparte de lectura del alta.

No son un CU: existen porque E1 exige enlazar a la ficha del producto con el que
se chocó, y porque después de cargar un lote hay que poder ver que quedó
cargado. Editar y dar de baja son CU-CAT-EDI y CU-CAT-BAJ (Módulo 02).
"""

from decimal import Decimal

import pytest
from django.db import IntegrityError
from django.urls import reverse

from apps.accounts.tests.factories import UsuarioFactory
from apps.catalog.models import Producto, ProductoEditorial
from apps.catalog.tests.factories import (
    EditorialFactory,
    EtiquetaFactory,
    FormatoFactory,
    LoteAltaFactory,
    ProductoFactory,
    TipoFactory,
)
from apps.catalog.tests.helpers_lote import URL_INVENTARIO, URL_NACIONAL, url_ficha

pytestmark = pytest.mark.django_db


def test_el_inventario_lista_los_productos_cargados(client_admin):
    ProductoFactory(titulo="Akira")

    respuesta = client_admin.get(URL_INVENTARIO)

    assert respuesta.status_code == 200
    assert "Akira" in respuesta.content.decode()


def test_el_buscador_filtra_por_titulo(client_admin):
    ProductoFactory(titulo="Akira")
    ProductoFactory(titulo="Berserk")

    respuesta = client_admin.get(URL_INVENTARIO, {"q": "akira"})

    contenido = respuesta.content.decode()
    assert "Akira" in contenido
    assert "Berserk" not in contenido


def test_los_filtros_ignoran_un_valor_inventado(client_admin):
    """Un valor arbitrario en la query string no rompe ni filtra de más."""
    ProductoFactory(titulo="Akira")

    respuesta = client_admin.get(URL_INVENTARIO, {"estado": "inventado"})

    assert respuesta.status_code == 200
    assert "Akira" in respuesta.content.decode()


def test_el_filtro_de_estado_funciona(client_admin):
    ProductoFactory(titulo="Akira", estado=Producto.ACTIVO)
    ProductoFactory(titulo="Berserk", estado=Producto.PRE_VENTA)

    respuesta = client_admin.get(URL_INVENTARIO, {"estado": Producto.PRE_VENTA})

    contenido = respuesta.content.decode()
    assert "Berserk" in contenido
    assert "Akira" not in contenido


def test_el_filtro_de_etiqueta_funciona(client_admin):
    """Las etiquetas no identifican un producto, pero son la forma natural de
    recortar el catálogo: "todo lo de Marvel" cruza editoriales y tipos, y
    ninguno de los otros filtros junta eso."""
    marvel = EtiquetaFactory(nombre="Marvel")
    con_etiqueta = ProductoFactory(titulo="Civil War")
    con_etiqueta.etiquetas.add(marvel)
    ProductoFactory(titulo="Akira")

    respuesta = client_admin.get(URL_INVENTARIO, {"etiqueta": marvel.pk})

    contenido = respuesta.content.decode()
    assert "Civil War" in contenido
    assert "Akira" not in contenido


def test_el_desplegable_de_etiquetas_solo_ofrece_las_que_filtran_algo(client_admin):
    """Es el único eje que puede no aplicarle a ningún producto —ninguna es
    obligatoria—, así que una etiqueta sin productos ocuparía lugar en el
    desplegable sin filtrar nada."""
    con_productos = EtiquetaFactory(nombre="Marvel")
    sin_productos = EtiquetaFactory(nombre="Star Trek")
    producto = ProductoFactory(titulo="Civil War")
    producto.etiquetas.add(con_productos)

    ofrecidas = client_admin.get(URL_INVENTARIO).context["etiquetas"]

    assert con_productos in ofrecidas
    assert sin_productos not in ofrecidas


def test_un_producto_puede_tener_varias_etiquetas(client_admin):
    """Es el defecto que la franquicia no podía expresar: Marvel publica cómics
    de Star Wars, o sea Marvel **y** Star Wars."""
    marvel = EtiquetaFactory(nombre="Marvel")
    star_wars = EtiquetaFactory(nombre="Star Wars")
    producto = ProductoFactory(titulo="Star Wars: Darth Vader")
    producto.etiquetas.set([marvel, star_wars])

    for etiqueta in (marvel, star_wars):
        respuesta = client_admin.get(URL_INVENTARIO, {"etiqueta": etiqueta.pk})
        assert "Darth Vader" in respuesta.content.decode()


def test_la_ficha_agrupa_las_etiquetas_por_su_grupo(client_admin):
    """Sin el grupo, la ficha mostraría "Marvel, Shonen, Edición limitada" como
    una bolsa. Es el mismo motivo por el que la tienda las necesita agrupadas."""
    producto = ProductoFactory(titulo="Civil War")
    producto.etiquetas.add(EtiquetaFactory(nombre="Marvel"))

    contenido = client_admin.get(url_ficha(producto)).content.decode()

    assert "Etiquetas" in contenido
    assert "Franquicia" in contenido
    assert "Marvel" in contenido


def test_el_parcial_devuelve_solo_el_fragmento_de_la_tabla(client_admin):
    ProductoFactory(titulo="Akira")

    respuesta = client_admin.get(URL_INVENTARIO, {"parcial": "1"})

    contenido = respuesta.content.decode()
    assert "Akira" in contenido
    # El fragmento no trae la cáscara de la pantalla.
    assert "<html" not in contenido


def test_la_ficha_muestra_los_datos_del_producto(client_admin):
    producto = ProductoFactory(titulo="Akira", volumen=3, autor="Katsuhiro Otomo")

    respuesta = client_admin.get(url_ficha(producto))

    contenido = respuesta.content.decode()
    assert "Akira" in contenido
    assert "Katsuhiro Otomo" in contenido


def test_la_ficha_marca_la_portada_pendiente(client_admin):
    producto = ProductoFactory()

    respuesta = client_admin.get(url_ficha(producto))

    assert "Imagen pendiente" in respuesta.content.decode()


def test_la_ficha_de_un_importado_muestra_la_composicion_del_precio(client_admin):
    lote = LoteAltaFactory(
        origen="importado", cre=Decimal("0.100000"), margen_aplicado=Decimal("0.4")
    )
    producto = ProductoFactory(
        origen=ProductoEditorial.IMPORTADO,
        costo_origen=Decimal("1000"),
        precio_base=Decimal("1100.00"),
        precio=Decimal("1540.00"),
        lote=lote,
    )

    respuesta = client_admin.get(url_ficha(producto))

    contenido = respuesta.content.decode()
    assert "Composición del precio" in contenido
    # El dinero sale como lo escribe la guía visual («$ 1.100», punto de miles);
    # el CRE, sin localizar, porque es un factor de cálculo y no un importe.
    assert "$ 1.100" in contenido
    assert "0.100000" in contenido


def test_la_ficha_avisa_cuando_el_precio_es_manual(client_admin):
    producto = ProductoFactory(precio_manual=True)

    respuesta = client_admin.get(url_ficha(producto))

    assert "fijó a mano" in respuesta.content.decode()


def test_el_inventario_avisa_cuando_esta_vacio(client_admin):
    respuesta = client_admin.get(URL_INVENTARIO)

    assert "No hay productos cargados en el catálogo." in respuesta.content.decode()


def test_el_alta_avisa_si_falta_configurar_editoriales(client_admin):
    """Sin editoriales no se puede dar de alta nada, y la pantalla lo dice.

    Los tipos vienen sembrados con la instalación; las editoriales las carga el
    negocio, así que son lo primero que puede faltar.
    """
    respuesta = client_admin.get(URL_NACIONAL)

    assert "Todavía no hay editoriales" in respuesta.content.decode()


def test_con_editoriales_cargadas_no_aparece_el_aviso(client_admin):
    EditorialFactory()

    respuesta = client_admin.get(URL_NACIONAL)

    assert "Todavía no hay" not in respuesta.content.decode()


def test_el_inventario_no_filtra_datos_al_cliente(client):
    """403 sin datos parciales, igual que la tabla de usuarios.

    **El Cajero sí entra**, y este test dejó de incluirlo en agosto 2026: es
    actor declarado de CU-CAT-INV y recibía un 403 porque estas pantallas nacieron
    dentro de Alta Editorial, que es exclusivo del Administrador. Era un defecto
    heredado, no una decisión.
    """
    ProductoFactory(titulo="Akira")
    client.force_login(UsuarioFactory(rol="cliente"))

    respuesta = client.get(URL_INVENTARIO)

    assert respuesta.status_code == 403
    assert "Akira" not in respuesta.content.decode()


def test_el_cajero_puede_consultar_el_inventario(client, cajero):
    """CU-CAT-INV lo declara actor: verifica disponibilidad para responder consultas
    de mostrador."""
    ProductoFactory(titulo="Akira")
    client.force_login(cajero)

    respuesta = client.get(URL_INVENTARIO)

    assert respuesta.status_code == 200
    assert "Akira" in respuesta.content.decode()


def test_el_cajero_puede_abrir_la_ficha(client, cajero):
    producto = ProductoFactory(titulo="Akira")
    client.force_login(cajero)

    assert client.get(url_ficha(producto)).status_code == 200


def test_la_ficha_no_se_abre_para_un_cliente(client):
    producto = ProductoFactory(titulo="Akira")
    client.force_login(UsuarioFactory(rol="cliente"))

    assert client.get(url_ficha(producto)).status_code == 403


@pytest.mark.parametrize("pantalla", ["catalog:lote_nacional", "catalog:lote_importado"])
def test_las_dos_pantallas_de_alta_se_dibujan_enteras(client_admin, pantalla):
    """Humo: las dos cargan con sus ítems vacíos y con el molde del `<template>`.

    El molde usa `empty_form`, que se arma por un camino distinto del de los
    ítems normales: si le faltara un argumento, la pantalla reventaría recién al
    abrirla y no al validar.
    """
    EditorialFactory()

    respuesta = client_admin.get(reverse(pantalla))

    assert respuesta.status_code == 200
    contenido = respuesta.content.decode()
    assert 'id="molde-item"' in contenido
    assert "{#" not in contenido


def test_cada_item_ofrece_quitarlo_y_duplicarlo(client_admin):
    """Contrato con el script de la pantalla: los `data-` son lo que busca.

    Duplicar existe porque cargar los doce tomos de una serie es el caso normal
    y es donde más se tipea de más.
    """
    EditorialFactory()

    html = client_admin.get(URL_NACIONAL).content.decode()

    assert html.count("data-quitar") >= 3
    assert html.count("data-duplicar") >= 3
    assert "data-numero" in html


def test_el_molde_de_items_nuevos_trae_los_mismos_campos_que_los_dibujados(client_admin):
    """El ítem que se agrega desde el navegador sale del `empty_form`.

    Se arma por un camino distinto del de los ítems normales: si le faltara un
    campo, el ítem agregado se guardaría incompleto y nadie lo notaría.
    """
    EditorialFactory()

    html = client_admin.get(URL_NACIONAL).content.decode()
    molde = html.split('<template id="molde-item">')[1].split("</template>")[0]

    for campo in ["titulo", "volumen", "editorial", "formato", "precio", "stock", "portada"]:
        assert f"form-__prefix__-{campo}" in molde, campo


def test_el_alta_de_importados_muestra_la_calculadora_de_envio(client_admin):
    EditorialFactory()

    respuesta = client_admin.get(reverse("catalog:lote_importado"))

    contenido = respuesta.content.decode()
    assert "Calculadora de envío" in contenido
    assert "Costo relativo de envío" in contenido


def test_el_alta_de_nacionales_no_muestra_la_calculadora_de_envio(client_admin):
    EditorialFactory()

    respuesta = client_admin.get(reverse("catalog:lote_nacional"))

    assert "Calculadora de envío" not in respuesta.content.decode()


def test_el_menu_del_administrador_ofrece_el_catalogo(client_admin):
    respuesta = client_admin.get(URL_INVENTARIO)

    contenido = respuesta.content.decode()
    assert "Nuevo lote nacional" in contenido
    assert "Nuevo lote importado" in contenido


def test_no_se_pueden_cargar_dos_productos_con_la_misma_tupla(client_admin):
    """La restricción de la base es la que realmente garantiza la unicidad:
    dos altas simultáneas pasarían las dos validaciones de formulario."""
    comun = {
        "editorial": EditorialFactory(),
        "tipo": TipoFactory(nombre="Manga"),
        "formato": FormatoFactory(nombre="B6"),
    }
    ProductoFactory(titulo="Akira", volumen=1, **comun)

    with pytest.raises(IntegrityError):
        ProductoFactory(titulo="AKIRA", volumen=1, **comun)


@pytest.mark.parametrize("sin_formato", [True, False])
def test_la_restriccion_tambien_alcanza_a_los_productos_sin_formato(client_admin, sin_formato):
    """En SQL dos nulos no son iguales: sin el `Coalesce` de la restricción, dos
    importados del mismo tomo entrarían los dos sin que nada lo impida."""
    comun = {
        "editorial": EditorialFactory(),
        "tipo": TipoFactory(nombre="Manga"),
        "formato": FormatoFactory(nombre="B6") if not sin_formato else None,
    }
    ProductoFactory(titulo="Berserk", volumen=1, **comun)

    with pytest.raises(IntegrityError):
        ProductoFactory(titulo="Berserk", volumen=1, **comun)


# ---------------------------------------------------------------------------
# El indicador de demora (CU-ALT-DEM)
#
# El caso de uso está bloqueado por Pedidos, pero el indicador se declara ahora
# por el mismo criterio que `precio_manual` y `proveedor`: agregarlo después
# obligaría a una migración retroactiva sobre productos de los que ya no se
# sabría el valor. Lo que se prueba acá es que la regla de lectura sea correcta
# desde el principio, no que la pantalla de CU-ALT-DEM exista.
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_un_producto_nuevo_no_nace_demorado():
    producto = ProductoFactory()

    assert producto.demorado is False
    assert producto.esta_demorado is False
    assert producto.fecha_estimada is None


@pytest.mark.django_db
def test_el_indicador_convive_con_pre_venta_y_no_la_reemplaza():
    """ "Demorado" no es un estado: como estado habría que elegir entre perder el
    "Pre-venta" o inventar un "Pre-venta demorado"."""
    from datetime import timedelta

    from django.utils import timezone

    producto = ProductoFactory(
        estado=Producto.PRE_VENTA,
        fecha_llegada=timezone.localdate() + timedelta(days=10),
        demorado=True,
    )

    assert producto.estado == Producto.PRE_VENTA
    assert producto.esta_en_pre_venta
    assert producto.esta_demorado


@pytest.mark.django_db
def test_un_producto_activo_no_figura_demorado_aunque_quede_la_bandera():
    """Leer la bandera sola mostraría "Demorado" en el catálogo sobre algo que
    ya está en la góndola."""
    producto = ProductoFactory(estado=Producto.ACTIVO, demorado=True)

    assert producto.demorado is True
    assert producto.esta_demorado is False


@pytest.mark.django_db
def test_la_fecha_estimada_pisa_a_la_programada():
    """Para que la ficha y las notificaciones digan lo mismo sin que cada una
    elija por su cuenta cuál de las dos mostrar."""
    from datetime import date

    producto = ProductoFactory(
        estado=Producto.PRE_VENTA,
        fecha_llegada=date(2026, 10, 1),
        fecha_estimada=date(2026, 11, 15),
        demorado=True,
    )

    assert producto.llegada_vigente == date(2026, 11, 15)


@pytest.mark.django_db
def test_sin_fecha_estimada_vale_la_programada():
    """Demorado sin fecha nueva es el flujo A1 del CU y un caso normal: el
    proveedor muchas veces avisa que se atrasa sin saber para cuándo."""
    from datetime import date

    producto = ProductoFactory(
        estado=Producto.PRE_VENTA, fecha_llegada=date(2026, 10, 1), demorado=True
    )

    assert producto.fecha_estimada is None
    assert producto.llegada_vigente == date(2026, 10, 1)


def titulos_de(respuesta):
    """Los títulos que la tabla devolvió, en orden.

    Se lee del contexto y no buscando posiciones en el HTML: un título que
    coincida con una palabra de la interfaz —"Agotado" es también el nombre de
    un estado, y aparece en el desplegable— haría pasar o fallar el test por
    un motivo que no tiene nada que ver con lo que prueba.
    """
    return [producto.titulo for producto in respuesta.context["productos"]]


# ---------------------------------------------------------------------------
# CU-CAT-INV — Consultar Inventario
#
# El listado nació como contraparte de lectura del alta en lote (A7 de
# `alta_editorial.md`), antes de que el Módulo 02 se abordara, y heredaba dos
# cosas que su propio CU contradice: estaba restringido al Administrador y
# ordenaba por fecha de alta. Acá se fija el comportamiento que el CU pide.
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_la_vista_por_defecto_muestra_solo_los_activos(client_admin):
    """Paso 2: "todos los productos en estado Activo". Un inventario que abre
    mostrando también lo descatalogado obliga a filtrar antes de poder leerlo."""
    ProductoFactory(titulo="Vigente", estado=Producto.ACTIVO)
    ProductoFactory(titulo="Retirado", volumen=2, estado=Producto.DESCATALOGADO)

    contenido = client_admin.get(URL_INVENTARIO).content.decode()

    assert "Vigente" in contenido
    assert "Retirado" not in contenido


@pytest.mark.django_db
def test_un_estado_vacio_explicito_muestra_todos(client_admin):
    """No es lo mismo que no mandar el parámetro: sin él se aplica el valor por
    defecto. Es la única forma de ver lo descatalogado."""
    ProductoFactory(titulo="Vigente", estado=Producto.ACTIVO)
    ProductoFactory(titulo="Retirado", volumen=2, estado=Producto.DESCATALOGADO)

    contenido = client_admin.get(URL_INVENTARIO, {"estado": ""}).content.decode()

    assert "Vigente" in contenido
    assert "Retirado" in contenido


@pytest.mark.django_db
def test_los_descatalogados_llevan_su_etiqueta(client_admin):
    """Paso 4: se presentan con una etiqueta visual diferenciada."""
    ProductoFactory(titulo="Retirado", estado=Producto.DESCATALOGADO)

    contenido = client_admin.get(URL_INVENTARIO, {"estado": ""}).content.decode()

    assert "Descatalogado" in contenido


@pytest.mark.django_db
def test_el_orden_por_defecto_es_alfabetico(client_admin):
    """Lo pide el paso 2. Antes ordenaba por fecha de alta descendente, que es
    lo que sirve después de cargar un lote y no lo que pide el CU."""
    ProductoFactory(titulo="Zeta")
    ProductoFactory(titulo="Alfa", volumen=2)

    respuesta = client_admin.get(URL_INVENTARIO)

    assert titulos_de(respuesta) == ["Alfa", "Zeta"]


@pytest.mark.django_db
def test_el_orden_por_lo_ultimo_cargado_sigue_disponible(client_admin):
    """Cambiar el orden por defecto no puede romper el uso que le da Alta
    Editorial: después de cargar un lote se quiere ver lo recién cargado."""
    ProductoFactory(titulo="Alfa")
    ProductoFactory(titulo="Zeta", volumen=2)

    respuesta = client_admin.get(URL_INVENTARIO, {"orden": "recientes"})

    assert titulos_de(respuesta) == ["Zeta", "Alfa"]


@pytest.mark.django_db
def test_un_orden_inventado_cae_en_el_por_defecto(client_admin):
    """Un valor de la query string no puede romper la pantalla."""
    ProductoFactory(titulo="Zeta")
    ProductoFactory(titulo="Alfa", volumen=2)

    respuesta = client_admin.get(URL_INVENTARIO, {"orden": "cualquiera"})

    assert titulos_de(respuesta) == ["Alfa", "Zeta"]


@pytest.mark.django_db
def test_el_filtro_de_stock_separa_lo_que_hay_de_lo_que_no(client_admin):
    """Es el filtro que más usa el Cajero: la pregunta del mostrador es "¿lo
    tenés?", no "¿en qué estado está?"."""
    ProductoFactory(titulo="Quedan tres", stock=3)
    ProductoFactory(titulo="No queda ninguno", volumen=2, stock=0)

    con = client_admin.get(URL_INVENTARIO, {"stock": "con"})
    sin = client_admin.get(URL_INVENTARIO, {"stock": "sin"})

    assert titulos_de(con) == ["Quedan tres"]
    assert titulos_de(sin) == ["No queda ninguno"]


@pytest.mark.django_db
def test_sin_filtro_de_stock_se_ven_los_dos(client_admin):
    ProductoFactory(titulo="Quedan tres", stock=3)
    ProductoFactory(titulo="No queda ninguno", volumen=2, stock=0)

    respuesta = client_admin.get(URL_INVENTARIO)

    assert sorted(titulos_de(respuesta)) == ["No queda ninguno", "Quedan tres"]


@pytest.mark.django_db
def test_el_catalogo_vacio_se_distingue_del_filtro_sin_resultados(client_admin):
    """Se rompió al darle un valor por defecto al estado: con un filtro siempre
    puesto, un catálogo vacío se anunciaba como "ningún resultado", que manda a
    buscar un problema donde no lo hay."""
    vacio = client_admin.get(URL_INVENTARIO).content.decode()
    assert "No hay productos cargados en el catálogo." in vacio

    ProductoFactory(titulo="Akira")
    sin_coincidencias = client_admin.get(URL_INVENTARIO, {"q": "nada"}).content.decode()
    assert "Ningún producto coincide" in sin_coincidencias


# ---------------------------------------------------------------------------
# La ficha diferenciada por rol (CU-CAT-INV paso 6)
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_el_administrador_ve_el_historial_de_modificaciones(client_admin):
    producto = ProductoFactory(titulo="Akira")

    contenido = client_admin.get(url_ficha(producto)).content.decode()

    assert "Historial de modificaciones" in contenido


@pytest.mark.django_db
def test_el_cajero_no_ve_la_informacion_interna(client, cajero):
    """No se esconde con CSS: no se dibuja. Es lo único que cuenta cuando lo que
    se protege es información y no una acción."""
    producto = ProductoFactory(titulo="Akira")
    client.force_login(cajero)

    contenido = client.get(url_ficha(producto)).content.decode()

    assert "Historial de modificaciones" not in contenido
    assert "Stock reservado en pedidos" not in contenido
    # Pero sí ve lo suyo: nombre, estado, stock y precio.
    assert "Akira" in contenido


@pytest.mark.django_db
def test_la_ficha_no_inventa_las_cifras_que_no_puede_calcular(client_admin):
    """Un cero acá se leería como "nadie lo tiene reservado", que es la
    conclusión equivocada para decidir una baja."""
    producto = ProductoFactory(titulo="Akira")

    contenido = client_admin.get(url_ficha(producto)).content.decode()

    assert "No disponible todavía" in contenido


@pytest.mark.django_db
def test_el_historial_sale_del_log_de_auditoria(client_admin, administrador):
    """Sale del log genérico, que desde A8 tiene un índice sobre
    `(objetivo_tipo, objetivo_pk)` puesto exactamente para esta consulta."""
    from apps.core.models import RegistroAuditoria

    producto = ProductoFactory(titulo="Akira")
    RegistroAuditoria.registrar(
        RegistroAuditoria.BORRADOR_CONFIRMADO,
        actor=administrador,
        objetivo=producto,
        detalle="desde el borrador #7",
    )

    contenido = client_admin.get(url_ficha(producto)).content.decode()

    assert "desde el borrador #7" in contenido
