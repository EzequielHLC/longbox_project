"""Buscar un producto para pedirlo a un proveedor (B-05-016, B-05-018).

Lo usan «Agregar un producto» de Restock y los renglones del pedido a mano. Nadie
recuerda trescientos códigos: el buscador ofrece el catálogo como «código — título
#tomo», y el servidor acepta el código, el ISBN, el código de barras o el título
con su número («Sakamoto Days 24»).
"""

from django.db.models import Q

from apps.catalog import isbn as isbn_util
from apps.catalog.models import Producto, ProductoEditorial
from apps.catalog.services import titulo_comparable

# El código primero, que es lo que identifica, y después el nombre, como en las ofertas.
SEPARADOR = " — "


def opciones_para_pedir():
    """Lo que se puede pedir: material editorial que no está cancelado ni descatalogado."""
    return [
        f"{codigo}{SEPARADOR}{titulo} #{volumen}"
        for codigo, titulo, volumen in ProductoEditorial.objects.exclude(
            estado__in=(*Producto.ESTADOS_TERMINALES, Producto.DESCATALOGADO)
        )
        .order_by("titulo", "volumen")
        .values_list("codigo", "titulo", "volumen")
    ]


def buscar_para_pedir(texto, *, solo_editorial=True):
    """`(producto, None)` o `(None, mensaje)` que dice qué pasó de verdad (B-05-016).

    Primero lo exacto: código, ISBN (con o sin guiones) o código de barras. Si no,
    el título con su número al final («Sakamoto Days 24»), sin tildes ni mayúsculas.
    """
    texto = (texto or "").split(SEPARADOR, 1)[0].strip()
    if not texto:
        return None, "Escribí el código, el ISBN o el título del producto."
    filtro = Q(codigo__iexact=texto) | Q(codigo_barras=texto)
    if isbn := isbn_util.normalizar(texto):
        filtro |= Q(productoeditorial__isbn=isbn)
    exacto = Producto.objects.filter(filtro).first()
    if exacto is not None:
        return _si_se_puede_pedir(exacto.especifico, solo_editorial=solo_editorial)

    *palabras, ultima = texto.split() or [""]
    if not palabras or not ultima.lstrip("#").isdigit():
        return None, (
            f"No encontré «{texto}» por código, ISBN ni código de barras. "
            "Para buscar por título, escribí también el número del tomo: «Sakamoto Days 24»."
        )
    buscado, volumen = titulo_comparable(" ".join(palabras)), int(ultima.lstrip("#"))
    candidatos = [
        tomo
        for tomo in ProductoEditorial.objects.filter(volumen=volumen).exclude(
            estado__in=(*Producto.ESTADOS_TERMINALES, Producto.DESCATALOGADO)
        )
        if buscado in titulo_comparable(tomo.titulo)
    ]
    if len(candidatos) == 1:
        return candidatos[0], None
    if not candidatos:
        return None, f"No encontré «{texto}» por código, ISBN, código de barras ni título."
    nombres = ", ".join(f"{tomo} ({tomo.codigo})" for tomo in candidatos[:4])
    return None, f"«{texto}» coincide con más de un producto: {nombres}. Elegí uno de la lista."


def _si_se_puede_pedir(producto, *, solo_editorial=True):
    if solo_editorial and not isinstance(producto, ProductoEditorial):
        return None, f"«{producto}» no es material editorial: el restock pide sólo tomos."
    if producto.estado in Producto.ESTADOS_TERMINALES:
        return None, (
            f"«{producto}» ({producto.codigo}) está cancelado por la editorial y no se pide. "
            "Si se volvió a anunciar, cargalo con «Volver a anunciar» desde su ficha."
        )
    if producto.estado == Producto.DESCATALOGADO:
        return None, (
            f"«{producto}» ({producto.codigo}) está dado de baja del catálogo: reactivalo "
            "para pedirlo."
        )
    return producto, None
