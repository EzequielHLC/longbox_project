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
**Estado:** Abierta

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
**Estado:** Abierta

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
