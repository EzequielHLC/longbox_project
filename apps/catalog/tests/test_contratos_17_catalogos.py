"""Pruebas de contrato del módulo 17 · catálogos de clasificación.

Se escriben desde el contrato, según `docs/pruebas/ESPECIFICACION.md` apartado 3:
cada prueba lleva el código del contrato y afirma sus postcondiciones, incluidas
las negativas (lo que la operación **no** debe cambiar).

Cubre editoriales (`CU-CFG-EDC`, `EDA`, `EDM`, `EDB`), tipos de material
(`TPC`, `TPA`, `TPM`, `TPB`) y formatos (`FMC`, `FMA`, `FMM`, `FMB`). Todas las
operaciones se ejercen por su dirección real.
"""

from decimal import Decimal

import pytest
from django.urls import reverse

from apps.catalog import revisiones
from apps.catalog.forms import CabeceraLoteForm, editoriales_activas, formatos_para
from apps.catalog.models import (
    EDITORIAL,
    NO_EDITORIAL,
    BorradorProducto,
    Editorial,
    Formato,
    Producto,
    ProductoEditorial,
    TablaPrecioReferencia,
    Tipo,
)
from apps.catalog.tests.factories import (
    EditorialFactory,
    FormatoFactory,
    PrecioReferenciaFactory,
    ProductoFactory,
    TipoFactory,
    formato_solo_para,
)
from apps.core.models import RegistroAuditoria
from apps.suppliers.models import CorreoProveedor
from apps.suppliers.tests.factories import ProveedorFactory

pytestmark = pytest.mark.django_db


def auditorias(accion):
    return RegistroAuditoria.objects.filter(accion=accion)


def borrador_con(*, editorial, tipo, formato=None):
    """Un borrador confirmable que hereda editorial y tipo de su proveedor."""
    proveedor = ProveedorFactory(editorial=editorial, tipo_por_defecto=tipo)
    correo = CorreoProveedor.objects.create(
        proveedor=proveedor,
        message_id=f"<{proveedor.pk}@prueba.test>",
        remitente=proveedor.correo_comercial,
        estado=CorreoProveedor.PROCESADO,
    )
    return BorradorProducto.objects.create(
        correo=correo,
        proveedor=proveedor,
        titulo="Berserk Deluxe",
        volumen=5,
        editorial=editorial,
        tipo=tipo,
        formato=formato,
        precio=Decimal("24900"),
        stock_inicial=1,
        estado_sugerido=Producto.ACTIVO,
    )


# ===========================================================================
# Editoriales
# ===========================================================================


def test_CO137_registrar_editorial_la_crea_activa_normalizada_y_auditada(
    client_admin, administrador
):
    respuesta = client_admin.post(reverse("catalog:editorial_crear"), {"nombre": "  Ovni   Press "})

    editorial = Editorial.objects.get(nombre="Ovni Press")
    assert respuesta.status_code == 302
    assert editorial.activa is True
    registro = auditorias(RegistroAuditoria.ALTA_CATALOGO).get()
    assert registro.actor == administrador
    assert registro.objetivo == editorial
    # Disponible de inmediato en los formularios de alta.
    assert editorial in editoriales_activas()


def test_CO137_E1_la_colision_enlaza_la_existente_con_su_estado_y_no_registra(client_admin):
    existente = EditorialFactory(nombre="Ivrea", activa=False)

    respuesta = client_admin.post(reverse("catalog:editorial_crear"), {"nombre": "IVREA"})

    contenido = respuesta.content.decode()
    assert respuesta.status_code == 200
    assert reverse("catalog:editorial_editar", args=[existente.pk]) in contenido
    assert "inactiva: puede reactivarse" in contenido
    assert Editorial.objects.count() == 1
    assert not auditorias(RegistroAuditoria.ALTA_CATALOGO).exists()


def test_CO137_E2_un_nombre_vacio_tras_normalizar_se_rechaza(client_admin):
    respuesta = client_admin.post(reverse("catalog:editorial_crear"), {"nombre": "    "})

    assert respuesta.context["form"].errors["nombre"]
    assert not Editorial.objects.exists()


def test_CO138_editar_editorial_corrige_el_nombre_y_conserva_sus_asociaciones(client_admin):
    editorial = EditorialFactory(nombre="Ivra")
    producto = ProductoFactory(editorial=editorial)
    proveedor = ProveedorFactory(editorial=editorial)
    fila = PrecioReferenciaFactory(editorial=editorial)

    client_admin.post(reverse("catalog:editorial_editar", args=[editorial.pk]), {"nombre": "Ivrea"})

    editorial.refresh_from_db()
    assert editorial.nombre == "Ivrea"
    for objeto in (producto, proveedor, fila):
        objeto.refresh_from_db()
        assert objeto.editorial_id == editorial.pk
    registro = auditorias(RegistroAuditoria.MODIFICACION_CATALOGO).get()
    assert "nombre: «Ivra» → «Ivrea»" in registro.detalle


def test_CO138_reactivar_la_vuelve_a_ofrecer_en_los_formularios(client_admin):
    editorial = EditorialFactory(nombre="Ivrea", activa=False)

    client_admin.post(
        reverse("catalog:editorial_editar", args=[editorial.pk]),
        {"nombre": "Ivrea", "reactivar": "on"},
    )

    editorial.refresh_from_db()
    assert editorial.activa is True
    assert editorial in CabeceraLoteForm().fields["editorial"].queryset
    assert "activo: no → sí" in auditorias(RegistroAuditoria.MODIFICACION_CATALOGO).get().detalle


def test_CO138_la_modificacion_no_da_de_baja(client_admin):
    """Postcondición negativa: la operación no pasa de activa a inactiva. El
    formulario no tiene el campo, y mandarlo a mano no hace nada."""
    editorial = EditorialFactory(nombre="Ivrea")

    client_admin.post(
        reverse("catalog:editorial_editar", args=[editorial.pk]),
        {"nombre": "Ivrea", "activa": "", "reactivar": ""},
    )

    editorial.refresh_from_db()
    assert editorial.activa is True


def test_CO138_E1_la_colision_no_registra_el_cambio(client_admin):
    EditorialFactory(nombre="Panini")
    editorial = EditorialFactory(nombre="Ivrea")

    client_admin.post(
        reverse("catalog:editorial_editar", args=[editorial.pk]), {"nombre": "panini"}
    )

    editorial.refresh_from_db()
    assert editorial.nombre == "Ivrea"
    assert not auditorias(RegistroAuditoria.MODIFICACION_CATALOGO).exists()


def test_CO139_solicitar_baja_de_editorial_informa_las_tres_cantidades_sin_cambiar_nada(
    client_admin,
):
    editorial = EditorialFactory(nombre="Ivrea")
    ProductoFactory(editorial=editorial)
    ProductoFactory(editorial=editorial)
    PrecioReferenciaFactory(editorial=editorial)
    ProveedorFactory(editorial=editorial)
    registros = RegistroAuditoria.objects.count()

    respuesta = client_admin.get(reverse("catalog:editorial_baja", args=[editorial.pk]))

    informe = {r.etiqueta: r.cantidad for r in respuesta.context["informe"]}
    assert informe == {"Productos": 2, "Filas de la tabla de precios": 1, "Proveedores": 1}
    editorial.refresh_from_db()
    assert editorial.activa is True
    assert RegistroAuditoria.objects.count() == registros


def test_CO139_la_precondicion_exige_que_este_activa(client_admin):
    editorial = EditorialFactory(nombre="Ivrea", activa=False)

    respuesta = client_admin.get(reverse("catalog:editorial_baja", args=[editorial.pk]))

    assert respuesta.status_code == 302


def test_CO140_confirmar_baja_de_editorial_la_desactiva_y_conserva_todo(
    client_admin, administrador
):
    editorial = EditorialFactory(nombre="Ivrea")
    producto = ProductoFactory(editorial=editorial)
    proveedor = ProveedorFactory(editorial=editorial)
    fila = PrecioReferenciaFactory(editorial=editorial)

    client_admin.post(reverse("catalog:editorial_baja", args=[editorial.pk]))

    editorial.refresh_from_db()
    assert editorial.activa is False
    for objeto in (producto, proveedor, fila):
        objeto.refresh_from_db()
        assert objeto.editorial_id == editorial.pk
    registro = auditorias(RegistroAuditoria.BAJA_CATALOGO).get()
    assert registro.actor == administrador
    assert registro.objetivo == editorial
    # Deja de ofrecerse en los formularios.
    assert editorial not in CabeceraLoteForm().fields["editorial"].queryset


def test_CO140_un_borrador_que_la_hereda_registra_un_reparo_y_no_se_confirma(
    client_admin, administrador
):
    editorial = EditorialFactory(nombre="Ivrea")
    borrador = borrador_con(
        editorial=editorial, tipo=TipoFactory(nombre="Manga", usa_formato=False)
    )
    client_admin.post(reverse("catalog:editorial_baja", args=[editorial.pk]))
    borrador.refresh_from_db()

    confirmacion = revisiones.confirmar(borrador, actor=administrador)

    assert any("Ivrea" in reparo for reparo in borrador.catalogos_dados_de_baja)
    assert not confirmacion
    assert confirmacion.motivo == revisiones.CATALOGO_DADO_DE_BAJA
    assert not ProductoEditorial.objects.filter(titulo="Berserk Deluxe").exists()


def test_CO140_reactivarla_destraba_el_borrador(client_admin, administrador):
    editorial = EditorialFactory(nombre="Ivrea", activa=False)
    borrador = borrador_con(
        editorial=editorial, tipo=TipoFactory(nombre="Manga", usa_formato=False)
    )

    client_admin.post(
        reverse("catalog:editorial_editar", args=[editorial.pk]),
        {"nombre": "Ivrea", "reactivar": "on"},
    )
    borrador.refresh_from_db()

    assert revisiones.confirmar(borrador, actor=administrador)


def test_CO140_confirmar_dos_veces_no_deja_dos_bajas(client_admin):
    """La segunda confirmación relee el estado bajo bloqueo y se retira."""
    editorial = EditorialFactory(nombre="Ivrea")
    url = reverse("catalog:editorial_baja", args=[editorial.pk])

    client_admin.post(url)
    client_admin.post(url)

    assert auditorias(RegistroAuditoria.BAJA_CATALOGO).count() == 1


@pytest.mark.parametrize(
    ("ruta", "fabrica", "campo"),
    [
        ("catalog:editorial_baja", lambda: EditorialFactory(nombre="Ivrea"), "activa"),
        ("catalog:tipo_baja", lambda: TipoFactory(nombre="Fanzine"), "activo"),
        ("catalog:formato_baja", lambda: FormatoFactory(nombre="A5"), "activo"),
    ],
    ids=["EDB", "TPB", "FMB"],
)
def test_CO156_abandonar_la_baja_de_un_catalogo_no_cambia_nada(client_admin, ruta, fabrica, campo):
    """CU-CFG-EDB A1, TPB A1, FMB A1: abrir la confirmación y volver."""
    registro = fabrica()
    registros = RegistroAuditoria.objects.count()

    assert client_admin.get(reverse(ruta, args=[registro.pk])).status_code == 200

    registro.refresh_from_db()
    assert getattr(registro, campo) is True
    assert RegistroAuditoria.objects.count() == registros


def test_CO211_consultar_editoriales_lista_activas_e_inactivas_con_sus_productos(client_admin):
    viva = EditorialFactory(nombre="Ivrea")
    EditorialFactory(nombre="Larp", activa=False)
    ProductoFactory(editorial=viva)
    url = reverse("catalog:editorial_lista")

    todas = client_admin.get(url)
    inactivas = client_admin.get(url + "?estado=inactivos").content.decode()

    por_nombre = {e.nombre: e for e in todas.context["registros"]}
    assert por_nombre["Ivrea"].cantidad_productos == 1
    assert "Larp" in por_nombre
    assert "Larp" in inactivas and "Ivrea" not in inactivas


# ===========================================================================
# Tipos de material
# ===========================================================================


def test_CO141_registrar_tipo_con_su_rubro_y_su_clasificacion(client_admin, administrador):
    client_admin.post(
        reverse("catalog:tipo_crear"),
        {"nombre": "Fanzine", "clase": NO_EDITORIAL, "usa_formato": ""},
    )

    tipo = Tipo.objects.get(nombre="Fanzine")
    assert (tipo.clase, tipo.usa_formato, tipo.activo) == (NO_EDITORIAL, False, True)
    registro = auditorias(RegistroAuditoria.ALTA_CATALOGO).get()
    assert registro.actor == administrador
    assert registro.objetivo == tipo


def test_CO142_E2_no_cambia_el_rubro_de_un_tipo_con_productos(client_admin):
    tipo = TipoFactory(nombre="Manga", clase=EDITORIAL)
    ProductoFactory(tipo=tipo)

    respuesta = client_admin.post(
        reverse("catalog:tipo_editar", args=[tipo.pk]),
        {"nombre": "Manga", "clase": NO_EDITORIAL, "usa_formato": "on"},
    )

    tipo.refresh_from_db()
    assert respuesta.context["form"].errors["clase"]
    assert tipo.clase == EDITORIAL


def test_CO142_E4_no_deja_de_clasificarse_por_formato_con_combinaciones_en_uso(client_admin):
    tipo = TipoFactory(nombre="Manga", usa_formato=True)
    ProductoFactory(tipo=tipo, formato=FormatoFactory(nombre="B6"))
    PrecioReferenciaFactory(tipo=tipo)

    respuesta = client_admin.post(
        reverse("catalog:tipo_editar", args=[tipo.pk]),
        {"nombre": "Manga", "clase": EDITORIAL, "usa_formato": ""},
    )

    error = respuesta.context["form"].errors["usa_formato"][0]
    assert "1 productos" in error and "1 filas de precio" in error
    tipo.refresh_from_db()
    assert tipo.usa_formato is True


def test_CO142_dejar_de_clasificarse_por_formato_rompe_sus_combinaciones(client_admin):
    tipo = TipoFactory(nombre="Artbook", usa_formato=True)
    formato = formato_solo_para("Apaisado", tipo)

    client_admin.post(
        reverse("catalog:tipo_editar", args=[tipo.pk]),
        {"nombre": "Artbook", "clase": EDITORIAL, "usa_formato": ""},
    )

    tipo.refresh_from_db()
    assert tipo.usa_formato is False
    assert not formato.tipos.filter(pk=tipo.pk).exists()


def test_CO142_reactivar_el_tipo_lo_vuelve_a_ofrecer(client_admin):
    tipo = TipoFactory(nombre="Fanzine", activo=False)

    client_admin.post(
        reverse("catalog:tipo_editar", args=[tipo.pk]),
        {"nombre": "Fanzine", "clase": EDITORIAL, "usa_formato": "on", "reactivar": "on"},
    )

    tipo.refresh_from_db()
    assert tipo.activo is True
    assert tipo in CabeceraLoteForm().fields["tipo"].queryset


def test_CO146_declarar_formatos_de_tipo_forma_y_rompe_combinaciones(client_admin):
    tipo = TipoFactory(nombre="Manga", usa_formato=True)
    b6 = formato_solo_para("B6", tipo)
    tankobon = formato_solo_para("Tankōbon")

    client_admin.post(
        reverse("catalog:tipo_editar", args=[tipo.pk]),
        {"nombre": "Manga", "clase": EDITORIAL, "usa_formato": "on", "formatos": [tankobon.pk]},
    )

    assert set(tipo.formatos.all()) == {tankobon}
    assert not b6.tipos.exists()
    detalles = auditorias(RegistroAuditoria.MODIFICACION_CATALOGO).values_list("detalle", flat=True)
    assert any("formatos declarados: B6 → Tankōbon" in detalle for detalle in detalles)


def test_CO146_no_ofrece_ni_toca_los_formatos_que_aplican_a_todos(client_admin):
    """T3: un formato universal no se declara tipo por tipo."""
    tipo = TipoFactory(nombre="Manga", usa_formato=True)
    universal = FormatoFactory(nombre="Tapa dura", aplica_a_todos=True)

    respuesta = client_admin.get(reverse("catalog:tipo_editar", args=[tipo.pk]))
    client_admin.post(
        reverse("catalog:tipo_editar", args=[tipo.pk]),
        {"nombre": "Manga", "clase": EDITORIAL, "usa_formato": "on", "formatos": [universal.pk]},
    )

    assert universal not in respuesta.context["form"].fields["formatos"].queryset
    universal.refresh_from_db()
    assert universal.aplica_a_todos is True
    assert not universal.tipos.exists()


def test_CO146_E5_no_se_quita_un_formato_en_uso(client_admin):
    tipo = TipoFactory(nombre="Manga", usa_formato=True)
    b6 = formato_solo_para("B6", tipo)
    ProductoFactory(tipo=tipo, formato=b6)

    respuesta = client_admin.post(
        reverse("catalog:tipo_editar", args=[tipo.pk]),
        {"nombre": "Manga", "clase": EDITORIAL, "usa_formato": "on", "formatos": []},
    )

    assert "«B6» (1 producto)" in respuesta.context["form"].errors["formatos"][0]
    assert b6.tipos.filter(pk=tipo.pk).exists()


def test_CO212_consultar_tipos_con_rubro_formatos_y_productos(client_admin):
    tipo = TipoFactory(nombre="Manga", usa_formato=True)
    formato_solo_para("B6", tipo)
    ProductoFactory(tipo=tipo)
    TipoFactory(nombre="Fanzine", activo=False)

    respuesta = client_admin.get(reverse("catalog:tipo_lista"))

    contenido = respuesta.content.decode()
    manga = next(t for t in respuesta.context["registros"] if t.nombre == "Manga")
    assert manga.cantidad_productos == 1
    assert "B6" in contenido and "Fanzine" in contenido and "Editorial" in contenido


def test_CO220_solicitar_baja_de_tipo_informa_ofertas_como_no_disponible(client_admin):
    """`Oferta` todavía no existe: un cero diría que se verificó que no hay
    ninguna (C-12)."""
    tipo = TipoFactory(nombre="Manga")
    ProductoFactory(tipo=tipo)
    ProveedorFactory(tipo_por_defecto=tipo)

    respuesta = client_admin.get(reverse("catalog:tipo_baja", args=[tipo.pk]))

    informe = {r.etiqueta: r.cantidad for r in respuesta.context["informe"]}
    assert informe["Productos"] == 1
    assert informe["Proveedores"] == 1
    assert informe["Filas de la tabla de precios"] == 0
    assert informe["Ofertas programadas o activas"] is None
    assert "No disponible" in respuesta.content.decode()


def test_CO221_confirmar_baja_de_tipo_conserva_sus_vinculos(client_admin, administrador):
    tipo = TipoFactory(nombre="Manga", usa_formato=True)
    formato = formato_solo_para("B6", tipo)
    producto = ProductoFactory(tipo=tipo, formato=formato)
    fila = PrecioReferenciaFactory(tipo=tipo, formato=formato)
    proveedor = ProveedorFactory(tipo_por_defecto=tipo)

    client_admin.post(reverse("catalog:tipo_baja", args=[tipo.pk]))

    tipo.refresh_from_db()
    assert tipo.activo is False
    producto.refresh_from_db()
    fila.refresh_from_db()
    proveedor.refresh_from_db()
    assert producto.tipo_id == fila.tipo_id == proveedor.tipo_por_defecto_id == tipo.pk
    assert formato.tipos.filter(pk=tipo.pk).exists()
    assert auditorias(RegistroAuditoria.BAJA_CATALOGO).get().actor == administrador


def test_CO221_un_borrador_que_hereda_el_tipo_no_se_confirma(client_admin, administrador):
    tipo = TipoFactory(nombre="Manga", usa_formato=False)
    borrador = borrador_con(editorial=EditorialFactory(nombre="Ivrea"), tipo=tipo)
    client_admin.post(reverse("catalog:tipo_baja", args=[tipo.pk]))
    borrador.refresh_from_db()

    confirmacion = revisiones.confirmar(borrador, actor=administrador)

    assert confirmacion.motivo == revisiones.CATALOGO_DADO_DE_BAJA


# ===========================================================================
# Formatos
# ===========================================================================


def test_CO144_registrar_formato_con_tipos_declarados(client_admin, administrador):
    manga = TipoFactory(nombre="Manga", usa_formato=True)

    client_admin.post(
        reverse("catalog:formato_crear"),
        {
            "nombre": "A6 de prueba",
            "descripcion": "10,5 × 14,8 cm",
            "aplica_a_todos": "false",
            "tipos": [manga.pk],
        },
    )

    formato = Formato.objects.get(nombre="A6 de prueba")
    assert formato.activo is True
    assert formato.aplica_a_todos is False
    assert formato.descripcion == "10,5 × 14,8 cm"
    assert list(formato.tipos.all()) == [manga]
    assert auditorias(RegistroAuditoria.ALTA_CATALOGO).get().actor == administrador


def test_CO144_un_formato_que_aplica_a_todos_no_declara_tipos(client_admin):
    manga = TipoFactory(nombre="Manga", usa_formato=True)

    client_admin.post(
        reverse("catalog:formato_crear"),
        {"nombre": "Tapa dura", "aplica_a_todos": "true", "tipos": [manga.pk]},
    )

    formato = Formato.objects.get(nombre="Tapa dura")
    assert formato.aplica_a_todos is True
    assert not formato.tipos.exists()
    assert formato in formatos_para(manga)


def test_CO145_pasar_a_aplica_a_todos_rompe_los_tipos_declarados(client_admin):
    manga = TipoFactory(nombre="Manga", usa_formato=True)
    formato = formato_solo_para("B6", manga)

    client_admin.post(
        reverse("catalog:formato_editar", args=[formato.pk]),
        {"nombre": "B6", "aplica_a_todos": "true"},
    )

    formato.refresh_from_db()
    assert formato.aplica_a_todos is True
    assert not formato.tipos.exists()
    detalle = auditorias(RegistroAuditoria.MODIFICACION_CATALOGO).get().detalle
    assert "aplica a todos los tipos: no → sí" in detalle
    assert "tipos: Manga → —" in detalle


def test_CO145_E3_no_deja_sin_declarar_un_tipo_en_uso(client_admin):
    manga = TipoFactory(nombre="Manga", usa_formato=True)
    comic = TipoFactory(nombre="Cómic", usa_formato=True)
    formato = FormatoFactory(nombre="Tapa dura", aplica_a_todos=True)
    PrecioReferenciaFactory(tipo=manga, formato=formato)

    respuesta = client_admin.post(
        reverse("catalog:formato_editar", args=[formato.pk]),
        {"nombre": "Tapa dura", "aplica_a_todos": "false", "tipos": [comic.pk]},
    )

    assert "Manga (1 fila de precio)" in respuesta.context["form"].errors["tipos"][0]
    formato.refresh_from_db()
    assert formato.aplica_a_todos is True


def test_CO145_reactivar_el_formato_lo_vuelve_a_ofrecer(client_admin):
    manga = TipoFactory(nombre="Manga", usa_formato=True)
    formato = FormatoFactory(nombre="B6", activo=False, aplica_a_todos=True)

    client_admin.post(
        reverse("catalog:formato_editar", args=[formato.pk]),
        {"nombre": "B6", "aplica_a_todos": "true", "reactivar": "on"},
    )

    formato.refresh_from_db()
    assert formato.activo is True
    assert formato in formatos_para(manga)


def test_CO147_solicitar_baja_de_formato_informa_las_tres_cantidades(client_admin):
    manga = TipoFactory(nombre="Manga", usa_formato=True)
    formato = formato_solo_para("B6", manga)
    ProductoFactory(tipo=manga, formato=formato)
    PrecioReferenciaFactory(tipo=manga, formato=formato)

    respuesta = client_admin.get(reverse("catalog:formato_baja", args=[formato.pk]))

    informe = {r.etiqueta: r.cantidad for r in respuesta.context["informe"]}
    assert informe == {
        "Productos": 1,
        "Filas de la tabla de precios": 1,
        "Tipos declarados": 1,
    }
    formato.refresh_from_db()
    assert formato.activo is True


def test_CO148_confirmar_baja_de_formato_conserva_productos_filas_y_tipos(client_admin):
    manga = TipoFactory(nombre="Manga", usa_formato=True)
    formato = formato_solo_para("B6", manga)
    producto = ProductoFactory(tipo=manga, formato=formato)
    fila = PrecioReferenciaFactory(tipo=manga, formato=formato)

    client_admin.post(reverse("catalog:formato_baja", args=[formato.pk]))

    formato.refresh_from_db()
    assert formato.activo is False
    producto.refresh_from_db()
    assert producto.formato_id == formato.pk
    assert TablaPrecioReferencia.objects.filter(pk=fila.pk, formato=formato).exists()
    assert formato.tipos.filter(pk=manga.pk).exists()
    assert formato not in formatos_para(manga)
    assert auditorias(RegistroAuditoria.BAJA_CATALOGO).count() == 1


def test_CO148_un_borrador_con_el_formato_dado_de_baja_no_se_confirma(client_admin, administrador):
    manga = TipoFactory(nombre="Manga", usa_formato=True)
    formato = FormatoFactory(nombre="B6", aplica_a_todos=True)
    borrador = borrador_con(editorial=EditorialFactory(nombre="Ivrea"), tipo=manga, formato=formato)
    client_admin.post(reverse("catalog:formato_baja", args=[formato.pk]))
    borrador.refresh_from_db()

    confirmacion = revisiones.confirmar(borrador, actor=administrador)

    assert confirmacion.motivo == revisiones.CATALOGO_DADO_DE_BAJA


def test_CO213_consultar_formatos_con_alcance_y_productos(client_admin):
    manga = TipoFactory(nombre="Manga", usa_formato=True)
    b6 = formato_solo_para("B6", manga)
    FormatoFactory(nombre="Tapa dura", aplica_a_todos=True)
    ProductoFactory(tipo=manga, formato=b6)

    respuesta = client_admin.get(reverse("catalog:formato_lista") + "?estado=activos")

    contenido = respuesta.content.decode()
    b6_listado = next(f for f in respuesta.context["registros"] if f.nombre == "B6")
    assert b6_listado.cantidad_productos == 1
    assert "Todos los tipos" in contenido and "Manga" in contenido


# ===========================================================================
# Control de acceso: por la dirección real, con el rol equivocado
# ===========================================================================


@pytest.mark.parametrize(
    ("ruta", "con_pk"),
    [
        ("catalog:editorial_lista", False),
        ("catalog:editorial_crear", False),
        ("catalog:editorial_editar", True),
        ("catalog:editorial_baja", True),
        ("catalog:tipo_lista", False),
        ("catalog:tipo_baja", True),
        ("catalog:formato_lista", False),
        ("catalog:formato_baja", True),
    ],
)
def test_el_cajero_no_opera_los_catalogos(client, cajero, ruta, con_pk):
    client.force_login(cajero)
    editorial = EditorialFactory(nombre="Ivrea")
    tipo = TipoFactory(nombre="Manga")
    formato = FormatoFactory(nombre="B6")
    objeto = {"editorial": editorial, "tipo": tipo, "formato": formato}[
        ruta.split(":")[1].split("_")[0]
    ]
    url = reverse(ruta, args=[objeto.pk]) if con_pk else reverse(ruta)

    assert client.get(url).status_code == 403
    assert client.post(url).status_code == 403
    editorial.refresh_from_db()
    assert editorial.activa is True
