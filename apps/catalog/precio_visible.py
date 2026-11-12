"""El precio visible de un producto (plan 07 y plan 03, segundas partes).

Es el precio que leen la tienda, el carrito y, cuando exista, el mostrador. Sale
de **una sola función** para que los dos canales no puedan diferir: un canal que
leyera `producto.precio` directamente cobraría sin la oferta vigente.

El precio guardado del producto no cambia nunca por una oferta. La oferta
modifica lo que se ve y se cobra, y por eso darla de baja o dejarla vencer
restaura el precio sin tener que recordar cuál era.

**Qué oferta aplica.** Una oferta descuenta hoy si no está dada de baja y hoy
está entre sus fechas, ambas incluidas: no hace falta que el Temporizador haya
corrido (plan 03, segunda parte, ambigüedades 1 y 2). Si a un producto le
aplican varias, manda la más específica: producto, etiqueta, grupo de
etiquetas, editorial y tipo, en ese orden (plan 03, tercera parte).

**Cuánto descuenta.** Todo en `Decimal`. El resultado se redondea al peso, como
cualquier precio de venta, y nunca baja de $1 (`CO-055`, I-09).
"""

from decimal import Decimal

from django.utils import timezone

from apps.catalog import precios
from apps.catalog.models import Oferta

PRECIO_MINIMO = Decimal("1.00")


def hoy_local():
    return timezone.localdate()


def descontar(precio, oferta):
    """El precio con el descuento de la oferta, redondeado al peso y con piso en $1."""
    precio = Decimal(precio)
    if oferta.tipo_descuento == Oferta.PORCENTAJE:
        resultado = precio * (Decimal("100") - oferta.valor) / Decimal("100")
    else:
        resultado = precio - oferta.valor
    return max(precios.redondear_a_peso(resultado), PRECIO_MINIMO)


class OfertasDelDia:
    """Las ofertas que descuentan en una fecha, leídas de una sola vez.

    Para las pantallas que muestran muchos productos: el catálogo, el carrito,
    la ficha de una oferta. Una consulta para las ofertas y, sólo si hay ofertas
    por editorial, etiqueta o grupo, una más para saber las editoriales y las
    etiquetas de los productos (`anotar` las lee juntas).

    **Qué oferta aplica** (plan 03, tercera parte): la más específica, en el
    orden de `Oferta.PRECEDENCIA`. Entre dos del mismo nivel —dos etiquetas del
    producto con oferta— manda la que empezó antes y, el mismo día, la creada
    primero. Una oferta sobre una editorial, una etiqueta o un grupo dados de
    baja no descuenta mientras lo estén.
    """

    def __init__(self, hoy=None):
        self.hoy = hoy or hoy_local()
        self.por_alcance = {alcance: {} for alcance, _ in Oferta.ALCANCES}
        vigentes = (
            Oferta.objects.en_vigencia(self.hoy)
            .select_related("editorial", "etiqueta__grupo", "grupo")
            .order_by("fecha_inicio", "pk")
        )
        for oferta in vigentes:
            if not _destino_vigente(oferta):
                continue
            destino = getattr(oferta, f"{Oferta.CAMPO_DEL_ALCANCE[oferta.alcance]}_id")
            self.por_alcance[oferta.alcance].setdefault(destino, oferta)
        self._indirectas = any(
            self.por_alcance[a] for a in (Oferta.EDITORIAL, Oferta.ETIQUETA, Oferta.GRUPO)
        )
        self._datos = {}

    def preparar(self, productos):
        """Lee de una vez la editorial y las etiquetas de estos productos.

        Quien recorre muchos productos preguntando el precio de cada uno lo
        llama antes del recorrido: sin esto, con ofertas por editorial, etiqueta
        o grupo, cada pregunta haría su propia consulta. Devuelve los productos.
        """
        productos = list(productos)
        self._leer([producto.pk for producto in productos])
        return productos

    # Por producto: su editorial y sus etiquetas (con el grupo de cada una).
    def _leer(self, pks):
        faltan = [pk for pk in pks if pk not in self._datos]
        if not faltan or not self._indirectas:
            return
        from apps.catalog.models import Etiqueta, ProductoEditorial

        editoriales = dict(
            ProductoEditorial.objects.filter(pk__in=faltan).values_list("pk", "editorial_id")
        )
        etiquetas = {}
        for producto_id, etiqueta_id, grupo_id in Etiqueta.productos.through.objects.filter(
            producto_id__in=faltan, etiqueta__activa=True, etiqueta__grupo__activo=True
        ).values_list("producto_id", "etiqueta_id", "etiqueta__grupo_id"):
            etiquetas.setdefault(producto_id, []).append((etiqueta_id, grupo_id))
        for pk in faltan:
            self._datos[pk] = (editoriales.get(pk), etiquetas.get(pk, []))

    def aplicada(self, producto):
        directa = self.por_alcance[Oferta.PRODUCTO].get(producto.pk)
        if directa is not None:
            return directa
        if self._indirectas:
            self._leer([producto.pk])
            editorial_id, etiquetas = self._datos.get(producto.pk, (None, []))
            for alcance, claves in (
                (Oferta.ETIQUETA, [e for e, _ in etiquetas]),
                (Oferta.GRUPO, [g for _, g in etiquetas]),
                (Oferta.EDITORIAL, [editorial_id] if editorial_id else []),
            ):
                candidatas = [
                    self.por_alcance[alcance][c] for c in claves if c in self.por_alcance[alcance]
                ]
                if candidatas:
                    return min(candidatas, key=lambda o: (o.fecha_inicio, o.pk))
        return self.por_alcance[Oferta.TIPO].get(producto.tipo_id)

    def precio(self, producto):
        oferta = self.aplicada(producto)
        return descontar(producto.precio, oferta) if oferta else producto.precio

    def anotar(self, productos):
        """Deja en cada producto `oferta_aplicada` y `precio_visible`, para las plantillas."""
        for producto in self.preparar(productos):
            producto.oferta_aplicada = self.aplicada(producto)
            producto.precio_visible = self.precio(producto)
        return productos


def _destino_vigente(oferta):
    """La editorial, la etiqueta o el grupo de la oferta siguen dados de alta."""
    if oferta.alcance == Oferta.EDITORIAL:
        return oferta.editorial.activa
    if oferta.alcance == Oferta.ETIQUETA:
        return oferta.etiqueta.activa and oferta.etiqueta.grupo.activo
    if oferta.alcance == Oferta.GRUPO:
        return oferta.grupo.activo
    return True


def oferta_aplicada(producto, *, hoy=None):
    """La oferta que descuenta hoy a este producto, o `None`."""
    return OfertasDelDia(hoy).aplicada(producto)


def precio_visible(producto, *, hoy=None):
    """El precio que se ve y se cobra hoy."""
    oferta = oferta_aplicada(producto, hoy=hoy)
    return descontar(producto.precio, oferta) if oferta else producto.precio
