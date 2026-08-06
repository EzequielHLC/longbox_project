from django import forms
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.forms import AuthenticationForm
from django.core.exceptions import ValidationError

from apps.accounts import services
from apps.core.utils import obtener_ip

Usuario = get_user_model()

# Mensaje único para credenciales inválidas: no distingue si falló el correo o
# la contraseña, ni revela si la cuenta existe (CU-46, excepción 1).
MENSAJE_CREDENCIALES = "Correo o contraseña incorrectos"
MENSAJE_CUENTA_INACTIVA = "Esta cuenta no está disponible"
MENSAJE_BLOQUEO = (
    "Superaste la cantidad de intentos permitidos. El acceso quedó bloqueado "
    "temporalmente y enviamos un aviso al correo registrado."
)


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
