> **Tipo: Normativo** una vez aprobado. Antes de la aprobación es una propuesta.
> Se escribe **antes** de programar y **no se reescribe** después: si algo cambió durante la
> construcción, eso va a la bitácora del módulo, no acá.

# Plan — `00` El circuito con los proveedores: pedidos, pre-ventas y llegadas

**Estado del plan:** Aprobado el 2026-10-26 con las decisiones del responsable de la sección 3 ·
**Fecha:** 2026-10-26

Recorrer el circuito con el correo de prueba mostró que la pre-venta y la reposición son lo mismo
visto desde el proveedor —pedí tanto, llega tanto—, pero viven en dos circuitos que no se hablan,
que el pedido al proveedor no queda registrado y que el stock de lo pedido se cuenta dos veces. El
responsable decidió reestructurar el flujo alrededor del **pedido a proveedor**, como lo hacen las
tiendas que venden contra mercadería en camino. El documento de análisis se enmienda después, con
lo que registren las bitácoras (el responsable tiene 15 días para eso).

**Ningún código nuevo de caso de uso ni de contrato se asigna acá** (`CLAUDE.md`). Las operaciones
nuevas se nombran por lo que hacen y sus pruebas, por su nombre; llevarán el código cuando el
responsable lo asigne.

---

## 1. El modelo

**Pedido a proveedor** (concepto nuevo): un proveedor, su origen, la fecha estimada de llegada y
sus líneas (producto, cantidad pedida, cantidad recibida, estado). Nace **sólo cuando el pedido
sale**, de cuatro lugares:

| Origen | Cuándo |
| --- | --- |
| Cierre de una sesión de revisión de novedades | `CO-074` exitoso desde `CU-ALT-REV` |
| Despacho de Restock | `CO-074` exitoso desde `CU-RST-APR` (`CO-072`) |
| Alta de un lote con fecha de llegada | El pedido se hizo por fuera del sistema; el alta lo registra |
| A mano | «Nuevo pedido a proveedor», para un producto que ya existe |

**Pre-venta = vender lo que viene en camino.** Un producto editorial sin stock con unidades
pendientes en un pedido pasa a Pre-venta y se puede reservar hasta su **cupo**: lo pendiente, menos
el margen global de Parámetros, menos lo ya reservado. Con el cupo lleno, la ficha ofrece
«Avisarme», la lista de espera que ya existe. Con stock en el local se vende el stock; al agotarse,
si hay pedido en camino, pasa solo a Pre-venta.

**Una sola llegada.** «Pedidos por llegar» lista los pedidos con líneas abiertas. Al confirmar lo
que llegó: en un producto en Pre-venta, se cubren las reservas en orden (`CO-013`); en uno sin
reservas, se suma al stock. Lo que sobra va a stock y dispara los avisos (`CO-077`). La línea
queda abierta con lo pendiente, o se cierra sin recibir con motivo.

---

## 2. Qué cubre

| # | Qué | Casos de uso | Contratos |
| --- | --- | --- | --- |
| A | **El producto de una novedad o de un lote en pre-venta nace con stock cero**; lo declarado es la cantidad pedida (B-01-016) | `CU-ALT-REV`, `CU-ALT-NAC`, `CU-ALT-IMP`, `CU-ALT-TRA` | `CO-022`, `CO-003`, `CO-009`, `CO-013` |
| B | **El pedido a proveedor queda registrado**, por cualquiera de sus orígenes | `CU-RST-PED`, `CU-RST-APR`, `CU-ALT-REV` | `CO-074`, `CO-072`, `CO-025` |
| C | **Nuevo pedido a proveedor a mano** | Nuevo, sin código | — |
| D | **El cupo de la pre-venta** y el paso automático a Pre-venta | `CU-TDA-CRA`, `CU-TDA-CRM`, `CU-TDA-CMP`, `CU-RST-SUS`, `CU-CFG-PAR` | `CO-083`, `CO-084`, `CO-089`, `CO-075`, `CO-130` |
| E | **Pedidos por llegar**: registrar lo que llegó y cerrar lo que no llegará | Nuevo, sin código; generaliza `CU-ALT-TRA` | `CO-013`, `CO-077` |
| F | **Consultar propuestas de restock**, también las cerradas (B-05-009) | Nuevo, sin código | — |
| G | **Los correos que no son de novedades** no fallan; la demora se ofrece registrar (B-04-010) | `CU-ALT-NOV`, `CU-PRV-COL`, `CU-ALT-DEM` | `CO-017` |
| H | **Redactar a mano un correo de proveedor** y revisar la casilla en el momento | Herramienta de demostración, fuera del sistema | — |

---

## 3. Decisiones del responsable (2026-10-26)

| # | Pregunta | Decisión |
| --- | --- | --- |
| 1 | ¿Cuándo se abre la pre-venta? | **Contra pedido enviado**: cupo fijo, nunca se vende lo que no se pidió |
| 2 | ¿Margen del cupo global o por pedido? | **Global**, un parámetro de Compra online |
| 3 | ¿Proveedores no editoriales (figuras, merchandising)? | **No por ahora**: la pre-venta sigue siendo editorial (I-06 queda) |
| 4 | Producto con stock y con pedido en camino | **Se vende el stock; al agotarse se abre la reserva** |

Y las recomendaciones del plan anterior, que siguen: la línea parcial queda abierta; lo que llega de
más se acepta y se audita; lo que no llega se cierra sin recibir con motivo; un correo que no es de
novedades se puede descartar también después de procesado; la respuesta de un proveedor a un
pedido se descarta en la cola.

---

## 4. Ambigüedades que quedan, con lo que se hace

| # | Dónde | Las dos lecturas | Lo que se hace |
| --- | --- | --- | --- |
| 1 | Las pre-ventas que ya existen en la base | Quedan sin cupo (no se pueden reservar) / se les arma un pedido | **Una migración les arma un pedido** «registrado» con lo que tenían como stock (o sus reservas, si eran más) y les deja el stock en cero: corrige de paso el doble conteo |
| 2 | Pre-venta de un producto sin fecha estimada | Exigir fecha / admitirla sin fecha | **Sin fecha se admite**: la ficha dice «Se envía cuando llegue»; el ciclo de vigilancia sólo mira las que tienen fecha |
| 3 | Un lote en pre-venta de una editorial sin proveedor cargado | No se registra pedido / se registra sin proveedor | **Se registra sin proveedor**: el pedido se hizo por fuera y el cupo lo necesita |
| 4 | El cupo y el carrito | El carrito reserva cupo / no | **No reserva** (`CO-083`): el cupo se controla al agregar y, con el producto bloqueado, al confirmar el pago; si se llenó mientras se pagaba, el cobro se reembolsa como el stock perdido (B-07-035) |
| 5 | «Avisarme» con la pre-venta completa | Sólo para Agotado (`CO-075`) / también para la pre-venta completa | **También para la pre-venta completa**: la lista de espera que se avisa cuando sobra al llegar |

---

## 5. Orden de construcción

| # | Qué | Motivo |
| --- | --- | --- |
| 1 | El pedido a proveedor y su migración (B, A) | Todo lo demás lo lee |
| 2 | Cupo y paso automático a Pre-venta (D) | Es lo que ve el Cliente |
| 3 | Pedidos por llegar (E) y nuevo pedido a mano (C) | La otra punta del pedido |
| 4 | Propuestas de restock (F) | Lee pedidos y llegadas |
| 5 | Correos que no son de novedades (G) y la herramienta (H) | Independientes |
| 6 | Cierre | Siete puertas, capturas, `ESTADO.md`, `COBERTURA.md`, bitácoras 01, 04, 05 y 07 |

---

## 6. Riesgos

| Riesgo | Cómo se cubre |
| --- | --- |
| Dos clientes toman el último lugar del cupo a la vez | El producto se bloquea al confirmar el pago y el cupo se vuelve a contar; prueba de concurrencia |
| Dos caminos de llegada (pre-ventas y pedidos) suman el mismo stock dos veces | Un único servicio registra la llegada contra las líneas del pedido; las dos pantallas lo usan |
| La migración sobre la base de presentación | Se prueba sobre una copia; las pre-ventas sin reservas ni stock quedan con un pedido de cero que se puede cerrar |
| Las pruebas que daban por bueno el stock con el que nacía una pre-venta | Se corrigen las pruebas, no el arreglo |

---

## 7. Fuera de alcance

- Pre-ventas de productos no editoriales y proveedores no editoriales (decisión 3).
- Pre-venta por fecha de corte y margen por pedido.
- Vincular la respuesta de un proveedor con su pedido.
