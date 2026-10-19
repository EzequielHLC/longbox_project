"""Regenera el respaldo local de cotizaciones."""

from django.core.management.base import BaseCommand, CommandError

from apps.core import cotizaciones


class Command(BaseCommand):
    help = (
        "Descarga la cotización del peso frente al dólar, el euro y el yen y reescribe "
        "el respaldo local (apps/core/datos/cotizaciones.json), que es el que se usa "
        "cuando la API no responde. Conviene correrlo seguido: a diferencia de los otros "
        "catálogos, este dato envejece todos los días."
    )

    def handle(self, *args, **opciones):
        self.stdout.write("Consultando las cotizaciones…")
        catalogo = cotizaciones.sincronizar()

        if not catalogo:
            # Se corta sin tocar el archivo: un respaldo vacío dejaría el alta
            # de importados sin ninguna cotización sugerida, que es peor que
            # una vieja —la vieja al menos se ve, con su fecha, y se corrige—.
            raise CommandError(
                "La API no devolvió cotizaciones. El respaldo anterior queda intacto."
            )

        detalle = ", ".join(
            f"{moneda} ${valor}" for moneda, valor in sorted(catalogo["valores"].items())
        )
        self.stdout.write(
            self.style.SUCCESS(
                f"Respaldo actualizado al {catalogo['fecha']} ({detalle}) "
                f"en {cotizaciones.RUTA_RESPALDO}."
            )
        )
