> **Tipo: Normativo** una vez aprobado. Antes de la aprobación es una propuesta.
> Se escribe **antes** de programar y **no se reescribe** después: si algo cambió durante la
> construcción, eso va a la bitácora del módulo, no acá.

# Plan — `10` Puntos · primera parte: el Cliente ve sus puntos

**Estado del plan:** Aprobado el 2026-10-09, con las recomendaciones de la sección 3. En la 2,
el responsable pidió además el saldo en la barra superior de la tienda, siempre a la vista, «cosa
de que quiera consultar si le alcanzan los puntos en todo momento para canjear algo» · **Fecha:**
2026-10-09

Primer plan del módulo, a pedido del responsable («ver los puntos»). `LotePuntos` y
`MovimientoPuntos` existen desde la compra online (plan 07, sexta parte). Falta que el Cliente los
vea. Va junto con el panel de cuenta (plan 11, segunda parte), que tiene una sección Puntos.

---

## 1. Qué cubre

| Caso de uso | Contratos | Operaciones de escritura | Operaciones de consulta |
| --- | --- | --- | --- |
| `CU-PTS-CON` | `CO-188`, `CO-189` | 0 | 2 |

---

## 2. Conceptos que toca

| Concepto | ¿Existe? | Qué hace este plan con él |
| --- | --- | --- |
| `LotePuntos`, `MovimientoPuntos` | Sí | Sólo los lee |
| `ConfiguracionSistema` | Sí | Lee la equivalencia, para mostrar el saldo en pesos |

---

## 3. Ambigüedades detectadas

| # | Dónde | Las dos lecturas | Qué se necesita para destrabarla |
| --- | --- | --- | --- |
| 1 | **El origen del movimiento.** `CU-PTS-CON` paso 2 pide el origen por lote («compra / reembolso / compensación / ajuste admin»), y el historial de movimientos sólo pide tipo, cantidad y saldo | **(a)** El historial muestra además de dónde viene cada movimiento (el pedido, cuando lo hay), con enlace a su detalle. **(b)** Sólo lo que pide la ficha | **Recomiendo (a)**: «Acreditación de 1800» sin decir de qué compra no le sirve al Cliente. Es un agregado y va a la bitácora |
| 2 | **Dónde se ve el saldo fuera del panel** | **(a)** Además del panel, el menú «Mi cuenta» de la tienda muestra el saldo. **(b)** Sólo en el panel y en el checkout | **Recomiendo (a)**, a pedido del responsable. Agregado |
| 3 | «Próximo a vencer»: 30 días en `CU-PTS-CON`, 7 días para el stock almacenado en `CU-CLI-HIS` | No es contradicción: son conceptos distintos | Se respeta cada uno |

---

## 4. Orden de construcción

| # | Qué | Depende de | Motivo |
| --- | --- | --- | --- |
| 1 | `CO-188`: saldo con su equivalencia, lotes con «Próximo a vencer» e historial de a 50 | Plan 11, segunda parte (el panel) | Se entra desde el panel |
| 2 | `CO-189`: filtro por tipo y por rango de fechas, total encontrado, E1 con «Limpiar filtros» | 1 | |
| 3 | El saldo en el menú «Mi cuenta» | 1 | |

---

## 5. Riesgos

| Riesgo | Dónde | Cómo se cubre |
| --- | --- | --- |
| Un Cliente ve los puntos de otro | `CO-188` | La consulta es siempre de quien pide; no recibe identificador. Prueba con dos clientes |
| La consulta modifica algo | `CO-188`, `CO-189` | Prueba que compara lotes y movimientos antes y después |
| Fechas del filtro inválidas | `CO-189` | Se ignoran, como en el padrón de usuarios |
| El personal entra a la pantalla | Acceso | 403 por la dirección real |

---

## 6. Fuera de alcance

- `CU-PTS-ADM` (ajuste manual), `CU-PTS-CAD` (caducidad) y la rama de mostrador de `CU-PTS-CJE`.
- La consulta de puntos de un cliente por el personal (`CO-191`).

---

# Plan — `10` Puntos · segunda parte: caducidad y ajuste manual

**Estado del plan:** Aprobado el 2026-10-17, con las recomendaciones de la sección 3 salvo la 5:
el responsable pidió además **un aviso unos días antes de que venzan, «animando a la compra, como
todas las tiendas»**, sin quitar el aviso de la caducidad. Los días de anticipación son un parámetro
nuevo de Parámetros, sección Fidelización, con 3 por defecto · **Fecha:** 2026-10-17

Segunda parte del plan del módulo. La primera, de arriba, está aprobada y no se toca. Ésta cierra
el módulo: los puntos vencen solos (`CU-PTS-CAD`, en el Temporizador) y el Administrador corrige
el saldo de un Cliente ante un caso de soporte (`CU-PTS-ADM`).

---

## 1. Qué cubre

| Caso de uso | Contratos | Escritura | Consulta |
| --- | --- | --- | --- |
| `CU-PTS-CAD` | `CO-105` | 1 | 0 |
| `CU-PTS-ADM` | `CO-191`, `CO-106` | 1 (`CO-106`) | 1 (`CO-191`) |

**Total: 3 contratos.** Con esto el módulo 10 queda completo.

---

## 2. Conceptos que toca

| Concepto | ¿Existe? | Qué hace este plan con él |
| --- | --- | --- |
| `LotePuntos` | Sí | `CO-105` lo pasa a Vencido; `CO-106` crea uno de origen Ajuste manual o consume los existentes |
| `MovimientoPuntos` | Sí | `CO-106` crea el del ajuste, con su motivo. `CO-105`, según la ambigüedad 4 |
| `CobroEnCurso` | Sí | Sólo lo lee: es lo que dice qué puntos están comprometidos en un canje (ambigüedad 1) |
| `ConfiguracionSistema` | Sí | Lee la caducidad estándar y la equivalencia. Gana «aviso previo a la caducidad (días)», 3 por defecto (decisión del responsable sobre la ambigüedad 5) |
| `RegistroAuditoria` | Sí | Tres acciones nuevas: caducidad de lote, incidente de caducidad y ajuste manual |

---

## 3. Ambigüedades detectadas

| # | Dónde | Las dos lecturas | Qué se necesita para destrabarla |
| --- | --- | --- | --- |
| 1 | **Qué puntos están «comprometidos en un canje en curso».** `CO-105` E2 no vence esos lotes y `CO-106` no los debita. El atributo `comprometido en canje` existe en el modelo, pero **la compra nunca lo marca**: los puntos de un canje se debitan recién cuando la pasarela aprueba el pago, y mientras tanto quedan en un `CobroEnCurso` pendiente. En el mostrador no hay ventana: el débito ocurre en la misma operación | **(a)** Derivarlo: un Cliente con un cobro pendiente que canjea N puntos tiene comprometidos los primeros N de sus lotes en orden de caducidad (los que el pago va a consumir). Esos lotes no vencen y no se debitan a mano. Cuenta un cobro pendiente de menos de 24 horas: uno más viejo está abandonado (`docs/DEUDA.md`, «Cobros en curso abandonados») y no puede trabar la caducidad para siempre. No toca la compra. **(b)** Marcar el atributo al confirmar el pedido y limpiarlo al resolver el pago. Cambia la compra online, que está verificada, y un cobro abandonado dejaría los lotes marcados para siempre | **Recomiendo (a).** Es un agregado sobre cómo se obtiene el dato que el contrato usa |
| 2 | **El registro del ciclo sin lotes vencidos.** La ficha (A1): «El evento queda registrado en el log con resultado "ciclo completado sin lotes vencidos"». `CO-105` no lo declara | **(a)** Lo del contrato: sin lotes no se registra nada, como el ciclo del stock en local (plan 18, ambigüedad 8). Correría todos los días. **(b)** Una entrada por día | **Recomiendo (a)**, por consistencia con el resto del Temporizador |
| 3 | **Qué día vence un lote.** La ficha: «fecha de caducidad menor o igual a la fecha actual». «Mis puntos» muestra «Vence el dd/mm» | **(a)** El lote vence al empezar su día de caducidad: el ciclo de ese día lo invalida. «Mis puntos» pasa a decir «Se pueden usar hasta el» día anterior. **(b)** Vence al terminar ese día (`<` en vez de `<=`) | **Recomiendo (a)**: es lo que dice la ficha, y el texto de la pantalla se corrige para que no prometa un día de más |
| 4 | **El historial del Cliente ante la caducidad.** `CO-105` cambia los lotes pero no crea un `MovimientoPuntos`. Sin movimiento, el saldo de «Mis puntos» baja sin que el historial diga por qué | **(a)** Se crea un movimiento de Débito por lote vencido, con el motivo «Caducidad» y su saldo resultante. **(b)** Sólo lo del contrato | **Recomiendo (a)**. Es un agregado: el contrato no prohíbe el movimiento y el historial queda completo |
| 5 | **Un aviso por lote o por Cliente.** Paso 4: «a cada Cliente afectado una notificación» «con el detalle del lote invalidado» | **(a)** Un correo por Cliente, con una fila por lote vencido y el saldo final. **(b)** Un correo por lote | **Recomiendo (a)** |
| 6 | **Una caducidad distinta para el ajuste.** La ficha de `CU-PTS-CAD` y las Notas de `CO-105`: los lotes del ajuste manual heredan la caducidad estándar «salvo que el Administrador indique lo contrario». `CO-106` no recibe una fecha y su postcondición dice «la fecha de caducidad estándar» | **(a)** Lo de `CO-106`: siempre la estándar, sin campo de fecha. **(b)** Un campo de fecha opcional en el ajuste | **Recomiendo (a)**: manda el contrato de la operación (C-08). Corrección de la ficha y de las Notas |
| 7 | **Dónde está «Ajustar puntos».** `CU-PTS-ADM` paso 1 lo pone en la cuenta del Cliente (`CU-CLI-CON`). La ficha del Cliente hoy no tiene ninguna acción, a propósito: sus datos personales los cambia su titular | **(a)** La ficha del Cliente gana un enlace «Puntos» al panel de `CO-191`, con el formulario del ajuste. No toca los datos personales. **(b)** Una pantalla aparte en el menú | **Recomiendo (a)**, que es lo que dice la ficha |
| 8 | **El incidente de `CO-105` E1.** «Registra el incidente en el log con el detalle del error» | **(a)** Una entrada de auditoría «Incidente de caducidad» con el lote y el error, y el lote queda como estaba para el próximo ciclo. **(b)** Sólo el registro técnico | **Recomiendo (a)**, como los incidentes de la pre-venta |

---

## 4. Orden de construcción

| # | Qué | Depende de | Motivo |
| --- | --- | --- | --- |
| 1 | Los puntos comprometidos (ambigüedad 1), como una función del módulo de puntos | — | La usan los dos casos de uso |
| 2 | `CO-105` en el Temporizador, con su aviso y el movimiento | 1 | El débito manual usa la misma regla de lotes |
| 3 | `CO-191`: el panel de puntos del Cliente para el Administrador, desde su ficha | — | |
| 4 | `CO-106`: el ajuste, con E1 (máximo debitable) y E2 (motivo) | 1, 3 | |

---

## 5. Riesgos

| Riesgo | Dónde | Cómo se cubre |
| --- | --- | --- |
| El ciclo vence un lote mientras el pago de un canje se aprueba | `CO-105`, `CO-089` | Los lotes se toman con bloqueo, como el débito del canje; el cobro pendiente difiere los comprometidos. Prueba de concurrencia |
| El Administrador debita mientras el Cliente paga un canje | `CO-106`, `CO-089` | Bloqueo de los lotes y recálculo de lo comprometido dentro de la transacción. Prueba de concurrencia |
| Correr el ciclo dos veces vence o avisa dos veces | `CO-105` | Sólo toca lotes Activos con disponible; prueba de doble corrida |
| Un lote que falla frena el ciclo | `CO-105` E1 | Una transacción por lote; prueba con un fallo forzado en uno de dos |
| Un Cajero o un Cliente ajusta puntos | `CO-106`, `CO-191` | Sólo el Administrador; 403 por la dirección real |
| El saldo queda negativo | `CO-106` | E1 en el servidor, y los lotes no admiten disponible negativo |

---

## 6. Fuera de alcance

- La limpieza de los cobros en curso abandonados (`docs/DEUDA.md`): este plan sólo deja de
  contarlos después de 24 horas.
- Un aviso **previo** a la caducidad: ninguna ficha lo pide.
