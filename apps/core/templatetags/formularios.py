"""Filtros de plantilla para renderizar formularios."""

from django import template

register = template.Library()


@register.filter
def con_estado_de_error(campo):
    """Dibuja el campo marcando su error para las tecnologías de asistencia.

    Un borde rojo no existe para quien no ve la pantalla. `aria-invalid` le
    dice al lector que el campo está mal, y `aria-describedby` lo enlaza con
    el texto del error, que es el que explica por qué; sin eso, el lector
    anuncia el campo y se queda callado sobre el problema.

    Va como filtro y no como atributo del widget en el formulario porque los
    errores recién se conocen después de validar, y los widgets se arman al
    construir el formulario.
    """
    if not campo.errors:
        return campo

    ids = " ".join(f"{campo.auto_id}_error_{numero}" for numero in range(1, len(campo.errors) + 1))
    return campo.as_widget(attrs={"aria-invalid": "true", "aria-describedby": ids})
