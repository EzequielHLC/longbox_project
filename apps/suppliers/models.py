"""Proveedores editoriales (CU-PRV-ALT a CU-PRV-CON) y la cola de sus correos.

El modelo existe por dos motivos distintos y conviene no confundirlos:

1. **Es una agenda de contactos comerciales.** Razón social, correo, teléfono:
   lo que hace falta para llamar a alguien y pedirle material.
2. **Es el filtro de remitentes válidos del pipeline automatizado de CU-ALT-NOV.**
   Un correo de novedades solo se procesa si su remitente coincide con un
   proveedor **activo y con el procesamiento habilitado**. Eso convierte a
   `correo_comercial` en algo más que un dato de contacto: es una credencial de
   confianza, y por eso la baja de CU-PRV-BAJ no es cosmética —saca el correo del
   filtro— y por eso el correo es único.
3. **Es la cabecera de los borradores que genere ese pipeline.** La editorial y
   el rubro no vienen en el correo, porque la comunicación es directa de la
   editorial a la comiquería y nadie escribe su propio nombre en su newsletter.
   Los aporta el proveedor y los heredan sus borradores, con el mismo patrón de
   cabecera/ítem del alta en lote de CU-ALT-NAC.

La segunda y la tercera son las que fijan casi todas las reglas de este archivo.

`CorreoProveedor`, al final, es la cola de aprobación por la que pasa todo lo
que llega antes de que el pipeline gaste un solo ciclo en procesarlo.
"""

import datetime

from django.conf import settings
from django.db import models
from django.db.models.functions import Lower
from django.utils import timezone


class ProveedorQuerySet(models.QuerySet):
    def activos(self):
        return self.filter(estado=Proveedor.ACTIVO)

    def con_novedades_habilitadas(self):
        """Los que además tienen prendido el procesamiento automático.

        Son dos condiciones y no una: la relación comercial puede estar viva y
        el procesamiento de sus correos apagado igual. Ver `procesa_novedades`.
        """
        return self.activos().filter(procesa_novedades=True)

    def remitente_valido(self, correo):
        """El proveedor habilitado dueño de ese correo, o `None`.

        Es el punto por el que CU-ALT-NOV decide si procesa un mensaje o lo saltea, y
        está acá y no en la tarea de fondo para que la regla viva junto al dato
        que la define: quien cambie el estado, el correo o la habilitación de un
        proveedor cambia el filtro de remitentes por el mismo acto, sin tocar el
        pipeline.

        La comparación **ignora mayúsculas**: la parte de dominio de una
        dirección no las distingue y ningún proveedor real las usa como
        distinción, así que un "Novedades@Editorial.com" en el encabezado de un
        correo tiene que encontrar al mismo proveedor que se cargó en minúscula.
        Comparar en crudo dejaría afuera mensajes legítimos, y el modo en que
        fallaría —silencio, sin error— es el peor de todos.
        """
        if not correo:
            return None
        habilitados = self.con_novedades_habilitadas()
        return habilitados.filter(correo_comercial__iexact=correo.strip()).first()


class Proveedor(models.Model):
    """Un proveedor editorial nacional o distribuidora (CU-PRV-ALT)."""

    ACTIVO = "activo"
    INACTIVO = "inactivo"

    ESTADO_CHOICES = [  # noqa: RUF012
        (ACTIVO, "Activo"),
        (INACTIVO, "Inactivo"),
    ]

    # Los dos obligatorios de CU-PRV-ALT paso 2.
    razon_social = models.CharField("razón social", max_length=200)
    correo_comercial = models.EmailField("correo comercial", max_length=254)

    # Los tres opcionales del mismo paso. Ninguno traba un alta.
    nombre_contacto = models.CharField("nombre de contacto", max_length=200, blank=True)
    telefono = models.CharField("teléfono", max_length=40, blank=True)
    notas = models.TextField("notas internas", blank=True)

    estado = models.CharField("estado", max_length=10, choices=ESTADO_CHOICES, default=ACTIVO)

    # ------------------------------------------------------------------
    # Procesamiento automático de novedades (CU-ALT-NOV)
    # ------------------------------------------------------------------

    # Separado del estado a propósito: "la relación comercial está viva" y "sus
    # correos se parsean solos" son dos cosas distintas y en la práctica se
    # separan enseguida. Un proveedor que manda las novedades en un formato que
    # el modelo lee mal, o que mezcla anuncios con promociones, se registra
    # igual —le seguís comprando y le seguís mandando pedidos— pero no conviene
    # que su casilla alimente el pipeline.
    #
    # Nace en `True` para que se siga cumpliendo literal la postcondición de
    # CU-PRV-ALT: el correo del proveedor recién dado de alta queda habilitado como
    # remitente válido sin que nadie tenga que acordarse de prenderlo.
    procesa_novedades = models.BooleanField(
        "procesa novedades automáticamente",
        default=True,
        help_text=(
            "Sus correos entran a la cola de procesamiento automático. "
            "Apagarlo no cambia el estado del proveedor."
        ),
    )

    # ------------------------------------------------------------------
    # Cabecera de los borradores que genere el pipeline
    #
    # Los correos de novedades no traen estos dos datos, y no por descuido:
    # la comunicación es directa de la editorial a la comiquería, así que la
    # editorial nunca escribe su propio nombre en su propio newsletter ni
    # aclara el rubro, porque publica siempre lo mismo. Y los dos son campos
    # bloqueantes en la revisión de CU-ALT-REV: sin esto, *todos* los borradores
    # nacerían trabados y revisarlos sería elegirle a cada uno la misma
    # editorial a mano — el trabajo que el pipeline venía a eliminar.
    #
    # No se le piden al LLM: se declaran acá una vez y los heredan todos sus
    # borradores, con el mismo patrón de cabecera/ítem del alta en lote.
    # ------------------------------------------------------------------

    # Vacío **significa** algo: que el proveedor no publica bajo una sola
    # editorial —una distribuidora, o un servicio conjunto de varias— y que
    # entonces sí hay que extraer la editorial de cada correo. Es el mismo
    # criterio con el que una cabecera de lote sin editorial significa "lote
    # mixto", y por eso la pantalla lo dice con todas las letras en vez de
    # dejar un desplegable vacío que se confunda con un dato sin cargar.
    editorial = models.ForeignKey(
        "catalog.Editorial",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="proveedores",
        verbose_name="editorial que publica",
        help_text=("Déjelo sin declarar si el proveedor trae varias editoriales."),
    )

    # El rubro con el que nacen sus borradores. Es un valor por defecto, no una
    # restricción: una editorial de manga que un día saque un artbook se
    # corrige en la revisión, sin tocar la ficha del proveedor.
    tipo_por_defecto = models.ForeignKey(
        "catalog.Tipo",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="proveedores",
        verbose_name="tipo de material habitual",
        help_text="Con qué rubro nacen sus borradores. Se puede corregir en la revisión.",
    )

    creado_en = models.DateTimeField("fecha de alta", auto_now_add=True)
    actualizado_en = models.DateTimeField("última modificación", auto_now=True)

    objects = ProveedorQuerySet.as_manager()

    class Meta:
        verbose_name = "proveedor"
        verbose_name_plural = "proveedores"
        # CU-PRV-CON paso 2: la vista por defecto es alfabética.
        ordering = ["razon_social"]
        constraints = [  # noqa: RUF012
            # Las dos unicidades que pide CU-PRV-ALT paso 4, y las dos sin distinguir
            # mayúsculas. "Editorial Ivrea" y "EDITORIAL IVREA" son el mismo
            # proveedor escrito distinto, y con dos filas la pantalla mostraría
            # dos agendas para el mismo interlocutor.
            #
            # En el correo la razón es más dura todavía: es el filtro de
            # remitentes de CU-ALT-NOV, y dos proveedores con el mismo correo en
            # distinta caja harían que qué proveedor "es" un mensaje dependiera
            # del orden de la consulta.
            models.UniqueConstraint(Lower("razon_social"), name="proveedor_unico_por_razon_social"),
            models.UniqueConstraint(
                Lower("correo_comercial"), name="proveedor_unico_por_correo_comercial"
            ),
        ]

    def __str__(self):
        return self.razon_social

    @property
    def esta_activo(self):
        return self.estado == self.ACTIVO

    @property
    def es_remitente_valido(self):
        """Si sus correos entran hoy al procesamiento automático.

        Las dos condiciones juntas, que es como las mira el pipeline. La ficha
        lo muestra así porque "activo" a secas ya no alcanza para responder por
        qué de este proveedor no llega nada.
        """
        return self.esta_activo and self.procesa_novedades

    @property
    def trae_varias_editoriales(self):
        """Distribuidora o servicio conjunto: la editorial sale de cada correo."""
        return self.editorial_id is None


class CorreoProveedorQuerySet(models.QuerySet):
    def pendientes(self):
        return self.filter(estado=CorreoProveedor.PENDIENTE)


class CorreoProveedor(models.Model):
    """Un correo de un proveedor, archivado y esperando una decisión.

    **Este modelo no está en la fuente**, y es la pieza que hace posible la
    aprobación humana. CU-ALT-NOV describe un ciclo que lee la casilla y parsea todo
    lo que encuentre de un remitente registrado; en la práctica por esa misma
    dirección llegan facturas, promociones y avisos de demora, así que
    auto-parsear todo genera borradores basura que alguien tiene que rechazar
    uno por uno más adelante: el trabajo no se elimina, se mueve. Ver la
    corrección 11 de `docs/correcciones-fuente.md`.

    Con esta cola de por medio, el correo llega, se archiva y **espera**. Nada
    se procesa sin una aprobación explícita, que es lo que evita gastar el
    modelo local en un saludo de fin de año.

    Y hay una razón más para que la cola viva en la base y no solo en la
    notificación: el aviso puede fallar —el servicio de mensajería se cae, el
    token vence— y en ese caso los correos tienen que seguir estando y poder
    resolverse desde el backoffice. La notificación es un atajo sobre esta
    tabla, nunca el único camino.
    """

    PENDIENTE = "pendiente"
    DESCARTADO = "descartado"
    EN_PROCESO = "en_proceso"
    PROCESADO = "procesado"
    FALLIDO = "fallido"

    # Los cinco se declaran completos desde el principio aunque hoy solo se
    # usen dos, con el mismo criterio que los estados de `Producto`: la
    # alternativa es migrar la tabla tres veces a medida que el pipeline crece.
    ESTADO_CHOICES = [  # noqa: RUF012
        (PENDIENTE, "Pendiente de aprobación"),
        (DESCARTADO, "Descartado"),
        (EN_PROCESO, "En proceso"),
        (PROCESADO, "Procesado"),
        (FALLIDO, "Falló el procesamiento"),
    ]

    # Los estados desde los que todavía se puede decidir algo.
    ESTADOS_ABIERTOS = (PENDIENTE,)

    proveedor = models.ForeignKey(
        Proveedor,
        on_delete=models.PROTECT,
        related_name="correos",
        verbose_name="proveedor",
    )

    # La clave de idempotencia. Un ciclo de lectura que se ejecuta dos veces
    # —porque se reintentó, o porque el correo quedó sin marcar en la casilla—
    # no puede duplicar la fila. El identificador lo pone el servidor que envía
    # y es único por mensaje, así que es la clave natural.
    message_id = models.CharField("identificador del mensaje", max_length=998, unique=True)

    # El remitente **tal como vino**, no el del proveedor: si el día de mañana
    # el proveedor cambia su correo, este archivo tiene que seguir diciendo
    # desde qué dirección llegó este mensaje en particular.
    remitente = models.EmailField("remitente", max_length=254)
    asunto = models.CharField("asunto", max_length=500, blank=True)

    # La del encabezado del correo. Puede faltar o venir ilegible, y en ese caso
    # el orden de la cola lo da `recibido_en`, que es un hecho nuestro.
    fecha = models.DateTimeField("fecha del correo", null=True, blank=True)

    # El original completo. CU-ALT-NOV pide archivarlo como respaldo, y además es lo
    # que permite volver a extraer el contenido si la extracción mejora, sin
    # depender de que el correo siga en la casilla.
    archivo = models.FileField("correo original", upload_to="correos/", blank=True)

    # El HTML del cuerpo y su versión con la tabla preservada. Se guardan los
    # dos: el primero para poder revisar qué llegó de verdad, el segundo porque
    # es exactamente lo que se le va a mandar al modelo, y tenerlo escrito hace
    # que el paso siguiente sea reproducible en vez de depender de volver a
    # parsear con el código de ese momento.
    html = models.TextField("cuerpo HTML", blank=True)
    contenido = models.TextField("contenido extraído", blank=True)

    # Resumen de las portadas embebidas: identificador, tipo y tamaño. Los bytes
    # no se copian acá —ya están en el archivo original— porque duplicarlos
    # engordaría la tabla sin agregar nada: se extraen cuando haya un borrador
    # al que asociarlas.
    imagenes = models.JSONField("imágenes embebidas", default=list, blank=True)

    # Lo que el modelo entendió del correo. Se guarda para poder **mirarlo antes
    # de que se convierta en borradores**: es la misma idea que muestra el
    # contenido extraído en la ficha, un paso más adelante. Sin esto, la única
    # forma de saber si la extracción salió bien sería revisar los borradores ya
    # creados, que es demasiado tarde.
    extraccion = models.JSONField("extracción del modelo", default=dict, blank=True)

    # Con qué versión del prompt se extrajo. Un resultado de marzo y otro de
    # junio no son comparables, y cuando algo salga raro la primera pregunta va
    # a ser con cuál se hizo.
    version_prompt = models.CharField("versión del prompt", max_length=10, blank=True)

    estado = models.CharField("estado", max_length=15, choices=ESTADO_CHOICES, default=PENDIENTE)
    # Por qué terminó así: el motivo del descarte, o el detalle del fallo.
    motivo = models.TextField("motivo", blank=True)

    recibido_en = models.DateTimeField("ingresado el", auto_now_add=True)
    resuelto_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="correos_de_proveedor_resueltos",
    )
    resuelto_en = models.DateTimeField("resuelto el", null=True, blank=True)

    objects = CorreoProveedorQuerySet.as_manager()

    class Meta:
        verbose_name = "correo de proveedor"
        verbose_name_plural = "correos de proveedores"
        # Lo último que llegó primero: la cola se mira para resolver lo nuevo.
        ordering = ["-recibido_en"]
        indexes = [  # noqa: RUF012
            # "Qué tengo pendiente" es la consulta de la pantalla, y se hace en
            # cada carga.
            models.Index(fields=["estado", "-recibido_en"]),
        ]

    def __str__(self):
        return f"{self.proveedor} · {self.asunto or 'sin asunto'}"

    @property
    def esta_abierto(self):
        """Todavía se puede decidir algo sobre él."""
        return self.estado in self.ESTADOS_ABIERTOS

    @property
    def cantidad_imagenes(self):
        return len(self.imagenes or [])

    @property
    def cids(self):
        """Los identificadores de las portadas que el correo trae de verdad.

        Es lo que le permite a la extracción descartar una portada inventada:
        sin esta comprobación, un identificador alucinado dejaría el borrador
        apuntando a una imagen que no existe.
        """
        return {imagen.get("cid") for imagen in (self.imagenes or []) if imagen.get("cid")}

    @property
    def productos_extraidos(self):
        """Lo que el modelo entendió, para la pantalla. Lista vacía si no corrió."""
        return (self.extraccion or {}).get("productos", [])

    @property
    def intencion(self):
        return (self.extraccion or {}).get("intencion", "")

    @property
    def demorados_extraidos(self):
        """Lo que un aviso de demora dice que se atrasa (B-04-010)."""
        return (self.extraccion or {}).get("demorados", [])

    @property
    def demorados_a_la_vista(self):
        """Lo mismo, con la fecha como fecha: la pantalla la muestra como todas (dd/mm/aaaa)."""
        vista = []
        for mencion in self.demorados_extraidos:
            try:
                fecha = datetime.date.fromisoformat(mencion.get("fecha") or "")
            except ValueError:
                fecha = None
            vista.append({**mencion, "fecha": fecha})
        return vista

    @property
    def es_aviso_de_demora(self):
        return self.estado == self.PROCESADO and self.intencion == "demora"

    @property
    def puede_descartarse(self):
        """Pendiente, o ya procesado sin ser de novedades (B-04-010).

        Un aviso de demora o una factura procesados no tienen borradores que
        perder: descartarlos después deja dicho que ya se atendieron. Uno de
        novedades no, porque sus borradores siguen en la revisión.
        """
        return self.estado == self.PENDIENTE or (
            self.estado == self.PROCESADO and self.intencion not in ("", "novedades")
        )


# ---------------------------------------------------------------------------
# El pedido a proveedor (plan 00 del circuito con los proveedores)
# ---------------------------------------------------------------------------


class PedidoProveedor(models.Model):
    """Lo que se le pidió a un proveedor y todavía puede llegar.

    **Nace sólo cuando el pedido sale** (decisión 1 del plan): el correo de
    `CO-074` exitoso, o el alta de un lote en pre-venta, cuyo pedido se hizo por
    fuera del sistema. Sus líneas pendientes son el **cupo** de la pre-venta: un
    producto se reserva contra lo que viene en camino, nunca contra lo que no se
    pidió. Su llegada se registra en «Pedidos por llegar».
    """

    REVISION = "revision"
    RESTOCK = "restock"
    LOTE = "lote"
    MANUAL = "manual"
    MIGRACION = "migracion"
    ORIGEN_CHOICES = [  # noqa: RUF012
        (REVISION, "Novedades revisadas"),
        (RESTOCK, "Restock"),
        (LOTE, "Alta de lote en pre-venta"),
        (MANUAL, "Pedido a mano"),
        (MIGRACION, "Pre-venta anterior al registro de pedidos"),
    ]

    ABIERTO = "abierto"
    CERRADO = "cerrado"
    ESTADO_CHOICES = [  # noqa: RUF012
        (ABIERTO, "Por llegar"),
        (CERRADO, "Cerrado"),
    ]

    proveedor = models.ForeignKey(
        Proveedor,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="pedidos",
        help_text="Vacío en un lote en pre-venta de una editorial sin proveedor cargado.",
    )
    origen = models.CharField("origen", max_length=12, choices=ORIGEN_CHOICES)
    estado = models.CharField("estado", max_length=10, choices=ESTADO_CHOICES, default=ABIERTO)
    fecha_estimada = models.DateField("llegada estimada", null=True, blank=True)
    creado_en = models.DateTimeField("pedido el", auto_now_add=True)
    creado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="pedidos_a_proveedor",
    )
    cerrado_en = models.DateTimeField("cerrado el", null=True, blank=True)
    # De dónde salió, para enlazarlo. Uno solo, según el origen.
    propuesta = models.ForeignKey(
        "restock.PropuestaRestock",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="pedidos",
    )
    sesion = models.ForeignKey(
        "catalog.SesionRevision",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="pedidos",
    )
    lote = models.ForeignKey(
        "catalog.LoteAlta",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="pedidos",
    )

    class Meta:
        verbose_name = "pedido a proveedor"
        verbose_name_plural = "pedidos a proveedores"
        ordering = ["-creado_en", "-pk"]

    def __str__(self):
        quien = self.proveedor.razon_social if self.proveedor else "sin proveedor"
        return f"Pedido #{self.pk} · {quien}"

    @property
    def nombre_proveedor(self):
        return self.proveedor.razon_social if self.proveedor else "Sin proveedor cargado"

    @property
    def unidades_pendientes(self):
        """Lo que todavía puede llegar, sumando sus líneas abiertas."""
        return sum(linea.pendiente for linea in self.lineas.all())

    @property
    def unidades_pedidas(self):
        return sum(linea.cantidad_pedida for linea in self.lineas.all())

    @property
    def unidades_recibidas(self):
        return sum(linea.cantidad_recibida for linea in self.lineas.all())

    # Las mismas palabras que «Pre-ventas por llegar» (`GrupoDeLlegada`): las dos
    # pantallas hablan de lo mismo visto desde dos lados.
    @property
    def dias_para(self):
        if self.estado != self.ABIERTO or self.fecha_estimada is None:
            return None
        return (self.fecha_estimada - timezone.localdate()).days

    @property
    def vencido(self):
        return self.dias_para is not None and self.dias_para < 0

    @property
    def cercano(self):
        """Lo atrasado y lo de la próxima semana se muestra abierto."""
        return self.dias_para is not None and self.dias_para <= 7

    @property
    def cuando(self):
        if self.estado != self.ABIERTO:
            return "Cerrado"
        dias = self.dias_para
        if dias is None:
            return "Sin fecha"
        if dias < 0:
            return f"Atrasado {-dias} día{'s' if dias != -1 else ''}"
        if dias == 0:
            return "Llega hoy"
        if dias == 1:
            return "Llega mañana"
        return f"Llega en {dias} días"


class LineaPedidoProveedor(models.Model):
    """Un producto del pedido: cuánto se pidió, cuánto llegó y si se sigue esperando.

    **Queda abierta mientras falte algo** (plan, decisión sobre las parciales): una
    llegada parcial suma lo recibido y deja el resto pendiente. Se cierra cuando
    llega todo —o más, que se acepta— o a mano, sin recibir, con motivo.
    """

    PENDIENTE = "pendiente"
    PARCIAL = "parcial"
    RECIBIDA = "recibida"
    SIN_RECIBIR = "sin_recibir"
    ESTADO_CHOICES = [  # noqa: RUF012
        (PENDIENTE, "Por llegar"),
        (PARCIAL, "Llegó una parte"),
        (RECIBIDA, "Recibida"),
        (SIN_RECIBIR, "Cerrada sin recibir"),
    ]
    ABIERTAS = (PENDIENTE, PARCIAL)

    pedido = models.ForeignKey(PedidoProveedor, on_delete=models.CASCADE, related_name="lineas")
    producto = models.ForeignKey(
        "catalog.Producto", on_delete=models.PROTECT, related_name="pedidos_a_proveedor"
    )
    cantidad_pedida = models.PositiveIntegerField("pedida")
    cantidad_recibida = models.PositiveIntegerField("recibida", default=0)
    estado = models.CharField("estado", max_length=12, choices=ESTADO_CHOICES, default=PENDIENTE)
    recibida_en = models.DateTimeField("última llegada", null=True, blank=True)
    motivo_cierre = models.TextField("motivo del cierre sin recibir", blank=True)

    class Meta:
        verbose_name = "línea de pedido a proveedor"
        verbose_name_plural = "líneas de pedidos a proveedores"
        ordering = ["pedido", "pk"]
        constraints = [  # noqa: RUF012
            # Cerrar sin recibir exige decir por qué (plan, como el descarte de CO-073).
            models.CheckConstraint(
                condition=~models.Q(estado="sin_recibir") | ~models.Q(motivo_cierre=""),
                name="linea_pedido_proveedor_cerrada_con_motivo",
            ),
            models.CheckConstraint(
                condition=models.Q(cantidad_pedida__gte=1),
                name="linea_pedido_proveedor_pide_algo",
            ),
        ]

    def __str__(self):
        return f"{self.producto} × {self.cantidad_pedida}"

    @property
    def pendiente(self):
        """Lo que todavía puede llegar. Cero en una línea cerrada."""
        if self.estado not in self.ABIERTAS:
            return 0
        return max(0, self.cantidad_pedida - self.cantidad_recibida)
