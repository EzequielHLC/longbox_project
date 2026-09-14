# Bitácora — `NN` Nombre del módulo

> Registro de lo que se decidió construyendo este módulo. **Se anexa, no se reescribe.**
> Una entrada resuelta se marca; no se borra.
>
> Este archivo es el material que el responsable lee para decidir qué se enmienda en el documento
> de análisis. Escribí para alguien que conoce el dominio y no tiene el código a la vista.

---

## Cómo se escribe una entrada

Cuatro campos, en este orden. El cuarto es el que decide si el documento cambia.

| Campo | Qué responde | Cómo se escribe |
| --- | --- | --- |
| **Qué apareció** | El hecho concreto que obligó a decidir | Lo observable, no la conclusión. "Los correos de Ivrea anuncian una sola fecha para todo el envío" |
| **Qué dice la especificación** | La cita textual, o `Nada` | Citá. Si no podés citar, escribí `Nada` y ya sabés que es un agregado |
| **Qué se hizo** | La decisión tomada, en términos del dominio | Qué cambia para el usuario o para el dato. No cómo se implementó |
| **Qué habría que cambiar** | La enmienda concreta al documento | Señalá el artefacto y el punto. Si no hay que cambiar nada, `Nada` |

Tres cosas que **no** van en una entrada:

- **Cómo se implementó.** Un índice, un patrón, una consulta reescrita. Nada de eso toca la
  especificación y no hace falta que el responsable lo lea.
- **Estado o avance.** "Ya va el 60 % del módulo" vive en `docs/ESTADO.md`.
- **Conclusiones sin el hecho.** "Convenía separarlo" no se puede evaluar; "dos administradores
  revisando el mismo día producían un solo correo mezclado" sí.

**El tipo se declara, no se deduce.** `Agregado` cuando la especificación no dice nada, `Corrección`
cuando dice algo y está mal, `Desvío` cuando dice algo correcto y el código se aparta igual. Un
desvío se consulta **antes** de tomarlo, nunca se registra después.

---

## Entradas

### B-NN-001 · Título corto y descriptivo

**Tipo:** Agregado · **Fecha:** AAAA-MM-DD · **Alcance:** `CU-MOD-AAA`, `CO-NNN`
**Estado:** Abierta

**Qué apareció.**
El hecho concreto, observable, que obligó a tomar una decisión. Sin la conclusión todavía.

**Qué dice la especificación.**
> Cita textual del artefacto, con su identificador.

O bien: `Nada. La especificación no cubre este punto.`

**Qué se hizo.**
La decisión, en términos de lo que cambia para el usuario o para el dato.

**Qué habría que cambiar.**
El artefacto y el punto exacto. Por ejemplo: *"CO-019, campo Excepciones: agregar el caso de la
portada referenciada que no llega entre las partes del correo."* O `Nada`.

---

### B-NN-002 · Otra entrada

**Tipo:** Corrección · **Fecha:** AAAA-MM-DD · **Alcance:** `CU-MOD-AAA`
**Estado:** Resuelta — aplicada al documento el AAAA-MM-DD

**Qué apareció.**
…

**Qué dice la especificación.**
> …

**Qué se hizo.**
…

**Qué habría que cambiar.**
…

---

## Valores del campo Estado

| Valor | Significa |
| --- | --- |
| `Abierta` | Registrada, todavía no la miró el responsable |
| `En discusión` | El responsable la vio y está decidiendo |
| `Resuelta` | Se aplicó al documento, o se decidió no aplicarla. Anotá cuál de las dos y la fecha |
| `Descartada` | Se evaluó y no corresponde. Anotá por qué |