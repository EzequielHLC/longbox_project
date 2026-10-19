"""Pedidos despachados, fotos y casos armados a mano para las pruebas del módulo 09."""

from datetime import timedelta
from io import BytesIO

from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone
from PIL import Image

from apps.devoluciones.models import CasoDevolucion
from apps.pedidos.models import LineaPedido, Pedido
from apps.pedidos.tests.util import crear_pedido


def pedido_despachado(usuario, *, hace_dias=1, lineas=(("10000", 1),)):
    """Un pedido online que pasó a Despachado hace `hace_dias` días, con sus líneas despachadas."""
    pedido = crear_pedido(usuario, estado=Pedido.DESPACHADO, lineas=lineas, hace_dias=hace_dias)
    pedido.lineas.update(estado=LineaPedido.DESPACHADO)
    return pedido


def foto(nombre="foto.png", formato="PNG", tamano=(40, 30)):
    salida = BytesIO()
    Image.new("RGB", tamano, (200, 40, 40)).save(salida, formato)
    tipo = {"PNG": "image/png", "JPEG": "image/jpeg", "WEBP": "image/webp"}[formato]
    return SimpleUploadedFile(nombre, salida.getvalue(), content_type=tipo)


def no_imagen(nombre="foto.png"):
    return SimpleUploadedFile(nombre, b"esto no es una imagen", content_type="image/png")


def caso_de(
    usuario, *, pedido=None, motivo=CasoDevolucion.DEFECTO, hace_dias=0, como=None, **linea
):
    """Un caso Pendiente sobre la primera línea de un pedido despachado.

    `como`: un producto con cuya editorial y formato queda el reclamado, para que
    sirva de reemplazo (plan 00, R7).
    """
    pedido = pedido or pedido_despachado(usuario, **linea)
    primera = pedido.lineas.order_by("pk").first()
    if como is not None:
        igualar(primera.producto, como)
    return CasoDevolucion.objects.create(
        linea=primera,
        usuario=usuario,
        correo=usuario.email if usuario else pedido.correo_de_contacto,
        motivo=motivo,
        unidades=primera.cantidad if motivo == CasoDevolucion.ARREPENTIMIENTO else 1,
        descripcion="La tapa vino rota.",
        abierto_en=timezone.now() - timedelta(days=hace_dias),
    )


def igualar(producto, como):
    from apps.catalog.models import ProductoEditorial

    ProductoEditorial.objects.filter(pk=producto.pk).update(
        editorial_id=como.editorial_id, formato_id=como.formato_id
    )
