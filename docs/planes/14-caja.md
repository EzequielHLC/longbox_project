> **Tipo: Normativo** una vez aprobado. Antes de la aprobación es una propuesta.
> Se escribe **antes** de programar y **no se reescribe** después: si algo cambió durante la
> construcción, eso va a la bitácora del módulo, no acá.

# Plan — `14` Caja

**Estado del plan:** Aprobado el 2026-10-10, con las recomendaciones de la sección 3 · **Fecha:** 2026-10-10

El cierre del día: consolida las ventas del mostrador (plan 06) y los cobros online por canal y
por medio de pago. Va después de Ventas presenciales.

---

## 1. Qué cubre

| Caso de uso | Contratos | Operaciones de escritura | Operaciones de consulta |
| --- | --- | --- | --- |
| `CU-CAJ-CIE` | `CO-203`, `CO-126`, `CO-127` | 1 (`CO-126`) | 2 |

---

## 2. Conceptos que toca

| Concepto | ¿Existe? | Qué hace este plan con él |
| --- | --- | --- |
| `CierreDeCaja` | **No** | Lo crea: fecha de la jornada única (I-23), totales por canal y por medio, total global, incluidas y excluidas |
| `TransaccionPago` | Sí | Se asocia al cierre; `incluida en cierre` pasa a sí |

---

## 3. Ambigüedades detectadas

| # | Dónde | Las dos lecturas | Qué se necesita para destrabarla |
| --- | --- | --- | --- |
| 1 | **Ventas posteriores a un cierre del mismo día.** `CU-CAJ-CIE` E1 sólo impide un segundo cierre «si no hay nuevas transacciones posteriores», y I-23 dice que hay a lo sumo un cierre por fecha | **(a)** Lo vendido después del cierre pasa al cierre siguiente. E1 informa que el día ya está cerrado y cuántas transacciones esperan el próximo. **(b)** Se reabre el cierre del día y se le suman. **(c)** Un cierre complementario el mismo día, lo que viola I-23 | Decisión. **Recomiendo (a)**: un cierre no cambia después de confirmado, e I-23 se cumple. Es una corrección de E1 y va a la bitácora |
| 2 | **Qué es la «jornada activa»** | **(a)** Todas las transacciones aprobadas que todavía no entraron en un cierre, aunque sean de días anteriores sin cerrar. La fecha del cierre es la de hoy. **(b)** Sólo las del día calendario; las de días sin cerrar quedan sueltas | **Recomiendo (a)**: ninguna venta queda fuera de un cierre. El resumen avisa si hay de días anteriores |
| 3 | **Compras pagadas sólo con puntos** | No tienen `TransaccionPago` (B-07-033): no hubo dinero | No entran al cierre. Se informan aparte, como cantidad |
| 4 | **Arqueo de efectivo** | La ficha no pide contar el efectivo de la caja ni comparar contra lo esperado | No se construye. Si se quiere, es un agregado que decide el responsable |
| 5 | **«Pendiente de verificación»** (A1) | Hoy ningún flujo crea transacciones en ese estado (la contingencia de R-06 no tiene caso de uso) | Se construye el tratamiento de A1 y se prueba montando el estado a mano |

---

## 4. Orden de construcción

| # | Qué | Depende de | Motivo |
| --- | --- | --- | --- |
| 1 | `CierreDeCaja` con su unicidad por fecha en la base | Plan 06 | |
| 2 | `CO-203`: el resumen previo, E1 y E2 | 1 | |
| 3 | `CO-126` con A1, y la pantalla del cierre definitivo | 2 | La única escritura |
| 4 | `CO-127`: CSV con cada transacción y los totales, auditado | 3 | |
| 5 | «Caja» en el menú del Cajero y del Administrador; listado de cierres anteriores | 3 | |

---

## 5. Riesgos

| Riesgo | Dónde | Cómo se cubre |
| --- | --- | --- |
| Dos usuarios cierran a la vez y la misma transacción entra en dos cierres | `CO-126` | Bloqueo de las transacciones al cerrar y unicidad por fecha en la base. Prueba de concurrencia |
| Una venta que se confirma mientras se cierra | `CO-126` | Entra en este cierre o en el siguiente, nunca en los dos ni en ninguno. Prueba |
| Totales con flotantes | `CO-126` | `Decimal`; los totales por canal y por medio se guardan como importes, no como texto |
| `CO-203` modifica algo | `CO-203` | Prueba que compara antes y después |
| Rol equivocado | Acceso | El Cliente recibe 403 por la dirección real |

---

## 6. Fuera de alcance

- El arqueo de efectivo (ambigüedad 4).
- Reabrir o anular un cierre.
- Los reportes por período (`CU-REP-GEN`, módulo 15).
