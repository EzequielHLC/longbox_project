"""Códigos telefónicos de país, desde un servicio público.

Fuente: `countriesnow.space`, que devuelve nombre, código ISO y código de
discado de cada país sin pedir credenciales.

Sobre la elección, para que quede asentada: el catálogo autoritativo de códigos
telefónicos es la recomendación **E.164 de la UIT**, que no se publica como API
gratuita, y tampoco existe una oficial del Estado argentino para códigos del
mundo (georef es de geografía nacional). Entre escribir 195 códigos a mano y
tomarlos de un servicio libre con respaldo local, esto último envejece mejor:
cuando el catálogo cambia, se corre un comando en vez de editar código.

Misma política de tres capas que el resto (`apps/core/integraciones.py`).
"""

import re
from pathlib import Path

from django.conf import settings

from apps.core import integraciones

RUTA_RESPALDO = Path(__file__).resolve().parent / "datos" / "paises.json"

CLAVE_PAISES = "paises:codigos"

# El servicio devuelve algunos códigos con el área adentro ("+1 684" para Samoa
# Americana). El código de país de E.164 es solo el primer grupo de dígitos: el
# resto ya es numeración interna.
PRIMER_GRUPO = re.compile(r"^\+(\d{1,3})")


def _codigo_de_pais(discado):
    encontrado = PRIMER_GRUPO.match(discado or "")
    return f"+{encontrado.group(1)}" if encontrado else None


def descargar_paises():
    """`[[código, etiqueta]]` ordenado por país. Sin caché ni respaldo.

    Se devuelven listas y no tuplas porque el resultado se serializa a JSON
    —tanto en el respaldo como en la caché— y JSON no distingue unas de otras;
    usar el mismo tipo en los dos caminos evita que el formulario se comporte
    distinto según de dónde salieron los datos.
    """
    datos = integraciones.pedir_json(settings.PAISES_API_URL, settings.PAISES_TIMEOUT)
    if not datos or datos.get("error"):
        return []

    paises = []
    for pais in datos.get("data", []):
        codigo = _codigo_de_pais(pais.get("dial_code"))
        nombre = (pais.get("name") or "").strip()
        if codigo and nombre:
            paises.append([codigo, f"{nombre} ({codigo})"])

    return sorted(paises, key=lambda pais: pais[1])


def obtener_paises():
    return integraciones.obtener_con_respaldo(
        clave_cache=CLAVE_PAISES,
        descargar=descargar_paises,
        ruta_respaldo=RUTA_RESPALDO,
        clave_respaldo="paises",
        vigencia=settings.PAISES_CACHE_SEGUNDOS,
    )


def paises_para_select():
    """`[(valor, etiqueta)]` para un `ChoiceField`."""
    return [(codigo, etiqueta) for codigo, etiqueta in obtener_paises()]


def guardar_respaldo(datos):
    integraciones.guardar_respaldo(RUTA_RESPALDO, datos)
