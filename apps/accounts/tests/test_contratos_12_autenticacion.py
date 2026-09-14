"""Pruebas de contrato del Módulo 12 — Autenticación (CO-114 a CO-119, CO-196).

Se escriben desde el contrato, no desde la implementación: cada prueba transcribe una
postcondición declarada y afirma sus dos mitades —el valor anterior y el posterior— según el
apartado 3 de `docs/pruebas/ESPECIFICACION.md`.

**Dos postcondiciones de este módulo no se pueden afirmar como están declaradas.** CO-117 declara
«se creó tr : TokenRecuperacion», CO-118 «tr.estado pasó de Vigente a Consumido» y CO-119
«EnlaceActivacion.estado pasó de Vigente a Consumido». `TokenRecuperacion` y `EnlaceActivacion`
son conceptos `<<planificado>>` del modelo de dominio: no existen como tabla, así que no hay
instancia cuyo estado mirar. Lo que sí es observable es la consecuencia —el enlace deja de
funcionar— y eso es lo que se afirma, con el rótulo `_efecto_observable` en el nombre para que no
se confunda con la postcondición literal. Anotado en `bitacora/12-autenticacion.md`.
"""

from datetime import timedelta

import pytest
from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.core import mail
from django.test import Client
from django.urls import reverse
from django.utils import timezone
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from freezegun import freeze_time

from apps.accounts.models import IntentoFallido, Usuario
from apps.accounts.tests.factories import PASSWORD_DE_PRUEBA, UsuarioFactory
from apps.core.models import RegistroAuditoria

pytestmark = pytest.mark.django_db

URL_LOGIN = reverse("accounts:login")
URL_LOGOUT = reverse("accounts:logout")
URL_RENOVAR = reverse("accounts:renovar_sesion")
URL_PEDIR_ENLACE = reverse("accounts:password_reset")
URL_PROTEGIDA = reverse("core:tienda")

NUEVA_CONTRASENA = "ContrasenaNueva789"


def hay_sesion(client):
    return "_auth_user_id" in client.session


def url_de_token(usuario):
    """La dirección del enlace de un solo uso, la misma forma para activar y para recuperar."""
    return reverse(
        "accounts:password_reset_confirm",
        kwargs={
            "uidb64": urlsafe_base64_encode(force_bytes(usuario.pk)),
            "token": default_token_generator.make_token(usuario),
        },
    )


def url_de_activacion(usuario):
    return reverse(
        "accounts:activar_cuenta",
        kwargs={
            "uidb64": urlsafe_base64_encode(force_bytes(usuario.pk)),
            "token": default_token_generator.make_token(usuario),
        },
    )


def fijar_contrasena(client, url, contrasena, confirmacion=None):
    """Recorre el enlace y envía el formulario, que es como lo usa una persona.

    Django mueve el token del enlace a la sesión y redirige a una dirección con `set-password`;
    el formulario se envía a esa segunda dirección y no a la del enlace.
    """
    respuesta = client.get(url, follow=True)
    destino = respuesta.redirect_chain[-1][0] if respuesta.redirect_chain else url
    return client.post(
        destino,
        {"new_password1": contrasena, "new_password2": confirmacion or contrasena},
        follow=True,
    )


# ---------------------------------------------------------------------------
# CO-114 · iniciarSesion
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("rol", "destino"),
    [
        (Usuario.CLIENTE, "core:tienda"),
        (Usuario.CAJERO, "core:mostrador"),
        (Usuario.ADMINISTRADOR, "core:panel"),
    ],
)
def test_CO114_credenciales_validas_establecen_sesion_con_el_nivel_del_rol(client, rol, destino):
    """Postcondición: se estableció una sesión con el nivel de permisos del rol."""
    usuario = UsuarioFactory(rol=rol)
    assert not hay_sesion(client)

    respuesta = client.post(URL_LOGIN, {"username": usuario.email, "password": PASSWORD_DE_PRUEBA})

    assert hay_sesion(client)
    assert client.session["_auth_user_id"] == str(usuario.pk)
    # La Salida del contrato: la redirección a la pantalla principal del rol.
    assert respuesta.url == reverse(destino)


def test_CO114_la_sesion_nace_con_expiracion_por_inactividad(client, cliente):
    """Postcondición: «un token con expiración por inactividad».

    La mitad que el contrato declara y acá **no** se afirma es «según ConfiguracionSistema»: el
    plazo vive hoy en `settings`, no en esa entidad. Ver `bitacora/12-autenticacion.md`, B-12-001.
    """
    client.post(URL_LOGIN, {"username": cliente.email, "password": PASSWORD_DE_PRUEBA})

    plazo = client.session.get_expiry_age()
    assert 0 < plazo <= settings.SESSION_COOKIE_AGE


def test_CO114_credenciales_validas_registran_el_inicio_en_auditoria(client, cliente):
    """Postcondición: se creó una entrada con acción «Inicio de sesión», actor y momento."""
    antes = timezone.now()
    assert not RegistroAuditoria.objects.filter(accion=RegistroAuditoria.INICIO_SESION).exists()

    client.post(URL_LOGIN, {"username": cliente.email, "password": PASSWORD_DE_PRUEBA})

    registro = RegistroAuditoria.objects.get(accion=RegistroAuditoria.INICIO_SESION)
    assert registro.actor == cliente
    assert registro.ocurrido_en >= antes


def test_CO114_credenciales_invalidas_crean_un_intento_fallido(client, cliente):
    """Postcondición (a): se creó if : IntentoFallido. Y (c): sus tres atributos."""
    assert IntentoFallido.objects.count() == 0
    antes = timezone.now()

    client.post(URL_LOGIN, {"username": cliente.email, "password": "la-que-no-es"})

    intento = IntentoFallido.objects.get()
    assert intento.email == cliente.email
    assert intento.ip is not None
    assert intento.ocurrido_en >= antes
    assert not hay_sesion(client)


def test_CO114_el_intento_fallido_guarda_el_correo_tal_como_se_escribio(client, cliente):
    """Postcondición (c): «if.correo tecleado quedó con el valor tal como se escribió»."""
    tecleado = f"  {cliente.email.upper()}  "

    client.post(URL_LOGIN, {"username": tecleado, "password": "la-que-no-es"})

    intento = IntentoFallido.objects.get()
    assert intento.email == tecleado.strip(), (
        "El contrato pide el valor tal como se escribió, para no distinguir "
        "una cuenta existente de una que no lo está."
    )


def test_CO114_se_registra_el_intento_aunque_la_cuenta_no_exista(client):
    """Notas del contrato: se registra «exista o no una cuenta con ese valor»."""
    inexistente = "nadie@longbox.test"
    assert not Usuario.objects.filter(email=inexistente).exists()

    client.post(URL_LOGIN, {"username": inexistente, "password": "cualquiera"})

    assert IntentoFallido.objects.get().email == inexistente


def test_CO114_el_quinto_intento_registra_el_bloqueo_en_auditoria(client, cliente):
    """Postcondición: «si los intentos dentro de la ventana alcanzaron cinco»."""
    accion = RegistroAuditoria.BLOQUEO_POR_INTENTOS
    for _ in range(settings.LOGIN_INTENTOS_MAXIMOS - 1):
        client.post(URL_LOGIN, {"username": cliente.email, "password": "la-que-no-es"})
    assert not RegistroAuditoria.objects.filter(accion=accion).exists()

    client.post(URL_LOGIN, {"username": cliente.email, "password": "la-que-no-es"})

    assert RegistroAuditoria.objects.filter(accion=accion).count() == 1


def test_CO114_bloqueado_no_entra_ni_con_la_contrasena_correcta(client, cliente):
    """Excepción E1: «se bloquea el acceso por el período parametrizado»."""
    for _ in range(settings.LOGIN_INTENTOS_MAXIMOS):
        client.post(URL_LOGIN, {"username": cliente.email, "password": "la-que-no-es"})

    client.post(URL_LOGIN, {"username": cliente.email, "password": PASSWORD_DE_PRUEBA})

    assert not hay_sesion(client), "El bloqueo tiene que ganarle a la credencial correcta."


def test_CO114_el_bloqueo_se_levanta_solo_al_salir_los_intentos_de_la_ventana(client, cliente):
    """Notas: «el bloqueo se levanta solo cuando los intentos salen de la ventana»."""
    ahora = timezone.now()
    with freeze_time(ahora):
        for _ in range(settings.LOGIN_INTENTOS_MAXIMOS):
            client.post(URL_LOGIN, {"username": cliente.email, "password": "la-que-no-es"})
        assert not hay_sesion(client)

    despues = ahora + timedelta(minutes=settings.LOGIN_BLOQUEO_MINUTOS + 1)
    with freeze_time(despues):
        client.post(URL_LOGIN, {"username": cliente.email, "password": PASSWORD_DE_PRUEBA})

    assert hay_sesion(client), "Ninguna limpieza hace falta: la ventana se corre sola."


def test_CO114_cuenta_inactiva_no_obtiene_sesion(client):
    """Excepción E2: cuenta en estado Inactivo, «sin otorgar sesión»."""
    inactivo = UsuarioFactory(estado=Usuario.INACTIVO)

    client.post(URL_LOGIN, {"username": inactivo.email, "password": PASSWORD_DE_PRUEBA})

    assert not hay_sesion(client)


def test_CO114_cuenta_inactiva_no_deja_rastro_de_inicio_en_auditoria(client):
    """Postcondición negativa: la rama de credenciales válidas no corrió."""
    inactivo = UsuarioFactory(estado=Usuario.INACTIVO)

    client.post(URL_LOGIN, {"username": inactivo.email, "password": PASSWORD_DE_PRUEBA})

    assert not RegistroAuditoria.objects.filter(accion=RegistroAuditoria.INICIO_SESION).exists()


# ---------------------------------------------------------------------------
# CO-115 · extenderSesion
# ---------------------------------------------------------------------------


def test_CO115_extender_renueva_el_plazo_de_inactividad(client, cliente):
    """Postcondición: «el plazo de expiración por inactividad del token quedó renovado»."""
    ahora = timezone.now()
    with freeze_time(ahora):
        client.force_login(cliente)
        vencimiento_anterior = client.session.get_expiry_date()

    with freeze_time(ahora + timedelta(minutes=10)):
        client.post(URL_RENOVAR)
        vencimiento_nuevo = client.session.get_expiry_date()

    assert vencimiento_nuevo > vencimiento_anterior
    assert hay_sesion(client)


def test_CO115_sobre_una_sesion_vencida_la_extension_no_procede(client, cliente):
    """Excepción: «si la sesión ya expiró, la extensión no procede»."""
    ahora = timezone.now()
    with freeze_time(ahora):
        client.force_login(cliente)

    vencida = ahora + timedelta(seconds=settings.SESSION_COOKIE_AGE + 60)
    with freeze_time(vencida):
        client.post(URL_RENOVAR)

    assert not hay_sesion(client)


# ---------------------------------------------------------------------------
# CO-116 · cerrarSesion
# ---------------------------------------------------------------------------


def test_CO116_cerrar_sesion_invalida_el_token_del_dispositivo_actual(client, cliente):
    """Postcondición: «el token de sesión del dispositivo actual quedó invalidado»."""
    client.force_login(cliente)
    assert hay_sesion(client)

    client.post(URL_LOGOUT)

    assert not hay_sesion(client)


def test_CO116_cerrar_sesion_no_afecta_las_sesiones_de_otros_dispositivos(cliente):
    """Postcondición negativa explícita: «las sesiones en otros dispositivos no fueron afectadas».

    Es la que distingue CO-116 de CO-118 y de CO-123, y la que ninguna prueba del camino feliz
    mira.
    """
    este_dispositivo, otro_dispositivo = Client(), Client()
    este_dispositivo.force_login(cliente)
    otro_dispositivo.force_login(cliente)
    assert hay_sesion(otro_dispositivo)

    este_dispositivo.post(URL_LOGOUT)

    assert not hay_sesion(este_dispositivo)
    assert hay_sesion(otro_dispositivo)
    assert otro_dispositivo.get(URL_PROTEGIDA).status_code == 200


def test_CO116_cerrar_sesion_registra_el_cierre_en_auditoria(client, cliente):
    """Postcondición: entrada con acción «Cierre de sesión», actor y timestamp."""
    client.force_login(cliente)
    accion = RegistroAuditoria.CIERRE_SESION
    assert not RegistroAuditoria.objects.filter(accion=accion).exists()

    client.post(URL_LOGOUT)

    registro = RegistroAuditoria.objects.get(accion=accion)
    assert registro.actor == cliente


# ---------------------------------------------------------------------------
# CO-117 · solicitarRecuperacionDeContrasena
# ---------------------------------------------------------------------------


def test_CO117_una_cuenta_activa_recibe_el_enlace_en_su_direccion(client, cliente):
    """Postcondición (a): «sólo si el correo corresponde a una cuenta Activa […] el enlace se
    envió a esa dirección»."""
    assert len(mail.outbox) == 0

    client.post(URL_PEDIR_ENLACE, {"email": cliente.email})

    assert len(mail.outbox) == 1
    assert mail.outbox[0].to == [cliente.email]


def test_CO117_un_correo_sin_cuenta_no_produce_ninguna_postcondicion(client):
    """Postcondición: «si el correo no corresponde a ninguna cuenta activa: ninguna
    postcondición»."""
    registros_antes = RegistroAuditoria.objects.count()

    client.post(URL_PEDIR_ENLACE, {"email": "nadie@longbox.test"})

    assert len(mail.outbox) == 0
    assert RegistroAuditoria.objects.count() == registros_antes


def test_CO117_la_respuesta_es_identica_exista_o_no_la_cuenta(client, cliente):
    """Notas: «la respuesta es idéntica exista o no una cuenta con el correo consultado»."""
    con_cuenta = client.post(URL_PEDIR_ENLACE, {"email": cliente.email}, follow=True)
    sin_cuenta = client.post(URL_PEDIR_ENLACE, {"email": "nadie@longbox.test"}, follow=True)

    assert con_cuenta.status_code == sin_cuenta.status_code
    assert (
        con_cuenta.content == sin_cuenta.content
    ), "Cualquier diferencia visible enumera cuentas, que es lo que el contrato evita."


def test_CO117_una_cuenta_inactiva_no_recibe_enlace(client):
    """Postcondición (a): la condición es «una cuenta Activa»."""
    UsuarioFactory(estado=Usuario.INACTIVO, email="dormida@longbox.test")

    client.post(URL_PEDIR_ENLACE, {"email": "dormida@longbox.test"})

    assert len(mail.outbox) == 0


# ---------------------------------------------------------------------------
# CO-118 · establecerNuevaContrasena
# ---------------------------------------------------------------------------


def test_CO118_la_credencial_pasa_del_hash_anterior_al_nuevo(client, cliente):
    """Postcondición (c): «u.credencial pasó del hash anterior al nuevo»."""
    hash_anterior = cliente.password
    assert cliente.check_password(PASSWORD_DE_PRUEBA)

    fijar_contrasena(client, url_de_token(cliente), NUEVA_CONTRASENA)

    cliente.refresh_from_db()
    assert cliente.password != hash_anterior
    assert cliente.check_password(NUEVA_CONTRASENA)


def test_CO118_la_contrasena_anterior_queda_invalidada(client, cliente):
    """Postcondición (c): «la contraseña anterior quedó invalidada»."""
    fijar_contrasena(client, url_de_token(cliente), NUEVA_CONTRASENA)

    cliente.refresh_from_db()
    assert not cliente.check_password(PASSWORD_DE_PRUEBA)


def test_CO118_el_token_queda_consumido_efecto_observable(client, cliente):
    """Postcondición (c): «tr.estado pasó de Vigente a Consumido».

    `TokenRecuperacion` no existe como tabla —es `<<planificado>>`—, así que no hay estado que
    leer. Lo observable es que el mismo enlace deja de servir para una segunda vez.
    """
    enlace = url_de_token(cliente)
    fijar_contrasena(client, enlace, NUEVA_CONTRASENA)

    otro = Client()
    fijar_contrasena(otro, enlace, "TerceraClave000")

    cliente.refresh_from_db()
    assert cliente.check_password(NUEVA_CONTRASENA), "El enlace no admite un segundo uso."
    assert not cliente.check_password("TerceraClave000")


def test_CO118_invalida_las_sesiones_en_todos_los_dispositivos(cliente):
    """Postcondición: «todas las sesiones activas del usuario, en cualquier dispositivo, quedaron
    invalidadas». Es la diferencia con CO-116."""
    uno, dos = Client(), Client()
    uno.force_login(cliente)
    dos.force_login(cliente)
    assert hay_sesion(uno) and hay_sesion(dos)

    fijar_contrasena(Client(), url_de_token(cliente), NUEVA_CONTRASENA)

    assert uno.get(URL_PROTEGIDA).status_code == 302
    assert dos.get(URL_PROTEGIDA).status_code == 302


def test_CO118_registra_el_cambio_de_contrasena_en_auditoria(client, cliente):
    """Postcondición: entrada con acción «Cambio de contraseña»."""
    accion = RegistroAuditoria.CAMBIO_CONTRASENA
    assert not RegistroAuditoria.objects.filter(accion=accion).exists()

    fijar_contrasena(client, url_de_token(cliente), NUEVA_CONTRASENA)

    assert RegistroAuditoria.objects.filter(accion=accion).count() == 1


def test_CO118_con_contrasenas_que_no_coinciden_el_enlace_no_se_consume(client, cliente):
    """Excepción E2: «el token no se consume y el usuario puede corregir sin necesidad de uno
    nuevo»."""
    enlace = url_de_token(cliente)
    hash_anterior = cliente.password

    fijar_contrasena(client, enlace, NUEVA_CONTRASENA, confirmacion="OtraDistinta111")

    cliente.refresh_from_db()
    assert cliente.password == hash_anterior, "El fallido no debe dejar nada escrito."

    # El mismo enlace tiene que seguir sirviendo: eso es «no se consume».
    fijar_contrasena(Client(), enlace, NUEVA_CONTRASENA)
    cliente.refresh_from_db()
    assert cliente.check_password(NUEVA_CONTRASENA)


def test_CO118_un_enlace_vencido_no_cambia_la_credencial(client, cliente):
    """Excepción E1: token vencido. Lo que se afirma es qué quedó en el sistema."""
    ahora = timezone.now()
    with freeze_time(ahora):
        enlace = url_de_token(cliente)
    hash_anterior = cliente.password

    vencido = ahora + timedelta(seconds=settings.VIGENCIA_ENLACE_RECUPERACION + 60)
    with freeze_time(vencido):
        fijar_contrasena(client, enlace, NUEVA_CONTRASENA)

    cliente.refresh_from_db()
    assert cliente.password == hash_anterior
    assert cliente.check_password(PASSWORD_DE_PRUEBA)


# ---------------------------------------------------------------------------
# CO-119 · activarCuenta
# ---------------------------------------------------------------------------


@pytest.fixture
def pendiente(db):
    """Una cuenta como la deja CO-120: Pendiente de activación y sin credencial utilizable."""
    usuario = UsuarioFactory(
        rol=Usuario.CAJERO,
        estado=Usuario.PENDIENTE_ACTIVACION,
        email="nuevo@longbox.test",
    )
    usuario.set_unusable_password()
    usuario.save()
    return usuario


def test_CO119_la_cuenta_pasa_de_pendiente_de_activacion_a_activo(client, pendiente):
    """Postcondición (c): «u.estado pasó de Pendiente de activación a Activo»."""
    assert pendiente.estado == Usuario.PENDIENTE_ACTIVACION

    fijar_contrasena(client, url_de_activacion(pendiente), NUEVA_CONTRASENA)

    pendiente.refresh_from_db()
    assert pendiente.estado == Usuario.ACTIVO


def test_CO119_la_credencial_pasa_de_nula_al_hash_de_la_elegida(client, pendiente):
    """Postcondición (c): «u.credencial pasó de nula al hash con sal única»."""
    assert not pendiente.has_usable_password()

    fijar_contrasena(client, url_de_activacion(pendiente), NUEVA_CONTRASENA)

    pendiente.refresh_from_db()
    assert pendiente.has_usable_password()
    assert pendiente.check_password(NUEVA_CONTRASENA)
    assert pendiente.password != NUEVA_CONTRASENA, "Nunca en texto plano (RNF-04)."


def test_CO119_el_enlace_no_admite_un_segundo_uso_efecto_observable(client, pendiente):
    """Postcondición (c): «EnlaceActivacion.estado pasó de Vigente a Consumido».

    `EnlaceActivacion` es `<<planificado>>` y no existe como tabla. Lo observable es que el mismo
    enlace no sirve una segunda vez para fijar otra contraseña.
    """
    enlace = url_de_activacion(pendiente)
    fijar_contrasena(client, enlace, NUEVA_CONTRASENA)

    fijar_contrasena(Client(), enlace, "SegundaClave222")

    pendiente.refresh_from_db()
    assert pendiente.check_password(NUEVA_CONTRASENA)
    assert not pendiente.check_password("SegundaClave222")


def test_CO119_registra_la_activacion_en_auditoria(client, pendiente):
    """Postcondición: entrada con acción «Activación de cuenta»."""
    accion = RegistroAuditoria.ACTIVACION_CUENTA
    assert not RegistroAuditoria.objects.filter(accion=accion).exists()

    fijar_contrasena(client, url_de_activacion(pendiente), NUEVA_CONTRASENA)

    assert RegistroAuditoria.objects.filter(accion=accion).count() == 1


def test_CO119_un_enlace_vencido_deja_la_cuenta_pendiente(client, pendiente):
    """Excepción E1: enlace vencido. Qué quedó en el sistema después del fallo."""
    ahora = timezone.now()
    with freeze_time(ahora):
        enlace = url_de_activacion(pendiente)

    vencido = ahora + timedelta(seconds=settings.VIGENCIA_ENLACE_ACTIVACION + 60)
    with freeze_time(vencido):
        fijar_contrasena(client, enlace, NUEVA_CONTRASENA)

    pendiente.refresh_from_db()
    assert pendiente.estado == Usuario.PENDIENTE_ACTIVACION
    assert not pendiente.has_usable_password()


def test_CO119_una_contrasena_rechazada_no_consume_el_enlace(client, pendiente):
    """Excepción E3: «el enlace no se consume por un intento fallido»."""
    enlace = url_de_activacion(pendiente)

    fijar_contrasena(client, enlace, "123", confirmacion="123")

    pendiente.refresh_from_db()
    assert pendiente.estado == Usuario.PENDIENTE_ACTIVACION
    assert not pendiente.has_usable_password()

    fijar_contrasena(Client(), enlace, NUEVA_CONTRASENA)
    pendiente.refresh_from_db()
    assert pendiente.estado == Usuario.ACTIVO


# ---------------------------------------------------------------------------
# CO-196 · abrirEnlaceDeActivacion  (operación de consulta)
# ---------------------------------------------------------------------------


def test_CO196_abrir_el_enlace_no_modifica_el_estado_del_sistema(client, pendiente):
    """Postcondición: «ninguna. La operación no modifica el estado del sistema».

    Suena trivial y no lo es: es lo que detecta que alguien le puso un efecto a una consulta.
    """
    estado_anterior = pendiente.estado
    hash_anterior = pendiente.password
    registros_antes = RegistroAuditoria.objects.count()

    respuesta = client.get(url_de_activacion(pendiente), follow=True)

    assert respuesta.status_code == 200
    pendiente.refresh_from_db()
    assert pendiente.estado == estado_anterior
    assert pendiente.password == hash_anterior
    assert RegistroAuditoria.objects.count() == registros_antes


def test_CO196_no_exige_sesion_iniciada(client, pendiente):
    """Precondición: «ninguna de sesión: el enlace es la credencial»."""
    assert not hay_sesion(client)

    respuesta = client.get(url_de_activacion(pendiente), follow=True)

    assert respuesta.status_code == 200
