"""`CO-086`: el inicio de sesión fusiona el carrito del invitado.

Va por la señal y no dentro de la vista de inicio de sesión porque la dispara
cualquier camino que autentique: el formulario, la activación de cuenta y el
registro de un Cliente nuevo, que inicia sesión solo.
"""

from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver

from apps.tienda import carrito as servicio
from apps.tienda.models import Carrito


@receiver(user_logged_in, dispatch_uid="tienda_fusionar_carrito")
def fusionar_carrito_de_sesion(sender, request, user, **kwargs):
    if request is None or not hasattr(request, "session"):
        return
    pk = request.session.pop(servicio.CLAVE_DE_SESION, None)
    if pk is None:
        return
    de_sesion = Carrito.objects.filter(pk=pk, usuario__isnull=True).first()
    if de_sesion is None:
        return
    if not servicio.puede_tener_carrito(user):
        # El personal no tiene carrito: lo que eligió como invitado se descarta.
        de_sesion.delete()
        return
    if de_sesion.lineas.exists():
        servicio.fusionar(de_sesion, user)
    else:
        de_sesion.delete()
