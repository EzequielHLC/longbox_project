"""El carnet de cliente de «Mi cuenta» (plan 00 de interfaz, 4.3).

Va en todas las pantallas de la cuenta: el código para dictar en el mostrador,
el saldo de puntos con su próximo vencimiento y lo que el local guarda a su
nombre. Son lecturas; no cambian nada.
"""

from django import template

from apps.almacen.servicios import del_cliente
from apps.puntos import servicios as puntos
from apps.puntos.caducidad import usable_hasta
from apps.puntos.models import LotePuntos

register = template.Library()


@register.inclusion_tag("cuenta/_carnet.html", takes_context=True)
def carnet(context):
    usuario = context["user"]
    proximo = (
        LotePuntos.objects.filter(usuario=usuario, estado=LotePuntos.ACTIVO, disponible__gt=0)
        .order_by("caduca_el", "pk")
        .first()
    )
    guardados = list(del_cliente(usuario))
    return {
        "user": usuario,
        # El retrato del carnet (plan 07, novena parte): las iniciales del nombre,
        # o la primera letra del correo si no lo cargó.
        "iniciales": _iniciales(usuario),
        "saldo": puntos.saldo(usuario),
        "proximo_lote": proximo,
        "proximo_hasta": usable_hasta(proximo) if proximo else None,
        "guardados": len(guardados),
        "guardados_hasta": min(
            (a.fecha_vencimiento for a in guardados if a.fecha_vencimiento), default=None
        ),
        "seccion": context.get("seccion", ""),
    }


def _iniciales(usuario):
    partes = [p for p in (usuario.first_name, usuario.last_name) if p and p.strip()]
    if partes:
        return "".join(p.strip()[0] for p in partes).upper()
    return (usuario.email or "?")[0].upper()
