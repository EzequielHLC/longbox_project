from .base import *  # noqa

DEBUG = True
ALLOWED_HOSTS = ["localhost", "127.0.0.1"]

# En desarrollo los correos (enlace de recuperación, aviso de bloqueo) se
# imprimen en la consola del runserver: no hace falta un SMTP real.
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
