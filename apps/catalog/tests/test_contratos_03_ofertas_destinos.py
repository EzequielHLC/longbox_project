"""Ofertas por editorial, etiqueta y grupo de etiquetas (plan 03, tercera parte).

Los contratos son los de siempre —`CO-054`, `CO-055`, `CO-056`, `CO-057`,
`CO-058`, `CO-059`, `CO-169`, `CO-170` y `CO-033`—, con los tres destinos nuevos.
Zona de foco reforzado (dinero): la precedencia decide cuánto se cobra, así que
se prueba cada nivel contra el siguiente, el empate y las postcondiciones
negativas (lo que una oferta **no** tiene que tocar).

Decisiones del responsable que se verifican acá:

1. Manda la más específica: producto > etiqueta > grupo > editorial > tipo.
2. Un destino por oferta.
3. Empate en el mismo nivel: la que empezó antes y, el mismo día, la creada primero.
4. No se solapan dos ofertas vivas sobre el mismo destino; sobre destinos distintos sí.
5. Un destino dado de baja deja de descontar.
6. Cada destino alcanza a los productos de la tienda (Activos y en Pre-venta).
"""

from datetime import timedelta
from decimal import Decimal

import pytest
from django.db import IntegrityError, connection
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from django.utils import timezone

from apps.catalog import ofertas
from apps.catalog.models import Oferta, Producto
from apps.catalog.precio_visible import OfertasDelDia, oferta_aplicada, precio_visible
from apps.catalog.services import calcular_impacto_de_baja
from apps.catalog.tests.factories import (
    EditorialFactory,
    EtiquetaFactory,
    GrupoEtiquetaFactory,
    ProductoFactory,
    ProductoNoEditorialFactory,
)
from apps.core.models import RegistroAuditoria
from apps.tienda.models import Carrito, LineaCarrito

pytestmark = pytest.mark.django_db

URL_ALTA = reverse("catalog:oferta_alta")
URL_LISTA = reverse("catalog:oferta_lista")


def hoy():
    return timezone.localdate()


def dias(n):
    return hoy() + timedelta(days=n)


def formulario(**cambios):
    datos = {
        "descripcion": "Semana de la editorial",
        "fecha_inicio": hoy().isoformat(),
        "fecha_vencimiento": dias(10).isoformat(),
        "tipo_descuento": Oferta.PORCENTAJE,
        "valor": "20",
        "alcance": Oferta.EDITORIAL,
        "producto": "",
        "tipo": "",
        "editorial": "",
        "etiqueta": "",
        "grupo": "",
    }
    datos.update(cambios)
    return datos


def oferta(**cambios):
    """Una oferta Activa del 10 %; el alcance se deduce del destino que se pase."""
    destino = next(campo for campo in Oferta.CAMPO_DEL_ALCANCE.values() if campo in cambios)
    datos = {
        "descripcion": f"Por {destino}",
        "fecha_inicio": hoy(),
        "fecha_vencimiento": dias(10),
        "tipo_descuento": Oferta.PORCENTAJE,
        "valor": Decimal("10"),
        "alcance": destino,
        "estado": Oferta.ACTIVA,
    }
    datos.update(cambios)
    return Oferta.objects.create(**datos)


def en_carrito(producto):
    return LineaCarrito.objects.create(
        carrito=Carrito.objects.create(),
        producto=producto,
        cantidad=1,
        precio_vigente=producto.precio,
        precio_visto=producto.precio,
    )


@pytest.fixture
def ivrea():
    return EditorialFactory(nombre="Ivrea")


@pytest.fixture
def franquicia():
    return GrupoEtiquetaFactory(nombre="Franquicia")


@pytest.fixture
def evangelion(franquicia):
    return EtiquetaFactory(nombre="Evangelion", grupo=franquicia)


@pytest.fixture
def tomo(ivrea, evangelion):
    """Un tomo de Ivrea con la etiqueta Evangelion, a $ 20.000."""
    producto = ProductoFactory(titulo="Evangelion 1", editorial=ivrea, precio=Decimal("20000"))
    producto.etiquetas.add(evangelion)
    return producto


# ===========================================================================
# El modelo: un solo destino, el del alcance
# ===========================================================================


@pytest.mark.parametrize(
    "alcance, sobra", [(Oferta.EDITORIAL, "tipo"), (Oferta.ETIQUETA, "editorial")]
)
def test_CO054_la_base_rechaza_un_destino_que_no_es_el_del_alcance(tomo, alcance, sobra):
    destinos = {
        "editorial": tomo.productoeditorial.editorial,
        "etiqueta": tomo.etiquetas.get(),
        "tipo": tomo.tipo,
    }
    with pytest.raises(IntegrityError):
        Oferta.objects.create(
            descripcion="Mal armada",
            fecha_inicio=hoy(),
            fecha_vencimiento=dias(3),
            tipo_descuento=Oferta.PORCENTAJE,
            valor=Decimal("10"),
            alcance=alcance,
            **{Oferta.CAMPO_DEL_ALCANCE[alcance]: destinos[Oferta.CAMPO_DEL_ALCANCE[alcance]]},
            **{sobra: destinos[sobra]},
        )


def test_CO054_la_base_rechaza_un_alcance_sin_destino():
    with pytest.raises(IntegrityError):
        Oferta.objects.create(
            descripcion="Sin destino",
            fecha_inicio=hoy(),
            fecha_vencimiento=dias(3),
            tipo_descuento=Oferta.PORCENTAJE,
            valor=Decimal("10"),
            alcance=Oferta.GRUPO,
        )


# ===========================================================================
# CO-054 · registrarOferta, por cada destino nuevo
# ===========================================================================


def test_CO054_por_editorial_se_asocia_a_la_editorial_y_descuenta_sus_tomos(
    client_admin, administrador, tomo, ivrea
):
    linea = en_carrito(tomo)
    de_otra = ProductoFactory(precio=Decimal("20000"))
    figura = ProductoNoEditorialFactory(precio=Decimal("20000"))

    respuesta = client_admin.post(URL_ALTA, formulario(editorial=ivrea.pk))

    nueva = Oferta.objects.get()
    assert respuesta.url == reverse("catalog:oferta_ficha", args=[nueva.pk])
    assert (nueva.alcance, nueva.editorial, nueva.estado) == (
        Oferta.EDITORIAL,
        ivrea,
        Oferta.ACTIVA,
    )
    assert (nueva.producto, nueva.tipo, nueva.etiqueta, nueva.grupo) == (None,) * 4
    assert precio_visible(tomo) == Decimal("16000.00")
    # Postcondiciones negativas: otra editorial y el otro rubro no cambian.
    assert precio_visible(de_otra) == Decimal("20000")
    assert precio_visible(figura) == Decimal("20000")
    # El precio guardado no se toca; la línea de carrito, sí.
    tomo.refresh_from_db()
    assert tomo.precio == Decimal("20000")
    linea.refresh_from_db()
    assert linea.precio_vigente == Decimal("16000")
    registro = RegistroAuditoria.objects.get(accion=RegistroAuditoria.ALTA_OFERTA)
    assert registro.actor == administrador
    assert "Editorial: Ivrea" in registro.detalle


def test_CO054_por_etiqueta_descuenta_a_los_que_la_llevan(client_admin, tomo, evangelion):
    sin_etiqueta = ProductoFactory(precio=Decimal("20000"))
    figura = ProductoNoEditorialFactory(precio=Decimal("30000"))
    figura.etiquetas.add(evangelion)

    client_admin.post(URL_ALTA, formulario(alcance=Oferta.ETIQUETA, etiqueta=evangelion.pk))

    assert Oferta.objects.get().etiqueta == evangelion
    assert precio_visible(tomo) == Decimal("16000.00")
    # La etiqueta cruza rubros: una figura con la etiqueta también descuenta.
    assert precio_visible(figura) == Decimal("24000.00")
    assert precio_visible(sin_etiqueta) == Decimal("20000")


def test_CO054_por_grupo_descuenta_a_los_que_llevan_cualquiera_de_sus_etiquetas(
    client_admin, tomo, franquicia
):
    otra = EtiquetaFactory(nombre="Akira", grupo=franquicia)
    de_otra = ProductoFactory(precio=Decimal("10000"))
    de_otra.etiquetas.add(otra)
    genero = EtiquetaFactory(nombre="Mecha", grupo=GrupoEtiquetaFactory(nombre="Género"))
    de_otro_grupo = ProductoFactory(precio=Decimal("10000"))
    de_otro_grupo.etiquetas.add(genero)

    client_admin.post(URL_ALTA, formulario(alcance=Oferta.GRUPO, grupo=franquicia.pk))

    assert Oferta.objects.get().grupo == franquicia
    assert precio_visible(tomo) == Decimal("16000.00")
    assert precio_visible(de_otra) == Decimal("8000.00")
    assert precio_visible(de_otro_grupo) == Decimal("10000")


def test_CO054_un_producto_con_dos_etiquetas_del_grupo_cuenta_una_vez(tomo, franquicia):
    tomo.etiquetas.add(EtiquetaFactory(nombre="Gainax", grupo=franquicia))
    nueva = oferta(grupo=franquicia)

    assert list(ofertas.productos_del_alcance(nueva)) == [tomo.producto_ptr]
    assert ofertas.productos_afectados(nueva)[0].precio_con_descuento == Decimal("18000.00")


@pytest.mark.parametrize("estado", [Producto.AGOTADO, Producto.DESCATALOGADO])
def test_CO054_el_destino_alcanza_solo_a_los_de_la_tienda(tomo, ivrea, estado):
    fuera = ProductoFactory(editorial=ivrea, estado=estado)
    nueva = oferta(editorial=ivrea)

    alcanzados = set(ofertas.productos_del_alcance(nueva).values_list("pk", flat=True))
    assert alcanzados == {tomo.pk}
    assert fuera.pk not in alcanzados


@pytest.mark.parametrize(
    "alcance, campo, mensaje",
    [
        (Oferta.EDITORIAL, "editorial", "Elegí la editorial de la oferta."),
        (Oferta.ETIQUETA, "etiqueta", "Elegí la etiqueta de la oferta."),
        (Oferta.GRUPO, "grupo", "Elegí el grupo de etiquetas de la oferta."),
    ],
)
def test_CO054_el_alcance_exige_su_destino(client_admin, alcance, campo, mensaje):
    respuesta = client_admin.post(URL_ALTA, formulario(alcance=alcance))

    assert respuesta.status_code == 200
    assert mensaje in respuesta.content.decode()
    assert not Oferta.objects.exists()


def test_CO054_ignora_los_destinos_de_otros_alcances(client_admin, tomo, ivrea, evangelion):
    client_admin.post(
        URL_ALTA, formulario(editorial=ivrea.pk, etiqueta=evangelion.pk, tipo=tomo.tipo.pk)
    )

    nueva = Oferta.objects.get()
    assert (nueva.editorial, nueva.etiqueta, nueva.tipo) == (ivrea, None, None)


@pytest.mark.parametrize("destino", ["editorial", "etiqueta", "grupo", "grupo_de_la_etiqueta"])
def test_CO054_un_destino_dado_de_baja_no_recibe_ofertas(administrador, tomo, destino):
    editorial, etiqueta = tomo.productoeditorial.editorial, tomo.etiquetas.get()
    if destino == "editorial":
        editorial.activa = False
        editorial.save()
        datos, alcance = editorial, Oferta.EDITORIAL
    elif destino == "etiqueta":
        etiqueta.activa = False
        etiqueta.save()
        datos, alcance = etiqueta, Oferta.ETIQUETA
    elif destino == "grupo":
        etiqueta.grupo.activo = False
        etiqueta.grupo.save()
        datos, alcance = etiqueta.grupo, Oferta.GRUPO
    else:
        etiqueta.grupo.activo = False
        etiqueta.grupo.save()
        datos, alcance = etiqueta, Oferta.ETIQUETA

    with pytest.raises(ofertas.OfertaRechazada, match="dad[ao]s? de baja"):
        ofertas.registrar(
            ofertas.DatosDeOferta(
                descripcion="A un inactivo",
                fecha_inicio=hoy(),
                fecha_vencimiento=dias(3),
                tipo_descuento=Oferta.PORCENTAJE,
                valor=Decimal("10"),
                alcance=alcance,
                **{Oferta.CAMPO_DEL_ALCANCE[alcance]: datos},
            ),
            actor=administrador,
        )
    assert not Oferta.objects.exists()


def test_CO054_el_formulario_no_ofrece_destinos_dados_de_baja(client_admin, ivrea):
    EditorialFactory(nombre="Cerrada", activa=False)

    contenido = client_admin.get(URL_ALTA).content.decode()

    assert ">Ivrea<" in contenido
    assert ">Cerrada<" not in contenido


@pytest.mark.parametrize(
    "alcance, campo, aviso",
    [
        (Oferta.EDITORIAL, "editorial", "La editorial seleccionada"),
        (Oferta.ETIQUETA, "etiqueta", "La etiqueta seleccionada"),
        (Oferta.GRUPO, "grupo", "El grupo de etiquetas seleccionado"),
    ],
)
def test_CO054_A1_un_destino_sin_productos_registra_con_aviso(client_admin, alcance, campo, aviso):
    destinos = {
        "editorial": lambda: EditorialFactory(nombre="Sin tomos"),
        "etiqueta": lambda: EtiquetaFactory(nombre="Sin productos"),
        "grupo": lambda: GrupoEtiquetaFactory(nombre="Vacío"),
    }
    vacio = destinos[campo]()

    respuesta = client_admin.post(
        URL_ALTA, formulario(alcance=alcance, **{campo: vacio.pk}), follow=True
    )

    assert getattr(Oferta.objects.get(), campo) == vacio
    assert f"{aviso} no tiene productos activos en este momento" in respuesta.content.decode()


# ===========================================================================
# CO-054 E2 · solapamiento sobre el mismo destino (I-20)
# ===========================================================================


def test_CO054_E2_rechaza_dos_ofertas_vivas_sobre_la_misma_etiqueta(client_admin, evangelion):
    oferta(etiqueta=evangelion, descripcion="Evangelion de verano")

    respuesta = client_admin.post(
        URL_ALTA,
        formulario(
            alcance=Oferta.ETIQUETA,
            etiqueta=evangelion.pk,
            fecha_inicio=dias(5).isoformat(),
            fecha_vencimiento=dias(20).isoformat(),
        ),
    )

    assert respuesta.status_code == 200
    assert "Se superpone con la oferta «Evangelion de verano»" in respuesta.content.decode()
    assert Oferta.objects.count() == 1


def test_CO054_E2_destinos_distintos_si_comparten_dias(administrador, tomo, ivrea, evangelion):
    oferta(editorial=ivrea)
    oferta(grupo=evangelion.grupo)

    nueva = ofertas.registrar(
        ofertas.DatosDeOferta(
            descripcion="Etiqueta",
            fecha_inicio=hoy(),
            fecha_vencimiento=dias(10),
            tipo_descuento=Oferta.PORCENTAJE,
            valor=Decimal("30"),
            alcance=Oferta.ETIQUETA,
            etiqueta=evangelion,
        ),
        actor=administrador,
    )

    assert Oferta.objects.count() == 3
    assert oferta_aplicada(tomo) == nueva


def test_CO054_E2_una_editorial_distinta_no_es_solapamiento(administrador, ivrea):
    oferta(editorial=EditorialFactory(nombre="Panini"))

    ofertas.registrar(
        ofertas.DatosDeOferta(
            descripcion="Ivrea",
            fecha_inicio=hoy(),
            fecha_vencimiento=dias(10),
            tipo_descuento=Oferta.PORCENTAJE,
            valor=Decimal("10"),
            alcance=Oferta.EDITORIAL,
            editorial=ivrea,
        ),
        actor=administrador,
    )

    assert Oferta.objects.filter(alcance=Oferta.EDITORIAL).count() == 2


# ===========================================================================
# Precedencia: la más específica, y el empate
# ===========================================================================


def test_la_precedencia_va_de_lo_mas_especifico_a_lo_mas_general(tomo, ivrea, evangelion):
    """Se registran del más general al más específico; cada una tapa a las anteriores."""
    cadena = [
        (Oferta.TIPO, {"tipo": tomo.tipo}, Decimal("50")),
        (Oferta.EDITORIAL, {"editorial": ivrea}, Decimal("40")),
        (Oferta.GRUPO, {"grupo": evangelion.grupo}, Decimal("30")),
        (Oferta.ETIQUETA, {"etiqueta": evangelion}, Decimal("20")),
        (Oferta.PRODUCTO, {"producto": tomo.producto_ptr}, Decimal("5")),
    ]
    for alcance, destino, valor in cadena:
        nueva = oferta(valor=valor, **destino)

        assert oferta_aplicada(tomo) == nueva, alcance
        assert precio_visible(tomo) == Decimal("20000") * (100 - valor) / 100
    assert [alcance for alcance, _, _ in reversed(cadena)] == list(Oferta.PRECEDENCIA)


def test_las_ofertas_nunca_se_suman(tomo, ivrea):
    oferta(tipo=tomo.tipo, valor=Decimal("10"))
    oferta(editorial=ivrea, valor=Decimal("10"))

    # Un 10 %, no un 19 % ni un 20 %.
    assert precio_visible(tomo) == Decimal("18000.00")


def test_empate_entre_dos_etiquetas_manda_la_que_empezo_antes(tomo, franquicia):
    segunda = EtiquetaFactory(nombre="Gainax", grupo=franquicia)
    tomo.etiquetas.add(segunda)
    posterior = oferta(etiqueta=tomo.etiquetas.get(nombre="Evangelion"), valor=Decimal("40"))
    anterior = oferta(etiqueta=segunda, valor=Decimal("15"), fecha_inicio=dias(-3))

    assert oferta_aplicada(tomo) == anterior
    assert posterior != anterior
    assert precio_visible(tomo) == Decimal("17000.00")


def test_empate_el_mismo_dia_manda_la_creada_primero(tomo, franquicia):
    segunda = EtiquetaFactory(nombre="Gainax", grupo=franquicia)
    tomo.etiquetas.add(segunda)
    primera = oferta(etiqueta=segunda, valor=Decimal("15"))
    oferta(etiqueta=tomo.etiquetas.get(nombre="Evangelion"), valor=Decimal("40"))

    assert oferta_aplicada(tomo) == primera


def test_una_programada_mas_especifica_no_tapa_todavia(tomo, ivrea, evangelion):
    vigente = oferta(editorial=ivrea)
    oferta(etiqueta=evangelion, fecha_inicio=dias(2), estado=Oferta.PROGRAMADA)

    assert oferta_aplicada(tomo) == vigente
    assert oferta_aplicada(tomo, hoy=dias(2)).etiqueta == evangelion


# ===========================================================================
# Decisión 5: un destino dado de baja deja de descontar
# ===========================================================================


def test_una_editorial_dada_de_baja_deja_de_descontar(tomo, ivrea):
    oferta(editorial=ivrea)
    ivrea.activa = False
    ivrea.save()

    assert precio_visible(tomo) == Decimal("20000")


def test_una_etiqueta_dada_de_baja_cede_a_la_oferta_siguiente(tomo, ivrea, evangelion):
    de_la_editorial = oferta(editorial=ivrea, valor=Decimal("5"))
    oferta(etiqueta=evangelion, valor=Decimal("30"))
    evangelion.activa = False
    evangelion.save()

    assert oferta_aplicada(tomo) == de_la_editorial


def test_un_grupo_dado_de_baja_apaga_sus_ofertas_y_las_de_sus_etiquetas(tomo, evangelion):
    oferta(grupo=evangelion.grupo)
    oferta(etiqueta=evangelion, descripcion="Etiqueta del grupo")
    evangelion.grupo.activo = False
    evangelion.grupo.save()

    assert oferta_aplicada(tomo) is None


def test_el_grupo_no_alcanza_por_una_etiqueta_inactiva(tomo, evangelion):
    oferta(grupo=evangelion.grupo)
    evangelion.activa = False
    evangelion.save()

    assert precio_visible(tomo) == Decimal("20000")


# ===========================================================================
# CO-055 · el tope de $ 1 con un monto fijo
# ===========================================================================


def test_CO055_el_monto_fijo_de_una_etiqueta_pide_el_tope_y_lo_aplica(client_admin, evangelion):
    barato = ProductoFactory(titulo="Póster", precio=Decimal("3000"))
    barato.etiquetas.add(evangelion)
    datos = formulario(
        alcance=Oferta.ETIQUETA,
        etiqueta=evangelion.pk,
        tipo_descuento=Oferta.MONTO_FIJO,
        valor="5000",
    )

    pedido = client_admin.post(URL_ALTA, datos)
    assert "El descuento supera el precio de 1 producto" in pedido.content.decode()
    assert not Oferta.objects.exists()

    client_admin.post(URL_ALTA, {**datos, "aceptar_tope": "1"})
    assert precio_visible(barato) == Decimal("1")


# ===========================================================================
# CO-056 · editar: cambiar de destino
# ===========================================================================


def test_CO056_cambiar_de_tipo_a_editorial_mueve_el_descuento_y_los_carritos(
    client_admin, tomo, ivrea
):
    del_tipo = ProductoFactory(tipo=tomo.tipo, precio=Decimal("10000"))
    linea_tipo, linea_tomo = en_carrito(del_tipo), en_carrito(tomo)
    otro_tomo = ProductoFactory(editorial=ivrea, precio=Decimal("10000"))
    vieja = oferta(tipo=tomo.tipo, valor=Decimal("20"))
    # `tomo` queda en los dos alcances; `del_tipo` sale y `otro_tomo` entra.

    client_admin.post(
        reverse("catalog:oferta_editar", args=[vieja.pk]),
        formulario(
            descripcion=vieja.descripcion,
            fecha_inicio=vieja.fecha_inicio.isoformat(),
            fecha_vencimiento=vieja.fecha_vencimiento.isoformat(),
            alcance=Oferta.EDITORIAL,
            editorial=ivrea.pk,
        ),
    )

    vieja.refresh_from_db()
    assert (vieja.alcance, vieja.editorial, vieja.tipo) == (Oferta.EDITORIAL, ivrea, None)
    assert precio_visible(del_tipo) == Decimal("10000")
    assert precio_visible(otro_tomo) == Decimal("8000.00")
    linea_tipo.refresh_from_db()
    linea_tomo.refresh_from_db()
    assert linea_tipo.precio_vigente == Decimal("10000")
    assert linea_tomo.precio_vigente == Decimal("16000")
    registro = RegistroAuditoria.objects.get(accion=RegistroAuditoria.MODIFICACION_OFERTA)
    assert "alcance: «Tipo de material:" in registro.detalle
    assert "» → «Editorial: Ivrea»" in registro.detalle


def test_CO056_una_oferta_sobre_un_destino_que_se_dio_de_baja_se_sigue_editando(
    administrador, ivrea
):
    vieja = oferta(editorial=ivrea)
    ivrea.activa = False
    ivrea.save()
    datos = ofertas.DatosDeOferta.de(vieja)
    datos.descripcion = "Cambió la descripción"

    cambios = ofertas.editar(vieja, datos, actor=administrador)

    assert cambios
    vieja.refresh_from_db()
    assert vieja.descripcion == "Cambió la descripción"


def test_CO056_no_se_puede_mover_a_un_destino_dado_de_baja(administrador, ivrea, evangelion):
    vieja = oferta(editorial=ivrea)
    evangelion.activa = False
    evangelion.save()
    datos = ofertas.DatosDeOferta.de(vieja)
    datos.alcance, datos.etiqueta = Oferta.ETIQUETA, evangelion

    with pytest.raises(ofertas.OfertaRechazada):
        ofertas.editar(vieja, datos, actor=administrador)
    vieja.refresh_from_db()
    assert (vieja.alcance, vieja.etiqueta) == (Oferta.EDITORIAL, None)


def test_CO168_la_edicion_abre_con_el_destino_actual(client_admin, evangelion):
    vieja = oferta(etiqueta=evangelion)

    respuesta = client_admin.get(reverse("catalog:oferta_editar", args=[vieja.pk]))

    assert respuesta.context["form"].initial["etiqueta"] == evangelion
    assert respuesta.context["form"].initial["alcance"] == Oferta.ETIQUETA


# ===========================================================================
# CO-057 y CO-058 · la baja
# ===========================================================================


def test_CO057_el_informe_no_cuenta_los_que_cobra_otra_mas_especifica(tomo, ivrea, evangelion):
    ProductoFactory(editorial=ivrea, precio=Decimal("10000"))
    de_la_editorial = oferta(editorial=ivrea)
    oferta(etiqueta=evangelion)
    en_carrito(tomo)

    informe = ofertas.solicitar_baja(de_la_editorial)

    assert informe.alcance == "Editorial: Ivrea"
    assert informe.con_descuento == 1  # el otro tomo: a `tomo` lo cobra la etiqueta
    assert informe.carritos == 1


def test_CO058_dar_de_baja_la_de_la_etiqueta_deja_cobrar_la_de_la_editorial(
    administrador, tomo, ivrea, evangelion
):
    oferta(editorial=ivrea, valor=Decimal("10"))
    de_la_etiqueta = oferta(etiqueta=evangelion, valor=Decimal("30"))
    linea = en_carrito(tomo)
    ofertas._actualizar_carritos(Producto.objects.filter(pk=tomo.pk))
    linea.refresh_from_db()
    assert linea.precio_vigente == Decimal("14000")

    resumen = ofertas.confirmar_baja(de_la_etiqueta, actor=administrador)

    assert resumen.productos == 1
    linea.refresh_from_db()
    assert linea.precio_vigente == Decimal("18000")
    registro = RegistroAuditoria.objects.get(accion=RegistroAuditoria.BAJA_OFERTA)
    assert "Etiqueta: Evangelion (Franquicia)" in registro.detalle


# ===========================================================================
# CO-059 · el Temporizador actualiza los carritos del destino
# ===========================================================================


def test_CO059_activar_una_de_grupo_actualiza_sus_carritos(tomo, franquicia):
    linea = en_carrito(tomo)
    oferta(grupo=franquicia, fecha_inicio=hoy(), estado=Oferta.PROGRAMADA, valor=Decimal("25"))

    resultado = ofertas.ejecutar_ciclo()

    assert len(resultado.activadas) == 1
    linea.refresh_from_db()
    assert linea.precio_vigente == Decimal("15000")


# ===========================================================================
# CO-169 y CO-170 · la lista y la ficha
# ===========================================================================


def test_CO169_la_lista_describe_el_destino_y_busca_por_su_nombre(client_admin, ivrea, evangelion):
    oferta(editorial=ivrea, descripcion="Una")
    oferta(etiqueta=evangelion, descripcion="Otra")
    oferta(grupo=evangelion.grupo, descripcion="Tercera")

    contenido = client_admin.get(URL_LISTA).content.decode()
    buscada = client_admin.get(URL_LISTA, {"q": "evangel"}).content.decode()

    assert "Editorial: Ivrea" in contenido
    assert "Etiqueta: Evangelion" in contenido
    assert "Grupo: Franquicia" in contenido
    assert "Otra" in buscada
    assert "Una" not in buscada


def test_CO170_la_ficha_marca_los_productos_que_cobra_otra_mas_especifica(
    client_admin, tomo, ivrea, evangelion
):
    otro = ProductoFactory(titulo="Ivrea suelto", editorial=ivrea, precio=Decimal("10000"))
    de_la_editorial = oferta(editorial=ivrea)
    oferta(etiqueta=evangelion, descripcion="Evangelion al 30")

    filas = {fila.producto.pk: fila for fila in ofertas.productos_afectados(de_la_editorial)}
    contenido = client_admin.get(
        reverse("catalog:oferta_ficha", args=[de_la_editorial.pk])
    ).content.decode()

    assert filas[tomo.pk].tapado_por.descripcion == "Evangelion al 30"
    assert filas[otro.pk].tapado_por is None
    assert "Editorial: Ivrea" in contenido
    assert "Se cobra con la oferta «Evangelion al 30», que tiene precedencia" in contenido


# ===========================================================================
# CO-033 · el informe de baja de un producto
# ===========================================================================


def test_CO033_cuenta_las_ofertas_de_su_editorial_etiquetas_y_grupos(tomo, ivrea, evangelion):
    oferta(producto=tomo.producto_ptr)
    oferta(editorial=ivrea)
    oferta(etiqueta=evangelion)
    oferta(grupo=evangelion.grupo)
    oferta(editorial=EditorialFactory(nombre="Ajena"))
    oferta(etiqueta=EtiquetaFactory(nombre="Ajena"))

    assert calcular_impacto_de_baja(tomo).ofertas_vigentes == 4


def test_CO033_un_producto_sin_editorial_no_cuenta_ofertas_de_editorial(ivrea):
    figura = ProductoNoEditorialFactory()
    oferta(editorial=ivrea)

    assert calcular_impacto_de_baja(figura).ofertas_vigentes == 0


# ===========================================================================
# Volumen: las etiquetas y las editoriales se leen de una vez
# ===========================================================================


def _consultas_del_catalogo(cliente):
    url = reverse("core:tienda_catalogo")
    cliente.get(url)
    with CaptureQueriesContext(connection) as capturadas:
        assert cliente.get(url).status_code == 200
    return len(capturadas)


def _productos(cantidad, ivrea, evangelion):
    for indice in range(cantidad):
        producto = ProductoFactory(editorial=ivrea, stock=2)
        if indice % 2:
            producto.etiquetas.add(evangelion)


def test_el_catalogo_no_consulta_una_vez_por_producto(client, ivrea, evangelion):
    oferta(editorial=ivrea)
    oferta(etiqueta=evangelion)
    _productos(3, ivrea, evangelion)
    pocos = _consultas_del_catalogo(client)

    _productos(40, ivrea, evangelion)
    muchos = _consultas_del_catalogo(client)

    assert muchos == pocos, f"{pocos} consultas con 3 productos y {muchos} con 43"


def test_preparar_lee_todo_en_una_consulta_por_tabla(ivrea, evangelion):
    oferta(editorial=ivrea)
    oferta(etiqueta=evangelion)
    _productos(10, ivrea, evangelion)
    productos = list(Producto.objects.all())
    del_dia = OfertasDelDia()

    with CaptureQueriesContext(connection) as capturadas:
        del_dia.preparar(productos)
        precios = [del_dia.precio(producto) for producto in productos]

    assert len(capturadas) == 2
    assert len(precios) == 10


def test_sin_ofertas_indirectas_no_hay_consultas_extra(tomo):
    oferta(tipo=tomo.tipo)
    del_dia = OfertasDelDia()

    with CaptureQueriesContext(connection) as capturadas:
        del_dia.preparar([tomo])
        del_dia.precio(tomo)

    assert len(capturadas) == 0
