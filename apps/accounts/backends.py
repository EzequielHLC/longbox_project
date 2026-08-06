from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend

Usuario = get_user_model()


class EmailBackend(ModelBackend):
    """Autentica con correo + contraseña en vez de username + contraseña.

    Solo cambia *cómo se busca* al usuario: la verificación de la contraseña
    la sigue haciendo Django contra el hash almacenado (RNF-04). Los usuarios
    inactivos son rechazados acá por `user_can_authenticate()`, igual que en
    el backend estándar.
    """

    def authenticate(self, request, username=None, password=None, **kwargs):
        email = username or kwargs.get("email")
        if not email or password is None:
            return None
        try:
            usuario = Usuario.objects.get(email__iexact=email)
        except (Usuario.DoesNotExist, Usuario.MultipleObjectsReturned):
            # Se hashea igual una contraseña descartable para que el tiempo de
            # respuesta no revele si el correo existe (timing attack).
            Usuario().set_password(password)
            return None
        if usuario.check_password(password) and self.user_can_authenticate(usuario):
            return usuario
        return None
