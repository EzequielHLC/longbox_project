"""Revisión integral, R-11: todo selector de fecha se pinta en formato ISO.

Con `LANGUAGE_CODE = "es-ar"`, un `DateInput(type="date")` sin `format` se pinta
como `01/11/2026`, y el navegador sólo acepta `2026-11-01`: lo descarta y el campo
aparece vacío. Al editar una oferta había que volver a cargar las dos fechas, y en
Reportes se perdía el período por omisión.

La prueba recorre los formularios de todas las apps, no una lista: un formulario
nuevo con el mismo descuido la hace fallar sin que nadie se acuerde de sumarlo.
"""

import importlib
import pkgutil
from datetime import date

from django import forms
from django.utils import translation

import apps

ISO = "%Y-%m-%d"


def _todos_los_formularios():
    for modulo in pkgutil.walk_packages(apps.__path__, "apps."):
        hoja = modulo.name.rsplit(".", 1)[-1]
        if ".tests" in modulo.name or ".migrations" in modulo.name:
            continue
        if hoja.startswith(("forms", "views")):
            importlib.import_module(modulo.name)
    vistos, pendientes = set(), [forms.BaseForm]
    while pendientes:
        clase = pendientes.pop()
        for hija in clase.__subclasses__():
            if hija not in vistos:
                vistos.add(hija)
                pendientes.append(hija)
    return [c for c in vistos if c.__module__.startswith("apps.")]


def _selectores_de_fecha(clase):
    for nombre, campo in getattr(clase, "base_fields", {}).items():
        widget = campo.widget
        if isinstance(widget, forms.DateInput) and widget.input_type == "date":
            yield nombre, widget
        elif getattr(widget, "attrs", {}).get("type") == "date":
            yield nombre, widget


def test_todo_selector_de_fecha_declara_el_formato_iso():
    sin_formato = [
        f"{clase.__module__}.{clase.__name__}.{nombre}"
        for clase in _todos_los_formularios()
        for nombre, widget in _selectores_de_fecha(clase)
        if getattr(widget, "format", None) != ISO
    ]

    assert sin_formato == []


def test_la_fecha_se_pinta_como_la_lee_el_navegador():
    from apps.catalog.forms_ofertas import OfertaForm

    with translation.override("es-ar"):
        html = str(OfertaForm(initial={"fecha_inicio": date(2026, 11, 1)})["fecha_inicio"])

    assert 'value="2026-11-01"' in html
