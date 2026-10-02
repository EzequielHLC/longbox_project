"""Los catálogos que se identifican por su nombre no distinguen mayúsculas.

Es la regla que evita que en seis meses convivan "Ivrea", "ivrea " e "IVREA"
como tres registros distintos con los productos repartidos entre los tres. Estaba
escrita, pero solo aplicada en tres de los cinco catálogos: `Tipo` y `Formato`
quedaron afuera, y son justamente los dos que **deciden** —el tipo entra en la
clave de unicidad del producto y en la tabla de precios de referencia—, así que
duplicarlos no repite una fila, parte una grilla de precios en dos.

Se prueba en los dos niveles, porque hacen cosas distintas:

- **El formulario** avisa con un mensaje que nombra al registro existente. Es lo
  que ve quien carga.
- **La base** lo impide aunque nadie haya pasado por el formulario. Es lo que
  queda cuando mañana alguien escribe un `create()` en un comando o un import.
"""

import pytest
from django.db import IntegrityError, transaction
from django.urls import reverse

from apps.catalog.forms import EditorialForm, FormatoForm, GrupoEtiquetaForm, TipoForm
from apps.catalog.models import Editorial, Formato, GrupoEtiqueta, Tipo

pytestmark = pytest.mark.django_db


# Cada catálogo con su formulario y los datos mínimos para que valide.
CATALOGOS = [
    (Tipo, TipoForm, {"clase": "editorial"}, "tipo"),
    (Formato, FormatoForm, {}, "formato"),
    (Editorial, EditorialForm, {}, "editorial"),
    (GrupoEtiqueta, GrupoEtiquetaForm, {}, "grupo"),
]

IDS = [c[3] for c in CATALOGOS]


# ---------------------------------------------------------------------------
# El formulario avisa
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(("modelo", "formulario", "extra", "_"), CATALOGOS, ids=IDS)
def test_el_mismo_nombre_en_otra_caja_se_rechaza(modelo, formulario, extra, _):
    modelo.objects.create(nombre="Zeta de prueba", **extra)

    form = formulario(data={"nombre": "ZETA DE PRUEBA", **extra})

    assert not form.is_valid()
    assert "nombre" in form.errors


@pytest.mark.parametrize(("modelo", "formulario", "extra", "_"), CATALOGOS, ids=IDS)
def test_el_aviso_nombra_al_registro_existente(modelo, formulario, extra, _):
    """Sin el nombre tal como está guardado, hay que ir a buscarlo a la lista."""
    modelo.objects.create(nombre="Zeta de prueba", **extra)

    form = formulario(data={"nombre": "zeta de prueba", **extra})
    form.is_valid()

    assert "Zeta de prueba" in str(form.errors["nombre"])


@pytest.mark.parametrize(("modelo", "formulario", "extra", "_"), CATALOGOS, ids=IDS)
def test_los_espacios_de_mas_se_normalizan(modelo, formulario, extra, _):
    form = formulario(data={"nombre": "  Tapa   inventada  ", **extra})

    assert form.is_valid(), form.errors
    assert form.cleaned_data["nombre"] == "Tapa inventada"


@pytest.mark.parametrize(("modelo", "formulario", "extra", "_"), CATALOGOS, ids=IDS)
def test_editarse_a_si_mismo_no_es_un_duplicado(modelo, formulario, extra, _):
    """Guardar un registro sin tocarle el nombre tiene que seguir andando: el
    choque se busca contra los demás, no contra uno mismo."""
    registro = modelo.objects.create(nombre="Zeta de prueba", **extra)

    form = formulario(data={"nombre": "Zeta de prueba", **extra}, instance=registro)

    assert form.is_valid(), form.errors


@pytest.mark.parametrize(("modelo", "formulario", "extra", "_"), CATALOGOS, ids=IDS)
def test_se_le_puede_corregir_la_capitalizacion(modelo, formulario, extra, _):
    """El caso que rompería una comparación ingenua contra sí mismo: cambiar
    "zeta de prueba" por "Zeta de prueba" es la misma fila, no un duplicado."""
    registro = modelo.objects.create(nombre="zeta de prueba", **extra)

    form = formulario(data={"nombre": "Zeta de prueba", **extra}, instance=registro)

    assert form.is_valid(), form.errors


# ---------------------------------------------------------------------------
# La base impide
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(("modelo", "_f", "extra", "_"), CATALOGOS, ids=IDS)
def test_la_restriccion_esta_en_la_base(modelo, _f, extra, _):
    """Sin esto la regla vale solo para quien pase por el formulario, y un
    `create()` en un comando o en un import la esquiva sin avisar."""
    modelo.objects.create(nombre="Zeta de prueba", **extra)

    with pytest.raises(IntegrityError), transaction.atomic():
        modelo.objects.create(nombre="ZETA DE PRUEBA", **extra)


# ---------------------------------------------------------------------------
# Las pantallas de edición, que hasta ahora no tenían ninguna prueba
# ---------------------------------------------------------------------------


PANTALLAS_DE_EDICION = [
    ("catalog:tipo_editar", Tipo, {}),
    ("catalog:formato_editar", Formato, {}),
    ("catalog:editorial_editar", Editorial, {}),
    ("catalog:grupo_etiqueta_editar", GrupoEtiqueta, {}),
]


@pytest.mark.parametrize(("ruta", "modelo", "extra"), PANTALLAS_DE_EDICION)
def test_la_pantalla_de_edicion_abre(client_admin, ruta, modelo, extra):
    registro = modelo.objects.create(nombre="Zeta de prueba", **extra)

    respuesta = client_admin.get(reverse(ruta, args=[registro.pk]))

    assert respuesta.status_code == 200
    assert "Zeta de prueba" in respuesta.content.decode()


@pytest.mark.parametrize(("ruta", "modelo", "extra"), PANTALLAS_DE_EDICION)
def test_la_edicion_rechaza_el_choque_con_otro(client_admin, ruta, modelo, extra):
    modelo.objects.create(nombre="Zeta de prueba", **extra)
    otro = modelo.objects.create(nombre="Omega de prueba", **extra)

    client_admin.post(reverse(ruta, args=[otro.pk]), {"nombre": "ZETA DE PRUEBA", **extra})

    otro.refresh_from_db()
    assert otro.nombre == "Omega de prueba"


@pytest.mark.parametrize(("ruta", "modelo", "extra"), PANTALLAS_DE_EDICION)
def test_solo_el_administrador_edita(client, ruta, modelo, extra):
    registro = modelo.objects.create(nombre="Zeta de prueba", **extra)

    assert client.get(reverse(ruta, args=[registro.pk])).status_code in (302, 403)
