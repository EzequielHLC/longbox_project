> **Tipo: Normativo** una vez aprobado. Antes de la aprobación es una propuesta.
> Se escribe **antes** de programar y **no se reescribe** después: si algo cambió durante la
> construcción, eso va a la bitácora del módulo, no acá.

# Plan — `03` Pricing

**Estado del plan:** Propuesto · **Fecha:** 2026-09-22

Este plan cubre **la reconciliación de `CU-PVP-TAB` y `CU-PVP-MAR` contra sus contratos**. Los
otros cuatro casos de uso del módulo —`CU-PVP-ALT`, `CU-PVP-EDI`, `CU-PVP-BAJ` y `CU-PVP-CON`—
introducen el concepto `Oferta`, que no existe, y quedan fuera: ver el apartado 6.

**Reconciliar es escribir la prueba de contrato desde el contrato**, según
[`../pruebas/ESPECIFICACION.md`](../pruebas/ESPECIFICACION.md), apartado 3, y no releer el código
para confirmar que hace lo que hace. Lo que no cumpla se registra como desvío y se consulta; no se
arregla al pasar.

---

## 1. Qué cubre

| Caso de uso | Contratos | Operaciones de escritura | Operaciones de consulta |
| --- | --- | --- | --- |
| `CU-PVP-TAB` | `CO-047`, `CO-048`, `CO-049`, `CO-050`, `CO-051`, `CO-156`, `CO-166` | 3 | 4 |
| `CU-PVP-MAR` | `CO-052`, `CO-053`, `CO-156`, `CO-167` | 1 | 3 |

**Total: 9 contratos distintos.** `CO-156 cancelarOperacion` lo comparten los dos, y con otros
trece casos de uso del sistema.

`CO-005 confirmarPrecioManual` y `CO-031 revertirPrecioManual` **no** están en la lista y son
centrales para este módulo: pertenecen a `CU-ALT-NAC`, `CU-ALT-IMP` y `CU-CAT-EDI`, y su marca
`precio_manual` es lo que excluye a un producto de las dos propagaciones. Se prueban como
precondición montada, no como contrato de este módulo.

### Lo que hay construido hoy

| Contrato | Qué existe | Qué falta |
| --- | --- | --- |
| `CO-166 consultarTablaDePrecios` | El listado dentro de `ParametrosView` | Nada aparente. Falta la prueba |
| `CO-049 registrarCombinacion…` | `PrecioCrearView` + `PrecioReferenciaForm` | **La validación de posibilidad**: que el tipo sea del rubro editorial y que el formato esté declarado para ese tipo |
| `CO-047 solicitarModificacion…` | — | La pantalla no informa a cuántos productos alcanza |
| `CO-048 confirmarModificacion…` | `PrecioEditarView` guarda el PVP | **La propagación entera**, y el resumen |
| `CO-050 solicitarBajaDeCombinacion` | `PrecioEliminarView` (`GET`) | La cifra de cuántos productos la usan |
| `CO-051 confirmarBajaDeCombinacion` | `PrecioEliminarView` (`POST`), con `SET_NULL` | La postcondición negativa —el precio se conserva— no está probada |
| `CO-167 consultarMargenGlobal` | `ParametrosView` | Nada aparente. Falta la prueba |
| `CO-052 simularCambioDeMargen…` | — | Los dos números del impacto |
| `CO-053 confirmarCambioDeMargen…` | `ParametrosView` guarda el margen y audita | **El recálculo entero**, y el resumen |
| `CO-156 cancelarOperacion` | Los botones «Cancelar» | La prueba de que abandonar no deja rastro |

---

## 2. Conceptos que toca

| Concepto | ¿Existe? | Qué hace este módulo con él |
| --- | --- | --- |
| `TablaPrecioReferencia` | Sí | Lo crea, lo modifica y lo elimina |
| `ConfiguracionSistema` | Sí | Modifica `margen_ganancia` |
| `ProductoEditorial` | Sí | Modifica `Producto.precio` en lote; **nunca** `precio_base` |
| `Editorial`, `Tipo`, `Formato` | Sí | Sólo los lee, para validar la terna |
| `RegistroAuditoria` | Sí | Escribe una entrada por operación confirmada |
| `LineaCarrito` | **No** | Lo declaran `CO-048` y `CO-053`. No se simula — ver 3.1 |
| `Oferta` | **No** | Lo nombran las Notas de `CO-048`. No se simula — ver 3.1 |

Ninguna migración nueva. Los campos que las postcondiciones nombran —`pvp`, `actualizado_en`,
`precio_manual`, `precio_referencia`, `precio_base`, `margen_ganancia`— ya existen con esos
nombres.

**Falta una acción de auditoría.** `CO-048` declara la acción «Modificación de precio de
referencia» y `RegistroAuditoria` no la tiene: hoy las tres operaciones de la tabla se registran
como `PARAMETRO_MODIFICADO`. Es una migración de una línea, del mismo tipo que la de
`ALTA_ADMINISTRADOR_INICIAL`. La postcondición nombra la acción, así que sin ella `CO-048` no se
puede verificar como está declarado.

---

## 3. Ambigüedades detectadas

### 3.1 Lo que no puede cerrar antes de la cadena comercial

No es una ambigüedad sino una dependencia, y va primero porque determina el alcance de todo lo
demás.

`CO-048` y `CO-053` declaran, cada uno, una postcondición sobre `LineaCarrito`:

> «(c) Por cada `LineaCarrito` que refiera a uno de esos productos, precio vigente pasó al nuevo
> valor y la línea quedó marcada con el aviso de cambio de precio.»

`Carrito` y `LineaCarrito` son dos de los dieciocho conceptos planificados y pertenecen al módulo
`07` Tienda Online. **Esa mitad de los dos contratos no se construye ni se simula**: los dos casos
de uso quedan `Parcial` con la dependencia dicha, y la fila de `docs/ESTADO.md` la nombra.

Lo mismo con las Notas de `CO-048`: «las ofertas de tipo porcentaje sobre los productos afectados
se recalculan automáticamente sobre el nuevo precio base». `Oferta` no existe. Es una Nota y no
una postcondición, así que no bloquea la verificación; se deja anotado que cuando `Oferta` exista,
la propagación tiene que alcanzarla.

**Lo que sí cierra en este pase** es la propagación sobre productos, que es la parte grande y la
que el sistema ya puede sostener entera.

### 3.2 Ambigüedades que necesitan una decisión

| # | Dónde | Las dos lecturas | Qué se necesita para destrabarla |
| --- | --- | --- | --- |
| 1 | `CO-048` postcondición 2 | «Por cada `ProductoEditorial` **activo** asociado a esa combinación». ¿Qué es *activo*: el estado `Activo` estricto, o también Pre-venta? Un producto en Pre-venta está vinculado a su combinación y todavía no llegó, así que el precio nuevo es el que debería cobrarse. Con la lectura estricta, un lote entero en Pre-venta queda con el precio viejo y nadie se entera hasta que llega | Una decisión del responsable. Afecta también a la cifra de `CO-047`, que tiene que contar lo mismo que `CO-048` propaga |
| 2 | `CO-053` postcondición 2 | «Por cada `ProductoEditorial` **importado**». El contrato no dice *activo*, a diferencia de `CO-048`. ¿Es deliberado —el margen alcanza a todo importado, incluso descatalogado— o es una omisión y hay que leer *activo* igual que en `CO-048`? Recalcular el precio de un producto descatalogado no es inocuo: es el precio con el que figura en el historial | Una decisión del responsable. Las dos operaciones son hermanas y hoy se leen distinto |
| 3 | `CO-049` precondición | «El formato está declarado como aplicable a ese tipo». `Formato.tipos` vacío significa «se ofrece para todos los tipos» (está dicho en el modelo). ¿Una terna con un formato de lista vacía es válida? Por la semántica del campo, sí; por la letra de la precondición, no está dicho | Se puede resolver con la semántica del modelo, pero conviene que quede confirmado: es la regla que decide si un alta se acepta |
| 4 | `CU-PVP-TAB` A2 vs. `CO-051` | La baja de una fila es la **única eliminación física** del módulo. `CU-CFG-EDT` y `CU-CFG-TIP` dan de baja por casilla `activa`, y `CU-PVP-TAB` A2 borra. ¿Es deliberado? El contrato lo justifica bien —«los productos conservan su precio; lo que pierden es el vínculo»— pero la asimetría con el resto de los catálogos no está dicha en ninguna parte | Confirmación. Si es deliberado, no hay trabajo; si no, cambia el contrato |
| 5 | `CO-052` precondición | «Existe al menos un `ProductoEditorial` importado con precio base almacenado». ¿Qué pasa si no existe ninguno? ¿La operación se rechaza, o devuelve cero y cero? A1 cubre el caso de «todos tienen precio manual» y dice que el margen se actualiza igual; el caso de «no hay ninguno» no está cubierto y es el estado de una instalación nueva | Una decisión del responsable. La lectura razonable es que se comporte como A1, pero el contrato no lo dice |

**Ninguna de las cinco bloquea el módulo entero.** Las dos primeras bloquean `CO-047`/`CO-048` y
`CO-052`/`CO-053` respectivamente, que son el corazón de cada caso de uso: si no se destraban, lo
que se puede construir es el resto y los dos quedan `Parcial` por otra razón que la del 3.1.

---

## 4. Orden de construcción

| # | Qué | Depende de | Motivo |
| --- | --- | --- | --- |
| 1 | Pruebas de contrato de las cuatro operaciones de consulta y de `CO-156` | Nada | Son las baratas y las que fijan el andamio de fixtures que usan todas las demás. `CO-156` es postcondición vacía: se ejerce el `GET`, se abandona y se afirma que no cambió nada ni se auditó |
| 2 | `CO-049` y `CO-051`: la validación de posibilidad y la postcondición negativa de la baja | 1 | No dependen de ninguna ambigüedad abierta salvo la 3, que es acotada. `CO-051` trae la postcondición negativa explícita —«Producto.precio conservó su valor»—, de las que se rompen sin que nadie las mire |
| 3 | La acción de auditoría «Modificación de precio de referencia» | Nada | Es la migración, y `CO-048` la necesita para poder verificarse |
| 4 | `CO-047` + `CO-048`: el par solicitar/confirmar con propagación | 1, 2, 3, **ambigüedad 1** | Es el trabajo grande de `CU-PVP-TAB`. El informe de alcance y la propagación tienen que contar y tocar exactamente el mismo conjunto, así que se construyen juntos |
| 5 | `CO-052` + `CO-053`: el par del margen con recálculo | 1, **ambigüedades 2 y 5** | Mismo patrón que 4, sobre `precio_base` en vez de sobre la tabla |

Los pasos 4 y 5 son el mismo patrón dos veces —informar el alcance, confirmar, propagar, auditar,
resumir— y comparten la regla de exclusión de `CO-005`. Se construye una vez la forma de contar y
propagar, con la fuente del precio como el único parámetro que cambia.

---

## 5. Riesgos

| Riesgo | Dónde aparece | Cómo se cubre |
| --- | --- | --- |
| **Aritmética decimal** | `CO-053`: `precio = precio_base × (1 + margen)` | `Decimal` en todo el camino, nunca punto flotante, y redondeo a la unidad monetaria al final. Ya es la regla de `catalog/precios.py`; la prueba la afirma sobre valores que delatan el error, no sobre redondos |
| **`precio_base` no se toca** | `CO-053` lo declara explícitamente | Postcondición negativa: se captura el valor antes, se afirma igual después. Es la que sostiene que recalcular indefinidamente no acumule error |
| **El informe y la propagación cuentan distinto** | `CO-047` dice N y `CO-048` toca M | Una sola consulta compartida por los dos, y una prueba que afirma que el resumen de `CO-048` devuelve el mismo número que informó `CO-047` sobre el mismo estado |
| **La exclusión por precio manual** | `CO-048` y `CO-053`, vía `CO-005` | Prueba con tres productos: uno vinculado, uno con `precio_manual`, uno de otra combinación. Se afirma que cambió el primero y que los otros dos no. El segundo es el que se rompe sin que nadie lo note |
| **Propagación sobre volumen** | `CO-048` toca todos los productos de una combinación; `CO-053`, todos los importados | Un `update()` de queryset y no un bucle de `save()`. Tiene una consecuencia que hay que decir: `update()` no llama a `save()` ni a `full_clean()`, así que **esquiva I-09** —ningún precio cero ni negativo— igual que cualquier otro camino que no pase por el formulario. Ver 5.1 |
| **Concurrencia** | Dos administradores cambiando el margen a la vez | `select_for_update()` sobre `ConfiguracionSistema`, que es una fila única. La prueba provoca la carrera y afirma que el resultado es uno de los dos estados válidos y nunca una mezcla |

### 5.1 I-05, I-06, I-09 e I-12 por cualquier camino de escritura

`docs/DEUDA.md` registra que las cuatro viven en `clean()` o en un validador y que sólo las
respeta el camino que pasa por un `ModelForm`. Este módulo es el que más presión les pone: la
propagación escribe precios en lote, sin formulario.

**La propuesta es cerrar I-09 en la base, con una `CheckConstraint`.** Es la única de las cuatro
que este módulo toca, y es la única que toca dinero: hoy nada impide un
`Producto.objects.update(precio=0)`. Una restricción sobre `precio > 0` la hace valer por
cualquier camino —el `update()` de la propagación incluido— y convierte en error lo que hoy sería
un catálogo con precios en cero sin ningún síntoma.

I-05, I-06 e I-12 no las toca este módulo y quedan donde están; su cierre pertenece a los planes
de los módulos 02 y 13.

### 5.2 P-05, el mecanismo de procesos periódicos

**No hace falta en este módulo y no se propone acá.** Se deja dicho para que no se lo busque:
ninguna de las nueve operaciones de `CU-PVP-TAB` y `CU-PVP-MAR` la dispara el Temporizador. Las
dos propagaciones son sincrónicas y las inicia el Administrador.

`docs/DEUDA.md` lo lista como decisión transversal abierta y nombra lo que bloquea: el ciclo de
`CO-016`, el ciclo de `CO-155`, `CU-ALT-TRA`, `CU-RST-NOT`, `CU-PTS-CAD` y `CU-STK-VEN`. **El
primer plan que lo necesita es el del módulo 01**, y ahí va la propuesta.

Lo único que este plan adelanta es el criterio con el que se va a proponer, porque la propagación
de `CO-048` ya lo roza: una operación larga disparada a mano y una disparada por reloj comparten
el problema de no poder ejecutarse dos veces sobre el mismo estado. La forma de contar y propagar
que se construye acá se escribe **idempotente** —repetirla con la misma entrada deja el sistema
igual— para que el mecanismo que se elija después no tenga que rehacerla.

---

## 6. Fuera de alcance

- **`CU-PVP-ALT`, `CU-PVP-EDI`, `CU-PVP-BAJ` y `CU-PVP-CON`.** Los cuatro giran alrededor de
  `Oferta`, que es un concepto planificado. Son 11 contratos que no se pueden empezar.
- **La propagación a los carritos**, de `CO-048` y `CO-053`. Depende de la cadena comercial y no
  se simula. Los dos casos de uso quedan `Parcial` con la dependencia dicha.
- **El recálculo de ofertas porcentuales** que nombran las Notas de `CO-048`. Mismo motivo.
- **Las cifras de impacto que dependen de módulos no construidos.** No aparecen en este módulo:
  las dos de `CO-047` y `CO-052` se calculan enteras sobre conceptos que existen. Se dice para que
  no se busque el equivalente del `None` de `ImpactoDeBaja`.
- **La separación de los casos de uso «Gestionar» y «Administrar»** en alta, baja y modificación.
  No toca a este módulo: `CU-PVP-TAB` ya viene separado en operaciones y este plan se organiza por
  contrato.
- **`CO-219`**, el tablero del Administrador. No está en `.contexto-ia/` y no se escriben pruebas
  contra él.

---

## 7. Condición de cierre

El módulo cierra cuando los 9 contratos tienen prueba que verifica sus postcondiciones, **con dos
excepciones declaradas**: la mitad de `CO-048` y la de `CO-053` que hablan de `LineaCarrito`.

`CU-PVP-TAB` y `CU-PVP-MAR` quedan entonces **`Parcial`**, no `Verificado`, y la observación de
`docs/ESTADO.md` dice exactamente qué falta y de qué depende. Un caso de uso que depende de un
concepto que no existe no se declara terminado porque lo construible esté hecho.
