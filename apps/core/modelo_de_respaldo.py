"""El modelo de respaldo: el sistema propone, el Administrador cambia (plan 00, A).

Cuando el modelo activo falla **tres veces seguidas** por conexión o por rechazo
del proveedor —sin servicio, credencial, cuota, límite de pedidos—, el sistema
avisa y propone pasar al modelo de respaldo de Parámetros (`CO-228`). **No cambia
solo** (regla 4 de `CLAUDE.md` en su espíritu: lo que decide sobre el sistema lo
confirma una persona). Una respuesta ilegible no cuenta: dice que el servicio
contesta y que el problema es el prompt o el modelo elegido, y cambiar de servidor
no lo arregla.

Confirmar (`CO-229`) prueba primero que el respaldo conteste; si contesta,
**intercambia** el activo y el respaldo, así se vuelve por el mismo camino.
"""

from django.db import transaction
from django.db.models import F
from django.utils import timezone

from apps.core.models import ConfiguracionSistema, RegistroAuditoria

UMBRAL = 3


class CambioRechazado(ValueError):
    """Lo que el cambio no admite, con el mensaje para la pantalla."""


def _fila():
    return ConfiguracionSistema.objects.filter(pk=ConfiguracionSistema.IDENTIFICADOR)


def anotar_acierto():
    """El servicio contestó: la racha se corta y se puede volver a proponer."""
    _fila().filter(llm_fallas_seguidas__gt=0).update(
        llm_fallas_seguidas=0, llm_cambio_propuesto_en=None
    )


def anotar_falla():
    """Una falla más. En la tercera seguida, si nadie lo pidió todavía, se propone.

    El incremento es en la base (`F`), no en memoria: el reloj por minuto y una
    pantalla pueden fallar a la vez. Y sólo uno de los dos gana el pedido: la marca
    se pone con un `UPDATE` condicionado a que siga vacía.
    """
    ConfiguracionSistema.obtener()
    _fila().update(llm_fallas_seguidas=F("llm_fallas_seguidas") + 1)
    if (
        _fila()
        .filter(llm_fallas_seguidas__gte=UMBRAL, llm_cambio_propuesto_en__isnull=True)
        .update(llm_cambio_propuesto_en=timezone.now())
    ):
        proponer_cambio()


def proponer_cambio():
    """`CO-228` proponerCambioDeModelo: el aviso a los Administradores y su registro.

    No cambia nada del modelo. Si no hay respaldo, el aviso lo dice y manda a
    Parámetros (ambigüedad A5).
    """
    from apps.avisos.canales import avisar_administradores, enlace
    from apps.avisos.models import MODELO
    from apps.core.segundo_plano import despues_del_commit

    configuracion = ConfiguracionSistema.obtener()
    activo = configuracion.llm_modelo or configuracion.llm_url
    respaldo = configuracion.llm_respaldo_modelo or configuracion.llm_respaldo_url
    RegistroAuditoria.registrar(
        accion=RegistroAuditoria.CAMBIO_MODELO_PROPUESTO,
        actor=None,
        objetivo=configuracion,
        detalle=(
            f"El modelo «{activo}» falló {configuracion.llm_fallas_seguidas} veces seguidas. "
            + (
                f"Se propone pasar al respaldo «{respaldo}»."
                if configuracion.tiene_respaldo
                else "No hay modelo de respaldo configurado."
            )
        ),
    )
    if configuracion.tiene_respaldo:
        aviso = {
            "asunto": "Longbox — el modelo de lenguaje no responde",
            "antetitulo": "Modelo de lenguaje",
            "titulo": "¿Pasamos al modelo de respaldo?",
            "parrafos": [
                f"El modelo «{activo}» falló {UMBRAL} veces seguidas. Los correos de los "
                "proveedores no se están procesando.",
                "El sistema no cambia solo: confirmá el cambio y antes de hacerlo se prueba "
                "que el respaldo conteste.",
            ],
            "filas": [
                ("Activo", activo),
                ("Respaldo", respaldo),
            ],
            "enlace": enlace("suppliers:cambiar_modelo"),
            "texto_enlace": "Cambiar al respaldo",
        }
    else:
        aviso = {
            "asunto": "Longbox — el modelo de lenguaje no responde",
            "antetitulo": "Modelo de lenguaje",
            "titulo": "El modelo de lenguaje no responde",
            "parrafos": [
                f"El modelo «{activo}» falló {UMBRAL} veces seguidas y no hay un modelo de "
                "respaldo configurado. Revisalo en el diagnóstico, o cargá un respaldo en "
                "Parámetros globales.",
            ],
            "enlace": enlace("suppliers:diagnostico_llm"),
            "texto_enlace": "Ver el diagnóstico",
        }
    despues_del_commit(avisar_administradores, MODELO, **aviso)


def confirmar_cambio(actor, *, ip=None, probar=None):
    """`CO-229` confirmarCambioDeModelo: intercambia el activo y el respaldo.

    Antes prueba que el respaldo conteste (ambigüedad A6); si no, no cambia nada.
    `probar` es la comprobación de disponibilidad, para poder reemplazarla en las
    pruebas; por omisión, la de `CU-CFG-LLM` contra el perfil de respaldo.
    """
    from apps.core import llm

    configuracion = ConfiguracionSistema.obtener()
    if not configuracion.tiene_respaldo:
        raise CambioRechazado("No hay un modelo de respaldo configurado en Parámetros globales.")
    estado = (probar or llm.estado)(llm.perfil_de_respaldo(configuracion))
    if not estado.disponible:
        raise CambioRechazado(f"El modelo de respaldo tampoco responde: {estado.detalle}")
    if estado.modelo_disponible is False:
        raise CambioRechazado(
            f"El servidor del respaldo contesta pero no ofrece el modelo "
            f"«{configuracion.llm_respaldo_modelo}». Revisá el nombre en Parámetros globales."
        )

    with transaction.atomic():
        c = ConfiguracionSistema.objects.select_for_update().get(pk=configuracion.pk)
        antes = f"{c.get_llm_modo_display()} {c.llm_url} ({c.llm_modelo or 'el que tenga cargado'})"
        (
            c.llm_modo,
            c.llm_url,
            c.llm_modelo,
            c.llm_api_key,
            c.llm_respaldo_modo,
            c.llm_respaldo_url,
            c.llm_respaldo_modelo,
            c.llm_respaldo_api_key,
        ) = (
            c.llm_respaldo_modo,
            c.llm_respaldo_url,
            c.llm_respaldo_modelo,
            c.llm_respaldo_api_key,
            c.llm_modo,
            c.llm_url,
            c.llm_modelo,
            c.llm_api_key,
        )
        c.llm_fallas_seguidas = 0
        c.llm_cambio_propuesto_en = None
        c.actualizado_por = actor
        c.save()
        # La clave no entra en la auditoría, como en Parámetros: el log es para siempre.
        RegistroAuditoria.registrar(
            accion=RegistroAuditoria.CAMBIO_MODELO,
            actor=actor,
            objetivo=c,
            ip=ip,
            detalle=(
                f"Activo: {antes} → {c.get_llm_modo_display()} {c.llm_url} "
                f"({c.llm_modelo or 'el que tenga cargado'}). El anterior quedó como respaldo."
            ),
        )
    return c
