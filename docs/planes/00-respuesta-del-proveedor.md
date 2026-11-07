> **Tipo: Normativo** una vez aprobado. Antes de la aprobación es una propuesta.
> Se escribe **antes** de programar y **no se reescribe** después: si algo cambió durante la
> construcción, eso va a la bitácora del módulo, no acá.

# Plan — `00` La respuesta del proveedor a una propuesta de restock

**Estado del plan:** Aprobado el 2026-10-28, con las recomendaciones · **Fecha:** 2026-10-28

Pedido del responsable (2026-10-28): una propuesta despachada **queda abierta** para anotar lo que
contesta el proveedor —qué líneas confirma, con qué cantidad, cuándo llega, qué no puede
abastecer— y esa respuesta también se da desde Telegram.

Decisiones que el responsable ya tomó, el 2026-10-28:

| Pregunta | Decisión |
| --- | --- |
| Dónde se anota | **En la propuesta, que queda abierta.** Por dentro, en el pedido a proveedor de cada uno |
| Qué se anota | Confirmar cada línea · cambiar la cantidad · la fecha de llegada · cerrar porque no puede (una línea o el pedido entero) |
| Telegram | **Avisos y respuesta rápida**: confirmar todo, poner la fecha, cerrar porque no puede. Las cantidades, línea por línea, en la web |
| El modelo lee la respuesta del correo | **No por ahora** |

**Es un desvío aprobado**: la especificación cierra la propuesta sola cuando cada proveedor se
despachó o se descartó (DME-13, `CO-072`, `CO-073`). Va a la bitácora del módulo 05 como desvío,
con la aprobación del responsable. Las operaciones nuevas **no tienen contrato**: esperan su código.

---

## 1. Qué cubre

| Qué | Dónde | Operaciones nuevas (sin código) |
| --- | --- | --- |
| La propuesta despachada queda en **«Esperando respuesta»** y se cierra cuando todos sus proveedores respondieron | `CU-RST-APR`, DME-13 | El cierre, que cambia de condición |
| **Registrar la respuesta** de un proveedor, en la ficha de la propuesta | Caso de uso nuevo (a codificar) | Confirmar línea · cambiar la cantidad confirmada · poner la fecha · cerrar línea o pedido sin abastecer |
| **Telegram**: el aviso del pedido que salió, con «✅ Confirmó todo», «📅 Fecha de llegada» y «⛔ No puede»; un recordatorio si no respondió | `CU-AVI-*` | Las mismas operaciones, desde el chat |

---

## 2. Conceptos que toca

| Concepto | ¿Existe? | Qué cambia |
| --- | --- | --- |
| `PropuestaRestock` | Sí | Un estado nuevo, **«Esperando respuesta»**, entre Pendiente y Cerrada. No cuenta para «una sola pendiente» (I-21): mientras espera, se puede generar la próxima |
| `LineaPedidoProveedor` | Sí | Gana **la respuesta** (sin respuesta · confirmada · con otra cantidad · no disponible) y **la cantidad confirmada**. Lo que falta llegar se cuenta sobre lo confirmado, no sobre lo pedido |
| `PedidoProveedor` | Sí | La fecha estimada pasa a editarse después del despacho |

---

## 3. Ambigüedades detectadas

| # | Dónde | Las dos lecturas | Recomendación |
| --- | --- | --- | --- |
| 1 | Cuándo se cierra la propuesta | Cuando todos respondieron / cuando llegó todo | **Cuando todos respondieron.** Lo que llega se sigue en «Pedidos por llegar», como hoy |
| 2 | Qué es «respondió» | Cada línea con su respuesta / alcanza con la fecha | **Cada línea con respuesta**: confirmada, con otra cantidad o no disponible. La fecha es aparte y se puede cambiar después |
| 3 | El proveedor confirma **menos** que lo pedido y hay **reservas de pre-venta** por encima de lo confirmado | Bloquear / aceptar y avisar | **Aceptar y avisar**: el pedido refleja la realidad. Las reservas que quedan sin cubrir se señalan en la pre-venta y en el aviso, para resolverlas con la demora o la cancelación que ya existen (`CU-ALT-DEM`, `CO-027`). Nada se cancela solo |
| 4 | Cambiar la fecha de un pedido con productos en pre-venta | Cambia la fecha y listo / es una demora | **Si la fecha se atrasa y hay reservas, es una demora**: se ofrece el registro de demora que ya existe (avisa a los clientes, `CO-015`). Si no hay reservas, cambia y listo |
| 5 | Cerrar el pedido entero «porque no puede» | Una por una / todo junto | **Todo junto, con un motivo**: es `cerrar_sin_recibir` sobre cada línea abierta, con la misma regla para las pre-ventas sin reservas |
| 6 | Recordatorio por Telegram | Nunca / a los N días sin respuesta | **A los 3 días** sin respuesta completa, una vez; y el resumen de la mañana suma «pedidos sin respuesta» |
| 7 | La fecha desde el chat | Calendario / escribirla | **Escribirla**, respondiendo al mensaje: «15/11» o «15/11/2026», con la misma lectura de fechas del sistema (día y mes sin año → la próxima) |

---

## 4. Orden de construcción

| # | Qué | Por qué |
| --- | --- | --- |
| 1 | El modelo: la respuesta en la línea, la cantidad confirmada, el estado nuevo; lo pendiente sobre lo confirmado | Lo usan todos los demás; toca el cálculo del cupo de las pre-ventas, con sus pruebas |
| 2 | Registrar la respuesta en la web, en la ficha de la propuesta | El caso completo |
| 3 | El cierre por respuesta y la ficha que muestra el seguimiento | |
| 4 | Telegram: el aviso del pedido con sus botones, la fecha respondiendo y el recordatorio | Sobre las operaciones ya probadas |

---

## 5. Riesgos

| Riesgo | Cómo se cubre |
| --- | --- |
| Lo pendiente pasa a contarse sobre lo confirmado y cambia el cupo de las pre-ventas | Pruebas de cupo con cantidad confirmada menor, igual y mayor; las propuestas viejas, sin respuesta, siguen contando lo pedido |
| Dos Administradores responden el mismo pedido a la vez (web y chat) | Bloqueo de fila del pedido, como la llegada; prueba de concurrencia |
| Una respuesta desde un botón ajeno | La firma por botón y la autorización en el momento, como los correos |
| Propuestas ya cerradas con pedidos abiertos | No cambian: la regla nueva rige para las que se despachen desde ahora |

---

## 6. Fuera de alcance

- Que el modelo lea la respuesta del correo del proveedor (decisión del responsable).
- Cambiar cantidades línea por línea desde Telegram.
- Reabrir una propuesta cerrada.

---

## 7. Lo que necesito del responsable

1. **Aprobar el plan**, o decir qué cambia, en especial las ambigüedades 3 y 4 (pre-ventas).
2. Más adelante, **los códigos** del caso de uso nuevo y de sus operaciones.
