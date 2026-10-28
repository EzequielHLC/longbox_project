"""Módulo 19, etapa 2 · `CU-AVI-CON` y `CU-AVI-BOR` desde el chat, y los comandos.

El modelo de lenguaje se reemplaza por respuestas fijas en `llm.pedir_json`: lo
que se prueba es lo que el sistema hace con ellas. Que el modelo **sólo elige**
(la consulta) o **sólo propone** (el borrador) es la regla 4, y por eso cada
prueba de carga mira también que no haya nacido ningún producto.
"""

from datetime import timedelta
from decimal import Decimal
from io import BytesIO
from unittest.mock import patch

import pytest
from django.utils import timezone

from apps.accounts.models import Usuario
from apps.accounts.tests.factories import UsuarioFactory
from apps.avisos import bot, consultas, telegram
from apps.avisos.models import VinculoTelegram
from apps.avisos.tests.telegram_falso import TOKEN, telegram_falso
from apps.catalog.models import BorradorProducto, Producto
from apps.catalog.tests.factories import (
    EditorialFactory,
    FormatoFactory,
    PrecioReferenciaFactory,
    ProductoFactory,
    TipoFactory,
)
from apps.core import integraciones, llm
from apps.core.models import RegistroAuditoria
from apps.suppliers.tests.factories import ProveedorFactory

pytestmark = pytest.mark.django_db

CHAT = 4242
# La descarga de verdad, tomada antes de que la fixture de red la corte.
DESCARGAR_REAL = integraciones.descargar


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


def mensaje(texto=None, chat=CHAT, **extra):
    cuerpo = {"message_id": 1, "chat": {"id": chat, "type": "private"}, "from": {}}
    if texto is not None:
        cuerpo["text"] = texto
    cuerpo.update(extra)
    return {"update_id": 1, "message": cuerpo}


def modelo(datos):
    return patch.object(llm, "pedir_json", return_value=llm.RespuestaDelModelo(datos=datos))


def leido(**campos):
    producto = {
        "isbn": "",
        "titulo": "",
        "volumen": "",
        "formato": "",
        "precio": "",
        "fecha": "",
        "confianza": dict.fromkeys(
            ("isbn", "titulo", "volumen", "formato", "precio", "fecha"), "alta"
        ),
    }
    cabecera = {
        "editorial": campos.pop("editorial", ""),
        "tipo": campos.pop("tipo", ""),
        "rubro": campos.pop("rubro", "editorial"),
    }
    producto.update(campos)
    return {**cabecera, "producto": producto}


# ---------------------------------------------------------------------------
# Los comandos y la ayuda
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("comando", ["/ayuda", "/help", "/help@longbox_prueba_bot"])
def test_la_ayuda_lista_los_comandos(comando, vinculado, falso):
    bot.procesar(mensaje(comando))

    texto = falso.textos(CHAT)[-1]
    for nombre in ("/stock", "/llega", "/pendientes", "/caja", "/cargar", "/salir"):
        assert nombre in texto


def test_un_comando_desconocido_lo_dice(vinculado, falso):
    bot.procesar(mensaje("/vender 3"))

    assert "No conozco /vender" in falso.textos(CHAT)[-1]


def test_un_mensaje_vacío_responde_la_ayuda(vinculado, falso):
    bot.procesar(mensaje(sticker={"file_id": "x"}))

    assert "/stock" in falso.textos(CHAT)[-1]


@pytest.mark.parametrize("texto", ["/stock Berserk", "/pendientes", "/cargar Berserk 5", "hola"])
def test_un_chat_sin_vínculo_no_consulta_ni_carga(texto, falso):
    with patch.object(llm, "pedir_json") as pedir:
        bot.procesar(mensaje(texto))

    assert "no está vinculado" in falso.textos(CHAT)[-1]
    pedir.assert_not_called()
    assert not BorradorProducto.objects.exists()


def test_un_administrador_dado_de_baja_no_consulta(vinculado, falso):
    # I-12: tiene que quedar otro Administrador activo para dar de baja a este.
    UsuarioFactory(rol=Usuario.ADMINISTRADOR)
    Usuario.objects.filter(pk=vinculado.pk).update(estado=Usuario.INACTIVO)

    bot.procesar(mensaje("/caja"))

    assert "no está vinculado" in falso.textos(CHAT)[-1]


def test_poner_comandos_registra_la_lista_en_telegram(falso):
    telegram.poner_comandos()

    metodo, cuerpo = falso.llamadas[-1]
    assert metodo == "setMyCommands"
    nombres = {c["command"] for c in cuerpo["commands"]}
    assert {"ayuda", "stock", "llega", "pendientes", "caja", "cargar", "salir"} <= nombres


# ---------------------------------------------------------------------------
# CU-AVI-CON · las consultas fijas
# ---------------------------------------------------------------------------


def test_stock_por_título_y_tomo(vinculado, falso):
    ProductoFactory(titulo="Chainsaw Man", volumen=12, codigo="CSM-12")
    ProductoFactory(titulo="Chainsaw Man", volumen=11)

    bot.procesar(mensaje("/stock chainsaw man 12"))

    texto = falso.textos(CHAT)[-1]
    assert "CSM-12" in texto and "Stock" in texto
    assert texto.count("<b>") == 1


def test_stock_por_código_exacto(vinculado, falso):
    ProductoFactory(titulo="Berserk", codigo="BER-01")

    bot.procesar(mensaje("/stock ber-01"))

    assert "BER-01" in falso.textos(CHAT)[-1]


def test_stock_de_una_preventa_dice_cuándo_llega_y_lo_reservado(vinculado, falso):
    llegada = timezone.localdate() + timedelta(days=10)
    ProductoFactory(titulo="Frieren", volumen=9, estado=Producto.PRE_VENTA, fecha_llegada=llegada)

    bot.procesar(mensaje("/stock Frieren 9"))

    texto = falso.textos(CHAT)[-1]
    assert llegada.strftime("%d/%m/%Y") in texto and "reservadas" in texto


def test_stock_sin_texto_y_sin_resultados(vinculado, falso):
    bot.procesar(mensaje("/stock"))
    bot.procesar(mensaje("/stock Nada que exista"))

    primero, segundo = falso.textos(CHAT)[-2:]
    assert "Decime qué buscar" in primero
    assert "No encontré nada" in segundo


def test_stock_no_muestra_lo_descatalogado(vinculado, falso):
    ProductoFactory(titulo="Akira", estado=Producto.DESCATALOGADO)

    assert consultas.buscar("Akira") == []


def test_llega_lista_preventas_próximas_y_marca_las_atrasadas(vinculado, falso):
    hoy = timezone.localdate()
    ProductoFactory(
        titulo="Pronto", estado=Producto.PRE_VENTA, fecha_llegada=hoy + timedelta(days=3)
    )
    ProductoFactory(
        titulo="Atrasado", estado=Producto.PRE_VENTA, fecha_llegada=hoy - timedelta(days=2)
    )
    ProductoFactory(
        titulo="Lejano", estado=Producto.PRE_VENTA, fecha_llegada=hoy + timedelta(days=40)
    )

    bot.procesar(mensaje("/llega"))

    texto = falso.textos(CHAT)[-1]
    assert "Pronto" in texto and "Atrasado" in texto and "(atrasada)" in texto
    assert "Lejano" not in texto
    assert "Pedidos a proveedores" in texto


def test_llega_sin_nada(vinculado, falso):
    bot.procesar(mensaje("/llega"))

    assert "No llega nada" in falso.textos(CHAT)[-1]


def test_pendientes_cuenta_lo_que_espera_una_decisión(vinculado, falso):
    bot.procesar(mensaje("/pendientes"))

    texto = falso.textos(CHAT)[-1]
    assert "Correos de proveedores sin decidir" in texto
    assert "Borradores para revisar" in texto


def test_caja_sin_cobros(vinculado, falso):
    bot.procesar(mensaje("/caja"))

    assert "Cobrado sin cerrar" in falso.textos(CHAT)[-1]


def test_las_consultas_no_escriben_nada(vinculado, falso):
    ProductoFactory(titulo="Berserk")
    auditoria = RegistroAuditoria.objects.count()

    for comando in ("/stock Berserk", "/llega", "/pendientes", "/caja"):
        bot.procesar(mensaje(comando))

    assert RegistroAuditoria.objects.count() == auditoria
    assert not BorradorProducto.objects.exists()


def test_una_pregunta_libre_el_modelo_elige_y_el_sistema_consulta(vinculado, falso):
    ProductoFactory(titulo="Chainsaw Man", volumen=12, codigo="CSM-12")

    with modelo({"consulta": "stock", "texto": "Chainsaw Man 12"}) as pedir:
        bot.procesar(mensaje("¿cuántos chainsaw 12 tengo?"))

    assert "CSM-12" in falso.textos(CHAT)[-1]
    # El modelo recibe la pregunta y nada de la base.
    assert pedir.call_args.args[1] == "¿cuántos chainsaw 12 tengo?"


def test_una_pregunta_que_no_es_ninguna_consulta(vinculado, falso):
    with modelo({"consulta": "ninguna", "texto": ""}):
        bot.procesar(mensaje("contame un chiste"))

    assert "no lo sé responder" in falso.textos(CHAT)[-1]


def test_una_consulta_inventada_por_el_modelo_cuenta_como_ninguna(vinculado, falso):
    with modelo({"consulta": "borrar_todo", "texto": ""}):
        bot.procesar(mensaje("borrá todo"))

    assert "no lo sé responder" in falso.textos(CHAT)[-1]


def test_sin_modelo_la_pregunta_libre_sugiere_los_comandos(vinculado, falso):
    bot.procesar(mensaje("¿qué llega mañana?"))

    assert "/stock" in falso.textos(CHAT)[-1] and "no contestó" in falso.textos(CHAT)[-1]


def test_una_pregunta_libre_de_llegadas(vinculado, falso):
    with modelo({"consulta": "llega", "texto": ""}):
        bot.procesar(mensaje("¿qué llega esta semana?"))

    assert "No llega nada" in falso.textos(CHAT)[-1]


# ---------------------------------------------------------------------------
# CU-AVI-BOR · el borrador desde el chat
# ---------------------------------------------------------------------------


@pytest.fixture
def ivrea():
    editorial = EditorialFactory(nombre="Ivrea")
    tipo = TipoFactory(nombre="Manga")
    formato = FormatoFactory(nombre="B6")
    formato.tipos.add(tipo)
    ProveedorFactory(editorial=editorial, tipo_por_defecto=tipo)
    PrecioReferenciaFactory(editorial=editorial, tipo=tipo, formato=formato, pvp=Decimal("21900"))
    return editorial


def test_cargar_crea_un_borrador_de_telegram_y_ningún_producto(vinculado, ivrea, falso):
    datos = leido(
        editorial="ivrea", titulo="Berserk Deluxe", volumen="5", formato="B6", precio="24900"
    )

    with modelo(datos):
        bot.procesar(mensaje("/cargar Berserk Deluxe 5, Ivrea, B6, 24900"))

    borrador = BorradorProducto.objects.get()
    assert borrador.origen == BorradorProducto.TELEGRAM
    assert borrador.cargado_por == vinculado
    assert borrador.correo is None
    assert borrador.editorial == ivrea
    assert borrador.titulo == "Berserk Deluxe" and borrador.volumen == 5
    assert borrador.precio == Decimal("24900")
    assert borrador.estado in BorradorProducto.ESTADOS_ABIERTOS
    assert not Producto.objects.exists()
    assert RegistroAuditoria.objects.filter(
        accion=RegistroAuditoria.BORRADORES_GENERADOS, actor=vinculado, detalle__contains="Telegram"
    ).exists()
    texto = falso.textos(CHAT)[-1]
    assert "Revisarlo en Longbox" in texto and f"/borradores/{borrador.pk}/" in texto


def test_sin_precio_toma_el_de_la_tabla_de_la_editorial(vinculado, ivrea, falso):
    with modelo(leido(editorial="Ivrea", titulo="Dandadan", volumen="3", formato="B6")):
        bot.procesar(mensaje("/cargar Dandadan 3 Ivrea B6"))

    assert BorradorProducto.objects.get().precio == Decimal("21900")


def test_una_editorial_que_no_existe_queda_para_elegir_con_un_reparo(vinculado, falso):
    with modelo(leido(editorial="Editorial Inventada", titulo="Algo", volumen="1")):
        bot.procesar(mensaje("/cargar Algo 1, Editorial Inventada"))

    borrador = BorradorProducto.objects.get()
    assert borrador.editorial is None
    assert any("Editorial Inventada" in r for r in borrador.reparos)
    assert "sin editorial" in falso.textos(CHAT)[-1]


def test_un_duplicado_se_avisa_en_el_chat(vinculado, ivrea, falso):
    existente = ProductoFactory(
        titulo="Berserk Deluxe",
        volumen=5,
        editorial=ivrea,
        tipo=ivrea.proveedores.get().tipo_por_defecto,
        formato=BorradorProducto._meta.get_field("formato").related_model.objects.get(nombre="B6"),
        codigo="BER-DLX-5",
    )

    with modelo(leido(editorial="Ivrea", titulo="Berserk Deluxe", volumen="5", formato="B6")):
        bot.procesar(mensaje("/cargar Berserk Deluxe 5 Ivrea B6"))

    texto = falso.textos(CHAT)[-1]
    assert "Ya está en el catálogo" in texto and existente.codigo in texto


def test_la_foto_es_la_portada_y_el_epígrafe_los_datos(vinculado, ivrea, falso):
    from PIL import Image

    imagen = BytesIO()
    Image.new("RGB", (600, 900), "red").save(imagen, "JPEG")
    foto = [{"file_id": "chica", "file_size": 10}, {"file_id": "grande", "file_size": 90}]

    with (
        modelo(leido(editorial="Ivrea", titulo="Berserk Deluxe", volumen="5", formato="B6")),
        patch.object(telegram, "descargar_archivo", return_value=imagen.getvalue()) as bajar,
    ):
        bot.procesar(mensaje(photo=foto, caption="Berserk Deluxe 5, Ivrea, B6"))

    bajar.assert_called_once_with("grande")
    borrador = BorradorProducto.objects.get()
    assert borrador.portada
    assert not Producto.objects.exists()
    borrador.portada.delete(save=False)


def test_una_foto_que_no_baja_deja_el_borrador_con_un_reparo(vinculado, ivrea, falso):
    foto = [{"file_id": "grande", "file_size": 90}]

    with (
        modelo(leido(editorial="Ivrea", titulo="Berserk Deluxe", volumen="5")),
        patch.object(telegram, "descargar_archivo", return_value=None),
    ):
        bot.procesar(mensaje(photo=foto, caption="/cargar Berserk Deluxe 5"))

    borrador = BorradorProducto.objects.get()
    assert not borrador.portada
    assert any("no se pudo descargar" in r for r in borrador.reparos)


def test_una_foto_que_no_es_imagen_deja_el_borrador_con_un_reparo(vinculado, ivrea, falso):
    foto = [{"file_id": "grande", "file_size": 90}]

    with (
        modelo(leido(editorial="Ivrea", titulo="Berserk Deluxe", volumen="5")),
        patch.object(telegram, "descargar_archivo", return_value=b"no soy una imagen"),
    ):
        bot.procesar(mensaje(photo=foto, caption="Berserk Deluxe 5"))

    borrador = BorradorProducto.objects.get()
    assert not borrador.portada
    assert any("no se pudo guardar" in r for r in borrador.reparos)


def test_cargar_sin_texto_pide_los_datos(vinculado, falso):
    with patch.object(llm, "pedir_json") as pedir:
        bot.procesar(mensaje("/cargar"))

    assert "Contame qué cargar" in falso.textos(CHAT)[-1]
    pedir.assert_not_called()


def test_cargar_sin_modelo_no_crea_nada(vinculado, falso):
    bot.procesar(mensaje("/cargar Berserk 5"))

    assert "no contestó" in falso.textos(CHAT)[-1]
    assert not BorradorProducto.objects.exists()


def test_cargar_sin_título_no_crea_nada(vinculado, falso):
    with modelo(leido(precio="1000")):
        bot.procesar(mensaje("/cargar 1000 pesos"))

    assert "No encontré un título" in falso.textos(CHAT)[-1]
    assert not BorradorProducto.objects.exists()


def test_una_pregunta_que_describe_un_producto_lo_carga(vinculado, ivrea, falso):
    respuestas = [
        llm.RespuestaDelModelo(datos={"consulta": "cargar", "texto": ""}),
        llm.RespuestaDelModelo(
            datos=leido(editorial="Ivrea", titulo="Berserk Deluxe", volumen="5")
        ),
    ]
    with patch.object(llm, "pedir_json", side_effect=respuestas):
        bot.procesar(mensaje("Dame de alta Berserk Deluxe 5 de Ivrea"))

    assert BorradorProducto.objects.get().origen == BorradorProducto.TELEGRAM


def test_la_revisión_muestra_el_origen_telegram(client_admin, vinculado, ivrea, falso):
    with modelo(leido(editorial="Ivrea", titulo="Berserk Deluxe", volumen="5", formato="B6")):
        bot.procesar(mensaje("/cargar Berserk Deluxe 5"))

    from django.urls import reverse

    lista = client_admin.get(reverse("catalog:borrador_lista"))
    ficha = client_admin.get(
        reverse("catalog:borrador_detalle", args=[BorradorProducto.objects.get().pk])
    )

    assert lista.status_code == 200 and "Telegram" in lista.content.decode()
    assert ficha.status_code == 200


# ---------------------------------------------------------------------------
# La única puerta: la descarga de la foto
# ---------------------------------------------------------------------------


def test_descargar_archivo_pide_la_ruta_y_baja_por_la_puerta(falso):
    falso_get_file = integraciones.Respuesta(
        datos={"ok": True, "result": {"file_path": "photos/a.jpg"}}
    )
    with (
        patch.object(integraciones, "pedir", return_value=falso_get_file),
        patch.object(integraciones, "descargar", return_value=b"bytes") as bajar,
    ):
        assert telegram.descargar_archivo("id") == b"bytes"

    url = bajar.call_args.args[0]
    assert url.endswith("/photos/a.jpg") and TOKEN in url
    assert bajar.call_args.kwargs["tope"] == telegram.TOPE_DE_FOTO


def test_descargar_archivo_sin_ruta_no_baja_nada(falso):
    with patch.object(integraciones, "descargar") as bajar:
        assert telegram.descargar_archivo("id") is None

    bajar.assert_not_called()


class _Archivo(BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()


def test_descargar_devuelve_los_bytes_dentro_del_tope():
    with patch.object(integraciones, "urlopen", return_value=_Archivo(b"12345")):
        assert DESCARGAR_REAL("https://x.test/a.jpg", timeout=1, tope=10) == b"12345"


def test_descargar_rechaza_lo_que_pasa_el_tope():
    with patch.object(integraciones, "urlopen", return_value=_Archivo(b"x" * 11)):
        assert DESCARGAR_REAL("https://x.test/a.jpg", timeout=1, tope=10) is None


def test_descargar_sin_conexión_devuelve_none():
    with patch.object(integraciones, "urlopen", side_effect=OSError("caída")):
        assert DESCARGAR_REAL("https://x.test/a.jpg", timeout=1, tope=10) is None


def test_descargar_rechaza_un_esquema_que_no_es_web():
    with patch.object(integraciones, "urlopen") as abrir:
        assert DESCARGAR_REAL("file:///etc/passwd", timeout=1, tope=10) is None

    abrir.assert_not_called()


def test_la_red_cortada_corta_también_las_descargas():
    assert integraciones.descargar("https://x.test/a.jpg", timeout=1, tope=10) is None
