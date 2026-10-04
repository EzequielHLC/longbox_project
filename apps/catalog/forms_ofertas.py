"""El formulario de una oferta: alta (`CU-PVP-ALT`) y edición (`CU-PVP-EDI`).

Valida la forma —campos obligatorios, el alcance con su destino, el producto
del catálogo activo—. Las reglas del contrato (fechas, solapamiento, tope) las
valida el servicio, `apps.catalog.ofertas`, para que valgan también fuera de
esta pantalla.
"""

from decimal import Decimal

from django import forms

from apps.catalog.models import Oferta, Producto, Tipo
from apps.catalog.ofertas import DatosDeOferta

ESTADOS_DEL_CATALOGO_ACTIVO = (Producto.ACTIVO, Producto.PRE_VENTA)
SEPARADOR = " — "


def productos_elegibles():
    """El buscador del paso 3: el catálogo activo."""
    return Producto.objects.filter(estado__in=ESTADOS_DEL_CATALOGO_ACTIVO).order_by("titulo")


def opcion_de(producto):
    """Cómo se lee un producto en el buscador: el código primero, que es lo que identifica."""
    return f"{producto.codigo}{SEPARADOR}{producto.titulo}"


class OfertaForm(forms.Form):
    descripcion = forms.CharField(label="Descripción", max_length=200)
    fecha_inicio = forms.DateField(
        label="Fecha de inicio", widget=forms.DateInput(attrs={"type": "date"})
    )
    fecha_vencimiento = forms.DateField(
        label="Fecha de vencimiento",
        widget=forms.DateInput(attrs={"type": "date"}),
        help_text="La oferta descuenta hasta el final de ese día.",
    )
    tipo_descuento = forms.ChoiceField(
        label="Tipo de descuento", choices=Oferta.TIPOS_DE_DESCUENTO, widget=forms.RadioSelect
    )
    valor = forms.DecimalField(
        label="Valor del descuento",
        max_digits=12,
        decimal_places=2,
        min_value=Decimal("0.01"),
        widget=forms.NumberInput(attrs={"step": "0.01", "inputmode": "decimal"}),
        help_text="Un porcentaje (15 es un 15 %) o un monto en pesos.",
    )
    alcance = forms.ChoiceField(label="Alcance", choices=Oferta.ALCANCES, widget=forms.RadioSelect)
    producto = forms.CharField(
        label="Producto",
        required=False,
        widget=forms.TextInput(
            attrs={"list": "productos-elegibles", "data-autocompletado": "productos-elegibles"}
        ),
        help_text="Escribí el código o el título y elegilo de la lista.",
    )
    tipo = forms.ModelChoiceField(
        label="Tipo de material",
        queryset=Tipo.objects.filter(activo=True).order_by("nombre"),
        required=False,
        empty_label="Elegí un tipo",
    )

    def __init__(self, *args, oferta=None, **kwargs):
        if oferta is not None and "initial" not in kwargs:
            kwargs["initial"] = {
                "descripcion": oferta.descripcion,
                "fecha_inicio": oferta.fecha_inicio,
                "fecha_vencimiento": oferta.fecha_vencimiento,
                "tipo_descuento": oferta.tipo_descuento,
                "valor": oferta.valor,
                "alcance": oferta.alcance,
                "producto": opcion_de(oferta.producto) if oferta.producto else "",
                "tipo": oferta.tipo,
            }
        super().__init__(*args, **kwargs)
        if oferta is not None and oferta.tipo and not oferta.tipo.activo:
            # La edición sigue ofreciendo el tipo actual aunque se haya dado de baja.
            self.fields["tipo"].queryset = Tipo.objects.filter(
                pk__in=[*self.fields["tipo"].queryset.values_list("pk", flat=True), oferta.tipo.pk]
            ).order_by("nombre")

    def clean_producto(self):
        texto = self.cleaned_data["producto"].strip()
        if not texto:
            return None
        codigo = texto.split(SEPARADOR, 1)[0].strip()
        producto = productos_elegibles().filter(codigo__iexact=codigo).first()
        if producto is None:
            raise forms.ValidationError("Elegí un producto activo o en pre-venta de la lista.")
        return producto

    def clean(self):
        datos = super().clean()
        alcance = datos.get("alcance")
        if (
            alcance == Oferta.PRODUCTO
            and not datos.get("producto")
            and "producto" not in self.errors
        ):
            self.add_error("producto", "Elegí el producto de la oferta.")
        if alcance == Oferta.TIPO and not datos.get("tipo"):
            self.add_error("tipo", "Elegí el tipo de material de la oferta.")
        return datos

    def datos(self):
        limpio = self.cleaned_data
        return DatosDeOferta(
            descripcion=limpio["descripcion"].strip(),
            fecha_inicio=limpio["fecha_inicio"],
            fecha_vencimiento=limpio["fecha_vencimiento"],
            tipo_descuento=limpio["tipo_descuento"],
            valor=limpio["valor"],
            alcance=limpio["alcance"],
            producto=limpio["producto"] if limpio["alcance"] == Oferta.PRODUCTO else None,
            tipo=limpio["tipo"] if limpio["alcance"] == Oferta.TIPO else None,
        )
