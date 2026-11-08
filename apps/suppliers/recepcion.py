"""«Por llegar»: la llegada de mercadería en una sola pantalla (B-05-017, `CO-232`).

Antes había dos: «Pre-ventas por llegar», por producto, y «Pedidos por llegar»,
por pedido. Desde B-05-010 casi toda pre-venta tiene su pedido, así que la misma
caja se podía cargar por dos lados y cada panel mostraba la mitad. Acá se junta
todo lo que se espera **por proveedor y fecha**, que es lo que entra por la
puerta, y cada línea trae lo de los dos paneles: el pedido, lo pedido, lo
confirmado y lo recibido, y si es pre-venta, sus reservas y su demora.

Confirmar no inventa nada nuevo: cada línea va a `llegadas.registrar_llegada`
(que pasa las pre-ventas por `CO-013`), la pre-venta sin pedido va a
`preventa.confirmar_ingreso`, y la pre-venta del grupo que queda en cero es un
faltante de `CU-ALT-TRA` A1: se demora si su fecha ya pasó.
"""

from collections import defaultdict
from dataclasses import dataclass, field
from datetime import timedelta

from django.db.models import Count, Q, Sum
from django.utils import timezone

from apps.catalog.models import Producto, ProductoEditorial
from apps.pedidos import preventa
from apps.suppliers import llegadas
from apps.suppliers.models import LineaPedidoProveedor, PedidoProveedor

SIN_FECHA = "sin-fecha"


class OperacionRechazada(ValueError):
    """Lo que la operación no admite, con el mensaje para la pantalla."""


# ---------------------------------------------------------------------------
# Lo que se espera
# ---------------------------------------------------------------------------


@dataclass
class Fila:
    """Una línea de un pedido, o una pre-venta que no tiene pedido registrado."""

    producto: Producto
    llegada: object
    linea: LineaPedidoProveedor | None = None
    reservadas: int = 0
    pedidos_de_clientes: int = 0

    @property
    def campo(self):
        """El nombre del campo del formulario: `l<pk>` una línea, `p<pk>` una pre-venta."""
        return f"l{self.linea.pk}" if self.linea else f"p{self.producto.pk}"

    @property
    def en_preventa(self):
        return self.producto.estado == Producto.PRE_VENTA

    @property
    def sin_pedido(self):
        return self.linea is None

    @property
    def pedido(self):
        return self.linea.pedido if self.linea else None

    @property
    def esperadas(self):
        """Lo que todavía falta que llegue: lo pendiente de la línea, o las reservas."""
        return self.linea.pendiente if self.linea else self.reservadas

    @property
    def sugeridas(self):
        """Lo que pone «Completar con lo esperado»."""
        return self.esperadas


@dataclass
class Grupo:
    llegada: object
    nombre: str
    clave_proveedor: str
    filas: list = field(default_factory=list)

    @property
    def clave(self):
        fecha = self.llegada.isoformat() if self.llegada else SIN_FECHA
        return f"{fecha}-{self.clave_proveedor}"

    @property
    def editorial(self):
        """El calendario rotula cada llegada con este nombre."""
        return self.nombre

    @property
    def dias_para(self):
        return (self.llegada - timezone.localdate()).days if self.llegada else None

    @property
    def vencido(self):
        return self.dias_para is not None and self.dias_para < 0

    @property
    def es_hoy(self):
        return self.dias_para == 0

    @property
    def cercano(self):
        """Lo atrasado y lo de la próxima semana se muestra abierto."""
        return self.dias_para is not None and self.dias_para <= 7

    @property
    def cuando(self):
        dias = self.dias_para
        if dias is None:
            return "Sin fecha"
        if dias < 0:
            return "Atrasado"
        if dias == 0:
            return "Llega hoy"
        if dias == 1:
            return "Llega mañana"
        return f"Llega en {dias} días"

    @property
    def reservadas(self):
        return sum(fila.reservadas for fila in self.filas)

    @property
    def preventas(self):
        """Las pre-ventas del grupo, una vez cada una: lo que se puede demorar junto."""
        vistas = {}
        for fila in self.filas:
            if fila.en_preventa:
                vistas.setdefault(fila.producto.pk, fila.producto)
        return list(vistas.values())


def _reservas(ids):
    """Las reservas sin cubrir de cada producto, en una sola consulta."""
    pendientes = Q(lineas_pedido__estado__in=preventa.PENDIENTES)
    filas = (
        Producto.objects.filter(pk__in=ids)
        .annotate(
            reservadas=Sum("lineas_pedido__cantidad", filter=pendientes, default=0),
            pedidos=Count("lineas_pedido__pedido", filter=pendientes, distinct=True),
        )
        .values_list("pk", "reservadas", "pedidos")
    )
    return {pk: (reservadas, pedidos) for pk, reservadas, pedidos in filas}


def _llegada(producto, linea):
    """La pre-venta se espera en su fecha vigente, que es la que ve el Cliente y la
    que vigila el Temporizador; lo demás, en la que dio el proveedor."""
    if producto.estado == Producto.PRE_VENTA:
        return producto.especifico.llegada_vigente
    return linea.pedido.fecha_estimada if linea else None


def _nombre_del_grupo(proveedor, producto):
    if proveedor is not None:
        return str(proveedor), f"prov{proveedor.pk}"
    editorial = getattr(producto.especifico, "editorial", None)
    if editorial is not None:
        return str(editorial), f"edit{editorial.pk}"
    return "Sin proveedor", "sin"


def filas_esperadas():
    """Todo lo que se espera: las líneas abiertas de pedidos que salieron, y las
    pre-ventas que no tienen ninguna (B-05-017, ambigüedad B4)."""
    lineas = list(
        LineaPedidoProveedor.objects.filter(
            estado__in=LineaPedidoProveedor.ABIERTAS,
            pedido__estado=PedidoProveedor.ABIERTO,
        )
        .select_related(
            "pedido__proveedor",
            "producto__productoeditorial__editorial",
            "producto__productonoeditorial",
        )
        .order_by("pedido__creado_en", "pk")
    )
    con_linea = {linea.producto_id for linea in lineas}
    sueltas = list(
        ProductoEditorial.objects.filter(estado=Producto.PRE_VENTA)
        .exclude(pk__in=con_linea)
        .select_related("editorial", "proveedor")
    )
    reservas = _reservas(con_linea | {p.pk for p in sueltas})

    filas = []
    for linea in lineas:
        producto = linea.producto
        reservadas, pedidos = reservas.get(producto.pk, (0, 0))
        filas.append(
            Fila(
                producto=producto,
                llegada=_llegada(producto, linea),
                linea=linea,
                reservadas=reservadas if producto.estado == Producto.PRE_VENTA else 0,
                pedidos_de_clientes=pedidos if producto.estado == Producto.PRE_VENTA else 0,
            )
        )
    for producto in sueltas:
        reservadas, pedidos = reservas.get(producto.pk, (0, 0))
        filas.append(
            Fila(
                producto=producto,
                llegada=producto.llegada_vigente,
                reservadas=reservadas,
                pedidos_de_clientes=pedidos,
            )
        )
    return filas


def por_llegar():
    """Lo que se espera, agrupado por proveedor y fecha (ambigüedad B1)."""
    grupos = {}
    for fila in filas_esperadas():
        proveedor = fila.pedido.proveedor if fila.pedido else fila.producto.proveedor
        nombre, clave = _nombre_del_grupo(proveedor, fila.producto)
        grupo = grupos.setdefault(
            (fila.llegada, clave), Grupo(llegada=fila.llegada, nombre=nombre, clave_proveedor=clave)
        )
        grupo.filas.append(fila)
    for grupo in grupos.values():
        grupo.filas.sort(
            key=lambda f: (
                f.producto.titulo.lower(),
                getattr(f.producto.especifico, "volumen", None) or 0,
                f.linea.pk if f.linea else 0,
            )
        )
    lejos = timezone.localdate().replace(year=9999)
    return sorted(grupos.values(), key=lambda g: (g.llegada or lejos, g.nombre.lower()))


def resumen(grupos):
    """Las cifras de arriba de la pantalla."""
    hoy = timezone.localdate()
    filas = [fila for grupo in grupos for fila in grupo.filas]
    return {
        "lineas": len(filas),
        "unidades": sum(fila.esperadas for fila in filas),
        "reservadas": sum(fila.reservadas for fila in filas),
        "esta_semana": sum(
            1 for grupo in grupos if grupo.llegada and hoy <= grupo.llegada <= hoy + timedelta(7)
        ),
        "atrasados": sum(1 for grupo in grupos if grupo.vencido),
    }


# ---------------------------------------------------------------------------
# Lo que se carga
# ---------------------------------------------------------------------------


def leer(datos):
    """Las filas del grupo enviado y sus unidades. Vacío es cero.

    Devuelve `(lineas, productos)`: de pk de línea a unidades, y de pk de pre-venta
    sin pedido a unidades. Las filas que vinieron en el formulario cuentan aunque
    estén en cero: es lo que hace de una pre-venta del grupo un faltante.
    """
    lineas, productos = {}, {}
    for campo in datos.getlist("fila"):
        tipo, pk = campo[:1], campo[1:]
        if tipo not in ("l", "p") or not pk.isdigit():
            continue
        valor = (datos.get(f"llegaron_{campo}") or "").strip()
        if valor and not valor.isdigit():
            raise OperacionRechazada(
                "Revisá las unidades: tienen que ser números enteros, sin signo."
            )
        unidades = int(valor or 0)
        if unidades > 9999:
            raise OperacionRechazada("Revisá las unidades: ninguna fila puede pasar de 9999.")
        (lineas if tipo == "l" else productos)[int(pk)] = unidades
    if not lineas and not productos:
        raise OperacionRechazada("Ese grupo ya no tiene nada por llegar.")
    return lineas, productos


def leer_vistas(datos, lineas):
    """Lo recibido de cada línea que mostraba la revisión (`vista_l<pk>`).

    La confirmación lo exige: es lo que permite saber, con la línea bloqueada, si
    otra persona registró la misma caja mientras tanto.
    """
    vistas = {}
    for pk in lineas:
        valor = (datos.get(f"vista_l{pk}") or "").strip()
        if not valor.isdigit():
            raise OperacionRechazada("Revisá la llegada antes de confirmarla.")
        vistas[pk] = int(valor)
    return vistas


@dataclass
class Previa:
    """Lo que le va a pasar a un producto, antes de registrarlo."""

    producto: Producto
    filas: list
    unidades: int
    reservas: int = 0
    cubiertas: int = 0
    a_la_venta: int = 0
    quedan: int = 0
    de_mas: int = 0
    se_demora: bool = False
    sin_cambios: bool = False

    @property
    def en_preventa(self):
        return self.producto.estado == Producto.PRE_VENTA

    @property
    def fuera_de_venta(self):
        """B-05-019: suma stock sin volver a la venta."""
        return self.producto.estado in (Producto.DESCATALOGADO, *Producto.ESTADOS_TERMINALES)


def _vigentes(lineas, productos):
    """Las líneas y las pre-ventas que siguen esperando, con su producto."""
    abiertas = {
        linea.pk: linea
        for linea in LineaPedidoProveedor.objects.filter(
            pk__in=lineas,
            estado__in=LineaPedidoProveedor.ABIERTAS,
            pedido__estado=PedidoProveedor.ABIERTO,
        ).select_related(
            "pedido__proveedor", "producto__productoeditorial", "producto__productonoeditorial"
        )
    }
    if len(abiertas) != len(lineas):
        raise OperacionRechazada(
            "Una de las líneas ya no está esperando mercadería. Volvé a «Por llegar»."
        )
    sueltas = {
        p.pk: p
        for p in ProductoEditorial.objects.filter(pk__in=productos, estado=Producto.PRE_VENTA)
    }
    if len(sueltas) != len(productos):
        raise OperacionRechazada("Uno de esos productos ya no está en pre-venta.")
    return abiertas, sueltas


def previsualizar(lineas, productos):
    """La revisión: qué pasa con cada producto, sin escribir nada."""
    abiertas, sueltas = _vigentes(lineas, productos)
    por_producto = defaultdict(list)
    for pk, unidades in lineas.items():
        linea = abiertas[pk]
        por_producto[linea.producto_id].append((linea, unidades))
    for pk, unidades in productos.items():
        por_producto[pk].append((None, unidades))

    previas = []
    for pk, partes in por_producto.items():
        producto = partes[0][0].producto if partes[0][0] else sueltas[pk]
        unidades = sum(u for _, u in partes)
        previa = Previa(producto=producto, filas=partes, unidades=unidades)
        for linea, recibidas in partes:
            if linea is not None:
                previa.quedan += max(0, linea.pendiente - recibidas)
                previa.de_mas += max(0, linea.cantidad_recibida + recibidas - linea.esperada)
        if producto.estado == Producto.PRE_VENTA:
            ingreso = preventa.previsualizar_ingreso(producto.especifico, unidades)
            # En unidades, no en pedidos: «cubre 3 de 3» dice cuántos tomos se apartan.
            reservas = list(preventa.reservas_pendientes(producto))
            cubiertas, _ = preventa._cubrir(reservas, producto.stock + unidades)
            previa.reservas = sum(linea.cantidad for linea in reservas)
            previa.cubiertas = sum(linea.cantidad for linea in cubiertas) if unidades else 0
            previa.a_la_venta = ingreso.a_la_venta
            previa.se_demora = ingreso.se_demora
            previa.sin_cambios = not unidades and not ingreso.se_demora
        else:
            previa.a_la_venta = 0 if previa.fuera_de_venta else unidades
            previa.sin_cambios = not unidades
        previas.append(previa)
    previas.sort(key=lambda p: (p.sin_cambios, str(p.producto).lower()))
    return previas


@dataclass
class Resultado:
    unidades: int = 0
    pedidos_proveedor: list = field(default_factory=list)
    al_stock: list = field(default_factory=list)
    ingreso: preventa.ResumenIngreso = field(default_factory=preventa.ResumenIngreso)
    errores: list = field(default_factory=list)


def confirmar(lineas, productos, actor, *, vistas, origen=""):
    """`CO-232`: registra lo que llegó del grupo.

    Un pedido por vez, como `CO-013` E3 un producto por vez: si uno falla, queda
    como estaba y los demás siguen. Las líneas en cero quedan abiertas; la
    pre-venta que no recibió nada en ninguna de sus filas es un faltante.

    `vistas` es lo recibido de cada línea que mostraba la revisión (`leer_vistas`):
    si otra persona se adelantó, ese pedido no suma nada.
    """
    abiertas, _ = _vigentes(lineas, productos)
    resultado = Resultado()

    por_pedido = defaultdict(dict)
    for pk, unidades in lineas.items():
        if unidades:
            por_pedido[abiertas[pk].pedido_id][pk] = unidades
    for pedido_id, cantidades in sorted(por_pedido.items()):
        pedido = abiertas[next(iter(cantidades))].pedido
        ingreso = preventa.ResumenIngreso()
        try:
            llegada = llegadas.registrar_llegada(
                pedido, cantidades, actor, origen=origen, ingreso=ingreso, vistas=vistas
            )
        except llegadas.OperacionRechazada as rechazo:
            resultado.errores.append(f"{pedido}: {rechazo}")
            continue
        resultado.unidades += llegada.unidades
        resultado.pedidos_proveedor.append(pedido)
        resultado.al_stock.extend(llegada.al_stock)
        resultado.ingreso.sumar(ingreso)

    # La pre-venta sin pedido, y la pre-venta del grupo que no recibió nada en
    # ninguna de sus filas: `CO-013` con cero es el faltante de A1.
    recibidas = defaultdict(int)
    producto_de = {}
    for pk, unidades in lineas.items():
        linea = abiertas[pk]
        recibidas[linea.producto_id] += unidades
        producto_de[linea.producto_id] = linea.producto
    directas = dict(productos)
    for pk, unidades in recibidas.items():
        if not unidades and producto_de[pk].estado == Producto.PRE_VENTA:
            directas.setdefault(pk, 0)
    if directas:
        ingreso = preventa.confirmar_ingreso(directas, actor, origen=origen)
        resultado.unidades += sum(directas.values())
        resultado.ingreso.sumar(ingreso)
    return resultado


def pedidos_sin_enviar():
    """Los pedidos que no salieron no se esperan: se avisan arriba (B-05-014)."""
    return PedidoProveedor.objects.filter(estado=PedidoProveedor.SIN_ENVIAR).count()
