"""Módulo 19 · los borradores en el chat: `CU-AVI-REB` y lo que se revisó de `CU-AVI-BOR`.

- **Rechazar sí, confirmar nunca** (B-19-008): la vista previa de un borrador trae
  «Rechazar…» y ningún otro botón; un botón firmado con otra acción no hace nada.
- Los nombres de catálogo se comparan sin tildes ni romanizaciones (B-01-023).
- Los parecidos: el duplicado exacto, el mismo tomo en otra edición y el borrador
  abierto repetido (B-19-010).
- Lo no editorial no se carga como borrador (B-19-009).
"""

from decimal import Decimal
from io import BytesIO
from unittest.mock import patch

import pytest
from django.core.files.base import ContentFile
from PIL import Image

from apps.accounts.models import Usuario
from apps.accounts.tests.factories import UsuarioFactory
from apps.avisos import bot, telegram
from apps.avisos.models import VinculoTelegram
from apps.avisos.tests.telegram_falso import TOKEN, telegram_falso
from apps.catalog import borradores, revisiones, services
from apps.catalog.models import BorradorProducto, Producto
from apps.catalog.tests.factories import (
    EditorialFactory,
    ProductoFactory,
    TipoFactory,
    formato_solo_para,
)
from apps.core import integraciones, llm
from apps.core.models import RegistroAuditoria

pytestmark = pytest.mark.django_db

CHAT = 4242
PEDIR_REAL = integraciones.pedir


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
def manga():
    return TipoFactory(nombre="Manga", usa_formato=True)


@pytest.fixture
def tankobon(manga):
    return formato_solo_para("Tankōbon", manga)


@pytest.fixture
def ivrea():
    return EditorialFactory(nombre="Ivrea")


def borrador(**cambios):
    datos = {"titulo": "Sakamoto Days", "volumen": 24, "precio": Decimal("15900")}
    datos.update(cambios)
    return BorradorProducto.objects.create(**datos)


def mensaje(texto=None, chat=CHAT, **extra):
    cuerpo = {"message_id": 1, "chat": {"id": chat, "type": "private"}, "from": {}}
    if texto is not None:
        cuerpo["text"] = texto
    cuerpo.update(extra)
    return {"update_id": 1, "message": cuerpo}


def boton(accion, pk, chat=CHAT, extra="", firma=None):
    datos = f"{accion}:{pk}:{extra}"
    firma = firma or telegram.firmar(datos, chat)
    return {
        "update_id": 2,
        "callback_query": {
            "id": "consulta",
            "data": f"{datos}:{firma}",
            "message": {"message_id": 9, "chat": {"id": chat, "type": "private"}},
        },
    }


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


def modelo(datos):
    return patch.object(llm, "pedir_json", return_value=llm.RespuestaDelModelo(datos=datos))


def con_portada(un_borrador):
    imagen = BytesIO()
    Image.new("RGB", (600, 900), "blue").save(imagen, "PNG")
    un_borrador.portada.save("prueba.png", ContentFile(imagen.getvalue()), save=True)
    return un_borrador


def acciones(cuerpo):
    marcado = cuerpo.get("reply_markup") or {}
    return [
        b["callback_data"].split(":")[0]
        for fila in marcado.get("inline_keyboard", [])
        for b in fila
    ]


# ---------------------------------------------------------------------------
# B-01-023 · los nombres de catálogo
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("escrito", "catalogo"),
    [
        ("Tankobon", "Tankōbon"),
        ("tankoubon", "Tankōbon"),
        ("Tanko-bon", "Tankōbon"),
        ("TAPA DURA", "Tapa dura"),
        ("Rustica", "Rústica"),
        ("b 6", "B6"),
    ],
)
def test_un_nombre_de_catálogo_se_reconoce_como_se_escriba(escrito, catalogo):
    assert services.nombre_comparable(escrito) == services.nombre_comparable(catalogo)


@pytest.mark.parametrize(("uno", "otro"), [("B6", "A5"), ("Deluxe", "Kanzenban"), ("Grapa", "")])
def test_nombres_distintos_siguen_distintos(uno, otro):
    assert services.nombre_comparable(uno) != services.nombre_comparable(otro)


def test_el_formato_sin_tilde_resuelve_el_del_catálogo(manga, tankobon):
    assert borradores._resolver_formato("Tankobon", manga) == tankobon


def test_el_formato_de_otro_tipo_sigue_sin_resolverse(tankobon):
    comic = TipoFactory(nombre="Cómic", usa_formato=True)

    assert borradores._resolver_formato("Tankobon", comic) is None


def test_cargar_con_el_tipo_y_el_formato_sin_tilde(vinculado, ivrea, manga, tankobon, falso):
    datos = leido(
        editorial="Ivrea", tipo="manga", titulo="Sakamoto Days", volumen="24", formato="Tankobon"
    )

    with modelo(datos):
        bot.procesar(mensaje("/cargar Sakamoto Days 24, Ivrea, manga tankobon"))

    nuevo = BorradorProducto.objects.get()
    assert nuevo.tipo == manga and nuevo.formato == tankobon
    assert not any("Formato descartado" in r for r in nuevo.reparos)


def test_un_tipo_que_no_existe_queda_con_un_reparo(vinculado, ivrea, falso):
    with modelo(leido(editorial="Ivrea", tipo="Manhwa", titulo="Solo Leveling", volumen="1")):
        bot.procesar(mensaje("/cargar Solo Leveling 1 manhwa"))

    assert any("Manhwa" in r for r in BorradorProducto.objects.get().reparos)


# ---------------------------------------------------------------------------
# B-19-010 · la editorial por la serie, y los parecidos
# ---------------------------------------------------------------------------


def test_sin_editorial_la_toma_de_la_serie(vinculado, ivrea, manga, tankobon, falso):
    ProductoFactory(titulo="Agencia Del Amor", volumen=4, editorial=ivrea, tipo=manga)

    with modelo(leido(titulo="Agencia del amor", volumen="5")):
        bot.procesar(mensaje("/cargar Agencia del amor 5"))

    nuevo = BorradorProducto.objects.get()
    assert nuevo.editorial == ivrea
    assert nuevo.tipo == manga
    assert nuevo.reparos == []


def test_una_editorial_que_no_existe_cede_a_la_de_la_serie_con_un_reparo(vinculado, ivrea, falso):
    ProductoFactory(titulo="Agencia Del Amor", volumen=4, editorial=ivrea)

    with modelo(leido(editorial="Nacional", titulo="Agencia del Amor", volumen="5")):
        bot.procesar(mensaje("/cargar Agencia del Amor 5 nacional"))

    nuevo = BorradorProducto.objects.get()
    assert nuevo.editorial == ivrea
    assert any("Nacional" in r and "la de la serie" in r for r in nuevo.reparos)


def test_una_serie_en_dos_editoriales_no_elige_ninguna(vinculado, ivrea, falso):
    ProductoFactory(titulo="Akira", volumen=1, editorial=ivrea)
    ProductoFactory(titulo="Akira", volumen=1, editorial=EditorialFactory(nombre="Norma"))

    with modelo(leido(titulo="Akira", volumen="2")):
        bot.procesar(mensaje("/cargar Akira 2"))

    assert BorradorProducto.objects.get().editorial is None


def test_el_duplicado_por_isbn_se_ve_aunque_falte_el_formato(ivrea):
    existente = ProductoFactory(titulo="Berserk", volumen=5, isbn="9789878341910", editorial=ivrea)

    parecidos = services.parecidos_al_borrador(borrador(titulo="Otro título", isbn="9789878341910"))

    assert parecidos.producto == existente


def test_el_mismo_tomo_en_otra_edición_es_un_parecido(ivrea):
    existente = ProductoFactory(titulo="Frieren: Más allá", volumen=3, editorial=ivrea)
    ProductoFactory(titulo="Frieren: Más allá", volumen=4, editorial=ivrea)

    parecidos = services.parecidos_al_borrador(borrador(titulo="frieren: mas alla", volumen=3))

    assert parecidos.producto is None
    assert parecidos.productos == [existente]


def test_otro_borrador_abierto_del_mismo_tomo_es_un_parecido():
    abierto = borrador()
    borrador(estado=BorradorProducto.RECHAZADO)

    parecidos = services.parecidos_al_borrador(borrador(titulo="SAKAMOTO DAYS"))

    assert parecidos.borradores == [abierto]


def test_sin_parecidos_es_falso():
    assert not services.parecidos_al_borrador(borrador())


def test_la_vista_previa_avisa_los_parecidos(vinculado, ivrea, falso):
    ProductoFactory(titulo="Sakamoto Days", volumen=24, editorial=ivrea, codigo="SAK-24")
    otro = borrador()

    bot.mostrar_borrador(CHAT, borrador())

    texto = falso.salidas(CHAT)[-1]
    assert "Parecido en el catálogo" in texto
    assert f"borrador #{otro.pk}" in texto


# ---------------------------------------------------------------------------
# B-19-009 · lo no editorial no es un borrador
# ---------------------------------------------------------------------------


def test_lo_no_editorial_no_crea_un_borrador(vinculado, falso):
    datos = leido(rubro="no_editorial", tipo="Figura", titulo="Figura Nendoroid de Kaneki")

    with modelo(datos):
        bot.procesar(mensaje("/cargar Figura Nendoroid de Kaneki 52000"))

    assert not BorradorProducto.objects.exists()
    texto = falso.textos(CHAT)[-1]
    assert "no editorial" in texto and "Alta no editorial" in texto


def test_un_tipo_no_editorial_tampoco_aunque_el_modelo_diga_editorial(vinculado, falso):
    TipoFactory(nombre="Figura", clase="no_editorial", usa_formato=False)

    with modelo(leido(tipo="figura", titulo="Kaneki")):
        bot.procesar(mensaje("/cargar figura de Kaneki"))

    assert not BorradorProducto.objects.exists()
    assert "(Figura)" in falso.textos(CHAT)[-1]


# ---------------------------------------------------------------------------
# CU-AVI-REB · la vista previa y el rechazo
# ---------------------------------------------------------------------------


def test_cargar_contesta_con_la_vista_previa_y_rechazar(vinculado, ivrea, falso):
    with modelo(leido(editorial="Ivrea", titulo="Berserk", volumen="5")):
        bot.procesar(mensaje("/cargar Berserk 5"))

    ultimo = falso.mensajes(CHAT)[-1]
    assert "Quedó este borrador" in ultimo["text"]
    assert acciones(ultimo) == ["rb"]


def test_borradores_lista_los_abiertos_más_nuevos(vinculado, falso):
    for numero in range(1, 8):
        borrador(titulo=f"Serie {numero}", volumen=numero)
    borrador(titulo="Rechazado", estado=BorradorProducto.RECHAZADO)

    bot.procesar(mensaje("/borradores"))

    salidas = falso.salidas(CHAT)
    assert "7 borrador(es) para revisar" in salidas[0]
    assert "se confirman en la web" in salidas[0]
    assert len(salidas) == 1 + bot.BORRADORES_POR_CONSULTA
    assert "Serie 7" in salidas[1]
    assert not any("Rechazado" in s for s in salidas)


def test_borradores_filtra_por_título_sin_tildes(vinculado, falso):
    borrador(titulo="Pokémon Adventures", volumen=1)
    borrador(titulo="Berserk", volumen=1)

    bot.procesar(mensaje("/borradores pokemon"))

    salidas = falso.salidas(CHAT)
    assert "1 borrador(es)" in salidas[0] and "Pokémon" in salidas[1]


def test_borradores_sin_nada_lo_dice(vinculado, falso):
    bot.procesar(mensaje("/borradores"))

    assert "No hay borradores para revisar" in falso.textos(CHAT)[-1]


def test_con_portada_la_vista_previa_es_una_foto_chica(vinculado, falso):
    con_portada(borrador())

    bot.procesar(mensaje("/borradores"))

    (foto,) = falso.fotos(CHAT)
    nombre, contenido, tipo = foto["photo"]
    assert tipo == "image/jpeg"
    assert max(Image.open(BytesIO(contenido)).size) <= 800
    assert "Sakamoto Days" in foto["caption"]
    assert acciones(foto) == ["rb"]


def test_si_la_foto_no_sale_manda_la_ficha_sola(vinculado, falso):
    nuevo = con_portada(borrador())

    with patch.object(telegram, "enviar_foto", return_value=None):
        bot.mostrar_borrador(CHAT, nuevo)

    assert acciones(falso.mensajes(CHAT)[-1]) == ["rb"]


def test_un_borrador_cerrado_no_ofrece_rechazar(vinculado, falso):
    bot.mostrar_borrador(CHAT, borrador(estado=BorradorProducto.CONFIRMADO))

    assert acciones(falso.mensajes(CHAT)[-1]) == []


def test_rechazar_ofrece_los_motivos(vinculado, falso):
    nuevo = borrador()

    bot.procesar(boton("rb", nuevo.pk))

    menu = falso.mensajes(CHAT)[-1]
    assert f"borrador #{nuevo.pk}" in menu["text"]
    assert acciones(menu) == ["rm"] * len(bot.MOTIVOS_DE_RECHAZO) + ["ro"]


def test_rechazar_con_un_motivo_rápido_rechaza_y_audita(vinculado, falso):
    nuevo = borrador()

    bot.procesar(boton("rm", nuevo.pk, extra="1"))

    nuevo.refresh_from_db()
    assert nuevo.estado == BorradorProducto.RECHAZADO
    assert nuevo.motivo_rechazo == bot.MOTIVOS_DE_RECHAZO[1]
    assert nuevo.resuelto_por == vinculado
    assert RegistroAuditoria.objects.filter(
        accion=RegistroAuditoria.BORRADOR_RECHAZADO,
        actor=vinculado,
        detalle__endswith="(desde Telegram)",
    ).exists()
    assert not Producto.objects.exists()
    assert "Se rechazó" in falso.textos(CHAT)[-1]


def test_rechazar_con_otro_motivo_lo_toma_de_la_respuesta(vinculado, falso):
    nuevo = borrador()

    bot.procesar(boton("ro", nuevo.pk))
    pregunta = falso.textos(CHAT)[-1]
    bot.procesar(mensaje("Es una reimpresión", reply_to_message={"text": pregunta}))

    nuevo.refresh_from_db()
    assert nuevo.estado == BorradorProducto.RECHAZADO
    assert nuevo.motivo_rechazo == "Es una reimpresión"


def test_responder_a_la_vista_previa_no_rechaza(vinculado, falso):
    nuevo = borrador()
    bot.mostrar_borrador(CHAT, nuevo)

    with patch.object(llm, "pedir_json", return_value=None):
        bot.procesar(mensaje("lindo", reply_to_message={"text": falso.textos(CHAT)[-1]}))

    nuevo.refresh_from_db()
    assert nuevo.esta_abierto


def test_rechazar_sin_motivo_lo_pide(vinculado, falso):
    nuevo = borrador()

    bot.procesar(mensaje("  ", reply_to_message={"text": f"para rechazar el borrador #{nuevo.pk}"}))

    nuevo.refresh_from_db()
    assert nuevo.esta_abierto
    assert "obligatorio" in falso.textos(CHAT)[-1]


def test_rechazar_lo_ya_resuelto_lo_dice(vinculado, falso):
    nuevo = borrador()
    revisiones.rechazar(nuevo, actor=vinculado, motivo="Desde la web")

    bot.procesar(boton("rm", nuevo.pk, extra="0"))

    nuevo.refresh_from_db()
    assert nuevo.motivo_rechazo == "Desde la web"
    assert "ya no está abierto" in falso.textos(CHAT)[-1]


def test_rechazar_un_borrador_que_no_existe(vinculado, falso):
    bot.procesar(boton("rm", 99999, extra="0"))

    assert "ya no existe" in falso.textos(CHAT)[-1]


def test_el_rechazo_desde_la_web_no_nombra_canal(administrador):
    nuevo = borrador()

    revisiones.rechazar(nuevo, actor=administrador, motivo="Repetido")

    detalle = RegistroAuditoria.objects.get(accion=RegistroAuditoria.BORRADOR_RECHAZADO).detalle
    assert "Telegram" not in detalle


# Foco reforzado: control de acceso. Confirmar no existe por el chat.


@pytest.mark.parametrize("accion", ["ok", "cf", "ap"])
def test_ningún_botón_confirma_un_borrador(vinculado, falso, accion):
    nuevo = borrador()

    bot.procesar(boton(accion, nuevo.pk))

    nuevo.refresh_from_db()
    assert nuevo.esta_abierto
    assert not Producto.objects.exists()


def test_un_botón_de_rechazo_armado_a_mano_no_hace_nada(vinculado, falso):
    nuevo = borrador()

    bot.procesar(boton("rm", nuevo.pk, extra="0", firma="000000000000"))

    nuevo.refresh_from_db()
    assert nuevo.esta_abierto


def test_el_botón_de_rechazo_de_otro_chat_no_sirve(vinculado, falso):
    nuevo = borrador()
    ajeno = boton("rm", nuevo.pk, chat=777, extra="0")
    ajeno["callback_query"]["message"]["chat"]["id"] = CHAT

    bot.procesar(ajeno)

    nuevo.refresh_from_db()
    assert nuevo.esta_abierto


def test_un_administrador_dado_de_baja_no_rechaza(vinculado, falso):
    UsuarioFactory(rol=Usuario.ADMINISTRADOR)
    Usuario.objects.filter(pk=vinculado.pk).update(estado=Usuario.INACTIVO)
    nuevo = borrador()

    bot.procesar(boton("rm", nuevo.pk, extra="0"))
    bot.procesar(mensaje("x", reply_to_message={"text": f"rechazar el borrador #{nuevo.pk}"}))
    bot.procesar(mensaje("/borradores"))

    nuevo.refresh_from_db()
    assert nuevo.esta_abierto
    assert not falso.fotos(CHAT)


def test_un_chat_sin_vínculo_no_ve_los_borradores(falso):
    borrador()

    bot.procesar(mensaje("/borradores"))

    assert "no está vinculado" in falso.textos(CHAT)[-1]


def test_una_pregunta_por_los_borradores(vinculado, falso):
    borrador()

    with modelo({"consulta": "borradores", "texto": "sakamoto"}):
        bot.procesar(mensaje("¿qué borradores de sakamoto hay?"))

    assert "1 borrador(es) para revisar con «sakamoto»" in falso.salidas(CHAT)[0]


# ---------------------------------------------------------------------------
# La foto por la única puerta: formulario multiparte
# ---------------------------------------------------------------------------


class _Respuesta(BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()


def test_la_foto_sale_como_formulario_multiparte_por_la_puerta():
    with patch.object(
        integraciones, "urlopen", return_value=_Respuesta(b'{"ok": true, "result": {}}')
    ) as abrir:
        respuesta = PEDIR_REAL(
            "https://api.telegram.org/botX/sendPhoto",
            timeout=1,
            metodo="POST",
            cuerpo={"chat_id": 5, "reply_markup": {"inline_keyboard": []}},
            archivos={"photo": ("portada.jpg", b"\xff\xd8JPEG", "image/jpeg")},
        )

    assert respuesta.datos == {"ok": True, "result": {}}
    pedido = abrir.call_args.args[0]
    assert pedido.get_header("Content-type").startswith("multipart/form-data; boundary=")
    assert b'name="photo"; filename="portada.jpg"' in pedido.data
    assert b"\xff\xd8JPEG" in pedido.data
    assert b'{"inline_keyboard": []}' in pedido.data


def test_enviar_foto_pide_send_photo(falso):
    telegram.enviar_foto(CHAT, b"jpeg", "<b>hola</b>", botones=[[{"text": "x"}]])

    (foto,) = falso.fotos(CHAT)
    assert foto["caption"] == "<b>hola</b>" and foto["parse_mode"] == "HTML"
    assert foto["photo"] == ("portada.jpg", b"jpeg", "image/jpeg")
