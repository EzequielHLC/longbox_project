"""Cotización del peso argentino frente a las monedas con las que se importa.

Fuente: `open.er-api.com`, la cara gratuita y sin credenciales de ExchangeRate-API.

Sobre la elección, para que quede asentada: el Banco Central publica la
Comunicación "A" 3500 pero no la ofrece como API abierta y estable, y las
alternativas locales (dólar blue, MEP) cotizan un mercado que no es el que se
usa para pagar una factura de importación. Este servicio devuelve la paridad de
referencia de las tres monedas que el negocio necesita, sin registrarse.

Se pide **una sola vez** con base en dólares y las otras dos salen por paridad
cruzada. Tres pedidos —uno por moneda— multiplicarían por tres la espera cuando
la caché está vacía, y RNF-02 pide respuesta en dos segundos.

Misma política de tres capas que el resto (`apps/core/integraciones.py`), con
una diferencia que importa: **una cotización vieja no es como una provincia
vieja**. Las provincias no cambian; el tipo de cambio sí, todos los días. Por
eso acá el respaldo viaja con su fecha, la pantalla la muestra, y el valor que
se ofrece es siempre una **sugerencia editable**: el que manda es el que el
Administrador pagó de verdad, que casi nunca coincide con el de referencia.
"""

from datetime import date, datetime, timezone
from decimal import Decimal, DivisionByZero, InvalidOperation
from pathlib import Path

from django.conf import settings

from apps.core import integraciones

RUTA_RESPALDO = Path(__file__).resolve().parent / "datos" / "cotizaciones.json"

CLAVE_COTIZACIONES = "cotizaciones:ars"

# La moneda del negocio. Un lote cargado en pesos no se convierte.
MONEDA_LOCAL = "ARS"

# Las únicas monedas con las que la comiquería importa. No es una limitación
# técnica: es el catálogo del negocio, y ofrecer 160 monedas en un desplegable
# para elegir siempre entre tres es ruido.
MONEDAS_EXTRANJERAS = ("USD", "EUR", "JPY")

NOMBRES_DE_MONEDA = {
    MONEDA_LOCAL: "Peso argentino",
    "USD": "Dólar estadounidense",
    "EUR": "Euro",
    "JPY": "Yen japonés",
}

MONEDA_CHOICES = [
    (MONEDA_LOCAL, f"{NOMBRES_DE_MONEDA[MONEDA_LOCAL]} (ARS) — sin conversión"),
    *[(codigo, f"{NOMBRES_DE_MONEDA[codigo]} ({codigo})") for codigo in MONEDAS_EXTRANJERAS],
]

# Cuatro decimales, los mismos que `LoteAlta.cotizacion`: el yen cotiza en el
# orden de los diez pesos y redondearlo a dos perdería precisión real.
PRECISION = Decimal("0.0001")

# A partir de acá el respaldo deja de ser "la última foto" y pasa a ser un dato
# viejo que hay que mirar con desconfianza. Una semana es holgado para un tipo
# de cambio, y es a propósito: la idea no es alarmar todos los días, es avisar
# cuando el número que se está por usar ya no sirve.
DIAS_PARA_CONSIDERARLA_VIEJA = 7


def _a_decimal(valor):
    """Pasa el número del JSON a `Decimal` sin pasar por `float`.

    El servicio devuelve JSON, y `json.loads` construye `float`. Convertir
    desde su representación en texto evita arrastrar el error binario a un
    número que después multiplica precios.
    """
    try:
        return Decimal(str(valor))
    except (InvalidOperation, TypeError):
        return None


def _paridad_cruzada(pesos_por_dolar, unidades_por_dolar):
    """Cuántos pesos vale una unidad de la moneda, partiendo de la base dólar."""
    try:
        return (pesos_por_dolar / unidades_por_dolar).quantize(PRECISION)
    except (DivisionByZero, InvalidOperation, ZeroDivisionError):
        return None


def descargar_cotizaciones():
    """`{"fecha": "AAAA-MM-DD", "valores": {"USD": "…"}}`. Sin caché ni respaldo."""
    datos = integraciones.pedir_json(settings.COTIZACIONES_API_URL, settings.COTIZACIONES_TIMEOUT)
    if not datos or datos.get("result") != "success":
        return {}

    tasas = datos.get("rates") or {}
    pesos_por_dolar = _a_decimal(tasas.get(MONEDA_LOCAL))
    if not pesos_por_dolar or pesos_por_dolar <= 0:
        # Sin la paridad contra el peso no hay nada que calcular, y una
        # cotización en cero o negativa es una respuesta rota, no un dato.
        return {}

    valores = {}
    for codigo in MONEDAS_EXTRANJERAS:
        if codigo == "USD":
            cotizacion = pesos_por_dolar.quantize(PRECISION)
        else:
            unidades_por_dolar = _a_decimal(tasas.get(codigo))
            if not unidades_por_dolar or unidades_por_dolar <= 0:
                continue
            cotizacion = _paridad_cruzada(pesos_por_dolar, unidades_por_dolar)
        if cotizacion and cotizacion > 0:
            # Se guarda como texto: JSON no tiene decimales exactos, y pasar
            # por `float` en el camino de ida y vuelta es justamente lo que se
            # quiere evitar en un dato que multiplica dinero.
            valores[codigo] = str(cotizacion)

    if not valores:
        return {}

    return {"fecha": _fecha_de(datos), "valores": valores}


def _fecha_de(datos):
    """La fecha que declara el servicio, o la de hoy si no la trae."""
    marca = datos.get("time_last_update_unix")
    if marca:
        try:
            return datetime.fromtimestamp(int(marca), tz=timezone.utc).date().isoformat()
        except (ValueError, OSError, OverflowError):
            pass
    return date.today().isoformat()


def obtener_cotizaciones():
    """Las tres cotizaciones vigentes, con su fecha. Siempre devuelve algo."""
    catalogo = integraciones.obtener_con_respaldo(
        clave_cache=CLAVE_COTIZACIONES,
        descargar=descargar_cotizaciones,
        ruta_respaldo=RUTA_RESPALDO,
        clave_respaldo="cotizaciones",
        vigencia=settings.COTIZACIONES_CACHE_SEGUNDOS,
    )
    return catalogo if isinstance(catalogo, dict) else {}


def cotizacion_de(moneda):
    """Los pesos que vale una unidad de `moneda`, o `None` si no se conoce.

    El peso vale un peso: la moneda local no se convierte y no depende de que
    ningún servicio externo esté en línea.
    """
    if not moneda or moneda == MONEDA_LOCAL:
        return Decimal("1")
    valor = obtener_cotizaciones().get("valores", {}).get(moneda)
    return _a_decimal(valor)


def fecha_de_cotizacion():
    """La fecha del juego de cotizaciones que se está usando, o `None`."""
    texto = obtener_cotizaciones().get("fecha")
    try:
        return date.fromisoformat(texto) if texto else None
    except ValueError:
        return None


def esta_desactualizada():
    """Si el dato que se está por ofrecer ya tiene demasiados días encima."""
    fecha = fecha_de_cotizacion()
    if fecha is None:
        return True
    return (date.today() - fecha).days > DIAS_PARA_CONSIDERARLA_VIEJA


def resumen_para_pantalla():
    """Lo que la pantalla de alta necesita saber, ya masticado."""
    catalogo = obtener_cotizaciones()
    return {
        "valores": catalogo.get("valores", {}),
        "fecha": fecha_de_cotizacion(),
        "desactualizada": esta_desactualizada(),
    }


def guardar_respaldo(datos):
    integraciones.guardar_respaldo(RUTA_RESPALDO, datos)


SIMBOLOS = {"USD": "US$", "EUR": "€", "JPY": "¥"}


def equivalencias(importe_en_pesos, valores=None):
    """Lo que vale un importe en pesos en cada moneda extranjera, como referencia.

    Es sólo informativo (B-03-006): el precio sigue siendo en pesos. Se divide
    por la cotización de referencia del día —no por la que el Administrador
    pagó en un lote, que es otra— y se redondea a centavos, salvo el yen, que
    no tiene. Una moneda sin cotización conocida no se informa.
    """
    if valores is None:
        valores = obtener_cotizaciones().get("valores", {})
    resultado = []
    for moneda in MONEDAS_EXTRANJERAS:
        cotizacion = _a_decimal(valores.get(moneda))
        if not cotizacion or cotizacion <= 0:
            continue
        paso = Decimal("1") if moneda == "JPY" else Decimal("0.01")
        valor = (Decimal(importe_en_pesos) / cotizacion).quantize(paso)
        resultado.append({"moneda": moneda, "simbolo": SIMBOLOS[moneda], "valor": valor})
    return resultado
