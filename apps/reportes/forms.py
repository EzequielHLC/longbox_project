"""Los parámetros de CU-REP-GEN paso 3, con E1 validado en el servidor."""

from django import forms
from django.utils import timezone

from apps.catalog.models import Tipo
from apps.puntos.models import MovimientoPuntos
from apps.reportes import servicios

MENSAJE_RANGO_INVERTIDO = "La fecha de inicio no puede ser posterior a la de fin."
MENSAJE_FUTURO = "El rango no puede incluir fechas futuras."


class ReporteForm(forms.Form):
    tipo = forms.ChoiceField(label="Reporte", choices=servicios.TIPOS)
    desde = forms.DateField(label="Desde", widget=forms.DateInput(attrs={"type": "date"}))
    hasta = forms.DateField(label="Hasta", widget=forms.DateInput(attrs={"type": "date"}))
    canal = forms.ChoiceField(
        label="Canal",
        required=False,
        choices=[("", "Todos"), *servicios.CANALES.items()],
        help_text="Sólo en Ventas totales.",
    )
    categoria = forms.ModelChoiceField(
        label="Categoría",
        required=False,
        queryset=Tipo.objects.order_by("nombre"),
        empty_label="Todas",
        help_text="En Productos más vendidos y Solicitudes de reposición.",
    )
    tipo_movimiento = forms.ChoiceField(
        label="Tipo de movimiento",
        required=False,
        choices=[("", "Todos"), *MovimientoPuntos.TIPO_CHOICES],
        help_text="Sólo en Movimientos de puntos.",
    )

    def clean(self):
        datos = super().clean()
        desde, hasta = datos.get("desde"), datos.get("hasta")
        hoy = timezone.localdate()
        if desde and hasta and desde > hasta:
            self.add_error("desde", MENSAJE_RANGO_INVERTIDO)
        for campo in ("desde", "hasta"):
            if datos.get(campo) and datos[campo] > hoy:
                self.add_error(campo, MENSAJE_FUTURO)
        return datos

    def parametros(self):
        datos = self.cleaned_data
        return {
            "canal": datos.get("canal") or "",
            "categoria": datos.get("categoria"),
            "tipo_movimiento": datos.get("tipo_movimiento") or "",
        }
