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

---

### R-03-001 · Resolución parcial de B-03-001

**Fecha:** 2026-10-03 · **Enmienda al documento:** ninguna

**Qué se decidió.**
Con `LineaCarrito` construida, la propagación de precios llega a los carritos.

**Qué se hizo.**
`CO-048` y `CO-053` actualizan el precio vigente de las líneas de carrito de los productos que tocan
(B-07-003). La parte de ofertas de B-03-001 sigue abierta hasta que exista `Oferta`.

---

### B-03-007 · La oferta cambia el precio visible, no el guardado, y el Temporizador es un comando

**Tipo:** Agregado · **Fecha:** 2026-10-03 · **Alcance:** `CO-054` a `CO-059`, P-05
**Estado:** Abierta — decidido por el responsable el 2026-10-03 (plan 03, segunda parte, ambigüedad 1)

**Qué apareció.**
Las ofertas se activan y vencen por fecha, y no existe forma de disparar las operaciones del
Temporizador (P-05). Si el descuento dependiera de que algo corra, una oferta empezaría tarde o no
terminaría nunca.

**Qué dice la especificación.**
> «El estado de cada oferta es calculado y mantenido automáticamente por el sistema según sus
> fechas configuradas» (`CU-PVP-CON`, Comentarios)

**Qué se hizo.**
- **El precio guardado del producto no cambia.** Una sola función calcula el precio visible, y la
  usan la tienda, el carrito y, cuando exista, el mostrador. Mira las fechas: una oferta descuenta
  desde su día de inicio hasta el final de su día de vencimiento, aunque nada haya corrido. Dar de
  baja o dejar vencer restaura el precio sin tener que recordar cuál era.
- **El Temporizador es `manage.py ejecutar_temporizador`.** Deja el estado guardado al día, pone las
  líneas de carrito al precio nuevo y escribe «Vencimiento automático de oferta» con el
  Temporizador como actor. Corre al arrancar `demostracion.bat`. En una instalación que queda
  encendida se programa una vez por día. Correrlo dos veces no duplica nada.
- **La lista de ofertas muestra el estado según las fechas**, aunque el comando no haya corrido.
- **El comando es la puerta de los otros procesos de P-05**: cada uno se suma como una función más.

**Qué habría que cambiar.**
`CU-PVP-CON`, Comentarios: «el precio con oferta se calcula a partir de las fechas; el Temporizador
deja el estado al día y registra el vencimiento». `CO-059`: nombrar que la activación no espera al
ciclo.

---

### B-03-008 · Reglas de aplicación que la especificación no fija

**Tipo:** Agregado · **Fecha:** 2026-10-03 · **Alcance:** `CO-054`, `CO-056`, `CO-059`, I-20
**Estado:** Abierta — plan 03, segunda parte, ambigüedades 2, 3, 5, 6 y 7, aprobadas el 2026-10-03

**Qué apareció.**
Cinco puntos donde la especificación admite más de una lectura.

**Qué dice la especificación.**
> «No se solapan dos ofertas Activas o Programadas sobre el mismo alcance» (I-20)

> «Por cada oferta Activa cuya fecha de vencimiento se alcanzó, o.estado pasó a Vencida» (`CO-059`)

Sobre lo demás: `Nada.`

**Qué se hizo.**
- **El día de vencimiento está incluido.** Con el día excluido, una oferta con inicio igual al
  vencimiento, que `CO-054` admite, no estaría activa nunca.
- **Individual sobre tipo.** I-20 permite una oferta individual y otra del tipo del mismo producto a
  la vez. Manda la individual; la ficha de la oferta por tipo marca los productos «tapados».
- **El alcance por tipo son los productos Activos y en Pre-venta.** La reserva también se cobra con
  precio vigente.
- **El porcentaje se redondea al peso**, con `Decimal` exacto, como cualquier precio de venta. Un
  porcentaje de 100 o más se rechaza: deja todo el alcance en cero.
- **La activación automática no deja entrada en el log**: `CO-059` sólo declara la del vencimiento.

**Qué habría que cambiar.**
`CU-PVP-ALT`, paso 5: «la oferta descuenta hasta el final del día de vencimiento». I-20: decir qué
pasa con una oferta individual y otra del tipo del mismo producto. `CU-PVP-ALT`, paso 3: nombrar
qué estados cuentan como «productos activos».

---

### B-03-009 · La baja de una oferta Programada: dos fichas no dicen lo mismo

**Tipo:** Corrección · **Fecha:** 2026-10-03 · **Alcance:** `CU-PVP-CON` paso 6, `CU-PVP-BAJ`, `CO-057`, `CO-058`
**Estado:** Abierta — plan 03, segunda parte, ambigüedad 4, aprobada el 2026-10-03

**Qué apareció.**
La consulta ofrece la baja sólo para las ofertas Activas. La baja y sus dos contratos aceptan
también las Programadas.

**Qué dice la especificación.**
> «o CU-PVP-BAJ (Dar de Baja) si está Activa» (`CU-PVP-CON`, paso 6)

> «La oferta objetivo existe en el sistema con estado Activa o Programada» (`CU-PVP-BAJ`, Precondiciones)

**Qué se hizo.**
Se siguió a `CU-PVP-BAJ` y a los dos contratos: la ficha ofrece «Dar de baja» en Activa y en
Programada.

**Qué habría que cambiar.**
`CU-PVP-CON`, paso 6: «o CU-PVP-BAJ si está Activa o Programada».

---

### B-03-010 · La edición también pide confirmar el tope de $1

**Tipo:** Agregado · **Fecha:** 2026-10-03 · **Alcance:** `CU-PVP-EDI`, `CO-056`, `CO-055`
**Estado:** Abierta

**Qué apareció.**
`CO-056` aplica «las mismas validaciones de `CO-054`», entre ellas que el descuento no deje precios
en cero. En el alta, ese caso no rechaza: pide confirmar el precio mínimo de $1 (`CO-055`). La
edición no dice si pide lo mismo o si rechaza.

**Qué dice la especificación.**
> «Las validaciones son las mismas de CO-054» (`CO-056`, Notas)

**Qué se hizo.**
La edición muestra la misma lista de productos afectados y el mismo botón «Confirmar con precio
mínimo de $ 1». Sin confirmar, no guarda nada.

**Qué habría que cambiar.**
`CU-PVP-EDI`, Excepciones: agregar la E3 del alta. `CO-055`, Referencias Cruzadas: sumar
`CU-PVP-EDI`.

---

### B-03-011 · El precio tachado en la tienda y el filtro por precio con oferta

**Tipo:** Agregado · **Fecha:** 2026-10-03 · **Alcance:** `CO-176`, `CO-177`, `CO-178`
**Estado:** Abierta

**Qué apareció.**
Con ofertas, la tienda tiene que mostrar el descuento. Además, el filtro por precio del catálogo
puede leer el precio guardado o el que se cobra.

**Qué dice la especificación.**
> «precio vigente» (`CU-TDA-CAT`, paso 6)

La guía visual no dibuja un precio con descuento.

**Qué se hizo.**
- La tarjeta, la ficha pública y el carrito muestran el precio original tachado, más chico y en
  segundo plano, antes del que se cobra. La ficha nombra la oferta y su vencimiento.
- El filtro «precio desde / hasta» mide el precio que se cobra. Se calcula con la misma función
  del precio visible, no con una segunda versión en la consulta a la base, para que no redondee
  distinto.

**Qué habría que cambiar.**
`identidad_visual.md`, Estantería y tarjeta: el precio con descuento. `CU-TDA-CAT`, paso 3: «el
filtro de precio usa el precio vigente».

---

### R-03-002 · Resolución de B-03-001

**Fecha:** 2026-10-03 · **Enmienda al documento:** ninguna

**Qué se decidió.**
Con `Oferta` construida, la parte pendiente de B-03-001 se cumple.

**Qué se hizo.**
Cada operación que cambia qué descuenta una oferta (alta, edición, baja, ciclo del Temporizador)
pone las líneas de carrito de los productos alcanzados al precio visible nuevo. B-03-001 queda
resuelta.

---

### B-03-012 · El sistema contaba los días en UTC: las ofertas vencían a las 21:00

**Tipo:** Corrección · **Fecha:** 2026-10-04 · **Alcance:** `CO-054`, `CO-059`, todo lo que dependa de «hoy» o muestre una hora
**Estado:** Resuelta — corregido el 2026-10-04, encontrado en el ensayo de la demostración (plan 00, D2-04)

**Qué apareció.**
Un caso borde del ensayo (una oferta a las 23:59 de su día de vencimiento, en hora argentina)
mostró que no descontaba. La configuración tenía `TIME_ZONE = "UTC"`, el valor que deja Django al
crear el proyecto, y nadie lo había decidido: no figura en ninguna bitácora. Para el sistema «hoy»
era la fecha de Greenwich, así que entre las 21:00 y la medianoche ya era el día siguiente. Las
ofertas empezaban y vencían tres horas antes, y las horas que se muestran (el log de auditoría, el
correo de los proveedores) se leían corridas.

**Qué dice la especificación.**
> «La oferta descuenta hasta el final del día de vencimiento» (B-03-008, aprobado el 2026-10-03)

**Qué se hizo.**
`TIME_ZONE = "America/Argentina/Buenos_Aires"`. Las fechas se siguen guardando en UTC (`USE_TZ`);
lo que cambia es cómo se leen y qué día es «hoy». La prueba
(`test_casos_borde.py::test_D2_04_la_oferta_descuenta_hasta_las_23_59_y_no_a_las_00_00`) se
escribió antes y fallaba.

**Qué habría que cambiar.**
Nada en el documento. Es transversal: la suite completa se volvió a correr después del cambio.
