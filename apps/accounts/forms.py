from django import forms
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.forms import (
    AuthenticationForm,
    BaseUserCreationForm,
    PasswordResetForm,
)
from django.core.exceptions import ValidationError
from django.template.loader import render_to_string
from django.urls import reverse

from apps.accounts import services
from apps.accounts.models import (
    PAIS_TELEFONO_PREDETERMINADO,
    TokenRecuperacion,
    provincia_del_codigo_postal,
)
from apps.core import georef, paises
from apps.core.mail import cuerpo_html, enviar_correo
from apps.core.utils import obtener_ip

Usuario = get_user_model()

# Mensaje único para credenciales inválidas: no distingue si falló el correo o
# la contraseña, ni revela si la cuenta existe (CU-AUT-INI, excepción 1).
MENSAJE_CREDENCIALES = "Correo o contraseña incorrectos"
MENSAJE_CUENTA_INACTIVA = "Esta cuenta no está disponible"
MENSAJE_BLOQUEO = (
    "Se superó la cantidad de intentos permitidos. El acceso quedó bloqueado "
    "temporalmente y se envió un aviso al correo registrado."
)

# CU-USR-ALT / CU-USR-MOD: conflicto de correo.
MENSAJE_CORREO_EN_USO = "Ya existe una cuenta registrada con ese correo electrónico."

# CU-USR-MOD / CU-USR-BAJ: no se puede dejar el sistema sin nadie que lo administre.
MENSAJE_UNICO_ADMINISTRADOR = "Debe existir al menos un Administrador activo en el sistema."

# CU-USR-MOD (cuenta congelada) y CU-USR-ELI (cuenta con historial).
MENSAJE_CUENTA_CONGELADA = (
    "La cuenta se encuentra dada de baja y no admite modificaciones. Para modificar sus "
    "datos debe reactivarse previamente."
)
MENSAJE_CUENTA_CON_HISTORIAL = (
    "La cuenta registra actividad previa, por lo que no puede eliminarse. Para retirarla "
    "del sistema debe darse de baja, conservando su historial."
)

# CU-CLI-ALT: registro de Cliente. El texto es el del CU, y va acompañado en la
# pantalla por el enlace a recuperación de contraseña (CU-AUT-REC).
MENSAJE_CORREO_YA_REGISTRADO = "Este correo ya tiene una cuenta asociada"
MENSAJE_POLITICA_OBLIGATORIA = "Debe aceptar la política de privacidad para poder crear la cuenta."

# Teléfono y dirección son opcionales, pero incompletos no sirven para nada:
# no se puede discar medio teléfono ni despachar a media dirección.
MENSAJE_FALTA_CODIGO_AREA = "Indique el código de área para poder utilizar el número."
MENSAJE_FALTA_NUMERO = "Indique el número de teléfono o deje el código de área vacío."
MENSAJE_DIRECCION_INCOMPLETA = (
    "Para guardar una dirección de envío debe completar la dirección, la localidad, el código "
    "postal y la provincia."
)
MENSAJE_CPA_DE_OTRA_PROVINCIA = (
    "El código postal corresponde a {provincia}. Verifique el dato o utilice el formato de "
    "cuatro dígitos."
)


# Un nombre de una o dos letras casi siempre es un tipeo a medias o una prueba
# ("a", "xx"): con tres ya se distingue de un accidente.
LARGO_MINIMO_NOMBRE = 3
MENSAJE_NOMBRE_CORTO = f"El nombre debe tener al menos {LARGO_MINIMO_NOMBRE} letras."
MENSAJE_NOMBRE_INVALIDO = (
    "El nombre solo puede contener letras, espacios y los signos ' - . (por ejemplo, "
    '"María José D\'Angelo").'
)

# Lo que puede aparecer en un nombre además de letras. Los apellidos reales los
# usan: guion en los compuestos, apóstrofo en O'Connor o D'Angelo, punto en las
# abreviaturas. Números y símbolos no tienen nada que hacer acá.
SIGNOS_DEL_NOMBRE = " '-."


def validar_nombre_completo(nombre):
    """Reglas de un nombre de persona. Devuelve la lista de errores encontrados.

    Se valida acá y no con un `RegexValidator` en el modelo porque son dos
    reglas distintas —el largo y los caracteres— y cada una merece su propio
    mensaje: "no cumple el formato" no le dice a nadie qué corregir.

    `isalpha()` de Python es consciente de Unicode, así que "á", "ñ" y "ü"
    pasan sin necesidad de enumerar los acentos en una expresión regular.
    """
    errores = []

    if any(not (letra.isalpha() or letra in SIGNOS_DEL_NOMBRE) for letra in nombre):
        errores.append(MENSAJE_NOMBRE_INVALIDO)

    # Se cuentan las letras, no los caracteres: "A.B" tiene tres caracteres
    # pero no es un nombre.
    if sum(letra.isalpha() for letra in nombre) < LARGO_MINIMO_NOMBRE:
        errores.append(MENSAJE_NOMBRE_CORTO)

    return errores


def partir_nombre(nombre_completo):
    """Parte un nombre completo en el (first_name, last_name) de Django.

    El sistema pide el nombre en un solo campo, pero `AbstractUser` lo guarda
    partido en dos. Se corta por el primer espacio, así "Ana María Pérez"
    vuelve a leerse igual al recomponerlo con `get_full_name()`.
    """
    nombre, _, apellido = nombre_completo.partition(" ")
    return nombre, apellido


class FormularioLogin(AuthenticationForm):
    """Login por correo, con bloqueo por intentos fallidos.

    Hereda de `AuthenticationForm` para reutilizar el manejo de sesión de
    Django; se sobreescribe `clean()` porque el orden de las validaciones es
    parte del CU: primero el bloqueo, después las credenciales.
    """

    username = forms.EmailField(
        label="Correo electrónico",
        widget=forms.EmailInput(attrs={"autofocus": True, "autocomplete": "email"}),
    )

    error_messages = {  # noqa: RUF012
        **AuthenticationForm.error_messages,
        "invalid_login": MENSAJE_CREDENCIALES,
        "inactive": MENSAJE_CUENTA_INACTIVA,
    }

    def clean(self):
        email = self.cleaned_data.get("username")
        password = self.cleaned_data.get("password")
        if not email or not password:
            return self.cleaned_data

        ip = obtener_ip(self.request)

        if services.esta_bloqueado(email, ip):
            raise ValidationError(MENSAJE_BLOQUEO, code="bloqueado")

        self.user_cache = authenticate(self.request, username=email, password=password)

        if self.user_cache is None:
            if self._es_cuenta_inactiva_con_credenciales_validas(email, password):
                # Solo se admite que la cuenta existe ante quien ya demostró
                # conocer la contraseña: para el resto sigue siendo el mensaje
                # genérico.
                raise ValidationError(MENSAJE_CUENTA_INACTIVA, code="inactive")
            services.registrar_intento_fallido(email, ip)
            raise ValidationError(MENSAJE_CREDENCIALES, code="invalid_login")

        self.confirm_login_allowed(self.user_cache)
        services.limpiar_intentos(email, ip)
        return self.cleaned_data

    def _es_cuenta_inactiva_con_credenciales_validas(self, email, password):
        usuario = Usuario.objects.filter(email__iexact=email, is_active=False).first()
        return usuario is not None and usuario.check_password(password)


class FormularioRecuperarContrasena(PasswordResetForm):
    """El de Django, pero emitiendo el `TokenRecuperacion` y enviando por `apps.core.mail`.

    Del de Django cambian dos cosas. El correo sale sin cortes de línea, porque
    el enlace pasa los 78 caracteres y si no viaja partido en dos (ver
    `apps/core/mail.py`). Y se emite la fila que `CO-117` declara.
    """

    def save(self, *args, **kwargs):
        """`CO-117` (a): «sólo si el correo corresponde a una cuenta Activa: se creó
        tr : TokenRecuperacion […] y se formó tr → Usuario».

        Se emite sobre la misma selección con la que Django decide a quién mandarle el
        correo, `get_users()`, y no sobre una consulta propia: si las dos discreparan habría
        correos sin fila o filas sin correo, y la postcondición dice que van juntos.

        El correo que no corresponde a ninguna cuenta activa no produce ninguna fila. Es la
        otra mitad de la postcondición, y la que sostiene que la respuesta sea indistinguible:
        lo único que no hay que dejar es una diferencia observable desde afuera.
        """
        for usuario in self.get_users(self.cleaned_data["email"]):
            TokenRecuperacion.emitir(usuario)
        return super().save(*args, **kwargs)

    def send_mail(
        self,
        subject_template_name,
        email_template_name,
        context,
        from_email,
        to_email,
        html_email_template_name=None,
    ):
        # El asunto se aplana en una sola línea, igual que en Django: una
        # cabecera con salto de línea permite inyectar cabeceras falsas.
        asunto = "".join(render_to_string(subject_template_name, context).splitlines())
        cuerpo = render_to_string(email_template_name, context)
        ruta = reverse(
            "accounts:password_reset_confirm",
            kwargs={"uidb64": context["uid"], "token": context["token"]},
        )
        html = cuerpo_html(
            "correo/recuperacion.html",
            {**context, "enlace": f"{context['protocol']}://{context['domain']}{ruta}"},
        )
        enviar_correo(
            asunto=asunto,
            cuerpo=cuerpo,
            destinatarios=[to_email],
            remitente=from_email,
            html=html,
        )


class FormularioUsuarioPersonal(forms.ModelForm):
    """Alta (CU-USR-ALT) y modificación (CU-USR-MOD) de una cuenta de personal.

    Es el mismo formulario para los dos CU porque los campos editables son los
    mismos: nombre completo, correo y rol. Lo que cambia entre alta y edición
    (estado inicial, token de activación, invalidación de sesiones) es
    responsabilidad de la vista, no del formulario.
    """

    nombre_completo = forms.CharField(
        label="Nombre completo",
        max_length=150,
        # El Administrador entra a la pantalla y escribe: sin pasar por el mouse.
        widget=forms.TextInput(attrs={"autofocus": True, "autocomplete": "off"}),
    )

    # El rol solo puede ser de personal. `Usuario.rol` acepta "cliente", pero
    # esa alta es el CU-CLI-ALT y esta pantalla no debe ofrecerla siquiera como
    # opción: un POST con rol="cliente" también tiene que morir acá.
    rol = forms.ChoiceField(
        label="Rol",
        choices=[
            (valor, etiqueta)
            for valor, etiqueta in Usuario.ROL_CHOICES
            if valor in Usuario.ROLES_DE_PERSONAL
        ],
    )

    # Los campos declarados acá arriba se renderizan después de los del modelo
    # si no se fuerza el orden.
    field_order = ["nombre_completo", "email", "rol"]  # noqa: RUF012

    class Meta:
        model = Usuario
        fields = ["email", "rol"]
        labels = {"email": "Correo electrónico"}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # CU-USR-MOD paso 1: al editar se precargan los datos actuales.
        if self.instance.pk:
            self.fields["nombre_completo"].initial = self.instance.get_full_name()

    def clean_nombre_completo(self):
        # Los espacios de más se limpian antes de validar: "  Ana   Pérez  " es
        # un nombre bien escrito con dedos apurados, no un dato inválido.
        nombre = " ".join(self.cleaned_data["nombre_completo"].split())
        errores = validar_nombre_completo(nombre)
        if errores:
            raise ValidationError(errores)
        return nombre

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        # `iexact` porque el modelo normaliza a minúsculas al guardar, pero el
        # correo puede venir tipeado de cualquier forma.
        cuentas_con_ese_correo = Usuario.objects.filter(email__iexact=email)
        if self.instance.pk:
            cuentas_con_ese_correo = cuentas_con_ese_correo.exclude(pk=self.instance.pk)
        # El CU habla de cuentas Activas o Pendientes; el correo es único a
        # nivel de base para *cualquier* estado, así que una cuenta dada de
        # baja también bloquea la reutilización del correo.
        if cuentas_con_ese_correo.exists():
            raise ValidationError(MENSAJE_CORREO_EN_USO, code="correo_en_uso")
        return email

    def save(self, commit=True):
        usuario = super().save(commit=False)
        usuario.first_name, usuario.last_name = partir_nombre(self.cleaned_data["nombre_completo"])
        if commit:
            usuario.save()
        return usuario


class FormularioReactivacionUsuario(forms.Form):
    """CU-USR-REA — el rol con el que la cuenta vuelve al sistema.

    `CO-124` declara la operación como `confirmarReactivacionDeUsuario(usuario, rol)`, y sus
    Notas explican para qué: «el rol se elige acá y queda registrado junto con la reactivación,
    en lugar de restaurarse el que tenía. Es lo que impide dejar preparado un cambio de rol
    sobre una cuenta dormida (ver CO-121)».

    `CO-121` prohíbe editar una cuenta Inactiva justamente para eso. Elegir el rol acá es la
    otra mitad de esa defensa: sin ella, reincorporar a alguien le devuelve automáticamente los
    permisos que tenía cuando se fue, sin que nadie los vuelva a mirar.

    Mismo criterio que el alta de personal: `cliente` no es una opción. Esa cuenta es del
    CU-CLI-ALT y un POST con `rol="cliente"` tiene que morir acá.
    """

    rol = forms.ChoiceField(
        label="Rol con el que se reactiva",
        choices=[
            (valor, etiqueta)
            for valor, etiqueta in Usuario.ROL_CHOICES
            if valor in Usuario.ROLES_DE_PERSONAL
        ],
    )


class FormularioRegistroCliente(BaseUserCreationForm):
    """CU-CLI-ALT — Registrar Cuenta de Cliente.

    Hereda de `BaseUserCreationForm` (la clase que la documentación de Django
    señala para personalizar el alta) para no reescribir el par
    contraseña/confirmación: de ahí salen gratis la comparación entre las dos y
    el paso por `AUTH_PASSWORD_VALIDATORS`, que es lo que el CU llama
    "requisitos mínimos".

    A diferencia del alta de personal (CU-USR-ALT), acá el rol no se elige ni se
    muestra: lo fija la vista en `cliente`. Un formulario que no tiene el campo
    no puede recibirlo por POST.
    """

    nombre_completo = forms.CharField(
        label="Nombre completo",
        max_length=150,
        widget=forms.TextInput(attrs={"autofocus": True, "autocomplete": "name"}),
    )

    acepta_politica = forms.BooleanField(
        # La pantalla dibuja esta misma etiqueta con el enlace a la política;
        # el texto de acá es el que queda si el campo se renderiza pelado.
        label=("Acepto la política de privacidad y el tratamiento de mis datos " "personales"),
        # Un `BooleanField` obligatorio solo valida si llega marcado: es
        # exactamente el bloqueo que pide la excepción 3 del CU.
        required=True,
        error_messages={"required": MENSAJE_POLITICA_OBLIGATORIA},
    )

    field_order = [  # noqa: RUF012
        "nombre_completo",
        "email",
        "password1",
        "password2",
        "telefono_pais",
        "telefono_area",
        "telefono_numero",
        "direccion",
        "direccion_linea2",
        "depto",
        "provincia",
        "localidad",
        "codigo_postal",
        "comentarios_envio",
        "acepta_politica",
    ]

    class Meta:
        model = Usuario
        fields = [
            "email",
            "telefono_pais",
            "telefono_area",
            "telefono_numero",
            "direccion",
            "direccion_linea2",
            "depto",
            "provincia",
            "localidad",
            "codigo_postal",
            "comentarios_envio",
        ]
        labels = {
            "email": "Correo electrónico",
            "telefono_pais": "País",
            "telefono_area": "Código de área",
            "telefono_numero": "Número",
            "direccion": "Dirección",
            "direccion_linea2": "Dirección línea 2",
            "depto": "Piso / depto.",
            "provincia": "Provincia",
            "localidad": "Localidad",
            "codigo_postal": "Código postal",
            "comentarios_envio": "Comentarios para la entrega",
        }
        widgets = {  # noqa: RUF012
            "email": forms.EmailInput(attrs={"autocomplete": "email"}),
            "telefono_area": forms.TextInput(
                attrs={
                    "autocomplete": "tel-area-code",
                    "inputmode": "numeric",
                    "placeholder": "376",
                }
            ),
            "telefono_numero": forms.TextInput(
                attrs={
                    "autocomplete": "tel-local",
                    "inputmode": "numeric",
                    "placeholder": "4123456",
                }
            ),
            "direccion": forms.TextInput(
                attrs={"autocomplete": "address-line1", "placeholder": "Calle y número"}
            ),
            "direccion_linea2": forms.TextInput(attrs={"autocomplete": "address-line2"}),
            "depto": forms.TextInput(attrs={"placeholder": "3.º B"}),
            "codigo_postal": forms.TextInput(
                attrs={"autocomplete": "postal-code", "placeholder": "3300 o N3300ABC"}
            ),
            # `list` engancha el campo con el `<datalist>` que la pantalla
            # rellena con las localidades de la provincia elegida. Sigue siendo
            # texto libre: si la API no contesta, no hay sugerencias pero el
            # campo se escribe igual.
            "localidad": forms.TextInput(
                attrs={
                    "autocomplete": "address-level2",
                    # `list` es el camino sin JavaScript; con JavaScript, el
                    # parcial `_autocompletado.html` lo saca y dibuja su propia
                    # lista con los tokens del sistema.
                    "list": "localidades",
                    "data-autocompletado": "localidades",
                    "placeholder": "Posadas",
                }
            ),
            "comentarios_envio": forms.Textarea(
                attrs={
                    "rows": 3,
                    "placeholder": "Timbre, horarios de entrega, cómo llegar…",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Las provincias se piden acá y no al importar el módulo: si se
        # resolvieran al arrancar el proceso, la lista quedaría congelada hasta
        # el próximo reinicio y una caída de la API al levantar el servidor
        # dejaría el formulario sin provincias para siempre.
        #
        # El campo pasa a ser un `ChoiceField` propio —el del modelo es un
        # `CharField` sin `choices`— y arranca sin elegir: la dirección es
        # opcional, y un valor precargado haría que quien no la completa igual
        # "elija" Buenos Aires sin querer.
        self.fields["provincia"] = forms.ChoiceField(
            label="Provincia",
            required=False,
            choices=[("", "Seleccionar…"), *georef.provincias_para_select()],
        )

        # Mismo criterio para el código de país: sale del catálogo externo, no
        # de una lista escrita a mano. Viene elegida Argentina, que es donde
        # está la comiquería y de donde va a ser casi todo el mundo.
        self.fields["telefono_pais"] = forms.ChoiceField(
            label="País",
            required=False,
            initial=PAIS_TELEFONO_PREDETERMINADO,
            choices=paises.paises_para_select(),
        )

        # Los `ChoiceField` se declararon después que el resto, así que hay que
        # reponer el orden que fija `field_order`.
        self.order_fields(self.field_order)

    def clean_nombre_completo(self):
        # Los espacios de más se limpian antes de validar: "  Ana   Pérez  " es
        # un nombre bien escrito con dedos apurados, no un dato inválido.
        nombre = " ".join(self.cleaned_data["nombre_completo"].split())
        errores = validar_nombre_completo(nombre)
        if errores:
            raise ValidationError(errores)
        return nombre

    def clean_telefono_pais(self):
        # El país no se puede vaciar: si lo borran, vuelve al predeterminado.
        # Es el único de los tres que tiene un valor sensato por omisión.
        pais = self.cleaned_data["telefono_pais"].strip().replace(" ", "")
        return pais or PAIS_TELEFONO_PREDETERMINADO

    def clean_telefono_area(self):
        # Los códigos de área se escriben sin el 0 y los celulares sin el 15;
        # se los saca acá en vez de rechazar el dato, porque es la forma en que
        # la mayoría de la gente tiene anotado su propio teléfono.
        area = self.cleaned_data["telefono_area"].strip().replace(" ", "").replace("-", "")
        return area.removeprefix("0")

    def clean_telefono_numero(self):
        numero = self.cleaned_data["telefono_numero"].strip().replace(" ", "").replace("-", "")
        return numero.removeprefix("15")

    def clean_codigo_postal(self):
        return self.cleaned_data["codigo_postal"].strip().upper()

    def clean_localidad(self):
        return " ".join(self.cleaned_data["localidad"].split())

    def clean(self):
        datos = super().clean()
        self._validar_telefono_completo(datos)
        self._validar_direccion_completa(datos)
        self._validar_codigo_postal_con_provincia(datos)
        return datos

    def _validar_telefono_completo(self, datos):
        """El teléfono es opcional, pero a medias no sirve.

        Un número sin código de área no se puede discar, así que o se cargan
        las dos partes o ninguna. El código de país no entra en la cuenta:
        tiene valor por defecto y nunca queda a elección del visitante.
        """
        if datos.get("telefono_numero") and not datos.get("telefono_area"):
            self.add_error("telefono_area", MENSAJE_FALTA_CODIGO_AREA)
        if datos.get("telefono_area") and not datos.get("telefono_numero"):
            self.add_error("telefono_numero", MENSAJE_FALTA_NUMERO)

    def _validar_direccion_completa(self, datos):
        """Ídem con la dirección: o va entera o no va.

        Una dirección sin código postal ni provincia no permite cotizar un
        envío, y guardarla igual sería guardar algo que después no se puede
        usar. Los campos accesorios (línea 2, depto, comentarios) no obligan a
        nada: por sí solos no son una dirección.
        """
        obligatorios = ("direccion", "localidad", "codigo_postal", "provincia")
        accesorios = ("direccion_linea2", "depto", "comentarios_envio")

        cargo_algo = any(datos.get(campo) for campo in obligatorios + accesorios)
        if not cargo_algo:
            return

        for campo in obligatorios:
            if not datos.get(campo):
                self.add_error(campo, MENSAJE_DIRECCION_INCOMPLETA)

    def _validar_codigo_postal_con_provincia(self, datos):
        """Cruza la letra del CPA con la provincia elegida.

        Es la validación que ninguna API gratuita ofrece —no existe uno
        público de códigos postales argentinos— y que sin embargo atrapa el
        error más común: elegir mal la provincia en el desplegable.

        Solo opina cuando tiene con qué. Un código de cuatro dígitos no lleva
        letra, así que no se lo puede contradecir, y ahí no dice nada.
        """
        provincia_del_codigo = provincia_del_codigo_postal(datos.get("codigo_postal"))
        provincia_elegida = datos.get("provincia")

        if not provincia_del_codigo or not provincia_elegida:
            return
        if provincia_del_codigo == provincia_elegida:
            return

        self.add_error(
            "codigo_postal",
            MENSAJE_CPA_DE_OTRA_PROVINCIA.format(provincia=provincia_del_codigo),
        )

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        # `iexact` porque el modelo normaliza a minúsculas recién al guardar.
        if Usuario.objects.filter(email__iexact=email).exists():
            raise ValidationError(MENSAJE_CORREO_YA_REGISTRADO, code="correo_en_uso")
        return email

    @property
    def correo_ya_registrado(self):
        """¿El rechazo fue por un correo que ya tiene cuenta?

        La pantalla lo usa para ofrecer el enlace a recuperación de contraseña
        (CU-AUT-REC) solo en ese caso; los demás errores del correo (formato
        inválido, campo vacío) no tienen nada que ver con recuperar el acceso.
        """
        # `as_data()` devuelve los `ValidationError` con su `code`; `errors` a
        # secas devuelve los mensajes ya renderizados, sin forma de distinguir
        # un error de otro salvo comparando textos.
        errores_del_correo = self.errors.as_data().get("email", [])
        return any(error.code == "correo_en_uso" for error in errores_del_correo)

    def save(self, commit=True):
        usuario = super().save(commit=False)
        usuario.first_name, usuario.last_name = partir_nombre(self.cleaned_data["nombre_completo"])
        if commit:
            usuario.save()
        return usuario


# ---------------------------------------------------------------------------
# CU-CLI-DAT — el Cliente edita su cuenta desde «Mi cuenta»
# ---------------------------------------------------------------------------


class DatosPersonalesForm(forms.ModelForm):
    """`CO-108`: nombre, teléfono y dirección de envío predeterminada.

    Las validaciones son las del registro (`FormularioRegistroCliente`): el
    teléfono y la dirección son opcionales pero no van a medias, y la letra del
    código postal tiene que ser la de la provincia. Se toman de ahí y no se
    copian, para que las dos pantallas no puedan discrepar. El correo y la
    contraseña no están: tienen sus propios flujos (`CO-109`, `CO-111`).
    """

    nombre_completo = forms.CharField(
        label="Nombre completo",
        max_length=150,
        widget=forms.TextInput(attrs={"autocomplete": "name"}),
    )

    CAMPOS = (  # noqa: RUF012
        "telefono_pais",
        "telefono_area",
        "telefono_numero",
        "direccion",
        "direccion_linea2",
        "depto",
        "provincia",
        "localidad",
        "codigo_postal",
        "comentarios_envio",
    )

    class Meta:
        model = Usuario
        fields = [  # noqa: RUF012
            "telefono_pais",
            "telefono_area",
            "telefono_numero",
            "direccion",
            "direccion_linea2",
            "depto",
            "provincia",
            "localidad",
            "codigo_postal",
            "comentarios_envio",
        ]
        labels = FormularioRegistroCliente.Meta.labels
        widgets = FormularioRegistroCliente.Meta.widgets

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["nombre_completo"].initial = self.instance.get_full_name()
        provincias = [("", "Seleccionar…"), *georef.provincias_para_select()]
        # Una provincia que ya no figura en la lista viva se ofrece igual.
        actual = self.instance.provincia
        if actual and actual not in {valor for valor, _ in provincias}:
            provincias.append((actual, actual))
        self.fields["provincia"] = forms.ChoiceField(
            label="Provincia", required=False, choices=provincias
        )
        self.fields["telefono_pais"] = forms.ChoiceField(
            label="País",
            required=False,
            initial=PAIS_TELEFONO_PREDETERMINADO,
            choices=paises.paises_para_select(),
        )
        self.order_fields(["nombre_completo", *self.CAMPOS])

    clean_nombre_completo = FormularioRegistroCliente.clean_nombre_completo
    clean_telefono_pais = FormularioRegistroCliente.clean_telefono_pais
    clean_telefono_area = FormularioRegistroCliente.clean_telefono_area
    clean_telefono_numero = FormularioRegistroCliente.clean_telefono_numero
    clean_codigo_postal = FormularioRegistroCliente.clean_codigo_postal
    clean_localidad = FormularioRegistroCliente.clean_localidad
    _validar_telefono_completo = FormularioRegistroCliente._validar_telefono_completo
    _validar_direccion_completa = FormularioRegistroCliente._validar_direccion_completa
    _validar_codigo_postal_con_provincia = (
        FormularioRegistroCliente._validar_codigo_postal_con_provincia
    )

    def clean(self):
        datos = super().clean()
        self._validar_telefono_completo(datos)
        self._validar_direccion_completa(datos)
        self._validar_codigo_postal_con_provincia(datos)
        return datos

    def save(self, commit=True):
        usuario = super().save(commit=False)
        usuario.first_name, usuario.last_name = partir_nombre(self.cleaned_data["nombre_completo"])
        if commit:
            usuario.save()
        return usuario


class BajaDeCuentaForm(forms.Form):
    """`CO-113`: la contraseña actual, como verificación de identidad (paso 4)."""

    contrasena = forms.CharField(
        label="Tu contraseña actual",
        strip=False,
        widget=forms.PasswordInput(attrs={"autocomplete": "current-password"}),
    )


class CambioDeCorreoForm(forms.Form):
    """`CO-109`: la contraseña actual y el correo nuevo.

    El correo nuevo no puede ser de ninguna cuenta, en cualquier estado (I-10).
    Ese rechazo tiene código propio: la pantalla ofrece recuperar la contraseña
    (E1), y ningún otro error tiene que ver con eso.
    """

    contrasena_actual = forms.CharField(
        label="Contraseña actual",
        strip=False,
        widget=forms.PasswordInput(attrs={"autocomplete": "current-password"}),
    )
    correo_nuevo = forms.EmailField(
        label="Correo nuevo",
        max_length=254,
        widget=forms.EmailInput(attrs={"autocomplete": "email"}),
    )

    def __init__(self, usuario, *args, **kwargs):
        self.usuario = usuario
        super().__init__(*args, **kwargs)

    def clean_contrasena_actual(self):
        contrasena = self.cleaned_data["contrasena_actual"]
        if not self.usuario.check_password(contrasena):
            raise ValidationError("La contraseña actual no coincide.", code="contrasena")
        return contrasena

    def clean_correo_nuevo(self):
        correo = self.cleaned_data["correo_nuevo"].strip().lower()
        if correo == self.usuario.email:
            raise ValidationError("Ese ya es el correo de tu cuenta.", code="mismo")
        if Usuario.objects.filter(email__iexact=correo).exists():
            raise ValidationError(MENSAJE_CORREO_YA_REGISTRADO, code="correo_en_uso")
        return correo

    @property
    def correo_ya_registrado(self):
        return any(e.code == "correo_en_uso" for e in self.errors.as_data().get("correo_nuevo", []))
