# Bitácora — `02` Catálogo

> Registro de lo que se decidió construyendo este módulo. **Se anexa, no se reescribe.**
> Una entrada resuelta se marca; no se borra.
>
> Este archivo es el material que el responsable lee para decidir qué se enmienda en el documento
> de análisis. Escribí para alguien que conoce el dominio y no tiene el código a la vista.

---

## Entradas

### B-02-001 · La reactivación de producto se construyó declarándola fuera de todo caso de uso

**Tipo:** Agregado · **Fecha:** 2026-09-14 · **Alcance:** `CU-CAT-REA`, `CO-035`, `CO-036`
**Estado:** Resuelta — comentario vencido; corregido el código el 2026-09-22

**Qué apareció.**
`ProductoReactivarView` y su plantilla llevan escrito, en el docstring y en el encabezado del
archivo, que ningún caso de uso describe la reactivación y que se agregó porque sin ella la baja
es un camino de ida. El esquema vigente sí la describe: `CU-CAT-REA` · Reactivar Producto
Descatalogado, con dos contratos propios, `CO-035 solicitarReactivacionDeProducto` y
`CO-036 confirmarReactivacionDeProducto`.

Desde el repositorio no se puede determinar cuál de las dos cosas pasó: si el caso de uso se
incorporó al documento después de que la pantalla existiera, o si ya estaba y el comentario nunca
fue cierto. El historial de git cubre el código, no las versiones del documento de análisis.

**Qué dice la especificación.**
> `CU-CAT-REA` · Reactivar Producto Descatalogado — 02 Catálogo.

Existe, con ficha y con dos contratos. Lo que la especificación no dice es si el flujo construido
coincide con el que la ficha describe: la pantalla actual pide una confirmación y reactiva, y
`CO-035`/`CO-036` declaran un par solicitar/confirmar cuyas postcondiciones nadie comparó todavía
contra lo que la vista hace.

**Qué se hizo.**
Nada sobre el comportamiento. Se registró la discrepancia entre lo que el código afirma sobre sí
mismo y lo que el documento contiene hoy.

**Qué habría que cambiar.**
En el documento, probablemente nada. Lo que hace falta es confirmar que lo construido cumple
`CO-035` y `CO-036` —es una de las verificaciones de contrato que están pendientes— y, hecho eso,
borrar del código la afirmación de que ningún caso de uso la describe. Mientras esa frase siga
ahí, el próximo que lea la vista va a creerle.

---

### B-02-002 · El modelo declara la unicidad insensible a mayúsculas en dos catálogos, y el código la aplica en los cinco

**Tipo:** Corrección · **Fecha:** 2026-09-14 · **Alcance:** `CU-CAT-ETQ`, `CU-CFG-TIP`, `CU-CFG-EDT`
**Estado:** Resuelta — con enmienda pendiente al documento, decidida el 2026-09-22

**Qué apareció.**
`MODELO_DE_DOMINIO.md`, Área 2, califica la unicidad del nombre de cada catálogo de clasificación
de cinco maneras distintas:

| Concepto | Lo que declara el modelo | Lo que aplica el código |
| --- | --- | --- |
| `Editorial` | «único, sin distinguir mayúsculas» | `UniqueConstraint(Lower("nombre"))` |
| `Tipo` | «único, sin distinguir mayúsculas» | `UniqueConstraint(Lower("nombre"))` |
| `Formato` | «único» | `UniqueConstraint(Lower("nombre"))` |
| `GrupoEtiqueta` | «único» | `UniqueConstraint(Lower("nombre"))` |
| `Etiqueta` | «único dentro del grupo» | `UniqueConstraint(Lower("nombre"), "grupo")` |

El código es **más estricto** que el modelo en tres de los cinco: «Rústica» y «rústica» son el
mismo formato para el sistema, y el modelo no dice que lo sean.

No es una divergencia accidental. El commit `b71bce9` —«la regla de nombres de catálogo valía en
tres de los cinco»— la unificó a propósito en el código. Lo que no se hizo en su momento fue
llevarla al documento, y por eso hoy el documento conserva la regla vieja justo invertida: dice la
regla estricta en los dos que ya la tenían y la omite en los tres que se corrigieron.

**Qué dice la especificación.**
> `Formato` — «nombre : texto «único»»
> `GrupoEtiqueta` — «nombre : texto «único»»
> `Etiqueta` — «nombre : texto «único dentro del grupo»»

Y el invariante correspondiente:

> I-08 — «Una etiqueta es única dentro de su grupo, no en todo el catálogo»

I-08 tampoco menciona las mayúsculas.

**Qué se hizo.**
Los cinco catálogos comparan el nombre en minúsculas. Para quien carga, la consecuencia es que
cargar «Tapa Dura» cuando ya existe «tapa dura» se rechaza como duplicado en vez de crear un
segundo formato que se lee igual y no lo es.

**Qué habría que cambiar.**
`MODELO_DE_DOMINIO.md`, Área 2: agregar «sin distinguir mayúsculas» a `Formato`, `GrupoEtiqueta` y
`Etiqueta`. Y I-08, para que diga que la unicidad dentro del grupo tampoco distingue mayúsculas.
Es una enmienda de redacción, pero de la clase que importa: es la regla que decide si un alta se
acepta o se rechaza, y hoy el documento describe un sistema más permisivo que el que existe.

---

## Resoluciones

> Lo que el responsable decidió sobre cada entrada, con la fecha y con qué se hizo en
> consecuencia. **La entrada original no se toca**: sólo se le marca el estado. Una enmienda
> declarada «pendiente» manda sobre el texto que hoy está volcado en `.contexto-ia/`, que no se
> edita a mano y se actualiza recién cuando el documento de análisis cambie.

### R-02-001 · Resolución de B-02-001

**Fecha:** 2026-09-22 · **Enmienda al documento:** ninguna

**Qué se decidió.**
La pregunta que la entrada no podía responder desde el repositorio —si el caso de uso se agregó
después o si el comentario nunca fue cierto— la responde el responsable: **`CU-CAT-REA` se
incorporó al documento el 05/09**, después de que la pantalla existiera. El comentario fue cierto
cuando se escribió y dejó de serlo ese día.

No es entonces una discrepancia entre código y documento sino un **comentario vencido**, y se
corrige sin más.

**Qué se hizo.**
Se sacó de `ProductoReactivarView`, de su plantilla y de `test_baja_producto.py` la afirmación de
que ningún caso de uso la describe, reemplazada por la referencia a `CU-CAT-REA` y a sus dos
contratos, `CO-035` y `CO-036`.

Lo que **no** cambió es el estado de verificación: que el caso de uso exista no dice que lo
construido cumpla el par solicitar/confirmar. Esa comparación sigue pendiente y es trabajo del
plan del módulo 02.

---

### R-02-002 · Resolución de B-02-002

**Fecha:** 2026-09-22 · **Enmienda al documento:** pendiente

**Qué se decidió.**
**Manda la regla del código.** Los cinco catálogos de clasificación —`Editorial`, `Tipo`,
`Formato`, `GrupoEtiqueta` y `Etiqueta`— comparan el nombre sin distinguir mayúsculas. Es la regla
correcta: «Rústica» y «rústica» son el mismo formato, y el documento describe hoy un sistema más
permisivo que el que existe.

**Enmienda pendiente.**
`MODELO_DE_DOMINIO.md`, Área 2: agregar «sin distinguir mayúsculas» a `Formato`, `GrupoEtiqueta` y
`Etiqueta`. E `I-08`, para que la unicidad dentro del grupo tampoco distinga mayúsculas.

**Qué se hizo.**
Nada. **No hay trabajo de código**: el código ya aplica la regla que se adopta, en los cinco.

---

### B-02-003 · Las etiquetas de un grupo se paginan de a cincuenta

**Tipo:** Agregado · **Fecha:** 2026-10-02 · **Alcance:** `CU-CAT-ETC`, `CO-165`
**Estado:** Abierta — anunciado en el plan 02, ambigüedad 3, sin objeción

**Qué apareció.**
El listado de etiquetas de un grupo tiene que paginarse y el contrato no dice el tamaño de
página.

**Qué dice la especificación.**
> «El listado se presenta paginado y con búsqueda por texto.» (`CO-165`, Responsabilidades)

**Qué se hizo.**
Cincuenta por página, el tamaño que `CO-205` declara para el log de auditoría. La búsqueda y el
filtro por estado se conservan al cambiar de página.

**Qué habría que cambiar.**
`CO-165`, Notas: «de a 50 etiquetas por página».

---

### B-02-004 · Los contratos sobre los filtros del catálogo público quedan parciales

**Tipo:** Agregado · **Fecha:** 2026-10-02 · **Alcance:** `CO-039`, `CO-041`, `CO-043`, `CO-045`
**Estado:** Abierta — recomendación del plan aplicada (consulta C-13)

**Qué apareció.**
Cuatro contratos de grupos y etiquetas afirman que algo «dejó de ofrecerse» o «volvió a
ofrecerse» en los filtros del catálogo público, que no existe hasta `CU-TDA-CAT`.

**Qué dice la especificación.**
> «El grupo y sus etiquetas dejaron de ofrecerse en los formularios de alta y edición de producto
> y en los filtros del catálogo público.» (`CO-041`, Postcondiciones)

**Qué se hizo.**
Las pruebas afirman sobre la única función que decide qué etiquetas se ofrecen, la que usan los
formularios. Esa parte de la postcondición queda sin verificar hasta que el catálogo público
exista y la use.

**Qué habría que cambiar.**
Nada.

---

### Nota de cierre · 2026-10-02

Grupos y etiquetas se operan con la misma maquinaria que los catálogos del módulo 17: listado
con filtro por estado, alta, modificación que reactiva y baja en dos tiempos. La pantalla de
etiquetas pasó a ser dos (grupos, y etiquetas de un grupo). El inventario exporta a CSV y filtra
por editorial. Queda: los filtros del catálogo público (B-02-004) y las pruebas de contrato de la
edición, la baja y la reactivación de producto (`CO-030` a `CO-036`).
