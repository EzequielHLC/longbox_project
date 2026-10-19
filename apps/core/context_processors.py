from django.urls import reverse
from django.utils.functional import SimpleLazyObject

# Cuánto antes del vencimiento se le avisa al usuario (CU-AUT-INI, comportamiento
# adicional: "cuando falten 5 minutos para que la sesión expire").
AVISO_PREVIO_SEGUNDOS = 5 * 60


def sesion(request):
    from apps.core.sesion import segundos_de_sesion

    return {
        "sesion_duracion_segundos": SimpleLazyObject(segundos_de_sesion),
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


def accesos_tienda(request):
    """La cinta de accesos de la tienda y el globo de preguntas frecuentes (B-07-012).

    Perezosos: sólo consultan la base si la plantilla los usa. El mostrador no
    los dibuja y no paga nada por ellos.
    """
    return {
        "accesos_tienda": SimpleLazyObject(lambda: _accesos(request)),
        "hay_faq": SimpleLazyObject(_hay_faq),
    }


def _hay_faq():
    from apps.core.models import ContenidoFAQ

    return bool(ContenidoFAQ.obtener().contenido.strip())


def _accesos(request):
    """«Novedades», «Pre-ventas» y una entrada por fila activa de la portada.

    Cada fila lleva al catálogo con el mismo filtro que su «Ver todo». La entrada
    actual es la que coincide con la dirección pedida.
    """
    from apps.core.models import FilaPortada

    catalogo = reverse("core:tienda_catalogo")
    accesos = [
        ("Novedades", f"{catalogo}?estado=todos"),
        ("Pre-ventas", f"{catalogo}?estado=pre_venta"),
    ]
    filas = FilaPortada.objects.filter(activa=True).select_related("etiqueta__grupo", "grupo")
    for fila in filas:
        if not fila.disponible:
            continue
        filtro = f"etiqueta={fila.etiqueta_id}" if fila.etiqueta_id else f"grupo={fila.grupo_id}"
        accesos.append((fila.titulo_visible, f"{catalogo}?{filtro}&estado=todos"))
    pedido = request.get_full_path()
    return [{"texto": texto, "url": url, "actual": url == pedido} for texto, url in accesos]
