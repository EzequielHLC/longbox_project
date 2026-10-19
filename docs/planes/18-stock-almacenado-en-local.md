> **Tipo: Normativo** una vez aprobado. Antes de la aprobación es una propuesta.
> Se escribe **antes** de programar y **no se reescribe** después: si algo cambió durante la
> construcción, eso va a la bitácora del módulo, no acá.

# Plan — `18` Stock Almacenado en Local

**Estado del plan:** Aprobado el 2026-10-14, con las recomendaciones de la sección 3 · **Fecha:** 2026-10-14

El artículo que un Cliente eligió recibir en un segundo envío (opción 2 de `CU-PED-OPC`) hoy llega
y queda «Disponible · Despacho diferido» sin nada que hacer con él (B-08-007). Este módulo le da su
ciclo: queda retenido a nombre del Cliente, el Cliente pide el envío (gratis o pago), el local lo
despacha o lo entrega en el mostrador, y si vence vuelve al stock. Destraba además la sección
Stock en Local de «Mi cuenta» (`CU-CLI-HIS`, B-11-003) y el informe de `CU-CLI-BAJ`.

---

## 1. Qué cubre

| Caso de uso | Contratos | Escritura | Consulta |
| --- | --- | --- | --- |
| `CU-STK-CON` | `CO-215` | 0 | 1 |
| `CU-STK-DES` | `CO-216`, `CO-087`, `CO-151`, `CO-089` | 2 (`CO-151`, `CO-089`) | 2 |
| `CU-STK-ADC` | `CO-217`, `CO-218` | 0 | 2 |
| `CU-STK-FIS` | `CO-152`, `CO-227` | 2 | 0 |
| `CU-STK-PLA` | `CO-153` | 1 | 0 |
| `CU-STK-VEN` | `CO-154` | 1 | 0 |

**Total: 9 contratos propios** y dos compartidos con la compra online (`CO-087`, `CO-089`), que
ganan el caso del envío de stock almacenado. `CU-PED-OPC` deja de ser `Parcial`: `CO-095` cumple
su opción 2 entera.

---

## 2. Conceptos que toca

| Concepto | ¿Existe? | Qué hace este plan con él |
| --- | --- | --- |
| `ArticuloRetenido` | **No** | Lo crea, con los seis estados de DME-12. «Reservado para cambio» queda declarado y lo usa el módulo 09 |
| Solicitud de despacho | **No** | Ambigüedad 3 |
| `LineaPedido` | Sí | Origen del artículo retenido (opción 2) |
| `TransaccionPago`, `CobroEnCurso` | Sí | El cobro del envío (A1) |
| `CierreDeCaja` | Sí | Incluye los cobros de envío como canal Online |
| `ConfiguracionSistema` | Sí | Gana «plazo de retención (meses)» (3) y «días de aviso previo al vencimiento» (7), que `CU-CFG-PAR` ya especifica en Logística |

---

## 3. Ambigüedades detectadas

| # | Dónde | Las dos lecturas | Qué se necesita para destrabarla |
| --- | --- | --- | --- |
| 1 | **Cuántos artículos nacen de una línea.** El modelo asocia `ArticuloRetenido 0..1 — 0..1 LineaPedido`, pero el artículo «es una unidad» del producto y `CO-154` devuelve «una unidad» al stock | **(a)** Un artículo por unidad: una línea de 2 tomos son 2 artículos, con el precio unitario como valor. Cada uno se despacha, retira o vence por separado. **(b)** Uno por línea, con cantidad | **Recomiendo (a)**. Corrige la multiplicidad del modelo (`0..*` artículos por línea) |
| 2 | **Qué pasa con la línea del pedido** cuando su artículo queda retenido. DME-08 no tiene un estado para «en el local a nombre del Cliente» | **(a)** La línea queda como está (Disponible · Despacho diferido) y el pedido muestra «En el local a tu nombre» con el enlace a Stock en Local; deja de contar como demorada en el listado del Administrador. **(b)** Un estado nuevo de línea | **Recomiendo (a)**: el seguimiento pasa al artículo, que tiene su propio ciclo |
| 3 | **Dónde vive la solicitud de despacho y su pago.** `CO-151` «genera la solicitud» y crea una `TransaccionPago`, pero hoy toda transacción pertenece a un pedido | **(a)** Un concepto nuevo, **Solicitud de despacho**: los artículos, la dirección copiada, el costo de envío y, si fue pago, su `TransaccionPago`. El cierre de caja la cuenta como canal Online. **(b)** Armar un `Pedido` por cada envío | **Recomiendo (a)**: un pedido sin venta duplicaría ventas en los totales. Es un agregado al modelo |
| 4 | **El vencimiento con despacho pendiente.** `CO-154` extiende 3 días y alerta. RF-25 (5): si pasa la extensión sin despacho, se reintegra al stock | **(a)** Se extiende 3 días y se alerta cada vez que vence mientras siga pendiente: un envío que el Cliente pudo haber pagado no vuelve al stock sin que lo decida el local. **(b)** Lo de RF-25: una sola extensión y después al stock | **Recomiendo (a)**. Es una corrección de RF-25 (5) |
| 5 | **«Exactamente 7 días antes»** (`CO-154`). El Temporizador puede no correr un día | **(a)** Se avisa cuando faltan los días configurados o menos, una sola vez por artículo y por fecha de vencimiento: si el plazo cambia, se avisa de nuevo. **(b)** Sólo el día exacto | **Recomiendo (a)** |
| 6 | **El umbral del envío gratis.** `CU-STK-DES`: «si el valor total **supera** el monto mínimo». La compra online lo aplica «desde» el monto | **(a)** El mismo criterio que la compra: desde el monto, gratis. **(b)** Estrictamente mayor | **Recomiendo (a)**: el Cliente ya lo ve así en la barra del envío gratis |
| 7 | **Qué se despacha de una vez.** `CO-152` confirma un artículo; una solicitud suele tener varios en el mismo paquete | **(a)** La ficha de la solicitud confirma todos sus artículos pendientes de una vez (cada uno con las postcondiciones de `CO-152`), y la del artículo, uno solo. **(b)** Sólo de a uno | **Recomiendo (a)** |
| 8 | **El ciclo sin artículos elegibles** (`CU-STK-VEN` E2 lo registra en el log; `CO-154` no) | **(a)** Lo del contrato: no deja entrada. Correría todos los días. **(b)** Una entrada por día | **Recomiendo (a)** |

---

## 4. Orden de construcción

| # | Qué | Depende de | Motivo |
| --- | --- | --- | --- |
| 1 | `ArticuloRetenido`, los dos parámetros, y su alta desde `CO-013` para la opción 2 (con migración de lo que ya llegó) | — | Sin artículos no hay módulo |
| 2 | `CU-STK-ADC` y `CU-STK-CON` (consultas, y la sección en «Mi cuenta») | 1 | |
| 3 | `CU-STK-FIS` (despacho y retiro) y `CU-STK-PLA` | 2 | Lo invocan desde la ficha |
| 4 | `CU-STK-DES` gratis, después con pago (A1) y su lugar en el cierre de caja | 2 | El pago reutiliza la pasarela |
| 5 | `CU-STK-VEN` en el Temporizador | 1 | |

---

## 5. Riesgos

| Riesgo | Dónde | Cómo se cubre |
| --- | --- | --- |
| El Cliente pide el envío mientras el ciclo lo vence, o dos pestañas lo piden | `CO-151`, `CO-154` | Los artículos se toman con bloqueo y se verifica que sigan Disponibles. Prueba de concurrencia |
| El pago se aprueba cuando un artículo ya venció o ya se pidió | `CO-089` | No se genera la solicitud y el cobro se reembolsa, como en la compra (E3). Prueba |
| El despacho y el retiro del mismo artículo a la vez | `CO-152`, `CO-227` | Bloqueo y E1. Prueba de concurrencia |
| Vencer suma stock dos veces | `CO-154` | Transacción por artículo con bloqueo; prueba de doble corrida |
| Cajero modifica el plazo | `CO-153` | Sólo el Administrador, 403 por la dirección real |

---

## 6. Fuera de alcance

- «Reservado para cambio» como origen: lo crea el módulo 09 (devoluciones). El estado queda
  declarado y el resto del ciclo ya lo admite.
- `CU-CLI-BAJ`: con este módulo su informe de impacto se puede calcular; es el siguiente plan.
