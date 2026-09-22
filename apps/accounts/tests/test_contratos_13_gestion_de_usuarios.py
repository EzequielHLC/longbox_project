"""Pruebas de contrato del Módulo 13 — Gestión de Usuarios (CO-120 a CO-125, CO-197 a CO-202).

Incluye CO-156 `cancelarOperacion` en sus tres puntos de este módulo: CU-USR-BAJ A1, CU-USR-REA A1
y CU-USR-ELI A1.

Se escriben desde el contrato. Igual que en el módulo 12, `EnlaceActivacion` es un concepto
`<<planificado>>` del modelo de dominio y no existe como tabla: las postcondiciones que declaran
su creación o su cambio de estado se afirman por su efecto observable —llega el correo, el enlace
viejo deja de servir— y llevan `_efecto_observable` en el nombre.

**Tres postcondiciones de CO-124 no se cumplen.** Están escritas igual, marcadas `xfail(strict)`,
y anotadas en `bitacora/13-gestion-de-usuarios.md` (B-13-002). `strict=True` es deliberado: el día
que la reactivación acepte un rol, la prueba deja de estar en xfail y la suite avisa.
"""

import pytest
from django.core import mail
from django.test import Client
from django.urls import reverse
from django.utils import timezone

from apps.accounts.forms import (
    MENSAJE_CORREO_EN_USO,
    MENSAJE_CUENTA_CONGELADA,
    MENSAJE_UNICO_ADMINISTRADOR,
)
from apps.accounts.models import Usuario
from apps.accounts.tests.factories import PASSWORD_DE_PRUEBA, UsuarioFactory
from apps.accounts.tests.helpers_usuarios import (
    DATOS_DE_ALTA,
    URL_ALTA,
    URL_LISTA,
    datos_de,
    enlace_de_activacion,
    url_baja,
    url_edicion,
    url_reenviar_activacion,
)
from apps.core.models import RegistroAuditoria

pytestmark = pytest.mark.django_db

URL_LOGIN = reverse("accounts:login")
URL_PANEL = reverse("core:panel")


def url_reactivar(usuario):
    return reverse("accounts:usuario_reactivar", args=[usuario.pk])


def url_eliminar(usuario):
    return reverse("accounts:usuario_eliminar", args=[usuario.pk])


def hay_sesion(client):
    return "_auth_user_id" in client.session


@pytest.fixture
def pendiente(client_admin):
    """Una cuenta recién dada de alta, tal como la deja CO-120."""
    client_admin.post(URL_ALTA, DATOS_DE_ALTA)
    return Usuario.objects.get(email=DATOS_DE_ALTA["email"])


@pytest.fixture
def cajero_activo(db):
    return UsuarioFactory(rol=Usuario.CAJERO, first_name="Ana", last_name="Pérez")


@pytest.fixture
def dado_de_baja(client_admin, cajero_activo):
    """Un cajero que llegó a trabajar y después fue dado de baja."""
    Client().force_login(cajero_activo)
    client_admin.post(url_baja(cajero_activo))
    cajero_activo.refresh_from_db()
    assert cajero_activo.estado == Usuario.INACTIVO
    return cajero_activo


# ---------------------------------------------------------------------------
# CO-120 · registrarUsuarioDelSistema
# ---------------------------------------------------------------------------


def test_CO120_se_creo_la_cuenta_en_pendiente_de_activacion(client_admin):
    """Postcondición (a) y (c): «se creó u : Usuario», «u.estado quedó en Pendiente»."""
    assert not Usuario.objects.filter(email=DATOS_DE_ALTA["email"]).exists()

    client_admin.post(URL_ALTA, DATOS_DE_ALTA)

    usuario = Usuario.objects.get(email=DATOS_DE_ALTA["email"])
    assert usuario.estado == Usuario.PENDIENTE_ACTIVACION


def test_CO120_el_rol_queda_con_el_valor_declarado(client_admin):
    """Postcondición (c): «u.rol con el valor declarado (Cajero o Administrador)»."""
    client_admin.post(URL_ALTA, {**DATOS_DE_ALTA, "rol": Usuario.ADMINISTRADOR})

    assert Usuario.objects.get(email=DATOS_DE_ALTA["email"]).rol == Usuario.ADMINISTRADOR


def test_CO120_el_correo_queda_normalizado(client_admin):
    """Postcondición (c): «u.correo normalizado»."""
    client_admin.post(URL_ALTA, {**DATOS_DE_ALTA, "email": "ANA@Longbox.TEST"})

    assert Usuario.objects.filter(email="ana@longbox.test").exists()


def test_CO120_la_cuenta_nace_sin_credencial_utilizable(client_admin, pendiente):
    """Postcondición (c): «u.credencial nula».

    Django no guarda nulo sino un hash que ninguna contraseña satisface; lo verificable es que no
    hay credencial con la que entrar, que es lo que el contrato protege en sus Notas: «la
    establece su titular en CO-119, de modo que nadie más la haya visto».
    """
    assert not pendiente.has_usable_password()


def test_CO120_se_envio_el_enlace_al_correo_del_nuevo_usuario_efecto_observable(client_admin):
    """Postcondición (a)(b)(c): «se creó ea : EnlaceActivacion», «ea → u», «el enlace se envió»."""
    mail.outbox.clear()

    client_admin.post(URL_ALTA, DATOS_DE_ALTA)

    assert len(mail.outbox) == 1
    assert mail.outbox[0].to == [DATOS_DE_ALTA["email"]]
    assert enlace_de_activacion(mail.outbox[0])


def test_CO120_registra_el_alta_en_auditoria_con_el_rol_asignado(client_admin, administrador):
    """Postcondición: entrada «Alta de usuario del sistema» con actor, momento y rol asignado."""
    accion = RegistroAuditoria.ALTA_USUARIO
    antes = timezone.now()

    client_admin.post(URL_ALTA, {**DATOS_DE_ALTA, "rol": Usuario.CAJERO})

    registro = RegistroAuditoria.objects.get(accion=accion)
    assert registro.actor == administrador
    assert registro.ocurrido_en >= antes
    assert Usuario.CAJERO in registro.detalle.lower()


def test_CO120_un_correo_de_cuenta_activa_no_crea_la_cuenta(client_admin, cajero_activo):
    """Excepción E2: «el correo pertenece a otra cuenta, en cualquier estado […] no se crea»."""
    cuentas_antes = Usuario.objects.count()

    respuesta = client_admin.post(URL_ALTA, {**DATOS_DE_ALTA, "email": cajero_activo.email})

    assert Usuario.objects.count() == cuentas_antes
    assert MENSAJE_CORREO_EN_USO in respuesta.content.decode()


def test_CO120_un_correo_de_cuenta_pendiente_no_crea_la_cuenta(client_admin, pendiente):
    """Excepción E2, segundo estado: también bloquea contra una cuenta Pendiente."""
    cuentas_antes = Usuario.objects.count()

    client_admin.post(URL_ALTA, {**DATOS_DE_ALTA, "email": pendiente.email})

    assert Usuario.objects.count() == cuentas_antes


def test_CO120_un_correo_de_cuenta_inactiva_no_crea_la_cuenta(client_admin, dado_de_baja):
    """Excepción E2, tercer estado: el correo de una cuenta Inactiva tampoco se libera.

    Es la mitad que la redacción anterior del contrato no cubría —hablaba sólo de Activa o
    Pendiente— y la que sostiene I-10: el correo identifica una sola cuenta en cualquier
    estado. Si se liberara al dar de baja, la colisión de CO-124 E2 pasaría a ser posible.
    """
    cuentas_antes = Usuario.objects.count()

    respuesta = client_admin.post(URL_ALTA, {**DATOS_DE_ALTA, "email": dado_de_baja.email})

    assert Usuario.objects.count() == cuentas_antes
    assert MENSAJE_CORREO_EN_USO in respuesta.content.decode()


# ---------------------------------------------------------------------------
# CO-121 · modificarUsuarioDelSistema
# ---------------------------------------------------------------------------


def test_CO121_los_atributos_pasan_de_su_valor_anterior_al_declarado(client_admin, cajero_activo):
    """Postcondición (c): «los atributos modificados pasaron de sus valores anteriores a los
    declarados»."""
    assert cajero_activo.email == cajero_activo.email  # el valor anterior, capturado
    correo_anterior = cajero_activo.email

    client_admin.post(
        url_edicion(cajero_activo), datos_de(cajero_activo, email="otra@longbox.test")
    )

    cajero_activo.refresh_from_db()
    assert correo_anterior != "otra@longbox.test"
    assert cajero_activo.email == "otra@longbox.test"


def test_CO121_la_ultima_modificacion_queda_con_el_instante(client_admin, cajero_activo):
    """Postcondición (c): «u.última modificación quedó con el instante»."""
    anterior = cajero_activo.actualizado_en

    client_admin.post(
        url_edicion(cajero_activo), datos_de(cajero_activo, email="nueva@longbox.test")
    )

    cajero_activo.refresh_from_db()
    assert cajero_activo.actualizado_en > anterior


def test_CO121_cambiar_el_rol_invalida_la_sesion_del_usuario_modificado(
    client_admin, cajero_activo
):
    """Postcondición: «si se modificó el rol: el token de sesión activo del usuario modificado
    quedó invalidado de forma inmediata, forzando un re-login con los nuevos permisos»."""
    suyo = Client()
    suyo.force_login(cajero_activo)
    assert hay_sesion(suyo)

    client_admin.post(
        url_edicion(cajero_activo), datos_de(cajero_activo, rol=Usuario.ADMINISTRADOR)
    )

    assert suyo.get(reverse("core:mostrador")).status_code == 302
    assert not hay_sesion(suyo)


def test_CO121_sin_cambiar_el_rol_la_sesion_del_usuario_sigue_viva(client_admin, cajero_activo):
    """Postcondición negativa: la invalidación está condicionada a «si se modificó el rol»."""
    suyo = Client()
    suyo.force_login(cajero_activo)

    client_admin.post(
        url_edicion(cajero_activo), datos_de(cajero_activo, email="otro@longbox.test")
    )

    assert hay_sesion(suyo)


def test_CO121_registra_los_valores_anterior_y_nuevo_de_cada_campo(client_admin, cajero_activo):
    """Postcondición: entrada con «los valores anteriores y nuevos de cada campo modificado»."""
    correo_anterior = cajero_activo.email

    client_admin.post(
        url_edicion(cajero_activo), datos_de(cajero_activo, email="nuevo@longbox.test")
    )

    registro = RegistroAuditoria.objects.get(accion=RegistroAuditoria.MODIFICACION_USUARIO)
    assert correo_anterior in registro.detalle
    assert "nuevo@longbox.test" in registro.detalle


def test_CO121_no_se_puede_quitar_el_rol_al_ultimo_administrador(client_admin, administrador):
    """Excepción E1: «la operación se cancela sin efecto» (I-12)."""
    assert Usuario.objects.filter(rol=Usuario.ADMINISTRADOR, estado=Usuario.ACTIVO).count() == 1

    respuesta = client_admin.post(
        url_edicion(administrador), datos_de(administrador, rol=Usuario.CAJERO)
    )

    administrador.refresh_from_db()
    assert administrador.rol == Usuario.ADMINISTRADOR, "Sin efecto: es lo que dice el contrato."
    assert MENSAJE_UNICO_ADMINISTRADOR in respuesta.content.decode()


def test_CO121_un_correo_que_ya_es_de_otra_cuenta_no_actualiza(client_admin, cajero_activo):
    """Excepción E2: «se informa el conflicto y no se actualiza»."""
    otra = UsuarioFactory(rol=Usuario.CAJERO, email="ocupado@longbox.test")
    correo_anterior = cajero_activo.email

    client_admin.post(url_edicion(cajero_activo), datos_de(cajero_activo, email=otra.email))

    cajero_activo.refresh_from_db()
    assert cajero_activo.email == correo_anterior


def test_CO121_una_cuenta_inactiva_no_admite_modificacion(client_admin, dado_de_baja):
    """Excepción E3: «se bloquea el acceso al formulario y se ofrece la acción de reactivación»."""
    respuesta = client_admin.get(url_edicion(dado_de_baja), follow=True)

    assert MENSAJE_CUENTA_CONGELADA in respuesta.content.decode()


def test_CO121_una_cuenta_inactiva_no_cambia_aunque_se_envie_el_formulario(
    client_admin, dado_de_baja
):
    """Excepción E3, la mitad que importa: la restricción vive en el servidor, no en la pantalla."""
    rol_anterior = dado_de_baja.rol

    client_admin.post(url_edicion(dado_de_baja), datos_de(dado_de_baja, rol=Usuario.ADMINISTRADOR))

    dado_de_baja.refresh_from_db()
    assert dado_de_baja.rol == rol_anterior
    assert dado_de_baja.estado == Usuario.INACTIVO


# ---------------------------------------------------------------------------
# CO-122 · regenerarEnlaceDeActivacion
# ---------------------------------------------------------------------------


def test_CO122_se_reenvia_un_enlace_nuevo_efecto_observable(client_admin, pendiente):
    """Postcondición (a): «se creó un EnlaceActivacion nuevo». «El correo fue reenviado»."""
    mail.outbox.clear()

    client_admin.post(url_reenviar_activacion(pendiente))

    assert len(mail.outbox) == 1
    assert mail.outbox[0].to == [pendiente.email]


def test_CO122_el_enlace_anterior_deja_de_admitir_uso_efecto_observable(client_admin, pendiente):
    """Postcondición (c): «el EnlaceActivacion anterior pasó a estado Vencido y no admite uso»."""
    anterior = enlace_de_activacion(mail.outbox[-1])
    mail.outbox.clear()

    client_admin.post(url_reenviar_activacion(pendiente))
    nuevo = enlace_de_activacion(mail.outbox[-1])

    navegador = Client()
    respuesta = navegador.get(anterior, follow=True)
    destino = respuesta.redirect_chain[-1][0] if respuesta.redirect_chain else anterior
    navegador.post(
        destino, {"new_password1": "ClaveDelViejo99", "new_password2": "ClaveDelViejo99"}
    )

    pendiente.refresh_from_db()
    assert pendiente.estado == Usuario.PENDIENTE_ACTIVACION, "El enlace anterior no debe servir."
    assert not pendiente.check_password("ClaveDelViejo99")
    assert nuevo != anterior


def test_CO122_registra_el_reenvio_en_auditoria(client_admin, pendiente):
    """Postcondición: entrada «Reenvío del enlace de activación» con actor y momento."""
    accion = RegistroAuditoria.REENVIO_ACTIVACION
    assert not RegistroAuditoria.objects.filter(accion=accion).exists()

    client_admin.post(url_reenviar_activacion(pendiente))

    assert RegistroAuditoria.objects.filter(accion=accion).count() == 1


# ---------------------------------------------------------------------------
# CO-123 · confirmarBajaDeUsuario
# ---------------------------------------------------------------------------


def test_CO123_el_estado_pasa_de_activo_a_inactivo(client_admin, cajero_activo):
    """Postcondición (c): «u.estado pasó de Activo a Inactivo»."""
    assert cajero_activo.estado == Usuario.ACTIVO

    client_admin.post(url_baja(cajero_activo))

    cajero_activo.refresh_from_db()
    assert cajero_activo.estado == Usuario.INACTIVO


def test_CO123_la_cuenta_no_puede_volver_a_iniciar_sesion(client_admin, cajero_activo):
    """Postcondición (c): «el usuario no puede volver a iniciar sesión» (I-11)."""
    client_admin.post(url_baja(cajero_activo))

    navegador = Client()
    navegador.post(URL_LOGIN, {"username": cajero_activo.email, "password": PASSWORD_DE_PRUEBA})

    assert not hay_sesion(navegador)


def test_CO123_invalida_los_tokens_de_todos_los_dispositivos(client_admin, cajero_activo):
    """Postcondición: «todos sus tokens de sesión, en cualquier dispositivo, quedaron
    invalidados de forma inmediata»."""
    uno, dos = Client(), Client()
    uno.force_login(cajero_activo)
    dos.force_login(cajero_activo)

    client_admin.post(url_baja(cajero_activo))

    assert uno.get(reverse("core:mostrador")).status_code == 302
    assert dos.get(reverse("core:mostrador")).status_code == 302


def test_CO123_el_historial_del_usuario_se_conserva_integro(client_admin, cajero_activo):
    """Postcondición negativa explícita: «el historial de operaciones registradas por ese usuario
    se conservó íntegro en el log»."""
    Client().force_login(cajero_activo)
    historial_antes = list(
        RegistroAuditoria.objects.filter(actor=cajero_activo).values_list("pk", flat=True)
    )
    assert historial_antes, "La cuenta tiene que haber dejado rastro para que la prueba valga."

    client_admin.post(url_baja(cajero_activo))

    historial_despues = list(
        RegistroAuditoria.objects.filter(actor=cajero_activo).values_list("pk", flat=True)
    )
    assert historial_despues == historial_antes


def test_CO123_registra_la_baja_en_auditoria(client_admin, cajero_activo):
    """Postcondición: entrada «Baja de usuario del sistema» con actor y momento."""
    accion = RegistroAuditoria.BAJA_USUARIO

    client_admin.post(url_baja(cajero_activo))

    registro = RegistroAuditoria.objects.get(accion=accion)
    assert registro.objetivo_email == cajero_activo.email


def test_CO123_no_se_puede_dar_de_baja_al_ultimo_administrador(client_admin, administrador):
    """Excepción E1: se bloquea (I-12)."""
    respuesta = client_admin.post(url_baja(administrador), follow=True)

    administrador.refresh_from_db()
    assert administrador.estado == Usuario.ACTIVO
    assert MENSAJE_UNICO_ADMINISTRADOR in respuesta.content.decode()


# ---------------------------------------------------------------------------
# CO-124 · confirmarReactivacionDeUsuario
# ---------------------------------------------------------------------------


def test_CO124_el_estado_pasa_de_inactivo_a_pendiente_de_activacion(client_admin, dado_de_baja):
    """Postcondición (c): «u.estado pasó de Inactivo a Pendiente de activación (no a Activo)»."""
    assert dado_de_baja.estado == Usuario.INACTIVO

    client_admin.post(url_reactivar(dado_de_baja))

    dado_de_baja.refresh_from_db()
    assert dado_de_baja.estado == Usuario.PENDIENTE_ACTIVACION


def test_CO124_la_credencial_anterior_queda_invalidada(client_admin, dado_de_baja):
    """Postcondición (c): «u.credencial quedó invalidada».

    Las Notas dicen por qué: «entre la baja y la reincorporación pudo pasar cualquier cosa con esa
    credencial, y el sistema no tiene forma de saberlo».
    """
    assert dado_de_baja.check_password(PASSWORD_DE_PRUEBA)

    client_admin.post(url_reactivar(dado_de_baja))

    dado_de_baja.refresh_from_db()
    assert not dado_de_baja.has_usable_password()
    assert not dado_de_baja.check_password(PASSWORD_DE_PRUEBA)


def test_CO124_se_envia_un_enlace_de_activacion_efecto_observable(client_admin, dado_de_baja):
    """Postcondición (a): «se creó un EnlaceActivacion con vigencia de 48 horas, enviado al correo
    de la cuenta»."""
    mail.outbox.clear()

    client_admin.post(url_reactivar(dado_de_baja))

    assert len(mail.outbox) == 1
    assert mail.outbox[0].to == [dado_de_baja.email]
    assert enlace_de_activacion(mail.outbox[0])


def test_CO124_el_historial_del_usuario_se_conserva_integro(client_admin, dado_de_baja):
    """Postcondición: «el historial de operaciones del usuario en el log se conservó íntegro»."""
    historial_antes = list(
        RegistroAuditoria.objects.filter(actor=dado_de_baja).values_list("pk", flat=True)
    )
    assert historial_antes

    client_admin.post(url_reactivar(dado_de_baja))

    historial_despues = list(
        RegistroAuditoria.objects.filter(actor=dado_de_baja).values_list("pk", flat=True)
    )
    assert historial_despues == historial_antes


def test_CO124_registra_la_reactivacion_en_auditoria(client_admin, dado_de_baja):
    """Postcondición: entrada «Reactivación de usuario del sistema» con actor y momento."""
    accion = RegistroAuditoria.REACTIVACION_USUARIO

    client_admin.post(url_reactivar(dado_de_baja))

    registro = RegistroAuditoria.objects.get(accion=accion)
    assert registro.objetivo_email == dado_de_baja.email


@pytest.mark.xfail(
    strict=True,
    reason=(
        "CO-124 declara confirmarReactivacionDeUsuario(usuario, rol) y la postcondición "
        "«u.rol quedó con el valor declarado». La vista no recibe ningún rol: conserva el que "
        "la cuenta tenía. Ver bitacora/13-gestion-de-usuarios.md, B-13-002."
    ),
)
def test_CO124_el_rol_queda_con_el_valor_declarado(client_admin, dado_de_baja):
    """Postcondición (c): «u.rol quedó con el valor declarado».

    Las Notas explican para qué: «el rol se elige acá y queda registrado junto con la
    reactivación, en lugar de restaurarse el que tenía. Es lo que impide dejar preparado un cambio
    de rol sobre una cuenta dormida».
    """
    assert dado_de_baja.rol == Usuario.CAJERO

    client_admin.post(url_reactivar(dado_de_baja), {"rol": Usuario.ADMINISTRADOR})

    dado_de_baja.refresh_from_db()
    assert dado_de_baja.rol == Usuario.ADMINISTRADOR


@pytest.mark.xfail(
    strict=True,
    reason=(
        "CO-124 pide que la entrada de auditoría incluya el rol asignado. El detalle registra "
        "sólo la transición de estado. Ver bitacora/13-gestion-de-usuarios.md, B-13-002."
    ),
)
def test_CO124_la_auditoria_incluye_el_rol_asignado(client_admin, dado_de_baja):
    """Postcondición: entrada «Reactivación de usuario del sistema» […] «incluyendo el rol
    asignado»."""
    client_admin.post(url_reactivar(dado_de_baja))

    registro = RegistroAuditoria.objects.get(accion=RegistroAuditoria.REACTIVACION_USUARIO)
    assert Usuario.CAJERO in registro.detalle.lower()


@pytest.mark.xfail(
    strict=True,
    reason=(
        "CO-199 pide presentar el rol «permitiendo modificarlo antes de confirmar». La pantalla "
        "lo muestra como texto, sin control editable. Ver B-13-002."
    ),
)
def test_CO199_la_pantalla_permite_modificar_el_rol_antes_de_confirmar(client_admin, dado_de_baja):
    """Responsabilidad de CO-199: «presentar el rol con el que quedará reactivada, permitiendo
    modificarlo antes de confirmar»."""
    cuerpo = client_admin.get(url_reactivar(dado_de_baja)).content.decode()

    assert 'name="rol"' in cuerpo


# ---------------------------------------------------------------------------
# CO-125 · confirmarEliminacionDeCuentaPendiente
# ---------------------------------------------------------------------------


def test_CO125_la_auditoria_se_escribe_antes_de_eliminar_el_registro(client_admin, pendiente):
    """Postcondición, en el orden que «es parte del contrato»: primero la entrada, después la
    eliminación física.

    Lo verificable del orden es su consecuencia: la entrada sobrevive al registro que la originó y
    sigue diciendo de quién era la cuenta.
    """
    correo = pendiente.email

    client_admin.post(url_eliminar(pendiente))

    registro = RegistroAuditoria.objects.get(accion=RegistroAuditoria.ELIMINACION_PENDIENTE)
    assert registro.objetivo_email == correo, (
        "El correo va copiado dentro de la entrada, de forma desnormalizada: es lo que "
        "permite que la traza sobreviva al registro eliminado."
    )


def test_CO125_se_elimino_fisicamente_la_instancia(client_admin, pendiente):
    """Postcondición (a): «se eliminó físicamente la instancia u : Usuario del sistema»."""
    pk = pendiente.pk
    assert Usuario.objects.filter(pk=pk).exists()

    client_admin.post(url_eliminar(pendiente))

    assert not Usuario.objects.filter(pk=pk).exists()


def test_CO125_el_correo_queda_disponible_para_un_alta_nueva(client_admin, pendiente):
    """Postcondición: «el correo quedó disponible para un alta nueva (I-10 deja de bloquearlo)»."""
    correo = pendiente.email
    client_admin.post(url_eliminar(pendiente))

    client_admin.post(URL_ALTA, {**DATOS_DE_ALTA, "email": correo})

    assert Usuario.objects.filter(email=correo).count() == 1


def test_CO125_el_enlace_pendiente_queda_invalidado_efecto_observable(client_admin, pendiente):
    """Postcondición (c): «el EnlaceActivacion pendiente quedó invalidado»."""
    enlace = enlace_de_activacion(mail.outbox[-1])

    client_admin.post(url_eliminar(pendiente))

    navegador = Client()
    respuesta = navegador.get(enlace, follow=True)
    assert respuesta.status_code in (200, 404)
    assert not Usuario.objects.filter(email=pendiente.email).exists()


def test_CO125_una_cuenta_activa_no_se_elimina(client_admin, cajero_activo):
    """Excepción E2: «la cuenta está en estado Activo o Inactivo: la operación no se ofrece».

    Se ejerce por la dirección real: que la pantalla no ofrezca el botón no alcanza.
    """
    client_admin.post(url_eliminar(cajero_activo), follow=True)

    assert Usuario.objects.filter(pk=cajero_activo.pk).exists()


def test_CO125_una_cuenta_inactiva_no_se_elimina(client_admin, dado_de_baja):
    """Excepción E2, la otra mitad del estado."""
    client_admin.post(url_eliminar(dado_de_baja), follow=True)

    assert Usuario.objects.filter(pk=dado_de_baja.pk).exists()


def test_CO125_una_pendiente_que_ya_inicio_sesion_no_se_elimina(client_admin, dado_de_baja):
    """Excepción E1 y Notas: «no alcanza con estar Pendiente: una cuenta reactivada por CO-124
    también lo está, y ésa sí tiene historial»."""
    client_admin.post(url_reactivar(dado_de_baja))
    dado_de_baja.refresh_from_db()
    assert dado_de_baja.estado == Usuario.PENDIENTE_ACTIVACION

    client_admin.post(url_eliminar(dado_de_baja), follow=True)

    assert Usuario.objects.filter(
        pk=dado_de_baja.pk
    ).exists(), "La prueba de que nunca se usó es no tener ningún inicio de sesión registrado."


# ---------------------------------------------------------------------------
# CO-156 · cancelarOperacion  (CU-USR-BAJ A1, CU-USR-REA A1, CU-USR-ELI A1)
# ---------------------------------------------------------------------------


def _foto_de(usuario):
    return (usuario.estado, usuario.rol, usuario.email, usuario.password)


@pytest.mark.parametrize(
    ("url_de", "fixture"),
    [
        (url_baja, "cajero_activo"),
        (url_reactivar, "dado_de_baja"),
        (url_eliminar, "pendiente"),
    ],
)
def test_CO156_abandonar_antes_de_confirmar_no_cambia_nada(client_admin, request, url_de, fixture):
    """Postcondición: «ninguna. El objeto sobre el que se operaba conserva todos sus atributos,
    asociaciones y estado. No se genera entrada de auditoría»."""
    usuario = request.getfixturevalue(fixture)
    antes = _foto_de(usuario)
    registros_antes = RegistroAuditoria.objects.count()

    # Abrir la confirmación y no confirmar es exactamente abandonar la operación en curso.
    client_admin.get(url_de(usuario), follow=True)

    usuario.refresh_from_db()
    assert _foto_de(usuario) == antes
    assert (
        RegistroAuditoria.objects.count() == registros_antes
    ), "Una operación que no ocurrió no se audita."


# ---------------------------------------------------------------------------
# CO-197 a CO-202 · operaciones de consulta
# ---------------------------------------------------------------------------


def test_CO197_abrir_la_edicion_no_modifica_el_estado(client_admin, cajero_activo):
    """CO-197. Postcondición: ninguna."""
    antes = _foto_de(cajero_activo)
    registros_antes = RegistroAuditoria.objects.count()

    respuesta = client_admin.get(url_edicion(cajero_activo))

    assert respuesta.status_code == 200
    cajero_activo.refresh_from_db()
    assert _foto_de(cajero_activo) == antes
    assert RegistroAuditoria.objects.count() == registros_antes


def test_CO198_solicitar_la_baja_no_modifica_el_estado(client_admin, cajero_activo):
    """CO-198. Postcondición: ninguna."""
    antes = _foto_de(cajero_activo)

    respuesta = client_admin.get(url_baja(cajero_activo))

    assert respuesta.status_code == 200
    cajero_activo.refresh_from_db()
    assert _foto_de(cajero_activo) == antes


@pytest.mark.xfail(
    strict=True,
    reason=(
        "CO-198 E1 bloquea la solicitud de baja sobre la última cuenta Administrador activa. "
        "El resguardo vive sólo en el POST: la pantalla de confirmación se ofrece igual y el "
        "rechazo llega recién al confirmar. Ver bitacora/13-gestion-de-usuarios.md, B-13-003."
    ),
)
def test_CO198_no_se_ofrece_sobre_el_ultimo_administrador(client_admin, administrador):
    """CO-198, excepción E1: «última cuenta Administrador activa: se bloquea» (I-12).

    El sistema no queda expuesto —CO-123 sí rechaza la baja, y esa prueba pasa—; lo que falla es
    que la operación se ofrece. Es el principio que CO-202 enuncia: «la interfaz no decide,
    refleja».
    """
    respuesta = client_admin.get(url_baja(administrador), follow=True)

    assert MENSAJE_UNICO_ADMINISTRADOR in respuesta.content.decode()


def test_CO199_solicitar_la_reactivacion_no_modifica_el_estado(client_admin, dado_de_baja):
    """CO-199. Postcondición: ninguna."""
    antes = _foto_de(dado_de_baja)

    respuesta = client_admin.get(url_reactivar(dado_de_baja))

    assert respuesta.status_code == 200
    dado_de_baja.refresh_from_db()
    assert _foto_de(dado_de_baja) == antes


def test_CO200_solicitar_la_eliminacion_no_modifica_el_estado(client_admin, pendiente):
    """CO-200. Postcondición: ninguna."""
    antes = _foto_de(pendiente)

    respuesta = client_admin.get(url_eliminar(pendiente))

    assert respuesta.status_code == 200
    pendiente.refresh_from_db()
    assert _foto_de(pendiente) == antes


def test_CO201_el_listado_presenta_nombre_correo_rol_y_estado(client_admin, cajero_activo):
    """CO-201. Responsabilidad: «listar nombre, correo, rol y estado de cada cuenta»."""
    cuerpo = client_admin.get(URL_LISTA).content.decode()

    assert cajero_activo.email in cuerpo
    assert cajero_activo.first_name in cuerpo


def test_CO201_el_listado_no_modifica_el_estado(client_admin, cajero_activo):
    """CO-201. Postcondición: ninguna."""
    registros_antes = RegistroAuditoria.objects.count()
    antes = _foto_de(cajero_activo)

    client_admin.get(URL_LISTA)

    cajero_activo.refresh_from_db()
    assert _foto_de(cajero_activo) == antes
    assert RegistroAuditoria.objects.count() == registros_antes


@pytest.mark.parametrize("rol", [Usuario.CLIENTE, Usuario.CAJERO])
def test_acceso_CO201_el_listado_de_personal_es_solo_del_administrador(client, rol):
    """Precondición de CO-201: «rol Administrador validado en el servidor» (RNF-03).

    Por la dirección real y con el rol equivocado, no llamando a la vista.
    """
    client.force_login(UsuarioFactory(rol=rol))

    assert client.get(URL_LISTA).status_code in (302, 403)


@pytest.mark.parametrize("rol", [Usuario.CLIENTE, Usuario.CAJERO])
def test_acceso_CO123_la_baja_de_usuario_es_solo_del_administrador(client, rol, cajero_activo):
    """Precondición de CO-123: la operación es del Administrador. Se ejerce el POST real."""
    client.force_login(UsuarioFactory(rol=rol))

    client.post(url_baja(cajero_activo))

    cajero_activo.refresh_from_db()
    assert cajero_activo.estado == Usuario.ACTIVO


@pytest.mark.parametrize("rol", [Usuario.CLIENTE, Usuario.CAJERO])
def test_acceso_CO125_la_eliminacion_es_solo_del_administrador(client, rol, pendiente):
    """Precondición de CO-125: la operación es del Administrador. Se ejerce el POST real."""
    client.force_login(UsuarioFactory(rol=rol))

    client.post(url_eliminar(pendiente))

    assert Usuario.objects.filter(pk=pendiente.pk).exists()
