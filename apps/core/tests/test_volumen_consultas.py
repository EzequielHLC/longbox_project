"""D5-04 · Volumen sin degradación: cada listado paginado hace las mismas consultas con pocos
registros que con muchos (plan 00).

Un listado que consulta la base una vez por fila (el problema N+1) anda bien con
diez registros y se arrastra con veinte mil. La prueba cuenta las consultas de una
página con pocos registros y de una página llena, con más de una página detrás:
tienen que ser las mismas. Si una crece, el número exacto queda en el mensaje.
"""

from datetime import timedelta
from decimal import Decimal

import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from django.utils import timezone

from apps.accounts.models import Usuario
from apps.accounts.tests.factories import UsuarioFactory
from apps.catalog.models import Oferta
from apps.catalog.tests.factories import ProductoFactory, ProductoNoEditorialFactory
from apps.core.models import RegistroAuditoria
from apps.suppliers.models import CorreoProveedor
from apps.suppliers.tests.factories import ProveedorFactory

pytestmark = pytest.mark.django_db

POCOS = 3
MUCHOS = 60  # más que cualquier página (25 o 50): la página va llena y hay una segunda


def consultas(cliente, url):
    # Una petición de calentamiento: la primera carga cosas una sola vez (la
    # sesión, la identidad visual) que no tienen que ver con el volumen.
    cliente.get(url)
    with CaptureQueriesContext(connection) as capturadas:
        respuesta = cliente.get(url)
    assert respuesta.status_code == 200, url
    return len(capturadas)


def productos(cantidad):
    for indice in range(cantidad):
        if indice % 3 == 2:
            ProductoNoEditorialFactory(stock=2)
        else:
            ProductoFactory(stock=2)


def entradas_de_auditoria(cantidad, actor):
    for indice in range(cantidad):
        RegistroAuditoria.registrar(
            accion=RegistroAuditoria.ALTA_USUARIO, actor=actor, detalle=f"entrada {indice}"
        )


def correos(cantidad):
    proveedor = ProveedorFactory()
    desde = CorreoProveedor.objects.count()
    for indice in range(desde, desde + cantidad):
        CorreoProveedor.objects.create(
            proveedor=proveedor,
            message_id=f"<volumen-{indice}@test>",
            remitente=proveedor.correo_comercial,
            asunto=f"Novedades {indice}",
        )


def cuentas(cantidad, rol):
    for _ in range(cantidad):
        UsuarioFactory(rol=rol)


def proveedores(cantidad):
    for _ in range(cantidad):
        ProveedorFactory()


def ofertas(cantidad):
    hoy = timezone.localdate()
    for _ in range(cantidad):
        Oferta.objects.create(
            descripcion="Volumen",
            fecha_inicio=hoy,
            fecha_vencimiento=hoy + timedelta(days=3),
            tipo_descuento=Oferta.PORCENTAJE,
            valor=Decimal("10"),
            alcance=Oferta.PRODUCTO,
            producto=ProductoFactory(),
            estado=Oferta.ACTIVA,
        )


LISTADOS = [
    ("catalog:producto_lista", "?estado=", productos),
    ("core:auditoria", "", None),
    ("suppliers:correo_lista", "?estado=", correos),
    ("suppliers:proveedor_lista", "", proveedores),
    ("accounts:usuario_lista", "", lambda n: cuentas(n, Usuario.CAJERO)),
    ("accounts:cliente_lista", "", lambda n: cuentas(n, Usuario.CLIENTE)),
    ("catalog:oferta_lista", "", ofertas),
]


@pytest.mark.parametrize(
    ("nombre", "parametros", "crear"), LISTADOS, ids=[listado[0] for listado in LISTADOS]
)
def test_el_listado_no_hace_mas_consultas_con_mas_registros(
    client_admin, administrador, nombre, parametros, crear
):
    url = reverse(nombre) + parametros
    llenar = crear or (lambda n: entradas_de_auditoria(n, administrador))

    llenar(POCOS)
    con_pocos = consultas(client_admin, url)
    llenar(MUCHOS)
    con_muchos = consultas(client_admin, url)

    mensaje = f"{nombre}: {con_pocos} consultas con pocos, {con_muchos} con muchos"
    assert con_muchos == con_pocos, mensaje


def test_el_catalogo_publico_no_hace_mas_consultas_con_mas_productos(client):
    url = reverse("core:tienda_catalogo") + "?estado=todos"

    productos(POCOS)
    con_pocos = consultas(client, url)
    productos(MUCHOS)
    con_muchos = consultas(client, url)

    assert con_muchos == con_pocos, f"{con_pocos} consultas con pocos, {con_muchos} con muchos"
