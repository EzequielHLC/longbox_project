"""`CU-AVI-EST` · el estado del sistema (plan 00 del bot, etapa 3, punto 5; B-19-013).

- `/estado` en el chat: disco, memoria, el tamaño de la base, el último respaldo y
  cuándo se revisó la casilla. **Sólo lee.**
- `controlar`, desde el reloj por minuto: si el disco pasa el 85 % o falta el
  respaldo de las últimas 26 horas, un aviso de tipo «Sistema», **uno por día y por
  problema** mientras siga.

El respaldo sólo se vigila donde hay uno diario programado (`VIGILAR_RESPALDO`, en
el `.env` de la VM): en esta PC no hay, y avisaría todos los días.
"""

import shutil
from datetime import timedelta
from pathlib import Path

from django.conf import settings
from django.db import connection, transaction
from django.utils import timezone

from apps.avisos.canales import avisar_administradores
from apps.avisos.models import SISTEMA
from apps.core.models import ConfiguracionSistema

DISCO_LLENO = 85  # por ciento
RESPALDO_VENCIDO = timedelta(hours=26)
_MEMINFO = Path("/proc/meminfo")


def _gb(bytes_):
    return f"{bytes_ / 1024**3:.1f} GB"


def disco():
    """`(usado %, libre en bytes)` del disco donde vive el sistema."""
    uso = shutil.disk_usage(settings.BASE_DIR)
    return round(uso.used * 100 / uso.total), uso.free


def memoria():
    """`(disponible, total)` en bytes, o `None` fuera de Linux."""
    try:
        datos = dict(
            linea.split(":", 1) for linea in _MEMINFO.read_text().splitlines() if ":" in linea
        )
        kilos = {clave: int(valor.split()[0]) * 1024 for clave, valor in datos.items()}
        return kilos["MemAvailable"], kilos["MemTotal"]
    except (OSError, KeyError, ValueError):
        return None


def tamano_de_la_base():
    if connection.vendor != "postgresql":
        return None
    with connection.cursor() as cursor:
        cursor.execute("SELECT pg_database_size(current_database())")
        return cursor.fetchone()[0]


def ultimo_respaldo():
    """`(cuándo, tamaño)` del respaldo más nuevo, o `None`."""
    from apps.core.management.commands.respaldar_base import RECONOCE

    carpeta = Path(settings.RESPALDOS_DIR)
    if not carpeta.is_dir():
        return None
    archivos = [a for a in carpeta.iterdir() if a.is_file() and RECONOCE.match(a.name)]
    if not archivos:
        return None
    nuevo = max(archivos, key=lambda a: a.stat().st_mtime)
    cuando = timezone.datetime.fromtimestamp(
        nuevo.stat().st_mtime, tz=timezone.get_current_timezone()
    )
    return cuando, nuevo.stat().st_size


def _hace(momento, ahora):
    minutos = int((ahora - momento).total_seconds() // 60)
    if minutos < 60:
        return f"hace {minutos} min"
    if minutos < 60 * 48:
        return f"hace {minutos // 60} h"
    return f"hace {minutos // (60 * 24)} días"


def texto_del_estado(ahora=None):
    """El mensaje de `/estado`, en el HTML de Telegram."""
    ahora = ahora or timezone.now()
    usado, libre = disco()
    lineas = ["<b>Estado del sistema</b>"]
    lineas.append(
        f"• Disco: {usado} % usado, {_gb(libre)} libres" + (" ⚠" if usado >= DISCO_LLENO else "")
    )
    if (ram := memoria()) is not None:
        disponible, total = ram
        lineas.append(f"• Memoria: {_gb(disponible)} disponibles de {_gb(total)}")
    if (base := tamano_de_la_base()) is not None:
        lineas.append(f"• Base: {base / 1024**2:.0f} MB")
    respaldo = ultimo_respaldo()
    if respaldo is None:
        lineas.append("• Respaldo: no hay ninguno" + (" ⚠" if settings.VIGILAR_RESPALDO else ""))
    else:
        cuando, tamano = respaldo
        vencido = settings.VIGILAR_RESPALDO and ahora - cuando > RESPALDO_VENCIDO
        lineas.append(
            f"• Último respaldo: {timezone.localtime(cuando):%d/%m %H:%M} "
            f"({_hace(cuando, ahora)}, {tamano / 1024**2:.0f} MB)" + (" ⚠" if vencido else "")
        )
    configuracion = ConfiguracionSistema.obtener()
    if configuracion.casilla_revisada_en:
        lineas.append(f"• Casilla revisada {_hace(configuracion.casilla_revisada_en, ahora)}")
    else:
        lineas.append("• Casilla: nunca se revisó")
    return "\n".join(lineas)


def problemas(ahora=None):
    """Los problemas de hoy: `{clave: texto}`."""
    ahora = ahora or timezone.now()
    encontrados = {}
    usado, libre = disco()
    if usado >= DISCO_LLENO:
        encontrados["disco"] = f"El disco está al {usado} %: quedan {_gb(libre)}."
    if settings.VIGILAR_RESPALDO:
        respaldo = ultimo_respaldo()
        if respaldo is None:
            encontrados["respaldo"] = "No hay ningún respaldo de la base."
        elif ahora - respaldo[0] > RESPALDO_VENCIDO:
            encontrados["respaldo"] = (
                f"El último respaldo de la base es de {_hace(respaldo[0], ahora)}: "
                "el de anoche no salió."
            )
    return encontrados


def controlar(ahora=None):
    """Avisa lo que está mal y todavía no se avisó hoy. Devuelve lo que avisó."""
    ahora = ahora or timezone.now()
    hoy = timezone.localdate(ahora).isoformat()
    encontrados = problemas(ahora)
    with transaction.atomic():
        configuracion = ConfiguracionSistema.objects.select_for_update().get(
            pk=ConfiguracionSistema.obtener().pk
        )
        avisados = dict(configuracion.salud_avisada or {})
        nuevos = {
            clave: texto for clave, texto in encontrados.items() if avisados.get(clave) != hoy
        }
        # Lo que se arregló sale del registro: si vuelve, se avisa de nuevo.
        avisados = {clave: dia for clave, dia in avisados.items() if clave in encontrados}
        avisados.update(dict.fromkeys(nuevos, hoy))
        if avisados != configuracion.salud_avisada:
            configuracion.salud_avisada = avisados
            configuracion.save(update_fields=["salud_avisada"])
    for texto in nuevos.values():
        avisar_administradores(
            SISTEMA,
            asunto="Longbox — un problema en el sistema",
            antetitulo="Estado del sistema",
            titulo="Hay algo para mirar",
            parrafos=[texto, "Mandá /estado al bot para ver todo."],
        )
    return list(nuevos)
