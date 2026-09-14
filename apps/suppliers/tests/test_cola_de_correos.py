"""La cola de aprobación: ingesta, pantallas y descarte.

Es la pieza que **no está en la fuente**. CU-ALT-NOV describe un ciclo que parsea
todo lo que encuentre de un remitente registrado; acá el correo llega, se
archiva y espera una decisión. Ver la corrección 11 de
`docs/correcciones-fuente.md`.
"""

import pytest
from django.urls import reverse

from apps.accounts.tests.factories import UsuarioFactory
from apps.catalog.tests.factories import EditorialFactory
from apps.core.models import RegistroAuditoria
from apps.suppliers import correos, services
from apps.suppliers.models import CorreoProveedor, Proveedor
from apps.suppliers.tests import correos_de_ejemplo as ejemplo
from apps.suppliers.tests.factories import ProveedorFactory

pytestmark = pytest.mark.django_db

URL_COLA = reverse("suppliers:correo_lista")

REMITENTE = "novedades@ivrea.test"


def url_ficha(correo):
    return reverse("suppliers:correo_detalle", args=[correo.pk])


@pytest.fixture
def ivrea():
    """El proveedor que manda los correos de ejemplo, habilitado."""
    return ProveedorFactory(
        razon_social="Editorial Ivrea",
        correo_comercial=REMITENTE,
        editorial=EditorialFactory(nombre="Ivrea"),
    )


# ---------------------------------------------------------------------------
# Ingesta
# ---------------------------------------------------------------------------


def test_un_correo_de_un_proveedor_habilitado_entra_a_la_cola(ivrea):
    resultado = services.ingerir(ejemplo.correo_de_novedades())

    assert resultado.ingresado
    correo = resultado.correo
    assert correo.proveedor == ivrea
    assert correo.estado == CorreoProveedor.PENDIENTE
    assert correo.asunto == "Novedades marzo 2026"


def test_el_correo_queda_archivado_entero(ivrea):
    """CU-ALT-NOV pide archivar el original como respaldo. Además es lo que permite
    volver a extraer el contenido si la extracción mejora, sin depender de que
    el correo siga en la casilla."""
    correo = services.ingerir(ejemplo.correo_de_novedades()).correo

    assert correo.archivo.name.endswith(".eml")
    # El HTML viaja codificado dentro del `.eml`, así que lo que se verifica no
    # es el texto crudo sino que el archivo alcance para reconstruir todo: es
    # justamente para eso que se archiva.
    releido = correos.leer(correo.archivo.read())
    assert releido.contenido == correo.contenido
    assert len(releido.imagenes) == correo.cantidad_imagenes


def test_se_guarda_el_contenido_extraido_y_el_resumen_de_las_portadas(ivrea):
    """El contenido se guarda y no se recalcula al leer: es exactamente lo que
    se le va a mandar al modelo, y tenerlo escrito hace que el paso siguiente
    sea reproducible."""
    correo = services.ingerir(ejemplo.correo_de_novedades()).correo

    assert "| 9789878271583 |" in correo.contenido
    assert correo.cantidad_imagenes == 4
    assert correo.imagenes[0]["tipo"] == "image/webp"


def test_un_remitente_no_registrado_no_genera_nada():
    """E1 de CU-ALT-NOV: se loguea y el ciclo sigue con el mensaje siguiente. No
    levanta: un correo raro no puede tumbar la lectura de la casilla entera."""
    resultado = services.ingerir(ejemplo.correo_de_novedades(remitente="spam@cualquiera.test"))

    assert resultado.correo is None
    assert resultado.motivo == services.MotivoDeDescarte.REMITENTE_DESCONOCIDO
    assert not CorreoProveedor.objects.exists()


def test_un_proveedor_dado_de_baja_no_alimenta_la_cola():
    ProveedorFactory(correo_comercial=REMITENTE, estado=Proveedor.INACTIVO)

    resultado = services.ingerir(ejemplo.correo_de_novedades())

    assert resultado.motivo == services.MotivoDeDescarte.REMITENTE_DESCONOCIDO


def test_un_proveedor_con_el_procesamiento_apagado_tampoco():
    """Es el efecto práctico del interruptor de A6: le seguís comprando, pero su
    casilla no entra al pipeline."""
    ProveedorFactory(correo_comercial=REMITENTE, procesa_novedades=False)

    resultado = services.ingerir(ejemplo.correo_de_novedades())

    assert resultado.motivo == services.MotivoDeDescarte.REMITENTE_DESCONOCIDO
    assert not CorreoProveedor.objects.exists()


def test_el_mismo_correo_dos_veces_no_se_duplica(ivrea):
    """Un ciclo que se ejecuta dos veces —porque se reintentó, o porque el
    mensaje quedó sin marcar en la casilla— no puede encolar dos filas."""
    primero = services.ingerir(ejemplo.correo_de_novedades())
    segundo = services.ingerir(ejemplo.correo_de_novedades())

    assert segundo.motivo == services.MotivoDeDescarte.REPETIDO
    assert segundo.correo == primero.correo
    assert CorreoProveedor.objects.count() == 1


def test_reingerir_no_pisa_un_correo_ya_resuelto(ivrea, administrador):
    """Si lo pisara, un correo ya descartado volvería a la cola en cada pasada."""
    correo = services.ingerir(ejemplo.correo_de_novedades()).correo
    services.descartar(correo, administrador, "es una factura")

    services.ingerir(ejemplo.correo_de_novedades())

    correo.refresh_from_db()
    assert correo.estado == CorreoProveedor.DESCARTADO


def test_un_correo_sin_identificador_no_entra(ivrea):
    """Sin `Message-ID` no hay clave de idempotencia, y cada pasada lo volvería
    a encolar. Se descarta en vez de inventarle uno: un identificador fabricado
    daría distinto en cada lectura y el efecto sería el mismo duplicado."""
    resultado = services.ingerir(ejemplo.correo_de_novedades(message_id=None))

    assert resultado.motivo == services.MotivoDeDescarte.SIN_IDENTIFICADOR
    assert not CorreoProveedor.objects.exists()


def test_un_aviso_de_demora_entra_igual_a_la_cola(ivrea):
    """No se procesa distinto todavía, pero entra: es la razón de ser de la cola
    de aprobación —por la casilla del proveedor no llegan solo novedades—."""
    resultado = services.ingerir(ejemplo.correo_de_demora())

    assert resultado.ingresado
    assert "se reprograma para mayo" in resultado.correo.contenido


# ---------------------------------------------------------------------------
# Las pantallas
# ---------------------------------------------------------------------------


def test_la_cola_lista_los_correos(client_admin, ivrea):
    services.ingerir(ejemplo.correo_de_novedades())

    contenido = client_admin.get(URL_COLA).content.decode()

    assert "Novedades marzo 2026" in contenido
    assert "Editorial Ivrea" in contenido


def test_la_cola_cuenta_los_pendientes(client_admin, ivrea):
    services.ingerir(ejemplo.correo_de_novedades())
    services.ingerir(ejemplo.correo_de_demora())

    assert client_admin.get(URL_COLA).context["pendientes"] == 2


def test_la_cola_vacia_no_es_un_error(client_admin):
    """Es el resultado normal de un ciclo sin novedades, que el propio CU-ALT-NOV
    contempla en E6."""
    contenido = client_admin.get(URL_COLA).content.decode()

    assert "No hay correos en la cola" in contenido


def test_el_buscador_de_la_cola_filtra(client_admin, ivrea):
    services.ingerir(ejemplo.correo_de_novedades())
    services.ingerir(ejemplo.correo_de_demora())

    respuesta = client_admin.get(URL_COLA, {"q": "reprogramación"})

    assert respuesta.context["correos"].count() == 1


def test_la_ficha_muestra_el_contenido_extraido(client_admin, ivrea):
    """Es lo que permite darse cuenta de que la extracción salió mal antes de
    gastar un solo ciclo del modelo."""
    correo = services.ingerir(ejemplo.correo_de_novedades()).correo

    respuesta = client_admin.get(url_ficha(correo))

    assert "| 9789878271583 |" in respuesta.content.decode()
    assert any(linea["es_fila"] for linea in respuesta.context["lineas"])


def test_la_ficha_muestra_las_portadas_embebidas(client_admin, ivrea):
    correo = services.ingerir(ejemplo.correo_de_novedades()).correo

    contenido = client_admin.get(url_ficha(correo)).content.decode()

    assert "tapa001@ivrea.test" in contenido
    assert "image/webp" in contenido


def test_la_ficha_muestra_que_va_a_heredar_el_borrador(client_admin, ivrea):
    """Si el proveedor tiene la editorial equivocada, todo lo que salga de este
    correo va a nacer mal: hay que poder verlo antes de aprobar."""
    correo = services.ingerir(ejemplo.correo_de_novedades()).correo

    contenido = client_admin.get(url_ficha(correo)).content.decode()

    assert "Sus borradores van a heredar" in contenido
    assert "Ivrea" in contenido


# ---------------------------------------------------------------------------
# Descarte
# ---------------------------------------------------------------------------


def test_descartar_lo_saca_de_la_cola(client_admin, ivrea, administrador):
    correo = services.ingerir(ejemplo.correo_de_novedades()).correo

    respuesta = client_admin.post(url_ficha(correo), {"motivo": "Es una factura, no un anuncio."})

    correo.refresh_from_db()
    assert respuesta.status_code == 302
    assert correo.estado == CorreoProveedor.DESCARTADO
    assert correo.motivo == "Es una factura, no un anuncio."
    assert correo.resuelto_por == administrador
    assert correo.resuelto_en is not None


def test_el_motivo_del_descarte_es_obligatorio(client_admin, ivrea):
    """Mismo criterio que el rechazo de un borrador en CU-ALT-REV: una cola llena de
    descartes sin explicación no sirve para entender nada después."""
    correo = services.ingerir(ejemplo.correo_de_novedades()).correo

    respuesta = client_admin.post(url_ficha(correo), {"motivo": ""})

    correo.refresh_from_db()
    assert respuesta.status_code == 200
    assert respuesta.context["form"].errors["motivo"]
    assert correo.estado == CorreoProveedor.PENDIENTE


def test_un_motivo_de_una_letra_no_alcanza(client_admin, ivrea):
    correo = services.ingerir(ejemplo.correo_de_novedades()).correo

    respuesta = client_admin.post(url_ficha(correo), {"motivo": "x"})

    assert respuesta.status_code == 200
    assert respuesta.context["form"].errors["motivo"]


def test_el_descarte_queda_auditado(client_admin, ivrea, administrador):
    correo = services.ingerir(ejemplo.correo_de_novedades()).correo

    client_admin.post(url_ficha(correo), {"motivo": "Es una factura."})

    registro = RegistroAuditoria.objects.get(accion=RegistroAuditoria.CORREO_DESCARTADO)
    assert registro.actor == administrador
    assert registro.objetivo == correo
    assert "Es una factura." in registro.detalle


def test_un_correo_ya_resuelto_no_se_vuelve_a_resolver(client_admin, ivrea, administrador):
    """El doble envío del formulario es el caso normal, no el raro."""
    correo = services.ingerir(ejemplo.correo_de_novedades()).correo
    client_admin.post(url_ficha(correo), {"motivo": "Es una factura."})

    client_admin.post(url_ficha(correo), {"motivo": "Otro motivo."})

    correo.refresh_from_db()
    assert correo.motivo == "Es una factura."
    assert RegistroAuditoria.objects.filter(accion=RegistroAuditoria.CORREO_DESCARTADO).count() == 1


def test_la_ficha_de_un_resuelto_no_ofrece_descartarlo(client_admin, ivrea, administrador):
    correo = services.ingerir(ejemplo.correo_de_novedades()).correo
    services.descartar(correo, administrador, "Es una factura.")

    contenido = client_admin.get(url_ficha(correo)).content.decode()

    assert "Ya resuelto" in contenido
    assert "Descartar correo" not in contenido


def test_el_get_de_la_ficha_no_resuelve_nada(client_admin, ivrea):
    correo = services.ingerir(ejemplo.correo_de_novedades()).correo

    client_admin.get(url_ficha(correo))

    correo.refresh_from_db()
    assert correo.estado == CorreoProveedor.PENDIENTE


# ---------------------------------------------------------------------------
# Permisos
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("rol_sin_permiso", ["cliente", "cajero"])
def test_la_cola_es_solo_del_administrador(client, ivrea, rol_sin_permiso):
    correo = services.ingerir(ejemplo.correo_de_novedades()).correo
    client.force_login(UsuarioFactory(rol=rol_sin_permiso))

    assert client.get(URL_COLA).status_code == 403
    assert client.get(url_ficha(correo)).status_code == 403
    assert client.post(url_ficha(correo), {"motivo": "cualquiera"}).status_code == 403
    correo.refresh_from_db()
    assert correo.estado == CorreoProveedor.PENDIENTE


def test_el_menu_enlaza_la_cola(client_admin):
    contenido = client_admin.get(URL_COLA).content.decode()

    assert URL_COLA in contenido
    assert "Correos recibidos" in contenido
