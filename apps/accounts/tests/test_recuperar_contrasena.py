"""CU-48 — Recuperar Contraseña."""

from datetime import datetime, timedelta

import pytest
from django.contrib.auth.tokens import default_token_generator
from django.core import mail
from django.test import Client
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from freezegun import freeze_time

from apps.accounts.tests.factories import PASSWORD_DE_PRUEBA, UsuarioFactory
from apps.core.models import RegistroAuditoria

URL_PEDIR_ENLACE = reverse("accounts:password_reset")
URL_PROTEGIDA = reverse("core:tienda")
NUEVA_CONTRASENA = "OtraClaveDistinta456"
MOMENTO_DE_EMISION = datetime(2026, 8, 5, 10, 0, 0)

MENSAJE_NEUTRO = (
    "Si el correo ingresado corresponde a una cuenta registrada, recibirás un enlace de "
    "recuperación en los próximos minutos."
)

pytestmark = pytest.mark.django_db


def url_de_restablecimiento(usuario):
    uid = urlsafe_base64_encode(force_bytes(usuario.pk))
    token = default_token_generator.make_token(usuario)
    return reverse("accounts:password_reset_confirm", kwargs={"uidb64": uid, "token": token})


def abrir_formulario(client, usuario):
    """Sigue el enlace del correo: Django mueve el token a la sesión y redirige."""
    return client.get(url_de_restablecimiento(usuario), follow=False)


def texto_plano(respuesta):
    """Colapsa los saltos de línea del HTML para comparar el texto renderizado."""
    return " ".join(respuesta.content.decode().split())


def test_correo_existente_e_inexistente_devuelven_el_mismo_mensaje(client, cliente):
    con_cuenta = client.post(URL_PEDIR_ENLACE, {"email": cliente.email}, follow=True)
    sin_cuenta = client.post(URL_PEDIR_ENLACE, {"email": "nadie@longbox.test"}, follow=True)

    assert con_cuenta.status_code == sin_cuenta.status_code == 200
    assert MENSAJE_NEUTRO in texto_plano(con_cuenta)
    assert MENSAJE_NEUTRO in texto_plano(sin_cuenta)
    assert con_cuenta.redirect_chain == sin_cuenta.redirect_chain


def test_solo_se_envia_correo_a_una_cuenta_real(client, cliente):
    client.post(URL_PEDIR_ENLACE, {"email": "nadie@longbox.test"})
    assert mail.outbox == []

    client.post(URL_PEDIR_ENLACE, {"email": cliente.email})
    assert len(mail.outbox) == 1
    assert mail.outbox[0].to == [cliente.email]


def test_una_cuenta_inactiva_no_recibe_enlace(client):
    usuario = UsuarioFactory(is_active=False)

    client.post(URL_PEDIR_ENLACE, {"email": usuario.email})

    assert mail.outbox == []


def test_el_correo_incluye_un_enlace_utilizable(client, cliente):
    client.post(URL_PEDIR_ENLACE, {"email": cliente.email})

    cuerpo = mail.outbox[0].body
    assert "/cuentas/recuperar/" in cuerpo


def test_un_token_valido_permite_cambiar_la_contrasena(client, cliente):
    respuesta = abrir_formulario(client, cliente)

    final = client.post(
        respuesta.url,
        {"new_password1": NUEVA_CONTRASENA, "new_password2": NUEVA_CONTRASENA},
    )

    assert final.status_code == 302
    cliente.refresh_from_db()
    assert cliente.check_password(NUEVA_CONTRASENA)


def test_un_token_expirado_es_rechazado(client, cliente):
    # El token se emite y se usa bajo tiempo congelado: así la comparación es
    # contra el mismo reloj y no depende del huso horario de la máquina.
    with freeze_time(MOMENTO_DE_EMISION):
        url = url_de_restablecimiento(cliente)

    with freeze_time(MOMENTO_DE_EMISION + timedelta(minutes=31)):
        respuesta = client.get(url)

    assert respuesta.status_code == 200
    assert "El enlace ya no es válido" in respuesta.content.decode()
    cliente.refresh_from_db()
    assert cliente.check_password(PASSWORD_DE_PRUEBA)


def test_un_token_vigente_a_los_29_minutos_sigue_sirviendo(client, cliente):
    with freeze_time(MOMENTO_DE_EMISION):
        url = url_de_restablecimiento(cliente)

    with freeze_time(MOMENTO_DE_EMISION + timedelta(minutes=29)):
        respuesta = client.get(url)

    assert respuesta.status_code == 302  # redirige al formulario de nueva contraseña


def test_un_token_ya_usado_no_puede_reutilizarse(client, cliente):
    url = url_de_restablecimiento(cliente)
    respuesta = client.get(url)
    client.post(
        respuesta.url,
        {"new_password1": NUEVA_CONTRASENA, "new_password2": NUEVA_CONTRASENA},
    )

    segundo_uso = Client().get(url)

    assert "El enlace ya no es válido" in segundo_uso.content.decode()


def test_contrasenas_que_no_coinciden_no_cambian_nada_y_no_queman_el_token(client, cliente):
    respuesta = abrir_formulario(client, cliente)

    fallido = client.post(
        respuesta.url,
        {"new_password1": NUEVA_CONTRASENA, "new_password2": "otra-distinta"},
    )

    assert fallido.status_code == 200
    assert fallido.context["form"].errors
    cliente.refresh_from_db()
    assert cliente.check_password(PASSWORD_DE_PRUEBA)

    # El mismo enlace sigue sirviendo: no hace falta pedir un token nuevo.
    reintento = client.post(
        respuesta.url,
        {"new_password1": NUEVA_CONTRASENA, "new_password2": NUEVA_CONTRASENA},
    )
    assert reintento.status_code == 302


def test_contrasena_debil_es_rechazada_con_el_motivo(client, cliente):
    respuesta = abrir_formulario(client, cliente)

    fallido = client.post(respuesta.url, {"new_password1": "123", "new_password2": "123"})

    assert fallido.status_code == 200
    assert fallido.context["form"].errors["new_password2"]
    cliente.refresh_from_db()
    assert cliente.check_password(PASSWORD_DE_PRUEBA)


def test_el_cambio_invalida_todas_las_sesiones_activas(cliente):
    telefono = Client()
    computadora = Client()
    telefono.force_login(cliente)
    computadora.force_login(cliente)
    assert telefono.get(URL_PROTEGIDA).status_code == 200

    navegador_de_recuperacion = Client()
    respuesta = navegador_de_recuperacion.get(url_de_restablecimiento(cliente))
    navegador_de_recuperacion.post(
        respuesta.url,
        {"new_password1": NUEVA_CONTRASENA, "new_password2": NUEVA_CONTRASENA},
    )

    assert telefono.get(URL_PROTEGIDA).status_code == 302
    assert computadora.get(URL_PROTEGIDA).status_code == 302


def test_el_cambio_queda_registrado_en_auditoria(client, cliente):
    respuesta = abrir_formulario(client, cliente)

    client.post(
        respuesta.url,
        {"new_password1": NUEVA_CONTRASENA, "new_password2": NUEVA_CONTRASENA},
    )

    registro = RegistroAuditoria.objects.get(accion=RegistroAuditoria.CAMBIO_CONTRASENA)
    assert registro.actor == cliente
