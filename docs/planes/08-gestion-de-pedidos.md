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

---
---

# Plan — `08` Gestión de Pedidos · segunda parte: el Cliente ante una demora

**Estado del plan:** Aprobado el 2026-10-12, con las recomendaciones de la sección 3 · **Fecha:** 2026-10-12

Cuando una pre-venta se demora (plan 01, ciclo de la pre-venta), el Cliente elige qué hacer con su
pedido: esperar todo, recibir ahora lo que hay con compensación por la espera, o cancelar el
artículo con reembolso en puntos. Se construye junto con el plan 01.

---

## 1. Qué cubre

| Caso de uso | Contratos | Escritura | Consulta |
| --- | --- | --- | --- |
| `CU-PED-OPC` | `CO-184`, `CO-094`, `CO-095`, `CO-096`, `CO-156` | 2 (`CO-095`, `CO-096`) | 3 |
| `CU-PED-CAN` | `CO-098`, `CO-156` | 1 | 1 |
| `CU-PED-CMP` | `CO-097` | 1 | 0 |

**Total: 6 contratos propios.** `CU-CLI-HIS` gana el acceso a la decisión desde el detalle del
pedido, que hoy le falta para dejar de estar `Parcial`.

---

## 2. Conceptos que toca

| Concepto | ¿Existe? | Qué hace este plan con él |
| --- | --- | --- |
| `LineaPedido` | Sí | Usa `decision_demora`, `compensacion_acumulada` y `fecha_llegada_original`, que ya existen. Gana la ventana de decisión (ambigüedad 1) |
| `LotePuntos`, `MovimientoPuntos` | Sí | Reembolso (`CO-098`) y compensación (`CO-097`) |
| `ConfiguracionSistema` | Sí | Gana «ventana de decisión ante demora (horas)», que `CU-CFG-PAR` ya especifica |
| `ArticuloRetenido` | **No** | Ambigüedad 3 |

---

## 3. Ambigüedades detectadas

| # | Dónde | Las dos lecturas | Qué se necesita para destrabarla |
| --- | --- | --- | --- |
| 1 | **Desde cuándo corre la ventana de decisión y dónde se guarda** (`CO-096`: «la ventana de decisión de esas líneas quedó cerrada»). El modelo no tiene dónde | **(a)** Arranca cuando se registra la demora; la línea guarda hasta cuándo puede decidir y si la ventana se cerró. La duración por defecto es de **72 horas**, que `CU-CFG-PAR` no fija. **(b)** Se deriva de la transición del pedido | Decisión. **Recomiendo (a)**. Es un agregado al modelo y va a la bitácora |
| 2 | **El stock al cancelar un artículo demorado.** `CO-098` y RF-17: «incrementa el stock general del artículo en una unidad». Una pre-venta demorada **nunca llegó**: la compra no le descontó stock | **(a)** Se devuelve al stock lo que la compra había descontado: en una pre-venta, nada. Sumar una unidad crearía stock que no existe y la tienda la vendería. **(b)** Lo que dice el contrato | Decisión. **Recomiendo (a)**. Es una corrección de `CO-098` y de RF-17 |
| 3 | **Opción 2, cuando el artículo llega.** `CO-095`: «se registra como ArticuloRetenido a nombre del Cliente», que es del módulo 18 y no existe | **(a)** Al llegar, la línea pasa a Disponible marcada «Despacho diferido» y el pedido aparece en el listado del Administrador para el segundo envío. El paso a `ArticuloRetenido` se suma con el módulo 18; hasta entonces `CU-PED-OPC` queda `Parcial`. **(b)** Construir ya una parte del módulo 18 | **Recomiendo (a)** |
| 4 | **Hasta cuándo corre la compensación de la opción 2.** RF-16: «hasta que el artículo sea despachado», y en el módulo 18 eso puede ser semanas después de que llegó | **(a)** Hasta que el artículo llega: la espera que se compensa es la de la imprenta, no la del cliente para retirarlo. **(b)** Hasta que se despacha | **Recomiendo (a)**. Va a la bitácora como corrección de RF-16 |
| 5 | **El estado del pedido con la opción 2.** `CO-095` mueve las líneas disponibles a Empaquetado, pero no dice qué pasa con el pedido | **(a)** El pedido pasa a Empaquetado, para que el Administrador pueda despacharlo; la línea demorada sigue esperando. **(b)** El pedido sigue en «Esperando artículo demorado» y no se puede despachar | **Recomiendo (a)** |
| 6 | **Cálculo de la compensación.** 5 % del valor por semana, hasta el 25 % | **(a)** Se calcula por semanas cumplidas desde la fecha original, contra lo ya acreditado: correr el Temporizador todos los días, o dos veces, nunca acredita de más. Puntos hacia arriba, como el reembolso (plan 01, amb. 5) | **Recomiendo (a)** |
| 7 | **Valor del artículo** para el reembolso y la compensación | **(a)** Precio unitario congelado por cantidad; si se pagó con puntos, el reembolso devuelve esos puntos (plan 01, amb. 4) | **Recomiendo (a)** |
| 8 | **Cómo se entera el Cliente** | **(a)** Un correo con las tres opciones y el enlace directo a la decisión, más el aviso en el detalle del pedido en «Mi cuenta» | **Recomiendo (a)** |

---

## 4. Orden de construcción

| # | Qué | Depende de | Motivo |
| --- | --- | --- | --- |
| 1 | Ventana de decisión en la línea y su parámetro | Plan 01, paso 3 | `CO-015` la abre |
| 2 | `CO-184`, `CO-094`, `CO-095` y `CO-156` en «Mi cuenta», con el correo | 1 | |
| 3 | `CO-098` desde la opción 3 | 2 | |
| 4 | `CO-096` y `CO-097` en el Temporizador | 1 | |

---

## 5. Riesgos

| Riesgo | Dónde | Cómo se cubre |
| --- | --- | --- |
| El Cliente decide dos veces (dos pestañas) | `CO-095` | La línea se toma con bloqueo y se verifica que no tenga decisión. Prueba de concurrencia |
| Decidir después de vencida la ventana | `CO-095` | Rechazo en el servidor. Prueba con el reloj adelantado |
| Compensación de más | `CO-097` | Cálculo contra lo ya acreditado y tope del 25 % en el servidor. Prueba de doble corrida y de tope |
| Reembolso parcial | `CO-098` E1 | Una sola transacción; prueba que fuerza el fallo |
| Un cliente decide sobre el pedido de otro | Acceso | 404 por la dirección real |

---

## 6. Fuera de alcance

- `ArticuloRetenido` y el despacho desde el stock almacenado (módulo 18).
- La resolución manual del Administrador después de una ventana vencida: la ficha la deja «a cargo
  del Administrador» sin caso de uso. El pedido queda visible en su listado con el filtro de
  demorados.
