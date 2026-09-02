"""Las pantallas de la revisión de borradores (CU-05).

Las reglas se prueban en `test_revision_borradores.py`. Acá está lo que solo
existe en la pantalla: que la cola diferencie visualmente lo que el CU pide
diferenciar, que la acción afirmativa sobre cada campo de confianza baja **se
valide en el servidor** y no escondiendo un botón (RNF-03), y que las exclusiones
de la confirmación en lote se informen en vez de desaparecer.
"""

from decimal import Decimal

import pytest
from django.core import mail
from django.urls import reverse

from apps.catalog.models import BorradorProducto, ConfianzaCampo, Producto
from apps.catalog.tests.factories import EditorialFactory, TipoFactory
from apps.suppliers.models import CorreoProveedor
from apps.suppliers.tests.factories import ProveedorFactory

pytestmark = pytest.mark.django_db

LISTA = reverse("catalog:borrador_lista")
EN_LOTE = reverse("catalog:borrador_confirmar_lote")
CERRAR = reverse("catalog:cerrar_sesion_revision")


@pytest.fixture
def proveedor(db):
    return ProveedorFactory(
        editorial=EditorialFactory(nombre="Ivrea"),
        tipo_por_defecto=TipoFactory(nombre="Manga", usa_formato=True),
    )


@pytest.fixture
def correo(db, proveedor):
    return CorreoProveedor.objects.create(
        proveedor=proveedor,
        message_id="<uno@ivrea.test>",
        remitente=proveedor.correo_comercial,
        estado=CorreoProveedor.PROCESADO,
    )


def borrador_de(correo, **cambios):
    datos = {
        "correo": correo,
        "proveedor": correo.proveedor,
        "titulo": "Berserk Deluxe",
        "volumen": 5,
        "editorial": correo.proveedor.editorial,
        "tipo": correo.proveedor.tipo_por_defecto,
        "precio": Decimal("24900"),
        "stock_inicial": 2,
        "estado_sugerido": Producto.ACTIVO,
    }
    datos.update(cambios)
    return BorradorProducto.objects.create(**datos)


def ficha(borrador):
    return reverse("catalog:borrador_detalle", args=[borrador.pk])


def campos_de(borrador, **cambios):
    """El POST de la ficha, con los campos ya cargados."""
    datos = {
        "titulo": borrador.titulo,
        "volumen": borrador.volumen or "",
        "isbn": borrador.isbn,
        "editorial": borrador.editorial_id or "",
        "tipo": borrador.tipo_id or "",
        "formato": borrador.formato_id or "",
        "precio": borrador.precio if borrador.precio is not None else "",
        "fecha_llegada": borrador.fecha_llegada or "",
        "estado_sugerido": borrador.estado_sugerido,
        "stock_inicial": borrador.stock_inicial,
        "autor": borrador.autor,
        "sinopsis": borrador.sinopsis,
    }
    datos.update(cambios)
    return datos


# ---------------------------------------------------------------------------
# La cola
# ---------------------------------------------------------------------------


def test_la_cola_lista_los_borradores_pendientes(client_admin, correo):
    borrador_de(correo)

    contenido = client_admin.get(LISTA).content.decode()

    assert "Berserk Deluxe" in contenido


def test_la_cola_vacia_lo_dice_y_apunta_a_donde_se_generan(client_admin, correo):
    """Sin borradores pendientes: informa y no presenta nada (excepción del CU)."""
    contenido = client_admin.get(LISTA).content.decode()

    assert "No hay borradores pendientes" in contenido


def test_la_cola_distingue_incompletos_de_confianza_baja(client_admin, correo):
    """No son lo mismo y no se arreglan igual: al incompleto le falta un dato,
    al dudoso hay que mirarle uno que ya está."""
    borrador_de(correo, titulo="Sin precio", precio=None, estado=BorradorProducto.INCOMPLETO)
    dudoso = borrador_de(correo, titulo="Dudoso", volumen=6)
    ConfianzaCampo.objects.create(borrador=dudoso, campo="precio", nivel=ConfianzaCampo.BAJA)

    contenido = client_admin.get(LISTA).content.decode()

    assert "Incompleto" in contenido
    assert "Confianza baja" in contenido


def test_solo_se_puede_seleccionar_lo_que_el_lote_va_a_confirmar(client_admin, correo):
    """Ofrecer la casilla en un incompleto sería invitar a un clic que termina
    en una advertencia."""
    listo = borrador_de(correo, titulo="Listo")
    incompleto = borrador_de(
        correo, titulo="Incompleto", volumen=6, precio=None, estado=BorradorProducto.INCOMPLETO
    )

    contenido = client_admin.get(LISTA).content.decode()

    assert f'value="{listo.pk}"' in contenido
    assert f'value="{incompleto.pk}"' not in contenido


def test_la_cola_no_muestra_una_sesion_hasta_que_haya_una_accion(client_admin, correo):
    borrador_de(correo)

    contenido = client_admin.get(LISTA).content.decode()

    assert "Ninguna en curso" in contenido


def test_el_buscador_filtra_por_titulo(client_admin, correo):
    borrador_de(correo, titulo="Berserk Deluxe")
    borrador_de(correo, titulo="Blue Period", volumen=12)

    contenido = client_admin.get(LISTA, {"q": "Blue"}).content.decode()

    assert "Blue Period" in contenido
    assert "Berserk" not in contenido


# ---------------------------------------------------------------------------
# La ficha: editar, confirmar, rechazar
# ---------------------------------------------------------------------------


def test_la_ficha_muestra_los_reparos_del_borrador(client_admin, correo):
    borrador = borrador_de(correo, reparos=["ISBN descartado: no verifica."])

    contenido = client_admin.get(ficha(borrador)).content.decode()

    assert "ISBN descartado" in contenido


def test_guardar_sin_confirmar_deja_el_borrador_en_la_cola(client_admin, correo):
    borrador = borrador_de(correo)

    client_admin.post(ficha(borrador), campos_de(borrador, titulo="Corregido", guardar="1"))

    borrador.refresh_from_db()
    assert borrador.titulo == "Corregido"
    assert borrador.esta_abierto
    assert Producto.objects.count() == 0


def test_confirmar_desde_la_ficha_crea_el_producto(client_admin, correo):
    borrador = borrador_de(correo)

    client_admin.post(ficha(borrador), campos_de(borrador, confirmar="1"))

    borrador.refresh_from_db()
    assert borrador.estado == BorradorProducto.CONFIRMADO
    assert Producto.objects.count() == 1


def test_el_titulo_editado_es_el_que_llega_al_producto(client_admin, correo):
    borrador = borrador_de(correo)

    client_admin.post(
        ficha(borrador), campos_de(borrador, titulo="Berserk edición deluxe", confirmar="1")
    )

    assert Producto.objects.get().titulo == "Berserk edición deluxe"


def test_un_isbn_mal_escrito_a_mano_se_rechaza(client_admin, correo):
    """El pipeline ya lo verifica al extraer, pero acá lo escribe una persona:
    es exactamente el momento del error de transcripción (A19)."""
    borrador = borrador_de(correo)

    respuesta = client_admin.post(
        ficha(borrador), campos_de(borrador, isbn="9789878271584", confirmar="1")
    )

    assert respuesta.status_code == 200
    assert Producto.objects.count() == 0
    borrador.refresh_from_db()
    assert borrador.esta_abierto


def test_una_pre_venta_sin_fecha_no_se_puede_guardar(client_admin, correo):
    borrador = borrador_de(correo)

    respuesta = client_admin.post(
        ficha(borrador),
        campos_de(borrador, estado_sugerido=Producto.PRE_VENTA, fecha_llegada="", confirmar="1"),
    )

    assert respuesta.status_code == 200
    assert "fecha de llegada" in respuesta.content.decode().lower()
    assert Producto.objects.count() == 0


def test_rechazar_sin_motivo_no_descarta_nada(client_admin, correo):
    borrador = borrador_de(correo)

    respuesta = client_admin.post(ficha(borrador), {"rechazar": "1", "motivo": "   "})

    assert respuesta.status_code == 200
    borrador.refresh_from_db()
    assert borrador.esta_abierto


def test_rechazar_con_motivo_descarta_el_borrador(client_admin, correo):
    borrador = borrador_de(correo)

    client_admin.post(ficha(borrador), {"rechazar": "1", "motivo": "No lo vamos a traer."})

    borrador.refresh_from_db()
    assert borrador.estado == BorradorProducto.RECHAZADO
    assert borrador.motivo_rechazo == "No lo vamos a traer."


def test_un_borrador_ya_resuelto_no_se_vuelve_a_resolver(client_admin, correo, administrador):
    """El doble envío del formulario es el caso normal, no el raro."""
    borrador = borrador_de(correo)
    client_admin.post(ficha(borrador), campos_de(borrador, confirmar="1"))

    client_admin.post(ficha(borrador), {"rechazar": "1", "motivo": "Otra cosa."})

    borrador.refresh_from_db()
    assert borrador.estado == BorradorProducto.CONFIRMADO
    assert Producto.objects.count() == 1


def test_la_ficha_de_un_borrador_resuelto_no_ofrece_acciones(client_admin, correo):
    borrador = borrador_de(correo)
    client_admin.post(ficha(borrador), campos_de(borrador, confirmar="1"))

    contenido = client_admin.get(ficha(borrador)).content.decode()

    assert "Ya resuelto" in contenido
    assert "Confirmar y agregar al catálogo" not in contenido


# ---------------------------------------------------------------------------
# La acción afirmativa sobre la confianza baja (CU-05 paso 3)
# ---------------------------------------------------------------------------


def test_la_ficha_pide_la_casilla_por_cada_campo_de_confianza_baja(client_admin, correo):
    borrador = borrador_de(correo)
    ConfianzaCampo.objects.create(borrador=borrador, campo="precio", nivel=ConfianzaCampo.BAJA)

    contenido = client_admin.get(ficha(borrador)).content.decode()

    assert 'name="revisado"' in contenido
    assert "confianza baja" in contenido


def test_confirmar_sin_revisar_la_confianza_baja_se_bloquea(client_admin, correo):
    """Se valida en el servidor y no escondiendo el botón: un POST armado a mano
    confirmaría igual un dato que nadie miró (RNF-03)."""
    borrador = borrador_de(correo)
    ConfianzaCampo.objects.create(borrador=borrador, campo="precio", nivel=ConfianzaCampo.BAJA)

    client_admin.post(ficha(borrador), campos_de(borrador, confirmar="1"))

    assert Producto.objects.count() == 0
    borrador.refresh_from_db()
    assert borrador.esta_abierto


def test_confirmar_marcando_la_casilla_funciona(client_admin, correo):
    borrador = borrador_de(correo)
    ConfianzaCampo.objects.create(borrador=borrador, campo="precio", nivel=ConfianzaCampo.BAJA)

    client_admin.post(ficha(borrador), campos_de(borrador, confirmar="1", revisado="precio"))

    assert Producto.objects.count() == 1


def test_revisar_un_campo_y_no_el_otro_sigue_bloqueando(client_admin, correo):
    """La acción es por campo, no un "revisé este borrador" genérico."""
    borrador = borrador_de(correo)
    ConfianzaCampo.objects.create(borrador=borrador, campo="precio", nivel=ConfianzaCampo.BAJA)
    ConfianzaCampo.objects.create(borrador=borrador, campo="titulo", nivel=ConfianzaCampo.BAJA)

    client_admin.post(ficha(borrador), campos_de(borrador, confirmar="1", revisado="precio"))

    assert Producto.objects.count() == 0


def test_la_marca_de_revisado_se_puede_retirar(client_admin, correo):
    """Dejar la marca puesta haría que un dato vuelto a poner en duda siguiera
    contando como mirado."""
    borrador = borrador_de(correo)
    confianza = ConfianzaCampo.objects.create(
        borrador=borrador, campo="precio", nivel=ConfianzaCampo.BAJA, revisado=True
    )

    client_admin.post(ficha(borrador), campos_de(borrador, guardar="1"))

    confianza.refresh_from_db()
    assert confianza.revisado is False


# ---------------------------------------------------------------------------
# Confirmación en lote
# ---------------------------------------------------------------------------


def test_el_lote_confirma_los_seleccionados(client_admin, correo):
    uno = borrador_de(correo, titulo="Uno", volumen=1)
    dos = borrador_de(correo, titulo="Dos", volumen=2)

    client_admin.post(EN_LOTE, {"borrador": [uno.pk, dos.pk]})

    assert Producto.objects.count() == 2


def test_el_lote_informa_lo_que_excluyo(client_admin, correo):
    """Se informa la exclusión: sin eso, el borrador que quedó afuera
    desaparecería de la vista sin explicación."""
    dudoso = borrador_de(correo, titulo="Dudoso", volumen=1)
    ConfianzaCampo.objects.create(borrador=dudoso, campo="precio", nivel=ConfianzaCampo.BAJA)
    sano = borrador_de(correo, titulo="Sano", volumen=2)

    respuesta = client_admin.post(EN_LOTE, {"borrador": [dudoso.pk, sano.pk]}, follow=True)

    contenido = respuesta.content.decode()
    assert "confianza baja sin revisar" in contenido
    assert Producto.objects.count() == 1
    dudoso.refresh_from_db()
    assert dudoso.esta_abierto


def test_el_lote_sin_seleccion_no_hace_nada(client_admin, correo):
    borrador_de(correo)

    respuesta = client_admin.post(EN_LOTE, {}, follow=True)

    assert "No se seleccionó ningún borrador" in respuesta.content.decode()
    assert Producto.objects.count() == 0


# ---------------------------------------------------------------------------
# El cierre de la sesión
# ---------------------------------------------------------------------------


def test_cerrar_manda_el_pedido_y_lo_informa(client_admin, correo):
    borrador = borrador_de(correo)
    client_admin.post(ficha(borrador), campos_de(borrador, confirmar="1"))
    mail.outbox.clear()

    respuesta = client_admin.post(CERRAR, follow=True)

    assert len(mail.outbox) == 1
    assert "1 pedido(s) de reposición" in respuesta.content.decode()


def test_cerrar_sin_sesion_en_curso_lo_dice(client_admin, correo):
    respuesta = client_admin.post(CERRAR, follow=True)

    assert "No hay ninguna sesión de revisión en curso" in respuesta.content.decode()
    assert mail.outbox == []


def test_cerrar_una_sesion_de_solo_rechazos_no_manda_pedidos(client_admin, correo):
    borrador = borrador_de(correo)
    client_admin.post(ficha(borrador), {"rechazar": "1", "motivo": "No va."})
    mail.outbox.clear()

    respuesta = client_admin.post(CERRAR, follow=True)

    assert mail.outbox == []
    assert "sin confirmaciones" in respuesta.content.decode()


def test_la_cola_muestra_la_sesion_en_curso(client_admin, correo, administrador):
    borrador = borrador_de(correo)
    client_admin.post(ficha(borrador), campos_de(borrador, confirmar="1"))

    contenido = client_admin.get(LISTA).content.decode()

    assert "Cerrar la revisión y pedir" in contenido


# ---------------------------------------------------------------------------
# Permisos (RNF-03)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("rol", ["cliente", "cajero"])
def test_las_pantallas_son_solo_del_administrador(client, correo, rol):
    from apps.accounts.tests.factories import UsuarioFactory

    client.force_login(UsuarioFactory(rol=rol))
    borrador = borrador_de(correo)

    assert client.get(LISTA).status_code == 403
    assert client.get(ficha(borrador)).status_code == 403
    assert client.post(EN_LOTE, {"borrador": [borrador.pk]}).status_code == 403
    assert client.post(CERRAR).status_code == 403
    assert Producto.objects.count() == 0


def test_el_menu_enlaza_la_revision(client_admin):
    contenido = client_admin.get(LISTA).content.decode()

    assert "Revisar borradores" in contenido


def test_confirmar_desde_la_pantalla_deja_al_producto_atado_a_su_proveedor(
    client_admin, correo, proveedor
):
    borrador = borrador_de(correo)

    client_admin.post(ficha(borrador), campos_de(borrador, confirmar="1"))

    assert Producto.objects.get().proveedor == proveedor


def test_la_ficha_avisa_si_el_producto_ya_esta_en_el_catalogo(client_admin, correo):
    """Salió de correr el pipeline sobre dos correos que anunciaban los mismos
    tomos: los borradores del segundo quedaban en la cola sin ninguna marca, y la
    única forma de enterarse era apretar «confirmar» y recibir el rechazo. Es la
    misma cortesía que CU-01 E1 le da a los duplicados del alta en lote."""
    from apps.catalog.tests.factories import ProductoFactory

    ya_cargado = ProductoFactory(
        titulo="Berserk Deluxe",
        volumen=5,
        editorial=correo.proveedor.editorial,
        tipo=correo.proveedor.tipo_por_defecto,
        formato=None,
        isbn="",
    )
    borrador = borrador_de(correo)

    contenido = client_admin.get(ficha(borrador)).content.decode()

    assert "ya está en el catálogo" in contenido
    assert reverse("catalog:producto_detalle", args=[ya_cargado.pk]) in contenido


def test_un_borrador_sin_duplicado_no_lleva_ese_aviso(client_admin, correo):
    borrador = borrador_de(correo)

    contenido = client_admin.get(ficha(borrador)).content.decode()

    assert "ya está en el catálogo" not in contenido


def test_la_ficha_de_un_confirmado_no_se_avisa_a_si_misma(client_admin, correo):
    """El "duplicado" de un borrador confirmado sería el producto que él mismo
    creó, y avisarlo sería absurdo."""
    borrador = borrador_de(correo)
    client_admin.post(ficha(borrador), campos_de(borrador, confirmar="1"))

    contenido = client_admin.get(ficha(borrador)).content.decode()

    assert "ya está en el catálogo" not in contenido
