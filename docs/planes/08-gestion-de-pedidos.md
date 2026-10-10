> **Tipo: Normativo** una vez aprobado. Antes de la aprobación es una propuesta.
> Se escribe **antes** de programar y **no se reescribe** después: si algo cambió durante la
> construcción, eso va a la bitácora del módulo, no acá.

# Plan — `08` Gestión de Pedidos · primera parte: listado, detalle y avance de estado

**Estado del plan:** Aprobado el 2026-10-09, con las recomendaciones de la sección 3; en la 5,
sólo el Administrador · **Fecha:** 2026-10-09

Primer plan del módulo, a pedido del responsable («el administrador y su pantalla de pedidos»).
Cubre lo que el Administrador necesita para despachar lo que ya vende la tienda: encontrar un
pedido, verlo entero y avanzarlo hasta Despachado. Los casos de la demora (`OPC`, `CAN`, `CMP`)
quedan para la segunda parte, porque hoy nada pone un artículo en «Esperando artículo demorado».

---

## 1. Qué cubre

| Caso de uso | Contratos | Operaciones de escritura | Operaciones de consulta |
| --- | --- | --- | --- |
| `CU-PED-CON` | `CO-182`, `CO-183` | 0 | 2 |
| `CU-PED-EST` | `CO-183`, `CO-092`, `CO-093` | 2 | 1 |

**Total: 4 contratos.** `CO-093` se construye y se prueba aunque hoy no pueda ocurrir (ningún
ítem llega a «Esperando artículo demorado» hasta `CU-ALT-DEM`): la prueba monta ese estado a mano.

---

## 2. Conceptos que toca

| Concepto | ¿Existe? | Qué hace este plan con él |
| --- | --- | --- |
| `Pedido`, `LineaPedido`, `TransaccionPago` | Sí (plan 07, sexta parte) | Los lee; `CO-092` cambia `Pedido.estado` y el estado de las líneas Disponibles |
| La línea de tiempo de estados | **No** | Ambigüedad 1 |
| `RegistroAuditoria` | Sí | Gana la acción «Avance de estado de pedido» |

---

## 3. Ambigüedades detectadas

| # | Dónde | Las dos lecturas | Qué se necesita para destrabarla |
| --- | --- | --- | --- |
| 1 | **«Línea de tiempo de estados con timestamps»** (`CO-183`, `CO-193`, `CU-PED-EST` paso 2). `Pedido` sólo tiene `estado`: el modelo no guarda cuándo se alcanzó cada uno | **(a)** Un concepto nuevo, `TransicionDePedido` (pedido, estado anterior, estado nuevo, cuándo, quién), que escriben la compra, `CO-092` y más adelante los procesos automáticos. **(b)** Derivarla del registro de auditoría, que ya guarda cada avance con su momento | Decisión. **Recomiendo (a)**: el Cliente también ve la línea de tiempo (`CO-193`), y el log de auditoría es una traza del Administrador, con el detalle en texto libre; leerlo desde la tienda lo convertiría en un dato del dominio. Es un agregado al modelo y va a la bitácora |
| 2 | **Qué estado tiene la línea en cada paso.** `CO-092`: «Si el destino es Empaquetado o Despachado, LineaPedido.estado del ítem de las líneas Disponibles pasó al estado correspondiente». DME-08 no tiene «Armado» | **(a)** Pendiente de armado → Armado no toca las líneas; Armado → Empaquetado las pasa a Empaquetado; Empaquetado → Despachado, a Despachado. **(b)** Otra correspondencia | **Recomiendo (a)**: es la lectura literal del contrato |
| 3 | **«Notifica al Cliente»** (`CU-PED-EST` paso 4) y «en tiempo real» (RF-18: «en un máximo de 30 segundos») | **(a)** Un correo en cada avance, al Cliente o al correo del invitado (`CU-TDA-INV` paso 9), y el estado leído de la base cada vez que el Cliente abre su pedido. **(b)** Además, la pantalla del pedido se refresca sola | **Recomiendo (a)** más un refresco cada 30 s sólo en el detalle de un pedido activo: es la cifra de RF-18 y no necesita infraestructura nueva |
| 4 | **Filtro «cliente»** (`CU-PED-CON` paso 3) | **(a)** Texto que busca por nombre o correo, también el del invitado. **(b)** Un desplegable de clientes | **Recomiendo (a)**: un desplegable con quinientos clientes no sirve |
| 5 | **Quién ve la pantalla** | El caso de uso dice Administrador. El Cajero arma y despacha en el local | **Recomiendo** sólo el Administrador, como dice la ficha. Si el Cajero tiene que despachar, es una enmienda que decide el responsable |
| 6 | **«Valor total»** de la fila (`CO-182`) | **(a)** Lo pagado en dinero más el envío. **(b)** El valor de los productos antes del canje | **Recomiendo (a)**, y el detalle muestra los puntos canjeados aparte (`CO-183`) |

---

## 4. Orden de construcción

| # | Qué | Depende de | Motivo |
| --- | --- | --- | --- |
| 1 | `TransicionDePedido`, y la compra escribe la primera transición | — | La línea de tiempo empieza al confirmar |
| 2 | `CU-PED-CON`: listado con filtros, paginado de a 50, y detalle (`CO-182`, `CO-183`) | 1 | |
| 3 | `CU-PED-EST`: avanzar de a un paso con confirmación, E1, E2 (`CO-092`, `CO-093`), correo y auditoría | 2 | |
| 4 | El acceso «Pedidos» en el menú del panel, y la cifra de pedidos por armar en el tablero | 2 | |

---

## 5. Riesgos

| Riesgo | Dónde | Cómo se cubre |
| --- | --- | --- |
| Dos administradores avanzan el mismo pedido a la vez y lo saltean dos pasos | `CO-092` | El pedido se toma con bloqueo y el avance compara contra el estado que se vio en pantalla. Prueba de concurrencia |
| Un avance manual desde un estado automático | `CO-092` E1 | Rechazo en el servidor, no sólo el botón oculto. Prueba por la dirección real |
| Retroceder un estado | DME-07 | La operación no recibe destino: sólo existe «el siguiente» |
| El correo caído tumba el avance | Paso 4 | El correo sale después del `commit` |
| Rol equivocado | Todo | Cajero y Cliente reciben 403 por la dirección real |
| Volumen | `CO-182` | El listado hace las mismas consultas con 10 que con 2000 pedidos |

---

## 6. Fuera de alcance

- `CU-PED-OPC`, `CAN` y `CMP` (segunda parte), y el acceso a `CU-PED-OPC` desde el detalle.
- Los pedidos del canal presencial: no existen hasta `CU-VTA-REG`. El filtro por canal ya los
  contempla.
- Exportar el listado.
