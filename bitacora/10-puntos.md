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

---

### B-10-005 · Qué puntos están comprometidos en un canje

**Tipo:** Agregado · **Fecha:** 2026-10-17 · **Alcance:** `CO-105` E2, `CO-106` E1, `CO-191`, `LotePuntos.comprometido en canje`
**Estado:** Abierta

**Qué apareció.**
La caducidad y el débito manual no pueden tocar los puntos de un canje en curso, pero la compra no
reserva puntos: los debita recién cuando la pasarela aprueba el pago. Mientras tanto, el canje sólo
existe como un cobro pendiente. Además, un cobro que el Cliente abandona queda pendiente para
siempre.

**Qué dice la especificación.**
> «Los lotes con `comprometido en canje = sí` no fueron modificados (E2).» (`CO-105`)

> «El débito consume sólo lotes no comprometidos en un canje en curso» (`CO-106`, Notas)

Nada sobre cuándo un lote pasa a comprometido ni cuándo deja de estarlo.

**Qué se hizo.**
El compromiso se deriva del cobro pendiente, sin tocar la compra: si un Cliente tiene un pago
pendiente que canjea N puntos, sus primeros N puntos en orden de caducidad (los que el pago va a
consumir) están comprometidos. Esos no vencen y no se debitan a mano. Un cobro pendiente de más de
24 horas se considera abandonado y deja de comprometer. El atributo del modelo no se usa.

**Qué habría que cambiar.**
`LotePuntos`: reemplazar el atributo «comprometido en canje» por la regla derivada, o declarar qué
operación lo marca y cuál lo limpia. `CO-105` E2 y `CO-106`, Notas: el plazo de 24 horas.

---

### B-10-006 · La caducidad: qué día vence, qué queda en el historial y el aviso previo

**Tipo:** Agregado · **Fecha:** 2026-10-17 · **Alcance:** `CU-PTS-CAD`, `CO-105`, `CU-PTS-CON`, `CU-CFG-PAR` (Fidelización)
**Estado:** Abierta

**Qué apareció.**
Tres puntos de la caducidad que la especificación no fija, y un pedido del responsable.

**Qué dice la especificación.**
> «consulta todos los lotes de puntos con saldo disponible mayor a cero y fecha de caducidad menor
> o igual a la fecha actual» (`CU-PTS-CAD`, paso 2)

`CO-105` no crea movimientos de puntos, y la ficha manda «a cada Cliente afectado una
notificación». Nada sobre avisar antes de vencer.

**Qué se hizo.**

- Un lote vence al empezar su día de caducidad. «Mis puntos» y el panel del Administrador muestran
  «Se pueden usar hasta el» día anterior, para no prometer un día de más.
- Cada lote vencido deja un movimiento de Débito con el motivo «Caducidad» y su saldo resultante:
  sin él, el historial del Cliente mostraba el saldo bajar sin explicación.
- Un solo correo por Cliente con todos sus lotes vencidos y el saldo final.
- **A pedido del responsable** (2026-10-17), un aviso antes de vencer «animando a la compra, como
  todas las tiendas»: sale una sola vez por lote cuando faltan los días configurados o menos, con
  el último día de uso y un enlace a la tienda. Los días son un parámetro nuevo, «aviso previo a la
  caducidad (días)», en Fidelización, con 3 por defecto. El correo de la caducidad se mantiene.

**Qué habría que cambiar.**
`CO-105`: agregar el movimiento de Débito a las postcondiciones y el aviso previo a la Salida (o un
contrato propio para el aviso). `CU-PTS-CAD`: el paso del aviso previo. `CU-CFG-PAR` y
`ConfiguracionSistema`: el parámetro nuevo. `CU-PTS-CON` paso 2: «se pueden usar hasta».

---

### B-10-007 · El ciclo sin lotes vencidos no deja entrada en el log

**Tipo:** Corrección · **Fecha:** 2026-10-17 · **Alcance:** `CU-PTS-CAD` A1, `CO-105`
**Estado:** Abierta

**Qué apareció.**
La ficha y el contrato no dicen lo mismo sobre el ciclo que no encuentra nada.

**Qué dice la especificación.**
> «El evento queda registrado en el log con resultado "ciclo completado sin lotes vencidos".»
> (`CU-PTS-CAD`, A1)

`CO-105` sólo declara una entrada por lote invalidado.

**Qué se hizo.**
Lo del contrato: sin lotes vencidos no se registra nada, como el ciclo del stock en local (plan
18). El ciclo corre todos los días y llenaría el log de entradas sin contenido.

**Qué habría que cambiar.**
`CU-PTS-CAD` A1: quitar el registro en el log.

---

### B-10-008 · El ajuste manual no elige la caducidad

**Tipo:** Corrección · **Fecha:** 2026-10-17 · **Alcance:** `CU-PTS-CAD` Comentarios, `CO-105` Notas, `CO-106`
**Estado:** Abierta

**Qué apareció.**
Dos textos permiten al Administrador elegir otra caducidad para el lote de un ajuste; el contrato
del ajuste no recibe ninguna fecha.

**Qué dice la especificación.**
> «los lotes creados por ajuste manual de CU-PTS-ADM heredan la misma caducidad estándar salvo que
> el Administrador indique lo contrario» (`CU-PTS-CAD`, Comentarios; `CO-105`, Notas)

> «registrarAjusteManualDePuntos(cliente, tipo, cantidad, motivo)»; «la fecha de caducidad
> estándar de ConfiguracionSistema» (`CO-106`)

**Qué se hizo.**
Lo de `CO-106`: el lote del ajuste vence siempre en la fecha estándar. El formulario no tiene campo
de fecha.

**Qué habría que cambiar.**
`CU-PTS-CAD` Comentarios y `CO-105` Notas: quitar «salvo que el Administrador indique lo
contrario».

---

### B-10-009 · Un lote que falla al vencer queda registrado como incidente

**Tipo:** Agregado · **Fecha:** 2026-10-17 · **Alcance:** `CO-105` E1
**Estado:** Abierta

**Qué apareció.**
E1 pide registrar el incidente «con el detalle del error» sin decir dónde.

**Qué dice la especificación.**
> «se revierte el cambio para ese lote, se registra el incidente y se continúa procesando los
> demás» (`CO-105`, Excepciones)

**Qué se hizo.**
Una entrada de auditoría «Fallo en la caducidad de un lote de puntos» con el lote, el Cliente y el
error. El lote queda como estaba y el ciclo siguiente lo reintenta.

**Qué habría que cambiar.**
La acción nueva en el enumerado del registro de auditoría.

---

### B-10-010 · El panel del ajuste muestra lo comprometido, y sólo para cuentas activas

**Tipo:** Agregado · **Fecha:** 2026-10-17 · **Alcance:** `CO-191`, `CO-106`
**Estado:** Abierta

**Qué apareció.**
El panel de `CO-191` muestra los puntos comprometidos «aparte», y la precondición exige una cuenta
activa.

**Qué dice la especificación.**
> «Los puntos comprometidos se muestran aparte porque no pueden debitarse manualmente.» (`CO-191`,
> Notas)

**Qué se hizo.**
El panel marca en cada lote cuánto está en un canje y, debajo de la cantidad, el máximo debitable.
Una cuenta que no está activa no ofrece el enlace a sus puntos y, si se entra por la dirección, se
vuelve a la ficha con el aviso.

**Qué habría que cambiar.**
Nada.

---

### B-10-011 · La ficha del Cliente gana un enlace a sus puntos

**Tipo:** Corrección · **Fecha:** 2026-10-17 · **Alcance:** `CO-195`, `CU-CLI-CON` paso 6, `CU-PTS-ADM` paso 1
**Estado:** Abierta

**Qué apareció.**
Dos casos de uso no dicen lo mismo sobre la ficha del Cliente. El responsable aprobó la lectura de
`CU-PTS-ADM` (plan 10, segunda parte, ambigüedad 7).

**Qué dice la especificación.**
> «Sin acciones de modificación: las operaciones sobre una cuenta de cliente pertenecen a su
> titular» (`CO-195`, Responsabilidades)

> «El Administrador localiza la cuenta del Cliente (CU-CLI-CON) y selecciona «Ajustar puntos».»
> (`CU-PTS-ADM`, paso 1)

**Qué se hizo.**
La ficha sigue sin formularios y sin acciones sobre los datos personales. Gana un único enlace,
«Puntos», a la pantalla de `CU-PTS-ADM`, sólo si la cuenta está activa. El fundamento de `CO-195`
son los datos personales, que el ajuste de puntos no toca.

**Qué habría que cambiar.**
`CO-195` y `CU-CLI-CON` paso 6: «Sin acciones de modificación sobre los datos de la cuenta; ofrece
el acceso a sus puntos (`CU-PTS-ADM`)».

---

### B-10-012 · Todo reembolso descuenta los puntos que ganó la unidad

**Tipo:** Corrección · **Fecha:** 2026-10-19 · **Alcance:** RF-19, `CO-098`, `CO-027`, `CO-101`, `CO-154`
**Estado:** Abierta

**Qué apareció.**
Un Cliente compraba, sumaba puntos y, al cancelar o devolver, recibía el valor en puntos y
conservaba los que había ganado (B-09-004).

**Qué dice la especificación.**
> «En caso de devolución posterior, el sistema debe descontar del saldo del cliente los puntos
> correspondientes al monto reembolsado, si estos ya hubieran sido acreditados.» (RF-19)

Ninguno de los contratos de reembolso lo declara.

**Qué se hizo** (decisión del responsable, plan 00, C2).
Cada reembolso de una unidad pagada en dinero debita lo que esa unidad sumó: la acreditación de la
compra repartida en proporción a lo pagado, hacia abajo. Se debita sólo lo libre (nunca lo
comprometido en un canje) y el saldo nunca queda negativo. Alcanza a la cancelación del artículo
demorado, la cancelación de pre-ventas en lote, la devolución, el arrepentimiento y el
vencimiento en el local. El débito queda en el historial con su línea y el motivo «Descuento de
los puntos ganados con la compra».

**Qué habría que cambiar.**
`CO-098`, `CO-027`, `CO-101` y `CO-154`: la postcondición del débito. RF-19 queda como está.

---

### Nota de cierre · 2026-10-17

El módulo queda completo: `CU-PTS-CAD` y `CU-PTS-ADM` verificados con sus tres contratos, y el
aviso previo que pidió el responsable. El Temporizador suma la caducidad. Las siete puertas pasan.
Quedan abiertas las enmiendas de B-10-005 a B-10-009 y B-10-011.
