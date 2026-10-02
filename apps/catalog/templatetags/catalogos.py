"""Las rutas de un registro de catálogo, para las plantillas compartidas.

Las plantillas no pueden llamar a un método con argumentos, y las filas de los
cinco catálogos comparten el parcial de estado y acciones: el catálogo sabe sus
rutas, y estos filtros se las piden.
"""

from django import template

register = template.Library()


@register.filter
def url_editar(catalogo, registro):
    return catalogo.url_editar(registro)


@register.filter
def url_baja(catalogo, registro):
    return catalogo.url_baja(registro)
