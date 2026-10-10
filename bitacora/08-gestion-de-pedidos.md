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
