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


def celda_csv(valor):
    """Una celda de CSV que la planilla no pueda interpretar como fórmula.

    Un texto que empieza con `=`, `+`, `-` o `@` se ejecutaría al abrir el
    archivo (inyección de fórmulas). Se antepone un apóstrofo, que la planilla
    muestra como texto (B-16-003). Lo usan las dos exportaciones del sistema.
    """
    texto = "" if valor is None else str(valor)
    if texto[:1] in ("=", "+", "-", "@", "\t", "\r"):
        return "'" + texto
    return texto
