"""Qué cambió entre dos versiones de algo, para el registro de auditoría.

Estaba escrito dos veces —una en `accounts` para CU-USR-MOD y otra en `suppliers` para
CU-PRV-EDI— y la edición de producto de CU-CAT-EDI iba a ser la tercera. Las tres necesitan
exactamente lo mismo: comparar campo por campo y dejar el par anterior→nuevo en
el log.

**El par completo, no solo el estado final.** Un registro que dice "rol:
administrador" no permite reconstruir nada; uno que dice "rol: 'cajero' →
'administrador'" sí. Es la diferencia entre una bitácora y una foto.

Qué campos se auditan lo decide cada módulo, porque depende del CU: se pasa un
diccionario `{etiqueta: cómo leerla}` y no se deduce del modelo. Deducirlo
metería en el log los campos técnicos —marcas de tiempo, banderas internas— y
dejaría afuera lo derivado, como el nombre completo, que no es un campo.
"""


def entre(anterior, nuevo, campos):
    """`{etiqueta: (valor_anterior, valor_nuevo)}` de lo que cambió.

    `campos` es `{etiqueta: función que lee el valor}`. Se comparan los valores
    ya leídos y no los atributos crudos, para que el log muestre "Administrador"
    y no "administrador".
    """
    return {
        etiqueta: (leer(anterior), leer(nuevo))
        for etiqueta, leer in campos.items()
        if leer(anterior) != leer(nuevo)
    }


def describir(cambios):
    """El texto que va al `detalle` del registro."""
    return "; ".join(
        f"{etiqueta}: '{anterior}' → '{nuevo}'" for etiqueta, (anterior, nuevo) in cambios.items()
    )
