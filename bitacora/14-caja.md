> **Tipo: Bitácora.** Se anexa, no se reescribe.

# Bitácora — `14` Caja

> Registro de lo que se decidió construyendo este módulo. **Se anexa, no se reescribe.**
> Una entrada resuelta se marca; no se borra.
>
> Este archivo es el material que el responsable lee para decidir qué se enmienda en el documento
> de análisis. Escribí para alguien que conoce el dominio y no tiene el código a la vista.

---

## Entradas

### B-14-001 · Lo vendido después del cierre del día va al cierre siguiente

**Tipo:** Corrección · **Fecha:** 2026-10-10 · **Alcance:** `CU-CAJ-CIE` E1, `CO-126`, I-23
**Estado:** Abierta — decidida por el responsable el 2026-10-10 (plan 14, amb. 1)

**Qué apareció.**
E1 sólo impide un segundo cierre cuando no hay transacciones nuevas, lo que deja abierto un
segundo cierre del mismo día. I-23 permite uno por fecha.

**Qué dice la especificación.**
> «si ya existe un cierre de caja registrado para la fecha actual y no hay nuevas transacciones
> posteriores a ese cierre, el sistema informa que el cierre del día ya fue realizado»
> (`CU-CAJ-CIE`, E1)

> «Existe a lo sumo un `CierreDeCaja` por fecha de jornada» (I-23)

**Qué se hizo.**
Un cierre confirmado no cambia. Lo cobrado después pasa al cierre siguiente, y la pantalla de
Caja muestra el cierre del día y cuántas transacciones esperan el próximo.

**Qué habría que cambiar.**
`CU-CAJ-CIE` E1: «si ya existe un cierre para la fecha actual, el sistema lo presenta; las
transacciones posteriores quedan para el cierre siguiente».

---

### B-14-002 · Qué entra en un cierre

**Tipo:** Agregado · **Fecha:** 2026-10-10 · **Alcance:** `CU-CAJ-CIE` paso 2, `CO-126`
**Estado:** Abierta — decidida por el responsable el 2026-10-10 (plan 14, amb. 2, 3 y 4)

**Qué apareció.**
La ficha habla de «la jornada activa» sin decir qué pasa con un día que no se cerró, ni con las
compras pagadas sólo con puntos.

**Qué dice la especificación.**
> «El sistema recopila todos los movimientos registrados en la jornada activa» (`CU-CAJ-CIE`,
> paso 2)

**Qué se hizo.**
- Un cierre incluye todas las transacciones aprobadas que todavía no entraron en uno, aunque
  sean de días anteriores sin cerrar. El resumen avisa cuántas son de días anteriores.
- Las compras online pagadas sólo con puntos no tienen transacción de pago: no suman dinero y se
  informan aparte, como cantidad.
- No hay arqueo del efectivo contado contra el esperado: la ficha no lo pide.

**Qué habría que cambiar.**
`CU-CAJ-CIE` paso 2: «todas las transacciones aprobadas sin cierre previo, de la fecha o
anteriores».

---

### B-14-003 · Las ventas de la jornada, en la caja

**Tipo:** Agregado · **Fecha:** 2026-10-21 · **Alcance:** `CU-CAJ-CIE`, `CO-203`
**Estado:** Abierta — decidida por el responsable el 2026-10-21 (plan 00 de interfaz, segunda parte, 12, opción a)

**Qué apareció.**
El cajero no tenía dónde ver lo que vendió en el día antes de cerrar: sólo los totales.

**Qué dice la especificación.**
> «Si el usuario exporta el resumen, el sistema genera el archivo CSV con el detalle de cada
> transacción individual del día» (`CU-CAJ-CIE`, A2)

El detalle existe sólo en la exportación.

**Qué se hizo.**
La caja lista las ventas de la jornada sin cerrar, la más reciente primero, con hora, cliente,
canal, medio y monto, un filtro por medio y el enlace al comprobante de cada venta de mostrador. El
detalle de un cierre anterior muestra lo mismo. Los totales se ven como recuadros por canal y por
medio de pago, con su proporción. Es una lectura: no cierra ni marca nada. Un historial de
cualquier fecha queda para los reportes (`CU-REP-GEN`).

**Qué habría que cambiar.**
`CU-CAJ-CIE` paso 3: suma «(e) el detalle de cada transacción incluida».
