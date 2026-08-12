"""Política común para consumir catálogos de servicios externos.

Todo catálogo que venga de afuera —provincias, localidades, códigos de país—
se resuelve igual, en tres capas:

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
CABECERAS = {
    "User-Agent": "Longbox/1.0 (sistema de gestión para comiquería; proyecto académico)",
    "Accept": "application/json",
}

# Cuando la API falla se cachea igual el resultado del respaldo, pero por poco
# rato: si el servicio vuelve en cinco minutos, no queremos seguir un día
# entero sirviendo la foto vieja.
CACHE_TRAS_FALLA_SEGUNDOS = 5 * 60


def pedir_json(url, timeout):
    """Un GET a un servicio externo. Devuelve el JSON, o `None` si no se pudo.

    Nunca propaga la excepción: quien llama tiene un respaldo y la pantalla
    tiene que seguir andando. El problema se registra en el log, que es donde
    corresponde enterarse, no en la cara del visitante.

    Usa `urlopen` de la biblioteca estándar: no hace falta sumar `requests` al
    proyecto para un puñado de GET contra endpoints públicos.
    """
    try:
        with urlopen(Request(url, headers=CABECERAS), timeout=timeout) as respuesta:  # noqa: S310
            return json.loads(respuesta.read())
    except (URLError, TimeoutError, ValueError, OSError) as error:
        logger.warning("El servicio externo no respondió (%s): %s", url, error)
        return None


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
