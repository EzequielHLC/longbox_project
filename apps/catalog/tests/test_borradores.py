"""La generación de borradores desde una extracción (CU-ALT-NOV pasos 5, 6, 7 y 9).

Es el punto del pipeline donde lo que el modelo propuso se cruza contra el
catálogo real, y donde se decide qué llega a la cola de revisión de CU-ALT-REV y qué
se descarta antes. **Ninguno de estos tests llama al modelo:** se trabaja sobre
la extracción ya guardada, que es exactamente como funciona en producción —
regenerar los borradores de un correo no vuelve a gastar una corrida de GPU.

Lo que se prueba es que nada inventado ni repetido llegue al catálogo, y que lo
que el sistema descarta quede dicho en vez de desaparecer en silencio.
"""

from datetime import timedelta
from decimal import Decimal

import pytest
from django.utils import timezone

from apps.catalog import borradores
from apps.catalog.models import BorradorProducto, ConfianzaCampo, Producto
from apps.catalog.tests.factories import (
    EditorialFactory,
    FormatoFactory,
    ProductoFactory,
    TipoFactory,
)
from apps.core.models import ConfiguracionSistema, RegistroAuditoria
from apps.suppliers.models import CorreoProveedor
from apps.suppliers.tests.factories import ProveedorFactory

BERSERK = "9789878271583"
BLUE_PERIOD = "9789878274652"

CONFIANZA_ALTA = {
    "isbn": "alta",
    "titulo": "alta",
    "volumen": "alta",
    "formato": "alta",
    "precio": "alta",
    "fecha": "alta",
}


def extraido(**cambios):
    """Un producto tal como queda guardado después de la extracción."""
    base = {
        "titulo": "Berserk Deluxe",
        "volumen": 5,
        "isbn": BERSERK,
        "formato": "Tapa dura",
        "precio": "24900",
        "fecha": "",
        "imagen": "",
        "confianza": dict(CONFIANZA_ALTA),
        "reparos": [],
    }
    base.update(cambios)
    return base


def extraccion(productos=None, periodo="", reparos=None):
    """El JSON que `CorreoProveedor.extraccion` guarda después de una corrida."""
    return {
        "version_prompt": "2",
        "intencion": "novedades",
        "error": "",
        "milisegundos": 1200,
        "periodo_texto": periodo,
        "periodo": periodo,
        "reparos": reparos or [],
        "productos": productos if productos is not None else [extraido()],
    }


@pytest.fixture
def editorial(db):
    return EditorialFactory(nombre="Ivrea")


@pytest.fixture
def tipo(db):
    """Un tipo que usa formato, que es el caso que ejercita más reglas."""
    return TipoFactory(nombre="Manga", usa_formato=True)


@pytest.fixture
def proveedor(db, editorial, tipo):
    """Con la cabecera cargada: es lo que evita que todo nazca bloqueado (A7)."""
    return ProveedorFactory(editorial=editorial, tipo_por_defecto=tipo)


@pytest.fixture
def correo(db, proveedor):
    return CorreoProveedor.objects.create(
        proveedor=proveedor,
        message_id="<novedades-1@ivrea.test>",
        remitente=proveedor.correo_comercial,
        asunto="Novedades",
        contenido="| fila |",
        estado=CorreoProveedor.PROCESADO,
    )


def generar(correo, datos, **kwargs):
    correo.extraccion = datos
    correo.save(update_fields=["extraccion"])
    return borradores.generar(correo, **kwargs)


# ---------------------------------------------------------------------------
# El camino feliz
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_un_producto_anunciado_se_convierte_en_borrador(correo, editorial, tipo):
    resultado = generar(correo, extraccion())

    assert len(resultado.creados) == 1
    borrador = resultado.creados[0]
    assert borrador.titulo == "Berserk Deluxe"
    assert borrador.volumen == 5
    assert borrador.isbn == BERSERK
    assert borrador.precio is not None
    assert borrador.estado == BorradorProducto.PENDIENTE
    # No es un producto: es una propuesta esperando que alguien la confirme.
    assert Producto.objects.count() == 0


@pytest.mark.django_db
def test_el_borrador_hereda_la_editorial_y_el_rubro_del_proveedor(correo, editorial, tipo):
    """El correo no los trae y el modelo no los inventa: los aporta la ficha del
    proveedor (A7). Sin esto todos los borradores nacerían bloqueados."""
    borrador = generar(correo, extraccion()).creados[0]

    assert borrador.editorial == editorial
    assert borrador.tipo == tipo
    assert borrador.campos_bloqueantes_vacios == []


@pytest.mark.django_db
def test_el_stock_inicial_sale_de_la_configuracion(correo):
    """Es el único stock del sistema que nace con un número que nadie contó, y
    por eso el de las altas manuales es cero y este no (A3)."""
    configuracion = ConfiguracionSistema.obtener()
    configuracion.stock_inicial_por_defecto = 3
    configuracion.save()

    borrador = generar(correo, extraccion()).creados[0]

    assert borrador.stock_inicial == 3


@pytest.mark.django_db
def test_el_borrador_guarda_de_que_correo_y_proveedor_salio(correo, proveedor):
    borrador = generar(correo, extraccion()).creados[0]

    assert borrador.correo == correo
    assert borrador.proveedor == proveedor


# ---------------------------------------------------------------------------
# Paso 5 — duplicados
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_un_producto_que_ya_esta_en_el_catalogo_se_omite(correo, editorial, tipo):
    ya_cargado = ProductoFactory(isbn=BERSERK, editorial=editorial, tipo=tipo)

    resultado = generar(correo, extraccion())

    assert resultado.creados == []
    assert len(resultado.duplicados) == 1
    omitido = resultado.duplicados[0]
    assert omitido.producto_existente == ya_cargado.pk
    assert omitido.motivo_legible == "Ya está en el catálogo"


@pytest.mark.django_db
def test_el_duplicado_se_detecta_por_isbn_aunque_el_titulo_este_escrito_distinto(
    correo, editorial, tipo
):
    """Es justamente lo que la tupla no atrapa: el mismo tomo anunciado como
    "Berserk edición deluxe vol. 5" en vez de "Berserk Deluxe 5" (A19)."""
    ProductoFactory(isbn=BERSERK, titulo="Berserk edición deluxe", editorial=editorial, tipo=tipo)

    resultado = generar(correo, extraccion())

    assert resultado.creados == []
    assert len(resultado.duplicados) == 1


@pytest.mark.django_db
def test_el_duplicado_se_detecta_por_la_tupla_cuando_no_hay_isbn(correo, editorial, tipo):
    formato = FormatoFactory(nombre="Tapa dura")
    ProductoFactory(
        titulo="Berserk Deluxe",
        volumen=5,
        editorial=editorial,
        tipo=tipo,
        formato=formato,
        isbn="",
    )

    resultado = generar(correo, extraccion([extraido(isbn="")]))

    assert resultado.creados == []
    assert len(resultado.duplicados) == 1


@pytest.mark.django_db
def test_un_duplicado_no_frena_a_los_demas_productos_del_correo(correo, editorial, tipo):
    """Una exclusión esperada no es un fallo transaccional: es la misma regla
    con la que un duplicado no aborta el alta en lote de CU-ALT-NAC."""
    ProductoFactory(isbn=BERSERK, editorial=editorial, tipo=tipo)

    resultado = generar(
        correo,
        extraccion(
            [
                extraido(),
                extraido(titulo="Blue Period", volumen=12, isbn=BLUE_PERIOD),
            ]
        ),
    )

    assert len(resultado.creados) == 1
    assert resultado.creados[0].titulo == "Blue Period"
    assert len(resultado.duplicados) == 1


# ---------------------------------------------------------------------------
# El repetido dentro del mismo correo (A11, llevado del formulario al correo)
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_dos_filas_con_el_mismo_isbn_generan_un_solo_borrador(correo):
    """Son el mismo tomo aunque les hayan escrito el título distinto."""
    resultado = generar(
        correo,
        extraccion([extraido(), extraido(titulo="Berserk edición deluxe")]),
    )

    assert len(resultado.creados) == 1
    assert len(resultado.omitidos) == 1
    assert resultado.omitidos[0].motivo == borradores.REPETIDO_EN_EL_CORREO


@pytest.mark.django_db
def test_se_omite_el_segundo_repetido_y_no_los_dos(correo):
    """Marcar los dos obligaría a adivinar cuál había que conservar."""
    resultado = generar(
        correo,
        extraccion([extraido(precio="24900"), extraido(precio="99999")]),
    )

    assert len(resultado.creados) == 1
    # El que quedó es el primero, con su precio.
    assert resultado.creados[0].precio == Decimal("24900")


@pytest.mark.django_db
def test_dos_filas_sin_isbn_y_con_la_misma_tupla_tambien_se_detectan(correo):
    resultado = generar(
        correo,
        extraccion([extraido(isbn=""), extraido(isbn="")]),
    )

    assert len(resultado.creados) == 1
    assert resultado.omitidos[0].motivo == borradores.REPETIDO_EN_EL_CORREO


@pytest.mark.django_db
def test_dos_tomos_distintos_de_la_misma_serie_no_son_repetidos(correo):
    """Comparar solo el título rechazaría el tomo 6 porque ya está el 5."""
    resultado = generar(
        correo,
        extraccion([extraido(volumen=5, isbn=BERSERK), extraido(volumen=6, isbn="")]),
    )

    assert len(resultado.creados) == 2


@pytest.mark.django_db
def test_un_producto_sin_titulo_no_llega_a_la_cola(correo):
    """Un borrador sin título solo se podría rechazar: no hay con qué buscarlo
    ni con qué mostrarlo."""
    resultado = generar(correo, extraccion([extraido(titulo="")]))

    assert resultado.creados == []
    assert resultado.omitidos[0].motivo == borradores.SIN_TITULO


# ---------------------------------------------------------------------------
# Paso 6 — el estado se deriva de la fecha
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_una_fecha_futura_deja_el_borrador_en_pre_venta(correo):
    futura = timezone.localdate() + timedelta(days=30)

    borrador = generar(correo, extraccion(periodo=futura.isoformat())).creados[0]

    assert borrador.estado_sugerido == Producto.PRE_VENTA
    assert borrador.fecha_llegada == futura
    assert borrador.nace_en_pre_venta


@pytest.mark.django_db
def test_sin_fecha_el_borrador_nace_activo(correo):
    borrador = generar(correo, extraccion()).creados[0]

    assert borrador.estado_sugerido == Producto.ACTIVO
    assert borrador.fecha_llegada is None


@pytest.mark.django_db
def test_una_fecha_ya_pasada_no_se_conserva(correo):
    """Si el material ya llegó, el producto va Activo y sin fecha (A10).
    Arrastrarla dejaría un activo con fecha de llegada del mes pasado, que no
    significa nada y ensucia la vigilancia de pre-ventas de CU-ALT-TRA."""
    pasada = timezone.localdate() - timedelta(days=30)

    borrador = generar(correo, extraccion(periodo=pasada.isoformat())).creados[0]

    assert borrador.estado_sugerido == Producto.ACTIVO
    assert borrador.fecha_llegada is None
    # Pero queda dicho, porque el correo sí anunciaba una fecha.
    assert any("ya pasó" in reparo for reparo in borrador.reparos)


@pytest.mark.django_db
def test_la_fecha_propia_de_una_fila_pisa_al_periodo_del_correo(correo):
    futura = timezone.localdate() + timedelta(days=60)
    periodo = timezone.localdate() + timedelta(days=10)

    resultado = generar(
        correo,
        extraccion([extraido(fecha=futura.isoformat())], periodo=periodo.isoformat()),
    )

    assert resultado.creados[0].fecha_llegada == futura


@pytest.mark.django_db
def test_una_pre_venta_siempre_tiene_fecha(correo):
    """A10: sin fecha no se puede vigilar, y el producto quedaría en pre-venta
    para siempre, invisible para el ciclo que debería sacarlo de ahí."""
    futura = timezone.localdate() + timedelta(days=30)

    borrador = generar(correo, extraccion(periodo=futura.isoformat())).creados[0]

    assert borrador.nace_en_pre_venta
    assert borrador.fecha_llegada is not None
    assert "fecha_llegada" not in borrador.campos_bloqueantes_vacios


# ---------------------------------------------------------------------------
# El formato: A12 y A20 valen igual acá que en el alta manual
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_el_formato_anunciado_se_resuelve_contra_el_catalogo(correo, tipo):
    formato = FormatoFactory(nombre="Tapa dura")

    borrador = generar(correo, extraccion()).creados[0]

    assert borrador.formato == formato


@pytest.mark.django_db
def test_un_formato_que_no_existe_se_descarta_con_su_reparo(correo):
    borrador = generar(correo, extraccion([extraido(formato="Formato inventado")])).creados[0]

    assert borrador.formato is None
    assert any("Formato descartado" in reparo for reparo in borrador.reparos)


@pytest.mark.django_db
def test_un_formato_que_no_se_ofrece_para_ese_tipo_se_descarta(correo, tipo):
    """A20: un formato enviado a mano que no aplique se rechaza. Que venga del
    modelo en vez de del navegador no lo hace más confiable."""
    otro_tipo = TipoFactory(nombre="Cómic")
    formato = FormatoFactory(nombre="Tapa dura")
    formato.tipos.set([otro_tipo])

    borrador = generar(correo, extraccion()).creados[0]

    assert borrador.formato is None
    assert any("no se ofrece" in reparo for reparo in borrador.reparos)


@pytest.mark.django_db
def test_en_un_tipo_que_no_usa_formato_no_se_busca_ninguno(correo, proveedor):
    """En un artbook el tamaño no fija el precio, así que no hay nada que
    resolver y tampoco nada que reparar."""
    proveedor.tipo_por_defecto = TipoFactory(nombre="Artbook", usa_formato=False)
    proveedor.save()

    borrador = generar(correo, extraccion()).creados[0]

    assert borrador.formato is None
    assert borrador.reparos == []


# ---------------------------------------------------------------------------
# Los borradores incompletos
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_un_producto_sin_precio_genera_un_borrador_incompleto(correo):
    """CU-ALT-NOV: los que el modelo identificó pero no pudo completar generan
    borradores incompletos, y van a la **misma** cola que los demás."""
    resultado = generar(correo, extraccion([extraido(precio="")]))

    borrador = resultado.creados[0]
    assert borrador.estado == BorradorProducto.INCOMPLETO
    assert "precio" in borrador.campos_bloqueantes_vacios
    assert borrador in BorradorProducto.objects.pendientes()


@pytest.mark.django_db
def test_el_fallo_parcial_deja_completos_e_incompletos_en_la_misma_cola(correo):
    resultado = generar(
        correo,
        extraccion(
            [
                extraido(),
                extraido(titulo="Blue Period", volumen=12, isbn=BLUE_PERIOD, precio=""),
            ]
        ),
    )

    assert len(resultado.creados) == 2
    assert len(resultado.incompletos) == 1
    assert BorradorProducto.objects.pendientes().count() == 2


@pytest.mark.django_db
def test_un_proveedor_sin_editorial_deja_los_borradores_bloqueados(correo, proveedor):
    """Una distribuidora trae varias editoriales y el correo no dice cuál: esos
    borradores sí hay que completarlos a mano, y el estado lo dice."""
    proveedor.editorial = None
    proveedor.save()

    borrador = generar(correo, extraccion()).creados[0]

    assert borrador.estado == BorradorProducto.INCOMPLETO
    assert "editorial" in borrador.campos_bloqueantes_vacios


# ---------------------------------------------------------------------------
# La confianza por campo
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_la_confianza_se_guarda_campo_por_campo(correo):
    """CU-ALT-REV depende de esa granularidad para decidir qué es confirmable en
    lote: un único nivel global no alcanzaría."""
    confianza = dict(CONFIANZA_ALTA, precio="baja", volumen="media")

    borrador = generar(correo, extraccion([extraido(confianza=confianza)])).creados[0]

    guardadas = {c.campo: c.nivel for c in borrador.confianzas.all()}
    assert guardadas["precio"] == ConfianzaCampo.BAJA
    assert guardadas["volumen"] == ConfianzaCampo.MEDIA
    assert guardadas["titulo"] == ConfianzaCampo.ALTA


@pytest.mark.django_db
def test_una_confianza_baja_nace_sin_revisar(correo):
    """Es la acción afirmativa que CU-ALT-REV paso 3 exige antes de confirmar."""
    confianza = dict(CONFIANZA_ALTA, precio="baja")

    borrador = generar(correo, extraccion([extraido(confianza=confianza)])).creados[0]

    pendientes = borrador.confianzas_bajas_sin_revisar
    assert [c.campo for c in pendientes] == ["precio"]
    assert pendientes[0].exige_revision


@pytest.mark.django_db
def test_una_confianza_alta_no_exige_revision(correo):
    borrador = generar(correo, extraccion()).creados[0]

    assert borrador.confianzas_bajas_sin_revisar == []


@pytest.mark.django_db
def test_un_nivel_inventado_se_guarda_como_bajo(correo):
    """Al alza sería peor: un valor raro leído como "alta" haría que un dato
    dudoso se confirme en lote sin que nadie lo mire."""
    confianza = dict(CONFIANZA_ALTA, precio="altísima")

    borrador = generar(correo, extraccion([extraido(confianza=confianza)])).creados[0]

    assert borrador.confianzas.get(campo="precio").nivel == ConfianzaCampo.BAJA


# ---------------------------------------------------------------------------
# Los reparos: lo que el sistema le corrigió al modelo
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_los_reparos_del_producto_viajan_al_borrador(correo):
    reparo = "ISBN descartado («9789878271584»): dígito de control inválido."

    borrador = generar(correo, extraccion([extraido(isbn="", reparos=[reparo])])).creados[0]

    assert reparo in borrador.reparos


@pytest.mark.django_db
def test_un_reparo_del_correo_entero_se_copia_a_cada_borrador(correo):
    """La cola de CU-ALT-REV se mira de a un borrador por vez: un reparo que solo
    viviera en el correo no lo vería nadie desde ahí."""
    reparo = "Período ilegible: «cuando salga». Los borradores nacen sin fecha."

    resultado = generar(
        correo,
        extraccion(
            [extraido(), extraido(titulo="Blue Period", volumen=12, isbn=BLUE_PERIOD)],
            reparos=[reparo],
        ),
    )

    assert all(reparo in borrador.reparos for borrador in resultado.creados)


# ---------------------------------------------------------------------------
# Regenerar
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_regenerar_reemplaza_los_borradores_abiertos_en_vez_de_duplicarlos(correo):
    generar(correo, extraccion())
    generar(correo, extraccion())

    assert BorradorProducto.objects.filter(correo=correo).count() == 1


@pytest.mark.django_db
def test_regenerar_conserva_los_ya_resueltos(correo):
    """Son historia: volver a proponerlos sería reabrir una decisión tomada."""
    primero = generar(correo, extraccion()).creados[0]
    primero.estado = BorradorProducto.RECHAZADO
    primero.motivo_rechazo = "No lo vamos a traer."
    primero.save()

    generar(correo, extraccion())

    assert BorradorProducto.objects.filter(correo=correo).count() == 2
    primero.refresh_from_db()
    assert primero.estado == BorradorProducto.RECHAZADO


# ---------------------------------------------------------------------------
# Paso 9 — auditoría
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_la_generacion_deja_una_sola_entrada_de_auditoria(correo, editorial, tipo):
    """Consolidada por correo, no una por borrador: lo que se quiere reconstruir
    después es qué produjo este correo, y treinta filas lo esconderían."""
    ProductoFactory(isbn=BLUE_PERIOD, editorial=editorial, tipo=tipo)

    generar(
        correo,
        extraccion(
            [
                extraido(),
                extraido(titulo="Blue Period", volumen=12, isbn=BLUE_PERIOD),
            ]
        ),
    )

    registros = RegistroAuditoria.objects.filter(accion=RegistroAuditoria.BORRADORES_GENERADOS)
    assert registros.count() == 1
    detalle = registros.get().detalle
    assert "1 borrador(es) generado(s)" in detalle
    assert "1 omitido(s) por duplicado" in detalle


@pytest.mark.django_db
def test_la_auditoria_apunta_al_correo_y_dice_con_que_prompt_se_extrajo(correo):
    generar(correo, extraccion())

    registro = RegistroAuditoria.objects.get(accion=RegistroAuditoria.BORRADORES_GENERADOS)
    assert registro.objetivo == correo
    assert "prompt v2" in registro.detalle


@pytest.mark.django_db
def test_la_auditoria_registra_al_administrador_cuando_lo_hay(correo, administrador):
    generar(correo, extraccion(), actor=administrador)

    registro = RegistroAuditoria.objects.get(accion=RegistroAuditoria.BORRADORES_GENERADOS)
    assert registro.actor == administrador


@pytest.mark.django_db
def test_la_fecha_heredada_del_periodo_no_lleva_confianza(correo):
    """Salió corriendo el pipeline contra el modelo de verdad, y es grave.

    Una fila de novedades casi nunca trae fecha propia —el período lo anuncia el
    correo entero—, así que el modelo declara "baja" correctamente sobre esa
    celda vacía. Si esa confianza se guardara, la confirmación en lote de CU-ALT-REV
    —que excluye a todo borrador con algún campo de confianza baja— dejaría
    **ningún borrador confirmable en lote nunca**, que es justo el trabajo que el
    pipeline venía a eliminar.
    """
    from datetime import timedelta

    futura = timezone.localdate() + timedelta(days=30)
    confianza = dict(CONFIANZA_ALTA, fecha="baja")

    borrador = generar(
        correo,
        extraccion([extraido(confianza=confianza)], periodo=futura.isoformat()),
    ).creados[0]

    assert borrador.fecha_llegada == futura
    assert not borrador.confianzas.filter(campo="fecha").exists()
    # Y por lo tanto es confirmable en lote, que es el punto.
    assert borrador.confianzas_bajas_sin_revisar == []


@pytest.mark.django_db
def test_la_fecha_propia_de_una_fila_si_lleva_confianza(correo):
    """Ahí sí hay un juicio del modelo que registrar: leyó una celda y dudó."""
    from datetime import timedelta

    futura = timezone.localdate() + timedelta(days=30)
    confianza = dict(CONFIANZA_ALTA, fecha="baja")

    borrador = generar(
        correo,
        extraccion([extraido(fecha=futura.isoformat(), confianza=confianza)]),
    ).creados[0]

    assert borrador.confianzas.get(campo="fecha").nivel == ConfianzaCampo.BAJA
    assert [c.campo for c in borrador.confianzas_bajas_sin_revisar] == ["fecha"]


@pytest.mark.django_db
def test_sin_ninguna_fecha_tampoco_se_guarda_confianza_de_fecha(correo):
    """Un borrador Activo sin fecha no tiene nada que revisar sobre ella: la
    fecha ni siquiera es bloqueante ahí."""
    borrador = generar(
        correo, extraccion([extraido(confianza=dict(CONFIANZA_ALTA, fecha="baja"))])
    ).creados[0]

    assert borrador.fecha_llegada is None
    assert not borrador.confianzas.filter(campo="fecha").exists()
