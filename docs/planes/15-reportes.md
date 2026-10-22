> **Tipo: Normativo** una vez aprobado. Antes de la aprobación es una propuesta.
> Se escribe **antes** de programar y **no se reescribe** después: si algo cambió durante la
> construcción, eso va a la bitácora del módulo, no acá.

# Plan — `15` Reportes

**Estado del plan:** Propuesto · **Fecha:** 2026-10-22

El único caso de uso del módulo. La revisión funcional lo dejó en su versión mínima (plan 00, A5:
RF-23). Las fuentes leídas: la ficha de `CU-REP-GEN`, su apartado del DSS, `CO-204` y `CO-128`, y
en el modelo `Pedido`, `LineaPedido`, `Producto`, `Tipo`, `MovimientoPuntos` y
`SuscripcionReposicion`. Sólo lee: no introduce ningún concepto del dominio.

---

## 1. Qué cubre

| Caso de uso | Contratos | Operaciones de escritura | Operaciones de consulta |
| --- | --- | --- | --- |
| `CU-REP-GEN` | `CO-204`, `CO-128` | 0 (`CO-128` sólo deja su entrada en el log) | 2 |

**Total del módulo:** 2 contratos. Los cinco reportes de `CO-204`:

| Reporte | Qué consolida | Filtro adicional (paso 3) |
| --- | --- | --- |
| Ventas totales | Cantidad de ventas, unidades e importe del período, por día | Canal |
| Ventas por canal | Lo mismo, separado en físico (mostrador) y online | — |
| Productos más vendidos | Unidades e importe por producto, de mayor a menor | Categoría (tipo de material) |
| Movimientos de puntos | Acreditaciones y débitos por motivo, con sus totales | Tipo de movimiento |
| Solicitudes de reposición activas | Productos con suscripciones en espera y cuántas | Categoría |

---

## 2. Conceptos que toca

| Concepto | ¿Existe? | Qué hace este plan con él |
| --- | --- | --- |
| `Pedido`, `LineaPedido` | Sí | Sólo los lee |
| `MovimientoPuntos` | Sí | Sólo lo lee |
| `SuscripcionReposicion` | Sí | Sólo la lee |
| `RegistroAuditoria` | Sí | Acción nueva «Exportación de reporte» (`CO-128`) |

Se propone una aplicación `apps/reportes` sin modelos: una pantalla, un servicio de consultas y la
exportación. Mezclarla con `ventas` o `pedidos` haría que el reporte de puntos o el de reposición
dependieran de un módulo ajeno.

---

## 3. Ambigüedades detectadas

| # | Dónde | Las lecturas | Qué se necesita para destrabarla |
| --- | --- | --- | --- |
| 1 | `CO-204`, qué es una venta | **(a)** Todo pedido del período que no esté Cancelado, por su fecha, con su importe en dinero. **(b)** Lo mismo, neto de los reembolsos de devoluciones del período. | Decisión. **Recomiendo (a)** con una columna aparte de reembolsos: restarlos mezcla dos fechas (la de la venta y la del reembolso) y el total del día deja de coincidir con el cierre de caja |
| 2 | `CO-204`, el costo de envío | **(a)** Fuera del importe de ventas: no es mercadería. **(b)** Dentro, porque se cobró. | Decisión. **Recomiendo (a)**, con el envío como columna propia en Ventas totales |
| 3 | `CO-204`, las líneas pagadas con puntos | **(a)** Cuentan como unidades vendidas y no suman importe. **(b)** No cuentan. | Decisión. **Recomiendo (a)**: en Productos más vendidos el canje es salida de mercadería igual |
| 4 | Solicitudes de reposición activas y el rango de fechas | **(a)** Las en espera hoy, creadas dentro del rango. **(b)** Las en espera hoy, sin mirar el rango. | Decisión. **Recomiendo (a)**: el rango es obligatorio para todos los reportes (`CO-204`), y así responde «cuánto se pidió en este período que todavía no llegó» |
| 5 | `CU-REP-GEN` E1, «alguna fecha en el futuro» | Hoy no es futuro: el rango puede terminar hoy. | Ninguna. Se anota |
| 6 | `CO-128`, `exportarReporte(reporte)` | El CSV se arma de nuevo con los mismos parámetros, no se guarda el reporte generado. | Ninguna: no hay instancia «reporte» en el modelo. Se anota |

---

## 4. Orden de construcción

| # | Qué | Depende de | Motivo |
| --- | --- | --- | --- |
| 1 | El formulario de parámetros con E1 y la pantalla vacía con E2 | — | Lo común a los cinco |
| 2 | Ventas totales y por canal | 1 | Comparten la consulta |
| 3 | Productos más vendidos, Movimientos de puntos, Solicitudes de reposición | 1 | Independientes entre sí |
| 4 | `CO-128`: el CSV y su entrada en el log | 2, 3 | Exporta lo que se ve |
| 5 | El indicador de carga (RNF-02) | 1 | El componente `_loader.html` que ya usan los listados |

---

## 5. Riesgos

| Riesgo | Dónde | Cómo se cubre |
| --- | --- | --- |
| Un rango de un año tarda más de 10 segundos | RNF-02 | Agregación en la base, no en Python; prueba de cantidad de consultas por reporte |
| El reporte cuenta un pedido cancelado o duplica uno con varias líneas | `CO-204` | Pruebas con pedidos cancelados y de varias líneas en cada reporte |
| La exportación difiere de la pantalla | `CO-128` | El CSV sale del mismo servicio que la pantalla; prueba que compara las dos |
| El Cajero llega a los reportes | Acceso | 403 por la dirección real |
| Una fecha mal formada en la dirección rompe la pantalla | E1 | Se valida con el formulario; prueba con texto basura |

---

## 6. Fuera de alcance

- Gráficos: el contrato pide datos consolidados en pantalla y CSV.
- El historial de ventas con búsqueda que el plan 00 de interfaz dejó para este módulo (sección 22,
  (b)): es otro reporte y no está entre los cinco de `CO-204`.
- Reportes programados o enviados por correo.
