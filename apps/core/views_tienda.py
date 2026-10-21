"""CU-TDA-CAT — Consultar Catálogo Público (`CO-176`, `CO-177`).

Público y sin sesión (precondición de `CO-176`). Sólo lectura: no modifica nada
ni se audita. El plan del módulo está en `docs/planes/07-tienda-online.md`.

**Qué es visible.** Los productos Activos, en Pre-venta y Agotados. Nunca los
Descatalogados ni los Cancelados por la editorial, bajo ningún filtro. Tampoco
los marcados «solo para adultos» (plan 07, ambigüedad 2).
"""

from datetime import timedelta
from decimal import Decimal, InvalidOperation
from types import SimpleNamespace
from urllib.parse import urlencode

from django.core.paginator import Paginator
from django.db.models import F, Prefetch, Q
from django.db.models.functions import Coalesce
from django.http import Http404
from django.shortcuts import render
from django.urls import reverse
from django.utils import timezone
from django.views import View

from apps.catalog.models import Editorial, Etiqueta, Producto, ProductoEditorial, Tipo
from apps.catalog.precio_visible import OfertasDelDia

POR_PAGINA = 24

ESTADOS_VISIBLES = (Producto.ACTIVO, Producto.PRE_VENTA, Producto.AGOTADO)

DISPONIBLE = "disponible"
AGOTADO = "agotado"
PRE_VENTA = "pre_venta"
TODOS = "todos"
FILTROS_DE_ESTADO = [
    (DISPONIBLE, "Disponible"),
    (AGOTADO, "Agotado"),
    (PRE_VENTA, "Pre-venta"),
    (TODOS, "Todos"),
]
# Los interruptores de estado del catálogo (plan 07, quinta parte): se pueden
# prender varios; «todos» en la dirección los prende a los tres.
ESTADOS_ELEGIBLES = [(DISPONIBLE, "Disponibles"), (PRE_VENTA, "Pre-ventas"), (AGOTADO, "Sin stock")]

RECIENTES = "recientes"
LLEGADA = "llegada"
TITULO = "titulo"
ORDENES = [(RECIENTES, "Lo más nuevo"), (LLEGADA, "Próximos a llegar"), (TITULO, "Título")]


def visibles():
    """Lo que el catálogo público puede mostrar, bajo cualquier filtro."""
    # La tarjeta lee la editorial del tomo o la marca del artículo: las dos hijas
    # van en la misma consulta, o cada artículo no editorial cuesta una más (B-07-007).
    return Producto.objects.filter(estado__in=ESTADOS_VISIBLES, solo_adultos=False).select_related(
        "tipo", "productoeditorial__editorial", "productoeditorial__formato", "productonoeditorial"
    )


def disponibles():
    return Q(estado=Producto.ACTIVO, stock__gt=0)


def sin_stock():
    return Q(estado=Producto.AGOTADO) | Q(estado=Producto.ACTIVO, stock=0)


def estado_publico(producto):
    """La palabra del estado, tal como la lee el cliente."""
    if producto.estado == Producto.PRE_VENTA:
        return PRE_VENTA
    if producto.estado == Producto.AGOTADO or producto.stock <= 0:
        return AGOTADO
    return DISPONIBLE


def _decimal(texto):
    try:
        valor = Decimal(str(texto).replace(",", "."))
    except (InvalidOperation, ValueError):
        return None
    return valor if valor >= 0 else None


def _entero(texto):
    return int(texto) if str(texto or "").isdigit() else None


def _enteros(parametros, nombre):
    valores = (
        parametros.getlist(nombre) if hasattr(parametros, "getlist") else [parametros.get(nombre)]
    )
    return sorted({int(v) for v in valores if str(v or "").isdigit()})


class FiltrosDelCatalogo:
    """Los filtros del paso 3. Un valor inválido en la dirección se ignora.

    Tipo, editorial, etiqueta y estado admiten varios valores (plan 07, quinta
    parte): dentro de un mismo grupo de etiquetas alcanza con una; entre grupos
    distintos, el producto tiene que cumplir todos. La vista por defecto sigue
    siendo la del paso 2: Activos con stock, lo más nuevo primero.
    """

    def __init__(self, parametros):
        self.busqueda = parametros.get("q", "").strip()
        self.tipos = _enteros(parametros, "tipo")
        self.editoriales = _enteros(parametros, "editorial")
        self.etiquetas = _enteros(parametros, "etiqueta")
        # Lo usa el «Ver todo» de una fila de la portada armada por grupo (B-07-009).
        self.grupo = _entero(parametros.get("grupo"))
        self.precio_desde = _decimal(parametros.get("desde")) if parametros.get("desde") else None
        self.precio_hasta = _decimal(parametros.get("hasta")) if parametros.get("hasta") else None
        validos = [valor for valor, _ in ESTADOS_ELEGIBLES]
        pedidos = (
            parametros.getlist("estado")
            if hasattr(parametros, "getlist")
            else [parametros.get("estado", "")]
        )
        if TODOS in pedidos:
            self.estados = validos
        else:
            self.estados = [e for e in validos if e in pedidos]
        if not self.estados:
            # Con el panel enviado y todos los estados apagados, no se filtra por
            # estado; sin panel, la vista por defecto del paso 2.
            self.estados = validos if parametros.get("f") else [DISPONIBLE]
        orden = parametros.get("orden", RECIENTES)
        self.orden = orden if orden in dict(ORDENES) else RECIENTES

    # Lo que leen las pantallas que conocen un solo valor por filtro.
    @property
    def estado(self):
        return self.estados[0] if len(self.estados) == 1 else TODOS

    @property
    def tipo(self):
        return self.tipos[0] if self.tipos else None

    @property
    def editorial(self):
        return self.editoriales[0] if self.editoriales else None

    @property
    def etiqueta(self):
        return self.etiquetas[0] if self.etiquetas else None

    @property
    def activos(self):
        return any(
            [
                self.busqueda,
                self.tipos,
                self.editoriales,
                self.etiquetas,
                self.grupo,
                self.precio_desde is not None,
                self.precio_hasta is not None,
                self.estados != [DISPONIBLE],
                self.orden != RECIENTES,
            ]
        )

    def aplicar(self, productos):
        if self.busqueda:
            productos = productos.filter(
                Q(titulo__icontains=self.busqueda)
                | Q(productoeditorial__autor__icontains=self.busqueda)
                | Q(productoeditorial__editorial__nombre__icontains=self.busqueda)
            )
        if self.tipos:
            productos = productos.filter(tipo_id__in=self.tipos)
        if self.editoriales:
            productos = productos.filter(productoeditorial__editorial_id__in=self.editoriales)
        if self.etiquetas:
            por_grupo = {}
            for pk, grupo in Etiqueta.objects.filter(pk__in=self.etiquetas).values_list(
                "pk", "grupo_id"
            ):
                por_grupo.setdefault(grupo, []).append(pk)
            for elegidas in por_grupo.values():
                productos = productos.filter(etiquetas__in=elegidas)
        if self.grupo:
            productos = productos.filter(etiquetas__grupo_id=self.grupo, etiquetas__activa=True)
        if self.precio_desde is not None or self.precio_hasta is not None:
            productos = productos.filter(pk__in=self._en_rango_de_precio(productos))
        condiciones = {
            DISPONIBLE: disponibles(),
            AGOTADO: sin_stock(),
            PRE_VENTA: Q(estado=Producto.PRE_VENTA),
        }
        if len(self.estados) < len(condiciones):
            elegidas = Q()
            for estado in self.estados:
                elegidas |= condiciones[estado]
            productos = productos.filter(elegidas)
        return productos.distinct()

    def ordenar(self, productos):
        if self.orden == LLEGADA:
            return productos.annotate(llegada=_llegada()).order_by(
                F("llegada").asc(nulls_last=True), "-creado_en", "-pk"
            )
        if self.orden == TITULO:
            return productos.order_by("titulo", "productoeditorial__volumen", "pk")
        return productos.order_by("-creado_en", "-pk")

    def _en_rango_de_precio(self, productos):
        """El rango se mide sobre el precio que se cobra, con la oferta aplicada.

        Se calcula en Python con la misma función que el carrito: una segunda
        versión del descuento escrita en SQL podría redondear distinto.
        """
        del_dia = OfertasDelDia()
        elegidos = []
        for producto in productos.select_related(None).only("pk", "precio", "tipo_id"):
            precio = del_dia.precio(producto)
            if self.precio_desde is not None and precio < self.precio_desde:
                continue
            if self.precio_hasta is not None and precio > self.precio_hasta:
                continue
            elegidos.append(producto.pk)
        return elegidos


def _llegada():
    """La fecha en la que hoy se espera un tomo: la estimada pisa a la programada."""
    return Coalesce("productoeditorial__fecha_estimada", "productoeditorial__fecha_llegada")


def _editorial(producto):
    try:
        return producto.productoeditorial
    except ProductoEditorial.DoesNotExist:
        return None


DIAS_DE_NOVEDAD = 30


def _carteles(productos):
    """«¡TOMO 1!» y «¡NOVEDAD!» (plan 07, quinta parte; B-07-024).

    «¡TOMO 1!» en el tomo 1 de una serie con más de un tomo. «¡NOVEDAD!» en lo
    que se dio de alta en los últimos treinta días y ya está a la venta: las
    pre-ventas tienen su rótulo. Si un tomo 1 es novedad, gana «¡TOMO 1!». La
    serie sólo se consulta para los tomos 1 de la estantería, en una consulta.
    """
    desde = timezone.now() - timedelta(days=DIAS_DE_NOVEDAD)
    primeros = []
    for producto in productos:
        editorial = _editorial(producto)
        if editorial is not None and editorial.volumen == 1:
            primeros.append((producto, editorial))
        elif producto.estado != Producto.PRE_VENTA and producto.creado_en >= desde:
            producto.cartel = "¡NOVEDAD!"
    if not primeros:
        return
    con_mas_tomos = set(
        ProductoEditorial.objects.filter(
            estado__in=ESTADOS_VISIBLES,
            solo_adultos=False,
            titulo__in={p.titulo for p, _ in primeros},
            volumen__gt=1,
        ).values_list("titulo", "editorial_id")
    )
    for producto, editorial in primeros:
        if (producto.titulo, editorial.editorial_id) in con_mas_tomos:
            producto.cartel = "¡TOMO 1!"
        elif producto.estado != Producto.PRE_VENTA and producto.creado_en >= desde:
            producto.cartel = "¡NOVEDAD!"


def _marcar(productos):
    for indice, producto in enumerate(productos):
        producto.estado_publico = estado_publico(producto)
        producto.indice = indice
    # El precio con la oferta vigente, y la oferta para tachar el original.
    OfertasDelDia().anotar(productos)
    _carteles(productos)
    return productos


def _con_productos():
    """Lo visible, sin las relaciones de la tarjeta: para saber qué opciones tienen algo."""
    return Producto.objects.filter(estado__in=ESTADOS_VISIBLES, solo_adultos=False)


class CatalogoPublicoView(View):
    """`CO-176`: la estantería con sus filtros, de lo más nuevo a lo más viejo.

    Con `parcial=1` responde sólo los resultados: es lo que pide el panel de
    filtros mientras el cliente los cambia, sin recargar la pantalla (plan 07,
    quinta parte). Sin JavaScript el panel se envía con su botón.
    """

    def get(self, request):
        filtros = FiltrosDelCatalogo(request.GET)
        productos = filtros.ordenar(filtros.aplicar(visibles()))
        pagina = Paginator(productos, POR_PAGINA).get_page(request.GET.get("page"))
        _marcar(pagina.object_list)

        parametros = request.GET.copy()
        for clave in ("page", "parcial"):
            parametros.pop(clave, None)
        contexto = {
            "pagina": pagina,
            "productos": pagina.object_list,
            "filtros": filtros,
            "parametros": parametros.urlencode(),
        }
        if request.GET.get("parcial") == "1":
            return render(request, "core/_catalogo_resultados.html", contexto)

        # Sólo las opciones que tienen algo para mostrar: una editorial sembrada
        # sin productos sería un interruptor que siempre deja el catálogo vacío.
        con_productos = _con_productos()
        contexto.update(
            {
                "estados": ESTADOS_ELEGIBLES,
                "ordenes": ORDENES,
                "tipos": Tipo.objects.filter(activo=True, productos__in=con_productos)
                .distinct()
                .order_by("nombre"),
                "editoriales": Editorial.objects.filter(activa=True, productos__in=con_productos)
                .distinct()
                .order_by("nombre"),
                "etiquetas": Etiqueta.objects.filter(
                    Q(productos__in=con_productos) | Q(pk__in=filtros.etiquetas),
                    activa=True,
                    grupo__activo=True,
                )
                .select_related("grupo")
                .distinct()
                .order_by("grupo__nombre", "nombre"),
            }
        )
        return render(request, "core/tienda_catalogo.html", contexto)


class FichaPublicaView(View):
    """`CO-177`: la ficha con la acción que corresponde a su estado.

    Un producto que no es visible responde 404, como si no existiera. Si pasó
    a Agotado entre el listado y la ficha (E2), se muestra como está, sin aviso.
    """

    def get(self, request, pk):
        producto = (
            visibles()
            .prefetch_related(
                Prefetch(
                    "etiquetas",
                    queryset=Etiqueta.objects.filter(activa=True, grupo__activo=True)
                    .select_related("grupo")
                    .order_by("grupo__nombre", "nombre"),
                ),
                "imagenes",
            )
            .filter(pk=pk)
            .first()
        )
        if producto is None:
            raise Http404("Producto no disponible en la tienda.")
        producto.estado_publico = estado_publico(producto)
        OfertasDelDia().anotar([producto])
        return render(
            request,
            "core/tienda_producto.html",
            {
                "serie": _mas_de_la_serie(producto),
                "producto": producto,
                "en_carrito": _en_carrito(request, producto),
                "editorial": getattr(producto, "productoeditorial", None),
                "aviso": _aviso(request, producto),
                # Volver al catálogo con los filtros que traía (paso 7).
                "volver": request.GET.get("volver", ""),
            },
        )


def _aviso(request, producto):
    """CU-RST-SUS paso 2: el botón, el estado del Cliente y cuántos esperan."""
    if producto.estado_publico != "agotado":
        return None
    from apps.restock import servicios as restock

    usuario = request.user
    return {
        "puede_pedir": not usuario.is_authenticated or usuario.rol == "cliente",
        "suscripcion": restock.suscripcion_de(usuario, producto),
        "en_espera": restock.en_espera(producto),
    }


TOMOS_DE_LA_SERIE = 30


def _mas_de_la_serie(producto):
    """«Más de la serie» en la ficha de un tomo (B-07-030): los demás tomos visibles
    del mismo título y editorial, en orden. `None` si no es un tomo o no hay más."""
    editorial = _editorial(producto)
    if editorial is None:
        return None
    tomos = list(
        visibles()
        .filter(
            productoeditorial__editorial_id=editorial.editorial_id,
            titulo=producto.titulo,
        )
        .exclude(pk=producto.pk)
        .order_by("productoeditorial__volumen", "pk")[:TOMOS_DE_LA_SERIE]
    )
    if not tomos:
        return None
    filtro = urlencode({"q": producto.titulo, "estado": TODOS, "orden": TITULO})
    return SimpleNamespace(
        pk="serie",
        titulo_visible=f"Más de {producto.titulo}",
        antetitulo="La serie",
        imagen=None,
        productos=_marcar(tomos),
        ver_todo=f"{reverse('core:tienda_catalogo')}?{filtro}",
    )


def _en_carrito(request, producto):
    """Cuántas unidades de este producto lleva quien mira: el acceso al carrito del paso 4."""
    from apps.tienda import carrito as servicio

    if not servicio.puede_tener_carrito(request.user):
        return 0
    carrito = servicio.carrito_de(request)
    linea = carrito.lineas.filter(producto=producto).first() if carrito else None
    return linea.cantidad if linea else 0


def recien_llegados(cantidad=8):
    """Para la portada: lo último disponible o en pre-venta."""
    productos = list(
        visibles()
        .filter(disponibles() | Q(estado=Producto.PRE_VENTA))
        .order_by("-creado_en", "-pk")[:cantidad]
    )
    return _marcar(productos)


PRODUCTOS_POR_FILA = 12


def filas_de_portada():
    """Las filas de la portada, cada una con sus productos (plan 07, tercera parte).

    Sólo las activas, con su etiqueta o su grupo vigentes, y con algún producto
    visible: una fila vacía no se dibuja.
    """
    from apps.core.models import FilaPortada

    filas = []
    for fila in FilaPortada.objects.filter(activa=True).select_related("etiqueta__grupo", "grupo"):
        if not fila.disponible:
            continue
        productos = visibles()
        if fila.etiqueta_id:
            productos = productos.filter(etiquetas=fila.etiqueta_id)
        else:
            productos = productos.filter(etiquetas__grupo=fila.grupo_id, etiquetas__activa=True)
        productos = list(productos.distinct().order_by("-creado_en", "-pk")[:PRODUCTOS_POR_FILA])
        if productos:
            fila.productos = _marcar(productos)
            fila.antetitulo = fila.etiqueta.grupo.nombre if fila.etiqueta_id else "Explorá"
            filtro = (
                f"etiqueta={fila.etiqueta_id}" if fila.etiqueta_id else f"grupo={fila.grupo_id}"
            )
            fila.ver_todo = f"{reverse('core:tienda_catalogo')}?{filtro}&estado=todos"
            filas.append(fila)
    return filas


def lo_que_se_viene(cantidad=PRODUCTOS_POR_FILA):
    """«Lo que se viene» (plan 07, quinta parte; B-07-015): las pre-ventas, la más próxima primero.

    Se dibuja como una fila más de la portada, sin imagen propia: el «Ver
    todo» lleva al catálogo de pre-ventas ordenado por llegada. Sin pre-ventas,
    `None` y la fila no aparece.
    """
    productos = list(
        visibles()
        .filter(estado=Producto.PRE_VENTA)
        .annotate(llegada=_llegada())
        .order_by(F("llegada").asc(nulls_last=True), "-creado_en", "-pk")[:cantidad]
    )
    if not productos:
        return None
    return SimpleNamespace(
        pk="se-viene",
        titulo_visible="Lo que se viene",
        antetitulo="Pre-ventas",
        imagen=None,
        productos=_marcar(productos),
        ver_todo=f"{reverse('core:tienda_catalogo')}?estado=pre_venta&orden={LLEGADA}",
    )


SUGERENCIAS = 5


class SugerenciasView(View):
    """Plan 00 de interfaz, U1: las primeras coincidencias mientras se escribe en el
    buscador del encabezado. La misma búsqueda del catálogo (`CO-176`), en todos
    los estados visibles; con menos de dos letras, nada. Sólo lee."""

    def get(self, request):
        texto = request.GET.get("q", "").strip()
        productos = []
        if len(texto) >= 2:
            filtros = FiltrosDelCatalogo({"q": texto, "estado": TODOS})
            productos = _marcar(list(filtros.ordenar(filtros.aplicar(visibles()))[:SUGERENCIAS]))
        return render(
            request, "core/_sugerencias.html", {"productos": productos, "busqueda": texto}
        )
