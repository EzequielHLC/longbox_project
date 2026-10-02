"""Pruebas de contrato del módulo 16 · Auditoría (CU-AUD-CON).

Se escriben desde el contrato, según `docs/pruebas/ESPECIFICACION.md` apartado 3.
La consulta no se audita; la exportación sí. El log no admite escritura por
ninguna dirección, tampoco para el Administrador.
"""

import csv
import io
from datetime import timedelta

import pytest
from django.contrib.contenttypes.models import ContentType
from django.urls import reverse
from django.utils import timezone

from apps.accounts.tests.factories import UsuarioFactory
from apps.catalog.models import Editorial
from apps.catalog.tests.factories import EditorialFactory
from apps.core.models import RegistroAuditoria

pytestmark = pytest.mark.django_db

URL = reverse("core:auditoria")
URL_EXPORTAR = reverse("core:auditoria_exportar")


def entrada(**datos):
    datos.setdefault("accion", RegistroAuditoria.INICIO_SESION)
    return RegistroAuditoria.registrar(**datos)


def filas_csv(respuesta):
    texto = b"".join(respuesta.streaming_content).decode("utf-8-sig")
    return list(csv.reader(io.StringIO(texto)))


def test_CO205_consultar_log_de_a_50_de_la_mas_reciente_a_la_mas_antigua(client_admin):
    for numero in range(55):
        entrada(actor_email=f"persona{numero}@longbox.test")
    registros = RegistroAuditoria.objects.count()

    primera = client_admin.get(URL)
    segunda = client_admin.get(URL, {"page": 2})

    pagina = list(primera.context["entradas"])
    assert len(pagina) == 50
    assert pagina == sorted(pagina, key=lambda e: (e.ocurrido_en, e.pk), reverse=True)
    assert len(segunda.context["entradas"]) == registros - 50
    # La consulta no se audita.
    assert RegistroAuditoria.objects.count() == registros


def test_CO205_filtra_por_actor_accion_entidad_rol_y_fechas(client_admin, cajero):
    editorial = EditorialFactory(nombre="Ivrea")
    buscada = entrada(accion=RegistroAuditoria.ALTA_CATALOGO, actor=cajero, objetivo=editorial)
    entrada(accion=RegistroAuditoria.ALTA_CATALOGO, actor_email="otra@longbox.test")
    entrada(accion=RegistroAuditoria.CIERRE_SESION, actor=cajero)
    tipo = ContentType.objects.get_for_model(Editorial)
    hoy = timezone.localdate()

    respuesta = client_admin.get(
        URL,
        {
            "actor": cajero.email[:6],
            "rol": "cajero",
            "accion": RegistroAuditoria.ALTA_CATALOGO,
            "entidad": tipo.pk,
            "desde": hoy.isoformat(),
            "hasta": hoy.isoformat(),
        },
    )

    assert list(respuesta.context["entradas"]) == [buscada]


def test_CO205_un_rango_de_fechas_sin_entradas_lo_dice(client_admin):
    entrada()
    pasado = (timezone.localdate() - timedelta(days=400)).isoformat()

    respuesta = client_admin.get(URL, {"hasta": pasado})

    assert "Ninguna entrada coincide con los filtros" in respuesta.content.decode()


def test_CO206_el_detalle_presenta_la_entrada_completa(client_admin, administrador):
    editorial = EditorialFactory(nombre="Ivrea")
    registro = entrada(
        accion=RegistroAuditoria.MODIFICACION_CATALOGO,
        actor=administrador,
        objetivo=editorial,
        ip="10.0.0.1",
        detalle="Editorial «Ivrea»: nombre: «Ivra» → «Ivrea»",
    )

    contenido = client_admin.get(reverse("core:auditoria_detalle", args=[registro.pk])).content
    contenido = contenido.decode()

    for esperado in (
        administrador.email,
        "Modificación de catálogo",
        "Editorial",
        str(editorial.pk),
        "10.0.0.1",
        "«Ivra» → «Ivrea»",
    ):
        assert esperado in contenido, esperado


def test_CO129_exportar_trae_todo_el_filtro_y_no_solo_la_pagina(client_admin, administrador):
    for numero in range(60):
        entrada(accion=RegistroAuditoria.ALTA_CATALOGO, actor_email=f"p{numero}@longbox.test")
    entrada(accion=RegistroAuditoria.CIERRE_SESION, actor_email="fuera@longbox.test")

    respuesta = client_admin.get(URL_EXPORTAR, {"accion": RegistroAuditoria.ALTA_CATALOGO})

    filas = filas_csv(respuesta)
    assert respuesta["Content-Type"].startswith("text/csv")
    assert filas[0][0] == "Momento"
    assert len(filas) - 1 == 60
    assert all(fila[2] == "Alta de catálogo" for fila in filas[1:])
    registro = RegistroAuditoria.objects.get(accion=RegistroAuditoria.EXPORTACION_AUDITORIA)
    assert registro.actor == administrador
    assert "60 entradas" in registro.detalle
    assert "acción Alta de catálogo" in registro.detalle


def test_CO129_las_celdas_no_se_interpretan_como_formulas(client_admin):
    entrada(actor_email="=HYPERLINK(1)@x.test", detalle="+cmd|' /C calc'!A0")

    filas = filas_csv(client_admin.get(URL_EXPORTAR))

    fila = next(f for f in filas[1:] if "HYPERLINK" in f[1])
    assert fila[1].startswith("'=")
    assert fila[7].startswith("'+")


@pytest.mark.parametrize("metodo", ["post", "put", "patch", "delete"])
def test_el_log_no_admite_escritura_ni_para_el_administrador(client_admin, metodo):
    registro = entrada(detalle="original")
    for url in (URL, reverse("core:auditoria_detalle", args=[registro.pk])):
        respuesta = getattr(client_admin, metodo)(url)
        assert respuesta.status_code == 403
    registro.refresh_from_db()
    assert registro.detalle == "original"


@pytest.mark.parametrize("rol", ["cajero", "cliente"])
def test_el_rol_equivocado_no_consulta_ni_exporta(client, rol):
    client.force_login(UsuarioFactory(rol=rol))
    registro = entrada()

    for url in (URL, URL_EXPORTAR, reverse("core:auditoria_detalle", args=[registro.pk])):
        assert client.get(url).status_code == 403
    assert not RegistroAuditoria.objects.filter(
        accion=RegistroAuditoria.EXPORTACION_AUDITORIA
    ).exists()


def test_sin_sesion_va_al_login(client):
    respuesta = client.get(URL)

    assert respuesta.status_code == 302
    assert reverse("accounts:login") in respuesta["Location"]
