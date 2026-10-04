"""`CO-017` E1 bajo concurrencia real: dos Administradores aprueban el mismo correo a la vez.

Hilos reales contra PostgreSQL (plan 00, D4-02). Las pruebas de `CO-017` E1 ya
cubren la segunda aprobación cuando la primera terminó; ésta suelta las dos
juntas. Una procesa y la otra informa el estado: **un solo juego de borradores**
y ninguna respuesta 500.
"""

import pytest

from apps.accounts.models import Usuario
from apps.accounts.tests.factories import UsuarioFactory
from apps.catalog.models import BorradorProducto
from apps.core.tests.concurrencia import a_la_vez, errores_internos, sesion_de
from apps.suppliers import services
from apps.suppliers.models import CorreoProveedor
from apps.suppliers.tests import correos_de_ejemplo as ejemplo
from apps.suppliers.tests.test_contratos_04_proveedores import (  # noqa: F401 - fixture
    contestando,
    producto,
    proveedor,
    respuesta,
    url_aprobar,
)

REPETICIONES = 5

pytestmark = pytest.mark.django_db(transaction=True)


def test_CO017_dos_aprobaciones_simultaneas_procesan_una_sola_vez(proveedor):  # noqa: F811
    a = UsuarioFactory(rol=Usuario.ADMINISTRADOR)
    b = UsuarioFactory(rol=Usuario.ADMINISTRADOR)
    for indice in range(REPETICIONES):
        BorradorProducto.objects.all().delete()
        datos = ejemplo.correo_de_novedades(message_id=f"<carrera-{indice}@ivrea.test>")
        correo = services.ingerir(datos).correo
        sesion_a, sesion_b = sesion_de(a), sesion_de(b)

        with contestando(respuesta([producto()])):
            respuestas = a_la_vez(
                lambda s=sesion_a: s.post(url_aprobar(correo)),
                lambda s=sesion_b: s.post(url_aprobar(correo)),
            )

        correo.refresh_from_db()
        assert correo.estado == CorreoProveedor.PROCESADO
        assert BorradorProducto.objects.filter(correo=correo).count() == 1
        assert errores_internos(respuestas) == []
