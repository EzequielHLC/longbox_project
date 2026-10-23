"""La dirección de una hoja o un guion con su versión.

Sin versión, el navegador puede seguir usando la hoja vieja después de un cambio
y la pantalla se ve rota sin estarlo. La versión es la fecha de modificación
del archivo: cambia sólo cuando el archivo cambia.
"""

import os

from django import template
from django.contrib.staticfiles import finders
from django.templatetags.static import static

register = template.Library()


@register.simple_tag
def estatico(ruta):
    archivo = finders.find(ruta)
    url = static(ruta)
    if not archivo:
        return url
    return f"{url}?v={int(os.path.getmtime(archivo))}"
