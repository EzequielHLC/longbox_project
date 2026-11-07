"""`CO-228` proponerCambioDeModelo y `CO-229` confirmarCambioDeModelo (plan 00, A).

El sistema propone y el Administrador cambia: nunca cambia solo. Por la dirección
real, con el modelo de mentira detrás de la puerta HTTP única.
"""

from unittest.mock import patch

import pytest
from django.urls import reverse

from apps.accounts.tests.factories import UsuarioFactory
from apps.core import integraciones, llm, modelo_de_respaldo
from apps.core.models import ConfiguracionSistema, RegistroAuditoria

pytestmark = pytest.mark.django_db

URL = reverse("suppliers:cambiar_modelo")
CAIDO = integraciones.Respuesta(motivo=integraciones.SIN_CONEXION)
SIN_CREDITO = integraciones.Respuesta(motivo=integraciones.RECHAZADO, estado_http=402)
BIEN = integraciones.Respuesta(datos={"choices": [{"message": {"content": '{"ok": true}'}}]})
ILEGIBLE = integraciones.Respuesta(datos={"choices": [{"message": {"content": "hola"}}]})


@pytest.fixture
def configuracion(db):
    c = ConfiguracionSistema.obtener()
    c.llm_modo = ConfiguracionSistema.LOCAL
    c.llm_url = "http://127.0.0.1:1234/v1/chat/completions"
    c.llm_modelo = "gemma-local"
    c.llm_api_key = ""
    c.llm_respaldo_modo = ConfiguracionSistema.REMOTO
    c.llm_respaldo_url = "https://proveedor.test/api/v1/chat/completions"
    c.llm_respaldo_modelo = "remoto-grande"
    c.llm_respaldo_api_key = "clave-del-respaldo-1234"
    c.save()
    return c


def pedir(respuesta, veces=1):
    with patch("apps.core.integraciones.pedir", return_value=respuesta):
        for _ in range(veces):
            llm.pedir_json("sistema", "usuario")


def propuestas():
    return RegistroAuditoria.objects.filter(accion=RegistroAuditoria.CAMBIO_MODELO_PROPUESTO)


# ---------------------------------------------------------------------------
# CO-228 proponerCambioDeModelo
# ---------------------------------------------------------------------------


def test_CO228_tres_fallas_seguidas_proponen_el_cambio_y_avisan(
    configuracion, administrador, mailoutbox, django_capture_on_commit_callbacks
):
    with django_capture_on_commit_callbacks(execute=True):
        pedir(CAIDO, veces=3)

    configuracion.refresh_from_db()
    assert configuracion.llm_fallas_seguidas == 3
    assert configuracion.llm_cambio_propuesto_en is not None
    assert propuestas().count() == 1
    assert "respaldo" in mailoutbox[-1].subject.lower() or "no responde" in mailoutbox[-1].subject
    assert administrador.email in mailoutbox[-1].to


def test_CO228_no_cambia_el_modelo_activo(configuracion):
    pedir(CAIDO, veces=5)

    configuracion.refresh_from_db()
    # Postcondición negativa: el sistema propone, no cambia.
    assert (configuracion.llm_url, configuracion.llm_modelo) == (
        "http://127.0.0.1:1234/v1/chat/completions",
        "gemma-local",
    )
    assert not RegistroAuditoria.objects.filter(accion=RegistroAuditoria.CAMBIO_MODELO).exists()


def test_CO228_se_propone_una_vez_por_racha(configuracion):
    pedir(CAIDO, veces=7)

    assert propuestas().count() == 1


def test_CO228_un_rechazo_del_proveedor_tambien_cuenta(configuracion):
    pedir(SIN_CREDITO, veces=3)

    assert propuestas().count() == 1


def test_CO228_dos_fallas_no_alcanzan(configuracion):
    pedir(CAIDO, veces=2)

    assert not propuestas().exists()


def test_CO228_un_acierto_corta_la_racha_y_permite_volver_a_proponer(configuracion):
    pedir(CAIDO, veces=3)
    pedir(BIEN)

    configuracion.refresh_from_db()
    assert (configuracion.llm_fallas_seguidas, configuracion.llm_cambio_propuesto_en) == (0, None)

    pedir(CAIDO, veces=3)
    assert propuestas().count() == 2


def test_CO228_una_respuesta_ilegible_no_cuenta_como_falla(configuracion):
    pedir(CAIDO, veces=2)
    pedir(ILEGIBLE)
    pedir(CAIDO, veces=2)

    assert not propuestas().exists()


def test_CO228_sin_respaldo_el_aviso_dice_que_no_hay(
    configuracion, administrador, mailoutbox, django_capture_on_commit_callbacks
):
    configuracion.llm_respaldo_url = ""
    configuracion.save()

    with django_capture_on_commit_callbacks(execute=True):
        pedir(CAIDO, veces=3)

    assert "No hay modelo de respaldo" in propuestas().get().detalle
    assert "no hay un modelo de respaldo" in mailoutbox[-1].body.lower()


# ---------------------------------------------------------------------------
# CO-229 confirmarCambioDeModelo
# ---------------------------------------------------------------------------


def disponible(_perfil):
    return llm.EstadoDelServicio(
        disponible=True, modelos=["remoto-grande"], modelo_configurado="remoto-grande"
    )


def caido(_perfil):
    return llm.EstadoDelServicio(detalle="El servicio no respondió.")


def test_CO229_intercambia_el_activo_y_el_respaldo(configuracion, administrador):
    pedir(CAIDO, veces=3)

    modelo_de_respaldo.confirmar_cambio(administrador, probar=disponible)

    configuracion.refresh_from_db()
    assert (configuracion.llm_modo, configuracion.llm_url, configuracion.llm_modelo) == (
        ConfiguracionSistema.REMOTO,
        "https://proveedor.test/api/v1/chat/completions",
        "remoto-grande",
    )
    assert configuracion.llm_api_key == "clave-del-respaldo-1234"
    assert (configuracion.llm_respaldo_url, configuracion.llm_respaldo_modelo) == (
        "http://127.0.0.1:1234/v1/chat/completions",
        "gemma-local",
    )
    assert (configuracion.llm_fallas_seguidas, configuracion.llm_cambio_propuesto_en) == (0, None)
    registro = RegistroAuditoria.objects.get(accion=RegistroAuditoria.CAMBIO_MODELO)
    assert registro.actor == administrador
    assert "clave-del-respaldo" not in registro.detalle


def test_CO229_prueba_el_respaldo_sobre_su_propio_perfil(configuracion, administrador):
    vistos = []

    def probar(perfil):
        vistos.append(perfil)
        return disponible(perfil)

    modelo_de_respaldo.confirmar_cambio(administrador, probar=probar)

    (perfil,) = vistos
    assert (perfil.llm_url, perfil.llm_api_key) == (
        "https://proveedor.test/api/v1/chat/completions",
        "clave-del-respaldo-1234",
    )


def test_CO229_si_el_respaldo_tampoco_responde_no_cambia_nada(configuracion, administrador):
    antes = (configuracion.llm_url, configuracion.llm_respaldo_url)

    with pytest.raises(modelo_de_respaldo.CambioRechazado, match="tampoco responde"):
        modelo_de_respaldo.confirmar_cambio(administrador, probar=caido)

    configuracion.refresh_from_db()
    assert (configuracion.llm_url, configuracion.llm_respaldo_url) == antes
    assert not RegistroAuditoria.objects.filter(accion=RegistroAuditoria.CAMBIO_MODELO).exists()


def test_CO229_si_el_servidor_no_ofrece_el_modelo_no_cambia(configuracion, administrador):
    def sin_el_modelo(_perfil):
        return llm.EstadoDelServicio(
            disponible=True, modelos=["otro"], modelo_configurado="remoto-grande"
        )

    with pytest.raises(modelo_de_respaldo.CambioRechazado, match="no ofrece el modelo"):
        modelo_de_respaldo.confirmar_cambio(administrador, probar=sin_el_modelo)


def test_CO229_sin_respaldo_no_se_puede(configuracion, administrador):
    configuracion.llm_respaldo_url = ""
    configuracion.save()

    with pytest.raises(modelo_de_respaldo.CambioRechazado, match="No hay un modelo de respaldo"):
        modelo_de_respaldo.confirmar_cambio(administrador, probar=disponible)


def test_CO229_por_la_pantalla_mirar_no_cambia_y_confirmar_si(client_admin, configuracion):
    pagina = client_admin.get(URL)

    assert "remoto-grande" in pagina.content.decode()
    assert "clave-del-respaldo" not in pagina.content.decode()
    configuracion.refresh_from_db()
    assert configuracion.llm_modelo == "gemma-local"

    with patch("apps.core.llm.estado", side_effect=disponible):
        respuesta = client_admin.post(URL)

    configuracion.refresh_from_db()
    assert respuesta.url == reverse("suppliers:diagnostico_llm")
    assert configuracion.llm_modelo == "remoto-grande"


def test_CO229_por_la_pantalla_un_respaldo_caido_se_informa(client_admin, configuracion):
    with patch("apps.core.llm.estado", side_effect=caido):
        respuesta = client_admin.post(URL)

    assert "tampoco responde" in respuesta.content.decode()
    configuracion.refresh_from_db()
    assert configuracion.llm_modelo == "gemma-local"


@pytest.mark.parametrize("rol", ["cajero", "cliente"])
def test_CO229_el_rol_equivocado_no_cambia_el_modelo(client, configuracion, rol):
    client.force_login(UsuarioFactory(rol=rol))

    with patch("apps.core.llm.estado", side_effect=disponible):
        respuestas = [client.get(URL), client.post(URL)]

    assert {r.status_code for r in respuestas} == {403}
    configuracion.refresh_from_db()
    assert configuracion.llm_modelo == "gemma-local"


# ---------------------------------------------------------------------------
# El respaldo en Parámetros
# ---------------------------------------------------------------------------


def test_el_respaldo_se_guarda_sin_mostrar_ni_auditar_la_clave(client_admin, configuracion):
    respuesta = client_admin.post(
        reverse("catalog:parametros"),
        {
            "guardar_respaldo": "1",
            "llm_respaldo_modo": ConfiguracionSistema.REMOTO,
            "llm_respaldo_url": "https://otro.test/v1/chat/completions",
            "llm_respaldo_modelo": "otro-modelo",
            "respaldo_api_key": "clave-nueva-9876",
        },
    )

    configuracion.refresh_from_db()
    assert respuesta.status_code == 302
    assert (configuracion.llm_respaldo_url, configuracion.llm_respaldo_api_key) == (
        "https://otro.test/v1/chat/completions",
        "clave-nueva-9876",
    )
    registro = RegistroAuditoria.objects.filter(accion=RegistroAuditoria.PARAMETRO_MODIFICADO)
    assert registro.exists()
    assert all("clave-nueva" not in r.detalle for r in registro)
    pagina = client_admin.get(reverse("catalog:parametros")).content.decode()
    assert "clave-nueva-9876" not in pagina
    assert "…9876" in pagina


def test_un_respaldo_remoto_sin_modelo_se_rechaza(client_admin, configuracion):
    respuesta = client_admin.post(
        reverse("catalog:parametros"),
        {
            "guardar_respaldo": "1",
            "llm_respaldo_modo": ConfiguracionSistema.REMOTO,
            "llm_respaldo_url": "https://otro.test/v1/chat/completions",
            "llm_respaldo_modelo": "",
        },
    )

    assert "necesita que se nombre el modelo" in respuesta.content.decode()
