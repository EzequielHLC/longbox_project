"""Artículos retenidos armados a mano para las pruebas del módulo 18."""

from datetime import timedelta
from decimal import Decimal

from django.utils import timezone

from apps.almacen.models import ArticuloRetenido, SolicitudDespacho
from apps.catalog.tests.factories import ProductoFactory

ENVIO = {
    "direccion": "Av. Colón 1234",
    "depto": "",
    "localidad": "Córdoba",
    "provincia": "Córdoba",
    "codigo_postal": "X5000ABC",
}


def retenido(usuario, *, vence_en=60, valor="10000", producto=None, estado=None, solicitud=None):
    """Un artículo Disponible (o en el estado pedido) que vence dentro de `vence_en` días."""
    hoy = timezone.localdate()
    if estado == ArticuloRetenido.PENDIENTE_DESPACHO and solicitud is None:
        solicitud = solicitud_de(usuario)
    return ArticuloRetenido.objects.create(
        usuario=usuario,
        producto=producto or ProductoFactory(stock=0, precio=Decimal(valor)),
        valor=Decimal(valor),
        fecha_ingreso=hoy - timedelta(days=30),
        fecha_vencimiento=hoy + timedelta(days=vence_en),
        estado=estado or ArticuloRetenido.DISPONIBLE,
        solicitud=solicitud,
    )


def solicitud_de(usuario, costo="0"):
    return SolicitudDespacho.objects.create(
        usuario=usuario,
        envio_direccion=ENVIO["direccion"],
        envio_localidad=ENVIO["localidad"],
        envio_provincia=ENVIO["provincia"],
        envio_codigo_postal=ENVIO["codigo_postal"],
        costo_envio=Decimal(costo),
    )
