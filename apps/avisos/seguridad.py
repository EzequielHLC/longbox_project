"""Las alertas de seguridad (plan 00 del bot, etapa 3, punto 4; B-19-012).

**Se enganchan en lo que ya se audita**, no en cada pantalla: el registro de
auditoría es la única puerta por la que pasa todo esto, y una alerta que
dependiera de la vista se perdería con la primera operación que entre por otro
lado. Al grabarse una entrada de las que importan, se decide si es para alertar:

- un **bloqueo por intentos** de una cuenta que existe;
- un **inicio de sesión del personal desde una IP** que esa cuenta no usó en los
  últimos 90 días (ambigüedad 7). El primer ingreso de una cuenta no cuenta:
  todavía no hay contra qué comparar;
- el **alta de un Administrador** o un **cambio de rol** que entra o sale de
  Administrador;
- una **propagación masiva de precios**: el margen global (`CO-053`) o una fila de
  la tabla (`CO-048`) que alcanzó productos (ambigüedad 8).

Sale después de confirmar la transacción y en segundo plano. Por defecto, por
correo y por Telegram (ambigüedad 1).
"""

import re
from datetime import timedelta

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

from apps.avisos.canales import avisar_administradores, enlace
from apps.avisos.models import SEGURIDAD
from apps.core.models import RegistroAuditoria
from apps.core.segundo_plano import despues_del_commit

DIAS_DE_UNA_IP_CONOCIDA = 90
_PRODUCTOS_ALCANZADOS = re.compile(r"(\d+) productos (?:actualizados|recalculados)")

ACCIONES = {
    RegistroAuditoria.BLOQUEO_POR_INTENTOS,
    RegistroAuditoria.INICIO_SESION,
    RegistroAuditoria.ALTA_USUARIO,
    RegistroAuditoria.MODIFICACION_USUARIO,
    RegistroAuditoria.MODIFICACION_PRECIO_REFERENCIA,
    RegistroAuditoria.PARAMETRO_MODIFICADO,
}


@receiver(post_save, sender=RegistroAuditoria, dispatch_uid="avisos_alertas_de_seguridad")
def al_auditar(sender, instance, created, **kwargs):
    if created and instance.accion in ACCIONES:
        despues_del_commit(revisar, instance.pk)


def revisar(registro_pk):
    """La alerta que corresponde a esa entrada, si corresponde alguna."""
    registro = RegistroAuditoria.objects.select_related("actor").filter(pk=registro_pk).first()
    if registro is None:
        return
    alerta = {
        RegistroAuditoria.BLOQUEO_POR_INTENTOS: _bloqueo,
        RegistroAuditoria.INICIO_SESION: _ip_nueva,
        RegistroAuditoria.ALTA_USUARIO: _administrador,
        RegistroAuditoria.MODIFICACION_USUARIO: _administrador,
        RegistroAuditoria.MODIFICACION_PRECIO_REFERENCIA: _precios,
        RegistroAuditoria.PARAMETRO_MODIFICADO: _precios,
    }[registro.accion](registro)
    if alerta:
        titulo, parrafos = alerta
        avisar_administradores(
            SEGURIDAD,
            asunto=f"Longbox — seguridad: {titulo}",
            antetitulo="Seguridad",
            titulo=titulo,
            parrafos=parrafos,
            filas=[
                ("Cuándo", timezone.localtime(registro.ocurrido_en).strftime("%d/%m/%Y %H:%M")),
                ("Quién", registro.actor_email or "desconocido"),
                ("IP", registro.ip or "sin dato"),
            ],
            enlace=enlace("core:auditoria"),
            texto_enlace="Ver la auditoría",
        )


def _bloqueo(registro):
    # Sólo de una cuenta que existe: lo mismo que decide el correo al afectado.
    if registro.actor is None:
        return None
    return (
        f"cuenta bloqueada por intentos ({registro.actor.get_rol_display()})",
        [
            f"La cuenta {registro.actor.email} acumuló {registro.detalle}. Si no fue su "
            "dueño, alguien está probando contraseñas."
        ],
    )


def _ip_nueva(registro):
    from apps.accounts.models import Usuario

    usuario = registro.actor
    if usuario is None or usuario.rol == Usuario.CLIENTE or not registro.ip:
        return None
    anteriores = RegistroAuditoria.objects.filter(
        accion=RegistroAuditoria.INICIO_SESION, actor=usuario
    ).exclude(pk=registro.pk)
    if not anteriores.exists():
        return None
    desde = registro.ocurrido_en - timedelta(days=DIAS_DE_UNA_IP_CONOCIDA)
    if anteriores.filter(ip=registro.ip, ocurrido_en__gte=desde).exists():
        return None
    return (
        f"ingreso desde una IP nueva ({usuario.get_rol_display()})",
        [
            f"{usuario.email} inició sesión desde {registro.ip}, que no usó en los últimos "
            f"{DIAS_DE_UNA_IP_CONOCIDA} días. Si no lo reconoce, conviene cambiar la contraseña "
            "y cerrar sus sesiones desde Cuentas."
        ],
    )


def _administrador(registro):
    from apps.accounts.models import Usuario

    objetivo = registro.objetivo
    if not isinstance(objetivo, Usuario):
        return None
    if registro.accion == RegistroAuditoria.ALTA_USUARIO:
        if objetivo.rol != Usuario.ADMINISTRADOR:
            return None
        return (
            "un Administrador nuevo",
            [f"{registro.actor_email} dio de alta a {objetivo.email} como Administrador."],
        )
    if "rol" not in registro.detalle.lower() or "administrador" not in registro.detalle.lower():
        return None
    return (
        "cambio de rol de un Administrador",
        [f"{registro.actor_email} cambió el rol de {objetivo.email}: {registro.detalle}."],
    )


def _precios(registro):
    if (
        registro.accion == RegistroAuditoria.PARAMETRO_MODIFICADO
        and not registro.detalle.startswith("margen global")
    ):
        return None
    alcanzados = _PRODUCTOS_ALCANZADOS.search(registro.detalle)
    if alcanzados is None or int(alcanzados.group(1)) == 0:
        return None
    return (
        f"cambio masivo de precios ({alcanzados.group(1)} productos)",
        [f"{registro.actor_email}: {registro.detalle}."],
    )
