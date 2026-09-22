"""CU-PRV-BAJ — Dar de Baja Proveedor Editorial, y la reactivación que lo revierte.

La baja tiene dos mitades que conviene no confundir: el **informe de impacto**
(pasos 2 y 3, lo que el Administrador lee antes de decidir) y el **efecto**
(paso 5, sacar el correo del filtro de remitentes sin perder el historial).
"""

import pytest
from django.urls import reverse

from apps.accounts.tests.factories import UsuarioFactory
from apps.catalog.tests.factories import ProductoFactory
from apps.core.models import RegistroAuditoria
from apps.suppliers.models import Proveedor
from apps.suppliers.tests.factories import ProveedorFactory

pytestmark = pytest.mark.django_db


def url_baja(proveedor):
    return reverse("suppliers:proveedor_baja", args=[proveedor.pk])


def url_reactivar(proveedor):
    return reverse("suppliers:proveedor_reactivar", args=[proveedor.pk])


# ---------------------------------------------------------------------------
# El informe de impacto (pasos 2 y 3)
# ---------------------------------------------------------------------------


def test_el_informe_cuenta_los_productos_vinculados(client_admin):
    proveedor = ProveedorFactory()
    ProductoFactory(proveedor=proveedor)
    ProductoFactory(proveedor=proveedor)
    ProductoFactory()  # de otro proveedor: no cuenta

    respuesta = client_admin.get(url_baja(proveedor))

    assert respuesta.status_code == 200
    assert respuesta.context["impacto"].productos_vinculados == 2


def test_sin_impacto_el_informe_lo_dice_explicitamente(client_admin):
    """A1: si no hay impacto, el informe lo indica en vez de mostrarse vacío."""
    proveedor = ProveedorFactory()

    respuesta = client_admin.get(url_baja(proveedor))

    assert respuesta.context["impacto"].hay_impacto is False
    assert "No hay productos del catálogo vinculados" in respuesta.content.decode()


def test_el_informe_no_afirma_que_no_hay_propuestas_de_restock(client_admin):
    """El módulo de Restock no existe todavía. Decir "0 propuestas afectadas"
    sería mentir sobre un dato que el propio CU considera parte de la decisión;
    la pantalla dice que no se puede determinar."""
    proveedor = ProveedorFactory()

    respuesta = client_admin.get(url_baja(proveedor))

    assert respuesta.context["impacto"].propuestas_de_restock is None
    assert "No disponible todavía" in respuesta.content.decode()


def test_mirar_el_informe_no_da_de_baja_nada(client_admin):
    """A2: el Administrador puede revisar el impacto y no confirmar."""
    proveedor = ProveedorFactory()

    client_admin.get(url_baja(proveedor))

    proveedor.refresh_from_db()
    assert proveedor.estado == Proveedor.ACTIVO


# ---------------------------------------------------------------------------
# El efecto de la baja (paso 5)
# ---------------------------------------------------------------------------


def test_la_baja_deja_el_proveedor_inactivo(client_admin):
    proveedor = ProveedorFactory()

    respuesta = client_admin.post(url_baja(proveedor))

    proveedor.refresh_from_db()
    assert respuesta.status_code == 302
    assert proveedor.estado == Proveedor.INACTIVO


def test_la_baja_saca_el_correo_del_filtro_de_remitentes(client_admin):
    """Es la postcondición que le da sentido a la baja: el pipeline de CU-ALT-NOV
    deja de procesar sus mensajes."""
    proveedor = ProveedorFactory(correo_comercial="novedades@ivrea.test")

    client_admin.post(url_baja(proveedor))

    assert Proveedor.objects.remitente_valido("novedades@ivrea.test") is None


def test_los_productos_conservan_la_referencia_al_proveedor(client_admin):
    """La baja es lógica: el CU pide expresamente que el historial sobreviva."""
    proveedor = ProveedorFactory()
    producto = ProductoFactory(proveedor=proveedor)

    client_admin.post(url_baja(proveedor))

    producto.refresh_from_db()
    assert producto.proveedor == proveedor
    assert Proveedor.objects.filter(pk=proveedor.pk).exists()


def test_la_baja_queda_auditada_con_el_impacto(client_admin, administrador):
    proveedor = ProveedorFactory(razon_social="Editorial Ivrea")
    ProductoFactory(proveedor=proveedor)

    client_admin.post(url_baja(proveedor))

    registro = RegistroAuditoria.objects.get(accion=RegistroAuditoria.BAJA_PROVEEDOR)
    assert registro.actor == administrador
    assert registro.objetivo == proveedor
    assert "Editorial Ivrea" in registro.detalle
    assert "1" in registro.detalle


def test_dar_de_baja_dos_veces_no_registra_dos_bajas(client_admin):
    """El doble envío del formulario es el caso normal, no el raro."""
    proveedor = ProveedorFactory()

    client_admin.post(url_baja(proveedor))
    client_admin.post(url_baja(proveedor))

    assert RegistroAuditoria.objects.filter(accion=RegistroAuditoria.BAJA_PROVEEDOR).count() == 1


# ---------------------------------------------------------------------------
# La vuelta: CU-PRV-REA, con CO-065 y CO-066 (ver la vista)
# ---------------------------------------------------------------------------


def test_reactivar_devuelve_el_correo_al_filtro_de_remitentes(client_admin):
    proveedor = ProveedorFactory(correo_comercial="novedades@ivrea.test", estado=Proveedor.INACTIVO)

    respuesta = client_admin.post(url_reactivar(proveedor))

    proveedor.refresh_from_db()
    assert respuesta.status_code == 302
    assert proveedor.estado == Proveedor.ACTIVO
    assert Proveedor.objects.remitente_valido("novedades@ivrea.test") == proveedor


def test_reactivar_conserva_los_datos_y_el_historial(client_admin):
    proveedor = ProveedorFactory(nombre_contacto="Laura", estado=Proveedor.INACTIVO)
    producto = ProductoFactory(proveedor=proveedor)

    client_admin.post(url_reactivar(proveedor))

    proveedor.refresh_from_db()
    assert proveedor.nombre_contacto == "Laura"
    # Se compara la fila y no la instancia: `proveedor.productos` devuelve
    # instancias del padre y acá se tiene una de la hija, y para Django dos
    # modelos concretos distintos nunca son iguales aunque compartan clave.
    assert producto.pk in proveedor.productos.values_list("pk", flat=True)


def test_reactivar_queda_auditado(client_admin):
    proveedor = ProveedorFactory(estado=Proveedor.INACTIVO)

    client_admin.post(url_reactivar(proveedor))

    assert RegistroAuditoria.objects.filter(
        accion=RegistroAuditoria.REACTIVACION_PROVEEDOR
    ).exists()


def test_reactivar_uno_ya_activo_no_hace_nada(client_admin):
    proveedor = ProveedorFactory()

    client_admin.post(url_reactivar(proveedor))

    assert not RegistroAuditoria.objects.filter(
        accion=RegistroAuditoria.REACTIVACION_PROVEEDOR
    ).exists()


def test_la_baja_no_bloquea_la_razon_social_para_siempre(client_admin):
    """Es el motivo por el que la reactivación existe: la razón social y el
    correo son únicos *en cualquier estado*, así que sin vuelta atrás un
    proveedor dado de baja se bloquearía a sí mismo."""
    proveedor = ProveedorFactory(razon_social="Editorial Ivrea")
    client_admin.post(url_baja(proveedor))

    client_admin.post(url_reactivar(proveedor))

    proveedor.refresh_from_db()
    assert proveedor.estado == Proveedor.ACTIVO
    assert Proveedor.objects.filter(razon_social="Editorial Ivrea").count() == 1


# ---------------------------------------------------------------------------
# Permisos
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("rol_sin_permiso", ["cliente", "cajero"])
def test_solo_el_administrador_da_de_baja(client, rol_sin_permiso):
    proveedor = ProveedorFactory()
    client.force_login(UsuarioFactory(rol=rol_sin_permiso))

    assert client.get(url_baja(proveedor)).status_code == 403
    assert client.post(url_baja(proveedor)).status_code == 403
    proveedor.refresh_from_db()
    assert proveedor.estado == Proveedor.ACTIVO


@pytest.mark.parametrize("rol_sin_permiso", ["cliente", "cajero"])
def test_solo_el_administrador_reactiva(client, rol_sin_permiso):
    proveedor = ProveedorFactory(estado=Proveedor.INACTIVO)
    client.force_login(UsuarioFactory(rol=rol_sin_permiso))

    assert client.post(url_reactivar(proveedor)).status_code == 403
    proveedor.refresh_from_db()
    assert proveedor.estado == Proveedor.INACTIVO
