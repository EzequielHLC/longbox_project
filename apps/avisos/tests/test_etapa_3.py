"""Módulo 19, etapa 3 (plan 00 del bot, etapa 3).

- Los tipos de aviso nuevos y su canal por defecto (ambigüedad 1).
- Los avisos de venta, el resumen de la mañana y su reloj, las alertas de seguridad,
  `/estado` y los controles de salud, el reclamo con sus fotos y el modo inline.

Telegram es el de mentira detrás de la única puerta; las tareas que salen después
de confirmar la transacción se corren con `django_capture_on_commit_callbacks`.
"""

import os
import time
from datetime import datetime, timedelta
from decimal import Decimal
from io import BytesIO, StringIO
from unittest.mock import patch

import pytest
from django.core.management import call_command
from django.urls import reverse
from django.utils import timezone
from PIL import Image

from apps.accounts import services as cuentas
from apps.accounts.models import Usuario
from apps.accounts.tests.factories import UsuarioFactory
from apps.avisos import bot, canales, resumen, salud, seguridad, ventas
from apps.avisos.models import TIPOS, PreferenciaAviso, VinculoTelegram, tipo_de_aviso
from apps.avisos.tests.telegram_falso import TOKEN, telegram_falso
from apps.catalog.models import Producto
from apps.catalog.tests.factories import ProductoFactory
from apps.core.models import ConfiguracionSistema, RegistroAuditoria
from apps.core.tests.concurrencia import a_la_vez
from apps.devoluciones import servicios as devoluciones
from apps.devoluciones.models import CasoDevolucion
from apps.devoluciones.tests.util import foto, pedido_despachado
from apps.pedidos.models import Pedido
from apps.tienda import compra
from apps.tienda.models import CobroEnCurso
from apps.tienda.tests.compra_util import cliente_con_direccion, fijar_parametros

pytestmark = pytest.mark.django_db

CHAT = 4242
URL_PARAMETROS = reverse("catalog:parametros")


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


def correos_a(mailoutbox, direccion):
    return [m for m in mailoutbox if direccion in m.to]


def a_las(hora, minuto=0, dia=28):
    return timezone.make_aware(datetime(2026, 10, dia, hora, minuto))


# ---------------------------------------------------------------------------
# Los tipos nuevos y su canal por defecto
# ---------------------------------------------------------------------------


def test_ventas_resumen_y_sistema_van_sólo_por_telegram_y_seguridad_por_los_dos():
    por_defecto = {t.clave: (t.por_correo, t.por_telegram) for t in TIPOS}

    assert (
        por_defecto["ventas"] == por_defecto["resumen"] == por_defecto["sistema"] == (False, True)
    )
    assert por_defecto["seguridad"] == (True, True)
    assert por_defecto["correos"] == (True, False)


def test_un_tipo_opcional_sin_telegram_no_se_manda(administrador):
    assert canales.destinatarios("ventas") == ([], [])


def test_un_tipo_opcional_con_telegram_va_sólo_al_chat(vinculado, falso):
    correos, chats = canales.destinatarios("ventas")

    assert correos == [] and chats == [(vinculado, CHAT)]


def test_seguridad_va_por_los_dos_y_sin_telegram_por_correo(vinculado, falso):
    correos, chats = canales.destinatarios("seguridad")
    assert correos == [vinculado.email] and chats == [(vinculado, CHAT)]

    VinculoTelegram.objects.all().delete()
    assert canales.destinatarios("seguridad") == ([vinculado.email], [])


def test_si_telegram_falla_un_opcional_no_cae_al_correo(vinculado, mailoutbox):
    falso, parche = telegram_falso(caido=True)
    with parche:
        canales.avisar_administradores("ventas", asunto="x", titulo="Venta", parrafos=[])
        canales.avisar_administradores("correos", asunto="Correo", titulo="Correo", parrafos=[])

    assert [m.subject for m in correos_a(mailoutbox, vinculado.email)] == ["Correo"]


def test_un_tipo_desconocido_sale_por_correo(administrador):
    assert tipo_de_aviso("").por_correo
    assert canales.destinatarios("")[0] == [administrador.email]


def test_el_perfil_muestra_los_tipos_nuevos_con_su_canal(client_admin, vinculado):
    filas = {
        f["clave"]: f for f in client_admin.get(reverse("avisos:perfil")).context["preferencias"]
    }

    assert (filas["ventas"]["por_correo"], filas["ventas"]["por_telegram"]) == (False, True)
    assert (filas["seguridad"]["por_correo"], filas["seguridad"]["por_telegram"]) == (True, True)


def test_sin_chat_marcar_telegram_en_un_opcional_lo_deja_sin_canal(client_admin, administrador):
    client_admin.post(
        reverse("avisos:canales"), {"telegram_ventas": "on", "telegram_correos": "on"}
    )

    ventas_ = PreferenciaAviso.objects.get(usuario=administrador, tipo="ventas")
    correos = PreferenciaAviso.objects.get(usuario=administrador, tipo="correos")
    assert (ventas_.por_correo, ventas_.por_telegram) == (False, False)
    assert (correos.por_correo, correos.por_telegram) == (True, False)


# ---------------------------------------------------------------------------
# Punto 2 · los avisos de venta
# ---------------------------------------------------------------------------


def _cobrar(titular, *lineas, retiro=False):
    total = sum(Decimal(precio) * cantidad for _, cantidad, precio in lineas)
    cobro = CobroEnCurso.objects.create(
        referencia=f"cobro-{CobroEnCurso.objects.count()}",
        pasarela="prueba",
        usuario=titular,
        lineas=[
            {"producto": p.pk, "cantidad": cantidad, "precio": precio, "puntos": 0}
            for p, cantidad, precio in lineas
        ],
        costo_envio=0,
        monto=total,
        retiro=True,
    )
    compra.registrar_resultado(cobro.referencia, referencia_pago="p-1", monto=total)
    return Pedido.objects.order_by("-pk").first()


@pytest.fixture
def titular(db):
    fijar_parametros()
    return cliente_con_direccion(first_name="Ana", last_name="Lectora")


def test_un_pago_aprobado_avisa_la_venta_por_telegram(
    vinculado, titular, falso, mailoutbox, django_capture_on_commit_callbacks
):
    tomo = ProductoFactory(titulo="Berserk", volumen=5, stock=3, precio=Decimal("10000"))

    with django_capture_on_commit_callbacks(execute=True):
        pedido = _cobrar(titular, (tomo, 2, "10000"))

    texto = falso.textos(CHAT)[-1]
    assert "Venta online" in texto and pedido.numero in texto and "$ 20.000" in texto
    assert "Berserk" in texto and "Ana Lectora" in texto
    assert "retira en el local" in texto
    assert not correos_a(mailoutbox, vinculado.email)


def test_la_venta_marca_las_reservas_y_avisa_el_cupo_agotado(
    vinculado, titular, falso, django_capture_on_commit_callbacks
):
    ConfiguracionSistema.objects.update(margen_cupo_preventa=0)
    preventa = ProductoFactory(
        titulo="Frieren",
        volumen=9,
        stock=0,
        estado=Producto.PRE_VENTA,
        fecha_llegada=timezone.localdate() + timedelta(days=10),
        precio=Decimal("10000"),
        pedido_en_camino=2,
    )

    with django_capture_on_commit_callbacks(execute=True):
        _cobrar(titular, (preventa, 2, "10000"))

    venta, agotada = falso.textos(CHAT)[-2:]
    assert "reserva" in venta
    assert "agotó el cupo" in agotada and "Frieren" in agotada


def test_sin_telegram_la_venta_no_le_escribe_al_administrador(
    administrador, titular, mailoutbox, django_capture_on_commit_callbacks
):
    tomo = ProductoFactory(stock=3, precio=Decimal("10000"))

    with django_capture_on_commit_callbacks(execute=True):
        _cobrar(titular, (tomo, 1, "10000"))

    assert not correos_a(mailoutbox, administrador.email)
    assert correos_a(mailoutbox, titular.email)


def test_un_aviso_de_venta_caído_no_deshace_la_venta(
    vinculado, titular, falso, django_capture_on_commit_callbacks
):
    tomo = ProductoFactory(stock=3, precio=Decimal("10000"))

    with (
        patch.object(ventas, "avisar_venta", side_effect=RuntimeError("caído")),
        django_capture_on_commit_callbacks(execute=True),
    ):
        pedido = _cobrar(titular, (tomo, 1, "10000"))

    assert pedido is not None and pedido.estado == Pedido.PENDIENTE_ARMADO


# ---------------------------------------------------------------------------
# Punto 1 · el resumen de la mañana y el reloj
# ---------------------------------------------------------------------------


def test_el_resumen_espera_la_hora_y_sale_una_vez_por_día(vinculado, falso):
    assert resumen.si_corresponde(a_las(8, 59)).estado == "no es la hora"
    assert resumen.si_corresponde(a_las(9, 0)).estado == "enviado"
    assert resumen.si_corresponde(a_las(9, 1)).estado == "ya salió"
    assert resumen.si_corresponde(a_las(9, 0, dia=29)).estado == "enviado"

    assert len([t for t in falso.textos(CHAT) if "Resumen de la mañana" in t]) == 2


def test_el_resumen_dice_lo_pendiente_lo_que_llega_y_lo_de_ayer(vinculado, falso):
    hoy = timezone.localdate()
    ProductoFactory(titulo="Llega hoy", estado=Producto.PRE_VENTA, fecha_llegada=hoy)
    ProductoFactory(
        titulo="Atrasada", estado=Producto.PRE_VENTA, fecha_llegada=hoy - timedelta(days=3)
    )

    resumen.enviar(hoy)

    texto = falso.textos(CHAT)[-1]
    assert "Correos de proveedores sin decidir: 0" in texto
    assert "Pre-ventas que llegan hoy: 1" in texto and "Pre-ventas atrasadas: 1" in texto
    assert "Llegan hoy: Llega hoy" in texto
    assert "Caja de ayer: sin cerrar" in texto
    assert "Ventas online de ayer: ninguna" in texto


def test_la_hora_del_resumen_se_cambia_en_parámetros(client_admin):
    datos = {
        "stock_inicial_por_defecto": "1",
        "intervalo_carrusel": "10",
        "dias_aviso_preventa": "2",
        "cantidad_minima_restock": "3",
        "margen_stock_restock": "2",
        "frecuencia_casilla_minutos": "5",
    }
    client_admin.post(URL_PARAMETROS, {**datos, "hora_resumen": "08:30"})
    assert ConfiguracionSistema.obtener().hora_resumen.strftime("%H:%M") == "08:30"

    client_admin.post(URL_PARAMETROS, datos)
    assert ConfiguracionSistema.obtener().hora_resumen.strftime("%H:%M") == "08:30"


@pytest.mark.django_db(transaction=True)
def test_dos_relojes_a_la_vez_mandan_un_solo_resumen():
    ConfiguracionSistema.obtener()
    with patch.object(resumen, "enviar") as enviar:
        resultados = a_la_vez(
            lambda: resumen.si_corresponde(a_las(9, 5)).estado,
            lambda: resumen.si_corresponde(a_las(9, 5)).estado,
        )

    assert sorted(resultados) == ["enviado", "ya salió"]
    enviar.assert_called_once()


def test_cada_minuto_corre_las_tres_tareas_aunque_una_falle(administrador):
    salida = StringIO()

    with patch.object(salud, "controlar", side_effect=RuntimeError("roto")):
        call_command("cada_minuto", stdout=salida)

    lineas = salida.getvalue().splitlines()
    assert lineas[0] == "casilla: sin configurar"
    assert lineas[1].startswith("resumen: ")
    assert lineas[2] == "salud: fallo"


# ---------------------------------------------------------------------------
# Punto 4 · seguridad
# ---------------------------------------------------------------------------


def test_un_bloqueo_por_intentos_avisa_por_los_dos_canales(
    vinculado, falso, mailoutbox, django_capture_on_commit_callbacks, settings
):
    cajero = UsuarioFactory(rol=Usuario.CAJERO)

    with django_capture_on_commit_callbacks(execute=True):
        for _ in range(settings.LOGIN_INTENTOS_MAXIMOS):
            cuentas.registrar_intento_fallido(cajero.email, "9.9.9.9")

    assert "cuenta bloqueada" in falso.textos(CHAT)[-1] and cajero.email in falso.textos(CHAT)[-1]
    assert any("seguridad" in m.subject for m in correos_a(mailoutbox, vinculado.email))


def test_un_bloqueo_de_una_cuenta_que_no_existe_no_avisa(
    vinculado, falso, django_capture_on_commit_callbacks, settings
):
    with django_capture_on_commit_callbacks(execute=True):
        for _ in range(settings.LOGIN_INTENTOS_MAXIMOS):
            cuentas.registrar_intento_fallido("nadie@correo.test", "9.9.9.9")

    assert not falso.textos(CHAT)


def _ingreso(usuario, ip, capturar):
    with capturar(execute=True):
        RegistroAuditoria.registrar(accion=RegistroAuditoria.INICIO_SESION, actor=usuario, ip=ip)


def test_el_personal_desde_una_ip_nueva_avisa(vinculado, falso, django_capture_on_commit_callbacks):
    cajero = UsuarioFactory(rol=Usuario.CAJERO)
    _ingreso(cajero, "1.1.1.1", django_capture_on_commit_callbacks)  # el primero no cuenta
    _ingreso(cajero, "1.1.1.1", django_capture_on_commit_callbacks)  # la misma IP tampoco
    assert not falso.textos(CHAT)

    _ingreso(cajero, "2.2.2.2", django_capture_on_commit_callbacks)

    assert "IP nueva" in falso.textos(CHAT)[-1] and "2.2.2.2" in falso.textos(CHAT)[-1]


def test_una_ip_que_no_se_usa_hace_más_de_noventa_días_es_nueva(
    vinculado, falso, django_capture_on_commit_callbacks
):
    cajero = UsuarioFactory(rol=Usuario.CAJERO)
    _ingreso(cajero, "1.1.1.1", django_capture_on_commit_callbacks)

    # El registro no se puede envejecer (es inmutable): se acorta la ventana.
    with patch.object(seguridad, "DIAS_DE_UNA_IP_CONOCIDA", 0):
        _ingreso(cajero, "1.1.1.1", django_capture_on_commit_callbacks)

    assert "IP nueva" in falso.textos(CHAT)[-1]


def test_un_cliente_desde_otra_ip_no_avisa(vinculado, falso, django_capture_on_commit_callbacks):
    cliente = UsuarioFactory(rol=Usuario.CLIENTE)
    _ingreso(cliente, "1.1.1.1", django_capture_on_commit_callbacks)
    _ingreso(cliente, "2.2.2.2", django_capture_on_commit_callbacks)

    assert not falso.textos(CHAT)


def _auditar(capturar, accion, detalle, objetivo=None):
    with capturar(execute=True):
        RegistroAuditoria.registrar(
            accion=accion, actor_email="otro@correo.test", detalle=detalle, objetivo=objetivo
        )


def test_el_alta_de_un_administrador_avisa_y_la_de_un_cajero_no(
    vinculado, falso, django_capture_on_commit_callbacks
):
    alta = RegistroAuditoria.ALTA_USUARIO
    _auditar(django_capture_on_commit_callbacks, alta, "", UsuarioFactory(rol=Usuario.CAJERO))
    assert not falso.textos(CHAT)

    nuevo = UsuarioFactory(rol=Usuario.ADMINISTRADOR)
    _auditar(django_capture_on_commit_callbacks, alta, "", nuevo)

    assert "Administrador nuevo" in falso.textos(CHAT)[-1] and nuevo.email in falso.textos(CHAT)[-1]


def test_un_cambio_de_rol_de_administrador_avisa(
    vinculado, falso, django_capture_on_commit_callbacks
):
    otro = UsuarioFactory(rol=Usuario.CAJERO)
    cambio = RegistroAuditoria.MODIFICACION_USUARIO
    _auditar(django_capture_on_commit_callbacks, cambio, "nombre: Ana → Ani", otro)
    assert not falso.textos(CHAT)

    _auditar(django_capture_on_commit_callbacks, cambio, "rol: Administrador → Cajero", otro)

    assert "cambio de rol" in falso.textos(CHAT)[-1]


@pytest.mark.parametrize(
    ("accion", "detalle", "avisa"),
    [
        (
            RegistroAuditoria.MODIFICACION_PRECIO_REFERENCIA,
            "Ivrea B6: $ 1 → $ 2; 12 productos actualizados",
            True,
        ),
        (
            RegistroAuditoria.MODIFICACION_PRECIO_REFERENCIA,
            "Ivrea B6: $ 1 → $ 2; 0 productos actualizados",
            False,
        ),
        (
            RegistroAuditoria.PARAMETRO_MODIFICADO,
            "margen global: 30 % → 35 %; 40 productos recalculados; 0 excluidos",
            True,
        ),
        (RegistroAuditoria.PARAMETRO_MODIFICADO, "stock por defecto: 1 → 2", False),
    ],
)
def test_sólo_las_propagaciones_de_precios_son_masivas(
    vinculado, falso, django_capture_on_commit_callbacks, accion, detalle, avisa
):
    _auditar(django_capture_on_commit_callbacks, accion, detalle)

    assert bool(falso.textos(CHAT)) is avisa


def test_una_alerta_de_seguridad_no_toca_el_registro(
    vinculado, falso, django_capture_on_commit_callbacks
):
    otro = UsuarioFactory(rol=Usuario.ADMINISTRADOR)
    antes = RegistroAuditoria.objects.count()

    _auditar(django_capture_on_commit_callbacks, RegistroAuditoria.ALTA_USUARIO, "", otro)

    assert RegistroAuditoria.objects.count() == antes + 1


# ---------------------------------------------------------------------------
# Punto 5 · /estado y la salud
# ---------------------------------------------------------------------------


def test_estado_en_el_chat(vinculado, falso):
    bot.procesar(
        {"update_id": 1, "message": {"chat": {"id": CHAT, "type": "private"}, "text": "/estado"}}
    )

    texto = falso.textos(CHAT)[-1]
    assert "Estado del sistema" in texto and "Disco:" in texto and "Casilla" in texto


def test_estado_no_responde_a_un_chat_sin_vínculo(falso):
    bot.procesar(
        {"update_id": 1, "message": {"chat": {"id": CHAT, "type": "private"}, "text": "/estado"}}
    )

    assert "no está vinculado" in falso.textos(CHAT)[-1]


def test_el_disco_lleno_se_avisa_una_vez_por_día(vinculado, falso):
    with patch.object(salud, "disco", return_value=(91, 2 * 1024**3)):
        assert salud.controlar(a_las(10)) == ["disco"]
        assert salud.controlar(a_las(10, 1)) == []
        assert salud.controlar(a_las(10, dia=29)) == ["disco"]

    assert "91 %" in falso.textos(CHAT)[-1]


def test_un_problema_que_se_arregla_y_vuelve_se_avisa_de_nuevo(vinculado, falso):
    with patch.object(salud, "disco", return_value=(91, 1)):
        salud.controlar(a_las(10))
    with patch.object(salud, "disco", return_value=(40, 1)):
        assert salud.controlar(a_las(11)) == []
    with patch.object(salud, "disco", return_value=(91, 1)):
        assert salud.controlar(a_las(12)) == ["disco"]


def test_el_respaldo_vencido_se_avisa_sólo_donde_se_vigila(vinculado, falso, settings, tmp_path):
    settings.RESPALDOS_DIR = str(tmp_path)
    viejo = tmp_path / "longbox-20261026-033000.dump"
    viejo.write_bytes(b"x")
    hace_dos_dias = time.time() - 2 * 24 * 3600
    os.utime(viejo, (hace_dos_dias, hace_dos_dias))

    settings.VIGILAR_RESPALDO = False
    assert "respaldo" not in salud.problemas()

    settings.VIGILAR_RESPALDO = True
    assert "el de anoche no salió" in salud.problemas()["respaldo"]
    assert "⚠" in salud.texto_del_estado()

    (tmp_path / "longbox-20261028-033000.dump").write_bytes(b"x")
    assert "respaldo" not in salud.problemas()


def test_sin_ningún_respaldo_lo_dice(settings, tmp_path):
    settings.RESPALDOS_DIR = str(tmp_path / "no-existe")
    settings.VIGILAR_RESPALDO = True

    assert salud.problemas()["respaldo"] == "No hay ningún respaldo de la base."


def test_la_memoria_fuera_de_linux_no_se_inventa(tmp_path):
    with patch.object(salud, "_MEMINFO", tmp_path / "no-existe"):
        assert salud.memoria() is None

    meminfo = tmp_path / "meminfo"
    meminfo.write_text("MemTotal:  1000 kB\nMemAvailable:  500 kB\n")
    with patch.object(salud, "_MEMINFO", meminfo):
        assert salud.memoria() == (500 * 1024, 1000 * 1024)


# ---------------------------------------------------------------------------
# Punto 6 · el reclamo con sus fotos
# ---------------------------------------------------------------------------


def test_el_reclamo_llega_al_chat_con_sus_fotos_achicadas(
    vinculado, falso, titular, django_capture_on_commit_callbacks
):
    PreferenciaAviso.objects.create(
        usuario=vinculado, tipo="devoluciones", por_correo=False, por_telegram=True
    )
    pedido = pedido_despachado(titular)
    linea = pedido.lineas.get()

    with django_capture_on_commit_callbacks(execute=True):
        devoluciones.registrar_caso(
            pedido, linea.pk, titular, CasoDevolucion.DEFECTO, "Rota", [foto(tamano=(1600, 1200))]
        )

    assert "Revisar el caso" in falso.textos(CHAT)[-1]
    (album,) = [c for m, c in falso.llamadas if m == "sendMediaGroup"]
    nombre, contenido, tipo = album["foto0"]
    assert tipo == "image/jpeg"
    assert max(Image.open(BytesIO(contenido)).size) == 800


def test_por_correo_el_reclamo_va_sin_fotos(
    administrador, titular, mailoutbox, django_capture_on_commit_callbacks
):
    pedido = pedido_despachado(titular)

    with django_capture_on_commit_callbacks(execute=True):
        devoluciones.registrar_caso(
            pedido, pedido.lineas.get().pk, titular, CasoDevolucion.DEFECTO, "", [foto()]
        )

    (aviso,) = correos_a(mailoutbox, administrador.email)
    assert not aviso.attachments


# ---------------------------------------------------------------------------
# Punto 3 · el modo inline
# ---------------------------------------------------------------------------


def _inline(texto, quien=CHAT):
    bot.procesar(
        {"update_id": 3, "inline_query": {"id": "q", "from": {"id": quien}, "query": texto}}
    )


def _resultados(falso):
    (cuerpo,) = [c for m, c in falso.llamadas if m == "answerInlineQuery"]
    assert cuerpo["is_personal"] is True
    return cuerpo["results"]


def test_inline_comparte_la_ficha_de_la_tienda_sin_el_stock(vinculado, falso):
    tomo = ProductoFactory(titulo="Berserk", volumen=5, stock=7, precio=Decimal("24900"))

    _inline("berserk 5")

    (resultado,) = _resultados(falso)
    assert resultado["id"] == str(tomo.pk)
    assert "stock 7" in resultado["description"]
    mensaje = resultado["input_message_content"]["message_text"]
    assert "Berserk" in mensaje and "$ 24.900" in mensaje and "Disponible" in mensaje
    assert "stock" not in mensaje.lower()
    assert f"https://longbox.test/tienda/producto/{tomo.pk}/" in mensaje


def test_inline_dice_la_pre_venta_y_lo_agotado(vinculado, falso):
    ProductoFactory(
        titulo="Frieren",
        volumen=1,
        estado=Producto.PRE_VENTA,
        fecha_llegada=timezone.localdate() + timedelta(days=5),
    )
    ProductoFactory(titulo="Frieren", volumen=2, stock=0)

    _inline("frieren")

    mensajes = [r["input_message_content"]["message_text"] for r in _resultados(falso)]
    assert any("En pre-venta, llega el" in m for m in mensajes)
    assert any("Agotado" in m for m in mensajes)


def test_inline_no_muestra_lo_que_la_tienda_no_muestra(vinculado, falso):
    ProductoFactory(titulo="Akira", volumen=1, solo_adultos=True)
    ProductoFactory(titulo="Akira", volumen=2, estado=Producto.DESCATALOGADO)

    _inline("akira")

    assert _resultados(falso) == []


# Foco reforzado: control de acceso. Telegram dice quién pregunta.


def test_inline_no_contesta_a_quien_no_está_vinculado(vinculado, falso):
    ProductoFactory(titulo="Berserk", volumen=5)

    _inline("berserk", quien=999)

    assert _resultados(falso) == []


def test_inline_no_contesta_a_un_administrador_dado_de_baja(vinculado, falso):
    UsuarioFactory(rol=Usuario.ADMINISTRADOR)
    Usuario.objects.filter(pk=vinculado.pk).update(estado=Usuario.INACTIVO)
    ProductoFactory(titulo="Berserk", volumen=5)

    _inline("berserk")

    assert _resultados(falso) == []


def test_inline_con_menos_de_dos_letras_no_busca(vinculado, falso):
    ProductoFactory(titulo="B", volumen=1)

    _inline("b")

    assert _resultados(falso) == []


def test_la_miniatura_sólo_con_https_y_portada(vinculado, falso, settings):
    tomo = ProductoFactory(titulo="Berserk", volumen=5)

    _inline("berserk")
    assert "thumbnail_url" not in _resultados(falso)[0]

    imagen = BytesIO()
    Image.new("RGB", (60, 90), "red").save(imagen, "PNG")
    from django.core.files.base import ContentFile

    tomo.portada.save("tapa.png", ContentFile(imagen.getvalue()), save=True)
    falso.llamadas.clear()
    _inline("berserk")
    assert _resultados(falso)[0]["thumbnail_url"].startswith("https://longbox.test/")
    tomo.portada.delete(save=False)


def test_el_bot_pide_las_búsquedas_en_línea(falso):
    from apps.avisos import telegram

    telegram.novedades()

    (cuerpo,) = [c for m, c in falso.llamadas if m == "getUpdates"]
    assert "inline_query" in cuerpo["allowed_updates"]
