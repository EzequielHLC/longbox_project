from decimal import Decimal

import factory

from apps.catalog.models import (
    Editorial,
    Etiqueta,
    Formato,
    GrupoEtiqueta,
    LoteAlta,
    Producto,
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
    class Meta:
        model = Producto

    titulo = factory.Sequence(lambda n: f"Título {n}")
    volumen = 1
    editorial = factory.SubFactory(EditorialFactory)
    tipo = factory.SubFactory(TipoFactory)
    formato = factory.SubFactory(FormatoFactory)
    origen = Producto.NACIONAL
    estado = Producto.ACTIVO
    precio = PVP_DE_PRUEBA
