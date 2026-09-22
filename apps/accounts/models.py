from datetime import timedelta

from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.db import models
from django.utils import timezone

# La comiquería está en Posadas y vende dentro del país: el visitante no
# debería tener que elegir "Argentina" en un desplegable de 200 países para
# cargar su teléfono. Se muestra editable por si alguien llama desde afuera.
PAIS_TELEFONO_PREDETERMINADO = "+54"

# El teléfono se guarda en tres partes y cada una acepta únicamente lo suyo.
# Un solo campo de texto libre deja pasar "-1", "no tengo" o el mismo número
# escrito de cinco formas distintas, y después no hay manera de llamar a nadie.
validar_codigo_pais = RegexValidator(
    r"^\+\d{1,3}$",
    "El código de país se escribe con un signo + y de uno a tres dígitos (por ejemplo, +54).",
)
validar_codigo_area = RegexValidator(
    r"^\d{2,5}$",
    "El código de área se compone de 2 a 5 dígitos, sin el 0 inicial (por ejemplo, 376).",
)
validar_numero_telefono = RegexValidator(
    r"^\d{6,10}$",
    "El número se compone de 6 a 10 dígitos, sin espacios ni guiones y sin el 15 inicial.",
)

# Código Postal Argentino: acepta tanto el formato viejo de 4 dígitos (3300)
# como el CPA actual, que le suma una letra de provincia adelante y tres de
# manzana atrás (N3300ABC).
validar_codigo_postal = RegexValidator(
    r"^[A-Za-z]?\d{4}[A-Za-z]{0,3}$",
    "El código postal debe tener el formato 3300 o N3300ABC.",
)

# La letra inicial del CPA identifica la provincia. Esto **no** es un catálogo
# de datos que haya que ir a buscar a ningún servidor —para eso está
# `apps/core/georef.py`—, es parte de la especificación del formato, del mismo
# modo que saber que un correo electrónico lleva una arroba. No cambia salvo
# que se cree una provincia nueva.
#
# Sirve para una validación cruzada que ninguna API gratuita ofrece: detectar
# que alguien escribió "N3300ABC" y eligió Corrientes.
LETRA_CPA_POR_PROVINCIA = {  # noqa: RUF012
    "A": "Salta",
    "B": "Buenos Aires",
    "C": "Ciudad Autónoma de Buenos Aires",
    "D": "San Luis",
    "E": "Entre Ríos",
    "F": "La Rioja",
    "G": "Santiago del Estero",
    "H": "Chaco",
    "J": "San Juan",
    "K": "Catamarca",
    "L": "La Pampa",
    "M": "Mendoza",
    "N": "Misiones",
    "P": "Formosa",
    "Q": "Neuquén",
    "R": "Río Negro",
    "S": "Santa Fe",
    "T": "Tucumán",
    "U": "Chubut",
    "V": "Tierra del Fuego, Antártida e Islas del Atlántico Sur",
    "W": "Corrientes",
    "X": "Córdoba",
    "Y": "Jujuy",
    "Z": "Santa Cruz",
}


def provincia_del_codigo_postal(codigo_postal):
    """La provincia que declara la letra inicial de un CPA, o `None`.

    Devuelve `None` para el formato viejo de cuatro dígitos (no lleva letra) y
    para cualquier cosa que no se reconozca: la validación cruzada solo opina
    cuando tiene con qué, nunca rechaza por las dudas.
    """
    if not codigo_postal:
        return None
    primera = codigo_postal[0].upper()
    if not primera.isalpha():
        return None
    return LETRA_CPA_POR_PROVINCIA.get(primera)


class Usuario(AbstractUser):
    CLIENTE = "cliente"
    CAJERO = "cajero"
    ADMINISTRADOR = "administrador"

    ROL_CHOICES = [  # noqa: RUF012
        (CLIENTE, "Cliente"),
        (CAJERO, "Cajero"),
        (ADMINISTRADOR, "Administrador"),
    ]

    # Roles de personal: los únicos que se dan de alta desde el backoffice
    # (CU-USR-ALT). El alta de una cuenta de Cliente es el CU-CLI-ALT, otro flujo.
    ROLES_DE_PERSONAL = (CAJERO, ADMINISTRADOR)

    PENDIENTE_ACTIVACION = "pendiente_activacion"
    ACTIVO = "activo"
    INACTIVO = "inactivo"

    ESTADO_CHOICES = [  # noqa: RUF012
        (PENDIENTE_ACTIVACION, "Pendiente de activación"),
        (ACTIVO, "Activo"),
        (INACTIVO, "Inactivo"),
    ]

    rol = models.CharField(max_length=20, choices=ROL_CHOICES, default=CLIENTE)

    # Estado de negocio de la cuenta (CU-USR-ALT, CU-USR-MOD y CU-USR-BAJ). Es la única fuente de
    # verdad: `is_active` —que es de Django y bloquea el login— se deriva de
    # acá en `save()`, así los dos campos no pueden quedar desincronizados.
    estado = models.CharField(max_length=25, choices=ESTADO_CHOICES, default=ACTIVO)

    # El login del sistema es por correo (CU-AUT-INI), así que el email tiene que
    # ser único e identificar a una sola cuenta. `username` se conserva como
    # identificador interno heredado de AbstractUser.
    email = models.EmailField("correo electrónico", unique=True)

    # Columna "última modificación" de la tabla de usuarios (CU-USR-MOD).
    actualizado_en = models.DateTimeField("última modificación", auto_now=True)

    # ----------------------------------------------------------------------
    # Datos opcionales del registro de Cliente (CU-CLI-ALT). Van acá y no en un
    # modelo aparte porque son *un* dato por cuenta: la libreta de direcciones
    # múltiples, si alguna vez hace falta, es del módulo de Pedidos.
    # ----------------------------------------------------------------------

    # Teléfono en tres partes. Se guarda desarmado, no formateado: así se puede
    # filtrar por código de área (útil para logística) y se puede reformatear
    # para mostrar sin tener que reinterpretar un texto libre.
    telefono_pais = models.CharField(
        "código de país",
        max_length=4,
        blank=True,
        default=PAIS_TELEFONO_PREDETERMINADO,
        validators=[validar_codigo_pais],
    )
    telefono_area = models.CharField(
        "código de área", max_length=5, blank=True, validators=[validar_codigo_area]
    )
    telefono_numero = models.CharField(
        "número de teléfono", max_length=10, blank=True, validators=[validar_numero_telefono]
    )

    # Dirección de envío predeterminada, desglosada en los campos que un
    # repartidor necesita para llegar.
    direccion = models.CharField("dirección", max_length=150, blank=True)
    direccion_linea2 = models.CharField("dirección, línea 2", max_length=150, blank=True)
    depto = models.CharField("piso / depto.", max_length=20, blank=True)
    codigo_postal = models.CharField(
        "código postal", max_length=8, blank=True, validators=[validar_codigo_postal]
    )
    localidad = models.CharField("localidad", max_length=120, blank=True)

    # Sin `choices`: la lista de provincias no vive en el código sino en
    # georef-ar-api (ver `apps/core/georef.py`), y el formulario valida contra
    # la lista viva. Ponerla acá obligaría a generar una migración cada vez que
    # el catálogo oficial cambiara, que es exactamente lo que se quiso evitar.
    provincia = models.CharField("provincia", max_length=60, blank=True)
    comentarios_envio = models.TextField("comentarios para la entrega", blank=True)

    # Consentimiento informado de la política de privacidad (Ley 25.326).
    # Se guarda la fecha y no un booleano: un `True` dice que aceptó pero no
    # cuándo, y lo que hay que poder demostrar es el acto fechado. De paso
    # sirve de booleano, porque estar en NULL ya significa "no aceptó".
    fecha_aceptacion_politica = models.DateTimeField(
        "aceptación de la política de privacidad", null=True, blank=True
    )

    def save(self, *args, **kwargs):
        # Se normaliza a minúsculas para que "Ana@x.com" y "ana@x.com" no
        # puedan convivir como dos cuentas distintas.
        self.email = self.email.strip().lower()
        # Solo una cuenta Activa puede iniciar sesión: mientras está pendiente
        # de activación todavía no eligió contraseña, y una cuenta dada de baja
        # no debe poder volver a entrar (CU-USR-BAJ).
        self.is_active = self.estado == self.ACTIVO
        return super().save(*args, **kwargs)

    @property
    def acepto_politica_privacidad(self):
        return self.fecha_aceptacion_politica is not None

    @property
    def telefono(self):
        """El teléfono armado para mostrar, o cadena vacía si no cargó ninguno.

        El número es lo que decide: sin él, el código de país solo no es un
        teléfono (y siempre está, porque tiene valor por defecto).
        """
        if not self.telefono_numero:
            return ""
        return f"{self.telefono_pais} {self.telefono_area} {self.telefono_numero}".strip()

    @property
    def direccion_completa(self):
        """La dirección de envío en una línea, con las partes que estén cargadas."""
        if not self.direccion:
            return ""
        primera_linea = ", ".join(
            parte for parte in (self.direccion, self.depto, self.direccion_linea2) if parte
        )
        # "N3300ABC Posadas": el código postal va pegado a la localidad, como
        # se escribe en un sobre.
        con_localidad = " ".join(parte for parte in (self.codigo_postal, self.localidad) if parte)
        return ", ".join(parte for parte in (primera_linea, con_localidad, self.provincia) if parte)

    @property
    def esta_pendiente_de_activacion(self):
        return self.estado == self.PENDIENTE_ACTIVACION

    @property
    def esta_congelada(self):
        """Una cuenta dada de baja no se edita: primero hay que reactivarla.

        Si no, se pueden dejar cambios preparados sobre una cuenta dormida
        —otro correo, un rol más alto— que recién surten efecto cuando alguien
        la reactiva. Congelarla obliga a que todo camino de vuelta al acceso
        pase por una reactivación explícita y auditada.
        """
        return self.estado == self.INACTIVO

    @property
    def se_puede_eliminar(self):
        """Solo se borra una cuenta que nunca llegó a usarse.

        No alcanza con que esté pendiente: una cuenta reactivada también queda
        pendiente, y esa sí tiene historial. `last_login` vacío es la prueba de
        que nunca pudo registrar ninguna operación.
        """
        return self.esta_pendiente_de_activacion and self.last_login is None

    @property
    def es_administrador_activo(self):
        return self.rol == self.ADMINISTRADOR and self.estado == self.ACTIVO


class IntentoFallido(models.Model):
    """Un intento de inicio de sesión rechazado por credenciales inválidas.

    Se guarda el correo tal como se tipeó (puede no corresponder a ninguna
    cuenta: si solo contáramos los intentos contra cuentas existentes, la
    diferencia de comportamiento delataría qué correos están registrados).
    """

    email = models.CharField(max_length=254, db_index=True)
    ip = models.GenericIPAddressField(null=True, blank=True)
    ocurrido_en = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        verbose_name = "intento fallido"
        verbose_name_plural = "intentos fallidos"
        ordering = ["-ocurrido_en"]

    def __str__(self):
        return f"{self.email} desde {self.ip} el {self.ocurrido_en:%Y-%m-%d %H:%M}"


class EnlaceDeCorreo(models.Model):
    """Base de `EnlaceActivacion` y `TokenRecuperacion` (`MODELO_DE_DOMINIO.md`, Área 1).

    Los dos son el mismo concepto con distinta vigencia y distinto caso de uso: algo que se
    emite para una cuenta, viaja por correo, se consume **una sola vez** y vence solo. El
    modelo de dominio los declara conceptos y no atributos por una razón que se ve acá:

    > «cuatro casos de uso los tratan como objetos con estado propio […] Un dato que se emite,
    > se consume una sola vez, vence solo y del que hay que distinguir tres razones de rechazo
    > no es un atributo de la cuenta: es un concepto.»

    **Qué aporta esta tabla que el token firmado no podía.** El token de Django distingue
    válido de inválido y nada más. Con la fila, un enlace rechazado dice *por qué*: consumido
    o vencido. Es lo que `CU-AUT-ACT` valida como tres estados distinguibles y lo que
    `CU-AUT-REC` E1 necesita para separar «ya utilizado» de «expirado».

    **La fila no reemplaza al token, lo acompaña.** La credencial que viaja en la URL sigue
    siendo el token firmado: la fila no puede viajar, porque su identificador sería adivinable.
    La fila es el *sujeto* de las postcondiciones; el token es la llave.

    **`estado` guarda la transición, no la deduce.** Los contratos declaran cambios de estado
    —`CO-118` «tr.estado pasó de Vigente a Consumido», `CO-122` «el anterior pasó a Vencido»—
    y un campo derivado no puede haber «pasado» de nada. El vencimiento por reloj es el único
    que no se escribe en el momento en que ocurre, porque nadie está mirando: para eso está
    `estado_actual`, que lo resuelve al leerlo.
    """

    VIGENTE = "vigente"
    CONSUMIDO = "consumido"
    VENCIDO = "vencido"

    ESTADO_CHOICES = [  # noqa: RUF012
        (VIGENTE, "Vigente"),
        (CONSUMIDO, "Consumido"),
        (VENCIDO, "Vencido"),
    ]

    # Cuánto vive un enlace de esta clase. Lo declara cada subclase.
    VIGENCIA = None

    # `default` y no `auto_now_add`: el vencimiento se calcula desde el momento
    # de emisión, y con `auto_now_add` ese momento no existe todavía cuando hay
    # que calcularlo. Tomando dos veces el reloj, «vence 48 horas después de
    # emitido» quedaba siendo casi cierto, que sobre un plazo es no serlo.
    emitido_en = models.DateTimeField("emitido en", default=timezone.now)
    vence_en = models.DateTimeField("vence en")
    estado = models.CharField(max_length=10, choices=ESTADO_CHOICES, default=VIGENTE)
    consumido_en = models.DateTimeField("consumido en", null=True, blank=True)

    class Meta:
        abstract = True
        ordering = ["-emitido_en"]

    def __str__(self):
        return f"{self._meta.verbose_name} de {self.usuario_id} · {self.estado_actual}"

    def save(self, *args, **kwargs):
        if self.vence_en is None:
            self.vence_en = self.emitido_en + self.VIGENCIA
        return super().save(*args, **kwargs)

    # ------------------------------------------------------------------ #
    # Estado
    # ------------------------------------------------------------------ #

    @property
    def vencido_por_reloj(self):
        return timezone.now() >= self.vence_en

    @property
    def estado_actual(self):
        """El estado que el concepto tiene *ahora*.

        Un enlace guardado como Vigente cuya vigencia ya pasó está Vencido, aunque nadie haya
        escrito la transición: no hay nadie mirando en el instante en que un plazo se cumple.
        Lo que sí se escribe es la transición que alguien provoca —consumirlo, reemplazarlo—,
        que es la que los contratos declaran.
        """
        if self.estado == self.VIGENTE and self.vencido_por_reloj:
            return self.VENCIDO
        return self.estado

    @property
    def esta_vigente(self):
        return self.estado_actual == self.VIGENTE

    @property
    def motivo_de_rechazo(self):
        """`None` si sirve; si no, por qué no. Es lo que la tabla vino a poder responder."""
        if self.esta_vigente:
            return None
        return self.estado_actual

    # ------------------------------------------------------------------ #
    # Transiciones
    # ------------------------------------------------------------------ #

    @classmethod
    def emitir(cls, usuario):
        """Emite uno nuevo y deja Vencidos los que el usuario tuviera vigentes.

        Es la postcondición de `CO-122`: «se creó un EnlaceActivacion nuevo […] el anterior
        pasó a estado Vencido y no admite uso». Vale igual en la primera emisión, donde no hay
        ninguno anterior que vencer, así que `CO-120` y `CO-122` comparten este camino.

        Al anterior se lo vence y no se lo borra: cuántos enlaces hizo falta emitir para una
        cuenta es un dato, y una fila borrada no lo cuenta.
        """
        cls.objects.filter(usuario=usuario, estado=cls.VIGENTE).update(estado=cls.VENCIDO)
        return cls.objects.create(usuario=usuario)

    @classmethod
    def vigente_de(cls, usuario):
        """El enlace que el usuario puede usar hoy, o `None`."""
        enlace = cls.objects.filter(usuario=usuario, estado=cls.VIGENTE).first()
        return enlace if enlace and enlace.esta_vigente else None

    @classmethod
    def ultimo_de(cls, usuario):
        """El último emitido, sirva o no. Es el que explica por qué un enlace fue rechazado."""
        return cls.objects.filter(usuario=usuario).first()

    def consumir(self):
        """Vigente → Consumido. No admite un segundo uso.

        Devuelve `True` si lo consumió esta llamada. Uno que ya estaba consumido o vencido
        devuelve `False` y no se toca: que el estado no cambie es la postcondición.
        """
        if not self.esta_vigente:
            return False
        self.estado = self.CONSUMIDO
        self.consumido_en = timezone.now()
        self.save(update_fields=["estado", "consumido_en"])
        return True


class EnlaceActivacion(EnlaceDeCorreo):
    """El enlace con el que el titular de una cuenta nueva elige su primera contraseña.

    Lo emiten `CO-120` (alta), `CO-122` (regeneración) y `CO-124` (reactivación); lo consume
    `CO-119`. Vigencia de 48 horas, según el modelo de dominio.
    """

    VIGENCIA = timedelta(seconds=settings.VIGENCIA_ENLACE_ACTIVACION)

    usuario = models.ForeignKey(
        "accounts.Usuario", on_delete=models.CASCADE, related_name="enlaces_de_activacion"
    )

    class Meta(EnlaceDeCorreo.Meta):
        abstract = False
        verbose_name = "enlace de activación"
        verbose_name_plural = "enlaces de activación"


class TokenRecuperacion(EnlaceDeCorreo):
    """El enlace con el que alguien que olvidó su contraseña elige una nueva.

    Lo emite `CO-117` y lo consume `CO-118`. Vigencia de 30 minutos, según el modelo de
    dominio: es más corta que la de activación porque este enlace lo pide cualquiera que sepa
    un correo, mientras que el de activación lo emite un Administrador sobre una cuenta que
    acaba de crear.
    """

    VIGENCIA = timedelta(seconds=settings.VIGENCIA_ENLACE_RECUPERACION)

    usuario = models.ForeignKey(
        "accounts.Usuario", on_delete=models.CASCADE, related_name="tokens_de_recuperacion"
    )

    class Meta(EnlaceDeCorreo.Meta):
        abstract = False
        verbose_name = "token de recuperación"
        verbose_name_plural = "tokens de recuperación"
