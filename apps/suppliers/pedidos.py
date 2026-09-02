"""El correo de pedido consolidado a un proveedor (CU-24).

**Es un CU compartido.** Lo invoca CU-05 al cerrar una sesión de revisión, y lo
va a invocar Restock (Módulo 05) cuando exista. Por eso vive acá y no dentro de
la revisión de borradores, y por eso no sabe nada de borradores ni de sesiones:
recibe un proveedor y una lista de líneas, y manda el correo. Quien arma esas
líneas es asunto de quien lo llama.

**Reintenta hasta tres veces.** Lo pide la excepción de CU-05, y el motivo es
que el fallo típico de un envío es transitorio —el servidor SMTP rechazando por
carga, la red cortada un segundo—. Lo que **no** hace es revertir nada: el alta
de los productos y el pedido al proveedor son operaciones separadas, y un correo
que no salió no puede deshacer productos que ya están en el catálogo. Se informa
y se sigue con los demás proveedores.
"""

import logging
from dataclasses import dataclass

from apps.core.mail import enviar_correo

logger = logging.getLogger(__name__)

# Tres, como pide CU-05. No es un número mágico elegido por gusto: con un solo
# intento un corte de un segundo pierde el pedido, y con muchos más la pantalla
# que espera el cierre de la sesión se queda colgada por un proveedor cuyo
# servidor está caído de verdad.
INTENTOS = 3


@dataclass
class LineaDePedido:
    """Un renglón del pedido: qué producto y cuántas unidades."""

    titulo: str
    volumen: int | None
    isbn: str
    cantidad: int

    def como_texto(self):
        """Una línea del cuerpo del correo, legible por una persona.

        El ISBN va primero cuando está: es lo que el proveedor usa para
        identificar sin ambigüedad qué edición se le está pidiendo, que es
        exactamente el problema que el título por sí solo no resuelve.
        """
        partes = [f"{self.isbn} —" if self.isbn else "—", self.titulo]
        if self.volumen:
            partes.append(f"vol. {self.volumen}")
        return f"  {' '.join(partes)}: {self.cantidad} unidad(es)"


@dataclass
class ResultadoDeEnvio:
    """Si el pedido salió, y si no, por qué."""

    proveedor: object
    lineas: list
    enviado: bool = False
    intentos: int = 0
    error: str = ""

    def __bool__(self):
        return self.enviado

    def como_json(self):
        """Lo que la sesión guarda para poder decir después qué pasó."""
        return {
            "proveedor": str(self.proveedor),
            "proveedor_id": self.proveedor.pk,
            "correo": self.proveedor.correo_comercial,
            "productos": len(self.lineas),
            "unidades": sum(linea.cantidad for linea in self.lineas),
            "enviado": self.enviado,
            "intentos": self.intentos,
            "error": self.error,
        }


def asunto_de(proveedor):
    return f"Pedido de reposición — {proveedor.razon_social}"


def cuerpo_de(proveedor, lineas):
    """El texto del pedido.

    Va en texto plano y no en HTML a propósito: es un pedido comercial que
    alguien del otro lado va a leer y probablemente copiar a su sistema, y el
    texto plano se lee igual en cualquier cliente de correo.
    """
    contacto = proveedor.nombre_contacto or proveedor.razon_social
    unidades = sum(linea.cantidad for linea in lineas)
    return "\n".join(
        [
            f"Estimado/a {contacto}:",
            "",
            "Por medio del presente le solicitamos la reposición de los " "siguientes títulos:",
            "",
            *[linea.como_texto() for linea in lineas],
            "",
            f"Total: {len(lineas)} título(s), {unidades} unidad(es).",
            "",
            "Quedamos a la espera de su confirmación.",
            "",
            "Longbox",
        ]
    )


def enviar_pedido(proveedor, lineas):
    """Manda el pedido y devuelve cómo salió. **Nunca levanta.**

    Que no levante no es comodidad: quien llama está recorriendo varios
    proveedores, y una excepción acá dejaría a los que faltan sin su pedido por
    culpa de uno. El fallo se devuelve como dato para que se pueda auditar y
    notificar, que es lo que pide el CU.
    """
    resultado = ResultadoDeEnvio(proveedor=proveedor, lineas=list(lineas))
    if not resultado.lineas:
        # Nada que pedir no es un fallo: es una sesión donde ese proveedor no
        # aportó ningún producto confirmado.
        resultado.error = "Sin líneas que pedir."
        return resultado

    for intento in range(1, INTENTOS + 1):
        resultado.intentos = intento
        try:
            enviar_correo(
                asunto_de(proveedor),
                cuerpo_de(proveedor, resultado.lineas),
                [proveedor.correo_comercial],
            )
        except OSError as fallo:
            # `OSError` cubre lo que levanta `smtplib` ante un servidor caído o
            # una red cortada, que es el fallo transitorio que los reintentos
            # vienen a cubrir.
            resultado.error = str(fallo) or fallo.__class__.__name__
            logger.warning(
                "Intento %s de %s: falló el pedido a %s (%s)",
                intento,
                INTENTOS,
                proveedor,
                resultado.error,
            )
            continue
        resultado.enviado = True
        resultado.error = ""
        return resultado

    return resultado
