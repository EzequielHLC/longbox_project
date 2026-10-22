"""La tabla de precios de referencia y el margen global (módulo 03).

Las operaciones que cambian precios vienen de a pares: primero se informa a
cuántos productos alcanza el cambio, después se confirma. **El número que se
informa y el conjunto que se toca salen de la misma consulta**: si se escribieran
por separado, tarde o temprano el informe diría una cosa y la propagación haría
otra (plan 03, riesgos).

Todo el dinero es `Decimal`. El margen conserva sus cuatro decimales y el
redondeo al peso se aplica sólo al resultado (`precios.calcular_precio_final`).

Las dos propagaciones alcanzan también a las líneas de carrito de los productos
que tocan (`actualizar_precios`), que es la postcondición que `CO-048` y `CO-053`
dejaban pendiente mientras no existía `LineaCarrito` (B-03-001).
"""

from dataclasses import dataclass
from decimal import Decimal

from django.db import transaction

from apps.catalog import precios, services
from apps.catalog.models import Producto, ProductoEditorial, TablaPrecioReferencia
from apps.core.models import ConfiguracionSistema, RegistroAuditoria


def combinacion(fila):
    return f"{fila.editorial} · {fila.tipo} · {fila.formato}"


def _pesos(valor):
    return f"${Decimal(valor):.2f}"


# ---------------------------------------------------------------------------
# Alta — CO-049
# ---------------------------------------------------------------------------


def registrar(formulario, *, actor, ip=None):
    """El alta no modifica precios ni vincula productos: es una fila nueva."""
    with transaction.atomic():
        fila = formulario.save()
        RegistroAuditoria.registrar(
            accion=RegistroAuditoria.ALTA_PRECIO_REFERENCIA,
            actor=actor,
            objetivo=fila,
            ip=ip,
            detalle=f"{combinacion(fila)}: {_pesos(fila.pvp)}",
        )
    return fila


# ---------------------------------------------------------------------------
# Modificación — CO-047 y CO-048
# ---------------------------------------------------------------------------


def alcanzados_por_modificacion(fila):
    """Los productos a los que llega la propagación de un precio de referencia.

    Los vinculados a la fila, en cualquier estado salvo Cancelado por editorial.
    Un producto con precio a mano no está vinculado (`CO-005`): su precio
    sobrevive al cambio, que es exactamente para lo que se lo corrigió.
    """
    # El precio a mano ya no tiene asociación (B-01-014); se excluye igual, por si
    # una fila vieja la conservara: una propagación nunca pisa una decisión manual.
    return ProductoEditorial.objects.filter(precio_referencia=fila, precio_manual=False).exclude(
        estado=Producto.CANCELADO_EDITORIAL
    )


def solicitar_modificacion(fila):
    """`CO-047`: cuántos productos alcanzará la propagación. No cambia nada."""
    return alcanzados_por_modificacion(fila).count()


@dataclass(frozen=True)
class ResumenDeModificacion:
    combinacion: str
    anterior: Decimal
    nuevo: Decimal
    actualizados: int


def confirmar_modificacion(fila, nuevo_pvp, *, actor, ip=None):
    """`CO-048`: el precio nuevo en la fila y en cada producto vinculado.

    La fila se relee bajo bloqueo: dos administradores que cambian el mismo
    precio a la vez no propagan los dos sobre el mismo valor anterior.
    """
    with transaction.atomic():
        fila = TablaPrecioReferencia.objects.select_for_update().get(pk=fila.pk)
        anterior = fila.pvp
        fila.pvp = nuevo_pvp
        fila.save(update_fields=["pvp", "actualizado_en"])

        alcanzados = alcanzados_por_modificacion(fila)
        productos = Producto.objects.filter(pk__in=alcanzados.values("pk"))
        actualizados = productos.update(precio=nuevo_pvp)
        _actualizar_carritos(productos)

        RegistroAuditoria.registrar(
            accion=RegistroAuditoria.MODIFICACION_PRECIO_REFERENCIA,
            actor=actor,
            objetivo=fila,
            ip=ip,
            detalle=(
                f"{combinacion(fila)}: {_pesos(anterior)} → {_pesos(nuevo_pvp)}; "
                f"{actualizados} productos actualizados"
            ),
        )
    return ResumenDeModificacion(combinacion(fila), anterior, Decimal(nuevo_pvp), actualizados)


# ---------------------------------------------------------------------------
# Baja — CO-050 y CO-051
# ---------------------------------------------------------------------------


def solicitar_baja(fila):
    """`CO-050`: todos los productos vinculados, en cualquier estado (R2)."""
    return ProductoEditorial.objects.filter(precio_referencia=fila).count()


def confirmar_baja(fila, *, actor, ip=None):
    """`CO-051`: la fila se elimina y sus productos quedan sin fuente.

    Conservan el precio y **no** quedan con precio a mano: su precio no fue
    corregido, simplemente ya no tiene de dónde salir. La clave foránea es
    `SET_NULL`, así que desvincularlos es la propia eliminación. Devuelve
    cuántos se desvincularon, o `None` si otro la eliminó antes.
    """
    with transaction.atomic():
        fila = TablaPrecioReferencia.objects.select_for_update().filter(pk=fila.pk).first()
        if fila is None:
            return None
        desvinculados = solicitar_baja(fila)
        descripcion, ultimo = combinacion(fila), fila.pvp
        RegistroAuditoria.registrar(
            accion=RegistroAuditoria.BAJA_PRECIO_REFERENCIA,
            actor=actor,
            ip=ip,
            detalle=(
                f"{descripcion}: último valor {_pesos(ultimo)}; "
                f"{desvinculados} productos desvinculados"
            ),
        )
        fila.delete()
    return desvinculados


# ---------------------------------------------------------------------------
# Restaurar el precio calculado — CO-031
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Restauracion:
    """Lo que `CO-031` informaría antes de guardar, o por qué no aplica."""

    precio_actual: Decimal
    precio_recalculado: Decimal | None = None
    fila: TablaPrecioReferencia | None = None
    motivo: str = ""

    @property
    def aplica(self):
        return self.precio_recalculado is not None


def restauracion_de(producto):
    """Si el producto puede volver a su precio calculado, y a cuál.

    Dos casos (`CO-031`, Notas): el producto con precio a mano, nacional o
    importado, y el nacional sin vínculo cuya combinación tiene fila —el que
    quedó sin fuente al darse de baja su fila—. Usa los valores vigentes.
    """
    editorial = getattr(producto, "productoeditorial", None) or (
        producto if isinstance(producto, ProductoEditorial) else None
    )
    if editorial is None:
        return Restauracion(producto.precio, motivo="Sólo aplica a productos editoriales.")

    if editorial.origen == ProductoEditorial.IMPORTADO:
        if not editorial.precio_manual:
            return Restauracion(editorial.precio, motivo="Su precio ya es el calculado.")
        if editorial.precio_base is None:
            return Restauracion(editorial.precio, motivo="No tiene precio base almacenado.")
        margen = ConfiguracionSistema.obtener().margen_ganancia
        return Restauracion(
            editorial.precio, precios.calcular_precio_final(editorial.precio_base, margen)
        )

    vinculado = editorial.precio_referencia_id is not None
    if vinculado and not editorial.precio_manual:
        return Restauracion(editorial.precio, motivo="Su precio ya sale de la tabla.")
    fila = services.precio_de_referencia(editorial.editorial, editorial.tipo, editorial.formato)
    if fila is None:
        return Restauracion(
            editorial.precio, motivo="Su combinación no tiene fila en la tabla de precios."
        )
    return Restauracion(editorial.precio, fila.pvp, fila=fila)


def restaurar_precio_calculado(producto, *, actor, ip=None):
    """`CO-031`: vuelve a atar el precio a su fuente y lo recalcula."""
    with transaction.atomic():
        editorial = ProductoEditorial.objects.select_for_update().get(pk=producto.pk)
        restauracion = restauracion_de(editorial)
        if not restauracion.aplica:
            return restauracion

        anterior = editorial.precio
        editorial.precio = restauracion.precio_recalculado
        editorial.precio_manual = False
        campos = ["precio", "precio_manual"]
        if restauracion.fila is not None:
            editorial.precio_referencia = restauracion.fila
            campos.append("precio_referencia")
        editorial.save(update_fields=campos)

        RegistroAuditoria.registrar(
            accion=RegistroAuditoria.MODIFICACION_PRODUCTO,
            actor=actor,
            objetivo=editorial,
            ip=ip,
            detalle=(
                f"Se restauró el precio calculado: precio {_pesos(anterior)} → "
                f"{_pesos(editorial.precio)}; precio fijado a mano: no"
            ),
        )
    return restauracion


# ---------------------------------------------------------------------------
# Margen global de importados — CO-052, CO-053 y CO-167
# ---------------------------------------------------------------------------


def importados():
    return ProductoEditorial.objects.filter(origen=ProductoEditorial.IMPORTADO)


def a_recalcular():
    """Los importados con el precio vinculado al margen, en cualquier estado.

    `CO-053` recalcula «todo importado con precio vinculado», sin excluir los
    cancelados por la editorial como sí hace `CO-048` (C-11: mandan los
    contratos). Todos tienen precio base: el campo es obligatorio.
    """
    return importados().filter(precio_manual=False)


@dataclass(frozen=True)
class Simulacion:
    a_recalcular: int
    excluidos_por_precio_manual: int

    @property
    def no_afecta_a_ninguno(self):
        """A1: todos los importados tienen precio a mano."""
        return self.a_recalcular == 0


def hay_importados():
    """La precondición de `CO-052`: al menos un importado con precio base."""
    return importados().exists()


def simular_cambio_de_margen():
    """`CO-052`: el impacto del cambio, antes de aplicarlo. No cambia nada.

    Las dos cifras no dependen del margen nuevo sino de qué importados tienen
    el vínculo intacto: por eso el sistema las puede dar mientras se escribe.
    """
    return Simulacion(
        a_recalcular=a_recalcular().count(),
        excluidos_por_precio_manual=importados().filter(precio_manual=True).count(),
    )


@dataclass(frozen=True)
class ResumenDeMargen:
    anterior: Decimal
    nuevo: Decimal
    recalculados: int
    excluidos_por_precio_manual: int


def confirmar_cambio_de_margen(nuevo_margen, *, actor, ip=None):
    """`CO-053`: el margen nuevo y el precio de cada importado vinculado.

    precio final = precio base × (1 + margen), redondeado al peso. El precio
    base no se toca: es lo que permite recalcular indefinidamente sin
    acumular error.

    La fila única de la configuración se toma con bloqueo durante todo el
    recálculo: un alta de lote importado que lee el margen espera a que
    termine, y no da de alta productos con el margen viejo a mitad del cambio.
    """
    nuevo_margen = Decimal(nuevo_margen)
    with transaction.atomic():
        configuracion = ConfiguracionSistema.objects.select_for_update().get(
            pk=ConfiguracionSistema.obtener().pk
        )
        anterior = configuracion.margen_ganancia
        configuracion.margen_ganancia = nuevo_margen
        configuracion.actualizado_por = actor
        configuracion.save()

        recalcular = list(a_recalcular().only("pk", "precio", "precio_base"))
        for producto in recalcular:
            producto.precio = precios.calcular_precio_final(producto.precio_base, nuevo_margen)
        ProductoEditorial.objects.bulk_update(recalcular, ["precio"], batch_size=500)
        _actualizar_carritos([producto.pk for producto in recalcular])
        excluidos = importados().filter(precio_manual=True).count()

        RegistroAuditoria.registrar(
            accion=RegistroAuditoria.PARAMETRO_MODIFICADO,
            actor=actor,
            objetivo=configuracion,
            ip=ip,
            detalle=(
                f"margen global: {porcentaje(anterior)} → {porcentaje(nuevo_margen)}; "
                f"{len(recalcular)} productos recalculados; "
                f"{excluidos} excluidos por precio a mano"
            ),
        )
    return ResumenDeMargen(anterior, nuevo_margen, len(recalcular), excluidos)


def porcentaje(margen):
    """`CO-167`: el margen expresado como porcentaje, sin perder decimales."""
    valor = (Decimal(margen) * 100).normalize()
    texto = f"{valor:f}".replace(".", ",")
    return f"{texto} %"


def _actualizar_carritos(productos):
    """Las líneas de carrito de estos productos pasan al precio nuevo (B-03-001).

    Se importa acá: el carrito depende del catálogo, y no al revés.
    """
    from apps.tienda.carrito import actualizar_precios

    return actualizar_precios(productos)
