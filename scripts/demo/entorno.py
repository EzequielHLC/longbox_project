"""Lo común a las herramientas de la demostración (plan 00).

Todas las herramientas de `scripts/demo/` arrancan por `preparar()`. Usa los
ajustes de producción con los archivos subidos aparte (`ajustes_demo.py`). Fija el
entorno de la demostración y **se niega a seguir** si la base no es
`longbox_demo` en el contenedor del puerto 5433: la demostración nunca toca la
base de desarrollo.

El contenedor se crea una vez:

    docker run -d --name longbox-demo-db -e POSTGRES_USER=longbox_demo
      -e POSTGRES_PASSWORD=demo-longbox -e POSTGRES_DB=longbox_demo
      -e TZ=America/Argentina/Buenos_Aires -p 127.0.0.1:5433:5432
      -v longbox_demo_datos:/var/lib/postgresql postgres:18

La contraseña es la de un contenedor descartable que sólo escucha en la máquina
local; no protege nada fuera de ella.
"""

import os
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
SALIDA = RAIZ / "scripts" / "demo" / "salida"

BASE_DEMO = "longbox_demo"
PUERTO_DEMO = "5433"
DIRECCION = "https://127.0.0.1:8443"
# El certificado de `Caddyfile.demo` lo firma la autoridad local de Caddy. Los
# clientes de la demostración lo verifican contra ella: la conexión es HTTPS de
# verdad, sin apagar la verificación.
AUTORIDAD_LOCAL = str(
    Path(os.environ.get("APPDATA", "")) / "Caddy" / "pki" / "authorities" / "local" / "root.crt"
)
CONTENEDOR = "longbox-demo-db"

ENTORNO = {
    "DB_NAME": BASE_DEMO,
    "DB_HOST": "127.0.0.1",
    "DB_PORT": PUERTO_DEMO,
    "DB_USER": "longbox_demo",
    "DB_PASSWORD": "demo-longbox",  # nosec B105 - contenedor descartable, sólo escucha en la máquina local
    # Sin servidor de correo: cada correo queda en la consola de `servir`, con
    # el enlace de activación o de recuperación a la vista (B-00-008).
    "EMAIL_HOST": "",
    "EMAIL_BACKEND": "apps.core.mail.CorreoConCopia",
    # 127.0.0.1 y no localhost: producción manda HSTS por un año, y el navegador
    # lo ignora para una dirección IP pero no para «localhost».
    "ALLOWED_HOSTS": "127.0.0.1,localhost",
    "CSRF_TRUSTED_ORIGINS": f"{DIRECCION},https://localhost:8443",
}


def preparar(settings="ajustes_demo", *, django_setup=True):
    """Fija el entorno, inicia Django y verifica que la base sea la de la demostración."""
    elegida = os.environ.get("DB_NAME")
    if elegida not in (None, "", BASE_DEMO):
        raise SystemExit(
            f"DB_NAME={elegida}: las herramientas de la demostración sólo corren sobre {BASE_DEMO}."
        )
    os.environ.update(ENTORNO)
    os.environ["DJANGO_SETTINGS_MODULE"] = settings
    for ruta in (str(RAIZ), str(RAIZ / "scripts" / "demo")):
        if ruta not in sys.path:
            sys.path.insert(0, ruta)
    os.chdir(RAIZ)
    SALIDA.mkdir(parents=True, exist_ok=True)
    if django_setup:
        import logging

        import django

        django.setup()
        exigir_base_demo()
        # Producción escribe cada 403 con su traza; en la demostración sólo
        # interesa ver los errores de verdad (500).
        logging.getLogger("django.request").setLevel(logging.ERROR)
        logging.getLogger("django.security.csrf").setLevel(logging.ERROR)


def exigir_base_demo():
    from django.conf import settings

    base = settings.DATABASES["default"]
    if base["NAME"] != BASE_DEMO or str(base["PORT"]) != PUERTO_DEMO:
        raise SystemExit(
            f"La base configurada es {base['NAME']}:{base['PORT']}, no {BASE_DEMO}:{PUERTO_DEMO}."
        )


def entorno_para_subproceso(settings="ajustes_demo"):
    """El entorno de la demostración, para lanzar `manage.py` u otra herramienta."""
    variables = dict(os.environ)
    variables.update(ENTORNO)
    variables["DJANGO_SETTINGS_MODULE"] = settings
    variables["PYTHONPATH"] = os.pathsep.join([str(RAIZ / "scripts" / "demo"), str(RAIZ)])
    variables["PYTHONIOENCODING"] = "utf-8"
    return variables
