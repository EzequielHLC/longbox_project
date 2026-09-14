from decimal import Decimal

from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.validators import MinValueValidator
from django.db import models


class RegistroAuditoriaError(Exception):
    """Se intentó modificar o borrar una entrada del log de auditoría."""


class ConfiguracionSistema(models.Model):
    """Los parámetros que el negocio ajusta sin tocar código.

    Es una tabla de **una sola fila**: el sistema tiene una configuración, no
    una lista de configuraciones. El identificador se fuerza en `save()` en vez
    de confiar en que nadie cree una segunda, porque si hubiera dos nadie sabría
    cuál rige y el precio de los importados dependería de cuál se leyó primero.

    Los valores nacen de los que estaban en `settings`, así estrenar la pantalla
    no cambia ningún cálculo. `settings` queda como semilla del primer arranque
    y deja de ser la fuente de verdad.
    """

    IDENTIFICADOR = 1

    # Se expresa como proporción y no como porcentaje: 0,40 es un 40%. Es lo que
    # multiplica al precio base, así que guardarlo en la forma en que se usa
    # evita dividir por cien en cada lectura y equivocarse una vez.
    margen_ganancia = models.DecimalField(
        "margen de ganancia global",
        max_digits=6,
        decimal_places=4,
        validators=[MinValueValidator(Decimal("0"))],
        help_text="Proporción sobre el precio base. 0,40 equivale a un 40 %.",
    )

    stock_inicial_por_defecto = models.PositiveIntegerField(
        "stock inicial por defecto",
        # Solo lo usan los borradores del procesamiento automático. El alta
        # manual nace en cero: el sistema no inventa unidades que nadie contó (A3).
        help_text="Unidades con las que nace un borrador que no declara stock.",
    )

    # ------------------------------------------------------------------
    # El modelo de lenguaje (CU-ALT-NOV)
    #
    # Vive acá y no en `settings` por el mismo motivo que el margen: es un
    # parámetro operativo que el negocio cambia sin tocar código. Pero además
    # por uno propio y más urgente — **el proyecto se demuestra desplegado.**
    # El modelo local corre en una máquina de escritorio que no viaja, así que
    # sin poder apuntar a un proveedor remoto desde la pantalla, la mitad del
    # sistema no se puede mostrar fuera de esa máquina.
    # ------------------------------------------------------------------

    LOCAL = "local"
    REMOTO = "remoto"

    # Sin nombrar proveedores. Los dos valores describen **dónde corre** el
    # modelo, que es lo que cambia el comportamiento del sistema; qué servidor o
    # qué empresa lo hospeda es un dato de la dirección, no del modo. Poner una
    # marca en un desplegable la convierte además en una recomendación que el
    # proyecto no tiene por qué hacer.
    MODO_LLM_CHOICES = [  # noqa: RUF012
        (LOCAL, "Local"),
        (REMOTO, "Remoto"),
    ]

    # No cambia lo que el sistema hace —la API es la misma, compatible con la de
    # OpenAI— pero sí lo que hay que mirar cuando algo falla: en local se revisa
    # si el servidor está levantado, y en remoto la credencial y el saldo. La
    # pantalla de diagnóstico usa esto para decir dónde buscar.
    llm_modo = models.CharField(
        "modo del modelo de lenguaje",
        max_length=10,
        choices=MODO_LLM_CHOICES,
        default=LOCAL,
    )

    llm_url = models.URLField(
        "dirección de la API",
        max_length=300,
        # Los tres valores por defecto son los del modelo local, que es con lo
        # que se desarrolla. No duplican a `settings`: son el valor con el que
        # nace la columna, y `obtener()` los pisa con los del entorno la
        # primera vez que crea la fila.
        default="http://127.0.0.1:1234/v1/chat/completions",
        help_text="La ruta de chat, compatible con la API de OpenAI.",
    )

    llm_modelo = models.CharField(
        "modelo",
        max_length=120,
        blank=True,
        help_text="Vacío usa el que el servidor tenga cargado. Los remotos exigen nombrarlo.",
    )

    # **Se guarda y no se muestra nunca.** Es una credencial, no un parámetro: la
    # pantalla la pide una vez y después solo enseña los últimos caracteres, lo
    # justo para reconocer cuál está puesta sin exponerla.
    #
    # Que viva en la base y no solo en el entorno es una decisión tomada a ojos
    # abiertos: rotar la clave sin acceso al servidor es lo que permite arreglar
    # una demostración a mitad de camino, y ese riesgo —no poder demostrar el
    # sistema— pesa más en este proyecto que el de tener el secreto en la base.
    # A cambio, nunca se devuelve al formulario y cada cambio queda auditado.
    llm_api_key = models.CharField("clave de la API", max_length=200, blank=True)

    llm_timeout = models.PositiveIntegerField(
        "tiempo de espera (segundos)",
        default=300,
        help_text="Un correo de cincuenta productos puede tardar minutos.",
    )

    llm_temperatura = models.DecimalField(
        "temperatura",
        max_digits=3,
        decimal_places=2,
        default=Decimal("0"),
        validators=[MinValueValidator(Decimal("0"))],
        help_text="Para extraer datos conviene dejarla en 0.",
    )

    actualizado_en = models.DateTimeField("última modificación", auto_now=True)
    actualizado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="configuraciones_editadas",
    )

    class Meta:
        verbose_name = "configuración del sistema"
        verbose_name_plural = "configuración del sistema"

    def __str__(self):
        return "Parámetros globales del sistema"

    def save(self, *args, **kwargs):
        self.pk = self.IDENTIFICADOR
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise RegistroAuditoriaError("La configuración del sistema no se borra, se edita.")

    @property
    def usa_modelo_remoto(self):
        return self.llm_modo == self.REMOTO

    @property
    def clave_enmascarada(self):
        """Lo justo para reconocer qué clave está puesta, sin exponerla.

        Se muestran los últimos cuatro caracteres porque es lo que alcanza para
        distinguir dos claves entre sí; los primeros no sirven —los proveedores
        usan prefijos iguales para todas— y mostrarlos enteros convertiría la
        pantalla de configuración en un lugar del que copiar el secreto.
        """
        if not self.llm_api_key:
            return ""
        return f"…{self.llm_api_key[-4:]}"

    @classmethod
    def obtener(cls):
        """La configuración vigente, creándola con los valores de `settings`.

        Se crea sola en la primera lectura para que el sistema funcione recién
        instalado, sin depender de que alguien se acuerde de entrar a la
        pantalla antes de dar de alta el primer lote.
        """
        configuracion, _ = cls.objects.get_or_create(
            pk=cls.IDENTIFICADOR,
            defaults={
                "margen_ganancia": settings.MARGEN_GANANCIA_GLOBAL,
                "stock_inicial_por_defecto": settings.STOCK_INICIAL_POR_DEFECTO,
                # `settings` sigue siendo la semilla del primer arranque, no la
                # fuente de verdad: el `.env` del despliegue decide con qué
                # arranca el sistema, y la pantalla lo cambia después sin
                # reiniciar nada.
                "llm_url": settings.LLM_URL,
                "llm_modelo": settings.LLM_MODELO,
                "llm_api_key": settings.LLM_API_KEY,
                "llm_timeout": settings.LLM_TIMEOUT,
                "llm_temperatura": settings.LLM_TEMPERATURA,
            },
        )
        return configuracion


class RegistroAuditoria(models.Model):
    """Bitácora de operaciones sensibles del sistema.

    Versión mínima para el Módulo 12 (autenticación). El CU-AUD-CON del módulo de
    Auditoría la va a ampliar con más acciones y con la vista de consulta.

    El log es *inmutable*: ningún rol, ni siquiera Administrador, puede editar
    o borrar una entrada. Eso se garantiza acá abajo, en el modelo, para que
    valga aunque alguien lo intente desde el admin o desde un shell.
    """

    INICIO_SESION = "inicio_sesion"
    CIERRE_SESION = "cierre_sesion"
    BLOQUEO_POR_INTENTOS = "bloqueo_por_intentos"
    CAMBIO_CONTRASENA = "cambio_contrasena"
    ALTA_USUARIO = "alta_usuario"
    MODIFICACION_USUARIO = "modificacion_usuario"
    BAJA_USUARIO = "baja_usuario"
    REACTIVACION_USUARIO = "reactivacion_usuario"
    REENVIO_ACTIVACION = "reenvio_activacion"
    ACTIVACION_CUENTA = "activacion_cuenta"
    ELIMINACION_PENDIENTE = "eliminacion_pendiente"
    REGISTRO_CLIENTE = "registro_cliente"
    ALTA_LOTE_EDITORIAL = "alta_lote_editorial"
    ALTA_PRODUCTO_NO_EDITORIAL = "alta_producto_no_editorial"
    MODIFICACION_PRODUCTO = "modificacion_producto"
    BAJA_PRODUCTO = "baja_producto"
    REACTIVACION_PRODUCTO = "reactivacion_producto"
    PARAMETRO_MODIFICADO = "parametro_modificado"
    ALTA_PROVEEDOR = "alta_proveedor"
    MODIFICACION_PROVEEDOR = "modificacion_proveedor"
    BAJA_PROVEEDOR = "baja_proveedor"
    REACTIVACION_PROVEEDOR = "reactivacion_proveedor"
    CORREO_DESCARTADO = "correo_descartado"
    BORRADORES_GENERADOS = "borradores_generados"
    BORRADOR_CONFIRMADO = "borrador_confirmado"
    BORRADOR_RECHAZADO = "borrador_rechazado"
    SESION_REVISION_CERRADA = "sesion_revision_cerrada"

    ACCION_CHOICES = [  # noqa: RUF012
        (INICIO_SESION, "Inicio de sesión"),
        (CIERRE_SESION, "Cierre de sesión"),
        (BLOQUEO_POR_INTENTOS, "Bloqueo por intentos fallidos"),
        (CAMBIO_CONTRASENA, "Cambio de contraseña"),
        (ALTA_USUARIO, "Alta de usuario del sistema"),
        (MODIFICACION_USUARIO, "Modificación de usuario del sistema"),
        (BAJA_USUARIO, "Baja de usuario del sistema"),
        (REACTIVACION_USUARIO, "Reactivación de usuario del sistema"),
        (REENVIO_ACTIVACION, "Reenvío del enlace de activación"),
        (ACTIVACION_CUENTA, "Activación de cuenta"),
        (ELIMINACION_PENDIENTE, "Eliminación de cuenta pendiente de activación"),
        (REGISTRO_CLIENTE, "Registro de cuenta de cliente"),
        (ALTA_LOTE_EDITORIAL, "Alta de lote de material editorial"),
        (ALTA_PRODUCTO_NO_EDITORIAL, "Alta de producto no editorial"),
        (MODIFICACION_PRODUCTO, "Modificación de producto"),
        (BAJA_PRODUCTO, "Baja de producto del catálogo"),
        (REACTIVACION_PRODUCTO, "Reactivación de producto"),
        (PARAMETRO_MODIFICADO, "Modificación de parámetros globales"),
        (ALTA_PROVEEDOR, "Alta de proveedor editorial"),
        (MODIFICACION_PROVEEDOR, "Modificación de proveedor editorial"),
        (BAJA_PROVEEDOR, "Baja de proveedor editorial"),
        (REACTIVACION_PROVEEDOR, "Reactivación de proveedor editorial"),
        (CORREO_DESCARTADO, "Descarte de un correo de proveedor"),
        (BORRADORES_GENERADOS, "Generación de borradores desde un correo"),
        (BORRADOR_CONFIRMADO, "Confirmación de un borrador de producto"),
        (BORRADOR_RECHAZADO, "Rechazo de un borrador de producto"),
        (SESION_REVISION_CERRADA, "Cierre de una sesión de revisión"),
    ]

    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="registros_auditoria",
    )
    # Se guarda desnormalizado para que la traza sobreviva a la baja del
    # usuario, y para poder registrar intentos con correos inexistentes.
    actor_email = models.CharField(max_length=254, blank=True)

    # Aquello *sobre lo que* se ejecutó la acción, cuando no es el propio actor.
    #
    # Arrancó siendo una clave foránea a `Usuario`, porque en el Módulo 13 el
    # Administrador opera sobre cuentas ajenas. El Módulo 01 audita altas de
    # lote, y los que vienen auditan pedidos, ventas y devoluciones: si cada
    # objetivo posible fuera una columna, la tabla terminaría con quince claves
    # foráneas nulas. Por eso el objetivo pasó a ser genérico —el tipo de objeto
    # y su clave— que es la forma en que Django resuelve exactamente esto.
    objetivo_tipo = models.ForeignKey(
        ContentType,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="registros_auditoria",
    )
    objetivo_pk = models.PositiveIntegerField(null=True, blank=True)
    objetivo = GenericForeignKey("objetivo_tipo", "objetivo_pk")

    # Se conserva desnormalizado por el mismo motivo que `actor_email`: cuando
    # el objetivo es una cuenta que después se elimina (la única eliminación
    # física del sistema), la traza tiene que seguir diciendo de quién era.
    objetivo_email = models.CharField(max_length=254, blank=True)

    accion = models.CharField(max_length=40, choices=ACCION_CHOICES)
    ip = models.GenericIPAddressField(null=True, blank=True)
    # Texto libre: en las modificaciones (CU-USR-MOD) guarda los valores anteriores
    # y los nuevos de cada campo, así que no entra en un largo fijo corto.
    detalle = models.TextField(blank=True)
    ocurrido_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "registro de auditoría"
        verbose_name_plural = "registros de auditoría"
        ordering = ["-ocurrido_en"]
        # "Todo lo que se hizo sobre este producto / esta cuenta / este lote" es
        # la consulta natural del historial, y sobre un objetivo genérico no hay
        # clave foránea que la indexe sola.
        indexes = [  # noqa: RUF012
            models.Index(fields=["objetivo_tipo", "objetivo_pk"]),
        ]

    def __str__(self):
        return f"{self.ocurrido_en:%Y-%m-%d %H:%M} · {self.accion} · {self.actor_email}"

    def save(self, *args, **kwargs):
        if self.pk is not None:
            raise RegistroAuditoriaError("El log de auditoría es inmutable: no se puede modificar.")
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise RegistroAuditoriaError("El log de auditoría es inmutable: no se puede borrar.")

    @classmethod
    def registrar(
        cls,
        accion,
        actor=None,
        actor_email="",
        ip=None,
        detalle="",
        objetivo=None,
        objetivo_email="",
    ):
        """Punto de entrada único para escribir en el log.

        `objetivo` acepta cualquier modelo, no solo cuentas: un `Usuario`, un
        `LoteAlta`, y lo que traigan los módulos siguientes. El correo se
        desnormaliza únicamente cuando el objetivo tiene uno —un lote no lo
        tiene— y por eso se pide con `getattr` y no directo.
        """
        return cls.objects.create(
            accion=accion,
            actor=actor,
            actor_email=actor_email or (actor.email if actor else ""),
            objetivo=objetivo,
            objetivo_email=objetivo_email or getattr(objetivo, "email", ""),
            ip=ip,
            detalle=detalle,
        )
