> **Tipo: Normativo** una vez aprobado. Antes de la aprobación es una propuesta.
> Se escribe **antes** de programar y **no se reescribe** después: si algo cambió durante la
> construcción, eso va a la bitácora del módulo, no acá.

# Plan — `01` Alta Editorial · el ciclo de la pre-venta

**Estado del plan:** Aprobado el 2026-10-12, con las recomendaciones de la sección 3 · **Fecha:** 2026-10-12

La pre-venta hoy se vende pero nunca llega: los pedidos quedan en «Esperando stock de pre-venta»
para siempre. Este plan construye el resto del ciclo del lado del Administrador: el aviso de lo
que está por llegar, la confirmación del ingreso, la demora y la cancelación por la editorial. La
respuesta del Cliente ante una demora es el plan 08, segunda parte, y se construye junto con éste.

---

## 1. Qué cubre

| Caso de uso | Contratos | Escritura | Consulta |
| --- | --- | --- | --- |
| `CU-ALT-TRA` | `CO-011`, `CO-012`, `CO-013` | 2 (`CO-012`, `CO-013`) | 1 |
| `CU-ALT-DEM` | `CO-014`, `CO-015`, `CO-156` | 1 | 2 |
| `CU-ALT-CAN` | `CO-026`, `CO-027`, `CO-156` | 1 | 2 |

**Total: 7 contratos propios** y `CO-156` en dos casos de uso más. `CO-013` encadena `CO-077`
(avisar a los suscriptores de reposición), que no existe hasta el módulo 05: `CU-ALT-TRA` queda
`Parcial` por eso.

---

## 2. Conceptos que toca

| Concepto | ¿Existe? | Qué hace este plan con él |
| --- | --- | --- |
| `ProductoEditorial` | Sí | Usa `fecha_llegada`, `demorado`, `fecha_estimada` y `nota_demora`, que ya existen |
| `Pedido`, `LineaPedido`, `TransicionDePedido` | Sí | Transiciones de estado de pedidos y líneas |
| `LotePuntos`, `MovimientoPuntos` | Sí | Reembolso en puntos (`CO-027`) |
| `ConfiguracionSistema` | Sí | Gana «días de aviso previo a la llegada» (N, por defecto 2), que `CU-CFG-PAR` ya especifica |

---

## 3. Ambigüedades detectadas

| # | Dónde | Las dos lecturas | Qué se necesita para destrabarla |
| --- | --- | --- | --- |
| 1 | **Qué es «el lote» que se confirma** (`CO-013 confirmarIngresoDeLote(lote, …)`). Las pre-ventas entran por la carga de lotes o desde los correos de los proveedores, y no todas quedan atadas a un `LoteAlta` | **(a)** Una pantalla «Pre-ventas por llegar», agrupada por fecha de llegada y editorial. El Administrador marca qué llegó, con las unidades de cada producto, y lo que no marca de ese grupo queda demorado (A1). **(b)** Sólo productos con `LoteAlta` | Decisión. **Recomiendo (a)**: cubre todas las pre-ventas, venga de donde venga. Es un agregado y va a la bitácora |
| 2 | **Cómo se avisa al Administrador** (`CO-011`: proximidad y recordatorio; `CO-012`: escalado) | **(a)** Un correo a cada Administrador activo, y además el bloque «Pre-ventas por llegar» en el tablero, con lo próximo, lo de hoy y lo vencido. **(b)** Sólo correo | **Recomiendo (a)**: el tablero es lo primero que ve cada día |
| 3 | **El escalado «a las 23:59 del día de llegada»** (`CO-012`) | El Temporizador corre una vez por día. **(a)** El escalado sale en la primera corrida posterior al día de llegada: el mismo resultado, sin un reloj de segundos. **(b)** Un proceso que corra cada minuto | **Recomiendo (a)**. Y el período de gracia no se vuelve parámetro: `CU-CFG-PAR` no lo declara |
| 4 | **Reembolso de una reserva pagada con puntos** (`CO-026`: «la suma de los valores abonados») | **(a)** Lo que se pagó en dinero vuelve convertido a puntos con el valor del punto; lo que se pagó con puntos vuelve con los mismos puntos. **(b)** Todo a precio de la línea | **Recomiendo (a)**: el cliente recupera exactamente lo que dio |
| 5 | **Redondeo del reembolso a puntos** | **(a)** Hacia arriba: un reembolso del 100 % no puede quedar corto por un redondeo. **(b)** Hacia abajo, como la acreditación | **Recomiendo (a)** |
| 6 | **Productos que no tienen pedidos** | Las fichas ya lo resuelven: la demora y la cancelación se registran igual, sin cascada | Sin ambigüedad |

---

## 4. Orden de construcción

| # | Qué | Depende de | Motivo |
| --- | --- | --- | --- |
| 1 | El parámetro N y la pantalla «Pre-ventas por llegar» (`CO-011` como consulta) | — | Es donde se confirma y donde se demora |
| 2 | `CO-013` con su atomicidad por producto (E3), y A1 hacia `CO-015` | 1 | Destraba los pedidos de pre-venta |
| 3 | `CO-014` y `CO-015` desde la ficha del producto, con informe de impacto y `CO-156` | 1 | Lo invocan `CO-013` y el plan 08 |
| 4 | `CO-026` y `CO-027` con atomicidad total, y `CO-156` | — | |
| 5 | `CO-011` y `CO-012` en el Temporizador, con correo y el bloque del tablero | 1 | |

---

## 5. Riesgos

| Riesgo | Dónde | Cómo se cubre |
| --- | --- | --- |
| Un fallo a mitad de `CO-013` deja productos a medias | `CO-013` E3 | Una transacción por producto; el que falla vuelve a Pre-venta y los demás siguen. Prueba que fuerza el fallo |
| Un reembolso parcial en la cancelación en lote | `CO-027` E1 | Una sola transacción; prueba que fuerza el fallo y verifica que no quedó nada |
| `CO-011` o `CO-012` cambian estados | Postcondiciones vacías | Prueba que compara productos y pedidos antes y después de cada ciclo |
| El Temporizador corrido dos veces el mismo día duplica avisos | `CO-011`, `CO-012` | Se recuerda qué se avisó y cuándo; prueba de doble corrida |
| La confirmación del ingreso choca con una venta | `CO-013` | Bloqueo de los productos, como en las otras escrituras de stock |
| Rol equivocado | Todo | Sólo el Administrador; 403 por la dirección real |

---

## 6. Fuera de alcance

- `CO-077`, la notificación a los suscriptores de reposición (módulo 05).
- La demora de un producto que ya estaba en stock (RF-18 a): ningún caso de uso la describe.
