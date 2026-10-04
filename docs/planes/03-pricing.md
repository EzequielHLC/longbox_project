> **Tipo: Normativo** una vez aprobado. Antes de la aprobación es una propuesta.
> Se escribe **antes** de programar y **no se reescribe** después: si algo cambió durante la
> construcción, eso va a la bitácora del módulo, no acá.

# Plan — `03` Pricing

**Estado del plan:** Aprobado el 2026-09-30, con las respuestas registradas en `docs/DEUDA.md` · **Fecha:** 2026-09-30

Reemplaza la propuesta del 2026-09-22, que no llegó a aprobarse y estaba escrita sobre
`CU-PVP-TAB`, un código que ya no existe. Tres de sus cinco ambigüedades las resolvió el documento
reestructurado: `CO-048` excluye ahora a los productos «Cancelado por editorial», `CO-049` nombra
«aplica a todos los tipos» y `CO-051` justifica la eliminación de la fila.

Cubre la tabla de precios de referencia y el margen global de importados. Las ofertas
(`CU-PVP-ALT` a `CON`) son de la etapa B.

---

## 1. Qué cubre

| Caso de uso | Contratos | Operaciones de escritura | Operaciones de consulta |
| --- | --- | --- | --- |
| `CU-PVP-TBC` | `CO-166` | 0 | 1 |
| `CU-PVP-TBA` | `CO-049`, `CO-031`, `CO-166` | 2 | 1 |
| `CU-PVP-TBM` | `CO-047`, `CO-048`, `CO-156`, `CO-166` | 1 | 3 |
| `CU-PVP-TBB` | `CO-050`, `CO-051`, `CO-031`, `CO-156`, `CO-166` | 2 | 3 |
| `CU-PVP-MAR` | `CO-052`, `CO-053`, `CO-156`, `CO-167` | 1 | 3 |

**Total: 11 contratos distintos.** `CO-031 restaurarPrecioCalculado` se invoca desde la edición de
producto (`CU-CAT-EDI` A2), pero sin él la promesa de `CO-051` —«pueden vincularse otra vez»— no
tiene camino. Se construye acá, y con él queda completo también `CU-CAT-EDI`.

**Cambio de comportamiento visible.**

- La tabla sale de la pantalla de parámetros a una pantalla propia, con filtros por editorial,
  tipo y formato.
- Modificar un precio pasa a ser un par: el sistema informa cuántos productos alcanza, pide
  confirmación y propaga el precio. La leyenda «cambiarlo acá no toca los productos ya cargados»
  deja de ser cierta y se quita.
- El margen deja de editarse en la pantalla de parámetros, como pide `CU-CFG-PAR` A1. Tiene su
  pantalla: valor vigente, simulación del impacto, confirmación y resumen.
- En la ficha de un producto editorial sin vínculo aparece «Restaurar precio calculado», con el
  precio recalculado a la vista antes de guardar.

**La propagación a carritos queda pendiente.** `CO-048` y `CO-053` declaran una postcondición
sobre `LineaCarrito`, que no existe. Se anota como tal en la bitácora, y los dos contratos
cierran como **parciales** hasta que exista `Carrito`. Con ellos, `CU-PVP-TBM` y `CU-PVP-MAR`.

---

## 2. Conceptos que toca

| Concepto | ¿Existe? | Qué hace este módulo con él |
| --- | --- | --- |
| `TablaPrecioReferencia` | Sí | Lo modifica |
| `ProductoEditorial` | Sí | Modifica `precio`, `precio_manual` y el vínculo `precio_referencia`. **Nunca `precio_base`** |
| `ConfiguracionSistema` | Sí | Modifica el margen global |
| `LineaCarrito` | **No** | Nada. Ver arriba |
| `Oferta` | **No** | Nada. «Las ofertas de tipo porcentaje se recalculan» (`CO-048`) no tiene sobre qué actuar |
| `RegistroAuditoria` | Sí | Suma la acción «Modificación de precio de referencia», ya declarada en el modelo (INC-06) |

---

## 3. Ambigüedades detectadas

| # | Dónde | Las dos lecturas | Qué se necesita para destrabarla |
| --- | --- | --- | --- |
| 1 | `CO-053` postcondición 2 frente a `CO-048` postcondición 2 | `CO-048` excluye a los productos «Cancelado por editorial». `CO-053` recalcula **todo** importado con precio vinculado, en cualquier estado. **(a)** Es deliberado y el margen alcanza también a los cancelados. **(b)** Es una omisión y se excluyen igual que en `CO-048`. Recalcular el precio de un producto cancelado cambia el precio con el que figura en el historial. **Recomiendo (b)** | Decisión del responsable. La cifra de `CO-052` tiene que contar lo mismo que `CO-053` recalcula |
| 2 | `CO-052` y `CU-PVP-MAR`, precondición: «existe al menos un producto importado con precio base» | En una instalación nueva no hay ninguno, y con la letra de la precondición el margen no se podría cambiar nunca. **(a)** Se comporta como A1: informa que no afecta a ningún producto y el margen se actualiza igual. **(b)** Se rechaza. **Recomiendo (a)** | Decisión del responsable |
| 3 | `CO-049` y `CO-051`: «entrada en el registro de auditoría de la operación» | Sólo `CO-048` nombra su acción. ¿El alta y la baja de una fila usan también «Modificación de precio de referencia»? Es la ambigüedad 4 del plan 17 | Misma decisión. No bloquea |
| 4 | `CO-049` precondición: «el formato … tiene aplica a todos los tipos = sí» | Depende de la ambigüedad 1 del plan 17. Mientras siga abierta, se valida con la regla actual, la lista vacía | La misma decisión. No bloquea `TBA`, pero su prueba cambia si se adopta el atributo |

---

## 4. Orden de construcción

| # | Caso de uso | Depende de | Motivo |
| --- | --- | --- | --- |
| 1 | `CU-PVP-TBC` | Estilo preliminar | Consulta con tres filtros. Fija la pantalla |
| 2 | `CU-PVP-TBA` | 1, plan 17 tanda 1 | Suma la validación de rubro editorial y el aviso con enlace a la fila existente |
| 3 | `CO-031` | — | Lo necesitan `TBB` y `CU-CAT-EDI`. Es dinero: redondeo al peso con la función existente |
| 4 | `CU-PVP-TBB` | 3 | Postcondición negativa explícita: el precio se conserva y `precio_manual` no cambia |
| 5 | `CU-PVP-TBM` | 1 | El informe y la propagación cuentan y tocan el mismo conjunto: una sola consulta para los dos |
| 6 | `CU-PVP-MAR` | **Ambigüedades 1 y 2** | El margen sale de `ParametrosView`. Si alguna sigue abierta, queda `Bloqueado` y se sigue con el 04 |

---

## 5. Riesgos

| Riesgo | Dónde aparece | Cómo se cubre |
| --- | --- | --- |
| Error de redondeo en la propagación | `CO-053`: precio base × (1 + margen) | `Decimal` de punta a punta, el margen con sus cuatro decimales y redondeo al peso sólo en el resultado. Prueba con valores que distinguen redondear antes de redondear después |
| `precio_base` modificado sin querer | `CO-053`, postcondición negativa | La prueba afirma `precio_base` antes y después en cada producto recalculado |
| Un producto con precio a mano alcanzado por la propagación | `CO-048`, `CO-053` | Prueba con un producto `precio_manual = sí` en la misma combinación y con el mismo margen: su precio no cambia |
| Un alta de lote importado mientras cambia el margen | `CO-053` frente a `CO-009` | Bloqueo de la fila única de `ConfiguracionSistema` durante el recálculo. Prueba de concurrencia |
| El informe cuenta distinto de lo que se propaga | `CO-047` y `CO-048`, `CO-052` y `CO-053` | Un solo queryset para cada par. La prueba compara la cifra informada con la cantidad efectivamente actualizada |

---

## 6. Fuera de alcance

- La propagación a `LineaCarrito`: cuando exista `Carrito`.
- El recálculo de ofertas de tipo porcentaje: cuando exista `Oferta`.
- `CU-PVP-ALT`, `EDI`, `BAJ` y `CON`: etapa B.
- El vencimiento automático de ofertas (`CO-059`, `CU-PVP-VEN`): sin ficha y dependiente de P-05.

---
---

# Plan — `03` Pricing · segunda parte: ofertas

**Estado del plan:** Aprobado el 2026-10-03, con las recomendaciones de la sección 3 · **Fecha:** 2026-10-03

Segunda parte del plan del módulo. La primera, de arriba, está aprobada y no se toca. Ésta cubre
las ofertas y se construye **después** del carrito (plan 07, segunda parte), porque cada contrato
de oferta termina actualizando las líneas de carrito.

---

## 1. Qué cubre

| Caso de uso | Contratos | Operaciones de escritura | Operaciones de consulta |
| --- | --- | --- | --- |
| `CU-PVP-CON` | `CO-169`, `CO-170` | 0 | 2 |
| `CU-PVP-ALT` | `CO-054`, `CO-055` | 2 | 0 |
| `CU-PVP-EDI` | `CO-168`, `CO-056` | 1 | 1 |
| `CU-PVP-BAJ` | `CO-057`, `CO-058`, `CO-156` | 1 | 2 |
| Sin caso de uso | `CO-059 ejecutarCicloDeVigenciaDeOfertas` | 1 | 0 |
| `CU-TDA-CAT` (cierre) | El precio tachado de `CO-176` y `CO-177` | — | — |

**Total: 10 contratos distintos**, de los cuales `CO-156` ya está verificado en otros casos de uso
y se ejerce acá de nuevo.

---

## 2. Conceptos que toca

| Concepto | ¿Existe? | Qué hace este plan con él |
| --- | --- | --- |
| `Oferta` | **No** | La crea, con los siete atributos del modelo y sus dos alcances (`Producto` o `Tipo`) |
| `Producto` | Sí | Lo lee. **Su precio guardado no cambia**: la oferta modifica el precio *visible*, que se calcula |
| `Tipo` | Sí | Alcance de una oferta por tipo de material |
| `LineaCarrito` | La crea el plan 07 | Su precio vigente se actualiza con cada cambio de oferta |
| `RegistroAuditoria` | Sí | Cuatro acciones nuevas: alta, modificación, baja y vencimiento automático de oferta |

---

## 3. Ambigüedades detectadas

| # | Dónde | Las dos lecturas | Qué se necesita para destrabarla |
| --- | --- | --- | --- |
| 1 | `CO-059` y **P-05**: no existe forma de disparar las operaciones del Temporizador | **(a)** El precio visible se calcula con las fechas en cada consulta, así que una oferta empieza y termina **a tiempo aunque nada corra**. El cambio de estado guardado y la entrada de auditoría los hace un comando, `manage.py ejecutar_temporizador`, que corre al arrancar `demostracion.bat` y que se puede programar en el Programador de tareas de Windows. Queda como la puerta única de todos los procesos periódicos que vengan. **(b)** Sólo el comando: si no corre, la oferta no empieza ni termina | **Recomiendo (a)**. Cierra P-05 para las ofertas y deja la puerta para los otros ocho procesos |
| 2 | «Fecha de vencimiento alcanzada» (`CO-059`) frente a «fecha de inicio ≤ fecha de vencimiento» (`CO-054`) | **(a)** El día de vencimiento **incluido**: la oferta vence al terminar ese día. **(b)** Excluido: vence al empezar ese día. Con (b), una oferta con inicio igual a vencimiento, que el contrato admite, no estaría activa nunca | **Recomiendo (a)** |
| 3 | Un producto con una oferta individual **y** una de su tipo, las dos activas. I-20 sólo prohíbe el solapamiento «sobre el mismo alcance» | **(a)** Manda la individual, por ser la más específica. **(b)** Manda la que deja el precio más bajo. **(c)** Se prohíbe el solapamiento cruzado | Decisión. **Recomiendo (a)**: es predecible para el Administrador y la ficha de la oferta puede mostrar qué productos quedan tapados |
| 4 | Baja de una oferta Programada | `CU-PVP-CON` paso 6 ofrece la baja sólo si está **Activa**. `CU-PVP-BAJ`, en su precondición, y `CO-057` y `CO-058` aceptan **Activa o Programada** | Es una contradicción entre dos fichas. **Recomiendo** seguir a `CU-PVP-BAJ` y a los dos contratos: la baja se ofrece también en Programada |
| 5 | Qué productos de un tipo alcanza la oferta | La ficha dice «productos activos». **(a)** Los que se ofrecen en la tienda: Activo y Pre-venta. **(b)** Sólo Activo | **Recomiendo (a)**: una reserva en Pre-venta también se cobra con precio vigente (`CU-TDA-CAT` A2) |
| 6 | Redondeo del porcentaje | No declarado | Se redondea al peso, como todo precio de venta (A1 del alta), con aritmética decimal exacta |
| 7 | La activación automática en el log | `CO-059` declara una entrada con la acción «Vencimiento automático de oferta». No dice nada de la activación | Sólo se audita el vencimiento, como dice el contrato. La activación no deja entrada |

---

## 4. Orden de construcción

| # | Caso de uso | Depende de | Motivo |
| --- | --- | --- | --- |
| 1 | `Oferta` y el precio visible con oferta | Plan 07, paso 1 | La función de precio visible ya existe y se extiende |
| 2 | `CU-PVP-CON` | 1 | Es el punto de entrada de los otros tres |
| 3 | `CU-PVP-ALT` | 2 | |
| 4 | `CU-PVP-EDI` | 3 | |
| 5 | `CU-PVP-BAJ` | 3 | |
| 6 | `CO-059` y el comando del Temporizador | 1 | |
| 7 | Precio tachado en la tienda y en el carrito | 1 | Cierra `CU-TDA-CAT` |

---

## 5. Riesgos

| Riesgo | Dónde aparece | Cómo se cubre |
| --- | --- | --- |
| Descuento en punto flotante | Precio visible | `Decimal` en todo el cálculo; prueba con porcentajes que no dan exacto |
| Dos administradores crean a la vez ofertas solapadas | `CO-054`, `CO-056` | La validación de solapamiento y el alta van en una transacción con bloqueo sobre el producto o el tipo del alcance |
| Una oferta de monto fijo deja un precio en cero | `CO-055`, I-09 | Tope de $1. Prueba en el borde: descuento igual al precio |
| Postcondiciones negativas | `CO-058`, `CO-059` | Una baja o un vencimiento no tocan el precio guardado del producto, ni otras ofertas, ni carritos sin productos del alcance |
| Control de acceso | Las seis pantallas | Prueba por la dirección real con Cajero y con Cliente |

---

## 6. Fuera de alcance

- El precio con oferta en el mostrador (`CU-VTA-REG`): usará la misma función cuando exista.
- La relación con el canje de puntos (RF-12): no existe Puntos.
- Los otros ocho procesos del Temporizador: el comando los recibirá a medida que existan.
