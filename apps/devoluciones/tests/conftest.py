import pytest


@pytest.fixture(autouse=True)
def evidencias_en_carpeta_temporal(settings, tmp_path):
    """Las fotos de las pruebas no quedan en la carpeta privada del proyecto."""
    settings.EVIDENCIA_ROOT = tmp_path / "privado"
    settings.MEDIA_ROOT = tmp_path / "media"
    return settings.EVIDENCIA_ROOT
