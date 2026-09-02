"""Formularios del alta y la edición de proveedores (CU-18, CU-19).

Los dos usan el mismo formulario porque piden exactamente los mismos campos: la
diferencia entre el alta y la edición no está en qué se carga sino en qué pasa
después, y eso vive en las vistas.
"""

import re

from django import forms
from django.db.models.functions import Lower

from apps.catalog.forms import editoriales_activas, tipos_activos
from apps.suppliers import muestras
from apps.suppliers.models import Proveedor

# CU-19 A1, textual: el CU la cita como el mensaje que el sistema debe mostrar
# antes de dejar cambiar el correo. Se conserva tal cual, con el mismo criterio
# que la advertencia del precio manual de CU-02.
ADVERTENCIA_CAMBIO_DE_CORREO = (
    "El correo anterior dejará de ser reconocido como remitente válido. Los mensajes del "
    "proveedor deben enviarse al correo nuevo a partir de este cambio."
)

RAZON_SOCIAL_MINIMA = 2


class ProveedorForm(forms.ModelForm):
    """Alta y edición de un proveedor editorial.

    El campo de confirmación no es un dato del proveedor: es la respuesta a la
    advertencia de CU-19 A1, y **la exige el servidor**. El cartel del navegador
    ayuda a no cambiar el correo sin querer, pero el que decide es este archivo:
    si la confirmación viviera solo en el JavaScript, una pestaña de
    herramientas abierta alcanzaría para sacar del filtro de remitentes el
    correo por el que entra todo el pipeline de CU-04.
    """

    confirma_cambio_de_correo = forms.BooleanField(
        label="Confirmo el cambio de correo comercial", required=False
    )

    class Meta:
        model = Proveedor
        fields = [
            "razon_social",
            "correo_comercial",
            "editorial",
            "tipo_por_defecto",
            "procesa_novedades",
            "nombre_contacto",
            "telefono",
            "notas",
        ]
        widgets = {  # noqa: RUF012
            "notas": forms.Textarea(attrs={"rows": 3}),
            "razon_social": forms.TextInput(attrs={"autocomplete": "off"}),
            "correo_comercial": forms.EmailInput(attrs={"autocomplete": "off"}),
        }
        help_texts = {  # noqa: RUF012
            "correo_comercial": (
                "Es el remitente que habilita el procesamiento automático de sus novedades."
            ),
            "notas": "Uso interno. No se le muestran al proveedor.",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # El correo anterior se guarda antes de que el formulario toque la
        # instancia: la vista lo necesita para auditar el par completo, y `clean`
        # para saber si hubo cambio.
        self.correo_anterior = self.instance.correo_comercial if self.instance.pk else ""
        # En un alta no hay correo anterior que invalidar, así que la
        # confirmación no tiene sentido y no se dibuja.
        if not self.instance.pk:
            del self.fields["confirma_cambio_de_correo"]

        # Los dos catálogos se pueden ampliar sin recargar la pantalla, así que
        # la consulta se rearma en cada instancia y no queda congelada en la
        # definición de la clase. Solo se ofrecen los activos: vincular un
        # proveedor a una editorial dada de baja dejaría borradores apuntando a
        # algo que ya no aparece en ningún desplegable del alta.
        self.fields["editorial"].queryset = editoriales_activas()
        self.fields["tipo_por_defecto"].queryset = tipos_activos()

        # El vacío significa algo, así que se dice. Es el mismo criterio con el
        # que la cabecera de un lote sin editorial anuncia "Mixto".
        self.fields["editorial"].empty_label = "Varias — se extrae de cada correo"
        self.fields["tipo_por_defecto"].empty_label = "Sin declarar — se extrae de cada correo"

    # -- normalización --------------------------------------------------------

    def clean_razon_social(self):
        """Espacios internos normalizados, igual que los títulos de producto.

        Sin esto, "Editorial  Ivrea" y "Editorial Ivrea" son dos proveedores
        distintos para cualquiera que compare sin normalizar —y para la
        restricción de unicidad de la base, que compara en crudo—.
        """
        razon = " ".join(self.cleaned_data["razon_social"].split())
        if len(razon) < RAZON_SOCIAL_MINIMA:
            raise forms.ValidationError(
                f"La razón social necesita al menos {RAZON_SOCIAL_MINIMA} caracteres."
            )
        self.conflicto_razon_social = self._existente("razon_social", razon)
        if self.conflicto_razon_social:
            raise forms.ValidationError(
                f"Ya hay un proveedor registrado con la razón social "
                f"«{self.conflicto_razon_social.razon_social}»."
            )
        return razon

    def clean_correo_comercial(self):
        """El correo se guarda en minúscula, no solo se compara así.

        Es la clave con la que CU-04 reconoce un remitente. Normalizarlo al
        guardar —y no únicamente al comparar— hace que la búsqueda del pipeline
        y lo que muestra la pantalla digan siempre lo mismo.
        """
        correo = self.cleaned_data["correo_comercial"].strip().lower()
        self.conflicto_correo = self._existente("correo_comercial", correo)
        if self.conflicto_correo:
            raise forms.ValidationError(
                f"El correo «{correo}» ya está registrado para "
                f"«{self.conflicto_correo.razon_social}»."
            )
        return correo

    def _existente(self, campo, valor):
        """El proveedor que ya ocupa ese valor, sin distinguir mayúsculas.

        E2 de CU-18 pide informar el conflicto **con enlace a la ficha del
        proveedor existente**, así que no alcanza con saber que hay choque: hace
        falta contra quién. Por eso devuelve el objeto y no un booleano.
        """
        return (
            Proveedor.objects.annotate(normalizado=Lower(campo))
            .filter(normalizado=valor.casefold())
            .exclude(pk=self.instance.pk)
            .first()
        )

    # -- la advertencia de CU-19 A1 ------------------------------------------

    @property
    def cambia_el_correo(self):
        nuevo = self.cleaned_data.get("correo_comercial") if hasattr(self, "cleaned_data") else ""
        return bool(self.correo_anterior) and bool(nuevo) and nuevo != self.correo_anterior

    def clean(self):
        datos = super().clean()
        if self.cambia_el_correo and not datos.get("confirma_cambio_de_correo"):
            self.add_error("correo_comercial", ADVERTENCIA_CAMBIO_DE_CORREO)
        return datos


MOTIVO_MINIMO = 4


class DescarteDeCorreoForm(forms.Form):
    """El motivo por el que un correo sale de la cola sin procesarse.

    Es obligatorio, con el mismo criterio con el que CU-05 lo exige al rechazar
    un borrador: una cola llena de correos descartados sin explicación no sirve
    para entender nada dentro de tres meses, y menos para decidir a qué
    proveedores conviene dejarles el procesamiento prendido.
    """

    motivo = forms.CharField(
        label="Motivo del descarte",
        max_length=500,
        widget=forms.Textarea(
            attrs={"rows": 2, "placeholder": "Por ejemplo: es una factura, no un anuncio."}
        ),
    )

    def clean_motivo(self):
        motivo = " ".join(self.cleaned_data["motivo"].split())
        if len(motivo) < MOTIVO_MINIMO:
            raise forms.ValidationError("Escriba un motivo: una o dos letras no explican nada.")
        return motivo


class PruebaDelModeloForm(forms.Form):
    """El texto que se le manda al modelo desde la pantalla de diagnóstico.

    Es editable a propósito: el valor de esta pantalla no es correr una prueba
    fija sino poder pegar el contenido de un correo que salió mal y ver qué
    entiende el modelo, sin tener que meterlo antes en la cola.

    Y la muestra **se genera distinta en cada carga** (ver `muestras.py`).
    Mostrar siempre los mismos tres tomos deja la duda de si el modelo los está
    reconociendo en vez de leerlos; con datos nuevos cada vez, lo que se ve es
    que lee. La contra es que hay que llevar los identificadores de portada
    junto con el texto, porque ya no son constantes: por eso el formulario
    guarda la muestra que armó y la vista le pide sus `cids`.
    """

    contenido = forms.CharField(
        label="Contenido a interpretar",
        widget=forms.Textarea(attrs={"rows": 10, "spellcheck": "false"}),
        help_text=(
            "Se genera una muestra distinta en cada carga. También puede pegar el "
            "contenido de un correo real."
        ),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # La muestra se arma solo cuando el formulario está vacío: en un envío,
        # lo que vale es lo que escribió la persona.
        self.muestra = None if self.is_bound else muestras.armar()
        if self.muestra:
            self.fields["contenido"].initial = self.muestra.contenido

    @property
    def cids(self):
        """Los identificadores de portada contra los que validar la extracción.

        Con la muestra recién armada son los suyos. Con un contenido pegado a
        mano no hay forma de saber qué portadas traía el correo original, así
        que se leen del propio texto: es lo único honesto: inventar un conjunto
        haría que la comprobación de portada inexistente rechazara todo.
        """
        if self.muestra:
            return self.muestra.cids
        return _cids_del_texto(self.data.get("contenido", ""))


def _cids_del_texto(contenido):
    """Los identificadores que aparecen marcados en el texto."""
    return frozenset(re.findall(r"\[imagen:([^\]]+)\]", contenido or ""))
