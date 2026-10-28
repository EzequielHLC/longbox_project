"""Módulo 19 · el perfil, los canales de aviso y el despachador (plan 00 de Telegram).

`CU-AVI-PEC`, `CU-AVI-CAM`, `CU-AVI-TGA` (la mitad de la web) y `CU-AVI-TGB`, por su
dirección real, y las cuatro decisiones del despachador: sin preferencia por
correo; Telegram si se eligió y se puede; si no se puede, por correo; nunca se pierde.
"""

import logging
from datetime import timedelta

import pytest
from django.urls import reverse
from django.utils import timezone

from apps.accounts.models import Usuario
from apps.accounts.tests.factories import UsuarioFactory
from apps.avisos.models import TIPOS, CodigoVinculacion, PreferenciaAviso, VinculoTelegram
from apps.avisos.tests.telegram_falso import TOKEN, telegram_falso
from apps.core import integraciones
from apps.core.models import RegistroAuditoria
from apps.pedidos import avisos

pytestmark = pytest.mark.django_db

PERFIL = reverse("avisos:perfil")
# La puerta de verdad, tomada antes de que la fixture de la red la reemplace.
PEDIR_REAL = integraciones.pedir


@pytest.fixture
def con_telegram(settings):
    settings.TELEGRAM_BOT_TOKEN = TOKEN
    return settings


def vincular(usuario, chat=555):
    return VinculoTelegram.objects.create(usuario=usuario, chat_id=chat, nombre_en_telegram="Eze")


def aviso(**cambios):
    datos = {
        "tipo": "preventas",
        "asunto": "Pre-ventas por llegar",
        "titulo": "Llegan pronto",
        "parrafos": ["Tres pre-ventas llegan esta semana."],
        "filas": [("Berserk #5", "08/11/2026")],
    }
    datos.update(cambios)
    return datos


# ---------------------------------------------------------------------------
# CU-AVI-PEC · el perfil, por su dirección real
# ---------------------------------------------------------------------------


def test_el_administrador_ve_su_perfil_con_sus_datos_y_sus_avisos(client_admin, administrador):
    respuesta = client_admin.get(PERFIL)

    html = respuesta.content.decode()
    assert respuesta.status_code == 200
    assert administrador.email in html
    assert "Mis avisos" in html
    assert len(respuesta.context["preferencias"]) == len(TIPOS)
    # Sin elegir nada, cada tipo muestra su canal por defecto (B-19-011).
    assert [(f["por_correo"], f["por_telegram"]) for f in respuesta.context["preferencias"]] == [
        (tipo.por_correo, tipo.por_telegram) for tipo in TIPOS
    ]
    assert "no está configurado" in html  # sin token, Telegram lo dice


@pytest.mark.parametrize("rol", ["cajero", "cliente"])
def test_otro_rol_no_entra_al_perfil_por_la_direccion_real(client, rol):
    client.force_login(UsuarioFactory(rol=rol))

    for url, metodo in [
        (PERFIL, "get"),
        (reverse("avisos:canales"), "post"),
        (reverse("avisos:vincular"), "post"),
        (reverse("avisos:desvincular"), "post"),
        (reverse("avisos:contrasena"), "get"),
    ]:
        assert getattr(client, metodo)(url).status_code == 403, url


def test_sin_sesion_el_perfil_pide_ingresar(client):
    assert reverse("accounts:login") in client.get(PERFIL).url


def test_el_encabezado_lleva_al_perfil_sólo_al_administrador(client_admin, client):
    assert PERFIL in client_admin.get(PERFIL).content.decode()
    client.force_login(UsuarioFactory(rol="cajero"))
    assert PERFIL not in client.get(reverse("caja:caja")).content.decode()


def test_el_administrador_cambia_su_contraseña_y_queda_auditado(client_admin, administrador):
    administrador.set_password("Vieja-2026!")
    administrador.save()
    client_admin.force_login(administrador)

    respuesta = client_admin.post(
        reverse("avisos:contrasena"),
        {
            "old_password": "Vieja-2026!",
            "new_password1": "Nueva-2026!xy",
            "new_password2": "Nueva-2026!xy",
        },
    )

    assert respuesta.url == PERFIL
    administrador.refresh_from_db()
    assert administrador.check_password("Nueva-2026!xy")
    assert RegistroAuditoria.objects.filter(
        accion=RegistroAuditoria.CAMBIO_CONTRASENA, objetivo_pk=administrador.pk
    ).exists()


# ---------------------------------------------------------------------------
# CU-AVI-CAM · los canales
# ---------------------------------------------------------------------------


def test_los_canales_se_guardan_por_tipo_y_quedan_auditados(client_admin, administrador):
    vincular(administrador)

    client_admin.post(
        reverse("avisos:canales"),
        {"correo_correos": "on", "telegram_correos": "on", "telegram_preventas": "on"},
    )

    preferencias = {p.tipo: p for p in PreferenciaAviso.objects.filter(usuario=administrador)}
    assert (preferencias["correos"].por_correo, preferencias["correos"].por_telegram) == (
        True,
        True,
    )
    assert (preferencias["preventas"].por_correo, preferencias["preventas"].por_telegram) == (
        False,
        True,
    )
    assert (preferencias["restock"].por_correo, preferencias["restock"].por_telegram) == (
        False,
        False,
    )
    registro = RegistroAuditoria.objects.get(accion=RegistroAuditoria.CANALES_DE_AVISO)
    assert "Pre-ventas: Telegram" in registro.detalle


def test_sin_chat_vinculado_telegram_no_se_puede_elegir(client_admin, administrador):
    client_admin.post(reverse("avisos:canales"), {"telegram_preventas": "on"})

    preferencia = PreferenciaAviso.objects.get(usuario=administrador, tipo="preventas")
    assert (preferencia.por_correo, preferencia.por_telegram) == (True, False)


def test_todo_por_telegram_con_el_chat_vinculado(client_admin, administrador):
    vincular(administrador)

    client_admin.post(reverse("avisos:canales"), {"atajo": "telegram"})

    assert PreferenciaAviso.objects.filter(
        usuario=administrador, por_telegram=True, por_correo=False
    ).count() == len(TIPOS)


# ---------------------------------------------------------------------------
# CU-AVI-TGA (la web) · CU-AVI-TGB
# ---------------------------------------------------------------------------


def test_sin_token_no_se_puede_vincular(client_admin, administrador):
    respuesta = client_admin.post(reverse("avisos:vincular"), follow=True)

    assert "no está configurado" in respuesta.content.decode()
    assert not CodigoVinculacion.objects.exists()


def test_vincular_da_un_enlace_de_un_solo_uso_al_bot(client_admin, administrador, con_telegram):
    falso, parche = telegram_falso()

    with parche:
        client_admin.post(reverse("avisos:vincular"))
        client_admin.post(reverse("avisos:vincular"))  # pedir otro anula el anterior
        html = client_admin.get(PERFIL).content.decode()

    codigo = CodigoVinculacion.objects.get(usuario=administrador)
    assert codigo.vigente
    assert codigo.vence_en <= timezone.now() + timedelta(minutes=15)
    assert f"https://t.me/longbox_prueba_bot?start={codigo.codigo}" in html


def test_desvincular_desde_el_perfil_borra_el_vínculo_y_queda_auditado(client_admin, administrador):
    vincular(administrador)

    client_admin.post(reverse("avisos:desvincular"))

    assert not VinculoTelegram.objects.exists()
    assert RegistroAuditoria.objects.filter(accion=RegistroAuditoria.DESVINCULO_TELEGRAM).exists()


# ---------------------------------------------------------------------------
# El despachador
# ---------------------------------------------------------------------------


def test_sin_preferencias_el_aviso_sale_por_correo_como_siempre(
    administrador, mailoutbox, con_telegram
):
    vincular(administrador)
    falso, parche = telegram_falso()

    with parche:
        avisos.avisar_administradores(**aviso())

    assert [m.to for m in mailoutbox] == [[administrador.email]]
    assert falso.mensajes() == []


def test_por_telegram_si_lo_eligió_y_se_puede(administrador, mailoutbox, con_telegram):
    vincular(administrador, chat=777)
    PreferenciaAviso.objects.create(
        usuario=administrador, tipo="preventas", por_correo=False, por_telegram=True
    )
    falso, parche = telegram_falso()

    with parche:
        avisos.avisar_administradores(**aviso())

    assert mailoutbox == []
    [texto] = falso.textos(777)
    assert "<b>Llegan pronto</b>" in texto and "Berserk #5" in texto


def test_si_telegram_no_contesta_le_llega_por_correo(administrador, mailoutbox, con_telegram):
    vincular(administrador)
    PreferenciaAviso.objects.create(
        usuario=administrador, tipo="preventas", por_correo=False, por_telegram=True
    )
    _, parche = telegram_falso(caido=True)

    with parche:
        avisos.avisar_administradores(**aviso())

    assert [m.to for m in mailoutbox] == [[administrador.email]]


def test_sin_chat_o_sin_token_le_llega_por_correo(administrador, mailoutbox):
    PreferenciaAviso.objects.create(
        usuario=administrador, tipo="preventas", por_correo=False, por_telegram=True
    )

    avisos.avisar_administradores(**aviso())

    assert [m.to for m in mailoutbox] == [[administrador.email]]


def test_lo_que_apagó_en_los_dos_canales_no_le_llega(administrador, mailoutbox):
    PreferenciaAviso.objects.create(
        usuario=administrador, tipo="restock", por_correo=False, por_telegram=False
    )

    avisos.avisar_administradores(**aviso(tipo="restock"))
    avisos.avisar_administradores(**aviso(tipo="preventas"))

    assert len(mailoutbox) == 1  # el de pre-ventas, que no tocó


def test_un_administrador_dado_de_baja_no_recibe_nada(administrador, mailoutbox):
    UsuarioFactory(rol="administrador", estado=Usuario.INACTIVO)

    avisos.avisar_administradores(**aviso())

    assert [m.to for m in mailoutbox] == [[administrador.email]]


# ---------------------------------------------------------------------------
# El token no queda en el log
# ---------------------------------------------------------------------------


def test_el_token_del_bot_no_queda_escrito_en_el_log(caplog):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

    assert TOKEN not in integraciones.para_el_log(url)
    assert integraciones.para_el_log(url) == "https://api.telegram.org/bot***/sendMessage"


def test_un_fallo_de_telegram_no_escribe_el_token(con_telegram, caplog, monkeypatch):
    from urllib.error import URLError

    from apps.avisos import telegram

    def sin_red(*args, **kwargs):
        raise URLError("sin red")

    monkeypatch.setattr(integraciones, "urlopen", sin_red)
    monkeypatch.setattr(integraciones, "pedir", PEDIR_REAL)
    with caplog.at_level(logging.WARNING):
        telegram.enviar(1, "hola")

    assert TOKEN not in caplog.text
    assert "bot***" in caplog.text
