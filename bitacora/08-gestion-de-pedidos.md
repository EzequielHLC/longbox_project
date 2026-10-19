> **Tipo: Bitácora.** Se anexa, no se reescribe.

# Bitácora — `08` Gestión de Pedidos

> Registro de lo que se decidió construyendo este módulo. **Se anexa, no se reescribe.**
> Una entrada resuelta se marca; no se borra.
>
> Este archivo es el material que el responsable lee para decidir qué se enmienda en el documento
> de análisis. Escribí para alguien que conoce el dominio y no tiene el código a la vista.

---

## Entradas

### B-08-001 · La línea de tiempo del pedido es un concepto propio, `TransicionDePedido`

**Tipo:** Agregado · **Fecha:** 2026-10-09 · **Alcance:** `CO-183`, `CO-193`, `CU-PED-EST` paso 2, DME-07
**Estado:** Abierta — decidida por el responsable el 2026-10-09 (plan 08, amb. 1)

**Qué apareció.**
El Administrador y el Cliente ven «la línea de tiempo de estados con timestamps» de un pedido.
`Pedido` sólo guarda el estado en el que está, no cuándo llegó a cada uno.

**Qué dice la especificación.**
> «línea de tiempo de estados con timestamps» (`CO-183`, salida)

> «Ítems, precios efectivos, estados alcanzados y fecha de cada transición.» (`CO-193`, salida)

El modelo de dominio no declara dónde vive ese dato.

**Qué se hizo.**
Cada cambio de estado de un pedido queda como una **transición**: el estado anterior, el nuevo,
cuándo y quién la hizo (el Administrador, o nadie si fue el sistema). La primera la escribe la
compra, al generar el pedido. El registro de auditoría sigue guardando lo suyo; la línea de tiempo
no se lee de ahí, porque el Cliente también la ve.

**Qué habría que cambiar.**
Modelo de dominio, Área 5: sumar `TransicionDePedido` (estado anterior opcional, estado nuevo,
ocurrida en) con `Pedido "1" *-- "1..*" TransicionDePedido` y `Usuario "0..1" -- "0..*"
TransicionDePedido`. `CO-089` y `CO-092`: sumar «se creó una TransicionDePedido».

---

### B-08-002 · Cada avance avisa por correo, y el pedido abierto se actualiza solo

**Tipo:** Agregado · **Fecha:** 2026-10-09 · **Alcance:** `CU-PED-EST` paso 4, `CO-092`, RF-18
**Estado:** Abierta — decidida por el responsable el 2026-10-09 (plan 08, amb. 3)

**Qué apareció.**
El caso de uso dice que el sistema «notifica al Cliente» y que el Cliente ve el estado «en tiempo
real», sin decir por qué medio.

**Qué dice la especificación.**
> «El sistema transiciona el pedido al nuevo estado, notifica al Cliente con el cambio de estado
> actualizado y registra la operación en el log de auditoría.» (`CU-PED-EST`, paso 4)

> «el cliente debe visualizar ese estado en su cuenta en un máximo de 30 segundos» (RF-18,
> condición de verificación)

**Qué se hizo.**
Cada avance manda un correo al Cliente, o al correo del invitado. El detalle de un pedido activo
en la cuenta del Cliente vuelve a pedir su estado cada 30 segundos.

**Qué habría que cambiar.**
`CU-PED-EST` paso 4: «notifica al Cliente por correo».

---

### B-08-003 · Cómo se filtra por cliente y qué es el total del listado

**Tipo:** Agregado · **Fecha:** 2026-10-09 · **Alcance:** `CU-PED-CON` pasos 2 y 3, `CO-182`
**Estado:** Abierta — decidida por el responsable el 2026-10-09 (plan 08, amb. 4 y 6)

**Qué apareció.**
El listado filtra por «cliente» y muestra un «valor total» por pedido. Ninguno de los dos está
definido.

**Qué dice la especificación.**
> «estado del pedido, cliente, canal de origen (físico / online), rango de fechas y presencia de
> artículos demorados» (`CU-PED-CON`, paso 3)

> «ID de pedido, nombre del cliente (o "Invitado" si la compra fue sin cuenta), fecha, canal
> (Físico / Online), estado actual y valor total» (`CU-PED-CON`, paso 2)

**Qué se hizo.**
- El filtro de cliente es un texto que busca por nombre o correo, también el correo del invitado.
- El total del listado es lo cobrado: lo pagado en dinero más el envío. Los puntos canjeados se ven
  en el detalle.

**Qué habría que cambiar.**
`CU-PED-CON` paso 2: «valor total cobrado (dinero y envío)». Paso 3: «cliente, por nombre o
correo».

---

### B-08-004 · Dónde vive la ventana de decisión y cuánto dura

**Tipo:** Agregado · **Fecha:** 2026-10-12 · **Alcance:** `CU-PED-OPC`, `CO-095`, `CO-096`, `CU-CFG-PAR`
**Estado:** Abierta — decidida por el responsable el 2026-10-12 (plan 08 segunda parte, amb. 1)

**Qué apareció.**
`CO-096` cierra «la ventana de decisión de esas líneas», y el modelo no tiene dónde guardar ni
desde cuándo corre ni si se cerró.

**Qué dice la especificación.**
> «La ventana de decisión configurada en `ConfiguracionSistema` está vigente» (`CO-095`,
> Precondiciones)

Desde cuándo corre y cuánto dura por defecto: `Nada`.

**Qué se hizo.**
La ventana se abre al registrarse la demora de la línea y dura lo que diga el parámetro «ventana de
decisión ante demora», 72 horas por defecto. La línea guarda hasta cuándo puede decidir y si la
ventana se cerró.

**Qué habría que cambiar.**
`LineaPedido` (área 5): «ventana de decisión vence : fecha y hora», «ventana cerrada : sí / no».
`CU-CFG-PAR`: el valor por defecto.

---

### B-08-005 · Cancelar una pre-venta demorada no devuelve stock

**Tipo:** Corrección · **Fecha:** 2026-10-12 · **Alcance:** `CO-098`, `CU-PED-CAN` paso 3, RF-17
**Estado:** Abierta — decidida por el responsable el 2026-10-12 (plan 08 segunda parte, amb. 2)

**Qué apareció.**
Una pre-venta demorada nunca llegó: la compra no le descontó stock. Sumar una unidad al cancelarla
crea stock que no existe, y la tienda lo vende.

**Qué dice la especificación.**
> «(c) Producto.stock pasó de su valor anterior a ese valor más una unidad. Si el producto estaba
> Agotado, pasó a Activo.» (`CO-098`, Postcondiciones)

**Qué se hizo.**
El stock no cambia. La reserva cancelada deja de contar, así que cuando el título llegue sus
unidades quedan para la venta.

**Qué habría que cambiar.**
`CO-098` y `CU-PED-CAN` paso 3 (c): quitar el incremento de stock. RF-17 ídem.

---

### B-08-006 · La compensación corre hasta que el artículo llega

**Tipo:** Corrección · **Fecha:** 2026-10-12 · **Alcance:** `CO-097`, `CU-PED-CMP` E1, RF-16
**Estado:** Abierta — decidida por el responsable el 2026-10-12 (plan 08 segunda parte, amb. 4)

**Qué apareció.**
Con la opción 2, el artículo que llega queda en el local a nombre del Cliente hasta que pide el
despacho, que puede ser semanas después.

**Qué dice la especificación.**
> «hasta que el artículo sea despachado» (RF-16)

**Qué se hizo.**
La compensación se cierra cuando el artículo llega. Lo que se compensa es la demora de la
editorial, no el tiempo que el Cliente tarda en retirarlo.

**Qué habría que cambiar.**
RF-16 y `CU-PED-CMP` E1: «hasta que el artículo llega al local».

---

### B-08-007 · La opción 2 empaqueta el pedido y el artículo que llega espera el módulo 18

**Tipo:** Desvío · **Fecha:** 2026-10-12 · **Alcance:** `CO-095` opción 2, `CU-PED-OPC` paso 6
**Estado:** Abierta — consultado y aprobado por el responsable el 2026-10-12 (plan 08 segunda parte, amb. 3 y 5). La espera del módulo 18 quedó resuelta el 2026-10-14: el artículo que llega pasa a `ArticuloRetenido` (B-18-002, B-18-003). Sigue abierto el paso del pedido a Empaquetado

**Qué apareció.**
`CO-095` mueve las líneas disponibles a Empaquetado pero no dice qué pasa con el pedido, y el
artículo que llega se registra como `ArticuloRetenido`, del módulo 18, que no existe.

**Qué dice la especificación.**
> «El artículo demorado queda marcado para despacho diferido y, cuando llegue, se registra como
> ArticuloRetenido a nombre del Cliente» (`CO-095`, Notas)

**Qué se hizo.**
El pedido pasa a Empaquetado para que el Administrador lo despache. El artículo demorado, al
llegar, queda Disponible con la marca «Despacho diferido» y el pedido aparece en el listado del
Administrador. El paso a `ArticuloRetenido` se agrega con el módulo 18; hasta entonces
`CU-PED-OPC` queda `Parcial`.

**Qué habría que cambiar.**
`CO-095` opción 2: «Pedido.estado pasó a Empaquetado».

---

### B-08-008 · Un pedido que se queda sin artículos se cancela

**Tipo:** Agregado · **Fecha:** 2026-10-12 · **Alcance:** DME-07, `CO-027`, `CO-098`, `CU-CLI-HIS`
**Estado:** Abierta — decidida por el responsable el 2026-10-12

**Qué apareció.**
Si la editorial cancela el único tomo de un pedido, o el Cliente cancela su único artículo
demorado, el pedido queda sin nada que armar ni despachar.

**Qué dice la especificación.**
> «Cancelar una línea no arrastra al pedido: si el pedido tiene otras líneas no afectadas, su
> estado no cambia necesariamente» (`CO-098`, Notas)

Qué pasa si no quedan otras líneas: `Nada`. DME-07 no tiene un estado de cancelación, aunque
`CU-CLI-HIS` lista «pedidos completados y cancelados».

**Qué se hizo.**
El pedido pasa a «Cancelado», un estado terminal: sale de los activos y queda en el historial del
Cliente. El costo de envío que pagó vuelve en puntos, con la misma conversión que el artículo
(B-01-010). Si queda algún artículo, el envío no se devuelve.

**Qué habría que cambiar.**
DME-07: el estado Cancelado. `CO-027` y `CO-098`: el reembolso del envío cuando el pedido se
cancela entero.

---

### B-08-009 · Qué opciones se ofrecen según cómo está el pedido

**Tipo:** Agregado · **Fecha:** 2026-10-12 · **Alcance:** `CU-PED-OPC` paso 2, `CO-184`, `CO-095`
**Estado:** Abierta

**Qué apareció.**
Las tres opciones no siempre tienen sentido. Un pedido de un solo tomo no tiene nada que
«despachar ahora»; uno que además espera otra pre-venta no se puede despachar a medias sin dejar
la otra reserva sin camino; y si otro artículo del mismo pedido ya eligió la opción 2, el pedido
está empaquetado y «pausar el envío completo» no corresponde.

**Qué dice la especificación.**
> «las tres opciones disponibles con descripción clara de las consecuencias de cada una»
> (`CU-PED-OPC`, paso 2)

Qué pasa cuando alguna no aplica: `Nada`.

**Qué se hizo.**
- **Esperar el pedido completo**, mientras el pedido siga entero en «Esperando artículo demorado».
- **Recibir ahora lo disponible**, si hay algo disponible o ya empaquetado y ninguna otra línea
  espera una pre-venta.
- **Cancelar el artículo**, siempre.

El servidor rechaza una opción que no corresponde aunque llegue por la dirección.

**Qué habría que cambiar.**
`CU-PED-OPC` paso 2: las condiciones de cada opción.

---

### B-08-010 · La compensación se calcula por semanas cumplidas contra lo ya acreditado

**Tipo:** Agregado · **Fecha:** 2026-10-12 · **Alcance:** `CO-097`, `CU-PED-CMP` pasos 3 y 4
**Estado:** Abierta — decidida por el responsable el 2026-10-12 (plan 08 segunda parte, amb. 6)

**Qué apareció.**
El Temporizador corre una vez por día, no por semana, y puede correr dos veces el mismo día. Un
cálculo «desde la última acreditación» acredita de más si se corre de nuevo.

**Qué dice la especificación.**
> «5 % del valor original del artículo por semana completa transcurrida desde la última
> acreditación, o desde la fecha de llegada original si es la primera» (`CO-097`, Notas)

**Qué se hizo.**
Lo que corresponde es 5 % del valor por cada semana completa desde la fecha de llegada original,
con tope del 25 %; se acredita la diferencia con lo ya acumulado. Lo acumulado se lleva en pesos y
lo acreditado se convierte a puntos hacia arriba. Si el Cliente elige la opción 2 tarde, las
semanas ya cumplidas se acreditan juntas en la primera corrida. El valor del artículo es su precio
congelado por la cantidad, aunque se haya pagado con puntos.

**Qué habría que cambiar.**
`CO-097` Notas: la regla de cálculo y la conversión a puntos.

---

### Nota de cierre · 2026-10-12

Los cinco casos de uso del módulo están construidos. El Administrador lista, consulta y avanza
pedidos; el Cliente decide ante una demora, cancela con reembolso y recibe la compensación
semanal. Queda: el paso del artículo diferido a `ArticuloRetenido` y su despacho (módulo 18,
B-08-007), y la gestión manual del Administrador después de una ventana vencida, que ninguna
ficha describe.
