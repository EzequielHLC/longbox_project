"""CU-19 — Editar Proveedor Editorial.

El punto delicado no es guardar campos: es que cambiar el correo comercial
**redirige el pipeline de CU-04**, y que esa consecuencia se confirme del lado
del servidor y no solo con un cartel del navegador.
"""

import pytest
from django.urls import reverse

from apps.accounts.tests.factories import UsuarioFactory
from apps.core.models import RegistroAuditoria
from apps.suppliers.forms import ADVERTENCIA_CAMBIO_DE_CORREO
from apps.suppliers.models import Proveedor
from apps.suppliers.tests.factories import ProveedorFactory

pytestmark = pytest.mark.django_db


def url(proveedor):
    return reverse("suppliers:proveedor_edicion", args=[proveedor.pk])


def datos(proveedor, **cambios):
    """El POST de la edición, con los valores actuales del proveedor.

    Una casilla desmarcada no viaja en el POST, así que `procesa_novedades`
    aparece solo cuando está prendido — que es exactamente lo que manda el
    navegador.
    """
    completo = {
        "razon_social": proveedor.razon_social,
        "correo_comercial": proveedor.correo_comercial,
        "editorial": proveedor.editorial_id or "",
        "tipo_por_defecto": proveedor.tipo_por_defecto_id or "",
        "nombre_contacto": proveedor.nombre_contacto,
        "telefono": proveedor.telefono,
        "notas": proveedor.notas,
    }
    if proveedor.procesa_novedades:
        completo["procesa_novedades"] = "on"
    completo.update(cambios)
    return completo


def test_se_editan_los_datos_de_contacto(client_admin):
    proveedor = ProveedorFactory()

    respuesta = client_admin.post(
        url(proveedor), datos(proveedor, nombre_contacto="Laura Gómez", telefono="376400000")
    )

    proveedor.refresh_from_db()
    assert respuesta.status_code == 302
    assert proveedor.nombre_contacto == "Laura Gómez"
    assert proveedor.telefono == "376400000"


# ---------------------------------------------------------------------------
# A1 — el cambio de correo se confirma, y lo exige el servidor
# ---------------------------------------------------------------------------


def test_cambiar_el_correo_sin_confirmar_es_rechazado(client_admin):
    """La advertencia del CU no es informativa: es una puerta.

    Si viviera solo en el JavaScript, una pestaña de herramientas abierta
    alcanzaría para sacar del filtro de remitentes el correo por el que entra
    todo el pipeline de novedades.
    """
    proveedor = ProveedorFactory(correo_comercial="viejo@ivrea.test")

    respuesta = client_admin.post(
        url(proveedor), datos(proveedor, correo_comercial="nuevo@ivrea.test")
    )

    proveedor.refresh_from_db()
    assert respuesta.status_code == 200
    assert respuesta.context["form"].errors["correo_comercial"] == [ADVERTENCIA_CAMBIO_DE_CORREO]
    assert proveedor.correo_comercial == "viejo@ivrea.test"


def test_cambiar_el_correo_confirmado_redirige_el_pipeline(client_admin):
    """Postcondición del CU: CU-04 empieza a procesar el nuevo y deja de
    procesar el anterior a partir de la confirmación."""
    proveedor = ProveedorFactory(correo_comercial="viejo@ivrea.test")

    respuesta = client_admin.post(
        url(proveedor),
        datos(proveedor, correo_comercial="nuevo@ivrea.test", confirma_cambio_de_correo="on"),
    )

    assert respuesta.status_code == 302
    assert Proveedor.objects.remitente_valido("nuevo@ivrea.test") == proveedor
    assert Proveedor.objects.remitente_valido("viejo@ivrea.test") is None


def test_editar_otros_campos_no_pide_confirmacion(client_admin):
    """La confirmación es del cambio de correo, no de la edición: pedirla
    siempre la convertiría en un clic automático."""
    proveedor = ProveedorFactory()

    respuesta = client_admin.post(url(proveedor), datos(proveedor, telefono="376400000"))

    assert respuesta.status_code == 302


def test_el_alta_no_ofrece_la_confirmacion_de_cambio_de_correo(client_admin):
    """En un alta no hay correo anterior que invalidar."""
    respuesta = client_admin.get(reverse("suppliers:proveedor_alta"))

    assert "confirma_cambio_de_correo" not in respuesta.context["form"].fields


# ---------------------------------------------------------------------------
# Conflictos y estado
# ---------------------------------------------------------------------------


def test_un_correo_de_otro_proveedor_es_rechazado(client_admin):
    """E2: no se puede pisar el remitente de otro. Si se pudiera, qué proveedor
    "es" un mensaje dependería del orden de la consulta."""
    ProveedorFactory(correo_comercial="ocupado@ivrea.test")
    proveedor = ProveedorFactory(correo_comercial="propio@ivrea.test")

    respuesta = client_admin.post(
        url(proveedor),
        datos(proveedor, correo_comercial="ocupado@ivrea.test", confirma_cambio_de_correo="on"),
    )

    proveedor.refresh_from_db()
    assert respuesta.status_code == 200
    assert respuesta.context["form"].errors["correo_comercial"]
    assert proveedor.correo_comercial == "propio@ivrea.test"


def test_guardar_sin_cambiar_el_correo_propio_no_choca_consigo_mismo(client_admin):
    proveedor = ProveedorFactory()

    assert client_admin.post(url(proveedor), datos(proveedor)).status_code == 302


def test_un_proveedor_inactivo_si_se_puede_editar(client_admin):
    """La precondición de CU-19 dice "cualquier estado", y acá no hay nada que
    congelar: un proveedor de baja no habilita nada mientras lo esté, porque el
    filtro de remitentes mira el estado antes que el correo."""
    proveedor = ProveedorFactory(estado=Proveedor.INACTIVO)

    respuesta = client_admin.post(url(proveedor), datos(proveedor, telefono="376400000"))

    proveedor.refresh_from_db()
    assert respuesta.status_code == 302
    assert proveedor.telefono == "376400000"
    assert proveedor.estado == Proveedor.INACTIVO


# ---------------------------------------------------------------------------
# Auditoría y permisos
# ---------------------------------------------------------------------------


def test_la_auditoria_guarda_los_valores_anteriores_y_nuevos(client_admin):
    """El CU lo pide explícitamente: con solo el estado final no se puede
    reconstruir qué pasó."""
    proveedor = ProveedorFactory(nombre_contacto="Laura")

    client_admin.post(url(proveedor), datos(proveedor, nombre_contacto="Marcelo"))

    registro = RegistroAuditoria.objects.get(accion=RegistroAuditoria.MODIFICACION_PROVEEDOR)
    assert "Laura" in registro.detalle
    assert "Marcelo" in registro.detalle


def test_guardar_sin_cambios_no_genera_entrada_de_auditoria(client_admin):
    """Un log lleno de entradas vacías esconde las que importan."""
    proveedor = ProveedorFactory()

    client_admin.post(url(proveedor), datos(proveedor))

    assert not RegistroAuditoria.objects.filter(
        accion=RegistroAuditoria.MODIFICACION_PROVEEDOR
    ).exists()


@pytest.mark.parametrize("rol_sin_permiso", ["cliente", "cajero"])
def test_solo_el_administrador_edita_proveedores(client, rol_sin_permiso):
    proveedor = ProveedorFactory(telefono="")
    client.force_login(UsuarioFactory(rol=rol_sin_permiso))

    assert client.get(url(proveedor)).status_code == 403
    assert client.post(url(proveedor), datos(proveedor, telefono="376400000")).status_code == 403
    proveedor.refresh_from_db()
    assert proveedor.telefono == ""
