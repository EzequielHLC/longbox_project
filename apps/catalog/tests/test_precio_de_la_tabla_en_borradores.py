"""El precio de la tabla de referencia en la revisión de borradores (B-01-018).

Decisiones del responsable del 2026-10-26: sin precio, el borrador toma el de
la tabla; uno distinto se respeta y se confirma como en `CU-ALT-NAC` A3, en el
servidor y también en lote; y si el precio es el de la tabla, la confianza que
el modelo declaró sobre él deja de exigir revisión. Las fechas sin año
(«13/11») se toman como la próxima vez que caen (B-01-019).
"""

import json
from datetime import date
from decimal import Decimal
from unittest.mock import patch

import pytest
from django.urls import reverse

from apps.catalog import borradores, revisiones
from apps.catalog.models import BorradorProducto, ConfianzaCampo, Producto
from apps.catalog.tests.factories import (
    EditorialFactory,
    FormatoFactory,
    PrecioReferenciaFactory,
    TipoFactory,
)
from apps.core import integraciones
from apps.suppliers import extraccion
from apps.suppliers.models import CorreoProveedor
from apps.suppliers.tests.factories import ProveedorFactory

pytestmark = pytest.mark.django_db

PVP = Decimal("21900.00")


@pytest.fixture
def editorial():
    return EditorialFactory(nombre="Ivrea")


@pytest.fixture
def tipo():
    return TipoFactory(nombre="Manga", usa_formato=True)


@pytest.fixture
def formato():
    return FormatoFactory(nombre="B6")


@pytest.fixture
def fila(editorial, tipo, formato):
    return PrecioReferenciaFactory(editorial=editorial, tipo=tipo, formato=formato, pvp=PVP)


@pytest.fixture
def correo(editorial, tipo):
    proveedor = ProveedorFactory(editorial=editorial, tipo_por_defecto=tipo)
    return CorreoProveedor.objects.create(
        proveedor=proveedor,
        message_id="<precio@ivrea.test>",
        remitente=proveedor.correo_comercial,
        asunto="Novedades",
        contenido="| fila |",
        estado=CorreoProveedor.PROCESADO,
    )


def borrador_de(correo, formato, **cambios):
    datos = {
        "correo": correo,
        "proveedor": correo.proveedor,
        "titulo": "Undead Unluck",
        "volumen": 13,
        "editorial": correo.proveedor.editorial,
        "tipo": correo.proveedor.tipo_por_defecto,
        "formato": formato,
        "precio": PVP,
        "stock_inicial": 1,
        "estado_sugerido": Producto.ACTIVO,
    }
    datos.update(cambios)
    return BorradorProducto.objects.create(**datos)


def generar_con(correo, **producto):
    base = {
        "titulo": "Undead Unluck",
        "volumen": 13,
        "isbn": "",
        "formato": "B6",
        "precio": "",
        "fecha": "",
        "imagen": "",
        "confianza": {c: "alta" for c in extraccion.CAMPOS_CON_CONFIANZA},
        "reparos": [],
    }
    base.update(producto)
    correo.extraccion = {"intencion": "novedades", "periodo": "", "productos": [base]}
    correo.save(update_fields=["extraccion"])
    return borradores.generar(correo).creados[0]


def url(borrador):
    return reverse("catalog:borrador_detalle", args=[borrador.pk])


def datos_del_formulario(borrador, **cambios):
    datos = {
        "titulo": borrador.titulo,
        "volumen": borrador.volumen,
        "isbn": "",
        "editorial": borrador.editorial_id,
        "tipo": borrador.tipo_id,
        "formato": borrador.formato_id,
        "precio": str(borrador.precio) if borrador.precio is not None else "",
        "estado_sugerido": borrador.estado_sugerido,
        "stock_inicial": 1,
        "autor": "",
        "sinopsis": "",
    }
    datos.update(cambios)
    return datos


# ---------------------------------------------------------------------------
# La generación
# ---------------------------------------------------------------------------


def test_sin_precio_en_el_correo_el_borrador_nace_con_el_de_la_tabla(correo, fila):
    borrador = generar_con(correo)

    assert borrador.precio == PVP
    assert borrador.estado == BorradorProducto.PENDIENTE  # ya no nace incompleto


def test_un_precio_del_correo_se_respeta_aunque_no_sea_el_de_la_tabla(correo, fila):
    borrador = generar_con(correo, precio="24900")

    assert borrador.precio == Decimal("24900")


def test_sin_fila_en_la_tabla_sigue_naciendo_sin_precio(correo, formato):
    borrador = generar_con(correo)

    assert borrador.precio is None
    assert borrador.estado == BorradorProducto.INCOMPLETO


# ---------------------------------------------------------------------------
# La confianza del precio
# ---------------------------------------------------------------------------


def test_con_el_precio_de_la_tabla_la_confianza_baja_no_exige_revision(correo, formato, fila):
    borrador = borrador_de(correo, formato)
    ConfianzaCampo.objects.create(borrador=borrador, campo="precio", nivel=ConfianzaCampo.BAJA)

    assert borrador.precio_es_el_de_la_tabla
    assert borrador.confianzas_bajas_sin_revisar == []
    assert revisiones.confirmar_en_lote([borrador], actor=None).confirmadas


def test_con_otro_precio_la_confianza_baja_sigue_exigiendo_revision(correo, formato, fila):
    borrador = borrador_de(correo, formato, precio=Decimal("24900"))
    ConfianzaCampo.objects.create(borrador=borrador, campo="precio", nivel=ConfianzaCampo.BAJA)

    assert [c.campo for c in borrador.confianzas_bajas_sin_revisar] == ["precio"]


# ---------------------------------------------------------------------------
# El precio distinto del de la tabla, en el servidor
# ---------------------------------------------------------------------------


def test_el_lote_excluye_un_precio_distinto_del_de_la_tabla(correo, formato, fila, administrador):
    aparte = borrador_de(correo, formato, precio=Decimal("24900"))
    de_tabla = borrador_de(correo, formato, titulo="Otro")

    resultado = revisiones.confirmar_en_lote([aparte, de_tabla], actor=administrador)

    assert [c.borrador.pk for c in resultado.confirmadas] == [de_tabla.pk]
    assert [e.motivo for e in resultado.excluidas] == [revisiones.PRECIO_APARTE_DE_LA_TABLA]


def test_confirmar_un_precio_distinto_sin_la_casilla_lo_rechaza(
    client_admin, correo, formato, fila
):
    borrador = borrador_de(correo, formato, precio=Decimal("24900"))

    respuesta = client_admin.post(
        url(borrador), {**datos_del_formulario(borrador), "confirmar": "1"}
    )

    assert respuesta.status_code == 200
    assert "romperá ese vínculo" in respuesta.content.decode()
    borrador.refresh_from_db()
    assert borrador.esta_abierto
    assert not Producto.objects.exists()


def test_confirmar_un_precio_distinto_con_la_casilla_lo_deja_a_mano(
    client_admin, correo, formato, fila
):
    borrador = borrador_de(correo, formato, precio=Decimal("24900"))

    client_admin.post(
        url(borrador),
        {**datos_del_formulario(borrador), "confirmar": "1", "confirma_precio_manual": "on"},
    )

    producto = Producto.objects.get().especifico
    assert producto.precio == Decimal("24900")
    assert producto.precio_manual is True
    assert producto.precio_referencia is None


def test_guardar_sin_confirmar_no_pide_la_casilla(client_admin, correo, formato, fila):
    borrador = borrador_de(correo, formato, precio=Decimal("24900"))

    respuesta = client_admin.post(url(borrador), {**datos_del_formulario(borrador), "guardar": "1"})

    assert respuesta.status_code == 302


def test_el_precio_de_la_tabla_confirma_vinculado(client_admin, correo, formato, fila):
    borrador = borrador_de(correo, formato)

    client_admin.post(url(borrador), {**datos_del_formulario(borrador), "confirmar": "1"})

    producto = Producto.objects.get().especifico
    assert producto.precio_manual is False
    assert producto.precio_referencia == fila


# ---------------------------------------------------------------------------
# La pantalla
# ---------------------------------------------------------------------------


def test_un_borrador_sin_precio_se_abre_con_el_de_la_tabla(client_admin, correo, formato, fila):
    borrador = borrador_de(correo, formato, precio=None)

    respuesta = client_admin.get(url(borrador))

    assert respuesta.context["form"].initial["precio"] == PVP
    html = respuesta.content.decode()
    assert "Tabla de referencia" in html
    assert "Usar el de la tabla" in html
    assert reverse("catalog:precio_referencia") in html


def test_con_el_precio_de_la_tabla_la_pantalla_no_pide_revisar_la_confianza(
    client_admin, correo, formato, fila
):
    borrador = borrador_de(correo, formato)
    ConfianzaCampo.objects.create(borrador=borrador, campo="precio", nivel=ConfianzaCampo.BAJA)

    html = client_admin.get(url(borrador)).content.decode()

    assert "no hace falta revisarlo" in html
    assert 'class="casilla casilla--critica reparo hidden" data-confianza="precio"' in html


def test_el_cajero_no_confirma_por_la_direccion_real(client, cajero, correo, formato, fila):
    borrador = borrador_de(correo, formato, precio=Decimal("24900"))
    client.force_login(cajero)

    respuesta = client.post(
        url(borrador),
        {**datos_del_formulario(borrador), "confirmar": "1", "confirma_precio_manual": "on"},
    )

    assert respuesta.status_code == 403
    assert not Producto.objects.exists()


# ---------------------------------------------------------------------------
# La fecha sin año (B-01-019)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("texto", "desde", "esperada"),
    [
        ("13/11", date(2026, 10, 26), date(2026, 11, 13)),
        ("13/11", date(2026, 11, 13), date(2026, 11, 13)),
        ("5/1", date(2026, 10, 26), date(2027, 1, 5)),
        ("sale el 13/11", date(2026, 10, 26), date(2026, 11, 13)),
        ("31/02", date(2026, 10, 26), None),
        ("marzo", date(2026, 10, 26), None),
        ("13/11/2026", date(2026, 10, 26), None),
    ],
)
def test_una_fecha_sin_anio_es_la_proxima_vez_que_cae(texto, desde, esperada):
    assert extraccion.fecha_sin_anio(texto, desde) == esperada


def _respuesta(productos, periodo=""):
    contenido = {"intencion": "novedades", "periodo": periodo, "productos": productos}
    return integraciones.Respuesta(
        datos={"choices": [{"message": {"content": json.dumps(contenido)}}]}
    )


def _fila(**cambios):
    base = {
        "isbn": "",
        "titulo": "Undead Unluck",
        "volumen": "13",
        "formato": "B6",
        "precio": "",
        "fecha": "",
        "imagen": "",
        "confianza": {c: "alta" for c in extraccion.CAMPOS_CON_CONFIANZA},
    }
    base.update(cambios)
    return base


def test_la_fecha_de_una_fila_sin_anio_se_toma_y_queda_anotada():
    with patch("apps.core.integraciones.pedir", return_value=_respuesta([_fila(fecha="13/11")])):
        resultado = extraccion.extraer(
            "| Undead Unluck | 13 | 13/11 |", recibido=date(2026, 10, 26)
        )

    producto = resultado.productos[0]
    assert producto.fecha == date(2026, 11, 13)
    assert producto.reparos == ["Fecha sin año: «13/11». Se tomó el 13/11/2026: revisala."]


def test_el_periodo_sin_anio_tambien_se_toma_y_queda_anotado():
    with patch(
        "apps.core.integraciones.pedir", return_value=_respuesta([_fila()], periodo="Salen el 5/1")
    ):
        resultado = extraccion.extraer("Salen el 5/1", recibido=date(2026, 10, 26))

    assert resultado.periodo == date(2027, 1, 5)
    assert "Se tomó el 05/01/2027" in resultado.reparos[0]


# ---------------------------------------------------------------------------
# La serie que ya está en el catálogo (B-01-020)
# ---------------------------------------------------------------------------


@pytest.fixture
def tanko():
    return FormatoFactory(nombre="Tankoubon")


@pytest.fixture
def serie(editorial, tipo, tanko):
    from apps.catalog.tests.factories import ProductoFactory

    ProductoFactory(
        titulo="UNDEAD UNLUCK",
        volumen=11,
        editorial=editorial,
        tipo=tipo,
        formato=tanko,
        autor="Yoshifumi Tozuka",
        descripcion="Andy y Fuuko contra la Unión.",
    )
    return ProductoFactory(
        titulo="Undead Unluck",
        volumen=12,
        editorial=editorial,
        tipo=tipo,
        formato=tanko,
        autor="",
        descripcion="",
        solo_adultos=True,
    )


def test_la_serie_se_reconoce_sin_mayusculas_ni_tildes_y_en_la_misma_editorial(editorial, serie):
    from apps.catalog import services

    encontrada = services.serie_de("undead  unlúck", editorial)

    assert encontrada.tomos == 2
    assert encontrada.ultimo == serie  # el último tomo manda en tipo y formato
    assert encontrada.autor == "Yoshifumi Tozuka"  # el último que lo tiene
    assert encontrada.sinopsis == "Andy y Fuuko contra la Unión."
    assert encontrada.solo_adultos is True
    assert services.serie_de("Undead Unluck", EditorialFactory(nombre="Panini")) is None
    assert services.serie_de("Undead", editorial) is None


def test_el_borrador_de_una_serie_conocida_nace_con_lo_que_ya_sabemos(correo, serie, formato):
    borrador = generar_con(correo, formato="B6")

    assert borrador.autor == "Yoshifumi Tozuka"
    assert borrador.sinopsis == "Andy y Fuuko contra la Unión."
    assert borrador.solo_adultos is True
    # El formato que leyó el modelo no se pisa: lo decide una persona.
    assert borrador.formato == formato


def test_sin_serie_en_el_catalogo_el_borrador_queda_como_vino(correo, formato):
    borrador = generar_con(correo, titulo="Serie Nueva")

    assert (borrador.autor, borrador.sinopsis, borrador.solo_adultos) == ("", "", False)


def test_la_ficha_ofrece_la_serie_y_señala_el_formato_distinto(
    client_admin, correo, formato, serie
):
    borrador = borrador_de(correo, formato, titulo="Undead Unluck", volumen=13)

    respuesta = client_admin.get(url(borrador))

    html = respuesta.content.decode()
    assert "Esta serie ya está en el catálogo" in html
    assert "El borrador dice B6" in html
    assert "Usar los datos de la serie" in html
    assert 'id="datos-de-la-serie"' in html
    assert respuesta.context["serie_datos"]["formato"] == serie.formato.pk
    # Un borrador generado antes se abre con lo vacío ya completado.
    assert respuesta.context["form"].initial["autor"] == "Yoshifumi Tozuka"
    assert respuesta.context["form"].initial["solo_adultos"] is True


def test_sin_serie_la_ficha_no_ofrece_nada(client_admin, correo, formato):
    borrador = borrador_de(correo, formato, titulo="Serie Nueva")

    respuesta = client_admin.get(url(borrador))

    assert respuesta.context["serie"] is None
    assert "Esta serie ya está en el catálogo" not in respuesta.content.decode()
