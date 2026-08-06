import pytest

from apps.accounts.tests.factories import UsuarioFactory


@pytest.fixture
def cliente(db):
    return UsuarioFactory(rol="cliente")


@pytest.fixture
def cajero(db):
    return UsuarioFactory(rol="cajero")


@pytest.fixture
def administrador(db):
    return UsuarioFactory(rol="administrador")
