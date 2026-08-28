"""La única puerta de salida HTTP del proyecto, y la política de los catálogos.

Son dos cosas y conviene leerlas por separado.

**`pedir` es la puerta.** Todo lo que sale a la red pasa por ahí: los catálogos
públicos, la tabla de cotizaciones y el modelo de lenguaje. Que sea una sola no
es prolijidad — es lo que hace que la fixture `sin_red` del `conftest.py` raíz
pueda cortar la red entera parcheando **un** punto. Una integración que saliera
por su cuenta no quedaría cubierta, y el primer test distraído saldría a
internet en el CI sin que nadie se entere.

Ojo con un caso que no es obvio: **también hay que cortar `localhost`**. El
modelo de lenguaje corre en la máquina del desarrollador, así que un test que lo
llamara de verdad andaría acá y se colgaría hasta el timeout en el CI, donde ese
servicio no existe.

**Y abajo está la política de catálogos.** Todo catálogo que venga de afuera
—provincias, localidades, códigos de país— se resuelve igual, en tres capas:

1. **Caché**: un catálogo que cambia una vez por década no se pide en cada
   carga de pantalla. Consultar un servicio gratuito por cada visitante es
   maltratarlo.
2. **La API**, cuando la caché está vacía.
3. **Respaldo local**, cuando la API no contesta.

La tercera capa es la que decide el diseño. Un formulario de registro que se
cae porque un servicio ajeno está lento es peor que uno con un catálogo de hace
un mes: que el alta de clientes dependa de que un tercero esté en línea no es
una opción.

Los archivos de respaldo se **generan** con los comandos `sincronizar_*`; no se
escriben a mano. La fuente de verdad sigue siendo la API, el archivo es su
última foto.
"""

import json
import logging
from urllib.error import URLError
from urllib.request import Request, urlopen

from django.core.cache import cache

logger = logging.getLogger(__name__)

# Identificarse es de buena educación con un servicio gratuito, y además es
# necesario: varios rechazan con 403 el "Python-urllib/3.x" que manda `urlopen`
# por omisión, porque es la firma típica de un raspador anónimo.
#
# **Sin tildes, a propósito.** Un valor de cabecera HTTP se transmite en ASCII;
# los caracteres fuera de ese rango quedaron obsoletos en la especificación y
# cada intermediario hace lo que quiere con ellos. Cloudflare —que está delante
# de buena parte de las APIs públicas— directamente contesta 403 a una cabecera
# con bytes no ASCII, y el error no dice nada de eso: llega como un rechazo
# genérico y se pierde tiempo buscándolo en el lugar equivocado.
CABECERAS = {
    "User-Agent": "Longbox/1.0 (sistema de gestion para comiqueria; proyecto academico)",
    "Accept": "application/json",
}

# Se suma solo cuando hay cuerpo: declarar un tipo de contenido en un GET sin
# cuerpo confunde a algunos servidores y no aporta nada.
CABECERA_JSON = {"Content-Type": "application/json"}

# Cuando la API falla se cachea igual el resultado del respaldo, pero por poco
# rato: si el servicio vuelve en cinco minutos, no queremos seguir un día
# entero sirviendo la foto vieja.
CACHE_TRAS_FALLA_SEGUNDOS = 5 * 60


def pedir(url, *, timeout, metodo="GET", cuerpo=None, cabeceras=None):
    """Un pedido HTTP que devuelve JSON, o `None` si no se pudo.

    **Es el único lugar del proyecto que abre una conexión**, y por eso acepta
    método, cuerpo y cabeceras en vez de resolver solo el GET que necesitaban
    los catálogos: cuando apareció el modelo de lenguaje —que es un POST con
    credencial— la alternativa era abrir una segunda puerta, y con dos puertas
    la fixture que corta la red deja de ser confiable.

    **Nunca propaga la excepción.** Quien llama tiene un respaldo, o sabe qué
    hacer con un `None`: una pantalla que se cae porque un servicio ajeno está
    lento es peor que una con el catálogo de hace un mes. El problema se
    registra en el log, que es donde corresponde enterarse.

    Usa `urlopen` de la biblioteca estándar: no hace falta sumar `requests` al
    proyecto para un puñado de pedidos.
    """
    datos = None
    propias = dict(cabeceras or {})
    if cuerpo is not None:
        datos = json.dumps(cuerpo).encode("utf-8")
        propias = {**CABECERA_JSON, **propias}
    pedido = Request(  # noqa: S310
        url,
        data=datos,
        method=metodo,
        headers={**CABECERAS, **propias},
    )
    try:
        with urlopen(pedido, timeout=timeout) as respuesta:  # noqa: S310
            return json.loads(respuesta.read())
    except (URLError, TimeoutError, ValueError, OSError) as error:
        logger.warning("El servicio externo no respondió (%s): %s", url, error)
        return None


def pedir_json(url, timeout):
    """Un GET, que es lo que necesitan los catálogos. Envoltorio de `pedir`."""
    return pedir(url, timeout=timeout)


def leer_respaldo(ruta):
    try:
        return json.loads(ruta.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        logger.error("No se pudo leer el respaldo en %s", ruta)
        return {}


def guardar_respaldo(ruta, datos):
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text(json.dumps(datos, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def obtener_con_respaldo(clave_cache, descargar, ruta_respaldo, clave_respaldo, vigencia):
    """Las tres capas, en orden. Devuelve siempre algo con lo que trabajar."""
    valor = cache.get(clave_cache)
    if valor is not None:
        return valor

    valor = descargar()
    if valor:
        cache.set(clave_cache, valor, vigencia)
        return valor

    valor = leer_respaldo(ruta_respaldo).get(clave_respaldo, [])
    cache.set(clave_cache, valor, CACHE_TRAS_FALLA_SEGUNDOS)
    return valor
