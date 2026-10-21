"""El ticket del mostrador (`CU-VTA-REG`): `CO-078` a `CO-082`.

Hasta confirmar, el ticket vive en la sesión de quien atiende y no toca el
dominio (B-06-002): ni stock, ni puntos. Los precios se leen en cada paso, con
la oferta vigente, y se congelan al confirmar. `CO-082` es la única escritura:
pedido, transacción de pago, stock y puntos en una sola transacción.
"""

import logging
from dataclasses import dataclass, field
from decimal import Decimal

from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from apps.accounts.models import Usuario
from apps.catalog import isbn
from apps.catalog.models import Producto
from apps.catalog.precio_visible import OfertasDelDia
from apps.core.models import ConfiguracionSistema, RegistroAuditoria
from apps.pedidos.models import LineaPedido, Pedido, TransaccionPago
from apps.pedidos.servicios import registrar_transicion
from apps.puntos import servicios as puntos
from apps.puntos.models import LotePuntos

logger = logging.getLogger(__name__)

CLAVE = "ticket_mostrador"
MEDIOS = (TransaccionPago.EFECTIVO, TransaccionPago.TRANSFERENCIA, TransaccionPago.TARJETA)


class VentaRechazada(ValueError):
    """Lo que el contrato rechaza. El mensaje es el que lee el Cajero."""


# ---------------------------------------------------------------------------
# El ticket en la sesión
# ---------------------------------------------------------------------------


def _vacio():
    return {"items": [], "cliente": None}


def _ticket(sesion):
    return sesion.get(CLAVE) or _vacio()


def _guardar(sesion, ticket):
    sesion[CLAVE] = ticket
    sesion.modified = True


def a_la_venta(producto):
    return producto.estado == Producto.ACTIVO and producto.stock > 0


@dataclass
class ItemDelTicket:
    producto: Producto
    cantidad: int
    precio: Decimal
    cubierta: bool
    puntos_necesarios: int

    @property
    def importe(self):
        return self.precio * self.cantidad

    @property
    def a_pagar(self):
        return Decimal("0") if self.cubierta else self.importe


@dataclass
class Ticket:
    items: list = field(default_factory=list)
    cliente: Usuario | None = None
    saldo: int = 0

    @property
    def vacio(self):
        return not self.items

    @property
    def total(self):
        return sum((item.a_pagar for item in self.items), Decimal("0"))

    @property
    def puntos_aplicados(self):
        return sum(item.puntos_necesarios for item in self.items if item.cubierta)

    @property
    def saldo_restante(self):
        return self.saldo - self.puntos_aplicados

    @property
    def puntos_a_acreditar(self):
        return puntos.puntos_por_monto(self.total) if self.cliente else 0

    @property
    def unidades(self):
        return sum(item.cantidad for item in self.items)


def consultar(sesion):
    """El ticket con los precios de hoy y el saldo del cliente vinculado."""
    datos = _ticket(sesion)
    valor = ConfiguracionSistema.obtener().equivalencia_puntos
    productos = Producto.objects.select_related("tipo", "productoeditorial").in_bulk(
        [item["producto"] for item in datos["items"]]
    )
    del_dia = OfertasDelDia()
    items = []
    for item in datos["items"]:
        producto = productos.get(item["producto"])
        if producto is None:
            continue
        precio = del_dia.precio(producto)
        items.append(
            ItemDelTicket(
                producto=producto,
                cantidad=item["cantidad"],
                precio=precio,
                cubierta=item["cubierta"],
                puntos_necesarios=puntos.puntos_para_cubrir(precio * item["cantidad"], valor),
            )
        )
    cliente = (
        Usuario.objects.filter(pk=datos["cliente"], rol=Usuario.CLIENTE).first()
        if datos["cliente"]
        else None
    )
    return Ticket(items=items, cliente=cliente, saldo=puntos.saldo(cliente) if cliente else 0)


# ---------------------------------------------------------------------------
# CO-078 abrirVentaPresencial · CO-079 agregarItemAlTicket · CO-080 quitarItemDelTicket
# ---------------------------------------------------------------------------


def abrir(sesion):
    """`CO-078`: un ticket en blanco. Hace falta al menos un producto con stock."""
    if not Producto.objects.filter(estado=Producto.ACTIVO, stock__gt=0).exists():
        raise VentaRechazada("No hay productos con stock para vender.")
    _guardar(sesion, _vacio())


def buscar_exacto(texto):
    """B-06-003: el producto cuyo código, código de barras o ISBN es exactamente ese."""
    texto = (texto or "").strip()
    if not texto:
        return None
    condicion = Q(codigo__iexact=texto) | Q(codigo_barras=texto)
    normalizado = isbn.normalizar(texto)
    if normalizado:
        condicion |= Q(productoeditorial__isbn=normalizado)
    return Producto.objects.filter(condicion).first()


def buscar(texto, limite=12):
    """Las coincidencias por título, sólo lo que se puede vender."""
    texto = (texto or "").strip()
    if len(texto) < 2:
        return []
    return list(
        Producto.objects.filter(estado=Producto.ACTIVO, stock__gt=0, titulo__icontains=texto)
        .select_related("productoeditorial")
        .order_by("titulo")[:limite]
    )


def agregar(sesion, producto, cantidad=1):
    """`CO-079`: suma al ticket. El stock no cambia (postcondición negativa)."""
    if cantidad < 1:
        raise VentaRechazada("La cantidad tiene que ser al menos uno.")
    producto = Producto.objects.get(pk=producto.pk)
    ticket = _ticket(sesion)
    item = next((i for i in ticket["items"] if i["producto"] == producto.pk), None)
    pedida = (item["cantidad"] if item else 0) + cantidad
    if not a_la_venta(producto):
        raise VentaRechazada(f"«{producto.titulo}» no tiene unidades disponibles.")
    if pedida > producto.stock:
        raise VentaRechazada(f"De «{producto.titulo}» hay {producto.stock} unidad(es).")
    if item:
        item["cantidad"] = pedida
    else:
        ticket["items"].append({"producto": producto.pk, "cantidad": cantidad, "cubierta": False})
    _guardar(sesion, ticket)


def quitar(sesion, producto_pk):
    """`CO-080`. Si estaba cubierto con puntos, el canje se va con él (`CO-104`)."""
    ticket = _ticket(sesion)
    ticket["items"] = [i for i in ticket["items"] if i["producto"] != producto_pk]
    _guardar(sesion, ticket)


# ---------------------------------------------------------------------------
# CO-081 vincularCuentaDeCliente
# ---------------------------------------------------------------------------


def vincular(sesion, texto):
    """`CO-081`: por código de cliente o por correo (B-06-001). Sin cambios persistentes."""
    texto = (texto or "").strip()
    codigo = texto.replace(" ", "")
    cliente = Usuario.objects.filter(
        Q(codigo_cliente=codigo) | Q(email__iexact=texto),
        rol=Usuario.CLIENTE,
        estado=Usuario.ACTIVO,
    ).first()
    if cliente is None:
        raise VentaRechazada("No hay un cliente activo con ese código o correo.")
    ticket = _ticket(sesion)
    ticket["cliente"] = cliente.pk
    _guardar(sesion, ticket)
    return cliente


def desvincular(sesion):
    """Quitar la cuenta vinculada por error. Los canjes se revierten con ella."""
    ticket = _ticket(sesion)
    ticket["cliente"] = None
    for item in ticket["items"]:
        item["cubierta"] = False
    _guardar(sesion, ticket)


# ---------------------------------------------------------------------------
# CO-103 aplicarCanjeDePuntosAItem · CO-104 revertirCanjeDePuntosDeItem (mostrador)
# ---------------------------------------------------------------------------


def aplicar_canje(sesion, producto_pk):
    """`CO-103` desde el ticket: el ítem entero, con el precio de hoy. Ningún lote cambia."""
    actual = consultar(sesion)
    if actual.cliente is None:
        raise VentaRechazada("Vinculá la cuenta del cliente para canjear puntos.")
    item = next((i for i in actual.items if i.producto.pk == producto_pk), None)
    if item is None or item.cubierta:
        return
    if item.puntos_necesarios > actual.saldo_restante:
        raise VentaRechazada(
            f"Para cubrir «{item.producto.titulo}» hacen falta {item.puntos_necesarios} "
            f"puntos y quedan {actual.saldo_restante}. No hay canje parcial."
        )
    _marcar(sesion, producto_pk, True)


def revertir_canje(sesion, producto_pk):
    """`CO-104`: el ítem vuelve a su precio."""
    _marcar(sesion, producto_pk, False)


def _marcar(sesion, producto_pk, cubierta):
    ticket = _ticket(sesion)
    for item in ticket["items"]:
        if item["producto"] == producto_pk:
            item["cubierta"] = cubierta
    _guardar(sesion, ticket)


# ---------------------------------------------------------------------------
# CO-082 confirmarVentaPresencial
# ---------------------------------------------------------------------------


def confirmar(sesion, medio, actor):
    """`CO-082`: la venta. Todo o nada, con los productos bloqueados en orden de clave.

    La venta nace despachada: el cliente se lleva el material en el momento.
    """
    actual = consultar(sesion)
    if actual.vacio:
        raise VentaRechazada("El ticket está vacío.")
    if actual.total > 0 and medio not in MEDIOS:
        raise VentaRechazada("Elegí el medio de pago.")
    if medio not in MEDIOS:
        medio = TransaccionPago.EFECTIVO  # sólo puntos: la transacción es por $ 0 (B-06-004)

    ahora = timezone.now()
    with transaction.atomic():
        ids = [item.producto.pk for item in actual.items]
        bloqueados = {
            p.pk: p for p in Producto.objects.select_for_update().filter(pk__in=ids).order_by("pk")
        }
        for item in actual.items:
            producto = bloqueados[item.producto.pk]
            if producto.estado != Producto.ACTIVO or producto.stock < item.cantidad:
                raise VentaRechazada(
                    f"De «{producto.titulo}» quedan {producto.stock} unidad(es). Corregí el ticket."
                )
        if actual.cliente and actual.puntos_aplicados > puntos.saldo(actual.cliente):
            raise VentaRechazada("El saldo de puntos del cliente cambió. Revisá los canjes.")

        pedido = Pedido.objects.create(
            canal=Pedido.PRESENCIAL,
            estado=Pedido.VENDIDO_EN_LOCAL,
            modalidad=Pedido.MOSTRADOR,
            usuario=actual.cliente,
            costo_envio=Decimal("0"),
            fecha=ahora,
        )
        pedido.asignar_numero()
        registrar_transicion(pedido, None, actor, ahora)

        for item in actual.items:
            LineaPedido.objects.create(
                pedido=pedido,
                producto=item.producto,
                cantidad=item.cantidad,
                precio_unitario=item.precio,
                cubierta_con_puntos=item.cubierta,
                puntos_canjeados=item.puntos_necesarios if item.cubierta else 0,
                estado=LineaPedido.ENTREGADO_EN_LOCAL,
            )
            queda = bloqueados[item.producto.pk].stock - item.cantidad
            Producto.objects.filter(pk=item.producto.pk).update(
                stock=queda,
                estado=Producto.AGOTADO if queda == 0 else Producto.ACTIVO,
                actualizado_en=ahora,
            )

        TransaccionPago.objects.create(
            pedido=pedido,
            medio=medio,
            monto=actual.total,
            estado=TransaccionPago.APROBADO,
            registrada_en=ahora,
        )

        acreditados = 0
        if actual.cliente:
            puntos.debitar(actual.cliente, actual.puntos_aplicados, pedido=pedido)
            acreditados = puntos.puntos_por_monto(actual.total)
            puntos.acreditar(actual.cliente, acreditados, origen=LotePuntos.COMPRA, pedido=pedido)

        RegistroAuditoria.registrar(
            accion=RegistroAuditoria.VENTA_PRESENCIAL,
            actor=actor,
            objetivo=pedido,
            objetivo_email=actual.cliente.email if actual.cliente else "",
            detalle=(
                f"Venta {pedido.numero}: {len(actual.items)} ítem(s), "
                f"{TransaccionPago(medio=medio).get_medio_display()} {actual.total}"
                + (f", cliente {actual.cliente.codigo_cliente}" if actual.cliente else "")
                + (f", canjeó {actual.puntos_aplicados} pts" if actual.puntos_aplicados else "")
                + (f", acreditó {acreditados} pts" if acreditados else "")
                + "."
            ),
        )
    _guardar(sesion, _vacio())
    return pedido
