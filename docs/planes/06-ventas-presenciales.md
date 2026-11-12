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

---
---

# Plan — `06` Ventas Presenciales · segunda parte: el mostrador encendido y el cobro con QR

**Estado del plan:** Aprobado el 2026-11-12, con las recomendaciones de la sección 3. La parte B espera los números de contrato · **Fecha:** 2026-11-12

**Pedido del responsable** (2026-11-12): rediseñar **todo lo visual del Cajero** con el lenguaje de
la tienda (plan 07, novena parte); **sólo el Administrador queda sobrio**. Y que el mostrador
pueda **cobrar con el QR de MercadoPago**.

Son dos trabajos de distinta naturaleza y van separados:

| | A. El mostrador encendido | B. El cobro con QR |
| --- | --- | --- |
| **Qué cambia** | Cómo se ve | Qué puede hacer el Cajero: un medio de pago nuevo |
| **Toca la especificación** | No: sólo `TOKENS_VISUALES.md` e `identidad_visual.md`, que enmienda el responsable | Sí: `CU-VTA-REG` paso 5, un flujo alternativo y dos o tres operaciones nuevas |
| **Puede empezar** | Con este plan aprobado | Con este plan aprobado **y los números de contrato confirmados** |

## 1. Qué cubre

| Caso de uso | Contratos | Parte | Qué cambia |
| --- | --- | --- | --- |
| `CU-VTA-REG` | `CO-078` a `CO-082`, `CO-103`, `CO-104` | A | Sólo la pantalla |
| `CU-VTA-REG` | `CO-082` y **operaciones nuevas** (sección 4) | B | El paso 5 suma «QR de MercadoPago»; la venta se materializa cuando el pago se aprueba |
| `CU-CAJ-CIE` | `CO-203`, `CO-126`, `CO-127` | A y B | La pantalla; el cobro con QR entra en el cierre como **Pasarela** del canal presencial (decisión 2) |
| Stock en local (módulo 18) | `CO-151`, `CO-152` y las consultas del Cajero | A | Sólo la pantalla |
| Consulta del inventario | La del Cajero (`ProductoListaView` y ficha) | A | Sólo la pantalla |

## 2. Conceptos que toca

| Concepto | ¿Existe? | Qué hace este plan con él |
| --- | --- | --- |
| `TransaccionPago` | Sí | B: una venta de mostrador con QR queda con medio **Pasarela** y la referencia del pago en MercadoPago |
| `Pedido`, `LineaPedido`, `LotePuntos`, `MovimientoPuntos` | Sí | Sin cambios: los crea `CO-082` como hoy, recién cuando el pago se aprueba |
| **Cobro de mostrador** | **No** | B: el ticket congelado mientras el cliente paga (ítems, precios, canjes, cliente, monto, referencia, estado, vencimiento). Es al mostrador lo que `CobroEnCurso` es a la tienda. Lleva migración |

## 3. Decisiones

### A. El mostrador encendido

| # | Punto | Recomendación |
| --- | --- | --- |
| A1 | ¿El estilo nuevo va **por rol** o **por pantalla**? El Administrador también usa el mostrador y la caja | **Por rol**, como lo pediste: todo lo que ve el Cajero, encendido; todo lo que ve el Administrador, sobrio, también el mostrador |
| A2 | La misma regla de forma que la tienda | **Aparatos** redondeados con lima para lo encendido: la barra, el menú, el **visor del total** (como el de una caja registradora), el teclado de medios de pago, el lector de código. **Impreso** recto: el ticket en curso, el comprobante, la cinta del cierre de caja. El naranja sigue siendo la acción (Agregar, Cobrar) |
| A3 | Qué no se toca de lo que funciona | El foco en el buscador al entrar y después de agregar (el lector de código de barras escribe ahí y manda Enter), el destello de la fila recién agregada, el vuelto, el comprobante imprimible en blanco y negro, los canjes, los avisos y la capa de carga. Se verifica cada uno con su prueba o su captura |
| A4 | Movimiento | Sobrio en el mostrador: es una pantalla de trabajo que se usa todo el día. Las animaciones van donde informan (el total que cambia, la venta registrada); nada que demore un cobro |

Antes de programar armo **una maqueta navegable** del mostrador, el comprobante y la caja con datos
reales, como se hizo con la tienda, y la ajustamos sobre eso.

### B. El cobro con QR

| # | Punto | Las lecturas | Recomendación |
| --- | --- | --- | --- |
| B1 | **Qué QR** | (a) El enlace de pago de Checkout Pro, el mismo de la tienda, dibujado como QR: el cliente lo escanea con la cámara y paga en MercadoPago con dinero en cuenta o tarjeta. (b) El **QR nativo** de MercadoPago (sucursal y caja dadas de alta en la cuenta), que se escanea desde la app | **(a)**: reutiliza la integración verificada de punta a punta el 2026-11-07, no exige configurar sucursal ni caja en la cuenta y funciona con la pasarela de prueba para las demostraciones. (b) queda como mejora |
| B2 | **Con qué medio** queda en la caja | (a) **Pasarela**, que ya existe en el modelo, en el canal presencial. (b) Un medio nuevo, «QR» | **(a)**: el modelo ya declara que lo confirmado por la pasarela es «Pasarela», y el cierre lo separa por canal. La pantalla lo nombra «QR de MercadoPago» |
| B3 | **Cuándo existe la venta** | (a) Al aprobarse el pago: hasta entonces el ticket queda congelado en un cobro de mostrador. (b) Al generar el QR, y se anula si no se paga | **(a)**: es lo que hace la tienda (`CO-089`) y respeta `CO-082`, que dice que la venta nace despachada. Una venta que hubiera que anular no sería «despachada» |
| B4 | **El stock** mientras el cliente paga | (a) No se reserva: se verifica al generar el QR y otra vez al aprobarse. (b) Se reserva | **(a)**: la espera dura un par de minutos. Si al aprobarse ya no alcanza, porque se vendió en otra caja, el pago se reembolsa solo y el Cajero lo ve, como en la tienda (E3) |
| B5 | **Cancelar y vencer** | — | El Cajero puede cancelar el QR y volver al ticket. Vence a los **10 minutos**. Un pago que llega después de cancelar o vencer se reembolsa solo (como B-07-045) |
| B6 | **Cómo se entera la pantalla** | (a) Sólo por el aviso de MercadoPago. (b) Además, la pantalla pregunta cada 3 segundos y el sistema consulta el pago a MercadoPago por la referencia | **(b)**: el aviso no llega a una máquina sin dirección pública (desarrollo, una demostración local) y puede perderse. Con las dos vías, el cobro se resuelve igual |
| B7 | **Puntos** | — | Igual que hoy: los canjes se aplican antes de generar el QR; el QR cobra el saldo en dinero, y la acreditación se calcula sobre ese saldo al aprobarse |
| B8 | **Quién** | — | Cajero y Administrador, como el resto del mostrador |

## 4. Las operaciones nuevas

Necesitan número de contrato, que **asignás vos** (según `CODIGOS.md`, desde `CO-233`, en el orden en
que se redacten). Propongo estos nombres:

| Operación | Qué hace | Paso |
| --- | --- | --- |
| `generarCobroConQR()` | Congela el ticket, verifica stock y saldo de puntos, crea el cobro en la pasarela y devuelve el QR y su vencimiento | `CU-VTA-REG` paso 5, flujo alternativo nuevo |
| `consultarCobroConQR(referencia)` | El estado del cobro: esperando, aprobado (con el comprobante), rechazado o vencido | El mismo flujo |
| `cancelarCobroConQR(referencia)` | Descarta el cobro y devuelve el ticket al Cajero | El mismo flujo |

Cuando se aprueba el pago, el sistema ejecuta `CO-082` con medio Pasarela y la referencia del pago.
No hace falta otra operación: es la misma escritura de hoy, con otro disparador.

Las pruebas llevan el código de cada contrato en el nombre, así que **la parte B arranca cuando
tenga los números**. Mientras tanto avanzo con la A.

## 5. Orden de construcción

| # | Qué | Motivo |
| --- | --- | --- |
| 1 | Maqueta del mostrador, el comprobante y la caja del Cajero | Decidir lo visual sobre algo que se ve, no sobre texto |
| 2 | La hoja del Cajero y la cáscara (barra y menú) | Todo lo demás se apoya ahí |
| 3 | Mostrador y comprobante | La pantalla que más se usa |
| 4 | Caja, stock en local, consulta del inventario y perfil | El resto de lo que ve el Cajero |
| 5 | El cobro de mostrador, el servicio y la pasarela de prueba | B, con los números confirmados |
| 6 | MercadoPago: la preferencia del mostrador, el aviso y la consulta por referencia | Se prueba con la puerta HTTP cortada, y después contra la cuenta de prueba en la VM |
| 7 | La pantalla del QR en el mostrador | Al final, sobre lo que ya funciona |

## 6. Riesgos

| Riesgo | Cómo se cubre |
| --- | --- |
| El estilo del Cajero se filtra al Administrador, o al revés | La hoja nueva sólo aplica bajo una clase que pone la cáscara cuando el rol es Cajero; una prueba lo verifica para cada rol |
| Romper el lector de código de barras o el foco | Pruebas del flujo de agregar, más una captura con el foco puesto |
| Un pago aprobado de un ticket sin stock | Verificación al aprobarse con bloqueo de los productos, como hoy; reembolso automático; prueba de concurrencia con dos cajas |
| Un aviso repetido crea dos ventas | La referencia del pago ya es única en `TransaccionPago`; prueba con el aviso duplicado |
| El celular no llega al sistema en desarrollo | En la VM sí. Para demostrar en local, la pasarela de prueba ofrece el mismo enlace también para abrirlo desde la computadora |

## 7. Fuera de alcance

- El QR nativo de MercadoPago con sucursal y caja (decisión B1).
- Cobrar con el posnet de MercadoPago (Point).
- Reembolsar desde el mostrador: la devolución sigue su circuito de siempre (módulo 09).
- Cambiar lo visual del Administrador.
