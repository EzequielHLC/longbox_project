"""«Avisos de stock» en «Mi cuenta»: el A1 de `CU-RST-SUS` (`CO-076`) desde la cuenta
(plan 00 de interfaz, segunda parte, 15)."""

from datetime import timedelta

import pytest
from django.urls import reverse
from django.utils import timezone

from apps.accounts.tests.factories import UsuarioFactory
from apps.catalog.models import Producto
from apps.catalog.tests.factories import ProductoFactory
from apps.core.models import RegistroAuditoria
from apps.restock.models import SuscripcionReposicion

pytestmark = pytest.mark.django_db

URL = reverse("cuenta:avisos")


def _agotado():
    return ProductoFactory(stock=0, estado=Producto.AGOTADO)


def _espera(usuario, producto, *, hace_horas=0, **extra):
    return SuscripcionReposicion.objects.create(
        usuario=usuario,
        producto=producto,
        creada_en=timezone.now() - timedelta(hours=hace_horas),
        **extra,
    )


@pytest.fixture
def lector(client):
    usuario = UsuarioFactory(rol="cliente")
    client.force_login(usuario)
    return usuario


def test_lista_los_propios_con_su_lugar_en_la_fila(client, lector):
    producto = _agotado()
    _espera(UsuarioFactory(rol="cliente"), producto, hace_horas=5)
    propia = _espera(lector, producto, hace_horas=1)
    _espera(UsuarioFactory(rol="cliente"), _agotado())

    respuesta = client.get(URL)

    (aviso,) = respuesta.context["esperando"]
    assert aviso.pk == propia.pk
    assert aviso.turno == 2
    assert 'sos el <span class="datos">2</span>.º en la lista' in respuesta.content.decode()


def test_lo_avisado_se_ve_sin_accion_y_lo_viejo_no(client, lector):
    reciente = _espera(
        lector,
        ProductoFactory(),
        estado=SuscripcionReposicion.NOTIFICADA,
        notificada_en=timezone.now(),
    )
    _espera(
        lector,
        ProductoFactory(),
        estado=SuscripcionReposicion.NOTIFICADA,
        notificada_en=timezone.now() - timedelta(days=120),
    )

    respuesta = client.get(URL)

    assert [a.pk for a in respuesta.context["avisados"]] == [reciente.pk]
    assert list(respuesta.context["esperando"]) == []


def test_CO076_cancelar_desde_la_cuenta_elimina_la_propia_sin_auditar(client, lector):
    producto = _agotado()
    _espera(lector, producto)
    ajena = _espera(UsuarioFactory(rol="cliente"), producto)
    registros = RegistroAuditoria.objects.count()

    respuesta = client.post(URL, {"producto": producto.pk}, follow=True)

    assert list(SuscripcionReposicion.objects.all()) == [ajena]
    assert RegistroAuditoria.objects.count() == registros
    assert "Cancelaste el aviso" in respuesta.content.decode()


@pytest.mark.parametrize("rol", ["cajero", "administrador"])
def test_acceso_el_personal_recibe_403(client, rol):
    client.force_login(UsuarioFactory(rol=rol))

    assert client.get(URL).status_code == 403
    assert client.post(URL, {"producto": _agotado().pk}).status_code == 403


def test_acceso_sin_sesion_va_al_ingreso(client):
    assert client.get(URL).url.startswith(reverse("accounts:login"))
