"""Lo común a las pruebas de concurrencia: hilos reales contra PostgreSQL.

Las pruebas que lo usan llevan `django_db(transaction=True)`: cada hilo abre su
propia conexión y tiene que ver lo que los otros confirmaron.
"""

import threading
from contextlib import contextmanager
from unittest import mock

from django.db import connection
from django.test import Client


def a_la_vez(*pedidos, espera=60):
    """Corre cada pedido en su hilo, soltados juntos por una barrera. Devuelve sus resultados."""
    barrera = threading.Barrier(len(pedidos))
    resultados = [None] * len(pedidos)

    def correr(indice, pedido):
        try:
            barrera.wait()
            resultados[indice] = pedido()
        finally:
            connection.close()

    hilos = [threading.Thread(target=correr, args=par) for par in enumerate(pedidos)]
    for hilo in hilos:
        hilo.start()
    for hilo in hilos:
        hilo.join(timeout=espera)
    return resultados


def sesion_de(usuario):
    """Una sesión que no propaga excepciones: se mide la respuesta que vería el usuario."""
    cliente = Client(raise_request_exception=False)
    cliente.force_login(usuario)
    return cliente


def errores_internos(respuestas):
    return [r.status_code for r in respuestas if r.status_code >= 500]


@contextmanager
def gana_la_carrera(formulario, insertar):
    """El otro pedido escribe el valor único entre la validación y el guardado.

    Con dos hilos la ventana se pisa sólo a veces; así se pisa siempre (plan 00 de
    cierre de deuda, D1). La primera vez que `formulario` valida bien, corre
    `insertar` —lo que el pedido ganador ya confirmó— y la vista sigue sin
    saberlo, como en la carrera de verdad. No hace falta `transaction=True`: la
    escritura va por la misma conexión y la restricción la ve igual.
    """
    original = formulario.is_valid
    pendiente = [True]

    def is_valid(self):
        valido = original(self)
        if valido and pendiente:
            pendiente.clear()
            insertar()
        return valido

    with mock.patch.object(formulario, "is_valid", is_valid):
        yield
