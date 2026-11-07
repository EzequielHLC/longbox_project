"""«Por llegar»: la llegada de mercadería en una sola pantalla (B-05-017, `CO-232`).

Sólo el Administrador. Dos tiempos, como siempre: se carga lo que llegó en un
grupo, la revisión dice qué va a pasar con cada producto, y recién al confirmar
se registra. Volver sin confirmar no deja nada.
"""

from django.contrib import messages
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views import View

from apps.accounts.models import Usuario
from apps.core.mixins import RolRequeridoMixin
from apps.pedidos import calendario
from apps.suppliers import recepcion


class LlegadasMixin(RolRequeridoMixin):
    roles_permitidos = (Usuario.ADMINISTRADOR,)


def _plural(cantidad, singular, plural):
    return f"{cantidad} {singular if cantidad == 1 else plural}"


class PorLlegarView(LlegadasMixin, View):
    """Todo lo que se espera, por proveedor y fecha, con el calendario del mes."""

    def get(self, request):
        grupos = recepcion.por_llegar()
        mes = calendario.mes_de(calendario.mes_pedido(request.GET.get("mes")), grupos)
        # Cambiar de mes sin recargar pide sólo el calendario.
        plantilla = (
            "pedidos/_calendario_preventas.html"
            if request.GET.get("parcial") == "calendario"
            else "suppliers/por_llegar.html"
        )
        return render(
            request,
            plantilla,
            {
                "grupos": grupos,
                "mes": mes,
                "dias_de_la_semana": calendario.DIAS_DE_LA_SEMANA,
                "resumen": recepcion.resumen(grupos),
                "sin_enviar": recepcion.pedidos_sin_enviar(),
            },
        )


class RevisarLlegadaView(LlegadasMixin, View):
    """`CO-232`. El primer envío muestra qué va a pasar; el segundo lo confirma."""

    def post(self, request):
        volver = reverse("suppliers:por_llegar")
        try:
            lineas, productos = recepcion.leer(request.POST)
            if "confirmar" not in request.POST:
                previas = recepcion.previsualizar(lineas, productos)
                if not any(p.unidades or p.se_demora for p in previas):
                    raise recepcion.OperacionRechazada(
                        "Indicá cuántas unidades llegaron de al menos un producto."
                    )
                return render(
                    request,
                    "suppliers/llegada_revisar.html",
                    {
                        "previas": previas,
                        "filas": request.POST.getlist("fila"),
                        "valores": {
                            campo: request.POST.get(f"llegaron_{campo}", "")
                            for campo in request.POST.getlist("fila")
                        },
                        "grupo": request.POST.get("grupo", ""),
                    },
                )
            resultado = recepcion.confirmar(
                lineas,
                productos,
                request.user,
                vistas=recepcion.leer_vistas(request.POST, lineas),
                origen=request.build_absolute_uri("/").rstrip("/"),
            )
        except recepcion.OperacionRechazada as rechazo:
            messages.error(request, str(rechazo))
            return redirect(volver)

        ingreso = resultado.ingreso
        partes = []
        if resultado.unidades:
            partes.append(_plural(resultado.unidades, "unidad recibida", "unidades recibidas"))
        if ingreso.activados:
            partes.append(
                _plural(len(ingreso.activados), "pre-venta a la venta", "pre-ventas a la venta")
            )
        if ingreso.parciales:
            partes.append(_plural(len(ingreso.parciales), "ingreso parcial", "ingresos parciales"))
        if ingreso.demorados:
            partes.append(
                _plural(len(ingreso.demorados), "pre-venta demorada", "pre-ventas demoradas")
            )
        if ingreso.pedidos:
            partes.append(
                _plural(
                    len(ingreso.pedidos),
                    "pedido de cliente actualizado",
                    "pedidos de clientes actualizados",
                )
            )
        if partes:
            messages.success(request, "Llegada registrada: " + ", ".join(partes) + ".")
        errores = resultado.errores + ingreso.errores
        if errores:
            messages.error(
                request,
                "Esto no se pudo registrar y quedó como estaba: " + "; ".join(errores) + ".",
            )
        if not partes and not errores:
            messages.info(request, "No cambió nada: lo que quedó en cero sigue esperando.")
        return redirect(volver)
