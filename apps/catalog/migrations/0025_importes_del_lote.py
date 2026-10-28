"""I-09 en los importes del lote (plan 00 de cierre de deuda, D3).

Los mismos topes que los validadores de `LoteAlta`, ahora también en la base. La
base de desarrollo no tenía ningún lote que los violara (2026-10-23).
"""

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("catalog", "0024_invariantes_en_la_base"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddConstraint(
            model_name="lotealta",
            constraint=models.CheckConstraint(
                condition=models.Q(
                    models.Q(
                        ("costo_envio_total__isnull", True),
                        ("costo_envio_total__gte", 0),
                        _connector="OR",
                    ),
                    models.Q(
                        ("valor_compra_total__isnull", True),
                        ("valor_compra_total__gt", 0),
                        _connector="OR",
                    ),
                    models.Q(("cre__isnull", True), ("cre__gte", 0), _connector="OR"),
                    models.Q(
                        ("margen_aplicado__isnull", True),
                        ("margen_aplicado__gte", 0),
                        _connector="OR",
                    ),
                    models.Q(("cotizacion__isnull", True), ("cotizacion__gt", 0), _connector="OR"),
                ),
                name="lote_importes_no_negativos",
            ),
        ),
    ]
