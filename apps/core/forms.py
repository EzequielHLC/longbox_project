"""Formularios del contenido de la tienda (módulo 17, tanda 2).

Las imágenes se procesan en el `clean` del campo (RNF-05): si una no cumple,
el formulario no es válido y nada se guarda. Lo que llega a la vista ya es la
versión WebP; el archivo subido no sigue de largo.
"""

import re

from django import forms
from django.core.validators import MaxValueValidator

from apps.core import imagenes
from apps.core.models import Banner, IdentidadVisual

HEX = re.compile(r"^#[0-9A-Fa-f]{6}$")

GUIA_BANNER = (
    "Relación 16:9 para pantalla completa o 21:9 panorámica, al menos 1920 px de ancho, "
    "en JPG o WebP. Se guarda en WebP con 1920 px en el lado mayor."
)


def _imagen(archivo, **opciones):
    try:
        return imagenes.procesar(archivo, **opciones)
    except imagenes.ImagenInvalida as error:
        raise forms.ValidationError(str(error)) from error


class FaqForm(forms.Form):
    contenido = forms.CharField(
        label="Contenido (Markdown)",
        required=False,
        strip=False,
        widget=forms.Textarea(attrs={"rows": 18, "spellcheck": "true"}),
        help_text="Títulos con #, listas con -, negrita con **texto**. No admite HTML.",
    )


class BannerForm(forms.Form):
    """`CO-132`: la imagen nueva, procesada con la dimensión de los banners."""

    imagen = forms.FileField(label="Imagen", help_text=GUIA_BANNER)

    def clean_imagen(self):
        return _imagen(
            self.cleaned_data["imagen"],
            lado_mayor=imagenes.LADO_MAYOR_BANNER,
            tamano_maximo=imagenes.TAMANO_MAXIMO_BANNER,
        )


class BannerEdicionForm(forms.Form):
    """`CO-133`: una imagen de reemplazo, una posición nueva, o las dos."""

    imagen = forms.FileField(label="Imagen de reemplazo", required=False, help_text=GUIA_BANNER)
    numero = forms.IntegerField(label="Posición", min_value=1)

    def __init__(self, *args, banner, **kwargs):
        super().__init__(*args, **kwargs)
        self.banner = banner
        total = Banner.objects.count()
        # Dentro del rango de la galería (`CO-133`, precondición).
        self.fields["numero"].validators.append(MaxValueValidator(total))
        self.fields["numero"].help_text = f"De 1 a {total}."
        self.fields["numero"].widget.attrs.update({"min": 1, "max": total})
        self.initial.setdefault("numero", banner.numero)

    def clean_imagen(self):
        archivo = self.cleaned_data.get("imagen")
        if not archivo:
            return None
        return _imagen(
            archivo,
            lado_mayor=imagenes.LADO_MAYOR_BANNER,
            tamano_maximo=imagenes.TAMANO_MAXIMO_BANNER,
        )

    def clean(self):
        datos = super().clean()
        sin_imagen = not datos.get("imagen")
        misma_posicion = datos.get("numero") in (None, self.banner.numero)
        if sin_imagen and misma_posicion and not self.errors:
            raise forms.ValidationError("Cargue una imagen de reemplazo o indique otra posición.")
        return datos


class IdentidadVisualForm(forms.ModelForm):
    """`CO-131`: las tres secciones de la ficha de `CU-CFG-VIS`."""

    logo_nuevo = forms.FileField(
        label="Logo",
        required=False,
        help_text="Cuadrado o 2:1 horizontal, en PNG, JPG o WebP. Se guarda en WebP.",
    )
    fondo_nuevo = forms.FileField(
        label="Imagen de fondo",
        required=False,
        help_text="JPG, PNG o WebP. Se guarda en WebP con 1920 px en el lado mayor.",
    )

    class Meta:
        model = IdentidadVisual
        fields = [
            "nombre_tienda",
            "correo_contacto",
            "telefono",
            "instagram",
            "facebook",
            "tiktok",
            "x_twitter",
            "color_primario",
            "color_secundario",
            "color_acento",
            "tipo_fondo",
            "color_fondo",
        ]
        widgets = {"tipo_fondo": forms.RadioSelect}  # noqa: RUF012

    COLORES = ("color_primario", "color_secundario", "color_acento", "color_fondo")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Obligatorios para `CO-131`, aunque el modelo los admita vacíos antes
        # de la primera configuración.
        self.fields["correo_contacto"].required = True
        self.fields["nombre_tienda"].required = True
        for campo in self.COLORES:
            self.fields[campo].widget.attrs.update(
                {"placeholder": "#RRGGBB", "maxlength": 7, "data-color-tienda": campo}
            )

    def _limpiar_hex(self, campo):
        valor = (self.cleaned_data.get(campo) or "").strip()
        if not HEX.match(valor):
            raise forms.ValidationError("Tiene que ser un código HEX de 6 dígitos, como #1A2B3C.")
        return valor.upper()

    def clean_color_primario(self):
        return self._limpiar_hex("color_primario")

    def clean_color_secundario(self):
        return self._limpiar_hex("color_secundario")

    def clean_color_acento(self):
        return self._limpiar_hex("color_acento")

    def clean_color_fondo(self):
        return self._limpiar_hex("color_fondo")

    def clean_nombre_tienda(self):
        nombre = " ".join(self.cleaned_data["nombre_tienda"].split())
        if not nombre:
            raise forms.ValidationError("El nombre de la tienda no puede quedar vacío.")
        return nombre

    def clean_logo_nuevo(self):
        archivo = self.cleaned_data.get("logo_nuevo")
        return _imagen(archivo) if archivo else None

    def clean_fondo_nuevo(self):
        archivo = self.cleaned_data.get("fondo_nuevo")
        if not archivo:
            return None
        return _imagen(archivo, lado_mayor=imagenes.LADO_MAYOR_BANNER)

    def clean(self):
        datos = super().clean()
        con_imagen = datos.get("fondo_nuevo") or self.instance.imagen_fondo
        if (
            datos.get("tipo_fondo") == IdentidadVisual.IMAGEN
            and not con_imagen
            and "fondo_nuevo" not in self.errors
        ):
            self.add_error("fondo_nuevo", "Un fondo de imagen necesita una imagen.")
        return datos
