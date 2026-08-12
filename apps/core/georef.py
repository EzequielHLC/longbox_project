"""Provincias y localidades desde georef-ar-api, el servicio oficial del Estado.

`https://apis.datos.gob.ar/georef/api` lo publica la Secretaría de Innovación
Pública sobre los datos del INDEC. De ahí salen las provincias y las
localidades, en vez de tenerlas escritas a mano en el código: la lista oficial
es la del Estado, no una copia nuestra que alguien tenga que acordarse de
actualizar.

La política de caché y respaldo está en `apps/core/integraciones.py`, que es la
misma para todos los catálogos externos.
"""

from pathlib import Path
from urllib.parse import urlencode

from django.conf import settings
from django.core.cache import cache

from apps.core import integraciones

RUTA_RESPALDO = Path(__file__).resolve().parent / "datos" / "georef.json"

CLAVE_PROVINCIAS = "georef:provincias"
CLAVE_LOCALIDADES = "georef:localidades:{provincia}"


def _pedir(recurso, **parametros):
    url = f"{settings.GEOREF_API_URL}/{recurso}?{urlencode(parametros)}"
    return integraciones.pedir_json(url, settings.GEOREF_TIMEOUT)


def descargar_provincias():
    """Las 24 jurisdicciones, tal como las nombra el INDEC. Sin caché ni respaldo."""
    datos = _pedir("provincias", campos="nombre", max=100)
    if not datos:
        return []
    return sorted(provincia["nombre"] for provincia in datos.get("provincias", []))


def obtener_provincias():
    """Las provincias para poblar un desplegable, con las tres capas."""
    return integraciones.obtener_con_respaldo(
        clave_cache=CLAVE_PROVINCIAS,
        descargar=descargar_provincias,
        ruta_respaldo=RUTA_RESPALDO,
        clave_respaldo="provincias",
        vigencia=settings.GEOREF_CACHE_SEGUNDOS,
    )


def provincias_para_select():
    """`[(valor, etiqueta)]` para un `ChoiceField` o un `<select>`."""
    return [(provincia, provincia) for provincia in obtener_provincias()]


def obtener_localidades(provincia):
    """Localidades de una provincia, para sugerir mientras se escribe.

    Sin respaldo en disco a propósito: son varios miles y ocuparían más que
    todo el resto del proyecto junto. Si la API no contesta se devuelve una
    lista vacía y el campo sigue siendo de texto libre — se pierde la ayuda, no
    la posibilidad de cargar la dirección.
    """
    if not provincia:
        return []

    clave = CLAVE_LOCALIDADES.format(provincia=provincia)
    localidades = cache.get(clave)
    if localidades is not None:
        return localidades

    datos = _pedir("localidades", provincia=provincia, campos="nombre", max=5000)
    localidades = sorted({item["nombre"] for item in (datos or {}).get("localidades", [])})

    cache.set(
        clave,
        localidades,
        settings.GEOREF_CACHE_SEGUNDOS if localidades else integraciones.CACHE_TRAS_FALLA_SEGUNDOS,
    )
    return localidades


def guardar_respaldo(datos):
    """Reescribe la foto local. La usa el comando `sincronizar_georef`."""
    integraciones.guardar_respaldo(RUTA_RESPALDO, datos)
