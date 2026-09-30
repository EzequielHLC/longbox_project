"""El comando que sirve el sistema en la demostración (`docs/despliegue/DEMOSTRACION.md`)."""

from unittest import mock

from django.core.management import call_command


def test_escucha_solo_en_la_interfaz_local_por_defecto():
    """Del lado de afuera atiende el proxy con TLS; `waitress` no se expone."""
    with mock.patch("waitress.serve") as serve:
        call_command("servir")

    argumentos = serve.call_args.kwargs
    assert argumentos["host"] == "127.0.0.1"
    assert argumentos["port"] == 8000
    assert argumentos["trusted_proxy"] == "127.0.0.1"
    assert "x-forwarded-proto" in argumentos["trusted_proxy_headers"]


def test_el_puerto_y_los_hilos_se_pueden_cambiar():
    with mock.patch("waitress.serve") as serve:
        call_command("servir", puerto=8080, hilos=2)

    assert serve.call_args.kwargs["port"] == 8080
    assert serve.call_args.kwargs["threads"] == 2
