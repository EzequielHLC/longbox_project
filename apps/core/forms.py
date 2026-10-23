"""Formularios del contenido de la tienda (módulo 17, tanda 2).

Las imágenes se procesan en el `clean` del campo (RNF-05): si una no cumple,
el formulario no es válido y nada se guarda. Lo que llega a la vista ya es la
versión WebP; el archivo subido no sigue de largo.
"""

import re

from django import forms
from django.core.validators import MaxValueValidator

from apps.core import colores, imagenes
from apps.core.contraste import MINIMO_TEXTO, contraste
from apps.core.models import Banner, FilaPortada, IdentidadVisual

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
    # Quitar una imagen vuelve a la vista predeterminada (B-07-025).
    quitar_logo = forms.BooleanField(label="Quitar el logo", required=False)
    quitar_acceso = forms.BooleanField(label="Quitar la imagen del ingreso", required=False)
    acceso_nueva = forms.FileField(
        label="Imagen del ingreso",
        required=False,
        help_text=(
            "Acompaña al formulario de ingreso y de registro, a la izquierda. Vertical o "
            "cuadrada. Sin imagen se usa el logo. Se guarda en WebP."
        ),
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
            *(rol.campo for rol in colores.ROLES),
            "descripcion_tienda",
            "portada_antetitulo",
            "portada_titulo",
            "portada_bajada",
            "ticker_mensajes",
        ]
        widgets = {  # noqa: RUF012
            "tipo_fondo": forms.RadioSelect,
            "ticker_mensajes": forms.Textarea(attrs={"rows": 4}),
        }

    COLORES = ("color_primario", "color_secundario", "color_acento", "color_fondo")
    TEXTOS_CON_VALOR_INICIAL = (
        "descripcion_tienda",
        "portada_antetitulo",
        "portada_titulo",
        "portada_bajada",
    )

    def _texto_o_inicial(self, campo):
        valor = " ".join((self.cleaned_data.get(campo) or "").split())
        return valor or IdentidadVisual._meta.get_field(campo).default

    def clean_descripcion_tienda(self):
        return self._texto_o_inicial("descripcion_tienda")

    def clean_portada_antetitulo(self):
        return self._texto_o_inicial("portada_antetitulo")

    def clean_portada_titulo(self):
        return self._texto_o_inicial("portada_titulo")

    def clean_portada_bajada(self):
        return self._texto_o_inicial("portada_bajada")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Obligatorios para `CO-131`, aunque el modelo los admita vacíos antes
        # de la primera configuración.
        self.fields["correo_contacto"].required = True
        self.fields["nombre_tienda"].required = True
        # Los textos del escaparate (B-17-015) no se pueden dejar en blanco:
        # vacíos, vuelven a su valor inicial.
        for campo in self.TEXTOS_CON_VALOR_INICIAL:
            self.fields[campo].required = False
        for campo in self.COLORES:
            self.fields[campo].widget.attrs.update(
                {"placeholder": "#RRGGBB", "maxlength": 7, "data-color-tienda": campo}
            )
        # El mapa de colores: cada rol ofrece sólo sus opciones (`colores.ROLES`).
        for rol in colores.ROLES:
            campo = self.fields[rol.campo]
            campo.choices = [(clave, colores.NOMBRES[clave]) for clave in rol.opciones]
            campo.help_text = rol.alcance
            campo.widget.attrs["data-rol-color"] = rol.clave
            # Un rol que no viaja conserva el que tenía (`clean`).
            campo.required = False

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

    def clean_acceso_nueva(self):
        archivo = self.cleaned_data.get("acceso_nueva")
        if not archivo:
            return None
        return _imagen(archivo, lado_mayor=imagenes.LADO_MAYOR_BANNER)

    def clean_fondo_nuevo(self):
        archivo = self.cleaned_data.get("fondo_nuevo")
        if not archivo:
            return None
        return _imagen(archivo, lado_mayor=imagenes.LADO_MAYOR_BANNER)

    def clean(self):
        datos = super().clean()
        for rol in colores.ROLES:
            if not datos.get(rol.campo) and rol.campo not in self.errors:
                datos[rol.campo] = getattr(self.instance, rol.campo, None) or rol.inicial
        # `identidad_visual.md`: el texto secundario y el acento tienen que
        # leerse sobre el fondo, con 4,5:1 como mínimo.
        fondo = datos.get("color_fondo")
        for campo, nombre in (("color_secundario", "secundario"), ("color_acento", "de acento")):
            color = datos.get(campo)
            if fondo and color and contraste(color, fondo) < MINIMO_TEXTO:
                self.add_error(
                    campo,
                    f"El color {nombre} no se lee sobre el fondo: el contraste es "
                    f"{contraste(color, fondo):.1f}:1 y el mínimo es 4,5:1.",
                )
        con_imagen = datos.get("fondo_nuevo") or self.instance.imagen_fondo
        if (
            datos.get("tipo_fondo") == IdentidadVisual.IMAGEN
            and not con_imagen
            and "fondo_nuevo" not in self.errors
        ):
            self.add_error("fondo_nuevo", "Un fondo de imagen necesita una imagen.")
        return datos


class FilaPortadaForm(forms.ModelForm):
    """Una fila de la portada: una etiqueta o un grupo entero (B-07-009).

    El origen es un solo desplegable con las dos clases de opción, agrupadas:
    primero los grupos enteros y después las etiquetas de cada grupo. Sólo se
    ofrecen las vigentes; la que ya tiene la fila se sigue ofreciendo aunque se
    haya dado de baja, para que la edición no la pierda en silencio.
    """

    origen = forms.ChoiceField(label="Etiqueta o grupo")
    # La imagen de la tarjeta titular (B-07-010). Archivo y «quitar» van por
    # separado: el control de Django que junta los dos no se dibuja con `_campo`.
    imagen = forms.FileField(
        label="Imagen del título",
        required=False,
        help_text="Opcional. Vertical, como una portada. Se guarda en WebP.",
    )
    quitar_imagen = forms.BooleanField(label="Quitar la imagen", required=False)

    class Meta:
        model = FilaPortada
        fields = ["titulo", "orden", "activa"]
        # El orden lo pone la pantalla al arrastrar las tarjetas (B-07-010).
        widgets = {"orden": forms.HiddenInput(attrs={"data-orden": ""})}  # noqa: RUF012

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from apps.catalog.models import Etiqueta, GrupoEtiqueta

        # El interruptor ya dice «Activa» o «Inactiva»: el rótulo no lo repite.
        self.fields["activa"].label = "Estado"
        actual = self.instance
        grupos = GrupoEtiqueta.objects.filter(activo=True) | GrupoEtiqueta.objects.filter(
            pk=actual.grupo_id or 0
        )
        etiquetas = Etiqueta.objects.filter(
            activa=True, grupo__activo=True
        ) | Etiqueta.objects.filter(pk=actual.etiqueta_id or 0)
        opciones = [("", "Elegí una etiqueta o un grupo")]
        opciones.append(
            (
                "Grupos enteros",
                [
                    (f"g:{g.pk}", f"{g.nombre} (todas sus etiquetas)")
                    for g in grupos.order_by("nombre")
                ],
            )
        )
        por_grupo = {}
        for etiqueta in etiquetas.select_related("grupo").order_by("grupo__nombre", "nombre"):
            por_grupo.setdefault(etiqueta.grupo.nombre, []).append(
                (f"e:{etiqueta.pk}", etiqueta.nombre)
            )
        opciones.extend(por_grupo.items())
        self.fields["origen"].choices = opciones
        if actual.etiqueta_id:
            self.initial["origen"] = f"e:{actual.etiqueta_id}"
        elif actual.grupo_id:
            self.initial["origen"] = f"g:{actual.grupo_id}"

    def clean_imagen(self):
        archivo = self.cleaned_data.get("imagen")
        return _imagen(archivo) if archivo else None

    def clean_origen(self):
        clase, _, pk = self.cleaned_data["origen"].partition(":")
        if clase not in ("e", "g") or not pk.isdigit():
            raise forms.ValidationError("Elegí una etiqueta o un grupo de la lista.")
        return clase, int(pk)

    def save(self, commit=True):
        clase, pk = self.cleaned_data["origen"]
        self.instance.etiqueta_id = pk if clase == "e" else None
        self.instance.grupo_id = pk if clase == "g" else None
        if self.cleaned_data.get("imagen"):
            self.instance.imagen = self.cleaned_data["imagen"]
        elif self.cleaned_data.get("quitar_imagen"):
            self.instance.imagen = ""
        return super().save(commit=commit)

    @property
    def cambio_la_imagen(self):
        return bool(self.cleaned_data.get("imagen") or self.cleaned_data.get("quitar_imagen"))


# Sin formulario vacío fijo: «Agregar fila» copia `empty_form` (B-07-010).
FilasPortadaFormSet = forms.modelformset_factory(
    FilaPortada, form=FilaPortadaForm, extra=0, can_delete=True
)
