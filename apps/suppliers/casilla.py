"""`CO-016 ejecutarCicloMonitoreoCasilla` (plan 00, A1).

El Temporizador lee la casilla de novedades y deja cada correo de un proveedor
habilitado en la cola, **sin procesarlo**: la extracción la dispara una persona
(`CO-017`). Es el mismo `services.ingerir` que usa la carga manual de `.eml`
(B-01-002), con su idempotencia por identificador de mensaje (I-16).

**`abrir` es la única salida a la casilla.** No es HTTP, así que no pasa por la
puerta de `core/integraciones.py`: las pruebas la cortan por su cuenta en el
`conftest`, igual que la red.
"""

import imaplib
import logging
from dataclasses import dataclass, field
from datetime import timedelta

from django.conf import settings
from django.urls import reverse
from django.utils import timezone

from apps.core.models import ConfiguracionSistema
from apps.pedidos import avisos
from apps.suppliers import services

logger = logging.getLogger(__name__)

TIEMPO_DE_ESPERA = 30


def configurada():
    return bool(settings.CASILLA_HOST and settings.CASILLA_USUARIO)


HOSTS_LOCALES = ("127.0.0.1", "localhost", "::1")


class CasillaSinCifrar(ValueError):
    """`CASILLA_SSL` apagado para una casilla que no está en esta máquina."""


def abrir():
    """La conexión a la casilla, ya autenticada y en la carpeta configurada.

    Sin SSL sólo para el correo de prueba de esta máquina (`config/correo-de-prueba/`):
    con una casilla de afuera, la clave viajaría en claro.
    """
    if settings.CASILLA_SSL:
        clase = imaplib.IMAP4_SSL
    elif settings.CASILLA_HOST in HOSTS_LOCALES:
        clase = imaplib.IMAP4
    else:
        raise CasillaSinCifrar(
            "CASILLA_SSL apagado sólo se admite con una casilla local, "
            f"no con {settings.CASILLA_HOST}."
        )
    conexion = clase(settings.CASILLA_HOST, settings.CASILLA_PUERTO, timeout=TIEMPO_DE_ESPERA)
    conexion.login(settings.CASILLA_USUARIO, settings.CASILLA_CLAVE)
    conexion.select(settings.CASILLA_CARPETA)
    return conexion


def mensajes_no_leidos(conexion):
    """Los mensajes sin leer, sin marcarlos todavía: `BODY.PEEK` no toca el estado."""
    _, datos = conexion.search(None, "UNSEEN")
    for numero in (datos[0] or b"").split():
        _, partes = conexion.fetch(numero, "(BODY.PEEK[])")
        crudo = next((p[1] for p in partes if isinstance(p, tuple)), None)
        if crudo:
            yield numero, crudo


@dataclass
class ResumenCasilla:
    estado: str = "revisada"
    ingresados: list = field(default_factory=list)
    repetidos: int = 0
    descartados: int = 0


def ciclo(ahora=None, *, forzar=False):
    """Una vuelta del monitoreo. Correrlo dos veces no encola dos veces (I-16).

    `forzar` saltea la frecuencia de Parámetros: es `manage.py revisar_casilla`,
    para no esperar al Temporizador en una demostración (plan 00 del circuito, H).
    """
    ahora = ahora or timezone.now()
    if not configurada():
        return ResumenCasilla(estado="sin configurar")
    configuracion = ConfiguracionSistema.obtener()
    ultima = configuracion.casilla_revisada_en
    frecuencia = timedelta(minutes=configuracion.frecuencia_casilla_minutos)
    if not forzar and ultima and ahora - ultima < frecuencia:
        return ResumenCasilla(estado="no corresponde todavía")

    resumen = ResumenCasilla()
    try:
        conexion = abrir()
    except Exception as error:  # noqa: BLE001 - E3: sin conexión, se avisa y se reintenta
        logger.exception("No se pudo conectar a la casilla de novedades.")
        _avisar_sin_conexion(error)
        return ResumenCasilla(estado="sin conexión")
    try:
        for numero, crudo in mensajes_no_leidos(conexion):
            resultado = services.ingerir(crudo, nombre_archivo=f"casilla-{numero.decode()}.eml")
            if resultado.ingresado:
                resumen.ingresados.append(resultado.correo)
            elif resultado.motivo == services.MotivoDeDescarte.REPETIDO:
                resumen.repetidos += 1
            else:
                resumen.descartados += 1  # E1, E2: se registra y se sigue
            conexion.store(numero, "+FLAGS", "\\Seen")
    finally:
        try:
            conexion.logout()
        except Exception:  # noqa: BLE001 - cerrar no puede tumbar lo ya ingresado
            logger.warning("La casilla no cerró la sesión limpiamente.")

    ConfiguracionSistema.objects.filter(pk=configuracion.pk).update(casilla_revisada_en=ahora)
    if resumen.ingresados:
        _avisar_nuevos(resumen.ingresados)
    return resumen


def proxima_revision():
    """Cuándo le toca a la lectura automática, o `None` si nunca se revisó.

    La frecuencia cuenta desde la última revisión, sea automática o a pedido —el
    botón de la cola o `/refresh` en el bot—: revisar a mano reinicia el reloj.
    """
    configuracion = ConfiguracionSistema.obtener()
    if configuracion.casilla_revisada_en is None:
        return None
    return configuracion.casilla_revisada_en + timedelta(
        minutes=configuracion.frecuencia_casilla_minutos
    )


def _enlace(nombre_url):
    return settings.URL_PUBLICA + reverse(nombre_url) if settings.URL_PUBLICA else ""


def _avisar_nuevos(correos):
    # Módulo 19: por correo, el resumen; por Telegram, cada correo con sus botones.
    from apps.avisos import canales

    canales.avisar_correos_nuevos(
        correos,
        asunto=f"{len(correos)} correo(s) de novedades en la cola",
        rotulo="Proveedores",
        antetitulo="Casilla de novedades",
        titulo="Correos nuevos",
        parrafos=["Llegaron correos de proveedores. Quedan en la cola hasta que los apruebes."],
        filas=[(str(correo.proveedor), correo.asunto) for correo in correos],
        enlace=_enlace("suppliers:correo_lista"),
        texto_enlace="Ver la cola",
    )


def _avisar_sin_conexion(error):
    avisos.avisar_administradores(
        tipo="correos",
        asunto="No se pudo leer la casilla de novedades",
        rotulo="Proveedores",
        antetitulo="Casilla de novedades",
        titulo="Sin conexión",
        parrafos=[
            "El Temporizador no pudo conectarse a la casilla. Se reintenta en el próximo ciclo.",
            f"Detalle: {type(error).__name__}.",
        ],
    )
