def obtener_ip(request):
    """IP del cliente que originó el request.

    Se usa `REMOTE_ADDR` a propósito: `X-Forwarded-For` lo puede falsear
    cualquiera y acá la IP alimenta el bloqueo por intentos fallidos. Cuando
    el sistema quede detrás de un proxy en producción, hay que leer la
    cabecera correcta y confiar solo en el proxy propio.
    """
    if request is None:
        return None
    return request.META.get("REMOTE_ADDR")
