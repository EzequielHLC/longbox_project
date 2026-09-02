"""Catálogo de productos y su clasificación.

Los estados y los campos de precio se declaran completos desde el principio
aunque los use un módulo posterior: la alternativa es migrar la tabla de
productos tres veces y, peor, tener que adivinar retroactivamente qué productos
ya cargados eran de precio manual.

**Cómo se clasifica un producto.** Hay una línea que ordena todo este archivo:

> **Los campos deciden. Las etiquetas describen.**

Lo que entra en la identidad del producto o en el cálculo de su precio es un
campo con su propia tabla. Lo que solo sirve para encontrarlo es una etiqueta.

Son dos ejes de decisión:

- **Tipo**: qué clase de material es (manga, cómic, artbook, novela ligera).
  Entra en la clave de unicidad y en la de la tabla de precios.
- **Formato**: el tamaño físico del tomo (B6, Tankōbon, grapa, tapa dura).
  Entra en las dos claves también, y es **lo que fija el precio**: dos tomos de
  la misma editorial y el mismo tipo valen distinto según su tamaño.

Y un eje descriptivo, `Etiqueta`, agrupado por `GrupoEtiqueta`: franquicia,
género, colección, lo que el negocio necesite. No entra en ninguna clave, no
interviene en ningún precio, y **un producto puede tener varias**.

La documentación de casos de uso llama "formato" a lo que acá es **tipo**, no
contempla el tamaño, y modela la franquicia como un campo único y obligatorio.
Está anotado en el `# Agregados` del módulo para corregirlo en la fuente.
"""

from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models, transaction
from django.db.models.functions import Lower

from apps.core import cotizaciones

# Los importes nunca son negativos. El validador va en el modelo y no solo en el
# formulario: el formulario protege una pantalla, el modelo protege la tabla —y
# por acá van a entrar después el pipeline automatizado y los comandos.
NO_NEGATIVO = MinValueValidator(Decimal("0"))
POSITIVO = MinValueValidator(Decimal("0.01"))

# Marcador de las excepciones A2/A3: un producto se puede dar de alta sin
# portada, y la portada se adjunta después desde la edición de producto.
IMAGEN_PENDIENTE = "Imagen pendiente"

# Los dos rubros del catálogo. Están acá arriba y no dentro de una clase porque
# los usan tres: `Tipo` para decir a qué rubro pertenece cada categoría,
# `Producto` como discriminador de la jerarquía, y las condiciones de las
# restricciones de `Meta`, que no ven las constantes de su propia clase.
EDITORIAL = "editorial"
NO_EDITORIAL = "no_editorial"

CLASE_CHOICES = [
    (EDITORIAL, "Editorial"),
    (NO_EDITORIAL, "No editorial"),
]


class ProductoAbstractoError(Exception):
    """Se intentó guardar un `Producto` que no es de ningún rubro.

    `Producto` es **abstracto en el sentido del modelo de dominio**: no hay
    productos sueltos, todos son editoriales o no editoriales. No lo es en el
    sentido de Django —tiene tabla propia, y la necesita— así que nada impedía
    instanciarlo salvo la buena voluntad. Esto lo convierte en una regla.
    """


class Editorial(models.Model):
    """Quién publica el material."""

    nombre = models.CharField("nombre", max_length=120)
    activa = models.BooleanField("activa", default=True)

    class Meta:
        verbose_name = "editorial"
        verbose_name_plural = "editoriales"
        ordering = ["nombre"]
        constraints = [  # noqa: RUF012
            models.UniqueConstraint(Lower("nombre"), name="editorial_unica_por_nombre")
        ]

    def __str__(self):
        return self.nombre


class GrupoEtiqueta(models.Model):
    """En qué eje describe una etiqueta: franquicia, género, colección.

    Existe por una razón concreta y no por prolijidad: **sin grupo, el filtro de
    la tienda es una bolsa**. Un cliente que busca cómics de Marvel y otro que
    busca manga shonen usarían la misma caja revuelta, cuando lo que necesitan
    son dos facetas separadas. El grupo es lo que permite dibujar "Franquicia:
    […]" y "Género: […]" como dos filtros distintos.

    Es una tabla y no una lista de opciones en el código por el mismo motivo que
    `Tipo`: agregar "Colección" el año que viene se resuelve desde la pantalla
    de parámetros y no tocando el modelo.
    """

    nombre = models.CharField("nombre", max_length=60)
    activo = models.BooleanField("activo", default=True)
    orden = models.PositiveSmallIntegerField(
        "orden", default=0, help_text="Posición en los filtros. Menor va primero."
    )

    class Meta:
        verbose_name = "grupo de etiquetas"
        verbose_name_plural = "grupos de etiquetas"
        ordering = ["orden", "nombre"]
        constraints = [  # noqa: RUF012
            models.UniqueConstraint(Lower("nombre"), name="grupo_etiqueta_unico_por_nombre")
        ]

    def __str__(self):
        return self.nombre


class Etiqueta(models.Model):
    """Un valor descriptivo del producto: "Marvel", "Shonen", "Edición limitada".

    **Nunca identifica ni fija precios.** Esa es la línea que evita que las
    etiquetas se conviertan en el tacho de basura del modelo: "Tapa dura" no es
    etiqueta porque es un `Formato` y fija el precio; "Ivrea" no es etiqueta
    porque es una `Editorial` y entra en la clave de unicidad. Si algo solo
    sirve para encontrar productos, es etiqueta; si decide algo, es un campo.

    Reemplaza al modelo `Franquicia`, que era exactamente esto pero para un solo
    eje y con un solo valor por producto — y ese "uno solo" ya era incorrecto:
    Marvel publica cómics de Star Wars, o sea Marvel **y** Star Wars.
    """

    nombre = models.CharField("nombre", max_length=80)
    grupo = models.ForeignKey(
        GrupoEtiqueta, on_delete=models.PROTECT, related_name="etiquetas", verbose_name="grupo"
    )
    activa = models.BooleanField("activa", default=True)

    class Meta:
        verbose_name = "etiqueta"
        verbose_name_plural = "etiquetas"
        ordering = ["grupo__orden", "grupo__nombre", "nombre"]
        constraints = [  # noqa: RUF012
            # Única **dentro de su grupo**, no en todo el catálogo: "Terror"
            # puede ser un género y también el nombre de una colección, y son
            # dos etiquetas distintas. Sin distinguir mayúsculas, como el resto
            # de los catálogos que se identifican por su nombre.
            models.UniqueConstraint(
                Lower("nombre"), "grupo", name="etiqueta_unica_por_nombre_y_grupo"
            )
        ]

    def __str__(self):
        return f"{self.grupo} · {self.nombre}"


class Tipo(models.Model):
    """Qué clase de cosa es un producto. **Clasifica los dos rubros, no uno.**

    De un lado manga, cómic, artbook, novela ligera y libro —lo que RF-04 llama
    mal "formato" (A12)—; del otro TCG, figura, merchandising e insumo, que es lo
    que CU-08 llama "categoría". **La fuente nunca dice que son el mismo eje**
    (corrección 23), y lo son: las dos preguntas responden "¿qué clase de cosa
    es esto?" y el inventario de CU-11 las filtra con un solo control.

    Es una tabla y no una lista fija en el código, y `usa_formato` es el motivo:
    **qué campos pide un producto es un dato, no un `if`**. Agregar "Fanzine" el
    año que viene se resuelve desde la pantalla de parámetros y no tocando el
    formulario.

    Tuvo una segunda bandera, `usa_franquicia`, que decidía en qué rubros se
    ofrecía el campo de universo. Se fue con la franquicia: las etiquetas que la
    reemplazan aplican a **todo** tipo de material —un manga tiene género, una
    figura tiene franquicia y escala— así que la bandera habría valido siempre
    `True`, y una bandera que nunca es falsa no es una bandera.
    """

    nombre = models.CharField("nombre", max_length=60)

    # De qué rubro es este tipo. Hace falta porque **cuatro de los cinco
    # consumidores de esta tabla son solo editoriales**: la tabla de precios de
    # referencia, los formatos de A20, `usa_formato` y la cabecera de borradores
    # del proveedor (A7). Sin el discriminador nada impide cargar una fila
    # "Ivrea + Figura + B6" en la tabla de precios, o ponerle "Figura" como tipo
    # habitual a un proveedor editorial y que el pipeline genere borradores con
    # un tipo que no le corresponde.
    #
    # **`usa_formato` no puede hacer este trabajo**, aunque lo parezca: Artbook,
    # Novela ligera y Libro son editoriales y ya lo tienen en falso. Son dos
    # preguntas distintas — "¿de qué rubro es?" y "¿el tamaño le fija el precio?".
    clase = models.CharField(
        "rubro",
        max_length=15,
        choices=CLASE_CHOICES,
        default=EDITORIAL,
    )

    # Si el tipo se mide por tamaño. Un manga se cobra distinto en B6 que en
    # Tankōbon; un artbook no tiene una grilla de tamaños que fije su precio.
    # Solo los tipos con esta bandera entran en la tabla de precios.
    usa_formato = models.BooleanField(
        "se clasifica por formato",
        default=True,
        help_text="El tamaño del tomo fija su precio y entra en la tabla de referencia.",
    )

    activo = models.BooleanField("activo", default=True)
    orden = models.PositiveSmallIntegerField(
        "orden", default=0, help_text="Posición en los desplegables. Menor va primero."
    )

    class Meta:
        verbose_name = "tipo de material"
        verbose_name_plural = "tipos de material"
        ordering = ["orden", "nombre"]
        constraints = [  # noqa: RUF012
            models.UniqueConstraint(Lower("nombre"), name="tipo_unico_por_nombre")
        ]

    def __str__(self):
        return self.nombre

    @property
    def es_editorial(self):
        return self.clase == EDITORIAL


class Formato(models.Model):
    """El tamaño físico del tomo: B6, Tankōbon, grapa, tapa dura.

    El catálogo de nombres es compartido —un B6 es un B6 en todas las
    editoriales— y lo que cambia por editorial es el precio, que vive en
    `TablaPrecioReferencia`. Al revés —un catálogo de formatos por editorial—
    habría que cargar "B6" tantas veces como editoriales haya, y no habría forma
    de comparar precios del mismo tamaño entre editoriales.

    **En qué tipos aplica cada formato lo declara el propio formato**, con una
    relación de muchos a muchos y no con un grupo. La diferencia importa: "Tapa
    dura" existe en manga, en cómic y en libro, y con grupos habría que
    duplicarla —"tapa dura de manga", "tapa dura de cómic"— lo que partiría la
    tabla de precios en dos filas para el mismo tamaño físico. Es el mismo
    razonamiento que hace que el catálogo sea compartido entre editoriales.
    """

    nombre = models.CharField("nombre", max_length=60)
    descripcion = models.CharField(
        "medidas", max_length=120, blank=True, help_text="Por ejemplo: 12,8 × 18,2 cm."
    )

    # **Vacío significa universal**, y el default va en esa dirección a
    # propósito: si el vacío quisiera decir "en ninguno", olvidarse de declarar
    # los tipos dejaría el formato invisible e inusable. Significando "en
    # todos", olvidarse deja el comportamiento que había antes de existir este
    # campo — el peor caso es no mejorar, no romper.
    tipos = models.ManyToManyField(
        "catalog.Tipo",
        blank=True,
        related_name="formatos",
        verbose_name="tipos en los que aplica",
        help_text="Sin declarar ninguno, el formato se ofrece para todos los tipos.",
    )

    activo = models.BooleanField("activo", default=True)
    orden = models.PositiveSmallIntegerField("orden", default=0)

    class Meta:
        verbose_name = "formato"
        verbose_name_plural = "formatos"
        ordering = ["orden", "nombre"]
        constraints = [  # noqa: RUF012
            models.UniqueConstraint(Lower("nombre"), name="formato_unico_por_nombre")
        ]

    def __str__(self):
        return self.nombre

    def aplica_a(self, tipo):
        """Si este formato se ofrece para ese tipo de material.

        Sin tipos declarados es universal, así que aplica a todos. Es la misma
        regla que usa el desplegable del alta, en un solo lugar para que la
        pantalla y la validación no puedan discrepar.
        """
        return not self.tipos.exists() or self.tipos.filter(pk=tipo.pk).exists()


class TablaPrecioReferencia(models.Model):
    """PVP por combinación editorial + tipo + formato (RF-11).

    Los tres campos hacen falta: la misma editorial cobra distinto un manga que
    un cómic, y dentro del manga cobra distinto un B6 que un Tankōbon. Sacar
    cualquiera de los tres deja filas que no se pueden distinguir.

    Los tipos sin formato (artbook, novela ligera) no entran acá: su precio se
    escribe en el alta. Si alguna vez se quisiera tabular alguno, alcanza con
    marcarle `usa_formato` desde la pantalla de parámetros.
    """

    editorial = models.ForeignKey(
        Editorial, on_delete=models.CASCADE, related_name="precios_de_referencia"
    )
    tipo = models.ForeignKey(Tipo, on_delete=models.CASCADE, related_name="precios_de_referencia")
    formato = models.ForeignKey(
        Formato, on_delete=models.CASCADE, related_name="precios_de_referencia"
    )
    pvp = models.DecimalField(
        "precio de venta al público", max_digits=12, decimal_places=2, validators=[POSITIVO]
    )
    actualizado_en = models.DateTimeField("última actualización", auto_now=True)

    class Meta:
        verbose_name = "precio de referencia"
        verbose_name_plural = "tabla de precios de referencia"
        ordering = ["editorial__nombre", "tipo__orden", "formato__orden"]
        constraints = [  # noqa: RUF012
            models.UniqueConstraint(
                fields=["editorial", "tipo", "formato"],
                name="precio_unico_por_editorial_tipo_y_formato",
            )
        ]

    def __str__(self):
        return f"{self.editorial} · {self.tipo} · {self.formato} · ${self.pvp}"


class LoteAlta(models.Model):
    """Una carga en lote de CU-01 o CU-02.

    Existe por dos motivos que el CU pide explícitamente y que no se pueden
    resolver con productos sueltos: la entrada de auditoría es **una sola por
    lote** (no una por ítem), y en importados hay que conservar el CRE y el
    margen *vigentes al momento del alta*, que después cambian.
    """

    NACIONAL = "nacional"
    IMPORTADO = "importado"

    ORIGEN_CHOICES = [  # noqa: RUF012
        (NACIONAL, "Nacional"),
        (IMPORTADO, "Importado"),
    ]

    origen = models.CharField("origen", max_length=10, choices=ORIGEN_CHOICES)

    # Cabecera del lote. Todos opcionales: si quedan vacíos el lote es "mixto" y
    # cada ítem declara los suyos.
    editorial = models.ForeignKey(
        Editorial, on_delete=models.PROTECT, null=True, blank=True, related_name="lotes"
    )
    tipo = models.ForeignKey(
        Tipo, on_delete=models.PROTECT, null=True, blank=True, related_name="lotes"
    )
    formato = models.ForeignKey(
        Formato, on_delete=models.PROTECT, null=True, blank=True, related_name="lotes"
    )
    fecha_llegada = models.DateField("fecha de llegada", null=True, blank=True)

    # ------------------------------------------------------------------
    # Calculadora de envío (solo importados, CU-02).
    # ------------------------------------------------------------------
    costo_envio_total = models.DecimalField(
        "costo total de envío internacional",
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[NO_NEGATIVO],
    )
    # Es el divisor del CRE, así que además de no ser negativo no puede ser
    # cero: un lote sin valor de compra no tiene contra qué prorratear el envío.
    valor_compra_total = models.DecimalField(
        "valor total de compra en origen",
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[POSITIVO],
    )

    # El CRE se persiste calculado y no se recalcula al leer: los totales del
    # lote se pueden corregir después, pero el CRE con el que se fijaron estos
    # precios es un hecho histórico.
    #
    # Seis decimales porque es un cociente, no dinero: redondearlo a dos
    # arrastraría el error a cada precio del lote.
    cre = models.DecimalField(
        "costo relativo de envío",
        max_digits=10,
        decimal_places=6,
        null=True,
        blank=True,
        validators=[NO_NEGATIVO],
    )
    margen_aplicado = models.DecimalField(
        "margen global aplicado",
        max_digits=6,
        decimal_places=4,
        null=True,
        blank=True,
        validators=[NO_NEGATIVO],
    )

    # Moneda de origen y cotización. **Esto no está en la documentación de casos
    # de uso**: la fuente habla de "costo base en origen" sin mencionar
    # conversión en ninguna de sus 128 páginas. Se agregó para no perder el dato
    # con el que se hizo la conversión (ver `# Agregados` del módulo).
    #
    # La cotización se guarda **aunque el lote sea en pesos** (vale 1): así el
    # cálculo de cualquier ítem se reconstruye sin preguntarse si hubo o no
    # conversión, y no hay un caso especial escondido en un `None`.
    moneda_origen = models.CharField(
        "moneda de origen",
        max_length=3,
        choices=cotizaciones.MONEDA_CHOICES,
        default=cotizaciones.MONEDA_LOCAL,
        blank=True,
    )
    cotizacion = models.DecimalField(
        "cotización aplicada",
        max_digits=12,
        decimal_places=4,
        null=True,
        blank=True,
        validators=[POSITIVO],
    )

    # Ítems excluidos por duplicado (E1). Se guardan acá y no como productos
    # porque justamente no se crearon: es el detalle del resumen que el CU pide
    # mostrarle al Administrador, y guardarlo hace que la pantalla de resumen se
    # pueda recargar y compartir en vez de vivir en la sesión.
    rechazados = models.JSONField("ítems rechazados por duplicado", default=list, blank=True)

    creado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="lotes_de_alta",
    )
    creado_en = models.DateTimeField("fecha de carga", auto_now_add=True)

    class Meta:
        verbose_name = "lote de alta"
        verbose_name_plural = "lotes de alta"
        ordering = ["-creado_en"]

    def __str__(self):
        return f"Lote {self.get_origen_display().lower()} #{self.pk} · {self.creado_en:%d/%m/%Y}"

    @property
    def es_mixto(self):
        """Un lote sin editorial y tipo en la cabecera: cada ítem los declara.

        El formato no entra en la cuenta: un lote puede compartir editorial y
        tipo y traer tomos de dos tamaños, y eso no lo vuelve mixto.
        """
        return not (self.editorial_id and self.tipo_id)

    @property
    def tiene_conversion(self):
        """Si los costos del lote vinieron en una moneda que hubo que convertir."""
        return bool(self.moneda_origen) and self.moneda_origen != cotizaciones.MONEDA_LOCAL


class Producto(models.Model):
    """Lo que todo artículo del catálogo tiene, sea del rubro que sea.

    **Es la clase padre de una jerarquía de dos**, y la herencia es de las de
    Django con tabla propia por hijo (*multi-table inheritance*): esta tabla
    guarda lo común y cada hija agrega la suya con lo que solo le corresponde a
    ella. Las dos especializaciones son `ProductoEditorial` y
    `ProductoNoEditorial`.

    **Por qué así y no con campos nulos.** Un mazo de cartas no tiene editorial,
    ni volumen, ni ISBN, ni formato; un tomo no tiene marca ni código interno.
    Con una sola tabla, la mitad de las columnas de cada fila serían nulas y lo
    que las hace obligatorias o no viviría en validaciones sueltas, lejos del
    modelo. Acá la base misma dice qué campos existen para qué cosa.

    **Por qué tabla propia y no clases abstractas.** CU-11 pide un inventario
    **único**: un listado con los mismos filtros, ordenado y paginado sobre los
    dos rubros a la vez. Con clases abstractas cada hija tendría su tabla suelta
    y no habría forma de hacer esa consulta, ni de conservar las claves foráneas
    que ya apuntan acá (`BorradorProducto.producto`, la auditoría, y las que
    traigan Pedidos y Ventas). Con tabla propia, `Producto.objects.all()` sigue
    devolviendo todo.

    **Qué queda acá y qué baja.** Queda lo que el inventario necesita poder
    consultar sobre los dos a la vez —título, tipo, estado, stock, precio— y lo
    que de verdad comparten. Baja lo que solo tiene sentido en uno.
    """

    # Se reexponen como atributos de clase para que el resto del código pueda
    # escribir `Producto.EDITORIAL` sin importar la constante suelta.
    EDITORIAL = EDITORIAL
    NO_EDITORIAL = NO_EDITORIAL
    CLASE_CHOICES = CLASE_CHOICES  # noqa: RUF012

    ACTIVO = "activo"
    PRE_VENTA = "pre_venta"
    AGOTADO = "agotado"
    CANCELADO_EDITORIAL = "cancelado_editorial"
    DESCATALOGADO = "descatalogado"

    ESTADO_CHOICES = [  # noqa: RUF012
        (ACTIVO, "Activo"),
        (PRE_VENTA, "Pre-venta"),
        (AGOTADO, "Agotado"),
        (CANCELADO_EDITORIAL, "Cancelado por editorial"),
        (DESCATALOGADO, "Descatalogado"),
    ]

    # CU-06: estado terminal. Un título cancelado por la editorial no llega
    # nunca, y por eso se reembolsa el 100%; no se reactiva y no se confunde con
    # la baja de catálogo de CU-10, que sí conserva el producto en inventario.
    ESTADOS_TERMINALES = (CANCELADO_EDITORIAL,)

    # De qué especialización es esta fila. Django ya sabe llegar a la hija, pero
    # **hace falta como columna** por dos motivos concretos: permite filtrar y
    # contar por rubro sin salir de esta tabla —el inventario lo hace en cada
    # carga— y permite condicionar restricciones de unicidad a un solo rubro,
    # que es lo que hace posible la clave de CU-08 (ver `Meta`).
    #
    # Lo escribe `save()`, no el que crea el objeto: un discriminador que haya
    # que acordarse de completar es un discriminador que en algún momento va a
    # estar mal.
    clase = models.CharField(
        "rubro", max_length=15, choices=CLASE_CHOICES, editable=False, default=""
    )

    # **La identidad de la fila.** Único, siempre presente, y no cambia nunca.
    # Es lo que va en la etiqueta de góndola y lo que el Cajero tipea o escanea
    # en el mostrador.
    #
    # **Identidad no es lo mismo que detección de duplicados**, y confundirlas
    # fue el error del que salió este campo. La identidad tiene que existir
    # siempre y no puede depender de datos descriptivos: en cuanto la marca o el
    # nombre entran en la clave, todo producto que no los tenga —el merch
    # genérico, lo no oficial— se vuelve inmodelable. El ISBN, el código de
    # barras y las tuplas descriptivas siguen existiendo, pero para **detectar
    # duplicados**, que es otra cosa y puede fallar sin romper nada.
    #
    # **Híbrido a propósito:** se puede escribir a mano, porque la comiquería ya
    # tiene una nomenclatura en sus planillas, y si se deja vacío lo genera el
    # sistema. Nunca falta y nunca choca.
    #
    # Que lo generemos nosotros **no contradice** la regla de que el código que
    # verifica un identificador no lo fabrica: esa regla es para el ISBN y el
    # código de barras, que se refieren a algo del mundo y que inventados dan un
    # número válido que no identifica nada. Este se refiere a nuestra propia
    # fila, y generarlo es la única forma de que exista.
    codigo = models.CharField(
        "código",
        max_length=30,
        unique=True,
        null=True,
        blank=True,
        help_text="Se genera solo si se deja vacío. No cambia una vez asignado.",
    )

    # El número que trae el envase. **Va acá y no en un rubro**, y eso no es
    # simetría por prolijidad: un ISBN-13 **es** un EAN-13. Los prefijos 978 y
    # 979 son "Bookland", el país ficticio que GS1 reservó para libros dentro
    # del sistema EAN, y el dígito verificador se calcula con los mismos pesos
    # alternados — está en `apps/catalog/isbn.py`. Decir que solo el material no
    # editorial tiene código de barras era, literalmente, falso.
    #
    # Opcional en los dos rubros: el merch genérico no lo trae, y el material
    # editorial de fondo puede tener un ISBN-10, que **no** es un EAN válido.
    #
    # **Hoy no lo escribe nada y es a propósito.** No hay lector de códigos en el
    # proyecto, así que el mostrador se maneja por `codigo`. Se declara porque es
    # un dato del producto, no una funcionalidad; cuando haya lector, el campo ya
    # está y no hace falta migrar nada.
    codigo_barras = models.CharField(
        "código de barras",
        max_length=20,
        blank=True,
        help_text="EAN o UPC del envase, si el producto lo trae.",
    )

    titulo = models.CharField("título", max_length=200)

    # El eje que clasifica a los dos rubros: manga, cómic y artbook de un lado;
    # TCG, figura, merchandising e insumo del otro. Está en el padre y no en
    # cada hija porque el inventario de CU-11 filtra por él **sobre los dos a la
    # vez** — el paso 3 lo llama "categoría".
    tipo = models.ForeignKey(Tipo, on_delete=models.PROTECT, related_name="productos")

    # Descriptivas y opcionales, sin efecto sobre identidad ni precio. En un tomo
    # son género y franquicia; en una figura, franquicia y escala. Sirven igual a
    # los dos, así que viven en el padre.
    etiquetas = models.ManyToManyField(
        Etiqueta, blank=True, related_name="productos", verbose_name="etiquetas"
    )

    # Cambia lo que el sistema hace —excluye del catálogo público—, así que es un
    # campo y no una etiqueta (A18). Aplica a los dos rubros: hay manga para
    # adultos y hay figuras para adultos.
    solo_adultos = models.BooleanField(
        "solo para adultos",
        default=False,
        help_text="Se excluye del catálogo público de la tienda.",
    )

    estado = models.CharField("estado", max_length=25, choices=ESTADO_CHOICES, default=ACTIVO)
    stock = models.PositiveIntegerField("stock", default=0)

    # El precio que se cobra, redondeado al peso (A1). Está en el padre porque el
    # inventario lo muestra y lo va a ordenar por él; **cómo se forma** es cosa de
    # cada hija, y por eso el precio base y el costo de origen bajan.
    precio = models.DecimalField("precio", max_digits=12, decimal_places=2, validators=[POSITIVO])

    portada = models.ImageField("imagen", upload_to="portadas/", blank=True)

    # En un tomo es la sinopsis y en una figura la descripción del artículo. Es
    # el mismo campo y se llama por el nombre que sirve para los dos; cada
    # formulario le pone la etiqueta de su rubro.
    descripcion = models.TextField("descripción", blank=True)

    # A4 de proveedores: de quién vino. Nula en las altas manuales, la completa
    # la confirmación de borradores de CU-05.
    proveedor = models.ForeignKey(
        "suppliers.Proveedor",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="productos",
        verbose_name="proveedor",
    )

    creado_en = models.DateTimeField("fecha de alta", auto_now_add=True)
    actualizado_en = models.DateTimeField("última modificación", auto_now=True)

    class Meta:
        verbose_name = "producto"
        verbose_name_plural = "productos"
        ordering = ["-creado_en"]
        # **Sin restricción de nombre + categoría, y es deliberado.** CU-08 E2 la
        # trata como bloqueo: si ya existe un producto con ese nombre y esa
        # categoría, el alta no se registra. El catálogo no editorial real no lo
        # tolera — hay merch genérico, sin marca y no oficial, y dos llaveros de
        # Naruto de proveedores distintos son dos productos. Con la clave dura,
        # el Administrador termina inventándole un nombre al segundo, y ahí el
        # nombre pasó a cargar información de identidad, que es justo lo que no
        # tiene que hacer.
        #
        # La identidad de la fila es `codigo`, que ya es único. El choque de
        # nombre + categoría se informa como **advertencia** con enlace a la
        # ficha existente, y el Administrador decide. Ver la corrección 21.
        constraints = [  # noqa: RUF012
            # Único cuando está, igual que el ISBN y por el mismo motivo: dos
            # productos con el mismo código de barras son el mismo producto. La
            # condición lo limita a los que lo declaran, así que los que no lo
            # tienen no chocan entre sí por compartir la cadena vacía.
            models.UniqueConstraint(
                fields=["codigo_barras"],
                condition=~models.Q(codigo_barras=""),
                name="producto_unico_por_codigo_de_barras",
            ),
        ]
        indexes = [  # noqa: RUF012
            # El inventario abre filtrando por estado y ordenando por título
            # (CU-11 paso 2), y lo hace en cada carga.
            models.Index(fields=["estado", "titulo"]),
        ]

    def __str__(self):
        return self.titulo

    # El prefijo del código generado. Es seguro que sea semántico porque **el
    # rubro de una fila no cambia nunca**: una fila no salta de una tabla hija a
    # la otra. Un prefijo derivado del tipo, en cambio, mentiría en cuanto
    # alguien recategorizara el producto.
    PREFIJO_CODIGO = "P"

    def save(self, *args, **kwargs):
        """Escribe el discriminador y, si hace falta, genera el código.

        El discriminador lo pone la clase real y no quien crea el objeto: sería
        pedirle que repita algo que el propio tipo ya dice, y alcanzaría con un
        olvido para tener una fila editorial contándose como no editorial en el
        inventario.

        **El código se deriva de la clave primaria**, y por eso se asigna en un
        segundo guardado. No es una torpeza: la clave primaria ya la garantiza
        única la base, así que un código derivado de ella no puede chocar ni
        necesita una tabla de secuencias ni un bloqueo. La alternativa —buscar el
        máximo y sumarle uno— sí tiene carrera.
        """
        if not self.CLASE_PROPIA:
            raise ProductoAbstractoError(
                "Un producto siempre es de un rubro: use ProductoEditorial o "
                "ProductoNoEditorial. `Producto` agrupa lo común y no se instancia."
            )
        if not self.clase:
            self.clase = self.CLASE_PROPIA

        generar = not self.codigo
        # **Las dos escrituras van juntas o no van.** El código se deriva de la
        # clave primaria, así que hay que insertar para poder calcularlo; sin la
        # transacción, entre el insert y la actualización hay un instante en el
        # que otra conexión ve una fila sin código. Envueltas, ese estado
        # intermedio no existe para nadie de afuera, y el `null` de la columna
        # deja de ser una debilidad para ser un detalle de cómo se asigna.
        with transaction.atomic():
            super().save(*args, **kwargs)
            if generar:
                self.codigo = f"{self.PREFIJO_CODIGO}-{self.pk:06d}"
                # Se escribe por la tabla del padre y no con otro `save()`: el
                # campo vive acá, y un `save()` completo desde una hija volvería
                # a tocar las dos tablas para actualizar una sola columna.
                Producto.objects.filter(pk=self.pk).update(codigo=self.codigo)

    # Qué rubro es cada clase de la jerarquía. El padre no declara ninguno: un
    # `Producto` suelto no existe en el negocio, siempre es de un rubro o del
    # otro.
    CLASE_PROPIA = ""

    @property
    def es_editorial(self):
        return self.clase == self.EDITORIAL

    @property
    def portada_pendiente(self):
        """A2: se dio de alta sin imagen y hay que adjuntarla desde CU-09."""
        return not self.portada

    @property
    def esta_en_pre_venta(self):
        return self.estado == self.PRE_VENTA

    @property
    def especifico(self):
        """La instancia de la hija que corresponde, o `self` si ya lo es.

        El listado del inventario trabaja con instancias del padre —es lo que
        hace posible la consulta única de CU-11— y la ficha necesita los campos
        propios del rubro. Esto es el puente, en un solo lugar: repartido por las
        plantillas, cada una elegiría su forma de bajar y una se olvidaría del
        caso que no conoce.

        **Quien lo use sobre una lista tiene que traer las hijas con
        `select_related`.** La herencia con tabla por hija no baja sola, así que
        sin eso cada fila dispara su propia consulta: es el N+1 clásico de esta
        forma de herencia, y con veinticinco filas por página se nota.
        """
        if type(self) is not Producto:
            return self
        try:
            return self.productoeditorial if self.es_editorial else self.productonoeditorial
        except (ProductoEditorial.DoesNotExist, ProductoNoEditorial.DoesNotExist):
            # Una fila del padre sin su hija no debería existir. Si existe, es
            # mejor devolverla que reventar una pantalla de consulta.
            return self

    def clave_de_duplicado(self):
        """Qué hace único a este producto. **Cada rubro la define distinta.**

        Es el método que justifica la jerarquía: un tomo se identifica por su
        ISBN o por título + volumen + tipo + formato + editorial, y una figura
        por nombre + categoría. Con un solo modelo, esa diferencia vivía en un
        `if` dentro de la función de búsqueda de duplicados.
        """
        raise NotImplementedError


class ProductoEditorial(Producto):
    """Un tomo: manga, cómic, artbook, novela ligera o libro (CU-01, CU-02).

    Suma a `Producto` todo lo que hace a una **edición**: el volumen dentro de
    su serie, el ISBN que la identifica en el mundo, la editorial que la publica,
    el tamaño físico que fija su precio, y la maquinaria de precio y llegada que
    el material no editorial no tiene.
    """

    NACIONAL = "nacional"
    IMPORTADO = "importado"

    # Cómo se forma el precio, que es lo único que esta distinción decide:
    # nacional lo toma de la tabla de referencia, importado lo calcula desde el
    # costo de origen con el CRE y el margen. **Ya no incluye "no editorial"**:
    # eso dejó de ser un valor de un campo y pasó a ser una clase.
    ORIGEN_CHOICES = [  # noqa: RUF012
        (NACIONAL, "Editorial nacional"),
        (IMPORTADO, "Editorial importado"),
    ]

    CLASE_PROPIA = Producto.EDITORIAL
    PREFIJO_CODIGO = "E"

    volumen = models.PositiveIntegerField("volumen")

    # El identificador global de la edición. Opcional —el material de fondo viejo
    # no siempre lo trae— pero **único cuando está**: dos productos con el mismo
    # ISBN son el mismo producto cargado dos veces.
    #
    # Se guarda normalizado, sin guiones (ver `apps/catalog/isbn.py`).
    isbn = models.CharField(
        "ISBN",
        max_length=13,
        blank=True,
        help_text="Con guiones o sin ellos: se guarda normalizado.",
    )
    editorial = models.ForeignKey(Editorial, on_delete=models.PROTECT, related_name="productos")

    # El tamaño físico. Nulo en los importados —ahí el precio sale del costo de
    # origen y no de ninguna tabla— y en los tipos que no lo usan (A12).
    formato = models.ForeignKey(
        Formato,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="productos",
    )

    origen = models.CharField("origen", max_length=15, choices=ORIGEN_CHOICES)
    autor = models.CharField("autor", max_length=200, blank=True)

    fecha_llegada = models.DateField("fecha de llegada", null=True, blank=True)

    # CU-07. **"Demorado" no es un estado, es un indicador** (A29): un producto
    # demorado sigue en Pre-venta, se sigue pudiendo reservar, y lo único que
    # cambió es que se sabe que no llega cuando decía. Solo aplica acá: el
    # material no editorial no admite Pre-venta (CU-08), así que no puede
    # demorarse.
    demorado = models.BooleanField(
        "demorado",
        default=False,
        help_text="El proveedor avisó que no llega en la fecha programada.",
    )
    fecha_estimada = models.DateField("nueva fecha estimada", null=True, blank=True)
    nota_demora = models.TextField("nota interna de la demora", blank=True)

    # El precio antes del redondeo, que se persiste **siempre** para poder
    # recalcular ante un cambio de margen sin volver a pedir los datos del lote.
    precio_base = models.DecimalField(
        "precio base", max_digits=12, decimal_places=2, validators=[NO_NEGATIVO]
    )
    # Lo que costó en origen, en la moneda del lote (A2). Solo en importados.
    costo_origen = models.DecimalField(
        "costo en origen",
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[NO_NEGATIVO],
    )
    precio_manual = models.BooleanField("precio fijado a mano", default=False)
    precio_referencia = models.ForeignKey(
        TablaPrecioReferencia,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="productos",
        verbose_name="precio de referencia",
    )

    lote = models.ForeignKey(
        LoteAlta,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="productos",
    )

    # La tupla de A13 —título, volumen, tipo, formato y editorial— guardada como
    # una sola cadena, para poder exigirla en la base.
    #
    # **Existe porque la herencia partió la tupla en dos tablas:** `titulo` y
    # `tipo` viven en el padre y el resto acá, y una restricción de unicidad no
    # abarca dos tablas. Esto copia los dos campos del padre a una columna de la
    # hija y la restricción vuelve a caber. Es la misma denormalización que la
    # auditoría hace con `actor_email` y `objetivo_email`, y por el mismo motivo:
    # una garantía que se pierde si el dato no está donde hace falta.
    #
    # El `or 0` del formato es el `Coalesce` de A13 escrito en Python: en SQL dos
    # nulos no son iguales, así que sin él dos importados sin formato —que es lo
    # normal— no chocarían nunca entre sí.
    #
    # **Condición de uso:** un producto editorial se edita **siempre** por esta
    # clase, nunca por `Producto`. Guardar por el padre no recalcula esta clave,
    # porque el `save()` del padre no toca la tabla de la hija.
    clave_edicion = models.CharField(max_length=320, editable=False, default="")

    class Meta:
        verbose_name = "producto editorial"
        verbose_name_plural = "productos editoriales"
        constraints = [  # noqa: RUF012
            # La clave más confiable, y **la única de este rubro que puede vivir
            # en la base**: un ISBN identifica una edición y nada más. La
            # condición la limita a los que lo declaran, así que los que no lo
            # tienen no chocan entre sí por compartir la cadena vacía.
            #
            # La otra clave —título + volumen + tipo + formato + editorial—
            # **no puede ser restricción de base con esta jerarquía**: título y
            # tipo viven en la tabla del padre y el resto acá, y una restricción
            # no abarca dos tablas. Queda en `services.buscar_duplicado`, que la
            # aplica antes de cada alta y antes de cada confirmación. Ver el
            # agregado A30 de `alta_editorial.md`, que explica qué se pierde y
            # por qué se aceptó.
            models.UniqueConstraint(
                fields=["isbn"],
                condition=~models.Q(isbn=""),
                name="producto_editorial_unico_por_isbn",
            ),
            # La tupla de A13, recuperada como garantía de base. Es el respaldo
            # del ISBN: el material de fondo viejo no siempre lo trae, y sin esto
            # dos altas simultáneas del mismo tomo sin ISBN entrarían las dos.
            models.UniqueConstraint(
                fields=["clave_edicion"],
                name="producto_editorial_unico_por_clave",
            ),
        ]

    def __str__(self):
        return f"{self.titulo} #{self.volumen}"

    def save(self, *args, **kwargs):
        self.clave_edicion = self.calcular_clave_edicion()
        return super().save(*args, **kwargs)

    def clean(self):
        super().clean()
        # El tipo tiene que ser del mismo rubro. Sin esto nada impide un tomo
        # cargado con categoría "Figura", que además entraría en la tabla de
        # precios de referencia por una combinación que no existe.
        if self.tipo_id and not self.tipo.es_editorial:
            raise ValidationError({"tipo": f"«{self.tipo}» no es un tipo de material editorial."})

    def calcular_clave_edicion(self):
        """La tupla de A13 en una cadena, normalizada igual que la comparación.

        El título va en minúsculas y con los espacios internos colapsados, que es
        lo mismo que hacía el `Lower()` de la restricción vieja: quien carga
        "Batman " un martes y "batman" el jueves está cargando el mismo tomo.
        """
        titulo = " ".join((self.titulo or "").split()).lower()
        return f"{titulo}|{self.volumen}|{self.tipo_id}|{self.formato_id or 0}|{self.editorial_id}"

    @property
    def es_importado(self):
        return self.origen == self.IMPORTADO

    @property
    def esta_demorado(self):
        """El indicador de CU-07, que **solo tiene sentido en Pre-venta**.

        Se pregunta por las dos cosas y no solo por la bandera: un producto que
        ya llegó y pasó a Activo no está demorado aunque la bandera hubiera
        quedado puesta, y leerla sola mostraría "Demorado" en el catálogo sobre
        algo que está en la góndola.
        """
        return self.demorado and self.esta_en_pre_venta

    @property
    def llegada_vigente(self):
        """La fecha en la que hoy se espera el producto.

        La estimada pisa a la programada cuando existe, que es lo que hace que la
        ficha y las notificaciones digan lo mismo sin que cada una elija por su
        cuenta cuál de las dos mostrar.
        """
        return self.fecha_estimada or self.fecha_llegada

    def clave_de_duplicado(self):
        """ISBN si lo tiene; si no, la tupla de A13.

        El orden importa y no es simétrico: si el ISBN encuentra algo, no hace
        falta mirar la tupla. Al revés no vale, porque un producto viejo cargado
        sin ISBN puede ser el mismo tomo que uno nuevo que sí lo trae.
        """
        if self.isbn:
            return ("isbn", self.isbn)
        return (
            "tupla",
            " ".join(self.titulo.split()).lower(),
            self.volumen,
            self.tipo_id,
            self.formato_id,
            self.editorial_id,
        )


class ProductoNoEditorial(Producto):
    """TCG, figura, merchandising o insumo (CU-08).

    Suma poco y quita bastante, que es justamente el punto: no tiene editorial,
    ni volumen, ni ISBN, ni formato, ni nada de la maquinaria de precio de los
    importados. Su precio se carga a mano y listo.

    **No admite Pre-venta.** Lo dice CU-08 en sus comentarios: el sistema asigna
    exclusivamente Activo al momento del alta. Se valida en `clean()` y no solo
    escondiendo la opción en la pantalla.
    """

    CLASE_PROPIA = Producto.NO_EDITORIAL
    PREFIJO_CODIGO = "N"

    ESTADOS_PERMITIDOS = (
        Producto.ACTIVO,
        Producto.AGOTADO,
        Producto.DESCATALOGADO,
    )

    # Quien lo fabrica. **No es una editorial y no se guarda como tal**: son dos
    # conjuntos que no se solapan, y meter "Bandai" en la tabla de editoriales lo
    # haría aparecer en el desplegable del alta de lotes y mezclaría figuras con
    # tomos en el filtro del catálogo. Es el mismo error que A17 desarmó con la
    # franquicia, y por eso acá es texto y no una clave foránea: la fuente lo
    # pide como campo opcional, no como catálogo administrado.
    marca = models.CharField("marca o fabricante", max_length=200, blank=True)

    class Meta:
        verbose_name = "producto no editorial"
        verbose_name_plural = "productos no editoriales"

    def clean(self):
        super().clean()
        if self.estado not in self.ESTADOS_PERMITIDOS:
            raise ValidationError(
                {"estado": "El material no editorial no admite Pre-venta ni cancelación editorial."}
            )
        if self.tipo_id and self.tipo.es_editorial:
            raise ValidationError({"tipo": f"«{self.tipo}» es un tipo de material editorial."})

    def clave_de_duplicado(self):
        """Nombre + categoría (CU-08 paso 6). Nada más y nada menos."""
        return ("nombre", " ".join(self.titulo.split()).lower(), self.tipo_id)


class BorradorProductoQuerySet(models.QuerySet):
    def pendientes(self):
        """Los que esperan una decisión del Administrador (CU-05 paso 1)."""
        return self.filter(estado__in=BorradorProducto.ESTADOS_ABIERTOS)


class BorradorProducto(models.Model):
    """Un producto propuesto por el pipeline de novedades. Todavía no es catálogo.

    Es la pieza que separa lo que el modelo de lenguaje **propone** de lo que el
    sistema **aplica**: nada de lo que sale de una extracción entra al catálogo
    sin que una persona lo confirme en CU-05. Por eso es una tabla propia y no
    un `Producto` con una bandera de "sin revisar" — un producto a medias en la
    misma tabla se filtra tarde o temprano en una consulta que se olvide de
    excluirlo, y para cuando se note ya estuvo a la venta.

    Vive en `catalog` y no en `suppliers` aunque nazca de un correo: tiene los
    mismos campos que `Producto`, se valida contra los mismos catálogos y al
    confirmarse crea uno. Del lado de proveedores solo están su origen —el
    correo y el proveedor— y la cabecera que hereda de la ficha de ese proveedor.

    **Lo que no tiene, y es a propósito:** etiquetas. El correo no las trae y el
    proveedor no las declara, así que sería una relación que nada llena. Cuando
    la revisión quiera ofrecerlas, agregarlas es una migración aditiva sin datos
    que trasladar — a diferencia de `precio_manual`, que se declaró antes de
    tiempo justamente porque después habría hecho falta adivinarles el valor a
    los productos ya cargados.
    """

    # Los cuatro que declaran CU-04 paso 6 y CU-05. Se declaran completos desde
    # el principio con el mismo criterio que los estados de `Producto` y los de
    # `CorreoProveedor`: la alternativa es migrar la tabla tres veces.
    PENDIENTE = "pendiente"
    INCOMPLETO = "incompleto"
    CONFIRMADO = "confirmado"
    RECHAZADO = "rechazado"

    ESTADO_CHOICES = [  # noqa: RUF012
        (PENDIENTE, "Pendiente de revisión"),
        (INCOMPLETO, "Extracción incompleta"),
        (CONFIRMADO, "Confirmado"),
        (RECHAZADO, "Rechazado"),
    ]

    # Los dos sobre los que todavía se puede decidir algo. Un borrador
    # confirmado ya es un producto y uno rechazado ya se descartó.
    ESTADOS_ABIERTOS = (PENDIENTE, INCOMPLETO)

    # ------------------------------------------------------------------
    # De dónde salió
    # ------------------------------------------------------------------

    # `PROTECT` en los dos: un borrador sin origen no se puede auditar, y saber
    # de qué correo salió es lo que permite volver a mirarlo cuando algo
    # extraído resulte raro. Los correos no se borran; si alguna vez se
    # borraran, esto lo diría en voz alta en vez de llevarse los borradores.
    correo = models.ForeignKey(
        "suppliers.CorreoProveedor",
        on_delete=models.PROTECT,
        related_name="borradores",
        verbose_name="correo de origen",
    )
    proveedor = models.ForeignKey(
        "suppliers.Proveedor",
        on_delete=models.PROTECT,
        related_name="borradores",
        verbose_name="proveedor",
    )

    # ------------------------------------------------------------------
    # Los mismos campos que un producto
    # ------------------------------------------------------------------

    titulo = models.CharField("título", max_length=200, blank=True)
    volumen = models.PositiveIntegerField("volumen", null=True, blank=True)
    isbn = models.CharField("ISBN", max_length=13, blank=True)

    # Que los tres puedan quedar nulos es la diferencia de fondo con `Producto`:
    # un borrador existe justamente para poder guardar algo incompleto y que una
    # persona lo termine.
    #
    # `editorial` y `tipo` los hereda de la ficha del proveedor (A7 de
    # proveedores) y no salen del correo. Vacíos significan que el proveedor es
    # una distribuidora que trae varias editoriales, y ahí sí hay que elegirlos
    # a mano en la revisión.
    editorial = models.ForeignKey(
        Editorial,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="borradores",
    )
    tipo = models.ForeignKey(
        Tipo,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="borradores",
    )
    formato = models.ForeignKey(
        Formato,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="borradores",
    )

    precio = models.DecimalField("precio", max_digits=12, decimal_places=2, null=True, blank=True)
    fecha_llegada = models.DateField("fecha de llegada", null=True, blank=True)
    portada = models.ImageField("portada", upload_to="borradores/", blank=True)
    sinopsis = models.TextField("sinopsis", blank=True)
    autor = models.CharField("autor", max_length=200, blank=True)
    solo_adultos = models.BooleanField("solo para adultos", default=False)

    # Pre-completado con el valor de `ConfiguracionSistema` y editable en la
    # revisión (CU-05 paso 2). Es el único stock del sistema que nace con un
    # número que nadie contó, y por eso el de las altas manuales es cero y este
    # no (A3): acá el Administrador mira el número antes de confirmarlo.
    stock_inicial = models.PositiveIntegerField("stock inicial", default=0)

    # El estado con el que nacería el producto, derivado de la fecha
    # (CU-04 paso 6). Se guarda en vez de derivarse al vuelo porque la revisión
    # lo deja editar, y una vez editado ya no es lo que la fecha diría.
    estado_sugerido = models.CharField(
        "estado sugerido",
        max_length=25,
        choices=[
            (Producto.ACTIVO, "Activo"),
            (Producto.PRE_VENTA, "Pre-venta"),
        ],
        default=Producto.ACTIVO,
    )

    # ------------------------------------------------------------------
    # Lo que solo tiene un borrador
    # ------------------------------------------------------------------

    estado = models.CharField("estado", max_length=15, choices=ESTADO_CHOICES, default=PENDIENTE)
    motivo_rechazo = models.TextField("motivo del rechazo", blank=True)

    # Lo que el sistema le corrigió o le descartó al modelo. **No es lo mismo
    # que una confianza baja:** la confianza la declara el modelo ("esto lo leí
    # dudando") y el reparo lo detectamos nosotros ("esto lo descarté porque no
    # verifica"). La pantalla los muestra distinto, y por eso viven separados.
    reparos = models.JSONField("reparos", default=list, blank=True)

    # El identificador de la portada dentro del correo. Se conserva aunque la
    # imagen ya se haya extraído: es lo que permite volver a sacarla del archivo
    # original si algo sale mal, sin tener que adivinar cuál era.
    cid_portada = models.CharField("identificador de la portada", max_length=200, blank=True)

    # En qué se convirtió al confirmarse (CU-05). Se declara ahora aunque
    # todavía nada lo escriba, por el mismo criterio con el que `Producto`
    # declaró `precio_manual` antes de que existiera la propagación: agregarlo
    # después obligaría a una migración retroactiva sobre borradores de los que
    # ya no se sabría qué produjeron.
    # Apunta a la hija editorial y **no al padre**, y no es prolijidad: es un
    # límite declarado del sistema. `contexto_alcance_y_limitaciones.md` dice que
    # la carga de artículos no editoriales "requerirá carga manual campo por
    # campo", y OBJ-02 acota la automatización a las altas de productos
    # **editoriales**. Apuntando al padre, nada impediría vincular un borrador a
    # una figura; el modelo tiene que impedirlo, no confiar en que nadie lo haga.
    producto = models.ForeignKey(
        ProductoEditorial,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="borrador_de_origen",
    )

    # La tanda de revisión en la que se confirmó o se rechazó (CU-05). Nulo
    # mientras está pendiente. Es lo que permite armar el pedido consolidado
    # **de esa sesión**: dos revisiones el mismo día tienen que producir dos
    # correos separados al mismo proveedor, no uno con todo mezclado.
    sesion = models.ForeignKey(
        "catalog.SesionRevision",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="borradores",
    )

    creado_en = models.DateTimeField("generado el", auto_now_add=True)
    resuelto_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="borradores_resueltos",
    )
    resuelto_en = models.DateTimeField("resuelto el", null=True, blank=True)

    objects = BorradorProductoQuerySet.as_manager()

    class Meta:
        verbose_name = "borrador de producto"
        verbose_name_plural = "borradores de producto"
        # Lo más viejo primero: la cola de revisión se atiende en orden de
        # llegada, al revés que la de correos, donde lo que importa es lo nuevo.
        ordering = ["creado_en", "pk"]
        indexes = [  # noqa: RUF012
            # "Qué tengo pendiente de revisar" es la consulta de CU-05, y se
            # hace en cada carga de la pantalla.
            models.Index(fields=["estado", "creado_en"]),
        ]

    def __str__(self):
        titulo = self.titulo or "(sin título)"
        return f"{titulo} #{self.volumen}" if self.volumen else titulo

    @property
    def esta_abierto(self):
        return self.estado in self.ESTADOS_ABIERTOS

    @property
    def portada_pendiente(self):
        """Sin portada: se adjunta en la revisión o después, desde CU-09."""
        return not self.portada

    @property
    def nace_en_pre_venta(self):
        return self.estado_sugerido == Producto.PRE_VENTA

    @property
    def campos_bloqueantes_vacios(self):
        """Lo que CU-05 paso 3 exige para poder confirmar y todavía falta.

        Son los cuatro que el CU enumera —título, editorial, formato y precio—
        con **dos apartamientos del texto, los dos deliberados**:

        - Donde el CU dice "formato" hay que leer `tipo`, que es lo que la
          fuente llama así (A12). El tamaño físico no puede ser bloqueante: los
          tipos que no lo usan no tienen ninguno, y exigirlo trabaría todos los
          artbooks y libros para siempre.
        - La fecha se suma **solo si el borrador nacería en Pre-venta**. Es el
          bloqueante condicional del propio CU, y coincide con A10: una
          pre-venta sin fecha se quedaría en pre-venta para siempre, invisible
          para el ciclo que debería sacarla de ahí.
        """
        faltantes = []
        if not self.titulo:
            faltantes.append("titulo")
        if not self.editorial_id:
            faltantes.append("editorial")
        if not self.tipo_id:
            faltantes.append("tipo")
        if self.precio is None:
            faltantes.append("precio")
        if self.nace_en_pre_venta and not self.fecha_llegada:
            faltantes.append("fecha_llegada")
        return faltantes

    @property
    def confianzas_bajas_sin_revisar(self):
        """Los campos que el modelo declaró dudosos y nadie miró todavía.

        CU-05 los usa para dos cosas distintas: bloquear la confirmación
        individual hasta que se los revise uno por uno, y **excluir el borrador
        entero** de una confirmación en lote.
        """
        return [confianza for confianza in self.confianzas.all() if confianza.exige_revision]


class SesionRevision(models.Model):
    """Una tanda de revisión de borradores (CU-05).

    **El caso de uso no la declara como entidad, y la necesita igual.** El flujo
    habla de "al finalizar la sesión", audita su cierre con confirmados,
    rechazados y pendientes, y arma un pedido consolidado por proveedor *de esa
    sesión*. Sin algo que agrupe la tanda no hay forma de decir cuáles son "los
    productos de esta sesión", y dos revisiones el mismo día generarían un solo
    correo mezclado en vez de dos.

    **Se crea con la primera acción, no al abrir la pantalla.** Mirar la cola no
    es revisar: crear la sesión al entrar llenaría la tabla de sesiones vacías
    cada vez que alguien pasa a ver qué hay. La primera confirmación o el primer
    rechazo la abren.
    """

    ABIERTA = "abierta"
    CERRADA = "cerrada"

    ESTADO_CHOICES = [  # noqa: RUF012
        (ABIERTA, "Abierta"),
        (CERRADA, "Cerrada"),
    ]

    revisor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="sesiones_de_revision",
    )
    estado = models.CharField("estado", max_length=10, choices=ESTADO_CHOICES, default=ABIERTA)
    abierta_en = models.DateTimeField("abierta el", auto_now_add=True)
    cerrada_en = models.DateTimeField("cerrada el", null=True, blank=True)

    # Qué pasó con los correos de pedido al cerrar (CU-05 paso 5). Se guarda el
    # detalle por proveedor —enviado, o falló con su motivo— porque el CU pide
    # notificar al Administrador indicando **cuál** proveedor falló, y porque un
    # pedido que no salió es algo que alguien va a tener que mandar a mano.
    envios = models.JSONField("correos de pedido", default=list, blank=True)

    class Meta:
        verbose_name = "sesión de revisión"
        verbose_name_plural = "sesiones de revisión"
        ordering = ["-abierta_en"]

    def __str__(self):
        return f"Revisión #{self.pk} · {self.abierta_en:%d/%m/%Y %H:%M}"

    @property
    def esta_abierta(self):
        return self.estado == self.ABIERTA

    @property
    def confirmados(self):
        return self.borradores.filter(estado=BorradorProducto.CONFIRMADO)

    @property
    def rechazados(self):
        return self.borradores.filter(estado=BorradorProducto.RECHAZADO)

    @property
    def envios_fallidos(self):
        return [envio for envio in (self.envios or []) if not envio.get("enviado")]


class ConfianzaCampo(models.Model):
    """Cuánto dijo el modelo que confiaba en un campo de un borrador.

    Es un modelo aparte y no un JSON dentro del borrador porque CU-05 paso 3 no
    pide solo *leer* la confianza: exige que el Administrador haga una acción
    afirmativa **sobre cada campo de confianza baja** antes de poder confirmar.
    Eso es un dato que se escribe, por campo — y meterlo en un JSON que además
    guarda otra cosa lo volvería un blob adentro de otro blob, imposible de
    consultar y fácil de pisar entero al escribir una sola casilla.
    """

    ALTA = "alta"
    MEDIA = "media"
    BAJA = "baja"

    NIVEL_CHOICES = [  # noqa: RUF012
        (ALTA, "Alta"),
        (MEDIA, "Media"),
        (BAJA, "Baja"),
    ]

    borrador = models.ForeignKey(
        BorradorProducto, on_delete=models.CASCADE, related_name="confianzas"
    )
    campo = models.CharField("campo", max_length=30)
    nivel = models.CharField("nivel", max_length=5, choices=NIVEL_CHOICES, default=BAJA)

    # La acción afirmativa de CU-05 paso 3. Solo tiene sentido sobre los de
    # confianza baja; en los demás queda en falso y nadie lo mira.
    revisado = models.BooleanField("revisado por el Administrador", default=False)

    class Meta:
        verbose_name = "confianza por campo"
        verbose_name_plural = "confianzas por campo"
        ordering = ["borrador", "campo"]
        constraints = [  # noqa: RUF012
            models.UniqueConstraint(
                fields=["borrador", "campo"],
                name="confianza_unica_por_campo_del_borrador",
            ),
        ]

    def __str__(self):
        return f"{self.campo}: {self.nivel}"

    @property
    def exige_revision(self):
        """Baja, y todavía sin la acción afirmativa del Administrador."""
        return self.nivel == self.BAJA and not self.revisado
