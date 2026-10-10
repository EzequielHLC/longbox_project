> **Tipo: Normativo** una vez aprobado. Antes de la aprobación es una propuesta.
> Se escribe **antes** de programar y **no se reescribe** después: si algo cambió durante la
> construcción, eso va a la bitácora del módulo, no acá.

# Plan — `10` Puntos · primera parte: el Cliente ve sus puntos

**Estado del plan:** Aprobado el 2026-10-09, con las recomendaciones de la sección 3. En la 2,
el responsable pidió además el saldo en la barra superior de la tienda, siempre a la vista, «cosa
de que quiera consultar si le alcanzan los puntos en todo momento para canjear algo» · **Fecha:**
2026-10-09

Primer plan del módulo, a pedido del responsable («ver los puntos»). `LotePuntos` y
`MovimientoPuntos` existen desde la compra online (plan 07, sexta parte). Falta que el Cliente los
vea. Va junto con el panel de cuenta (plan 11, segunda parte), que tiene una sección Puntos.

---

## 1. Qué cubre

| Caso de uso | Contratos | Operaciones de escritura | Operaciones de consulta |
| --- | --- | --- | --- |
| `CU-PTS-CON` | `CO-188`, `CO-189` | 0 | 2 |

---

## 2. Conceptos que toca

| Concepto | ¿Existe? | Qué hace este plan con él |
| --- | --- | --- |
| `LotePuntos`, `MovimientoPuntos` | Sí | Sólo los lee |
| `ConfiguracionSistema` | Sí | Lee la equivalencia, para mostrar el saldo en pesos |

---

## 3. Ambigüedades detectadas

| # | Dónde | Las dos lecturas | Qué se necesita para destrabarla |
| --- | --- | --- | --- |
| 1 | **El origen del movimiento.** `CU-PTS-CON` paso 2 pide el origen por lote («compra / reembolso / compensación / ajuste admin»), y el historial de movimientos sólo pide tipo, cantidad y saldo | **(a)** El historial muestra además de dónde viene cada movimiento (el pedido, cuando lo hay), con enlace a su detalle. **(b)** Sólo lo que pide la ficha | **Recomiendo (a)**: «Acreditación de 1800» sin decir de qué compra no le sirve al Cliente. Es un agregado y va a la bitácora |
| 2 | **Dónde se ve el saldo fuera del panel** | **(a)** Además del panel, el menú «Mi cuenta» de la tienda muestra el saldo. **(b)** Sólo en el panel y en el checkout | **Recomiendo (a)**, a pedido del responsable. Agregado |
| 3 | «Próximo a vencer»: 30 días en `CU-PTS-CON`, 7 días para el stock almacenado en `CU-CLI-HIS` | No es contradicción: son conceptos distintos | Se respeta cada uno |

---

## 4. Orden de construcción

| # | Qué | Depende de | Motivo |
| --- | --- | --- | --- |
| 1 | `CO-188`: saldo con su equivalencia, lotes con «Próximo a vencer» e historial de a 50 | Plan 11, segunda parte (el panel) | Se entra desde el panel |
| 2 | `CO-189`: filtro por tipo y por rango de fechas, total encontrado, E1 con «Limpiar filtros» | 1 | |
| 3 | El saldo en el menú «Mi cuenta» | 1 | |

---

## 5. Riesgos

| Riesgo | Dónde | Cómo se cubre |
| --- | --- | --- |
| Un Cliente ve los puntos de otro | `CO-188` | La consulta es siempre de quien pide; no recibe identificador. Prueba con dos clientes |
| La consulta modifica algo | `CO-188`, `CO-189` | Prueba que compara lotes y movimientos antes y después |
| Fechas del filtro inválidas | `CO-189` | Se ignoran, como en el padrón de usuarios |
| El personal entra a la pantalla | Acceso | 403 por la dirección real |

---

## 6. Fuera de alcance

- `CU-PTS-ADM` (ajuste manual), `CU-PTS-CAD` (caducidad) y la rama de mostrador de `CU-PTS-CJE`.
- La consulta de puntos de un cliente por el personal (`CO-191`).
