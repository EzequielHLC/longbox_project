"""Lo que el proveedor le aporta al procesamiento automático de CU-ALT-NOV.

Son tres campos y dos responsabilidades distintas:

- `procesa_novedades` decide **si** sus correos entran al pipeline. Está
  separado del estado a propósito: la relación comercial puede estar viva y el
  procesamiento apagado igual.
- `editorial` y `tipo_por_defecto` son la **cabecera de sus borradores**. Los
  correos de novedades no traen esos dos datos —quien los manda los da por
  obvios— y los dos son campos bloqueantes en la revisión de CU-ALT-REV, así que sin
  esto todos los borradores nacerían trabados.
"""

import pytest
from django.urls import reverse

from apps.catalog.tests.factories import EditorialFactory, TipoFactory
from apps.core.models import RegistroAuditoria
from apps.suppliers.models import Proveedor
from apps.suppliers.tests.factories import ProveedorFactory

pytestmark = pytest.mark.django_db

URL_LISTA = reverse("suppliers:proveedor_lista")
URL_ALTA = reverse("suppliers:proveedor_alta")


def url_ficha(proveedor):
    return reverse("suppliers:proveedor_detalle", args=[proveedor.pk])


def url_edicion(proveedor):
    return reverse("suppliers:proveedor_edicion", args=[proveedor.pk])


# ---------------------------------------------------------------------------
# El interruptor del pipeline
# ---------------------------------------------------------------------------


def test_un_proveedor_con_las_novedades_apagadas_no_es_remitente_valido():
    """El caso que justifica que el campo exista: le seguís comprando, pero sus
    correos no alimentan el pipeline."""
    ProveedorFactory(correo_comercial="novedades@ivrea.test", procesa_novedades=False)

    assert Proveedor.objects.remitente_valido("novedades@ivrea.test") is None


def test_apagarlo_no_lo_da_de_baja():
    """Son dos cosas distintas: el proveedor sigue activo para todo lo demás
    —pedidos de restock, contacto, historial—, solo que su casilla no se lee."""
    proveedor = ProveedorFactory(procesa_novedades=False)

    assert proveedor.esta_activo is True
    assert proveedor.es_remitente_valido is False


def test_con_novedades_habilitadas_pide_las_dos_condiciones():
    habilitado = ProveedorFactory()
    ProveedorFactory(procesa_novedades=False)
    ProveedorFactory(estado=Proveedor.INACTIVO)

    assert list(Proveedor.objects.con_novedades_habilitadas()) == [habilitado]


def test_el_alta_lo_deja_habilitado_por_defecto(client_admin):
    """Postcondición de CU-PRV-ALT: el correo queda habilitado como remitente válido.
    Nadie tiene que acordarse de prenderlo."""
    respuesta = client_admin.get(URL_ALTA)

    assert respuesta.context["form"].fields["procesa_novedades"].initial is True


def test_se_puede_dar_de_alta_con_el_procesamiento_apagado(client_admin):
    """Sirve para registrar al proveedor primero y probar el parseo después."""
    client_admin.post(
        URL_ALTA,
        {
            "razon_social": "Editorial Ivrea",
            "correo_comercial": "novedades@ivrea.test",
            "editorial": "",
            "tipo_por_defecto": "",
            "nombre_contacto": "",
            "telefono": "",
            "notas": "",
        },
    )

    proveedor = Proveedor.objects.get()
    assert proveedor.procesa_novedades is False
    assert proveedor.esta_activo is True


# ---------------------------------------------------------------------------
# La cabecera de los borradores
# ---------------------------------------------------------------------------


def test_el_proveedor_declara_la_editorial_bajo_la_que_publica(client_admin):
    editorial = EditorialFactory(nombre="Ivrea")
    tipo = TipoFactory(nombre="Manga")

    client_admin.post(
        URL_ALTA,
        {
            "razon_social": "Editorial Ivrea",
            "correo_comercial": "novedades@ivrea.test",
            "procesa_novedades": "on",
            "editorial": editorial.pk,
            "tipo_por_defecto": tipo.pk,
            "nombre_contacto": "",
            "telefono": "",
            "notas": "",
        },
    )

    proveedor = Proveedor.objects.get()
    assert proveedor.editorial == editorial
    assert proveedor.tipo_por_defecto == tipo
    assert proveedor.trae_varias_editoriales is False


def test_sin_editorial_declarada_el_proveedor_trae_varias():
    """El vacío significa algo: distribuidora o servicio conjunto, y ahí sí la
    editorial se extrae de cada correo. Es el mismo criterio con el que una
    cabecera de lote sin editorial significa "lote mixto"."""
    proveedor = ProveedorFactory()

    assert proveedor.editorial is None
    assert proveedor.trae_varias_editoriales is True


def test_solo_se_ofrecen_editoriales_y_tipos_activos(client_admin):
    """Vincular un proveedor a una editorial dada de baja dejaría sus borradores
    apuntando a algo que ya no aparece en ningún desplegable del alta."""
    activa = EditorialFactory(nombre="Ivrea", activa=True)
    inactiva = EditorialFactory(nombre="Editorial cerrada", activa=False)
    tipo_activo = TipoFactory(nombre="Manga", activo=True)
    tipo_inactivo = TipoFactory(nombre="Rubro viejo", activo=False)

    form = client_admin.get(URL_ALTA).context["form"]

    assert activa in form.fields["editorial"].queryset
    assert inactiva not in form.fields["editorial"].queryset
    assert tipo_activo in form.fields["tipo_por_defecto"].queryset
    assert tipo_inactivo not in form.fields["tipo_por_defecto"].queryset


def test_el_alta_ofrece_crear_la_editorial_sin_salir_de_la_pantalla(client_admin):
    """Vincularlo a una editorial que todavía no existe es el caso normal la
    primera vez. Es el mismo atajo de la carga de lotes, y del otro lado el
    mismo formulario: no hay dos caminos con reglas distintas."""
    contenido = client_admin.get(URL_ALTA).content.decode()

    assert 'data-catalogo-rapido="editorial"' in contenido
    assert reverse("catalog:editorial_rapida") in contenido


# ---------------------------------------------------------------------------
# Auditoría — los tres cambian el pipeline sin que se vea en el catálogo
# ---------------------------------------------------------------------------


def test_apagar_el_procesamiento_queda_auditado(client_admin):
    """Sin esto, "por qué de Ivrea no llega nada desde marzo" sería una pregunta
    sin respuesta: el pipeline deja de generar borradores en silencio."""
    proveedor = ProveedorFactory(razon_social="Editorial Ivrea")

    client_admin.post(
        url_edicion(proveedor),
        {
            "razon_social": proveedor.razon_social,
            "correo_comercial": proveedor.correo_comercial,
            "editorial": "",
            "tipo_por_defecto": "",
            "nombre_contacto": "",
            "telefono": "",
            "notas": "",
        },
    )

    proveedor.refresh_from_db()
    assert proveedor.procesa_novedades is False
    registro = RegistroAuditoria.objects.get(accion=RegistroAuditoria.MODIFICACION_PROVEEDOR)
    assert "procesamiento de novedades" in registro.detalle
    assert "'sí' → 'no'" in registro.detalle


def test_cambiar_la_editorial_queda_auditado_con_los_dos_valores(client_admin):
    """Cambia bajo qué sello nacen todos los borradores siguientes."""
    proveedor = ProveedorFactory()
    editorial = EditorialFactory(nombre="Ivrea")

    client_admin.post(
        url_edicion(proveedor),
        {
            "razon_social": proveedor.razon_social,
            "correo_comercial": proveedor.correo_comercial,
            "procesa_novedades": "on",
            "editorial": editorial.pk,
            "tipo_por_defecto": "",
            "nombre_contacto": "",
            "telefono": "",
            "notas": "",
        },
    )

    registro = RegistroAuditoria.objects.get(accion=RegistroAuditoria.MODIFICACION_PROVEEDOR)
    assert "editorial: 'varias' → 'Ivrea'" in registro.detalle


# ---------------------------------------------------------------------------
# Las pantallas
# ---------------------------------------------------------------------------


def test_la_ficha_distingue_los_dos_motivos_por_los_que_no_se_procesa(client_admin):
    """ "Activo" ya no alcanza para responder por qué de un proveedor no llega
    nada, y los dos motivos se arreglan en lugares distintos."""
    apagado = ProveedorFactory(procesa_novedades=False)
    de_baja = ProveedorFactory(estado=Proveedor.INACTIVO)

    contenido_apagado = client_admin.get(url_ficha(apagado)).content.decode()
    contenido_de_baja = client_admin.get(url_ficha(de_baja)).content.decode()

    assert "el procesamiento automático está apagado" in contenido_apagado
    assert "el proveedor está dado de baja" in contenido_de_baja


def test_la_ficha_muestra_la_cabecera_de_sus_borradores(client_admin):
    proveedor = ProveedorFactory(
        editorial=EditorialFactory(nombre="Ivrea"),
        tipo_por_defecto=TipoFactory(nombre="Manga"),
    )

    contenido = client_admin.get(url_ficha(proveedor)).content.decode()

    assert "Cabecera de sus borradores" in contenido
    assert "Ivrea" in contenido
    assert "Manga" in contenido


def test_la_ficha_de_una_distribuidora_lo_dice(client_admin):
    proveedor = ProveedorFactory(razon_social="Distribuidora del Litoral")

    contenido = client_admin.get(url_ficha(proveedor)).content.decode()

    assert "Varias — se extrae de cada correo" in contenido


def test_el_listado_marca_solo_al_activo_con_las_novedades_apagadas(client_admin):
    """Es el único caso invisible: que un proveedor de baja no alimente el
    pipeline ya lo dice su estado, y que uno normal sí lo haga es lo esperable."""
    ProveedorFactory(razon_social="Apagada", procesa_novedades=False)

    contenido = client_admin.get(URL_LISTA).content.decode()

    assert contenido.count("Novedades apagadas") == 1


def test_un_proveedor_normal_no_lleva_ninguna_marca(client_admin):
    ProveedorFactory(razon_social="Normal")
    ProveedorFactory(razon_social="De baja", estado=Proveedor.INACTIVO)

    contenido = client_admin.get(URL_LISTA).content.decode()

    assert "Novedades apagadas" not in contenido


def test_el_tablero_cuenta_aparte_los_que_alimentan_el_pipeline(client_admin):
    """La diferencia entre "activos" y "alimentan" es justo el grupo que de otro
    modo quedaría invisible."""
    ProveedorFactory()
    ProveedorFactory()
    ProveedorFactory(procesa_novedades=False)
    ProveedorFactory(estado=Proveedor.INACTIVO)

    resumen = client_admin.get(URL_LISTA).context["resumen"]

    assert resumen["total"] == 4
    assert resumen["activos"] == 3
    assert resumen["alimentan"] == 2
    assert resumen["inactivos"] == 1
