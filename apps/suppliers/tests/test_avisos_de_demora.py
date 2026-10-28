"""Un aviso de demora procesado no falla: propone registrar la demora (B-04-010).

Plan 00 del circuito con los proveedores, ítem G. El correo bien clasificado que
no es de novedades queda Procesado, sin borradores; si es una demora, su ficha
propone `CU-ALT-DEM` sobre las pre-ventas del proveedor, con lo que el modelo
reconoció. **Nada se aplica sin confirmar** (regla 4): la demora se registra
recién en su pantalla, con el informe de impacto de `CO-014`.

El modelo nunca se llama: se parchea la puerta HTTP.
"""

import json
from datetime import date, timedelta
from unittest.mock import patch

import pytest
from django.urls import reverse
from django.utils import timezone

from apps.accounts.tests.factories import UsuarioFactory
from apps.catalog.models import BorradorProducto, Producto
from apps.catalog.tests.factories import EditorialFactory, ProductoFactory, TipoFactory
from apps.core import integraciones
from apps.core.models import RegistroAuditoria
from apps.pedidos.tests.util import reservar
from apps.suppliers import demoras, extraccion, services
from apps.suppliers.models import CorreoProveedor, LineaPedidoProveedor, PedidoProveedor
from apps.suppliers.tests import correos_de_ejemplo as ejemplo
from apps.suppliers.tests.factories import ProveedorFactory

pytestmark = pytest.mark.django_db

ISBN_BERSERK = "9789878271583"


def mencion(**cambios):
    base = {
        "isbn": "",
        "titulo": "Berserk Deluxe",
        "volumen": "5",
        "formato": "",
        "precio": "",
        "fecha": "",
        "imagen": "",
        "confianza": {campo: "alta" for campo in extraccion.CAMPOS_CON_CONFIANZA},
    }
    base.update(cambios)
    return base


def respuesta(intencion=extraccion.DEMORA, productos=(), periodo=""):
    contenido = {"intencion": intencion, "periodo": periodo, "productos": list(productos)}
    return integraciones.Respuesta(
        datos={"choices": [{"message": {"content": json.dumps(contenido)}}]}
    )


def contestando(valor):
    return patch("apps.core.integraciones.pedir", return_value=valor)


def en_dias(dias):
    return timezone.localdate() + timedelta(days=dias)


@pytest.fixture
def ivrea(db):
    return EditorialFactory(nombre="Ivrea")


@pytest.fixture
def proveedor(ivrea):
    return ProveedorFactory(
        correo_comercial="novedades@ivrea.test",
        editorial=ivrea,
        tipo_por_defecto=TipoFactory(nombre="Manga", usa_formato=True),
    )


@pytest.fixture
def berserk(ivrea):
    return ProductoFactory(
        titulo="Berserk Deluxe",
        volumen=5,
        editorial=ivrea,
        estado=Producto.PRE_VENTA,
        fecha_llegada=en_dias(5),
    )


@pytest.fixture
def aviso(proveedor):
    return services.ingerir(ejemplo.correo_de_demora()).correo


def procesar(correo, administrador, **kwargs):
    with contestando(respuesta(**kwargs)):
        services.aprobar_correo(correo.pk, actor=administrador)
    correo.refresh_from_db()
    return correo


def url_ficha(correo):
    return reverse("suppliers:correo_detalle", args=[correo.pk])


def url_demora(producto, correo=None):
    url = reverse("pedidos:demora", args=[producto.pk])
    return f"{url}?correo={correo.pk}" if correo else url


# ---------------------------------------------------------------------------
# La extracción
# ---------------------------------------------------------------------------


def test_la_demora_trae_lo_que_se_atrasa_con_su_fecha_y_la_del_aviso():
    with contestando(
        respuesta(
            productos=[mencion(fecha="15/06/2026"), mencion(titulo="Vagabond", volumen="2")],
            periodo="mayo 2026",
        )
    ):
        resultado = extraccion.extraer("Berserk y Vagabond se reprograman")

    assert resultado.productos == []
    assert [(p.titulo, p.volumen) for p in resultado.demorados] == [
        ("Berserk Deluxe", 5),
        ("Vagabond", 2),
    ]
    assert resultado.demorados[0].fecha == date(2026, 6, 15)
    assert resultado.periodo == date(2026, 5, 1)
    assert resultado.como_json()["demorados"][0]["fecha"] == "2026-06-15"


def test_una_demora_con_fecha_ilegible_lo_anota():
    with contestando(respuesta(productos=[mencion()], periodo="cuando se pueda")):
        resultado = extraccion.extraer("Berserk se atrasa")

    assert resultado.periodo is None
    assert "sin fecha nueva" in resultado.reparos[0]


def test_de_un_correo_otro_no_se_lee_nada():
    with contestando(respuesta(intencion=extraccion.OTRO, productos=[mencion()])):
        resultado = extraccion.extraer("Factura 0001")

    assert resultado.productos == []
    assert resultado.demorados == []


# ---------------------------------------------------------------------------
# El estado del correo
# ---------------------------------------------------------------------------


def test_un_aviso_de_demora_queda_procesado_sin_borradores(aviso, administrador):
    correo = procesar(aviso, administrador, productos=[mencion()])

    assert correo.estado == CorreoProveedor.PROCESADO
    assert correo.es_aviso_de_demora
    assert "aviso de demora" in correo.motivo
    assert not BorradorProducto.objects.exists()
    assert correo.puede_descartarse


def test_un_correo_de_novedades_sin_productos_sigue_fallando(aviso, administrador):
    """`CO-017` E4 sigue en pie para lo que sí es una falla."""
    correo = procesar(aviso, administrador, intencion=extraccion.NOVEDADES)

    assert correo.estado == CorreoProveedor.FALLIDO
    assert not correo.puede_descartarse


def test_si_el_modelo_no_responde_sigue_fallando(aviso, administrador):
    with contestando(integraciones.Respuesta(motivo=integraciones.SIN_CONEXION)):
        services.aprobar_correo(aviso.pk, actor=administrador)
    aviso.refresh_from_db()

    assert aviso.estado == CorreoProveedor.FALLIDO


def test_procesar_un_aviso_no_toca_la_preventa(aviso, administrador, berserk):
    """Regla 4: el modelo propone, nunca aplica. Postcondición negativa."""
    antes = (berserk.fecha_llegada, berserk.demorado, berserk.estado)

    procesar(aviso, administrador, productos=[mencion(fecha="2026-12-01")])

    berserk.refresh_from_db()
    assert (berserk.fecha_llegada, berserk.demorado, berserk.estado) == antes


# ---------------------------------------------------------------------------
# La propuesta
# ---------------------------------------------------------------------------


def test_la_propuesta_pone_primero_lo_que_el_aviso_menciona(aviso, administrador, berserk, ivrea):
    otra = ProductoFactory(titulo="Akira", volumen=1, editorial=ivrea, estado=Producto.PRE_VENTA)
    ProductoFactory(titulo="Ajena", estado=Producto.PRE_VENTA)  # de otra editorial
    fecha = en_dias(40)
    correo = procesar(
        aviso, administrador, productos=[mencion(titulo="berserk  DELUXE", fecha=fecha.isoformat())]
    )

    propuesta = demoras.proponer(correo)

    assert [fila.producto.pk for fila in propuesta.filas] == [berserk.pk, otra.pk]
    assert propuesta.filas[0].mencionado
    assert propuesta.filas[0].fecha_propuesta == fecha
    assert propuesta.filas[1].mencionado is None
    assert propuesta.sin_preventa == []


def test_sin_fecha_propia_se_propone_la_del_aviso(aviso, administrador, berserk):
    correo = procesar(aviso, administrador, productos=[mencion()], periodo="junio 2027")

    assert demoras.proponer(correo).filas[0].fecha_propuesta == date(2027, 6, 1)


def test_el_isbn_reconoce_aunque_el_titulo_no_coincida(aviso, administrador, ivrea):
    tomo = ProductoFactory(
        titulo="Berserk Edición Deluxe",
        volumen=5,
        isbn=ISBN_BERSERK,
        editorial=ivrea,
        estado=Producto.PRE_VENTA,
    )
    correo = procesar(aviso, administrador, productos=[mencion(isbn="978-987-827-158-3")])

    assert demoras.proponer(correo).filas[0].producto.pk == tomo.pk
    assert demoras.proponer(correo).filas[0].mencionado


def test_otro_volumen_no_es_el_mismo_producto(aviso, administrador, berserk):
    correo = procesar(aviso, administrador, productos=[mencion(volumen="6")])

    propuesta = demoras.proponer(correo)
    assert propuesta.mencionadas == []
    assert [m["volumen"] for m in propuesta.sin_preventa] == [6]


def test_una_distribuidora_ve_lo_que_tiene_en_camino_con_ella(db, administrador):
    distribuidora = ProveedorFactory(correo_comercial="novedades@ivrea.test", editorial=None)
    tomo = ProductoFactory(titulo="Berserk Deluxe", volumen=5, stock=0, estado=Producto.AGOTADO)
    pedido = PedidoProveedor.objects.create(proveedor=distribuidora, origen=PedidoProveedor.MANUAL)
    LineaPedidoProveedor.objects.create(pedido=pedido, producto=tomo, cantidad_pedida=4)
    Producto.objects.filter(pk=tomo.pk).update(estado=Producto.PRE_VENTA)
    correo = procesar(
        services.ingerir(ejemplo.correo_de_demora()).correo,
        administrador,
        productos=[mencion()],
    )

    assert [fila.producto.pk for fila in demoras.proponer(correo).filas] == [tomo.pk]


# ---------------------------------------------------------------------------
# Las pantallas, por su dirección real
# ---------------------------------------------------------------------------


def test_la_ficha_del_aviso_ofrece_registrar_la_demora(client_admin, aviso, administrador, berserk):
    reservar(UsuarioFactory(rol="cliente"), berserk, cantidad=2)
    procesar(aviso, administrador, productos=[mencion(), mencion(titulo="Vagabond")])

    html = client_admin.get(url_ficha(aviso)).content.decode()

    assert "Registrar la demora" in html
    # Lo que el aviso nombra va arriba; no hay otras pre-ventas que plegar.
    assert "Otras pre-ventas" not in html
    assert url_demora(berserk, aviso) in html
    assert "Vagabond" in html and "no está en pre-venta" in html


def test_la_pantalla_de_demora_trae_la_propuesta_sin_registrarla(
    client_admin, aviso, administrador, berserk
):
    fecha = en_dias(30)
    procesar(aviso, administrador, productos=[mencion(fecha=fecha.isoformat())])

    respuesta_http = client_admin.get(url_demora(berserk, aviso))

    formulario = respuesta_http.context["form"]
    assert formulario.initial["fecha_estimada"] == fecha
    assert aviso.asunto in formulario.initial["nota"]
    assert "Volver al correo" in respuesta_http.content.decode()
    berserk.refresh_from_db()
    assert not berserk.demorado
    assert berserk.fecha_llegada == en_dias(5)


def test_una_fecha_propuesta_que_ya_paso_no_se_carga(client_admin, aviso, administrador, berserk):
    procesar(aviso, administrador, productos=[mencion(fecha="2020-01-01")])

    formulario = client_admin.get(url_demora(berserk, aviso)).context["form"]

    assert formulario.initial["fecha_estimada"] is None


def test_un_correo_que_no_es_aviso_de_demora_no_propone_nada(
    client_admin, aviso, administrador, berserk
):
    procesar(aviso, administrador, intencion=extraccion.OTRO)

    respuesta_http = client_admin.get(url_demora(berserk, aviso))

    assert respuesta_http.context["correo"] is None
    assert respuesta_http.context["form"].initial == {}


def test_confirmar_la_demora_desde_el_aviso_vuelve_al_correo(
    client_admin, aviso, administrador, berserk
):
    fecha = en_dias(30)
    procesar(aviso, administrador, productos=[mencion(fecha=fecha.isoformat())])

    respuesta_http = client_admin.post(
        url_demora(berserk, aviso),
        {"fecha_estimada": fecha.isoformat(), "nota": "Aviso", "confirmar": "1"},
    )

    assert respuesta_http.url == url_ficha(aviso)
    berserk.refresh_from_db()
    assert berserk.demorado
    # CO-015: la fecha nueva va a `fecha_estimada`; la de llegada queda como la original.
    assert berserk.fecha_estimada == fecha


def test_el_cajero_no_abre_la_propuesta_por_su_direccion(
    client, cajero, aviso, administrador, berserk
):
    procesar(aviso, administrador, productos=[mencion()])
    client.force_login(cajero)

    assert client.get(url_demora(berserk, aviso)).status_code == 403
    assert client.get(url_ficha(aviso)).status_code == 403


# ---------------------------------------------------------------------------
# Descartar después de procesar
# ---------------------------------------------------------------------------


def test_un_aviso_procesado_se_puede_descartar(client_admin, aviso, administrador):
    procesar(aviso, administrador, productos=[mencion()])

    client_admin.post(url_ficha(aviso), {"motivo": "Demora ya registrada"})

    aviso.refresh_from_db()
    assert aviso.estado == CorreoProveedor.DESCARTADO
    assert aviso.motivo == "Demora ya registrada"
    assert RegistroAuditoria.objects.filter(
        accion=RegistroAuditoria.CORREO_DESCARTADO, objetivo_pk=aviso.pk
    ).exists()


def test_un_correo_de_novedades_procesado_no_se_descarta(client_admin, aviso, administrador):
    """Sus borradores siguen en la revisión: descartarlo los dejaría huérfanos."""
    with contestando(
        respuesta(
            intencion=extraccion.NOVEDADES,
            productos=[mencion(precio="24900", formato="Tapa dura")],
        )
    ):
        services.aprobar_correo(aviso.pk, actor=administrador)

    client_admin.post(url_ficha(aviso), {"motivo": "No"})

    aviso.refresh_from_db()
    assert aviso.estado == CorreoProveedor.PROCESADO


def test_lo_que_cu_alt_dem_no_admite_no_ofrece_el_boton(
    client_admin, aviso, administrador, berserk, ivrea
):
    vencida = ProductoFactory(
        titulo="Akira",
        volumen=1,
        editorial=ivrea,
        estado=Producto.PRE_VENTA,
        fecha_llegada=en_dias(-3),
    )
    procesar(aviso, administrador, productos=[mencion()])

    propuesta = demoras.proponer(aviso)
    html = client_admin.get(url_ficha(aviso)).content.decode()

    fila = next(f for f in propuesta.filas if f.producto.pk == vencida.pk)
    assert "ya pasó" in fila.no_admite
    assert url_demora(vencida, aviso) not in html
    assert url_demora(berserk, aviso) in html


def test_las_que_el_aviso_no_nombra_quedan_plegadas(
    client_admin, aviso, administrador, berserk, ivrea
):
    otra = ProductoFactory(titulo="Akira", volumen=1, editorial=ivrea, estado=Producto.PRE_VENTA)
    procesar(aviso, administrador, productos=[mencion()])

    html = client_admin.get(url_ficha(aviso)).content.decode()

    plegado = html[html.index('<details class="plegable"') :]
    assert url_demora(otra, aviso) in plegado
    assert url_demora(berserk, aviso) not in plegado


# ---------------------------------------------------------------------------
# El volumen pegado al título y la fecha del aviso (revisión del 2026-10-26)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("titulo", "esperado"),
    [
        ("Ichi The Witch #1", ("Ichi The Witch", 1)),
        ("Berserk Deluxe vol. 5", ("Berserk Deluxe", 5)),
        ("Dragon Ball Super Tomo 24", ("Dragon Ball Super", 24)),
        ("One Piece Nº 109", ("One Piece", 109)),
        ("Kaiju No. 8 #3", ("Kaiju No. 8", 3)),
        # Sin marca explícita no se separa: el número es parte del título.
        ("Kaiju No. 8", ("Kaiju No. 8", None)),
        ("Mono 3", ("Mono 3", None)),
        ("Another 0", ("Another 0", None)),
    ],
)
def test_el_volumen_pegado_al_titulo_se_separa_solo_con_marca(titulo, esperado):
    assert extraccion.separar_volumen(titulo) == esperado


def test_la_extraccion_separa_el_volumen_que_el_modelo_dejo_en_el_titulo():
    with contestando(respuesta(productos=[mencion(titulo="Ichi The Witch #1", volumen="")])):
        resultado = extraccion.extraer("Ichi The Witch 1 se atrasa")

    assert (resultado.demorados[0].titulo, resultado.demorados[0].volumen) == (
        "Ichi The Witch",
        1,
    )


def test_una_extraccion_vieja_con_el_volumen_en_el_titulo_igual_se_reconoce(
    aviso, administrador, berserk
):
    procesar(aviso, administrador, productos=[mencion()])
    aviso.extraccion["demorados"] = [{"titulo": "BERSERK DELUXE #5", "volumen": None}]
    aviso.save(update_fields=["extraccion"])

    assert [fila.producto.pk for fila in demoras.proponer(aviso).mencionadas] == [berserk.pk]


def test_la_preventa_elegida_de_la_lista_recibe_la_fecha_del_aviso(
    client_admin, aviso, administrador, berserk
):
    fecha = en_dias(36)
    procesar(aviso, administrador, productos=[mencion(titulo="Vagabond", fecha=fecha.isoformat())])

    propuesta = demoras.proponer(aviso)
    formulario = client_admin.get(url_demora(berserk, aviso)).context["form"]

    assert propuesta.mencionadas == []
    assert propuesta.otras[0].fecha_propuesta == fecha
    assert formulario.initial["fecha_estimada"] == fecha


def test_con_dos_fechas_distintas_no_se_propone_ninguna_a_la_elegida(aviso, administrador, berserk):
    procesar(
        aviso,
        administrador,
        productos=[
            mencion(titulo="Vagabond", fecha=en_dias(30).isoformat()),
            mencion(titulo="Akira", fecha=en_dias(60).isoformat()),
        ],
    )

    assert demoras.proponer(aviso).otras[0].fecha_propuesta is None


def test_la_lista_plegada_tiene_buscador(client_admin, aviso, administrador, berserk):
    procesar(aviso, administrador, productos=[mencion(titulo="Vagabond")])

    html = client_admin.get(url_ficha(aviso)).content.decode()

    plegado = html[html.index('<details class="plegable"') :]
    assert "data-filtro-demora" in plegado
    assert 'data-fila-demora="berserk deluxe 5' in plegado


def test_la_fecha_de_lo_que_se_atrasa_se_muestra_como_las_demas(
    client_admin, aviso, administrador, berserk
):
    procesar(aviso, administrador, productos=[mencion(fecha="2026-12-01")])

    html = client_admin.get(url_ficha(aviso)).content.decode()

    assert "01/12/2026" in html
    assert "2026-12-01" not in html


# ---------------------------------------------------------------------------
# Varios tomos desde el aviso (B-01-022)
# ---------------------------------------------------------------------------


def test_el_aviso_elige_de_antemano_lo_que_nombra_para_demorarlo_junto(
    client_admin, aviso, administrador, berserk, ivrea
):
    otra = ProductoFactory(titulo="Akira", volumen=1, editorial=ivrea, estado=Producto.PRE_VENTA)
    procesar(aviso, administrador, productos=[mencion()])

    html = client_admin.get(url_ficha(aviso)).content.decode()

    assert reverse("pedidos:demora_lote") in html
    assert f'name="producto" value="{berserk.pk}" checked' in html
    assert f'name="producto" value="{otra.pk}">' in html
    assert "Registrar la demora de los elegidos" in html


def test_la_demora_de_varios_tomos_trae_la_fecha_del_aviso(
    client_admin, aviso, administrador, berserk
):
    fecha = en_dias(40)
    procesar(aviso, administrador, productos=[mencion(fecha=fecha.isoformat())])

    respuesta = client_admin.get(
        reverse("pedidos:demora_lote"), {"correo": aviso.pk, "producto": [berserk.pk]}
    )

    fila = respuesta.context["filas"][0]
    assert fila["fecha_texto"] == fecha.isoformat()
    assert aviso.asunto in respuesta.content.decode()  # la nota precargada
    berserk.refresh_from_db()
    assert berserk.demorado is False
