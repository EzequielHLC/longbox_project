"""Formularios del ciclo de la pre-venta (plan 01)."""

from django import forms
from django.utils import timezone


class DemoraForm(forms.Form):
    """`CU-ALT-DEM` paso 2: los dos campos son opcionales (A1)."""

    fecha_estimada = forms.DateField(
        label="Nueva fecha estimada",
        required=False,
        widget=forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
    )
    nota = forms.CharField(
        label="Nota interna",
        required=False,
        max_length=1000,
        widget=forms.Textarea(attrs={"rows": 3}),
    )

    def clean_fecha_estimada(self):
        fecha = self.cleaned_data.get("fecha_estimada")
        # E1: posterior al día de hoy.
        if fecha and fecha <= timezone.localdate():
            raise forms.ValidationError("La fecha estimada debe ser posterior a hoy.")
        return fecha
