> **Tipo: Normativo** una vez aprobado. Antes de la aprobación es una propuesta.
> Se escribe **antes** de programar y **no se reescribe** después: si algo cambió durante la
> construcción, eso va a la bitácora del módulo, no acá.

# Plan — `05` Restock

**Estado del plan:** Aprobado el 2026-10-14, con las recomendaciones de la sección 3 · **Fecha:** 2026-10-14

Dos piezas que se alimentan entre sí. El Cliente que encuentra un producto agotado pide que le
avisen cuando vuelva (`CU-RST-SUS`), y ese pedido es la demanda con la que el sistema arma cada
semana la propuesta de reposición (`CU-RST-PRO`). El Administrador la ajusta y la despacha a cada
proveedor (`CU-RST-APR`, con el correo de `CU-RST-PED`, que ya existe). Cuando el producto vuelve a
tener stock, los primeros en la lista reciben el aviso (`CU-RST-NOT`). Destraba `CO-077` en
`CU-ALT-TRA`, `CU-ALT-NAC` y `CU-ALT-REV`, y la cifra de propuestas en `CU-PRV-BAJ` (B-04-001).

---

## 1. Qué cubre

| Caso de uso | Contratos | Escritura | Consulta |
| --- | --- | --- | --- |
| `CU-RST-SUS` | `CO-075`, `CO-076` | 2 | 0 |
| `CU-RST-NOT` | `CO-077` | 1 | 0 |
| `CU-RST-PRO` | `CO-067`, `CO-068` | 2 | 0 |
| `CU-RST-APR` | `CO-174`, `CO-175`, `CO-069` a `CO-073` | 5 | 2 |
| `CU-RST-PED` | `CO-074` | 0 (comunicación) | 0 |

**Total: 13 contratos.** `CO-074` ya existe (`suppliers/pedidos.py`) y lo usa `CU-ALT-REV`; acá
gana su segundo invocante y su prueba de contrato.

---

## 2. Conceptos que toca

| Concepto | ¿Existe? | Qué hace este plan con él |
| --- | --- | --- |
| `SuscripcionReposicion` | **No** | La crea, con I-22 (una activa por cliente y producto) en la base |
| `PropuestaRestock`, `LineaPropuestaRestock` | **No** | Las crea, con I-21 (a lo sumo una pendiente) en la base |
| `Producto`, `ProductoEditorial` | Sí | Sólo los lee; la ficha pública gana el botón de aviso |
| `Proveedor` | Sí | Agrupa la propuesta; recibe el correo |
| `ConfiguracionSistema` | Sí | Gana «cantidad mínima de pedido de restock» y «margen de stock mínimo», que `CU-CFG-PAR` ya especifica |

---

## 3. Ambigüedades detectadas

| # | Dónde | Las dos lecturas | Qué se necesita para destrabarla |
| --- | --- | --- | --- |
| 1 | **Por dónde entra la reposición** (`CU-RST-NOT` paso 1). Las cuatro altas que nombra crean productos nuevos o activan pre-ventas, que no pueden tener suscriptores. Lo que se repone por un pedido a proveedor entra hoy editando el stock (`CU-CAT-EDI`) | **(a)** Toda suba del stock de un producto dispara el aviso con N = lo que subió: la edición, las unidades que sobran al llegar una pre-venta (`CO-013`) y el artículo que vuelve por vencimiento (`CO-154`). **(b)** Sólo las cuatro altas: el aviso no saldría nunca | Decisión. **Recomiendo (a)**. Es un agregado y va a la bitácora |
| 2 | **Cuándo se puede pedir el aviso.** `CO-075`: «el producto está en estado Activo con stock igual a cero». El sistema pasa a **Agotado** todo producto que llega a cero | **(a)** Se admite en Agotado (y en Activo con stock cero). **(b)** Lo literal: nunca se mostraría | **Recomiendo (a)**. Corrección de `CO-075` |
| 3 | **Qué productos entran en la propuesta.** `LineaPropuestaRestock` pide un `ProductoEditorial`; `CU-RST-APR` dice «cualquier producto del catálogo» | **(a)** Sólo editoriales, Activos o Agotados, como dice el modelo; el material no editorial se repone por fuera. **(b)** Todos | **Recomiendo (a)** |
| 4 | **Un producto sin proveedor.** Muchos se cargaron a mano y no tienen proveedor; la propuesta agrupa por proveedor | **(a)** Se usa el proveedor activo que tiene esa editorial como habitual, si hay uno solo. Si no, queda en el grupo «Sin proveedor», que no se puede despachar (sí descartar) hasta asignarle uno desde la ficha. **(b)** Se excluye | **Recomiendo (a)** |
| 5 | **Valores por defecto** de los dos parámetros nuevos (`CU-CFG-PAR` no los fija) | **(a)** Cantidad mínima **3**, margen **2**: entran los productos con 0 o 1 unidad, y la sugerencia es el mayor entre suscriptores + 2 y 3 | **Recomiendo (a)**; se ajustan en Parámetros |
| 6 | **Cuándo corre el ciclo semanal.** El Temporizador corre una vez por día | **(a)** El ciclo intenta todos los días y genera si no hay ninguna propuesta de los últimos 7 días (`CO-067`) ni una pendiente (I-21). Sin día fijo de la semana. Los resultados sin propuesta (E1 sin elegibles, E3 pendiente sin resolver) se registran y avisan una vez por semana, no todos los días | **Recomiendo (a)** |
| 7 | **Los reintentos «con intervalo»** del aviso al suscriptor (`CO-077` E1) | **(a)** Tres intentos seguidos, como el correo a proveedores (`CO-074`), para no colgar la pantalla que subió el stock. **(b)** Reintentos diferidos con espera | **Recomiendo (a)** |
| 8 | **La suscripción con «Notificación fallida»** conserva su lugar (`CO-077` E1). ¿Entra en la ronda siguiente? | **(a)** Sí: compite por turno con las activas, en su orden original. **(b)** Queda congelada | **Recomiendo (a)**: es lo que «conserva su posición» quiere decir |
| 9 | **El aviso de reposición**: para el invitado y para el personal | **(a)** Sólo el Cliente con sesión; el invitado ve el botón y va al ingreso; el personal no lo ve | **Recomiendo (a)** (`CO-075` exige sesión) |

---

## 4. Orden de construcción

| # | Qué | Depende de | Motivo |
| --- | --- | --- | --- |
| 1 | `SuscripcionReposicion`, `CO-075` y `CO-076` en la ficha pública | — | La demanda alimenta todo lo demás |
| 2 | `CO-077` enganchado a las subas de stock (amb. 1) | 1 | Destraba `CO-013` |
| 3 | `PropuestaRestock`, los parámetros, `CO-067` en el Temporizador y `CO-068` desde el panel | 1 | |
| 4 | `CU-RST-APR`: consulta, ajustes (`CO-069` a `CO-071`), despacho (`CO-072`, con `CO-074`) y descarte (`CO-073`) | 3 | |
| 5 | La cifra de propuestas en la baja de proveedor (B-04-001) | 3 | |

---

## 5. Riesgos

| Riesgo | Dónde | Cómo se cubre |
| --- | --- | --- |
| Dos suscripciones del mismo cliente al mismo producto (doble clic) | `CO-075` | I-22 como restricción única parcial en la base; prueba de concurrencia |
| Dos propuestas pendientes a la vez (el ciclo y el botón manual) | `CO-067`, `CO-068` | I-21 como restricción única parcial; prueba de concurrencia |
| Más avisos que unidades | `CO-077` E2 | Se seleccionan `min(N, M)` y una cancelación no transfiere el cupo; prueba |
| Despachar dos veces al mismo proveedor | `CO-072` | Las líneas se toman con bloqueo y se verifica que sigan Pendientes |
| El correo al proveedor falla | `CO-072` E2 | El proveedor vuelve a Pendiente; prueba con la red cortada |

---

## 6. Fuera de alcance

- Registrar la llegada de lo pedido al proveedor como un ingreso propio: entra editando el stock
  (amb. 1).
- El seguimiento de pedidos en tránsito: `CU-RST-PRO` paso 2 los incluye en la propuesta, y como el
  sistema no los registra, todo producto bajo el margen entra igual.
