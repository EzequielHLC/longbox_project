"""Dónde se guardan las fotos de un reclamo (plan 09, ambigüedad 10).

**Fuera de `media/`**, que el servidor web publica entero: una foto que un
Cliente adjunta a su reclamo es suya y del Administrador, no de quien adivine la
dirección. La sirve una vista que pide sesión (`EvidenciaView`), y por eso este
almacenamiento no tiene URL.

La carpeta se lee de `settings.EVIDENCIA_ROOT` en cada uso, no al importar: las
pruebas la apuntan a una carpeta temporal.
"""

import os

from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.utils.deconstruct import deconstructible


@deconstructible(path="apps.devoluciones.almacenamiento.AlmacenamientoPrivado")
class AlmacenamientoPrivado(FileSystemStorage):
    @property
    def base_location(self):
        return self._value_or_setting(self._location, settings.EVIDENCIA_ROOT)

    @property
    def location(self):
        return os.path.abspath(self.base_location)

    def url(self, name):
        raise ValueError("La evidencia de un reclamo no tiene dirección pública.")


evidencias = AlmacenamientoPrivado()
