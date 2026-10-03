"""CU-TDA-CAT — Consultar Catálogo Público (`CO-176`, `CO-177`).

Público y sin sesión (precondición de `CO-176`). Sólo lectura: no modifica nada
ni se audita. El plan del módulo está en `docs/planes/07-tienda-online.md`.

**Qué es visible.** Los productos Activos, en Pre-venta y Agotados. Nunca los
Descatalogados ni los Cancelados por la editorial, bajo ningún filtro. Tampoco
los marcados «solo para adultos» (plan 07, ambigüedad 2).
"""

from decimal import Decimal, InvalidOperation

from django.core.paginator import Paginator
from django.db.models import Prefetch, Q
from django.http import Http404
from django.shortcuts import render
from django.views import View

from apps.catalog.models import Editorial, Etiqueta, Producto, Tipo

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


def visibles():
    """Lo que el catálogo público puede mostrar, bajo cualquier filtro."""
    return Producto.objects.filter(estado__in=ESTADOS_VISIBLES, solo_adultos=False).select_related(
        "tipo", "productoeditorial__editorial", "productoeditorial__formato"
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


class FiltrosDelCatalogo:
    """Los filtros del paso 3. Un valor inválido en la dirección se ignora."""

    def __init__(self, parametros):
        self.busqueda = parametros.get("q", "").strip()
        self.tipo = _entero(parametros.get("tipo"))
        self.editorial = _entero(parametros.get("editorial"))
        self.etiqueta = _entero(parametros.get("etiqueta"))
        self.precio_desde = _decimal(parametros.get("desde")) if parametros.get("desde") else None
        self.precio_hasta = _decimal(parametros.get("hasta")) if parametros.get("hasta") else None
        estado = parametros.get("estado", DISPONIBLE)
        # La vista por defecto: Activos con stock (paso 2 de la ficha).
        self.estado = estado if estado in dict(FILTROS_DE_ESTADO) else DISPONIBLE

    @property
    def activos(self):
        return any(
            [
                self.busqueda,
                self.tipo,
                self.editorial,
                self.etiqueta,
                self.precio_desde is not None,
                self.precio_hasta is not None,
                self.estado != DISPONIBLE,
            ]
        )

    def aplicar(self, productos):
        if self.busqueda:
            productos = productos.filter(
                Q(titulo__icontains=self.busqueda)
                | Q(productoeditorial__autor__icontains=self.busqueda)
                | Q(productoeditorial__editorial__nombre__icontains=self.busqueda)
            )
        if self.tipo:
            productos = productos.filter(tipo_id=self.tipo)
        if self.editorial:
            productos = productos.filter(productoeditorial__editorial_id=self.editorial)
        if self.etiqueta:
            productos = productos.filter(etiquetas=self.etiqueta)
        if self.precio_desde is not None:
            productos = productos.filter(precio__gte=self.precio_desde)
        if self.precio_hasta is not None:
            productos = productos.filter(precio__lte=self.precio_hasta)
        if self.estado == DISPONIBLE:
            productos = productos.filter(disponibles())
        elif self.estado == AGOTADO:
            productos = productos.filter(sin_stock())
        elif self.estado == PRE_VENTA:
            productos = productos.filter(estado=Producto.PRE_VENTA)
        return productos.distinct()


def _marcar(productos):
    for indice, producto in enumerate(productos):
        producto.estado_publico = estado_publico(producto)
        producto.indice = indice
    return productos


class CatalogoPublicoView(View):
    """`CO-176`: la estantería con sus filtros, de lo más nuevo a lo más viejo."""

    def get(self, request):
        filtros = FiltrosDelCatalogo(request.GET)
        productos = filtros.aplicar(visibles()).order_by("-creado_en", "-pk")
        pagina = Paginator(productos, POR_PAGINA).get_page(request.GET.get("page"))
        _marcar(pagina.object_list)

        parametros = request.GET.copy()
        parametros.pop("page", None)
        etiquetas = (
            Etiqueta.objects.filter(activa=True, grupo__activo=True)
            .select_related("grupo")
            .order_by("grupo__nombre", "nombre")
        )
        return render(
            request,
            "core/tienda_catalogo.html",
            {
                "pagina": pagina,
                "productos": pagina.object_list,
                "filtros": filtros,
                "estados": FILTROS_DE_ESTADO,
                "tipos": Tipo.objects.filter(activo=True).order_by("nombre"),
                "editoriales": Editorial.objects.filter(activa=True).order_by("nombre"),
                "etiquetas": etiquetas,
                "parametros": parametros.urlencode(),
            },
        )


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
        return render(
            request,
            "core/tienda_producto.html",
            {
                "producto": producto,
                "editorial": getattr(producto, "productoeditorial", None),
                # Volver al catálogo con los filtros que traía (paso 7).
                "volver": request.GET.get("volver", ""),
            },
        )


def recien_llegados(cantidad=8):
    """Para la portada: lo último disponible o en pre-venta."""
    productos = list(
        visibles()
        .filter(disponibles() | Q(estado=Producto.PRE_VENTA))
        .order_by("-creado_en", "-pk")[:cantidad]
    )
    return _marcar(productos)
