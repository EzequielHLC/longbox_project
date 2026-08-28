"""Cliente del modelo de lenguaje. Le pide JSON y devuelve JSON, o nada.

Está en `core` y no en `suppliers` porque acá no hay ninguna regla del negocio:
esto sabe hablar con un servidor compatible con la API de OpenAI y **nada más**.
El prompt de novedades, el esquema que se espera y su validación viven en
`apps/suppliers/extraccion.py`, que es donde están las reglas.

Es la misma división que ya tienen `integraciones.py` —el transporte— y
`georef.py` o `cotizaciones.py` —lo que cada uno hace con él—. Sirve para lo
mismo: cuando aparezca una segunda cosa que pedirle al modelo (clasificar un
aviso de demora, por ejemplo), va a reusar este archivo entero y escribir solo
su prompt.

**Sale por `integraciones.pedir`**, la única puerta HTTP del proyecto, para
quedar cubierto por la fixture que corta la red en los tests. Ver la nota de ese
archivo sobre por qué también hay que cortar `localhost`.
"""

import json
import logging
import time
from dataclasses import dataclass, field

from django.conf import settings

from apps.core import integraciones

logger = logging.getLogger(__name__)

# Motivos por los que no hay respuesta utilizable. Se distinguen porque cada uno
# se resuelve en un lugar distinto: el servicio caído es de infraestructura, la
# respuesta ilegible es del prompt o del modelo elegido.
SIN_SERVICIO = "sin_servicio"
RESPUESTA_ILEGIBLE = "respuesta_ilegible"


class RespuestaDelModelo:
    """Lo que devolvió el modelo, o por qué no hay nada.

    No es una excepción a propósito: quien llama está procesando un correo
    dentro de un ciclo y tiene que poder registrar el fallo y seguir con el
    siguiente, que es lo que piden E2 y E3 de CU-04.
    """

    def __init__(self, datos=None, error="", crudo="", milisegundos=0):
        self.datos = datos
        self.error = error
        # El texto tal como vino. Se conserva incluso cuando no se pudo leer:
        # es lo único con lo que se puede entender por qué falló, y sin él
        # ajustar el prompt es adivinar.
        self.crudo = crudo
        # Cuánto tardó de punta a punta. Con un modelo local la diferencia entre
        # dos segundos y dos minutos decide si el pipeline puede correr en una
        # tarea corta o necesita una cola de verdad, así que es un dato del
        # sistema y no una curiosidad.
        self.milisegundos = milisegundos

    def __bool__(self):
        return self.datos is not None


def pedir_json(sistema, usuario, *, formato=None):
    """Le pide al modelo una respuesta en JSON y la devuelve ya interpretada.

    `sistema` son las instrucciones —qué es, qué tiene que hacer, qué no— y
    `usuario` el material concreto sobre el que trabajar. Van separados porque
    es la separación que el modelo entiende: mezclarlos hace que el contenido de
    un correo pueda leerse como una instrucción más.

    `formato` es el esquema JSON que se le exige a la respuesta. Cuando el
    servidor lo soporta —LM Studio sí— deja de ser una sugerencia del prompt y
    pasa a ser una garantía del decodificador: el modelo **no puede** emitir
    algo que no encaje. Es la diferencia entre validar y prevenir, y ahorra la
    mitad de los reintentos.
    """
    cuerpo = {
        "messages": [
            {"role": "system", "content": sistema},
            {"role": "user", "content": usuario},
        ],
        "temperature": float(settings.LLM_TEMPERATURA),
        "stream": False,
    }
    if settings.LLM_MODELO:
        cuerpo["model"] = settings.LLM_MODELO
    if formato:
        cuerpo["response_format"] = {
            "type": "json_schema",
            "json_schema": {"name": "respuesta", "strict": True, "schema": formato},
        }

    arranque = time.perf_counter()
    respuesta = integraciones.pedir(
        settings.LLM_URL,
        timeout=settings.LLM_TIMEOUT,
        metodo="POST",
        cuerpo=cuerpo,
        cabeceras={"Authorization": f"Bearer {settings.LLM_API_KEY}"},
    )
    tardanza = round((time.perf_counter() - arranque) * 1000)

    if respuesta is None:
        # `pedir` ya lo registró en el log. Acá solo se traduce a un motivo que
        # el pipeline pueda mostrarle a una persona.
        return RespuestaDelModelo(error=SIN_SERVICIO, milisegundos=tardanza)

    texto = _contenido(respuesta)
    if not texto:
        logger.warning("El modelo respondió sin contenido: %s", respuesta)
        return RespuestaDelModelo(
            error=RESPUESTA_ILEGIBLE, crudo=json.dumps(respuesta), milisegundos=tardanza
        )

    try:
        return RespuestaDelModelo(datos=json.loads(texto), crudo=texto, milisegundos=tardanza)
    except ValueError:
        # Pasa cuando el modelo envuelve el JSON en prosa o en un bloque de
        # código. No se intenta rescatarlo con expresiones regulares: eso
        # esconde un prompt que hay que arreglar detrás de un parche que
        # funciona a veces.
        logger.warning("El modelo no devolvió JSON legible: %.200s", texto)
        return RespuestaDelModelo(error=RESPUESTA_ILEGIBLE, crudo=texto, milisegundos=tardanza)


def _contenido(respuesta):
    """El texto de la respuesta, en el formato que devuelve la API de OpenAI.

    Se navega con cuidado y sin `KeyError`: la respuesta viene de afuera, y un
    servidor que conteste distinto no puede tumbar el ciclo con una excepción.

    **Los modelos de razonamiento dejan la respuesta en otro campo.** Con
    `qwen3.5` corriendo en LM Studio, el JSON pedido llegó entero en
    `reasoning_content` y `content` vino vacío — la extracción era correcta, los
    tres productos estaban bien, y el pipeline la descartaba igual. Se cae a ese
    campo **solo si el principal está vacío**: cuando los dos vienen, el que
    manda es `content`, que es donde está la respuesta y no el razonamiento.

    Esto no contradice la regla de no rescatar JSON de la prosa con expresiones
    regulares. Acá no se adivina nada: se lee otro campo declarado de la misma
    respuesta.
    """
    opciones = respuesta.get("choices") or []
    if not opciones:
        return ""
    mensaje = opciones[0].get("message") or {}
    return (mensaje.get("content") or mensaje.get("reasoning_content") or "").strip()


# El estado se consulta **con un timeout corto**, no con el del modelo. Son dos
# cosas distintas: generar puede tardar minutos y está bien, pero preguntar si
# el servicio está vivo tiene que contestar enseguida o no contestar. Con el
# timeout largo, una pantalla de diagnóstico contra un servicio caído quedaría
# cargando cinco minutos, que es la peor forma de enterarse de que está caído.
TIMEOUT_ESTADO = 4


@dataclass
class EstadoDelServicio:
    """Si el modelo está disponible y con qué. Para la pantalla de diagnóstico."""

    disponible: bool = False
    modelos: list = field(default_factory=list)
    milisegundos: int = 0
    url: str = ""
    detalle: str = ""


def estado():
    """Pregunta si el servicio está en línea y qué modelos tiene cargados.

    Es un `GET` barato al catálogo de modelos, no una generación: contesta en
    milisegundos y no gasta nada. Sirve para separar los dos motivos por los que
    una extracción puede fallar —el servicio no está, o el servicio está y la
    respuesta no se pudo interpretar— que se arreglan en lugares distintos.
    """
    url = _url_de_modelos()
    if not url:
        return EstadoDelServicio(
            detalle=(
                "No se pudo deducir la dirección del catálogo de modelos desde "
                f"«{settings.LLM_URL}»: no parece una API compatible con la de OpenAI."
            )
        )

    arranque = time.perf_counter()
    respuesta = integraciones.pedir(url, timeout=TIMEOUT_ESTADO)
    tardanza = round((time.perf_counter() - arranque) * 1000)

    if respuesta is None:
        return EstadoDelServicio(
            url=url,
            milisegundos=tardanza,
            detalle="El servicio no respondió. Verifique que esté corriendo y en esa dirección.",
        )

    modelos = [
        entrada.get("id", "")
        for entrada in respuesta.get("data", [])
        if isinstance(entrada, dict) and entrada.get("id")
    ]
    return EstadoDelServicio(
        disponible=True,
        modelos=modelos,
        milisegundos=tardanza,
        url=url,
        detalle="" if modelos else "El servicio responde pero no declara ningún modelo cargado.",
    )


def _url_de_modelos():
    """La dirección del catálogo, deducida de la del chat.

    Se deduce en vez de pedir otra variable de entorno: las dos rutas son del
    mismo servidor y obligar a configurar las dos es una oportunidad más de que
    queden apuntando a lugares distintos.
    """
    corte = settings.LLM_URL.rfind("/v1/")
    return settings.LLM_URL[:corte] + "/v1/models" if corte != -1 else ""
