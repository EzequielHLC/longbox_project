"""Pruebas de contrato de las ofertas (módulo 03, plan 03 segunda parte).

`CO-054` a `CO-059`, `CO-168` a `CO-170` y `CO-156` en la baja. Zona de foco
reforzado (dinero): aritmética decimal exacta, ramas de error y postcondiciones
negativas. El precio guardado del producto no cambia nunca: lo que cambia es el
precio visible, en la tienda y en el carrito.

Las fechas son relativas a hoy: congelar el reloj vencería la sesión del
Administrador, que se abrió con el reloj real.
"""

from datetime import timedelta
from decimal import Decimal
from io import StringIO

import pytest
from django.core.management import call_command
from django.urls import reverse
from django.utils import timezone

from apps.catalog import ofertas
from apps.catalog.models import Oferta, Producto
from apps.catalog.precio_visible import precio_visible
from apps.catalog.tests.factories import ProductoFactory, TipoFactory
from apps.core.models import RegistroAuditoria
from apps.tienda.models import Carrito, LineaCarrito

pytestmark = pytest.mark.django_db

URL_LISTA = reverse("catalog:oferta_lista")
URL_ALTA = reverse("catalog:oferta_alta")


def hoy():
    return timezone.localdate()


def dias(n):
    return hoy() + timedelta(days=n)


def formulario(**cambios):
    datos = {
        "descripcion": "Semana del manga",
        "fecha_inicio": hoy().isoformat(),
        "fecha_vencimiento": dias(10).isoformat(),
        "tipo_descuento": Oferta.PORCENTAJE,
        "valor": "15",
        "alcance": Oferta.PRODUCTO,
        "producto": "",
        "tipo": "",
    }
    datos.update(cambios)
    return datos


def del_producto(producto, **cambios):
    return formulario(producto=f"{producto.codigo} — {producto.titulo}", **cambios)


def oferta(producto=None, tipo=None, **cambios):
    datos = {
        "descripcion": "Oferta existente",
        "fecha_inicio": hoy(),
        "fecha_vencimiento": dias(10),
        "tipo_descuento": Oferta.PORCENTAJE,
        "valor": Decimal("10"),
        "alcance": Oferta.PRODUCTO if producto else Oferta.TIPO,
        "producto": producto,
        "tipo": tipo,
        "estado": Oferta.ACTIVA,
    }
    datos.update(cambios)
    return Oferta.objects.create(**datos)


def en_carrito(producto, precio=None):
    precio = precio if precio is not None else producto.precio
    return LineaCarrito.objects.create(
        carrito=Carrito.objects.create(),
        producto=producto,
        cantidad=1,
        precio_vigente=precio,
        precio_visto=precio,
    )


def auditorias(accion):
    return RegistroAuditoria.objects.filter(accion=accion)


@pytest.fixture
def akira(db):
    return ProductoFactory(titulo="Akira", precio=Decimal("18500"), stock=4)


# ===========================================================================
# El precio visible
# ===========================================================================


def test_el_porcentaje_se_calcula_con_decimal_exacto_y_redondea_al_peso(akira):
    oferta(producto=akira, valor=Decimal("33.33"))

    # 18500 × 0,6667 = 12333,95: con punto flotante o redondeando el
    # porcentaje antes de multiplicar se pierde o se gana un peso.
    assert precio_visible(akira) == Decimal("12334.00")


def test_el_dia_de_vencimiento_todavia_descuenta(akira):
    oferta(producto=akira, fecha_inicio=dias(-5), fecha_vencimiento=hoy())

    assert precio_visible(akira) == Decimal("16650.00")
    assert precio_visible(akira, hoy=dias(1)) == Decimal("18500")


def test_la_oferta_individual_manda_sobre_la_de_su_tipo(akira):
    oferta(tipo=akira.tipo, valor=Decimal("50"))
    oferta(producto=akira, valor=Decimal("10"))

    assert precio_visible(akira) == Decimal("16650.00")


def test_una_oferta_dada_de_baja_no_descuenta(akira):
    oferta(producto=akira, estado=Oferta.DADA_DE_BAJA)

    assert precio_visible(akira) == Decimal("18500")


# ===========================================================================
# CO-054 · registrarOferta
# ===========================================================================


def test_CO054_registrar_con_inicio_hoy_la_deja_activa_y_aplicada_en_los_dos_canales(
    client_admin, administrador, akira
):
    linea = en_carrito(akira)

    respuesta = client_admin.post(URL_ALTA, del_producto(akira))

    nueva = Oferta.objects.get()
    assert respuesta.url == reverse("catalog:oferta_ficha", args=[nueva.pk])
    assert nueva.estado == Oferta.ACTIVA
    assert nueva.producto_id == akira.pk
    assert nueva.tipo is None
    assert (nueva.descripcion, nueva.tipo_descuento, nueva.valor) == (
        "Semana del manga",
        Oferta.PORCENTAJE,
        Decimal("15"),
    )
    assert (nueva.fecha_inicio, nueva.fecha_vencimiento) == (hoy(), dias(10))
    # Tienda: el precio visible lleva el descuento.
    ficha = client_admin.get(reverse("core:tienda_producto", args=[akira.pk])).content.decode()
    assert "$ 15.725" in ficha
    # Carrito: la línea quedó al día.
    linea.refresh_from_db()
    assert linea.precio_vigente == Decimal("15725")
    registro = auditorias(RegistroAuditoria.ALTA_OFERTA).get()
    assert registro.actor == administrador
    assert "«Semana del manga» · 15 % · Producto: Akira" in registro.detalle


def test_CO054_con_inicio_futuro_queda_programada_y_no_descuenta_todavia(client_admin, akira):
    linea = en_carrito(akira)

    client_admin.post(URL_ALTA, del_producto(akira, fecha_inicio=dias(3).isoformat()))

    assert Oferta.objects.get().estado == Oferta.PROGRAMADA
    assert precio_visible(akira) == Decimal("18500")
    linea.refresh_from_db()
    assert linea.precio_vigente == Decimal("18500")


def test_CO054_por_tipo_se_asocia_al_tipo_y_alcanza_a_sus_productos(client_admin, akira):
    otro = ProductoFactory(tipo=akira.tipo, precio=Decimal("10000"))

    client_admin.post(URL_ALTA, formulario(alcance=Oferta.TIPO, tipo=akira.tipo.pk))

    nueva = Oferta.objects.get()
    assert (nueva.tipo, nueva.producto) == (akira.tipo, None)
    assert precio_visible(otro) == Decimal("8500.00")


def test_CO054_no_toca_el_precio_guardado_del_producto(client_admin, akira):
    client_admin.post(URL_ALTA, del_producto(akira))

    akira.refresh_from_db()
    assert akira.precio == Decimal("18500")


@pytest.mark.parametrize("vencimiento", [0, -1])
def test_CO054_E1_el_vencimiento_tiene_que_ser_futuro(client_admin, akira, vencimiento):
    respuesta = client_admin.post(
        URL_ALTA, del_producto(akira, fecha_vencimiento=dias(vencimiento).isoformat())
    )

    assert not Oferta.objects.exists()
    contenido = respuesta.content.decode()
    assert "El vencimiento tiene que ser una fecha futura." in contenido
    # El formulario conserva lo ingresado.
    assert 'value="Semana del manga"' in contenido


def test_CO054_el_inicio_no_puede_pasar_al_vencimiento(client_admin, akira):
    client_admin.post(
        URL_ALTA,
        del_producto(
            akira, fecha_inicio=dias(5).isoformat(), fecha_vencimiento=dias(4).isoformat()
        ),
    )

    assert not Oferta.objects.exists()


def test_CO054_E2_rechaza_el_solapamiento_con_el_nombre_y_el_periodo(client_admin, akira):
    oferta(
        producto=akira, descripcion="Aniversario", fecha_inicio=dias(5), fecha_vencimiento=dias(20)
    )

    respuesta = client_admin.post(URL_ALTA, del_producto(akira))

    assert Oferta.objects.count() == 1
    periodo = f"del {dias(5):%d/%m/%Y} al {dias(10):%d/%m/%Y}"
    assert f"Se superpone con la oferta «Aniversario» {periodo}." in respuesta.content.decode()


def test_CO054_E2_no_cuentan_las_dadas_de_baja_ni_las_de_otro_alcance(client_admin, akira):
    oferta(producto=akira, estado=Oferta.DADA_DE_BAJA)
    oferta(tipo=akira.tipo)

    client_admin.post(URL_ALTA, del_producto(akira))

    assert Oferta.objects.count() == 3


def test_CO054_rechaza_un_porcentaje_de_cien(client_admin, akira):
    client_admin.post(URL_ALTA, del_producto(akira, valor="100"))

    assert not Oferta.objects.exists()


def test_CO054_E3_un_monto_que_supera_el_precio_pide_confirmacion_y_no_registra(
    client_admin, akira
):
    barato = ProductoFactory(tipo=akira.tipo, titulo="Fanzine", precio=Decimal("2000"))

    respuesta = client_admin.post(
        URL_ALTA,
        formulario(
            alcance=Oferta.TIPO, tipo=akira.tipo.pk, tipo_descuento=Oferta.MONTO_FIJO, valor="2000"
        ),
    )

    assert not Oferta.objects.exists()
    contenido = respuesta.content.decode()
    assert "El descuento supera el precio de 1 producto" in contenido
    assert barato.codigo in contenido
    assert "Confirmar con precio mínimo de $ 1" in contenido


def test_CO054_A1_un_tipo_sin_productos_registra_con_aviso(client_admin):
    vacio = TipoFactory()

    respuesta = client_admin.post(
        URL_ALTA, formulario(alcance=Oferta.TIPO, tipo=vacio.pk), follow=True
    )

    assert Oferta.objects.get().tipo == vacio
    assert "no tiene productos activos en este momento" in respuesta.content.decode()


# ===========================================================================
# CO-055 · confirmarOfertaConTopeMinimo
# ===========================================================================


def test_CO055_confirmar_registra_y_deja_en_un_peso_a_los_que_no_alcanzan(client_admin, akira):
    barato = ProductoFactory(tipo=akira.tipo, precio=Decimal("2000"))
    datos = formulario(
        alcance=Oferta.TIPO,
        tipo=akira.tipo.pk,
        tipo_descuento=Oferta.MONTO_FIJO,
        valor="2500",
        aceptar_tope="1",
    )

    client_admin.post(URL_ALTA, datos)

    assert Oferta.objects.get().estado == Oferta.ACTIVA
    assert precio_visible(barato) == Decimal("1.00")
    assert precio_visible(akira) == Decimal("16000.00")
    detalle = auditorias(RegistroAuditoria.ALTA_OFERTA).get().detalle
    assert "precio mínimo de $ 1 en 1 producto(s)" in detalle


# ===========================================================================
# CO-168 · abrirEdicionDeOferta y CO-056 · editarOferta
# ===========================================================================


def test_CO168_abre_con_los_campos_actuales(client_admin, akira):
    actual = oferta(producto=akira, descripcion="Aniversario")

    contenido = client_admin.get(
        reverse("catalog:oferta_editar", args=[actual.pk])
    ).content.decode()

    assert 'value="Aniversario"' in contenido
    assert akira.codigo in contenido


@pytest.mark.parametrize(
    "cambios",
    [
        {"estado": Oferta.DADA_DE_BAJA},
        {"fecha_inicio": dias(-10), "fecha_vencimiento": dias(-1), "estado": Oferta.ACTIVA},
    ],
    ids=["dada_de_baja", "vencida"],
)
def test_CO168_E2_vencida_o_dada_de_baja_no_abre_ni_guarda(client_admin, akira, cambios):
    actual = oferta(producto=akira, **cambios)
    url = reverse("catalog:oferta_editar", args=[actual.pk])

    abrir = client_admin.get(url)
    guardar = client_admin.post(url, del_producto(akira, descripcion="Otra"))

    assert abrir.url == reverse("catalog:oferta_ficha", args=[actual.pk])
    assert guardar.url == abrir.url
    actual.refresh_from_db()
    assert actual.descripcion == "Oferta existente"


def test_CO056_cambiar_el_valor_de_una_activa_actualiza_precio_carrito_y_log(
    client_admin, administrador, akira
):
    actual = oferta(producto=akira)
    linea = en_carrito(akira, Decimal("16650"))

    client_admin.post(
        reverse("catalog:oferta_editar", args=[actual.pk]),
        del_producto(akira, descripcion="Oferta existente", valor="20"),
    )

    actual.refresh_from_db()
    assert actual.valor == Decimal("20")
    assert precio_visible(akira) == Decimal("14800.00")
    linea.refresh_from_db()
    assert linea.precio_vigente == Decimal("14800")
    registro = auditorias(RegistroAuditoria.MODIFICACION_OFERTA).get()
    assert registro.actor == administrador
    assert "valor: «10 %» → «20 %»" in registro.detalle
    assert "descripción" not in registro.detalle


def test_CO056_A1_reducir_el_alcance_restaura_a_los_que_quedan_afuera(client_admin, akira):
    otro = ProductoFactory(tipo=akira.tipo, titulo="Monster", precio=Decimal("10000"), stock=2)
    actual = oferta(tipo=akira.tipo)
    linea = en_carrito(akira, Decimal("16650"))

    client_admin.post(
        reverse("catalog:oferta_editar", args=[actual.pk]),
        del_producto(otro, descripcion="Oferta existente", valor="10"),
    )

    actual.refresh_from_db()
    assert (actual.alcance, actual.producto_id, actual.tipo) == (Oferta.PRODUCTO, otro.pk, None)
    assert precio_visible(akira) == Decimal("18500")
    assert precio_visible(otro) == Decimal("9000.00")
    linea.refresh_from_db()
    assert linea.precio_vigente == Decimal("18500")
    assert (
        "alcance: «Tipo de material:"
        in auditorias(RegistroAuditoria.MODIFICACION_OFERTA).get().detalle
    )


def test_CO056_E1_un_solapamiento_no_actualiza_ningun_campo(client_admin, akira):
    oferta(
        producto=akira, descripcion="Aniversario", fecha_inicio=dias(15), fecha_vencimiento=dias(30)
    )
    actual = oferta(producto=akira)

    respuesta = client_admin.post(
        reverse("catalog:oferta_editar", args=[actual.pk]),
        del_producto(akira, descripcion="Nueva", fecha_vencimiento=dias(20).isoformat()),
    )

    assert "Se superpone con la oferta «Aniversario»" in respuesta.content.decode()
    actual.refresh_from_db()
    assert (actual.descripcion, actual.fecha_vencimiento) == ("Oferta existente", dias(10))
    assert not auditorias(RegistroAuditoria.MODIFICACION_OFERTA).exists()


def test_CO056_mover_el_inicio_al_futuro_la_vuelve_programada(client_admin, akira):
    actual = oferta(producto=akira)

    client_admin.post(
        reverse("catalog:oferta_editar", args=[actual.pk]),
        del_producto(
            akira, descripcion="Oferta existente", valor="10", fecha_inicio=dias(2).isoformat()
        ),
    )

    actual.refresh_from_db()
    assert actual.estado == Oferta.PROGRAMADA
    assert precio_visible(akira) == Decimal("18500")


def test_CO056_sin_cambios_no_audita(client_admin, akira):
    actual = oferta(producto=akira)

    client_admin.post(
        reverse("catalog:oferta_editar", args=[actual.pk]),
        del_producto(akira, descripcion="Oferta existente", valor="10"),
    )

    assert not auditorias(RegistroAuditoria.MODIFICACION_OFERTA).exists()


# ===========================================================================
# CO-057 · solicitarBajaDeOferta, CO-058 · confirmarBajaDeOferta, CO-156
# ===========================================================================


def test_CO057_el_informe_cuenta_productos_con_descuento_y_carritos(client_admin, akira):
    tapado = ProductoFactory(tipo=akira.tipo, precio=Decimal("5000"))
    oferta(producto=tapado, descripcion="Propia")
    por_tipo = oferta(tipo=akira.tipo, descripcion="Del tipo")
    en_carrito(akira)
    en_carrito(tapado)

    respuesta = client_admin.get(reverse("catalog:oferta_baja", args=[por_tipo.pk]))

    informe = respuesta.context["informe"]
    # El de la oferta propia no cuenta: a ése lo descuenta la individual.
    assert informe.con_descuento == 1
    assert informe.carritos == 2
    assert "vuelven a su valor sin descuento" in respuesta.content.decode()
    assert not auditorias(RegistroAuditoria.BAJA_OFERTA).exists()


def test_CO057_E1_una_vencida_informa_que_ya_expiro_y_no_registra_nada(client_admin, akira):
    vencida = oferta(producto=akira, fecha_inicio=dias(-10), fecha_vencimiento=dias(-1))

    respuesta = client_admin.get(reverse("catalog:oferta_baja", args=[vencida.pk]), follow=True)

    assert (
        "La oferta ya venció y los precios originales ya se restauraron"
        in respuesta.content.decode()
    )
    vencida.refresh_from_db()
    assert vencida.estado == Oferta.ACTIVA
    assert not auditorias(RegistroAuditoria.BAJA_OFERTA).exists()


def test_CO156_cancelar_la_baja_no_cambia_nada(client_admin, akira):
    actual = oferta(producto=akira)

    client_admin.get(reverse("catalog:oferta_baja", args=[actual.pk]))

    actual.refresh_from_db()
    assert actual.estado == Oferta.ACTIVA
    assert precio_visible(akira) == Decimal("16650.00")
    assert not auditorias(RegistroAuditoria.BAJA_OFERTA).exists()


def test_CO058_confirmar_la_deja_dada_de_baja_y_restaura_precio_y_carritos(
    client_admin, administrador, akira
):
    actual = oferta(producto=akira)
    otra = oferta(producto=ProductoFactory(), descripcion="Otra")
    linea = en_carrito(akira, Decimal("16650"))

    client_admin.post(reverse("catalog:oferta_baja", args=[actual.pk]))

    actual.refresh_from_db()
    assert actual.estado == Oferta.DADA_DE_BAJA
    assert precio_visible(akira) == Decimal("18500")
    linea.refresh_from_db()
    assert linea.precio_vigente == Decimal("18500")
    registro = auditorias(RegistroAuditoria.BAJA_OFERTA).get()
    assert registro.actor == administrador
    assert "1 productos con precio restaurado; 1 carritos actualizados" in registro.detalle
    # Postcondiciones negativas: el producto y las otras ofertas siguen igual.
    akira.refresh_from_db()
    assert akira.precio == Decimal("18500")
    otra.refresh_from_db()
    assert otra.estado == Oferta.ACTIVA


def test_CO058_una_programada_tambien_se_da_de_baja(client_admin, akira):
    programada = oferta(producto=akira, fecha_inicio=dias(3), estado=Oferta.PROGRAMADA)

    client_admin.post(reverse("catalog:oferta_baja", args=[programada.pk]))

    programada.refresh_from_db()
    assert programada.estado == Oferta.DADA_DE_BAJA


def test_CO058_una_dada_de_baja_no_se_reactiva_ni_se_audita_dos_veces(client_admin, akira):
    actual = oferta(producto=akira)
    url = reverse("catalog:oferta_baja", args=[actual.pk])

    client_admin.post(url)
    client_admin.post(url)

    assert auditorias(RegistroAuditoria.BAJA_OFERTA).count() == 1


# ===========================================================================
# CO-059 · ejecutarCicloDeVigenciaDeOfertas
# ===========================================================================


def test_CO059_activa_las_programadas_y_vence_las_activas_con_su_entrada(akira):
    monster = ProductoFactory(precio=Decimal("10000"))
    programada = oferta(producto=akira, fecha_inicio=hoy(), estado=Oferta.PROGRAMADA)
    a_vencer = oferta(producto=monster, fecha_inicio=dias(-10), fecha_vencimiento=dias(-1))
    baja = oferta(
        tipo=akira.tipo,
        fecha_inicio=dias(-10),
        fecha_vencimiento=dias(-1),
        estado=Oferta.DADA_DE_BAJA,
    )
    linea_akira = en_carrito(akira)
    linea_monster = en_carrito(monster, Decimal("9000"))

    salida = StringIO()
    call_command("ejecutar_temporizador", stdout=salida)

    programada.refresh_from_db()
    a_vencer.refresh_from_db()
    baja.refresh_from_db()
    assert programada.estado == Oferta.ACTIVA
    assert a_vencer.estado == Oferta.VENCIDA
    assert baja.estado == Oferta.DADA_DE_BAJA
    linea_akira.refresh_from_db()
    linea_monster.refresh_from_db()
    assert linea_akira.precio_vigente == Decimal("16650")
    assert linea_monster.precio_vigente == Decimal("10000")
    registro = auditorias(RegistroAuditoria.VENCIMIENTO_AUTOMATICO_OFERTA).get()
    assert registro.actor is None
    assert registro.actor_email == ofertas.TEMPORIZADOR
    assert "ofertas: 1 activadas, 1 vencidas" in salida.getvalue()


def test_CO059_correrlo_dos_veces_no_duplica_nada(akira):
    oferta(producto=akira, fecha_inicio=dias(-10), fecha_vencimiento=dias(-1))

    ofertas.ejecutar_ciclo()
    segunda = ofertas.ejecutar_ciclo()

    assert segunda.vencidas == []
    assert auditorias(RegistroAuditoria.VENCIMIENTO_AUTOMATICO_OFERTA).count() == 1


# ===========================================================================
# CO-169 · consultarOfertas y CO-170 · consultarFichaDeOferta
# ===========================================================================


def test_CO169_lista_de_la_mas_reciente_a_la_mas_vieja_con_su_estado_por_fecha(client_admin, akira):
    vieja = oferta(
        producto=akira, descripcion="Vieja", fecha_inicio=dias(-20), fecha_vencimiento=dias(-5)
    )
    nueva = oferta(
        producto=akira,
        descripcion="Nueva",
        fecha_inicio=dias(5),
        fecha_vencimiento=dias(9),
        estado=Oferta.PROGRAMADA,
    )

    respuesta = client_admin.get(URL_LISTA)

    listadas = list(respuesta.context["ofertas"])
    assert listadas == [nueva, vieja]
    # Venció por fecha aunque el Temporizador no haya corrido.
    assert listadas[1].estado_hoy == Oferta.VENCIDA
    assert respuesta.context["pagina"].paginator.count == 2


@pytest.mark.parametrize(
    ("parametros", "esperadas"),
    [
        ({"estado": "activa"}, {"Activa"}),
        ({"estado": "programada"}, {"Programada", "Del tipo"}),
        ({"estado": "vencida"}, {"Vencida"}),
        ({"estado": "dada_de_baja"}, {"Baja"}),
        ({"q": "akira"}, {"Activa", "Programada", "Vencida", "Baja"}),
        ({"q": "manga"}, {"Del tipo"}),
        ({"fecha": "vencimiento", "hasta": "VENCE_AYER"}, {"Vencida"}),
    ],
)
def test_CO169_filtra_por_estado_texto_y_fechas(client_admin, akira, parametros, esperadas):
    manga = TipoFactory(nombre="Manga de prueba")
    oferta(producto=akira, descripcion="Activa")
    oferta(
        producto=akira, descripcion="Programada", fecha_inicio=dias(20), fecha_vencimiento=dias(25)
    )
    oferta(
        producto=akira, descripcion="Vencida", fecha_inicio=dias(-20), fecha_vencimiento=dias(-1)
    )
    oferta(
        producto=akira,
        descripcion="Baja",
        fecha_inicio=dias(30),
        fecha_vencimiento=dias(35),
        estado=Oferta.DADA_DE_BAJA,
    )
    oferta(tipo=manga, descripcion="Del tipo", fecha_inicio=dias(40), fecha_vencimiento=dias(45))
    parametros = {
        clave: (dias(-1).isoformat() if valor == "VENCE_AYER" else valor)
        for clave, valor in parametros.items()
    }

    respuesta = client_admin.get(URL_LISTA, parametros)

    assert {o.descripcion for o in respuesta.context["ofertas"]} == esperadas


def test_CO169_E1_sin_resultados_ofrece_limpiar_y_E2_sin_ofertas_ofrece_la_alta(
    client_admin, akira
):
    vacia = client_admin.get(URL_LISTA).content.decode()
    assert "Todavía no hay ofertas registradas." in vacia
    assert URL_ALTA in vacia

    oferta(producto=akira)
    sin_resultados = client_admin.get(URL_LISTA, {"q": "nada que ver"}).content.decode()
    assert "Ninguna oferta cumple los filtros." in sin_resultados
    assert "Limpiar filtros" in sin_resultados


def test_CO170_la_ficha_muestra_los_dos_precios_y_las_acciones_del_estado(client_admin, akira):
    tapado = ProductoFactory(tipo=akira.tipo, titulo="Monster", precio=Decimal("10000"))
    oferta(producto=tapado, descripcion="Propia de Monster")
    por_tipo = oferta(tipo=akira.tipo, descripcion="Del tipo")

    respuesta = client_admin.get(reverse("catalog:oferta_ficha", args=[por_tipo.pk]))
    contenido = respuesta.content.decode()

    assert "$ 18.500" in contenido
    assert "$ 16.650" in contenido
    assert "Se cobra con su oferta propia, «Propia de Monster»" in contenido
    assert reverse("catalog:oferta_editar", args=[por_tipo.pk]) in contenido
    assert reverse("catalog:oferta_baja", args=[por_tipo.pk]) in contenido


def test_CO170_una_vencida_es_de_solo_lectura(client_admin, akira):
    vencida = oferta(producto=akira, fecha_inicio=dias(-10), fecha_vencimiento=dias(-1))

    contenido = client_admin.get(
        reverse("catalog:oferta_ficha", args=[vencida.pk])
    ).content.decode()

    assert reverse("catalog:oferta_editar", args=[vencida.pk]) not in contenido
    assert reverse("catalog:oferta_baja", args=[vencida.pk]) not in contenido


# ===========================================================================
# La tienda: precio tachado y filtro por el precio que se cobra
# ===========================================================================


def test_la_tienda_tacha_el_precio_original(client, akira):
    oferta(producto=akira, descripcion="Aniversario")

    ficha = client.get(reverse("core:tienda_producto", args=[akira.pk])).content.decode()
    catalogo = client.get(reverse("core:tienda_catalogo")).content.decode()

    for contenido in (ficha, catalogo):
        assert (
            '<s class="precio-anterior"><span class="sr-only">Antes </span>$ 18.500</s>'
            in contenido
        )
        assert "$ 16.650" in contenido
    assert "Aniversario" in ficha


def test_el_filtro_de_precio_mide_el_precio_con_oferta(client, akira):
    oferta(producto=akira)

    hasta_17000 = client.get(reverse("core:tienda_catalogo"), {"hasta": "17000"})

    assert akira.pk in [producto.pk for producto in hasta_17000.context["productos"]]


def test_el_carrito_muestra_el_precio_con_oferta(client, akira):
    oferta(producto=akira, descripcion="Aniversario")
    client.post(reverse("tienda:agregar", args=[akira.pk]), {"cantidad": 2})

    contenido = client.get(reverse("tienda:carrito")).content.decode()

    assert "$ 33.300" in contenido
    assert "Aniversario" in contenido


# ===========================================================================
# Control de acceso — por la dirección real, con el rol equivocado
# ===========================================================================


@pytest.mark.parametrize("rol", ["cajero", "cliente"])
def test_solo_el_administrador_gestiona_ofertas(client, request, rol, akira):
    client.force_login(request.getfixturevalue(rol))
    actual = oferta(producto=akira)

    for url in (
        URL_LISTA,
        URL_ALTA,
        reverse("catalog:oferta_ficha", args=[actual.pk]),
        reverse("catalog:oferta_editar", args=[actual.pk]),
        reverse("catalog:oferta_baja", args=[actual.pk]),
    ):
        assert client.get(url).status_code == 403, url
    assert client.post(URL_ALTA, del_producto(akira)).status_code == 403
    assert client.post(reverse("catalog:oferta_baja", args=[actual.pk])).status_code == 403
    actual.refresh_from_db()
    assert actual.estado == Oferta.ACTIVA
    assert Oferta.objects.count() == 1


def test_sin_sesion_redirige_al_inicio_de_sesion(client, akira):
    actual = oferta(producto=akira)

    respuesta = client.post(reverse("catalog:oferta_baja", args=[actual.pk]))

    assert respuesta.status_code == 302
    assert reverse("accounts:login") in respuesta.url
    actual.refresh_from_db()
    assert actual.estado == Oferta.ACTIVA


def test_el_producto_debe_ser_del_catalogo_activo(client_admin):
    descatalogado = ProductoFactory(estado=Producto.DESCATALOGADO)

    respuesta = client_admin.post(URL_ALTA, del_producto(descatalogado))

    assert not Oferta.objects.exists()
    assert "Elegí un producto activo o en pre-venta de la lista." in respuesta.content.decode()
