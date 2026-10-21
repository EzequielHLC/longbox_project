"""El riel de estados de un pedido (plan 00 de interfaz, 4.2).

Los pasos salen de la misma tabla con la que el servidor avanza el pedido
(`SIGUIENTE` o `SIGUIENTE_RETIRO`, según la modalidad), y la fecha de cada uno
de sus transiciones: el riel no puede mostrar un paso que el pedido no recorre.

Esperar una pre-venta, esperar un artículo demorado y la cancelación no son
pasos del recorrido sino interrupciones: se dicen con su palabra encima del
riel, que queda en el último paso alcanzado.
"""

from dataclasses import dataclass, field

from apps.pedidos.models import Pedido
from apps.pedidos.servicios import SIGUIENTE, SIGUIENTE_RETIRO

ICONOS = {
    Pedido.PENDIENTE_ARMADO: "caja-abierta",
    Pedido.ARMADO: "caja-cinta",
    Pedido.EMPAQUETADO: "paquete",
    Pedido.DESPACHADO: "camion",
    Pedido.EN_LOCAL: "local",
}
INTERRUPCIONES = (Pedido.ESPERANDO_PRE_VENTA, Pedido.ESPERANDO_DEMORADO, Pedido.CANCELADO)
NOMBRES = dict(Pedido.ESTADO_CHOICES)


@dataclass
class Paso:
    estado: str
    nombre: str
    icono: str
    fecha: object = None
    hecho: bool = False
    actual: bool = False


@dataclass
class Riel:
    clave: str
    estado: str
    pasos: list = field(default_factory=list)
    interrupcion: str = ""

    @property
    def terminado(self):
        return bool(self.pasos) and self.pasos[-1].actual

    @property
    def actual(self):
        return next((paso for paso in self.pasos if paso.actual), None)


def recorrido(pedido):
    siguiente = SIGUIENTE_RETIRO if pedido.modalidad == Pedido.RETIRO else SIGUIENTE
    estados = [Pedido.PENDIENTE_ARMADO]
    while estados[-1] in siguiente:
        estados.append(siguiente[estados[-1]])
    return estados


def riel_de(pedido, transiciones=None):
    """El recorrido del pedido con lo alcanzado. `transiciones` evita volver a
    consultarlas cuando la vista ya las trae."""
    if transiciones is None:
        transiciones = list(pedido.transiciones.all())
    fechas = {}
    for transicion in sorted(transiciones, key=lambda t: t.ocurrida_en):
        fechas[transicion.estado_nuevo] = transicion.ocurrida_en

    estados = recorrido(pedido)
    if pedido.estado in estados:
        alcanzado = estados.index(pedido.estado)
    else:
        # Una interrupción deja el riel en el último paso que el pedido tocó.
        alcanzado = max((i for i, estado in enumerate(estados) if estado in fechas), default=-1)

    pasos = [
        Paso(
            estado=estado,
            nombre=NOMBRES[estado],
            icono=ICONOS[estado],
            fecha=fechas.get(estado),
            hecho=i <= alcanzado,
            actual=i == alcanzado,
        )
        for i, estado in enumerate(estados)
    ]
    return Riel(
        clave=pedido.numero,
        estado=pedido.estado,
        pasos=pasos,
        interrupcion=NOMBRES[pedido.estado] if pedido.estado in INTERRUPCIONES else "",
    )
