"""La aritmética de precios de RF-10, sin Django de por medio.

Vive aparte de los modelos y de las vistas a propósito: es la parte del módulo
que hay que poder probar sola, con una tabla de casos, sin base de datos ni
formularios. La fórmula es corta pero encadena tres multiplicaciones, y ahí es
donde el redondeo empieza a importar.

**Decisiones de redondeo** (no están en la documentación de casos de uso; se
resolvieron al implementar, ver `# Agregados` del módulo):

- Todo el dinero es `Decimal`, nunca `float`. Un `float` no puede representar
  0,10 exactamente, y en un sistema que suma precios eso se acumula.
- El **precio base** conserva centavos: es un valor intermedio que se almacena
  para recalcular después (CU-13), así que redondearlo de más arrastraría el
  error a cada recálculo futuro.
- El **precio final** se redondea al peso: es el número que se cobra, y en una
  comiquería nadie cobra centavos.
- El **CRE** no es dinero sino un cociente, y se guarda con seis decimales por
  el mismo motivo: es un factor que multiplica a todos los ítems del lote.
"""

from decimal import ROUND_HALF_UP, Decimal, DivisionByZero, InvalidOperation

UN_CENTAVO = Decimal("0.01")
UN_PESO = Decimal("1")
PRECISION_CRE = Decimal("0.000001")

# Cuando el lote no declara moneda extranjera, los importes ya vienen en pesos.
SIN_CONVERSION = Decimal("1")


def redondear_a_centavos(valor):
    """Redondeo a dos decimales, con el medio centavo para arriba."""
    return Decimal(valor).quantize(UN_CENTAVO, rounding=ROUND_HALF_UP)


def redondear_a_peso(valor):
    """Redondeo al peso entero, con el medio peso para arriba.

    Devuelve igual dos decimales (`1234.00`) porque el campo del modelo los
    tiene: lo que se redondea es el valor, no el formato de almacenamiento.
    """
    entero = Decimal(valor).quantize(UN_PESO, rounding=ROUND_HALF_UP)
    return entero.quantize(UN_CENTAVO)


def calcular_cre(costo_envio_total, valor_compra_total):
    """CRE = costo total de envío ÷ valor total de compra (RF-10, paso 1).

    Como es un cociente entre dos importes del mismo lote, la moneda se
    simplifica: da lo mismo declararlos en dólares o en pesos mientras los dos
    estén en la misma. Por eso la conversión no entra acá.

    Un valor de compra en cero no es un error del Administrador que haya que
    hacerle explotar en la cara: significa que no hay contra qué prorratear el
    envío, y el CRE es cero. Quien quiera prohibirlo lo valida en el formulario.
    """
    try:
        cre = Decimal(costo_envio_total) / Decimal(valor_compra_total)
    except (DivisionByZero, InvalidOperation, ZeroDivisionError):
        return Decimal("0").quantize(PRECISION_CRE)
    return cre.quantize(PRECISION_CRE, rounding=ROUND_HALF_UP)


def convertir_a_pesos(importe, cotizacion=SIN_CONVERSION):
    """Pasa un importe de la moneda de origen a pesos.

    **Agregado a la documentación de casos de uso.** La fuente dice "costo base
    en origen" y no menciona conversión ni cotización en ningún lado. Cuando el
    lote no declara moneda extranjera, la cotización es 1 y esta función no
    hace nada: la fórmula de RF-10 queda exactamente como está escrita.
    """
    return redondear_a_centavos(Decimal(importe) * Decimal(cotizacion or SIN_CONVERSION))


def calcular_precio_base(costo_origen, cre, cotizacion=SIN_CONVERSION):
    """Precio base = costo base en origen × (1 + CRE) (RF-10, paso 2)."""
    costo = convertir_a_pesos(costo_origen, cotizacion)
    return redondear_a_centavos(costo * (Decimal("1") + Decimal(cre)))


def calcular_precio_final(precio_base, margen):
    """Precio final = precio base × (1 + margen global) (RF-10, paso 3).

    Es también la fórmula del recálculo de CU-13: dado un margen nuevo, el
    precio final sale del precio base almacenado, sin los datos del lote.
    """
    return redondear_a_peso(Decimal(precio_base) * (Decimal("1") + Decimal(margen)))


def desglose_importado(costo_origen, cre, margen, cotizacion=SIN_CONVERSION):
    """Los tres valores que CU-02 paso 6 exige mostrar de forma explícita.

    Devuelve `(costo_en_pesos, precio_base, precio_final)`. Se calculan juntos
    porque la pantalla los muestra juntos, y porque calcular el final por su
    cuenta —`costo × (1 + CRE) × (1 + margen)` de una sola tirada— daría un
    número distinto del que resulta de encadenar los redondeos, y sería el que
    no coincide con el desglose que el Administrador tiene delante.
    """
    costo = convertir_a_pesos(costo_origen, cotizacion)
    precio_base = calcular_precio_base(costo_origen, cre, cotizacion)
    return costo, precio_base, calcular_precio_final(precio_base, margen)
