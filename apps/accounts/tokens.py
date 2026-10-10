"""Tokens de un solo uso para los enlaces que se mandan por correo.

El proyecto necesita dos vigencias distintas sobre el *mismo* mecanismo:
30 minutos para el enlace de recuperación de contraseña (CU-AUT-REC) y 48 horas
para el de activación de una cuenta nueva (CU-USR-ALT). Django resuelve la vigencia
con un único setting global (`PASSWORD_RESET_TIMEOUT`), así que acá se lo deja
como tope máximo y cada generador aplica encima su propia ventana, más corta.

No se toca `key_salt`: los tokens que emite `TokenConVigencia` son idénticos a
los del generador por defecto de Django, lo que cambia es hasta cuándo se
aceptan.
"""

from django.conf import settings
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.http import base36_to_int


class TokenConVigencia(PasswordResetTokenGenerator):
    """Generador de tokens con una vigencia propia, en segundos."""

    def __init__(self, vigencia_segundos):
        super().__init__()
        self.vigencia_segundos = vigencia_segundos

    def check_token(self, user, token):
        # `super()` verifica la firma (que el token no fue manipulado y que
        # todavía no se usó) y el tope de `PASSWORD_RESET_TIMEOUT`; acá arriba
        # solo se acorta la ventana.
        if not super().check_token(user, token):
            return False
        return self._segundos_desde_la_emision(token) <= self.vigencia_segundos

    def _segundos_desde_la_emision(self, token):
        # El formato ya lo validó `super().check_token()`.
        marca_de_tiempo, _, _ = token.partition("-")
        return self._num_seconds(self._now()) - base36_to_int(marca_de_tiempo)


# CU-AUT-REC — "Recuperá tu contraseña": 30 minutos.
token_de_recuperacion = TokenConVigencia(settings.VIGENCIA_ENLACE_RECUPERACION)

# CU-USR-ALT — "Activá tu cuenta": 48 horas.
token_de_activacion = TokenConVigencia(settings.VIGENCIA_ENLACE_ACTIVACION)


class TokenDeCambioDeCorreo(TokenConVigencia):
    """El token del enlace que confirma un correo nuevo (CU-CLI-DAT A1, `CO-110`).

    Usa su propia sal —un token de recuperación no tiene que servir para cambiar
    el correo— y firma también el correo pedido y la fila que lo guarda: pedir
    otro cambio invalida el enlace anterior. Como el hash de Django incluye el
    correo de la cuenta, el enlace deja de servir en cuanto se usa.
    """

    key_salt = "longbox.accounts.cambio-de-correo"

    def _make_hash_value(self, user, timestamp):
        from apps.accounts.models import TokenCambioCorreo

        pendiente = TokenCambioCorreo.vigente_de(user)
        propio = f"{pendiente.pk}{pendiente.correo_nuevo}" if pendiente else ""
        return super()._make_hash_value(user, timestamp) + propio


# CU-CLI-DAT A1 — "Confirmá tu correo nuevo": 24 horas.
token_de_cambio_de_correo = TokenDeCambioDeCorreo(settings.VIGENCIA_CAMBIO_CORREO)
