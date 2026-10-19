"""La parte de `CO-039`, `CO-041`, `CO-043` y `CO-045` sobre el catálogo público.

Quedaban parciales (B-02-004) porque el catálogo público no existía. Ahora sí
(`CU-TDA-CAT`): se verifica que los filtros dejan de ofrecer, y vuelven a
ofrecer, lo que el Administrador da de baja o reactiva (plan 00, A6).
"""

import pytest
from django.test import Client
from django.urls import reverse

from apps.catalog.models import Etiqueta
from apps.catalog.tests.factories import GrupoEtiquetaFactory, ProductoFactory

pytestmark = pytest.mark.django_db

URL_CATALOGO = reverse("core:tienda_catalogo")


def _ofrecidas():
    return list(Client().get(URL_CATALOGO).context["etiquetas"])


def _con_producto(nombre, grupo, **extra):
    etiqueta = Etiqueta.objects.create(nombre=nombre, grupo=grupo, **extra)
    ProductoFactory().etiquetas.add(etiqueta)
    return etiqueta


def test_CO041_el_grupo_dado_de_baja_y_sus_etiquetas_dejan_de_ofrecerse_en_la_tienda(
    client_admin,
):
    grupo = GrupoEtiquetaFactory(nombre="Demografía")
    etiqueta = _con_producto("Seinen", grupo)
    assert etiqueta in _ofrecidas()

    client_admin.post(reverse("catalog:grupo_etiqueta_baja", args=[grupo.pk]))

    assert etiqueta not in _ofrecidas()


def test_CO039_el_grupo_reactivado_vuelve_a_ofrecer_las_etiquetas_activas(client_admin):
    grupo = GrupoEtiquetaFactory(nombre="Apagado", activo=False)
    viva = _con_producto("Viva", grupo)
    dormida = _con_producto("Dormida", grupo, activa=False)
    assert viva not in _ofrecidas()

    client_admin.post(
        reverse("catalog:grupo_etiqueta_editar", args=[grupo.pk]),
        {"nombre": "Apagado", "reactivar": "on"},
    )

    ofrecidas = _ofrecidas()
    assert viva in ofrecidas
    assert dormida not in ofrecidas  # conserva su propio estado


def test_CO045_la_etiqueta_dada_de_baja_deja_de_ofrecerse_en_la_tienda(client_admin):
    etiqueta = _con_producto("Retirada", GrupoEtiquetaFactory(nombre="Con uso"))
    assert etiqueta in _ofrecidas()

    client_admin.post(reverse("catalog:etiqueta_baja", args=[etiqueta.pk]))

    assert etiqueta not in _ofrecidas()


def test_CO043_la_etiqueta_reactivada_vuelve_a_ofrecerse_en_la_tienda(client_admin):
    grupo = GrupoEtiquetaFactory(nombre="Vivo")
    etiqueta = _con_producto("Dormida", grupo, activa=False)
    assert etiqueta not in _ofrecidas()

    client_admin.post(
        reverse("catalog:etiqueta_editar", args=[etiqueta.pk]),
        {"nombre": "Dormida", "grupo": grupo.pk, "reactivar": "on"},
    )

    assert etiqueta in _ofrecidas()
