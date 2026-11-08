"""Pedidos a proveedores: lo que viene en camino y su llegada (plan 00 del circuito).

Sólo el Administrador. La llegada va en dos tiempos, como «Pre-ventas por
llegar»: se carga lo que llegó de verdad, el sistema muestra lo que va a pasar
—cuántas reservas cubre, cuánto queda a la venta— y recién al confirmar se
registra. Volver sin confirmar no deja nada.
"""

import datetime
from urllib.parse import urlencode

from django import forms
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Prefetch
from django.forms import formset_factory
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.html import format_html
from django.utils.http import url_has_allowed_host_and_scheme
from django.views import View

from apps.accounts.models import Usuario
from apps.catalog import busqueda
from apps.catalog.models import Producto
from apps.core.mixins import RolRequeridoMixin
from apps.suppliers import llegadas, recepcion, respuestas
from apps.suppliers import pedidos as correo_de_pedido
from apps.suppliers.models import LineaPedidoProveedor, PedidoProveedor, Proveedor


def fecha_o_nada(texto):
    """Una fecha `AAAA-MM-DD` del formulario, o `None` si viene vacía o no existe."""
    try:
        return datetime.date.fromisoformat((texto or "").strip())
    except ValueError:
        return None


def _entero(texto):
    texto = (texto or "").strip()
    return int(texto) if texto.isdigit() else None


class PedidosMixin(RolRequeridoMixin):
    roles_permitidos = (Usuario.ADMINISTRADOR,)


# ---------------------------------------------------------------------------
# Lista y ficha
# ---------------------------------------------------------------------------


class PedidoListaView(PedidosMixin, View):
    """Los pedidos, abiertos primero. «Por llegar» es la vista por omisión."""

    FILTROS = {"abiertos": "Por llegar", "cerrados": "Cerrados", "todos": "Todos"}  # noqa: RUF012

    def get(self, request):
        filtro = request.GET.get("estado", "abiertos")
        if filtro not in self.FILTROS:
            filtro = "abiertos"
        # Cada línea con su producto ya bajado a la hija: el nombre lleva el tomo.
        pedidos = PedidoProveedor.objects.select_related("proveedor").prefetch_related(
            Prefetch("lineas", queryset=_lineas_con_producto())
        )
        if filtro == "abiertos":
            # Los que no salieron, primero: esperan una mano (B-05-014).
            pedidos = pedidos.filter(
                estado__in=(PedidoProveedor.SIN_ENVIAR, PedidoProveedor.ABIERTO)
            ).order_by("-estado", "fecha_estimada", "creado_en")
        elif filtro == "cerrados":
            pedidos = pedidos.filter(estado=PedidoProveedor.CERRADO)
        pagina = Paginator(pedidos, 30).get_page(request.GET.get("pagina"))
        abiertos = PedidoProveedor.objects.filter(estado=PedidoProveedor.ABIERTO)
        return render(
            request,
            "suppliers/pedido_lista.html",
            {
                "pagina": pagina,
                "filtro": filtro,
                "filtros": self.FILTROS,
                "por_llegar": abiertos.count(),
                "unidades_por_llegar": sum(
                    linea.pendiente
                    for linea in LineaPedidoProveedor.objects.filter(
                        estado__in=LineaPedidoProveedor.ABIERTAS,
                        pedido__estado=PedidoProveedor.ABIERTO,
                    )
                ),
                "sin_enviar": PedidoProveedor.objects.filter(
                    estado=PedidoProveedor.SIN_ENVIAR
                ).count(),
                "atrasados": abiertos.filter(fecha_estimada__lt=datetime.date.today()).count(),
            },
        )


def _lineas_con_producto():
    return LineaPedidoProveedor.objects.select_related(
        "producto__productoeditorial", "producto__productonoeditorial"
    ).order_by("pk")


def _filas(pedido):
    """Cada línea con lo que hace falta para decidir la llegada."""
    filas = []
    for linea in _lineas_con_producto().filter(pedido=pedido):
        producto = linea.producto
        filas.append(
            {
                "linea": linea,
                "producto": producto,
                "en_preventa": producto.estado == Producto.PRE_VENTA,
                "reservado": llegadas.reservado(producto),
            }
        )
    return filas


class PedidoDetalleView(PedidosMixin, View):
    def get(self, request, pk):
        pedido = get_object_or_404(
            PedidoProveedor.objects.select_related("proveedor").prefetch_related(
                Prefetch("lineas", queryset=_lineas_con_producto())
            ),
            pk=pk,
        )
        return render(
            request,
            "suppliers/pedido_detalle.html",
            {
                "pedido": pedido,
                "filas": _filas(pedido),
                "volver": request.path,
                "enlaces": enlaces_de_respuesta(pedido, request.path),
            },
        )


# ---------------------------------------------------------------------------
# B-05-014 · el pedido que no salió
# ---------------------------------------------------------------------------


class ReintentarEnvioView(PedidosMixin, View):
    """Vuelve a mandar el correo de un pedido «Sin enviar»."""

    http_method_names = ["post"]  # noqa: RUF012

    def post(self, request, pk):
        pedido = get_object_or_404(PedidoProveedor, pk=pk)
        try:
            envio = correo_de_pedido.reintentar(pedido, request.user)
        except llegadas.OperacionRechazada as rechazo:
            messages.error(request, str(rechazo))
        else:
            if envio.enviado:
                messages.success(
                    request, f"Salió el pedido a {pedido.nombre_proveedor}: ya está por llegar."
                )
            else:
                messages.error(
                    request,
                    f"Sigue sin salir ({envio.error}). Revisá el correo del proveedor o la "
                    "configuración del correo saliente, y probá de nuevo.",
                )
        return redirect("suppliers:pedido_detalle", pk=pedido.pk)


class DescartarSinEnviarView(PedidosMixin, View):
    """Un pedido «Sin enviar» que ya no se va a mandar, con su motivo."""

    http_method_names = ["post"]  # noqa: RUF012

    def post(self, request, pk):
        pedido = get_object_or_404(PedidoProveedor, pk=pk)
        try:
            correo_de_pedido.descartar_sin_enviar(pedido, request.POST.get("motivo"), request.user)
        except llegadas.OperacionRechazada as rechazo:
            messages.error(request, str(rechazo))
        else:
            messages.success(request, "Se descartó el pedido sin enviar.")
        return redirect("suppliers:pedido_detalle", pk=pedido.pk)


# ---------------------------------------------------------------------------
# La respuesta del proveedor (plan 00 de la respuesta del proveedor)
# ---------------------------------------------------------------------------


def _es_del_sitio(request, destino):
    return bool(destino) and url_has_allowed_host_and_scheme(
        destino, allowed_hosts={request.get_host()}, require_https=request.is_secure()
    )


def _volver_a(request, pedido):
    """La ficha a la que se vuelve (la del pedido, o la propuesta de la que vino)."""
    destino = request.GET.get("volver", "")
    return (
        destino
        if _es_del_sitio(request, destino)
        else reverse("suppliers:pedido_detalle", args=[pedido.pk])
    )


def _volver(request, pedido):
    """A la ficha de la que vino el formulario (la propuesta o el pedido), dentro del sitio."""
    destino = request.POST.get("volver", "")
    if not _es_del_sitio(request, destino):
        destino = reverse("suppliers:pedido_detalle", args=[pedido.pk])
    return redirect(f"{destino}#respuesta-{pedido.pk}")


# Plan 00 de la respuesta simple: una pregunta con tres respuestas, cada una en su
# pantalla (que se abre como diálogo sobre la ficha), más cambiar la fecha.
TIPOS_DE_RESPUESTA = {
    "todo": "Confirmó todo",
    "cambios": "Confirmó con cambios",
    "no-puede": "No puede abastecer",
    "fecha": "La fecha de llegada",
}


def enlaces_de_respuesta(pedido, volver):
    """Las pantallas de cada respuesta, con la ficha a la que vuelven."""
    consulta = urlencode({"volver": volver})
    return {
        tipo.replace("-", "_"): f"{reverse('suppliers:pedido_responder', args=[pedido.pk, tipo])}"
        f"?{consulta}"
        for tipo in TIPOS_DE_RESPUESTA
    }


class ResponderView(PedidosMixin, View):
    """La pantalla de una respuesta. El formulario va a `RespuestaView`."""

    def get(self, request, pk, tipo):
        if tipo not in TIPOS_DE_RESPUESTA:
            raise Http404
        pedido = get_object_or_404(
            PedidoProveedor.objects.select_related("proveedor").prefetch_related(
                Prefetch("lineas", queryset=_lineas_con_producto())
            ),
            pk=pk,
        )
        if pedido.estado != PedidoProveedor.ABIERTO:
            messages.error(request, "Ese pedido no está esperando respuesta.")
            return redirect("suppliers:pedido_detalle", pk=pedido.pk)
        contexto = {
            "pedido": pedido,
            "tipo": tipo,
            "titulo": TIPOS_DE_RESPUESTA[tipo],
            "volver": _volver_a(request, pedido),
            "motivos": respuestas.MOTIVOS_NO_PUEDE,
        }
        if tipo == "cambios":
            contexto["lineas"] = [
                linea
                for linea in pedido.lineas.all()
                if linea.estado in LineaPedidoProveedor.ABIERTAS
            ]
        if tipo == "no-puede":
            contexto["consecuencias"] = respuestas.consecuencias_de_no_puede(pedido)
        return render(request, "suppliers/pedido_responder.html", contexto)


class RespuestaView(PedidosMixin, View):
    """Lo que contestó el proveedor: todo, con cambios, nada, o la fecha."""

    http_method_names = ["post"]  # noqa: RUF012

    def post(self, request, pk):
        pedido = get_object_or_404(PedidoProveedor, pk=pk)
        accion = request.POST.get("accion", "cambios")
        fecha = fecha_o_nada(request.POST.get("fecha"))
        if fecha == pedido.fecha_estimada:
            fecha = None
        try:
            if accion == "todo":
                resultado = respuestas.confirmar_todo(pedido, request.user, fecha=fecha)
            elif accion == "nada":
                motivo = request.POST.get("motivo", "")
                if motivo == "otro":
                    motivo = request.POST.get("motivo_otro", "")
                resultado = respuestas.no_puede(pedido, motivo, request.user)
            elif accion == "fecha":
                if request.POST.get("sin_fecha"):
                    respuestas.quitar_fecha(pedido, request.user)
                    messages.success(request, f"El pedido #{pedido.pk} quedó sin fecha.")
                    return _volver(request, pedido)
                if fecha_o_nada(request.POST.get("fecha")) is None:
                    raise llegadas.OperacionRechazada("Elegí la fecha, o marcá «Sin fecha».")
                if fecha is None:
                    messages.info(request, "La fecha no cambió.")
                    return _volver(request, pedido)
                resultado = respuestas.poner_fecha(pedido, fecha, request.user)
            else:
                resultado = respuestas.responder(
                    pedido, _respuestas_del_formulario(request, pedido), request.user, fecha=fecha
                )
        except llegadas.OperacionRechazada as rechazo:
            messages.error(request, str(rechazo))
            return _de_nuevo(request, pedido, accion)
        if accion != "fecha" and not resultado.respondidas and fecha is None:
            messages.info(request, "No cambió nada: la respuesta ya estaba anotada así.")
            return _volver(request, pedido)
        messages.success(request, f"Se anotó la respuesta de {pedido.nombre_proveedor}.")
        _advertencias(request, resultado)
        return _volver(request, pedido)


def _respuestas_del_formulario(request, pedido):
    """«Con cambios»: cada línea abierta con su opción, su cantidad y su motivo."""
    elegidas = {}
    for linea in pedido.lineas.filter(estado__in=LineaPedidoProveedor.ABIERTAS):
        respuesta = request.POST.get(f"respuesta-{linea.pk}", "")
        if respuesta:
            elegidas[linea.pk] = (
                respuesta,
                _entero(request.POST.get(f"cantidad-{linea.pk}")),
                request.POST.get(f"motivo-{linea.pk}", ""),
            )
    return elegidas


def _de_nuevo(request, pedido, accion):
    """Ante un error, a la misma pantalla de la respuesta, para corregir."""
    tipo = {"todo": "todo", "nada": "no-puede", "fecha": "fecha"}.get(accion, "cambios")
    destino = reverse("suppliers:pedido_responder", args=[pedido.pk, tipo])
    volver = request.POST.get("volver", "")
    return redirect(
        f"{destino}?{urlencode({'volver': volver})}" if _es_del_sitio(request, volver) else destino
    )


def _advertencias(request, resultado):
    """R7: lo que queda para resolver en Pre-ventas, con el enlace a cada producto."""
    for producto, reservado, esperado in resultado.sin_cubrir:
        messages.warning(
            request,
            format_html(
                "«{}» tiene {} reservas y ahora se esperan {}: "
                '<a href="{}">registrá la demora</a> o cancelá la pre-venta.',
                producto.especifico,
                reservado,
                esperado,
                reverse("pedidos:demora", args=[producto.pk]),
            ),
        )
    for producto in resultado.para_demorar:
        messages.warning(
            request,
            format_html(
                "«{}» tiene reservas y la fecha nueva la atrasa: es una demora. "
                '<a href="{}">Registrala</a> para avisar a los clientes.',
                producto.especifico,
                reverse("pedidos:demora", args=[producto.pk]),
            ),
        )
    if resultado.propuesta_cerrada:
        messages.info(request, "Respondieron todos los proveedores: la propuesta se cerró.")


# ---------------------------------------------------------------------------
# La llegada, en dos tiempos
# ---------------------------------------------------------------------------


class LlegadaView(PedidosMixin, View):
    """B-05-017: la llegada se carga en «Por llegar» (`CO-232`). La ficha del pedido
    lleva ahí, abierta en el grupo donde están sus líneas; un envío a la dirección
    vieja no registra nada."""

    def get(self, request, pk):
        pedido = get_object_or_404(PedidoProveedor, pk=pk)
        destino = reverse("suppliers:por_llegar")
        for grupo in recepcion.por_llegar():
            if any(fila.linea and fila.linea.pedido_id == pedido.pk for fila in grupo.filas):
                return redirect(f"{destino}#grupo-{grupo.clave}")
        messages.error(request, "Ese pedido no está esperando mercadería.")
        return redirect("suppliers:pedido_detalle", pk=pedido.pk)

    def post(self, request, pk):
        messages.info(request, "La llegada se carga ahora en «Por llegar». No se registró nada.")
        return redirect("suppliers:pedido_llegada", pk=pk)


class CerrarLineaView(PedidosMixin, View):
    """Lo que no va a llegar: la línea se cierra con su motivo."""

    def _linea(self, pk):
        return get_object_or_404(
            LineaPedidoProveedor.objects.select_related("pedido", "producto"), pk=pk
        )

    def get(self, request, pk):
        linea = self._linea(pk)
        return render(
            request,
            "suppliers/pedido_cerrar_linea.html",
            {"linea": linea, "reservado": llegadas.reservado(linea.producto)},
        )

    def post(self, request, pk):
        linea = self._linea(pk)
        try:
            con_reservas = llegadas.cerrar_sin_recibir(
                linea, request.POST.get("motivo"), request.user
            )
        except llegadas.OperacionRechazada as rechazo:
            messages.error(request, str(rechazo))
            return redirect("suppliers:pedido_cerrar_linea", pk=linea.pk)
        if con_reservas:
            messages.warning(
                request,
                f"«{linea.producto.especifico}» tiene reservas sin cubrir: registrá la demora "
                "o cancelá la pre-venta desde su ficha.",
            )
        else:
            messages.success(request, f"Se cerró «{linea.producto.especifico}» sin recibir.")
        return redirect("suppliers:pedido_detalle", pk=linea.pedido_id)


# ---------------------------------------------------------------------------
# Nuevo pedido a mano
# ---------------------------------------------------------------------------


class PedidoNuevoForm(forms.Form):
    proveedor = forms.ModelChoiceField(
        label="Proveedor",
        queryset=Proveedor.objects.activos().exclude(correo_comercial="").order_by("razon_social"),
        empty_label="Elegí el proveedor",
    )
    fecha_estimada = forms.DateField(
        label="Llegada estimada",
        required=False,
        widget=forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
        help_text="Opcional. Lo que está agotado se ofrece en pre-venta con esta fecha.",
    )

    def clean_fecha_estimada(self):
        fecha = self.cleaned_data.get("fecha_estimada")
        if fecha and fecha < datetime.date.today():
            raise forms.ValidationError("La llegada estimada no puede ser una fecha pasada.")
        return fecha


class RenglonForm(forms.Form):
    # B-05-018: nadie recuerda trescientos códigos. El campo ofrece el catálogo como
    # «código — título #tomo» y acepta también el título con su número.
    producto = forms.CharField(
        label="Producto",
        required=False,
        max_length=200,
        widget=forms.TextInput(
            attrs={
                "placeholder": "Código, ISBN o título con su número",
                "autocomplete": "off",
                "list": "productos-para-pedir",
                "data-autocompletado": "productos-para-pedir",
            }
        ),
    )
    cantidad = forms.IntegerField(
        label="Cantidad",
        required=False,
        min_value=1,
        max_value=9999,
        widget=forms.NumberInput(attrs={"class": "entrada-cifra", "inputmode": "numeric"}),
    )

    def clean(self):
        datos = super().clean()
        texto, cantidad = datos.get("producto"), datos.get("cantidad")
        if not texto and not cantidad:
            return datos
        if not texto:
            self.add_error("producto", "Indicá el producto.")
        else:
            producto, problema = busqueda.buscar_para_pedir(texto, solo_editorial=False)
            if problema:
                self.add_error("producto", problema)
            else:
                datos["producto_resuelto"] = producto
        if not cantidad:
            self.add_error("cantidad", "Indicá cuántas unidades pedir.")
        return datos


RenglonesFormSet = formset_factory(RenglonForm, extra=5, max_num=30)


class PedidoNuevoView(PedidosMixin, View):
    """Un pedido para un producto que ya existe: el correo de `CO-074` y su registro."""

    def get(self, request):
        return self._pantalla(request, PedidoNuevoForm(), RenglonesFormSet(prefix="renglon"))

    def post(self, request):
        form = PedidoNuevoForm(request.POST)
        renglones = RenglonesFormSet(request.POST, prefix="renglon")
        if not (form.is_valid() and renglones.is_valid()):
            return self._pantalla(request, form, renglones)
        elegidos = [r.cleaned_data for r in renglones if r.cleaned_data.get("producto_resuelto")]
        if not elegidos:
            messages.error(request, "Agregá al menos un producto al pedido.")
            return self._pantalla(request, form, renglones)

        proveedor = form.cleaned_data["proveedor"]
        if _de_otro_proveedor(proveedor, renglones):
            return self._pantalla(request, form, renglones)
        lineas = [
            correo_de_pedido.LineaDePedido(
                titulo=datos["producto_resuelto"].titulo,
                volumen=getattr(datos["producto_resuelto"].especifico, "volumen", None),
                isbn=getattr(datos["producto_resuelto"].especifico, "isbn", ""),
                cantidad=datos["cantidad"],
                producto=datos["producto_resuelto"],
            )
            for datos in elegidos
        ]
        envio = correo_de_pedido.enviar_y_registrar(
            proveedor,
            lineas,
            request.user,
            origen=PedidoProveedor.MANUAL,
            fecha_estimada=form.cleaned_data.get("fecha_estimada"),
        )
        if not envio.enviado:
            messages.error(
                request,
                f"No salió el pedido a {proveedor.razon_social} ({envio.error}). No quedó "
                "registrado: volvé a intentarlo.",
            )
            return self._pantalla(request, form, renglones)
        messages.success(request, f"Se envió el pedido a {proveedor.razon_social}.")
        return redirect("suppliers:pedido_detalle", pk=envio.pedido.pk)

    def _pantalla(self, request, form, renglones):
        return render(
            request,
            "suppliers/pedido_nuevo.html",
            {
                "form": form,
                "renglones": renglones,
                "opciones": busqueda.opciones_para_pedir(),
            },
        )


def _de_otro_proveedor(proveedor, renglones):
    """B-05-018: no se le pide a un proveedor lo que trae otro.

    Quién trae cada producto es la regla de Restock (B-05-003): su proveedor, si
    está activo, o el único habitual de su editorial. Si no se sabe, tampoco se
    pide (B-05-021): no hay cómo saber si este proveedor lo tiene. Marca el
    renglón y devuelve si hubo alguno.
    """
    from apps.restock.servicios import proveedor_de

    hubo = False
    for renglon in renglones:
        producto = renglon.cleaned_data.get("producto_resuelto")
        if producto is None:
            continue
        producto = producto.especifico
        lo_trae = (
            proveedor_de(producto)
            if hasattr(producto, "editorial_id")
            else (producto.proveedor if producto.proveedor_id else None)
        )
        if lo_trae is None:
            renglon.add_error(
                "producto",
                f"No se sabe qué proveedor trae «{producto}». Asignale el proveedor en su "
                "ficha antes de pedirlo.",
            )
            hubo = True
        elif lo_trae != proveedor:
            renglon.add_error(
                "producto",
                f"«{producto}» lo trae {lo_trae.razon_social}, no {proveedor.razon_social}. "
                "Pedíselo a ese proveedor, o corregí el proveedor del producto.",
            )
            hubo = True
    return hubo
