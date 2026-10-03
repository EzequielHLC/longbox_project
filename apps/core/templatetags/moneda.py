"""Los importes como los escribe la guía visual: «$ 18.500».

Punto de miles y coma decimal. Los decimales sólo aparecen cuando no son cero:
un precio redondeado al peso se lee sin «,00», y una cotización conserva los
suyos.
"""

from decimal import Decimal, InvalidOperation

from django import template

register = template.Library()


def _con_puntos(entero):
    return f"{entero:,}".replace(",", ".")


@register.filter
def pesos(valor):
    if valor in (None, ""):
        return ""
    try:
        numero = Decimal(str(valor))
    except (InvalidOperation, ValueError):
        return valor
    signo = "-" if numero < 0 else ""
    numero = abs(numero)
    entero = int(numero)
    resto = numero - entero
    if resto == 0:
        return f"{signo}$ {_con_puntos(entero)}"
    decimales = format(resto.normalize(), "f").split(".")[1]
    decimales = decimales.ljust(2, "0")
    return f"{signo}$ {_con_puntos(entero)},{decimales}"
