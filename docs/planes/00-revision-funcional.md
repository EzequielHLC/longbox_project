> **Tipo: Normativo** una vez aprobado. Antes de la aprobación es una propuesta.
> Se escribe **antes** de programar y **no se reescribe** después: si algo cambió durante la
> construcción, eso va a la bitácora del módulo, no acá.

# Plan — `00` Revisión funcional y recorte para el cierre

**Estado del plan:** Aprobado el 2026-10-19 · **Fecha:** 2026-10-19

El código tiene que estar terminado antes de noviembre. Revisando el sistema contra su alcance,
sus límites y sus procesos automáticos, aparecieron funciones que hacen aguas (reembolsos sin
devolución, devoluciones que nunca terminan, reglas parecidas que se contradicen) y otras que el
alcance no pide y cuestan más de lo que aportan. El responsable aprobó el 2026-10-19: **corregir
lo que hace aguas, completar lo que el alcance promete y descartar el resto, con su
justificación**. Una primera versión de este plan (el reclamo como ticket, el reembolso en pesos
por la pasarela, anexar lo guardado al próximo pedido) quedó descartada por ese recorte y no se
construye.

---

## 1. Qué se corrige

### C1 · Devoluciones: la ley, simple y sin comprometer al negocio

Un solo formulario de reclamo con **dos tipos**. Lo que no sea registrar (la prueba de
destrucción, la devolución del artículo) se coordina **por fuera del sistema**, por correo o
teléfono, con los datos de contacto a la vista en la ficha del caso.

| | Arrepentimiento | Garantía |
| --- | --- | --- |
| **Motivos** | Arrepentimiento (reemplaza a «Disconformidad») | Defecto de fabricación, Error de imprenta |
| **Base legal** | Revocación de la venta a distancia (Ley 24.240, art. 34; botón de arrepentimiento, Res. 424/2020) | Garantía legal de la cosa (Ley 24.240) |
| **Quién y desde dónde** | **El botón de arrepentimiento**, visible en la cabecera de la tienda y **sin registración**: con sesión, desde el pedido; sin sesión, con el número de pedido y el correo de la compra. Sirve también al invitado | El Cliente desde «Mi cuenta», en el detalle del pedido |
| **Pedidos** | Sólo online (venta a distancia) | Online y de mostrador con cuenta |
| **Plazo** | «Plazo de arrepentimiento (días)», mínimo legal 10, desde el despacho; en un pedido retirado, desde el retiro | **«Plazo de garantía (días)», parámetro nuevo**, 90 por defecto, con el mismo punto de partida |
| **Fotos** | No | Obligatorias, 1 a 5 (como hoy) |
| **El artículo** | El local lo recibe (coordinado por fuera) y **vuelve al stock** al resolver | No vuelve: la prueba de destrucción se ve por el canal externo |
| **Resolución** | **Reembolso por el medio de pago**: se registra; el dinero se devuelve desde el panel de la pasarela. Lo pagado con puntos vuelve en puntos | **Cambio** por un tomo de la **misma editorial y el mismo formato**, que queda en el stock en local del Cliente con **envío sin costo**; o **reembolso en puntos**; o **reembolso por el medio de pago** (sólo pedidos online) |

En los dos: el Cliente recibe por correo **el código de su caso** al abrirlo (Res. 424/2020); se
descuentan los puntos que ganó la unidad (C2); el rechazo sigue con motivo obligatorio.

Se retiran `DevolucionFisica` y el estado «Reservado para cambio» de `ArticuloRetenido`.

**Una limitación, a propósito.** El reembolso por el medio de pago no se ofrece en una compra de
mostrador: devolver efectivo desde el sistema exigiría transacciones negativas en la caja (I-09).
En el mostrador, el defecto se resuelve con cambio o puntos, o por fuera del sistema.

### C2 · Los puntos de un reembolso

- Todo reembolso de una unidad pagada en dinero **descuenta los puntos que ganó esa unidad**
  (RF-19): la acreditación de la compra, repartida en proporción a lo pagado, hacia abajo.
  - En un reembolso en puntos, se netea: se acredita el valor menos lo ganado.
  - En uno por el medio de pago, se debita lo libre (sin tocar lo comprometido en un canje),
    sin dejar el saldo negativo.
  - Alcanza a: la devolución, el arrepentimiento, la cancelación de pre-ventas en lote, la del
    artículo demorado y el vencimiento en el local.
- El vencimiento del stock en local **devuelve el valor en puntos a todas las procedencias**: el
  despacho diferido deja de ser la excepción.

### C3 · Cobros abandonados

El Temporizador descarta los cobros pendientes de más de 24 horas. Un pago que la pasarela
aprueba después de descartado **se reembolsa solo** y se avisa al Cliente.

---

## 2. Qué se completa para cumplir el alcance

| # | Qué | Por qué |
| --- | --- | --- |
| A1 | `CO-016`: el Temporizador revisa la casilla de novedades, con la frecuencia de Parámetros | Proceso automático que el alcance promete («Extracción asistida de novedades») |
| A2 | `CO-155`: la sincronización de cotizaciones entra al Temporizador | Proceso automático del pricing de importados |
| A3 | Sección Seguridad de Parámetros (`CO-114`, `CO-130`; B-12-001) | «Seguridad, trazabilidad y conciliación» |
| A4 | `CU-CLI-BAJ` | Ley 25.326 y BR-11. Plan propio |
| A5 | `CU-REP-GEN` mínimo | RF-23. Plan propio |
| A6 | Cerrar `CU-TDA-CAT`, `CU-CAT-GRM`, `GRB`, `ETM`, `ETB`: lo que esperaban ya existe | Sólo pruebas |
| V1 | Pruebas de contrato de las altas de lote | Módulo 01, prioridad Alta, dinero |
| V2 | Pruebas de contrato de lo construido sin verificar | Condición de salida |

---

## 3. Qué se descarta, y por qué

Queda declarado como **próxima implementación**. El lugar del documento es la tabla «Alcance
construido y alcance especificado».

| Se descarta | Justificación |
| --- | --- |
| Reclamo como ticket con conversación | No está en el alcance. Devoluciones es de prioridad Media y frecuencia baja según su ficha. Un canal externo (correo o teléfono) cumple la misma función sin mensajería, adjuntos ni avisos nuevos |
| Prueba de destrucción dentro del sistema | Se pide y se ve por el canal externo; el sistema registra la resolución, que es lo que deja traza |
| Reembolso en pesos por la API de la pasarela | Exigiría transacciones negativas en la caja (contra I-09) y probar la API real. Es infrecuente: se hace desde el panel de la pasarela y el sistema lo registra |
| Anexar lo guardado en el local al próximo pedido | Comodidad. Ya existen pagar el envío, el envío gratis desde el mínimo y el retiro; tocaría la compra verificada |
| Vincular pedidos de invitado a una cuenta | El registro no verifica el correo: haría falta un circuito de confirmación. El botón de arrepentimiento por número de pedido y correo cubre lo que el invitado necesitaba |
| Estado «Entregado» y plazo desde la recepción | Límite declarado: «No rastreará el paquete más allá del estado Despachado» |
| Limpieza de carritos de invitado y aviso de carrito abandonado | Sin caso de uso; sólo un parámetro en el modelo |
| Costo de envío por peso y destino | Requiere el peso de cada producto y una cuenta comercial con el operador |

---

## 4. Ambigüedades

| # | Dónde | Las dos lecturas | Decisión |
| --- | --- | --- | --- |
| 1 | Los valores legales de los plazos | El sistema no puede saberlos | **Son parámetros.** El de arrepentimiento conserva el piso de 10 días en la base; el de garantía nace en 90. El responsable confirma los valores con su tutor |
| 2 | El envío en el arrepentimiento | Se reembolsa o no | **Se reembolsa sólo si se devuelve el pedido entero**, como lo pagado. A confirmar con el tutor |
| 3 | Un caso por línea (I-19) con varias unidades | — | Se mantiene: un caso cubre una unidad (B-09-003) |
| 4 | El código del caso (Res. 424/2020) | En la pantalla o por correo | **Los dos**: en la confirmación y en un correo inmediato |

---

## 5. Orden

| # | Qué | Sesiones |
| --- | --- | --- |
| 1 | C2 | 0,5 |
| 2 | C1 | 1,5 |
| 3 | C3, A1, A2 | 1 |
| 4 | A3, A6 | 0,75 |
| 5 | A4, A5 (con sus planes) | 2 |
| 6 | V1, V2 | 3,5 |
| 7 | Cierre | 1 |

**Total: unas 10 sesiones.**

---

## 6. Riesgos

| Riesgo | Dónde | Cómo se cubre |
| --- | --- | --- |
| Alguien abre un arrepentimiento sobre un pedido ajeno sin sesión | C1 | Número de pedido **y** correo de la compra tienen que coincidir; respuesta idéntica si no coinciden. Prueba |
| Reembolsar dos veces la misma unidad | C1 | I-19 en la base: un caso por línea, en cualquier estado |
| Los puntos ganados se descuentan dos veces | C2 | Cada descuento queda vinculado a la línea; prueba de doble reembolso |
| Un pago tardío sobre un cobro descartado | C3 | Reembolso automático, idempotente |
| El monitoreo de la casilla sale a la red en las pruebas | A1 | Pasa por la puerta única de integraciones, interceptada |
