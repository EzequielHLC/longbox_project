"""Pruebas de contrato de «Mi cuenta» (plan 11, segunda parte).

`CO-192` consultarPanelDeCuenta, `CO-193` consultarDetalleDePedidoPropio,
`CO-108` actualizarDatosPersonales, `CO-109` solicitarCambioDeCorreo, `CO-110`
confirmarCambioDeCorreo y `CO-111` cambiarContrasena. Por la dirección real.

Postcondiciones negativas: las consultas no cambian nada, `CO-109` no cambia el
correo, una contraseña equivocada no cambia nada.
"""

import re
from datetime import timedelta

import pytest
from django.core import mail
from django.test import Client
from django.urls import reverse
from django.utils import timezone

from apps.accounts.models import TokenCambioCorreo, Usuario
from apps.accounts.tests.factories import PASSWORD_DE_PRUEBA, UsuarioFactory
from apps.core.models import RegistroAuditoria
from apps.pedidos.models import Pedido
from apps.pedidos.tests.util import crear_pedido

pytestmark = pytest.mark.django_db

URL_PANEL = reverse("cuenta:panel")
URL_PEDIDOS = reverse("cuenta:pedidos")
URL_HISTORIAL = reverse("cuenta:historial")
URL_DATOS = reverse("cuenta:datos")
URL_CORREO = reverse("cuenta:correo")
URL_CONTRASENA = reverse("cuenta:contrasena")

DATOS = {
    "nombre_completo": "Ana Lectora",
    "telefono_pais": "+54",
    "telefono_area": "351",
    "telefono_numero": "4123456",
    "direccion": "Av. Colón 1234",
    "direccion_linea2": "",
    "depto": "3 B",
    "provincia": "Córdoba",
    "localidad": "Córdoba",
    "codigo_postal": "X5000ABC",
    "comentarios_envio": "Timbre 3",
}


@pytest.fixture
def titular(db):
    return UsuarioFactory(rol=Usuario.CLIENTE, email="ana@correo.test", first_name="Ana")


@pytest.fixture
def navegador(client, titular):
    client.force_login(titular)
    return client


def enlace_del_correo(mensaje):
    return re.search(r"https?://\S+/cuenta/correo/confirmar/\S+/", mensaje.body).group(0)


def ruta(enlace):
    return enlace.split("testserver", 1)[1]


# ===========================================================================
# CO-192 · consultarPanelDeCuenta
# ===========================================================================


def test_CO192_muestra_los_pedidos_activos_del_cliente(navegador, titular):
    activo = crear_pedido(titular)
    crear_pedido(titular, estado=Pedido.DESPACHADO)
    crear_pedido(UsuarioFactory(rol=Usuario.CLIENTE))

    respuesta = navegador.get(URL_PANEL)

    assert [p.pk for p in respuesta.context["pedidos"]] == [activo.pk]


def test_CO192_el_historial_muestra_los_despachados(navegador, titular):
    crear_pedido(titular)
    despachado = crear_pedido(titular, estado=Pedido.DESPACHADO)

    respuesta = navegador.get(URL_PEDIDOS)

    assert [p.pk for p in respuesta.context["historial"]] == [despachado.pk]


def test_CO192_la_direccion_del_historial_lleva_a_su_grupo(navegador):
    assert navegador.get(URL_HISTORIAL).url == URL_PEDIDOS + "#historial"


def test_CO192_E1_sin_pedidos_activos_informa_y_las_demas_secciones_siguen(navegador):
    contenido = navegador.get(URL_PANEL).content.decode()

    assert "No tenés pedidos en curso." in contenido
    for url in (URL_PEDIDOS, reverse("cuenta:puntos"), URL_DATOS):
        assert url in contenido


def test_CO192_la_seccion_stock_en_local_se_muestra(navegador):
    """Plan 18: la sección oculta por B-11-003 ya existe."""
    assert reverse("cuenta:stock") in navegador.get(URL_PANEL).content.decode()


def test_CO192_no_modifica_el_estado_del_sistema(navegador, titular):
    pedido = crear_pedido(titular)
    registros = RegistroAuditoria.objects.count()

    navegador.get(URL_PANEL)
    navegador.get(URL_HISTORIAL)

    pedido.refresh_from_db()
    assert pedido.estado == Pedido.PENDIENTE_ARMADO
    assert RegistroAuditoria.objects.count() == registros


# ===========================================================================
# CO-193 · consultarDetalleDePedidoPropio
# ===========================================================================


def test_CO193_muestra_items_precios_estados_alcanzados_y_sus_fechas(navegador, titular):
    pedido = crear_pedido(titular, lineas=(("10000", 2), ("5000", 1, 500)))
    pedido.transiciones.create(estado_anterior=Pedido.PENDIENTE_ARMADO, estado_nuevo=Pedido.ARMADO)

    respuesta = navegador.get(reverse("cuenta:pedido", args=[pedido.numero]))

    contenido = respuesta.content.decode()
    assert len(respuesta.context["lineas"]) == 2
    assert [t.estado_nuevo for t in respuesta.context["transiciones"]] == [
        Pedido.PENDIENTE_ARMADO,
        Pedido.ARMADO,
    ]
    assert "500 pts" in contenido
    assert respuesta.context["cobrado"] == 21500


def test_CO193_el_pedido_de_otro_cliente_responde_404(navegador):
    ajeno = crear_pedido(UsuarioFactory(rol=Usuario.CLIENTE))

    assert navegador.get(reverse("cuenta:pedido", args=[ajeno.numero])).status_code == 404


def test_CO193_un_pedido_activo_se_actualiza_solo_y_uno_despachado_no(navegador, titular):
    activo = crear_pedido(titular)
    despachado = crear_pedido(titular, estado=Pedido.DESPACHADO)

    con_refresco = navegador.get(reverse("cuenta:pedido", args=[activo.numero]))
    sin_refresco = navegador.get(reverse("cuenta:pedido", args=[despachado.numero]))

    assert 'http-equiv="refresh" content="30"' in con_refresco.content.decode()
    assert 'http-equiv="refresh"' not in sin_refresco.content.decode()


def test_CO193_no_modifica_el_estado_del_sistema(navegador, titular):
    pedido = crear_pedido(titular)

    navegador.get(reverse("cuenta:pedido", args=[pedido.numero]))

    assert pedido.transiciones.count() == 1


# ===========================================================================
# CO-108 · actualizarDatosPersonales
# ===========================================================================


def test_CO108_c_los_atributos_modificados_pasan_a_los_declarados(navegador, titular):
    assert (titular.direccion, titular.telefono_area) == ("", "")
    antes = titular.actualizado_en

    navegador.post(URL_DATOS, DATOS)

    titular.refresh_from_db()
    assert (titular.first_name, titular.last_name) == ("Ana", "Lectora")
    assert titular.direccion == "Av. Colón 1234"
    assert titular.codigo_postal == "X5000ABC"
    assert titular.telefono_area == "351"
    assert titular.actualizado_en > antes


def test_CO108_queda_en_la_auditoria_con_el_actor(navegador, titular):
    navegador.post(URL_DATOS, DATOS)

    registro = RegistroAuditoria.objects.get(accion=RegistroAuditoria.MODIFICACION_DATOS_CLIENTE)
    assert registro.actor == titular
    assert "«Av. Colón 1234»" in registro.detalle


def test_CO108_el_correo_no_se_cambia_desde_aca(navegador, titular):
    navegador.post(URL_DATOS, {**DATOS, "email": "otro@correo.test"})

    titular.refresh_from_db()
    assert titular.email == "ana@correo.test"


def test_CO108_una_direccion_incoherente_no_cambia_nada(navegador, titular):
    respuesta = navegador.post(URL_DATOS, {**DATOS, "provincia": "Misiones"})

    titular.refresh_from_db()
    assert respuesta.context["form"].errors["codigo_postal"]
    assert titular.direccion == ""
    assert not RegistroAuditoria.objects.filter(
        accion=RegistroAuditoria.MODIFICACION_DATOS_CLIENTE
    ).exists()


def test_CO108_guardar_sin_cambios_no_audita(navegador, titular):
    navegador.post(URL_DATOS, DATOS)
    navegador.post(URL_DATOS, DATOS)

    assert (
        RegistroAuditoria.objects.filter(
            accion=RegistroAuditoria.MODIFICACION_DATOS_CLIENTE
        ).count()
        == 1
    )


# ===========================================================================
# CO-109 · solicitarCambioDeCorreo
# ===========================================================================


def pedir_cambio(navegador, correo="nuevo@correo.test", contrasena=PASSWORD_DE_PRUEBA):
    return navegador.post(URL_CORREO, {"contrasena_actual": contrasena, "correo_nuevo": correo})


def test_CO109_a_se_crea_un_token_de_cambio_de_correo(navegador, titular):
    pedir_cambio(navegador, "Nuevo@Correo.test")

    token = TokenCambioCorreo.objects.get(usuario=titular)
    assert token.correo_nuevo == "nuevo@correo.test"
    assert token.estado == TokenCambioCorreo.VIGENTE
    assert token.vence_en - token.emitido_en == timedelta(hours=24)


def test_CO109_el_correo_de_la_cuenta_no_cambia(navegador, titular):
    pedir_cambio(navegador)

    titular.refresh_from_db()
    assert titular.email == "ana@correo.test"


def test_CO109_el_enlace_va_al_correo_nuevo(navegador):
    pedir_cambio(navegador)

    assert mail.outbox[-1].to == ["nuevo@correo.test"]
    assert "/cuenta/correo/confirmar/" in mail.outbox[-1].body


def test_CO109_con_la_contrasena_equivocada_no_se_emite_nada(navegador):
    respuesta = pedir_cambio(navegador, contrasena="otra-cosa")

    assert respuesta.context["form"].errors["contrasena_actual"]
    assert not TokenCambioCorreo.objects.exists()
    assert not mail.outbox


def test_CO109_E1_un_correo_con_cuenta_se_rechaza_y_ofrece_recuperar(navegador):
    UsuarioFactory(email="tomado@correo.test")

    respuesta = pedir_cambio(navegador, "Tomado@correo.test")

    assert "Este correo ya tiene una cuenta asociada" in respuesta.content.decode()
    assert reverse("accounts:password_reset") in respuesta.content.decode()
    assert not TokenCambioCorreo.objects.exists()


def test_CO109_un_pedido_nuevo_vence_el_anterior(navegador, titular):
    pedir_cambio(navegador, "uno@correo.test")
    primer_enlace = enlace_del_correo(mail.outbox[-1])
    pedir_cambio(navegador, "dos@correo.test")

    primero = TokenCambioCorreo.objects.get(correo_nuevo="uno@correo.test")
    assert primero.estado == TokenCambioCorreo.VENCIDO
    Client().post(ruta(primer_enlace))
    titular.refresh_from_db()
    assert titular.email == "ana@correo.test"


# ===========================================================================
# CO-110 · confirmarCambioDeCorreo
# ===========================================================================


def test_CO110_abrir_el_enlace_no_cambia_nada(navegador, titular):
    pedir_cambio(navegador)

    Client().get(ruta(enlace_del_correo(mail.outbox[-1])))

    titular.refresh_from_db()
    assert titular.email == "ana@correo.test"


def test_CO110_c_el_correo_pasa_al_nuevo_y_el_token_queda_consumido(navegador, titular):
    pedir_cambio(navegador, "Nuevo@Correo.test")

    Client().post(ruta(enlace_del_correo(mail.outbox[-1])))

    titular.refresh_from_db()
    assert titular.email == "nuevo@correo.test"
    assert TokenCambioCorreo.objects.get().estado == TokenCambioCorreo.CONSUMIDO


def test_CO110_queda_en_la_auditoria(navegador, titular):
    pedir_cambio(navegador)

    Client().post(ruta(enlace_del_correo(mail.outbox[-1])))

    registro = RegistroAuditoria.objects.get(accion=RegistroAuditoria.CAMBIO_CORREO)
    assert registro.actor == titular
    assert registro.detalle == "ana@correo.test → nuevo@correo.test"


def test_CO110_el_correo_anterior_recibe_un_aviso(navegador):
    pedir_cambio(navegador)

    Client().post(ruta(enlace_del_correo(mail.outbox[-1])))

    aviso = mail.outbox[-1]
    assert aviso.to == ["ana@correo.test"]
    assert "nu•" in aviso.body
    assert "nuevo@correo.test" not in aviso.body


def test_CO110_un_enlace_usado_no_sirve_dos_veces(navegador, titular):
    pedir_cambio(navegador)
    enlace = ruta(enlace_del_correo(mail.outbox[-1]))
    Client().post(enlace)
    Usuario.objects.filter(pk=titular.pk).update(email="ana@correo.test")

    respuesta = Client().post(enlace)

    titular.refresh_from_db()
    assert titular.email == "ana@correo.test"
    assert "ya no sirve" in respuesta.content.decode()


def test_CO110_un_enlace_vencido_no_sirve(navegador, titular):
    pedir_cambio(navegador)
    TokenCambioCorreo.objects.update(vence_en=timezone.now() - timedelta(minutes=1))

    respuesta = Client().post(ruta(enlace_del_correo(mail.outbox[-1])))

    titular.refresh_from_db()
    assert titular.email == "ana@correo.test"
    assert "ya no sirve" in respuesta.content.decode()


def test_CO110_si_otra_cuenta_tomo_el_correo_en_el_medio_no_se_cambia(navegador, titular):
    pedir_cambio(navegador)
    UsuarioFactory(email="nuevo@correo.test")

    respuesta = Client().post(ruta(enlace_del_correo(mail.outbox[-1])))

    titular.refresh_from_db()
    assert titular.email == "ana@correo.test"
    assert "ya tiene una cuenta asociada" in respuesta.content.decode()


# ===========================================================================
# CO-111 · cambiarContrasena
# ===========================================================================


def cambiar_contrasena(navegador, actual=PASSWORD_DE_PRUEBA, nueva="Otra-Clave-Larga-2026"):
    return navegador.post(
        URL_CONTRASENA,
        {"old_password": actual, "new_password1": nueva, "new_password2": nueva},
    )


def test_CO111_c_la_credencial_pasa_al_hash_nuevo(navegador, titular):
    antes = titular.password

    cambiar_contrasena(navegador)

    titular.refresh_from_db()
    assert titular.password != antes
    assert titular.check_password("Otra-Clave-Larga-2026")


def test_CO111_la_sesion_actual_sigue_y_las_otras_se_cierran(navegador, titular):
    otro_dispositivo = Client()
    otro_dispositivo.force_login(titular)

    cambiar_contrasena(navegador)

    assert navegador.get(URL_PANEL).status_code == 200
    assert otro_dispositivo.get(URL_PANEL).status_code == 302


def test_CO111_queda_en_la_auditoria(navegador, titular):
    cambiar_contrasena(navegador)

    registro = RegistroAuditoria.objects.get(accion=RegistroAuditoria.CAMBIO_CONTRASENA)
    assert registro.actor == titular


def test_CO111_con_la_contrasena_actual_equivocada_no_cambia_nada(navegador, titular):
    antes = titular.password

    respuesta = cambiar_contrasena(navegador, actual="no-es")

    titular.refresh_from_db()
    assert titular.password == antes
    assert respuesta.context["form"].errors["old_password"]
    assert not RegistroAuditoria.objects.filter(accion=RegistroAuditoria.CAMBIO_CONTRASENA).exists()


# ===========================================================================
# Acceso
# ===========================================================================


@pytest.mark.parametrize("rol", ["cajero", "administrador"])
@pytest.mark.parametrize(
    "url",
    [
        URL_PANEL,
        URL_PEDIDOS,
        URL_HISTORIAL,
        URL_DATOS,
        URL_CORREO,
        URL_CONTRASENA,
        reverse("cuenta:puntos"),
    ],
)
def test_acceso_el_personal_recibe_403_en_mi_cuenta(client, request, rol, url):
    client.force_login(request.getfixturevalue(rol))

    assert client.get(url).status_code == 403


def test_acceso_sin_sesion_va_al_ingreso(client):
    assert client.get(URL_PANEL).url.startswith(reverse("accounts:login"))


def test_acceso_el_personal_no_cambia_sus_datos_por_aca(client, cajero):
    client.force_login(cajero)

    respuesta = client.post(URL_DATOS, DATOS)

    cajero.refresh_from_db()
    assert respuesta.status_code == 403
    assert cajero.direccion == ""
