"""Las operaciones del carrito (plan 07, segunda parte).

`CO-083` agregar, `CO-084` modificar la cantidad, `CO-085` quitar, `CO-178`
consultar y `CO-086` fusionar al iniciar sesión. Más la propagación de precios
que piden `CO-048`, `CO-053` y los contratos de oferta: `actualizar_precios`.

**El carrito no reserva stock.** Lo verifica al agregar y al cambiar la cantidad,
y la consulta lo vuelve a mirar: entre una cosa y otra el stock puede bajar, y
la línea queda marcada (`CU-TDA-CRA`, Comentarios).

**No se audita** ninguna de estas operaciones: el carrito es una selección sin
compromiso, no una operación del negocio (`CU-TDA-CRC`, Comentarios).
"""

from dataclasses import dataclass, field
from decimal import Decimal

from django.db import transaction
from django.utils import timezone

from apps.accounts.models import Usuario
from apps.catalog.models import Producto
from apps.catalog.precio_visible import OfertasDelDia, precio_visible
from apps.tienda.models import Carrito, LineaCarrito

# Dónde guarda la sesión de un invitado el identificador de su carrito. Django
# rota la clave de sesión al iniciar sesión, pero conserva sus datos: por eso el
# carrito se ubica por este valor y la fusión de `CO-086` lo encuentra.
CLAVE_DE_SESION = "carrito_id"

DISPONIBLE = "disponible"
NO_DISPONIBLE = "no_disponible"
STOCK_INSUFICIENTE = "stock_insuficiente"

ESTADOS_NO_DISPONIBLES = (
    Producto.DESCATALOGADO,
    Producto.CANCELADO_EDITORIAL,
    Producto.AGOTADO,
)


class OperacionRechazada(ValueError):
    """Lo que el contrato rechaza: el mensaje es el que lee el Cliente."""


# ---------------------------------------------------------------------------
# Quién tiene carrito y cuál es
# ---------------------------------------------------------------------------


def puede_tener_carrito(usuario):
    """Invitado o Cliente. El personal no compra con su cuenta de trabajo (plan 07, amb. 3)."""
    return not usuario.is_authenticated or usuario.rol == Usuario.CLIENTE


def carrito_de(request, *, crear=False):
    """El carrito de quien pide, o `None` si no tiene y no se pidió crearlo.

    `CO-083` (a): el de un Cliente nace Persistente y asociado a su cuenta; el de
    un invitado, De sesión y sin dueño.
    """
    usuario = request.user
    if usuario.is_authenticated:
        if crear:
            carrito, _ = Carrito.objects.get_or_create(
                usuario=usuario, defaults={"persistencia": Carrito.PERSISTENTE}
            )
            return carrito
        return Carrito.objects.filter(usuario=usuario).first()

    pk = request.session.get(CLAVE_DE_SESION)
    carrito = Carrito.objects.filter(pk=pk, usuario__isnull=True).first() if pk else None
    if carrito is None and crear:
        carrito = Carrito.objects.create(persistencia=Carrito.DE_SESION)
        request.session[CLAVE_DE_SESION] = carrito.pk
    return carrito


def unidades_en(carrito):
    """Cuántas unidades lleva: lo que muestra el encabezado de la tienda."""
    if carrito is None:
        return 0
    return sum(carrito.lineas.values_list("cantidad", flat=True))


# ---------------------------------------------------------------------------
# Disponibilidad — la derivación de `CO-178`
# ---------------------------------------------------------------------------


def disponibilidad(producto, cantidad):
    """Disponible, Producto no disponible o Stock insuficiente.

    Se deriva en cada consulta y no se guarda (plan 07, amb. 2). Un Activo con
    stock cero se lee como no disponible, igual que en el catálogo público
    (plan 07, amb. 4): ofrecerle al Cliente «reducí a cero» no resuelve nada.
    """
    if producto.estado == Producto.PRE_VENTA:
        return DISPONIBLE
    if producto.estado in ESTADOS_NO_DISPONIBLES or producto.stock <= 0:
        return NO_DISPONIBLE
    if producto.stock < cantidad:
        return STOCK_INSUFICIENTE
    return DISPONIBLE


def se_puede_agregar(producto):
    """Precondición de `CO-083`: Activo con stock, o en Pre-venta."""
    if producto.solo_adultos:
        return False
    return producto.estado == Producto.PRE_VENTA or (
        producto.estado == Producto.ACTIVO and producto.stock > 0
    )


def _tope(producto, pedida):
    """La cantidad que entra: sin tope en Pre-venta, hasta el stock si está Activo."""
    if producto.estado == Producto.ACTIVO and pedida > producto.stock:
        return producto.stock
    return pedida


# ---------------------------------------------------------------------------
# Consulta — CO-178
# ---------------------------------------------------------------------------


@dataclass
class LineaConsultada:
    linea: LineaCarrito
    precio: Decimal
    disponibilidad: str
    oferta: object = None

    @property
    def producto(self):
        return self.linea.producto

    @property
    def subtotal(self):
        return self.precio * self.linea.cantidad

    @property
    def precio_cambio(self):
        """`CU-TDA-CRC` A2: el precio no es el que el Cliente vio."""
        return self.precio != self.linea.precio_visto

    @property
    def maximo(self):
        return self.linea.producto.stock

    @property
    def pre_venta(self):
        return self.linea.producto.estado == Producto.PRE_VENTA


@dataclass
class CarritoConsultado:
    lineas: list = field(default_factory=list)

    @property
    def total(self):
        return sum((linea.subtotal for linea in self.lineas), Decimal("0"))

    @property
    def unidades(self):
        return sum(linea.linea.cantidad for linea in self.lineas)

    @property
    def vacio(self):
        return not self.lineas

    @property
    def se_puede_pagar(self):
        """La condición de `CO-179`: al menos una línea y todas disponibles."""
        return bool(self.lineas) and all(
            linea.disponibilidad == DISPONIBLE for linea in self.lineas
        )


def consultar(carrito):
    """`CO-178`: las líneas con su precio de hoy, su disponibilidad y el total.

    Sólo lee. El precio que muestra es el visible en este momento, aunque la
    línea guarde otro: una oferta empieza por su fecha sin que nada escriba en
    la línea, y el Cliente tiene que ver lo que se le va a cobrar.
    """
    if carrito is None:
        return CarritoConsultado()
    lineas = carrito.lineas.select_related(
        "producto", "producto__tipo", "producto__productoeditorial"
    ).order_by("agregada_en", "pk")
    del_dia = OfertasDelDia()
    return CarritoConsultado(
        [
            LineaConsultada(
                linea=linea,
                precio=del_dia.precio(linea.producto),
                disponibilidad=disponibilidad(linea.producto, linea.cantidad),
                oferta=del_dia.aplicada(linea.producto),
            )
            for linea in lineas
        ]
    )


# ---------------------------------------------------------------------------
# Agregar — CO-083
# ---------------------------------------------------------------------------


@dataclass
class ResultadoDeAgregado:
    linea: LineaCarrito
    pedida: int
    tope: int | None = None


def agregar(carrito, producto, cantidad):
    """`CO-083`: crea la línea o suma a la que había, con tope en el stock.

    El carrito se toma con bloqueo: dos pestañas que agregan el mismo producto
    a la vez suman las dos, en vez de que una pise a la otra.
    """
    if cantidad < 1:
        raise OperacionRechazada("La cantidad tiene que ser al menos uno.")
    with transaction.atomic():
        carrito = Carrito.objects.select_for_update().get(pk=carrito.pk)
        producto = Producto.objects.get(pk=producto.pk)
        if not se_puede_agregar(producto):
            raise OperacionRechazada("Este producto no se puede agregar al carrito.")

        linea = carrito.lineas.filter(producto=producto).first()
        pedida = (linea.cantidad if linea else 0) + cantidad
        queda = _tope(producto, pedida)
        precio = precio_visible(producto)
        if linea is None:
            linea = LineaCarrito.objects.create(
                carrito=carrito,
                producto=producto,
                cantidad=queda,
                precio_vigente=precio,
                precio_visto=precio,
            )
        else:
            linea.cantidad = queda
            linea.precio_vigente = linea.precio_visto = precio
            linea.save(update_fields=["cantidad", "precio_vigente", "precio_visto"])
        _tocar(carrito)
    return ResultadoDeAgregado(linea, pedida, queda if queda < pedida else None)


# ---------------------------------------------------------------------------
# Modificar — CO-084
# ---------------------------------------------------------------------------


@dataclass
class ResultadoDeModificacion:
    linea: LineaCarrito
    tope: int | None = None


def modificar_cantidad(linea, cantidad):
    """`CO-084`: la cantidad nueva, al menos uno y, si está Activo, hasta el stock.

    Pasarse del stock no se rechaza: la línea queda en el máximo y se informa
    (E1). Cambiar la cantidad es tocar la línea, así que el precio nuevo, si lo
    hubo, deja de avisarse.
    """
    if cantidad < 1:
        raise OperacionRechazada(
            "La cantidad tiene que ser al menos uno. Para sacar el producto, usá «Quitar»."
        )
    with transaction.atomic():
        linea = LineaCarrito.objects.select_for_update().select_related("producto").get(pk=linea.pk)
        producto = linea.producto
        if disponibilidad(producto, 1) == NO_DISPONIBLE:
            raise OperacionRechazada(
                "Este producto ya no está disponible: sólo se puede quitar del carrito."
            )
        queda = _tope(producto, cantidad)
        precio = precio_visible(producto)
        linea.cantidad = queda
        linea.precio_vigente = linea.precio_visto = precio
        linea.save(update_fields=["cantidad", "precio_vigente", "precio_visto"])
        _tocar(linea.carrito)
    return ResultadoDeModificacion(linea, queda if queda < cantidad else None)


# ---------------------------------------------------------------------------
# Quitar — CO-085
# ---------------------------------------------------------------------------


def quitar(linea):
    """`CO-085`: la línea deja de existir. Sin confirmación (`CU-TDA-CRB`)."""
    with transaction.atomic():
        carrito = linea.carrito
        linea.delete()
        _tocar(carrito)


# ---------------------------------------------------------------------------
# Fusión al iniciar sesión — CO-086
# ---------------------------------------------------------------------------


def fusionar(carrito_de_sesion, usuario):
    """`CO-086`: el carrito del invitado pasa a la cuenta, o se suma al que tenía.

    Los repetidos suman cantidades con tope en el stock si el producto está
    Activo con stock. Uno que ya no tiene stock conserva la suma: la consulta lo
    marca no disponible y el Cliente decide (B-07-005).
    """
    with transaction.atomic():
        sesion = Carrito.objects.select_for_update().get(pk=carrito_de_sesion.pk)
        persistido = Carrito.objects.select_for_update().filter(usuario=usuario).first()
        if persistido is None:
            sesion.usuario = usuario
            sesion.persistencia = Carrito.PERSISTENTE
            sesion.actualizado_en = timezone.now()
            sesion.save(update_fields=["usuario", "persistencia", "actualizado_en"])
            return sesion

        existentes = {linea.producto_id: linea for linea in persistido.lineas.all()}
        for linea in sesion.lineas.select_related("producto"):
            propia = existentes.get(linea.producto_id)
            if propia is None:
                LineaCarrito.objects.create(
                    carrito=persistido,
                    producto=linea.producto,
                    cantidad=linea.cantidad,
                    precio_vigente=linea.precio_vigente,
                    precio_visto=linea.precio_visto,
                )
                continue
            suma = propia.cantidad + linea.cantidad
            if linea.producto.stock > 0:
                suma = _tope(linea.producto, suma)
            propia.cantidad = suma
            propia.save(update_fields=["cantidad"])
        sesion.delete()
        _tocar(persistido)
    return persistido


# ---------------------------------------------------------------------------
# Propagación de precios — CO-048, CO-053 y ofertas
# ---------------------------------------------------------------------------


def actualizar_precios(productos):
    """Las líneas de estos productos pasan a su precio visible de hoy.

    No tocan `precio_visto`: la diferencia entre los dos es justamente el aviso
    de `CU-TDA-CRC` A2. Devuelve cuántas líneas cambiaron.
    """
    lineas = list(LineaCarrito.objects.filter(producto__in=productos).select_related("producto"))
    cambiadas = []
    del_dia = OfertasDelDia()
    for linea in lineas:
        precio = del_dia.precio(linea.producto)
        if linea.precio_vigente != precio:
            linea.precio_vigente = precio
            cambiadas.append(linea)
    LineaCarrito.objects.bulk_update(cambiadas, ["precio_vigente"], batch_size=500)
    return len(cambiadas)


def carritos_con(productos):
    """Cuántos carritos tienen alguno de estos productos: el informe de una baja de oferta."""
    return Carrito.objects.filter(lineas__producto__in=productos).distinct().count()


def _tocar(carrito):
    carrito.actualizado_en = timezone.now()
    carrito.save(update_fields=["actualizado_en"])
