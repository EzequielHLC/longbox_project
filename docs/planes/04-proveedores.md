> **Tipo: Normativo** una vez aprobado. Antes de la aprobación es una propuesta.
> Se escribe **antes** de programar y **no se reescribe** después: si algo cambió durante la
> construcción, eso va a la bitácora del módulo, no acá.

# Plan — `04` Proveedores (con la aprobación de `01`)

**Estado del plan:** Aprobado el 2026-09-30, con las respuestas registradas en `docs/DEUDA.md` · **Fecha:** 2026-09-30

Cubre la cola de correos (`CU-PRV-COL`): aprobar y reprocesar desde la pantalla. La aprobación
dispara la extracción de `CU-ALT-NOV`. Suma la verificación de `cancelarOperacion` en la
reactivación de proveedor.

El ciclo de monitoreo de la casilla (`CO-016`) queda fuera: depende de P-05. La extracción ya
existe y hoy se dispara con `manage.py extraer_novedades`. Ese comando se conserva como
herramienta de consola (R-01-002).

---

## 1. Qué cubre

| Caso de uso | Contratos | Operaciones de escritura | Operaciones de consulta |
| --- | --- | --- | --- |
| `CU-PRV-COL` | `CO-017`, `CO-019`, `CO-018`, `CO-157`, `CO-158` | 3 | 2 |
| `CU-ALT-NOV` | `CO-017`, `CO-019` (sin `CO-016`) | 2 | 0 |
| `CU-PRV-REA` | `CO-156` (sólo esta verificación) | 0 | 1 |

**Total: 6 contratos distintos.** `CU-ALT-NOV` no cierra en esta sesión porque `CO-016` sigue
fuera. Sí quedan verificados los dos contratos que comparte con `CU-PRV-COL`.

**Cambio de comportamiento visible.** La ficha de un correo *Pendiente de aprobación* ofrece
«Aprobar» y «Descartar». La de un correo *Procesado* o *Falló el procesamiento* ofrece
«Reprocesar». Las dos acciones terminan en el resumen: borradores generados, productos omitidos
por existir ya y reparos registrados.

**`CU-PRV-REA`.** Mismo caso que `CU-CAT-REA`: el `dss/DSS.md` vigente no muestra
`cancelarOperacion` y `CO-156` sí lo referencia. Se agrega la prueba de abandono. Se extiende a
`CU-PRV-BAJ`, que ya lo declaraba.

---

## 2. Conceptos que toca

| Concepto | ¿Existe? | Qué hace este módulo con él |
| --- | --- | --- |
| `CorreoProveedor` | Sí | Lo modifica: estado *En proceso*, `resuelto_por` y `resuelto_el` al aprobar |
| `BorradorProducto`, `ConfianzaCampo` | Sí | Los crea; en el reprocesamiento reemplaza sólo los abiertos |
| `RegistroAuditoria` | Sí | Usa «Generación de borradores desde un correo», que ya existe |

---

## 3. Ambigüedades detectadas

| # | Dónde | Las dos lecturas | Qué se necesita para destrabarla |
| --- | --- | --- | --- |
| 1 | `CO-017` E4 frente a `suppliers/services.py::extraer_novedades` | El contrato: si el modelo «no identifica ningún producto», el correo pasa a **Falló el procesamiento**. El código: si el modelo respondió y clasificó el correo como «otro» o encontró cero productos, lo marca **Procesado**, y lo justifica diciendo que un correo que no es de novedades es un resultado válido. **Es un desvío existente, anterior al contrato.** O se corrige el código, o se enmienda `CO-017` | Decisión del responsable. **Bloquea la prueba de `CO-017` E4** y con ella el cierre de `CU-PRV-COL` |
| 2 | `CO-019` con E4 | El reprocesamiento elimina los borradores abiertos y crea los nuevos. Si la nueva extracción falla, ¿los abiertos ya se eliminaron? **(a)** Se reemplazan sólo si la extracción tuvo éxito, en una sola transacción. **(b)** Se eliminan primero y el correo queda sin borradores. **Recomiendo (a)**: con (b), un corte del servicio borra trabajo sin reemplazarlo | Decisión del responsable |
| 3 | `CU-PRV-COL` paso 5: «ejecuta la extracción» | La extracción puede tardar hasta el tiempo de espera configurado. **(a)** Corre dentro de la petición, con el correo ya marcado *En proceso* y el indicador de carga visible. **(b)** Corre en segundo plano, lo que necesita un mecanismo de tareas, una decisión de la misma naturaleza que P-05. **Recomiendo (a)** | Confirmación |
| 4 | `CO-017` postcondición: «c.estado pasó de Pendiente de aprobación a En proceso y luego a Procesado» | Hoy el código no usa *En proceso* ni registra `resuelto_por` y `resuelto_el` al procesar. No hay ambigüedad: se construye | — |

---

## 4. Orden de construcción

| # | Qué | Depende de | Motivo |
| --- | --- | --- | --- |
| 1 | Pruebas de contrato de `CO-157`, `CO-158` y `CO-018` | Estilo preliminar | Ya construidos: se verifican primero, contra el contrato |
| 2 | `CO-017` desde la ficha, sin E4 | 1, ambigüedad 3 | Aprobación con transición atómica de Pendiente a En proceso |
| 3 | `CO-017` E1: dos administradores aprueban el mismo correo | 2 | Foco reforzado de concurrencia: bloqueo de la fila del correo |
| 4 | `CO-019` | 2, **ambigüedad 2** | Postcondición negativa: los borradores confirmados y rechazados no cambian |
| 5 | `CO-017` E4 | **Ambigüedad 1** | Si sigue abierta, `CU-PRV-COL` queda `Bloqueado` con ese motivo |
| 6 | `CO-156` en `CU-PRV-REA` y `CU-PRV-BAJ` | — | Prueba sola |

---

## 5. Riesgos

| Riesgo | Dónde aparece | Cómo se cubre |
| --- | --- | --- |
| La red en las pruebas | La extracción llama al modelo de lenguaje | Pasa por `core/integraciones.py`, que las pruebas interceptan. Ninguna prueba nueva sale a la red |
| Doble procesamiento | `CO-017` E1 | `select_for_update` sobre el correo y transición condicionada al estado. Prueba con dos aprobaciones sobre el mismo correo: una genera borradores, la otra informa el estado |
| Un corte del servicio a mitad de la extracción | `CO-017` E4, `CO-019` | El correo termina en *Falló el procesamiento*. En el reprocesamiento, los borradores abiertos siguen según la ambigüedad 2 |
| La petición supera el tiempo del servidor | Ambigüedad 3 | Se documenta en `docs/despliegue/` si se elige (a) |

---

## 6. Fuera de alcance

- `CO-016 ejecutarCicloMonitoreoCasilla`: depende de P-05.
- La pantalla de ingesta manual: la carga de `.eml` sigue siendo el comando `ingerir_correos`.
- `CU-PRV-BAJ`: la cifra de propuestas de restock sigue en «No disponible» hasta el módulo 05.
