from .base import *  # noqa

DEBUG = False
ALLOWED_HOSTS = []  # completar con el dominio real cuando corresponda

# RNF-10: toda la comunicación viaja por HTTPS/TLS en producción.
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
