"""Utilidades compartidas por los tests del alta editorial.

Un formset de Django viaja en el POST con un prefijo por ítem
(`form-0-titulo`, `form-1-titulo`, …) y con un formulario de gestión que dice
cuántos hay. Armar eso a mano en cada test escondería lo que el test quiere
probar detrás de veinte líneas de diccionario.
"""

from django.urls import reverse

URL_NACIONAL = reverse("catalog:lote_nacional")
URL_IMPORTADO = reverse("catalog:lote_importado")
URL_INVENTARIO = reverse("catalog:producto_lista")
URL_PARAMETROS = reverse("catalog:parametros")


def url_ficha(producto):
    return reverse("catalog:producto_detalle", args=[producto.pk])


def item(titulo="Akira", volumen=1, **campos):
    """Un ítem del lote. Solo título y volumen son obligatorios siempre."""
    datos = {"titulo": titulo, "volumen": str(volumen)}
    datos.update({nombre: "" if valor is None else str(valor) for nombre, valor in campos.items()})
    return datos


def payload(items, **cabecera):
    """El POST completo: formulario de gestión, cabecera e ítems con prefijo."""
    datos = {
        "form-TOTAL_FORMS": str(len(items)),
        "form-INITIAL_FORMS": "0",
        "form-MIN_NUM_FORMS": "0",
        "form-MAX_NUM_FORMS": "1000",
    }
    datos.update(
        {nombre: "" if valor is None else str(valor) for nombre, valor in cabecera.items()}
    )
    for numero, campos in enumerate(items):
        for nombre, valor in campos.items():
            datos[f"form-{numero}-{nombre}"] = valor
    return datos


def lote_nacional(items, referencia, **cabecera):
    """El POST de un lote nacional que hereda la combinación de `referencia`."""
    datos = {
        "editorial": referencia.editorial.pk,
        "tipo": referencia.tipo.pk,
        "formato": referencia.formato.pk,
    }
    datos.update(cabecera)
    return payload(items, **datos)
