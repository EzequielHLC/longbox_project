"""El filtro de remitentes válidos: lo que este módulo le aporta a CU-04.

`Proveedor.objects.remitente_valido` es la única puerta por la que el pipeline
de novedades decide si procesa un correo o lo saltea. Todavía no hay pipeline,
pero la regla ya existe y se prueba sola: cuando CU-04 se implemente, va a
apoyarse en algo verificado en vez de inventarlo de nuevo dentro de una tarea de
Celery, que es donde peor se prueba.
"""

import pytest

from apps.suppliers.models import Proveedor
from apps.suppliers.tests.factories import ProveedorFactory

pytestmark = pytest.mark.django_db


def test_un_proveedor_activo_es_remitente_valido():
    proveedor = ProveedorFactory(correo_comercial="novedades@ivrea.test")

    assert Proveedor.objects.remitente_valido("novedades@ivrea.test") == proveedor


def test_un_proveedor_inactivo_no_lo_es():
    """Es el efecto de CU-20: la baja saca el correo del filtro."""
    ProveedorFactory(correo_comercial="novedades@ivrea.test", estado=Proveedor.INACTIVO)

    assert Proveedor.objects.remitente_valido("novedades@ivrea.test") is None


def test_un_proveedor_con_el_procesamiento_apagado_tampoco():
    """La otra mitad del filtro: son dos condiciones, no una."""
    ProveedorFactory(correo_comercial="novedades@ivrea.test", procesa_novedades=False)

    assert Proveedor.objects.remitente_valido("novedades@ivrea.test") is None


def test_un_correo_desconocido_no_devuelve_nada():
    """E1 de CU-04: el remitente no registrado no se procesa."""
    ProveedorFactory(correo_comercial="novedades@ivrea.test")

    assert Proveedor.objects.remitente_valido("cualquiera@spam.test") is None


@pytest.mark.parametrize("escrito", ["Novedades@Ivrea.TEST", "NOVEDADES@IVREA.TEST"])
def test_la_busqueda_ignora_las_mayusculas(escrito):
    """Un encabezado de correo puede traer cualquier caja. Comparar en crudo
    dejaría afuera mensajes legítimos, y el modo en que fallaría —silencio, sin
    error— es el peor de todos."""
    proveedor = ProveedorFactory(correo_comercial="novedades@ivrea.test")

    assert Proveedor.objects.remitente_valido(escrito) == proveedor


def test_los_espacios_alrededor_no_estorban():
    proveedor = ProveedorFactory(correo_comercial="novedades@ivrea.test")

    assert Proveedor.objects.remitente_valido("  novedades@ivrea.test ") == proveedor


@pytest.mark.parametrize("vacio", ["", None])
def test_un_remitente_vacio_no_encuentra_nada(vacio):
    """Un correo sin remitente legible no puede caer por casualidad en el primer
    proveedor de la tabla."""
    ProveedorFactory()

    assert Proveedor.objects.remitente_valido(vacio) is None


def test_activos_solo_devuelve_los_activos():
    activo = ProveedorFactory()
    ProveedorFactory(estado=Proveedor.INACTIVO)

    assert list(Proveedor.objects.activos()) == [activo]


def test_el_proveedor_se_identifica_por_su_razon_social():
    """Es lo que se lee en el log de auditoría y en los desplegables."""
    proveedor = ProveedorFactory(razon_social="Editorial Ivrea")

    assert str(proveedor) == "Editorial Ivrea"
