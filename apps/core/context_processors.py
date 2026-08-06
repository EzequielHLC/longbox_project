from django.conf import settings

# Cuánto antes del vencimiento se le avisa al usuario (CU-46, comportamiento
# adicional: "cuando falten 5 minutos para que la sesión expire").
AVISO_PREVIO_SEGUNDOS = 5 * 60


def sesion(request):
    return {
        "sesion_duracion_segundos": settings.SESSION_COOKIE_AGE,
        "sesion_aviso_previo_segundos": AVISO_PREVIO_SEGUNDOS,
    }
