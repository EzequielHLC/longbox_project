"""Lo común a las pruebas de concurrencia: hilos reales contra PostgreSQL.

Las pruebas que lo usan llevan `django_db(transaction=True)`: cada hilo abre su
propia conexión y tiene que ver lo que los otros confirmaron.
"""

import threading

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
