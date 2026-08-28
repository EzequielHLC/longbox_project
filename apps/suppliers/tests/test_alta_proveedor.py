"""CU-18 — Registrar Proveedor Editorial.

Lo que se prueba acá no es un CRUD: es que el alta deje bien puesta la única
cosa que este módulo le aporta al resto del sistema, que es el filtro de
remitentes válidos del procesamiento automático de CU-04.
"""

import pytest
from django.urls import reverse

from apps.accounts.tests.factories import UsuarioFactory
from apps.core.models import RegistroAuditoria
from apps.suppliers.models import Proveedor
from apps.suppliers.tests.factories import ProveedorFactory

pytestmark = pytest.mark.django_db

URL_ALTA = reverse("suppliers:proveedor_alta")


def datos(**cambios):
    """El POST del alta. Solo los dos primeros son obligatorios (CU-18 paso 2).

    `procesa_novedades` viaja marcado porque así se dibuja el formulario: el
    campo nace en `True` para que se cumpla literal la postcondición del CU
    —el correo queda habilitado como remitente sin que nadie lo prenda— y una
    casilla desmarcada simplemente no viaja en el POST.
    """
    completo = {
        "razon_social": "Editorial Ivrea",
        "correo_comercial": "novedades@ivrea.test",
        "procesa_novedades": "on",
        "editorial": "",
        "tipo_por_defecto": "",
        "nombre_contacto": "",
        "telefono": "",
        "notas": "",
    }
    completo.update(cambios)
    return completo


def test_el_alta_deja_el_proveedor_activo(client_admin):
    """Postcondición del CU: queda registrado con estado Activo."""
    respuesta = client_admin.post(URL_ALTA, datos())

    proveedor = Proveedor.objects.get()
    assert respuesta.status_code == 302
    assert respuesta.url == reverse("suppliers:proveedor_detalle", args=[proveedor.pk])
    assert proveedor.razon_social == "Editorial Ivrea"
    assert proveedor.estado == Proveedor.ACTIVO


def test_el_correo_queda_habilitado_como_remitente_valido(client_admin):
    """La otra postcondición, y la que le da sentido al módulo entero."""
    client_admin.post(URL_ALTA, datos())

    assert Proveedor.objects.remitente_valido("novedades@ivrea.test") is not None


def test_los_campos_opcionales_no_traban_el_alta(client_admin):
    """E1 solo se dispara con los obligatorios: nombre de contacto, teléfono y
    notas pueden quedar vacíos."""
    assert client_admin.post(URL_ALTA, datos()).status_code == 302
    proveedor = Proveedor.objects.get()
    assert proveedor.nombre_contacto == ""
    assert proveedor.telefono == ""


def test_los_campos_opcionales_se_guardan_cuando_vienen(client_admin):
    client_admin.post(
        URL_ALTA,
        datos(nombre_contacto="Laura Gómez", telefono="+54 376 400000", notas="Paga a 30 días."),
    )

    proveedor = Proveedor.objects.get()
    assert proveedor.nombre_contacto == "Laura Gómez"
    assert proveedor.telefono == "+54 376 400000"
    assert proveedor.notas == "Paga a 30 días."


@pytest.mark.parametrize("faltante", ["razon_social", "correo_comercial"])
def test_falta_un_campo_obligatorio_y_no_procede(client_admin, faltante):
    """E1: se resaltan los faltantes y el formulario permanece abierto."""
    respuesta = client_admin.post(URL_ALTA, datos(**{faltante: ""}))

    assert respuesta.status_code == 200
    assert respuesta.context["form"].errors[faltante]
    assert not Proveedor.objects.exists()


# ---------------------------------------------------------------------------
# E2 — conflictos de unicidad
# ---------------------------------------------------------------------------


def test_una_razon_social_repetida_es_rechazada(client_admin):
    ProveedorFactory(razon_social="Editorial Ivrea")

    respuesta = client_admin.post(URL_ALTA, datos())

    assert respuesta.status_code == 200
    assert respuesta.context["form"].errors["razon_social"]
    assert Proveedor.objects.count() == 1


def test_un_correo_repetido_es_rechazado(client_admin):
    ProveedorFactory(razon_social="Otra editorial", correo_comercial="novedades@ivrea.test")

    respuesta = client_admin.post(URL_ALTA, datos())

    assert respuesta.status_code == 200
    assert respuesta.context["form"].errors["correo_comercial"]
    assert Proveedor.objects.count() == 1


def test_el_conflicto_se_informa_con_enlace_a_la_ficha_existente(client_admin):
    """E2 lo pide explícitamente: sin el enlace, el aviso obligaría a salir a
    buscar el proveedor a mano."""
    existente = ProveedorFactory(razon_social="Editorial Ivrea")

    respuesta = client_admin.post(URL_ALTA, datos())

    assert respuesta.context["conflicto"] == existente
    ficha = reverse("suppliers:proveedor_detalle", args=[existente.pk])
    assert ficha in respuesta.content.decode()


def test_la_razon_social_repetida_se_detecta_sin_distinguir_mayusculas(client_admin):
    """ "Editorial Ivrea" y "EDITORIAL IVREA" son el mismo proveedor escrito
    distinto: con dos filas habría dos agendas del mismo interlocutor."""
    ProveedorFactory(razon_social="Editorial Ivrea")

    respuesta = client_admin.post(URL_ALTA, datos(razon_social="  EDITORIAL   IVREA "))

    assert respuesta.status_code == 200
    assert Proveedor.objects.count() == 1


def test_el_correo_repetido_se_detecta_sin_distinguir_mayusculas(client_admin):
    ProveedorFactory(correo_comercial="novedades@ivrea.test")

    respuesta = client_admin.post(URL_ALTA, datos(correo_comercial="Novedades@Ivrea.TEST"))

    assert respuesta.status_code == 200
    assert Proveedor.objects.count() == 1


# ---------------------------------------------------------------------------
# Normalización
# ---------------------------------------------------------------------------


def test_una_razon_social_de_una_letra_es_rechazada(client_admin):
    """Una sola letra no distingue a nadie y casi siempre es un enter de más."""
    respuesta = client_admin.post(URL_ALTA, datos(razon_social="I"))

    assert respuesta.status_code == 200
    assert respuesta.context["form"].errors["razon_social"]
    assert not Proveedor.objects.exists()


def test_la_razon_social_se_normaliza(client_admin):
    client_admin.post(URL_ALTA, datos(razon_social="  Editorial   Ivrea  "))

    assert Proveedor.objects.get().razon_social == "Editorial Ivrea"


def test_el_correo_se_guarda_en_minuscula(client_admin):
    """Es la clave con la que CU-04 reconoce un remitente: normalizarlo al
    guardar hace que la búsqueda del pipeline y la pantalla digan lo mismo."""
    client_admin.post(URL_ALTA, datos(correo_comercial="  Novedades@Ivrea.TEST  "))

    assert Proveedor.objects.get().correo_comercial == "novedades@ivrea.test"


# ---------------------------------------------------------------------------
# Auditoría y permisos
# ---------------------------------------------------------------------------


def test_el_alta_queda_auditada(client_admin, administrador):
    client_admin.post(URL_ALTA, datos())

    registro = RegistroAuditoria.objects.get(accion=RegistroAuditoria.ALTA_PROVEEDOR)
    assert registro.actor == administrador
    assert registro.objetivo == Proveedor.objects.get()
    assert registro.objetivo_email == "novedades@ivrea.test"
    assert "Editorial Ivrea" in registro.detalle


@pytest.mark.parametrize("rol_sin_permiso", ["cliente", "cajero"])
def test_solo_el_administrador_da_de_alta_proveedores(client, rol_sin_permiso):
    client.force_login(UsuarioFactory(rol=rol_sin_permiso))

    assert client.get(URL_ALTA).status_code == 403
    assert client.post(URL_ALTA, datos()).status_code == 403
    assert not Proveedor.objects.exists()


def test_sin_sesion_el_alta_redirige_al_login(client):
    respuesta = client.get(URL_ALTA)

    assert respuesta.status_code == 302
    assert reverse("accounts:login") in respuesta.url
