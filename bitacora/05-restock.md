# Bitácora — `05` Restock

> Registro de lo que se decidió construyendo este módulo. **Se anexa, no se reescribe.**
> Una entrada resuelta se marca; no se borra.
>
> Este archivo es el material que el responsable lee para decidir qué se enmienda en el documento
> de análisis. Escribí para alguien que conoce el dominio y no tiene el código a la vista.

---

## Entradas

### B-05-001 · El aviso de reposición sale con toda suba de stock

**Tipo:** Agregado · **Fecha:** 2026-10-14 · **Alcance:** `CU-RST-NOT` paso 1, `CO-077`, `CU-CAT-EDI`, `CO-013`, `CO-154`
**Estado:** Abierta — decidida por el responsable el 2026-10-14 (plan 05, amb. 1)

**Qué apareció.**
Las cuatro altas que nombra `CU-RST-NOT` crean productos nuevos o activan pre-ventas: ninguno de esos productos puede tener suscriptores. Lo pedido a un proveedor entra editando el stock del producto.

**Qué dice la especificación.**
> «El evento es disparado por la finalización exitosa del alta de unidades en CU-ALT-NAC, CU-ALT-IMP, CU-ALT-TRA o CU-ALT-REV» (`CU-RST-NOT`, paso 1)

**Qué se hizo.**
Toda suba del stock a la venta dispara el aviso, con N igual a lo que subió: la edición del producto, las unidades que quedan libres al llegar una pre-venta y el artículo retenido que vuelve por vencimiento.

**Qué habría que cambiar.**
`CU-RST-NOT` paso 1 y `CO-077` Referencias Cruzadas: «toda operación que aumente el stock a la venta».

---

### B-05-002 · El aviso se pide sobre un producto Agotado

**Tipo:** Corrección · **Fecha:** 2026-10-14 · **Alcance:** `CO-075`, `CU-RST-SUS` Precondiciones
**Estado:** Abierta — decidida por el responsable el 2026-10-14 (plan 05, amb. 2 y 9)

**Qué apareció.**
El sistema pasa a Agotado todo producto que llega a cero unidades.

**Qué dice la especificación.**
> «El producto está en estado Activo con stock igual a cero.» (`CO-075`, Precondiciones)

**Qué se hizo.**
El aviso se admite sobre un producto Agotado, o Activo sin stock. Lo pide el Cliente con sesión; el invitado va al ingreso y el personal no lo ve.

**Qué habría que cambiar.**
`CO-075` y `CU-RST-SUS`: «Agotado, o Activo con stock cero».

---

### B-05-003 · Qué entra en la propuesta y a qué proveedor va

**Tipo:** Agregado · **Fecha:** 2026-10-14 · **Alcance:** `CO-067`, `CO-071`, `CU-RST-PRO` paso 4, `CU-RST-APR` A2
**Estado:** Abierta — decidida por el responsable el 2026-10-14 (plan 05, amb. 3 y 4)

**Qué apareció.**
Muchos productos se cargaron a mano y no tienen proveedor, y la propuesta agrupa por proveedor. Además, `CU-RST-APR` deja agregar «cualquier producto del catálogo» y la línea de la propuesta pide un producto editorial.

**Qué dice la especificación.**
> «LineaPropuestaRestock "0..*" -- "1" ProductoEditorial : pide» (Área 4)

Qué hacer con un producto sin proveedor: `Nada`.

**Qué se hizo.**
Entran sólo los productos editoriales Activos o Agotados. Un producto sin proveedor va al proveedor activo que tiene su editorial como habitual, si hay uno solo; si no, al grupo «Sin proveedor», que se puede descartar pero no despachar hasta asignarle uno.

**Qué habría que cambiar.**
`CU-RST-PRO` paso 4: el criterio de asignación de proveedor.

---

### B-05-004 · El ciclo semanal intenta todos los días

**Tipo:** Agregado · **Fecha:** 2026-10-14 · **Alcance:** `CO-067`, `CU-RST-PRO` paso 1, E1 y E3, `CU-CFG-PAR`
**Estado:** Abierta — decidida por el responsable el 2026-10-14 (plan 05, amb. 5 y 6)

**Qué apareció.**
El Temporizador corre una vez por día y no hay un día fijo de la semana. `CU-CFG-PAR` no da valores por defecto para la cantidad mínima ni para el margen.

**Qué dice la especificación.**
> «No existe una `PropuestaRestock`, en cualquier estado, cuya `fecha de generación` caiga dentro de los 7 días previos.» (`CO-067`, Precondiciones)

**Qué se hizo.**
El ciclo intenta todos los días y genera cuando no hay propuesta de los últimos 7 días ni una pendiente. Cuando no genera por falta de elegibles (E1) o por una pendiente (E3), lo registra y avisa una vez por semana, no todos los días. Por defecto, cantidad mínima 3 y margen 2.

**Qué habría que cambiar.**
`CU-RST-PRO` paso 1: «el ciclo corre diariamente y genera a lo sumo una propuesta por semana». `CU-CFG-PAR`: los valores por defecto.

---

### B-05-005 · Reintentos seguidos y la notificación fallida vuelve a la fila

**Tipo:** Agregado · **Fecha:** 2026-10-14 · **Alcance:** `CO-077` E1
**Estado:** Abierta — decidida por el responsable el 2026-10-14 (plan 05, amb. 7 y 8)

**Qué apareció.**
El aviso sale en la misma operación que subió el stock. Una espera entre reintentos colgaría esa pantalla.

**Qué dice la especificación.**
> «se reintenta hasta tres veces. Si persiste, se registra el incidente, la suscripción se marca como Notificación fallida sin eliminarla de la lista de espera» (`CO-077`, Excepciones)

**Qué se hizo.**
Tres intentos seguidos, como el correo a proveedores. Una suscripción con notificación fallida compite en la ronda siguiente con su turno original.

**Qué habría que cambiar.**
`CO-077` E1: «tres intentos seguidos». La notificación fallida entra en las rondas siguientes.

---

### B-05-006 · Reponer stock a mano devuelve el producto a la venta

**Tipo:** Agregado · **Fecha:** 2026-10-14 · **Alcance:** `CU-CAT-EDI`, `CO-030`, `CU-RST-NOT`
**Estado:** Abierta

**Qué apareció.**
Un producto que se queda sin unidades pasa a Agotado. Al editarle el stock para cargar lo que llegó
del proveedor, seguía en Agotado: no se podía comprar ni vender aunque tuviera unidades.

**Qué dice la especificación.**
Qué pasa con el estado cuando la edición sube el stock de un Agotado: `Nada`.

**Qué se hizo.**
Si la edición deja un producto Agotado con stock, pasa a Activo y el cambio de estado queda en la
misma entrada de auditoría de la modificación. La edición no hace lo inverso: bajar el stock a cero
a mano no lo pasa a Agotado.

**Qué habría que cambiar.**
`CO-030` Postcondiciones: «si el producto estaba Agotado y el stock quedó mayor que cero, pasó a
Activo».

---

### Nota de cierre · 2026-10-14

Los cinco casos de uso están construidos: el aviso de reposición desde la ficha pública, el aviso
FIFO con cada suba de stock, la propuesta semanal o manual, y su despacho o descarte por proveedor.
Los productos sin proveedor quedan agrupados aparte hasta que su editorial tenga uno habitual.

---

### B-05-007 · El Cliente ve y cancela sus avisos de stock desde «Mi cuenta»

**Tipo:** Agregado · **Fecha:** 2026-10-21 · **Alcance:** `CU-RST-SUS`, `CO-076`
**Estado:** Abierta — decidida por el responsable el 2026-10-21 (plan 00 de interfaz, segunda parte, 15)

**Qué apareció.**
El Cliente sólo podía ver o cancelar un aviso de reposición entrando a la ficha de cada producto.

**Qué dice la especificación.**
> «La suscripción permanece activa hasta que CU-RST-NOT envíe la notificación al Cliente por turno
> FIFO, o hasta que el Cliente la cancele manualmente.» (`CU-RST-SUS`, postcondiciones)

No dice desde dónde.

**Qué se hizo.**
«Mi cuenta» suma «Avisos de stock»: los que esperan, con el lugar en la fila, y los ya avisados de
los últimos 90 días. «Cancelar aviso» es `CO-076`, el mismo de la ficha, y tampoco se audita.

**Qué habría que cambiar.**
`CU-RST-SUS` A1: «desde la ficha del producto o desde la sección Avisos de stock de su cuenta».

---

### B-05-008 · Las cantidades de un proveedor se guardan de una vez

**Tipo:** Agregado · **Fecha:** 2026-10-21 · **Alcance:** `CU-RST-APR`, `CO-069`
**Estado:** Abierta — decidida por el responsable el 2026-10-21 (plan 00 de interfaz, segunda parte, 14)

**Qué apareció.**
Una propuesta automática trae cientos de productos, y cada cantidad se guardaba con su propio botón:
ajustar diez eran diez envíos.

**Qué dice la especificación.**
`Nada` sobre cuántas líneas se ajustan por vez. `CO-069` ajusta una.

**Qué se hizo.**
Cada proveedor de la propuesta es un bloque plegable con sus cifras, y un solo «Guardar cantidades»
aplica `CO-069` a cada línea que cambió, todo o nada: si una cantidad no es válida, no cambia
ninguna. La propuesta se puede filtrar por título.

**Qué habría que cambiar.**
`CU-RST-APR` paso de ajuste: «el Administrador ajusta las cantidades de un proveedor y las guarda
juntas».

---

### B-05-009 · Las propuestas cerradas no se ven y lo pedido por restock no tiene ingreso

**Tipo:** Agregado · **Fecha:** 2026-10-26 · **Alcance:** `CU-RST-APR`, `CU-RST-NOT`, `CU-ALT-TRA`, `CO-013`, `CO-072`, `CO-077`, `PropuestaRestock`, `LineaPropuestaRestock`
**Estado:** Resuelta — plan 00 del circuito de proveedores, aprobado el 2026-10-26; ver B-05-010. Los códigos de los casos de uso nuevos los asigna el responsable

**Qué apareció.**
Probando el restock con el correo de prueba, el responsable quiso volver a ver las propuestas que
ya había despachado y registrar la llegada de lo pedido. Ninguna de las dos cosas se puede hacer:
una propuesta cerrada desaparece de la pantalla, y cuando la mercadería llega, la única forma de
sumarla es editar el stock de cada producto a mano (B-05-006). Esa edición no deja rastro de a qué
pedido corresponde, ni distingue si llegó todo, una parte o nada.

**Qué dice la especificación.**
> «El Administrador accede al panel de propuestas de restock y selecciona la propuesta activa.»
> (`CU-RST-APR` paso 1) · «El evento es disparado por la finalización exitosa del alta de unidades
> en CU-ALT-NAC, CU-ALT-IMP, CU-ALT-TRA o CU-ALT-REV, según el canal de ingreso.» (`CU-RST-NOT`
> paso 1) · «El lote existe y contiene productos en estado Pre-venta.» (`CO-013`, precondiciones)

Ningún caso de uso consulta las propuestas cerradas. Los cuatro canales de ingreso de
`CU-RST-NOT` dan de alta productos nuevos o confirman pre-ventas; ninguno recibe lo pedido por
restock de un producto que ya existe. `CO-013`, el que más se parece, exige productos en Pre-venta
y resuelve reservas y demoras que una reposición no tiene.

**Qué se hizo.**
Nada todavía. Por `CLAUDE.md`, un caso de uso que no existe no se inventa: se consulta.

**Qué habría que cambiar.**
Dos casos de uso nuevos en el módulo 05, con los códigos que asigne el responsable:

- **Consultar propuestas de restock**: el listado de las propuestas, abiertas y cerradas, con su
  fecha, su disparo y su resumen por proveedor, y la ficha de cada una con sus líneas, su estado de
  despacho y, si se aprueba el siguiente, su estado de recepción.
- **Registrar el ingreso de un pedido de restock**: las líneas despachadas pendientes de recibir,
  agrupadas por proveedor y pedido, con la misma mecánica que «Pre-ventas por llegar» de
  `CU-ALT-TRA` (lista, revisión de lo recibido, confirmación). Al confirmar, el stock de cada
  producto sube en lo recibido, un Agotado vuelve a Activo (B-05-006), se dispara `CO-077` y queda la
  auditoría. Requiere un contrato propio: `CO-013` no aplica fuera de la Pre-venta.

Y en el modelo de dominio, `LineaPropuestaRestock` gana el estado de recepción, la cantidad
recibida y la fecha.

---

### B-05-010 · Los pedidos a proveedor quedan registrados, su llegada se confirma en «Pedidos por llegar» y las propuestas se consultan

**Tipo:** Agregado · **Fecha:** 2026-10-26 · **Alcance:** `CU-RST-PED`, `CU-RST-APR`, `CU-RST-NOT`, `CU-ALT-REV`, `CU-ALT-TRA`, `CO-013`, `CO-025`, `CO-072`, `CO-074`, `CO-077`
**Estado:** Abierta — decidida por el responsable el 2026-10-26 (plan 00 del circuito de proveedores); reemplaza a B-05-009. **Los códigos de los casos de uso nuevos los asigna el responsable**

**Qué apareció.**
Lo de B-05-009, y algo más que apareció al recorrer el circuito: la pre-venta y la reposición son
lo mismo visto desde el proveedor —pedí tanto, llega tanto—, pero vivían en dos circuitos que no se
hablaban. Lo pedido no quedaba registrado en ningún lado, así que la pre-venta no podía saber
cuánto venía en camino (B-07-042) y la llegada de una reposición no tenía dónde confirmarse.

**Qué dice la especificación.**
`Nada` sobre un registro del pedido: `CO-074` envía el correo y registra el resultado del envío,
pero no lo pedido como algo que va a llegar. Ningún caso de uso consulta las propuestas cerradas ni
recibe lo pedido por restock (B-05-009).

**Qué se hizo.**
- **El pedido a proveedor queda registrado cuando sale**, con una línea por producto y cantidad: el
  correo exitoso de `CO-074` (al cerrar una sesión de revisión, al despachar una propuesta de
  restock, o un pedido a mano) y el alta de un lote en pre-venta, cuyo pedido se hizo por fuera. Si
  el correo falla, no queda nada registrado. Lleva la llegada estimada, que en el despacho de
  restock y en el pedido a mano se puede indicar.
- **«Pedidos por llegar»** (Proveedores, sólo el Administrador): los pedidos abiertos con lo que
  falta y los atrasados. En la ficha de un pedido se carga cuánto llegó de cada producto; la
  pantalla siguiente muestra qué va a pasar —cuántas reservas cubre, cuánto queda a la venta, cuánto
  sigue pendiente, si llegó de más— y recién al confirmar se registra. En un producto en Pre-venta
  lo recibido pasa por `CO-013`; en uno sin reservas suma al stock, lo vuelve Activo y dispara
  `CO-077`. Una línea que llegó en parte queda abierta con lo que falta; lo que llega de más se
  acepta y queda en la auditoría.
- **Lo que no va a llegar se cierra con motivo**, sin tocar el stock. Si el producto estaba en
  Pre-venta sólo por esa línea y nadie lo reservó, deja de estarlo; si tiene reservas, sigue en
  Pre-venta y se avisa que hay que registrar la demora o cancelar la pre-venta.
- **Nuevo pedido a mano**: proveedor, llegada estimada y renglones por código o ISBN de productos que
  ya existen. Sale el mismo correo de `CO-074`.
- **Consultar propuestas de restock**: el listado de todas, también las cerradas, con su fecha, su
  disparo, su estado y lo que se pidió, y la ficha de cada una con sus líneas y el pedido que
  generó cada proveedor.
- La auditoría gana dos acciones: la llegada de un pedido y el cierre de una línea sin recibir.

**Qué habría que cambiar.**
Tres casos de uso nuevos en el módulo 05, con los códigos que asigne el responsable:
**Consultar propuestas de restock**, **Registrar la llegada de un pedido a proveedor** (generaliza
«Pre-ventas por llegar» de `CU-ALT-TRA`, con el cierre de una línea sin recibir como flujo
alternativo) y **Registrar un pedido a proveedor a mano**; cada uno con sus contratos. `CO-074`,
postcondiciones: con el envío exitoso se crea el pedido y sus líneas. `CO-003`/`CO-009` en pre-venta:
también lo crean (B-01-017). En el modelo de dominio, **PedidoProveedor** (proveedor, origen, estado,
llegada estimada, enlace a la propuesta, la sesión o el lote) y **LineaPedidoProveedor** (producto,
cantidad pedida y recibida, estado, motivo de cierre).

---

### B-05-011 · La propuesta pendiente se trabaja también desde su ficha

**Tipo:** Agregado · **Fecha:** 2026-10-28 · **Alcance:** `CU-RST-APR`, `CU-RST-PRC`
**Estado:** Abierta — pedido del responsable el 2026-10-28

**Qué apareció.**
La ficha de una propuesta (`CU-RST-PRC`) era de sólo lectura: para cambiar algo había que ir a
«Restock» con «Trabajar la propuesta».

**Qué dice la especificación.**
> `CU-RST-APR`: el Administrador ajusta cantidades (`CO-069`), quita (`CO-070`) y agrega productos
> (`CO-071`) en la propuesta pendiente.

No dice desde qué pantalla.

**Qué se hizo.**
Si la propuesta está pendiente, su ficha muestra los mismos controles que «Restock»: cantidades,
quitar, agregar y el paso a despachar o descartar cada proveedor. Son las mismas operaciones, y cada
formulario vuelve a la pantalla de la que vino, siempre dentro del sitio. Una propuesta cerrada sigue
siendo de lectura.

**Qué habría que cambiar.**
`CU-RST-PRC`: la ficha de la pendiente lleva a `CU-RST-APR` sin cambiar de pantalla.

---

### B-05-012 · Una propuesta se puede armar a mano, vacía

**Tipo:** Agregado · **Fecha:** 2026-10-28 · **Alcance:** `CU-RST-PRO`, `CU-RST-APR`, `CO-067`, `CO-068`
**Estado:** Abierta — pedido del responsable el 2026-10-28. **Falta el código `CO-NNN` de la
operación nueva**

**Qué apareció.**
El responsable quiere poder pedir a un proveedor lo que él sabe que hace falta, sin esperar a que la
demanda lo muestre.

**Qué dice la especificación.**
> «En lugar del paso 1, el Administrador ejecuta el ciclo manualmente desde el panel de gestión.»
> (`CU-RST-PRO` A1, `CO-068`)

El disparo manual arma la propuesta **desde la demanda**, y su E1 deja **cerrada** la que sale vacía.
Sobre una propuesta armada a mano, `Nada`.

**Qué se hizo.**
- «Armar una a mano» crea una propuesta **vacía y pendiente**, de tipo «Armada a mano», auditada. Se
  carga con «Agregar un producto» (`CO-071`) y sigue el camino de siempre: cantidades, despacho o
  descarte por proveedor.
- Como toda propuesta, **una sola pendiente por vez** (I-21): con otra pendiente se rechaza, también
  si dos Administradores la arman a la vez.
- **No cuenta como el ciclo de la semana**: el ciclo automático de la demanda corre igual.
- **Una pendiente sin productos se puede cerrar** («Cerrar la propuesta vacía»), auditado. Si no,
  bloquearía la siguiente.
- `CO-068` no cambia: el disparo manual sigue mirando la demanda.

**Qué habría que cambiar.**
`CU-RST-PRO`: un flujo alternativo «armar a mano», con su operación y su contrato (código a asignar),
y el cierre de una propuesta vacía. El estado «Armada a mano» en el tipo de disparo.

---

### B-05-013 · La propuesta despachada espera la respuesta del proveedor

**Tipo:** Desvío · **Fecha:** 2026-10-28 · **Alcance:** `CU-RST-APR`, `CU-RST-LLE`, DME-13, `CO-072`, `CO-073`
**Estado:** Abierta — consultado y aprobado por el responsable el 2026-10-28 ([plan de la respuesta
del proveedor](../docs/planes/00-respuesta-del-proveedor.md)). **Faltan los códigos** del caso de
uso nuevo y de sus operaciones

**Qué apareció.**
Despachado el pedido, el proveedor contesta qué manda, cuánto y cuándo, o que no puede. El sistema no
tenía dónde anotarlo: la propuesta ya estaba cerrada y el pedido sólo esperaba la mercadería.

**Qué dice la especificación.**
> DME-13: la propuesta se cierra sola cuando no queda ningún proveedor pendiente de despacho o descarte.

Es correcto para lo que modela, y el código se aparta igual: el responsable quiere seguir la
respuesta desde la propuesta.

**Qué se hizo.**
- La propuesta despachada pasa a **«Esperando respuesta»** y se cierra cuando **todos sus proveedores
  respondieron**. Mientras espera no cuenta como pendiente, así que se puede generar la próxima.
- En cada línea del pedido se anota la respuesta: **confirmada**, **con otra cantidad** o **no
  disponible**, con su motivo. También se anota **la fecha de llegada**. Se hace desde la ficha de la
  propuesta y desde la del pedido, línea por línea, con «Confirmó todo» y «No puede abastecer nada».
  Desde Telegram van las tres de un toque (B-19-019).
- **Lo que se espera es lo confirmado**: cambiar la cantidad cambia lo pendiente, el cupo de la
  pre-venta y cuándo la llegada se da por completa. Lo que llega, o se cierra sin recibir desde
  «Pedidos por llegar», cuenta como respuesta.
- **Si se confirma menos de lo reservado**, se acepta y se avisa. Nada se cancela solo: se resuelve
  con la demora o la cancelación que ya existen.
- **Atrasar la fecha de una pre-venta con reservas es una demora**: no se toca la fecha que ve el
  Cliente y se pide registrar la demora (`CU-ALT-DEM`). Sin reservas, la pre-venta toma la fecha nueva.
- Si a los tres días el proveedor no respondió, un recordatorio por Telegram, una sola vez, y una
  línea en el resumen de la mañana.
- La web y el chat pueden responder a la vez: el pedido se toma con bloqueo de fila.

**Qué habría que cambiar.**
DME-13: el estado «Esperando respuesta» y el cierre por respuesta. Un caso de uso nuevo, «Registrar la
respuesta del proveedor», con sus operaciones (confirmar línea, cambiar la cantidad confirmada, cerrar
lo que no puede abastecer, poner la fecha) y sus contratos. `CO-072` y `CO-073`: la propuesta ya no se
cierra al despachar. En el modelo de dominio, **LineaPedidoProveedor** gana la respuesta y la cantidad
confirmada, y **PedidoProveedor** la fecha del recordatorio.

---

### B-05-014 · El pedido que no salió queda a la vista, y el restock ve la pre-venta sin nada en camino

**Tipo:** Agregado · **Fecha:** 2026-10-28 · **Alcance:** `CO-074`, `CU-ALT-REV`, `CU-RST-PRO`, `CU-RST-LLE`
**Estado:** Abierta — decidido por el responsable el 2026-10-28

**Qué apareció.**
En la VM, Sakamoto Days #24 entró por un borrador y se confirmó en una sesión de revisión. Nació en
Pre-venta, como toda novedad (B-01-017). Al cerrar la sesión, el correo del pedido falló: Gmail rechaza
el inicio de sesión desde la VM. Como el pedido sólo se registraba si salía (decisión 1 del plan del
circuito), el tomo quedó en Pre-venta sin nada en camino, con cupo cero y sin ningún lugar desde donde
volver a pedirlo. El restock tampoco lo proponía, porque sólo mira lo Activo o Agotado.

**Qué dice la especificación.**
> `CO-074` E1: si el envío falla tras tres reintentos, registra el error definitivo en el log y
> notifica al Administrador.

No dice nada de volver a intentarlo, ni de una pre-venta que se queda sin pedido.

**Qué se hizo.**
- **El pedido que no sale al cerrar una revisión queda registrado «Sin enviar»**, con el error, en
  «Pedidos por llegar» (primero, y con su cifra). Desde su ficha se **reintenta el envío** o se
  **descarta** con motivo. También se reintenta desde Telegram, donde llega el aviso con el botón.
- **No da cupo hasta que sale**, porque nadie lo está mandando: lo que viene en camino cuenta sólo de
  pedidos enviados. Tampoco recibe llegadas ni respuestas.
- Si el reintento sale, queda «Por llegar» como si hubiera salido la primera vez: abre sus pre-ventas,
  da cupo y avisa. Si se descarta, la pre-venta sin reservas deja de estarlo, como al cerrar una línea
  sin recibir.
- **Una pre-venta sin nada en camino entra en la propuesta de restock**, con al menos lo reservado como
  cantidad sugerida.
- El despacho de restock y el pedido a mano no cambian: si fallan, ya quedaban para reintentarse desde
  su pantalla (`CO-072` E2 y el formulario).

**Qué habría que cambiar.**
`CO-074` E1: el pedido queda «Sin enviar» para reintentarlo o descartarlo. `CU-RST-PRO` paso 2: entra
también la pre-venta sin nada en camino. En el modelo de dominio, **PedidoProveedor** gana el estado
«Sin enviar» y el error del envío.

---

### B-05-015 · La respuesta del proveedor, en un solo lugar y con una pregunta por vez

**Tipo:** Agregado · **Fecha:** 2026-10-28 · **Alcance:** caso de uso de la respuesta del proveedor (B-05-013, sin código), `CU-RST-APR`
**Estado:** Abierta — plan [00 de la respuesta simple](../docs/planes/00-respuesta-simple-y-tomo-que-vuelve.md), aprobado el 2026-10-28

**Qué apareció.**
El responsable encontró confusa la respuesta del proveedor y la pantalla, recargada. El análisis
encontró siete problemas de pantalla y cinco de lógica, listados en el plan. Los más serios:

- una llegada no contaba como respuesta, y a los 3 días salía el recordatorio de «no respondió»
  aunque ya hubiera llegado mercadería;
- se podía confirmar más de lo pedido, lo que inflaba el cupo de la pre-venta;
- el número de cada línea se ignoraba sin aviso si el desplegable no decía «Con otra cantidad».

**Qué dice la especificación.**
`Nada`: el caso de uso de la respuesta todavía no está en el documento (B-05-013).

**Qué se hizo.**
- **La respuesta se anota sólo en la ficha del pedido.** Una pregunta, «¿Qué contestó…?», con
  tres respuestas como en Telegram: *Confirmó todo* · *Confirmó con cambios* · *No puede
  abastecer*. Cada una es una pantalla propia que se abre como diálogo. «Con cambios» muestra por
  línea *Tal cual* · *Menos* · *No la tiene*; el número aparece sólo con «Menos» y el motivo sólo
  con «No la tiene». «No puede» dice antes de confirmar qué pre-ventas pierden lo que esperaban.
  Cuando todo tiene respuesta, se achica a una línea.
- **Una sola tabla de productos, que sólo informa.** La llegada se carga en su pantalla, antes del
  segundo tiempo de siempre.
- **La propuesta ya no tiene formularios**: una columna «Respuesta» con «Anotar la respuesta», y el
  estado dice hace cuánto espera, o que espera un reintento de envío.
- **Reglas** (valen también para Telegram):
  - **R1:** lo que llega es una respuesta: la línea queda confirmada entera (ambigüedad 4).
  - **R2:** no se confirma más de lo pedido (ambigüedad 3).
  - **R3:** lo que no cambió no se vuelve a anotar ni a auditar.
  - **R4:** el motivo es de cada línea.
  - **R7:** las advertencias enlazan la demora del producto.
  - Además, la fecha se puede borrar.
- Telegram suma «✏️ Confirmó con cambios», que abre la pantalla de la web.

**Qué habría que cambiar.**
Cuando el caso de uso de la respuesta entre al documento: las reglas R1 a R4 como postcondiciones.

---

### B-05-016 · Agregar un producto a la propuesta, también por título, y con mensajes que dicen qué pasó

**Tipo:** Agregado · **Fecha:** 2026-10-28 · **Alcance:** `CU-RST-APR` A2, `CO-071`
**Estado:** Abierta — pedido del responsable el 2026-10-28, con el plan de la respuesta simple

**Qué apareció.**
El responsable no pudo agregar Sakamoto Days #24 (`E-003891`) a una propuesta: el error decía «no
hay un producto editorial con el código…». El tomo existía y se podía pedir. El buscador sólo
aceptaba el código, el ISBN o el código de barras exactos, y este tomo no tenía ni ISBN ni código
de barras. El mensaje decía «código» aunque se hubiera escrito un título, y no distinguía entre
algo que no existe y algo que no se puede pedir.

**Qué dice la especificación.**
> `CU-RST-APR` paso 2: «Puede […] añadir cualquier producto del catálogo con una cantidad definida
> manualmente.»

Cómo se lo busca, `Nada`.

**Qué se hizo.**
- **El campo ofrece el catálogo**, como en las ofertas: el código primero y después el nombre, sólo
  lo que se puede pedir (ni cancelado ni dado de baja).
- **El servidor acepta también el título con su número** («Sakamoto Days 24»), sin tildes ni
  mayúsculas, y el ISBN con guiones.
- **Los mensajes dicen qué pasó**:
  - falta el número del tomo;
  - no existe por ningún criterio;
  - coincide con más de uno, y cuáles son;
  - está cancelado por la editorial (con la salida «Volver a anunciar», B-01-026);
  - está dado de baja;
  - no es material editorial.

**Qué habría que cambiar.**
`Nada` en el documento de análisis.

---

### B-05-017 · Una sola pantalla para la llegada de mercadería

**Tipo:** Agregado · **Fecha:** 2026-11-07 · **Alcance:** `CU-ALT-TRA` pasos 4 a 7, `CU-RST-LLE`, `CO-013`, `CO-232`
**Estado:** Abierta — plan [00 de últimos cambios](../docs/planes/00-ultimos-cambios-antes-del-cierre.md), aprobado por el responsable el 2026-11-07 con sus recomendaciones

**Qué apareció.**
La llegada de una pre-venta se cargaba en «Pre-ventas por llegar» (por producto, fecha y editorial) y
la de un pedido a proveedor en «Pedidos por llegar» (por pedido). Desde B-05-010 casi toda pre-venta
tiene su pedido, así que la misma caja se podía cargar por dos lados, y cada panel mostraba la mitad:
uno las reservas, el otro lo pedido y lo confirmado. El responsable: «la información se pierde entre
un panel y otro. Hace la operatividad confusa».

**Qué dice la especificación.**
> «El Administrador recibe el lote físico, verifica su contenido y confirma el ingreso de stock en el
> sistema, indicando las unidades recibidas por producto.» (`CU-ALT-TRA`, paso 4)

La llegada de un pedido a proveedor no está en el documento (`CU-RST-LLE`, código aprobado en C-23).

**Qué se hizo.**
- **Una pantalla, «Por llegar»** (Proveedores), agrupada **por proveedor y fecha estimada**: lo que
  entra junto por la puerta. Cada línea dice de qué pedido es, cuánto se pidió, se confirmó y se
  recibió y, si es pre-venta, sus reservas y si está demorada. Conserva el calendario del mes.
- **Una carga y una revisión.** Al confirmar, cada línea suma a su pedido; una pre-venta cubre sus
  reservas como siempre (`CO-013`). **Un faltante** (una pre-venta del grupo que queda en cero) se
  demora si su fecha ya pasó, como `CU-ALT-TRA` A1; lo que no es pre-venta queda abierto.
- **Una pre-venta sin pedido registrado** aparece en su grupo, marcada, y se carga igual.
- Las dos direcciones viejas llevan a la nueva. La lista de pedidos queda como consulta.
- **Códigos.** El responsable autorizó el 2026-11-07 nombrar los contratos nuevos de este plan:
  `CO-228` y `CO-229` (modelo de respaldo), `CO-230` y `CO-231` (Google) y **`CO-232`
  `confirmarLlegadaDeMercaderia`**, el de esta pantalla. Se toman los siguientes al último existente
  (`CO-227`) y no se reusan los huecos (`CO-219`, `CO-222` a `CO-226`).

**Qué habría que cambiar.**
`CU-ALT-TRA` pasos 4 a 7: invoca la llegada de mercadería; el caso de uso conserva la vigilancia
(avisos y escalado). `CU-RST-LLE`, ficha nueva, «Registrar la llegada de mercadería», con `CO-232`:
*precondición*, hay líneas abiertas de pedidos enviados o pre-ventas sin pedido; *postcondiciones*,
cada línea suma lo recibido (Parcial o Recibida, con lo de más en la auditoría), cada pre-venta pasa
por `CO-013`, cada producto sin reservas suma al stock con `CO-077`, cada pre-venta del grupo en cero
con la fecha cumplida se demora (`CO-015`); *excepción*, el fallo de un pedido no frena a los demás
(como `CO-013` E3).

---

### B-05-018 · El pedido a mano busca por nombre, quita renglones y no pide lo que trae otro proveedor

**Tipo:** Agregado · **Fecha:** 2026-11-07 · **Alcance:** `CU-RST-PDA`, `CU-RST-APR` A2, `CO-071`, `CO-074`
**Estado:** Abierta — pedido del responsable el 2026-11-07, durante el plan [00 de últimos cambios](../docs/planes/00-ultimos-cambios-antes-del-cierre.md)

**Qué apareció.**
El responsable: «Nadie se acuerda de +300 códigos de producto», y «hay que revisar también si los
productos que se piden corresponden al proveedor declarado, si no, le estamos pidiendo algo que no
tiene». El pedido a mano sólo aceptaba código o ISBN, sus renglones no se podían quitar, y nada
impedía pedirle a un proveedor un tomo que trae otro.

**Qué dice la especificación.**
`Nada`. El pedido a mano no tiene ficha (`CU-RST-PDA`, código aprobado en C-23).

**Qué se hizo.**
- **Cada renglón busca en el catálogo**, como «Agregar un producto» de Restock (B-05-016): la lista
  ofrece «código — título #tomo» y el servidor acepta el código, el ISBN, el código de barras o el
  título con su número. La búsqueda vive ahora en un solo lugar para los dos (`catalog.busqueda`).
- **Los renglones se agregan y se quitan.** El último no se quita: se vacía.
- **No se le pide a un proveedor lo que trae otro.** Quién trae cada producto es la regla de Restock
  (B-05-003): su proveedor, si está activo; si no, el único proveedor habitual de su editorial. Si es
  otro, el renglón lo dice («lo trae Panini Argentina, no Distribuidora Ivrea») y el pedido no sale.
  **Si no se puede saber quién lo trae, se acepta**: bloquearlo frenaría a una distribuidora que
  trae varias editoriales y no tiene sus tomos asignados.
- Como en Restock, no se pide un tomo cancelado por la editorial ni uno dado de baja; a diferencia
  de Restock, el pedido a mano admite material no editorial por su código.

**Qué habría que cambiar.**
La ficha de `CU-RST-PDA`: el renglón por código, ISBN o título con su número; la excepción del
producto que trae otro proveedor; y la regla de quién trae cada producto, que hoy sólo describe
`CU-RST-PRO` paso 4 (B-05-003).
