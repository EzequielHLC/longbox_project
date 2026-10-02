"""Revisar y confirmar borradores (CU-ALT-REV).

Es el paso donde una persona convierte una propuesta del modelo en catálogo. La
línea que ordena todo el archivo:

> **El modelo propone, la persona aplica.** Nada de acá crea un producto sin una
> acción explícita del Administrador, y ninguna validación se saltea porque el
> dato "ya venía revisado" del pipeline.

Las reglas del CU que más fácil se implementan mal, y cómo quedaron:

- **Confirmar valida de nuevo contra el catálogo.** Entre que el borrador se
  generó y que alguien lo confirma pueden pasar días, y en el medio el producto
  pudo cargarse a mano. Volver a chequear el duplicado no es redundancia: la
  comprobación del pipeline caducó.
- **La confianza baja se revisa campo por campo**, no con una casilla genérica
  de "revisé este borrador". Es lo que pide el paso 3, y sin la granularidad no
  hay diferencia entre mirar un dato dudoso y decir que se miró.
- **La confirmación en lote excluye, no bloquea.** Un borrador con confianza
  baja o con un bloqueante vacío se saltea informando por qué, y los demás se
  confirman igual. Es la misma distinción de CU-ALT-NAC entre una exclusión esperada
  y un fallo transaccional.
"""

from dataclasses import dataclass, field

from django.db import IntegrityError, transaction
from django.utils import timezone

from apps.catalog import precios, services
from apps.catalog.models import (
    BorradorProducto,
    Producto,
    ProductoEditorial,
    SesionRevision,
)
from apps.core.models import RegistroAuditoria
from apps.suppliers import pedidos

# Por qué un borrador no se pudo confirmar. Constantes y no cadenas sueltas
# porque la pantalla las muestra y el resumen de la sesión las cuenta.
BLOQUEANTES_VACIOS = "bloqueantes_vacios"
CONFIANZA_SIN_REVISAR = "confianza_sin_revisar"
YA_EXISTE = "ya_existe"
NO_ESTA_ABIERTO = "no_esta_abierto"
CATALOGO_DADO_DE_BAJA = "catalogo_dado_de_baja"

MOTIVOS = {
    BLOQUEANTES_VACIOS: "Le faltan campos obligatorios",
    CONFIANZA_SIN_REVISAR: "Tiene campos de confianza baja sin revisar",
    YA_EXISTE: "Mientras tanto se cargó al catálogo",
    NO_ESTA_ABIERTO: "Ya estaba resuelto",
    CATALOGO_DADO_DE_BAJA: "Tiene una editorial, un tipo o un formato dados de baja",
}


@dataclass
class Confirmacion:
    """El resultado de intentar confirmar un borrador."""

    borrador: BorradorProducto
    producto: Producto | None = None
    motivo: str = ""
    producto_existente: int | None = None

    def __bool__(self):
        return self.producto is not None

    @property
    def motivo_legible(self):
        return MOTIVOS.get(self.motivo, self.motivo)


@dataclass
class ResultadoDeLote:
    """Lo que dejó una confirmación en lote (CU-ALT-REV paso 4)."""

    confirmadas: list = field(default_factory=list)
    excluidas: list = field(default_factory=list)

    @property
    def productos(self):
        return [c.producto for c in self.confirmadas]


# ---------------------------------------------------------------------------
# La sesión
# ---------------------------------------------------------------------------


def sesion_abierta_de(revisor):
    """La sesión en curso de ese revisor, o `None`.

    Hay **una por revisor** y no una global: dos administradores revisando a la
    vez son dos tandas distintas, y mezclarlas haría que el pedido consolidado
    de uno se lleve los productos del otro.
    """
    return SesionRevision.objects.filter(revisor=revisor, estado=SesionRevision.ABIERTA).first()


def abrir_o_seguir(revisor):
    """La sesión en curso, creándola si es la primera acción de la tanda.

    Se crea acá y no al entrar a la pantalla: mirar la cola no es revisar, y
    abrir una sesión por cada visita llenaría la tabla de tandas vacías.
    """
    return sesion_abierta_de(revisor) or SesionRevision.objects.create(revisor=revisor)


# ---------------------------------------------------------------------------
# Confirmar
# ---------------------------------------------------------------------------


def confirmar(borrador, *, actor, ip=None, en_lote=False):
    """Convierte un borrador en un producto del catálogo (CU-ALT-REV paso 3).

    `en_lote` cambia **una** cosa: en lote, un borrador con confianza baja sin
    revisar se excluye en vez de intentar confirmarse. Individualmente ese
    borrador sí se puede confirmar, porque la pantalla exige la acción
    afirmativa campo por campo antes de dejar apretar el botón.

    Devuelve una `Confirmacion`, nunca levanta por un borrador que no se pueda
    confirmar: eso es una exclusión esperada, no un fallo.
    """
    with transaction.atomic():
        # Se relee bajo bloqueo y se vuelve a mirar el estado **adentro** de la
        # transacción. Es lo que evita que dos confirmaciones simultáneas del
        # mismo borrador creen el producto dos veces: la segunda encuentra el
        # borrador ya confirmado y se retira.
        actual = BorradorProducto.objects.select_for_update().get(pk=borrador.pk)
        if not actual.esta_abierto:
            return Confirmacion(borrador=actual, motivo=NO_ESTA_ABIERTO)

        faltantes = actual.campos_bloqueantes_vacios
        if faltantes:
            return Confirmacion(borrador=actual, motivo=BLOQUEANTES_VACIOS)

        # `CO-140`, `CO-221`, `CO-148`: lo dado de baja no se asigna a un
        # producto nuevo por ninguna vía, tampoco por la del correo.
        if actual.catalogos_dados_de_baja:
            return Confirmacion(borrador=actual, motivo=CATALOGO_DADO_DE_BAJA)

        if en_lote and actual.confianzas_bajas_sin_revisar:
            return Confirmacion(borrador=actual, motivo=CONFIANZA_SIN_REVISAR)

        # El duplicado se vuelve a chequear: entre la generación del borrador y
        # este momento pueden haber pasado días, y el producto pudo cargarse a
        # mano desde el alta en lote.
        existente = services.buscar_duplicado(
            actual.titulo,
            actual.volumen,
            actual.tipo,
            actual.formato,
            actual.editorial,
            actual.isbn,
        )
        if existente is not None:
            return Confirmacion(borrador=actual, motivo=YA_EXISTE, producto_existente=existente.pk)

        try:
            producto = _crear_producto(actual)
        except IntegrityError:
            # Carrera contra otra alta: la restricción de la base es la que
            # realmente garantiza la unicidad, y acá se la trata como lo que es
            # —un duplicado— y no como un error de sistema.
            existente = services.buscar_duplicado(
                actual.titulo,
                actual.volumen,
                actual.tipo,
                actual.formato,
                actual.editorial,
                actual.isbn,
            )
            return Confirmacion(
                borrador=actual,
                motivo=YA_EXISTE,
                producto_existente=existente.pk if existente else None,
            )

        sesion = abrir_o_seguir(actor)
        actual.estado = BorradorProducto.CONFIRMADO
        actual.producto = producto
        actual.sesion = sesion
        actual.resuelto_por = actor
        actual.resuelto_en = timezone.now()
        actual.save(update_fields=["estado", "producto", "sesion", "resuelto_por", "resuelto_en"])

    # Una entrada por confirmación, además del resumen del cierre. Son dos
    # preguntas distintas: "qué pasó en esta tanda" la contesta la sesión,
    # y "de dónde salió este producto" solo la contesta esta.
    RegistroAuditoria.registrar(
        RegistroAuditoria.BORRADOR_CONFIRMADO,
        actor=actor,
        ip=ip,
        objetivo=producto,
        detalle=(
            f"«{producto}» desde el borrador #{actual.pk} "
            f"(correo #{actual.correo_id}, {actual.proveedor}); "
            f"stock inicial {actual.stock_inicial}"
        ),
    )
    return Confirmacion(borrador=actual, producto=producto)


def _crear_producto(borrador):
    """El producto que sale de un borrador, con su precio ya resuelto.

    **El origen es `nacional`** y no es una suposición: el correo trae el PVP ya
    fijado por la editorial, que es exactamente la forma en que se arma el precio
    de un producto nacional. Un importado se calcula desde el costo de origen con
    el CRE, y de eso el pipeline no sabe nada.
    """
    referencia = services.precio_de_referencia(borrador.editorial, borrador.tipo, borrador.formato)
    precio = precios.redondear_a_peso(borrador.precio)

    # `precio_manual` sigue el criterio de A4: si el precio que se confirma no es
    # el de la tabla, alguien lo decidió a propósito y la propagación de CU-PVP-MAR no
    # debe pisárselo. Sin fila de referencia no hay de dónde propagar, así que la
    # marca no aplica.
    manual = referencia is not None and precios.redondear_a_peso(referencia.pvp) != precio

    return ProductoEditorial.objects.create(
        titulo=borrador.titulo,
        volumen=borrador.volumen,
        isbn=borrador.isbn,
        editorial=borrador.editorial,
        tipo=borrador.tipo,
        formato=borrador.formato,
        origen=ProductoEditorial.NACIONAL,
        estado=borrador.estado_sugerido,
        precio=precio,
        precio_base=borrador.precio,
        precio_referencia=referencia,
        precio_manual=manual,
        fecha_llegada=borrador.fecha_llegada,
        stock=borrador.stock_inicial,
        descripcion=borrador.sinopsis,
        autor=borrador.autor,
        solo_adultos=borrador.solo_adultos,
        portada=borrador.portada,
        # A4 de proveedores: el producto nace atado al proveedor que lo anunció.
        # Es la única vía por la que ese dato se llena — las altas manuales no
        # lo piden.
        proveedor=borrador.proveedor,
    )


def confirmar_en_lote(borradores, *, actor, ip=None):
    """Confirma varios de una sola acción, excluyendo lo que no corresponde.

    La exclusión **no bloquea a los demás**, que es lo que pide el CU: un
    borrador de confianza baja metido en la selección se saltea informando por
    qué y queda en cola para revisión individual.
    """
    resultado = ResultadoDeLote()
    for borrador in borradores:
        confirmacion = confirmar(borrador, actor=actor, ip=ip, en_lote=True)
        if confirmacion:
            resultado.confirmadas.append(confirmacion)
        else:
            resultado.excluidas.append(confirmacion)
    return resultado


# ---------------------------------------------------------------------------
# Rechazar
# ---------------------------------------------------------------------------


def rechazar(borrador, *, actor, motivo, ip=None):
    """Descarta un borrador. **El motivo es obligatorio** (CU-ALT-REV).

    Es el mismo criterio con el que el descarte de un correo lo exige: una cola
    llena de rechazos sin explicación no sirve para entender nada después, ni
    para decidir a qué proveedores conviene dejarles el procesamiento prendido.
    """
    motivo = (motivo or "").strip()
    if not motivo:
        raise ValueError("El rechazo de un borrador exige un motivo.")

    with transaction.atomic():
        actual = BorradorProducto.objects.select_for_update().get(pk=borrador.pk)
        if not actual.esta_abierto:
            return None

        sesion = abrir_o_seguir(actor)
        actual.estado = BorradorProducto.RECHAZADO
        actual.motivo_rechazo = motivo
        actual.sesion = sesion
        actual.resuelto_por = actor
        actual.resuelto_en = timezone.now()
        actual.save(
            update_fields=[
                "estado",
                "motivo_rechazo",
                "sesion",
                "resuelto_por",
                "resuelto_en",
            ]
        )

    RegistroAuditoria.registrar(
        RegistroAuditoria.BORRADOR_RECHAZADO,
        actor=actor,
        ip=ip,
        objetivo=actual,
        detalle=f"«{actual}» — {motivo}",
    )
    return actual


# ---------------------------------------------------------------------------
# Cerrar la sesión (CU-ALT-REV pasos 5 y 6)
# ---------------------------------------------------------------------------


def cerrar(sesion, *, actor, ip=None):
    """Cierra la tanda, manda un pedido por proveedor y lo deja auditado.

    **Un correo por proveedor, con los productos de esta sesión.** No reabre
    pedidos de sesiones anteriores: dos tandas el mismo día van en dos correos
    separados, porque son dos decisiones distintas y el proveedor tiene que
    poder tratarlas como tales.

    **Una sesión sin confirmaciones no manda nada.** Solo rechazos, o ninguna
    acción, queda registrada con ese resultado. Mandar un correo vacío sería
    peor que no mandarlo.
    """
    confirmados = list(
        sesion.confirmados.select_related("proveedor", "producto").order_by("proveedor", "titulo")
    )

    envios = [
        _pedir_a(proveedor, borradores)
        for proveedor, borradores in _por_proveedor(confirmados).items()
    ]

    sesion.estado = SesionRevision.CERRADA
    sesion.cerrada_en = timezone.now()
    sesion.envios = [envio.como_json() for envio in envios]
    sesion.save(update_fields=["estado", "cerrada_en", "envios"])

    _auditar_cierre(sesion, confirmados, envios, actor=actor, ip=ip)
    return envios


def _por_proveedor(borradores):
    """Agrupa conservando el orden, para que el resumen sea reproducible."""
    grupos = {}
    for borrador in borradores:
        grupos.setdefault(borrador.proveedor, []).append(borrador)
    return grupos


def _pedir_a(proveedor, borradores):
    lineas = [
        pedidos.LineaDePedido(
            titulo=borrador.titulo,
            volumen=borrador.volumen,
            isbn=borrador.isbn,
            cantidad=borrador.stock_inicial,
        )
        for borrador in borradores
    ]
    return pedidos.enviar_pedido(proveedor, lineas)


def _auditar_cierre(sesion, confirmados, envios, *, actor, ip):
    """Una entrada por sesión, con lo que el paso 6 pide registrar."""
    fallidos = [envio for envio in envios if not envio]
    partes = [
        f"sesión #{sesion.pk}",
        f"{len(confirmados)} confirmado(s)",
        f"{sesion.rechazados.count()} rechazado(s)",
        f"{BorradorProducto.objects.pendientes().count()} pendiente(s) en la cola",
        f"{len(envios) - len(fallidos)} correo(s) de pedido enviado(s)",
    ]
    if fallidos:
        # Se nombra a cada proveedor: el CU pide notificar **cuál** falló, y sin
        # el nombre el aviso no sirve para ir a mandarlo a mano.
        nombres = ", ".join(str(envio.proveedor) for envio in fallidos)
        partes.append(f"{len(fallidos)} fallido(s): {nombres}")

    RegistroAuditoria.registrar(
        RegistroAuditoria.SESION_REVISION_CERRADA,
        actor=actor,
        ip=ip,
        objetivo=sesion,
        detalle="; ".join(partes),
    )
