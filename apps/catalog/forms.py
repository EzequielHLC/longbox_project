"""Formularios del alta en lote.

El armado tiene dos piezas: una **cabecera** con los datos que comparte todo el
lote y un **formset de ítems**. Dos reglas ordenan todo el archivo:

1. **La cabecera es opcional.** Si queda vacía, el lote es *mixto* y cada ítem
   declara lo suyo. Por eso la validación de los campos obligatorios no puede
   vivir en la cabecera: corre por ítem, sobre el valor ya resuelto.
2. **Qué campos pide un ítem depende de su tipo**, y eso es un dato y no un
   `if` con nombres escritos a mano. Un manga pide formato y solo se le ofrecen
   los tamaños de manga; un artbook no pide ninguno. Las etiquetas, en cambio,
   se ofrecen para todo: describen y no identifican, así que ningún tipo las
   excluye y ninguna traba un alta.

Sobre la validación: la pantalla también valida, pero acá está la que cuenta. El
navegador ayuda a no perder el viaje; el que decide qué entra a la base es este
archivo. Cualquier regla que esté solo en el JavaScript se esquiva con una
pestaña de herramientas del desarrollador abierta.
"""

from decimal import Decimal

from django import forms
from django.core.validators import MinLengthValidator
from django.db import models
from django.db.models.functions import Lower
from django.utils import timezone

from apps.catalog import isbn as isbn_util
from apps.catalog import precios
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
from apps.catalog.services import precio_de_referencia
from apps.core import cotizaciones
from apps.core.models import ConfiguracionSistema

# Texto exacto que la documentación de casos de uso exige mostrar al editar el
# precio final de un importado. Se deja tal cual está en la fuente —tuteo
# incluido— porque está citado como el mensaje que el sistema debe mostrar:
# cambiarlo sería modificar un requisito, no un estilo.
ADVERTENCIA_PRECIO_MANUAL = (
    "Modificar el precio final rompe el vínculo con el margen global. "
    "Este precio no será recalculado automáticamente ante cambios de margen."
)

MENSAJE_LOTE_VACIO = "Cargue al menos un ítem para poder guardar el lote."
MENSAJE_REPETIDO_EN_LOTE = (
    "Este ítem está repetido dentro del mismo lote: ya hay otro con el mismo título, "
    "volumen, tipo, formato y editorial."
)
MENSAJE_FECHA_PASADA = "La fecha de llegada no puede ser anterior a hoy."
MENSAJE_COTIZACION_EN_PESOS = (
    "Un lote cargado en pesos no lleva cotización. Elija una moneda extranjera o "
    "deje el campo vacío."
)
MENSAJE_FORMATO_NO_APLICA = "El tipo elegido no se clasifica por formato."

# ---------------------------------------------------------------------------
# Topes. No son límites técnicos —la base aguanta mucho más— sino filtros de
# tipeo: nadie carga el volumen 40.000 de una serie ni un cómic de cien
# millones de pesos, y las dos cosas se escriben solas con un cero de más.
# ---------------------------------------------------------------------------
VOLUMEN_MAXIMO = 9999
STOCK_MAXIMO = 100_000
IMPORTE_MAXIMO = Decimal("9999999.99")
TOTAL_MAXIMO = Decimal("999999999.99")
COTIZACION_MAXIMA = Decimal("9999999.9999")
TITULO_MINIMO = 2

# Vale para el nombre de cualquier catálogo (editorial, etiqueta): una sola
# letra no distingue nada y casi siempre es un enter de más.
NOMBRE_MINIMO = 2

# 5 MB. Una portada es una tapa, no un escaneo de imprenta; el tope evita que
# alguien suba un archivo de 40 MB y deje la pantalla colgada subiéndolo.
PORTADA_MAXIMA_BYTES = 5 * 1024 * 1024

# Estados con los que puede *nacer* un producto. Los otros tres del modelo
# —agotado, cancelado por editorial, descatalogado— son consecuencia de algo que
# pasa después, no una opción del alta.
ESTADOS_DE_ALTA = [
    (Producto.ACTIVO, "Activo"),
    (Producto.PRE_VENTA, "Pre-venta"),
]


def tipos_activos():
    return Tipo.objects.filter(activo=True)


def formatos_activos():
    return Formato.objects.filter(activo=True)


def editoriales_activas():
    return Editorial.objects.filter(activa=True)


def etiquetas_activas():
    """Las etiquetas ofrecibles, ya ordenadas por grupo.

    Se traen con su grupo porque la pantalla las dibuja agrupadas: sin
    `select_related` serían tantas consultas como etiquetas haya, en un
    formulario que además se repite por cada ítem del lote.
    """
    return Etiqueta.objects.filter(activa=True, grupo__activo=True).select_related("grupo")


def formatos_para(tipo):
    """Los formatos que aplican a un tipo.

    Un formato sin tipos declarados es universal —ver el modelo— así que entra
    siempre. Sin tipo elegido se ofrecen todos: esconder opciones antes de saber
    para qué son solo lograría que el campo parezca roto.
    """
    formatos = formatos_activos()
    if tipo is None:
        return formatos
    return formatos.filter(models.Q(tipos__isnull=True) | models.Q(tipos=tipo)).distinct()


def _validar_fecha_no_pasada(fecha):
    """Una fecha de llegada anterior a hoy no describe nada.

    Si el material ya llegó, el producto va Activo y sin fecha; si todavía no
    llegó, la fecha es futura. Una fecha pasada suele ser un año mal tipeado, y
    dejarla entrar genera una pre-venta que nunca se va a disparar.
    """
    if fecha and fecha < timezone.localdate():
        raise forms.ValidationError(MENSAJE_FECHA_PASADA)
    return fecha


def _campo_fecha(etiqueta):
    return forms.DateField(
        label=etiqueta,
        required=False,
        widget=forms.DateInput(attrs={"type": "date"}),
        validators=[_validar_fecha_no_pasada],
    )


def _campo_importe(etiqueta, *, required=True, maximo=IMPORTE_MAXIMO, ayuda="", minimo=None):
    """Un campo de dinero, siempre con el mismo tope, paso y alineación."""
    return forms.DecimalField(
        label=etiqueta,
        required=required,
        max_digits=12,
        decimal_places=2,
        min_value=Decimal("0.01") if minimo is None else minimo,
        max_value=maximo,
        help_text=ayuda,
        # `inputmode` le pide al celular el teclado numérico y `_campos.html`
        # lo usa además para alinear los importes a la derecha.
        widget=forms.NumberInput(attrs={"step": "0.01", "inputmode": "decimal"}),
    )


def _campo_etiquetas(etiqueta, ayuda):
    """El selector de etiquetas: casillas, no un desplegable múltiple.

    Un `<select multiple>` nativo obliga a saber que hay que sostener Ctrl y no
    deja ver de un vistazo qué está elegido. Las casillas ocupan más lugar pero
    se leen solas, y la pantalla las agrupa por grupo para que el bloque no sea
    una lista de treinta valores sueltos.
    """
    campo = forms.ModelMultipleChoiceField(
        label=etiqueta,
        queryset=Etiqueta.objects.none(),
        required=False,
        widget=forms.CheckboxSelectMultiple,
        help_text=ayuda,
    )
    # `Etiqueta.__str__` incluye el grupo —"Franquicia · Marvel"— porque en una
    # lista suelta hace falta para desambiguar. Acá las casillas ya vienen
    # agrupadas bajo el encabezado del grupo, así que repetirlo en cada una
    # sería ruido: se muestra solo el nombre.
    campo.label_from_instance = lambda etiqueta: etiqueta.nombre
    return campo


class CabeceraLoteForm(forms.Form):
    """Datos compartidos del lote. Todos los campos son opcionales."""

    editorial = forms.ModelChoiceField(
        label="Editorial",
        queryset=editoriales_activas(),
        required=False,
        empty_label="Mixto — se declara por ítem",
    )
    tipo = forms.ModelChoiceField(
        label="Tipo de material",
        queryset=tipos_activos(),
        required=False,
        empty_label="Mixto — se declara por ítem",
    )
    formato = forms.ModelChoiceField(
        label="Formato",
        queryset=formatos_activos(),
        required=False,
        empty_label="Se declara por ítem",
    )
    fecha_llegada = _campo_fecha("Fecha de llegada")

    # Las etiquetas van en la cabecera porque es donde se declaran una sola vez:
    # veinte tomos de la misma serie comparten franquicia y género igual que
    # comparten editorial. Cada ítem puede sumar las suyas, pero el caso normal
    # se resuelve acá arriba y no veinte veces.
    etiquetas = _campo_etiquetas(
        "Etiquetas del lote", "Se aplican a todos los ítems. Cada uno puede sumar las suyas."
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # El conjunto de editoriales se puede ampliar sin recargar la pantalla,
        # así que la consulta se rearma en cada instancia y no queda congelada
        # en la definición de la clase.
        self.fields["editorial"].queryset = editoriales_activas()
        self.fields["tipo"].queryset = tipos_activos()
        self.fields["formato"].queryset = formatos_activos()
        self.fields["etiquetas"].queryset = etiquetas_activas()

    def clean(self):
        datos = super().clean()
        tipo = datos.get("tipo")
        # Un formato de cabecera sobre un tipo que no se clasifica por formato
        # es contradictorio: se avisa en vez de guardarlo y que después nadie
        # entienda de dónde salió.
        if tipo and not tipo.usa_formato and datos.get("formato"):
            self.add_error("formato", MENSAJE_FORMATO_NO_APLICA)
        return datos

    def etiquetas_del_lote(self):
        """Las que heredan todos los ítems. Vacío si la cabecera no validó."""
        datos = getattr(self, "cleaned_data", {})
        return list(datos.get("etiquetas") or [])

    def lote(self):
        """Un `LoteAlta` sin guardar con la cabecera ya cargada."""
        return LoteAlta(
            origen=LoteAlta.NACIONAL,
            editorial=self.cleaned_data.get("editorial"),
            tipo=self.cleaned_data.get("tipo"),
            formato=self.cleaned_data.get("formato"),
            fecha_llegada=self.cleaned_data.get("fecha_llegada"),
        )


class CabeceraLoteImportadoForm(CabeceraLoteForm):
    """La cabecera del lote importado suma la calculadora de envío.

    A diferencia de la del nacional, el costo de envío y el valor de compra
    **no** son opcionales: sin ellos no hay CRE, y sin CRE no hay precio.
    """

    costo_envio_total = _campo_importe(
        "Costo total de envío internacional",
        maximo=TOTAL_MAXIMO,
        # Cero es válido: hay proveedores que bonifican el envío, y en ese caso
        # el CRE da cero y el precio base termina siendo el costo.
        minimo=Decimal("0"),
        ayuda="En la moneda de origen. Puede ser cero si el envío está bonificado.",
    )
    valor_compra_total = _campo_importe(
        "Valor total de compra en origen",
        maximo=TOTAL_MAXIMO,
        ayuda="En la moneda de origen. Es el divisor del CRE, así que no puede ser cero.",
    )
    moneda_origen = forms.ChoiceField(
        label="Moneda de origen",
        choices=cotizaciones.MONEDA_CHOICES,
        initial=cotizaciones.MONEDA_LOCAL,
        required=False,
    )
    cotizacion = forms.DecimalField(
        label="Cotización",
        max_digits=12,
        decimal_places=4,
        required=False,
        min_value=Decimal("0.0001"),
        max_value=COTIZACION_MAXIMA,
        help_text="Pesos por unidad de la moneda de origen.",
        widget=forms.NumberInput(attrs={"step": "0.0001", "inputmode": "decimal"}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # En un lote importado el precio no sale de ninguna tabla, así que el
        # formato es informativo: se ofrece para poder distinguir ediciones, no
        # para calcular.
        self.fields["formato"].help_text = (
            "Opcional. En un lote importado el precio sale del costo de origen, "
            "no de la tabla de referencia."
        )
        self.referencia_de_cotizaciones = cotizaciones.resumen_para_pantalla()

    def clean_moneda_origen(self):
        return self.cleaned_data.get("moneda_origen") or cotizaciones.MONEDA_LOCAL

    def clean(self):
        datos = super().clean()
        moneda = datos.get("moneda_origen")
        cotizacion = datos.get("cotizacion")

        if moneda == cotizaciones.MONEDA_LOCAL:
            # En pesos no hay nada que convertir. Se rechaza en vez de ignorar:
            # descartar en silencio un número que alguien escribió es la forma
            # más rápida de que un precio salga mal sin que nadie se entere.
            if cotizacion is not None and cotizacion != Decimal("1"):
                self.add_error("cotizacion", MENSAJE_COTIZACION_EN_PESOS)
            datos["cotizacion"] = Decimal("1")
        elif cotizacion is None:
            self.add_error("cotizacion", "Indique la cotización de la moneda declarada.")

        return datos

    @property
    def cotizacion_aplicada(self):
        """La cotización a usar en los cálculos: 1 si el lote ya viene en pesos."""
        datos = getattr(self, "cleaned_data", {})
        return datos.get("cotizacion") or precios.SIN_CONVERSION

    @property
    def cre_calculado(self):
        """El CRE del lote, o cero mientras la calculadora esté incompleta.

        Se consulta también cuando la cabecera **no** validó: los ítems se
        siguen dibujando y su desglose necesita un CRE con el que trabajar.
        """
        datos = getattr(self, "cleaned_data", {})
        envio = datos.get("costo_envio_total")
        compra = datos.get("valor_compra_total")
        if envio is None or compra is None:
            return Decimal("0")
        return precios.calcular_cre(envio, compra)

    def lote(self):
        lote = super().lote()
        lote.origen = LoteAlta.IMPORTADO
        lote.costo_envio_total = self.cleaned_data["costo_envio_total"]
        lote.valor_compra_total = self.cleaned_data["valor_compra_total"]
        # El CRE y el margen se congelan en el lote: los dos cambian con el
        # tiempo y la auditoría tiene que poder decir con cuáles se dieron de
        # alta estos precios.
        lote.cre = self.cre_calculado
        lote.margen_aplicado = ConfiguracionSistema.obtener().margen_ganancia
        lote.moneda_origen = self.cleaned_data.get("moneda_origen") or cotizaciones.MONEDA_LOCAL
        lote.cotizacion = self.cotizacion_aplicada
        return lote


class ItemLoteForm(forms.Form):
    """Un producto del lote.

    Recibe la cabecera ya validada porque necesita saber qué le toca aportar.
    Mientras la cabecera declare editorial y tipo, los del ítem llegan
    bloqueados y **manda la cabecera**; para variarlos hay que desbloquear el
    ítem, y eso convierte el lote en mixto.
    """

    # Campos que la cabecera puede imponer. El resto —precio, estado, fecha— se
    # puede sobrescribir por ítem sin desbloquear nada, tal como pide el CU.
    CAMPOS_HEREDABLES = ("editorial", "tipo", "formato")

    # En el alta nacional el formato fija el precio, así que es obligatorio para
    # los tipos que lo usan. En la importada es informativo.
    formato_obligatorio = True

    titulo = forms.CharField(
        label="Título",
        max_length=200,
        validators=[MinLengthValidator(TITULO_MINIMO)],
        widget=forms.TextInput(attrs={"autocomplete": "off", "placeholder": "Título del tomo"}),
    )
    volumen = forms.IntegerField(
        label="Volumen",
        min_value=0,
        max_value=VOLUMEN_MAXIMO,
        widget=forms.NumberInput(
            attrs={"inputmode": "numeric", "placeholder": "1", "data-solo-enteros": "1"}
        ),
    )
    isbn = forms.CharField(
        label="ISBN",
        max_length=20,
        required=False,
        help_text="Opcional. Con guiones o sin ellos: se guarda normalizado.",
        widget=forms.TextInput(
            attrs={
                "autocomplete": "off",
                "placeholder": "978-987-827-158-3",
                "inputmode": "numeric",
            }
        ),
    )
    editorial = forms.ModelChoiceField(
        label="Editorial",
        queryset=Editorial.objects.none(),
        required=False,
        empty_label="Según la cabecera",
    )
    tipo = forms.ModelChoiceField(
        label="Tipo de material",
        queryset=Tipo.objects.none(),
        required=False,
        empty_label="Según la cabecera",
    )
    formato = forms.ModelChoiceField(
        label="Formato",
        queryset=Formato.objects.none(),
        required=False,
        empty_label="Según la cabecera",
    )
    etiquetas = _campo_etiquetas(
        "Etiquetas propias", "Se suman a las del lote. Solo para lo que distingue a este ítem."
    )
    solo_adultos = forms.BooleanField(
        label="Solo para adultos",
        required=False,
        help_text="Se excluye del catálogo público.",
    )
    desbloqueado = forms.BooleanField(
        label="Este ítem usa otra clasificación", required=False, widget=forms.HiddenInput
    )
    estado = forms.ChoiceField(
        label="Estado",
        choices=[("", "Según la fecha de llegada"), *ESTADOS_DE_ALTA],
        required=False,
    )
    fecha_llegada = _campo_fecha("Fecha de llegada")
    stock = forms.IntegerField(
        label="Stock inicial",
        min_value=0,
        max_value=STOCK_MAXIMO,
        required=False,
        help_text="Sin declarar, el producto nace en cero.",
        widget=forms.NumberInput(
            attrs={"inputmode": "numeric", "placeholder": "0", "data-solo-enteros": "1"}
        ),
    )
    autor = forms.CharField(
        label="Autor",
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={"autocomplete": "off"}),
    )
    sinopsis = forms.CharField(
        label="Sinopsis", required=False, widget=forms.Textarea(attrs={"rows": 3})
    )
    portada = forms.ImageField(
        label="Portada",
        required=False,
        widget=forms.ClearableFileInput(attrs={"accept": "image/*"}),
    )

    def __init__(self, *args, cabecera=None, **kwargs):
        super().__init__(*args, **kwargs)
        # `cabecera` puede llegar vacía si la cabecera no validó: en ese caso el
        # ítem se comporta como si el lote fuera mixto y pide todo. La pantalla
        # muestra igual los dos bloques de errores.
        self.cabecera = cabecera or {}
        self.fields["editorial"].queryset = editoriales_activas()
        self.fields["tipo"].queryset = tipos_activos()
        self.fields["etiquetas"].queryset = etiquetas_activas()

        # El desplegable de formato se recorta a los que aplican al tipo que
        # rige para este ítem. Es la validación de verdad: la pantalla también
        # esconde las opciones, pero un valor enviado a mano tiene que morir
        # acá, no dibujarse distinto allá.
        self.fields["formato"].queryset = formatos_para(self._tipo_que_rige())

    def _tipo_que_rige(self):
        """El tipo del ítem o, si no lo declara, el de la cabecera.

        Se resuelve antes de validar porque de él depende qué formatos son
        aceptables, y eso hay que saberlo al armar el campo, no después.
        """
        propio = self.data.get(self.add_prefix("tipo")) if self.data else None
        elegido = propio or (self.cabecera.get("tipo").pk if self.cabecera.get("tipo") else None)
        return Tipo.objects.filter(pk=elegido).first() if elegido else None

    # -- resolución de lo que hereda de la cabecera ---------------------------

    @property
    def esta_desbloqueado(self):
        """El ítem declara su propia clasificación, aunque la cabecera exista."""
        return bool(self.data.get(self.add_prefix("desbloqueado")))

    def _resuelto(self, campo):
        """El valor que finalmente rige para este ítem.

        Con el ítem bloqueado manda la cabecera; desbloqueado, manda el ítem. En
        los campos que no son heredables la cabecera es solo un valor por
        defecto y el ítem siempre puede pisarla.
        """
        propio = self.cleaned_data.get(campo)
        heredado = self.cabecera.get(campo)
        if campo in self.CAMPOS_HEREDABLES and not self.esta_desbloqueado:
            return heredado or propio
        return propio or heredado

    def clean_titulo(self):
        # Los espacios de más son invisibles y convertirían "Akira" y "Akira "
        # en dos productos distintos para cualquiera que compare sin normalizar.
        return " ".join(self.cleaned_data["titulo"].split())

    def clean_isbn(self):
        """Se normaliza y se verifica el dígito de control antes de guardar.

        Un ISBN mal copiado no falla de forma ruidosa: pasa a identificar un
        producto que no existe, y el chequeo de duplicados deja de encontrar el
        que sí. El dígito verificador atrapa eso con aritmética, sin consultar
        nada externo (ver `apps/catalog/isbn.py`).
        """
        valor = isbn_util.normalizar(self.cleaned_data.get("isbn", ""))
        if not valor:
            return ""
        motivo = isbn_util.motivo_de_rechazo(valor)
        if motivo:
            raise forms.ValidationError(motivo)
        return valor

    def clean_portada(self):
        portada = self.cleaned_data.get("portada")
        if portada and portada.size > PORTADA_MAXIMA_BYTES:
            raise forms.ValidationError(
                f"La imagen pesa {portada.size // 1024 // 1024} MB y el máximo es "
                f"{PORTADA_MAXIMA_BYTES // 1024 // 1024} MB."
            )
        return portada

    def clean(self):
        datos = super().clean()

        editorial = self._resuelto("editorial")
        tipo = self._resuelto("tipo")
        formato = self._resuelto("formato")

        if not editorial:
            self.add_error("editorial", "Indique la editorial: la cabecera del lote no la declara.")
        if not tipo:
            self.add_error("tipo", "Indique el tipo: la cabecera del lote no lo declara.")

        formato = self._validar_formato(tipo, formato)

        fecha = self._resuelto("fecha_llegada")
        # Un ítem en Pre-venta sin fecha no se puede vigilar: el ciclo que los
        # transiciona busca justamente por fecha de llegada.
        if datos.get("estado") == Producto.PRE_VENTA and not fecha:
            self.add_error(
                "fecha_llegada",
                "Un ítem en Pre-venta necesita una fecha de llegada, propia o de la cabecera.",
            )

        datos["editorial_resuelta"] = editorial
        datos["tipo_resuelto"] = tipo
        datos["formato_resuelto"] = formato
        datos["fecha_llegada_resuelta"] = fecha
        return datos

    def _validar_formato(self, tipo, formato):
        """El formato depende del tipo, y el tipo lo dice con una bandera."""
        if tipo is None:
            return formato

        if not tipo.usa_formato:
            # No se rechaza: se descarta, porque el desplegable de la pantalla
            # lo esconde al cambiar de tipo y el valor puede haber quedado de la
            # selección anterior. Guardarlo sería registrar una clasificación
            # que el propio tipo declara inaplicable.
            return None

        if self.formato_obligatorio and not formato:
            self.add_error("formato", f"El formato es obligatorio para {tipo}.")
        return formato

    # -------------------------------------------------------------------------

    @property
    def esta_vacio(self):
        """Un ítem que nadie tocó. El formset lo saltea sin dar error.

        `desbloqueado` no cuenta: es una marca de la pantalla, no un dato del
        producto. Sin esta exclusión, desbloquear un ítem en blanco y no
        completarlo lo convertiría en un ítem a medio cargar que reclama todos
        los campos obligatorios.
        """
        return not [campo for campo in self.changed_data if campo != "desbloqueado"]

    def clave_de_duplicado(self):
        """La clave con la que se detecta un repetido dentro del mismo envío.

        Si el ítem declara ISBN alcanza con eso: identifica la edición y nada
        más, así que dos ítems con el mismo ISBN son el mismo tomo aunque les
        hayan escrito el título distinto. Sin ISBN se cae a la tupla completa.
        """
        if self.cleaned_data.get("isbn"):
            return ("isbn", self.cleaned_data["isbn"])

        formato = self.cleaned_data.get("formato_resuelto")
        return (
            self.cleaned_data["titulo"].casefold(),
            self.cleaned_data["volumen"],
            self.cleaned_data["tipo_resuelto"].pk,
            formato.pk if formato else None,
            self.cleaned_data["editorial_resuelta"].pk,
        )

    def estado_resultante(self):
        """Pre-venta si hay fecha de llegada; Activo si no.

        Lo automático es el valor por defecto, no una imposición: si el
        Administrador eligió un estado para este ítem, manda el suyo.
        """
        elegido = self.cleaned_data.get("estado")
        if elegido:
            return elegido
        if self.cleaned_data.get("fecha_llegada_resuelta"):
            return Producto.PRE_VENTA
        return Producto.ACTIVO

    def etiquetas_propias(self):
        """Las que este ítem suma a las del lote."""
        return list(self.cleaned_data.get("etiquetas") or [])

    def datos_del_producto(self):
        """Los campos del `Producto`, con todo ya resuelto. Lo consume el servicio.

        Las etiquetas **no** entran acá: son una relación de muchos a muchos y
        no se pueden asignar hasta que el producto exista. Las agrega el
        servicio, después de crearlo.
        """
        return {
            "titulo": self.cleaned_data["titulo"],
            "volumen": self.cleaned_data["volumen"],
            "isbn": self.cleaned_data.get("isbn", ""),
            "editorial": self.cleaned_data["editorial_resuelta"],
            "tipo": self.cleaned_data["tipo_resuelto"],
            "formato": self.cleaned_data["formato_resuelto"],
            "solo_adultos": self.cleaned_data.get("solo_adultos", False),
            "estado": self.estado_resultante(),
            "fecha_llegada": self.cleaned_data.get("fecha_llegada_resuelta"),
            # Sin declarar, cero: el sistema no inventa unidades que nadie contó.
            "stock": self.cleaned_data.get("stock") or 0,
            "autor": self.cleaned_data.get("autor", ""),
            "sinopsis": self.cleaned_data.get("sinopsis", ""),
            # Sin portada el ítem se registra igual y queda marcado como
            # "Imagen pendiente" (lo deriva `Producto.portada_pendiente`).
            "portada": self.cleaned_data.get("portada"),
        }


class ItemLoteNacionalForm(ItemLoteForm):
    """El precio se pre-completa desde la tabla de referencia y queda editable."""

    precio = _campo_importe(
        "Precio",
        required=False,
        ayuda="Vacío toma el precio de referencia de la editorial, el tipo y el formato.",
    )

    def clean(self):
        datos = super().clean()

        referencia = precio_de_referencia(
            datos.get("editorial_resuelta"),
            datos.get("tipo_resuelto"),
            datos.get("formato_resuelto"),
        )
        precio = datos.get("precio")

        # Que la combinación no esté en la tabla no bloquea el alta: solo
        # obliga a escribir el precio a mano.
        if precio is None and referencia is None:
            if datos.get("editorial_resuelta") and datos.get("tipo_resuelto"):
                self.add_error(
                    "precio",
                    "No hay precio de referencia para esa combinación: indíquelo a mano.",
                )
            return datos

        datos["precio_final"] = precio if precio is not None else referencia.pvp
        datos["referencia"] = referencia
        # Sobrescribir el precio pre-completado no lleva advertencia, pero sí
        # deja marcado el producto, para que un cambio de la tabla de precios no
        # le pise después una decisión tomada a mano.
        datos["precio_manual"] = bool(referencia) and datos["precio_final"] != referencia.pvp
        return datos

    def datos_del_producto(self):
        datos = super().datos_del_producto()
        datos.update(
            origen=Producto.NACIONAL,
            precio=self.cleaned_data["precio_final"],
            precio_manual=self.cleaned_data.get("precio_manual", False),
            precio_referencia=self.cleaned_data.get("referencia"),
        )
        return datos


class ItemLoteImportadoForm(ItemLoteForm):
    """El precio sale del costo en origen, el CRE del lote y el margen global."""

    # En un lote importado el precio no sale de ninguna tabla: el formato queda
    # como dato descriptivo y no traba el alta.
    formato_obligatorio = False

    costo_origen = _campo_importe(
        "Costo base en origen", ayuda="En la moneda declarada en la cabecera."
    )
    precio = _campo_importe("Precio final", required=False, ayuda="Vacío toma el precio calculado.")
    confirma_precio_manual = forms.BooleanField(
        label="Confirmo la edición del precio final", required=False
    )

    def __init__(self, *args, cre=None, margen=None, cotizacion=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.cre = cre if cre is not None else Decimal("0")
        self.margen = (
            margen if margen is not None else ConfiguracionSistema.obtener().margen_ganancia
        )
        self.cotizacion = cotizacion or precios.SIN_CONVERSION

    def clean(self):
        datos = super().clean()
        costo = datos.get("costo_origen")
        if costo is None:
            return datos

        costo_en_pesos, precio_base, precio_calculado = precios.desglose_importado(
            costo, self.cre, self.margen, self.cotizacion
        )
        precio_ingresado = datos.get("precio")
        editado = precio_ingresado is not None and precio_ingresado != precio_calculado

        # La advertencia se muestra y el Administrador confirma. El chequeo va
        # acá, del lado del servidor: un cartel de JavaScript esquivado no
        # debería poder romper el vínculo con el margen global.
        if editado and not datos.get("confirma_precio_manual"):
            self.add_error("precio", ADVERTENCIA_PRECIO_MANUAL)

        datos["costo_en_pesos"] = costo_en_pesos
        datos["precio_base"] = precio_base
        datos["precio_final"] = precio_ingresado if editado else precio_calculado
        datos["precio_manual"] = editado
        return datos

    def datos_del_producto(self):
        datos = super().datos_del_producto()
        datos.update(
            origen=Producto.IMPORTADO,
            costo_origen=self.cleaned_data["costo_origen"],
            # Se almacena siempre, incluso con el precio final editado a mano:
            # es lo que permite recalcular ante un cambio de margen sin volver a
            # pedir los datos del lote. Nunca se deriva del final.
            precio_base=self.cleaned_data["precio_base"],
            precio=self.cleaned_data["precio_final"],
            precio_manual=self.cleaned_data["precio_manual"],
        )
        return datos


class BaseItemFormSet(forms.BaseFormSet):
    """Saltea los ítems vacíos, exige al menos uno y caza los repetidos."""

    def items_cargados(self):
        return [form for form in self.forms if not form.esta_vacio]

    @property
    def hay_items_desbloqueados(self):
        """Si algún ítem se apartó de la clasificación de la cabecera.

        Cuando pasa, el lote deja de estar descrito por su cabecera y se
        registra como mixto: dejarle la cabecera puesta haría que el resumen y
        la auditoría dijeran algo que no es cierto para todos sus productos.
        """
        return any(form.esta_desbloqueado for form in self.items_cargados())

    def clean(self):
        super().clean()
        if self.total_error_count():
            return

        cargados = self.items_cargados()
        if not cargados:
            raise forms.ValidationError(MENSAJE_LOTE_VACIO)

        self._marcar_repetidos(cargados)

    def _marcar_repetidos(self, cargados):
        """Dos ítems idénticos dentro del mismo envío.

        El duplicado contra el catálogo ya cargado se resuelve al guardar, y es
        una exclusión esperada que no aborta el lote. Este otro es distinto: es
        un error de carga, todavía se puede arreglar sin perder nada, y si se
        dejara pasar el segundo ítem se rechazaría contra el primero recién
        después de guardar, cuando ya no hay nada que corregir en pantalla.
        """
        vistos = set()
        for form in cargados:
            clave = form.clave_de_duplicado()
            if clave in vistos:
                form.add_error("titulo", MENSAJE_REPETIDO_EN_LOTE)
            vistos.add(clave)

    def datos_de_los_productos(self, etiquetas_del_lote=()):
        """Los datos de cada ítem, con las etiquetas del lote ya sumadas.

        La unión se hace acá y no en cada formulario porque las del lote son un
        dato de la cabecera, y el ítem no tiene por qué conocerla. Se usa un
        conjunto para que declarar la misma etiqueta arriba y abajo no la
        duplique.
        """
        productos = []
        for form in self.items_cargados():
            datos = form.datos_del_producto()
            datos["etiquetas"] = sorted(
                {*etiquetas_del_lote, *form.etiquetas_propias()}, key=lambda e: e.pk
            )
            productos.append(datos)
        return productos


def formset_de_items(origen):
    """La clase de formset que corresponde al origen del lote."""
    formulario = ItemLoteImportadoForm if origen == LoteAlta.IMPORTADO else ItemLoteNacionalForm
    return forms.formset_factory(formulario, formset=BaseItemFormSet, extra=3)


class PrecioReferenciaForm(forms.ModelForm):
    """Una fila de la tabla de precios, para la pantalla de parámetros."""

    class Meta:
        model = TablaPrecioReferencia
        fields = ["editorial", "tipo", "formato", "pvp"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["editorial"].queryset = editoriales_activas()
        # Solo los tipos que se clasifican por formato pueden tener una fila:
        # los demás no tienen con qué completar la clave.
        self.fields["tipo"].queryset = tipos_activos().filter(usa_formato=True)
        self.fields["formato"].queryset = formatos_activos()
        self.fields["pvp"].widget.attrs.update({"step": "0.01", "inputmode": "decimal"})

    def clean(self):
        """Una fila para una combinación que no existe es una fila muerta.

        Un formato que no aplica al tipo elegido —una grapa de manga— no va a
        coincidir nunca con ningún producto, así que la fila queda ahí ocupando
        lugar y confundiendo a quien la lea. Se rechaza al cargarla, que es el
        único momento en que se puede corregir sin perder nada.
        """
        datos = super().clean()
        tipo, formato = datos.get("tipo"), datos.get("formato")
        if tipo and formato and not formato.aplica_a(tipo):
            self.add_error("formato", f"«{formato}» no se usa en {tipo}.")
        return datos

    def clean_pvp(self):
        pvp = self.cleaned_data["pvp"]
        if pvp > IMPORTE_MAXIMO:
            raise forms.ValidationError(f"El máximo es ${IMPORTE_MAXIMO}.")
        return pvp


class CatalogoNombradoForm(forms.ModelForm):
    """Base de los catálogos que se identifican por su nombre y nada más.

    La normalización no es cosmética: sin ella, en seis meses conviven "Ivrea",
    "ivrea " e "IVREA" como tres editoriales distintas, cada una con su tabla de
    precios, y los productos quedan repartidos entre las tres sin que ninguna
    consulta los junte. Con las etiquetas pasa lo mismo entre "Universo DC",
    "universo dc" y "DC".

    Está compartida y no copiada en cada formulario porque los dos catálogos se
    pueden crear desde dos lugares —la pantalla de parámetros y el atajo de la
    carga de un lote—: cuatro caminos de alta con la regla escrita cuatro veces
    es la forma más segura de que uno quede más laxo que los otros y se convierta
    en la puerta de entrada de los duplicados.
    """

    # Cada catálogo pone el suyo: el mensaje nombra al modelo y concuerda en
    # género, cosa que un texto genérico armado con `verbose_name` no hace.
    mensaje_repetido = "Ya existe un registro llamado «{nombre}»."

    def clean_nombre(self):
        nombre = " ".join(self.cleaned_data["nombre"].split())
        if len(nombre) < NOMBRE_MINIMO:
            raise forms.ValidationError(f"El nombre necesita al menos {NOMBRE_MINIMO} caracteres.")

        existente = (
            self._meta.model.objects.annotate(normalizado=Lower("nombre"))
            .filter(normalizado=nombre.casefold())
            .exclude(pk=self.instance.pk)
            .first()
        )
        if existente:
            raise forms.ValidationError(self.mensaje_repetido.format(nombre=existente.nombre))
        return nombre


class EditorialForm(CatalogoNombradoForm):
    """Alta de editorial, tanto desde parámetros como al vuelo desde un lote."""

    mensaje_repetido = "Ya existe una editorial llamada «{nombre}»."

    class Meta:
        model = Editorial
        fields = ["nombre", "activa"]


class GrupoEtiquetaForm(CatalogoNombradoForm):
    """El eje en el que describe una etiqueta: franquicia, género, colección."""

    mensaje_repetido = "Ya existe un grupo llamado «{nombre}»."

    class Meta:
        model = GrupoEtiqueta
        fields = ["nombre", "activo", "orden"]


class EtiquetaForm(forms.ModelForm):
    """Alta de etiqueta, tanto desde parámetros como al vuelo desde un lote.

    No hereda de `CatalogoNombradoForm` porque su unicidad no es global sino
    **por grupo**: "Terror" puede ser un género y también una colección, y son
    dos etiquetas distintas. La normalización del nombre sí es la misma.
    """

    class Meta:
        model = Etiqueta
        fields = ["nombre", "grupo", "activa"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["grupo"].queryset = GrupoEtiqueta.objects.filter(activo=True)

    def clean(self):
        datos = super().clean()
        nombre = " ".join((datos.get("nombre") or "").split())
        grupo = datos.get("grupo")
        if not nombre or grupo is None:
            return datos

        if len(nombre) < NOMBRE_MINIMO:
            self.add_error("nombre", f"El nombre necesita al menos {NOMBRE_MINIMO} caracteres.")
            return datos

        existente = (
            Etiqueta.objects.annotate(normalizado=Lower("nombre"))
            .filter(normalizado=nombre.casefold(), grupo=grupo)
            .exclude(pk=self.instance.pk)
            .first()
        )
        if existente:
            self.add_error(
                "nombre", f"«{grupo}» ya tiene una etiqueta llamada «{existente.nombre}»."
            )
        datos["nombre"] = nombre
        return datos


class TipoForm(forms.ModelForm):
    class Meta:
        model = Tipo
        fields = ["nombre", "usa_formato", "activo", "orden"]


class FormatoForm(forms.ModelForm):
    """El tamaño del tomo y en qué tipos se ofrece.

    Dejar los tipos sin declarar es la opción válida y frecuente: significa que
    el formato es universal. Es lo que hace que "Tapa dura" no haya que cargarla
    tres veces, una por rubro, partiendo la tabla de precios.
    """

    class Meta:
        model = Formato
        fields = ["nombre", "descripcion", "tipos", "activo", "orden"]
        widgets = {"tipos": forms.CheckboxSelectMultiple}  # noqa: RUF012

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["tipos"].queryset = tipos_activos()
        self.fields["tipos"].required = False


class ConfiguracionForm(forms.ModelForm):
    """Margen global y stock por defecto."""

    class Meta:
        model = ConfiguracionSistema
        fields = ["margen_ganancia", "stock_inicial_por_defecto"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["margen_ganancia"].widget.attrs.update(
            {"step": "0.01", "inputmode": "decimal", "min": "0", "max": "10"}
        )
        self.fields["stock_inicial_por_defecto"].widget.attrs.update(
            {"inputmode": "numeric", "min": "0", "max": str(STOCK_MAXIMO)}
        )

    def clean_margen_ganancia(self):
        margen = self.cleaned_data["margen_ganancia"]
        # Un margen de 10 es un 1000 %: casi siempre significa que alguien
        # escribió el porcentaje en vez de la proporción.
        if margen > 10:
            raise forms.ValidationError(
                "El margen se expresa como proporción, no como porcentaje: 0,40 es un 40 %."
            )
        return margen

    def clean_stock_inicial_por_defecto(self):
        stock = self.cleaned_data["stock_inicial_por_defecto"]
        if stock > STOCK_MAXIMO:
            raise forms.ValidationError(f"El máximo es {STOCK_MAXIMO}.")
        return stock
