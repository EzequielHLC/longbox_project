> **Tipo: Normativo** una vez aprobado. Antes de la aprobación es una propuesta.
> Se escribe **antes** de programar y **no se reescribe** después: si algo cambió durante la
> construcción, eso va a la bitácora del módulo, no acá.

# Plan — `09` Devoluciones

**Estado del plan:** Aprobado el 2026-10-16, con las recomendaciones de la sección 3 · **Fecha:** 2026-10-16

El Cliente abre un reclamo sobre un artículo que recibió, con fotos; el Administrador lo resuelve
con un cambio por otro producto, con el reembolso en puntos o con un rechazo fundado. Es el único
módulo del sistema que todavía no tiene código. Trae además el parámetro «plazo máximo de
devolución» que `CU-CFG-PAR` especifica en la sección Comercial y hoy no existe (`CO-130` parcial).

La contradicción sobre el ciclo del cambio (ambigüedad 1, B-09-001) quedó resuelta el
2026-10-16: los diagramas de estados están desactualizados y mandan la ficha y `CO-100` (R-09-001).

---

## 1. Qué cubre

| Caso de uso | Contratos | Escritura | Consulta |
| --- | --- | --- | --- |
| `CU-DEV-SOL` | `CO-185`, `CO-099` | 1 (`CO-099`) | 1 (`CO-185`) |
| `CU-DEV-RES` | `CO-186`, `CO-187`, `CO-100`, `CO-101`, `CO-102` | 3 (`CO-100`, `CO-101`, `CO-102`) | 2 (`CO-186`, `CO-187`) |

**Total: 7 contratos propios.** Además, `CO-130` (Parámetros) gana el plazo máximo de devolución
con su excepción E1 aislada: se rechaza sólo ese campo y los demás se guardan.

---

## 2. Conceptos que toca

| Concepto | ¿Existe? | Qué hace este plan con él |
| --- | --- | --- |
| `CasoDevolucion` | **No** | Lo crea, con los estados de DME-15 (Pendiente, Resuelto, Rechazado). I-19 como unicidad en la base: un caso por `LineaPedido`, en cualquier estado |
| Evidencia del caso | **No** | Una o más imágenes por caso (ambigüedad 10) |
| `DevolucionFisica` | **No** | Lo crea `CO-100` en Pendiente de retiro |
| `ArticuloRetenido` | Sí | No lo toca: «Reservado para cambio» queda sin uso (R-09-001) |
| `LineaPedido`, `Pedido`, `TransicionDePedido` | Sí | Sólo los lee: qué línea se puede reclamar y desde cuándo corre el plazo |
| `LotePuntos`, `MovimientoPuntos` | Sí | `CO-101` acredita un lote de origen Reembolso. El movimiento queda vinculado al caso (el modelo declara `MovimientoPuntos 0..* — 0..1 CasoDevolucion`) |
| `Producto` | Sí | `CO-100` descuenta una unidad del reemplazo y lo pasa a Agotado si llega a cero |
| `ConfiguracionSistema` | Sí | Gana «plazo máximo de devolución (días)», entero ≥ 10, por defecto 10 |
| `RegistroAuditoria` | Sí | Cuatro acciones nuevas: apertura, cambio, reembolso y rechazo |

---

## 3. Ambigüedades detectadas

| # | Dónde | Las dos lecturas | Qué se necesita para destrabarla |
| --- | --- | --- | --- |
| 1 | **El ciclo del cambio.** `CO-100` y el diagrama de clases dicen: se descuenta una unidad del reemplazo y se crea una `DevolucionFisica` «Pendiente de retiro» (estados: Pendiente de retiro, Retirado). **DME-12 y DME-16 dicen otra cosa**: `CO-100` crea un `ArticuloRetenido` «Reservado para cambio» y un `CambioProducto` que, según el motivo, espera una prueba de destrucción (defecto o error de imprenta) o la recepción del artículo (disconformidad). Lo cierran `CO-223` a `CO-226`, que **no existen**: no tienen contrato, ni ficha, ni DSS (B-09-001) | **(a)** Construir `CO-100` tal como lo declara el contrato: descuenta el stock, crea la `DevolucionFisica` pendiente y avisa al Cliente con las instrucciones. El reemplazo se entrega por fuera del sistema; DME-12 y DME-16 quedan como corrección del documento. **(b)** Lo mismo, y además crear el `ArticuloRetenido` reservado. Queda varado en ese estado hasta que existan los contratos que lo liberan. **(c)** No construir `CO-100` hasta que el responsable escriba `CO-223` a `CO-226` y la ficha que los usa (quién presenta la prueba de destrucción, quién la acepta) | **Resuelta por (a)** el 2026-10-16: los DME están desactualizados (R-09-001) |
| 2 | **Desde cuándo corre el plazo.** La ficha y `CO-099`: «desde el despacho». BR-14: «desde la recepción del bien». El sistema no registra la recepción | **(a)** Desde que el pedido pasó a Despachado (su transición); en una venta de mostrador, desde la venta. **(b)** Agregar una fecha de recepción | **Recomiendo (a)**. BR-14 queda como corrección: el sistema no conoce la recepción |
| 3 | **Qué línea se puede reclamar.** «El pedido está en estado Despachado», pero un pedido despachado puede tener líneas canceladas o artículos que quedaron retenidos en el local (despacho diferido) | **(a)** Sólo las líneas que salieron con el pedido (estado Despachado). Las canceladas y las de despacho diferido no se ofrecen. **(b)** También las diferidas, con el plazo contado desde su propia entrega | **Recomiendo (a)**. Lo diferido queda fuera de alcance |
| 4 | **Una línea de varias unidades.** El caso es único por línea (I-19), pero `CO-100` cambia «una unidad» | **(a)** El caso cubre una unidad: el cambio es una unidad y el reembolso vale una unidad. Una línea de 2 tomos admite un solo reclamo. **(b)** El caso cubre la línea entera: el cambio repone todas las unidades y el reembolso vale la línea | **Recomiendo (a)**, que es lo que dice `CO-100`. Si en la práctica hace falta reclamar varias unidades, es una enmienda de I-19 |
| 5 | **Cómo se calcula «el 100 % del valor original»** (`CO-101`) | **(a)** La regla del reembolso que ya usan la cancelación de pre-ventas y la demora (B-01-010): lo pagado en dinero se convierte a puntos hacia arriba; lo pagado con puntos devuelve los mismos puntos (con (a) en la 4, la parte de una unidad, hacia arriba). **(b)** Otra regla | **Recomiendo (a)** |
| 6 | **Los puntos que se ganaron con la compra.** RF-19: «En caso de devolución posterior, el sistema debe descontar del saldo del cliente los puntos correspondientes al monto reembolsado». `CO-101` no lo declara | **(a)** Lo del contrato: se acredita el reembolso y no se descuenta nada. Es lo mismo que hacen hoy la cancelación de pre-ventas y la del artículo demorado. **(b)** Además se debitan los puntos ganados por esa unidad, hasta donde alcance el saldo | **Recomiendo (a)**, con el criterio de C-08 (mandan los contratos). Queda como corrección de RF-19 o de `CO-101`, según lo que decida el responsable |
| 7 | **«El tiempo de respuesta estimado, si está configurado en CU-CFG-PAR»** (paso 6, `CO-099`). `CU-CFG-PAR` no tiene ese parámetro | **(a)** No se muestra, porque no hay de dónde sacarlo. **(b)** Agregar el parámetro | **Recomiendo (a)**. Corrección de la ficha o agregado de un parámetro, según decida el responsable |
| 8 | **«De valor igual o comparable»** (paso 5, opción A) | **(a)** No se valida: se muestran los dos precios y el Administrador decide. **(b)** Se exige el mismo precio | **Recomiendo (a)**. La ficha sólo bloquea la falta de stock (E1) |
| 9 | **Cómo se avisa al Administrador del caso nuevo** (paso 5) | **(a)** Por correo a los Administradores activos, como los avisos de pre-venta (B-01-009), y el caso aparece en el panel de Devoluciones. **(b)** Sólo en el panel | **Recomiendo (a)** |
| 10 | **La evidencia.** «Imagen o imágenes», «tamaño máximo admitido», «formato aceptado» (E4). Ningún artefacto da los valores | **(a)** De 1 a 5 imágenes, JPG, PNG o WebP de hasta 5 MB cada una, convertidas a WebP como las demás imágenes (RNF-05). **Se guardan fuera de la carpeta pública**: sólo las ven el Cliente dueño y el Administrador. **(b)** Otros límites | **Recomiendo (a)** |
| 11 | **Dónde ve el Cliente sus casos.** E2 presenta «el estado actual» del caso existente; ninguna ficha dice dónde se consulta después | **(a)** En el detalle del pedido de «Mi cuenta», al lado de cada línea reclamada: estado, resolución y motivo del rechazo. **(b)** Una sección propia | **Recomiendo (a)** |

---

## 4. Orden de construcción

| # | Qué | Depende de | Motivo |
| --- | --- | --- | --- |
| 1 | El parámetro «plazo máximo de devolución» en Parámetros, con E1 aislada (`CO-130`) | — | `CO-099` lo necesita para su precondición |
| 2 | `CasoDevolucion` y su evidencia; `CU-DEV-SOL` (`CO-185`, `CO-099`) desde el detalle del pedido | 1 | Sin casos no hay nada que resolver |
| 3 | `CO-186` y `CO-187`: el panel de casos pendientes, el historial filtrado y el detalle | 2 | |
| 4 | `CO-102` (rechazo) y `CO-101` (reembolso en puntos) | 3 | No dependen de la ambigüedad 1 |
| 5 | `CO-100` (cambio) | 3 | Toca stock: bloqueo y foco reforzado |

---

## 5. Riesgos

| Riesgo | Dónde | Cómo se cubre |
| --- | --- | --- |
| Dos Administradores resuelven el mismo caso a la vez, o lo resuelve uno y lo rechaza el otro | `CO-100` a `CO-102` | El caso se toma con bloqueo y se verifica que siga Pendiente. Prueba de concurrencia |
| El reemplazo se vende en el mostrador mientras se confirma el cambio | `CO-100` | El producto se toma con bloqueo y se verifica el stock dentro de la transacción (RNF-06). Prueba de concurrencia |
| Dos reclamos sobre la misma línea, desde dos pestañas | `CO-099` | I-19 es una restricción de unicidad en la base, no una comprobación de pantalla. Prueba |
| Un Cliente reclama sobre el pedido de otro, o un Cajero resuelve | `CO-099`, `CO-100` a `CO-102` | 404 para el pedido ajeno y 403 para el rol equivocado, probados por la dirección real |
| Las fotos de un Cliente quedan accesibles por su URL | Evidencia | Se sirven desde una vista que exige al dueño o al Administrador. Prueba de acceso |
| Un archivo que dice ser imagen y no lo es | E4 | Se abre con Pillow antes de guardar, como las demás imágenes. Prueba |

---

## 6. Fuera de alcance

- La confirmación del retiro físico (`DevolucionFisica` → Retirado): ningún caso de uso la
  especifica. El concepto guarda la fecha para cuando exista.
- Los reclamos de compras como invitado: la ficha de `CU-TDA-INV` los deja fuera del sistema.
- Los artículos de despacho diferido (ambigüedad 3).
- El reembolso en dinero: RF-14 sólo admite el cambio o los puntos.
