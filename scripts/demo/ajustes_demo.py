"""Ajustes de la demostración: los de producción, con los archivos subidos aparte.

Hereda **todo** de `config.settings.production` (`DEBUG=False`, HTTPS, cookies
seguras, HSTS). Lo único que cambia es la carpeta de archivos subidos: las
portadas de la demostración son contenido de Ivrea y se borran al terminar
(plan 00, decisión 7), así que no se mezclan con las de `media/` de desarrollo.
"""

from config.settings.production import *  # noqa: F403
from config.settings.production import BASE_DIR

MEDIA_ROOT = BASE_DIR / "scripts" / "demo" / "datos" / "media"
