"""Regenera el respaldo local de datos geográficos desde la API oficial."""

from django.core.cache import cache
from django.core.management.base import BaseCommand, CommandError

from apps.core import georef


class Command(BaseCommand):
    help = (
        "Descarga las provincias de georef-ar-api y reescribe el respaldo local "
        "(apps/core/datos/georef.json), que es el que se usa cuando la API no responde."
    )

    def handle(self, *args, **opciones):
        self.stdout.write("Consultando georef-ar-api…")
        provincias = georef.descargar_provincias()

        if not provincias:
            # Se corta sin tocar el archivo: un respaldo vacío es peor que uno
            # desactualizado, porque deja el formulario sin ninguna provincia.
            raise CommandError("La API no devolvió provincias. El respaldo anterior queda intacto.")

        georef.guardar_respaldo({"provincias": provincias})
        cache.delete(georef.CLAVE_PROVINCIAS)

        self.stdout.write(
            self.style.SUCCESS(
                f"Respaldo actualizado con {len(provincias)} provincias "
                f"en {georef.RUTA_RESPALDO}."
            )
        )
