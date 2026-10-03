"""Ajustes de despliegue. Lo que cambia respecto de desarrollo es seguridad.

Se valida con `python manage.py check --deploy --settings=config.settings.production`,
que el CI corre en cada push: los avisos de esa lista son deuda de despliegue, no
opiniones, y descubrirlos el día de la demostración es tarde.

El procedimiento completo —servidor, proxy con TLS y nombre dinámico— está en
`docs/despliegue/DEMOSTRACION.md`.
"""

from decouple import Csv, config

from .base import *  # noqa
from .base import BASE_DIR

DEBUG = False

# Sin esto Django rechaza todas las peticiones. Va por entorno y no fijo en el
# archivo porque el dominio cambia entre la demostración y cualquier otra cosa.
ALLOWED_HOSTS = config("ALLOWED_HOSTS", default="", cast=Csv())


def _origen_confiable(host):
    """El origen HTTPS que corresponde a una entrada de `ALLOWED_HOSTS`.

    Una entrada con punto adelante (`.trycloudflare.com`) acepta cualquier
    subdominio, que es lo que hace falta con un túnel cuya dirección cambia en
    cada arranque. CSRF escribe ese mismo comodín como `https://*.dominio`.
    """
    return f"https://*{host}" if host.startswith(".") else f"https://{host}"


# Los formularios llegan desde el nombre público y no desde el host interno
# con el que el proxy le habla a Django. Sin declararlo, un proxy que no
# preserve exactamente el encabezado `Host` hace fallar el CSRF de todos los
# formularios, empezando por el de inicio de sesión.
CSRF_TRUSTED_ORIGINS = config(
    "CSRF_TRUSTED_ORIGINS",
    default=",".join(_origen_confiable(host) for host in ALLOWED_HOSTS if host),
    cast=Csv(),
)

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
# **Es un compromiso difícil de revertir**: salir de esa lista tarda meses. El
# encabezado solo no anota nada; la anotación es un trámite aparte que sólo
# tiene sentido con el dominio definitivo.
SECURE_HSTS_PRELOAD = True

# El proxy que termina el TLS avisa por este encabezado. Sin declararlo, Django
# ve tráfico HTTP, y con `SECURE_SSL_REDIRECT` activo eso es un bucle infinito
# de redirecciones.
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# `collectstatic` junta acá los estáticos de todas las apps. No los sirve
# Django sino el proxy, igual que `media/`.
STATIC_ROOT = BASE_DIR / "staticfiles"

# El correo saliente se configura en base.py, igual que en desarrollo.

# Con DEBUG apagado un error 500 no deja rastro en ningún lado. Esto lo manda a
# la ventana del servidor, que en una demostración es lo único que se mira.
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"consola": {"class": "logging.StreamHandler"}},
    "root": {"handlers": ["consola"], "level": "WARNING"},
}
