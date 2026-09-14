# Bitácora — `01` Alta Editorial

> Registro de lo que se decidió construyendo este módulo. **Se anexa, no se reescribe.**
> Una entrada resuelta se marca; no se borra.
>
> Este archivo es el material que el responsable lee para decidir qué se enmienda en el documento
> de análisis. Escribí para alguien que conoce el dominio y no tiene el código a la vista.

---

## Entradas

### B-01-001 · A qué caso de uso pertenecen los campos de demora del formulario de edición

**Tipo:** Agregado · **Fecha:** 2026-09-14 · **Alcance:** `CU-ALT-DEM`, `CU-ALT-CAN`, `CU-CAT-EDI`
**Estado:** Abierta

**Qué apareció.**
El formulario de edición de un tomo (`ProductoEditorialForm`) enumera los campos que
deliberadamente **no** ofrece, y de tres de ellos —`demorado`, `fecha_estimada`, `nota_demora`—
dice que pertenecen al caso de uso de cancelación. En el modelo, esos mismos tres campos están
comentados como pertenecientes al caso de uso de demora, y son los que alimentan el indicador
«Demorado» del inventario. Los dos comentarios señalan casos de uso distintos para los mismos tres
campos, y los dos casos de uso están igualmente bloqueados por Pedidos, así que la contradicción
no tuvo consecuencia práctica hasta ahora.

La contradicción venía del esquema anterior de numeración y sobrevivió a la migración de códigos
del 2026-09-14, que tradujo cada referencia por su número y no la corrigió: el formulario quedó
diciendo `CU-ALT-CAN` y el modelo `CU-ALT-DEM`.

**Qué dice la especificación.**
> `CU-ALT-DEM` — «El sistema asigna el indicador "Demorado" al producto, transiciona los pedidos
> activos asociados a "Esperando Artículo Demorado" […]»

> `CU-ALT-CAN` — «Ante la cancelación definitiva de un título por parte de la editorial, el
> Administrador ejecuta la cancelación en lote de todas las reservas activas del producto.»

La ficha atribuye el indicador a `CU-ALT-DEM` sin ambigüedad. Lo que la especificación **no** dice
es cuál de los dos casos de uso es el que debe impedir que esos campos se editen desde la pantalla
de edición de producto, que es la afirmación que el formulario hace.

**Qué se hizo.**
Nada todavía. La migración de códigos preservó lo que cada comentario decía en vez de arreglarlo,
para que la discrepancia quedara visible en lugar de desaparecer dentro de una decisión tomada al
pasar. El comportamiento del sistema no cambió: los tres campos no se ofrecen en la edición, y no
hay pantalla que los escriba.

**Qué habría que cambiar.**
Confirmar que los tres campos pertenecen a `CU-ALT-DEM` y que la restricción del formulario de
edición se deriva de ese caso de uso. Con eso resuelto, el comentario de
`apps/catalog/forms.py` se corrige en una línea. Si en cambio la intención era otra —por ejemplo
que la cancelación en lote también los toque— eso sí cambia el alcance de `CU-ALT-CAN` y hay que
decirlo en la ficha.

---

### B-01-002 · La ingesta de correos se dispara a mano; el ciclo automático no existe

**Tipo:** Agregado · **Fecha:** 2026-09-14 · **Alcance:** `CU-ALT-NOV`, `CO-016`
**Estado:** Abierta

**Qué apareció.**
El pipeline de novedades está construido de la cola en adelante: un correo que entra a
`CorreoProveedor` se aprueba, se extrae con el modelo de lenguaje y genera borradores. Lo que no
existe es el paso previo: nada lee la casilla. Los correos entran por dos comandos de gestión
—`manage.py ingerir_correos` y `manage.py extraer_novedades`— que una persona ejecuta.

Los dos comandos declaran en su docstring que no son un andamio descartable: cuando exista el
ciclo automático, va a invocar el mismo código.

**Qué dice la especificación.**
> `CO-016 ejecutarCicloMonitoreoCasilla` — operación disparada por el Temporizador del Sistema.

La especificación declara el ciclo. No dice nada sobre una vía manual de ingesta, ni sobre si esa
vía debe seguir existiendo una vez que el ciclo funcione.

**Qué se hizo.**
La ingesta quedó disponible como operación manual del Administrador sobre archivos `.eml`. El
resto del flujo —aprobación, extracción, generación de borradores— es idéntico venga el correo de
donde venga, así que el ciclo automático puede enchufarse sin tocar nada de lo que ya existe.

**Qué habría que cambiar.**
Decidir si la ingesta manual es permanente o transitoria. Si es permanente, `CU-ALT-NOV` necesita
declararla como flujo alternativo con el Administrador como actor primario, y probablemente un
contrato propio: hoy es una operación que modifica el estado del sistema y que ningún contrato
declara. Si es transitoria, alcanza con dejarlo dicho.
