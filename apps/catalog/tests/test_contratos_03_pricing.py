"""Pruebas de contrato del módulo 03 · Pricing.

Se escriben desde el contrato, según `docs/pruebas/ESPECIFICACION.md` apartado 3.
Es una zona de foco reforzado (dinero): se cubren las ramas de error, la
aritmética decimal exacta y las postcondiciones negativas —lo que la operación
**no** debe cambiar—.

La parte de `CO-048` y `CO-053` que llega a las líneas de carrito se prueba en
`apps/tienda/tests/test_contratos_07_carrito.py` (R-03-001). Las ofertas, en
`test_contratos_03_ofertas.py`.
"""

from decimal import Decimal

import pytest
from django.urls import reverse

from apps.catalog import tabla_de_precios
from apps.catalog.models import Producto, ProductoEditorial, TablaPrecioReferencia
from apps.catalog.tests.factories import (
    EditorialFactory,
    FormatoFactory,
    PrecioReferenciaFactory,
    ProductoFactory,
    TipoFactory,
    TipoNoEditorialFactory,
    formato_solo_para,
)
from apps.core.models import ConfiguracionSistema, RegistroAuditoria

pytestmark = pytest.mark.django_db


def auditorias(accion):
    return RegistroAuditoria.objects.filter(accion=accion)


def vinculado(fila, **extra):
    """Un producto nacional atado a la fila, con su precio."""
    datos = {
        "editorial": fila.editorial,
        "tipo": fila.tipo,
        "formato": fila.formato,
        "precio": fila.pvp,
        "precio_base": fila.pvp,
        "precio_referencia": fila,
    }
    datos.update(extra)
    return ProductoFactory(**datos)


def importado(precio_base, margen="0.40", **extra):
    margen = Decimal(margen)
    datos = {
        "origen": ProductoEditorial.IMPORTADO,
        "precio_base": Decimal(precio_base),
        "precio": (Decimal(precio_base) * (1 + margen)).quantize(Decimal("1")),
    }
    datos.update(extra)
    return ProductoFactory(**datos)


def fijar_margen(valor):
    configuracion = ConfiguracionSistema.obtener()
    configuracion.margen_ganancia = Decimal(valor)
    configuracion.save()


# ===========================================================================
# Consulta — CO-166
# ===========================================================================


def test_CO166_consultar_tabla_con_filtros_combinables(client_admin):
    ivrea = EditorialFactory(nombre="Ivrea")
    manga = TipoFactory(nombre="Manga")
    buscada = PrecioReferenciaFactory(editorial=ivrea, tipo=manga)
    PrecioReferenciaFactory(editorial=ivrea)
    PrecioReferenciaFactory(tipo=manga)
    url = reverse("catalog:precio_lista")

    todas = client_admin.get(url)
    filtradas = client_admin.get(url, {"editorial": ivrea.pk, "tipo": manga.pk})
    vacia = client_admin.get(url, {"formato": FormatoFactory(nombre="Sin filas").pk})

    assert len(todas.context["precios"]) == 3
    assert list(filtradas.context["precios"]) == [buscada]
    assert "Ninguna combinación cumple los filtros" in vacia.content.decode()


# ===========================================================================
# Alta — CO-049
# ===========================================================================


def test_CO049_registrar_combinacion_crea_la_fila_y_no_toca_productos(client_admin, administrador):
    ivrea = EditorialFactory(nombre="Ivrea")
    manga = TipoFactory(nombre="Manga", usa_formato=True)
    b6 = formato_solo_para("B6", manga)
    sin_vinculo = ProductoFactory(editorial=ivrea, tipo=manga, formato=b6, precio=Decimal("9000"))

    respuesta = client_admin.post(
        reverse("catalog:precio_crear"),
        {"editorial": ivrea.pk, "tipo": manga.pk, "formato": b6.pk, "pvp": "12500"},
    )

    assert respuesta.status_code == 302
    fila = TablaPrecioReferencia.objects.get(editorial=ivrea, tipo=manga, formato=b6)
    assert fila.pvp == Decimal("12500")
    sin_vinculo.refresh_from_db()
    assert sin_vinculo.precio == Decimal("9000")
    assert sin_vinculo.precio_referencia is None
    registro = auditorias(RegistroAuditoria.ALTA_PRECIO_REFERENCIA).get()
    assert registro.actor == administrador
    assert "$12500.00" in registro.detalle


def test_CO049_E1_la_combinacion_existente_se_enlaza_y_no_se_registra(client_admin):
    fila = PrecioReferenciaFactory()

    respuesta = client_admin.post(
        reverse("catalog:precio_crear"),
        {
            "editorial": fila.editorial.pk,
            "tipo": fila.tipo.pk,
            "formato": fila.formato.pk,
            "pvp": "1",
        },
    )

    assert reverse("catalog:precio_editar", args=[fila.pk]) in respuesta.content.decode()
    assert TablaPrecioReferencia.objects.count() == 1


@pytest.mark.parametrize(
    "caso", ["tipo_no_editorial", "tipo_sin_formato", "formato_no_aplica", "editorial_de_baja"]
)
def test_CO049_E2_una_combinacion_imposible_se_rechaza(client_admin, caso):
    editorial = EditorialFactory(nombre="Ivrea", activa=caso != "editorial_de_baja")
    tipo = {
        "tipo_no_editorial": lambda: TipoNoEditorialFactory(nombre="Figura", usa_formato=True),
        "tipo_sin_formato": lambda: TipoFactory(nombre="Artbook", usa_formato=False),
    }.get(caso, lambda: TipoFactory(nombre="Manga", usa_formato=True))()
    formato = (
        formato_solo_para("Grapa", TipoFactory(nombre="Cómic", usa_formato=True))
        if caso == "formato_no_aplica"
        else FormatoFactory(nombre="Tapa dura", aplica_a_todos=True)
    )

    respuesta = client_admin.post(
        reverse("catalog:precio_crear"),
        {"editorial": editorial.pk, "tipo": tipo.pk, "formato": formato.pk, "pvp": "10000"},
    )

    assert respuesta.status_code == 200
    assert respuesta.context["form"].errors
    assert not TablaPrecioReferencia.objects.exists()


def test_CO049_E3_un_precio_no_mayor_que_cero_se_rechaza(client_admin):
    manga = TipoFactory(nombre="Manga", usa_formato=True)

    respuesta = client_admin.post(
        reverse("catalog:precio_crear"),
        {
            "editorial": EditorialFactory(nombre="Ivrea").pk,
            "tipo": manga.pk,
            "formato": FormatoFactory(nombre="Tapa dura", aplica_a_todos=True).pk,
            "pvp": "0",
        },
    )

    assert respuesta.context["form"].errors["pvp"]
    assert not TablaPrecioReferencia.objects.exists()


# ===========================================================================
# Modificación — CO-047 y CO-048
# ===========================================================================


def test_CO047_solicitar_modificacion_informa_el_alcance_sin_cambiar_nada(client_admin):
    fila = PrecioReferenciaFactory(pvp=Decimal("10000"))
    vinculado(fila)
    vinculado(fila, estado=Producto.DESCATALOGADO)
    vinculado(fila, estado=Producto.CANCELADO_EDITORIAL)
    registros = RegistroAuditoria.objects.count()

    respuesta = client_admin.post(
        reverse("catalog:precio_editar", args=[fila.pk]), {"pvp": "12000"}
    )

    # Cuenta todos los vinculados salvo los cancelados por la editorial.
    assert respuesta.context["informe"] == 2
    fila.refresh_from_db()
    assert fila.pvp == Decimal("10000")
    assert RegistroAuditoria.objects.count() == registros


def test_CO047_sin_vinculados_informa_que_solo_afecta_a_la_tabla(client_admin):
    fila = PrecioReferenciaFactory()

    respuesta = client_admin.post(reverse("catalog:precio_editar", args=[fila.pk]), {"pvp": "500"})

    assert "sólo afecta a la tabla" in respuesta.content.decode()


def test_CO047_E1_un_precio_no_mayor_que_cero_se_rechaza(client_admin):
    fila = PrecioReferenciaFactory(pvp=Decimal("10000"))

    respuesta = client_admin.post(
        reverse("catalog:precio_editar", args=[fila.pk]), {"pvp": "0", "confirmar": "1"}
    )

    assert respuesta.context["form"].errors["pvp"]
    fila.refresh_from_db()
    assert fila.pvp == Decimal("10000")


def test_CO048_confirmar_propaga_a_los_vinculados_y_respeta_las_excepciones(
    client_admin, administrador
):
    fila = PrecioReferenciaFactory(pvp=Decimal("10000"))
    activo = vinculado(fila)
    descatalogado = vinculado(fila, estado=Producto.DESCATALOGADO)
    cancelado = vinculado(fila, estado=Producto.CANCELADO_EDITORIAL)
    a_mano = vinculado(fila, precio=Decimal("9500"), precio_manual=True, precio_referencia=None)

    client_admin.post(
        reverse("catalog:precio_editar", args=[fila.pk]), {"pvp": "12000", "confirmar": "1"}
    )

    fila.refresh_from_db()
    assert fila.pvp == Decimal("12000")
    for producto, esperado in (
        (activo, "12000"),
        (descatalogado, "12000"),
        (cancelado, "10000"),
        (a_mano, "9500"),
    ):
        producto.refresh_from_db()
        assert producto.precio == Decimal(esperado), producto.estado
    registro = auditorias(RegistroAuditoria.MODIFICACION_PRECIO_REFERENCIA).get()
    assert registro.actor == administrador
    assert "$10000.00 → $12000.00" in registro.detalle
    assert "2 productos actualizados" in registro.detalle


def test_CO048_el_informe_cuenta_lo_mismo_que_se_propaga(client_admin):
    fila = PrecioReferenciaFactory(pvp=Decimal("10000"))
    for estado in (Producto.ACTIVO, Producto.PRE_VENTA, Producto.CANCELADO_EDITORIAL):
        vinculado(fila, estado=estado)

    informado = tabla_de_precios.solicitar_modificacion(fila)
    resumen = tabla_de_precios.confirmar_modificacion(fila, Decimal("11000"), actor=None)

    assert informado == resumen.actualizados == 2


def test_CO048_no_toca_el_precio_base(client_admin):
    """Postcondición negativa: sólo cambia `Producto.precio`."""
    fila = PrecioReferenciaFactory(pvp=Decimal("10000"))
    producto = vinculado(fila, precio_base=Decimal("10000"))

    client_admin.post(
        reverse("catalog:precio_editar", args=[fila.pk]), {"pvp": "12000", "confirmar": "1"}
    )

    producto.refresh_from_db()
    assert producto.precio_base == Decimal("10000")


def test_CO156_abandonar_la_modificacion_no_cambia_el_precio(client_admin):
    """CU-PVP-TBM A1: ver el informe y volver."""
    fila = PrecioReferenciaFactory(pvp=Decimal("10000"))
    producto = vinculado(fila)
    registros = RegistroAuditoria.objects.count()

    client_admin.post(reverse("catalog:precio_editar", args=[fila.pk]), {"pvp": "12000"})

    fila.refresh_from_db()
    producto.refresh_from_db()
    assert fila.pvp == producto.precio == Decimal("10000")
    assert RegistroAuditoria.objects.count() == registros


# ===========================================================================
# Baja — CO-050 y CO-051
# ===========================================================================


def test_CO050_solicitar_baja_cuenta_todos_los_vinculados(client_admin):
    fila = PrecioReferenciaFactory()
    vinculado(fila)
    vinculado(fila, estado=Producto.CANCELADO_EDITORIAL)

    respuesta = client_admin.get(reverse("catalog:precio_eliminar", args=[fila.pk]))

    assert respuesta.context["vinculados"] == 2
    assert TablaPrecioReferencia.objects.filter(pk=fila.pk).exists()


def test_CO051_confirmar_baja_desvincula_y_conserva_precio_y_marca(client_admin, administrador):
    fila = PrecioReferenciaFactory(pvp=Decimal("10000"))
    producto = vinculado(fila)
    combinacion = tabla_de_precios.combinacion(fila)

    client_admin.post(reverse("catalog:precio_eliminar", args=[fila.pk]))

    assert not TablaPrecioReferencia.objects.filter(pk=fila.pk).exists()
    producto.refresh_from_db()
    assert producto.precio_referencia is None
    assert producto.precio == Decimal("10000")
    assert producto.precio_manual is False
    registro = auditorias(RegistroAuditoria.BAJA_PRECIO_REFERENCIA).get()
    assert registro.actor == administrador
    assert combinacion in registro.detalle
    assert "último valor $10000.00" in registro.detalle


def test_CO156_abandonar_la_baja_de_una_combinacion_no_cambia_nada(client_admin):
    """CU-PVP-TBB A1."""
    fila = PrecioReferenciaFactory()
    producto = vinculado(fila)

    client_admin.get(reverse("catalog:precio_eliminar", args=[fila.pk]))

    producto.refresh_from_db()
    assert producto.precio_referencia_id == fila.pk
    assert not auditorias(RegistroAuditoria.BAJA_PRECIO_REFERENCIA).exists()


# ===========================================================================
# Restaurar el precio calculado — CO-031
# ===========================================================================


def test_CO031_un_nacional_a_mano_vuelve_a_la_tabla_y_se_vincula(client_admin, administrador):
    fila = PrecioReferenciaFactory(pvp=Decimal("12000"))
    producto = vinculado(fila, precio=Decimal("9999"), precio_manual=True, precio_referencia=None)

    vista_previa = client_admin.get(
        reverse("catalog:producto_restaurar_precio", args=[producto.pk])
    )
    client_admin.post(reverse("catalog:producto_restaurar_precio", args=[producto.pk]))

    assert vista_previa.context["restauracion"].precio_recalculado == Decimal("12000")
    producto.refresh_from_db()
    assert (producto.precio, producto.precio_manual) == (Decimal("12000"), False)
    assert producto.precio_referencia == fila
    registro = auditorias(RegistroAuditoria.MODIFICACION_PRODUCTO).get()
    assert registro.actor == administrador
    assert "$9999.00 → $12000.00" in registro.detalle


def test_CO031_un_nacional_que_perdio_su_fila_se_vuelve_a_vincular(client_admin):
    """El caso que `CO-051` promete: «pueden vincularse otra vez»."""
    fila = PrecioReferenciaFactory(pvp=Decimal("10000"))
    producto = vinculado(fila)
    client_admin.post(reverse("catalog:precio_eliminar", args=[fila.pk]))
    nueva = PrecioReferenciaFactory(
        editorial=producto.editorial, tipo=producto.tipo, formato=producto.formato, pvp=11000
    )

    client_admin.post(reverse("catalog:producto_restaurar_precio", args=[producto.pk]))

    producto.refresh_from_db()
    assert producto.precio_referencia == nueva
    assert producto.precio == Decimal("11000")


def test_CO031_un_importado_a_mano_vuelve_al_margen_vigente_desde_su_base(client_admin):
    fijar_margen("0.4250")
    producto = importado("10000.55", precio=Decimal("15000"), precio_manual=True)

    client_admin.post(reverse("catalog:producto_restaurar_precio", args=[producto.pk]))

    producto.refresh_from_db()
    # 10000,55 × 1,425 = 14250,78… → redondeo al peso al final, no antes.
    assert producto.precio == Decimal("14251.00")
    assert producto.precio_base == Decimal("10000.55")
    assert producto.precio_manual is False


def test_CO031_no_aplica_a_un_producto_que_ya_sigue_su_fuente(client_admin):
    """Precondición: precio a mano, o nacional sin vínculo con fila."""
    fila = PrecioReferenciaFactory(pvp=Decimal("10000"))
    producto = vinculado(fila)
    registros = RegistroAuditoria.objects.count()

    client_admin.post(reverse("catalog:producto_restaurar_precio", args=[producto.pk]))

    producto.refresh_from_db()
    assert producto.precio == Decimal("10000")
    assert RegistroAuditoria.objects.count() == registros


# ===========================================================================
# Margen global — CO-052, CO-053 y CO-167
# ===========================================================================


def test_CO167_consultar_margen_lo_expresa_como_porcentaje(client_admin):
    fijar_margen("0.4250")

    contenido = client_admin.get(reverse("catalog:margen")).content.decode()

    assert "42,5 %" in contenido


def test_CO052_simular_informa_el_impacto_sin_cambiar_nada(client_admin):
    fijar_margen("0.40")
    importado("10000")
    importado("20000", estado=Producto.CANCELADO_EDITORIAL)
    importado("30000", precio_manual=True)
    registros = RegistroAuditoria.objects.count()

    respuesta = client_admin.post(reverse("catalog:margen"), {"margen": "50"})

    simulacion = respuesta.context["simulacion"]
    assert (simulacion.a_recalcular, simulacion.excluidos_por_precio_manual) == (2, 1)
    assert ConfiguracionSistema.obtener().margen_ganancia == Decimal("0.4000")
    assert RegistroAuditoria.objects.count() == registros


def test_CO052_sin_importados_la_precondicion_no_se_cumple(client_admin):
    """C-11: mandan los contratos. Sin importados no hay cambio (C-19 abierta)."""
    fijar_margen("0.40")

    respuesta = client_admin.post(reverse("catalog:margen"), {"margen": "50", "confirmar": "1"})

    assert "Todavía no hay productos importados" in respuesta.content.decode()
    assert ConfiguracionSistema.obtener().margen_ganancia == Decimal("0.4000")


def test_CO052_A1_todos_a_mano_avisa_que_no_afecta_a_ninguno(client_admin):
    importado("10000", precio_manual=True)

    respuesta = client_admin.post(reverse("catalog:margen"), {"margen": "50"})

    assert "la propagación no afecta a ninguno" in respuesta.content.decode()


def test_CO053_confirmar_recalcula_desde_el_precio_base_con_decimal_exacto(
    client_admin, administrador
):
    fijar_margen("0.40")
    # 9999,99 × 1,4255 = 14254,985… : redondear el margen o el base antes de
    # multiplicar da otro peso.
    vinculado_al_margen = importado("9999.99")
    cancelado = importado("10000", estado=Producto.CANCELADO_EDITORIAL)
    a_mano = importado("10000", precio=Decimal("12345"), precio_manual=True)

    client_admin.post(reverse("catalog:margen"), {"margen": "42.55", "confirmar": "1"})

    configuracion = ConfiguracionSistema.obtener()
    assert configuracion.margen_ganancia == Decimal("0.4255")
    assert configuracion.actualizado_por == administrador
    vinculado_al_margen.refresh_from_db()
    cancelado.refresh_from_db()
    a_mano.refresh_from_db()
    assert vinculado_al_margen.precio == Decimal("14255.00")
    assert vinculado_al_margen.precio_base == Decimal("9999.99")
    # C-11: el margen alcanza también a los cancelados por la editorial.
    assert cancelado.precio == Decimal("14255.00")
    assert a_mano.precio == Decimal("12345")
    registro = auditorias(RegistroAuditoria.PARAMETRO_MODIFICADO).get()
    assert registro.actor == administrador
    assert "40 % → 42,55 %" in registro.detalle
    assert "2 productos recalculados" in registro.detalle


def test_CO053_no_toca_a_los_nacionales(client_admin):
    importado("10000")
    nacional = ProductoFactory(precio=Decimal("8000"), precio_base=Decimal("8000"))

    client_admin.post(reverse("catalog:margen"), {"margen": "90", "confirmar": "1"})

    nacional.refresh_from_db()
    assert nacional.precio == Decimal("8000")


def test_CO156_abandonar_el_cambio_de_margen_lo_deja_como_estaba(client_admin):
    """CU-PVP-MAR A2: simular y no confirmar."""
    fijar_margen("0.40")
    producto = importado("10000")

    client_admin.post(reverse("catalog:margen"), {"margen": "90"})

    producto.refresh_from_db()
    assert ConfiguracionSistema.obtener().margen_ganancia == Decimal("0.4000")
    assert producto.precio == Decimal("14000")


# ===========================================================================
# Control de acceso: por la dirección real, con el rol equivocado
# ===========================================================================


@pytest.mark.parametrize(
    "ruta",
    [
        "catalog:precio_lista",
        "catalog:precio_crear",
        "catalog:precio_editar",
        "catalog:precio_eliminar",
        "catalog:margen",
        "catalog:producto_restaurar_precio",
    ],
)
def test_el_cajero_no_opera_los_precios(client, cajero, ruta):
    fila = PrecioReferenciaFactory(pvp=Decimal("10000"))
    producto = vinculado(fila, precio_manual=True, precio=Decimal("1"), precio_referencia=None)
    argumentos = {
        "catalog:precio_editar": [fila.pk],
        "catalog:precio_eliminar": [fila.pk],
        "catalog:producto_restaurar_precio": [producto.pk],
    }.get(ruta, [])
    client.force_login(cajero)

    url = reverse(ruta, args=argumentos)
    assert client.get(url).status_code == 403
    assert client.post(url, {"pvp": "1", "margen": "1", "confirmar": "1"}).status_code == 403
    fila.refresh_from_db()
    producto.refresh_from_db()
    assert fila.pvp == Decimal("10000")
    assert producto.precio == Decimal("1")
