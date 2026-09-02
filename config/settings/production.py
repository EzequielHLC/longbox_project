"""Ajustes de despliegue. Lo que cambia respecto de desarrollo es seguridad.

Se valida con `python manage.py check --deploy --settings=config.settings.production`,
que el CI corre en cada push: los avisos de esa lista son deuda de despliegue, no
opiniones, y descubrirlos el día de la demostración es tarde.
"""

from decouple import Csv, config

from .base import *  # noqa

DEBUG = False

# Sin esto Django rechaza todas las peticiones. Va por entorno y no fijo en el
# archivo porque el dominio cambia entre la demostración y cualquier otra cosa.
ALLOWED_HOSTS = config("ALLOWED_HOSTS", default="", cast=Csv())

# RNF-10: toda la comunicación viaja por HTTPS/TLS en producción.
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True

# Habilita anotar el dominio en la lista de precarga de los navegadores, que es
# lo que cierra la única ventana que HSTS deja abierta: la primera visita, que
# todavía viaja en claro porque el navegador no vio el encabezado nunca.
#
# **Es un compromiso difícil de revertir**: salir de esa lista tarda meses. Solo
# tiene sentido con el dominio definitivo y todos sus subdominios ya en HTTPS.
SECURE_HSTS_PRELOAD = True

# El proxy que termina el TLS avisa por este encabezado. Sin declararlo, Django
# ve tráfico HTTP, y con `SECURE_SSL_REDIRECT` activo eso es un bucle infinito
# de redirecciones.
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
