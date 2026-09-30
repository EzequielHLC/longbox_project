"""Pruebas de contrato del módulo 04 · Proveedores (cola de correos y abandono).

Se escriben desde el contrato, según `docs/pruebas/ESPECIFICACION.md` apartado 3:
se monta lo que piden las precondiciones, se captura el valor anterior de lo
que cambia, se ejerce la operación **por su dirección real** una vez y se
afirma cada postcondición por separado.

Cubre `CO-017`, `CO-018`, `CO-019`, `CO-157` y `CO-158` (CU-PRV-COL, y la parte
de CU-ALT-NOV que comparten), y `CO-156 cancelarOperacion` en CU-PRV-BAJ y
CU-PRV-REA. El modelo de lenguaje nunca se llama: se parchea la puerta HTTP.
"""

import json
from unittest.mock import patch

import pytest
from django.urls import reverse

from apps.catalog.models import BorradorProducto
from apps.core import integraciones
from apps.core.models import ConfiguracionSistema, RegistroAuditoria
from apps.suppliers import extraccion, services
from apps.suppliers.models import CorreoProveedor, Proveedor
from apps.suppliers.tests import correos_de_ejemplo as ejemplo
from apps.suppliers.tests.factories import ProveedorFactory

pytestmark = pytest.mark.django_db

BERSERK = "9789878271583"
BLUE_PERIOD = "9789878274652"


def producto(**cambios):
    base = {
        "isbn": BERSERK,
        "titulo": "Berserk Deluxe",
        "volumen": "5",
        "formato": "Tapa dura",
        "precio": "24900",
        "fecha": "",
        "imagen": "tapa001@ivrea.test",
        "confianza": {
            campo: "alta" for campo in ("isbn", "titulo", "volumen", "formato", "precio", "fecha")
        },
    }
    base.update(cambios)
    return base


def respuesta(productos=None, intencion=extraccion.NOVEDADES):
    contenido = {"intencion": intencion, "periodo": "", "productos": productos or []}
    return integraciones.Respuesta(
        datos={"choices": [{"message": {"content": json.dumps(contenido)}}]}
    )


def contestando(valor):
    return patch("apps.core.integraciones.pedir", return_value=valor)


SIN_SERVICIO = integraciones.Respuesta(motivo=integraciones.SIN_CONEXION)


@pytest.fixture
def proveedor(db):
    from apps.catalog.tests.factories import EditorialFactory, TipoFactory

    return ProveedorFactory(
        correo_comercial="novedades@ivrea.test",
        editorial=EditorialFactory(nombre="Ivrea"),
        tipo_por_defecto=TipoFactory(nombre="Manga", usa_formato=True),
    )


@pytest.fixture
def correo(db, proveedor):
    """Un correo real, archivado y Pendiente de aprobación (precondición de CO-017)."""
    correo = services.ingerir(ejemplo.correo_de_novedades()).correo
    assert correo.estado == CorreoProveedor.PENDIENTE
    return correo


def url_aprobar(correo):
    return reverse("suppliers:correo_aprobar", args=[correo.pk])


def url_reprocesar(correo):
    return reverse("suppliers:correo_reprocesar", args=[correo.pk])


def url_ficha(correo):
    return reverse("suppliers:correo_detalle", args=[correo.pk])


def _foto(correo):
    correo.refresh_from_db()
    return (correo.estado, correo.motivo, correo.resuelto_por_id, correo.resuelto_en)


# ---------------------------------------------------------------------------
# CO-017 · aprobarCorreoParaProcesamiento
# ---------------------------------------------------------------------------


def test_CO017_aprobar_pasa_el_correo_de_pendiente_a_procesado(client_admin, correo, administrador):
    assert correo.estado == CorreoProveedor.PENDIENTE
    assert correo.resuelto_en is None
    assert correo.extraccion == {}

    with contestando(respuesta([producto()])):
        client_admin.post(url_aprobar(correo))

    correo.refresh_from_db()
    # (c) estado: Pendiente → En proceso → Procesado.
    assert correo.estado == CorreoProveedor.PROCESADO
    # (c) extracción y versión del prompt pasaron de nulos a sus valores.
    assert correo.productos_extraidos[0]["titulo"] == "Berserk Deluxe"
    assert correo.version_prompt == extraccion.VERSION_PROMPT
    # (c) resuelto el quedó con el instante; (b) c → Usuario (resuelto por).
    assert correo.resuelto_en is not None
    assert correo.resuelto_por == administrador
    # El original sigue archivado.
    assert correo.archivo


def test_CO017_crea_un_borrador_por_producto_con_sus_asociaciones(client_admin, correo, proveedor):
    stock = ConfiguracionSistema.obtener().stock_inicial_por_defecto
    assert not BorradorProducto.objects.exists()

    with contestando(respuesta([producto()])):
        client_admin.post(url_aprobar(correo))

    # (a) Se creó b : BorradorProducto, y (a) sus ConfianzaCampo.
    borrador = BorradorProducto.objects.get()
    assert borrador.confianzas.exists()
    # (b) b → CorreoProveedor, b → Editorial (heredada).
    assert borrador.correo == correo
    assert borrador.editorial == proveedor.editorial
    # (c) estado, stock inicial y confianza sin revisar.
    assert borrador.estado == BorradorProducto.PENDIENTE
    assert borrador.stock_inicial == stock
    assert not borrador.confianzas.filter(revisado=True).exists()


def test_CO017_la_operacion_queda_auditada(client_admin, correo, administrador):
    antes = RegistroAuditoria.objects.filter(accion=RegistroAuditoria.BORRADORES_GENERADOS).count()

    with contestando(respuesta([producto()])):
        client_admin.post(url_aprobar(correo))

    registros = RegistroAuditoria.objects.filter(accion=RegistroAuditoria.BORRADORES_GENERADOS)
    assert registros.count() == antes + 1
    assert registros.latest("ocurrido_en").actor_email == administrador.email


def test_CO017_el_resumen_informa_generados_omitidos_y_reparos(client_admin, correo):
    with contestando(respuesta([producto()])):
        respuesta_http = client_admin.post(url_aprobar(correo), follow=True)

    texto = respuesta_http.content.decode()
    assert "1 borrador(es) generado(s)" in texto
    assert "omitido(s) por existir ya en el catálogo" in texto
    assert "con reparos" in texto


def test_CO017_E1_un_correo_ya_tomado_por_otro_no_se_vuelve_a_procesar(client_admin, correo):
    """Otro Administrador lo aprobó mientras éste lo tenía abierto."""
    CorreoProveedor.objects.filter(pk=correo.pk).update(estado=CorreoProveedor.EN_PROCESO)
    antes = _foto(correo)

    with contestando(respuesta([producto()])) as pedir:
        respuesta_http = client_admin.post(url_aprobar(correo), follow=True)

    assert not pedir.called, "Un correo tomado por otro no llega al modelo."
    assert _foto(correo) == antes
    assert not BorradorProducto.objects.exists()
    assert "Estado actual: En proceso" in respuesta_http.content.decode()


def test_CO017_E1_la_segunda_aprobacion_encuentra_el_correo_tomado(correo, administrador):
    """La transición es condicionada: sólo la primera aprobación pasa."""
    with contestando(respuesta([producto()])):
        services.aprobar_correo(correo.pk, actor=administrador)
        with pytest.raises(services.CorreoYaResuelto):
            services.aprobar_correo(correo.pk, actor=administrador)

    assert BorradorProducto.objects.count() == 1


def test_CO017_E4_si_el_servicio_no_responde_el_correo_falla_y_queda_en_la_cola(
    client_admin, correo
):
    with contestando(SIN_SERVICIO):
        client_admin.post(url_aprobar(correo))

    correo.refresh_from_db()
    assert correo.estado == CorreoProveedor.FALLIDO
    assert correo.estado != CorreoProveedor.DESCARTADO
    assert not BorradorProducto.objects.exists()
    # La decisión del Administrador queda registrada igual (CU-PRV-COL).
    assert RegistroAuditoria.objects.filter(
        accion=RegistroAuditoria.BORRADORES_GENERADOS, objetivo_pk=correo.pk
    ).exists()


def test_CO017_E4_si_no_identifica_ningun_producto_el_correo_falla(client_admin, correo):
    with contestando(respuesta([], intencion=extraccion.OTRO)):
        client_admin.post(url_aprobar(correo))

    correo.refresh_from_db()
    assert correo.estado == CorreoProveedor.FALLIDO
    assert not BorradorProducto.objects.exists()


def test_CO017_por_la_direccion_real_con_rol_cajero_no_procesa(client, cajero, correo):
    client.force_login(cajero)
    antes = _foto(correo)

    with contestando(respuesta([producto()])) as pedir:
        respuesta_http = client.post(url_aprobar(correo))

    assert respuesta_http.status_code == 403
    assert not pedir.called
    assert _foto(correo) == antes


def test_CO017_no_acepta_get(client_admin, correo):
    """Una operación con efecto no se dispara con un enlace."""
    assert client_admin.get(url_aprobar(correo)).status_code == 405


# ---------------------------------------------------------------------------
# CO-018 · descartarCorreo
# ---------------------------------------------------------------------------


def test_CO018_descartar_registra_estado_motivo_y_responsable(client_admin, correo, administrador):
    assert correo.motivo == ""
    assert correo.resuelto_por is None

    client_admin.post(url_ficha(correo), {"motivo": "Es una factura, no novedades."})

    correo.refresh_from_db()
    assert correo.estado == CorreoProveedor.DESCARTADO
    assert correo.motivo == "Es una factura, no novedades."
    assert correo.resuelto_en is not None
    assert correo.resuelto_por == administrador
    assert RegistroAuditoria.objects.filter(
        accion=RegistroAuditoria.CORREO_DESCARTADO, objetivo_pk=correo.pk
    ).exists()


def test_CO018_E3_sin_motivo_no_se_descarta(client_admin, correo):
    antes = _foto(correo)

    client_admin.post(url_ficha(correo), {"motivo": "   "})

    assert _foto(correo) == antes
    assert not RegistroAuditoria.objects.filter(accion=RegistroAuditoria.CORREO_DESCARTADO).exists()


# ---------------------------------------------------------------------------
# CO-019 · reprocesarCorreo
# ---------------------------------------------------------------------------


@pytest.fixture
def correo_procesado_con_decisiones(correo, administrador):
    """Un correo Procesado con tres borradores: uno confirmado, uno rechazado y
    uno todavía abierto."""
    tres = [
        producto(),
        producto(isbn=BLUE_PERIOD, titulo="Blue Period", volumen="3"),
        producto(isbn="", titulo="Vagabond", volumen="1"),
    ]
    with contestando(respuesta(tres)):
        services.aprobar_correo(correo.pk, actor=administrador)
    confirmado, rechazado, abierto = BorradorProducto.objects.order_by("pk")
    BorradorProducto.objects.filter(pk=confirmado.pk).update(estado=BorradorProducto.CONFIRMADO)
    BorradorProducto.objects.filter(pk=rechazado.pk).update(estado=BorradorProducto.RECHAZADO)
    correo.refresh_from_db()
    assert correo.estado == CorreoProveedor.PROCESADO
    return correo, confirmado.pk, rechazado.pk, abierto.pk


def test_CO019_reemplaza_solo_los_borradores_abiertos(
    client_admin, correo_procesado_con_decisiones
):
    correo, confirmado, rechazado, abierto = correo_procesado_con_decisiones
    resueltos_antes = {
        b.pk: (b.estado, b.titulo, b.precio)
        for b in BorradorProducto.objects.filter(pk__in=[confirmado, rechazado])
    }

    with contestando(respuesta([producto(isbn="", titulo="Vagabond", volumen="2")])):
        client_admin.post(url_reprocesar(correo))

    # Se eliminó el abierto y (a) se creó el nuevo.
    assert not BorradorProducto.objects.filter(pk=abierto).exists()
    nuevo = BorradorProducto.objects.exclude(pk__in=[confirmado, rechazado]).get()
    assert nuevo.titulo == "Vagabond"
    assert nuevo.correo == correo
    # Postcondición negativa: los confirmados y rechazados no fueron modificados.
    resueltos_despues = {
        b.pk: (b.estado, b.titulo, b.precio)
        for b in BorradorProducto.objects.filter(pk__in=[confirmado, rechazado])
    }
    assert resueltos_despues == resueltos_antes
    # (c) estado y versión del prompt.
    correo.refresh_from_db()
    assert correo.estado == CorreoProveedor.PROCESADO
    assert correo.version_prompt == extraccion.VERSION_PROMPT


def test_CO019_queda_auditado(client_admin, correo_procesado_con_decisiones):
    correo, *_ = correo_procesado_con_decisiones
    antes = RegistroAuditoria.objects.filter(accion=RegistroAuditoria.BORRADORES_GENERADOS).count()

    with contestando(respuesta([producto(isbn="", titulo="Vagabond", volumen="2")])):
        client_admin.post(url_reprocesar(correo))

    assert (
        RegistroAuditoria.objects.filter(accion=RegistroAuditoria.BORRADORES_GENERADOS).count()
        == antes + 1
    )


def test_CO019_si_la_extraccion_falla_los_abiertos_se_conservan(
    client_admin, correo_procesado_con_decisiones
):
    """Las excepciones de CO-017 aplican: un corte del servicio no borra trabajo."""
    correo, _, _, abierto = correo_procesado_con_decisiones

    with contestando(SIN_SERVICIO):
        client_admin.post(url_reprocesar(correo))

    assert BorradorProducto.objects.filter(pk=abierto).exists()
    correo.refresh_from_db()
    assert correo.estado == CorreoProveedor.FALLIDO


def test_CO019_un_correo_pendiente_no_se_reprocesa(client_admin, correo):
    """Precondición: el correo está Procesado o Falló el procesamiento."""
    antes = _foto(correo)

    with contestando(respuesta([producto()])) as pedir:
        client_admin.post(url_reprocesar(correo))

    assert not pedir.called
    assert _foto(correo) == antes


def test_CO019_la_ficha_ofrece_reprocesar_solo_si_corresponde(
    client_admin, correo_procesado_con_decisiones
):
    correo, *_ = correo_procesado_con_decisiones
    assert url_reprocesar(correo) in client_admin.get(url_ficha(correo)).content.decode()


# ---------------------------------------------------------------------------
# CO-157 · consultarColaDeCorreos · CO-158 · abrirFichaDeCorreo
# ---------------------------------------------------------------------------


def test_CO157_consultar_la_cola_no_modifica_nada(client_admin, correo):
    antes = _foto(correo)
    registros = RegistroAuditoria.objects.count()

    respuesta_http = client_admin.get(reverse("suppliers:correo_lista"))

    assert respuesta_http.status_code == 200
    assert correo.asunto in respuesta_http.content.decode()
    assert _foto(correo) == antes
    assert RegistroAuditoria.objects.count() == registros


def test_CO157_por_la_direccion_real_con_rol_cajero_se_deniega(client, cajero):
    client.force_login(cajero)
    assert client.get(reverse("suppliers:correo_lista")).status_code == 403


def test_CO158_abrir_la_ficha_muestra_el_contenido_y_no_modifica_nada(client_admin, correo):
    antes = _foto(correo)
    registros = RegistroAuditoria.objects.count()

    respuesta_http = client_admin.get(url_ficha(correo))

    contenido = respuesta_http.content.decode()
    assert "Contenido extraído" in contenido
    assert "Portadas embebidas" in contenido
    assert _foto(correo) == antes
    assert RegistroAuditoria.objects.count() == registros


def test_CO158_la_ficha_de_un_pendiente_ofrece_aprobar_y_descartar(client_admin, correo):
    contenido = client_admin.get(url_ficha(correo)).content.decode()

    assert url_aprobar(correo) in contenido
    assert "Descartar correo" in contenido
    assert url_reprocesar(correo) not in contenido


# ---------------------------------------------------------------------------
# CO-156 · cancelarOperacion  (CU-PRV-REA A1, CU-PRV-BAJ A2)
# ---------------------------------------------------------------------------


def _foto_proveedor(proveedor):
    proveedor.refresh_from_db()
    return (proveedor.estado, proveedor.correo_comercial, proveedor.razon_social)


@pytest.mark.parametrize(
    ("ruta", "estado_inicial"),
    [
        ("suppliers:proveedor_reactivar", Proveedor.INACTIVO),
        ("suppliers:proveedor_baja", Proveedor.ACTIVO),
    ],
)
def test_CO156_abandonar_la_confirmacion_no_cambia_el_proveedor(client_admin, ruta, estado_inicial):
    """Postcondición: «ninguna. El objeto conserva todos sus atributos. No se
    genera entrada de auditoría: una operación que no ocurrió no se audita»."""
    proveedor = ProveedorFactory(estado=estado_inicial)
    antes = _foto_proveedor(proveedor)
    registros = RegistroAuditoria.objects.count()

    # Abrir la confirmación y no confirmar es exactamente abandonar la operación.
    assert client_admin.get(reverse(ruta, args=[proveedor.pk])).status_code == 200

    assert _foto_proveedor(proveedor) == antes
    assert RegistroAuditoria.objects.count() == registros
