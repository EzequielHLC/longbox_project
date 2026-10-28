from datetime import time
from decimal import Decimal

from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from apps.core import colores


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

    # ------------------------------------------------------------------
    # Catálogo y pre-venta (CU-CFG-PAR; CO-011)
    # ------------------------------------------------------------------

    dias_aviso_preventa = models.PositiveIntegerField(
        "aviso previo de pre-venta (días)",
        default=2,
        help_text="Con cuántos días de anticipación se avisa la llegada de una pre-venta.",
    )

    # ------------------------------------------------------------------
    # Inventario y restock (CU-CFG-PAR; B-05-004)
    # ------------------------------------------------------------------

    cantidad_minima_restock = models.PositiveIntegerField(
        "cantidad mínima de pedido de restock",
        default=3,
        validators=[MinValueValidator(1)],
        help_text="Lo menos que se sugiere pedir de un producto.",
    )
    margen_stock_restock = models.PositiveIntegerField(
        "margen de stock mínimo",
        default=2,
        help_text="Entra en la propuesta todo producto con menos unidades que este margen.",
    )

    # ------------------------------------------------------------------
    # Seguridad (CU-CFG-PAR; CO-114; B-12-001, plan 00, A3)
    # ------------------------------------------------------------------

    expiracion_sesion_minutos = models.PositiveIntegerField(
        "expiración de la sesión por inactividad (minutos)",
        default=30,
        validators=[MinValueValidator(1)],
        help_text="Sin actividad durante este tiempo, la sesión se cierra.",
    )
    bloqueo_intentos_minutos = models.PositiveIntegerField(
        "bloqueo tras intentos fallidos (minutos)",
        default=15,
        validators=[MinValueValidator(1)],
        help_text="Cuánto dura el bloqueo después de 5 intentos fallidos seguidos.",
    )

    # ------------------------------------------------------------------
    # Proveedores (CU-CFG-PAR; CO-016, plan 00, A1)
    # ------------------------------------------------------------------

    # En minutos desde el 2026-10-27 (B-04-015): con el aviso por Telegram, leer la
    # casilla una vez por día no sirve; el documento la declaraba en horas.
    frecuencia_casilla_minutos = models.PositiveIntegerField(
        "frecuencia de monitoreo de la casilla (minutos)",
        default=5,
        validators=[MinValueValidator(1)],
        help_text="Cada cuántos minutos se lee la casilla de novedades.",
    )
    # Cuándo la leyó por última vez: el vigilante corre más seguido que eso.
    casilla_revisada_en = models.DateTimeField("casilla revisada el", null=True, blank=True)

    # ------------------------------------------------------------------
    # El bot de Telegram, etapa 3 (B-19-011)
    # ------------------------------------------------------------------

    hora_resumen = models.TimeField(
        "hora del resumen de la mañana",
        default=time(9, 0),
        help_text="A qué hora sale el resumen del día a los Administradores que lo eligieron.",
    )
    # El día que ya salió: el reloj por minuto lo mira para no mandarlo dos veces.
    resumen_enviado_el = models.DateField("resumen enviado el", null=True, blank=True)
    # Qué problema de salud se avisó y qué día (`{"disco": "2026-10-28"}`): uno por
    # día y por problema, mientras siga.
    salud_avisada = models.JSONField("problemas de salud avisados", default=dict, blank=True)

    # ------------------------------------------------------------------
    # Tienda (CU-CFG-PAR, sección Tienda; B-17-003)
    # ------------------------------------------------------------------

    intervalo_carrusel = models.PositiveIntegerField(
        "intervalo del carrusel (segundos)",
        default=10,
        validators=[MinValueValidator(1)],
        help_text="Cada cuántos segundos la portada pasa al banner siguiente.",
    )

    # ------------------------------------------------------------------
    # Logística (CU-CFG-PAR) y el costo de envío (B-07-032)
    # ------------------------------------------------------------------

    costo_envio = models.DecimalField(
        "costo de envío",
        max_digits=12,
        decimal_places=2,
        default=Decimal("8000"),
        validators=[MinValueValidator(Decimal("0"))],
        help_text="Lo que paga una compra online que no alcanza el envío gratuito.",
    )
    monto_minimo_envio_gratuito = models.DecimalField(
        "monto mínimo para envío gratuito",
        max_digits=12,
        decimal_places=2,
        default=Decimal("100000"),
        validators=[MinValueValidator(Decimal("0.01"))],
        help_text="Desde este subtotal de productos, el envío no se cobra.",
    )
    # B-08-004: corre desde que se registra la demora de la línea.
    ventana_decision_horas = models.PositiveIntegerField(
        "ventana de decisión ante demora (horas)",
        default=72,
        validators=[MinValueValidator(1)],
        help_text="Cuánto tiene el Cliente para elegir qué hacer con un artículo demorado.",
    )
    # Stock almacenado en local (RF-25, BR-09).
    plazo_retencion_meses = models.PositiveIntegerField(
        "plazo de retención en local (meses)",
        default=3,
        validators=[MinValueValidator(1)],
        help_text="Cuánto guarda el local un artículo a nombre del Cliente.",
    )
    dias_aviso_retencion = models.PositiveIntegerField(
        "aviso previo al vencimiento (días)",
        default=7,
        validators=[MinValueValidator(1)],
        help_text="Con cuántos días de anticipación se avisa al Cliente.",
    )

    # ------------------------------------------------------------------
    # Comercial (CU-CFG-PAR; CO-099)
    # ------------------------------------------------------------------

    # El piso es la ley (BR-14; Ley 24.240 art. 34), no una preferencia: vive
    # también como restricción de la base, para cualquier camino de escritura.
    PISO_LEGAL_DEVOLUCION = 10
    # Plan 00, C1: es el plazo del arrepentimiento (revocación de la venta a
    # distancia). La garantía por defectos tiene el suyo, más largo.
    plazo_devolucion_dias = models.PositiveIntegerField(
        "plazo de arrepentimiento (días)",
        default=PISO_LEGAL_DEVOLUCION,
        validators=[MinValueValidator(PISO_LEGAL_DEVOLUCION)],
        help_text="Desde el despacho o el retiro. El mínimo legal es de 10 días corridos.",
    )
    plazo_garantia_dias = models.PositiveIntegerField(
        "plazo de garantía (días)",
        default=90,
        validators=[MinValueValidator(PISO_LEGAL_DEVOLUCION)],
        help_text="Para reclamar un defecto de fabricación o un error de imprenta.",
    )
    # Plan 00 de tope de reservas: cuenta la línea del carrito más lo que el
    # Cliente ya tiene reservado de ese tomo en pedidos en curso.
    maximo_reserva_preventa = models.PositiveIntegerField(
        "máximo de unidades por reserva",
        default=5,
        validators=[MinValueValidator(1)],
        help_text="Cuántas unidades de una misma pre-venta puede reservar un Cliente en total.",
    )
    # Plan 00 del circuito con los proveedores, decisión 2: el cupo de una pre-venta es
    # lo pedido menos este margen, por fallados y cancelaciones del proveedor.
    margen_cupo_preventa = models.PositiveIntegerField(
        "margen del cupo de pre-venta (%)",
        default=10,
        validators=[MaxValueValidator(50)],
        help_text="Qué parte de lo pedido no se ofrece en pre-venta, por si llega menos.",
    )

    # ------------------------------------------------------------------
    # Fidelización (CU-CFG-PAR; RF-19)
    # ------------------------------------------------------------------

    # Dos parámetros independientes (B-10-004): lo que vale un punto al
    # canjearlo, y qué porcentaje de cada compra vuelve en puntos. Puntos
    # ganados = pagado en dinero × porcentaje ÷ valor del punto.
    equivalencia_puntos = models.DecimalField(
        "valor del punto",
        max_digits=10,
        decimal_places=2,
        default=Decimal("10"),
        validators=[MinValueValidator(Decimal("0.01"))],
        help_text="Lo que vale 1 punto al canjearlo.",
    )
    porcentaje_puntos = models.DecimalField(
        "reintegro en puntos",
        max_digits=5,
        decimal_places=2,
        default=Decimal("5"),
        validators=[MinValueValidator(Decimal("0.01")), MaxValueValidator(Decimal("100"))],
        help_text="Sobre lo pagado en dinero, sin el envío.",
    )
    caducidad_puntos_meses = models.PositiveIntegerField(
        "caducidad de puntos (meses)",
        default=12,
        validators=[MinValueValidator(1)],
        help_text="Cuánto dura un lote de puntos desde que se acredita.",
    )
    # Plan 10, segunda parte: a pedido del responsable, un aviso antes de que
    # venzan, «animando a la compra». La caducidad misma sigue avisándose.
    dias_aviso_caducidad_puntos = models.PositiveIntegerField(
        "aviso previo a la caducidad (días)",
        default=3,
        validators=[MinValueValidator(1)],
        help_text="Con cuántos días de anticipación se avisa que unos puntos están por vencer.",
    )

    # ------------------------------------------------------------------
    # Pasarela de pago (B-07-031)
    # ------------------------------------------------------------------

    PASARELA_PRUEBA = "prueba"
    PASARELA_MERCADOPAGO = "mercadopago"
    PASARELA_CHOICES = [  # noqa: RUF012
        (PASARELA_PRUEBA, "Pasarela de prueba"),
        (PASARELA_MERCADOPAGO, "MercadoPago"),
    ]
    pasarela = models.CharField(
        "pasarela de pago",
        max_length=15,
        choices=PASARELA_CHOICES,
        default=PASARELA_PRUEBA,
        help_text="La de prueba no mueve dinero real.",
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
        constraints = [  # noqa: RUF012
            models.CheckConstraint(
                condition=models.Q(plazo_devolucion_dias__gte=10),
                name="plazo_devolucion_piso_legal",
            ),
        ]

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
    o borrar una entrada. Eso se garantiza acá abajo, en el modelo y no en
    permisos de pantalla, para que valga por cualquier camino de escritura
    —una migración de datos, un `update()` de queryset, el shell—.

    `ALTA_ADMINISTRADOR_INICIAL` tiene acción propia y no comparte la de un alta
    común a propósito: es la única cuenta del sistema que nace sin que otra
    cuenta la haya creado, así que su entrada es la única con `actor` nulo en
    todo el módulo 13. Con acción propia se la encuentra; mezclada con las demás
    habría que buscarla por la ausencia de un dato.
    """

    INICIO_SESION = "inicio_sesion"
    CIERRE_SESION = "cierre_sesion"
    BLOQUEO_POR_INTENTOS = "bloqueo_por_intentos"
    CAMBIO_CONTRASENA = "cambio_contrasena"
    ALTA_USUARIO = "alta_usuario"
    ALTA_ADMINISTRADOR_INICIAL = "alta_administrador_inicial"
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
    # B-17-005: un catálogo no es un parámetro (`CO-130`), y el contenido de
    # la tienda no tenía ninguna acción aplicable.
    ALTA_CATALOGO = "alta_catalogo"
    MODIFICACION_CATALOGO = "modificacion_catalogo"
    BAJA_CATALOGO = "baja_catalogo"
    ALTA_PRECIO_REFERENCIA = "alta_precio_referencia"
    MODIFICACION_PRECIO_REFERENCIA = "modificacion_precio_referencia"
    BAJA_PRECIO_REFERENCIA = "baja_precio_referencia"
    PUBLICACION_FAQ = "publicacion_faq"
    MODIFICACION_IDENTIDAD_VISUAL = "modificacion_identidad_visual"
    ALTA_BANNER = "alta_banner"
    MODIFICACION_BANNER = "modificacion_banner"
    BAJA_BANNER = "baja_banner"
    EXPORTACION_INVENTARIO = "exportacion_inventario"
    EXPORTACION_AUDITORIA = "exportacion_auditoria"
    ALTA_OFERTA = "alta_oferta"
    MODIFICACION_OFERTA = "modificacion_oferta"
    BAJA_OFERTA = "baja_oferta"
    VENCIMIENTO_AUTOMATICO_OFERTA = "vencimiento_automatico_oferta"
    MODIFICACION_FILAS_PORTADA = "modificacion_filas_portada"
    # Plan 07, sexta parte: la compra online (CU-TDA-CMP, CU-TDA-INV).
    COMPRA_ONLINE = "compra_online"
    PAGO_RECHAZADO = "pago_rechazado"
    INCIDENTE_COMPRA = "incidente_compra"
    # Plan 08: el avance manual del pedido (CU-PED-EST).
    AVANCE_ESTADO_PEDIDO = "avance_estado_pedido"
    # Plan 11, segunda parte: el Cliente edita su cuenta (CU-CLI-DAT).
    MODIFICACION_DATOS_CLIENTE = "modificacion_datos_cliente"
    CAMBIO_CORREO = "cambio_correo"
    # Planes 06 y 14: el mostrador y la caja.
    VENTA_PRESENCIAL = "venta_presencial"
    CIERRE_CAJA = "cierre_caja"
    EXPORTACION_CIERRE = "exportacion_cierre"
    # Plan 01, ciclo de la pre-venta, y plan 08, segunda parte.
    CONFIRMACION_INGRESO = "confirmacion_ingreso"
    TRANSICION_PEDIDO = "transicion_pedido"
    INCIDENTE_PREVENTA = "incidente_preventa"
    REGISTRO_DEMORA = "registro_demora"
    ESCALADO_PREVENTA = "escalado_preventa"
    CANCELACION_PREVENTA_LOTE = "cancelacion_preventa_lote"
    DECISION_DEMORA = "decision_demora"
    VENCIMIENTO_VENTANA = "vencimiento_ventana"
    COMPENSACION_RETRASO = "compensacion_retraso"
    CANCELACION_ARTICULO_DEMORADO = "cancelacion_articulo_demorado"
    # Plan 18: el stock almacenado en local.
    INGRESO_STOCK_ALMACENADO = "ingreso_stock_almacenado"
    SOLICITUD_DESPACHO = "solicitud_despacho"
    DESPACHO_STOCK_ALMACENADO = "despacho_stock_almacenado"
    RETIRO_EN_LOCAL = "retiro_en_local"
    PLAZO_RETENCION = "plazo_retencion"
    VENCIMIENTO_RETENCION = "vencimiento_retencion"
    # Plan 05: restock.
    PROPUESTA_RESTOCK = "propuesta_restock"
    DESPACHO_RESTOCK = "despacho_restock"
    DESCARTE_RESTOCK = "descarte_restock"
    CIERRE_PROPUESTA_RESTOCK = "cierre_propuesta_restock"
    PEDIDO_A_PROVEEDOR = "pedido_a_proveedor"
    # Plan 00 del circuito con los proveedores: la llegada de lo pedido.
    LLEGADA_PEDIDO = "llegada_pedido"
    CIERRE_SIN_RECIBIR = "cierre_sin_recibir"
    # Módulo 19 · Perfil y avisos (plan 00 de Telegram).
    VINCULO_TELEGRAM = "vinculo_telegram"
    DESVINCULO_TELEGRAM = "desvinculo_telegram"
    CANALES_DE_AVISO = "canales_de_aviso"
    NOTIFICACION_REPOSICION = "notificacion_reposicion"
    NOTIFICACION_FALLIDA = "notificacion_fallida"
    # Plan 09: devoluciones.
    APERTURA_DEVOLUCION = "apertura_devolucion"
    DEVOLUCION_CON_CAMBIO = "devolucion_con_cambio"
    DEVOLUCION_CON_REEMBOLSO = "devolucion_con_reembolso"
    RECHAZO_DEVOLUCION = "rechazo_devolucion"
    DEVOLUCION_REEMBOLSO_MEDIO = "devolucion_reembolso_medio"
    # Plan 10, segunda parte: caducidad y ajuste manual.
    CADUCIDAD_PUNTOS = "caducidad_puntos"
    INCIDENTE_CADUCIDAD = "incidente_caducidad"
    AJUSTE_PUNTOS = "ajuste_puntos"
    # CU-CFG-LLM: el diagnóstico (CO-149) y la comprobación de disponibilidad (CO-150).
    DIAGNOSTICO_LLM = "diagnostico_llm"
    DISPONIBILIDAD_LLM = "disponibilidad_llm"
    # CU-CLI-BAJ (CO-113).
    BAJA_CUENTA_CLIENTE = "baja_cuenta_cliente"
    # CU-REP-GEN A1 (CO-128).
    EXPORTACION_REPORTE = "exportacion_reporte"

    ACCION_CHOICES = [  # noqa: RUF012
        (INICIO_SESION, "Inicio de sesión"),
        (CIERRE_SESION, "Cierre de sesión"),
        (BLOQUEO_POR_INTENTOS, "Bloqueo por intentos fallidos"),
        (CAMBIO_CONTRASENA, "Cambio de contraseña"),
        (ALTA_ADMINISTRADOR_INICIAL, "Alta del primer Administrador de la instalación"),
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
        (ALTA_CATALOGO, "Alta de catálogo"),
        (MODIFICACION_CATALOGO, "Modificación de catálogo"),
        (BAJA_CATALOGO, "Baja de catálogo"),
        (ALTA_PRECIO_REFERENCIA, "Alta de precio de referencia"),
        (MODIFICACION_PRECIO_REFERENCIA, "Modificación de precio de referencia"),
        (BAJA_PRECIO_REFERENCIA, "Baja de precio de referencia"),
        (PUBLICACION_FAQ, "Publicación de FAQ"),
        (MODIFICACION_IDENTIDAD_VISUAL, "Modificación de identidad visual"),
        (ALTA_BANNER, "Alta de banner"),
        (MODIFICACION_BANNER, "Modificación de banner"),
        (BAJA_BANNER, "Baja de banner"),
        (EXPORTACION_INVENTARIO, "Exportación de inventario"),
        (EXPORTACION_AUDITORIA, "Exportación del log de auditoría"),
        (ALTA_OFERTA, "Alta de oferta"),
        (MODIFICACION_OFERTA, "Modificación de oferta"),
        (BAJA_OFERTA, "Baja de oferta"),
        (VENCIMIENTO_AUTOMATICO_OFERTA, "Vencimiento automático de oferta"),
        (MODIFICACION_FILAS_PORTADA, "Modificación de las filas de la portada"),
        (COMPRA_ONLINE, "Compra online"),
        (PAGO_RECHAZADO, "Pago rechazado por la pasarela"),
        (INCIDENTE_COMPRA, "Compra fallida con reembolso"),
        (AVANCE_ESTADO_PEDIDO, "Avance de estado de pedido"),
        (MODIFICACION_DATOS_CLIENTE, "Modificación de datos personales del Cliente"),
        (CAMBIO_CORREO, "Cambio de correo electrónico"),
        (VENTA_PRESENCIAL, "Venta presencial"),
        (CIERRE_CAJA, "Cierre de caja"),
        (EXPORTACION_CIERRE, "Exportación de cierre de caja"),
        (CONFIRMACION_INGRESO, "Confirmación de ingreso de pre-venta"),
        (TRANSICION_PEDIDO, "Transición de pedido"),
        (INCIDENTE_PREVENTA, "Fallo en una operación de pre-venta"),
        (REGISTRO_DEMORA, "Registro de demora en artículo de pre-venta"),
        (ESCALADO_PREVENTA, "Escalado por inacción sobre pre-venta"),
        (CANCELACION_PREVENTA_LOTE, "Cancelación de pre-ventas en lote"),
        (DECISION_DEMORA, "Decisión ante artículo demorado"),
        (VENCIMIENTO_VENTANA, "Vencimiento de la ventana de decisión"),
        (COMPENSACION_RETRASO, "Compensación por retraso"),
        (CANCELACION_ARTICULO_DEMORADO, "Cancelación de artículo demorado"),
        (INGRESO_STOCK_ALMACENADO, "Ingreso a stock almacenado"),
        (SOLICITUD_DESPACHO, "Solicitud de despacho de stock almacenado"),
        (DESPACHO_STOCK_ALMACENADO, "Despacho de stock almacenado"),
        (RETIRO_EN_LOCAL, "Retiro en local de stock almacenado"),
        (PLAZO_RETENCION, "Modificación de plazo de retención"),
        (VENCIMIENTO_RETENCION, "Vencimiento de retención"),
        (PROPUESTA_RESTOCK, "Generación de propuesta de restock"),
        (DESPACHO_RESTOCK, "Despacho de restock a proveedor"),
        (DESCARTE_RESTOCK, "Descarte de proveedor en propuesta de restock"),
        (CIERRE_PROPUESTA_RESTOCK, "Cierre de propuesta de restock"),
        (PEDIDO_A_PROVEEDOR, "Correo de pedido a proveedor"),
        (LLEGADA_PEDIDO, "Llegada de un pedido a proveedor"),
        (CIERRE_SIN_RECIBIR, "Línea de pedido cerrada sin recibir"),
        (VINCULO_TELEGRAM, "Vínculo con Telegram"),
        (DESVINCULO_TELEGRAM, "Desvínculo de Telegram"),
        (CANALES_DE_AVISO, "Cambio de los canales de aviso"),
        (NOTIFICACION_REPOSICION, "Notificación de reposición"),
        (NOTIFICACION_FALLIDA, "Notificación fallida"),
        (APERTURA_DEVOLUCION, "Apertura de caso de devolución"),
        (DEVOLUCION_CON_CAMBIO, "Resolución de devolución con cambio"),
        (DEVOLUCION_CON_REEMBOLSO, "Resolución de devolución con reembolso en puntos"),
        (RECHAZO_DEVOLUCION, "Rechazo de caso de devolución"),
        (DEVOLUCION_REEMBOLSO_MEDIO, "Resolución de devolución con reembolso por el medio de pago"),
        (CADUCIDAD_PUNTOS, "Caducidad de lote de puntos"),
        (INCIDENTE_CADUCIDAD, "Fallo en la caducidad de un lote de puntos"),
        (AJUSTE_PUNTOS, "Ajuste manual de puntos"),
        (DIAGNOSTICO_LLM, "Diagnóstico del modelo de lenguaje"),
        (DISPONIBILIDAD_LLM, "Comprobación de disponibilidad del modelo de lenguaje"),
        (BAJA_CUENTA_CLIENTE, "Baja de cuenta de cliente"),
        (EXPORTACION_REPORTE, "Exportación de reporte"),
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


class InstanciaUnica(models.Model):
    """P-14: conceptos de los que existe exactamente uno.

    La clave se fuerza en cada guardado, igual que en `ConfiguracionSistema`:
    si hubiera dos, nadie sabría cuál rige.
    """

    IDENTIFICADOR = 1

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        self.pk = self.IDENTIFICADOR
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise RegistroAuditoriaError(f"{self._meta.verbose_name} no se borra, se edita.")

    @classmethod
    def obtener(cls):
        instancia, _ = cls.objects.get_or_create(pk=cls.IDENTIFICADOR)
        return instancia


class ContenidoFAQ(InstanciaUnica):
    """La sección de preguntas frecuentes de la tienda (CU-CFG-FAQ, I-14).

    Publicar reemplaza, no agrega. Se escribe en Markdown y se publica sin HTML
    crudo (C-16): el Markdown escrito por el Administrador se muestra en una
    pantalla pública, y el HTML crudo sería una vía para inyectar guiones.
    """

    contenido = models.TextField("contenido", blank=True)
    actualizado_en = models.DateTimeField("actualizado en", null=True, blank=True)

    class Meta:
        verbose_name = "contenido de la FAQ"
        verbose_name_plural = "contenido de la FAQ"

    def __str__(self):
        return "Preguntas frecuentes"


class IdentidadVisual(InstanciaUnica):
    """Nombre, contacto y apariencia de la tienda pública (CU-CFG-VIS).

    Los colores pintan sólo las cuatro variables `--tienda-*` del modo
    público (C-07, `identidad_visual.md`); el backoffice no las lee nunca. Los
    valores iniciales son los de Viñeta Nocturna (`TOKENS_VISUALES.md`,
    Identidad configurable). El fondo puede ser una imagen (C-07).
    """

    COLOR = "color"
    IMAGEN = "imagen"
    TIPOS_DE_FONDO = [(COLOR, "Color sólido"), (IMAGEN, "Imagen")]  # noqa: RUF012

    nombre_tienda = models.CharField("nombre de la tienda", max_length=80, default="Longbox")
    correo_contacto = models.EmailField("correo de contacto", blank=True)
    telefono = models.CharField("teléfono o WhatsApp", max_length=40, blank=True)
    instagram = models.URLField("Instagram", blank=True)
    facebook = models.URLField("Facebook", blank=True)
    tiktok = models.URLField("TikTok", blank=True)
    x_twitter = models.URLField("X / Twitter", blank=True)

    logo = models.ImageField("logo", upload_to="identidad/", blank=True)
    color_primario = models.CharField("color primario", max_length=7, default="#FF6A13")
    color_secundario = models.CharField("color secundario", max_length=7, default="#9A9AA5")
    color_acento = models.CharField("color de acento", max_length=7, default="#FF6A13")
    tipo_fondo = models.CharField("fondo", max_length=10, choices=TIPOS_DE_FONDO, default=COLOR)
    color_fondo = models.CharField("color de fondo", max_length=7, default="#0A0A0C")
    imagen_fondo = models.ImageField("imagen de fondo", upload_to="identidad/", blank=True)
    # El mapa de colores (plan 00 de interfaz, cuarta parte, B; B-17-019): qué
    # color de la paleta lleva cada parte de la tienda. Los roles, sus opciones
    # válidas y lo que pinta cada uno están en `apps/core/colores.py`.
    color_rol_boton = models.CharField(
        "botón principal", max_length=10, choices=colores.OPCIONES, default=colores.PRIMARIO
    )
    color_rol_enlaces = models.CharField(
        "botones secundarios y enlaces",
        max_length=10,
        choices=colores.OPCIONES,
        default=colores.ACENTO,
    )
    color_rol_precios = models.CharField(
        "precios", max_length=10, choices=colores.OPCIONES, default=colores.NEUTRO
    )
    color_rol_marcas = models.CharField(
        "rótulos y carteles", max_length=10, choices=colores.OPCIONES, default=colores.ACENTO
    )
    color_rol_titulos = models.CharField(
        "títulos de sección", max_length=10, choices=colores.OPCIONES, default=colores.ACENTO
    )
    color_rol_tarjetas = models.CharField(
        "tarjetas e imágenes", max_length=10, choices=colores.OPCIONES, default=colores.ACENTO
    )
    color_rol_encabezado = models.CharField(
        "encabezado y pie", max_length=10, choices=colores.OPCIONES, default=colores.FONDO
    )
    # La que acompaña al formulario en las pantallas de acceso (B-07-020). Sin
    # ella, el logo; sin logo, el nombre de la tienda en grande.
    imagen_acceso = models.ImageField("imagen del ingreso", upload_to="identidad/", blank=True)

    # Los textos de la portada y del pie (B-17-015). Son anuncios del
    # escaparate: los decide el negocio, no el código.
    descripcion_tienda = models.CharField(
        "descripción de la tienda",
        max_length=200,
        default="Comiquería. Historietas, manga, libros y coleccionables.",
        help_text="Se lee en el pie de todas las pantallas de la tienda.",
    )
    portada_antetitulo = models.CharField(
        "antetítulo de la portada", max_length=60, default="Nuevo en tienda"
    )
    portada_titulo = models.CharField(
        "título de la portada",
        max_length=60,
        default="Historietas de noche",
        help_text="El título grande de la portada. Corto se lee mejor.",
    )
    portada_bajada = models.CharField(
        "bajada de la portada",
        max_length=200,
        default=(
            "Manga, cómic, libros y coleccionables. "
            "Lo que llega, lo que se viene y lo que se agota."
        ),
    )
    ticker_mensajes = models.TextField(
        "mensajes del ticker",
        blank=True,
        help_text=(
            "Un mensaje por renglón. Vacío, la franja muestra los títulos de lo último que llegó."
        ),
    )

    actualizado_en = models.DateTimeField("actualizada en", null=True, blank=True)
    actualizado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="identidades_editadas",
    )

    class Meta:
        verbose_name = "identidad visual"
        verbose_name_plural = "identidad visual"

    def __str__(self):
        return self.nombre_tienda

    @property
    def configurada(self):
        """Si el Administrador la guardó alguna vez. Hasta entonces rigen los tokens."""
        return self.actualizado_en is not None

    @property
    def version(self):
        """Cambia con cada guardado, para que el navegador no use la hoja vieja."""
        return int(self.actualizado_en.timestamp()) if self.actualizado_en else 0

    @property
    def sobre_primario(self):
        """El texto sobre el primario: noche o blanco, el que dé más contraste.

        No es configurable (`TOKENS_VISUALES.md`): el sistema lo elige.
        """
        from apps.core.contraste import mas_legible

        return mas_legible(self.color_primario, ("#0A0A0C", "#FFFFFF"))

    @property
    def mensajes_del_ticker(self):
        return [linea.strip() for linea in self.ticker_mensajes.splitlines() if linea.strip()]

    @property
    def redes(self):
        nombres = (
            ("Instagram", self.instagram),
            ("Facebook", self.facebook),
            ("TikTok", self.tiktok),
            ("X", self.x_twitter),
        )
        return [(nombre, url) for nombre, url in nombres if url]


class Banner(models.Model):
    """Una imagen de la galería de la portada (CU-CFG-BNA a BNC).

    La posición se guarda desde 0 y se muestra desde 1 (plan 17, ambigüedad 7).
    Las posiciones son siempre consecutivas: cada alta, cambio de lugar y baja
    las reajusta en la misma transacción.
    """

    imagen = models.ImageField("imagen", upload_to="banners/")
    posicion = models.PositiveIntegerField("posición")
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "banner"
        verbose_name_plural = "banners"
        ordering = ["posicion"]

    def __str__(self):
        return f"Banner {self.posicion + 1}"

    @property
    def numero(self):
        return self.posicion + 1


class FilaPortada(models.Model):
    """Una fila de productos de la portada de la tienda (plan 07, tercera parte; B-07-009).

    Sale de una etiqueta («Shonen») o de un grupo de etiquetas entero
    («Demografía»): nunca de las dos. La fila se recorre de costado y muestra los
    productos visibles en la tienda más nuevos de ese origen.
    """

    titulo = models.CharField(
        "título",
        max_length=80,
        blank=True,
        help_text="Vacío, usa el nombre de la etiqueta o del grupo.",
    )
    etiqueta = models.ForeignKey(
        "catalog.Etiqueta",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="filas_portada",
    )
    grupo = models.ForeignKey(
        "catalog.GrupoEtiqueta",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="filas_portada",
    )
    # Abre la fila en la portada, en una tarjeta con su título (B-07-010).
    # Llega ya procesada por RNF-05, como toda imagen del sistema.
    imagen = models.ImageField("imagen", upload_to="filas/", blank=True)
    orden = models.PositiveIntegerField("orden", default=0)
    activa = models.BooleanField("activa", default=True)

    class Meta:
        verbose_name = "fila de la portada"
        verbose_name_plural = "filas de la portada"
        ordering = ["orden", "pk"]  # noqa: RUF012
        constraints = [  # noqa: RUF012
            models.CheckConstraint(
                condition=(
                    models.Q(etiqueta__isnull=False, grupo__isnull=True)
                    | models.Q(etiqueta__isnull=True, grupo__isnull=False)
                ),
                name="fila_portada_de_etiqueta_o_de_grupo",
            ),
        ]

    def __str__(self):
        return self.titulo_visible

    @property
    def origen(self):
        return self.etiqueta or self.grupo

    @property
    def titulo_visible(self):
        return self.titulo or (self.origen.nombre if self.origen else "")

    @property
    def disponible(self):
        """Sin la etiqueta o el grupo dados de baja (decisión 5)."""
        if self.etiqueta_id:
            return self.etiqueta.activa and self.etiqueta.grupo.activo
        return self.grupo.activo
