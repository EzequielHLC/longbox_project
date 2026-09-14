> **Tipo: Normativo** una vez aprobado. Antes de la aprobación es una propuesta.
> Se escribe **antes** de programar y **no se reescribe** después: si algo cambió durante la
> construcción, eso va a la bitácora del módulo, no acá.

# Plan — `NN` Nombre del módulo

**Estado del plan:** Propuesto · **Fecha:** AAAA-MM-DD

---

## 1. Qué cubre

Los casos de uso del módulo y los contratos de cada uno. Esta tabla es la que permite verificar el
cierre: al terminar, o están todos, o el caso de uso quedó parcial y se sabe exactamente qué falta.

| Caso de uso | Contratos | Operaciones de escritura | Operaciones de consulta |
| --- | --- | --- | --- |
| `CU-MOD-AAA` | `CO-001` a `CO-006` | 4 | 2 |

**Total del módulo:** — contratos.

---

## 2. Conceptos que toca

Del modelo de dominio. Distinguir los que ya existen de los que este módulo introduce, porque los
segundos traen migración y suelen ser el trabajo más pesado.

| Concepto | ¿Existe? | Qué hace este módulo con él |
| --- | --- | --- |
| — | Sí / No | Lo crea · Lo modifica · Sólo lo lee |

---

## 3. Ambigüedades detectadas

**Este es el punto del plan.** Encontrarlas ahora, cuando decidirlas es barato, y no cuando ya
quedaron resueltas por omisión dentro de una función.

Una ambigüedad es un punto donde la especificación admite dos lecturas que producen sistemas
distintos. No es una duda de implementación.

| # | Dónde | Las dos lecturas | Qué se necesita para destrabarla |
| --- | --- | --- | --- |
| 1 | `CU-MOD-AAA` paso N | … / … | Una decisión del responsable |

**Si una ambigüedad bloquea un caso de uso completo, decilo acá.** Es preferible construir el resto
del módulo y dejar ese caso de uso pendiente, a resolverla por cuenta propia.

---

## 4. Orden de construcción

Los casos de uso en el orden en que se van a implementar, y por qué ese orden. Normalmente lo
dictan las dependencias: lo que crea un concepto va antes de lo que lo consulta.

| # | Caso de uso | Depende de | Motivo |
| --- | --- | --- | --- |
| 1 | — | — | — |

---

## 5. Riesgos

Lo que puede salir mal y no es una ambigüedad de la especificación. Concurrencia, volumen,
integraciones externas, migraciones sobre datos existentes.

| Riesgo | Dónde aparece | Cómo se cubre |
| --- | --- | --- |
| — | — | — |

---

## 6. Fuera de alcance

Lo que alguien podría esperar de este módulo y **no** va a estar. Decirlo evita que se descubra al
cerrar.

- —