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
from django.core.exceptions import NON_FIELD_ERRORS
from django.core.validators import MaxValueValidator, MinLengthValidator
from django.db import models
from django.db.models.functions import Lower
from django.utils import timezone

from apps.catalog import isbn as isbn_util
from apps.catalog import precios, services
from apps.catalog.models import (
    EDITORIAL,
    NO_EDITORIAL,
    BorradorProducto,
    Editorial,
    Etiqueta,
    Formato,
    GrupoEtiqueta,
    ImagenProducto,
    LoteAlta,
    Producto,
    ProductoEditorial,
    ProductoNoEditorial,
    TablaPrecioReferencia,
    Tipo,
)
from apps.catalog.services import precio_de_referencia
from apps.core import cotizaciones
from apps.core import imagenes as imagenes_util
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


def con_el_actual(consulta, actual):
    """Lo ofrecible más el valor que el registro ya tiene, aunque esté dado de baja.

    La baja de un catálogo conserva lo que ya lo usa (`CO-140`, `CO-045`). Si la
    edición ofreciera sólo lo activo, el valor actual no figuraría entre las
    opciones y guardar cualquier otro cambio lo perdería —o rechazaría el
    formulario— sin que nadie lo decidiera.
    """
    pks = [actual] if isinstance(actual, int) else [pk for pk in actual or [] if pk]
    if not pks:
        return consulta
    return consulta | consulta.model.objects.filter(pk__in=pks)


def _etiquetas_de(producto):
    if not producto.pk:
        return []
    return list(producto.etiquetas.values_list("pk", flat=True))


def formato_con_medidas(formato):
    """Cómo se ofrece un formato en un desplegable: con sus medidas.

    «B6» solo obliga a recordar qué tamaño era; «B6 · 12,8 × 18,2 cm» se elige
    mirando el tomo que se tiene en la mano.
    """
    return f"{formato.nombre} · {formato.descripcion}" if formato.descripcion else formato.nombre


def mostrar_medidas(campo):
    """Hace que un campo de formato (simple o múltiple) muestre las medidas."""
    campo.label_from_instance = formato_con_medidas
    return campo


def formatos_para(tipo):
    """Los formatos que aplican a un tipo.

    Un formato que aplica a todos los tipos entra siempre. Sin tipo elegido
    se ofrecen todos: esconder opciones antes de saber para qué son solo
    lograría que el campo parezca roto.
    """
    formatos = formatos_activos()
    if tipo is None:
        return formatos
    return formatos.filter(models.Q(aplica_a_todos=True) | models.Q(tipos=tipo)).distinct()


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
        # `inputmode` le pide al celular el teclado numérico y la hoja de estilo
        # lo usa además para alinear los importes a la derecha.
        widget=forms.NumberInput(attrs={"step": "0.01", "inputmode": "decimal"}),
    )


def _campo_etiquetas(etiqueta, ayuda):
    """El selector de etiquetas: se busca y se acumulan fichas.

    El widget es el `<select multiple>` nativo a propósito: la pantalla lo
    esconde y arma encima el buscador con fichas, pero el que viaja en el POST
    sigue siendo este. Sin JavaScript el campo sigue funcionando.

    Antes eran casillas agrupadas. Con cinco etiquetas se leían solas; con
    doscientas —que es a donde va un catálogo real— eran una pared que había que
    recorrer entera para encontrar una.
    """
    return forms.ModelMultipleChoiceField(
        label=etiqueta,
        queryset=Etiqueta.objects.none(),
        required=False,
        # `Etiqueta.__str__` da "Franquicia · Marvel", y de ahí sale el agrupado
        # de la lista: el guion lo parte en grupo y nombre sin que la vista
        # tenga que armar ninguna estructura aparte.
        widget=forms.SelectMultiple,
        help_text=ayuda,
    )


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
        mostrar_medidas(self.fields["formato"])
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
        mostrar_medidas(self.fields["formato"])

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
            # El campo del producto se llama `descripcion` desde la jerarquía:
            # en un tomo es la sinopsis y en una figura la descripción del
            # artículo. El formulario del alta editorial lo sigue etiquetando
            # "sinopsis", que es como lo llama quien lo carga.
            "descripcion": self.cleaned_data.get("sinopsis", ""),
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
        precio = self.cleaned_data["precio_final"]
        datos.update(
            origen=ProductoEditorial.NACIONAL,
            precio=precio,
            # En un nacional el precio **es** su base: no hay cadena de cálculo
            # que redondear, porque el PVP viene dado por la tabla de referencia
            # o escrito a mano. Se guarda igual para que valga en los dos rubros
            # la misma invariante —`precio` es el base redondeado— y para que
            # CU-PVP-MAR no tenga que preguntar de qué origen es antes de leerlo.
            precio_base=precio,
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
            origen=ProductoEditorial.IMPORTADO,
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


# El texto de la advertencia de duplicado. Va como constante porque lo usan el
# formulario y su test, y una advertencia que el test copia a mano deja de
# probar que el usuario ve lo que creemos que ve.
ADVERTENCIA_DUPLICADO = (
    "Ya existe «{producto}» con esta misma categoría. Si es un producto distinto "
    "—otra medida, otro proveedor, otra edición— confirmelo para continuar."
)

# El equivalente editorial, y a propósito **no** ofrece salida: la unicidad de una
# edición la sostiene la base, así que no hay confirmación que pueda dejarla
# pasar. El mensaje dice qué hacer en vez de invitar a reintentar.
CHOQUE_DE_EDICION = (
    "«{producto}» ya ocupa esta edición. Dos filas con el mismo título, volumen, "
    "tipo, formato y editorial son el mismo tomo: corrija los datos o edite el "
    "producto existente."
)


class VariasImagenesWidget(forms.ClearableFileInput):
    """Un `input[type=file]` que acepta varios archivos de una vez."""

    allow_multiple_selected = True


class CampoVariasImagenes(forms.FileField):
    """Cero o más archivos; devuelve siempre una lista."""

    widget = VariasImagenesWidget

    def clean(self, data, initial=None):
        if not data:
            return []
        archivos = data if isinstance(data, (list, tuple)) else [data]
        return [super(CampoVariasImagenes, self).clean(archivo, initial) for archivo in archivos]


class GaleriaFormMixin:
    """Las imágenes adicionales del producto (B-01-003), en el alta y la edición.

    Se procesan al validar (RNF-05): si una no cumple, el formulario entero no
    es válido y se dice cuál falló. Lo que llega a la vista ya es WebP.
    """

    def _armar_galeria(self):
        if self.instance.pk and self.instance.imagenes.exists():
            self.fields["quitar_imagenes"] = forms.ModelMultipleChoiceField(
                label="Quitar imágenes",
                queryset=self.instance.imagenes.all(),
                required=False,
                widget=forms.CheckboxSelectMultiple,
            )
        self.fields["imagenes_nuevas"] = CampoVariasImagenes(
            label="Imágenes adicionales",
            required=False,
            help_text=(
                f"Hasta {ImagenProducto.MAXIMO} además de la portada: contratapa, interior, "
                "detalles. JPG, PNG o WebP; se guardan en WebP."
            ),
        )
        self.fields["imagenes_nuevas"].widget.attrs["accept"] = "image/jpeg,image/png,image/webp"

    def clean_imagenes_nuevas(self):
        archivos = self.cleaned_data.get("imagenes_nuevas") or []
        existentes = self.instance.imagenes.count() if self.instance.pk else 0
        quitadas = len(self.cleaned_data.get("quitar_imagenes") or [])
        if existentes - quitadas + len(archivos) > ImagenProducto.MAXIMO:
            raise forms.ValidationError(
                f"Un producto admite hasta {ImagenProducto.MAXIMO} imágenes adicionales."
            )
        procesadas = []
        for archivo in archivos:
            try:
                procesadas.append(imagenes_util.procesar(archivo))
            except imagenes_util.ImagenInvalida as error:
                raise forms.ValidationError(f"«{archivo.name}»: {error}") from error
        return procesadas


class ProductoNoEditorialForm(GaleriaFormMixin, forms.ModelForm):
    """Alta de TCG, figura, merchandising o insumo (CU-CAT-ALT).

    **Es de a uno, no por lote**, a diferencia del alta editorial. No es una
    simplificación: el CU describe un alta singular, y tiene sentido — un lote
    editorial son veinte tomos de la misma serie que comparten editorial, tipo y
    precio, mientras que cinco artículos no editoriales no comparten nada.

    **El estado no se ofrece.** CU-CAT-ALT lo dice en sus comentarios: el sistema
    asigna exclusivamente Activo. La restricción vive en el modelo, que rechaza
    Pre-venta para este rubro; acá simplemente no hay campo que mandar.
    """

    # La mitad **de control** de la advertencia de duplicado. La consulta en vivo
    # de la pantalla es la mitad cómoda: avisa antes de que alguien escriba el
    # formulario entero. Pero el que decide es este campo, y lo exige el
    # servidor — es el mismo criterio de RNF-03 con el que se validan la
    # confirmación del precio manual y la del cambio de correo del proveedor: un
    # aviso de JavaScript esquivado no debería poder meter un duplicado.
    confirma_duplicado = forms.BooleanField(
        label="Es un producto distinto del que ya existe",
        required=False,
        help_text="Solo si el nombre y la categoría coinciden con un producto cargado.",
    )

    class Meta:
        model = ProductoNoEditorial
        fields = [
            "titulo",
            "tipo",
            "precio",
            "stock",
            "portada",
            "marca",
            "codigo",
            "codigo_barras",
            "descripcion",
            # Está en `Producto`, así que este rubro lo tiene igual que el otro.
            # Sin ofrecerlo, una figura para adultos no se podría excluir nunca
            # del catálogo público, que es lo único que este campo hace.
            "solo_adultos",
            "etiquetas",
        ]
        labels = {  # noqa: RUF012
            "titulo": "Nombre del producto",
            "tipo": "Categoría",
            "precio": "Precio de venta al público",
            "stock": "Stock inicial",
            "portada": "Imagen referencial",
            "codigo": "Código de producto interno",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._armar_galeria()

        # Solo categorías del rubro, y solo activas. El recorte del desplegable
        # es comodidad; la validación de verdad la hace el modelo en su `clean`,
        # con el mismo criterio de A20 — un valor enviado a mano no es más
        # confiable por venir de esta pantalla.
        self.fields["tipo"].queryset = con_el_actual(
            Tipo.objects.filter(activo=True, clase=NO_EDITORIAL), self.instance.tipo_id
        ).order_by("nombre")
        self.fields["tipo"].empty_label = "Elegir categoría"

        # El widget primero y el queryset después: asignar el queryset es lo que
        # carga las opciones en el widget. Al revés, el widget nuevo queda sin
        # ninguna y el selector dice que «ya están todas elegidas».
        self.fields["etiquetas"].widget = forms.SelectMultiple()
        self.fields["etiquetas"].queryset = con_el_actual(
            etiquetas_activas(), _etiquetas_de(self.instance)
        )

        # Los cuatro obligatorios de CU-CAT-ALT paso 2, menos la imagen: no bloquea el
        # alta en ninguno de los dos rubros (A5 de `alta_editorial.md`, unificado
        # en la decisión 3 de este módulo).
        for nombre in ("titulo", "tipo", "precio", "stock"):
            self.fields[nombre].required = True
        self.fields["portada"].required = False

        self.fields["titulo"].validators.append(MinLengthValidator(TITULO_MINIMO))
        self.fields["stock"].validators.append(MaxValueValidator(STOCK_MAXIMO))
        self.fields["codigo"].help_text = (
            "Opcional: si se deja vacío, el sistema genera uno y no se repite nunca."
        )

        # Editando (CU-CAT-EDI) el código no se ofrece. Es la identidad del producto y
        # el modelo la declara inmutable; un campo editable que el `save()` va a
        # ignorar es peor que no tenerlo, porque promete un cambio que no ocurre.
        #
        # Y el stock deja de llamarse "inicial": en el alta describe con cuántas
        # unidades nace el producto, y editando eso ya pasó.
        if self.instance.pk:
            del self.fields["codigo"]
            self.fields["stock"].label = "Stock"

    def clean_titulo(self):
        # Sin normalizar, "Llavero  Naruto" y "Llavero Naruto" serían dos
        # productos distintos para cualquiera que compare sin hacerlo — y la
        # búsqueda de duplicados es una de esas.
        return " ".join((self.cleaned_data.get("titulo") or "").split())

    def clean_precio(self):
        precio = self.cleaned_data.get("precio")
        if precio is not None and precio > IMPORTE_MAXIMO:
            raise forms.ValidationError(f"El máximo es ${IMPORTE_MAXIMO}.")
        return precio

    def clean(self):
        datos = super().clean()

        # El duplicado **no bloquea**: pide una confirmación explícita
        # (corrección 21). Con el choque a la vista y la casilla marcada, el alta
        # sigue — porque dos artículos con el mismo nombre y la misma categoría
        # pueden ser dos productos de verdad.
        self.duplicado = services.buscar_duplicado_no_editorial(
            datos.get("titulo", ""), datos.get("tipo"), excluir=self.instance.pk
        )
        if self.duplicado and not datos.get("confirma_duplicado"):
            self.add_error(
                "titulo",
                ADVERTENCIA_DUPLICADO.format(producto=self.duplicado),
            )
        return datos


class ProductoEditorialForm(GaleriaFormMixin, forms.ModelForm):
    """Edición de un tomo ya cargado (CU-CAT-EDI).

    **No existe un alta editorial de a uno**: el material editorial entra por
    lote, porque veinte tomos de una serie comparten editorial, tipo y formato.
    Este formulario es solo para editar, y por eso no hereda del formulario de
    ítem del lote: aquel trabaja sobre datos sueltos que después arman el
    producto, y este trabaja sobre el producto que ya existe.

    **Qué no se ofrece, y por qué:**

    - `codigo` — es la identidad y el modelo la declara inmutable.
    - `estado` — el ciclo de vida lo gobiernan los CU que lo mueven. Ofrecerlo
      acá permitiría descatalogar un producto sin pasar por el informe de
      impacto de CU-CAT-BAJ, que es justamente para lo que ese informe existe.
    - `origen`, `lote`, `precio_base`, `costo_origen` — describen de dónde vino
      el producto y con qué aritmética se le fijó el precio. Son la historia del
      lote, no datos del tomo: cambiarlos acá haría que el resumen del lote
      dejara de coincidir con sus propios productos.
    - `demorado`, `fecha_estimada`, `nota_demora` — son de CU-ALT-DEM, que está
      bloqueado por Pedidos.
    """

    confirma_precio_manual = forms.BooleanField(
        label="Confirmo la edición del precio", required=False
    )

    class Meta:
        model = ProductoEditorial
        fields = [
            "titulo",
            "volumen",
            "isbn",
            "editorial",
            "tipo",
            "formato",
            "precio",
            "stock",
            "fecha_llegada",
            "autor",
            "portada",
            "descripcion",
            "codigo_barras",
            "solo_adultos",
            "etiquetas",
        ]
        labels = {  # noqa: RUF012
            "titulo": "Título",
            "tipo": "Tipo de material",
            "precio": "Precio de venta al público",
            "portada": "Portada",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._armar_galeria()

        # Lo activo más lo que el producto ya tiene: la baja de un catálogo
        # conserva lo que ya lo usa, y editar otro dato no debe perderlo.
        producto = self.instance
        self.fields["editorial"].queryset = con_el_actual(
            editoriales_activas(), producto.editorial_id
        )
        self.fields["tipo"].queryset = con_el_actual(
            tipos_activos().filter(clase=EDITORIAL), producto.tipo_id
        )
        self.fields["formato"].queryset = con_el_actual(formatos_activos(), producto.formato_id)
        mostrar_medidas(self.fields["formato"])
        # El widget antes que el queryset, que es el que le carga las opciones.
        self.fields["etiquetas"].widget = forms.SelectMultiple()
        self.fields["etiquetas"].queryset = con_el_actual(
            etiquetas_activas(), _etiquetas_de(producto)
        )

        self.fields["isbn"].required = False
        self.fields["portada"].required = False
        self.fields["formato"].required = False

        self.fields["titulo"].validators.append(MinLengthValidator(TITULO_MINIMO))
        self.fields["volumen"].validators.append(MaxValueValidator(VOLUMEN_MAXIMO))
        self.fields["stock"].validators.append(MaxValueValidator(STOCK_MAXIMO))

        # De qué precio se parte para decidir si lo editaron. Se guarda antes de
        # que el formulario toque nada: comparar contra `self.instance` después
        # de `_post_clean` compararía el valor nuevo consigo mismo.
        self.precio_original = self.instance.precio
        self.era_manual = self.instance.precio_manual

    def clean_titulo(self):
        return " ".join((self.cleaned_data.get("titulo") or "").split())

    def clean_isbn(self):
        """Se verifica la aritmética del dígito de control, no una API.

        Un dígito mal copiado no falla de forma ruidosa: pasa a identificar algo
        que no existe, y como el ISBN es el criterio primario de duplicados, uno
        inválido deja de encontrar el tomo que ya está cargado.
        """
        valor = isbn_util.normalizar(self.cleaned_data.get("isbn") or "")
        if not valor:
            return ""
        motivo = isbn_util.motivo_de_rechazo(valor)
        if motivo:
            raise forms.ValidationError(motivo)
        return valor

    def clean_precio(self):
        precio = self.cleaned_data.get("precio")
        if precio is not None and precio > IMPORTE_MAXIMO:
            raise forms.ValidationError(f"El máximo es ${IMPORTE_MAXIMO}.")
        return precio

    def clean(self):
        datos = super().clean()

        # **Acá el duplicado bloquea y no se puede confirmar**, al revés que en
        # el rubro no editorial. No es una decisión de este formulario: la base
        # tiene `producto_editorial_unico_por_clave` y
        # `producto_editorial_unico_por_isbn`, así que la fila no entra de
        # ninguna manera. Ofrecer una casilla de confirmación sería prometer una
        # salida que termina en un error de integridad.
        #
        # Que las dos políticas sean opuestas es correcto y está razonado en el
        # A4 del módulo: dos llaveros de Naruto pueden ser dos productos
        # distintos, pero dos filas con el mismo ISBN son la misma edición
        # cargada dos veces.
        self.duplicado = services.buscar_duplicado(
            datos.get("titulo", ""),
            datos.get("volumen"),
            datos.get("tipo"),
            datos.get("formato"),
            datos.get("editorial"),
            isbn=datos.get("isbn", ""),
            excluir=self.instance.pk,
        )
        if self.duplicado:
            self.add_error("titulo", CHOQUE_DE_EDICION.format(producto=self.duplicado))

        self._revisar_precio(datos)
        return datos

    def _revisar_precio(self, datos):
        """A1 de CU-CAT-EDI — editar el precio a mano rompe el vínculo automático.

        La regla se expresa sobre el estado del producto y no sobre de dónde
        vino el precio, que es lo que la vuelve una sola regla para los dos
        orígenes: un nacional está atado a la tabla de referencia y un importado
        al margen global, pero **los dos dejan de estarlo por la misma razón**.

        Si el producto ya tenía el precio fijado a mano no hay vínculo que
        romper, y volver a pedir la confirmación sería un trámite que enseña a
        tildar sin leer.
        """
        precio = datos.get("precio")
        if precio is None or self.era_manual or precio == self.precio_original:
            return

        if not datos.get("confirma_precio_manual"):
            self.add_error("precio", ADVERTENCIA_PRECIO_MANUAL)
        datos["precio_manual"] = True

    def save(self, commit=True):
        producto = super().save(commit=False)
        if self.cleaned_data.get("precio_manual"):
            producto.precio_manual = True
        if commit:
            producto.save()
            self.save_m2m()
        return producto


class PrecioReferenciaForm(forms.ModelForm):
    """`CO-049`: el alta de una combinación de la tabla de precios.

    Ofrece sólo lo que puede formar una combinación posible (paso 2 de
    `CU-PVP-TBA`): editoriales, tipos y formatos activos; como tipo, los del
    rubro editorial que se clasifican por formato. La combinación es la
    identidad de la fila y no se modifica: el precio se cambia con
    `PrecioModificacionForm`.
    """

    INCOMPATIBLE = "No está activa o no puede formar parte de una combinación de la tabla."

    class Meta:
        model = TablaPrecioReferencia
        fields = ["editorial", "tipo", "formato", "pvp"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # La fila existente con la misma combinación (E1), para enlazarla.
        self.colision = None
        self.fields["editorial"].queryset = editoriales_activas()
        self.fields["tipo"].queryset = tipos_activos().filter(clase=EDITORIAL, usa_formato=True)
        self.fields["formato"].queryset = formatos_activos()
        mostrar_medidas(self.fields["formato"])
        for nombre in ("editorial", "tipo", "formato"):
            self.fields[nombre].error_messages["invalid_choice"] = self.INCOMPATIBLE
        self.fields["pvp"].widget.attrs.update({"step": "0.01", "inputmode": "decimal"})

    def clean(self):
        """E1 y E2 de `CU-PVP-TBA`.

        Una fila para una combinación imposible es una fila muerta: un formato
        que no aplica al tipo no va a coincidir nunca con ningún producto. Se
        rechaza al cargarla, que es el único momento en que se puede corregir
        sin perder nada.
        """
        datos = super().clean()
        editorial, tipo, formato = datos.get("editorial"), datos.get("tipo"), datos.get("formato")
        if tipo and formato and not formato.aplica_a(tipo):
            self.add_error("formato", f"«{formato}» no se ofrece en {tipo}.")
        if editorial and tipo and formato:
            self.colision = TablaPrecioReferencia.objects.filter(
                editorial=editorial, tipo=tipo, formato=formato
            ).first()
            if self.colision:
                raise forms.ValidationError(
                    "La combinación ya está en la tabla. Para cambiar su precio, modifíquela."
                )
        return datos

    def validate_unique(self):
        # La colisión ya se informó con su enlace; la restricción de la base
        # repetiría el mismo error con un texto genérico.
        if self.colision is None:
            super().validate_unique()

    def clean_pvp(self):
        pvp = self.cleaned_data["pvp"]
        if pvp > IMPORTE_MAXIMO:
            raise forms.ValidationError(f"El máximo es ${IMPORTE_MAXIMO}.")
        return pvp


class PrecioModificacionForm(forms.Form):
    """`CO-047`: el precio nuevo de una combinación, mayor que cero (I-09)."""

    pvp = forms.DecimalField(
        label="Precio de venta al público nuevo",
        max_digits=12,
        decimal_places=2,
        min_value=Decimal("0.01"),
        max_value=IMPORTE_MAXIMO,
        widget=forms.NumberInput(attrs={"step": "0.01", "inputmode": "decimal"}),
        error_messages={"min_value": "El precio tiene que ser mayor que cero."},
    )


class MargenForm(forms.Form):
    """`CU-PVP-MAR`: el margen nuevo, escrito como porcentaje (`CO-167`).

    Se guarda como proporción con cuatro decimales (0,4250), así que el
    porcentaje admite dos (42,50 %). La conversión es exacta: es dividir un
    `Decimal` por cien.
    """

    MAXIMO_PORCENTAJE = Decimal("1000")

    margen = forms.DecimalField(
        label="Margen nuevo (%)",
        max_digits=6,
        decimal_places=2,
        min_value=Decimal("0"),
        max_value=MAXIMO_PORCENTAJE,
        widget=forms.NumberInput(attrs={"step": "0.01", "inputmode": "decimal"}),
        help_text="Sobre el precio base. 40 es un 40 %: el precio final es 1,40 veces el base.",
    )

    def proporcion(self):
        return self.cleaned_data["margen"] / Decimal("100")


class CatalogoNombradoForm(forms.ModelForm):
    """Base de los catálogos que se identifican por su nombre.

    La normalización no es cosmética: sin ella, en seis meses conviven "Ivrea",
    "ivrea " e "IVREA" como tres editoriales distintas, cada una con su tabla de
    precios, y los productos quedan repartidos entre las tres sin que ninguna
    consulta los junte. Con las etiquetas pasa lo mismo entre "Universo DC",
    "universo dc" y "DC".

    Está compartida y no copiada en cada formulario porque los catálogos se
    pueden crear desde dos lugares —su propia pantalla y el atajo de la carga de
    un lote—: varios caminos de alta con la regla escrita varias veces es la
    forma más segura de que uno quede más laxo y se convierta en la puerta de
    entrada de los duplicados.

    **El estado no es un campo del formulario.** El alta nace activa, la
    modificación sólo reactiva y la baja es un par con informe (R-17-002). La
    casilla `reactivar` aparece sólo en lo que está dado de baja.
    """

    # Cada catálogo pone el suyo: el mensaje nombra al modelo y concuerda en
    # género, cosa que un texto genérico armado con `verbose_name` no hace.
    mensaje_repetido = "Ya existe un registro llamado «{nombre}»."
    campo_estado = "activo"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # La entrada existente con la que choca el nombre, para que la pantalla
        # la enlace con su estado (E1 de cada alta).
        self.colision = None
        if self.esta_dado_de_baja:
            self.fields["reactivar"] = forms.BooleanField(
                label="Reactivar",
                required=False,
                help_text="Vuelve a ofrecerse en los formularios.",
            )

    @property
    def esta_dado_de_baja(self):
        return bool(self.instance.pk) and not getattr(self.instance, self.campo_estado)

    def _normalizar(self, nombre):
        nombre = " ".join(nombre.split())
        if len(nombre) < NOMBRE_MINIMO:
            raise forms.ValidationError(f"El nombre necesita al menos {NOMBRE_MINIMO} caracteres.")
        return nombre

    def clean_nombre(self):
        nombre = self._normalizar(self.cleaned_data["nombre"])
        existente = (
            self._meta.model.objects.annotate(normalizado=Lower("nombre"))
            .filter(normalizado=nombre.casefold())
            .exclude(pk=self.instance.pk)
            .first()
        )
        if existente:
            self.colision = existente
            raise forms.ValidationError(self.mensaje_repetido.format(nombre=existente.nombre))
        return nombre

    def _post_clean(self):
        """El duplicado que aparece entre `clean_nombre` y la validación del modelo.

        Si otro envío del mismo nombre se guardó en ese instante (un doble clic),
        la restricción de unicidad del modelo lo detecta con un error general y el
        nombre técnico de la restricción. Se cambia por el aviso de siempre, con su
        enlace al registro existente (B-17-016).
        """
        super()._post_clean()
        nombre = self.cleaned_data.get("nombre")
        if not nombre or NON_FIELD_ERRORS not in self._errors:
            return
        existente = (
            self._meta.model.objects.annotate(normalizado=Lower("nombre"))
            .filter(normalizado=nombre.casefold())
            .exclude(pk=self.instance.pk)
            .first()
        )
        if existente is not None:
            del self._errors[NON_FIELD_ERRORS]
            self.colision = existente
            self.add_error("nombre", self.mensaje_repetido.format(nombre=existente.nombre))


class EditorialForm(CatalogoNombradoForm):
    """Alta y modificación de editorial (`CO-137`, `CO-138`), también al vuelo."""

    mensaje_repetido = "Ya existe una editorial llamada «{nombre}»."
    campo_estado = "activa"

    class Meta:
        model = Editorial
        fields = ["nombre"]


class GrupoEtiquetaForm(CatalogoNombradoForm):
    """El eje en el que describe una etiqueta (`CO-038`, `CO-039`)."""

    mensaje_repetido = "Ya existe un grupo llamado «{nombre}»."

    class Meta:
        model = GrupoEtiqueta
        fields = ["nombre"]


class EtiquetaForm(CatalogoNombradoForm):
    """Alta y modificación de etiqueta (`CO-042`, `CO-043`).

    Su unicidad no es global sino **por grupo** (I-08): "Terror" puede ser un
    género y también una colección. Por eso el chequeo de repetidos corre en
    `clean()`, cuando ya se sabe en qué grupo queda.
    """

    campo_estado = "activa"

    class Meta:
        model = Etiqueta
        fields = ["nombre", "grupo"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # El destino tiene que estar activo (`CO-043`). El grupo actual se
        # ofrece igual aunque esté dado de baja: si no, corregir el nombre de
        # una etiqueta de un grupo inactivo obligaría a moverla.
        activos = models.Q(activo=True)
        if self.instance.pk:
            activos |= models.Q(pk=self.instance.grupo_id)
        self.fields["grupo"].queryset = GrupoEtiqueta.objects.filter(activos)

    def clean_nombre(self):
        return self._normalizar(self.cleaned_data["nombre"])

    def clean(self):
        datos = super().clean()
        nombre, grupo = datos.get("nombre"), datos.get("grupo")
        if not nombre or grupo is None:
            return datos

        existente = (
            Etiqueta.objects.annotate(normalizado=Lower("nombre"))
            .filter(normalizado=nombre.casefold(), grupo=grupo)
            .exclude(pk=self.instance.pk)
            .first()
        )
        if existente:
            self.colision = existente
            self.add_error(
                "nombre", f"«{grupo}» ya tiene una etiqueta llamada «{existente.nombre}»."
            )

        # E3: una etiqueta no vuelve a ofrecerse dentro de un grupo que no se
        # ofrece.
        if datos.get("reactivar") and not grupo.activo:
            self.add_error(
                "reactivar",
                f"El grupo «{grupo}» está dado de baja. Reactívelo primero, o mueva la "
                "etiqueta a un grupo activo.",
            )
        return datos


def combinaciones_en_uso(tipo=None, formato=None):
    """Cuántos productos y filas de precio usan una combinación de tipo y formato.

    Es la regla que comparten `CO-142` E4, `CO-145` E3 y `CO-146` E5: el formato
    forma parte de la clave de unicidad del producto (I-04) y de la terna de
    precios (I-07), así que ninguna modificación puede dejar sin declarar una
    combinación que algo ya usa.
    """
    productos = ProductoEditorial.objects.filter(formato__isnull=False)
    filas = TablaPrecioReferencia.objects.all()
    if tipo is not None:
        productos, filas = productos.filter(tipo=tipo), filas.filter(tipo=tipo)
    if formato is not None:
        productos, filas = productos.filter(formato=formato), filas.filter(formato=formato)
    return productos.count(), filas.count()


def _que_la_usa(productos, filas):
    partes = []
    if productos:
        partes.append(f"{productos} producto" + ("s" if productos != 1 else ""))
    if filas:
        partes.append(f"{filas} fila" + ("s" if filas != 1 else "") + " de precio")
    return " y ".join(partes)


class TipoForm(CatalogoNombradoForm):
    """Alta y modificación de tipo de material (`CO-141`, `CO-142`), con la
    declaración de sus formatos (`CO-146`).

    Se identifica por su nombre como el resto de los catálogos. Acá importa más
    que en ningún otro: `Tipo` entra en la clave de unicidad del producto **y**
    en la tabla de precios de referencia.

    Los formatos no son un campo del modelo —la relación la declara `Formato`—
    así que se guardan aparte, con `formatos_elegidos()`, y se auditan como su
    propia operación.
    """

    mensaje_repetido = "Ya existe un tipo llamado «{nombre}»."

    formatos = forms.ModelMultipleChoiceField(
        label="Formatos que se ofrecen en este tipo",
        queryset=Formato.objects.none(),
        required=False,
        widget=forms.CheckboxSelectMultiple,
        help_text="Los formatos que aplican a todos los tipos no se declaran acá.",
    )

    class Meta:
        model = Tipo
        fields = ["nombre", "clase", "usa_formato"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # A2 de `TPA` y `TPM`: sólo los activos que no aplican a todos.
        self.fields["formatos"].queryset = Formato.objects.filter(activo=True, aplica_a_todos=False)
        mostrar_medidas(self.fields["formatos"])
        if self.instance.pk:
            self.fields["formatos"].initial = list(
                self.instance.formatos.filter(aplica_a_todos=False).values_list("pk", flat=True)
            )

    def _guardado(self):
        """Lo que la base tiene hoy: `is_valid()` ya pisó la instancia."""
        if not self.instance.pk:
            return None
        return Tipo.objects.get(pk=self.instance.pk)

    def _conservados(self):
        """Los formatos declarados que el formulario no ofrece: los dados de baja.

        No se quitan por no aparecer en la lista. Quitarlos sería romper una
        asociación que nadie eligió romper.
        """
        if not self.instance.pk:
            return []
        return list(
            self.instance.formatos.exclude(pk__in=self.fields["formatos"].queryset.values("pk"))
        )

    def formatos_elegidos(self):
        """La lista final de formatos del tipo, ya validada.

        Un tipo que no se clasifica por formato no declara ninguno: si dejó de
        clasificarse, sus formatos se desvinculan (`CO-142`).
        """
        if not self.cleaned_data.get("usa_formato"):
            return []
        return [*self.cleaned_data.get("formatos", []), *self._conservados()]

    def clean(self):
        datos = super().clean()
        guardado = self._guardado()
        if guardado is None:
            return datos

        # E2: el rubro decide la especialización del producto (PD-03).
        clase = datos.get("clase")
        if clase and clase != guardado.clase and guardado.productos.exists():
            self.add_error(
                "clase",
                f"«{guardado}» tiene {guardado.productos.count()} productos: el rubro decide "
                "de qué clase es cada uno y no puede cambiar.",
            )

        # E4: dejar de clasificarse por formato con combinaciones en uso.
        if guardado.usa_formato and not datos.get("usa_formato"):
            productos, filas = combinaciones_en_uso(tipo=guardado)
            if productos or filas:
                self.add_error(
                    "usa_formato",
                    f"No puede dejar de clasificarse por formato: hay {productos} productos "
                    f"con formato asignado y {filas} filas de precio que lo combinan con un "
                    "formato.",
                )
            return datos

        # E5: quitar de la lista un formato cuya combinación está en uso.
        if datos.get("usa_formato"):
            elegidos = {formato.pk for formato in datos.get("formatos", [])}
            quitados = guardado.formatos.filter(aplica_a_todos=False, activo=True).exclude(
                pk__in=elegidos
            )
            en_uso = []
            for formato in quitados:
                usado = _que_la_usa(*combinaciones_en_uso(tipo=guardado, formato=formato))
                if usado:
                    en_uso.append(f"«{formato}» ({usado})")
            if en_uso:
                self.add_error(
                    "formatos",
                    "No se pueden quitar formatos en uso: " + ", ".join(en_uso) + ".",
                )
        return datos


class FormatoForm(CatalogoNombradoForm):
    """Alta y modificación de formato (`CO-144`, `CO-145`).

    «Aplica a todos los tipos» es un atributo y se elige (B-17-004). Al pasar a
    sí, los tipos declarados se desvinculan: dejan de decir algo (A2 de `FMM`).
    """

    mensaje_repetido = "Ya existe un formato llamado «{nombre}»."

    class Meta:
        model = Formato
        fields = ["nombre", "descripcion", "aplica_a_todos", "tipos"]
        widgets = {"tipos": forms.CheckboxSelectMultiple}  # noqa: RUF012

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Los declarables: activos y que se clasifican por formato (`CO-144`).
        self.fields["tipos"].queryset = tipos_activos().filter(usa_formato=True)
        self.fields["tipos"].required = False

    def _conservados(self):
        """Los tipos declarados que no se ofrecen, por estar dados de baja."""
        if not self.instance.pk:
            return []
        return list(
            Formato.objects.get(pk=self.instance.pk).tipos.exclude(
                pk__in=self.fields["tipos"].queryset.values("pk")
            )
        )

    def clean(self):
        datos = super().clean()
        if datos.get("aplica_a_todos"):
            datos["tipos"] = []
            return datos

        elegidos = [*datos.get("tipos", []), *self._conservados()]
        datos["tipos"] = elegidos

        # E3: ningún tipo cuya combinación con el formato está en uso queda
        # sin declarar.
        if self.instance.pk:
            declarados = {tipo.pk for tipo in elegidos}
            usados = Tipo.objects.filter(
                models.Q(productos__productoeditorial__formato=self.instance)
                | models.Q(precios_de_referencia__formato=self.instance)
            ).distinct()
            faltan = []
            for tipo in usados.exclude(pk__in=declarados):
                usado = _que_la_usa(*combinaciones_en_uso(tipo=tipo, formato=self.instance))
                faltan.append(f"{tipo} ({usado})")
            if faltan:
                self.add_error(
                    "tipos",
                    "Estos tipos usan el formato y tienen que seguir declarados: "
                    + ", ".join(faltan)
                    + ".",
                )
        return datos


class ModeloDeLenguajeForm(forms.ModelForm):
    """A qué modelo de lenguaje le habla el sistema (CU-ALT-NOV, A16).

    Está separado de `ConfiguracionForm` y no es solo prolijidad de pantalla:
    son dos cosas que se tocan por motivos distintos. El margen y el stock los
    cambia el negocio; esto lo cambia quien despliega, y una de sus dos mitades
    es una **credencial**.

    **La clave se escribe pero no se lee.** El campo llega siempre vacío y solo
    reemplaza a la guardada cuando se escribe algo: así la pantalla deja de ser
    un lugar del que copiar el secreto, y dejarla en blanco al editar cualquier
    otro parámetro no la borra sin querer.
    """

    api_key = forms.CharField(
        label="Clave de la API",
        required=False,
        widget=forms.PasswordInput(render_value=False, attrs={"autocomplete": "off"}),
        help_text="No se vuelve a mostrar una vez guardada.",
    )

    class Meta:
        model = ConfiguracionSistema
        fields = ["llm_modo", "llm_url", "llm_modelo", "llm_timeout", "llm_temperatura"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["llm_timeout"].widget.attrs.update(
            {"inputmode": "numeric", "min": "5", "max": "900"}
        )
        self.fields["llm_temperatura"].widget.attrs.update(
            {"step": "0.1", "inputmode": "decimal", "min": "0", "max": "2"}
        )
        if self.instance and self.instance.llm_api_key:
            self.fields["api_key"].help_text = (
                f"Hay una clave guardada ({self.instance.clave_enmascarada}). "
                "Escriba una nueva solo si quiere reemplazarla."
            )

    def clean_llm_url(self):
        """La dirección tiene que ser la de **chat**, no la base del servidor.

        Pegar `http://127.0.0.1:1234` o `https://proveedor/api` es el error más
        natural que hay acá, y el formulario lo aceptaba: quedaba una
        configuración que no puede funcionar y el diagnóstico decía "no parece
        una API compatible con la de OpenAI", que es verdad pero no dice qué
        corregir. Se avisa donde se puede arreglar.

        Se exige `/v1/` porque es la parte de la convención que los dos modos
        comparten, y es de donde se deduce la dirección del catálogo de modelos.
        """
        url = (self.cleaned_data.get("llm_url") or "").strip().rstrip("/")
        if "/v1/" not in f"{url}/":
            raise forms.ValidationError(
                "Falta la ruta de la API. Tiene que terminar en algo como "
                "«/v1/chat/completions», no ser solo la dirección del servidor."
            )
        return url

    def clean(self):
        datos = super().clean()

        # Un proveedor remoto sin clave no va a contestar nunca, y el fallo
        # aparecería recién en la pantalla de diagnóstico como un rechazo. Se
        # avisa acá, que es donde se puede arreglar.
        sin_clave = not (datos.get("api_key") or self.instance.llm_api_key)
        if datos.get("llm_modo") == ConfiguracionSistema.REMOTO and sin_clave:
            self.add_error("api_key", "Un proveedor remoto necesita una clave de API.")

        # El modelo tampoco es opcional en remoto: los proveedores hospedan
        # cientos y sin nombrarlo devuelven un error que cuesta interpretar.
        if datos.get("llm_modo") == ConfiguracionSistema.REMOTO and not datos.get("llm_modelo"):
            self.add_error("llm_modelo", "Un proveedor remoto necesita que se nombre el modelo.")

        temperatura = datos.get("llm_temperatura")
        if temperatura is not None and temperatura > 2:
            self.add_error("llm_temperatura", "El máximo razonable es 2.")
        return datos

    def save(self, commit=True):
        configuracion = super().save(commit=False)
        # Solo se pisa si se escribió una nueva: el campo llega vacío siempre.
        nueva = self.cleaned_data.get("api_key")
        if nueva:
            configuracion.llm_api_key = nueva
        if commit:
            configuracion.save()
        return configuracion


class ConfiguracionForm(forms.ModelForm):
    """El stock por defecto de los borradores y el intervalo del carrusel.

    El margen global ya no está acá: cambiarlo propaga precios y tiene su
    propia pantalla con simulación y confirmación (`CU-CFG-PAR` A1, `CU-PVP-MAR`).
    """

    class Meta:
        model = ConfiguracionSistema
        fields = [
            "stock_inicial_por_defecto",
            "intervalo_carrusel",
            "dias_aviso_preventa",
            "cantidad_minima_restock",
            "margen_stock_restock",
            "frecuencia_casilla_horas",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["stock_inicial_por_defecto"].widget.attrs.update(
            {"inputmode": "numeric", "min": "0", "max": str(STOCK_MAXIMO)}
        )
        self.fields["intervalo_carrusel"].widget.attrs.update({"inputmode": "numeric", "min": "1"})
        self.fields["dias_aviso_preventa"].widget.attrs.update({"inputmode": "numeric", "min": "0"})
        self.fields["cantidad_minima_restock"].widget.attrs.update(
            {"inputmode": "numeric", "min": "1"}
        )
        self.fields["margen_stock_restock"].widget.attrs.update(
            {"inputmode": "numeric", "min": "0"}
        )
        self.fields["frecuencia_casilla_horas"].widget.attrs.update(
            {"inputmode": "numeric", "min": "1"}
        )

    def clean_stock_inicial_por_defecto(self):
        stock = self.cleaned_data["stock_inicial_por_defecto"]
        if stock > STOCK_MAXIMO:
            raise forms.ValidationError(f"El máximo es {STOCK_MAXIMO}.")
        return stock


class SeguridadForm(forms.ModelForm):
    """La sección Seguridad de `CU-CFG-PAR` (B-12-001, plan 00, A3)."""

    class Meta:
        model = ConfiguracionSistema
        fields = ["expiracion_sesion_minutos", "bloqueo_intentos_minutos"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for campo in self.Meta.fields:
            self.fields[campo].widget.attrs.update({"inputmode": "numeric", "min": "1"})


class CompraOnlineForm(forms.ModelForm):
    """Lo que usa la compra online (plan 07, sexta parte), en su propio formulario.

    Las secciones Logística, Comercial y Fidelización de `CU-CFG-PAR`, más el costo de envío
    (B-07-032) y la pasarela de pago (B-07-031). Van aparte de los valores
    operativos por la misma razón que el modelo de lenguaje: se tocan por otro
    motivo, y un error en uno no tiene por qué borrar lo escrito en el otro.
    """

    class Meta:
        model = ConfiguracionSistema
        fields = [
            "costo_envio",
            "monto_minimo_envio_gratuito",
            "ventana_decision_horas",
            "plazo_retencion_meses",
            "dias_aviso_retencion",
            "plazo_devolucion_dias",
            "plazo_garantia_dias",
            "equivalencia_puntos",
            "porcentaje_puntos",
            "caducidad_puntos_meses",
            "dias_aviso_caducidad_puntos",
            "pasarela",
        ]

    PISO_LEGAL = "El plazo mínimo legal de devolución es 10 días corridos (Ley 24.240, Art. 34)."

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for campo in (
            "costo_envio",
            "monto_minimo_envio_gratuito",
            "equivalencia_puntos",
            "porcentaje_puntos",
        ):
            self.fields[campo].widget.attrs.update({"inputmode": "decimal"})
        for campo in (
            "caducidad_puntos_meses",
            "dias_aviso_caducidad_puntos",
            "ventana_decision_horas",
            "plazo_retencion_meses",
            "dias_aviso_retencion",
        ):
            self.fields[campo].widget.attrs.update({"inputmode": "numeric", "min": "1"})
        for campo in ("plazo_devolucion_dias", "plazo_garantia_dias"):
            self.fields[campo].widget.attrs.update(
                {"inputmode": "numeric", "min": str(ConfiguracionSistema.PISO_LEGAL_DEVOLUCION)}
            )

    def clean_plazo_devolucion_dias(self):
        plazo = self.cleaned_data["plazo_devolucion_dias"]
        if plazo < ConfiguracionSistema.PISO_LEGAL_DEVOLUCION:
            raise forms.ValidationError(self.PISO_LEGAL)
        return plazo

    def solo_falla_el_plazo_de_devolucion(self):
        """`CO-130` E1: el piso legal se rechaza aparte, sin frenar a los demás."""
        return set(self.errors) == {"plazo_devolucion_dias"}


class BorradorForm(forms.ModelForm):
    """Edición de un borrador antes de confirmarlo (CU-ALT-REV paso 2).

    Es un `ModelForm` y no el `ItemLoteForm` del alta manual aunque los campos se
    parezcan, y la diferencia de fondo es cuál es el estado válido de cada uno:
    un ítem de lote **tiene que estar completo para poder guardarse**, y un
    borrador existe justamente para poder guardarse a medias mientras alguien lo
    termina. Compartir el formulario obligaría a que uno de los dos afloje sus
    reglas, y el que aflojaría sería el del alta.

    Los topes sí se comparten, porque son los mismos filtros de tipeo: un volumen
    de cinco cifras es un cero de más lo escriba quien lo escriba.
    """

    class Meta:
        model = BorradorProducto
        fields = [
            "titulo",
            "volumen",
            "isbn",
            "editorial",
            "tipo",
            "formato",
            "precio",
            "fecha_llegada",
            "estado_sugerido",
            "stock_inicial",
            "solo_adultos",
            "autor",
            "sinopsis",
            "portada",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Los catálogos activos, más el que el borrador ya trae aunque esté dado
        # de baja: así se ve cuál es, y el reparo explica por qué no se puede
        # confirmar hasta cambiarlo (`CO-140`, `CO-221`, `CO-148`).
        borrador = self.instance
        self.fields["editorial"].queryset = con_el_actual(
            editoriales_activas(), borrador.editorial_id
        )
        self.fields["tipo"].queryset = con_el_actual(tipos_activos(), borrador.tipo_id)
        self.fields["formato"].queryset = con_el_actual(formatos_activos(), borrador.formato_id)
        mostrar_medidas(self.fields["formato"])

        self.fields["volumen"].validators.append(MaxValueValidator(VOLUMEN_MAXIMO))
        self.fields["stock_inicial"].validators.append(MaxValueValidator(STOCK_MAXIMO))
        self.fields["stock_inicial"].help_text = (
            "Las unidades que se le van a pedir al proveedor al cerrar la revisión."
        )
        self.fields["isbn"].required = False
        self.fields["fecha_llegada"].widget = forms.DateInput(
            attrs={"type": "date"}, format="%Y-%m-%d"
        )

    def clean_titulo(self):
        # Mismo criterio que el alta: sin normalizar, "Akira  vol" y "Akira vol"
        # serían dos productos distintos para cualquiera que compare sin hacerlo.
        return " ".join((self.cleaned_data.get("titulo") or "").split())

    def clean_isbn(self):
        """Se normaliza y **se verifica el dígito de control** (A19).

        El pipeline ya lo verifica al extraer, pero acá el ISBN lo puede escribir
        una persona: es exactamente el momento en que se comete el error de
        transcripción que el verificador existe para atrapar.
        """
        valor = isbn_util.normalizar(self.cleaned_data.get("isbn") or "")
        if not valor:
            return ""
        motivo = isbn_util.motivo_de_rechazo(valor)
        if motivo:
            raise forms.ValidationError(motivo)
        return valor

    def clean(self):
        datos = super().clean()

        # A20: el formato tiene que estar ofrecido para ese tipo. Se valida en el
        # servidor y no solo recortando el desplegable, por el mismo motivo que
        # en el alta — un valor enviado a mano no es más confiable por venir de
        # esta pantalla.
        tipo, formato = datos.get("tipo"), datos.get("formato")
        if formato and tipo and not formato.aplica_a(tipo):
            self.add_error("formato", f"«{formato}» no se ofrece para {tipo}.")
        if formato and tipo and not tipo.usa_formato:
            self.add_error("formato", f"{tipo} no usa formato.")

        # A10: una pre-venta necesita fecha, y no puede ser pasada. La misma
        # regla que en el alta manual, por el mismo motivo: sin fecha el producto
        # queda en pre-venta para siempre, invisible para el ciclo que debería
        # sacarlo de ahí.
        estado, fecha = datos.get("estado_sugerido"), datos.get("fecha_llegada")
        if estado == Producto.PRE_VENTA and not fecha:
            self.add_error("fecha_llegada", "Una pre-venta necesita fecha de llegada.")
        if fecha:
            _validar_fecha_no_pasada(fecha)

        precio = datos.get("precio")
        if precio is not None and precio > IMPORTE_MAXIMO:
            self.add_error("precio", f"El máximo es ${IMPORTE_MAXIMO}.")

        return datos


class RechazoDeBorradorForm(forms.Form):
    """El motivo, que es obligatorio (CU-ALT-REV).

    Mismo criterio que el descarte de un correo: una cola llena de rechazos sin
    explicación no sirve para entender nada después.
    """

    motivo = forms.CharField(
        label="Motivo del rechazo",
        widget=forms.Textarea(attrs={"rows": 3}),
        max_length=500,
        help_text="Queda registrado. Ej.: «ya lo trae otra editorial».",
    )

    def clean_motivo(self):
        motivo = " ".join((self.cleaned_data.get("motivo") or "").split())
        if not motivo:
            raise forms.ValidationError("Indique por qué se descarta el borrador.")
        return motivo
