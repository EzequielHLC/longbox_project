> **Tipo: Normativo** una vez aprobado. Antes de la aprobación es una propuesta.
> Se escribe **antes** de programar y **no se reescribe** después: si algo cambió durante la
> construcción, eso va a la bitácora del módulo, no acá.

# Plan — `11` Cuenta de Cliente

**Estado del plan:** Aprobado el 2026-09-30, con las respuestas registradas en `docs/DEUDA.md` · **Fecha:** 2026-09-30

Primer plan del módulo. Esta sesión cubre sólo la consulta del padrón por el Administrador
(`CU-CLI-CON`). El resto del módulo depende del panel del Cliente o de Pedido.

---

## 1. Qué cubre

| Caso de uso | Contratos | Operaciones de escritura | Operaciones de consulta |
| --- | --- | --- | --- |
| `CU-CLI-CON` | `CO-194`, `CO-195` | 0 | 2 |

**Total: 2 contratos.** El listado de `CO-194` existe (`ClienteListaView`) y se verifica contra
el contrato. La ficha de `CO-195` no existe y se construye: identificación, contacto, domicilio,
estado, fecha de registro y fecha de aceptación de la política de privacidad, **sin ninguna
acción**. Cada fila del listado enlaza a la ficha.

---

## 2. Conceptos que toca

| Concepto | ¿Existe? | Qué hace este módulo con él |
| --- | --- | --- |
| `Usuario` con rol Cliente | Sí | Sólo lo lee |

---

## 3. Ambigüedades detectadas

| # | Dónde | Las dos lecturas | Qué se necesita para destrabarla |
| --- | --- | --- | --- |
| 1 | `CO-195`: «identificación» | La cuenta de Cliente no guarda documento. **(a)** Identificación es nombre y apellido. **(b)** Falta un dato. **Recomiendo (a)**: `CO-107` no pide documento en el alta | Nada, salvo objeción |
| 2 | `CO-195`: sin acciones de modificación | La ficha no ofrece ninguna acción, ni siquiera un enlace a otra pantalla que modifique. La prueba lo afirma sobre el HTML de la respuesta: no hay formularios ni enlaces a direcciones de escritura | — |

---

## 4. Orden de construcción

| # | Qué | Depende de | Motivo |
| --- | --- | --- | --- |
| 1 | Prueba de contrato de `CO-194`, con acceso por la dirección real con rol Cajero y Cliente | Estilo preliminar | Ya construido |
| 2 | Ficha de `CO-195` con su prueba | 1 | Datos personales (Ley 25.326): la restricción se prueba en el servidor |

---

## 5. Riesgos

| Riesgo | Dónde aparece | Cómo se cubre |
| --- | --- | --- |
| La ficha abierta a otro rol | `CO-195` | Prueba por la dirección real con Cajero, Cliente y sin sesión |
| La ficha muestra una cuenta de personal | La dirección recibe un identificador de `Usuario` | La vista filtra por rol Cliente; con una cuenta de personal responde 404. Con prueba |

---

## 6. Fuera de alcance

`CU-CLI-DAT`, `CU-CLI-HIS` y `CU-CLI-BAJ`.
