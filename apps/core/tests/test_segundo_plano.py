"""Los avisos salen en un hilo propio después del commit (`apps/core/segundo_plano.py`)."""

import threading

import pytest

from apps.core import segundo_plano


def _esperar_avisos():
    for hilo in threading.enumerate():
        if hilo.name == "aviso":
            hilo.join(timeout=5)


def test_con_segundo_plano_el_aviso_corre_en_otro_hilo_que_no_es_demonio(settings):
    settings.AVISOS_EN_SEGUNDO_PLANO = True
    vistos = []

    def aviso():
        hilo = threading.current_thread()
        vistos.append((hilo.name, hilo.daemon))

    segundo_plano.lanzar(aviso)
    _esperar_avisos()

    assert vistos == [("aviso", False)]


def test_sin_segundo_plano_corre_en_el_acto():
    vistos = []

    segundo_plano.lanzar(lambda: vistos.append(threading.current_thread().name))

    assert vistos == [threading.current_thread().name]


def test_un_aviso_que_falla_se_registra_y_no_sale_del_hilo(settings, caplog):
    settings.AVISOS_EN_SEGUNDO_PLANO = True

    def roto():
        raise ConnectionError("SMTP caído")

    segundo_plano.lanzar(roto)
    _esperar_avisos()

    assert "Falló un aviso en segundo plano" in caplog.text


@pytest.mark.django_db
def test_el_aviso_espera_a_que_se_confirme_la_transaccion(django_capture_on_commit_callbacks):
    vistos = []

    with django_capture_on_commit_callbacks(execute=False) as pendientes:
        segundo_plano.despues_del_commit(vistos.append, "aviso")

    assert vistos == []
    for callback in pendientes:
        callback()
    assert vistos == ["aviso"]
