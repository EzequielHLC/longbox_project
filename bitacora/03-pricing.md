# Bitácora — `03` Pricing

> Registro de lo que se decidió construyendo este módulo. **Se anexa, no se reescribe.**
> Una entrada resuelta se marca; no se borra.
>
> Este archivo es el material que el responsable lee para decidir qué se enmienda en el documento
> de análisis. Escribí para alguien que conoce el dominio y no tiene el código a la vista.

---

## Entradas

### B-03-001 · La propagación a carritos y a ofertas no tiene sobre qué actuar

**Tipo:** Agregado · **Fecha:** 2026-10-02 · **Alcance:** `CU-PVP-TBM`, `CU-PVP-MAR`, `CO-048`, `CO-053`
**Estado:** Abierta — se cierra cuando existan `Carrito` y `Oferta`

**Qué apareció.**
Las dos propagaciones de precio declaran efectos sobre las líneas de carrito y sobre las ofertas
de tipo porcentaje. Ninguno de los dos conceptos existe todavía.

**Qué dice la especificación.**
> «(c) Por cada LineaCarrito que refiere a uno de esos productos, el precio vigente pasó al nuevo
> valor y la línea quedó marcada con el aviso de cambio de precio.» (`CO-048`, Postcondiciones)
> «(c) LineaCarrito: las líneas con esos productos quedaron con el precio actualizado y el aviso
> de cambio.» (`CO-053`, Postcondiciones)

**Qué se hizo.**
Se construyó todo lo demás: la fila, los productos, la auditoría. Las postcondiciones sobre
carritos quedan sin ejercer, y por eso `CO-048` y `CO-053` cierran como parciales, y con ellos
`CU-PVP-TBM` y `CU-PVP-MAR`. Las ofertas de tipo porcentaje no necesitan recalcularse: cuando
existan se calcularán sobre el precio vigente del producto, que es el que la propagación cambia.

**Qué habría que cambiar.**
Nada.

---

### B-03-002 · El margen alcanza también a los importados cancelados por la editorial

**Tipo:** Agregado · **Fecha:** 2026-10-02 · **Alcance:** `CU-PVP-MAR`, `CO-052`, `CO-053`
**Estado:** Resuelta — decisión del responsable el 2026-09-30 (consulta C-11): mandan los contratos

**Qué apareció.**
`CO-048` excluye de la propagación a los productos cancelados por la editorial. `CO-053` recalcula
todo importado con precio vinculado, sin esa exclusión.

**Qué dice la especificación.**
> «(c) Por cada ProductoEditorial importado con precio fijado a mano = no, Producto.precio pasó
> del valor anterior a precio base × (1 + nuevo margen).» (`CO-053`, Postcondiciones)

**Qué se hizo.**
Se aplica la letra del contrato: el cambio de margen recalcula también a los cancelados, y la
cifra de la simulación (`CO-052`) cuenta exactamente lo mismo que el cambio recalcula.

**Qué habría que cambiar.**
Nada. Si se quisiera la exclusión, `CO-052` y `CO-053` tendrían que declararla como `CO-048`.

---

### B-03-003 · Sin importados, el margen no se puede cambiar

**Tipo:** Agregado · **Fecha:** 2026-10-02 · **Alcance:** `CU-PVP-MAR`, `CO-052`
**Estado:** Abierta — consulta C-19

**Qué apareció.**
Con la precondición de `CO-052` y el margen fuera de la pantalla de parámetros (`CU-CFG-PAR` A1),
una instalación sin productos importados no tiene ninguna pantalla desde la que fijar el margen
de su primer lote importado.

**Qué dice la especificación.**
> «Existe al menos un ProductoEditorial importado con precio base almacenado.» (`CO-052`,
> Precondiciones)

**Qué se hizo.**
La pantalla muestra el margen vigente y, sin importados, informa que se podrá cambiar cuando
exista al menos uno. El servidor rechaza el cambio igual. El primer lote importado usa el margen
inicial de la instalación.

**Qué habría que cambiar.**
Si no es lo que se quiere: `CO-052`, Precondiciones, quitar la existencia de un importado y
tratar ese caso como A1 («la propagación no afectará a ninguno»).

---

### B-03-004 · El margen se escribe como porcentaje

**Tipo:** Agregado · **Fecha:** 2026-10-02 · **Alcance:** `CU-PVP-MAR`, `CO-167`
**Estado:** Abierta

**Qué apareció.**
El margen se guarda como proporción (0,40) y la pantalla de parámetros lo pedía así, con un
control que rechazaba el «40» como error frecuente. `CO-167` pide presentarlo como porcentaje.

**Qué dice la especificación.**
> «Devolver el margen vigente expresado como porcentaje.» (`CO-167`, Responsabilidades)

Sobre cómo se ingresa el nuevo: `Nada`.

**Qué se hizo.**
Se presenta y se ingresa como porcentaje, con hasta dos decimales (42,55 %). Se guarda como
proporción con cuatro decimales, sin pérdida: la conversión es dividir por cien. El recálculo
redondea al peso sólo el resultado.

**Qué habría que cambiar.**
`CU-PVP-MAR`, paso 2: «El Administrador ingresa el nuevo valor del margen, como porcentaje».

---

### B-03-005 · Restaurar el precio calculado se ofrece desde la ficha y desde la edición

**Tipo:** Agregado · **Fecha:** 2026-10-02 · **Alcance:** `CO-031`, `CU-CAT-EDI` A2
**Estado:** Abierta

**Qué apareció.**
`CO-031` se invoca desde la edición de producto, y sus notas piden mostrar el precio recalculado
antes de guardar.

**Qué dice la especificación.**
> «El resultado se informa antes de guardar, para que el Administrador vea a qué precio queda el
> producto antes de aceptar.» (`CO-031`, Notas)

**Qué se hizo.**
La opción «Restaurar precio calculado» aparece, con el precio al que quedaría, en la ficha y en
la edición del producto, sólo cuando hay un precio calculado al cual volver. Lleva a una
confirmación que muestra el precio actual, el calculado y de dónde sale. Es una operación aparte
del guardado de la edición: restaurar no guarda otros cambios a medio escribir.

**Qué habría que cambiar.**
`CU-CAT-EDI`, A2: agregar que la restauración también se ofrece desde la ficha del producto.

---

### Nota de cierre · 2026-10-02

La tabla de precios y el margen tienen pantallas propias con informe de alcance antes de
propagar, y `CO-031` permite volver al precio calculado. Queda: la propagación a carritos y las
ofertas, que esperan a `Carrito` y `Oferta` (B-03-001), y la respuesta a C-19.

---

### B-03-006 · Equivalencias del precio en otras monedas, como referencia

**Tipo:** Agregado · **Fecha:** 2026-10-02 · **Alcance:** `CU-PVP-TBC`, `CU-ALT-IMP`
**Estado:** Abierta — pedido del responsable el 2026-10-02

**Qué apareció.**
El responsable pidió ver cotizaciones en varias monedas en la tabla de precios y en la carga de
importados.

**Qué dice la especificación.**
`Nada.` Las cotizaciones sólo aparecen como sugerencia editable de la carga de importados.

**Qué se hizo.**
La tabla de precios muestra, junto al precio en pesos, su equivalencia en dólares, euros y yenes a
la cotización de referencia del día, con la fecha y un aviso si está desactualizada. La carga de
importados muestra la cotización de referencia de las tres monedas. Es sólo informativo: se
cobra el precio en pesos y el cálculo usa la cotización que el Administrador escribe.

**Qué habría que cambiar.**
`CU-PVP-TBC` paso 2: «con su equivalencia de referencia en las monedas de importación».
