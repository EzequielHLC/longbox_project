import factory

from apps.suppliers.models import Proveedor


class ProveedorFactory(factory.django.DjangoModelFactory):
    """Un proveedor activo. Los tests que necesiten uno de baja lo declaran.

    La razón social y el correo van por secuencia porque los dos son únicos a
    nivel de base: un valor fijo haría que el segundo proveedor de cualquier
    test chocara contra la restricción en vez de contra lo que se quiere probar.
    """

    class Meta:
        model = Proveedor

    razon_social = factory.Sequence(lambda n: f"Editorial {n}")
    correo_comercial = factory.Sequence(lambda n: f"novedades{n}@editorial.test")
    estado = Proveedor.ACTIVO
    # Nace habilitado, igual que en el alta real: es lo que hace que la mayoría
    # de los tests no tengan que decir nada al respecto.
    procesa_novedades = True
