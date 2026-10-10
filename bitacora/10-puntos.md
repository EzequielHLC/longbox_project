> **Tipo: Bitácora.** Se anexa, no se reescribe.

# Bitácora — `10` Puntos

> Registro de lo que se decidió construyendo este módulo. **Se anexa, no se reescribe.**
> Una entrada resuelta se marca; no se borra.
>
> Este archivo es el material que el responsable lee para decidir qué se enmienda en el documento
> de análisis. Escribí para alguien que conoce el dominio y no tiene el código a la vista.

---

## Entradas

### B-10-001 · Cada movimiento de puntos dice de qué pedido viene

**Tipo:** Agregado · **Fecha:** 2026-10-09 · **Alcance:** `CU-PTS-CON` paso 2, `CO-188`
**Estado:** Abierta — decidida por el responsable el 2026-10-09 (plan 10, amb. 1)

**Qué apareció.**
El historial de movimientos pide fecha, tipo, cantidad y saldo resultante. «Acreditación de 1800»
sin decir de qué compra no le sirve al Cliente para reconocerla.

**Qué dice la especificación.**
> «Historial de movimientos: listado cronológico descendente de todas las operaciones sobre la
> cuenta: acreditaciones y débitos con fecha, tipo de movimiento, cantidad y saldo resultante tras
> cada operación.» (`CU-PTS-CON`, paso 2)

**Qué se hizo.**
Cada movimiento suma su origen: el pedido que lo produjo, con enlace a su detalle, o el motivo
cuando no hay pedido (un ajuste manual, más adelante).

**Qué habría que cambiar.**
`CU-PTS-CON` paso 2 (c) y `CO-188`, salida: sumar «el pedido o el motivo que lo originó».

---

### B-10-002 · El saldo de puntos está siempre a la vista en la tienda

**Tipo:** Agregado · **Fecha:** 2026-10-09 · **Alcance:** `CU-PTS-CON`, encabezado de la tienda
**Estado:** Abierta — pedido del responsable el 2026-10-09 (plan 10, amb. 2)

**Qué apareció.**
El responsable pidió que el Cliente pueda ver en todo momento si le alcanzan los puntos para
canjear algo.

**Qué dice la especificación.**
> «El saldo disponible presentado aquí es el mismo que el sistema expone en tiempo real durante
> el checkout» (`CU-PTS-CON`, comentarios)

Fuera del panel y del checkout: `Nada`.

**Qué se hizo.**
El encabezado de la tienda muestra el saldo del Cliente con su equivalencia en pesos, en todas
las pantallas, y lleva a «Mis puntos». El menú «Mi cuenta» también lo muestra. Un invitado o el
personal no lo ven.

**Qué habría que cambiar.**
`CU-PTS-CON`, comentarios: «el saldo también está a la vista en el encabezado de la tienda».

---

### B-10-003 · La equivalencia de puntos se configura como «1 punto por cada $ X gastados»

**Tipo:** Agregado · **Fecha:** 2026-10-09 · **Alcance:** `CU-CFG-PAR` (Fidelización), RF-19
**Estado:** Resuelta — reemplazada el mismo día por B-10-004, a pedido del responsable

**Qué apareció.**
Parámetros mostraba «Equivalencia de puntos ($ por punto)», y al Administrador no le quedaba claro
qué número poner.

**Qué dice la especificación.**
> «El Administrador debe poder configurar la equivalencia parametrizable entre puntos y pesos
> argentinos (por ejemplo: 1 punto = $10 ARS).» (RF-19)

> «Equivalencia de puntos en $ ARS por punto (decimal > 0 ej: 10 = un punto vale $10 ARS)»
> (`CU-CFG-PAR`, paso 2)

**Qué se hizo.**
El campo se lee como una frase: «1 punto por cada $ [10] gastados», con la aclaración «Al canjear,
1 punto vale el mismo monto». El dato y el cálculo no cambian: sigue siendo una sola equivalencia
para acreditar y para canjear, como pide RF-19.

**Qué habría que cambiar.**
`CU-CFG-PAR` paso 2, Fidelización: «Puntos por compra: 1 punto por cada $ X gastados (decimal > 0);
al canjear, 1 punto vale $ X».

---

### B-10-004 · Los puntos tienen dos parámetros: el valor del punto y el reintegro

**Tipo:** Corrección · **Fecha:** 2026-10-09 · **Alcance:** RF-19, `CU-CFG-PAR` (Fidelización), `CO-089`, `ConfiguracionSistema`
**Estado:** Abierta — decidida por el responsable el 2026-10-09

**Qué apareció.**
Con una sola equivalencia para ganar y para canjear, cada compra devolvía su valor completo en
puntos: con 1 punto = $10, una compra de $10.000 acreditaba 1.000 puntos, que valen $10.000. El
Administrador no podía decidir cuánto devuelve el programa sin cambiar también lo que vale un
punto.

**Qué dice la especificación.**
> «Tras la confirmación de un pago de monto M con una equivalencia configurada de E puntos por
> peso, el saldo del cliente debe incrementarse en M / E puntos» (RF-19, condición de verificación)

**Qué se hizo.**
Dos parámetros independientes en Parámetros → Compra online → Fidelización:
- **Valor del punto:** «1 punto = $ X». Es lo que vale un punto al canjearlo.
- **Reintegro en puntos:** «Y % de cada compra», sobre lo pagado en dinero y sin el envío.

Puntos ganados = pagado en dinero × Y % ÷ X, hacia abajo. El porcentaje es exactamente lo que el
cliente recupera en pesos: con 5 % y 1 punto = $10, una compra de $10.000 suma 50 puntos, que valen
$500. Cambiar el valor del punto no cambia ese reintegro. La pantalla muestra el ejemplo con los
valores vigentes. El reintegro nace en 5 %.

**Qué habría que cambiar.**
RF-19: «El Administrador configura el valor del punto en pesos (1 punto = $ X) y el porcentaje de
cada compra que se reintegra en puntos (Y %). Tras un pago de monto M, el saldo se incrementa en
⌊M × Y / 100 / X⌋ puntos». `CU-CFG-PAR` paso 2, Fidelización: los dos parámetros.
`ConfiguracionSistema`: sumar «reintegro en puntos (%)».
