"""I-05, I-06 e I-09 en la base (plan 00 de cierre de deuda, D3).

Las tres vivían en `clean()` o en el validador del campo, así que una escritura que
no pasara por el formulario —la propagación de precios con `update()`, un
`bulk_update()`, SQL directo— podía romperlas. El modelo de dominio las declara
«verdaderas antes y después de todas» las operaciones (§ 6).

- **I-09**: el precio de venta y el PVP de la tabla son mayores que cero; el precio
  base y el costo en origen, no negativos. Restricciones de fila.
- **I-06**: el no editorial no está en Pre-venta ni Cancelado por editorial. El
  rubro vive en la misma tabla (`clase`), así que también es una restricción de
  fila.
- **I-05**: el tipo es del mismo rubro que el producto. El rubro del tipo está en
  otra tabla y una restricción no la alcanza: lo cierran dos disparadores, uno
  sobre el producto (alta o cambio de tipo) y otro sobre el tipo (cambio de
  rubro). Son inmediatos: el producto ya trae su rubro al insertarse, así que no
  hace falta esperar a la tabla hija.

La base de desarrollo no tenía ninguna fila que las violara (2026-10-23).
"""

from django.db import migrations, models

CREAR_I05 = """
CREATE OR REPLACE FUNCTION longbox_producto_tipo_del_rubro() RETURNS trigger AS $$
DECLARE
    rubro_del_tipo varchar;
BEGIN
    SELECT clase INTO rubro_del_tipo FROM catalog_tipo WHERE id = NEW.tipo_id;
    IF rubro_del_tipo IS DISTINCT FROM NEW.clase THEN
        RAISE EXCEPTION 'El tipo de un producto pertenece al mismo rubro que el producto (I-05).'
            USING ERRCODE = 'check_violation';
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER producto_tipo_del_rubro
    BEFORE INSERT OR UPDATE OF tipo_id, clase ON catalog_producto
    FOR EACH ROW EXECUTE FUNCTION longbox_producto_tipo_del_rubro();

CREATE OR REPLACE FUNCTION longbox_tipo_conserva_su_rubro() RETURNS trigger AS $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM catalog_producto WHERE tipo_id = NEW.id AND clase <> NEW.clase
    ) THEN
        RAISE EXCEPTION 'El rubro de un tipo con productos no cambia (I-05).'
            USING ERRCODE = 'check_violation';
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER tipo_conserva_su_rubro
    BEFORE UPDATE OF clase ON catalog_tipo
    FOR EACH ROW WHEN (OLD.clase IS DISTINCT FROM NEW.clase)
    EXECUTE FUNCTION longbox_tipo_conserva_su_rubro();
"""

QUITAR_I05 = """
DROP TRIGGER IF EXISTS tipo_conserva_su_rubro ON catalog_tipo;
DROP FUNCTION IF EXISTS longbox_tipo_conserva_su_rubro();
DROP TRIGGER IF EXISTS producto_tipo_del_rubro ON catalog_producto;
DROP FUNCTION IF EXISTS longbox_producto_tipo_del_rubro();
"""


class Migration(migrations.Migration):

    dependencies = [
        ("catalog", "0023_precio_manual_sin_referencia"),
        ("suppliers", "0005_ayudas_de_pantalla"),
    ]

    operations = [
        migrations.AddConstraint(
            model_name="producto",
            constraint=models.CheckConstraint(
                condition=models.Q(("precio__gt", 0)), name="producto_precio_positivo"
            ),
        ),
        migrations.AddConstraint(
            model_name="producto",
            constraint=models.CheckConstraint(
                condition=models.Q(
                    ("clase", "no_editorial"),
                    ("estado__in", ["pre_venta", "cancelado_editorial"]),
                    _negated=True,
                ),
                name="producto_no_editorial_sin_preventa_ni_cancelado",
            ),
        ),
        migrations.AddConstraint(
            model_name="productoeditorial",
            constraint=models.CheckConstraint(
                condition=models.Q(
                    ("precio_base__gte", 0),
                    models.Q(
                        ("costo_origen__isnull", True), ("costo_origen__gte", 0), _connector="OR"
                    ),
                ),
                name="producto_editorial_importes_no_negativos",
            ),
        ),
        migrations.AddConstraint(
            model_name="tablaprecioreferencia",
            constraint=models.CheckConstraint(
                condition=models.Q(("pvp__gt", 0)), name="precio_referencia_pvp_positivo"
            ),
        ),
        migrations.RunSQL(CREAR_I05, reverse_sql=QUITAR_I05),
    ]
