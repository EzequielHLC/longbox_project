"""La dirección de envío del checkout (`CO-087`) y los datos del invitado (`CO-090`).

Las validaciones son las del registro de clientes: el formato del código
postal y su letra contra la provincia elegida. Acá la dirección es obligatoria
entera: sin ella no hay a dónde despachar.
"""

from django import forms

from apps.accounts.forms import MENSAJE_CPA_DE_OTRA_PROVINCIA
from apps.accounts.models import provincia_del_codigo_postal, validar_codigo_postal
from apps.core import georef

MENSAJE_SIN_NUMERO = "Escribí la calle y el número (por ejemplo, «Av. Colón 1234»)."


class DireccionDeEnvioForm(forms.Form):
    direccion = forms.CharField(
        label="Calle y número",
        max_length=150,
        widget=forms.TextInput(attrs={"autocomplete": "address-line1"}),
    )
    depto = forms.CharField(
        label="Piso / depto.",
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={"placeholder": "3.º B"}),
    )
    provincia = forms.ChoiceField(label="Provincia")
    localidad = forms.CharField(
        label="Localidad",
        max_length=120,
        widget=forms.TextInput(
            attrs={
                "autocomplete": "address-level2",
                "list": "localidades",
                "data-autocompletado": "localidades",
            }
        ),
    )
    codigo_postal = forms.CharField(
        label="Código postal",
        max_length=8,
        validators=[validar_codigo_postal],
        widget=forms.TextInput(
            attrs={"autocomplete": "postal-code", "placeholder": "5000 o X5000ABC"}
        ),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["provincia"].choices = [
            ("", "Seleccionar…"),
            *georef.provincias_para_select(),
        ]
        # Una provincia que ya no figura en la lista (la del perfil, cargada con
        # otra versión del catálogo) se ofrece igual: no se la borra en silencio.
        elegida = (self.initial or {}).get("provincia") or (self.data or {}).get("provincia")
        valores = {valor for valor, _ in self.fields["provincia"].choices}
        if elegida and elegida not in valores:
            self.fields["provincia"].choices.append((elegida, elegida))

    def clean_direccion(self):
        direccion = " ".join(self.cleaned_data["direccion"].split())
        if not any(caracter.isdigit() for caracter in direccion):
            raise forms.ValidationError(MENSAJE_SIN_NUMERO)
        return direccion

    def clean_localidad(self):
        return " ".join(self.cleaned_data["localidad"].split())

    def clean_codigo_postal(self):
        return self.cleaned_data["codigo_postal"].strip().upper()

    def clean(self):
        datos = super().clean()
        del_codigo = provincia_del_codigo_postal(datos.get("codigo_postal"))
        elegida = datos.get("provincia")
        if del_codigo and elegida and del_codigo != elegida:
            self.add_error(
                "codigo_postal", MENSAJE_CPA_DE_OTRA_PROVINCIA.format(provincia=del_codigo)
            )
        return datos


class DatosDeInvitadoForm(DireccionDeEnvioForm):
    """`CU-TDA-INV` paso 2: correo y dirección completa, todos obligatorios."""

    correo = forms.EmailField(
        label="Correo electrónico",
        max_length=254,
        widget=forms.EmailInput(attrs={"autocomplete": "email"}),
        help_text="Ahí te llegan la confirmación y los cambios de estado del pedido.",
    )

    field_order = [
        "correo",
        "direccion",
        "depto",
        "provincia",
        "localidad",
        "codigo_postal",
    ]  # noqa: RUF012

    def clean_correo(self):
        return self.cleaned_data["correo"].strip().lower()
