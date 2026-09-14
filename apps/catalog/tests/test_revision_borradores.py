"""Revisar y confirmar borradores (CU-ALT-REV), del lado de las reglas.

La pantalla se prueba aparte; acá está lo que tiene que valer aunque se la
invoque desde un comando o desde una tarea de fondo.

Lo que se pone a prueba es la línea que sostiene todo el pipeline: **el modelo
propone, la persona aplica**. Ningún camino de este archivo puede terminar con un
producto en el catálogo sin una acción explícita del Administrador, y ninguna
validación se saltea porque el dato "ya venía revisado".
"""

from datetime import timedelta
from decimal import Decimal
from unittest.mock import patch

import pytest
from django.core import mail
from django.utils import timezone

from apps.catalog import revisiones
from apps.catalog.models import (
    BorradorProducto,
    ConfianzaCampo,
    Producto,
    SesionRevision,
)
from apps.catalog.tests.factories import (
    EditorialFactory,
    FormatoFactory,
    PrecioReferenciaFactory,
    ProductoFactory,
    TipoFactory,
)
from apps.core.models import ConfiguracionSistema, RegistroAuditoria
from apps.suppliers.models import CorreoProveedor
from apps.suppliers.tests.factories import ProveedorFactory

BERSERK = "9789878271583"


@pytest.fixture
def editorial(db):
    return EditorialFactory(nombre="Ivrea")


@pytest.fixture
def tipo(db):
    return TipoFactory(nombre="Manga", usa_formato=True)


@pytest.fixture
def proveedor(db, editorial, tipo):
    return ProveedorFactory(editorial=editorial, tipo_por_defecto=tipo)


@pytest.fixture
def correo(db, proveedor):
    return CorreoProveedor.objects.create(
        proveedor=proveedor,
        message_id="<uno@ivrea.test>",
        remitente=proveedor.correo_comercial,
        estado=CorreoProveedor.PROCESADO,
    )


def borrador_de(correo, **cambios):
    """Un borrador confirmable, salvo por lo que el test cambie."""
    datos = {
        "correo": correo,
        "proveedor": correo.proveedor,
        "titulo": "Berserk Deluxe",
        "volumen": 5,
        "isbn": BERSERK,
        "editorial": correo.proveedor.editorial,
        "tipo": correo.proveedor.tipo_por_defecto,
        "precio": Decimal("24900"),
        "stock_inicial": 2,
        "estado_sugerido": Producto.ACTIVO,
    }
    datos.update(cambios)
    return BorradorProducto.objects.create(**datos)


# ---------------------------------------------------------------------------
# Confirmar de a uno
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_confirmar_crea_el_producto(correo, administrador):
    borrador = borrador_de(correo)

    confirmacion = revisiones.confirmar(borrador, actor=administrador)

    assert confirmacion
    producto = confirmacion.producto
    assert producto.titulo == "Berserk Deluxe"
    assert producto.isbn == BERSERK
    assert producto.stock == 2
    assert producto.estado == Producto.ACTIVO
    assert Producto.objects.count() == 1


@pytest.mark.django_db
def test_el_producto_nace_atado_al_proveedor_que_lo_anuncio(correo, administrador, proveedor):
    """Es la única vía por la que ese dato se llena: las altas manuales no lo
    piden (A4 de proveedores)."""
    producto = revisiones.confirmar(borrador_de(correo), actor=administrador).producto

    assert producto.proveedor == proveedor


@pytest.mark.django_db
def test_el_borrador_queda_confirmado_y_apunta_a_su_producto(correo, administrador):
    borrador = borrador_de(correo)

    producto = revisiones.confirmar(borrador, actor=administrador).producto

    borrador.refresh_from_db()
    assert borrador.estado == BorradorProducto.CONFIRMADO
    assert borrador.producto == producto
    assert borrador.resuelto_por == administrador
    assert borrador.resuelto_en is not None
    assert not borrador.esta_abierto


@pytest.mark.django_db
def test_una_pre_venta_conserva_su_fecha(correo, administrador):
    futura = timezone.localdate() + timedelta(days=30)
    borrador = borrador_de(correo, estado_sugerido=Producto.PRE_VENTA, fecha_llegada=futura)

    producto = revisiones.confirmar(borrador, actor=administrador).producto

    assert producto.estado == Producto.PRE_VENTA
    assert producto.fecha_llegada == futura


@pytest.mark.django_db
def test_el_precio_se_redondea_al_peso(correo, administrador):
    """A1: el precio final es el número que se cobra, y en una comiquería no se
    cobran centavos. El base conserva los centavos para poder recalcular."""
    borrador = borrador_de(correo, precio=Decimal("24900.60"))

    producto = revisiones.confirmar(borrador, actor=administrador).producto

    assert producto.precio == Decimal("24901.00")
    assert producto.precio_base == Decimal("24900.60")


@pytest.mark.django_db
def test_un_precio_que_coincide_con_la_tabla_no_queda_manual(
    correo, administrador, editorial, tipo
):
    formato = FormatoFactory(nombre="Tapa dura")
    PrecioReferenciaFactory(editorial=editorial, tipo=tipo, formato=formato, pvp=Decimal("24900"))
    borrador = borrador_de(correo, formato=formato, precio=Decimal("24900"))

    producto = revisiones.confirmar(borrador, actor=administrador).producto

    assert producto.precio_manual is False
    assert producto.precio_referencia is not None


@pytest.mark.django_db
def test_un_precio_distinto_del_de_la_tabla_queda_manual(correo, administrador, editorial, tipo):
    """A4: si el precio confirmado no es el de la tabla, alguien lo decidió a
    propósito y la propagación de CU-PVP-MAR no debe pisárselo."""
    formato = FormatoFactory(nombre="Tapa dura")
    PrecioReferenciaFactory(editorial=editorial, tipo=tipo, formato=formato, pvp=Decimal("20000"))
    borrador = borrador_de(correo, formato=formato, precio=Decimal("24900"))

    producto = revisiones.confirmar(borrador, actor=administrador).producto

    assert producto.precio_manual is True


@pytest.mark.django_db
def test_sin_fila_en_la_tabla_la_marca_no_aplica(correo, administrador):
    """No hay de dónde propagarle, así que no se lo marca como manual."""
    producto = revisiones.confirmar(borrador_de(correo), actor=administrador).producto

    assert producto.precio_referencia is None
    assert producto.precio_manual is False


# ---------------------------------------------------------------------------
# Lo que bloquea una confirmación
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_un_bloqueante_vacio_impide_confirmar(correo, administrador):
    borrador = borrador_de(correo, precio=None, estado=BorradorProducto.INCOMPLETO)

    confirmacion = revisiones.confirmar(borrador, actor=administrador)

    assert not confirmacion
    assert confirmacion.motivo == revisiones.BLOQUEANTES_VACIOS
    assert Producto.objects.count() == 0
    borrador.refresh_from_db()
    assert borrador.esta_abierto


@pytest.mark.django_db
def test_una_pre_venta_sin_fecha_no_se_puede_confirmar(correo, administrador):
    """Bloqueante condicional del CU, y A10: sin fecha quedaría en pre-venta
    para siempre, invisible para el ciclo que debería sacarla de ahí."""
    borrador = borrador_de(correo, estado_sugerido=Producto.PRE_VENTA, fecha_llegada=None)

    confirmacion = revisiones.confirmar(borrador, actor=administrador)

    assert not confirmacion
    assert "fecha_llegada" in borrador.campos_bloqueantes_vacios


@pytest.mark.django_db
def test_el_mismo_borrador_sin_fecha_se_confirma_si_nace_activo(correo, administrador):
    """La fecha es bloqueante **solo** si el borrador quedaría en Pre-venta."""
    borrador = borrador_de(correo, estado_sugerido=Producto.ACTIVO, fecha_llegada=None)

    assert revisiones.confirmar(borrador, actor=administrador)


@pytest.mark.django_db
def test_un_producto_que_se_cargo_mientras_tanto_bloquea_la_confirmacion(
    correo, administrador, editorial, tipo
):
    """Entre que el borrador se generó y que alguien lo confirma pueden pasar
    días: la comprobación del pipeline caducó y hay que rehacerla."""
    borrador = borrador_de(correo)
    ProductoFactory(isbn=BERSERK, editorial=editorial, tipo=tipo)

    confirmacion = revisiones.confirmar(borrador, actor=administrador)

    assert not confirmacion
    assert confirmacion.motivo == revisiones.YA_EXISTE
    assert confirmacion.producto_existente is not None


@pytest.mark.django_db
def test_confirmar_dos_veces_no_duplica_el_producto(correo, administrador):
    """La segunda confirmación encuentra el borrador ya resuelto y se retira."""
    borrador = borrador_de(correo)

    primera = revisiones.confirmar(borrador, actor=administrador)
    segunda = revisiones.confirmar(borrador, actor=administrador)

    assert primera
    assert not segunda
    assert segunda.motivo == revisiones.NO_ESTA_ABIERTO
    assert Producto.objects.count() == 1


# ---------------------------------------------------------------------------
# Confirmación en lote
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_el_lote_confirma_todos_los_que_estan_en_condiciones(correo, administrador):
    borradores = [
        borrador_de(correo, titulo="Uno", isbn="", volumen=1),
        borrador_de(correo, titulo="Dos", isbn="", volumen=2),
    ]

    resultado = revisiones.confirmar_en_lote(borradores, actor=administrador)

    assert len(resultado.confirmadas) == 2
    assert resultado.excluidas == []
    assert Producto.objects.count() == 2


@pytest.mark.django_db
def test_el_lote_excluye_la_confianza_baja_sin_bloquear_al_resto(correo, administrador):
    """Es la excepción central del CU: se informa la exclusión y el borrador
    permanece en cola para revisión individual."""
    dudoso = borrador_de(correo, titulo="Dudoso", isbn="", volumen=1)
    ConfianzaCampo.objects.create(borrador=dudoso, campo="precio", nivel=ConfianzaCampo.BAJA)
    sano = borrador_de(correo, titulo="Sano", isbn="", volumen=2)

    resultado = revisiones.confirmar_en_lote([dudoso, sano], actor=administrador)

    assert [c.producto.titulo for c in resultado.confirmadas] == ["Sano"]
    assert len(resultado.excluidas) == 1
    assert resultado.excluidas[0].motivo == revisiones.CONFIANZA_SIN_REVISAR
    dudoso.refresh_from_db()
    assert dudoso.esta_abierto


@pytest.mark.django_db
def test_una_confianza_baja_ya_revisada_no_excluye_del_lote(correo, administrador):
    """La acción afirmativa del paso 3 es lo que la desbloquea."""
    borrador = borrador_de(correo)
    ConfianzaCampo.objects.create(
        borrador=borrador, campo="precio", nivel=ConfianzaCampo.BAJA, revisado=True
    )

    resultado = revisiones.confirmar_en_lote([borrador], actor=administrador)

    assert len(resultado.confirmadas) == 1


@pytest.mark.django_db
def test_la_confianza_media_no_excluye_del_lote(correo, administrador):
    """El CU habla de confianza **baja**: la media no traba nada."""
    borrador = borrador_de(correo)
    ConfianzaCampo.objects.create(borrador=borrador, campo="precio", nivel=ConfianzaCampo.MEDIA)

    assert len(revisiones.confirmar_en_lote([borrador], actor=administrador).confirmadas) == 1


@pytest.mark.django_db
def test_un_borrador_de_confianza_baja_si_se_puede_confirmar_de_a_uno(correo, administrador):
    """La pantalla exige la acción afirmativa antes de dejar apretar el botón;
    el servicio no la vuelve a exigir en el camino individual."""
    borrador = borrador_de(correo)
    ConfianzaCampo.objects.create(borrador=borrador, campo="precio", nivel=ConfianzaCampo.BAJA)

    assert revisiones.confirmar(borrador, actor=administrador)


# ---------------------------------------------------------------------------
# Rechazar
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_rechazar_exige_motivo(correo, administrador):
    borrador = borrador_de(correo)

    with pytest.raises(ValueError):
        revisiones.rechazar(borrador, actor=administrador, motivo="   ")

    borrador.refresh_from_db()
    assert borrador.esta_abierto


@pytest.mark.django_db
def test_rechazar_persiste_el_motivo_y_lo_audita(correo, administrador):
    borrador = borrador_de(correo)

    revisiones.rechazar(borrador, actor=administrador, motivo="No lo vamos a traer.")

    borrador.refresh_from_db()
    assert borrador.estado == BorradorProducto.RECHAZADO
    assert borrador.motivo_rechazo == "No lo vamos a traer."
    registro = RegistroAuditoria.objects.get(accion=RegistroAuditoria.BORRADOR_RECHAZADO)
    assert "No lo vamos a traer." in registro.detalle


@pytest.mark.django_db
def test_rechazar_no_crea_ningun_producto(correo, administrador):
    revisiones.rechazar(borrador_de(correo), actor=administrador, motivo="Duplicado editorial.")

    assert Producto.objects.count() == 0


# ---------------------------------------------------------------------------
# La sesión
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_mirar_la_cola_no_abre_una_sesion(correo, administrador):
    """Se crea con la primera acción: abrirla al entrar llenaría la tabla de
    tandas vacías cada vez que alguien pasa a ver qué hay."""
    assert revisiones.sesion_abierta_de(administrador) is None
    assert SesionRevision.objects.count() == 0


@pytest.mark.django_db
def test_la_primera_confirmacion_abre_la_sesion(correo, administrador):
    revisiones.confirmar(borrador_de(correo), actor=administrador)

    sesion = revisiones.sesion_abierta_de(administrador)
    assert sesion is not None
    assert sesion.confirmados.count() == 1


@pytest.mark.django_db
def test_las_acciones_siguientes_reusan_la_misma_sesion(correo, administrador):
    revisiones.confirmar(borrador_de(correo, isbn="", volumen=1), actor=administrador)
    revisiones.rechazar(
        borrador_de(correo, isbn="", volumen=2), actor=administrador, motivo="No va."
    )

    assert SesionRevision.objects.count() == 1


@pytest.mark.django_db
def test_dos_revisores_tienen_sesiones_distintas(correo, administrador):
    """Mezclarlas haría que el pedido consolidado de uno se lleve los productos
    del otro."""
    from apps.accounts.tests.factories import UsuarioFactory

    otro = UsuarioFactory(rol="administrador")

    revisiones.confirmar(borrador_de(correo, isbn="", volumen=1), actor=administrador)
    revisiones.confirmar(borrador_de(correo, isbn="", volumen=2), actor=otro)

    assert SesionRevision.objects.count() == 2


# ---------------------------------------------------------------------------
# El cierre y el pedido consolidado (CU-RST-PED)
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_cerrar_manda_un_correo_por_proveedor(correo, administrador, editorial, tipo):
    otro_proveedor = ProveedorFactory(editorial=editorial, tipo_por_defecto=tipo)
    otro_correo = CorreoProveedor.objects.create(
        proveedor=otro_proveedor,
        message_id="<dos@otra.test>",
        remitente=otro_proveedor.correo_comercial,
        estado=CorreoProveedor.PROCESADO,
    )

    revisiones.confirmar(borrador_de(correo, isbn="", volumen=1), actor=administrador)
    revisiones.confirmar(borrador_de(otro_correo, isbn="", volumen=2), actor=administrador)
    mail.outbox.clear()

    sesion = revisiones.sesion_abierta_de(administrador)
    revisiones.cerrar(sesion, actor=administrador)

    assert len(mail.outbox) == 2
    destinatarios = {mensaje.to[0] for mensaje in mail.outbox}
    assert destinatarios == {
        correo.proveedor.correo_comercial,
        otro_proveedor.correo_comercial,
    }


@pytest.mark.django_db
def test_cada_correo_lleva_solo_los_productos_de_su_proveedor(
    correo, administrador, editorial, tipo
):
    otro_proveedor = ProveedorFactory(editorial=editorial, tipo_por_defecto=tipo)
    otro_correo = CorreoProveedor.objects.create(
        proveedor=otro_proveedor,
        message_id="<tres@otra.test>",
        remitente=otro_proveedor.correo_comercial,
        estado=CorreoProveedor.PROCESADO,
    )

    revisiones.confirmar(
        borrador_de(correo, titulo="De Ivrea", isbn="", volumen=1), actor=administrador
    )
    revisiones.confirmar(
        borrador_de(otro_correo, titulo="De la otra", isbn="", volumen=2), actor=administrador
    )
    mail.outbox.clear()

    revisiones.cerrar(revisiones.sesion_abierta_de(administrador), actor=administrador)

    por_destinatario = {mensaje.to[0]: mensaje.body for mensaje in mail.outbox}
    assert "De Ivrea" in por_destinatario[correo.proveedor.correo_comercial]
    assert "De la otra" not in por_destinatario[correo.proveedor.correo_comercial]


@pytest.mark.django_db
def test_el_pedido_lleva_las_cantidades_de_stock_solicitadas(correo, administrador):
    revisiones.confirmar(borrador_de(correo, stock_inicial=7), actor=administrador)
    mail.outbox.clear()

    revisiones.cerrar(revisiones.sesion_abierta_de(administrador), actor=administrador)

    assert "7 unidad(es)" in mail.outbox[0].body


@pytest.mark.django_db
def test_una_sesion_sin_confirmaciones_no_manda_ningun_correo(correo, administrador):
    """Solo rechazos: la sesión queda registrada, pero un correo vacío sería
    peor que no mandarlo."""
    revisiones.rechazar(borrador_de(correo), actor=administrador, motivo="No va.")
    mail.outbox.clear()

    sesion = revisiones.sesion_abierta_de(administrador)
    revisiones.cerrar(sesion, actor=administrador)

    assert mail.outbox == []
    sesion.refresh_from_db()
    assert sesion.estado == SesionRevision.CERRADA


@pytest.mark.django_db
def test_dos_sesiones_el_mismo_dia_son_dos_correos_separados(correo, administrador):
    """No reabre pedidos de sesiones anteriores: son dos decisiones distintas y
    el proveedor tiene que poder tratarlas como tales."""
    revisiones.confirmar(borrador_de(correo, isbn="", volumen=1), actor=administrador)
    revisiones.cerrar(revisiones.sesion_abierta_de(administrador), actor=administrador)

    revisiones.confirmar(borrador_de(correo, isbn="", volumen=2), actor=administrador)
    mail.outbox.clear()
    revisiones.cerrar(revisiones.sesion_abierta_de(administrador), actor=administrador)

    assert len(mail.outbox) == 1
    # Y el segundo pedido lleva solo el tomo de su propia sesión.
    assert "vol. 2" in mail.outbox[0].body
    assert "vol. 1" not in mail.outbox[0].body


# ---------------------------------------------------------------------------
# Cuando el correo al proveedor falla
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_el_envio_se_reintenta_tres_veces(correo, administrador):
    revisiones.confirmar(borrador_de(correo), actor=administrador)
    sesion = revisiones.sesion_abierta_de(administrador)

    with patch("apps.suppliers.pedidos.enviar_correo", side_effect=OSError("smtp caído")) as envio:
        revisiones.cerrar(sesion, actor=administrador)

    assert envio.call_count == 3


@pytest.mark.django_db
def test_un_envio_fallido_no_revierte_los_productos(correo, administrador):
    """El alta y el pedido son operaciones separadas: un correo que no salió no
    puede deshacer productos que ya están en el catálogo."""
    revisiones.confirmar(borrador_de(correo), actor=administrador)
    sesion = revisiones.sesion_abierta_de(administrador)

    with patch("apps.suppliers.pedidos.enviar_correo", side_effect=OSError("smtp caído")):
        revisiones.cerrar(sesion, actor=administrador)

    assert Producto.objects.count() == 1
    sesion.refresh_from_db()
    assert sesion.estado == SesionRevision.CERRADA


@pytest.mark.django_db
def test_el_fallo_queda_registrado_con_el_proveedor(correo, administrador, proveedor):
    """El CU pide notificar indicando **cuál** proveedor falló: sin el nombre el
    aviso no sirve para ir a mandarlo a mano."""
    revisiones.confirmar(borrador_de(correo), actor=administrador)
    sesion = revisiones.sesion_abierta_de(administrador)

    with patch("apps.suppliers.pedidos.enviar_correo", side_effect=OSError("smtp caído")):
        revisiones.cerrar(sesion, actor=administrador)

    sesion.refresh_from_db()
    assert len(sesion.envios_fallidos) == 1
    assert sesion.envios_fallidos[0]["proveedor"] == str(proveedor)

    registro = RegistroAuditoria.objects.get(accion=RegistroAuditoria.SESION_REVISION_CERRADA)
    assert str(proveedor) in registro.detalle


@pytest.mark.django_db
def test_un_proveedor_caido_no_frena_al_resto(correo, administrador, editorial, tipo):
    otro_proveedor = ProveedorFactory(editorial=editorial, tipo_por_defecto=tipo)
    otro_correo = CorreoProveedor.objects.create(
        proveedor=otro_proveedor,
        message_id="<cuatro@otra.test>",
        remitente=otro_proveedor.correo_comercial,
        estado=CorreoProveedor.PROCESADO,
    )
    revisiones.confirmar(borrador_de(correo, isbn="", volumen=1), actor=administrador)
    revisiones.confirmar(borrador_de(otro_correo, isbn="", volumen=2), actor=administrador)
    sesion = revisiones.sesion_abierta_de(administrador)

    def falla_solo_el_primero(asunto, cuerpo, destinatarios, remitente=None):
        if destinatarios == [correo.proveedor.correo_comercial]:
            raise OSError("smtp caído")

    with patch("apps.suppliers.pedidos.enviar_correo", side_effect=falla_solo_el_primero):
        envios = revisiones.cerrar(sesion, actor=administrador)

    assert sum(1 for envio in envios if envio) == 1
    assert sum(1 for envio in envios if not envio) == 1


# ---------------------------------------------------------------------------
# Auditoría
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_cada_confirmacion_deja_su_entrada(correo, administrador):
    """ "Qué pasó en esta tanda" la contesta la sesión; "de dónde salió este
    producto" solo la contesta esta entrada."""
    producto = revisiones.confirmar(borrador_de(correo), actor=administrador).producto

    registro = RegistroAuditoria.objects.get(accion=RegistroAuditoria.BORRADOR_CONFIRMADO)
    assert registro.objetivo == producto
    assert registro.actor == administrador
    assert "stock inicial 2" in registro.detalle


@pytest.mark.django_db
def test_el_cierre_registra_confirmados_rechazados_y_pendientes(correo, administrador):
    revisiones.confirmar(borrador_de(correo, isbn="", volumen=1), actor=administrador)
    revisiones.rechazar(
        borrador_de(correo, isbn="", volumen=2), actor=administrador, motivo="No va."
    )
    borrador_de(correo, isbn="", volumen=3)  # queda pendiente

    revisiones.cerrar(revisiones.sesion_abierta_de(administrador), actor=administrador)

    detalle = RegistroAuditoria.objects.get(
        accion=RegistroAuditoria.SESION_REVISION_CERRADA
    ).detalle
    assert "1 confirmado(s)" in detalle
    assert "1 rechazado(s)" in detalle
    assert "1 pendiente(s)" in detalle
    assert "1 correo(s) de pedido enviado(s)" in detalle


@pytest.mark.django_db
def test_el_stock_por_defecto_de_la_configuracion_llega_al_producto(correo, administrador):
    configuracion = ConfiguracionSistema.obtener()
    configuracion.stock_inicial_por_defecto = 4
    configuracion.save()
    borrador = borrador_de(correo, stock_inicial=configuracion.stock_inicial_por_defecto)

    producto = revisiones.confirmar(borrador, actor=administrador).producto

    assert producto.stock == 4


@pytest.mark.django_db
def test_una_carrera_contra_la_base_se_trata_como_duplicado(correo, administrador):
    """La restricción de la base es la que **realmente** garantiza la unicidad.

    Dos confirmaciones simultáneas del mismo tomo pueden pasar las dos el
    chequeo previo y chocar recién al insertar. Eso no es un error del sistema:
    es un duplicado, y tiene que informarse como tal en vez de reventar con un
    500 después de haber creado el producto una vez.
    """
    from django.db import IntegrityError

    borrador = borrador_de(correo)

    with patch("apps.catalog.revisiones._crear_producto", side_effect=IntegrityError("choque")):
        confirmacion = revisiones.confirmar(borrador, actor=administrador)

    assert not confirmacion
    assert confirmacion.motivo == revisiones.YA_EXISTE
    borrador.refresh_from_db()
    assert borrador.esta_abierto


@pytest.mark.django_db
def test_un_proveedor_sin_productos_confirmados_no_recibe_correo(correo, administrador):
    """Nada que pedir no es un fallo: es una sesión donde ese proveedor no
    aportó ningún producto."""
    from apps.suppliers import pedidos

    resultado = pedidos.enviar_pedido(correo.proveedor, [])

    assert not resultado
    assert mail.outbox == []
