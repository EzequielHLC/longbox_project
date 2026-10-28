"""Pedidos a proveedores: lo que viene en camino y su llegada (plan 00 del circuito).

Sólo el Administrador. La llegada va en dos tiempos, como «Pre-ventas por
llegar»: se carga lo que llegó de verdad, el sistema muestra lo que va a pasar
—cuántas reservas cubre, cuánto queda a la venta— y recién al confirmar se
registra. Volver sin confirmar no deja nada.
"""

import datetime

from django import forms
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Prefetch, Q
from django.forms import formset_factory
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View

from apps.accounts.models import Usuario
from apps.catalog import isbn as isbn_util
from apps.catalog.models import Producto
from apps.core.mixins import RolRequeridoMixin
from apps.suppliers import llegadas
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
            pedidos = pedidos.filter(estado=PedidoProveedor.ABIERTO).order_by(
                "fecha_estimada", "creado_en"
            )
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
                        estado__in=LineaPedidoProveedor.ABIERTAS
                    )
                ),
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
        pedido = get_object_or_404(PedidoProveedor.objects.select_related("proveedor"), pk=pk)
        return render(
            request,
            "suppliers/pedido_detalle.html",
            {"pedido": pedido, "filas": _filas(pedido)},
        )


# ---------------------------------------------------------------------------
# La llegada, en dos tiempos
# ---------------------------------------------------------------------------


class LlegadaView(PedidosMixin, View):
    def post(self, request, pk):
        pedido = get_object_or_404(PedidoProveedor, pk=pk)
        abiertas = {
            linea.pk: linea
            for linea in pedido.lineas.select_related("producto").filter(
                estado__in=LineaPedidoProveedor.ABIERTAS
            )
        }
        cantidades = {}
        for pk_linea in abiertas:
            valor = request.POST.get(f"llegaron_{pk_linea}", "")
            if valor.strip() and _entero(valor) is None:
                messages.error(request, "Las unidades tienen que ser números enteros, sin signo.")
                return redirect("suppliers:pedido_detalle", pk=pedido.pk)
            cantidades[pk_linea] = _entero(valor) or 0

        if not any(cantidades.values()):
            messages.error(request, "Indicá cuántas unidades llegaron de al menos un producto.")
            return redirect("suppliers:pedido_detalle", pk=pedido.pk)

        if "confirmar" not in request.POST:
            return render(
                request,
                "suppliers/pedido_llegada.html",
                {"pedido": pedido, "filas": _previa(abiertas, cantidades)},
            )
        try:
            resumen = llegadas.registrar_llegada(
                pedido,
                cantidades,
                request.user,
                origen=request.build_absolute_uri("/").rstrip("/"),
            )
        except llegadas.OperacionRechazada as rechazo:
            messages.error(request, str(rechazo))
            return redirect("suppliers:pedido_detalle", pk=pedido.pk)
        messages.success(
            request, f"Se registró la llegada de {resumen.unidades} unidad(es) de {pedido}."
        )
        return redirect("suppliers:pedido_detalle", pk=pedido.pk)


def _previa(abiertas, cantidades):
    """Lo que va a pasar con cada línea, sin tocar nada."""
    filas = []
    for pk, unidades in cantidades.items():
        if not unidades:
            continue
        linea = abiertas[pk]
        producto = linea.producto
        reservado = llegadas.reservado(producto) if producto.estado == Producto.PRE_VENTA else 0
        cubre = min(unidades, reservado)
        filas.append(
            {
                "linea": linea,
                "producto": producto,
                "unidades": unidades,
                "cubre": cubre,
                "a_la_venta": unidades - cubre,
                "quedan_pendientes": max(
                    0, linea.cantidad_pedida - linea.cantidad_recibida - unidades
                ),
                "de_mas": max(0, linea.cantidad_recibida + unidades - linea.cantidad_pedida),
            }
        )
    return filas


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


def buscar_producto(texto):
    """Un producto por su código interno o su ISBN, o `None`."""
    texto = (texto or "").strip()
    if not texto:
        return None
    isbn = isbn_util.normalizar(texto)
    filtro = Q(codigo__iexact=texto)
    if isbn:
        filtro |= Q(productoeditorial__isbn=isbn)
    return Producto.objects.filter(filtro).exclude(estado=Producto.DESCATALOGADO).first()


class PedidoNuevoForm(forms.Form):
    proveedor = forms.ModelChoiceField(
        label="Proveedor",
        queryset=Proveedor.objects.activos().exclude(correo_comercial="").order_by("razon_social"),
        empty_label="Elegí el proveedor",
    )
    fecha_estimada = forms.DateField(
        label="Llegada estimada",
        required=False,
        widget=forms.DateInput(attrs={"type": "date"}),
        help_text="Opcional. Lo que está agotado se ofrece en pre-venta con esta fecha.",
    )

    def clean_fecha_estimada(self):
        fecha = self.cleaned_data.get("fecha_estimada")
        if fecha and fecha < datetime.date.today():
            raise forms.ValidationError("La llegada estimada no puede ser una fecha pasada.")
        return fecha


class RenglonForm(forms.Form):
    producto = forms.CharField(
        label="Código o ISBN",
        required=False,
        max_length=30,
        widget=forms.TextInput(
            attrs={"placeholder": "E-003896 o 978-987-…", "autocomplete": "off"}
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
            self.add_error("producto", "Indicá el código o el ISBN.")
        elif (producto := buscar_producto(texto)) is None:
            self.add_error("producto", f"No hay un producto con el código o ISBN «{texto}».")
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
            request, "suppliers/pedido_nuevo.html", {"form": form, "renglones": renglones}
        )
