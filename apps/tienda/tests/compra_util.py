"""Lo que comparten las pruebas de la compra: el escenario y los pasos por la dirección real."""

from datetime import timedelta
from decimal import Decimal

from django.urls import reverse
from django.utils import timezone

from apps.accounts.tests.factories import UsuarioFactory
from apps.catalog.tests.factories import ProductoFactory
from apps.core.models import ConfiguracionSistema
from apps.puntos.models import LotePuntos
from apps.tienda.models import CobroEnCurso
from apps.tienda.pasarelas import PasarelaDePrueba

URL_PAGAR = reverse("compra:pagar")
URL_CHECKOUT = reverse("compra:checkout")
URL_CONFIRMAR = reverse("compra:confirmar")
URL_CANJE_LISTO = reverse("compra:canje_listo")
URL_INVITADO = reverse("compra:invitado")
URL_INVITADO_RESUMEN = reverse("compra:invitado_resumen")
URL_INVITADO_CONFIRMAR = reverse("compra:invitado_confirmar")
URL_AVISO_PRUEBA = reverse("compra:aviso", args=["prueba"])

COSTO_ENVIO = Decimal("1500")
MINIMO_GRATIS = Decimal("50000")
EQUIVALENCIA = Decimal("10")
PORCENTAJE = Decimal("10")

DIRECCION_PERFIL = {
    "direccion": "Av. Colón 1234",
    "depto": "",
    "localidad": "Córdoba",
    "provincia": "Córdoba",
    "codigo_postal": "X5000ABC",
}
OTRA_DIRECCION = {
    "direccion": "San Martín 50",
    "depto": "2 B",
    "localidad": "Posadas",
    "provincia": "Misiones",
    "codigo_postal": "N3300ABC",
}


def fijar_parametros(**cambios):
    configuracion = ConfiguracionSistema.obtener()
    valores = {
        "costo_envio": COSTO_ENVIO,
        "monto_minimo_envio_gratuito": MINIMO_GRATIS,
        "equivalencia_puntos": EQUIVALENCIA,
        "porcentaje_puntos": PORCENTAJE,
        "caducidad_puntos_meses": 12,
        "pasarela": ConfiguracionSistema.PASARELA_PRUEBA,
        **cambios,
    }
    for campo, valor in valores.items():
        setattr(configuracion, campo, valor)
    configuracion.save()
    return configuracion


def cliente_con_direccion(**extra):
    return UsuarioFactory(rol="cliente", **{**DIRECCION_PERFIL, **extra})


def producto(stock=5, precio="10000", **extra):
    return ProductoFactory(stock=stock, precio=Decimal(precio), **extra)


def dar_puntos(usuario, cantidad, *, dias=200):
    return LotePuntos.objects.create(
        usuario=usuario,
        cantidad_acreditada=cantidad,
        disponible=cantidad,
        origen=LotePuntos.AJUSTE_MANUAL,
        caduca_el=timezone.localdate() + timedelta(days=dias),
    )


def agregar(client, prod, cantidad=1):
    return client.post(reverse("tienda:agregar", args=[prod.pk]), {"cantidad": cantidad})


def confirmar(client):
    """`CO-088` por la dirección real; devuelve el cobro que quedó congelado."""
    respuesta = client.post(URL_CONFIRMAR)
    return respuesta, CobroEnCurso.objects.order_by("-pk").first()


def aviso_firmado(cobro, *, aprobado=True, monto=None, mensaje=""):
    """El cuerpo y la cabecera de un aviso de la pasarela de prueba."""
    prueba = PasarelaDePrueba()
    if monto is not None:
        original = cobro.monto
        cobro.monto = Decimal(monto)
        cuerpo, firma = prueba.armar_aviso(cobro, aprobado=aprobado, mensaje=mensaje)
        cobro.monto = original
    else:
        cuerpo, firma = prueba.armar_aviso(cobro, aprobado=aprobado, mensaje=mensaje)
    return cuerpo, firma


def avisar(client, cobro, **kwargs):
    """`CO-089` por la dirección real del webhook."""
    cuerpo, firma = aviso_firmado(cobro, **kwargs)
    return client.post(
        URL_AVISO_PRUEBA,
        data=cuerpo,
        content_type="application/json",
        HTTP_X_FIRMA_PASARELA=firma,
    )
