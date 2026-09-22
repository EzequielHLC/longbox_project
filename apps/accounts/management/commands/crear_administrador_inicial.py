"""Alta de la primera cuenta Administrador de una instalacion nueva.

    python manage.py crear_administrador_inicial

Es una **tarea de consola**, fuera del modelo de casos de uso, igual que el
respaldo de la base y la sincronizacion de los catalogos geograficos (ver
`bitacora/01-alta-editorial.md`, R-01-002). No tiene ficha ni contrato, y eso es
deliberado: no hay actor del sistema que pueda ejecutarla, porque el sistema
todavia no tiene ninguna cuenta.

Ocupa el lugar que antes tenia `createsuperuser`, que se fue junto con el admin
de Django. Las dos reglas que lo sacaron valen tambien aca, y son las que dan
forma a este comando:

1. **Ninguna escritura del sistema ocurre fuera de una operacion contratada.**
   Este comando escribe una sola fila, de un solo tipo, bajo una condicion que
   no se puede repetir. No es una puerta de escritura: es el arranque.
2. **No existe ninguna cuenta fuera de los tres roles.** Crea un `Usuario` con
   rol Administrador. No crea un superusuario: `is_superuser` e `is_staff`
   quedan en False, que es su valor por omision.

Tres decisiones mas:

- **Corre una sola vez.** Si ya hay un Administrador activo, se niega. Eso lo
  vuelve seguro de dejar en un guion de despliegue: la segunda corrida no hace
  nada. Y cierra la via por la que, si no, alguien con acceso al servidor se
  fabricaria una cuenta de Administrador sin pasar por CU-USR-ALT.
- **La cuenta nace Activa, con la contrasena que se tipea aca.** El camino
  normal de un alta —Pendiente de activacion y un enlace por correo— no sirve en
  una instalacion nueva: no hay quien reciba el enlace ni garantia de que el
  correo saliente este configurado todavia. La contrasena pasa igual por
  AUTH_PASSWORD_VALIDATORS, que es lo que el sistema exige en cualquier otro
  camino.
- **Queda en el registro de auditoria**, con accion propia
  (`ALTA_ADMINISTRADOR_INICIAL`) y sin actor: es la unica cuenta del sistema que
  nace sin que otra cuenta la haya creado, y la entrada tiene que poder decir
  eso.

La salida va en ASCII a proposito: la consola de Windows corre en cp1252 y un
acento la hace reventar con UnicodeEncodeError.
"""

import getpass
import sys

from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.accounts import services
from apps.accounts.forms import partir_nombre, validar_nombre_completo
from apps.accounts.models import Usuario
from apps.core.models import RegistroAuditoria

YA_HAY_ADMINISTRADOR = (
    "Ya existe al menos una cuenta Administrador activa. Este comando solo corre sobre una "
    "instalacion sin administradores: el alta de las demas cuentas de personal es CU-USR-ALT, "
    "desde la pantalla de gestion de usuarios."
)


class Command(BaseCommand):
    help = "Crea la primera cuenta Administrador de una instalacion nueva."

    def add_arguments(self, parser):
        parser.add_argument("--email", help="correo de la cuenta; si falta, se pregunta")
        parser.add_argument("--nombre", help="nombre completo; si falta, se pregunta")
        parser.add_argument(
            "--password",
            help=(
                "contrasena; si falta, se pide sin eco. Pasarla por argumento la deja visible "
                "para cualquiera que liste procesos: usar solo en un despliegue automatizado."
            ),
        )

    def handle(self, *args, **opciones):
        if Usuario.objects.filter(rol=Usuario.ADMINISTRADOR, estado=Usuario.ACTIVO).exists():
            raise CommandError(YA_HAY_ADMINISTRADOR)

        email = self._normalizar_email(opciones.get("email") or self._pedir("Correo: "))
        nombre = self._validar_nombre(opciones.get("nombre") or self._pedir("Nombre completo: "))
        password = opciones.get("password") or self._pedir_password()
        self._validar_password(password, email)

        with transaction.atomic():
            # Se vuelve a mirar dentro de la transaccion, y con bloqueo: entre
            # el chequeo de arriba y este punto pudo entrar otra corrida, y dos
            # primeros Administradores no es un estado valido.
            ya_hay = (
                Usuario.objects.select_for_update()
                .filter(rol=Usuario.ADMINISTRADOR, estado=Usuario.ACTIVO)
                .exists()
            )
            if ya_hay:
                raise CommandError(YA_HAY_ADMINISTRADOR)

            nombre_de_pila, apellido = partir_nombre(nombre)
            usuario = Usuario(
                username=services.username_disponible_para(email),
                email=email,
                first_name=nombre_de_pila,
                last_name=apellido,
                rol=Usuario.ADMINISTRADOR,
                estado=Usuario.ACTIVO,
            )
            usuario.set_password(password)
            usuario.save()

            RegistroAuditoria.registrar(
                accion=RegistroAuditoria.ALTA_ADMINISTRADOR_INICIAL,
                objetivo=usuario,
                detalle=(
                    "alta del primer Administrador de la instalacion, desde consola; "
                    "no hay actor porque el sistema no tenia ninguna cuenta"
                ),
            )

        self.stdout.write(
            self.style.SUCCESS(f"Cuenta Administrador creada y activa: {usuario.email}")
        )
        self.stdout.write(
            "Las demas cuentas de personal se dan de alta desde la pantalla de gestion de "
            "usuarios. Este comando no vuelve a correr."
        )

    # ----------------------------------------------------------------- #

    def _pedir(self, etiqueta):
        if not sys.stdin.isatty():
            raise CommandError(
                f"Falta un dato ({etiqueta.strip(': ')}) y la consola no es interactiva. "
                "Pasalo por argumento."
            )
        valor = input(etiqueta).strip()
        if not valor:
            raise CommandError("El valor no puede quedar vacio.")
        return valor

    def _pedir_password(self):
        if not sys.stdin.isatty():
            raise CommandError(
                "Falta la contrasena y la consola no es interactiva. Pasala con --password."
            )
        password = getpass.getpass("Contrasena: ")
        if password != getpass.getpass("Contrasena (otra vez): "):
            raise CommandError("Las dos contrasenas no coinciden.")
        return password

    def _normalizar_email(self, email):
        email = email.strip().lower()
        if "@" not in email:
            raise CommandError(f"'{email}' no parece un correo electronico.")
        if Usuario.objects.filter(email__iexact=email).exists():
            # I-10: el correo identifica una sola cuenta en cualquier estado.
            raise CommandError(f"Ya existe una cuenta con el correo '{email}'.")
        return email

    def _validar_nombre(self, nombre):
        nombre = " ".join(nombre.split())
        errores = validar_nombre_completo(nombre)
        if errores:
            raise CommandError(" ".join(str(e) for e in errores))
        return nombre

    def _validar_password(self, password, email):
        # El mismo juego de validadores que cualquier otro camino del sistema:
        # que esta cuenta se cree por consola no le baja el umbral.
        candidata = Usuario(username=email, email=email, rol=Usuario.ADMINISTRADOR)
        try:
            validate_password(password, candidata)
        except ValidationError as error:
            raise CommandError(" ".join(error.messages)) from error
