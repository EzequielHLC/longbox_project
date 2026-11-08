"""El correo de pedido consolidado a un proveedor (CU-RST-PED).

**Es un CU compartido.** Lo invoca CU-ALT-REV al cerrar una sesión de revisión, y lo
va a invocar Restock (Módulo 05) cuando exista. Por eso vive acá y no dentro de
la revisión de borradores, y por eso no sabe nada de borradores ni de sesiones:
recibe un proveedor y una lista de líneas, y manda el correo. Quien arma esas
líneas es asunto de quien lo llama.

**Reintenta hasta tres veces.** Lo pide la excepción de CU-ALT-REV, y el motivo es
que el fallo típico de un envío es transitorio —el servidor SMTP rechazando por
carga, la red cortada un segundo—. Lo que **no** hace es revertir nada: el alta
de los productos y el pedido al proveedor son operaciones separadas, y un correo
que no salió no puede deshacer productos que ya están en el catálogo. Se informa
y se sigue con los demás proveedores.
"""

import logging
from dataclasses import dataclass

from django.utils import timezone

from apps.core.mail import cuerpo_html, enviar_correo

logger = logging.getLogger(__name__)

# Tres, como pide CU-ALT-REV. No es un número mágico elegido por gusto: con un solo
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
    # El producto del catálogo, para registrar el pedido cuando sale (plan 00 del
    # circuito con los proveedores). El correo no lo usa.
    producto: object = None

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
    # El pedido registrado, si salió y sus líneas traían producto.
    pedido: object = None

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

    El texto plano va siempre: es un pedido comercial que alguien del otro lado
    va a leer y probablemente copiar a su sistema, y se lee igual en cualquier
    cliente de correo. La versión HTML de `html_de` viaja como alternativa
    (B-00-008).
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


def html_de(proveedor, lineas):
    """La alternativa con el estilo del sistema: el mismo pedido, en tabla."""
    return cuerpo_html(
        "correo/pedido_proveedor.html",
        {
            "proveedor": proveedor,
            "contacto": proveedor.nombre_contacto or proveedor.razon_social,
            "lineas": lineas,
            "unidades": sum(linea.cantidad for linea in lineas),
        },
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
                html=html_de(proveedor, resultado.lineas),
                reintentar=False,  # el reintento es este bucle
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


def enviar_y_registrar(
    proveedor, lineas, actor=None, *, origen=None, registrar_si_falla=False, **referencias
):
    """`CO-074` completo: el envío, su entrada en el log y E2.

    Sin correo registrado no se intenta (E2). Lo invocan `CU-ALT-REV` al cerrar
    la sesión, `CU-RST-APR` al despachar y el pedido a mano; cada uno decide cómo
    seguir. **Si sale**, queda registrado como pedido a proveedor con su `origen`
    y sus `referencias` (`propuesta`, `sesion`, `fecha_estimada`): es lo que da
    cupo a la pre-venta y lo que se espera en «Pedidos por llegar».
    """
    from apps.core.models import RegistroAuditoria

    if not proveedor.correo_comercial:
        resultado = ResultadoDeEnvio(proveedor=proveedor, lineas=list(lineas))
        resultado.error = "sin correo registrado"
    else:
        resultado = enviar_pedido(proveedor, lineas)
    unidades = sum(linea.cantidad for linea in resultado.lineas)
    RegistroAuditoria.registrar(
        accion=RegistroAuditoria.PEDIDO_A_PROVEEDOR,
        actor=actor,
        objetivo=proveedor,
        objetivo_email=proveedor.correo_comercial,
        detalle=(
            f"Pedido a {proveedor.razon_social}: {len(resultado.lineas)} título(s), "
            f"{unidades} unidad(es). "
            + (
                "Enviado."
                if resultado.enviado
                else f"No se envió ({resultado.error}, {resultado.intentos} intento(s))."
            )
        ),
    )
    if resultado.enviado and origen:
        from apps.suppliers import llegadas

        resultado.pedido = llegadas.registrar(
            proveedor,
            origen,
            [(linea.producto, linea.cantidad) for linea in resultado.lineas if linea.producto],
            actor,
            **referencias,
        )
        # Plan 00 de la respuesta del proveedor: el aviso, con los botones para anotar
        # lo que conteste. Después de confirmar, y fuera del pedido: si falla, el
        # pedido queda.
        from apps.avisos import canales
        from apps.core.segundo_plano import despues_del_commit

        despues_del_commit(canales.avisar_pedido, resultado.pedido)
    elif origen and registrar_si_falla:
        # B-05-014: si no sale, queda «Sin enviar», a la vista para reintentarlo. Sin
        # esto, lo confirmado en una revisión quedaba en Pre-venta sin nada en camino
        # y sin ningún lugar desde donde volver a pedirlo.
        from apps.avisos import canales
        from apps.core.segundo_plano import despues_del_commit
        from apps.suppliers import llegadas

        resultado.pedido = llegadas.registrar(
            proveedor,
            origen,
            [(linea.producto, linea.cantidad) for linea in resultado.lineas if linea.producto],
            actor,
            error_de_envio=resultado.error or "no se envió",
            **referencias,
        )
        if resultado.pedido:
            despues_del_commit(canales.avisar_pedido_sin_enviar, resultado.pedido)
    return resultado


# ---------------------------------------------------------------------------
# B-05-014 · el pedido que no salió: reintentar o descartar
# ---------------------------------------------------------------------------


def reintentar(pedido, actor, *, desde=""):
    """Vuelve a mandar un pedido «Sin enviar». Si sale, queda «Por llegar» y abre sus
    pre-ventas, como si hubiera salido la primera vez. Devuelve el `ResultadoDeEnvio`."""
    from django.db import transaction

    from apps.avisos import canales
    from apps.core.models import RegistroAuditoria
    from apps.core.segundo_plano import despues_del_commit
    from apps.suppliers import llegadas
    from apps.suppliers.models import PedidoProveedor

    with transaction.atomic():
        pedido = PedidoProveedor.objects.select_for_update().get(pk=pedido.pk)
        if pedido.estado != PedidoProveedor.SIN_ENVIAR:
            raise llegadas.OperacionRechazada("Ese pedido ya salió o se descartó.")
        proveedor = pedido.proveedor
        lineas = [
            LineaDePedido(
                titulo=linea.producto.titulo,
                volumen=getattr(linea.producto.especifico, "volumen", None),
                isbn=getattr(linea.producto.especifico, "isbn", ""),
                cantidad=linea.cantidad_pedida,
                producto=linea.producto,
            )
            for linea in pedido.lineas.select_related("producto")
        ]
        if proveedor is None or not proveedor.correo_comercial:
            resultado = ResultadoDeEnvio(proveedor=proveedor, lineas=lineas)
            resultado.error = "sin correo registrado"
        else:
            resultado = enviar_pedido(proveedor, lineas)
        RegistroAuditoria.registrar(
            accion=RegistroAuditoria.PEDIDO_A_PROVEEDOR,
            actor=actor,
            objetivo=pedido,
            detalle=(
                f"Reintento del {pedido}: "
                + (
                    "enviado."
                    if resultado.enviado
                    else f"no se envió ({resultado.error}, {resultado.intentos} intento(s))."
                )
                + (f" (desde {desde})" if desde else "")
            ),
        )
        if resultado.enviado:
            pedido.estado = PedidoProveedor.ABIERTO
            pedido.error_de_envio = ""
            pedido.save(update_fields=["estado", "error_de_envio"])
            for linea in lineas:
                llegadas.abrir_preventa(linea.producto, pedido.fecha_estimada)
            despues_del_commit(canales.avisar_pedido, pedido)
        else:
            pedido.error_de_envio = (resultado.error or "no se envió")[:300]
            pedido.save(update_fields=["error_de_envio"])
    resultado.pedido = pedido
    return resultado


def descartar_sin_enviar(pedido, motivo, actor, *, desde=""):
    """Un pedido «Sin enviar» que ya no se va a mandar: se cierra con su motivo, y lo
    que estaba en Pre-venta sólo por él deja de estarlo (como `cerrar_sin_recibir`)."""
    from django.db import transaction

    from apps.core.models import RegistroAuditoria
    from apps.suppliers import llegadas
    from apps.suppliers.models import LineaPedidoProveedor, PedidoProveedor

    motivo = " ".join((motivo or "").split())[:500]
    if not motivo:
        raise llegadas.OperacionRechazada("El motivo es obligatorio.")
    with transaction.atomic():
        pedido = PedidoProveedor.objects.select_for_update().get(pk=pedido.pk)
        if pedido.estado != PedidoProveedor.SIN_ENVIAR:
            raise llegadas.OperacionRechazada("Ese pedido ya salió o se descartó.")
        for linea in pedido.lineas.filter(estado__in=LineaPedidoProveedor.ABIERTAS):
            llegadas.cerrar_sin_recibir(linea, motivo, actor)
        PedidoProveedor.objects.filter(pk=pedido.pk).update(
            estado=PedidoProveedor.CERRADO, cerrado_en=timezone.now()
        )
        RegistroAuditoria.registrar(
            accion=RegistroAuditoria.PEDIDO_A_PROVEEDOR,
            actor=actor,
            objetivo=pedido,
            detalle=f"{pedido} descartado sin enviar: {motivo}"
            + (f" (desde {desde})" if desde else ""),
        )
    pedido.refresh_from_db()
    return pedido
