"""Restock (plan 05): el aviso de reposición y la propuesta a proveedores.

`CO-075` y `CO-076` anotan y quitan a un Cliente de la lista de espera.
`CO-077` avisa a los primeros cuando el stock sube (B-05-001). `CO-067` y
`CO-068` arman la propuesta, que el Administrador ajusta (`CO-069` a `CO-071`) y
despacha o descarta por proveedor (`CO-072`, `CO-073`, con el correo de
`CO-074`).
"""

import logging
from collections import OrderedDict
from dataclasses import dataclass, field
from datetime import timedelta

from django.conf import settings
from django.db import IntegrityError, transaction
from django.db.models import Count, Q
from django.urls import reverse
from django.utils import timezone

from apps.catalog.models import Producto, ProductoEditorial
from apps.core.mail import cuerpo_html, enviar_correo
from apps.core.models import ConfiguracionSistema, RegistroAuditoria
from apps.core.segundo_plano import despues_del_commit
from apps.pedidos import avisos
from apps.restock.models import LineaPropuestaRestock, PropuestaRestock, SuscripcionReposicion
from apps.suppliers import pedidos as pedidos_a_proveedor
from apps.suppliers.models import Proveedor

logger = logging.getLogger(__name__)

INTENTOS = 3
SEMANA = timedelta(days=7)


class OperacionRechazada(ValueError):
    """La operación no corresponde al estado actual."""


class YaHayStock(OperacionRechazada):
    """`CO-075` E2: el producto recuperó stock entre la ficha y el clic."""


# ---------------------------------------------------------------------------
# CO-075 suscribirseAReposicion · CO-076 cancelarSuscripcionDeReposicion
# ---------------------------------------------------------------------------


def admite_aviso(producto):
    """B-05-002: Agotado, o Activo sin stock. Y la pre-venta completa (plan 00 del
    circuito, ambigüedad 5): la lista de espera se avisa si llega de más."""
    from apps.suppliers import llegadas

    if producto.estado == Producto.PRE_VENTA:
        return llegadas.cupo(producto) == 0
    return producto.estado == Producto.AGOTADO or (
        producto.estado == Producto.ACTIVO and producto.stock == 0
    )


def en_espera(producto):
    """El contador de suscriptores activos: derivado, no guardado."""
    return SuscripcionReposicion.objects.filter(
        producto_id=producto.pk, estado__in=SuscripcionReposicion.EN_ESPERA
    ).count()


def suscripcion_de(usuario, producto):
    if not getattr(usuario, "is_authenticated", False):
        return None
    return SuscripcionReposicion.objects.filter(
        usuario=usuario, producto_id=producto.pk, estado__in=SuscripcionReposicion.EN_ESPERA
    ).first()


def suscribir(usuario, producto):
    """`CO-075`. Sin auditoría: lo dice el contrato. E1 devuelve la que ya había."""
    with transaction.atomic():
        producto = Producto.objects.select_for_update().get(pk=producto.pk)
        if not admite_aviso(producto):
            raise YaHayStock("Este producto ya tiene unidades disponibles.")
        existente = suscripcion_de(usuario, producto)
        if existente:
            return existente
        try:
            with transaction.atomic():
                return SuscripcionReposicion.objects.create(usuario=usuario, producto=producto)
        except IntegrityError:
            # I-22: otra pestaña la creó en el mismo instante.
            return suscripcion_de(usuario, producto)


def cancelar_suscripcion(usuario, producto):
    """`CO-076`: se elimina la suscripción. Sin auditoría."""
    return SuscripcionReposicion.objects.filter(
        usuario=usuario, producto_id=producto.pk, estado__in=SuscripcionReposicion.EN_ESPERA
    ).delete()[0]


# ---------------------------------------------------------------------------
# CO-077 notificarReposicionASuscriptores
# ---------------------------------------------------------------------------


@dataclass
class ResultadoDeReposicion:
    notificadas: list = field(default_factory=list)
    fallidas: list = field(default_factory=list)
    en_espera: int = 0


def reposicion(producto, unidades, *, origen=""):
    """`CO-077` con N = unidades que subió el stock (B-05-001).

    Se llama después de confirmar la suba. Se eligen los primeros `min(N, M)` en
    espera; si uno canceló antes de que le llegue su turno (E2), su cupo no pasa
    al siguiente.
    """
    if unidades <= 0:
        return ResultadoDeReposicion()
    elegidas = list(
        SuscripcionReposicion.objects.filter(
            producto_id=producto.pk, estado__in=SuscripcionReposicion.EN_ESPERA
        )
        .order_by("creada_en", "pk")
        .values_list("pk", flat=True)[:unidades]
    )
    resultado = ResultadoDeReposicion()
    if not elegidas:
        return resultado  # A1: nada que avisar ni que registrar.
    origen = origen or settings.URL_PUBLICA
    enlace = origen + reverse("core:tienda_producto", args=[producto.pk]) if origen else ""
    for pk in elegidas:
        with transaction.atomic():
            suscripcion = (
                SuscripcionReposicion.objects.select_for_update()
                .select_related("usuario", "producto")
                .filter(pk=pk, estado__in=SuscripcionReposicion.EN_ESPERA)
                .first()
            )
            if suscripcion is None:
                continue  # E2
            if _avisar_reposicion(suscripcion, enlace):
                suscripcion.estado = SuscripcionReposicion.NOTIFICADA
                suscripcion.notificada_en = timezone.now()
                resultado.notificadas.append(suscripcion)
            else:
                suscripcion.estado = SuscripcionReposicion.FALLIDA
                resultado.fallidas.append(suscripcion)
                RegistroAuditoria.registrar(
                    accion=RegistroAuditoria.NOTIFICACION_FALLIDA,
                    objetivo=suscripcion.usuario,
                    detalle=(
                        f"Aviso de reposición de {producto} a {suscripcion.usuario.email}: falló "
                        f"{INTENTOS} veces. Conserva su turno."
                    ),
                )
            suscripcion.save(update_fields=["estado", "notificada_en"])
    resultado.en_espera = en_espera(producto)
    RegistroAuditoria.registrar(
        accion=RegistroAuditoria.NOTIFICACION_REPOSICION,
        objetivo=producto,
        detalle=(
            f"{producto}: ingresaron {unidades} unidad(es), {len(resultado.notificadas)} "
            f"suscriptor(es) notificado(s), {resultado.en_espera} en espera."
        ),
    )
    return resultado


def _avisar_reposicion(suscripcion, enlace):
    """Tres intentos seguidos (B-05-005). Devuelve si salió."""
    producto = suscripcion.producto.especifico
    parrafos = [f"{producto} volvió a tener stock. Te avisamos porque lo pediste."]
    texto = "\n\n".join(parrafos) + (f"\n\nComprarlo: {enlace}" if enlace else "") + "\n"
    contexto = {
        "asunto": f"{producto} volvió a tener stock",
        "titulo": "Volvió a tener stock",
        "antetitulo": "Aviso de reposición",
        "rotulo": "Tienda",
        "parrafos": parrafos,
        "filas": (),
        "enlace": enlace,
        "texto_enlace": "Comprarlo",
    }
    for intento in range(1, INTENTOS + 1):
        try:
            enviar_correo(
                asunto=contexto["asunto"],
                cuerpo=texto,
                destinatarios=[suscripcion.usuario.email],
                html=cuerpo_html("correo/aviso.html", contexto),
            )
        except Exception as error:  # noqa: BLE001 - se reintenta y se registra
            logger.warning(
                "Intento %s de %s: falló el aviso de reposición a %s (%s)",
                intento,
                INTENTOS,
                suscripcion.usuario.email,
                error,
            )
            continue
        return True
    return False


def al_subir_stock(producto, antes, despues, *, origen=""):
    """El enganche de las subas de stock (B-05-001): se avisa después del commit."""
    if despues > antes:
        despues_del_commit(reposicion, producto, despues - antes, origen=origen)


# ---------------------------------------------------------------------------
# A qué proveedor va cada producto (B-05-003)
# ---------------------------------------------------------------------------


def _habituales():
    """Editorial → el único proveedor activo que la tiene como habitual."""
    por_editorial = {}
    for proveedor in Proveedor.objects.filter(estado=Proveedor.ACTIVO, editorial__isnull=False):
        por_editorial.setdefault(proveedor.editorial_id, []).append(proveedor)
    return {e: lista[0] for e, lista in por_editorial.items() if len(lista) == 1}


def _inactivos():
    """Editorial → un proveedor dado de baja que la tenía como habitual."""
    return dict(
        Proveedor.objects.filter(estado=Proveedor.INACTIVO, editorial__isnull=False)
        .order_by("-pk")
        .values_list("editorial_id", "pk")
    )


def proveedor_inactivo_de(producto, resuelto, inactivos):
    """`CO-064` (c): el proveedor dado de baja que la línea involucraba, o `None`.

    El suyo, si lo tiene y está inactivo; si no lo tiene, el habitual inactivo de
    su editorial, sólo cuando ningún activo lo reemplaza. Se deriva y no se
    guarda: la reactivación (`CO-066`) la limpia sin tocar la propuesta.
    """
    if producto.proveedor_id:
        return producto.proveedor if producto.proveedor.estado == Proveedor.INACTIVO else None
    if resuelto is None and producto.editorial_id in inactivos:
        return Proveedor.objects.get(pk=inactivos[producto.editorial_id])
    return None


def proveedor_de(producto, habituales=None):
    if producto.proveedor_id and producto.proveedor.estado == Proveedor.ACTIVO:
        return producto.proveedor
    habituales = _habituales() if habituales is None else habituales
    return habituales.get(producto.editorial_id)


# ---------------------------------------------------------------------------
# CO-067 ejecutarCicloDePropuestaDeRestock · CO-068 generarPropuestaDeRestock
# ---------------------------------------------------------------------------


def elegibles(configuracion=None):
    """Editoriales Activos o Agotados con menos unidades que el margen (B-05-003).

    Con margen cero entra lo que tiene stock cero.
    """
    configuracion = configuracion or ConfiguracionSistema.obtener()
    tope = max(configuracion.margen_stock_restock, 1)
    return (
        ProductoEditorial.objects.filter(
            estado__in=(Producto.ACTIVO, Producto.AGOTADO), stock__lt=tope
        )
        .select_related("proveedor", "editorial")
        .annotate(
            en_espera=Count(
                "suscripciones_reposicion",
                filter=Q(suscripciones_reposicion__estado__in=SuscripcionReposicion.EN_ESPERA),
            )
        )
    )


def sugerida(suscriptores, configuracion):
    """El mayor entre suscriptores + margen y la cantidad mínima (`CO-067`)."""
    return max(
        suscriptores + configuracion.margen_stock_restock, configuracion.cantidad_minima_restock
    )


@dataclass
class ResultadoDeCiclo:
    propuesta: PropuestaRestock | None = None
    motivo: str = ""


def pendiente():
    return PropuestaRestock.objects.filter(estado=PropuestaRestock.PENDIENTE).first()


def ciclo_semanal(ahora=None):
    """`CO-067`: el Temporizador lo intenta todos los días (B-05-004)."""
    ahora = ahora or timezone.now()
    if PropuestaRestock.objects.filter(fecha_generacion__gt=ahora - SEMANA).exists():
        return ResultadoDeCiclo(motivo="reciente")  # E4: ya hubo una esta semana.
    return _generar(PropuestaRestock.AUTOMATICO, None, ahora)


def generar_manual(actor):
    """`CO-068`: sin la ventana de la semana, sólo con I-21 (E3)."""
    return _generar(PropuestaRestock.MANUAL, actor, timezone.now())


def _generar(disparo, actor, ahora):
    configuracion = ConfiguracionSistema.obtener()
    if pendiente():
        _registrar_sin_propuesta(
            disparo, actor, ahora, "Hay una propuesta pendiente sin resolver.", "pendiente"
        )
        return ResultadoDeCiclo(motivo="pendiente")  # E3
    productos = list(elegibles(configuracion))
    if not productos and disparo == PropuestaRestock.AUTOMATICO:
        _registrar_sin_propuesta(
            disparo, actor, ahora, "Ciclo completado sin productos elegibles.", "sin_elegibles"
        )
        return ResultadoDeCiclo(motivo="sin_elegibles")  # E1
    try:
        with transaction.atomic():
            propuesta = PropuestaRestock.objects.create(
                tipo_disparo=disparo, fecha_generacion=ahora
            )
            LineaPropuestaRestock.objects.bulk_create(
                LineaPropuestaRestock(
                    propuesta=propuesta,
                    producto=p,
                    cantidad_sugerida=sugerida(p.en_espera, configuracion),
                    suscriptores_activos=p.en_espera,
                )
                for p in productos
            )
            if not productos:
                # CO-068 E1: la propuesta manual vacía queda cerrada, y su fecha
                # basta para omitir el ciclo de la semana.
                propuesta.estado = PropuestaRestock.CERRADA
                propuesta.cerrada_en = ahora
                propuesta.save(update_fields=["estado", "cerrada_en"])
            grupos = agrupar(propuesta)
            RegistroAuditoria.registrar(
                accion=RegistroAuditoria.PROPUESTA_RESTOCK,
                actor=actor,
                objetivo=propuesta,
                detalle=(
                    f"Disparo {propuesta.get_tipo_disparo_display().lower()}: "
                    + (
                        "; ".join(f"{g.nombre}: {len(g.lineas)} producto(s)" for g in grupos)
                        if productos
                        else "ciclo completado sin productos elegibles"
                    )
                    + (
                        ". Se omite el ciclo automático de la semana."
                        if disparo == PropuestaRestock.MANUAL
                        else "."
                    )
                ),
            )
    except IntegrityError:
        # I-21: el ciclo y el botón generaron a la vez; quedó la otra.
        return ResultadoDeCiclo(motivo="pendiente")
    if productos:
        despues_del_commit(_avisar_propuesta, propuesta)
    return ResultadoDeCiclo(propuesta=propuesta)


def _registrar_sin_propuesta(disparo, actor, ahora, texto, clave):
    """E1 y E3: se registra y se avisa una vez por semana, no todos los días (B-05-004)."""
    if (
        disparo == PropuestaRestock.AUTOMATICO
        and RegistroAuditoria.objects.filter(
            accion=RegistroAuditoria.PROPUESTA_RESTOCK,
            actor__isnull=True,
            detalle=texto,
            ocurrido_en__gt=ahora - SEMANA,
        ).exists()
    ):
        return
    RegistroAuditoria.registrar(
        accion=RegistroAuditoria.PROPUESTA_RESTOCK, actor=actor, detalle=texto
    )
    if clave == "pendiente":
        avisos.avisar_administradores(
            tipo="restock",
            rotulo="Restock",
            asunto="Propuesta de restock pendiente",
            antetitulo="Restock",
            titulo="Propuesta pendiente",
            parrafos=["Hay una propuesta de restock sin resolver: no se generó una nueva."],
        )


def _avisar_propuesta(propuesta):
    grupos = agrupar(propuesta)
    lineas = [linea for g in grupos for linea in g.lineas]
    avisos.avisar_administradores(
        tipo="restock",
        rotulo="Restock",
        asunto="Nueva propuesta de restock",
        antetitulo="Restock",
        titulo="Propuesta de restock",
        parrafos=["Hay una propuesta de restock para revisar."],
        filas=[
            ("Productos", len(lineas)),
            ("Proveedores", len([g for g in grupos if g.proveedor])),
            ("Suscriptores en espera", sum(linea.suscriptores_activos for linea in lineas)),
        ],
        enlace=settings.URL_PUBLICA + reverse("restock:propuesta") if settings.URL_PUBLICA else "",
        texto_enlace="Revisar la propuesta",
    )


# ---------------------------------------------------------------------------
# CO-174 consultarPropuestaDeRestock · CO-175 consultarLineasDeProveedor
# ---------------------------------------------------------------------------


@dataclass
class Grupo:
    proveedor: Proveedor | None
    lineas: list = field(default_factory=list)

    @property
    def clave(self):
        return self.proveedor.pk if self.proveedor else 0

    @property
    def nombre(self):
        return self.proveedor.razon_social if self.proveedor else "Sin proveedor"

    @property
    def estado(self):
        estados = {linea.estado_despacho for linea in self.lineas}
        if LineaPropuestaRestock.PENDIENTE in estados:
            return LineaPropuestaRestock.PENDIENTE
        return estados.pop() if len(estados) == 1 else LineaPropuestaRestock.DESPACHADO

    @property
    def pendiente(self):
        return self.estado == LineaPropuestaRestock.PENDIENTE

    @property
    def sin_contacto(self):
        """E2: el proveedor no tiene correo."""
        return self.proveedor is not None and not self.proveedor.correo_comercial

    @property
    def unidades(self):
        return sum(linea.cantidad_sugerida for linea in self.lineas)

    @property
    def suscriptores(self):
        return sum(linea.suscriptores_activos for linea in self.lineas)

    @property
    def despachable(self):
        return self.pendiente and self.proveedor is not None and not self.sin_contacto


def agrupar(propuesta):
    """Las líneas por proveedor; dentro de cada grupo, por suscriptores (CO-067)."""
    habituales, inactivos = _habituales(), _inactivos()
    grupos = OrderedDict()
    lineas = propuesta.lineas.select_related(
        "producto", "producto__proveedor", "producto__editorial"
    ).order_by("-suscriptores_activos", "producto__titulo", "producto__volumen")
    for linea in lineas:
        proveedor = proveedor_de(linea.producto, habituales)
        linea.proveedor_inactivo = proveedor_inactivo_de(linea.producto, proveedor, inactivos)
        clave = proveedor.pk if proveedor else 0
        grupos.setdefault(clave, Grupo(proveedor=proveedor)).lineas.append(linea)
    return sorted(grupos.values(), key=lambda g: (g.proveedor is None, g.nombre.lower()))


def grupo_de(propuesta, clave):
    for grupo in agrupar(propuesta):
        if grupo.clave == clave:
            return grupo
    raise OperacionRechazada("Ese proveedor no está en la propuesta.")


# ---------------------------------------------------------------------------
# CO-069 a CO-071: ajustes antes de despachar
# ---------------------------------------------------------------------------


def _linea_editable(linea_pk):
    linea = (
        LineaPropuestaRestock.objects.select_for_update()
        .select_related("propuesta", "producto")
        .get(pk=linea_pk)
    )
    if (
        linea.propuesta.estado != PropuestaRestock.PENDIENTE
        or linea.estado_despacho != LineaPropuestaRestock.PENDIENTE
    ):
        raise OperacionRechazada("Ese producto ya se despachó o se descartó.")
    return linea


def ajustar_cantidad(linea_pk, cantidad):
    """`CO-069`. La cantidad es mayor que cero; los suscriptores no cambian."""
    if cantidad is None or cantidad <= 0:
        raise OperacionRechazada("La cantidad tiene que ser mayor que cero.")
    with transaction.atomic():
        linea = _linea_editable(linea_pk)
        linea.cantidad_sugerida = cantidad
        linea.save(update_fields=["cantidad_sugerida"])
    return linea


def ajustar_cantidades(propuesta, clave, cantidades):
    """`CO-069` sobre varias líneas de un mismo proveedor, todo o nada (plan 00 de
    interfaz, segunda parte, 14.3). `cantidades` va de la línea a su cantidad nueva;
    las que no cambian no se tocan. Devuelve cuántas cambiaron."""
    grupo = grupo_de(propuesta, clave)
    actuales = {linea.pk: linea for linea in grupo.lineas}
    cambiadas = 0
    with transaction.atomic():
        for pk, cantidad in cantidades.items():
            linea = actuales.get(pk)
            if linea is None or cantidad == linea.cantidad_sugerida:
                continue
            if cantidad is None or cantidad <= 0:
                raise OperacionRechazada(
                    f"«{linea.producto}»: la cantidad tiene que ser mayor que cero."
                )
            ajustar_cantidad(pk, cantidad)
            cambiadas += 1
    return cambiadas


def eliminar_linea(linea_pk):
    """`CO-070`."""
    with transaction.atomic():
        linea = _linea_editable(linea_pk)
        linea.delete()
    return linea


def agregar_producto(propuesta, producto, cantidad):
    """`CO-071`: va al grupo de su proveedor, no al que se estaba mirando."""
    if cantidad is None or cantidad <= 0:
        raise OperacionRechazada("La cantidad tiene que ser mayor que cero.")
    with transaction.atomic():
        propuesta = PropuestaRestock.objects.select_for_update().get(pk=propuesta.pk)
        if propuesta.estado != PropuestaRestock.PENDIENTE:
            raise OperacionRechazada("La propuesta ya está cerrada.")
        if propuesta.lineas.filter(producto=producto).exists():
            raise OperacionRechazada(f"«{producto}» ya está en la propuesta.")
        proveedor = proveedor_de(producto)
        clave = proveedor.pk if proveedor else 0
        for grupo in agrupar(propuesta):
            if grupo.clave == clave and not grupo.pendiente:
                raise OperacionRechazada(
                    f"El pedido a {grupo.nombre} ya se despachó o se descartó."
                )
        return LineaPropuestaRestock.objects.create(
            propuesta=propuesta,
            producto=producto,
            cantidad_sugerida=cantidad,
            suscriptores_activos=en_espera(producto),
            anadida_a_mano=True,
        )


# ---------------------------------------------------------------------------
# CO-072 despacharPedidoAProveedor · CO-073 descartarProveedorDePropuesta
# ---------------------------------------------------------------------------


def _lineas_del_grupo(propuesta, clave):
    """Las líneas pendientes del grupo, con bloqueo, tras bloquear la propuesta."""
    propuesta = PropuestaRestock.objects.select_for_update().get(pk=propuesta.pk)
    if propuesta.estado != PropuestaRestock.PENDIENTE:
        raise OperacionRechazada("La propuesta ya está cerrada.")
    grupo = grupo_de(propuesta, clave)
    pks = [
        linea.pk
        for linea in grupo.lineas
        if linea.estado_despacho == LineaPropuestaRestock.PENDIENTE
    ]
    lineas = list(
        LineaPropuestaRestock.objects.select_for_update()
        .filter(pk__in=pks, estado_despacho=LineaPropuestaRestock.PENDIENTE)
        .select_related("producto")
        .order_by("pk")
    )
    if not lineas:
        raise OperacionRechazada(f"El pedido a {grupo.nombre} ya se despachó o se descartó.")
    return propuesta, grupo, lineas


def despachar(propuesta, clave, actor, *, fecha_estimada=None):
    """`CO-072`, con el correo de `CO-074`. Si falla (E2), el grupo sigue Pendiente.

    Si sale, queda el pedido a proveedor que se espera en «Pedidos por llegar», con
    la llegada estimada si el Administrador la indicó (plan 00 del circuito).
    """
    with transaction.atomic():
        propuesta, grupo, lineas = _lineas_del_grupo(propuesta, clave)
        if grupo.proveedor is None:
            raise OperacionRechazada(
                "Estos productos no tienen proveedor: asígnele la editorial a un proveedor o "
                "descarte el grupo."
            )
        envio = enviar_pedido_consolidado(
            grupo.proveedor, lineas, actor, propuesta=propuesta, fecha_estimada=fecha_estimada
        )
        if not envio.enviado:
            despues_del_commit(_avisar_fallo_de_pedido, grupo.proveedor, envio.error)
            return envio
        LineaPropuestaRestock.objects.filter(pk__in=[linea.pk for linea in lineas]).update(
            estado_despacho=LineaPropuestaRestock.DESPACHADO
        )
        RegistroAuditoria.registrar(
            accion=RegistroAuditoria.DESPACHO_RESTOCK,
            actor=actor,
            objetivo=propuesta,
            detalle=f"{grupo.nombre}: "
            + ", ".join(f"{linea.producto} × {linea.cantidad_sugerida}" for linea in lineas),
        )
        _cerrar_si_corresponde(propuesta, actor)
    return envio


def descartar(propuesta, clave, motivo, actor):
    """`CO-073`: todo el grupo, con su motivo."""
    motivo = (motivo or "").strip()
    if not motivo:
        raise OperacionRechazada("El motivo es obligatorio.")
    with transaction.atomic():
        propuesta, grupo, lineas = _lineas_del_grupo(propuesta, clave)
        LineaPropuestaRestock.objects.filter(pk__in=[linea.pk for linea in lineas]).update(
            estado_despacho=LineaPropuestaRestock.DESCARTADO, motivo_descarte=motivo
        )
        RegistroAuditoria.registrar(
            accion=RegistroAuditoria.DESCARTE_RESTOCK,
            actor=actor,
            objetivo=propuesta,
            detalle=f"{grupo.nombre}: {len(lineas)} producto(s) descartado(s). Motivo: {motivo}",
        )
        _cerrar_si_corresponde(propuesta, actor)


def _cerrar_si_corresponde(propuesta, actor):
    """El cierre es automático cuando no queda nada pendiente (DME-13)."""
    if propuesta.lineas.filter(estado_despacho=LineaPropuestaRestock.PENDIENTE).exists():
        return
    propuesta.estado = PropuestaRestock.CERRADA
    propuesta.cerrada_en = timezone.now()
    propuesta.save(update_fields=["estado", "cerrada_en"])
    lineas = propuesta.lineas.all()
    despachadas = sum(
        1 for linea in lineas if linea.estado_despacho == LineaPropuestaRestock.DESPACHADO
    )
    RegistroAuditoria.registrar(
        accion=RegistroAuditoria.CIERRE_PROPUESTA_RESTOCK,
        actor=actor,
        objetivo=propuesta,
        detalle=(
            f"{propuesta}: {despachadas} producto(s) despachado(s), "
            f"{len(lineas) - despachadas} descartado(s)."
        ),
    )


# ---------------------------------------------------------------------------
# CO-074 enviarPedidoConsolidado
# ---------------------------------------------------------------------------


def enviar_pedido_consolidado(proveedor, lineas, actor, *, propuesta=None, fecha_estimada=None):
    """`CO-074` desde la propuesta: el correo de `suppliers/pedidos.py`, su registro
    y, si sale, el pedido a proveedor."""
    from apps.suppliers.models import PedidoProveedor

    renglones = [
        pedidos_a_proveedor.LineaDePedido(
            titulo=linea.producto.titulo,
            volumen=linea.producto.volumen,
            isbn=linea.producto.isbn,
            cantidad=linea.cantidad_sugerida,
            producto=linea.producto,
        )
        for linea in lineas
    ]
    return pedidos_a_proveedor.enviar_y_registrar(
        proveedor,
        renglones,
        actor,
        origen=PedidoProveedor.RESTOCK,
        propuesta=propuesta,
        fecha_estimada=fecha_estimada,
    )


def _avisar_fallo_de_pedido(proveedor, error):
    avisos.avisar_administradores(
        tipo="restock",
        rotulo="Restock",
        asunto=f"No salió el pedido a {proveedor.razon_social}",
        antetitulo="Restock",
        titulo="Pedido sin enviar",
        parrafos=[
            f"El correo a {proveedor.razon_social} falló {INTENTOS} veces. El pedido sigue "
            "pendiente: vuelva a despacharlo.",
        ],
        filas=[("Error", error or "Sin correo registrado")],
    )
