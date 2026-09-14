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

from apps.core import integraciones

logger = logging.getLogger(__name__)

# Motivos por los que no hay respuesta utilizable. Se distinguen porque cada uno
# se resuelve en un lugar distinto: el servicio caído es de infraestructura, la
# respuesta ilegible es del prompt o del modelo elegido.
SIN_SERVICIO = "sin_servicio"
RESPUESTA_ILEGIBLE = "respuesta_ilegible"
# El servicio contestó, y contestó que no: clave inválida, sin crédito, modelo
# inexistente. Es el fallo más probable con un proveedor remoto y el que antes
# se confundía con "está caído", que se arregla en otro lado y esperando.
RECHAZADO = "rechazado"


class RespuestaDelModelo:
    """Lo que devolvió el modelo, o por qué no hay nada.

    No es una excepción a propósito: quien llama está procesando un correo
    dentro de un ciclo y tiene que poder registrar el fallo y seguir con el
    siguiente, que es lo que piden E2 y E3 de CU-ALT-NOV.
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


def _configuracion():
    """Los parámetros vigentes del modelo, de la base y no de `settings`.

    Se lee en cada llamada a propósito: cambiar de proveedor desde la pantalla
    tiene que surtir efecto sin reiniciar el servidor, que es justamente para lo
    que existe la pantalla. Es una consulta a una tabla de una fila.
    """
    from apps.core.models import ConfiguracionSistema

    return ConfiguracionSistema.obtener()


def _credencial(configuracion):
    """La cabecera de autorización, si hay clave que mandar.

    Un servidor local no la pide y algunos rechazan el pedido si llega una
    cabecera vacía, así que se omite en vez de mandar `Bearer ` pelado.
    """
    if not configuracion.llm_api_key:
        return {}
    return {"Authorization": f"Bearer {configuracion.llm_api_key}"}


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
    configuracion = _configuracion()
    cuerpo = {
        "messages": [
            {"role": "system", "content": sistema},
            {"role": "user", "content": usuario},
        ],
        "temperature": float(configuracion.llm_temperatura),
        "stream": False,
    }
    if configuracion.llm_modelo:
        cuerpo["model"] = configuracion.llm_modelo
    if formato:
        cuerpo["response_format"] = {
            "type": "json_schema",
            "json_schema": {"name": "respuesta", "strict": True, "schema": formato},
        }

    arranque = time.perf_counter()
    respuesta = integraciones.pedir(
        configuracion.llm_url,
        timeout=configuracion.llm_timeout,
        metodo="POST",
        cuerpo=cuerpo,
        cabeceras=_credencial(configuracion),
    )
    tardanza = round((time.perf_counter() - arranque) * 1000)

    if not respuesta:
        # `pedir` ya lo registró en el log. Acá se traduce a un motivo que el
        # pipeline pueda mostrarle a una persona — y **se distinguen los dos**:
        # un rechazo del proveedor no se arregla esperando.
        rechazado = getattr(respuesta, "motivo", "") == integraciones.RECHAZADO
        return RespuestaDelModelo(
            error=RECHAZADO if rechazado else SIN_SERVICIO,
            crudo=getattr(respuesta, "detalle", ""),
            milisegundos=tardanza,
        )

    # Algunos proveedores devuelven el fallo **con código 200 y el error en el
    # cuerpo**: el modelo de arriba se cayó, o está sobrecargado. Sin mirarlo, eso
    # sale como "respuesta ilegible" y manda a revisar el prompt, que está bien.
    ajeno = _error_declarado(respuesta.datos)
    if ajeno:
        logger.warning("El proveedor devolvió un error en el cuerpo: %s", ajeno)
        return RespuestaDelModelo(error=RECHAZADO, crudo=ajeno, milisegundos=tardanza)

    texto = _contenido(respuesta.datos)
    if not texto:
        logger.warning("El modelo respondió sin contenido: %s", respuesta.datos)
        return RespuestaDelModelo(
            error=RESPUESTA_ILEGIBLE, crudo=json.dumps(respuesta.datos), milisegundos=tardanza
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


def _error_declarado(respuesta):
    """El mensaje de error que algunos proveedores devuelven con código 200.

    Pasa con los modelos gratuitos hospedados: la pasarela contesta bien y el
    fallo es del modelo de arriba —sobrecargado, caído— y viaja en el cuerpo. Se
    lee para poder decirlo, en vez de reportar una respuesta ilegible y mandar a
    revisar el prompt.
    """
    if not isinstance(respuesta, dict):
        return ""
    error = respuesta.get("error")
    if not error:
        return ""
    if isinstance(error, dict):
        return str(error.get("message") or error)
    return str(error)


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
    # El servicio contestó y contestó que no. Se distingue de `disponible=False`
    # a secas porque se arregla en otro lado: uno es la credencial o la cuenta,
    # el otro es esperar a que el servidor vuelva.
    rechazado: bool = False
    estado_http: int | None = None
    # El modelo que el sistema tiene configurado, y si el servidor lo ofrece.
    # **La lista completa no se muestra**: un proveedor remoto declara cientos y
    # llenar la pantalla con ellos entierra lo único que se vino a mirar.
    modelo_configurado: str = ""

    @property
    def modelo_disponible(self):
        """Si el modelo configurado está entre los que el servidor ofrece.

        Es el diagnóstico que **adelanta** el 404 más común: un identificador mal
        copiado se ve acá, antes de gastar una corrida y recibir un "no endpoints
        found" en medio de un procesamiento.
        """
        if not self.modelo_configurado:
            return None
        return self.modelo_configurado in self.modelos


def estado():
    """Pregunta si el servicio está en línea y qué modelos tiene cargados.

    Es un `GET` barato al catálogo de modelos, no una generación: contesta en
    milisegundos y no gasta nada. Sirve para separar los dos motivos por los que
    una extracción puede fallar —el servicio no está, o el servicio está y la
    respuesta no se pudo interpretar— que se arreglan en lugares distintos.
    """
    configuracion = _configuracion()
    url = _url_de_modelos(configuracion.llm_url)
    if not url:
        return EstadoDelServicio(
            detalle=(
                "No se pudo deducir la dirección del catálogo de modelos desde "
                f"«{configuracion.llm_url}»: no parece una API compatible con la de OpenAI."
            )
        )

    arranque = time.perf_counter()
    # **Con la credencial.** Antes iba sin ella, y contra un proveedor que la
    # exige en el catálogo de modelos la pantalla informaba "caído" con el
    # servicio perfectamente vivo — el diagnóstico equivocado que esta pantalla
    # existe para evitar.
    respuesta = integraciones.pedir(
        url, timeout=TIMEOUT_ESTADO, cabeceras=_credencial(configuracion)
    )
    tardanza = round((time.perf_counter() - arranque) * 1000)

    if getattr(respuesta, "motivo", "") == integraciones.RECHAZADO:
        return EstadoDelServicio(
            url=url,
            milisegundos=tardanza,
            rechazado=True,
            estado_http=respuesta.estado_http,
            detalle=_motivo_del_rechazo(respuesta, configuracion),
        )

    if not respuesta:
        return EstadoDelServicio(
            url=url,
            milisegundos=tardanza,
            detalle=(
                "El servicio no respondió. Con un modelo local, verifique que el servidor "
                "esté corriendo en esa dirección; con uno remoto, la conexión a internet."
            ),
        )

    modelos = [
        entrada.get("id", "")
        for entrada in (respuesta.datos or {}).get("data", [])
        if isinstance(entrada, dict) and entrada.get("id")
    ]
    return EstadoDelServicio(
        disponible=True,
        modelos=modelos,
        modelo_configurado=configuracion.llm_modelo,
        milisegundos=tardanza,
        url=url,
        detalle="" if modelos else "El servicio responde pero no declara ningún modelo cargado.",
    )


def _motivo_del_rechazo(respuesta, configuracion):
    """Qué decirle a quien mira la pantalla cuando el proveedor dice que no.

    Los tres casos se arreglan en lugares distintos, y el número solo no lo
    dice: sin traducirlos, la pantalla muestra "401" y quien la mira tiene que
    salir a buscar qué significa.
    """
    if respuesta.no_autorizado:
        return (
            "El proveedor rechazó la credencial. Revise la clave de la API en "
            "Parámetros globales; puede estar vencida o mal copiada."
        )
    if respuesta.sin_credito:
        return "La cuenta del proveedor no tiene crédito disponible."
    if respuesta.estado_http == 429:
        return (
            "El proveedor está limitando los pedidos. Es lo habitual en los modelos "
            "gratuitos: espere unos minutos o elija otro modelo."
        )
    detalle = respuesta.detalle or f"Código {respuesta.estado_http}."
    if configuracion.usa_modelo_remoto:
        return f"El proveedor rechazó el pedido: {detalle}"
    return f"El servidor rechazó el pedido: {detalle}"


def _url_de_modelos(url_del_chat):
    """La dirección del catálogo, deducida de la del chat.

    Se deduce en vez de pedir otra variable de configuración: las dos rutas son
    del mismo servidor y obligar a configurar las dos es una oportunidad más de
    que queden apuntando a lugares distintos. Funciona igual con LM Studio
    (`.../v1/chat/completions`) que con un proveedor remoto, porque `/v1/` es
    parte de la convención de la API que los dos implementan.
    """
    corte = url_del_chat.rfind("/v1/")
    return url_del_chat[:corte] + "/v1/models" if corte != -1 else ""
