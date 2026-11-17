"""Qué cambió entre dos versiones de algo, para el registro de auditoría.

Estaba escrito dos veces —una en `accounts` para CU-USR-MOD y otra en `suppliers` para
CU-PRV-EDI— y la edición de producto de CU-CAT-EDI iba a ser la tercera. Las tres necesitan
exactamente lo mismo: comparar campo por campo y dejar el par anterior→nuevo en
el log.

**El par completo, no solo el estado final.** Un registro que dice "rol:
administrador" no permite reconstruir nada; uno que dice "rol: «cajero» →
«administrador»" sí. Es la diferencia entre una bitácora y una foto.

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
    """El texto que va al `detalle` del registro.

    Entre comillas angulares, como el resto del log: las comillas simples de
    Python se leían como parte del valor.
    """
    return "; ".join(
        f"{etiqueta}: «{anterior}» → «{nuevo}»" for etiqueta, (anterior, nuevo) in cambios.items()
    )


# ---------------------------------------------------------------------------
# La forma estructurada del registro (plan 16, segunda parte)
# ---------------------------------------------------------------------------
#
# La cátedra pide que toda modificación deje dicho qué se cambió y cómo estaba
# antes, y `CO-206` lo presenta por separado. Por eso cada entrada guarda,
# además del texto, la lista `[{campo, antes, despues}]`: el texto se arma de
# la lista y no al revés, así ningún sitio puede escribir uno sin el otro.


def imagen(campo, antes, despues):
    """Un cambio cuyo valor es un archivo de imagen: se guarda su nombre en `media/`.

    El archivo anterior **se conserva** (B-16-005): sin él, «cómo estaba antes»
    sería sólo un nombre que ya no apunta a nada.
    """
    return {"campo": campo, "antes": antes or "", "despues": despues or "", "imagen": True}


def _texto(valor):
    return "" if valor is None else str(valor)


def a_lista(cambios):
    """Normaliza lo que cambió al formato del registro.

    Acepta el diccionario de `entre` (`{etiqueta: (antes, después)}`), una lista
    de tuplas `(campo, antes, después)` o de diccionarios ya armados con
    `imagen`. Los valores se guardan como texto: el log dice lo que se veía, y
    un `Decimal` o una fecha no son JSON.
    """
    if not cambios:
        return []
    if isinstance(cambios, dict):
        cambios = [(campo, antes, despues) for campo, (antes, despues) in cambios.items()]
    lista = []
    for cambio in cambios:
        if isinstance(cambio, dict):
            item = dict(cambio)
        else:
            campo, antes, despues = cambio
            item = {"campo": campo, "antes": antes, "despues": despues}
        item["campo"] = _texto(item["campo"])
        item["antes"] = _texto(item["antes"])
        item["despues"] = _texto(item["despues"])
        lista.append(item)
    return lista


def describir_lista(lista):
    """El texto del `detalle` a partir de la lista: el mismo formato que `describir`."""
    partes = []
    for item in lista:
        if item.get("imagen"):
            if item["antes"] and item["despues"]:
                partes.append(f"{item['campo']}: imagen reemplazada")
            elif item["despues"]:
                partes.append(f"{item['campo']}: imagen cargada")
            else:
                partes.append(f"{item['campo']}: imagen quitada")
        else:
            partes.append(f"{item['campo']}: «{item['antes']}» → «{item['despues']}»")
    return "; ".join(partes)
