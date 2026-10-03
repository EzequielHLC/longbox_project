from django.conf import settings

# Cuánto antes del vencimiento se le avisa al usuario (CU-AUT-INI, comportamiento
# adicional: "cuando falten 5 minutos para que la sesión expire").
AVISO_PREVIO_SEGUNDOS = 5 * 60


def sesion(request):
    return {
        "sesion_duracion_segundos": settings.SESSION_COOKIE_AGE,
        "sesion_aviso_previo_segundos": AVISO_PREVIO_SEGUNDOS,
    }


def identidad_tienda(request):
    """La identidad visual de la tienda, para la cáscara pública (CU-CFG-VIS).

    Sólo cuando el Administrador la guardó alguna vez: hasta entonces la tienda
    se dibuja con los tokens, sin hoja extra ni pie de contacto.
    """
    from apps.core.models import IdentidadVisual

    identidad = IdentidadVisual.obtener()
    return {
        # La hoja de colores, el logo y el contacto sólo cuando se configuró.
        "identidad_tienda": identidad if identidad.configurada else None,
        # Los textos del escaparate siempre: tienen valores iniciales propios.
        "textos_tienda": identidad,
    }
