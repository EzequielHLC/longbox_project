"""RF-10 — la aritmética del precio importado.

Son los únicos tests del módulo que no tocan la base: la fórmula es una función
pura y probarla sola permite recorrer muchos casos sin armar un lote cada vez.
"""

from decimal import Decimal

import pytest

from apps.catalog import precios


def test_el_cre_es_el_cociente_entre_el_envio_y_la_compra():
    assert precios.calcular_cre(Decimal("10000"), Decimal("100000")) == Decimal("0.100000")


def test_el_cre_se_guarda_con_seis_decimales():
    """Es un factor que multiplica a todos los ítems: redondearlo a dos
    arrastraría el error del cociente a cada precio del lote."""
    assert precios.calcular_cre(Decimal("1"), Decimal("3")) == Decimal("0.333333")


def test_un_valor_de_compra_en_cero_da_un_cre_de_cero():
    """No hay contra qué prorratear el envío. No es un error que deba explotar."""
    assert precios.calcular_cre(Decimal("5000"), Decimal("0")) == Decimal("0.000000")


def test_la_formula_encadena_costo_cre_y_margen():
    """`precio_final = C × (1 + R) × (1 + M)`, la condición de verificación de RF-10."""
    _, base, final = precios.desglose_importado(
        costo_origen=Decimal("1000"), cre=Decimal("0.1"), margen=Decimal("0.4")
    )

    assert base == Decimal("1100.00")
    assert final == Decimal("1540.00")


@pytest.mark.parametrize(
    ("costo", "cre", "margen", "base_esperada", "final_esperado"),
    [
        # Sin envío ni margen, el precio es el costo.
        (Decimal("2500"), Decimal("0"), Decimal("0"), Decimal("2500.00"), Decimal("2500.00")),
        # Caso con centavos en el intermedio: 1234.56 × 1.075 = 1327.152.
        (
            Decimal("1234.56"),
            Decimal("0.075"),
            Decimal("0.33"),
            Decimal("1327.15"),
            Decimal("1765.00"),
        ),
        # Envío que duplica el costo del lote.
        (Decimal("800"), Decimal("1"), Decimal("0.5"), Decimal("1600.00"), Decimal("2400.00")),
    ],
)
def test_casos_de_la_formula(costo, cre, margen, base_esperada, final_esperado):
    _, base, final = precios.desglose_importado(costo, cre, margen)

    assert base == base_esperada
    assert final == final_esperado


def test_el_precio_base_conserva_centavos():
    """Es el valor que se persiste para recalcular en CU-PVP-MAR: redondearlo al peso
    metería el error del redondeo dentro de cada recálculo futuro."""
    base = precios.calcular_precio_base(Decimal("1234.56"), Decimal("0.075"))

    assert base == Decimal("1327.15")


def test_el_precio_final_se_redondea_al_peso():
    final = precios.calcular_precio_final(Decimal("1327.15"), Decimal("0.33"))

    assert final == Decimal("1765.00")


@pytest.mark.parametrize(
    ("valor", "esperado"),
    [
        (Decimal("100.49"), Decimal("100.00")),
        (Decimal("100.50"), Decimal("101.00")),
        (Decimal("100.51"), Decimal("101.00")),
    ],
)
def test_el_medio_peso_redondea_para_arriba(valor, esperado):
    assert precios.redondear_a_peso(valor) == esperado


def test_sin_cotizacion_el_importe_ya_esta_en_pesos():
    assert precios.convertir_a_pesos(Decimal("1500")) == Decimal("1500.00")


def test_la_cotizacion_convierte_el_costo_en_origen_a_pesos():
    """Agregado a la fuente: el CU habla de 'costo base en origen' sin decir en
    qué moneda. Con cotización declarada, el sistema convierte."""
    assert precios.convertir_a_pesos(Decimal("10"), Decimal("1200")) == Decimal("12000.00")


def test_el_desglose_convierte_antes_de_aplicar_el_cre():
    costo, base, final = precios.desglose_importado(
        costo_origen=Decimal("10"),
        cre=Decimal("0.2"),
        margen=Decimal("0.5"),
        cotizacion=Decimal("1000"),
    )

    assert costo == Decimal("10000.00")
    assert base == Decimal("12000.00")
    assert final == Decimal("18000.00")


def test_el_recalculo_de_cu_13_sale_del_precio_base_almacenado():
    """Ante un margen nuevo, el precio final se recalcula sin los datos del lote.

    Es la mitad de la condición de verificación de RF-10, y lo que justifica que
    `precio_base` se persista.
    """
    base = Decimal("1100.00")

    assert precios.calcular_precio_final(base, Decimal("0.40")) == Decimal("1540.00")
    assert precios.calcular_precio_final(base, Decimal("0.55")) == Decimal("1705.00")
