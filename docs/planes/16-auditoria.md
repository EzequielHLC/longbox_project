> **Tipo: Normativo** una vez aprobado. Antes de la aprobación es una propuesta.
> Se escribe **antes** de programar y **no se reescribe** después: si algo cambió durante la
> construcción, eso va a la bitácora del módulo, no acá.

# Plan — `16` Auditoría

**Estado del plan:** Aprobado el 2026-09-30, con las respuestas registradas en `docs/DEUDA.md` · **Fecha:** 2026-09-30

---

## 1. Qué cubre

| Caso de uso | Contratos | Operaciones de escritura | Operaciones de consulta |
| --- | --- | --- | --- |
| `CU-AUD-CON` | `CO-205`, `CO-206`, `CO-129` | 1 (la exportación, que se audita) | 2 |

**Total: 3 contratos.** `RegistroAuditoria` existe, es inmutable y ya está poblado. Se construye
la pantalla de consulta: 50 entradas por página, de la más reciente a la más antigua, con
filtros por actor, tipo de acción, entidad y rango de fechas. Se suman el detalle de una
entrada y la exportación CSV de **todas** las entradas del filtro activo, no sólo la página.

La consulta no se audita. La exportación sí, con la acción «Exportación del log de auditoría»,
ya declarada en el modelo (INC-06).

La ficha dice que cualquier intento de escritura sobre el log se rechaza con 403. Las direcciones
nuevas responden 403, y no 405, a todo método que no sea de lectura, salvo la exportación.
La prueba lo ejerce con `POST`, `PUT` y `DELETE`.

---

## 2. Conceptos que toca

| Concepto | ¿Existe? | Qué hace este módulo con él |
| --- | --- | --- |
| `RegistroAuditoria` | Sí | Lo lee. Escribe sólo la entrada de la exportación |

---

## 3. Ambigüedades detectadas

| # | Dónde | Las dos lecturas | Qué se necesita para destrabarla |
| --- | --- | --- | --- |
| 1 | `CU-AUD-CON` paso 3: tipo de acción «alta / modificación / eliminación / cobro / cancelación / cambio de rol / inicio de sesión / cierre de sesión / exportación» | El log guarda un enumerado cerrado de acciones concretas (28 hoy). Las nueve categorías de la ficha no están mapeadas a ese enumerado en ninguna parte. **(a)** El filtro ofrece las acciones del enumerado, agrupadas. **(b)** Ofrece las nueve categorías, con un mapeo que hay que inventar. **Recomiendo (a)** | Decisión del responsable. Con (b), el mapeo lo tiene que escribir el documento |
| 2 | Paso 3: filtro por actor «usuario específico o tipo de rol» | La entrada guarda el correo del actor, no su rol en ese momento. **(a)** El filtro por rol usa el rol **actual** de la cuenta; una cuenta eliminada no entra en ningún rol. **(b)** Hay que guardar el rol en cada entrada, lo que cambia el modelo. **Recomiendo (a)**, y que la pantalla lo diga | Decisión del responsable |
| 3 | `CO-206`: «valor anterior y valor nuevo cuando aplican» | El modelo declara un único `detalle` que contiene los dos valores. Se presenta el detalle tal como se registró. No se separan con un análisis de texto que el modelo no declara | Nada, salvo objeción |
| 4 | Paso 3: «entidad afectada» | Es el tipo del objetivo genérico (P-10). El filtro ofrece los tipos que aparecen en el log | — |

---

## 4. Orden de construcción

| # | Qué | Depende de | Motivo |
| --- | --- | --- | --- |
| 1 | `CO-205` sin filtros de acción ni de rol | Estilo preliminar | Paginado y orden. Fija la pantalla |
| 2 | Filtros | **Ambigüedades 1 y 2** | Si siguen abiertas, se construyen actor por correo, entidad y fechas, y `CU-AUD-CON` queda `Parcial` |
| 3 | `CO-206` | 1 | — |
| 4 | `CO-129` | 2 | La prueba compara las filas del CSV con el total del filtro, en más de una página |

---

## 5. Riesgos

| Riesgo | Dónde aparece | Cómo se cubre |
| --- | --- | --- |
| Volumen del log | La exportación recorre todo el filtro | Se genera en flujo, sin cargar todas las entradas en memoria |
| Inyección de fórmulas en el CSV | Un correo o un detalle que empieza con `=`, `+`, `-` o `@` | Esas celdas se escapan. Con prueba |
| Control de acceso | Las tres operaciones | Prueba por la dirección real con Cajero, Cliente y sin sesión |

---

## 6. Fuera de alcance

Nada más en el módulo.
