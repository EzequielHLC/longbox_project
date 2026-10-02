"""Pruebas de contrato del módulo 02 · Catálogo.

Se escriben desde el contrato, según `docs/pruebas/ESPECIFICACION.md` apartado 3.

Por ahora cubre `CO-156 cancelarOperacion` en la baja y en la reactivación de
producto (CU-CAT-BAJ A1, CU-CAT-REA A1). La reactivación sumó la operación a su
DSS el 2026-09-30; el contrato ya la referenciaba.
"""

import csv
import io
import re

import pytest
from django.urls import reverse

from apps.catalog.forms import etiquetas_activas
from apps.catalog.models import Etiqueta, GrupoEtiqueta, Producto
from apps.catalog.tests.factories import (
    EditorialFactory,
    GrupoEtiquetaFactory,
    ProductoFactory,
    TipoFactory,
)
from apps.core.models import RegistroAuditoria

pytestmark = pytest.mark.django_db


def _foto(producto):
    producto.refresh_from_db()
    return (producto.estado, producto.precio, producto.stock, producto.titulo)


@pytest.mark.parametrize(
    ("ruta", "estado_inicial"),
    [
        ("catalog:producto_baja", Producto.ACTIVO),
        ("catalog:producto_reactivar", Producto.DESCATALOGADO),
    ],
)
def test_CO156_abandonar_la_confirmacion_no_cambia_el_producto(client_admin, ruta, estado_inicial):
    """Postcondición: «ninguna. El objeto conserva todos sus atributos,
    asociaciones y estado. No se genera entrada de auditoría»."""
    producto = ProductoFactory(estado=estado_inicial, stock=3)
    antes = _foto(producto)
    registros = RegistroAuditoria.objects.count()

    # Abrir la confirmación y no confirmar es exactamente abandonar la operación.
    assert client_admin.get(reverse(ruta, args=[producto.pk])).status_code == 200

    assert _foto(producto) == antes
    assert RegistroAuditoria.objects.count() == registros


# ===========================================================================
# Grupos de etiquetas — CU-CAT-GRC, GRA, GRM, GRB
# ===========================================================================


def _etiqueta(nombre, grupo, **extra):
    return Etiqueta.objects.create(nombre=nombre, grupo=grupo, **extra)


def test_CO038_registrar_grupo_lo_crea_activo_y_auditado(client_admin, administrador):
    client_admin.post(reverse("catalog:grupo_etiqueta_crear"), {"nombre": "  Edición  especial "})

    grupo = GrupoEtiqueta.objects.get(nombre="Edición especial")
    assert grupo.activo is True
    registro = RegistroAuditoria.objects.get(accion=RegistroAuditoria.ALTA_CATALOGO)
    assert (registro.actor, registro.objetivo) == (administrador, grupo)


def test_CO038_E1_la_colision_enlaza_el_grupo_existente(client_admin):
    existente = GrupoEtiquetaFactory(nombre="Colección de prueba", activo=False)

    respuesta = client_admin.post(
        reverse("catalog:grupo_etiqueta_crear"), {"nombre": "colección de prueba"}
    )

    url = reverse("catalog:grupo_etiqueta_editar", args=[existente.pk])
    assert url in respuesta.content.decode()
    assert GrupoEtiqueta.objects.filter(nombre__iexact="colección de prueba").count() == 1


def test_CO039_reactivar_el_grupo_no_reactiva_sus_etiquetas(client_admin):
    """E9: el sistema no distingue las que bajó el grupo de las que ya estaban."""
    grupo = GrupoEtiquetaFactory(nombre="Apagado", activo=False)
    etiqueta = _etiqueta("Dormida", grupo, activa=False)

    client_admin.post(
        reverse("catalog:grupo_etiqueta_editar", args=[grupo.pk]),
        {"nombre": "Apagado", "reactivar": "on"},
    )

    grupo.refresh_from_db()
    etiqueta.refresh_from_db()
    assert grupo.activo is True
    assert etiqueta.activa is False
    registro = RegistroAuditoria.objects.get(accion=RegistroAuditoria.MODIFICACION_CATALOGO)
    assert "activo: no → sí" in registro.detalle


def test_CO040_solicitar_baja_de_grupo_informa_etiquetas_y_productos(client_admin):
    grupo = GrupoEtiquetaFactory(nombre="Género de prueba")
    shonen, seinen = _etiqueta("Shonen", grupo), _etiqueta("Seinen", grupo)
    ProductoFactory().etiquetas.add(shonen, seinen)
    ProductoFactory().etiquetas.add(shonen)
    registros = RegistroAuditoria.objects.count()

    respuesta = client_admin.get(reverse("catalog:grupo_etiqueta_baja", args=[grupo.pk]))

    informe = {r.etiqueta: r.cantidad for r in respuesta.context["informe"]}
    assert informe == {"Etiquetas": 2, "Productos con alguna de sus etiquetas": 2}
    assert RegistroAuditoria.objects.count() == registros


def test_CO041_la_baja_del_grupo_alcanza_a_sus_etiquetas_y_conserva_las_asignaciones(
    client_admin, administrador
):
    grupo = GrupoEtiquetaFactory(nombre="Género de prueba")
    etiquetas = [_etiqueta(f"Valor {n}", grupo) for n in range(3)]
    producto = ProductoFactory()
    producto.etiquetas.add(*etiquetas)

    client_admin.post(reverse("catalog:grupo_etiqueta_baja", args=[grupo.pk]))

    grupo.refresh_from_db()
    assert grupo.activo is False
    assert not Etiqueta.objects.filter(grupo=grupo, activa=True).exists()
    assert set(producto.etiquetas.all()) == set(etiquetas)
    assert not etiquetas_activas().filter(grupo=grupo).exists()
    registro = RegistroAuditoria.objects.get(accion=RegistroAuditoria.BAJA_CATALOGO)
    assert registro.actor == administrador


@pytest.mark.parametrize("ruta", ["catalog:grupo_etiqueta_baja", "catalog:etiqueta_baja"])
def test_CO156_abandonar_la_baja_de_grupo_o_etiqueta_no_cambia_nada(client_admin, ruta):
    """CU-CAT-GRB A1 y CU-CAT-ETB A1."""
    grupo = GrupoEtiquetaFactory(nombre="Intacto")
    etiqueta = _etiqueta("Intacta", grupo)
    objeto = grupo if "grupo" in ruta else etiqueta
    registros = RegistroAuditoria.objects.count()

    assert client_admin.get(reverse(ruta, args=[objeto.pk])).status_code == 200

    grupo.refresh_from_db()
    etiqueta.refresh_from_db()
    assert grupo.activo and etiqueta.activa
    assert RegistroAuditoria.objects.count() == registros


def test_CO164_consultar_grupos_lista_activos_e_inactivos_con_sus_etiquetas(client_admin):
    vivo = GrupoEtiquetaFactory(nombre="Vivo")
    _etiqueta("Una", vivo)
    _etiqueta("Otra", vivo)
    GrupoEtiquetaFactory(nombre="Apagado", activo=False)

    respuesta = client_admin.get(reverse("catalog:etiquetas"))
    inactivos = client_admin.get(reverse("catalog:etiquetas") + "?estado=inactivos")

    por_nombre = {g.nombre: g for g in respuesta.context["registros"]}
    assert por_nombre["Vivo"].cantidad_etiquetas == 2
    assert "Apagado" in por_nombre
    assert [g.nombre for g in inactivos.context["registros"]] == ["Apagado"]


# ===========================================================================
# Etiquetas — CU-CAT-ETC, ETA, ETM, ETB
# ===========================================================================


def test_CO042_registrar_etiqueta_la_crea_activa_en_su_grupo(client_admin, administrador):
    grupo = GrupoEtiquetaFactory(nombre="Género de prueba")

    client_admin.post(reverse("catalog:etiqueta_crear"), {"nombre": " Shonen ", "grupo": grupo.pk})

    etiqueta = Etiqueta.objects.get(nombre="Shonen", grupo=grupo)
    assert etiqueta.activa is True
    registro = RegistroAuditoria.objects.get(accion=RegistroAuditoria.ALTA_CATALOGO)
    assert registro.actor == administrador
    assert "grupo: «Género de prueba»" in registro.detalle


def test_CO042_E1_la_colision_es_dentro_del_grupo_y_enlaza_la_existente(client_admin):
    grupo = GrupoEtiquetaFactory(nombre="Género de prueba")
    existente = _etiqueta("Terror", grupo, activa=False)

    respuesta = client_admin.post(
        reverse("catalog:etiqueta_crear"), {"nombre": "TERROR", "grupo": grupo.pk}
    )

    url = reverse("catalog:etiqueta_editar", args=[existente.pk])
    assert url in respuesta.content.decode()
    assert Etiqueta.objects.filter(grupo=grupo).count() == 1


def test_CO042_no_se_crea_en_un_grupo_dado_de_baja(client_admin):
    """Precondición: el grupo existe en estado activo."""
    grupo = GrupoEtiquetaFactory(nombre="Apagado", activo=False)

    respuesta = client_admin.post(
        reverse("catalog:etiqueta_crear"), {"nombre": "Nueva", "grupo": grupo.pk}
    )

    assert respuesta.context["form"].errors["grupo"]
    assert not Etiqueta.objects.filter(grupo=grupo).exists()


def test_CO043_mover_la_etiqueta_conserva_sus_asignaciones_y_su_estado(client_admin):
    origen = GrupoEtiquetaFactory(nombre="Origen")
    destino = GrupoEtiquetaFactory(nombre="Destino")
    etiqueta = _etiqueta("Movible", origen)
    producto = ProductoFactory()
    producto.etiquetas.add(etiqueta)

    client_admin.post(
        reverse("catalog:etiqueta_editar", args=[etiqueta.pk]),
        {"nombre": "Movible", "grupo": destino.pk},
    )

    etiqueta.refresh_from_db()
    assert etiqueta.grupo == destino
    assert etiqueta.activa is True
    assert etiqueta in producto.etiquetas.all()
    registro = RegistroAuditoria.objects.get(accion=RegistroAuditoria.MODIFICACION_CATALOGO)
    assert "grupo: «Origen» → «Destino»" in registro.detalle


def test_CO043_E3_no_se_reactiva_dentro_de_un_grupo_dado_de_baja(client_admin):
    grupo = GrupoEtiquetaFactory(nombre="Apagado", activo=False)
    etiqueta = _etiqueta("Dormida", grupo, activa=False)

    respuesta = client_admin.post(
        reverse("catalog:etiqueta_editar", args=[etiqueta.pk]),
        {"nombre": "Dormida", "grupo": grupo.pk, "reactivar": "on"},
    )

    assert "Reactívelo primero" in respuesta.context["form"].errors["reactivar"][0]
    etiqueta.refresh_from_db()
    assert etiqueta.activa is False


def test_CO043_reactivar_moviendola_a_un_grupo_activo(client_admin):
    apagado = GrupoEtiquetaFactory(nombre="Apagado", activo=False)
    vivo = GrupoEtiquetaFactory(nombre="Vivo")
    etiqueta = _etiqueta("Dormida", apagado, activa=False)

    client_admin.post(
        reverse("catalog:etiqueta_editar", args=[etiqueta.pk]),
        {"nombre": "Dormida", "grupo": vivo.pk, "reactivar": "on"},
    )

    etiqueta.refresh_from_db()
    assert (etiqueta.grupo, etiqueta.activa) == (vivo, True)
    assert etiqueta in etiquetas_activas()


def test_CO044_solicitar_baja_de_etiqueta_informa_sus_productos(client_admin):
    etiqueta = _etiqueta("Contada", GrupoEtiquetaFactory(nombre="Con uso"))
    for _ in range(2):
        ProductoFactory().etiquetas.add(etiqueta)

    respuesta = client_admin.get(reverse("catalog:etiqueta_baja", args=[etiqueta.pk]))

    informe = [(r.etiqueta, r.cantidad) for r in respuesta.context["informe"]]
    assert informe == [("Productos", 2)]


def test_CO045_confirmar_baja_de_etiqueta_la_retira_y_conserva_sus_asignaciones(
    client_admin, administrador
):
    etiqueta = _etiqueta("Retirada", GrupoEtiquetaFactory(nombre="Con uso"))
    producto = ProductoFactory()
    producto.etiquetas.add(etiqueta)

    client_admin.post(reverse("catalog:etiqueta_baja", args=[etiqueta.pk]))

    etiqueta.refresh_from_db()
    assert etiqueta.activa is False
    assert etiqueta in producto.etiquetas.all()
    assert etiqueta not in etiquetas_activas()
    registro = RegistroAuditoria.objects.get(accion=RegistroAuditoria.BAJA_CATALOGO)
    assert registro.actor == administrador


def test_CO045_la_edicion_del_producto_la_presenta_marcada_y_no_la_pierde(client_admin):
    """«En la edición de un producto que la tiene asignada se presenta marcada y
    puede quitarse (CO-030).» Antes, el desplegable sólo ofrecía las activas y
    guardar cualquier otro cambio la perdía sin que nadie lo decidiera."""
    etiqueta = _etiqueta("Retirada", GrupoEtiquetaFactory(nombre="Con uso"))
    producto = ProductoFactory()
    producto.etiquetas.add(etiqueta)
    client_admin.post(reverse("catalog:etiqueta_baja", args=[etiqueta.pk]))

    respuesta = client_admin.get(reverse("catalog:producto_editar", args=[producto.pk]))

    formulario = respuesta.context["form"]
    assert etiqueta in formulario.fields["etiquetas"].queryset
    select = re.search(
        r'<select name="etiquetas"[^>]*>(.*?)</select>', respuesta.content.decode(), re.S
    )
    assert re.search(rf'value="{etiqueta.pk}"[^>]*selected', select.group(1))


# ===========================================================================
# Inventario — CU-CAT-INV
# ===========================================================================


def _filas_csv(respuesta):
    texto = respuesta.content.decode("utf-8-sig")
    return list(csv.reader(io.StringIO(texto)))


def test_CO037_exportar_inventario_trae_las_filas_del_listado_filtrado(client_admin, administrador):
    tipo = TipoFactory(nombre="Manga")
    elegido = ProductoFactory(titulo="Berserk", tipo=tipo, stock=4)
    ProductoFactory(titulo="Otro tipo", tipo=TipoFactory(nombre="Cómic"))
    ProductoFactory(titulo="Descatalogado", tipo=tipo, estado=Producto.DESCATALOGADO)
    filtros = f"?tipo={tipo.pk}"

    listado = client_admin.get(reverse("catalog:producto_lista") + filtros)
    respuesta = client_admin.get(reverse("catalog:producto_exportar") + filtros)

    filas = _filas_csv(respuesta)
    assert respuesta["Content-Type"].startswith("text/csv")
    assert filas[0][:2] == ["Código", "Título"]
    assert [fila[1] for fila in filas[1:]] == [p.titulo for p in listado.context["productos"]]
    assert [fila[1] for fila in filas[1:]] == ["Berserk"]
    assert filas[1][0] == elegido.codigo
    registro = RegistroAuditoria.objects.get(accion=RegistroAuditoria.EXPORTACION_INVENTARIO)
    assert registro.actor == administrador
    assert f"tipo={tipo.pk}" in registro.detalle
    assert "estado=activo" in registro.detalle


def test_CO037_el_cajero_no_exporta_por_la_direccion_real(client, cajero):
    """La única acción de CU-CAT-INV restringida por rol, validada en el servidor."""
    client.force_login(cajero)
    ProductoFactory()

    respuesta = client.get(reverse("catalog:producto_exportar"))

    assert respuesta.status_code == 403
    assert not RegistroAuditoria.objects.filter(
        accion=RegistroAuditoria.EXPORTACION_INVENTARIO
    ).exists()


def test_CO037_el_cajero_no_ve_la_opcion_de_exportar(client, cajero):
    client.force_login(cajero)
    ProductoFactory()

    contenido = client.get(reverse("catalog:producto_lista")).content.decode()

    assert reverse("catalog:producto_exportar") not in contenido


def test_CO162_consultar_inventario_filtra_por_editorial(client_admin):
    ivrea = EditorialFactory(nombre="Ivrea")
    ProductoFactory(titulo="De Ivrea", editorial=ivrea)
    ProductoFactory(titulo="De otra", editorial=EditorialFactory(nombre="Panini"))

    respuesta = client_admin.get(reverse("catalog:producto_lista") + f"?editorial={ivrea.pk}")

    assert [p.titulo for p in respuesta.context["productos"]] == ["De Ivrea"]


def test_CO162_el_filtro_ofrece_las_etiquetas_inactivas_marcadas(client_admin):
    """Para localizar los productos que las conservan (comentario de la ficha)."""
    etiqueta = _etiqueta("Retirada", GrupoEtiquetaFactory(nombre="Con uso"), activa=False)
    ProductoFactory().etiquetas.add(etiqueta)

    contenido = client_admin.get(reverse("catalog:producto_lista")).content.decode()

    assert "Retirada (inactiva)" in contenido


def test_CO163_la_ficha_dibuja_para_el_cajero_solo_sus_campos(client, cajero):
    """«El Cajero ve nombre, imagen, tipo, estado, stock y precio. La restricción
    se implementa no dibujando el dato»: el resto no viaja en la respuesta."""
    producto = ProductoFactory(titulo="Akira", stock=3)
    client.force_login(cajero)

    contenido = client.get(reverse("catalog:producto_detalle", args=[producto.pk])).content
    contenido = contenido.decode()

    assert "Akira" in contenido
    assert "Información interna" not in contenido
    assert "Historial de modificaciones" not in contenido
    assert reverse("catalog:producto_editar", args=[producto.pk]) not in contenido


def test_CO163_los_indicadores_que_no_puede_calcular_se_declaran_no_disponibles(client_admin):
    producto = ProductoFactory(titulo="Akira")

    contenido = client_admin.get(reverse("catalog:producto_detalle", args=[producto.pk]))

    texto = contenido.content.decode()
    assert "Stock reservado en pedidos" in texto
    assert "No disponible todavía" in texto


def test_CO165_consultar_etiquetas_de_grupo_paginadas_con_busqueda_y_estado(client_admin):
    grupo = GrupoEtiquetaFactory(nombre="Grande", activo=False)
    Etiqueta.objects.bulk_create(
        [Etiqueta(nombre=f"Valor {numero:03}", grupo=grupo) for numero in range(55)]
    )
    _etiqueta("Apagada", grupo, activa=False)
    _etiqueta("Otro grupo", GrupoEtiquetaFactory(nombre="Ajeno"))
    url = reverse("catalog:grupo_etiquetas", args=[grupo.pk])
    registros = RegistroAuditoria.objects.count()

    primera = client_admin.get(url)
    segunda = client_admin.get(url, {"page": 2})
    buscadas = client_admin.get(url, {"q": "valor 05"})
    inactivas = client_admin.get(url, {"estado": "inactivos"})

    assert len(primera.context["registros"]) == 50
    assert len(segunda.context["registros"]) == 6
    assert [e.nombre for e in buscadas.context["registros"]] == [
        f"Valor {n:03}" for n in range(50, 55)
    ]
    assert [e.nombre for e in inactivas.context["registros"]] == ["Apagada"]
    # El estado del grupo se presenta junto con sus etiquetas (un grupo en
    # cualquier estado se puede consultar).
    assert "Dado de baja" in primera.content.decode()
    assert RegistroAuditoria.objects.count() == registros
