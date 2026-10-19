"""Los artículos de despacho diferido que llegaron antes de este módulo (plan 18).

Hasta acá quedaban «Disponible · Despacho diferido» en su pedido sin un lugar
donde seguir. Pasan a ser artículos retenidos, uno por unidad, con el plazo de
Parámetros contado desde hoy: no se sabe cuándo llegaron.
"""

import calendar
from datetime import date

from django.db import migrations
from django.utils import timezone


def _sumar_meses(dia, meses):
    anio, mes = divmod(dia.month - 1 + meses, 12)
    anio, mes = dia.year + anio, mes + 1
    return date(anio, mes, min(dia.day, calendar.monthrange(anio, mes)[1]))


def retener(apps, schema_editor):
    LineaPedido = apps.get_model("pedidos", "LineaPedido")
    ArticuloRetenido = apps.get_model("almacen", "ArticuloRetenido")
    ConfiguracionSistema = apps.get_model("core", "ConfiguracionSistema")
    configuracion = ConfiguracionSistema.objects.first()
    meses = configuracion.plazo_retencion_meses if configuracion else 3
    hoy = timezone.localdate()
    vence = _sumar_meses(hoy, meses)
    lineas = LineaPedido.objects.filter(
        estado="disponible", decision_demora="despacho_diferido", pedido__usuario__isnull=False
    ).select_related("pedido")
    for linea in lineas:
        if ArticuloRetenido.objects.filter(linea_pedido=linea).exists():
            continue
        for _ in range(linea.cantidad):
            ArticuloRetenido.objects.create(
                usuario_id=linea.pedido.usuario_id,
                producto_id=linea.producto_id,
                linea_pedido=linea,
                valor=linea.precio_unitario,
                fecha_ingreso=hoy,
                fecha_vencimiento=vence,
                estado="disponible",
            )


class Migration(migrations.Migration):
    dependencies = [
        ("almacen", "0001_initial"),
        ("core", "0033_configuracionsistema_dias_aviso_retencion_and_more"),
        ("pedidos", "0005_transaccionpago_solicitud_and_more"),
    ]

    operations = [migrations.RunPython(retener, migrations.RunPython.noop)]
