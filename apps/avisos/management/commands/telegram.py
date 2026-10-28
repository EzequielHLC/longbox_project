"""El bot de Telegram desde la consola (decisión 7 del plan 00 de Telegram).

    python manage.py telegram estado     # el bot, y si tiene webhook
    python manage.py telegram escuchar   # en esta PC: atiende el bot y corre el reloj
    python manage.py telegram webhook    # en la VM: Telegram entrega en URL_PUBLICA

`escuchar` saca el webhook antes de empezar (Telegram no admite las dos cosas a la
vez) y atiende hasta Ctrl+C. Entre una consulta y otra corre el reloj por minuto
(`core.reloj`), que en la VM corre por su cuenta. `webhook` necesita `URL_PUBLICA`
con HTTPS.
"""

import time

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.urls import reverse

from apps.avisos import bot, telegram
from apps.core.consola import ascii_seguro

# Las líneas del reloj que no cuentan nada: no se muestran en la consola del bot.
SIN_NOVEDAD = (
    " 0 correo(s) nuevo(s)",
    "no corresponde todavía",
    "sin configurar",
    "no es la hora",
    "ya salió",
    "sin avisos",
)


class Command(BaseCommand):
    help = "El bot de Telegram: estado, escuchar (esta PC) o webhook (la VM)."

    def add_arguments(self, parser):
        parser.add_argument("accion", choices=["estado", "escuchar", "webhook"])
        parser.add_argument(
            "--una-vez", action="store_true", help="escuchar: una sola consulta y terminar."
        )

    def handle(self, *args, accion, una_vez=False, **opciones):
        if not telegram.configurado():
            raise CommandError("Falta TELEGRAM_BOT_TOKEN en el .env.")
        getattr(self, f"_{accion}")(una_vez)

    def _estado(self, _):
        usuario = telegram.usuario_del_bot()
        if not usuario:
            raise CommandError("Telegram no contestó: revisá el token o la conexión.")
        self.stdout.write(ascii_seguro(f"Bot @{usuario}: https://t.me/{usuario}"))

    def _reloj(self):
        """Una vuelta del reloj por minuto (B-19-011). Muestra sólo lo que pasó algo."""
        from apps.core import reloj

        for linea in reloj.tic():
            if not linea.endswith(SIN_NOVEDAD):
                self.stdout.write(ascii_seguro(linea))

    def _webhook(self, _):
        if not settings.URL_PUBLICA.startswith("https://"):
            raise CommandError("El webhook necesita URL_PUBLICA con https:// (la de la VM).")
        url = settings.URL_PUBLICA + reverse("avisos:webhook")
        if telegram.poner_webhook(url) is None:
            raise CommandError("Telegram no aceptó el webhook.")
        telegram.poner_comandos()
        self.stdout.write(f"Webhook en {url}")

    def _escuchar(self, una_vez):
        telegram.sacar_webhook()
        telegram.poner_comandos()
        self.stdout.write("Escuchando al bot y corriendo el reloj (Ctrl+C para salir)...")
        desde = None
        ultimo_tic = None
        try:
            while True:
                for novedad in telegram.novedades(desde):
                    desde = novedad["update_id"] + 1
                    bot.procesar(novedad)
                # B-04-015 y B-19-011: el reloj, a lo sumo una vez por minuto. Así un
                # correo nuevo llega al chat en minutos, sin el botón.
                if ultimo_tic is None or time.monotonic() - ultimo_tic >= 60:
                    self._reloj()
                    ultimo_tic = time.monotonic()
                if una_vez:
                    break
        except KeyboardInterrupt:
            self.stdout.write("Listo.")
