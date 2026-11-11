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
from apps.core.models import Banner, IdentidadVisual, ImagenDeSeccion, SeccionPortada

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


def _opciones_de_etiquetas(etiqueta_actual=None, grupo_actual=None, texto_grupo="{}"):
    """Grupos enteros y etiquetas por grupo, vigentes, para un desplegable agrupado.

    La etiqueta o el grupo que ya tiene el registro se sigue ofreciendo aunque se
    haya dado de baja, para que la edición no lo pierda en silencio.
    """
    from apps.catalog.models import Etiqueta, GrupoEtiqueta

    grupos = GrupoEtiqueta.objects.filter(activo=True) | GrupoEtiqueta.objects.filter(
        pk=grupo_actual or 0
    )
    etiquetas = Etiqueta.objects.filter(activa=True, grupo__activo=True) | Etiqueta.objects.filter(
        pk=etiqueta_actual or 0
    )
    opciones = [
        (
            "Grupos enteros",
            [(f"g:{g.pk}", texto_grupo.format(g.nombre)) for g in grupos.order_by("nombre")],
        )
    ]
    por_grupo = {}
    for etiqueta in etiquetas.select_related("grupo").order_by("grupo__nombre", "nombre"):
        por_grupo.setdefault(etiqueta.grupo.nombre, []).append(
            (f"e:{etiqueta.pk}", etiqueta.nombre)
        )
    opciones.extend(por_grupo.items())
    return opciones


class SeccionPortadaForm(forms.ModelForm):
    """Una sección de la portada (`CU-CFG-SEC`; plan 07, novena parte).

    El tipo se elige al agregarla y después no cambia: cambiar una cinta de fotos
    por una fila de productos dejaría imágenes huérfanas. Lo que pide cada tipo
    lo valida el servidor, no la pantalla: el origen, sólo en las de productos;
    la presentación en vitrina, también; las fijas no se borran.

    El origen de las de productos es un solo desplegable con las dos clases de
    opción, agrupadas: primero los grupos enteros y después las etiquetas de
    cada grupo (B-07-009).
    """

    origen = forms.ChoiceField(label="Etiqueta o grupo", required=False)
    # La imagen de la tarjeta titular de una fila (B-07-010). Archivo y «quitar»
    # van por separado: el control de Django que junta los dos no se dibuja con `_campo`.
    imagen = forms.FileField(
        label="Imagen del título",
        required=False,
        help_text="Opcional. Vertical, como una portada. Se guarda en WebP.",
    )
    quitar_imagen = forms.BooleanField(label="Quitar la imagen", required=False)

    class Meta:
        model = SeccionPortada
        fields = [
            "tipo",
            "presentacion",
            "titulo",
            "antetitulo",
            "texto",
            "texto_boton",
            "orden",
            "activa",
        ]
        # El orden lo pone la pantalla al arrastrar las tarjetas (B-07-010).
        widgets = {  # noqa: RUF012
            "orden": forms.HiddenInput(attrs={"data-orden": ""}),
            "tipo": forms.Select(attrs={"data-tipo-seccion": ""}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # El interruptor ya dice «Activa» o «Inactiva»: el rótulo no lo repite.
        self.fields["activa"].label = "Estado"
        self.fields["presentacion"].required = False
        # Las fijas existen siempre: no se agregan desde «Agregar sección».
        self.fields["tipo"].choices = [
            (valor, nombre)
            for valor, nombre in SeccionPortada.TIPOS
            if valor not in SeccionPortada.FIJAS or valor == self.instance.tipo
        ]
        actual = self.instance
        self.fields["origen"].choices = [
            ("", "Elegí una etiqueta o un grupo"),
            *_opciones_de_etiquetas(
                actual.etiqueta_id, actual.grupo_id, "{} (todas sus etiquetas)"
            ),
        ]
        if actual.etiqueta_id:
            self.initial["origen"] = f"e:{actual.etiqueta_id}"
        elif actual.grupo_id:
            self.initial["origen"] = f"g:{actual.grupo_id}"

    @property
    def tipo_elegido(self):
        """El tipo con que se dibuja la tarjeta: el guardado, o el elegido al agregarla."""
        if self.instance.pk:
            return self.instance.tipo
        if self.is_bound:
            return self.data.get(self.add_prefix("tipo")) or SeccionPortada.PRODUCTOS
        return self.initial.get("tipo", SeccionPortada.PRODUCTOS)

    def clean_tipo(self):
        tipo = self.cleaned_data["tipo"]
        if self.instance.pk and tipo != self.instance.tipo:
            raise forms.ValidationError("El tipo de una sección no se cambia: agregue otra.")
        return tipo

    def clean_imagen(self):
        archivo = self.cleaned_data.get("imagen")
        return _imagen(archivo) if archivo else None

    def clean(self):
        datos = super().clean()
        tipo = datos.get("tipo")
        if tipo is None:
            return datos
        if tipo == SeccionPortada.PRODUCTOS:
            clase, _, pk = (datos.get("origen") or "").partition(":")
            if clase not in ("e", "g") or not pk.isdigit():
                self.add_error("origen", "Elegí una etiqueta o un grupo de la lista.")
            else:
                datos["origen"] = (clase, int(pk))
            datos["presentacion"] = datos.get("presentacion") or SeccionPortada.FILA
        else:
            datos["origen"] = None
            datos["presentacion"] = SeccionPortada.FILA
        if datos.get("DELETE") and self.instance.fija:
            raise forms.ValidationError(
                f"«{self.instance.titulo_visible}» no se puede quitar: se puede apagar."
            )
        return datos

    def save(self, commit=True):
        origen = self.cleaned_data.get("origen")
        clase, pk = origen if origen else (None, None)
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


class _SeccionesBase(forms.BaseModelFormSet):
    def clean(self):
        super().clean()
        borradas = [f for f in self.deleted_forms if f.instance.pk and f.instance.fija]
        if borradas:
            raise forms.ValidationError("Recién llegados y Lo que se viene no se quitan.")


# Sin formulario vacío fijo: «Agregar sección» copia `empty_form` (B-07-010).
SeccionesPortadaFormSet = forms.modelformset_factory(
    SeccionPortada,
    form=SeccionPortadaForm,
    formset=_SeccionesBase,
    extra=0,
    can_delete=True,
)


class ImagenDeSeccionForm(forms.ModelForm):
    """Una imagen de una sección: un acceso, una viñeta, una foto o la del panel.

    «Lleva a» es una lista cerrada (ambigüedad 4): sin enlace, las pre-ventas,
    un grupo, una etiqueta, un tipo, una editorial o un producto, que se indica
    por su código porque es lo que lo identifica (regla 1 del dominio).
    Cualquier otro valor se rechaza, y la base exige además que el destino
    tenga su dato.
    """

    lleva_a = forms.ChoiceField(label="Lleva a", required=False)
    codigo_producto = forms.CharField(
        label="Código del producto",
        required=False,
        max_length=40,
        help_text="El código de la ficha del producto.",
    )
    imagen = forms.FileField(
        label="Imagen",
        required=False,
        help_text="Se guarda en WebP, con 1920 px en el lado mayor.",
    )

    class Meta:
        model = ImagenDeSeccion
        fields = ["titulo", "texto", "forma_texto", "orden"]
        widgets = {"orden": forms.HiddenInput(attrs={"data-orden-imagen": ""})}  # noqa: RUF012

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from apps.catalog.models import Editorial, Tipo

        actual = self.instance
        tipos = Tipo.objects.filter(activo=True) | Tipo.objects.filter(
            pk=actual.tipo_producto_id or 0
        )
        editoriales = Editorial.objects.filter(activa=True) | Editorial.objects.filter(
            pk=actual.editorial_id or 0
        )
        self.fields["lleva_a"].choices = [
            (ImagenDeSeccion.SIN_ENLACE, "Sin enlace"),
            (ImagenDeSeccion.PREVENTAS, "Las pre-ventas"),
            (ImagenDeSeccion.PRODUCTO, "Un producto (por su código)"),
            *_opciones_de_etiquetas(actual.etiqueta_id, actual.grupo_id, "{} (grupo entero)"),
            ("Tipos de producto", [(f"t:{t.pk}", t.nombre) for t in tipos.order_by("nombre")]),
            ("Editoriales", [(f"d:{e.pk}", e.nombre) for e in editoriales.order_by("nombre")]),
        ]
        prefijos = {
            ImagenDeSeccion.ETIQUETA: "e",
            ImagenDeSeccion.GRUPO: "g",
            ImagenDeSeccion.TIPO: "t",
            ImagenDeSeccion.EDITORIAL: "d",
        }
        if actual.destino in prefijos:
            dato = actual.dato_del_destino
            self.initial["lleva_a"] = f"{prefijos[actual.destino]}:{dato.pk}"
        else:
            self.initial["lleva_a"] = actual.destino
        if actual.producto_id:
            self.initial["codigo_producto"] = actual.producto.codigo

    def clean_imagen(self):
        archivo = self.cleaned_data.get("imagen")
        return _imagen(archivo) if archivo else None

    def clean(self):
        from apps.catalog.models import Editorial, Etiqueta, GrupoEtiqueta, Producto, Tipo

        datos = super().clean()
        elegido = datos.get("lleva_a") or ImagenDeSeccion.SIN_ENLACE
        destino = {"destino": elegido}
        clase, _, pk = elegido.partition(":")
        modelos = {
            "e": (ImagenDeSeccion.ETIQUETA, "etiqueta", Etiqueta),
            "g": (ImagenDeSeccion.GRUPO, "grupo", GrupoEtiqueta),
            "t": (ImagenDeSeccion.TIPO, "tipo_producto", Tipo),
            "d": (ImagenDeSeccion.EDITORIAL, "editorial", Editorial),
        }
        if clase in modelos and pk.isdigit():
            valor, campo, modelo = modelos[clase]
            objeto = modelo.objects.filter(pk=int(pk)).first()
            if objeto is None:
                self.add_error("lleva_a", "Elegí un destino de la lista.")
            destino = {"destino": valor, campo: objeto}
        elif elegido == ImagenDeSeccion.PRODUCTO:
            codigo = (datos.get("codigo_producto") or "").strip()
            producto = Producto.objects.filter(codigo__iexact=codigo).first() if codigo else None
            if producto is None:
                self.add_error(
                    "codigo_producto",
                    (
                        "No hay ningún producto con ese código."
                        if codigo
                        else "Indique el código del producto."
                    ),
                )
            destino["producto"] = producto
        elif elegido not in (ImagenDeSeccion.SIN_ENLACE, ImagenDeSeccion.PREVENTAS):
            self.add_error("lleva_a", "Elegí un destino de la lista.")
        datos["destino"] = destino
        tiene_imagen = datos.get("imagen") or self.instance.imagen
        if not tiene_imagen and datos.get("forma_texto") != ImagenDeSeccion.GRITO:
            self.add_error("imagen", "Falta la imagen. Sólo una onomatopeya puede ir sin imagen.")
        if datos.get("forma_texto") == ImagenDeSeccion.GRITO and not datos.get("texto"):
            self.add_error("texto", "Una onomatopeya necesita su texto.")
        return datos

    def save(self, commit=True):
        destino = self.cleaned_data["destino"]
        for campo in ("etiqueta", "grupo", "tipo_producto", "editorial", "producto"):
            setattr(self.instance, campo, destino.get(campo))
        self.instance.destino = destino["destino"]
        if self.cleaned_data.get("imagen"):
            self.instance.imagen = self.cleaned_data["imagen"]
        return super().save(commit=commit)

    @property
    def cambio_la_imagen(self):
        return bool(self.cleaned_data.get("imagen"))


class _ImagenesBase(forms.BaseInlineFormSet):
    """Las imágenes de una sección, dentro de la tarjeta de la sección.

    El formulario vacío usa `__imagen__` y no `__prefix__`: la tarjeta de una
    sección nueva también es un formulario vacío, y el guion que la copia
    reemplaza `__prefix__` en todo su contenido.
    """

    @property
    def empty_form(self):
        formulario = self.form(
            auto_id=self.auto_id,
            prefix=self.add_prefix("__imagen__"),
            empty_permitted=True,
            use_required_attribute=False,
            **self.get_form_kwargs(None),
            renderer=self.renderer,
        )
        self.add_fields(formulario, None)
        return formulario

    def cantidad(self):
        """Cuántas quedan al guardar: las que no se quitan y no están vacías."""
        return sum(
            1
            for f in self.forms
            if not (self.can_delete and self._should_delete_form(f))
            and (f.instance.pk or f.has_changed())
        )


ImagenesDeSeccionFormSet = forms.inlineformset_factory(
    SeccionPortada,
    ImagenDeSeccion,
    form=ImagenDeSeccionForm,
    formset=_ImagenesBase,
    extra=0,
    can_delete=True,
)
