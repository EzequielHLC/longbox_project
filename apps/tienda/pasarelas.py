"""Las pasarelas de pago, detrás de una sola interfaz (RNF-07; B-07-031).

Cada pasarela sabe tres cosas: **iniciar un cobro** (a dónde se manda al
Cliente), **leer un aviso** (qué resultado trae y si es auténtico) y
**reembolsar**. Lo que hace el sistema con el resultado —`CO-089`— no depende de
cuál sea.

**Un aviso no se cree por sí mismo.** Quien conoce la dirección del aviso puede
mandarle cualquier cosa; sin verificarlo, generar un pedido sin pagar sería
cuestión de un `curl`. La pasarela de prueba firma sus avisos; MercadoPago no
firma igual, y por eso su aviso sólo dice «mirá el pago tal», y el pago se
consulta a su API.
"""

import hmac
import json
import logging
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation

from django.urls import reverse
from django.utils.crypto import salted_hmac

from apps.core.models import ConfiguracionSistema

logger = logging.getLogger(__name__)

CABECERA_FIRMA = "X-Firma-Pasarela"


class AvisoInvalido(ValueError):
    """El aviso no es auténtico o no se entiende: no se procesa."""


@dataclass
class AvisoDePago:
    """Lo que `CO-089` recibe: `registrarResultadoDePago(referencia, resultado, monto)`.

    `referencia` es la del cobro, la que el sistema generó al confirmar.
    `referencia_pago` es la que el pago tiene en la pasarela: es la que queda en
    `TransaccionPago` y la que se usa para reembolsar.
    """

    referencia: str
    referencia_pago: str
    aprobado: bool
    monto: Decimal
    mensaje: str = ""


def _monto(texto):
    try:
        return Decimal(str(texto))
    except (InvalidOperation, TypeError) as error:
        raise AvisoInvalido("El monto del aviso no es un número.") from error


class PasarelaDePrueba:
    """Una pasarela que es parte del sistema: aprueba o rechaza desde una pantalla.

    Firma sus avisos con la clave del sistema. El reembolso no tiene a quién
    pedírselo: queda registrado en el cobro y en el log, que es lo mismo que
    haría una real del lado de la tienda.
    """

    clave = ConfiguracionSistema.PASARELA_PRUEBA
    nombre = "Pasarela de prueba"
    SAL = "longbox.tienda.pasarela-de-prueba"

    def iniciar_cobro(self, cobro, request):
        return reverse("compra:pasarela_prueba", args=[cobro.referencia])

    def firmar(self, cuerpo):
        return salted_hmac(self.SAL, cuerpo, algorithm="sha256").hexdigest()

    def armar_aviso(self, cobro, *, aprobado, mensaje=""):
        """El cuerpo y la firma del aviso que la pantalla de prueba manda al sistema."""
        cuerpo = json.dumps(
            {
                "referencia": cobro.referencia,
                "pago": f"prueba-{cobro.referencia}",
                "resultado": "aprobado" if aprobado else "rechazado",
                "monto": str(cobro.monto),
                "mensaje": mensaje,
            }
        ).encode("utf-8")
        return cuerpo, self.firmar(cuerpo)

    def leer_aviso(self, cuerpo, cabeceras, consulta=""):
        firma = cabeceras.get(CABECERA_FIRMA, "")
        if not firma or not hmac.compare_digest(firma, self.firmar(cuerpo)):
            raise AvisoInvalido("La firma del aviso no es válida.")
        try:
            datos = json.loads(cuerpo)
            return AvisoDePago(
                referencia=str(datos["referencia"]),
                referencia_pago=str(datos["pago"]),
                aprobado=datos["resultado"] == "aprobado",
                monto=_monto(datos["monto"]),
                mensaje=str(datos.get("mensaje", ""))[:300],
            )
        except (ValueError, KeyError, TypeError) as error:
            raise AvisoInvalido("El aviso no tiene el formato esperado.") from error

    def reembolsar(self, cobro, referencia_pago):
        logger.info("Reembolso del cobro %s (%s) en la pasarela de prueba.", cobro, referencia_pago)
        return True


def pasarela(clave=None):
    """La pasarela por su clave, o la que eligió el Administrador en Parámetros."""
    from apps.tienda import mercadopago

    clave = clave or ConfiguracionSistema.obtener().pasarela
    if clave == ConfiguracionSistema.PASARELA_MERCADOPAGO:
        return mercadopago.MercadoPago()
    if clave == ConfiguracionSistema.PASARELA_PRUEBA:
        return PasarelaDePrueba()
    raise AvisoInvalido(f"No hay una pasarela «{clave}».")
