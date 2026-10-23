"""Una celda de reporte según su tipo: el importe como importe, la fecha como fecha."""

from datetime import date
from decimal import Decimal

from django import template

from apps.core.templatetags.moneda import _con_puntos, pesos

register = template.Library()


@register.filter
def celda(valor):
    if isinstance(valor, Decimal):
        return pesos(valor)
    if isinstance(valor, date):
        return valor.strftime("%d/%m/%Y")
    if isinstance(valor, int) and not isinstance(valor, bool):
        return _con_puntos(valor)
    return valor


@register.filter
def es_cifra(valor):
    return isinstance(valor, (int, Decimal)) and not isinstance(valor, bool)
