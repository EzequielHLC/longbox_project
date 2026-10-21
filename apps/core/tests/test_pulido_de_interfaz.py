"""Plan 00 de interfaz: diálogos de confirmación, selector de entrega y carnet.

Las confirmaciones se abren en un `<dialog>` sólo con guion: sin él, el enlace
navega a la pantalla de siempre. Por eso lo que se prueba acá es el contrato
entre las dos partes (el enlace marcado, el bloque marcado con su formulario) y
que la pantalla sigue respondiendo sola.
"""

import re
from pathlib import Path

import pytest
from django.conf import settings
from django.urls import reverse

from apps.accounts.tests.factories import UsuarioFactory
from apps.catalog.tests.factories import ProductoFactory
from apps.pedidos.models import Pedido
from apps.pedidos.tests.util import crear_pedido
from apps.tienda.tests.compra_util import (
    agregar,
    cliente_con_direccion,
    dar_puntos,
    fijar_parametros,
    producto,
)

RAIZ = Path(settings.BASE_DIR)

CONFIRMACIONES = (
    "accounts/usuario_baja",
    "accounts/usuario_eliminar",
    "almacen/retiro",
    "almacen/retiro_pedido",
    "catalog/catalogo_baja",
    "catalog/oferta_baja",
    "catalog/precio_eliminar",
    "catalog/producto_baja",
    "catalog/producto_reactivar",
    "catalog/producto_restaurar_precio",
    "core/banner_baja",
    "devoluciones/reembolso",
    "devoluciones/reembolso_medio",
    "pedidos/cancelar_preventa",
    "pedidos/pedido_avanzar",
    "suppliers/proveedor_baja",
    "suppliers/proveedor_reactivar",
)


@pytest.mark.parametrize("nombre", CONFIRMACIONES)
def test_cada_confirmacion_marca_el_bloque_que_va_al_dialogo(nombre):
    (archivo,) = RAIZ.glob(f"apps/*/templates/{nombre}.html")
    texto = archivo.read_text(encoding="utf-8")

    bloque = re.search(r"<div data-dialogo-contenido[^>]*>(.*)</div>", texto, flags=re.S)

    assert bloque, nombre
    assert '<form method="post"' in bloque.group(1)


def test_las_bajas_se_marcan_como_destructivas():
    for nombre in CONFIRMACIONES:
        (archivo,) = RAIZ.glob(f"apps/*/templates/{nombre}.html")
        critico = 'data-dialogo-contenido="critico"' in archivo.read_text(encoding="utf-8")
        assert critico == any(p in nombre for p in ("baja", "eliminar", "cancelar")), nombre


@pytest.mark.django_db
def test_sin_guion_la_confirmacion_sigue_siendo_una_pantalla(client_admin):
    pedido = crear_pedido(estado=Pedido.ARMADO)

    detalle = client_admin.get(reverse("pedidos:detalle", args=[pedido.pk])).content.decode()
    url = reverse("pedidos:avanzar", args=[pedido.pk])
    confirmacion = client_admin.get(url)

    assert f'<a data-dialogo href="{url}"' in detalle
    assert confirmacion.status_code == 200
    assert "data-dialogo-contenido" in confirmacion.content.decode()


@pytest.mark.django_db
def test_el_formulario_del_dialogo_envia_a_la_confirmacion_y_cambia_lo_mismo(client_admin):
    """El guion le pone al formulario la dirección de la confirmación: el POST
    que llega es el de siempre."""
    pedido = crear_pedido(estado=Pedido.ARMADO)

    client_admin.post(reverse("pedidos:avanzar", args=[pedido.pk]), {"estado_visto": Pedido.ARMADO})

    pedido.refresh_from_db()
    assert pedido.estado == Pedido.EMPAQUETADO


def test_el_guion_de_los_dialogos_esta_en_todas_las_pantallas():
    base = (RAIZ / "templates" / "base.html").read_text(encoding="utf-8")
    guion = (RAIZ / "templates" / "_interfaz_js.html").read_text(encoding="utf-8")

    assert '{% include "_interfaz_js.html" %}' in base
    assert "showModal()" in guion
    assert 'setAttribute("action", url)' in guion


@pytest.mark.django_db
def test_la_entrega_se_elige_con_tarjetas_de_opcion(client):
    fijar_parametros()
    cliente = cliente_con_direccion()
    client.force_login(cliente)
    agregar(client, producto(precio="10000"))

    pantalla = client.get(reverse("compra:checkout")).content.decode()

    assert 'type="radio" name="modalidad" value="envio" checked' in pantalla
    assert 'type="radio" name="modalidad" value="retiro"' in pantalla
    assert "data-enviar-al-elegir" in pantalla
    assert "data-sin-guion>Usar esta entrega</button>" in pantalla


@pytest.mark.django_db
def test_sin_saldo_suficiente_cubrir_con_puntos_esta_deshabilitado(client):
    fijar_parametros()
    cliente = cliente_con_direccion()
    dar_puntos(cliente, 10)
    client.force_login(cliente)
    agregar(client, producto(precio="10000"))

    pantalla = client.get(reverse("compra:checkout")).content.decode()

    assert re.search(
        r'<button type="submit" class="boton-menor" disabled aria-describedby="sin-saldo-', pantalla
    )


@pytest.mark.django_db
def test_el_carnet_muestra_codigo_saldo_y_lo_guardado(client):
    cliente = UsuarioFactory(rol="cliente")
    dar_puntos(cliente, 750)
    client.force_login(cliente)

    pantalla = client.get(reverse("cuenta:panel")).content.decode()

    assert "Carnet de cliente" in pantalla
    assert cliente.codigo_cliente in pantalla
    assert '<span class="datos">750</span> pts' in pantalla
    assert "Nada guardado" in pantalla
    assert 'aria-label="Secciones de mi cuenta"' in pantalla


@pytest.mark.django_db
def test_cada_pedido_de_la_lista_lleva_su_riel_y_sus_portadas(client):
    cliente = UsuarioFactory(rol="cliente")
    crear_pedido(cliente, lineas=(("1000", 1), ("1000", 1), ("1000", 1), ("1000", 1)))
    client.force_login(cliente)

    respuesta = client.get(reverse("cuenta:pedidos"))
    (pedido,) = respuesta.context["en_curso"]

    assert len(pedido.portadas) == 3
    assert pedido.mas_productos == 1
    assert "riel riel--reducido" in respuesta.content.decode()


@pytest.mark.django_db
def test_el_pago_aprobado_de_una_cuenta_lleva_a_su_pedido(client):
    from apps.tienda.tests.compra_util import avisar, confirmar

    fijar_parametros()
    cliente = cliente_con_direccion()
    client.force_login(cliente)
    agregar(client, ProductoFactory(stock=3))
    _, cobro = confirmar(client)
    avisar(client, cobro)
    cobro.refresh_from_db()

    pantalla = client.get(reverse("compra:resultado", args=[cobro.referencia])).content.decode()

    url = reverse("cuenta:pedido", args=[cobro.pedido.numero])
    assert f'<a href="{url}" class="boton-primario">Ver mi pedido</a>' in pantalla


# ---------------------------------------------------------------------------
# Segunda parte: U1 a U5 y P1 a P7
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_U1_las_sugerencias_traen_las_primeras_coincidencias_visibles(client):
    for numero in range(7):
        ProductoFactory(titulo=f"Berserk {numero}", stock=3)
    ProductoFactory(titulo="Monster", stock=3)

    respuesta = client.get(reverse("core:tienda_sugerencias"), {"q": "berser"})

    assert len(respuesta.context["productos"]) == 5
    assert all("Berserk" in p.titulo for p in respuesta.context["productos"])
    assert "Ver todos los resultados" in respuesta.content.decode()


@pytest.mark.django_db
def test_U1_con_menos_de_dos_letras_no_sugiere_nada(client):
    ProductoFactory(titulo="Berserk", stock=3)

    respuesta = client.get(reverse("core:tienda_sugerencias"), {"q": "b"})

    assert respuesta.context["productos"] == []
    assert respuesta.content.decode().strip() == ""


@pytest.mark.django_db
def test_U5_el_menu_del_administrador_cuenta_lo_que_espera(client_admin):
    crear_pedido(estado=Pedido.PENDIENTE_ARMADO)
    crear_pedido(estado=Pedido.PENDIENTE_ARMADO)
    crear_pedido(estado=Pedido.DESPACHADO)

    pantalla = client_admin.get(reverse("pedidos:lista")).content.decode()

    assert '<span class="sr-only">, </span>2<span class="sr-only"> por armar</span>' in pantalla


@pytest.mark.django_db
def test_U5_el_cajero_no_ve_contadores(client, cajero):
    crear_pedido(estado=Pedido.PENDIENTE_ARMADO)
    client.force_login(cajero)

    assert "contador-menu" not in client.get(reverse("core:mostrador")).content.decode()


@pytest.mark.django_db
def test_P1_los_pasos_de_la_compra_marcan_el_actual(client):
    fijar_parametros()
    agregar(client, producto())

    pantalla = client.get(reverse("tienda:carrito")).content.decode()

    assert 'class="pasos-compra"' in pantalla
    assert 'pasos-compra__paso--actual" aria-current="step"' in pantalla
    assert pantalla.index("Carrito</span>") < pantalla.index("Entrega</span>")


@pytest.mark.django_db
def test_P2_sin_imagen_la_tarjeta_dibuja_una_tapa_con_el_titulo(client):
    ProductoFactory(titulo="Akira", stock=3, portada=None)

    pantalla = client.get(reverse("core:tienda_catalogo")).content.decode()

    assert 'class="portada-vacia portada-vacia--tapa"' in pantalla
    assert '<span class="portada-vacia__titulo">Akira</span>' in pantalla


@pytest.mark.django_db
def test_P7_la_lista_de_pedidos_lleva_el_riel_reducido_y_la_venta_de_mostrador_no(client_admin):
    from apps.pedidos.tests.util import como_venta_de_mostrador

    online = crear_pedido(estado=Pedido.ARMADO)
    mostrador = como_venta_de_mostrador(crear_pedido(estado=Pedido.DESPACHADO))

    pantalla = client_admin.get(reverse("pedidos:lista")).content.decode()

    assert pantalla.count('class="riel-de-fila"') == 1
    assert online.numero in pantalla and mostrador.numero in pantalla


def test_P3_el_guion_marca_el_boton_y_frena_el_doble_envio():
    guion = (RAIZ / "templates" / "_interfaz_js.html").read_text(encoding="utf-8")

    assert 'boton.setAttribute("aria-busy", "true")' in guion
    assert "formulario.dataset.enviando" in guion
    assert 'window.addEventListener("submit"' in guion


def test_lo_que_se_toca_dentro_de_una_tarjeta_queda_sobre_su_enlace():
    """B-00-024: el enlace que cubre la tarjeta tapaba «Cancelar aviso»."""
    hoja = (RAIZ / "static" / "css" / "longbox.css").read_text(encoding="utf-8")

    assert ".pedido-de-cuenta__numero::after" in hoja
    regla = ".pedido-de-cuenta__cierre :is(a, button, form, label, input) "
    assert regla + "{ position: relative; z-index: 1; }" in hoja


@pytest.mark.django_db
def test_la_lista_de_pedidos_separa_estado_y_seguimiento(client_admin):
    crear_pedido(estado=Pedido.ARMADO)

    pantalla = client_admin.get(reverse("pedidos:lista")).content.decode()

    assert "<th>Estado</th>\n            <th>Seguimiento</th>" in pantalla
