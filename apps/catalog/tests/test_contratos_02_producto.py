"""Contratos del ciclo de vida de un producto: alta no editorial, edición, baja y
reactivación (`CO-028`, `CO-029`, `CO-030`, `CO-032`, `CO-161`, `CO-033` a
`CO-036`).

Cada prueba lleva el código del contrato y verifica sus postcondiciones por la
dirección real, con el Administrador. Las de comportamiento —los mensajes, la
pantalla, los casos borde— viven en `test_alta_no_editorial.py`,
`test_edicion_producto.py` y `test_baja_producto.py`; acá está lo que el contrato
declara que cambia, y lo que declara que **no** cambia.
"""

from datetime import timedelta
from decimal import Decimal

import pytest
from django.urls import reverse
from django.utils import timezone

from apps.accounts.tests.factories import UsuarioFactory
from apps.catalog.models import Oferta, Producto, ProductoNoEditorial
from apps.catalog.tests.factories import (
    EditorialFactory,
    EtiquetaFactory,
    FormatoFactory,
    PrecioReferenciaFactory,
    ProductoFactory,
    ProductoNoEditorialFactory,
    TipoFactory,
    TipoNoEditorialFactory,
)
from apps.catalog.tests.test_edicion_producto import datos_editoriales, datos_no_editoriales
from apps.core.models import RegistroAuditoria
from apps.pedidos.models import LineaPedido, Pedido
from apps.pedidos.tests.util import crear_pedido
from apps.restock.models import SuscripcionReposicion
from apps.tienda.models import Carrito, LineaCarrito

pytestmark = pytest.mark.django_db

URL_ALTA = reverse("catalog:producto_no_editorial_alta")


def url_editar(producto):
    return reverse("catalog:producto_editar", args=[producto.pk])


def url_baja(producto):
    return reverse("catalog:producto_baja", args=[producto.pk])


def url_reactivar(producto):
    return reverse("catalog:producto_reactivar", args=[producto.pk])


def auditorias(accion):
    return RegistroAuditoria.objects.filter(accion=accion)


def alta(categoria, **cambios):
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


def en_el_catalogo_publico(client, producto):
    """Por el enlace a su ficha: el buscador repite el texto buscado."""
    respuesta = client.get(
        reverse("core:tienda_catalogo"), {"q": producto.titulo, "estado": "todos"}
    )
    return reverse("core:tienda_producto", args=[producto.pk]) in respuesta.content.decode()


@pytest.fixture
def categoria(db):
    return TipoNoEditorialFactory(nombre="Figura")


# ---------------------------------------------------------------------------
# CO-028 · registrarProductoNoEditorial
# ---------------------------------------------------------------------------


def test_CO028_crea_el_producto_con_sus_atributos_y_asociaciones(
    client_admin, categoria, administrador
):
    etiqueta = EtiquetaFactory()

    respuesta = client_admin.post(
        URL_ALTA,
        alta(
            categoria,
            codigo="FIG-GOJO",
            codigo_barras="4580590170000",
            marca="Good Smile",
            descripcion="Escala 1/7",
            solo_adultos="on",
            etiquetas=[etiqueta.pk],
        ),
    )

    producto = ProductoNoEditorial.objects.get()
    assert respuesta.url == reverse("catalog:producto_detalle", args=[producto.pk])
    # (a) y (b)
    assert producto.tipo == categoria
    assert list(producto.etiquetas.all()) == [etiqueta]
    # (c)
    assert producto.codigo == "FIG-GOJO"
    assert producto.estado == Producto.ACTIVO
    assert producto.stock == 3
    assert producto.precio == Decimal("45000")
    assert producto.titulo == "Figura Nendoroid Gojo"
    assert producto.marca == "Good Smile"
    assert producto.solo_adultos
    assert producto.descripcion == "Escala 1/7"
    assert producto.portada_pendiente
    registro = auditorias(RegistroAuditoria.ALTA_PRODUCTO_NO_EDITORIAL).get()
    assert registro.actor == administrador
    assert registro.objetivo_pk == producto.pk


def test_CO028_sin_codigo_declarado_se_genera_uno_unico(client_admin, categoria):
    client_admin.post(URL_ALTA, alta(categoria, titulo="Llavero Naruto"))
    client_admin.post(URL_ALTA, alta(categoria, titulo="Llavero Sasuke"))

    codigos = list(ProductoNoEditorial.objects.values_list("codigo", flat=True))
    assert all(codigos)
    assert len(set(codigos)) == 2


def test_CO028_E1_falta_un_obligatorio_no_registra_y_conserva_lo_escrito(client_admin, categoria):
    respuesta = client_admin.post(URL_ALTA, alta(categoria, precio="", marca="Bandai"))

    assert respuesta.status_code == 200
    assert not ProductoNoEditorial.objects.exists()
    assert "Bandai" in respuesta.content.decode()
    assert not auditorias(RegistroAuditoria.ALTA_PRODUCTO_NO_EDITORIAL).exists()


def test_CO028_E2_el_homonimo_advierte_con_enlace_y_no_registra_sin_confirmar(
    client_admin, categoria
):
    existente = ProductoNoEditorialFactory(titulo="Figura Nendoroid Gojo", tipo=categoria)

    respuesta = client_admin.post(URL_ALTA, alta(categoria))

    assert respuesta.status_code == 200
    assert ProductoNoEditorial.objects.count() == 1
    contenido = respuesta.content.decode()
    assert reverse("catalog:producto_detalle", args=[existente.pk]) in contenido
    assert 'name="confirma_duplicado"' in contenido


@pytest.mark.parametrize("campo", ["codigo", "codigo_barras"])
def test_CO028_E3_un_codigo_ajeno_bloquea_aunque_se_confirme(client_admin, categoria, campo):
    """La asimetría con E2 es deliberada: el código identifica, el nombre describe."""
    ProductoNoEditorialFactory(codigo="FIG-001", codigo_barras="4580590170000", tipo=categoria)
    repetido = {"codigo": "FIG-001", "codigo_barras": "4580590170000"}[campo]

    respuesta = client_admin.post(
        URL_ALTA,
        alta(categoria, titulo="Otra figura", confirma_duplicado="on", **{campo: repetido}),
    )

    assert respuesta.status_code == 200
    assert ProductoNoEditorial.objects.count() == 1


def test_CO028_precondicion_el_tipo_tiene_que_ser_del_rubro(client_admin):
    respuesta = client_admin.post(URL_ALTA, alta(TipoFactory(nombre="Manga")))

    assert respuesta.status_code == 200
    assert not ProductoNoEditorial.objects.exists()


@pytest.mark.parametrize("precio", ["0", "-10"])
def test_CO028_precondicion_el_precio_es_mayor_que_cero(client_admin, categoria, precio):
    client_admin.post(URL_ALTA, alta(categoria, precio=precio))

    assert not ProductoNoEditorial.objects.exists()


def test_CO028_precondicion_el_stock_no_es_negativo(client_admin, categoria):
    client_admin.post(URL_ALTA, alta(categoria, stock="-1"))

    assert not ProductoNoEditorial.objects.exists()


# ---------------------------------------------------------------------------
# CO-029 · confirmarAltaPeseAHomonimo
# ---------------------------------------------------------------------------


def test_CO029_confirmado_el_homonimo_se_crea_con_las_postcondiciones_de_CO028(
    client_admin, categoria, administrador
):
    existente = ProductoNoEditorialFactory(titulo="Figura Nendoroid Gojo", tipo=categoria)

    client_admin.post(URL_ALTA, alta(categoria, confirma_duplicado="on", marca="Bandai"))

    nuevo = ProductoNoEditorial.objects.exclude(pk=existente.pk).get()
    assert nuevo.codigo
    assert nuevo.codigo != existente.codigo
    assert nuevo.estado == Producto.ACTIVO
    assert nuevo.marca == "Bandai"
    assert auditorias(RegistroAuditoria.ALTA_PRODUCTO_NO_EDITORIAL).get().actor == administrador


def test_CO029_E1_un_faltante_sigue_bloqueando_aunque_se_confirme(client_admin, categoria):
    ProductoNoEditorialFactory(titulo="Figura Nendoroid Gojo", tipo=categoria)

    client_admin.post(URL_ALTA, alta(categoria, confirma_duplicado="on", precio=""))

    assert ProductoNoEditorial.objects.count() == 1


# ---------------------------------------------------------------------------
# CO-161 · abrirEdicionDeProducto
# ---------------------------------------------------------------------------


def test_CO161_muestra_los_campos_actuales_y_declara_los_inmutables(client_admin):
    producto = ProductoFactory(titulo="Berserk", stock=3)

    respuesta = client_admin.get(url_editar(producto))

    contenido = respuesta.content.decode()
    assert respuesta.context["form"].initial["titulo"] == "Berserk"
    assert producto.codigo in contenido
    assert "rubro Editorial" in contenido
    assert 'name="codigo"' not in contenido
    assert 'name="clase"' not in contenido


def test_CO161_el_importado_declara_su_costo_en_origen(client_admin):
    producto = ProductoFactory(origen="importado", costo_origen=Decimal("12.50"))

    contenido = client_admin.get(url_editar(producto)).content.decode()

    assert "costo en origen" in contenido
    assert 'name="costo_origen"' not in contenido
    assert 'name="precio_base"' not in contenido


def test_CO161_abrir_la_edicion_no_modifica_nada(client_admin):
    producto = ProductoFactory(estado=Producto.DESCATALOGADO)

    client_admin.get(url_editar(producto))

    producto.refresh_from_db()
    assert producto.estado == Producto.DESCATALOGADO
    assert not auditorias(RegistroAuditoria.MODIFICACION_PRODUCTO).exists()


# ---------------------------------------------------------------------------
# CO-030 · editarProducto
# ---------------------------------------------------------------------------


def test_CO030_los_atributos_cambian_y_la_auditoria_guarda_el_par(client_admin, administrador):
    producto = ProductoFactory(titulo="Berserk", stock=3)

    client_admin.post(url_editar(producto), datos_editoriales(producto, titulo="Vagabond", stock=5))

    producto.refresh_from_db()
    assert producto.titulo == "Vagabond"
    assert producto.stock == 5
    registro = auditorias(RegistroAuditoria.MODIFICACION_PRODUCTO).get()
    assert registro.actor == administrador
    assert "Berserk" in registro.detalle
    assert "Vagabond" in registro.detalle


def test_CO030_se_forman_y_rompen_las_asociaciones(client_admin):
    vieja, nueva = EtiquetaFactory(), EtiquetaFactory()
    producto = ProductoFactory()
    producto.etiquetas.add(vieja)
    otra_editorial = EditorialFactory()
    otro_formato = FormatoFactory()

    client_admin.post(
        url_editar(producto),
        datos_editoriales(
            producto,
            editorial=otra_editorial.pk,
            formato=otro_formato.pk,
            etiquetas=[nueva.pk],
        ),
    )

    producto.refresh_from_db()
    assert list(producto.etiquetas.all()) == [nueva]
    assert producto.editorial == otra_editorial
    assert producto.formato == otro_formato


def test_CO030_cambiar_un_precio_vinculado_cumple_CO005(client_admin):
    referencia = PrecioReferenciaFactory(pvp=Decimal("10000"))
    producto = ProductoFactory(
        editorial=referencia.editorial,
        tipo=referencia.tipo,
        formato=referencia.formato,
        precio=Decimal("10000"),
        precio_referencia=referencia,
    )

    client_admin.post(
        url_editar(producto),
        datos_editoriales(producto, precio="9500", confirma_precio_manual="on"),
    )

    producto.refresh_from_db()
    assert producto.precio == Decimal("9500")
    assert producto.precio_manual
    assert producto.precio_referencia is None


def test_CO030_E1_un_obligatorio_vacio_no_actualiza(client_admin):
    producto = ProductoFactory(titulo="Berserk")

    respuesta = client_admin.post(url_editar(producto), datos_editoriales(producto, titulo=""))

    producto.refresh_from_db()
    assert respuesta.status_code == 200
    assert producto.titulo == "Berserk"
    assert not auditorias(RegistroAuditoria.MODIFICACION_PRODUCTO).exists()


def test_CO030_E1_una_clasificacion_de_otro_rubro_no_actualiza(client_admin):
    producto = ProductoFactory()
    tipo = producto.tipo

    client_admin.post(
        url_editar(producto), datos_editoriales(producto, tipo=TipoNoEditorialFactory().pk)
    )

    producto.refresh_from_db()
    assert producto.tipo == tipo


def test_CO030_E2_la_colision_bloqueante_informa_con_enlace_y_no_actualiza(client_admin):
    editorial, tipo, formato = EditorialFactory(), TipoFactory(), FormatoFactory()
    existente = ProductoFactory(
        titulo="Berserk", volumen=1, editorial=editorial, tipo=tipo, formato=formato
    )
    otro = ProductoFactory(
        titulo="Vagabond", volumen=1, editorial=editorial, tipo=tipo, formato=formato
    )

    respuesta = client_admin.post(url_editar(otro), datos_editoriales(otro, titulo="Berserk"))

    otro.refresh_from_db()
    assert otro.titulo == "Vagabond"
    assert reverse("catalog:producto_detalle", args=[existente.pk]) in respuesta.content.decode()
    assert not auditorias(RegistroAuditoria.MODIFICACION_PRODUCTO).exists()


def test_CO030_E3_la_colision_no_bloqueante_pide_confirmacion(client_admin):
    categoria = TipoNoEditorialFactory()
    ProductoNoEditorialFactory(titulo="Llavero Naruto", tipo=categoria)
    otro = ProductoNoEditorialFactory(titulo="Llavero Sasuke", tipo=categoria)

    respuesta = client_admin.post(
        url_editar(otro), datos_no_editoriales(otro, titulo="Llavero Naruto")
    )

    otro.refresh_from_db()
    assert otro.titulo == "Llavero Sasuke"
    assert 'name="confirma_duplicado"' in respuesta.content.decode()


def test_CO030_precondicion_un_descatalogado_se_edita(client_admin):
    producto = ProductoFactory(titulo="Berserk", estado=Producto.DESCATALOGADO)

    client_admin.post(url_editar(producto), datos_editoriales(producto, titulo="Berserk Deluxe"))

    producto.refresh_from_db()
    assert producto.titulo == "Berserk Deluxe"
    assert producto.estado == Producto.DESCATALOGADO


# ---------------------------------------------------------------------------
# CO-032 · confirmarEdicionPeseAColision
# ---------------------------------------------------------------------------


def test_CO032_confirmada_la_colision_se_cumplen_las_postcondiciones_de_CO030(
    client_admin, administrador
):
    categoria = TipoNoEditorialFactory()
    ProductoNoEditorialFactory(titulo="Llavero Naruto", tipo=categoria)
    otro = ProductoNoEditorialFactory(titulo="Llavero Sasuke", tipo=categoria)

    client_admin.post(
        url_editar(otro),
        datos_no_editoriales(otro, titulo="Llavero Naruto", confirma_duplicado="on"),
    )

    otro.refresh_from_db()
    assert otro.titulo == "Llavero Naruto"
    registro = auditorias(RegistroAuditoria.MODIFICACION_PRODUCTO).get()
    assert registro.actor == administrador
    assert "Llavero Sasuke" in registro.detalle


def test_CO032_precondicion_un_tomo_no_admite_la_confirmacion(client_admin):
    editorial, tipo, formato = EditorialFactory(), TipoFactory(), FormatoFactory()
    ProductoFactory(titulo="Berserk", volumen=1, editorial=editorial, tipo=tipo, formato=formato)
    otro = ProductoFactory(
        titulo="Vagabond", volumen=1, editorial=editorial, tipo=tipo, formato=formato
    )

    client_admin.post(
        url_editar(otro), datos_editoriales(otro, titulo="Berserk", confirma_duplicado="on")
    )

    otro.refresh_from_db()
    assert otro.titulo == "Vagabond"


# ---------------------------------------------------------------------------
# CO-033 · solicitarBajaDeProducto
# ---------------------------------------------------------------------------


@pytest.fixture
def atado():
    """Un producto con algo en cada una de las cuatro categorías del informe."""
    producto = ProductoFactory(titulo="Akira", stock=2)
    otro_del_tipo = ProductoFactory(tipo=producto.tipo)
    cliente = UsuarioFactory(rol="cliente", email="lector@correo.test")

    pedido = crear_pedido(cliente)
    LineaPedido.objects.create(
        pedido=pedido,
        producto=producto,
        cantidad=1,
        precio_unitario=producto.precio,
        estado=LineaPedido.DISPONIBLE,
    )
    SuscripcionReposicion.objects.create(usuario=cliente, producto=producto)
    hoy = timezone.localdate()
    comunes = {
        "fecha_inicio": hoy,
        "fecha_vencimiento": hoy + timedelta(days=10),
        "tipo_descuento": Oferta.PORCENTAJE,
        "valor": Decimal("10"),
        "estado": Oferta.ACTIVA,
    }
    exclusiva = Oferta.objects.create(
        descripcion="Sólo Akira", alcance=Oferta.PRODUCTO, producto=producto, **comunes
    )
    del_tipo = Oferta.objects.create(
        descripcion="Todo el tipo", alcance=Oferta.TIPO, tipo=producto.tipo, **comunes
    )
    carrito = Carrito.objects.create(usuario=cliente, persistencia=Carrito.PERSISTENTE)
    LineaCarrito.objects.create(
        carrito=carrito,
        producto=producto,
        cantidad=1,
        precio_vigente=producto.precio,
        precio_visto=producto.precio,
    )
    return {
        "producto": producto,
        "otro_del_tipo": otro_del_tipo,
        "pedido": pedido,
        "exclusiva": exclusiva,
        "del_tipo": del_tipo,
        "carrito": carrito,
    }


def test_CO033_el_informe_trae_las_cuatro_categorias_y_la_accion(client_admin, atado):
    respuesta = client_admin.get(url_baja(atado["producto"]))

    impacto = respuesta.context["impacto"]
    assert impacto.pedidos_activos == 1
    assert impacto.suscripciones_de_reposicion == 1
    assert impacto.ofertas_vigentes == 2
    assert impacto.carritos_con_el_producto == 1


def test_CO033_pedir_el_informe_no_modifica_nada(client_admin, atado):
    producto = atado["producto"]

    client_admin.get(url_baja(producto))

    producto.refresh_from_db()
    assert producto.estado == Producto.ACTIVO
    assert SuscripcionReposicion.objects.filter(producto=producto).exists()
    assert Oferta.objects.filter(pk=atado["exclusiva"].pk).exists()
    assert not RegistroAuditoria.objects.filter(accion=RegistroAuditoria.BAJA_PRODUCTO).exists()


def test_CO033_E2_un_cancelado_por_editorial_se_rechaza(client_admin):
    producto = ProductoFactory(estado=Producto.CANCELADO_EDITORIAL)

    contenido = client_admin.get(url_baja(producto)).content.decode()

    assert "Confirmar baja" not in contenido


# ---------------------------------------------------------------------------
# CO-034 · confirmarBajaDeProducto
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("estado", [Producto.ACTIVO, Producto.PRE_VENTA, Producto.AGOTADO])
def test_CO034_el_estado_pasa_a_descatalogado(client_admin, estado):
    producto = ProductoFactory(estado=estado, stock=0 if estado != Producto.ACTIVO else 2)

    client_admin.post(url_baja(producto))

    producto.refresh_from_db()
    assert producto.estado == Producto.DESCATALOGADO


def test_CO034_deja_de_verse_en_el_catalogo_publico_y_la_busqueda(client, client_admin):
    producto = ProductoFactory(titulo="Akira Edición Única", stock=2)
    assert en_el_catalogo_publico(client, producto)

    client_admin.post(url_baja(producto))

    assert not en_el_catalogo_publico(client, producto)


def test_CO034_las_suscripciones_quedan_canceladas(client_admin, atado):
    client_admin.post(url_baja(atado["producto"]))

    assert not SuscripcionReposicion.objects.filter(
        producto=atado["producto"], estado__in=SuscripcionReposicion.EN_ESPERA
    ).exists()


def test_CO034_la_oferta_exclusiva_queda_dada_de_baja_y_la_del_tipo_lo_deja_de_alcanzar(
    client_admin, atado
):
    """Desvío B-02-007: el contrato dice eliminarla; el responsable decidió que
    quede Dada de baja, como cualquier baja de oferta, con su entrada propia."""
    client_admin.post(url_baja(atado["producto"]))

    exclusiva = Oferta.objects.get(pk=atado["exclusiva"].pk)
    assert exclusiva.estado == Oferta.DADA_DE_BAJA
    assert RegistroAuditoria.objects.filter(
        accion=RegistroAuditoria.BAJA_OFERTA, objetivo_pk=exclusiva.pk
    ).exists()
    # La del tipo sigue para los demás: referencia a varios y no se elimina.
    del_tipo = Oferta.objects.get(pk=atado["del_tipo"].pk)
    assert del_tipo.estado == Oferta.ACTIVA


def test_CO034_el_carrito_queda_no_disponible_y_el_cliente_se_entera(
    client, client_admin, atado, mailoutbox, django_capture_on_commit_callbacks
):
    with django_capture_on_commit_callbacks(execute=True):
        client_admin.post(url_baja(atado["producto"]))

    linea = LineaCarrito.objects.get(carrito=atado["carrito"])
    linea.producto.refresh_from_db()
    assert linea.producto.estado == Producto.DESCATALOGADO
    assert [correo.to for correo in mailoutbox] == [["lector@correo.test"]]
    assert "Akira" in mailoutbox[0].subject

    client.force_login(atado["carrito"].usuario)
    assert "no disponible" in client.get(reverse("tienda:carrito")).content.decode().lower()


def test_CO034_los_pedidos_activos_no_se_modifican(client_admin, atado):
    """Postcondición negativa explícita del caso de uso."""
    pedido = atado["pedido"]
    antes = (pedido.estado, list(pedido.lineas.values_list("producto_id", "cantidad", "estado")))

    client_admin.post(url_baja(atado["producto"]))

    pedido.refresh_from_db()
    despues = (pedido.estado, list(pedido.lineas.values_list("producto_id", "cantidad", "estado")))
    assert despues == antes
    assert pedido.estado != Pedido.CANCELADO


def test_CO034_una_sola_entrada_con_el_impacto_resuelto(client_admin, atado, administrador):
    client_admin.post(url_baja(atado["producto"]))

    registro = auditorias(RegistroAuditoria.BAJA_PRODUCTO).get()
    assert registro.actor == administrador
    assert "Activo" in registro.detalle
    assert "Descatalogado" in registro.detalle
    assert "suscripciones canceladas: 1" in registro.detalle
    assert "ofertas dadas de baja: 1" in registro.detalle
    assert "carritos marcados: 1" in registro.detalle


def test_CO034_E1_sin_referencias_la_baja_procede_igual(client_admin, mailoutbox):
    producto = ProductoFactory()

    client_admin.post(url_baja(producto))

    producto.refresh_from_db()
    assert producto.estado == Producto.DESCATALOGADO
    assert auditorias(RegistroAuditoria.BAJA_PRODUCTO).count() == 1
    assert mailoutbox == []


# ---------------------------------------------------------------------------
# CO-035 · solicitarReactivacionDeProducto
# ---------------------------------------------------------------------------


def test_CO035_el_resumen_no_modifica_nada(client_admin):
    producto = ProductoFactory(estado=Producto.DESCATALOGADO)

    respuesta = client_admin.get(url_reactivar(producto))

    producto.refresh_from_db()
    assert respuesta.status_code == 200
    assert producto.estado == Producto.DESCATALOGADO
    assert not auditorias(RegistroAuditoria.REACTIVACION_PRODUCTO).exists()


def test_CO035_E1_un_cancelado_por_editorial_se_rechaza(client_admin):
    producto = ProductoFactory(estado=Producto.CANCELADO_EDITORIAL)

    client_admin.post(url_reactivar(producto))

    producto.refresh_from_db()
    assert producto.estado == Producto.CANCELADO_EDITORIAL
    assert not auditorias(RegistroAuditoria.REACTIVACION_PRODUCTO).exists()


# ---------------------------------------------------------------------------
# CO-036 · confirmarReactivacionDeProducto
# ---------------------------------------------------------------------------


def test_CO036_vuelve_activo_y_visible_con_su_identidad(client, client_admin):
    etiqueta = EtiquetaFactory()
    producto = ProductoFactory(titulo="Akira Edición Única", stock=2)
    producto.etiquetas.add(etiqueta)
    codigo = producto.codigo
    client_admin.post(url_baja(producto))

    client_admin.post(url_reactivar(producto))

    producto.refresh_from_db()
    assert producto.estado == Producto.ACTIVO
    assert producto.codigo == codigo
    assert list(producto.etiquetas.all()) == [etiqueta]
    assert en_el_catalogo_publico(client, producto)
    # Su historial se conserva: la baja sigue apuntando al mismo producto.
    assert auditorias(RegistroAuditoria.BAJA_PRODUCTO).get().objetivo_pk == producto.pk


def test_CO036_el_material_para_adultos_sigue_sujeto_a_su_indicador(client, client_admin):
    producto = ProductoFactory(titulo="Akira Edición Única", stock=2, estado=Producto.DESCATALOGADO)
    producto.solo_adultos = True
    producto.save(update_fields=["solo_adultos"])

    client_admin.post(url_reactivar(producto))

    assert not en_el_catalogo_publico(client, producto)


def test_CO036_no_se_restituyen_suscripciones_ni_ofertas(client_admin, atado):
    """Postcondición negativa explícita."""
    producto = atado["producto"]
    client_admin.post(url_baja(producto))

    client_admin.post(url_reactivar(producto))

    assert not SuscripcionReposicion.objects.filter(producto=producto).exists()
    assert Oferta.objects.get(producto=producto).estado == Oferta.DADA_DE_BAJA


def test_CO036_la_entrada_guarda_el_estado_anterior_y_el_nuevo(client_admin, administrador):
    producto = ProductoFactory(estado=Producto.DESCATALOGADO)

    client_admin.post(url_reactivar(producto))

    registro = auditorias(RegistroAuditoria.REACTIVACION_PRODUCTO).get()
    assert registro.actor == administrador
    assert "Descatalogado" in registro.detalle
    assert "Activo" in registro.detalle


def test_CO036_E2_la_fecha_vencida_queda_sin_efecto_y_se_informa(client_admin):
    producto = ProductoFactory(
        estado=Producto.DESCATALOGADO,
        fecha_llegada=timezone.localdate() - timedelta(days=30),
    )

    respuesta = client_admin.post(url_reactivar(producto), follow=True)

    producto.refresh_from_db()
    assert producto.estado == Producto.ACTIVO
    assert "quedó sin efecto" in respuesta.content.decode()


# ---------------------------------------------------------------------------
# Control de acceso: por la dirección real, con el rol equivocado
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("rol", ["cajero", "cliente"])
def test_CO028_el_alta_no_la_hace_otro_rol(client, categoria, rol):
    client.force_login(UsuarioFactory(rol=rol))

    respuesta = client.post(URL_ALTA, alta(categoria))

    assert respuesta.status_code in (302, 403)
    assert not ProductoNoEditorial.objects.exists()


@pytest.mark.parametrize("rol", ["cajero", "cliente"])
def test_CO030_la_edicion_no_la_hace_otro_rol(client, rol):
    client.force_login(UsuarioFactory(rol=rol))
    producto = ProductoFactory(titulo="Berserk")

    client.post(url_editar(producto), datos_editoriales(producto, titulo="Vagabond"))

    producto.refresh_from_db()
    assert producto.titulo == "Berserk"


@pytest.mark.parametrize("rol", ["cajero", "cliente"])
def test_CO034_CO036_baja_y_reactivacion_no_las_hace_otro_rol(client, rol):
    client.force_login(UsuarioFactory(rol=rol))
    activo = ProductoFactory()
    fuera = ProductoFactory(estado=Producto.DESCATALOGADO)

    client.post(url_baja(activo))
    client.post(url_reactivar(fuera))

    activo.refresh_from_db()
    fuera.refresh_from_db()
    assert activo.estado == Producto.ACTIVO
    assert fuera.estado == Producto.DESCATALOGADO
