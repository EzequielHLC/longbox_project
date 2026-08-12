"""Regenera el respaldo local de códigos telefónicos de país."""

from django.core.cache import cache
from django.core.management.base import BaseCommand, CommandError

from apps.core import paises


class Command(BaseCommand):
    help = (
        "Descarga los códigos telefónicos de país y reescribe el respaldo local "
        "(apps/core/datos/paises.json), que es el que se usa cuando la API no responde."
    )

    def handle(self, *args, **opciones):
        self.stdout.write("Consultando el catálogo de países…")
        catalogo = paises.descargar_paises()

        if not catalogo:
            # Se corta sin tocar el archivo: un respaldo vacío es peor que uno
            # desactualizado, porque deja el formulario sin ningún código.
            raise CommandError("La API no devolvió países. El respaldo anterior queda intacto.")

        paises.guardar_respaldo({"paises": catalogo})
        cache.delete(paises.CLAVE_PAISES)

        self.stdout.write(
            self.style.SUCCESS(
                f"Respaldo actualizado con {len(catalogo)} países en {paises.RUTA_RESPALDO}."
            )
        )
