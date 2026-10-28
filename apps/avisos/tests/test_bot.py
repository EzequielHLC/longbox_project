"""Módulo 19 · el bot: `CU-AVI-TGA` y `CU-AVI-TGB` desde el chat, y `CU-AVI-COR`.

Las novedades se arman como las manda Telegram y entran por el webhook real (con
su secreto) o por `bot.procesar`. La autorización se mira en cada acción: un
botón ajeno, uno armado a mano o el de un Administrador dado de baja no hacen nada.
"""

from datetime import timedelta
from io import StringIO
from unittest.mock import patch

import pytest
from django.core.management import call_command
from django.urls import reverse
from django.utils import timezone

from apps.accounts.models import Usuario
from apps.accounts.tests.factories import UsuarioFactory
from apps.avisos import bot, telegram
from apps.avisos.models import CodigoVinculacion, VinculoTelegram
from apps.avisos.tests.telegram_falso import TOKEN, telegram_falso
from apps.core.models import RegistroAuditoria
from apps.suppliers import casilla, services
from apps.suppliers.models import CorreoProveedor
from apps.suppliers.tests import correos_de_ejemplo as ejemplo
from apps.suppliers.tests.factories import ProveedorFactory

pytestmark = pytest.mark.django_db

CHAT = 4242
WEBHOOK = reverse("avisos:webhook")


@pytest.fixture(autouse=True)
def con_telegram(settings):
    settings.TELEGRAM_BOT_TOKEN = TOKEN
    settings.URL_PUBLICA = "https://longbox.test"


@pytest.fixture
def falso():
    falso, parche = telegram_falso()
    with parche:
        yield falso


@pytest.fixture
def vinculado(administrador):
    VinculoTelegram.objects.create(usuario=administrador, chat_id=CHAT, nombre_en_telegram="Eze")
    return administrador


@pytest.fixture
def correo(db):
    ProveedorFactory(correo_comercial="novedades@ivrea.test")
    return services.ingerir(ejemplo.correo_de_novedades()).correo


def mensaje(texto, chat=CHAT, responde_a=None):
    cuerpo = {
        "message_id": 1,
        "chat": {"id": chat, "type": "private"},
        "from": {"first_name": "Ezequiel", "username": "eze"},
        "text": texto,
    }
    if responde_a:
        cuerpo["reply_to_message"] = {"text": responde_a}
    return {"update_id": 1, "message": cuerpo}


def boton(datos, chat=CHAT):
    return {
        "update_id": 2,
        "callback_query": {
            "id": "consulta",
            "data": datos,
            "message": {"message_id": 9, "chat": {"id": chat, "type": "private"}},
        },
    }


def datos_de(accion, correo_pk, chat=CHAT, extra=""):
    return bot._boton_de(accion, correo_pk, chat, extra)


# ---------------------------------------------------------------------------
# CU-AVI-TGA · /start con el código
# ---------------------------------------------------------------------------


def test_start_no_vincula_todavía_da_un_número_para_el_perfil(administrador, falso):
    """B-19-005: abrir el enlace no alcanza; un enlace filtrado no toma la cuenta."""
    codigo = CodigoVinculacion.nuevo(administrador)

    bot.procesar(mensaje(f"/start {codigo.codigo}"))

    assert not VinculoTelegram.objects.exists()
    codigo.refresh_from_db()
    assert (codigo.chat_pendiente, codigo.nombre_pendiente) == (CHAT, "Ezequiel")
    assert len(codigo.confirmacion) == 6 and codigo.confirmacion.isdigit()
    numero = f"{codigo.confirmacion[:3]} {codigo.confirmacion[3:]}"
    assert numero in falso.textos(CHAT)[-1]


def test_el_número_en_el_perfil_vincula_el_chat(client_admin, administrador, falso):
    codigo = CodigoVinculacion.nuevo(administrador)
    bot.procesar(mensaje(f"/start {codigo.codigo}"))
    codigo.refresh_from_db()

    respuesta = client_admin.post(
        reverse("avisos:confirmar"), {"numero": codigo.confirmacion}, follow=True
    )

    vinculo = VinculoTelegram.objects.get()
    assert (vinculo.usuario, vinculo.chat_id, vinculo.nombre_en_telegram) == (
        administrador,
        CHAT,
        "Ezequiel",
    )
    codigo.refresh_from_db()
    assert codigo.usado_en is not None
    assert RegistroAuditoria.objects.filter(accion=RegistroAuditoria.VINCULO_TELEGRAM).exists()
    assert "quedó vinculado" in falso.textos(CHAT)[-1]
    assert "Telegram quedó vinculado" in respuesta.content.decode()


def test_un_número_equivocado_no_vincula_y_cinco_anulan_el_enlace(
    client_admin, administrador, falso
):
    codigo = CodigoVinculacion.nuevo(administrador)
    bot.procesar(mensaje(f"/start {codigo.codigo}"))
    codigo.refresh_from_db()
    malo = "000000" if codigo.confirmacion != "000000" else "111111"

    for _ in range(4):
        client_admin.post(reverse("avisos:confirmar"), {"numero": malo})
    codigo.refresh_from_db()
    assert codigo.intentos == 4
    respuesta = client_admin.post(reverse("avisos:confirmar"), {"numero": malo}, follow=True)

    assert "Demasiados intentos" in respuesta.content.decode()
    assert not CodigoVinculacion.objects.exists()
    assert not VinculoTelegram.objects.exists()


def test_confirmar_sin_que_el_bot_haya_dado_un_número(client_admin, administrador, falso):
    CodigoVinculacion.nuevo(administrador)

    respuesta = client_admin.post(reverse("avisos:confirmar"), {"numero": "123456"}, follow=True)

    assert "No hay una vinculación esperando" in respuesta.content.decode()
    assert not VinculoTelegram.objects.exists()


def test_no_fui_yo_anula_el_enlace(client_admin, administrador, falso):
    codigo = CodigoVinculacion.nuevo(administrador)
    bot.procesar(mensaje(f"/start {codigo.codigo}", chat=9999))

    client_admin.post(reverse("avisos:cancelar"))

    assert not CodigoVinculacion.objects.exists()
    assert not VinculoTelegram.objects.exists()


def test_el_número_de_otra_cuenta_no_sirve(client, administrador, falso):
    codigo = CodigoVinculacion.nuevo(administrador)
    bot.procesar(mensaje(f"/start {codigo.codigo}"))
    codigo.refresh_from_db()
    otro = UsuarioFactory(rol="administrador")
    client.force_login(otro)

    client.post(reverse("avisos:confirmar"), {"numero": codigo.confirmacion})

    assert not VinculoTelegram.objects.exists()


def test_un_código_vencido_o_usado_no_vincula(administrador, falso):
    vencido = CodigoVinculacion.nuevo(administrador)
    CodigoVinculacion.objects.filter(pk=vencido.pk).update(
        vence_en=timezone.now() - timedelta(minutes=1)
    )

    bot.procesar(mensaje(f"/start {vencido.codigo}"))
    bot.procesar(mensaje("/start inventado"))

    assert not VinculoTelegram.objects.exists()
    assert all("no sirve" in t for t in falso.textos(CHAT))


def test_el_código_de_otro_rol_no_vincula(falso):
    codigo = CodigoVinculacion.nuevo(UsuarioFactory(rol="cajero"))

    bot.procesar(mensaje(f"/start {codigo.codigo}"))

    assert not VinculoTelegram.objects.exists()


def test_un_chat_es_de_una_sola_cuenta(administrador, falso):
    otro = UsuarioFactory(rol="administrador")
    VinculoTelegram.objects.create(usuario=otro, chat_id=CHAT)
    codigo = CodigoVinculacion.nuevo(administrador)
    bot.procesar(mensaje(f"/start {codigo.codigo}"))
    codigo.refresh_from_db()

    bot.confirmar_vinculo(administrador, codigo.confirmacion)

    assert list(VinculoTelegram.objects.values_list("usuario", flat=True)) == [administrador.pk]


# ---------------------------------------------------------------------------
# CU-AVI-TGB · /salir
# ---------------------------------------------------------------------------


def test_salir_desvincula_desde_el_chat(vinculado, falso):
    bot.procesar(mensaje("/salir"))

    assert not VinculoTelegram.objects.exists()
    assert RegistroAuditoria.objects.filter(
        accion=RegistroAuditoria.DESVINCULO_TELEGRAM, detalle__contains="el chat"
    ).exists()


def test_ayuda_responde_la_lista_de_comandos(vinculado, falso):
    bot.procesar(mensaje("/ayuda"))

    assert "/salir" in falso.textos(CHAT)[-1]


# ---------------------------------------------------------------------------
# CU-AVI-COR · el correo nuevo con sus botones
# ---------------------------------------------------------------------------


def test_un_correo_nuevo_llega_por_telegram_con_sus_dos_botones(
    vinculado, correo, falso, mailoutbox
):
    vinculado.preferencias_de_aviso.create(tipo="correos", por_correo=False, por_telegram=True)

    casilla._avisar_nuevos([correo])

    [enviado] = falso.mensajes(CHAT)
    assert correo.asunto in enviado["text"]
    textos = [b[0]["text"] for b in enviado["reply_markup"]["inline_keyboard"]]
    assert textos == ["Aprobar y procesar", "Descartar"]
    assert mailoutbox == []  # eligió sólo Telegram


def test_aprobar_desde_el_chat_es_co017_con_el_administrador_como_actor(vinculado, correo, falso):
    with patch.object(services, "aprobar_correo", wraps=services.aprobar_correo) as aprobar:
        bot.procesar(boton(datos_de("ap", correo.pk)))

    aprobar.assert_called_once_with(correo.pk, actor=vinculado)
    correo.refresh_from_db()
    assert correo.resuelto_por == vinculado
    # Sin modelo de lenguaje (la red está cortada), falla como desde la web.
    assert correo.estado == CorreoProveedor.FALLIDO
    assert any(f"correo #{correo.pk}" in t for t in falso.textos(CHAT))


def test_aprobar_lo_que_otro_ya_resolvió_lo_avisa(vinculado, correo, falso, administrador):
    services.descartar(correo, administrador, "Repetido")

    bot.procesar(boton(datos_de("ap", correo.pk)))

    assert "ya resolvió" in falso.textos(CHAT)[-1]


def test_descartar_con_un_motivo_rápido_es_co018_y_se_audita(vinculado, correo, falso):
    bot.procesar(boton(datos_de("de", correo.pk)))
    motivos = falso.mensajes(CHAT)[-1]["reply_markup"]["inline_keyboard"]
    primero = motivos[0][0]["callback_data"]

    bot.procesar(boton(primero))

    correo.refresh_from_db()
    assert (correo.estado, correo.motivo) == (CorreoProveedor.DESCARTADO, bot.MOTIVOS[0])
    assert correo.resuelto_por == vinculado
    registro = RegistroAuditoria.objects.get(accion=RegistroAuditoria.CORREO_DESCARTADO)
    assert "desde Telegram" in registro.detalle


def test_descartar_con_otro_motivo_lo_pide_y_lo_toma_de_la_respuesta(vinculado, correo, falso):
    bot.procesar(boton(datos_de("do", correo.pk)))
    pregunta = falso.mensajes(CHAT)[-1]
    assert pregunta["reply_markup"]["force_reply"] is True

    bot.procesar(mensaje("Es un saludo de fin de año", responde_a=pregunta["text"]))

    correo.refresh_from_db()
    assert (correo.estado, correo.motivo) == (
        CorreoProveedor.DESCARTADO,
        "Es un saludo de fin de año",
    )


def test_un_botón_armado_a_mano_no_hace_nada(vinculado, correo, falso):
    bot.procesar(boton(f"dm:{correo.pk}:0:firmafalsa00"))

    correo.refresh_from_db()
    assert correo.estado == CorreoProveedor.PENDIENTE
    assert (
        "answerCallbackQuery",
        {"callback_query_id": "consulta", "text": "Botón inválido."},
    ) in falso.llamadas


def test_el_botón_de_otro_chat_no_sirve_en_este(vinculado, correo, falso):
    ajeno = datos_de("dm", correo.pk, chat=999, extra="0")

    bot.procesar(boton(ajeno))

    correo.refresh_from_db()
    assert correo.estado == CorreoProveedor.PENDIENTE


def test_un_administrador_dado_de_baja_no_resuelve_desde_su_chat(vinculado, correo, falso):
    UsuarioFactory(rol="administrador")  # I-12: siempre queda uno activo
    Usuario.objects.filter(pk=vinculado.pk).update(estado=Usuario.INACTIVO)

    bot.procesar(boton(datos_de("dm", correo.pk, extra="0")))

    correo.refresh_from_db()
    assert correo.estado == CorreoProveedor.PENDIENTE


# ---------------------------------------------------------------------------
# El webhook y el comando
# ---------------------------------------------------------------------------


def test_el_webhook_exige_el_secreto_de_telegram(client, vinculado, falso):
    sin_secreto = client.post(WEBHOOK, mensaje("/salir"), content_type="application/json")
    con_otro = client.post(
        WEBHOOK,
        mensaje("/salir"),
        content_type="application/json",
        headers={"X-Telegram-Bot-Api-Secret-Token": "otro"},
    )

    assert (sin_secreto.status_code, con_otro.status_code) == (403, 403)
    assert VinculoTelegram.objects.exists()


def test_el_webhook_con_el_secreto_procesa_la_novedad(client, vinculado, falso):
    respuesta = client.post(
        WEBHOOK,
        mensaje("/salir"),
        content_type="application/json",
        headers={"X-Telegram-Bot-Api-Secret-Token": telegram.secreto_del_webhook()},
    )

    assert respuesta.status_code == 200
    assert not VinculoTelegram.objects.exists()


def test_escuchar_procesa_lo_que_llegó(vinculado):
    falso, parche = telegram_falso(novedades=[mensaje("/salir")])

    with parche:
        call_command("telegram", "escuchar", "--una-vez", stdout=StringIO())

    assert not VinculoTelegram.objects.exists()
    assert ("deleteWebhook", {"drop_pending_updates": False}) in falso.llamadas


def test_estado_dice_el_bot(falso):
    salida = StringIO()

    call_command("telegram", "estado", stdout=salida)

    assert "@longbox_prueba_bot" in salida.getvalue()


def test_el_webhook_se_pone_en_la_url_pública(falso):
    call_command("telegram", "webhook", stdout=StringIO())

    metodo, cuerpo = next(llamada for llamada in falso.llamadas if llamada[0] == "setWebhook")
    assert [m for m, _ in falso.llamadas][-1] == "setMyCommands"
    assert cuerpo["url"] == "https://longbox.test" + WEBHOOK
    assert cuerpo["secret_token"] == telegram.secreto_del_webhook()


# ---------------------------------------------------------------------------
# Las ramas de error y los demás resultados (foco reforzado: control de acceso)
# ---------------------------------------------------------------------------


def test_una_novedad_rota_no_frena_al_bot(falso):
    bot.procesar({"update_id": 3, "callback_query": {"id": "x"}})  # sin mensaje ni datos
    bot.procesar(
        {"update_id": 4, "message": {"chat": {"id": 1, "type": "group"}, "text": "/salir"}}
    )

    assert (
        "answerCallbackQuery",
        {"callback_query_id": "x", "text": "Botón inválido."},
    ) in falso.llamadas
    assert falso.mensajes() == []  # en un grupo no contesta


def test_salir_sin_vínculo_lo_dice(falso):
    bot.procesar(mensaje("/salir"))

    assert "no está vinculado" in falso.textos(CHAT)[-1]


def test_aprobar_un_correo_con_novedades_informa_los_borradores(vinculado, correo, falso):
    from types import SimpleNamespace

    def procesado(pk, *, actor):
        CorreoProveedor.objects.filter(pk=pk).update(estado=CorreoProveedor.PROCESADO)
        return SimpleNamespace(
            generacion=SimpleNamespace(resumen={"generados": 3, "duplicados": 1})
        )

    with patch.object(services, "aprobar_correo", side_effect=procesado):
        bot.procesar(boton(datos_de("ap", correo.pk)))

    texto = falso.textos(CHAT)[-1]
    assert "3 borrador(es)" in texto and "1 omitido(s)" in texto
    assert "Revisar los borradores" in texto


def test_aprobar_un_aviso_de_demora_dice_su_motivo(vinculado, correo, falso):
    from types import SimpleNamespace

    def demora(pk, *, actor):
        CorreoProveedor.objects.filter(pk=pk).update(
            estado=CorreoProveedor.PROCESADO, motivo="Es un aviso de demora."
        )
        return SimpleNamespace(generacion=None)

    with patch.object(services, "aprobar_correo", side_effect=demora):
        bot.procesar(boton(datos_de("ap", correo.pk)))

    assert "Es un aviso de demora." in falso.textos(CHAT)[-1]


def test_aprobar_un_correo_que_ya_no_existe(vinculado, falso):
    bot.procesar(boton(datos_de("ap", 99999)))

    assert "ya no existe" in falso.textos(CHAT)[-1]


def test_descartar_lo_que_ya_no_se_puede_descartar_lo_dice(vinculado, correo, falso):
    CorreoProveedor.objects.filter(pk=correo.pk).update(estado=CorreoProveedor.FALLIDO)

    bot.procesar(boton(datos_de("dm", correo.pk, extra="0")))

    assert "ya no se puede descartar" in falso.textos(CHAT)[-1]
    correo.refresh_from_db()
    assert correo.estado == CorreoProveedor.FALLIDO


def test_descartar_sin_motivo_lo_pide(vinculado, correo, falso):
    bot.procesar(
        mensaje("   ", responde_a=f"Escribí el motivo para descartar el correo #{correo.pk}")
    )

    assert "obligatorio" in falso.textos(CHAT)[-1]
    correo.refresh_from_db()
    assert correo.estado == CorreoProveedor.PENDIENTE


def test_descartar_un_correo_que_ya_no_existe(vinculado, falso):
    bot.procesar(mensaje("Spam", responde_a="Escribí el motivo para descartar el correo #99999"))

    assert "ya no existe" in falso.textos(CHAT)[-1]


def test_descartar_desde_un_chat_sin_vínculo_no_hace_nada(correo, falso):
    bot.procesar(mensaje("Spam", responde_a=f"descartar el correo #{correo.pk}"))

    correo.refresh_from_db()
    assert correo.estado == CorreoProveedor.PENDIENTE
    assert "no está vinculado" in falso.textos(CHAT)[-1]


def test_el_menú_de_motivos_y_la_pregunta_del_otro_motivo(vinculado, correo, falso):
    bot.procesar(boton(datos_de("de", correo.pk)))

    opciones = [
        fila[0]["text"] for fila in falso.mensajes(CHAT)[-1]["reply_markup"]["inline_keyboard"]
    ]
    assert opciones == [*bot.MOTIVOS, "Otro motivo…"]


def test_un_motivo_fuera_de_la_lista_es_un_botón_inválido(vinculado, correo, falso):
    bot.procesar(boton(datos_de("dm", correo.pk, extra="9")))

    correo.refresh_from_db()
    assert correo.estado == CorreoProveedor.PENDIENTE


def test_sin_token_los_comandos_lo_dicen(settings):
    from django.core.management.base import CommandError

    settings.TELEGRAM_BOT_TOKEN = ""
    with pytest.raises(CommandError, match="TELEGRAM_BOT_TOKEN"):
        call_command("telegram", "estado", stdout=StringIO())


def test_el_webhook_sin_https_no_se_pone(settings, falso):
    from django.core.management.base import CommandError

    settings.URL_PUBLICA = "http://127.0.0.1:8000"
    with pytest.raises(CommandError, match="https"):
        call_command("telegram", "webhook", stdout=StringIO())


def test_el_webhook_con_un_cuerpo_ilegible_responde_400(client, falso):
    respuesta = client.post(
        WEBHOOK,
        "no es json",
        content_type="application/json",
        headers={"X-Telegram-Bot-Api-Secret-Token": telegram.secreto_del_webhook()},
    )

    assert respuesta.status_code == 400
