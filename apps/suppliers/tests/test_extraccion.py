"""La extracción del modelo: el prompt, la validación y lo que se guarda.

**Ninguno de estos tests llama al modelo de verdad.** Se parchea
`integraciones.pedir`, que es la única puerta HTTP del proyecto y la misma que
corta la fixture `sin_red`. Eso no es solo por velocidad: el modelo corre en
`localhost`, así que un test que lo llamara andaría en la máquina del
desarrollador —dando una falsa sensación de estar cubierto— y en el CI, donde no
existe, se colgaría hasta el timeout.

Lo que se prueba es la parte que decide si el pipeline es confiable: que un dato
inventado no llegue al catálogo. Un modelo no falla avisando; falla devolviendo
algo con la forma correcta y el contenido equivocado.
"""

import json
from decimal import Decimal
from unittest.mock import patch

import pytest

from apps.core import llm
from apps.suppliers import extraccion, services
from apps.suppliers.models import CorreoProveedor
from apps.suppliers.tests import correos_de_ejemplo as ejemplo
from apps.suppliers.tests.factories import ProveedorFactory

BERSERK = "9789878271583"
BLUE_PERIOD = "9789878274652"

CONFIANZA_ALTA = {
    "isbn": "alta",
    "titulo": "alta",
    "volumen": "alta",
    "formato": "alta",
    "precio": "alta",
}


def producto(**cambios):
    """Un producto tal como lo devolvería el modelo, con lo justo."""
    base = {
        "isbn": BERSERK,
        "titulo": "Berserk Deluxe",
        "volumen": "5",
        "formato": "Tapa dura",
        "precio": "24900",
        "imagen": "tapa001@ivrea.test",
        "confianza": dict(CONFIANZA_ALTA),
    }
    base.update(cambios)
    return base


def respuesta(intencion=extraccion.NOVEDADES, productos=None):
    """La forma exacta en que contesta un servidor compatible con OpenAI."""
    contenido = {"intencion": intencion, "productos": productos or []}
    return {"choices": [{"message": {"content": json.dumps(contenido)}}]}


def contestando(valor):
    """Parchea la puerta HTTP para que el modelo devuelva `valor`."""
    return patch("apps.core.integraciones.pedir", return_value=valor)


# ---------------------------------------------------------------------------
# El camino feliz
# ---------------------------------------------------------------------------


def test_extrae_los_productos_de_un_correo_de_novedades():
    with contestando(respuesta(productos=[producto()])):
        resultado = extraccion.extraer("| contenido |", cids={"tapa001@ivrea.test"})

    assert resultado
    assert resultado.intencion == extraccion.NOVEDADES
    extraido = resultado.productos[0]
    assert extraido.titulo == "Berserk Deluxe"
    assert extraido.volumen == 5
    assert extraido.isbn == BERSERK
    assert extraido.precio == Decimal("24900")
    assert extraido.imagen == "tapa001@ivrea.test"
    assert extraido.reparos == []
    assert extraido.esta_completo


def test_el_resultado_dice_con_que_version_del_prompt_se_extrajo():
    """Un borrador de marzo y otro de junio no son comparables, y cuando algo
    salga raro la primera pregunta va a ser con cuál se hizo."""
    with contestando(respuesta(productos=[producto()])):
        resultado = extraccion.extraer("| contenido |")

    assert resultado.version_prompt == extraccion.VERSION_PROMPT


def test_el_esquema_le_exige_al_servidor_la_forma_de_la_respuesta():
    """Es la primera de las tres defensas: con el esquema declarado, el modelo
    **no puede** emitir algo que no encaje, y la validación deja de tener que
    ocuparse de la estructura."""
    with contestando(respuesta()) as pedir:
        extraccion.extraer("| contenido |")

    cuerpo = pedir.call_args.kwargs["cuerpo"]
    esquema = cuerpo["response_format"]["json_schema"]["schema"]
    assert esquema["required"] == ["intencion", "productos"]
    assert cuerpo["temperature"] == 0.0


def test_el_contenido_del_correo_va_separado_de_las_instrucciones():
    """Mezclarlos haría que el texto de un correo se pueda leer como una
    instrucción más."""
    with contestando(respuesta()) as pedir:
        extraccion.extraer("| una fila del correo |")

    mensajes = pedir.call_args.kwargs["cuerpo"]["messages"]
    assert mensajes[0]["role"] == "system"
    assert mensajes[1] == {"role": "user", "content": "| una fila del correo |"}


# ---------------------------------------------------------------------------
# Clasificación de intención
# ---------------------------------------------------------------------------


def test_un_aviso_de_demora_no_produce_productos():
    """Si el modelo clasificó "demora" y devolvió productos igual, se ignoran:
    mezclar las dos cosas es el error que la clasificación viene a evitar."""
    with contestando(respuesta(intencion=extraccion.DEMORA, productos=[producto()])):
        resultado = extraccion.extraer("Berserk se reprograma para mayo")

    assert resultado.intencion == extraccion.DEMORA
    assert resultado.productos == []


def test_una_intencion_inventada_se_toma_como_otro():
    with contestando(respuesta(intencion="cualquier_cosa", productos=[producto()])):
        resultado = extraccion.extraer("| contenido |")

    assert resultado.intencion == extraccion.OTRO
    assert resultado.productos == []


# ---------------------------------------------------------------------------
# El ISBN: la defensa contra un número inventado
# ---------------------------------------------------------------------------


def test_un_isbn_que_no_verifica_se_descarta_con_su_reparo():
    """Es la defensa que atrapa un ISBN alucinado. Guardarlo sería peor que no
    tenerlo: pasaría a identificar un producto que no existe, y el chequeo de
    duplicados dejaría de encontrar el que sí."""
    with contestando(respuesta(productos=[producto(isbn="9789878271584")])):
        resultado = extraccion.extraer("| contenido |")

    extraido = resultado.productos[0]
    assert extraido.isbn == ""
    assert any("ISBN descartado" in reparo for reparo in extraido.reparos)


def test_un_isbn_con_guiones_se_normaliza():
    with contestando(respuesta(productos=[producto(isbn="978-987-827-158-3")])):
        resultado = extraccion.extraer("| contenido |")

    assert resultado.productos[0].isbn == BERSERK


def test_sin_isbn_no_hay_reparo():
    """No tenerlo es válido; inventarlo no."""
    with contestando(respuesta(productos=[producto(isbn="")])):
        resultado = extraccion.extraer("| contenido |")

    assert resultado.productos[0].isbn == ""
    assert resultado.productos[0].reparos == []


# ---------------------------------------------------------------------------
# La portada: la defensa contra una imagen inventada
# ---------------------------------------------------------------------------


def test_una_portada_que_no_esta_en_el_correo_se_ignora():
    """Sin esta comprobación, el borrador quedaría apuntando a una imagen que no
    existe y el fallo aparecería recién al intentar adjuntarla."""
    with contestando(respuesta(productos=[producto(imagen="inventada@ivrea.test")])):
        resultado = extraccion.extraer("| contenido |", cids={"tapa001@ivrea.test"})

    extraido = resultado.productos[0]
    assert extraido.imagen == ""
    assert any("Portada inexistente" in reparo for reparo in extraido.reparos)


def test_el_marcador_completo_tambien_se_acepta():
    """El modelo a veces devuelve el marcador entero en vez del identificador."""
    with contestando(respuesta(productos=[producto(imagen="[imagen:tapa001@ivrea.test]")])):
        resultado = extraccion.extraer("| contenido |", cids={"tapa001@ivrea.test"})

    assert resultado.productos[0].imagen == "tapa001@ivrea.test"


# ---------------------------------------------------------------------------
# Precio y volumen
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("escrito", "esperado"),
    [("24900", "24900"), ("$24900", "24900"), ("$ 24.900", "24900"), ("24900,50", "24900.50")],
)
def test_el_precio_se_lee_venga_como_venga(escrito, esperado):
    """El prompt lo pide limpio, pero llega con signo y separador de miles igual.
    En Argentina el separador de miles es el punto, así que se saca antes de
    interpretar — leerlo como decimal daría $24,90 en vez de $24.900."""
    with contestando(respuesta(productos=[producto(precio=escrito)])):
        resultado = extraccion.extraer("| contenido |")

    assert resultado.productos[0].precio == Decimal(esperado)


@pytest.mark.parametrize("malo", ["", "consultar", "gratis"])
def test_un_precio_ilegible_deja_el_producto_incompleto(malo):
    with contestando(respuesta(productos=[producto(precio=malo)])):
        resultado = extraccion.extraer("| contenido |")

    extraido = resultado.productos[0]
    assert extraido.precio is None
    assert not extraido.esta_completo


def test_un_precio_en_cero_se_rechaza():
    with contestando(respuesta(productos=[producto(precio="0")])):
        resultado = extraccion.extraer("| contenido |")

    assert resultado.productos[0].precio is None


def test_el_volumen_se_lee_aunque_venga_con_texto():
    with contestando(respuesta(productos=[producto(volumen="Vol. 12")])):
        resultado = extraccion.extraer("| contenido |")

    assert resultado.productos[0].volumen == 12


def test_un_volumen_ilegible_deja_su_reparo():
    """Un tomo único puede venir sin volumen; "primavera" es otra cosa."""
    with contestando(respuesta(productos=[producto(volumen="primavera")])):
        resultado = extraccion.extraer("| contenido |")

    extraido = resultado.productos[0]
    assert extraido.volumen is None
    assert any("Volumen ilegible" in reparo for reparo in extraido.reparos)


def test_un_producto_sin_titulo_lo_dice():
    """Sin título no hay forma de identificarlo, ni siquiera para revisarlo a
    mano en la cola."""
    with contestando(respuesta(productos=[producto(titulo="")])):
        resultado = extraccion.extraer("| contenido |")

    extraido = resultado.productos[0]
    assert not extraido.esta_completo
    assert any("Sin título" in reparo for reparo in extraido.reparos)


def test_el_resumen_cuenta_completos_incompletos_y_con_reparos():
    """Es lo que va al log de auditoría y a la salida del comando: sin eso, la
    única forma de saber cómo salió una pasada es abrir el correo."""
    productos = [producto(), producto(precio=""), producto(isbn="9789878271584")]
    with contestando(respuesta(productos=productos)):
        resultado = extraccion.extraer("| contenido |", cids={"tapa001@ivrea.test"})

    resumen = resultado.resumen
    assert resumen["productos"] == 3
    assert resumen["completos"] == 2
    assert resumen["incompletos"] == 1
    assert resumen["con_reparos"] == 1


def test_se_declara_el_modelo_cuando_esta_configurado(settings):
    """Vacío significa "el que esté cargado", que es lo cómodo con LM Studio;
    contra un servicio remoto hay que nombrarlo."""
    settings.LLM_MODELO = "qwen/qwen3.5-9b"

    with contestando(respuesta()) as pedir:
        extraccion.extraer("| contenido |")

    assert pedir.call_args.kwargs["cuerpo"]["model"] == "qwen/qwen3.5-9b"


# ---------------------------------------------------------------------------
# Confianza
# ---------------------------------------------------------------------------


def test_una_confianza_inventada_se_toma_como_baja():
    """Al alza sería peor: un valor raro leído como "alta" haría que un dato
    dudoso se confirme en lote sin que nadie lo mire (CU-05)."""
    confianza = {**CONFIANZA_ALTA, "precio": "altisima"}
    with contestando(respuesta(productos=[producto(confianza=confianza)])):
        resultado = extraccion.extraer("| contenido |")

    assert resultado.productos[0].confianza["precio"] == "baja"


def test_sin_confianza_declarada_no_rompe():
    with contestando(respuesta(productos=[producto(confianza="no es un objeto")])):
        resultado = extraccion.extraer("| contenido |")

    assert resultado.productos[0].confianza == {}


# ---------------------------------------------------------------------------
# Fallos del servicio — E3 de CU-04
# ---------------------------------------------------------------------------


def test_si_el_servicio_no_responde_no_se_extrae_nada():
    """`pedir` devuelve `None` cuando no hay conexión, y eso tiene que llegar
    como un motivo, no como una excepción: el ciclo sigue con el correo
    siguiente."""
    with contestando(None):
        resultado = extraccion.extraer("| contenido |")

    assert not resultado
    assert resultado.error == llm.SIN_SERVICIO
    assert resultado.productos == []


def test_una_respuesta_que_no_es_json_se_reporta_como_ilegible():
    """Pasa cuando el modelo envuelve el JSON en prosa. No se intenta rescatar
    con expresiones regulares: eso esconde un prompt que hay que arreglar."""
    crudo = {"choices": [{"message": {"content": "Claro! Aca van los productos:"}}]}
    with contestando(crudo):
        resultado = extraccion.extraer("| contenido |")

    assert not resultado
    assert resultado.error == llm.RESPUESTA_ILEGIBLE


def test_un_modelo_de_razonamiento_deja_la_respuesta_en_otro_campo():
    """Caso real, no hipotético: `qwen3.5` en LM Studio devolvió el JSON entero
    en `reasoning_content` con `content` vacío. La extracción era correcta —los
    tres productos estaban bien— y el pipeline la descartaba igual."""
    contenido = json.dumps({"intencion": extraccion.NOVEDADES, "productos": [producto()]})
    crudo = {"choices": [{"message": {"content": "", "reasoning_content": contenido}}]}

    with contestando(crudo):
        resultado = extraccion.extraer("| contenido |", cids={"tapa001@ivrea.test"})

    assert resultado
    assert resultado.productos[0].titulo == "Berserk Deluxe"


def test_si_vienen_los_dos_campos_manda_el_principal():
    """`reasoning_content` es el razonamiento, no la respuesta: solo se usa
    cuando no hay otra cosa."""
    bueno = json.dumps({"intencion": extraccion.NOVEDADES, "productos": [producto()]})
    pensado = json.dumps({"intencion": extraccion.DEMORA, "productos": []})
    crudo = {"choices": [{"message": {"content": bueno, "reasoning_content": pensado}}]}

    with contestando(crudo):
        resultado = extraccion.extraer("| contenido |", cids={"tapa001@ivrea.test"})

    assert resultado.intencion == extraccion.NOVEDADES


def test_una_respuesta_sin_opciones_no_rompe():
    """La respuesta viene de afuera: un servidor que conteste distinto no puede
    tumbar el ciclo con un `KeyError`."""
    with contestando({"error": "modelo no cargado"}):
        resultado = extraccion.extraer("| contenido |")

    assert not resultado
    assert resultado.error == llm.RESPUESTA_ILEGIBLE


def test_el_texto_crudo_se_conserva_aunque_no_se_haya_podido_leer():
    """Es lo único con lo que se puede entender por qué falló; sin él, ajustar
    el prompt es adivinar."""
    crudo = {"choices": [{"message": {"content": "no es json"}}]}
    with contestando(crudo):
        resultado = extraccion.extraer("| contenido |")

    assert resultado.crudo == "no es json"


# ---------------------------------------------------------------------------
# El servicio: qué queda escrito en el correo
# ---------------------------------------------------------------------------


@pytest.fixture
def correo(db):
    ProveedorFactory(correo_comercial="novedades@ivrea.test")
    return services.ingerir(ejemplo.correo_de_novedades()).correo


@pytest.mark.django_db
def test_una_extraccion_exitosa_deja_el_correo_procesado(correo):
    with contestando(respuesta(productos=[producto()])):
        services.extraer_novedades(correo)

    correo.refresh_from_db()
    assert correo.estado == CorreoProveedor.PROCESADO
    assert correo.intencion == extraccion.NOVEDADES
    assert correo.productos_extraidos[0]["titulo"] == "Berserk Deluxe"
    assert correo.version_prompt == extraccion.VERSION_PROMPT


@pytest.mark.django_db
def test_un_correo_que_no_era_de_novedades_igual_queda_procesado(correo):
    """Que resulte no ser de novedades es un resultado válido, no un fallo: es
    justamente lo que la clasificación viene a detectar."""
    with contestando(respuesta(intencion=extraccion.OTRO)):
        services.extraer_novedades(correo)

    correo.refresh_from_db()
    assert correo.estado == CorreoProveedor.PROCESADO
    assert correo.productos_extraidos == []


@pytest.mark.django_db
def test_si_el_servicio_esta_caido_el_correo_queda_fallido(correo):
    with contestando(None):
        services.extraer_novedades(correo)

    correo.refresh_from_db()
    assert correo.estado == CorreoProveedor.FALLIDO
    assert "modelo de lenguaje" in correo.motivo


@pytest.mark.django_db
def test_el_motivo_distingue_el_servicio_caido_de_la_respuesta_ilegible(correo):
    """Se arreglan en lugares distintos: uno es infraestructura, el otro es el
    prompt o el modelo elegido."""
    with contestando({"choices": [{"message": {"content": "no es json"}}]}):
        services.extraer_novedades(correo)

    correo.refresh_from_db()
    assert "no se pudo interpretar" in correo.motivo


@pytest.mark.django_db
def test_las_portadas_del_correo_se_usan_para_validar_la_extraccion(correo):
    """El correo sabe qué imágenes trae, y eso es lo que permite descartar una
    inventada. Sin pasarlas, la comprobación no tendría contra qué comparar."""
    with contestando(respuesta(productos=[producto(imagen="inventada@x.test")])):
        services.extraer_novedades(correo)

    correo.refresh_from_db()
    assert correo.productos_extraidos[0]["imagen"] == ""


@pytest.mark.django_db
def test_reprocesar_pisa_la_extraccion_anterior(correo):
    """Ajustar el prompt y volver a correr tiene que dejar el resultado nuevo,
    no dos resultados conviviendo."""
    with contestando(respuesta(productos=[producto()])):
        services.extraer_novedades(correo)
    with contestando(respuesta(productos=[producto(titulo="Blue Period", isbn=BLUE_PERIOD)])):
        services.extraer_novedades(correo)

    correo.refresh_from_db()
    assert len(correo.productos_extraidos) == 1
    assert correo.productos_extraidos[0]["titulo"] == "Blue Period"


@pytest.mark.django_db
def test_la_ficha_muestra_lo_que_entendio_el_modelo(client_admin, correo):
    """Es el paso siguiente de la misma idea que muestra el contenido extraído:
    cada etapa del pipeline se puede mirar antes de que la próxima gaste algo."""
    from django.urls import reverse

    with contestando(respuesta(productos=[producto(imagen="inventada@x.test")])):
        services.extraer_novedades(correo)

    contenido = client_admin.get(
        reverse("suppliers:correo_detalle", args=[correo.pk])
    ).content.decode()

    assert "Lo que entendió el modelo" in contenido
    assert "Berserk Deluxe" in contenido
    assert BERSERK in contenido
    # Y el reparo, que es lo que avisa que algo se descartó.
    assert "Portada inexistente" in contenido
