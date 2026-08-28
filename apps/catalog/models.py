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
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models.functions import Coalesce, Lower

from apps.core import cotizaciones

# Los importes nunca son negativos. El validador va en el modelo y no solo en el
# formulario: el formulario protege una pantalla, el modelo protege la tabla —y
# por acá van a entrar después el pipeline automatizado y los comandos.
NO_NEGATIVO = MinValueValidator(Decimal("0"))
POSITIVO = MinValueValidator(Decimal("0.01"))

# Marcador de las excepciones A2/A3: un producto se puede dar de alta sin
# portada, y la portada se adjunta después desde la edición de producto.
IMAGEN_PENDIENTE = "Imagen pendiente"


class Editorial(models.Model):
    """Quién publica el material."""

    nombre = models.CharField("nombre", max_length=120, unique=True)
    activa = models.BooleanField("activa", default=True)

    class Meta:
        verbose_name = "editorial"
        verbose_name_plural = "editoriales"
        ordering = ["nombre"]

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

    nombre = models.CharField("nombre", max_length=60, unique=True)
    activo = models.BooleanField("activo", default=True)
    orden = models.PositiveSmallIntegerField(
        "orden", default=0, help_text="Posición en los filtros. Menor va primero."
    )

    class Meta:
        verbose_name = "grupo de etiquetas"
        verbose_name_plural = "grupos de etiquetas"
        ordering = ["orden", "nombre"]

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
    """Qué clase de material editorial es: manga, cómic, artbook, novela ligera.

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

    nombre = models.CharField("nombre", max_length=60, unique=True)

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

    def __str__(self):
        return self.nombre


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

    nombre = models.CharField("nombre", max_length=60, unique=True)
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
    """Un artículo del catálogo.

    Por ahora solo cubre lo editorial (CU-01/CU-02). El material no editorial
    (CU-08, Módulo 02) entra sobre esta misma tabla cuando corresponda: por eso
    `tipo` ya contempla el valor, aunque este módulo no lo dé de alta.
    """

    # De dónde viene el producto y, sobre todo, **cómo se forma su precio**:
    # nacional lo toma de la tabla de referencia, importado lo calcula desde el
    # costo de origen con el CRE y el margen, y no editorial se carga a mano.
    # Se llama `origen` y no `tipo` porque `tipo` es la clase de material
    # (manga, cómic): son dos clasificaciones distintas y confundirlas en un
    # solo nombre fue el primer error de este modelo.
    NACIONAL = "nacional"
    IMPORTADO = "importado"
    NO_EDITORIAL = "no_editorial"

    ORIGEN_CHOICES = [  # noqa: RUF012
        (NACIONAL, "Editorial nacional"),
        (IMPORTADO, "Editorial importado"),
        (NO_EDITORIAL, "No editorial"),
    ]

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

    titulo = models.CharField("título", max_length=200)
    volumen = models.PositiveIntegerField("volumen")

    # El identificador global de la edición. Opcional porque no todo producto
    # tiene uno —el material no editorial de RF-05 no responde a estándares
    # editoriales— pero **único cuando está**: dos productos con el mismo ISBN
    # son el mismo producto cargado dos veces.
    #
    # Se guarda normalizado, sin guiones (ver `apps/catalog/isbn.py`). La
    # unicidad va como restricción parcial y no como `unique=True` a secas
    # porque el "sin ISBN" se representa con la cadena vacía —lo idiomático en
    # Django para un `CharField`— y un `unique` común haría chocar entre sí a
    # todos los productos que no lo tienen.
    isbn = models.CharField(
        "ISBN",
        max_length=13,
        blank=True,
        help_text="Sin guiones. Es el criterio más confiable para detectar un duplicado.",
    )
    editorial = models.ForeignKey(Editorial, on_delete=models.PROTECT, related_name="productos")
    tipo = models.ForeignKey(Tipo, on_delete=models.PROTECT, related_name="productos")

    # El tamaño del tomo. Opcional porque no todos los tipos lo usan y porque un
    # lote importado no lo declara: ahí el precio sale del costo de origen y no
    # de ninguna tabla.
    formato = models.ForeignKey(
        Formato, on_delete=models.PROTECT, null=True, blank=True, related_name="productos"
    )

    # Todo lo que describe al producto sin identificarlo ni fijar su precio:
    # franquicia, género, colección. Son varias y son opcionales — un producto
    # sin ninguna etiqueta es un producto completo, solo más difícil de
    # encontrar.
    etiquetas = models.ManyToManyField(
        Etiqueta, blank=True, related_name="productos", verbose_name="etiquetas"
    )

    # **No es una etiqueta, y la diferencia es la que ordena todo el modelo.**
    # Una etiqueta describe; esto *decide*: saca el producto del catálogo
    # público. Como etiqueta, la tienda tendría que preguntar
    # `etiquetas.filter(nombre="NSFW")` —una comparación contra una cadena
    # escrita a mano— y renombrarla rompería la tienda en silencio.
    solo_adultos = models.BooleanField(
        "solo para adultos",
        default=False,
        help_text="Se excluye del catálogo público.",
    )

    origen = models.CharField("origen", max_length=15, choices=ORIGEN_CHOICES)
    estado = models.CharField("estado", max_length=25, choices=ESTADO_CHOICES, default=ACTIVO)

    sinopsis = models.TextField("sinopsis", blank=True)
    autor = models.CharField("autor", max_length=200, blank=True)
    portada = models.ImageField("portada", upload_to="portadas/", blank=True)

    fecha_llegada = models.DateField("fecha de llegada", null=True, blank=True)
    stock = models.PositiveIntegerField("stock", default=0)

    # ------------------------------------------------------------------
    # Precios
    # ------------------------------------------------------------------

    precio = models.DecimalField(
        "precio de venta", max_digits=12, decimal_places=2, validators=[POSITIVO]
    )

    # Solo importados (RF-10): `precio × (1 + CRE)`, **antes** del margen. Se
    # almacena para poder recalcular el precio final ante un cambio de margen
    # (CU-13) sin volver a pedir los datos del lote. La relación es en un solo
    # sentido: el precio base nunca se deriva del final.
    precio_base = models.DecimalField(
        "precio base",
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[POSITIVO],
    )
    costo_origen = models.DecimalField(
        "costo base en origen",
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[POSITIVO],
    )

    # El precio lo fijó una persona a mano, así que ninguna propagación
    # automática lo pisa (CU-13). Vale para los dos orígenes: en importados lo
    # pide RF-10, y en nacionales es la misma decisión —si el Administrador
    # escribió un precio, sobrescribírselo le borra una decisión deliberada.
    precio_manual = models.BooleanField("precio fijado a mano", default=False)

    # El precio de un nacional no es una foto sino un vínculo (RF-11): al
    # cambiar el PVP de la combinación, CU-12 propaga a todos los productos
    # activos vinculados. Sin esta clave foránea no habría a quién propagarle.
    precio_referencia = models.ForeignKey(
        TablaPrecioReferencia,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="productos",
    )

    lote = models.ForeignKey(
        LoteAlta, on_delete=models.SET_NULL, null=True, blank=True, related_name="productos"
    )

    # De quién vino el material. Nulo en las altas manuales de CU-01/CU-02, que
    # no lo piden: lo completa la confirmación de borradores de CU-05, donde el
    # producto sí nace atado al proveedor que lo anunció.
    #
    # Se declara desde ahora aunque todavía nadie lo escriba, por el mismo
    # motivo que `precio_manual`: CU-20 exige que los productos conserven la
    # referencia al proveedor dado de baja y CU-21 muestra cuántos tiene cada
    # uno, así que sin esta columna esos dos casos de uso no se pueden cumplir.
    # `PROTECT` porque un proveedor con productos no se borra —se da de baja
    # lógica (CU-20)— y perder de quién vino un tomo rompería el historial que
    # esa misma baja promete conservar.
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
        constraints = [  # noqa: RUF012
            # La combinación que define un duplicado. Va también como
            # restricción de base y no solo como validación de formulario: dos
            # altas simultáneas del mismo título pasarían las dos validaciones y
            # crearían el duplicado igual.
            #
            # `Lower` sobre el título porque "Batman" y "batman" son el mismo
            # tomo, y una restricción sensible a mayúsculas no atajaría nada.
            #
            # `Coalesce` sobre el formato porque en SQL dos NULL no son iguales:
            # sin él, dos importados sin formato —que es lo normal— no chocarían
            # nunca entre sí y el mismo tomo entraría dos veces. El cero hace de
            # "sin formato" y es un identificador que ninguna fila real usa.
            models.UniqueConstraint(
                Lower("titulo"),
                "volumen",
                "tipo",
                Coalesce("formato", models.Value(0)),
                "editorial",
                name="producto_unico_por_titulo_volumen_tipo_formato_editorial",
            ),
            # La otra clave de unicidad, y la más confiable de las dos cuando
            # está: un ISBN identifica una edición y nada más. La condición la
            # limita a los productos que lo declaran, así que los que no lo
            # tienen —que se identifican por la restricción de arriba— no
            # chocan entre sí por compartir la cadena vacía.
            models.UniqueConstraint(
                fields=["isbn"],
                condition=~models.Q(isbn=""),
                name="producto_unico_por_isbn",
            ),
        ]

    def __str__(self):
        return f"{self.titulo} #{self.volumen}"

    @property
    def portada_pendiente(self):
        """A2: se dio de alta sin portada y hay que adjuntarla desde CU-09."""
        return not self.portada

    @property
    def es_importado(self):
        return self.origen == self.IMPORTADO

    @property
    def esta_en_pre_venta(self):
        return self.estado == self.PRE_VENTA
