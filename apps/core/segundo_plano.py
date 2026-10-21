"""Avisos por correo fuera del pedido que los origina.

Un correo por SMTP tarda de uno a tres segundos: conexión, TLS y
autenticación. Avanzar un pedido manda uno y abrir un arrepentimiento, dos, y la
pantalla esperaba a todos antes de responder. Un aviso no cambia el estado del
sistema —el avance o el caso ya quedaron guardados— y su falla ya se registraba
sin deshacer nada, así que no hay motivo para hacer esperar a quien lo dispara.

`despues_del_commit` reemplaza a `transaction.on_commit` para los avisos:
cuando la transacción se confirma, el aviso corre en un hilo propio.

- El hilo **no es demonio**: un comando de consola (el Temporizador) espera a
  que termine antes de salir, y ningún correo se pierde al cerrar el proceso.
- Con `AVISOS_EN_SEGUNDO_PLANO = False` corre en el acto, como antes. Las
  pruebas lo apagan: el buzón de prueba se lee apenas vuelve la operación.
- El hilo cierra su conexión a la base al terminar.

Lo que tiene que saber si el correo salió (el pedido a proveedor, con sus
reintentos; el enlace de activación, cuyo fallo llega a la pantalla) no pasa
por acá.
"""

import logging
import threading
from functools import partial

from django.conf import settings
from django.db import connections, transaction

logger = logging.getLogger(__name__)


def despues_del_commit(funcion, *args, **kwargs):
    tarea = partial(funcion, *args, **kwargs)
    transaction.on_commit(partial(lanzar, tarea))


def lanzar(tarea):
    if not getattr(settings, "AVISOS_EN_SEGUNDO_PLANO", True):
        tarea()
        return
    threading.Thread(target=_correr, args=(tarea,), name="aviso", daemon=False).start()


def _correr(tarea):
    try:
        tarea()
    except Exception:  # noqa: BLE001 - un aviso caído no deshace lo que avisa
        logger.exception("Falló un aviso en segundo plano: %r", tarea)
    finally:
        connections.close_all()
