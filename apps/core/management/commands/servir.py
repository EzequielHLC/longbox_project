"""Sirve el sistema con un servidor WSGI apto para producción.

`runserver` no sirve para esto: es de un solo proceso, no está pensado para
tráfico real y Django lo desaconseja fuera del desarrollo. `waitress` corre en
Windows sin compilar nada, que es donde se hace la demostración.

Escucha sólo en la interfaz local a propósito. Del lado de afuera atiende el
proxy (`config/caddy/Caddyfile`), que termina el TLS y sirve `static/` y
`media/`. Exponer `waitress` directamente dejaría el sistema sin HTTPS.
"""

from django.core.management.base import BaseCommand
from django.core.wsgi import get_wsgi_application


class Command(BaseCommand):
    help = (
        "Sirve el sistema con waitress, detrás del proxy descrito en "
        "docs/despliegue/DEMOSTRACION.md."
    )

    def add_arguments(self, parser):
        parser.add_argument("--host", default="127.0.0.1")
        parser.add_argument("--puerto", type=int, default=8000)
        parser.add_argument("--hilos", type=int, default=8)

    def handle(self, *args, **opciones):
        # Se importa acá y no arriba: el resto de los comandos no necesita el
        # servidor, y la suite no debería depender de que esté instalado.
        from waitress import serve

        self.stdout.write(
            f"Sirviendo en http://{opciones['host']}:{opciones['puerto']} "
            f"con {opciones['hilos']} hilos. Ctrl+C para detener."
        )
        serve(
            get_wsgi_application(),
            host=opciones["host"],
            port=opciones["puerto"],
            threads=opciones["hilos"],
            # El proxy informa el esquema y el cliente reales. `waitress` sólo
            # confía en ellos si vienen de la interfaz local.
            trusted_proxy="127.0.0.1",
            trusted_proxy_headers={"x-forwarded-proto", "x-forwarded-for", "x-forwarded-host"},
            clear_untrusted_proxy_headers=True,
        )
