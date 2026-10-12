> **Tipo: Normativo** una vez aprobado. Antes de la aprobación es una propuesta.
> Se escribe **antes** de programar y **no se reescribe** después: si algo cambió durante la
> construcción, eso va a la bitácora del módulo, no acá.

# Plan — `06` Ventas Presenciales

**Estado del plan:** Aprobado el 2026-10-10, con las recomendaciones de la sección 3 salvo la 1: en
lugar del DNI, un código de cliente fácil de recordar, visible en «Mi cuenta» (B-06-001) ·
**Fecha:** 2026-10-10

El mostrador: el Cajero o el Administrador arma un ticket, vincula la cuenta del cliente si la
tiene, canjea puntos por ítem y cobra. Hoy `MostradorView` es una pantalla vacía. Va antes que
Caja (plan 14), que consolida estas ventas con las online.

---

## 1. Qué cubre

| Caso de uso | Contratos | Operaciones de escritura | Operaciones de consulta |
| --- | --- | --- | --- |
| `CU-VTA-REG` | `CO-078` a `CO-082` | 1 (`CO-082`) | 4 |
| `CU-PTS-CJE` (rama de mostrador) | `CO-103`, `CO-104` desde el ticket | 0 | 2 |

**Total: 7 contratos.** `CO-103` y `CO-104` ya están verificados en la tienda; acá se ejercen
sobre el ticket, y con eso `CU-PTS-CJE` deja de estar `Parcial`.

---

## 2. Conceptos que toca

| Concepto | ¿Existe? | Qué hace este plan con él |
| --- | --- | --- |
| `Pedido`, `LineaPedido`, `TransaccionPago` | Sí | `CO-082` los crea: canal Presencial, estado Despachado, medio Efectivo, Transferencia o Tarjeta |
| `TransicionDePedido` | Sí | La venta nace con su única transición, Despachado |
| `LotePuntos`, `MovimientoPuntos` | Sí | Débito FIFO del canje y acreditación del reintegro (B-10-004) |
| `Producto` | Sí | Descuento de stock con bloqueo; el que llega a cero pasa a Agotado |
| `Usuario` | Sí | Ambigüedad 1: cómo se lo encuentra en el mostrador |
| El ticket en curso | **No** | Ambigüedad 2 |

---

## 3. Ambigüedades detectadas

| # | Dónde | Las dos lecturas | Qué se necesita para destrabarla |
| --- | --- | --- | --- |
| 1 | **«Por DNI o código de cliente»** (RF-13, `CU-VTA-REG` paso 3, `CO-081`). `Usuario` no tiene DNI ni código de cliente | **(a)** `Usuario` gana el **DNI**, opcional y único, que el Cliente carga al registrarse o en «Mis datos». El **código de cliente** es el número de cuenta, que el Cliente ve en «Mi cuenta». El mostrador busca por DNI, código o correo. **(b)** Sólo por correo, sin campos nuevos | Decisión. **Recomiendo (a)**: es lo que piden RF-13 y el contrato; el correo es un respaldo para quien no cargó el DNI. Es una corrección del modelo y va a la bitácora |
| 2 | **Dónde vive el ticket en curso.** `CO-078`: «una transacción de venta en curso, sin materializar aún ningún concepto persistente del dominio» | **(a)** En la sesión del Cajero, como el checkout. Si cierra la pestaña, el ticket sigue al volver; si cierra sesión, se pierde. **(b)** Una tabla técnica | **Recomiendo (a)**: no es un concepto del dominio, y el contrato lo dice |
| 3 | **Agregar por código** (`CU-VTA-REG` paso 2: «por nombre o código») | **(a)** Un solo campo: si lo escrito coincide exacto con un código, un código de barras o un ISBN, se agrega directo (sirve para un lector de códigos); si no, se listan coincidencias por título para elegir. **(b)** Sólo búsqueda por título | **Recomiendo (a)**: en un mostrador, escanear y seguir es la operación más frecuente |
| 4 | **Qué se puede vender** | `CO-079`: «el producto tiene stock mayor o igual a la cantidad». **(a)** Sólo productos Activos con stock; una pre-venta no se vende en el local hasta que llega | **Recomiendo (a)** |
| 5 | **El comprobante** (`CO-082`, salida) | **(a)** Una pantalla de confirmación con el detalle, imprimible desde el navegador. No es una factura: la facturación electrónica no está en el alcance. **(b)** Un PDF | **Recomiendo (a)** |
| 6 | **«Corrección de transacciones»** del Administrador (`CU-VTA-REG`, actores) | Ningún caso de uso la describe | No se construye. Si hace falta, es un caso de uso nuevo que asigna el responsable |

---

## 4. Orden de construcción

| # | Qué | Depende de | Motivo |
| --- | --- | --- | --- |
| 1 | `Usuario.dni` (si la amb. 1 es (a)), en el registro, «Mis datos» y la ficha del cliente; el código de cliente en «Mi cuenta» | — | Sin esto no hay cómo vincular |
| 2 | El ticket en sesión: `CO-078`, `CO-079` (con E1), `CO-080` | — | |
| 3 | `CO-081` y el canje desde el ticket (`CO-103`, `CO-104`, E2) | 1, 2 | |
| 4 | `CO-082`: pedido, transacción, stock, puntos, auditoría y comprobante | 3 | La única escritura |
| 5 | La pantalla del mostrador, rápida de usar con teclado | 2–4 | Reemplaza la vacía de hoy |

---

## 5. Riesgos

| Riesgo | Dónde | Cómo se cubre |
| --- | --- | --- |
| Venta del último ejemplar a la vez en el local y en la tienda | `CO-082`, RNF-06 | Bloqueo de los productos en orden de clave, como `CO-089`. Prueba de concurrencia mostrador contra tienda |
| El saldo cambió entre el canje y la confirmación | `CO-082` | Se vuelve a verificar al confirmar; si no alcanza, no se confirma y se avisa |
| Dinero con flotantes | Totales, puntos | `Decimal` en todo |
| Un Cliente u otro rol usa el mostrador | Acceso | 403 por la dirección real |
| `CO-079` toca el stock antes de tiempo | `CO-079` | Postcondición negativa explícita, con prueba |

---

## 6. Fuera de alcance

- La factura electrónica y el ticket fiscal.
- La corrección de una venta ya confirmada (ambigüedad 6).
- Dividir un pago entre varios medios: RF-13 lo excluye.
- La integración con la terminal de tarjeta: se registra el medio, no se cobra desde el sistema.
