> **Tipo: Normativo** una vez aprobado. Antes de la aprobación es una propuesta.
> Se escribe **antes** de construir y **no se reescribe** después: lo que cambie va a
> `bitacora/00-documentacion-de-pruebas.md`.

# Plan — `00` Pruebas integrales: fiabilidad, eficacia y eficiencia

**Estado del plan:** Propuesto · **Fecha:** 2026-10-15

Los casos de prueba de [`CASOS_DE_PRUEBA.md`](../pruebas/CASOS_DE_PRUEBA.md) (CP-01 a CP-28) se
eligieron el 2026-10-07, cuando no existían la compra, los pedidos, los puntos, el mostrador, la
caja, la pre-venta, el stock en local ni el restock. Por eso dejaron afuera R-03 y R-06. Desde
entonces el sistema creció a 75 casos de uso verificados, y la suite (2495 pruebas) los cubre
operación por operación: **cada contrato por separado**. Este plan agrega lo que la suite no mira:

- **Fiabilidad:** que el sistema siga siendo coherente cuando las operaciones se combinan, se
  repiten, fallan a mitad o corren durante semanas.
- **Eficacia:** que cada actor pueda llegar a su objetivo recorriendo las pantallas. **La capa de
  flujo de [`ESPECIFICACION.md`](../pruebas/ESPECIFICACION.md) no tiene hoy ninguna prueba.**
- **Eficiencia:** que los tiempos y el costo en consultas se mantengan con volumen y con carga,
  incluidas las pantallas y los procesos nuevos.

No cambia el comportamiento del sistema. Lo que estas pruebas encuentren va a la bitácora del
módulo afectado y se corrige como cualquier hallazgo.

---

## 1. Qué cubre

Treinta y un casos nuevos, CP-29 a CP-59, en tres grupos. Cada uno dice con qué se ejecuta.

### Fiabilidad

| Caso | Qué verifica | Riesgo o requisito | Se ejecuta con |
| --- | --- | --- | --- |
| CP-29 | **Ninguna unidad aparece ni desaparece.** Una jornada simulada de ventas por tienda y mostrador, reservas, llegadas, demoras, cancelaciones, retiros y vencimientos de stock en local. Al final, para cada producto: stock inicial + llegadas + reintegros − ventas = stock final, y nunca negativo | `RNF-06` · R-03 | Prueba de la suite, semilla fija |
| CP-30 | **Ningún punto aparece ni desaparece.** La misma jornada: para cada cliente, saldo = acreditado − debitado − vencido, cada lote con disponible entre 0 y lo acreditado, y cada movimiento con su saldo resultante | `RF-19` · `BR-05` · `BR-06` | Prueba de la suite |
| CP-31 | **El dinero cuadra.** La suma de transacciones aprobadas es igual a lo cobrado en pedidos más los envíos de stock en local, y el cierre de caja da la misma cifra por canal y por medio | `CU-CAJ-CIE` · R-03 | Prueba de la suite |
| CP-32 | **El estado de cada pedido es coherente con sus líneas** después de la jornada: ninguno en espera sin líneas que esperen, ninguno cancelado con líneas vivas, ninguno despachado con líneas pendientes salvo el diferido | DME-07, DME-08 | Prueba de la suite |
| CP-33 | **Cien días de Temporizador.** Con el reloj avanzando de a un día y escenarios sembrados: a lo sumo una propuesta de restock por semana, ninguna compensación arriba del 25 %, ningún aviso repetido, cada vencimiento procesado una sola vez, ofertas activadas y vencidas en su día | R-15 · `BR-05`, `BR-09`, `BR-10` | Prueba marcada `lenta` |
| CP-34 | **Correr el Temporizador dos veces el mismo día no cambia nada la segunda vez**: ni datos, ni correos, ni auditoría | R-15 | Prueba de la suite |
| CP-35 | **Un fallo a mitad no deja nada a medias**, en cada operación que escribe en varias tablas: compra (`CO-089`), venta de mostrador (`CO-082`), cierre de caja (`CO-126`), cancelación en lote (`CO-027`), cancelación de un demorado (`CO-098`), envío de stock en local (`CO-151`) y despacho a proveedor (`CO-072`). Se fuerza el fallo en cada escritura, una por vez | `RNF-06` · R-08 | Prueba de la suite (amplía CP-25) |
| CP-36 | **Un correo caído nunca deshace la operación.** Con el servidor de correo rechazando todo, cada operación que avisa termina igual y el fallo queda registrado | R-03 | Prueba de la suite |
| CP-37 | **El aviso de la pasarela, mal comportado**: repetido, desordenado (rechazo después de aprobación), con otro monto, de un cobro que no existe, sin firma, y llegando después de que el stock se agotó. Cada caso deja un solo resultado válido y, si cobró sin entregar, el reembolso | R-06 | Prueba de frontera |
| CP-38 | **La pasarela caída al iniciar el cobro**: no queda nada cobrado ni reservado, y el carrito sigue igual | R-06 | Prueba de frontera |
| CP-39 | **Sin internet, el local sigue vendiendo.** Con toda salida a la red cortada (pasarela, correo, cotizaciones, modelo de lenguaje), el mostrador vende en efectivo y con canje, y la caja cierra | R-03 | Prueba de la suite |
| CP-40 | **Carreras cruzadas** que hoy no tienen prueba: canje del mismo saldo en tienda y mostrador a la vez; cierre de caja durante una venta; demora registrada mientras un cliente reserva esa pre-venta; edición de stock durante una compra del último ejemplar | `RNF-06` | Prueba de concurrencia |
| CP-41 | **La base se cae en medio del aviso de pago** y vuelve: la pasarela reintenta y el pedido se genera una sola vez | R-08 · R-06 | `scripts/demo/caida_base.py` (amplía CP-24) |

### Eficacia

| Caso | Recorrido de punta a punta, sólo por las pantallas | Casos de uso | Se ejecuta con |
| --- | --- | --- | --- |
| CP-42 | El Cliente se registra, activa la cuenta desde el correo, busca, agrega al carrito, paga y sigue el pedido hasta que el Administrador lo despacha | `CLI-ALT`, `AUT-ACT`, `TDA-CAT`, `TDA-CRA`, `TDA-CMP`, `PED-EST`, `CLI-HIS` | Prueba de flujo |
| CP-43 | El invitado compra sin cuenta y recibe cada cambio de estado por correo | `TDA-INV`, `PED-EST` | Prueba de flujo |
| CP-44 | Una pre-venta se reserva, se demora, el Cliente elige recibir lo disponible, el artículo llega, queda en el local y el Cliente pide el envío y lo paga | `ALT-DEM`, `PED-OPC`, `ALT-TRA`, `STK-CON`, `STK-DES`, `STK-FIS` | Prueba de flujo |
| CP-45 | El cajero vende con canje usando el código de cliente, y al final del día cierra la caja y exporta el CSV | `VTA-REG`, `PTS-CJE`, `CAJ-CIE` | Prueba de flujo |
| CP-46 | Un producto se agota, dos clientes piden el aviso, la propuesta de restock lo incluye, se pide al proveedor, se repone y los avisados lo compran | `RST-SUS`, `RST-PRO`, `RST-APR`, `CAT-EDI`, `RST-NOT` | Prueba de flujo |
| CP-47 | La editorial cancela un título con reservas de varios clientes, cada uno ve su reembolso en «Mis puntos» y lo canjea en otra compra | `ALT-CAN`, `PTS-CON`, `PTS-CJE` | Prueba de flujo |
| CP-48 | Un lote importado se carga, se le pone una oferta, se vende con el precio de la oferta y la oferta vence sola | `ALT-IMP`, `PVP-ALT`, `TDA-CMP` | Prueba de flujo |
| CP-49 | Un correo de proveedor llega, el modelo propone borradores, el Administrador los revisa y confirma, y sale el pedido al proveedor | `ALT-NOV`, `ALT-REV`, `RST-PED` | Prueba de flujo |
| CP-50 | **Ningún enlace roto.** Un rastreador recorre, para cada rol, todas las páginas a las que se llega desde el menú y sigue cada enlace interno: ninguno responde 404 ni 500, y ninguno lleva a una página que el rol no puede abrir | `RNF-03` · eficacia de la navegación | Prueba de flujo, sobre datos sembrados |
| CP-51 | **Cada correo lleva a donde dice.** Para cada correo que el sistema manda, el enlace que trae abre la página correcta para su destinatario | `RF-23` | Prueba de flujo |
| CP-52 | **La suite detecta los errores de las zonas nuevas.** Las mutaciones de puntos, compensación, reembolso, costo de envío y cobertura de reservas hacen fallar al menos una prueba cada una | Foco reforzado: dinero y stock | `scripts/demo/mutacion.py` y `sabotaje.py` (amplía CP-01) |

### Eficiencia

| Caso | Qué verifica | Requisito | Se ejecuta con |
| --- | --- | --- | --- |
| CP-53 | **Las pantallas nuevas no crecen en consultas con el volumen**: pedidos, «Mi cuenta», «Mis puntos», stock en local (panel y cliente), pre-ventas por llegar, propuesta de restock, resumen de caja y mostrador. Mismas consultas con 10 registros que con 2000, y nunca más que el tope de la ambigüedad 6 | `RNF-02` | Prueba de la suite (amplía CP-28) |
| CP-54 | **Los procesos del Temporizador escalan**: con 10 000 artículos retenidos, 10 000 suscripciones y 2000 líneas demoradas, cada ciclo termina dentro del tope y sus consultas crecen como mucho en proporción a lo que procesa | `RNF-07` · R-15 | Prueba marcada `lenta` |
| CP-55 | **Las consultas que más se repiten usan índice**: pedidos de un cliente, líneas por producto y estado, artículos por estado y vencimiento, suscripciones por producto, transacciones sin cierre. Ninguna recorre la tabla entera sobre la base poblada | `RNF-02` | Script nuevo sobre la base de la demostración |
| CP-56 | **Línea base de las operaciones nuevas**: checkout, confirmar venta, resumen de caja, pre-ventas por llegar, propuesta de restock, stock en local. Percentil 95 por debajo de 2 segundos | `RNF-02` | `scripts/demo/linea_base.py` (amplía CP-26) |
| CP-57 | **Carga con compras reales**: 50 sesiones durante 10 minutos, con clientes que compran por la pasarela de prueba y cajeros que venden en el mostrador. Ningún error, ninguna venta del mismo último ejemplar dos veces, y la degradación dentro del 20 % | `RNF-07` · `RNF-06` | `locustfile.py` (amplía CP-27) |
| CP-58 | **Dónde se quiebra.** Escalones de 10 en 10 usuarios hasta que el percentil 95 pasa de 2 segundos o aparece el primer error: queda registrado el punto de quiebre y qué se agotó primero | `RNF-07` | `scripts/demo/escalones.py` |
| CP-59 | **El tiempo de la suite** se mide en cada cierre de módulo: si crece más de un 25 % respecto del cierre anterior, se identifican las pruebas responsables | Mantenibilidad | `pytest --durations` en el cierre |

---

## 2. Qué toca

| Pieza | ¿Existe? | Qué hace este plan |
| --- | --- | --- |
| `docs/pruebas/CASOS_DE_PRUEBA.md` | Sí | Gana CP-29 a CP-59 y el criterio ampliado (ambigüedad 2) |
| `docs/pruebas/ESPECIFICACION.md` | Sí | Gana lo que se decida en la ambigüedad 1 |
| `apps/*/tests/` | Sí | Pruebas nuevas de flujo, de frontera, de concurrencia y de invariantes |
| Un simulador de jornada | **No** | Genera la secuencia de operaciones de CP-29 a CP-32, siempre por los servicios reales |
| `scripts/demo/` | Sí | `linea_base.py`, `locustfile.py`, `mutacion.py`, `sabotaje.py` y `caida_base.py` se amplían; se agrega uno para los índices (CP-55) |
| El código de la aplicación | Sí | **No cambia.** Lo que se encuentre va a la bitácora y se corrige aparte |

---

## 3. Ambigüedades detectadas

| # | Dónde | Las lecturas | Qué se necesita para destrabarla |
| --- | --- | --- | --- |
| 1 | **En qué capa van las invariantes y el rendimiento.** `ESPECIFICACION.md` tiene cinco capas; las invariantes de jornada (CP-29 a CP-32) y la medición de consultas no encajan en ninguna | **(a)** Una sexta capa, **Invariante**, con el prefijo `test_invariante_`, y el rendimiento como prefijo `test_volumen_` dentro de Flujo. **(b)** Forzarlas en Contrato y Flujo | **Recomiendo (a)**: cambia un archivo Normativo y se aprueba con este plan |
| 2 | **El criterio de selección** de `CASOS_DE_PRUEBA.md` deja afuera R-06 (exposición 1,20, debajo del corte de 1,80) | **(a)** Entran R-03 y R-06 ahora que ventas y pagos están construidos: la pasarela mueve dinero. **(b)** Sólo R-03, que pasa el corte | **Recomiendo (a)** |
| 3 | **El azar en la simulación.** Una jornada aleatoria encuentra más, pero una falla que no se repite no se puede diagnosticar | **(a)** En la suite, tres semillas fijas: siempre la misma secuencia. Aparte, un script que corre semillas nuevas y guarda la que falló para volverla una prueba fija. **(b)** Semillas nuevas en cada corrida de la suite | **Recomiendo (a)** |
| 4 | **Las pruebas lentas** (CP-33, CP-54) tardan minutos y la suite hoy tarda tres | **(a)** Se marcan `lenta`, se excluyen de la corrida de todos los días y son obligatorias en el cierre de cada módulo y en el ensayo de la demostración. **(b)** Siempre en la suite | **Recomiendo (a)**. La puerta «Suite de pruebas» pasa a decir «incluidas las lentas, en el cierre» |
| 5 | **Qué quiere decir R-03** en lo construido. El sistema no tiene modo sin conexión, y eso está aceptado | **(a)** Que lo que no necesita la red siga funcionando cuando la red se cae: el mostrador, la caja y el panel (CP-39). **(b)** Construir un modo sin conexión | **Recomiendo (a)**: (b) cambia el alcance |
| 6 | **Los topes de eficiencia**, que `RNF-02` no fija salvo los 2 segundos | **(a)** Hasta **30 consultas** por pantalla; hasta **10 segundos** por ciclo del Temporizador con el volumen de CP-54; el tiempo de la suite, hasta un 25 % más que el cierre anterior. **(b)** Medir sin topes y decidir después | **Recomiendo (a)**: un número que no se puede pasar es lo que convierte una medición en una prueba |
| 7 | **El rastreador de enlaces** (CP-50) sigue todo lo que encuentra, y algunos enlaces son acciones | **(a)** Sigue sólo los `GET`; los formularios no se envían. **(b)** También envía los formularios | **Recomiendo (a)**: los formularios ya los recorren CP-42 a CP-49 |
| 8 | **Si una prueba nueva encuentra un error.** El plan es de pruebas y no cambia la aplicación | **(a)** Se registra en la bitácora del módulo, se corrige en esa misma tanda con su prueba en verde, y se informa en el cierre. **(b)** Se deja la prueba marcada como fallida esperada y se corrige en otro plan | **Recomiendo (a)**, salvo que la corrección cambie lo que el usuario puede hacer: eso se consulta |

---

## 4. Orden de construcción

| # | Qué | Depende de | Motivo |
| --- | --- | --- | --- |
| 1 | La capa y los prefijos nuevos en `ESPECIFICACION.md`, y el criterio y la tabla de riesgos en `CASOS_DE_PRUEBA.md` | Aprobación | Fija dónde va cada cosa antes de escribir pruebas |
| 2 | Flujos CP-42 a CP-49 y rastreador CP-50, CP-51 | 1 | Es la capa que falta entera y la que más rápido encuentra pasos inalcanzables |
| 3 | Simulador de jornada y CP-29 a CP-32 | 1 | Lo usan CP-33 y CP-40 |
| 4 | Fallos y frontera: CP-35 a CP-39, CP-41 | 3 | |
| 5 | Concurrencia y Temporizador: CP-33, CP-34, CP-40 | 3 | |
| 6 | Eficiencia en la suite: CP-53, CP-54, CP-59 | 1 | |
| 7 | Eficiencia sobre la base de la demostración: CP-55 a CP-58 | 6 | Necesita el servidor y la base poblada; se amplía `poblar.py` con pedidos, puntos, stock en local y suscripciones |
| 8 | Mutación y sabotaje en las zonas nuevas: CP-52 | 2 a 5 | Mide si todo lo anterior detecta errores de verdad |

---

## 5. Riesgos

| Riesgo | Dónde | Cómo se cubre |
| --- | --- | --- |
| La simulación encuentra fallos que dependen del orden y no se pueden repetir | CP-29 a CP-33 | Semillas fijas en la suite y la semilla guardada en cada falla (amb. 3) |
| Las pruebas de concurrencia fallan a veces por la máquina, no por el sistema | CP-40, CP-57 | Cada una corre cinco veces seguidas antes de darla por buena, como las existentes |
| Las mediciones de tiempo dependen de la máquina | CP-56 a CP-58 | Se comparan contra la línea base de la misma máquina y se informa el equipo usado |
| La suite se vuelve lenta y se deja de correr | Todo | Marca `lenta` (amb. 4) y CP-59 |
| La base de la demostración no tiene los datos de las partes nuevas | CP-55 a CP-58 | Se amplía `poblar.py`; `restaurar.py` la vuelve al punto de partida |

---

## 6. Fuera de alcance

- La compatibilidad con navegadores (`RNF-08`) y el diseño responsivo (`RNF-01`): se revisan a mano
  con capturas, como hasta ahora.
- HTTPS (`RNF-10`) más allá de lo que ya verifica `check --deploy`.
- Los módulos que faltan (09, el resto del 10, `CU-CLI-BAJ`, 15): sus casos se agregan cuando
  existan.
- Las pruebas de penetración externas: CP-12 a CP-22 cubren lo que se puede automatizar acá.
