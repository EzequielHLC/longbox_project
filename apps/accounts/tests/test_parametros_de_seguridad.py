"""La sección Seguridad de Parámetros (`CO-130`; `CO-114`; B-12-001, plan 00, A3).

El bloqueo tras intentos fallidos y la expiración de la sesión por inactividad
salen de `ConfiguracionSistema`, como declara `CO-114`, y no de constantes.
"""

from datetime import timedelta

import pytest
from django.urls import reverse
from django.utils import timezone
from freezegun import freeze_time

from apps.accounts.forms import MENSAJE_BLOQUEO
from apps.accounts.tests.factories import PASSWORD_DE_PRUEBA
from apps.core.models import ConfiguracionSistema, RegistroAuditoria

pytestmark = pytest.mark.django_db

URL_LOGIN = reverse("accounts:login")
URL_PARAMETROS = reverse("catalog:parametros")


def _intentar(client, email, password="clave-incorrecta"):
    return client.post(URL_LOGIN, {"username": email, "password": password}, REMOTE_ADDR="10.0.0.9")


def _fijar(**valores):
    ConfiguracionSistema.obtener()
    ConfiguracionSistema.objects.update(**valores)


def test_CO130_la_seccion_seguridad_guarda_los_dos_valores_y_los_audita(client_admin):
    assert ConfiguracionSistema.obtener().expiracion_sesion_minutos == 30

    client_admin.post(
        URL_PARAMETROS,
        {
            "guardar_seguridad": "1",
            "expiracion_sesion_minutos": "45",
            "bloqueo_intentos_minutos": "20",
        },
    )

    configuracion = ConfiguracionSistema.obtener()
    assert configuracion.expiracion_sesion_minutos == 45
    assert configuracion.bloqueo_intentos_minutos == 20
    detalles = set(
        RegistroAuditoria.objects.filter(accion=RegistroAuditoria.PARAMETRO_MODIFICADO).values_list(
            "detalle", flat=True
        )
    )
    assert detalles == {
        "expiración de la sesión (min): 30 → 45",
        "bloqueo tras intentos fallidos (min): 15 → 20",
    }


def test_CO130_E2_un_valor_fuera_de_rango_no_guarda_nada(client_admin):
    respuesta = client_admin.post(
        URL_PARAMETROS,
        {
            "guardar_seguridad": "1",
            "expiracion_sesion_minutos": "0",
            "bloqueo_intentos_minutos": "20",
        },
    )

    assert respuesta.context["form_seguridad"].errors
    assert ConfiguracionSistema.obtener().bloqueo_intentos_minutos == 15


def test_CO114_E1_el_bloqueo_dura_el_periodo_parametrizado(client, cliente):
    _fijar(bloqueo_intentos_minutos=2)
    momento = timezone.now()
    with freeze_time(momento):
        for _ in range(5):
            _intentar(client, cliente.email)
        assert MENSAJE_BLOQUEO in _intentar(client, cliente.email).content.decode()

    with freeze_time(momento + timedelta(minutes=3)):
        respuesta = _intentar(client, cliente.email, password=PASSWORD_DE_PRUEBA)

    assert respuesta.status_code == 302  # con 15 minutos seguiría bloqueado


def test_CO114_la_sesion_vence_por_inactividad_segun_el_parametro(client, cliente):
    _fijar(expiracion_sesion_minutos=5)

    _intentar(client, cliente.email, password=PASSWORD_DE_PRUEBA)
    client.get(reverse("cuenta:panel"))

    assert client.session.get_expiry_age() == 5 * 60
    renovada = client.post(reverse("accounts:renovar_sesion"))
    assert renovada.json()["segundos_restantes"] == 5 * 60


def test_acceso_el_cajero_no_cambia_los_parametros_de_seguridad(client, cajero):
    client.force_login(cajero)

    respuesta = client.post(
        URL_PARAMETROS, {"guardar_seguridad": "1", "expiracion_sesion_minutos": "999"}
    )

    assert respuesta.status_code == 403
    assert ConfiguracionSistema.obtener().expiracion_sesion_minutos == 30


def test_CO207_parametros_presenta_todas_las_secciones_sin_modificar_nada(client_admin):
    """`CU-CFG-PAR` paso 2: con los módulos construidos, ya no falta ninguna sección."""
    registros = RegistroAuditoria.objects.count()

    contenido = client_admin.get(URL_PARAMETROS).content.decode()

    for seccion in ("Logística", "Comercial", "Fidelización", "Seguridad"):
        assert seccion in contenido
    for campo in (
        "dias_aviso_preventa",
        "plazo_devolucion_dias",
        "plazo_garantia_dias",
        "frecuencia_casilla_horas",
        "expiracion_sesion_minutos",
        "bloqueo_intentos_minutos",
        "caducidad_puntos_meses",
        "cantidad_minima_restock",
    ):
        assert f'name="{campo}"' in contenido
    assert RegistroAuditoria.objects.count() == registros


def test_CO053_desde_parametros_el_margen_global_se_cambia_en_su_pantalla(client_admin):
    """`CU-CFG-PAR` A1: el panel no edita el margen; enlaza a `CO-053`, que recalcula."""
    from decimal import Decimal

    from apps.catalog.tests.test_contratos_03_pricing import fijar_margen, importado

    fijar_margen("0.40")
    vinculado = importado("10000")
    panel = client_admin.get(URL_PARAMETROS).content.decode()
    assert reverse("catalog:margen") in panel
    assert 'name="margen_ganancia"' not in panel

    client_admin.post(reverse("catalog:margen"), {"margen": "50", "confirmar": "1"})

    vinculado.refresh_from_db()
    assert ConfiguracionSistema.obtener().margen_ganancia == Decimal("0.5")
    assert vinculado.precio == Decimal("15000.00")
