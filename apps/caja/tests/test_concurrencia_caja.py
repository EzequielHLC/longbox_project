"""`CO-126` bajo concurrencia real: dos usuarios cierran la caja a la vez.

Hilos contra PostgreSQL. Tiene que quedar un solo cierre (I-23) con todas las
transacciones, cada una en ese cierre y en ningún otro, y sin errores 500.
"""

from decimal import Decimal

import pytest
from django.urls import reverse

from apps.accounts.models import Usuario
from apps.accounts.tests.factories import UsuarioFactory
from apps.caja.models import CierreDeCaja
from apps.core.tests.concurrencia import a_la_vez, errores_internos, sesion_de
from apps.pedidos.models import TransaccionPago
from apps.pedidos.tests.util import como_venta_de_mostrador, crear_pedido

pytestmark = pytest.mark.django_db(transaction=True)


def test_CO126_dos_cierres_a_la_vez_dejan_uno_solo_con_cada_transaccion_una_vez():
    for _ in range(4):
        pedido = crear_pedido(correo_invitado="x@correo.test", con_pago=False)
        como_venta_de_mostrador(pedido)
        TransaccionPago.objects.create(
            pedido=pedido,
            medio=TransaccionPago.EFECTIVO,
            monto=Decimal("100"),
            estado=TransaccionPago.APROBADO,
        )
    uno = sesion_de(UsuarioFactory(rol=Usuario.CAJERO))
    otro = sesion_de(UsuarioFactory(rol=Usuario.ADMINISTRADOR))

    respuestas = a_la_vez(
        lambda: uno.post(reverse("caja:cerrar")),
        lambda: otro.post(reverse("caja:cerrar")),
    )

    assert errores_internos(respuestas) == []
    cierre = CierreDeCaja.objects.get()
    assert cierre.transacciones.count() == 4
    assert cierre.total_global == Decimal("400")
    assert not TransaccionPago.objects.filter(incluida_en_cierre=False).exists()
