"""Acceso a la gestión de pedidos por la dirección real, y dos administradores a la vez."""

import pytest
from django.urls import reverse

from apps.accounts.models import Usuario
from apps.accounts.tests.factories import UsuarioFactory
from apps.core.models import RegistroAuditoria
from apps.core.tests.concurrencia import a_la_vez, errores_internos, sesion_de
from apps.pedidos.models import Pedido
from apps.pedidos.tests.util import crear_pedido


@pytest.mark.django_db
@pytest.mark.parametrize("rol", ["cajero", "cliente"])
@pytest.mark.parametrize("nombre", ["pedidos:lista", "pedidos:detalle", "pedidos:avanzar"])
def test_acceso_solo_el_administrador_ve_y_avanza_pedidos(client, request, rol, nombre):
    pedido = crear_pedido(request.getfixturevalue("cliente"))
    client.force_login(request.getfixturevalue(rol))
    url = reverse(nombre) if nombre == "pedidos:lista" else reverse(nombre, args=[pedido.pk])

    lectura = client.get(url)
    escritura = client.post(
        reverse("pedidos:avanzar", args=[pedido.pk]), {"estado_visto": pedido.estado}
    )

    pedido.refresh_from_db()
    assert (lectura.status_code, escritura.status_code) == (403, 403)
    assert pedido.estado == Pedido.PENDIENTE_ARMADO


@pytest.mark.django_db
def test_acceso_sin_sesion_va_al_ingreso(client):
    respuesta = client.get(reverse("pedidos:lista"))

    assert respuesta.url.startswith(reverse("accounts:login"))


@pytest.mark.django_db
def test_acceso_el_menu_del_administrador_lleva_a_pedidos(client_admin):
    contenido = client_admin.get(reverse("core:panel")).content.decode()

    assert reverse("pedidos:lista") in contenido
    assert "Por armar" in contenido


@pytest.mark.django_db(transaction=True)
def test_CO092_dos_administradores_que_avanzan_a_la_vez_avanzan_un_solo_paso():
    for _ in range(5):
        cliente = UsuarioFactory(rol=Usuario.CLIENTE)
        pedido = crear_pedido(cliente)
        url = reverse("pedidos:avanzar", args=[pedido.pk])
        uno = sesion_de(UsuarioFactory(rol=Usuario.ADMINISTRADOR))
        otro = sesion_de(UsuarioFactory(rol=Usuario.ADMINISTRADOR))
        datos = {"estado_visto": Pedido.PENDIENTE_ARMADO}

        respuestas = a_la_vez(lambda: uno.post(url, datos), lambda: otro.post(url, datos))

        pedido.refresh_from_db()
        assert errores_internos(respuestas) == []
        assert pedido.estado == Pedido.ARMADO
        assert pedido.transiciones.count() == 2
        assert (
            RegistroAuditoria.objects.filter(
                accion=RegistroAuditoria.AVANCE_ESTADO_PEDIDO, objetivo_pk=pedido.pk
            ).count()
            == 1
        )
