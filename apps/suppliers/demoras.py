"""Lo que un aviso de demora propone registrar (B-04-010, plan 00 del circuito).

Un correo que el modelo clasificó como demora no genera borradores: dice que
algo que ya está en Pre-venta se atrasa. Acá se cruza lo que el modelo
reconoció —título, volumen, ISBN, la fecha nueva— con las pre-ventas de ese
proveedor, y se arma la propuesta. **No se aplica nada** (regla 4): cada fila
lleva a la pantalla de `CU-ALT-DEM` con la fecha sugerida, y la demora se
registra recién cuando el Administrador la confirma ahí, con su informe de
impacto (`CO-014`, `CO-015`).
"""

import datetime
from dataclasses import dataclass, field

from django.db.models import Q

from apps.catalog import isbn as isbn_util
from apps.catalog import services
from apps.catalog.models import Producto, ProductoEditorial
from apps.suppliers import llegadas
from apps.suppliers.extraccion import separar_volumen
from apps.suppliers.models import LineaPedidoProveedor

_titulo = services.titulo_comparable


@dataclass
class FilaDeDemora:
    producto: object
    reservado: int = 0
    mencionado: dict | None = None
    fecha_propuesta: datetime.date | None = None
    # Por qué `CU-ALT-DEM` no la admite (ya demorada, llegada vencida), o vacío.
    no_admite: str = ""


@dataclass
class PropuestaDeDemora:
    filas: list = field(default_factory=list)
    # Lo que el modelo nombró y no es una pre-venta de este proveedor.
    sin_preventa: list = field(default_factory=list)

    @property
    def mencionadas(self):
        return [fila for fila in self.filas if fila.mencionado]

    @property
    def otras(self):
        """Las que el aviso no nombra y admiten demora: por si el modelo no las reconoció."""
        return [fila for fila in self.filas if not fila.mencionado and not fila.no_admite]

    @property
    def sin_admitir(self):
        """Cuántas no nombradas no admiten demora (ya demoradas o con la llegada vencida)."""
        return sum(1 for fila in self.filas if not fila.mencionado and fila.no_admite)


def preventas_del_proveedor(proveedor):
    """Las pre-ventas de su editorial, más las que tienen un pedido suyo en camino.

    La segunda parte cubre a una distribuidora con varias editoriales, que no
    tiene una editorial propia en su ficha.
    """
    filtro = Q(
        pk__in=LineaPedidoProveedor.objects.filter(
            pedido__proveedor=proveedor, estado__in=LineaPedidoProveedor.ABIERTAS
        ).values("producto_id")
    )
    if proveedor.editorial_id:
        filtro |= Q(editorial_id=proveedor.editorial_id)
    return (
        ProductoEditorial.objects.filter(filtro, estado=Producto.PRE_VENTA)
        .select_related("editorial")
        .order_by("fecha_llegada", "titulo", "volumen")
    )


def _coincide(mencion, producto):
    isbn = isbn_util.normalizar(mencion.get("isbn") or "")
    if isbn and producto.isbn:
        return isbn == producto.isbn
    titulo, volumen = mencion.get("titulo") or "", mencion.get("volumen")
    if volumen in (None, ""):
        # Una extracción vieja, o un modelo que no separó «Ichi The Witch #1».
        titulo, volumen = separar_volumen(titulo)
    if not titulo or _titulo(titulo) != _titulo(producto.titulo):
        return False
    return volumen in (None, "") or int(volumen) == producto.volumen


def _fecha(texto):
    try:
        return datetime.date.fromisoformat(texto) if texto else None
    except ValueError:
        return None


def _no_admite(producto):
    from apps.pedidos import preventa

    try:
        preventa.validar_demora(producto)
    except preventa.OperacionRechazada as rechazo:
        return str(rechazo)
    return ""


def proponer(correo):
    """Las pre-ventas del proveedor del correo, con lo que el aviso menciona primero."""
    periodo = _fecha((correo.extraccion or {}).get("periodo"))
    menciones = list(correo.demorados_extraidos)
    # La fecha del aviso, para la pre-venta que el Administrador elija de la
    # lista: la general, o la única que da el aviso. Con dos fechas distintas no
    # hay cuál proponer.
    fechas = {fecha for fecha in (_fecha(m.get("fecha")) for m in menciones) if fecha}
    fecha_del_aviso = periodo or (next(iter(fechas)) if len(fechas) == 1 else None)
    usadas = set()
    filas = []
    for producto in preventas_del_proveedor(correo.proveedor):
        indice, mencion = next(
            ((i, m) for i, m in enumerate(menciones) if i not in usadas and _coincide(m, producto)),
            (None, None),
        )
        if mencion is not None:
            usadas.add(indice)
        filas.append(
            FilaDeDemora(
                producto=producto,
                reservado=llegadas.reservado(producto),
                mencionado=mencion,
                fecha_propuesta=(
                    (_fecha(mencion.get("fecha")) or periodo) if mencion else fecha_del_aviso
                ),
                no_admite=_no_admite(producto),
            )
        )
    filas.sort(key=lambda fila: fila.mencionado is None)
    return PropuestaDeDemora(
        filas=filas,
        sin_preventa=[m for i, m in enumerate(menciones) if i not in usadas],
    )
