> **Tipo: Normativo** una vez aprobado. Antes de la aprobación es una propuesta.
> Se escribe **antes** de programar y **no se reescribe** después: si algo cambió durante la
> construcción, eso va a la bitácora del módulo, no acá.

# Plan — `00` La respuesta del proveedor, simple · El tomo cancelado que vuelve

**Estado del plan:** Propuesto · **Fecha:** 2026-10-28

Dos pedidos del responsable, del 2026-10-28:

1. **La respuesta del proveedor es confusa** y la pantalla está demasiado cargada. Pide un análisis
   del flujo, de sus fallos posibles, y una solución más robusta. El flujo es el del [plan
   00](00-respuesta-del-proveedor.md), B-05-013 y B-19-019.
2. **Un tomo «Cancelado por editorial» que la editorial vuelve a anunciar** no se puede traer: la
   protección de duplicados lo choca contra el cancelado.

---

## Parte A · La respuesta del proveedor

### A.1 Qué hay hoy

La respuesta se anota en un formulario (`suppliers/_respuesta_pedido.html`) que aparece **en dos
pantallas**: la ficha del pedido y la de la propuesta. Hay una tabla con un desplegable por línea
(Sin respuesta / Confirmada / Con otra cantidad / No la puede abastecer), un número por línea, una
fecha, un motivo y tres botones. La lógica está en `suppliers/respuestas.py` y la usa también Telegram.

### A.2 Problemas encontrados

**De pantalla:**

| # | Problema | Dónde |
| --- | --- | --- |
| P1 | **Los mismos productos aparecen dos veces**, en dos tablas con dos formularios: «Productos» (la llegada) y «Respuesta de…». En la propuesta, **tres veces**: la tabla de pedidos, un formulario entero por cada pedido y los grupos de productos | `pedido_detalle.html`, `propuesta_detalle.html` |
| P2 | **El número de cada línea parece editable pero se ignora** salvo que el desplegable diga «Con otra cantidad». Si se cambia el número y se deja «Confirmada», se pierde sin aviso | `_respuesta_pedido.html`, `RespuestaView` |
| P3 | **Un solo motivo para todo el pedido**, lejos de las líneas. Dos productos no disponibles por razones distintas no se pueden anotar; un motivo escrito sin marcar nada se pierde | ídem |
| P4 | **Tres botones con alcances distintos en un mismo formulario**: «Guardar» lee los desplegables y la fecha; «Confirmó todo» ignora los desplegables; «No puede abastecer nada» cierra el pedido entero **sin pedir confirmación** | ídem |
| P5 | Volver a guardar **vuelve a anotar las líneas ya respondidas**: se pisa la hora de respuesta y la auditoría repite «confirmada» por cada guardado | `RespuestaView` manda todos los desplegables |
| P6 | «No disponible» cierra la línea **sin vuelta atrás** y sin una advertencia que lo diga | ídem |
| P7 | Las advertencias (reservas sin cubrir, demora) **mandan a otra pantalla** sin enlace al producto | `RespuestaView` |

**De lógica:**

| # | Fallo | Qué pasa |
| --- | --- | --- |
| F1 | **Una llegada no cuenta como respuesta.** Si llega mercadería de una línea que nadie marcó, la línea queda «parcial» y «sin respuesta» | A los 3 días sale el **recordatorio de que el proveedor no respondió**, aunque ya mandó mercadería; la propuesta **sigue esperando** |
| F2 | **Se puede confirmar más de lo pedido** («Con otra cantidad» acepta hasta 9999) | Sube el cupo de la pre-venta por encima de lo pedido y la tienda acepta reservas que nadie pidió |
| F3 | **Un pedido «Sin enviar» dentro de una propuesta** la deja esperando una respuesta que no puede llegar, porque el proveedor nunca recibió el correo | La propuesta queda en «Esperando respuesta» sin decir que en realidad espera un reintento |
| F4 | **Sin respuesta nunca, la propuesta espera para siempre.** El recordatorio sale una sola vez, a los 3 días | No bloquea el restock (sólo bloquea una «Pendiente»), pero la lista no dice hace cuánto espera |
| F5 | La fecha **no se puede borrar** una vez puesta, y viaja en el mismo envío que las líneas | Un error de tipeo en la fecha sólo se corrige con otra fecha |

Lo que **funciona bien** y se conserva: el bloqueo de fila del pedido (web y chat a la vez), una sola
función de servicio para web y Telegram, la regla de que menos que lo reservado avisa y no cancela, y la
de que atrasar una pre-venta con reservas es una demora.

### A.3 La propuesta

**Una respuesta, un lugar, una pregunta por vez.**

1. **La ficha del pedido es el único lugar donde se anota.** La propuesta deja de tener formularios:
   su tabla de pedidos gana una columna «Respuesta» con el estado («Esperando respuesta hace 4 días»,
   «Confirmó todo», «Confirmó con cambios», «No puede») y un enlace «Anotar la respuesta» a la ficha.
2. **Una sola tabla de productos** en la ficha del pedido. Cada línea muestra en una columna «Estado»
   lo que se sabe de ella: *Esperando respuesta* · *Confirmada* · *Confirma 3 de 5* · *No disponible:
   motivo* · *Llegaron 2 de 5*. La tabla de la respuesta desaparece.
3. **Arriba, una pregunta con tres respuestas**, como en Telegram, mientras quede algo sin responder:
   **«¿Qué contestó {proveedor}?»** → **Confirmó todo** · **Confirmó con cambios** · **No puede
   abastecer**. Cuando todo tiene respuesta, se achica a una línea: *«Respondió el 28/10: confirmó 4,
   1 no disponible · llega el 15/11 · Cambiar»*.
4. **Cada respuesta abre su diálogo propio** (componente del sistema, no del navegador):
   - **Confirmó todo**: «¿Dijo cuándo llega?» con la fecha, opcional. Un clic.
   - **Confirmó con cambios**: las líneas, cada una con tres opciones en botones segmentados
     (*Tal cual* · *Menos* · *No la tiene*). El número **sólo aparece al elegir «Menos»**, y el
     motivo **sólo al elegir «No la tiene»**, en esa línea. Más la fecha.
   - **No puede abastecer**: el motivo, con los rápidos de siempre, y **qué va a pasar antes de
     confirmar**: «Se cierran 5 líneas sin recibir. 2 pre-ventas pierden cupo: Frieren #9 (3
     reservas)…».
   - **Cambiar la fecha** queda como acción aparte, con «Sin fecha» posible.
5. **La llegada sigue igual**: el botón «Registrar la llegada» lleva a la pantalla en dos tiempos de
   siempre. La tabla ya no tiene campos: sólo informa.

**Reglas que cambian (servicio, valen también para Telegram):**

| # | Regla | Arregla |
| --- | --- | --- |
| R1 | **Lo que llega es una respuesta**: registrar una llegada de una línea sin respuesta la deja «Confirmada» | F1 |
| R2 | **No se confirma más de lo pedido.** Para más unidades, otro pedido | F2 |
| R3 | **Sólo se anota lo que cambió**: una línea con la misma respuesta no se vuelve a registrar | P5 |
| R4 | **El motivo es de cada línea** no disponible | P3 |
| R5 | Una propuesta con un pedido «Sin enviar» lo dice: **«Esperando un reintento de envío»**, con el enlace | F3 |
| R6 | La lista y la ficha de la propuesta muestran **hace cuántos días espera** | F4 |
| R7 | Las advertencias de reservas y demoras **enlazan el producto** en Pre-ventas | P7 |

Telegram ya es simple (tres botones) y se queda como está, con dos cambios: «Confirmó con cambios»
manda el enlace a la ficha, y vale R1 a R4.

---

## Parte B · El tomo cancelado que vuelve

### B.1 Qué dice la especificación

> `CU-ALT-CAN`, comentarios: «La cancelación por editorial que este caso de uso establece es **un
> estado del que no se retorna** […] la reactivación de CU-CAT-REA tampoco lo admite. Moverlo a un
> estado del que sí se retorna borraría la única marca de que ese título no va a llegar nunca.»
>
> Postcondición: «El estado **se conserva en el inventario interno y en el historial de ventas** para
> preservar la integridad del registro histórico.»

Y la detección de duplicados (`CO-006`, notas) compara contra **todo** el catálogo: primero ISBN, si no
la combinación título + volumen + tipo + formato + editorial. En la base son dos restricciones de
unicidad sobre `ProductoEditorial`: `isbn` y `clave_edicion`.

### B.2 El problema

La especificación **no prevé que un título cancelado vuelva**, y en la práctica pasa: una editorial
cancela un tomo y meses después lo reprograma. Hoy el tomo nuevo choca contra el cancelado, por ISBN o
por la combinación, y no hay salida: reactivarlo está prohibido, y borrarlo, como se hizo con Sakamoto
Days #24 el 2026-10-28, **rompe la postcondición del historial** si el cancelado tuvo reservas.

### B.3 Las tres salidas posibles

| | Qué es | A favor | En contra |
| --- | --- | --- | --- |
| **1 · Reanunciar (recomendada)** | El que vuelve es **un producto nuevo, con código nuevo, enlazado al cancelado**. El cancelado queda intacto en el historial | Respeta las dos frases de `CU-ALT-CAN`. Sigue la regla 1 del dominio: la identidad la lleva el código, los datos descriptivos sólo detectan duplicados | Dos fichas para el mismo título (una cancelada, oculta en la tienda) |
| 2 · Reactivar | El cancelado vuelve a Pre-venta | Una sola ficha | **Contradice `CU-ALT-CAN`** y borra la marca. Haría falta enmendar el documento |
| 3 · Borrar | Lo que se hizo con Sakamoto #24 | Simple | **Pierde el historial**. Sólo sirve para datos de prueba sin reservas ni ventas |

### B.4 Cómo funciona la salida 1

- **La edición cancelada libera su identidad.** Al cancelar (`CO-027`), dentro de la misma
  transacción, el producto queda marcado como **edición retirada**. Las dos restricciones de unicidad
  pasan a valer **sólo entre ediciones no retiradas**. La marca va en la misma tabla que el ISBN
  porque una restricción no abarca dos tablas, que es la razón por la que el estado no sirve
  directamente. Una migración marca los cancelados que ya existen.
- **El duplicado contra un cancelado no bloquea: avisa y ofrece.** En el alta, en el lote y en el
  borrador: *«Este tomo fue cancelado por la editorial el 12/09. Si la editorial lo volvió a anunciar,
  se carga como una edición nueva; el cancelado queda en el historial.»* Con un botón «Cargarlo como
  reanunciado».
- **En la ficha del cancelado, «Volver a anunciar»**, que abre el alta con los datos copiados.
- El nuevo guarda **a cuál reanuncia**, y las dos fichas se enlazan: «Reanuncia a E-003889» y
  «Reanunciado como E-004120».
- **Un duplicado contra un producto vivo sigue bloqueando**, como hoy.

---

## 1. Qué cubre

| Qué | Dónde | Operaciones |
| --- | --- | --- |
| Ficha del pedido con una tabla y una pregunta | Caso de uso de la respuesta del proveedor (B-05-013, **sin código**) | Las mismas, sin operaciones nuevas |
| R1 a R7 | `respuestas.py`, `llegadas.py`, restock | Cambian condiciones de operaciones existentes |
| La propuesta sin formularios | `CU-RST-APR`, ficha | Sólo consulta |
| Edición retirada al cancelar | `CU-ALT-CAN`, **`CO-027`** | Una postcondición más |
| El duplicado contra un cancelado avisa | `CO-003`, `CO-006`, el alta de `CU-CAT-ALT`, los borradores | Cambia la condición de la excepción |
| Reanunciar | **Operación nueva, sin código** | Una de escritura |

---

## 2. Conceptos que toca

| Concepto | ¿Existe? | Qué cambia |
| --- | --- | --- |
| `LineaPedidoProveedor` | Sí | El motivo pasa a ser de cada línea (el campo de cierre ya existe) |
| `PropuestaRestock` | Sí | Sólo lectura: hace cuánto espera, y si espera un reintento |
| `ProductoEditorial` | Sí | Gana la marca de **edición retirada** y el enlace **reanuncia a**. Migración con datos: marca los cancelados existentes |
| Restricciones `producto_editorial_unico_por_isbn` y `_por_clave` | Sí | Pasan a ser condicionales. **Hay que verificar que sobrevivan a la migración como índices** (`CLAUDE.md`) |

---

## 3. Ambigüedades detectadas

| # | Dónde | Las dos lecturas | Recomendación |
| --- | --- | --- | --- |
| 1 | Parte B, `CU-ALT-CAN` | El que vuelve **es otra edición, con código nuevo** / es **el mismo producto, reactivado** | **Otra edición** (salida 1). Es un **agregado** al documento: el comentario de `CU-ALT-CAN` no cambia |
| 2 | Parte B, «Reanunciar» | ¿**Caso de uso nuevo** o **flujo alternativo** del alta (`CU-ALT-*` / `CU-CAT-ALT`)? | Flujo alternativo del alta. **El código, si hace falta, lo asigna el responsable** |
| 3 | R2 | Más de lo pedido: **se rechaza** / se acepta con advertencia | **Se rechaza**: el cupo sale de lo pedido, y lo de más se pide con otro pedido |
| 4 | R1 | La llegada **confirma la línea entera** / sólo lo que llegó | **La línea entera**: si llegó algo, el proveedor la está mandando; si después no manda el resto, se cierra como hoy |
| 5 | Parte A | El borrado forzado de Sakamoto #24 | Queda anotado en la bitácora como lo que fue: limpieza de un dato sin reservas. Con la salida 1 no vuelve a hacer falta |

---

## 4. Orden de construcción

| # | Qué | Depende de | Motivo |
| --- | --- | --- | --- |
| 1 | R1 a R4 y R7 en el servicio, con pruebas (también de Telegram) | — | Arreglan fallos reales, sin tocar pantallas |
| 2 | Ficha del pedido: una tabla, la pregunta y sus tres diálogos | 1 | El cambio grande de pantalla |
| 3 | Ficha y lista de la propuesta sin formularios, R5 y R6 | 2 | Se vacía cuando la ficha del pedido ya lo hace todo |
| 4 | Edición retirada: campo, migración y restricciones condicionales | — | La base primero; verificar los índices sobre la base de desarrollo |
| 5 | El duplicado contra un cancelado avisa, en alta, lote y borrador | 4 | — |
| 6 | «Volver a anunciar» y el enlace entre las dos fichas | 5 | — |
| 7 | Capturas, bitácora (05, 01, 19), ESTADO, DEUDA y las siete puertas | todo | — |

---

## 5. Riesgos

| Riesgo | Dónde | Cómo se cubre |
| --- | --- | --- |
| Restricciones condicionales mal migradas: dos ediciones vivas con el mismo ISBN | Migración de la parte B | Prueba de la restricción en la base, y verificación a mano del índice en desarrollo y en la VM |
| R1 cambia el comportamiento de una llegada ya probada | `llegadas.py` | Pruebas de contrato de la llegada (`CO-013`, `CO-077`) intactas, más la postcondición nueva |
| Un cancelado con reservas que vuelve: ¿se reasignan las reservas? | Parte B | **No**: ya se reembolsaron en puntos (`CO-027`). El nuevo arranca sin reservas. Se dice en el aviso |
| Pruebas que leen la tabla de respuesta vieja | `test_respuesta_del_proveedor.py` | Se reescriben con la pantalla nueva; el servicio no cambia de firma |

---

## 6. Fuera de alcance

- Que el modelo lea la respuesta del correo del proveedor: sigue fuera, como en el plan anterior.
- Reactivar un cancelado (salida 2): contradice `CU-ALT-CAN`.
- Reasignar al reanunciado las reservas que el cancelado reembolsó.
- Cambiar los botones de Telegram, más allá del enlace de «Confirmó con cambios».
