"""Reglas de proveedores que no son de una pantalla en particular.

Están acá y no en las vistas porque el informe de impacto de CU-PRV-BAJ tiene que
poder calcularse sin levantar un request —lo van a necesitar los reportes y, más
adelante, el ciclo de restock— y porque describir los cambios para la auditoría
es la misma operación en el alta, la edición y la baja.

La ingesta de correos está acá por el mismo motivo, y con más razón: la va a
invocar una tarea de fondo, un comando de consola y —cuando exista— la lectura
de la casilla, ninguno de los tres con un request de por medio.
"""

from dataclasses import dataclass

from django.core.files.base import ContentFile
from django.db import IntegrityError, transaction
from django.utils import timezone

from apps.catalog import borradores as borradores_de_producto
from apps.core import cambios, llm
from apps.core.models import RegistroAuditoria
from apps.suppliers import correos
from apps.suppliers import extraccion as extraccion_de_novedades
from apps.suppliers.models import CorreoProveedor, Proveedor

# Qué campos se auditan con su par anterior → nuevo (CU-PRV-EDI postcondición). Las
# notas internas entran: son el lugar donde queda escrito por qué se dejó de
# trabajar con alguien, y un cambio ahí importa tanto como uno del teléfono.
#
# Los tres últimos importan por un motivo más fuerte que la trazabilidad: los
# tres cambian el comportamiento del pipeline sin que se vea en ninguna
# pantalla del catálogo. Apagar `procesa_novedades` deja de generar borradores
# **en silencio**, y cambiar la editorial cambia bajo qué sello nacen todos los
# borradores siguientes. Si no quedaran en el log, "por qué de Ivrea no llega
# nada desde marzo" sería una pregunta sin respuesta.
CAMPOS_AUDITADOS = {  # noqa: RUF012
    "razón social": lambda p: p.razon_social,
    "correo comercial": lambda p: p.correo_comercial,
    "nombre de contacto": lambda p: p.nombre_contacto,
    "teléfono": lambda p: p.telefono,
    "notas": lambda p: p.notas,
    "procesamiento de novedades": lambda p: "sí" if p.procesa_novedades else "no",
    "editorial": lambda p: str(p.editorial) if p.editorial else "varias",
    "tipo habitual": lambda p: str(p.tipo_por_defecto) if p.tipo_por_defecto else "sin declarar",
}


@dataclass
class ImpactoDeBaja:
    """Lo que CU-PRV-BAJ paso 3 le tiene que mostrar al Administrador antes de bajar.

    El CU pide dos cifras: las propuestas de restock afectadas y los productos
    del catálogo vinculados. La segunda se puede calcular; la primera no, porque
    el módulo 05, Restock, todavía no existe. Se declara igual
    y en `None` —no en cero— para que la pantalla pueda decir "no se puede
    calcular todavía" en vez de afirmar que no hay ninguna, que sería mentir
    sobre un dato que el CU considera parte de la decisión.
    """

    productos_vinculados: int
    propuestas_de_restock: int | None = None

    @property
    def hay_impacto(self):
        return bool(self.productos_vinculados)


def calcular_impacto_de_baja(proveedor):
    """CU-PRV-BAJ paso 2 — el mapeo de impacto previo a la confirmación."""
    return ImpactoDeBaja(productos_vinculados=proveedor.productos.count())


def cambios_entre(anterior, nuevo):
    """`{campo: (valor_anterior, valor_nuevo)}` de los campos que cambiaron."""
    return cambios.entre(anterior, nuevo, CAMPOS_AUDITADOS)


def describir_cambios(lo_que_cambio):
    """Texto para el log: no alcanza con el estado final, va el par completo."""
    return cambios.describir(lo_que_cambio)


# ---------------------------------------------------------------------------
# Ingesta de correos (CU-ALT-NOV pasos 1 a 3, con la aprobación humana de por medio)
# ---------------------------------------------------------------------------


class MotivoDeDescarte:
    """Por qué un correo no entró a la cola. Son los casos que el CU enumera."""

    SIN_IDENTIFICADOR = "sin_identificador"
    REMITENTE_DESCONOCIDO = "remitente_desconocido"
    REPETIDO = "repetido"


@dataclass
class ResultadoDeIngesta:
    """Qué pasó con un correo. Nunca es una excepción: siempre hay que seguir.

    E1 del CU-ALT-NOV es taxativo en esto —un remitente no registrado se loguea y el
    ciclo continúa con el siguiente mensaje— y lo mismo vale para el resto: un
    correo raro no puede tumbar la lectura de la casilla entera.
    """

    correo: CorreoProveedor | None = None
    motivo: str = ""

    @property
    def ingresado(self):
        """Entró a la cola *en esta pasada*. Un repetido no cuenta."""
        return self.correo is not None and not self.motivo


def ingerir(datos, nombre_archivo=""):
    """Archiva un correo y lo deja pendiente de aprobación, si corresponde.

    Devuelve siempre un `ResultadoDeIngesta`, nunca levanta: quien llame está
    recorriendo una casilla y tiene que poder seguir con el mensaje siguiente.

    Los tres motivos por los que un correo no entra:

    - **Sin identificador.** Sin `Message-ID` no hay forma de saber si ya se
      leyó, y sin eso cada pasada del ciclo lo volvería a encolar. Se descarta
      en vez de inventarle uno: un identificador fabricado por nosotros daría
      distinto en cada lectura y el efecto sería el mismo duplicado.
    - **Remitente desconocido** (E1). No es solo "no está registrado": también
      cae acá el proveedor dado de baja y el que tiene el procesamiento apagado,
      porque los tres significan lo mismo para el pipeline.
    - **Repetido.** Ya está en la cola. Se devuelve el que ya existe, no se
      crea otro ni se pisa el anterior —que puede estar ya resuelto—.
    """
    leido = correos.leer(datos)

    if not leido.message_id:
        return ResultadoDeIngesta(motivo=MotivoDeDescarte.SIN_IDENTIFICADOR)

    proveedor = Proveedor.objects.remitente_valido(leido.remitente)
    if proveedor is None:
        return ResultadoDeIngesta(motivo=MotivoDeDescarte.REMITENTE_DESCONOCIDO)

    existente = CorreoProveedor.objects.filter(message_id=leido.message_id).first()
    if existente is not None:
        return ResultadoDeIngesta(correo=existente, motivo=MotivoDeDescarte.REPETIDO)

    try:
        with transaction.atomic():
            correo = CorreoProveedor(
                proveedor=proveedor,
                message_id=leido.message_id,
                remitente=leido.remitente,
                asunto=leido.asunto[:500],
                fecha=leido.fecha,
                html=leido.html,
                contenido=leido.contenido,
                imagenes=[imagen.resumen() for imagen in leido.imagenes],
            )
            correo.archivo.save(
                nombre_archivo or _nombre_de_archivo(correo.message_id),
                ContentFile(datos),
                save=False,
            )
            correo.save()
    except IntegrityError:
        # Carrera: entre la consulta de arriba y el insert, otra pasada encoló
        # el mismo mensaje. La restricción de la base es la que garantiza que no
        # haya dos, y acá se resuelve como lo que es: un repetido.
        return ResultadoDeIngesta(
            correo=CorreoProveedor.objects.filter(message_id=leido.message_id).first(),
            motivo=MotivoDeDescarte.REPETIDO,
        )

    return ResultadoDeIngesta(correo=correo)


def descartar(correo, actor, motivo):
    """Saca un correo de la cola sin procesarlo.

    Es la respuesta a "esto no es un anuncio de novedades": una factura, una
    promoción, un saludo. Exige un motivo por el mismo criterio con el que CU-ALT-REV
    lo exige al rechazar un borrador — sin él, la cola resuelta no explica nada
    dentro de tres meses.
    """
    correo.estado = CorreoProveedor.DESCARTADO
    correo.motivo = motivo
    correo.resuelto_por = actor
    correo.resuelto_en = timezone.now()
    correo.save(update_fields=["estado", "motivo", "resuelto_por", "resuelto_en"])
    return correo


class CorreoYaResuelto(Exception):
    """El correo ya no está en el estado que la operación exige.

    Es `CO-017` E1: otro Administrador lo aprobó mientras éste lo tenía
    abierto. Lleva el estado actual para informarlo.
    """

    def __init__(self, correo):
        super().__init__(correo.get_estado_display())
        self.correo = correo


def _tomar_para_procesar(correo_pk, estados_de_partida, actor):
    """Pasa el correo a *En proceso* si todavía está en uno de los estados de partida.

    La transición se hace con el correo bloqueado y en su propia transacción,
    que se confirma **antes** de llamar al modelo: así una segunda aprobación
    concurrente ve *En proceso* y no vuelve a procesarlo (`CO-017` E1), y el
    bloqueo no queda tomado durante los minutos que puede tardar la extracción.
    """
    with transaction.atomic():
        correo = CorreoProveedor.objects.select_for_update().get(pk=correo_pk)
        if correo.estado not in estados_de_partida:
            raise CorreoYaResuelto(correo)
        correo.estado = CorreoProveedor.EN_PROCESO
        correo.resuelto_por = actor
        correo.resuelto_en = timezone.now()
        correo.save(update_fields=["estado", "resuelto_por", "resuelto_en"])
    return correo


def aprobar_correo(correo_pk, *, actor, ip=None):
    """`CO-017 aprobarCorreoParaProcesamiento`.

    Autoriza el procesamiento de un correo *Pendiente de aprobación*, ejecuta la
    extracción y genera los borradores. El correo pasa por *En proceso* y
    termina *Procesado* o *Falló el procesamiento* (E4). Levanta
    `CorreoYaResuelto` si el correo ya no estaba pendiente (E1).
    """
    correo = _tomar_para_procesar(correo_pk, (CorreoProveedor.PENDIENTE,), actor)
    return _procesar(correo, actor=actor, ip=ip)


def reprocesar_correo(correo_pk, *, actor, ip=None):
    """`CO-019 reprocesarCorreo`.

    Vuelve a extraer un correo *Procesado* o *Falló el procesamiento*. Sólo si
    la extracción tiene éxito se reemplazan los borradores abiertos; los
    confirmados y los rechazados no se tocan nunca, y si la extracción falla
    los abiertos se conservan.
    """
    correo = _tomar_para_procesar(
        correo_pk, (CorreoProveedor.PROCESADO, CorreoProveedor.FALLIDO), actor
    )
    return _procesar(correo, actor=actor, ip=ip)


def _procesar(correo, *, actor, ip):
    resultado = extraer_novedades(correo, actor=actor, ip=ip)
    if resultado.generacion is None:
        # La generación de borradores audita su propia operación. Si no la
        # hubo (E4), la decisión del Administrador igual queda registrada: el
        # CU-PRV-COL la declara auditada en cualquier caso.
        RegistroAuditoria.registrar(
            accion=RegistroAuditoria.BORRADORES_GENERADOS,
            actor=actor,
            objetivo=correo,
            ip=ip,
            detalle=f"«{correo.asunto or 'sin asunto'}»: sin borradores. {correo.motivo}",
        )
    return resultado


def _nombre_de_archivo(message_id):
    """Un nombre de archivo legible derivado del identificador del mensaje.

    El identificador trae ángulos y una arroba que el almacenamiento sanea por
    su cuenta, y el resultado es impronunciable. Se limpia acá para que la
    carpeta de correos archivados se pueda leer: el que va a mirarla es alguien
    buscando un mensaje puntual.
    """
    limpio = "".join(
        caracter if caracter.isalnum() or caracter in "-_." else "-"
        for caracter in message_id.strip("<>")
    )
    return f"{limpio.strip('-')[:80] or 'correo'}.eml"


@dataclass
class ResultadoDeProcesamiento:
    """Lo que dejó procesar un correo: lo que el modelo entendió y lo que se armó.

    Son dos cosas distintas y las dos hacen falta arriba. El comando de consola
    las reporta por separado —"entendió cinco productos, generó tres, omitió dos
    por duplicado"—, y esa diferencia es justamente la que dice si el pipeline
    está funcionando o si el catálogo ya tenía todo.

    Se comporta como verdadero o falso según **la extracción**, que es la parte
    que puede fallar: una generación que no produjo nada porque estaba todo
    duplicado no es un error.
    """

    extraccion: object
    generacion: object = None

    def __bool__(self):
        return bool(self.extraccion)


def portadas_de(correo):
    """Las imágenes embebidas del correo, por identificador.

    Sale de releer el `.eml` archivado y no de la tabla: `CorreoProveedor.imagenes`
    guarda a propósito el resumen —identificador, tipo, tamaño— y no los bytes,
    porque duplicarlos engordaría la tabla sin agregar nada. El original está
    guardado justamente para esto.

    Devuelve un diccionario vacío si el archivo no está o no se puede leer. Que
    falte una portada no interrumpe el procesamiento del correo (CU-ALT-NOV): los
    borradores quedan con la portada pendiente y se adjunta a mano después.
    """
    if not correo.archivo:
        return {}
    try:
        with correo.archivo.open("rb") as archivo:
            leido = correos.leer(archivo.read())
    except (OSError, ValueError):
        return {}
    return {imagen.cid: imagen for imagen in leido.imagenes if imagen.cid}


def extraer_novedades(correo, *, actor=None, ip=None):
    """Le pasa el correo al modelo, guarda lo que entendió y arma los borradores.

    **Sigue sin crear productos**, que es lo que importa: un borrador es una
    propuesta que espera la confirmación de una persona en CU-ALT-REV. Lo que el
    modelo devolvió queda igual guardado en el correo, y la ficha lo muestra —
    así, cuando un borrador salga raro, se puede ver contra qué texto se armó
    sin tener que volver a gastar una corrida del modelo.

    El estado del correo cambia según cómo salga (`CO-017`):

    - **Procesado** si el modelo respondió e identificó al menos un producto.
    - **Falló el procesamiento** si no hubo respuesta utilizable **o si no
      identificó ningún producto** (`CO-017` E4). El correo queda en la cola
      para reprocesarlo: el fallo puede deberse a una indisponibilidad
      transitoria y no al contenido. Hasta el 2026-09-30 un correo sin
      productos quedaba Procesado; se corrigió a favor del contrato (B-04-004).

    Nunca levanta: quien llama puede estar recorriendo una cola.
    """
    resultado = extraccion_de_novedades.extraer(correo.contenido, cids=correo.cids)

    correo.extraccion = resultado.como_json()
    correo.version_prompt = resultado.version_prompt
    identifico_productos = bool(resultado) and bool(resultado.productos)
    if identifico_productos:
        correo.estado = CorreoProveedor.PROCESADO
        correo.motivo = ""
    else:
        correo.estado = CorreoProveedor.FALLIDO
        correo.motivo = _motivo_del_fallo(resultado)
    correo.save(update_fields=["extraccion", "version_prompt", "estado", "motivo"])

    # Los borradores se arman sólo si hubo algo que entender. Un correo fallido
    # no genera nada, y los borradores abiertos que ya tenía se conservan: sólo
    # una extracción exitosa los reemplaza (`CO-019`).
    generacion = None
    if identifico_productos and resultado.intencion == extraccion_de_novedades.NOVEDADES:
        generacion = borradores_de_producto.generar(
            correo, portadas=portadas_de(correo), actor=actor, ip=ip
        )
    return ResultadoDeProcesamiento(extraccion=resultado, generacion=generacion)


def _motivo_del_fallo(resultado):
    """En castellano y con la causa separada, que es lo que se arregla distinto."""
    if resultado:
        return (
            "El modelo no identificó ningún producto en el correo. Si es un anuncio de "
            "novedades, revise el contenido extraído y vuelva a procesarlo."
        )
    if resultado.error == llm.SIN_SERVICIO:
        return (
            "No se pudo consultar el modelo de lenguaje. Verifique que el servicio "
            "esté corriendo y vuelva a intentar."
        )
    return (
        "El modelo respondió algo que no se pudo interpretar. Suele ser el prompt "
        "o el modelo elegido, no el correo."
    )
