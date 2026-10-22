"""Pruebas de contrato del módulo 04 · Proveedores (el padrón).

Cubre `CO-061` y `CO-062` (CU-PRV-EDI), `CO-063` y `CO-064` (CU-PRV-BAJ), `CO-065`
y `CO-066` (CU-PRV-REA), y `CO-171` a `CO-173` (la apertura de la edición y la
consulta). La cola de correos está en `test_contratos_04_proveedores.py`.

Se escriben desde el contrato, según `docs/pruebas/ESPECIFICACION.md` apartado 3:
se captura el valor anterior de lo que cambia, se ejerce la operación **por su
dirección real** una vez y se afirma cada postcondición por separado, incluidas
las negativas.
"""

import pytest
from django.urls import reverse

from apps.accounts.tests.factories import UsuarioFactory
from apps.catalog.models import Producto
from apps.catalog.tests.factories import EditorialFactory, ProductoFactory, TipoFactory
from apps.core.models import RegistroAuditoria
from apps.restock.models import LineaPropuestaRestock, PropuestaRestock
from apps.suppliers import pedidos
from apps.suppliers.models import Proveedor
from apps.suppliers.tests.factories import ProveedorFactory
from apps.suppliers.tests.test_edicion_proveedor import datos

pytestmark = pytest.mark.django_db

URL_LISTA = reverse("suppliers:proveedor_lista")


def url_editar(proveedor):
    return reverse("suppliers:proveedor_edicion", args=[proveedor.pk])


def url_baja(proveedor):
    return reverse("suppliers:proveedor_baja", args=[proveedor.pk])


def url_reactivar(proveedor):
    return reverse("suppliers:proveedor_reactivar", args=[proveedor.pk])


def url_ficha(proveedor):
    return reverse("suppliers:proveedor_detalle", args=[proveedor.pk])


def auditorias(accion):
    return RegistroAuditoria.objects.filter(accion=accion)


def remitente(correo):
    return Proveedor.objects.remitente_valido(correo)


def en_propuesta(producto):
    propuesta = PropuestaRestock.objects.create(tipo_disparo=PropuestaRestock.MANUAL)
    return LineaPropuestaRestock.objects.create(
        propuesta=propuesta, producto=producto, cantidad_sugerida=3
    )


# ---------------------------------------------------------------------------
# CO-060 · registrarProveedor
# ---------------------------------------------------------------------------

URL_ALTA = reverse("suppliers:proveedor_alta")


def alta(**cambios):
    base = {
        "razon_social": "  Editorial   Ivrea ",
        "correo_comercial": "Novedades@Ivrea.TEST",
        "editorial": "",
        "tipo_por_defecto": "",
        "nombre_contacto": "Laura",
        "telefono": "376400000",
        "notas": "",
    }
    base.update(cambios)
    return base


def test_CO060_crea_el_proveedor_activo_normalizado_y_habilitado(client_admin, administrador):
    editorial, tipo = EditorialFactory(), TipoFactory()

    respuesta = client_admin.post(
        URL_ALTA, alta(editorial=editorial.pk, tipo_por_defecto=tipo.pk, procesa_novedades="on")
    )

    proveedor = Proveedor.objects.get()
    assert respuesta.url == url_ficha(proveedor)
    assert proveedor.estado == Proveedor.ACTIVO
    assert proveedor.procesa_novedades is True
    assert proveedor.razon_social == "Editorial Ivrea"
    assert proveedor.correo_comercial == "novedades@ivrea.test"
    assert proveedor.nombre_contacto == "Laura"
    assert proveedor.editorial == editorial
    assert proveedor.tipo_por_defecto == tipo
    assert proveedor.creado_en is not None
    assert remitente("novedades@ivrea.test") == proveedor
    registro = auditorias(RegistroAuditoria.ALTA_PROVEEDOR).get()
    assert registro.actor == administrador
    assert registro.objetivo_pk == proveedor.pk


def test_CO060_el_procesamiento_apagado_queda_apagado(client_admin):
    client_admin.post(URL_ALTA, alta())

    assert Proveedor.objects.get().procesa_novedades is False
    assert remitente("novedades@ivrea.test") is None


def test_CO060_E1_un_obligatorio_vacio_no_procede(client_admin):
    respuesta = client_admin.post(URL_ALTA, alta(correo_comercial=""))

    assert respuesta.status_code == 200
    assert not Proveedor.objects.exists()


def test_CO060_E2_un_dato_repetido_en_cualquier_estado_enlaza_la_ficha(client_admin):
    existente = ProveedorFactory(razon_social="Editorial Ivrea", estado=Proveedor.INACTIVO)

    respuesta = client_admin.post(URL_ALTA, alta())

    assert Proveedor.objects.count() == 1
    assert url_ficha(existente) in respuesta.content.decode()
    assert not auditorias(RegistroAuditoria.ALTA_PROVEEDOR).exists()


# ---------------------------------------------------------------------------
# CO-171 · abrirEdicionDeProveedor
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("estado", [Proveedor.ACTIVO, Proveedor.INACTIVO])
def test_CO171_muestra_los_campos_actuales_en_cualquier_estado(client_admin, estado):
    proveedor = ProveedorFactory(razon_social="Editorial Ivrea", estado=estado)
    antes = Proveedor.objects.get(pk=proveedor.pk).actualizado_en

    respuesta = client_admin.get(url_editar(proveedor))

    assert respuesta.status_code == 200
    assert respuesta.context["form"].initial["razon_social"] == "Editorial Ivrea"
    assert Proveedor.objects.get(pk=proveedor.pk).actualizado_en == antes
    assert not auditorias(RegistroAuditoria.MODIFICACION_PROVEEDOR).exists()


# ---------------------------------------------------------------------------
# CO-061 · editarProveedor
# ---------------------------------------------------------------------------


def test_CO061_los_atributos_cambian_y_la_modificacion_queda_con_el_instante(client_admin):
    proveedor = ProveedorFactory(nombre_contacto="Laura")
    antes = proveedor.actualizado_en

    client_admin.post(url_editar(proveedor), datos(proveedor, nombre_contacto="Laura Gómez"))

    proveedor.refresh_from_db()
    assert proveedor.nombre_contacto == "Laura Gómez"
    assert proveedor.actualizado_en > antes


def test_CO061_se_forman_y_rompen_editorial_y_tipo(client_admin):
    vieja, nueva = EditorialFactory(), EditorialFactory()
    proveedor = ProveedorFactory(editorial=vieja, tipo_por_defecto=TipoFactory())

    client_admin.post(
        url_editar(proveedor), datos(proveedor, editorial=nueva.pk, tipo_por_defecto="")
    )

    proveedor.refresh_from_db()
    assert proveedor.editorial == nueva
    assert proveedor.tipo_por_defecto is None


def test_CO061_la_auditoria_guarda_cada_par_anterior_y_nuevo(client_admin, administrador):
    proveedor = ProveedorFactory(nombre_contacto="Laura", telefono="111")

    client_admin.post(
        url_editar(proveedor), datos(proveedor, nombre_contacto="Marta", telefono="222")
    )

    registro = auditorias(RegistroAuditoria.MODIFICACION_PROVEEDOR).get()
    assert registro.actor == administrador
    assert registro.objetivo_pk == proveedor.pk
    for valor in ("Laura", "Marta", "111", "222"):
        assert valor in registro.detalle


def test_CO061_E1_un_obligatorio_vacio_no_procede(client_admin):
    proveedor = ProveedorFactory(razon_social="Editorial Ivrea")

    respuesta = client_admin.post(url_editar(proveedor), datos(proveedor, razon_social=""))

    proveedor.refresh_from_db()
    assert respuesta.status_code == 200
    assert proveedor.razon_social == "Editorial Ivrea"
    assert not auditorias(RegistroAuditoria.MODIFICACION_PROVEEDOR).exists()


@pytest.mark.parametrize(
    "campo, valor",
    [("razon_social", "EDITORIAL PANINI"), ("correo_comercial", "Novedades@Panini.test")],
)
def test_CO061_E2_el_dato_de_otro_proveedor_se_informa_con_enlace(client_admin, campo, valor):
    otro = ProveedorFactory(
        razon_social="Editorial Panini", correo_comercial="novedades@panini.test"
    )
    proveedor = ProveedorFactory(razon_social="Editorial Ivrea")

    respuesta = client_admin.post(
        url_editar(proveedor), datos(proveedor, confirma_cambio_de_correo="on", **{campo: valor})
    )

    proveedor.refresh_from_db()
    assert respuesta.status_code == 200
    assert url_ficha(otro) in respuesta.content.decode()
    assert proveedor.razon_social == "Editorial Ivrea"


# ---------------------------------------------------------------------------
# CO-062 · confirmarCambioDeCorreoComercial
# ---------------------------------------------------------------------------


def test_CO062_confirmado_el_correo_anterior_deja_de_ser_remitente_y_el_nuevo_pasa_a_serlo(
    client_admin, administrador
):
    proveedor = ProveedorFactory(correo_comercial="viejo@ivrea.test")

    client_admin.post(
        url_editar(proveedor),
        datos(proveedor, correo_comercial="nuevo@ivrea.test", confirma_cambio_de_correo="on"),
    )

    proveedor.refresh_from_db()
    assert proveedor.correo_comercial == "nuevo@ivrea.test"
    assert remitente("viejo@ivrea.test") is None
    assert remitente("nuevo@ivrea.test") == proveedor
    detalle = auditorias(RegistroAuditoria.MODIFICACION_PROVEEDOR).get().detalle
    assert "viejo@ivrea.test" in detalle
    assert "nuevo@ivrea.test" in detalle


def test_CO062_sin_la_advertencia_confirmada_el_correo_no_cambia(client_admin):
    proveedor = ProveedorFactory(correo_comercial="viejo@ivrea.test")

    client_admin.post(url_editar(proveedor), datos(proveedor, correo_comercial="nuevo@ivrea.test"))

    assert remitente("viejo@ivrea.test") == proveedor
    assert remitente("nuevo@ivrea.test") is None


# ---------------------------------------------------------------------------
# CO-063 · solicitarBajaDeProveedor
# ---------------------------------------------------------------------------


def test_CO063_el_informe_trae_productos_propuestas_y_reversibilidad(client_admin):
    proveedor = ProveedorFactory()
    producto = ProductoFactory(proveedor=proveedor, stock=0, estado=Producto.AGOTADO)
    ProductoFactory(proveedor=proveedor)
    en_propuesta(producto)

    respuesta = client_admin.get(url_baja(proveedor))

    impacto = respuesta.context["impacto"]
    assert impacto.productos_vinculados == 2
    assert impacto.propuestas_de_restock == 1
    assert "Se puede reactivar." in respuesta.content.decode()


def test_CO063_pedir_el_informe_no_modifica_nada(client_admin):
    proveedor = ProveedorFactory(correo_comercial="novedades@ivrea.test")

    client_admin.get(url_baja(proveedor))

    proveedor.refresh_from_db()
    assert proveedor.estado == Proveedor.ACTIVO
    assert remitente("novedades@ivrea.test") == proveedor
    assert not auditorias(RegistroAuditoria.BAJA_PROVEEDOR).exists()


# ---------------------------------------------------------------------------
# CO-064 · confirmarBajaDeProveedor
# ---------------------------------------------------------------------------


def test_CO064_pasa_a_inactivo_y_el_correo_deja_de_ser_remitente(client_admin):
    proveedor = ProveedorFactory(correo_comercial="novedades@ivrea.test")

    client_admin.post(url_baja(proveedor))

    proveedor.refresh_from_db()
    assert proveedor.estado == Proveedor.INACTIVO
    assert remitente("novedades@ivrea.test") is None


def test_CO064_los_productos_conservan_su_proveedor(client_admin):
    """Postcondición negativa explícita: el historial no se toca."""
    proveedor = ProveedorFactory()
    producto = ProductoFactory(proveedor=proveedor)

    client_admin.post(url_baja(proveedor))

    producto.refresh_from_db()
    assert producto.proveedor_id == proveedor.pk


def test_CO064_la_propuesta_activa_marca_proveedor_inactivo(client_admin):
    proveedor = ProveedorFactory(razon_social="Editorial Ivrea")
    producto = ProductoFactory(proveedor=proveedor, stock=0, estado=Producto.AGOTADO)
    en_propuesta(producto)
    sin_baja = client_admin.get(reverse("restock:propuesta")).content.decode()

    client_admin.post(url_baja(proveedor))

    con_baja = client_admin.get(reverse("restock:propuesta")).content.decode()
    assert "Proveedor inactivo" not in sin_baja
    assert "Proveedor inactivo" in con_baja


def test_CO064_el_habitual_de_la_editorial_tambien_marca_la_linea(client_admin):
    """Sin proveedor propio, la línea involucraba al habitual de su editorial."""
    editorial = EditorialFactory()
    proveedor = ProveedorFactory(editorial=editorial)
    producto = ProductoFactory(editorial=editorial, stock=0, estado=Producto.AGOTADO)
    en_propuesta(producto)

    client_admin.post(url_baja(proveedor))

    assert "Proveedor inactivo" in client_admin.get(reverse("restock:propuesta")).content.decode()


def test_CO064_queda_auditada(client_admin, administrador):
    proveedor = ProveedorFactory()

    client_admin.post(url_baja(proveedor))

    registro = auditorias(RegistroAuditoria.BAJA_PROVEEDOR).get()
    assert registro.actor == administrador
    assert registro.objetivo_pk == proveedor.pk


# ---------------------------------------------------------------------------
# CO-065 · solicitarReactivacionDeProveedor
# ---------------------------------------------------------------------------


def test_CO065_presenta_los_datos_vigentes_con_el_correo_destacado(client_admin):
    proveedor = ProveedorFactory(
        razon_social="Editorial Ivrea",
        correo_comercial="novedades@ivrea.test",
        estado=Proveedor.INACTIVO,
    )

    respuesta = client_admin.get(url_reactivar(proveedor))

    contenido = respuesta.content.decode()
    assert respuesta.context["form"].initial["correo_comercial"] == "novedades@ivrea.test"
    assert respuesta.context["form"].initial["razon_social"] == "Editorial Ivrea"
    assert "data-correo-destacado" in contenido


def test_CO065_no_modifica_nada(client_admin):
    proveedor = ProveedorFactory(estado=Proveedor.INACTIVO)

    client_admin.get(url_reactivar(proveedor))

    proveedor.refresh_from_db()
    assert proveedor.estado == Proveedor.INACTIVO
    assert not auditorias(RegistroAuditoria.REACTIVACION_PROVEEDOR).exists()


# ---------------------------------------------------------------------------
# CO-066 · confirmarReactivacionDeProveedor
# ---------------------------------------------------------------------------


def test_CO066_pasa_a_activo_con_las_correcciones_y_vuelve_al_filtro(client_admin):
    proveedor = ProveedorFactory(correo_comercial="viejo@ivrea.test", estado=Proveedor.INACTIVO)

    client_admin.post(
        url_reactivar(proveedor),
        datos(
            proveedor,
            razon_social="Ivrea Argentina",
            correo_comercial="nuevo@ivrea.test",
            nombre_contacto="Marta",
        ),
    )

    proveedor.refresh_from_db()
    assert proveedor.estado == Proveedor.ACTIVO
    assert proveedor.razon_social == "Ivrea Argentina"
    assert proveedor.correo_comercial == "nuevo@ivrea.test"
    assert proveedor.nombre_contacto == "Marta"
    assert remitente("nuevo@ivrea.test") == proveedor
    assert remitente("viejo@ivrea.test") is None


@pytest.mark.parametrize("prendido", [True, False])
def test_CO066_el_procesamiento_queda_con_el_valor_declarado(client_admin, prendido):
    proveedor = ProveedorFactory(
        correo_comercial="novedades@ivrea.test",
        estado=Proveedor.INACTIVO,
        procesa_novedades=not prendido,
    )
    formulario = datos(proveedor)
    formulario.pop("procesa_novedades", None)
    if prendido:
        formulario["procesa_novedades"] = "on"

    client_admin.post(url_reactivar(proveedor), formulario)

    proveedor.refresh_from_db()
    assert proveedor.procesa_novedades is prendido
    assert (remitente("novedades@ivrea.test") == proveedor) is prendido


def test_CO066_los_productos_conservan_su_proveedor(client_admin):
    proveedor = ProveedorFactory(estado=Proveedor.INACTIVO)
    producto = ProductoFactory(proveedor=proveedor)

    client_admin.post(url_reactivar(proveedor), datos(proveedor))

    producto.refresh_from_db()
    assert producto.proveedor_id == proveedor.pk


def test_CO066_queda_auditada_con_las_correcciones(client_admin, administrador):
    proveedor = ProveedorFactory(nombre_contacto="Laura", estado=Proveedor.INACTIVO)

    client_admin.post(url_reactivar(proveedor), datos(proveedor, nombre_contacto="Marta"))

    registro = auditorias(RegistroAuditoria.REACTIVACION_PROVEEDOR).get()
    assert registro.actor == administrador
    assert "Inactivo" in registro.detalle
    assert "Activo" in registro.detalle
    assert "Laura" in registro.detalle
    assert "Marta" in registro.detalle


def test_CO066_la_reactivacion_limpia_la_marca_de_la_propuesta(client_admin):
    proveedor = ProveedorFactory()
    producto = ProductoFactory(proveedor=proveedor, stock=0, estado=Producto.AGOTADO)
    en_propuesta(producto)
    client_admin.post(url_baja(proveedor))
    proveedor.refresh_from_db()

    client_admin.post(url_reactivar(proveedor), datos(proveedor))

    assert (
        "Proveedor inactivo" not in client_admin.get(reverse("restock:propuesta")).content.decode()
    )


@pytest.mark.parametrize(
    "campo, valor",
    [("razon_social", "Editorial Panini"), ("correo_comercial", "NOVEDADES@panini.test")],
)
def test_CO066_E1_la_colision_se_informa_con_enlace_y_no_reactiva(client_admin, campo, valor):
    otro = ProveedorFactory(
        razon_social="Editorial Panini", correo_comercial="novedades@panini.test"
    )
    proveedor = ProveedorFactory(estado=Proveedor.INACTIVO)

    respuesta = client_admin.post(url_reactivar(proveedor), datos(proveedor, **{campo: valor}))

    proveedor.refresh_from_db()
    assert respuesta.status_code == 200
    assert proveedor.estado == Proveedor.INACTIVO
    assert url_ficha(otro) in respuesta.content.decode()
    assert not auditorias(RegistroAuditoria.REACTIVACION_PROVEEDOR).exists()


def test_CO066_E2_un_correo_mal_formado_se_rechaza(client_admin):
    proveedor = ProveedorFactory(correo_comercial="novedades@ivrea.test", estado=Proveedor.INACTIVO)

    client_admin.post(url_reactivar(proveedor), datos(proveedor, correo_comercial="novedades@"))

    proveedor.refresh_from_db()
    assert proveedor.estado == Proveedor.INACTIVO
    assert proveedor.correo_comercial == "novedades@ivrea.test"


def test_CO066_el_doble_envio_no_registra_dos_reactivaciones(client_admin):
    proveedor = ProveedorFactory(estado=Proveedor.INACTIVO)
    formulario = datos(proveedor)

    client_admin.post(url_reactivar(proveedor), formulario)
    client_admin.post(url_reactivar(proveedor), formulario)

    assert auditorias(RegistroAuditoria.REACTIVACION_PROVEEDOR).count() == 1


# ---------------------------------------------------------------------------
# CO-172 · consultarProveedores
# ---------------------------------------------------------------------------


def test_CO172_lista_razon_social_correo_estado_y_productos(client_admin):
    proveedor = ProveedorFactory(razon_social="Editorial Ivrea", correo_comercial="n@ivrea.test")
    ProductoFactory(proveedor=proveedor)
    ProductoFactory(proveedor=proveedor)

    respuesta = client_admin.get(URL_LISTA)

    fila = next(p for p in respuesta.context["proveedores"] if p.pk == proveedor.pk)
    assert fila.cantidad_productos == 2
    contenido = respuesta.content.decode()
    for dato in ("Editorial Ivrea", "n@ivrea.test", "Activo"):
        assert dato in contenido


def test_CO172_filtra_por_estado_y_por_texto(client_admin):
    ProveedorFactory(razon_social="Editorial Ivrea")
    inactivo = ProveedorFactory(razon_social="Editorial Panini", estado=Proveedor.INACTIVO)

    por_estado = client_admin.get(URL_LISTA, {"estado": Proveedor.INACTIVO}).context["proveedores"]
    por_texto = client_admin.get(URL_LISTA, {"q": "panini"}).context["proveedores"]

    assert [p.pk for p in por_estado] == [inactivo.pk]
    assert [p.pk for p in por_texto] == [inactivo.pk]


def test_CO172_E1_sin_resultados(client_admin):
    ProveedorFactory(razon_social="Editorial Ivrea")

    contenido = client_admin.get(URL_LISTA, {"q": "zzz"}).content.decode()

    assert "Ningún proveedor coincide" in contenido


def test_CO172_E2_sin_proveedores_ofrece_el_alta(client_admin):
    respuesta = client_admin.get(URL_LISTA)

    assert not respuesta.context["proveedores"]
    assert reverse("suppliers:proveedor_alta") in respuesta.content.decode()


def test_CO172_por_la_direccion_real_con_rol_cajero_se_deniega(client):
    client.force_login(UsuarioFactory(rol="cajero"))

    assert client.get(URL_LISTA).status_code == 403


# ---------------------------------------------------------------------------
# CO-173 · consultarFichaDeProveedor
# ---------------------------------------------------------------------------


def test_CO173_contacto_productos_y_procesamiento_a_la_vista(client_admin):
    proveedor = ProveedorFactory(nombre_contacto="Laura Gómez", procesa_novedades=False)
    producto = ProductoFactory(proveedor=proveedor, titulo="Berserk")

    respuesta = client_admin.get(url_ficha(proveedor))

    contenido = respuesta.content.decode()
    assert "Laura Gómez" in contenido
    assert "Berserk" in contenido
    assert producto.pk in [p.pk for p in respuesta.context["productos"]]
    assert "No se reconoce como remitente" in contenido


def test_CO173_el_historial_trae_los_pedidos_despachados(client_admin, administrador):
    proveedor = ProveedorFactory()
    pedidos.enviar_y_registrar(
        proveedor,
        [pedidos.LineaDePedido(titulo="Berserk", volumen=1, isbn="", cantidad=3)],
        administrador,
    )

    respuesta = client_admin.get(url_ficha(proveedor))

    assert len(respuesta.context["pedidos"]) == 1
    assert "3 unidad(es)" in respuesta.content.decode()


def test_CO173_el_historial_no_mezcla_pedidos_de_otro_proveedor(client_admin, administrador):
    proveedor, otro = ProveedorFactory(), ProveedorFactory()
    pedidos.enviar_y_registrar(
        otro, [pedidos.LineaDePedido(titulo="Berserk", volumen=1, isbn="", cantidad=3)]
    )

    assert not client_admin.get(url_ficha(proveedor)).context["pedidos"]


def test_CO173_consultar_la_ficha_no_modifica_nada(client_admin):
    proveedor = ProveedorFactory()
    antes = proveedor.actualizado_en

    client_admin.get(url_ficha(proveedor))

    proveedor.refresh_from_db()
    assert proveedor.actualizado_en == antes


# ---------------------------------------------------------------------------
# Control de acceso de las operaciones que modifican
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("rol", ["cajero", "cliente"])
def test_CO061_CO064_CO066_otro_rol_no_modifica_el_padron(client, rol):
    client.force_login(UsuarioFactory(rol=rol))
    activo = ProveedorFactory(nombre_contacto="Laura")
    inactivo = ProveedorFactory(estado=Proveedor.INACTIVO)

    client.post(url_editar(activo), datos(activo, nombre_contacto="Marta"))
    client.post(url_baja(activo))
    client.post(url_reactivar(inactivo), datos(inactivo))

    activo.refresh_from_db()
    inactivo.refresh_from_db()
    assert activo.nombre_contacto == "Laura"
    assert activo.estado == Proveedor.ACTIVO
    assert inactivo.estado == Proveedor.INACTIVO
