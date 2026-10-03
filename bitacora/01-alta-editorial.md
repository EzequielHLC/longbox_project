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
**Estado:** Resuelta — sin enmienda al documento; corregido el código el 2026-09-22

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
**Estado:** Resuelta — con enmienda pendiente al documento, decidida el 2026-09-22

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

---

## Resoluciones

> Lo que el responsable decidió sobre cada entrada, con la fecha y con qué se hizo en
> consecuencia. **La entrada original no se toca**: sólo se le marca el estado. Una enmienda
> declarada «pendiente» manda sobre el texto que hoy está volcado en `.contexto-ia/`, que no se
> edita a mano y se actualiza recién cuando el documento de análisis cambie.

### R-01-001 · Resolución de B-01-001

**Fecha:** 2026-09-22 · **Enmienda al documento:** ninguna

**Qué se decidió.**
Los tres campos —`demorado`, `fecha_estimada`, `nota_demora`— pertenecen a `CU-ALT-DEM`. La ficha
ya lo dice sin ambigüedad y no hay nada que enmendar: el que estaba mal era el comentario del
formulario, que quedó diciendo `CU-ALT-CAN` al migrar la numeración.

La restricción del formulario de edición se deriva de `CU-ALT-DEM`: es ese caso de uso el que
escribe esos campos, y por eso `CU-CAT-EDI` no los ofrece. `CU-ALT-CAN` no los toca.

**Qué se hizo.**
`apps/catalog/forms.py`, docstring de `ProductoEditorialForm`: la referencia pasa de `CU-ALT-CAN`
a `CU-ALT-DEM`. El comportamiento no cambia —los campos siguen sin ofrecerse en la edición— y
ahora el formulario y el modelo dicen lo mismo.

---

### R-01-002 · Resolución de B-01-002

**Fecha:** 2026-09-22 · **Enmienda al documento:** pendiente

**Qué se decidió.**
La carga de correos desde archivos `.eml` es una **herramienta de operación**, no un caso de uso.
No necesita ficha, no necesita contrato propio y no es la vía manual permanente de un flujo
especificado: es una utilidad de consola para operar el sistema.

`CO-016 ejecutarCicloMonitoreoCasilla` **sigue pendiente**. La decisión no lo cubre ni lo
reemplaza: el ciclo automático es lo que la especificación declara y lo que hay que construir. Lo
que queda resuelto es que los comandos de consola que hoy ocupan su lugar no son deuda de
especificación.

**Enmienda pendiente.**
Un **límite nuevo del sistema** que declare fuera del modelo de casos de uso a las tareas de
consola:

- el respaldo de la base (`respaldar_base`);
- la sincronización de los catálogos geográficos y de países (`sincronizar_georef`,
  `sincronizar_paises`);
- la carga de correos desde `.eml` (`ingerir_correos`, `extraer_novedades`);
- el alta de la primera cuenta Administrador en una instalación nueva.

Mientras esa enmienda no llegue a `.contexto-ia/`, esta resolución manda sobre el texto volcado.
Con ella, las cuatro filas correspondientes salen de «Código sin contrato» en `docs/DEUDA.md`: no
son contratos que falten escribir sino comportamiento deliberadamente fuera del alcance funcional.

**Qué se hizo.**
Nada en el código de la ingesta. La cuarta tarea de la lista —el alta del primer Administrador— se
construye en el bloque 2 como consecuencia del retiro del admin de Django, y queda registrada en
`bitacora/13-gestion-de-usuarios.md`.

---

### B-01-003 · Un producto admite imágenes adicionales además de su portada

**Tipo:** Agregado · **Fecha:** 2026-10-02 · **Alcance:** `Producto`, `CU-CAT-ALT`, `CU-CAT-EDI`, `CU-CAT-INV`, RNF-05
**Estado:** Abierta — pedido explícito del responsable el 2026-10-02

**Qué apareció.**
El responsable pidió poder subir más de una imagen por producto.

**Qué dice la especificación.**
> «imagen : archivo «marcador "imagen pendiente" si falta»» (`MODELO_DE_DOMINIO.md`, `Producto`)

RNF-05 habla de «portadas, imágenes de producto» en plural, sin declarar cuántas.

**Qué se hizo.**
La portada sigue siendo **la** imagen del producto, con su marcador «imagen pendiente»: ningún
contrato cambia. Se suma una galería de hasta 8 imágenes adicionales, que se cargan en el alta no
editorial y en la edición, se pueden quitar de a una, se procesan con RNF-05 (WebP, 800 px) y se
ven en la ficha. Agregarlas o quitarlas queda en el historial del producto. La carga de lotes no
las ofrece.

**Qué habría que cambiar.**
`MODELO_DE_DOMINIO.md`, Área 3: agregar `ImagenProducto` (imagen, posición) con `Producto` 1 —
0..8. `CO-030`, parámetros: «imágenes adicionales?».

---

### B-01-004 · El historial del producto incluye su alta por lote y todo lo que la edición cambia

**Tipo:** Agregado · **Fecha:** 2026-10-02 · **Alcance:** `CU-CAT-INV` paso 6, `CO-030`, `CO-163`
**Estado:** Abierta

**Qué apareció.**
El historial de un tomo cargado por lote empezaba en su primera modificación: el alta se audita
sobre el lote, una entrada por lote. Además, una edición que sólo cambiaba etiquetas, sinopsis,
portada o fecha de llegada se guardaba pero no dejaba entrada, y la pantalla decía «No había
cambios para guardar».

**Qué dice la especificación.**
> «Se creó una entrada en el registro de auditoría con acción «Modificación de producto», el actor y
> el momento de la operación» (`CO-030`, Postcondiciones)

Sobre qué campos se registran y qué muestra el historial de la ficha: `Nada`.

**Qué se hizo.**
La ficha suma al historial la entrada del alta del lote del que salió el producto. La edición
registra también etiquetas, sinopsis (por su largo, comparando el texto entero), portada, fecha de
llegada e imágenes adicionales. Los valores del detalle van entre comillas angulares, como el
resto del log.

**Qué habría que cambiar.**
`CU-CAT-INV` paso 6: el historial de la ficha incluye el alta del lote de origen.

---

### B-01-005 · Los desplegables de formato muestran las medidas

**Tipo:** Agregado · **Fecha:** 2026-10-02 · **Alcance:** `CU-ALT-NAC`, `CU-ALT-IMP`, `CU-CAT-EDI`, `CU-ALT-REV`, `CU-PVP-TBA`, `CU-CFG-TPM`
**Estado:** Abierta — pedido del responsable el 2026-10-02

**Qué apareció.**
Elegir un formato por su nombre obliga a recordar qué tamaño era.

**Qué dice la especificación.**
`Nada.`

**Qué se hizo.**
Todo desplegable o lista de formatos los ofrece como «B6 · 12,8 × 18,2 cm» cuando el formato tiene
medidas cargadas.

**Qué habría que cambiar.**
Nada.
