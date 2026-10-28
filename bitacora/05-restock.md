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
