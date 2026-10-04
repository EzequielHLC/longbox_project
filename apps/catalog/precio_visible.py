"""El precio visible de un producto (plan 07 y plan 03, segundas partes).

Es el precio que leen la tienda, el carrito y, cuando exista, el mostrador. Sale
de **una sola función** para que los dos canales no puedan diferir: un canal que
leyera `producto.precio` directamente cobraría sin la oferta vigente.

El precio guardado del producto no cambia nunca por una oferta. La oferta
modifica lo que se ve y se cobra, y por eso darla de baja o dejarla vencer
restaura el precio sin tener que recordar cuál era.

**Qué oferta aplica.** Una oferta descuenta hoy si no está dada de baja y hoy
está entre sus fechas, ambas incluidas: no hace falta que el Temporizador haya
corrido (plan 03, segunda parte, ambigüedades 1 y 2). Si un producto tiene una
oferta individual y otra de su tipo, manda la individual (ambigüedad 3).

**Cuánto descuenta.** Todo en `Decimal`. El resultado se redondea al peso, como
cualquier precio de venta, y nunca baja de $1 (`CO-055`, I-09).
"""

from decimal import Decimal

from django.db.models import Q
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
    la ficha de una oferta. Una consulta en vez de una por producto.
    """

    def __init__(self, hoy=None):
        self.hoy = hoy or hoy_local()
        self.por_producto = {}
        self.por_tipo = {}
        for oferta in Oferta.objects.en_vigencia(self.hoy).order_by("pk"):
            if oferta.alcance == Oferta.PRODUCTO:
                self.por_producto.setdefault(oferta.producto_id, oferta)
            else:
                self.por_tipo.setdefault(oferta.tipo_id, oferta)

    def aplicada(self, producto):
        return self.por_producto.get(producto.pk) or self.por_tipo.get(producto.tipo_id)

    def precio(self, producto):
        oferta = self.aplicada(producto)
        return descontar(producto.precio, oferta) if oferta else producto.precio

    def anotar(self, productos):
        """Deja en cada producto `oferta_aplicada` y `precio_visible`, para las plantillas."""
        for producto in productos:
            producto.oferta_aplicada = self.aplicada(producto)
            producto.precio_visible = self.precio(producto)
        return productos


def oferta_aplicada(producto, *, hoy=None):
    """La oferta que descuenta hoy a este producto, o `None`."""
    hoy = hoy or hoy_local()
    candidatas = list(
        Oferta.objects.en_vigencia(hoy)
        .filter(
            Q(alcance=Oferta.PRODUCTO, producto_id=producto.pk)
            | Q(alcance=Oferta.TIPO, tipo_id=producto.tipo_id)
        )
        .order_by("pk")
    )
    individuales = [oferta for oferta in candidatas if oferta.alcance == Oferta.PRODUCTO]
    return (individuales or candidatas or [None])[0]


def precio_visible(producto, *, hoy=None):
    """El precio que se ve y se cobra hoy."""
    oferta = oferta_aplicada(producto, hoy=hoy)
    return descontar(producto.precio, oferta) if oferta else producto.precio
