"""Pruebas de contrato del módulo 11 · Cuenta de Cliente (CU-CLI-CON).

Se escriben desde el contrato, según `docs/pruebas/ESPECIFICACION.md` apartado 3.
Las dos operaciones son consultas: su prueba es ejercerlas por la dirección real
y afirmar que nada cambió. Como el padrón contiene datos personales (Ley
25.326), el control de acceso se ejerce con cada rol equivocado.
"""

import re

import pytest
from django.urls import reverse
from django.utils import timezone

from apps.accounts.models import Usuario
from apps.accounts.tests.factories import UsuarioFactory
from apps.core.models import RegistroAuditoria

pytestmark = pytest.mark.django_db

URL_PADRON = reverse("accounts:cliente_lista")


def url_ficha(cliente):
    return reverse("accounts:cliente_ficha", args=[cliente.pk])


@pytest.fixture
def lucia(db):
    return UsuarioFactory(
        rol=Usuario.CLIENTE,
        first_name="Lucía",
        last_name="Gómez",
        email="lucia@correo.test",
        direccion="San Martín 1234",
        localidad="Posadas",
        provincia="Misiones",
        codigo_postal="3300",
        fecha_aceptacion_politica=timezone.now(),
    )


def _foto(usuario):
    usuario.refresh_from_db()
    return (usuario.estado, usuario.email, usuario.direccion, usuario.password)


# ---------------------------------------------------------------------------
# CO-194 · consultarCuentasDeCliente
# ---------------------------------------------------------------------------


def test_CO194_el_padron_lista_nombre_correo_estado_y_registro(client_admin, lucia):
    antes = _foto(lucia)
    registros = RegistroAuditoria.objects.count()

    contenido = client_admin.get(URL_PADRON).content.decode()

    assert "Lucía Gómez" in contenido
    assert "lucia@correo.test" in contenido
    assert lucia.get_estado_display() in contenido
    # En hora local: entre las 21 y las 24 de Buenos Aires, en UTC ya es mañana.
    assert timezone.localtime(lucia.date_joined).strftime("%d/%m/%Y") in contenido
    # Postcondición: ninguna.
    assert _foto(lucia) == antes
    assert RegistroAuditoria.objects.count() == registros


def test_CO194_A1_sin_coincidencias_lo_informa(client_admin, lucia):
    contenido = client_admin.get(URL_PADRON, {"q": "nadie-se-llama-asi"}).content.decode()

    assert "Ningún cliente coincide" in contenido


@pytest.mark.parametrize("rol", [Usuario.CAJERO, Usuario.CLIENTE])
def test_CO194_E1_por_la_direccion_real_con_otro_rol_se_deniega(client, rol):
    client.force_login(UsuarioFactory(rol=rol))

    assert client.get(URL_PADRON).status_code == 403


def test_CO194_E1_sin_sesion_no_se_ve_el_padron(client, lucia):
    respuesta = client.get(URL_PADRON)

    assert respuesta.status_code == 302
    assert "lucia@correo.test" not in respuesta.content.decode()


# ---------------------------------------------------------------------------
# CO-195 · consultarFichaDeCliente
# ---------------------------------------------------------------------------


def test_CO195_la_ficha_presenta_los_datos_que_declara_el_contrato(client_admin, lucia):
    contenido = client_admin.get(url_ficha(lucia)).content.decode()

    # Identificación, contacto, domicilio, estado, registro y aceptación de la política.
    assert "Lucía Gómez" in contenido
    assert "lucia@correo.test" in contenido
    assert "San Martín 1234" in contenido
    assert "Posadas" in contenido
    assert "Misiones" in contenido
    assert lucia.get_estado_display() in contenido
    # En hora local: entre las 21 y las 24 de Buenos Aires, en UTC ya es mañana.
    assert timezone.localtime(lucia.date_joined).strftime("%d/%m/%Y") in contenido
    assert timezone.localtime(lucia.fecha_aceptacion_politica).strftime("%d/%m/%Y") in contenido


def test_CO195_la_ficha_no_ofrece_ninguna_modificacion(client_admin, lucia):
    """«Sin acciones de modificación»: ni formularios ni enlaces a operaciones."""
    contenido = client_admin.get(url_ficha(lucia)).content.decode()
    cuerpo = contenido[contenido.index('<main class="area-de-trabajo">') :]
    cuerpo = cuerpo[: cuerpo.index("</main>")]

    assert "<form" not in cuerpo
    destinos = re.findall(r'<a href="([^"]+)"', cuerpo)
    # B-10-011: además de volver, sólo sus puntos (CU-PTS-ADM), que no tocan datos personales.
    assert destinos == [URL_PADRON, reverse("accounts:cliente_puntos", args=[lucia.pk])]


def test_CO195_la_ficha_no_modifica_el_estado(client_admin, lucia):
    antes = _foto(lucia)
    registros = RegistroAuditoria.objects.count()

    client_admin.get(url_ficha(lucia))

    assert _foto(lucia) == antes
    assert RegistroAuditoria.objects.count() == registros


@pytest.mark.parametrize("rol", [Usuario.CAJERO, Usuario.CLIENTE])
def test_CO195_por_la_direccion_real_con_otro_rol_se_deniega(client, lucia, rol):
    client.force_login(UsuarioFactory(rol=rol))

    respuesta = client.get(url_ficha(lucia))

    assert respuesta.status_code == 403
    assert "San Martín 1234" not in respuesta.content.decode()


def test_CO195_una_cuenta_de_personal_no_tiene_ficha_de_cliente(client_admin, administrador):
    assert client_admin.get(url_ficha(administrador)).status_code == 404
