from decimal import Decimal

import factory

from apps.catalog.models import (
    Editorial,
    Etiqueta,
    Formato,
    GrupoEtiqueta,
    LoteAlta,
    Producto,
    ProductoEditorial,
    ProductoNoEditorial,
    TablaPrecioReferencia,
    Tipo,
)

PVP_DE_PRUEBA = Decimal("5000.00")

# Los catálogos de clasificación se siembran con la migración `0002`, porque sin
# al menos un tipo cargado el sistema no se puede usar. Por eso las factorías de
# los cuatro catálogos buscan antes de crear: pedir "B6" en un test tiene que
# devolver el B6 que ya existe, no chocar contra su restricción de unicidad.
BUSCAR_POR_NOMBRE = ("nombre",)


class EditorialFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Editorial
        django_get_or_create = BUSCAR_POR_NOMBRE

    nombre = factory.Sequence(lambda n: f"Editorial {n}")


class GrupoEtiquetaFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = GrupoEtiqueta
        django_get_or_create = BUSCAR_POR_NOMBRE

    nombre = "Franquicia"


class EtiquetaFactory(factory.django.DjangoModelFactory):
    """Una etiqueta del grupo Franquicia, que es el que siembra la migración.

    Se busca por nombre **y grupo** porque su unicidad es por grupo: pedir
    "Terror" en un test tiene que devolver el "Terror" de *ese* grupo.
    """

    class Meta:
        model = Etiqueta
        django_get_or_create = ("nombre", "grupo")

    nombre = factory.Sequence(lambda n: f"Universo {n}")
    grupo = factory.SubFactory(GrupoEtiquetaFactory)


class TipoFactory(factory.django.DjangoModelFactory):
    """Un tipo de material. Por omisión se comporta como el manga.

    `usa_formato` es lo que decide si el alta pide el tamaño, así que cada test
    la declara según el caso que esté probando en vez de depender de que la
    migración de catálogos iniciales haya sembrado un nombre en particular.
    """

    class Meta:
        model = Tipo
        django_get_or_create = BUSCAR_POR_NOMBRE

    nombre = factory.Sequence(lambda n: f"Tipo {n}")
    usa_formato = True


class FormatoFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Formato
        django_get_or_create = BUSCAR_POR_NOMBRE

    nombre = factory.Sequence(lambda n: f"Formato {n}")
    # Universal, como lo eran todos los formatos de prueba antes de que el
    # alcance fuera un atributo (B-17-004). Para acotarlo: `formato_solo_para`.
    aplica_a_todos = True


def formato_solo_para(nombre, *tipos):
    """Un formato que se ofrece sólo en los tipos dados.

    Ajusta el existente si la fábrica lo encuentra por nombre —los formatos
    sembrados por las migraciones nacen universales— en vez de crear otro.
    """
    formato = FormatoFactory(nombre=nombre)
    formato.aplica_a_todos = False
    formato.save(update_fields=["aplica_a_todos"])
    formato.tipos.set(tipos)
    return formato


class PrecioReferenciaFactory(factory.django.DjangoModelFactory):
    """Una fila de la tabla de precios: precondición del alta nacional."""

    class Meta:
        model = TablaPrecioReferencia

    editorial = factory.SubFactory(EditorialFactory)
    tipo = factory.SubFactory(TipoFactory)
    formato = factory.SubFactory(FormatoFactory)
    pvp = PVP_DE_PRUEBA


class LoteAltaFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = LoteAlta

    origen = LoteAlta.NACIONAL


class ProductoFactory(factory.django.DjangoModelFactory):
    """Un producto **editorial**, que es el caso por defecto del catálogo.

    Conserva el nombre viejo a propósito: es el que usan más de doscientos tests
    que no tienen nada que decir sobre el rubro, y renombrarlos en masa habría
    escondido los pocos cambios que sí importan detrás de un diff enorme. Para el
    otro rubro está `ProductoNoEditorialFactory`.
    """

    class Meta:
        model = ProductoEditorial
        # `pedido_en_camino` no cambia el producto: no hace falta volver a guardarlo.
        skip_postgeneration_save = True

    titulo = factory.Sequence(lambda n: f"Título {n}")
    volumen = 1
    editorial = factory.SubFactory(EditorialFactory)
    tipo = factory.SubFactory(TipoFactory)
    formato = factory.SubFactory(FormatoFactory)
    origen = ProductoEditorial.NACIONAL
    estado = Producto.ACTIVO
    precio = PVP_DE_PRUEBA
    precio_base = PVP_DE_PRUEBA

    @factory.post_generation
    def pedido_en_camino(self, create, cantidad, **kwargs):
        """Una pre-venta se reserva contra lo pedido al proveedor (plan 00 del circuito
        con los proveedores): la fábrica le da un pedido en camino de 100 unidades,
        o los que diga la prueba. `pedido_en_camino=0` la deja sin pedido."""
        if not create or self.estado != Producto.PRE_VENTA:
            return
        cantidad = 100 if cantidad is None else cantidad
        if not cantidad:
            return
        from apps.suppliers.models import LineaPedidoProveedor, PedidoProveedor

        pedido = PedidoProveedor.objects.create(
            origen=PedidoProveedor.LOTE, fecha_estimada=self.fecha_llegada
        )
        LineaPedidoProveedor.objects.create(pedido=pedido, producto=self, cantidad_pedida=cantidad)


class TipoNoEditorialFactory(factory.django.DjangoModelFactory):
    """Una categoría del otro rubro: TCG, figura, merchandising o insumo."""

    class Meta:
        model = Tipo
        django_get_or_create = BUSCAR_POR_NOMBRE

    nombre = factory.Sequence(lambda n: f"Categoría {n}")
    clase = Producto.NO_EDITORIAL
    usa_formato = False


class ProductoNoEditorialFactory(factory.django.DjangoModelFactory):
    """Una figura, un mazo o un insumo. Sin editorial, sin volumen, sin ISBN."""

    class Meta:
        model = ProductoNoEditorial

    titulo = factory.Sequence(lambda n: f"Artículo {n}")
    tipo = factory.SubFactory(TipoNoEditorialFactory)
    estado = Producto.ACTIVO
    precio = PVP_DE_PRUEBA
