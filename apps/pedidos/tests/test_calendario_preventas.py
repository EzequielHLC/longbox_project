"""El calendario de las pre-ventas por llegar (plan 00 de interfaz, tercera parte, 22).

Se arma con los mismos grupos que la lista: lo que dice el calendario no puede
ser distinto de lo que se ingresa abajo.
"""

from datetime import date, timedelta

import pytest
from django.urls import reverse
from django.utils import timezone

from apps.accounts.tests.factories import UsuarioFactory
from apps.pedidos import calendario, preventa
from apps.pedidos.tests.util import crear_preventa, reservar

pytestmark = pytest.mark.django_db

URL = reverse("pedidos:preventas")


def test_el_mes_pedido_se_entiende_y_lo_ilegible_es_el_actual():
    assert calendario.mes_pedido("2026-11") == date(2026, 11, 1)
    assert calendario.mes_pedido("cualquier cosa") == timezone.localdate().replace(day=1)
    assert calendario.mes_pedido(None) == timezone.localdate().replace(day=1)


def test_el_mes_empieza_en_lunes_y_completa_sus_semanas():
    mes = calendario.mes_de(date(2026, 11, 1), [])

    assert all(len(semana) == 7 for semana in mes.semanas)
    assert all(semana[0].fecha.weekday() == 0 for semana in mes.semanas)
    assert mes.nombre == "Noviembre 2026"
    assert (mes.anterior, mes.siguiente) == (date(2026, 10, 1), date(2026, 12, 1))


def test_cada_llegada_cae_en_su_dia_con_los_grupos_de_la_lista():
    llega = crear_preventa(dias=3)
    grupos = preventa.por_llegar()

    mes = calendario.mes_de(llega.llegada_vigente.replace(day=1), grupos)

    (dia,) = [d for semana in mes.semanas for d in semana if d.fecha == llega.llegada_vigente]
    assert [g.clave for g in dia.grupos] == [grupos[0].clave]
    assert dia in mes.dias_con_llegadas


def test_las_cifras_cuentan_productos_reservas_semana_y_atrasos():
    cliente = UsuarioFactory(rol="cliente")
    atrasado = crear_preventa(dias=-2)
    reservar(cliente, atrasado, cantidad=3)
    crear_preventa(dias=4)
    crear_preventa(dias=30)

    resumen = calendario.resumen(preventa.por_llegar())

    assert resumen == {"productos": 3, "reservadas": 3, "esta_semana": 1, "atrasados": 1}


@pytest.mark.parametrize(
    ("dias", "cuando"),
    [(-1, "Atrasado"), (0, "Llega hoy"), (1, "Llega mañana"), (5, "Llega en 5 días")],
)
def test_cada_grupo_dice_cuando_llega_con_palabras(dias, cuando):
    crear_preventa(dias=dias)

    (grupo,) = preventa.por_llegar()

    assert grupo.cuando == cuando
    assert grupo.cercano is (dias <= 7)


def test_la_pantalla_dibuja_el_mes_y_lleva_de_cada_llegada_a_su_grupo(client_admin):
    crear_preventa(dias=2)

    respuesta = client_admin.get(URL)
    contenido = respuesta.content.decode()
    (grupo,) = respuesta.context["grupos"]

    assert 'class="calendario"' in contenido
    assert f'href="#grupo-{grupo.clave}"' in contenido
    assert f'id="grupo-{grupo.clave}" open' in contenido
    assert 'aria-current="date"' in contenido


def test_se_navega_de_mes_en_mes_por_la_direccion(client_admin):
    siguiente = (timezone.localdate().replace(day=1) + timedelta(days=31)).replace(day=1)

    respuesta = client_admin.get(URL, {"mes": siguiente.strftime("%Y-%m")})

    assert respuesta.context["mes"].primero == siguiente


def test_ver_el_calendario_no_cambia_nada(client_admin):
    producto = crear_preventa(dias=2)

    client_admin.get(URL)

    producto.refresh_from_db()
    assert producto.stock == 0
