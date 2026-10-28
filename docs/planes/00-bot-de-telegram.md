> **Tipo: Normativo** una vez aprobado. Antes de la aprobación es una propuesta.
> Se escribe **antes** de programar y **no se reescribe** después: si algo cambió durante la
> construcción, eso va a la bitácora del módulo, no acá.

# Plan — `00` El perfil del Administrador y el bot de Telegram

**Estado del plan:** Aprobado el 2026-10-27, con las decisiones recomendadas · **Fecha:** 2026-10-27

Pedido del responsable (2026-10-27): una página de perfil para el Administrador, desde donde
vincular Telegram y elegir por dónde recibir los avisos del sistema; por el bot, recibir los
correos de proveedores y aprobarlos o descartarlos, y los avisos de pre-ventas (llegadas,
atrasos, demoras); y, más adelante, cargar productos como borradores desde el móvil.

**La especificación no menciona Telegram**: no hay requerimiento, caso de uso ni contrato (ya lo
decía el plan 00 de interfaz, apartado 24). **Es un cambio de alcance**: hacen falta casos de uso
nuevos, con los códigos que asigne el responsable, y la enmienda del documento.

---

## 1. Qué cubre

Dos etapas. La primera es la que pidió el responsable; la segunda, lo que propone este plan.

| # | Caso de uso (nombre) | Código | Etapa | Qué hace |
| --- | --- | --- | --- | --- |
| A | **Consultar mi perfil** | A asignar | 1 | El Administrador ve sus datos (nombre, correo, rol, último ingreso) y entra a sus avisos y a Telegram. Los datos se corrigen por `CU-USR-MOD`, como hoy |
| B | **Elegir los canales de aviso** | A asignar | 1 | Por cada tipo de aviso (tabla del apartado 2), correo, Telegram, los dos o ninguno |
| C | **Vincular Telegram** | A asignar | 1 | Un enlace `t.me/<bot>?start=<código>` de un solo uso, que vence en 15 minutos; el bot confirma el vínculo en el chat |
| D | **Desvincular Telegram** | A asignar | 1 | Desde el perfil o con `/salir` en el chat. Los avisos vuelven a salir por correo |
| E | **Resolver un correo de proveedor desde Telegram** | A asignar | 1 | El aviso de correo nuevo trae «Aprobar y procesar» y «Descartar». Aprobar es `CO-017`; descartar es `CO-018`, con el motivo elegido de una lista corta o escrito |
| F | **Cargar un borrador desde Telegram** | A asignar | 2 | Una foto de la tapa y un texto («Berserk Deluxe 5, Ivrea, B6, 24900»). El modelo lo lee como lee una novedad y queda un **borrador** en la revisión de la web (`CU-ALT-REV`). Nunca un producto |
| G | **Consultar desde Telegram** | A asignar | 2 | Preguntas de sólo lectura: «¿cuántos Chainsaw Man #12 hay?», «¿qué llega esta semana?». El modelo elige una de las consultas permitidas y el sistema la responde |

**Los avisos no son casos de uso nuevos**: son el mismo aviso de hoy (las llegadas de `CO-013`, la
demora de `CO-015`, el correo nuevo de `CO-016`, la propuesta de `CO-067`, el reclamo de
devoluciones…), que sale por el canal que eligió cada Administrador. Cambia la enmienda de esos
pasos («notifica al Administrador **por los canales que eligió**»), no su flujo.

---

## 2. Conceptos que toca

| Concepto | ¿Existe? | Qué hace este plan con él |
| --- | --- | --- |
| `Usuario` | Sí | Sólo lo lee: el perfil y el rol |
| **Vínculo con Telegram** | No | Lo crea: usuario, identificador del chat, desde cuándo. Uno por usuario. Es un dato personal |
| **Código de vinculación** | No | Lo crea: un solo uso, vence en 15 minutos, como `EnlaceActivacion` |
| **Preferencia de aviso** | No | Lo crea: usuario, tipo de aviso, correo sí/no, Telegram sí/no |
| `CorreoProveedor` | Sí | Etapa 1: se aprueba o se descarta desde el bot, con las mismas operaciones |
| `BorradorProducto` | Sí | Etapa 2: **gana un origen** (correo o Telegram) y el correo pasa a ser opcional |
| `RegistroAuditoria` | Sí | Lo que se hace desde el bot se audita igual, con el canal en el detalle |

**Los tipos de aviso**, sacados de los doce lugares donde hoy se avisa al Administrador:

| Tipo | De dónde sale hoy |
| --- | --- |
| Correos de proveedores | Correo nuevo en la cola, casilla sin conexión (`CO-016`) |
| Pre-ventas | Las que llegan pronto o hoy, las atrasadas (`CO-011`, `CO-012`), la demora con pedidos sin actualizar |
| Pedidos de clientes | Decisiones ante una demora, cancelaciones (`CU-PED-OPC`) |
| Restock | Propuesta lista, pedido que no salió (`CO-067`, `CO-074`) |
| Devoluciones | Reclamo nuevo |
| Stock en local | Solicitud de despacho, vencimientos |

---

## 3. Ambigüedades detectadas

| # | Dónde | Las dos lecturas | Lo que recomiendo |
| --- | --- | --- | --- |
| 1 | Quién usa el bot | Sólo el Administrador / también el Cajero y el Cliente | **Sólo el Administrador** por ahora. El Cliente con Telegram (sus pedidos, el aviso de stock) queda para después del cierre |
| 2 | El perfil | Sólo ver los datos / también editarlos ahí | **Ver**, con un enlace a `CU-USR-MOD` para corregirlos: ya existe y ya se audita. Y el cambio de contraseña propio, que hoy el personal no tiene salvo por la recuperación |
| 3 | Preferencias por defecto | Todo por correo / todo por los dos canales | **Todo por correo, como hoy**. Vincular Telegram ofrece encender los avisos ahí |
| 4 | Telegram caído o desvinculado | El aviso se pierde / vuelve al correo | **Vuelve al correo**: un aviso no se pierde por el canal |
| 5 | Descartar desde el bot | Motivo obligatorio escrito / motivos rápidos | **Botones con motivos frecuentes** («No es de novedades», «Repetido», «Promoción») y «Otro motivo…» para escribirlo. `CO-018` exige motivo y lo sigue teniendo |
| 6 | Correo nuevo con el modelo | El aviso dice sólo asunto y remitente / el modelo lo clasifica antes | **Asunto, remitente y las primeras líneas, sin el modelo.** Clasificar antes de aprobar contradice `CU-PRV-COL` (el modelo corre recién al aprobar); si se quiere, es una decisión aparte |
| 7 | Webhook o consulta | El bot recibe por webhook (HTTPS público) / el sistema pregunta cada tanto | **Webhook en la VM** (ya tiene HTTPS) y, en esta PC, `manage.py escuchar_telegram` que consulta mientras corre |
| 8 | El borrador desde Telegram (etapa 2) | Exige correo de origen / origen propio | **Origen propio** («Telegram», con quién lo cargó): el borrador va a la misma revisión, con los mismos controles. Cambia `CO-017` y el modelo |
| 9 | La foto en la etapa 2 | El modelo lee la tapa / la foto es sólo la portada | **La foto es la portada** y los datos salen del texto. Leer la tapa necesita un modelo con visión: el local no la tiene; OpenRouter sí, con costo |
| 10 | Las consultas (etapa 2) | El modelo arma la consulta / elige entre consultas fijas | **Entre consultas fijas** (stock de un producto, lo que llega, pedidos por armar, correos pendientes, la caja del día). El modelo no toca la base: elige la consulta y sus parámetros, y el sistema responde. Regla 4: nada que modifique |

---

## 4. Orden de construcción

| # | Qué | Depende de | Motivo |
| --- | --- | --- | --- |
| 1 | **Avisos con canales**: el aviso dice qué y a quién; un despachador decide por dónde. Sin Telegram, todo sigue saliendo por correo | — | Es la pieza que usa todo lo demás, y no cambia nada visible |
| 2 | **El perfil y las preferencias** (A, B) | 1 | La página que pidió el responsable |
| 3 | **La salida a Telegram** por la única puerta HTTP (`integraciones.pedir`), el token en `.env` y la vinculación (C, D) | 2 | Con la red cortada en las pruebas desde el primer día |
| 4 | **Los avisos por Telegram** y el correo con sus botones (E) | 3 | Lo que el responsable más quiere |
| 5 | Etapa 2: el borrador y las consultas (F, G) | 4 | Si hay tiempo antes del cierre |

---

## 5. Riesgos

| Riesgo | Dónde aparece | Cómo se cubre |
| --- | --- | --- |
| Alguien que no es el Administrador aprieta un botón | E | Cada botón lleva una firma; se verifica que el chat sea de un Administrador **activo** en el momento de la acción, no al mandar el aviso |
| Dos administradores aprueban el mismo correo, uno en la web y otro en el chat | E | Ya lo resuelve `CO-017` E1: el segundo ve el estado actual |
| El token del bot se filtra | 3 | Vive en el `.env` (no en la base ni en el repositorio); el webhook exige el secreto de Telegram en una cabecera |
| El procesamiento tarda minutos y Telegram espera la respuesta | E | Se contesta enseguida («Procesando…») y el resultado llega como otro mensaje |
| Las pruebas mandan mensajes de verdad | 3 | La salida pasa por `integraciones.pedir`, que las pruebas cortan |
| El identificador del chat es un dato personal | C, D | Se borra al desvincular y en la baja de la cuenta |

---

## 6. Fuera de alcance

- Telegram para el Cliente y para el Cajero.
- Leer la tapa con el modelo (necesita visión).
- Registrar llegadas, demoras o pagos desde el chat: se hacen en la web.

---

## 7. Lo que necesito del responsable

1. **Aprobar el plan**, o decir qué cambia.
2. **Las diez ambigüedades** del apartado 3.
3. **Los códigos** de los casos de uso A a G (o de los de la etapa 1, si la 2 queda para después).
4. **Crear el bot**: en Telegram, hablarle a **@BotFather**, `/newbot`, elegir el nombre y el usuario
   (termina en `bot`, por ejemplo `longbox_comiqueria_bot`). Te da un **token**: va en el `.env` de
   esta PC y en el de la VM como `TELEGRAM_BOT_TOKEN=…`. **No lo pegues en el chat**.
