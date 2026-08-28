"""Corre la extracción del modelo sobre los correos que están en la cola.

Es la puerta de entrada mientras no exista el disparo desde la notificación al
celular. No es un andamio descartable: cuando ese disparo exista va a invocar el
**mismo** `services.extraer_novedades`, y este comando va a seguir sirviendo
para reprocesar un correo a mano después de ajustar el prompt.

**Por defecto no procesa nada sin que se lo pidan.** Hay que nombrar el correo o
pedir explícitamente toda la cola: el modelo corre local y cada pasada son
minutos de GPU, así que un comando que procese todo por omisión es la forma más
rápida de gastar una tarde sin querer.
"""

from django.core.management.base import BaseCommand, CommandError

from apps.core.consola import ascii_seguro
from apps.suppliers import services
from apps.suppliers.models import CorreoProveedor

FLECHA = "->"


class Command(BaseCommand):
    help = "Extrae los productos de un correo de la cola con el modelo de lenguaje."

    def add_arguments(self, parser):
        parser.add_argument(
            "--correo",
            type=int,
            help="Identificador del correo a procesar.",
        )
        parser.add_argument(
            "--pendientes",
            action="store_true",
            help="Procesa todos los correos pendientes de la cola.",
        )

    def handle(self, *args, **opciones):
        correos = self._elegir(opciones)
        if not correos:
            self.stdout.write("No hay correos que procesar.")
            return

        for correo in correos:
            # El asunto y el título vienen del correo del proveedor: pueden
            # traer cualquier cosa. Se transcriben para que un kanji no tumbe la
            # salida con el trabajo ya hecho.
            self.stdout.write(f"Procesando: {ascii_seguro(correo.asunto) or 'sin asunto'}")
            resultado = services.extraer_novedades(correo)

            if not resultado:
                self.stdout.write(self.style.ERROR(f"  {FLECHA} {ascii_seguro(correo.motivo)}"))
                continue

            resumen = resultado.resumen
            self.stdout.write(
                self.style.SUCCESS(
                    f"  {FLECHA} intencion: {resumen['intencion']}, "
                    f"{resumen['productos']} productos "
                    f"({resumen['completos']} completos, "
                    f"{resumen['incompletos']} incompletos, "
                    f"{resumen['con_reparos']} con reparos)"
                )
            )
            for producto in resultado.productos:
                for reparo in producto.reparos:
                    titulo = ascii_seguro(producto.titulo) or "sin titulo"
                    self.stdout.write(f"     ! {titulo}: {ascii_seguro(reparo)}")

    def _elegir(self, opciones):
        if opciones.get("correo"):
            correo = CorreoProveedor.objects.filter(pk=opciones["correo"]).first()
            if correo is None:
                raise CommandError(f"No existe el correo {opciones['correo']}.")
            return [correo]

        if opciones.get("pendientes"):
            return list(CorreoProveedor.objects.pendientes())

        raise CommandError("Indique --correo <id> o --pendientes.")
