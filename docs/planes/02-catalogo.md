> **Tipo: Normativo** una vez aprobado. Antes de la aprobación es una propuesta.
> Se escribe **antes** de programar y **no se reescribe** después: si algo cambió durante la
> construcción, eso va a la bitácora del módulo, no acá.

# Plan — `02` Catálogo

**Estado del plan:** Aprobado el 2026-09-30, con las respuestas registradas en `docs/DEUDA.md` · **Fecha:** 2026-09-30

Cubre la clasificación descriptiva (grupos y etiquetas), la exportación del inventario y la
verificación de `cancelarOperacion` en la reactivación de producto. El alta, la edición, la baja
y la reactivación de productos no se reconstruyen.

---

## 1. Qué cubre

| Caso de uso | Contratos | Operaciones de escritura | Operaciones de consulta |
| --- | --- | --- | --- |
| `CU-CAT-GRC` | `CO-164` | 0 | 1 |
| `CU-CAT-GRA` | `CO-038`, `CO-164` | 1 | 1 |
| `CU-CAT-GRM` | `CO-039`, `CO-164` | 1 | 1 |
| `CU-CAT-GRB` | `CO-040`, `CO-041`, `CO-156`, `CO-164` | 1 | 3 |
| `CU-CAT-ETC` | `CO-165` | 0 | 1 |
| `CU-CAT-ETA` | `CO-042`, `CO-165` | 1 | 1 |
| `CU-CAT-ETM` | `CO-043`, `CO-165` | 1 | 1 |
| `CU-CAT-ETB` | `CO-044`, `CO-045`, `CO-156`, `CO-165` | 1 | 3 |
| `CU-CAT-INV` | `CO-037`, `CO-162`, `CO-163` | 1 | 2 |
| `CU-CAT-REA` | `CO-156` (sólo esta verificación) | 0 | 1 |

**Total: 14 contratos distintos**, más la verificación puntual de `CO-156` en `CU-CAT-REA`.

**Cambio de comportamiento visible.** Igual que en los catálogos del módulo 17: la casilla de
estado sale de los formularios y la baja pasa a un par con informe. La pantalla de etiquetas
pasa a ser dos pantallas. Una lista los grupos con filtro por estado (`CO-164`). La otra lista
las etiquetas **de un grupo**, paginadas, con búsqueda y filtro por estado (`CO-165`).

**La baja de grupo cambia el dato, no sólo el filtro.** Hoy un grupo inactivo esconde sus
etiquetas de los desplegables sin tocarlas. `CO-041` pide que cada etiqueta del grupo pase a
`activa = no`. Por eso la reactivación del grupo no las reactiva (`CO-039`).

**`CU-CAT-REA`.** Su DSS, en el `dss/DSS.md` vigente, no muestra `cancelarOperacion`. `CO-156`
sí lo referencia. Se agrega la prueba que abre la confirmación, la abandona y afirma que el
producto no cambió y que no se auditó nada. La misma prueba se extiende a `CU-CAT-BAJ`, que ya
declaraba el abandono.

---

## 2. Conceptos que toca

| Concepto | ¿Existe? | Qué hace este módulo con él |
| --- | --- | --- |
| `GrupoEtiqueta` | Sí | Lo modifica: la baja pasa a un par con informe |
| `Etiqueta` | Sí | Lo modifica: la baja del grupo la alcanza |
| `Producto` | Sí | Sólo lo lee: cuenta asignaciones y exporta |
| `RegistroAuditoria` | Sí | Suma la acción «Exportación de inventario», ya declarada en el modelo (INC-06) |

---

## 3. Ambigüedades detectadas

| # | Dónde | Las dos lecturas | Qué se necesita para destrabarla |
| --- | --- | --- | --- |
| 1 | `CO-039`, `CO-041`, `CO-043`, `CO-045`: «dejó de ofrecerse en los filtros del catálogo público» | El catálogo público no existe hasta `CU-TDA-CAT`. **(a)** La prueba afirma sobre la única función que decide qué etiquetas se ofrecen, la que usan los formularios, y el contrato queda **parcial** hasta que el catálogo público la use. **(b)** Se da por verificado porque hoy no hay filtros públicos. **Recomiendo (a)**: con (b) la afirmación es verdadera porque no hay nada que mirar | Confirmación. Con (a), `GRM`, `GRB`, `ETM` y `ETB` cierran como `Parcial` hasta la etapa B |
| 2 | `CO-037`: «un archivo descargable» | No dice el formato. `CO-129`, la otra exportación del sistema, dice CSV. **Recomiendo CSV**, con las mismas columnas del listado y los filtros aplicados | Confirmación |
| 3 | `CO-165`: «paginado» | No dice el tamaño de página. `CO-205` usa 50. Se usa 50 y se anota como agregado | Nada, salvo objeción |
| 4 | Auditoría de alta, modificación y baja de grupo y etiqueta | Es la ambigüedad 4 del plan 17: hoy se auditan como «Modificación de parámetros globales», y un catálogo no es un parámetro | La misma decisión del responsable. No bloquea: ningún contrato nombra la acción |
| 5 | `CO-162` y la ficha de `CU-CAT-INV`: el filtro por etiqueta ofrece también las inactivas, marcadas | Hoy el filtro ofrece sólo las activas. No es una ambigüedad: se construye | — |

---

## 4. Orden de construcción

| # | Caso de uso | Depende de | Motivo |
| --- | --- | --- | --- |
| 1 | `CU-CAT-GRC`, `GRA`, `GRM` | Plan 17, tanda 1 | Mismo patrón que los catálogos del 17 |
| 2 | `CU-CAT-ETC`, `ETA`, `ETM` | 1 | Las etiquetas se listan por grupo |
| 3 | `CU-CAT-ETB`, `GRB` | 2 | `GRB` baja las etiquetas del grupo, así que va después de `ETB` |
| 4 | `CO-156` en `CU-CAT-REA` y `CU-CAT-BAJ` | — | Prueba sola, sin código nuevo |
| 5 | `CU-CAT-INV`: exportación y filtro por etiqueta inactiva | Ambigüedad 2 | La exportación se prueba por la dirección real con rol Cajero: debe responder 403 |

---

## 5. Riesgos

| Riesgo | Dónde aparece | Cómo se cubre |
| --- | --- | --- |
| La baja de un grupo grande | `CO-041` sobre cientos de etiquetas | Un solo `update()` dentro de la transacción. La prueba cuenta las etiquetas antes y después |
| Mover una etiqueta rompe la unicidad | `CO-043` E1 | La restricción vive en la base (I-08). La prueba la ejerce por el formulario y por un `save()` directo |
| La exportación filtra distinto que la pantalla | `CO-037` | Las dos usan el mismo queryset. La prueba compara las filas del archivo con las del listado |
| Control de acceso | `CO-037` es la única acción restringida de `CU-CAT-INV` | Prueba con Cajero por la dirección real |

---

## 6. Fuera de alcance

- Los filtros por etiqueta del catálogo público: `CU-TDA-CAT`, etapa B.
- `CO-031 restaurarPrecioCalculado` en `CU-CAT-EDI`: va en el plan 03.
