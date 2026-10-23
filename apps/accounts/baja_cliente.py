"""CU-CLI-BAJ — Dar de Baja Cuenta de Cliente (plan 11, tercera parte).

`CO-112` es el informe y sus dos bloqueos; `CO-113`, la confirmación con la
contraseña, todo en una sola transacción. Las decisiones del plan aprobado:

- Los puntos se invalidan lote por lote con un débito «Baja de la cuenta» cada
  uno, como la caducidad: el historial explica por qué el saldo llegó a cero.
- Cuentan como pedidos activos todos los del ciclo (`pedidos.servicios.ACTIVOS`),
  no sólo los tres que nombra la ficha.
- Tres contraseñas equivocadas bloquean **la baja**, no el inicio de sesión:
  su contador es propio (`IntentoFallido.BAJA_CUENTA`).
"""

from dataclasses import dataclass
from datetime import timedelta
from decimal import Decimal

from django.db import transaction
from django.utils import timezone

from apps.accounts.models import IntentoFallido, Usuario
from apps.accounts.services import invalidar_sesiones_de, minutos_de_bloqueo
from apps.almacen.models import ArticuloRetenido
from apps.core.models import ConfiguracionSistema, RegistroAuditoria
from apps.core.segundo_plano import despues_del_commit
from apps.pedidos import avisos
from apps.pedidos.models import LineaPedido, Pedido
from apps.pedidos.servicios import ACTIVOS
from apps.puntos import servicios as puntos
from apps.puntos.models import LotePuntos, MovimientoPuntos
from apps.restock.models import SuscripcionReposicion
from apps.tienda.models import LineaCarrito

INTENTOS_MAXIMOS = 3
MOTIVO_PUNTOS = "Baja de la cuenta"

MENSAJE_RETENIDOS = (
    "Tenés artículos retenidos en el local que deben ser resueltos antes de dar de baja la "
    "cuenta. Podés solicitar su despacho desde la sección Stock en Local de tu cuenta."
)
MENSAJE_DEMORADOS = (
    "Tenés pedidos con artículos demorados que requieren tu decisión antes de dar de baja la "
    "cuenta."
)
MENSAJE_CONTRASENA = "La contraseña no es correcta."
MENSAJE_BLOQUEO = (
    "Por seguridad, la baja de la cuenta quedó bloqueada durante {minutos} minutos después de "
    "tres intentos fallidos."
)
MENSAJE_DESACTIVADA = "Tu cuenta ha sido desactivada correctamente."


class BajaBloqueada(Exception):
    """E1 o E2: algo que el Cliente tiene que resolver antes."""

    def __init__(self, motivo):
        super().__init__(motivo)
        self.motivo = motivo


@dataclass
class Implicaciones:
    """`CO-112`: las cuatro categorías del paso 2, y los dos bloqueos."""

    puntos: int
    equivalencia: Decimal
    pedidos_activos: int
    suscripciones: int
    lineas_carrito: int
    retenidos: int
    decisiones_pendientes: int

    @property
    def bloqueo(self):
        if self.retenidos:
            return MENSAJE_RETENIDOS
        if self.decisiones_pendientes:
            return MENSAJE_DEMORADOS
        return ""


def implicaciones(usuario):
    """`CO-112`. Sólo lee."""
    saldo = puntos.saldo(usuario)
    valor = ConfiguracionSistema.obtener().equivalencia_puntos
    return Implicaciones(
        puntos=saldo,
        equivalencia=Decimal(saldo) * valor,
        pedidos_activos=Pedido.objects.filter(usuario=usuario, estado__in=ACTIVOS).count(),
        suscripciones=SuscripcionReposicion.objects.filter(
            usuario=usuario, estado__in=SuscripcionReposicion.EN_ESPERA
        ).count(),
        lineas_carrito=LineaCarrito.objects.filter(carrito__usuario=usuario).count(),
        retenidos=ArticuloRetenido.objects.filter(
            usuario=usuario, estado__in=ArticuloRetenido.CON_PLAZO
        ).count(),
        decisiones_pendientes=LineaPedido.objects.filter(
            pedido__usuario=usuario,
            estado=LineaPedido.ESPERANDO_DEMORADO,
            decision_demora="",
        ).count(),
    )


# ---------------------------------------------------------------------------
# E3 — el bloqueo tras tres intentos
# ---------------------------------------------------------------------------


def _intentos(usuario):
    desde = timezone.now() - timedelta(minutes=minutos_de_bloqueo())
    return IntentoFallido.objects.filter(
        flujo=IntentoFallido.BAJA_CUENTA, email__iexact=usuario.email, ocurrido_en__gte=desde
    )


def esta_bloqueada(usuario):
    return _intentos(usuario).count() >= INTENTOS_MAXIMOS


def registrar_intento(usuario, ip):
    IntentoFallido.objects.create(flujo=IntentoFallido.BAJA_CUENTA, email=usuario.email, ip=ip)


# ---------------------------------------------------------------------------
# CO-113 — la confirmación
# ---------------------------------------------------------------------------


@dataclass
class Baja:
    puntos: int
    suscripciones: int
    lineas_carrito: int
    pedidos_activos: int


def confirmar(usuario, *, ip=None):
    """Las postcondiciones de `CO-113`, todas o ninguna (E4).

    Los bloqueos se vuelven a mirar adentro de la transacción: entre el informe y
    la confirmación pudo llegarle un artículo retenido o una demora.
    """
    with transaction.atomic():
        cuenta = Usuario.objects.select_for_update().get(pk=usuario.pk)
        motivo = implicaciones(cuenta).bloqueo
        if motivo:
            raise BajaBloqueada(motivo)

        cuenta.estado = Usuario.INACTIVO
        cuenta.save(update_fields=["estado", "is_active"])
        invalidar_sesiones_de(cuenta)

        hecho = Baja(
            puntos=_invalidar_puntos(cuenta),
            suscripciones=SuscripcionReposicion.objects.filter(
                usuario=cuenta, estado__in=SuscripcionReposicion.EN_ESPERA
            ).delete()[0],
            lineas_carrito=LineaCarrito.objects.filter(carrito__usuario=cuenta).delete()[0],
            pedidos_activos=Pedido.objects.filter(usuario=cuenta, estado__in=ACTIVOS).count(),
        )
        IntentoFallido.objects.filter(
            flujo=IntentoFallido.BAJA_CUENTA, email__iexact=cuenta.email
        ).delete()
        RegistroAuditoria.registrar(
            accion=RegistroAuditoria.BAJA_CUENTA_CLIENTE,
            actor=cuenta,
            objetivo=cuenta,
            ip=ip,
            detalle=(
                f"{cuenta.email} · puntos invalidados: {hecho.puntos} · suscripciones "
                f"canceladas: {hecho.suscripciones} · pedidos activos transferidos a la "
                f"gestión del Administrador: {hecho.pedidos_activos} · líneas de carrito "
                f"vaciadas: {hecho.lineas_carrito}"
            ),
        )
        despues_del_commit(_avisar, cuenta.email, hecho)
    return hecho


def _invalidar_puntos(cuenta):
    """Cada lote Activo a cero y Vencido, con su débito en el historial."""
    total = 0
    for lote in LotePuntos.objects.select_for_update().filter(
        usuario=cuenta, estado=LotePuntos.ACTIVO
    ):
        cantidad = lote.disponible
        lote.disponible = 0
        lote.estado = LotePuntos.VENCIDO
        lote.save(update_fields=["disponible", "estado"])
        total += cantidad
        movimiento = MovimientoPuntos.objects.create(
            usuario=cuenta,
            tipo=MovimientoPuntos.DEBITO,
            cantidad=cantidad,
            saldo_resultante=puntos.saldo(cuenta),
            motivo=MOTIVO_PUNTOS,
        )
        movimiento.lotes.add(lote)
    return total


def _avisar(correo, hecho):
    """Paso 9: la confirmación, al correo que se conserva para los pedidos."""
    parrafos = ["Tu cuenta de Longbox quedó desactivada."]
    if hecho.pedidos_activos:
        parrafos.append(
            "Tus pedidos en curso siguen su camino: el local los gestiona y te avisa a este "
            "correo cada cambio de estado."
        )
    parrafos.append("Si querés volver, escribinos: sólo el local puede reactivar la cuenta.")
    avisos.avisar(
        [correo],
        asunto="Tu cuenta quedó desactivada",
        rotulo="Cuenta",
        antetitulo="Tu cuenta",
        titulo="Cuenta desactivada",
        parrafos=parrafos,
        filas=[
            ("Puntos invalidados", f"{hecho.puntos} pts"),
            ("Avisos de reposición cancelados", hecho.suscripciones),
            ("Pedidos en curso", hecho.pedidos_activos),
        ],
    )
