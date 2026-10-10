"""MercadoPago Checkout Pro, detrás de la interfaz de `pasarelas` (B-07-031).

Tres llamadas a su API, todas por `core.integraciones.pedir`, la única puerta
HTTP del proyecto (y la que las pruebas cortan):

1. **Preferencia** (`POST /checkout/preferences`): el cobro por el total, con la
   referencia del sistema como `external_reference` y la dirección del aviso.
   Devuelve `init_point`, a donde se manda al Cliente.
2. **Pago** (`GET /v1/payments/{id}`): el aviso de MercadoPago sólo dice qué
   pago mirar. **El resultado se lee de acá**, no del aviso: un aviso falso
   apunta a un pago que no existe o que no es de esta cuenta, y ahí termina.
3. **Reembolso** (`POST /v1/payments/{id}/refunds`): E3 de la compra.

La credencial es la de la cuenta de prueba del vendedor, en el `.env`
(`MERCADOPAGO_ACCESS_TOKEN`). Sin ella, elegir MercadoPago no inicia cobros.
"""

import json
import logging
from urllib.parse import parse_qs

from django.conf import settings
from django.urls import reverse

from apps.core import integraciones
from apps.tienda.pasarelas import AvisoDePago, AvisoInvalido, _monto

logger = logging.getLogger(__name__)

API = "https://api.mercadopago.com"


class SinCredencial(RuntimeError):
    """MercadoPago está elegido y no hay credencial configurada."""


class AvisoSinResultado(AvisoInvalido):
    """Un aviso que no es de un pago, o de un pago que todavía no se resolvió.

    No es un error: MercadoPago avisa también los pagos pendientes y otros
    temas. Se contesta que se recibió y no se hace nada.
    """


class MercadoPago:
    clave = "mercadopago"
    nombre = "MercadoPago"

    def __init__(self, token=None):
        self.token = token if token is not None else settings.MERCADOPAGO_ACCESS_TOKEN

    def _cabeceras(self, **extra):
        if not self.token:
            raise SinCredencial("Falta MERCADOPAGO_ACCESS_TOKEN en el .env.")
        return {"Authorization": f"Bearer {self.token}", **extra}

    def iniciar_cobro(self, cobro, request):
        resultado = request.build_absolute_uri(reverse("compra:resultado", args=[cobro.referencia]))
        cuerpo = {
            "items": [
                {
                    "id": cobro.referencia,
                    "title": f"Compra en la tienda ({cobro.referencia[:8]})",
                    "quantity": 1,
                    "currency_id": "ARS",
                    # La API pide un número JSON. Es transporte, no aritmética:
                    # el importe ya está calculado en `Decimal` con dos decimales.
                    "unit_price": float(cobro.monto),
                }
            ],
            "external_reference": cobro.referencia,
            "notification_url": request.build_absolute_uri(
                reverse("compra:aviso", args=[self.clave])
            ),
            "back_urls": {"success": resultado, "failure": resultado, "pending": resultado},
            "auto_return": "approved",
        }
        respuesta = integraciones.pedir(
            f"{API}/checkout/preferences",
            timeout=settings.MERCADOPAGO_TIMEOUT,
            metodo="POST",
            cuerpo=cuerpo,
            cabeceras=self._cabeceras(),
        )
        if not respuesta or "init_point" not in respuesta.datos:
            logger.error("MercadoPago no creó la preferencia: %s", respuesta.detalle)
            return None
        cobro.id_externo = str(respuesta.datos.get("id", ""))
        cobro.save(update_fields=["id_externo"])
        return respuesta.datos["init_point"]

    def _id_del_pago(self, cuerpo, consulta):
        """El aviso llega por cuerpo JSON (webhook) o por parámetros (IPN)."""
        try:
            datos = json.loads(cuerpo) if cuerpo else {}
        except ValueError:
            datos = {}
        parametros = {clave: valores[0] for clave, valores in parse_qs(consulta).items()}
        tema = (
            datos.get("type")
            or datos.get("topic")
            or parametros.get("type")
            or parametros.get("topic")
        )
        if tema != "payment":
            raise AvisoSinResultado(f"Aviso de «{tema}»: no es un pago.")
        pago = (
            (datos.get("data") or {}).get("id") or parametros.get("data.id") or parametros.get("id")
        )
        if not pago:
            raise AvisoInvalido("El aviso no dice qué pago mirar.")
        return str(pago)

    def leer_aviso(self, cuerpo, cabeceras, consulta=""):
        pago = self._id_del_pago(cuerpo, consulta)
        respuesta = integraciones.pedir(
            f"{API}/v1/payments/{pago}",
            timeout=settings.MERCADOPAGO_TIMEOUT,
            cabeceras=self._cabeceras(),
        )
        if not respuesta:
            raise AvisoInvalido(f"MercadoPago no confirmó el pago {pago}: {respuesta.detalle}")
        datos = respuesta.datos
        estado = datos.get("status")
        if estado not in ("approved", "rejected", "cancelled"):
            raise AvisoSinResultado(f"El pago {pago} sigue en «{estado}».")
        return AvisoDePago(
            referencia=str(datos.get("external_reference") or ""),
            referencia_pago=f"mp-{pago}",
            aprobado=estado == "approved",
            monto=_monto(datos.get("transaction_amount")),
            mensaje=str(datos.get("status_detail") or "")[:300],
        )

    def reembolsar(self, cobro, referencia_pago):
        pago = referencia_pago.removeprefix("mp-")
        respuesta = integraciones.pedir(
            f"{API}/v1/payments/{pago}/refunds",
            timeout=settings.MERCADOPAGO_TIMEOUT,
            metodo="POST",
            cuerpo={},
            cabeceras=self._cabeceras(**{"X-Idempotency-Key": f"reembolso-{cobro.referencia}"}),
        )
        if not respuesta:
            logger.error("MercadoPago no aceptó el reembolso de %s: %s", pago, respuesta.detalle)
            return False
        return True
