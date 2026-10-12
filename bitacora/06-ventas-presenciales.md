> **Tipo: Bitácora.** Se anexa, no se reescribe.

# Bitácora — `06` Ventas Presenciales

> Registro de lo que se decidió construyendo este módulo. **Se anexa, no se reescribe.**
> Una entrada resuelta se marca; no se borra.
>
> Este archivo es el material que el responsable lee para decidir qué se enmienda en el documento
> de análisis. Escribí para alguien que conoce el dominio y no tiene el código a la vista.

---

## Entradas

### B-06-001 · El cliente se identifica en el mostrador con un código de cliente

**Tipo:** Corrección · **Fecha:** 2026-10-10 · **Alcance:** RF-13, `CU-VTA-REG` paso 3, `CO-081`, `Usuario`
**Estado:** Abierta — decidida por el responsable el 2026-10-10 (plan 06, amb. 1)

**Qué apareció.**
La venta vincula la cuenta del cliente «por DNI o código de cliente», y `Usuario` no tiene ninguno
de los dos.

**Qué dice la especificación.**
> «Vinculación opcional de una cuenta de cliente por DNI o código de cliente» (RF-13)

> «vincularCuentaDeCliente(dniOCodigo)» (`CO-081`)

**Qué se hizo.**
- Cada cuenta de Cliente tiene un **código de cliente** de 6 cifras, asignado al crearse y único.
  Las cuentas que ya existían lo recibieron al migrar.
- El Cliente lo ve en «Mi cuenta»; el Administrador, en el padrón y en la ficha del cliente.
- El mostrador vincula por código de cliente o, si el cliente no lo recuerda, por correo.
- No se pide DNI, por decisión del responsable.

**Qué habría que cambiar.**
RF-13 y `CU-VTA-REG` paso 3: «por código de cliente o correo». `CO-081`:
«vincularCuentaDeCliente(codigoOCorreo)». `Usuario`: sumar «código de cliente : texto «único, 6
cifras»».

---

### B-06-002 · El ticket en curso vive en la sesión del Cajero

**Tipo:** Agregado · **Fecha:** 2026-10-10 · **Alcance:** `CO-078` a `CO-081`
**Estado:** Abierta — decidida por el responsable el 2026-10-10 (plan 06, amb. 2)

**Qué apareció.**
El contrato dice que el ticket no materializa ningún concepto persistente hasta `CO-082`, sin
decir dónde vive mientras tanto.

**Qué dice la especificación.**
> «(a) Se creó una transacción de venta en curso, sin materializar aún ningún concepto persistente
> del dominio.» (`CO-078`)

**Qué se hizo.**
El ticket vive en la sesión de quien atiende: sobrevive a recargar o cerrar la pestaña y se pierde
al cerrar sesión. Los precios se leen en cada paso y se congelan al confirmar.

**Qué habría que cambiar.**
`Nada`.

---

### B-06-003 · Un solo campo para agregar: código exacto o búsqueda por título

**Tipo:** Agregado · **Fecha:** 2026-10-10 · **Alcance:** `CU-VTA-REG` paso 2, `CO-079`
**Estado:** Abierta — decidida por el responsable el 2026-10-10 (plan 06, amb. 3 y 4)

**Qué apareció.**
El Cajero busca «por nombre o código». En un mostrador, lo más frecuente es leer el código del
envase.

**Qué dice la especificación.**
> «El Cajero busca y añade productos al ticket por nombre o código.» (`CU-VTA-REG`, paso 2)

**Qué se hizo.**
- Si lo escrito coincide exacto con el código interno, el código de barras o el ISBN de un
  producto, se agrega directo: sirve para un lector de códigos. Si no, se listan coincidencias
  por título.
- Sólo se venden productos Activos con stock suficiente; una pre-venta no se vende en el local.

**Qué habría que cambiar.**
`CU-VTA-REG` paso 2: «por título, o por código interno, código de barras o ISBN».

---

### B-06-004 · El comprobante es una pantalla imprimible, no una factura

**Tipo:** Agregado · **Fecha:** 2026-10-10 · **Alcance:** `CO-082` (salida)
**Estado:** Abierta — decidida por el responsable el 2026-10-10 (plan 06, amb. 5 y 6)

**Qué apareció.**
`CO-082` devuelve un comprobante sin decir qué es. El caso de uso también menciona una
«corrección de transacciones» del Administrador que ningún caso de uso describe.

**Qué dice la especificación.**
> «confirmarVentaPresencial(medioDePago) : Comprobante» (`CO-082`)

> «Administrador: ídem al Cajero, con acceso adicional a corrección de transacciones.»
> (`CU-VTA-REG`, actores)

**Qué se hizo.**
- El comprobante es una pantalla con el detalle de la venta y los puntos acreditados, que se
  imprime desde el navegador. La facturación electrónica no está en el alcance.
- No se construye la corrección de transacciones.
- Una venta cubierta entera con puntos registra igual su transacción de pago, por $ 0, como pide
  `CO-082` (a).

**Qué habría que cambiar.**
`CU-VTA-REG`, actores: quitar la corrección de transacciones o asignarle un caso de uso.
