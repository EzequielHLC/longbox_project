> **Tipo: Bitácora.** Registro de lo que se decidió construyendo este módulo. **Se anexa, no se
> reescribe.** Una entrada resuelta se marca; no se borra.

# Bitácora — `19` Perfil y avisos

> Este archivo es el material que el responsable lee para decidir qué se enmienda en el documento
> de análisis. Escribí para alguien que conoce el dominio y no tiene el código a la vista.

El formato de cada entrada está en [`_PLANTILLA.md`](_PLANTILLA.md). El plan es
[`docs/planes/00-bot-de-telegram.md`](../docs/planes/00-bot-de-telegram.md).

---

## Entradas

### B-19-001 · Un módulo nuevo, `19` Perfil y avisos, con sus códigos

**Tipo:** Agregado · **Fecha:** 2026-10-27 · **Alcance:** el documento entero (alcance, requerimientos, casos de uso, modelo de dominio)
**Estado:** Abierta — decidida por el responsable el 2026-10-27

**Qué apareció.**
El responsable pidió una página de perfil para el Administrador y un bot de Telegram para recibir
los avisos del sistema y resolver los correos de proveedores desde el teléfono. La especificación
no menciona Telegram ni un perfil del personal.

**Qué dice la especificación.**
`Nada`. No hay requerimiento, caso de uso ni contrato sobre canales de aviso ni sobre Telegram.

**Qué se hizo.**
Con el plan aprobado y **por autorización expresa del responsable**, que delegó la asignación de
los códigos en esta ocasión siguiendo el reglamento (`CU-MOD-AAA`, con dos letras del objeto más
A/B/M/C en los de alta, baja, modificación y consulta), se abrió el módulo **`19` Perfil y
avisos**, código **`AVI`**:

| Código | Caso de uso | Etapa |
| --- | --- | --- |
| `CU-AVI-PEC` | Consultar mi perfil (PErfil, Consulta), con la contraseña propia | 1 · construido |
| `CU-AVI-CAM` | Modificar los canales de aviso (CAnales, Modificación) | 1 · construido |
| `CU-AVI-TGA` | Vincular Telegram (TeleGram, Alta del vínculo) | 1 · construido |
| `CU-AVI-TGB` | Desvincular Telegram (TeleGram, Baja del vínculo) | 1 · construido |
| `CU-AVI-COR` | Resolver un correo de proveedor desde Telegram | 1 · construido |
| `CU-AVI-BOR` | Cargar un borrador desde Telegram | 2 · pendiente |
| `CU-AVI-CON` | Consultar desde Telegram | 2 · pendiente |

Se verificó antes que ningún código estuviera usado. Los contratos (`CO-NNN`) no se asignaron: los
numera el documento.

**Qué habría que cambiar.**
El documento gana el módulo 19, sus requerimientos (los canales de aviso del Administrador y el bot),
las fichas y contratos de los siete casos de uso y los conceptos de B-19-002 y B-19-003.

---

### B-19-002 · Los avisos al Administrador salen por los canales que eligió

**Tipo:** Agregado · **Fecha:** 2026-10-27 · **Alcance:** `CU-AVI-CAM`; los pasos que «notifican al Administrador» de `CO-011`, `CO-012`, `CO-015`, `CO-016`, `CO-067`, `CO-074`, `CU-PED-OPC`, `CU-DEV-SOL` y `CU-STK-DES`
**Estado:** Abierta — decisiones 3 y 4 del plan, aprobadas por el responsable el 2026-10-27

**Qué apareció.**
Cada aviso al Administrador salía por correo, a todos los Administradores activos, sin forma de
elegir. Con Telegram hace falta decidir por dónde sale cada uno, y qué pasa si el canal falla.

**Qué dice la especificación.**
> «el sistema notifica al Administrador» (en los pasos de cada caso de uso, sin decir por dónde)

**Qué se hizo.**
- **Seis tipos de aviso**, sacados de los lugares donde hoy se avisa: correos de proveedores,
  pre-ventas, pedidos de clientes, Restock, devoluciones y stock en local.
- Desde su perfil, cada Administrador elige por tipo **correo, Telegram, los dos o ninguno**.
- **Sin elegir, por correo, como antes.** Telegram sólo se puede marcar con el chat vinculado.
- **Si eligió Telegram y no se puede** (el bot no está configurado, desvinculó el chat, Telegram no
  contestó), **el aviso le llega por correo**, aunque haya apagado el correo: un aviso no se pierde
  por el canal.
- El aviso es el mismo por los dos canales (título, párrafos, la tabla y el enlace). El de correos
  nuevos de proveedores es distinto por Telegram: un mensaje por correo, con sus botones (B-19-004).

**Qué habría que cambiar.**
Cada paso que notifica al Administrador: «por los canales que eligió en su perfil, y por correo si
el elegido no responde». En el modelo de dominio, **PreferenciaAviso** (usuario, tipo de aviso,
por correo, por Telegram), única por usuario y tipo.

---

### B-19-003 · Vincular y desvincular Telegram, y el perfil del Administrador

**Tipo:** Agregado · **Fecha:** 2026-10-27 · **Alcance:** `CU-AVI-PEC`, `CU-AVI-TGA`, `CU-AVI-TGB`, `CO-111`, `CU-USR-MOD`
**Estado:** Abierta — decisiones 1, 2 y 7 del plan, aprobadas por el responsable el 2026-10-27

**Qué apareció.**
El personal no tenía una pantalla propia: ni sus datos, ni el cambio de su propia contraseña, que
hoy sólo tiene el Cliente (`CO-111`).

**Qué dice la especificación.**
`Nada` sobre un perfil del personal; `CO-111` es del Cliente desde «Mi cuenta».

**Qué se hizo.**
- **Mi perfil** (sólo el Administrador, decisión 1), desde su correo en el encabezado y desde el
  menú: sus datos, que se corrigen por `CU-USR-MOD` como hasta ahora (decisión 2); **el cambio de su
  contraseña**, con la misma regla que `CO-111` (con la actual, cierra las demás sesiones, auditado);
  sus avisos; y Telegram.
- **Vincular**: el perfil da un enlace `t.me/<bot>?start=<código>`, de un solo uso, que **vence a los
  15 minutos**; pedir otro anula el anterior. Al abrirlo en el teléfono, el bot vincula el chat y lo
  confirma. Un chat es de una sola cuenta y una cuenta tiene un solo chat. Queda auditado.
- **Desvincular**: desde el perfil o con `/salir` en el chat. Se borra el chat (es un dato personal) y
  los avisos vuelven al correo. Queda auditado.
- El bot recibe por **webhook** en la VM y, en la PC de desarrollo, con `manage.py telegram escuchar`
  (decisión 7). El webhook exige el secreto que manda Telegram en cada llamada.
- **El token del bot nunca queda escrito**: vive en el `.env`, y la puerta HTTP lo tapa en el log
  (viaja en la dirección de la API).

**Qué habría que cambiar.**
Las fichas de `CU-AVI-PEC`, `CU-AVI-TGA` y `CU-AVI-TGB`. `CO-111`: también para el personal, desde
«Mi perfil». En el modelo de dominio, **VinculoTelegram** (usuario, chat, nombre en Telegram, desde
cuándo) y **CodigoVinculacion** (usuario, código, vence, usado). La baja de una cuenta de personal
(`CU-USR-BAJ`) deja el chat sin efecto: la autorización exige un Administrador activo.

---

### B-19-004 · Un correo de proveedor se aprueba o se descarta desde Telegram

**Tipo:** Agregado · **Fecha:** 2026-10-27 · **Alcance:** `CU-AVI-COR`, `CU-PRV-COL`, `CO-016`, `CO-017`, `CO-018`
**Estado:** Abierta — decisiones 5 y 6 del plan, aprobadas por el responsable el 2026-10-27

**Qué apareció.**
El pedido central del responsable: enterarse en el teléfono de que llegó un correo de un proveedor
y decidir ahí mismo si se procesa.

**Qué dice la especificación.**
> «El Administrador accede a la cola de correos…» (`CU-PRV-COL`): la decisión se toma en la web.

**Qué se hizo.**
- Por Telegram, **cada correo nuevo llega como un mensaje propio**: proveedor, asunto, remitente, las
  primeras líneas del contenido y el enlace a su ficha. **Sin el modelo de lenguaje** (decisión 6):
  el modelo sigue leyendo el correo recién cuando se aprueba (`CU-PRV-COL`).
- **«Aprobar y procesar»** es `CO-017` con el Administrador del chat como actor. Se contesta enseguida
  («Procesando…») y el resultado llega en otro mensaje: borradores generados, el aviso de demora,
  o la falla, con el enlace a revisar. Si otro Administrador ya lo resolvió, lo dice (`CO-017` E1).
- **«Descartar»** es `CO-018`: ofrece motivos frecuentes («No es de novedades», «Repetido»,
  «Promoción o publicidad», «Factura o resumen de cuenta») y «Otro motivo…», que pide escribirlo
  respondiendo al mensaje (decisión 5). El motivo sigue siendo obligatorio, y queda auditado como
  desde la web, con «(desde Telegram)».
- **La autorización se mira en cada acción**: el chat tiene que estar vinculado a un Administrador
  activo en ese momento. Cada botón lleva una firma con la acción, el correo y el chat, así que no se
  puede armar uno a mano ni usar el de otro chat.

**Qué habría que cambiar.**
La ficha de `CU-AVI-COR`. `CU-PRV-COL`: la aprobación y el descarte también desde Telegram, con las
mismas operaciones. `CO-016`: el aviso del correo nuevo por el canal elegido.

---

### B-19-005 · Vincular Telegram pide confirmar un número en el perfil

**Tipo:** Agregado · **Fecha:** 2026-10-27 · **Alcance:** `CU-AVI-TGA`
**Estado:** Abierta — pedido del responsable el 2026-10-27

**Qué apareció.**
Con el enlace solo, quien lo abre primero queda vinculado. Si se filtra (una captura, un mensaje
reenviado) en sus 15 minutos, otra persona recibe los avisos y resuelve correos con la cuenta del
Administrador.

**Qué dice la especificación.**
`Nada`. B-19-003 describe la vinculación de un solo paso.

**Qué se hizo.**
- Abrir el enlace **ya no vincula**. El bot anota el chat que lo pidió y le muestra un **número de seis
  cifras**, al azar.
- El Administrador escribe ese número en **Mi perfil**, con su sesión abierta. Recién ahí queda
  vinculado, y el bot lo confirma en el chat. Así quien tenga el enlace no alcanza: le falta la sesión.
- Se aceptan **cinco intentos**. Al quinto número equivocado el enlace se anula y hay que pedir otro.
  «No fui yo» anula el pedido desde el perfil. Abrir el enlace de nuevo cambia el número.
- El código del enlace sigue siendo de un solo uso y venciendo a los 15 minutos. Lo que se audita es
  la confirmación, que es cuando se vincula de verdad.

**Qué habría que cambiar.**
La ficha de `CU-AVI-TGA`: el flujo es enlace → número en el chat → confirmación en el perfil, con la
excepción de los intentos agotados. En el modelo de dominio, **CodigoVinculacion** gana el chat
pendiente, el número de confirmación y los intentos.

---

### B-19-006 · Un borrador se puede cargar desde Telegram, con origen propio

**Tipo:** Agregado · **Fecha:** 2026-10-27 · **Alcance:** `CU-AVI-BOR`, `CU-ALT-REV`, `CO-022`
**Estado:** Abierta — decisiones 8 y 9 del plan, aprobadas por el responsable el 2026-10-27

**Qué apareció.**
El responsable pidió cargar productos desde el teléfono, en el local o en una feria, sin sentarse a la
computadora, y terminarlos después en la web.

**Qué dice la especificación.**
> «Por cada producto identificado en el correo, el sistema crea un borrador…» (`CU-ALT-NOV`). El
> borrador siempre nace de un correo de proveedor.

**Qué se hizo.**
- `/cargar` con un texto («Berserk Deluxe 5, Ivrea, B6, 24900»), o **una foto de la tapa con ese texto
  como epígrafe**. El modelo de lenguaje lee el texto como lee una novedad, y pasa por la misma
  validación: ISBN con dígito verificador, precio, fecha, tomo pegado al título.
- **La foto es la portada; los datos salen del texto** (decisión 9). Leer la tapa necesita un modelo
  con visión, que el modelo local no tiene.
- Sale **un borrador, nunca un producto** (regla 4). Va a la misma revisión (`CU-ALT-REV`), con los
  mismos controles, el mismo precio de la tabla y los mismos datos de la serie que un borrador de
  correo (B-01-019, B-01-020). La editorial se reconoce por su nombre entre las activas; si no está
  cargada, queda para elegir, con un reparo que lo dice.
- **El borrador gana un origen**: «Correo» o «Telegram», y quién lo cargó. El correo y el proveedor
  pasan a ser opcionales. El proveedor es el de la editorial, si tiene uno.
- El chat contesta con el borrador, lo que falta mirar, un aviso si ya existe un producto con esa
  identidad, y el enlace para revisarlo. Queda auditado como una generación de borradores, con el
  Administrador como actor.
- La foto se baja por la única puerta HTTP, con un tope de tamaño, y las pruebas la cortan igual que
  el resto de la red.

**Qué habría que cambiar.**
La ficha de `CU-AVI-BOR`. `CU-ALT-REV`: la cola mezcla borradores de correo y de Telegram, y muestra el
origen. El contrato de la generación de borradores: un borrador puede nacer sin correo. En el modelo de
dominio, **BorradorProducto** gana origen y quién lo cargó, y su asociación con el correo y con el
proveedor pasa a 0..1.

---

### B-19-007 · El bot responde comandos y preguntas con consultas fijas

**Tipo:** Agregado · **Fecha:** 2026-10-27 · **Alcance:** `CU-AVI-CON`
**Estado:** Abierta — decisión 10 del plan y pedido del responsable el 2026-10-27

**Qué apareció.**
Desde el teléfono, el Administrador quiere saber cosas rápidas: cuántos quedan de un tomo, qué llega
esta semana, qué espera una decisión, cuánto se cobró hoy. También pidió comandos con `/` y una ayuda.

**Qué dice la especificación.**
`Nada`.

**Qué se hizo.**
- Comandos, registrados en Telegram para que aparezcan en el menú del chat: `/stock` (título con su
  tomo, código o ISBN), `/llega` (pre-ventas y pedidos a proveedores de los próximos siete días y lo
  atrasado), `/pendientes` (correos sin decidir, borradores, pedidos por armar, la propuesta de
  restock), `/caja` (lo cobrado sin cerrar), `/cargar`, `/salir` y `/ayuda` (también `/help`).
- **Una pregunta con palabras** («¿cuántos Chainsaw Man 12 hay?») la lee el modelo de lenguaje, que
  **sólo elige** una de esas consultas y su argumento. El sistema consulta y responde: el modelo no ve
  la base. Si elige algo fuera de la lista, o no contesta, el bot lo dice y sugiere los comandos.
- **Las consultas sólo leen.** Lo que cambia algo se hace en la web, salvo aprobar o descartar un
  correo (B-19-004) y cargar un borrador (B-19-006).
- Todo exige un chat vinculado a un Administrador activo en ese momento. Un chat sin vínculo sólo
  recibe la ayuda y el pedido de vincularse.

**Qué habría que cambiar.**
La ficha de `CU-AVI-CON`: la lista de consultas, que son de sólo lectura, y que la pregunta libre se
traduce a una de ellas.

---

### Nota de cierre · 2026-10-27

Los siete casos de uso del módulo están construidos y probados (103 pruebas en `apps/avisos/tests/`),
con las siete puertas en verde. Ninguno tiene contrato todavía: esperan sus fichas y sus `CO-NNN` en
el documento (B-19-001). Falta probar la etapa 2 desde el chat real, y en la VM subir el sistema,
instalar `longbox-casilla.timer` y volver a correr `telegram webhook`.

---

### B-19-008 · Los borradores se ven y se rechazan desde Telegram, pero no se confirman

**Tipo:** Agregado · **Fecha:** 2026-10-28 · **Alcance:** `CU-AVI-REB`, `CU-ALT-REV`
**Estado:** Abierta — pedido del responsable el 2026-10-28; el código `CU-AVI-REB` se asignó con la
autorización de B-19-001

**Qué apareció.**
El responsable pidió poder **rechazar** borradores desde el teléfono, con una vista previa simple del
borrador, y **nunca aprobarlos** desde ahí.

**Qué dice la especificación.**
> El rechazo de un borrador exige un motivo (`CU-ALT-REV`).

Sobre hacerlo fuera de la pantalla de revisión, `Nada`.

**Qué se hizo.**
- `/borradores`, con un título opcional, muestra los abiertos, los más nuevos primero, de a cinco. Cada
  uno llega como una **vista previa**: la portada en chico, con la ficha corta como epígrafe (título y
  tomo, editorial, tipo y formato, precio, estado con el que nacería, de dónde vino, los parecidos y los
  reparos) y el enlace a la revisión. Sin portada, la ficha sola.
- El único botón es **«Rechazar…»**: ofrece motivos frecuentes («Ya está en el catálogo», «No lo vamos a
  traer», «Los datos están mal», «Lo cargué por error») y «Otro motivo…», que se escribe respondiendo.
  Es el mismo rechazo de la web: motivo obligatorio y la misma auditoría, con «(desde Telegram)».
- **No hay forma de confirmar desde el chat**: ningún botón la ofrece, y un botón firmado con otra
  acción no hace nada. El producto nace en la web, con la revisión entera a la vista (regla 4).
- La vista previa también es la respuesta a `/cargar`, así que un borrador cargado por error se
  rechaza en el acto.
- Como en la web, rechazar deja abierta la sesión de revisión del Administrador. Los pedidos a
  proveedores salen al cerrarla, desde la web.

**Qué habría que cambiar.**
La ficha de `CU-AVI-REB`. `CU-ALT-REV`: el rechazo también desde Telegram, con la misma operación.

---

### B-19-009 · Lo que no es material editorial no se carga como borrador

**Tipo:** Agregado · **Fecha:** 2026-10-28 · **Alcance:** `CU-AVI-BOR`
**Estado:** En discusión — **espera la decisión del responsable** sobre los borradores no editoriales

**Qué apareció.**
El responsable cargó desde Telegram «Figura Nendoroid de Kaneki». Quedó como un borrador **editorial**,
sin editorial ni formato. Confirmarlo habría creado un tomo que es una figura.

**Qué dice la especificación.**
> «Por cada producto identificado en el correo, el sistema crea un borrador…» (`CU-ALT-NOV`), y la
> confirmación crea un producto editorial (`CU-ALT-REV`).

El borrador es, por construcción, de material editorial: tiene volumen, ISBN, formato y precio de
tabla, y no tiene marca.

**Qué se hizo.**
- El modelo de lenguaje dice ahora también el **rubro** y el **tipo** del producto. Si el rubro es no
  editorial, o el tipo nombrado es de ese rubro (figura, TCG, merchandising, insumo), **no se crea nada**.
  El bot lo explica y enlaza el alta no editorial de la web (`CU-CAT-ALT`).
- Cargar material no editorial **como borrador** necesitaría que el borrador tenga rubro, marca y sin
  pre-venta, y que la confirmación cree un producto no editorial. Eso cambia el alcance de
  `CU-ALT-REV` y de su contrato, y se consulta antes.

**Qué habría que cambiar.**
La ficha de `CU-AVI-BOR`: la excepción del material no editorial. Lo demás depende de la decisión.

---

### B-19-010 · La carga desde el chat avisa los parecidos y deduce la editorial de la serie

**Tipo:** Agregado · **Fecha:** 2026-10-28 · **Alcance:** `CU-AVI-BOR`, `CU-AVI-REB`
**Estado:** Abierta — pedido del responsable el 2026-10-28

**Qué apareció.**
- El aviso de duplicado del chat sólo miraba la tupla completa: con el formato sin resolver no avisaba
  nada, ni siquiera con el mismo ISBN.
- No veía otro borrador abierto del mismo tomo, que es el caso de un tomo que llega por correo y además
  lo cargan por el chat.
- «Agencia del Amor 5, nacional» quedó sin editorial: el modelo tomó «Nacional» por editorial, y la serie
  ya existía en Ivrea.

**Qué dice la especificación.**
> «…ISBN idéntico, o combinación título+volumen+tipo+formato+editorial idéntica con el título
> normalizado…» (el criterio de duplicado de los contratos de alta del módulo 01).

Sobre parecidos que no son duplicados, y sobre deducir la editorial, `Nada`.

**Qué se hizo.**
- La ficha del borrador en el chat distingue tres cosas:
  - **«Ya está en el catálogo»**: el duplicado de verdad, por ISBN o por la tupla, el que la
    confirmación rechazaría.
  - **«Parecido en el catálogo»**: el mismo título y tomo en otra editorial, tipo o formato,
    comparado sin mayúsculas ni tildes.
  - **«Otro borrador abierto»**: el mismo título y tomo, o el mismo ISBN.
- **Ninguno bloquea**: informan. La confirmación sigue rechazando sólo el duplicado de verdad.
- Si el mensaje no nombra una editorial cargada y **la serie existe en una sola editorial**, se toma
  esa. Si había nombrado otra, queda un reparo que lo dice. Si la serie está en dos editoriales, no se
  elige.
- El tipo nombrado en el mensaje se usa antes que el del proveedor. Al modelo se le aclara que
  «nacional» e «importado» son el origen y no una editorial.

**Qué habría que cambiar.**
La ficha de `CU-AVI-BOR`: los tres avisos, y la editorial deducida de la serie, con su reparo.

---

### B-19-011 · Avisos de venta, resumen de la mañana y un reloj por minuto

**Tipo:** Agregado · **Fecha:** 2026-10-28 · **Alcance:** `CU-AVI-CAM`, `CU-AVI-RES`, `CU-CFG-PAR`, `CO-016`, `CO-130`
**Estado:** Abierta — [plan de la etapa 3](../docs/planes/00-bot-de-telegram-etapa-3.md), aprobado
por el responsable el 2026-10-28 con las decisiones recomendadas. `CU-AVI-RES` se asignó con la
autorización de B-19-001

**Qué apareció.**
El responsable aprobó, para el bot, un resumen cada mañana y un aviso en el momento por cada venta.

**Qué dice la especificación.**
`Nada`. Los avisos al Administrador son siempre por correo (B-19-002 los hizo elegibles por canal).

**Qué se hizo.**
- **Cuatro tipos de aviso nuevos**: «Ventas online», «Resumen de la mañana», «Seguridad» y «Estado del
  sistema». Cada tipo tiene un **canal por defecto**, el que rige mientras el Administrador no eligió
  nada. Los de antes siguen por correo (decisión 3 del plan anterior).
  - **Ventas, resumen y estado del sistema van sólo por Telegram**. Sin chat vinculado no se mandan,
    y si Telegram falla no caen al correo: serían decenas por día. Se los llama **opcionales**.
  - **Seguridad va por los dos canales**.
  - Los demás siguen cayendo al correo si Telegram falla.
  - En el perfil, marcar Telegram en un aviso opcional sin chat lo deja sin canal, en vez de
    pasarlo al correo.
- **Aviso de venta**:
  - Sale por cada pago online aprobado, con las líneas, el total, el cliente, la modalidad y las
    reservas de pre-venta marcadas.
  - Sale otro aparte si la venta **agotó el cupo** de una pre-venta.
  - **Sólo las online**: la venta de mostrador la hace alguien que está en el local.
  - Se manda después de confirmar el pago y en segundo plano: un aviso caído no deshace la venta.
- **Resumen de la mañana** (`CU-AVI-RES`), a la hora de Parámetros (09:00 por defecto). Trae:
  - lo que espera una decisión: correos, borradores, pedidos por armar y restock;
  - las pre-ventas que llegan hoy y las atrasadas, y los pedidos a proveedores atrasados;
  - las ventas online y la caja de ayer.

  **Sale siempre**, aunque esté todo en cero: confirma que el bot anda. El día se marca con bloqueo
  de fila antes de mandar, así que dos relojes a la vez lo mandan una sola vez.
- **El reloj por minuto** reemplaza a la vigilancia de la casilla (B-04-015). Cada minuto corre la
  casilla si le toca, el resumen si es la hora y los controles de salud (B-19-013).
  - En la VM corre como `longbox-reloj.timer` (`manage.py cada_minuto`).
  - En esta PC corre dentro de `telegram escuchar`.
  - Una tarea que falla no frena a las demás.
- `ConfiguracionSistema` gana la hora del resumen, el último día enviado y los problemas de salud
  avisados.

**Qué habría que cambiar.**
- La ficha de `CU-AVI-RES`.
- `CU-AVI-CAM`: los tipos de aviso con su canal por defecto y los opcionales.
- `CU-CFG-PAR` y `CO-130`: la hora del resumen.
- P-05: el reloj por minuto, al lado del Temporizador diario.
- En el modelo de dominio, los atributos nuevos de `ConfiguracionSistema`.

---

### B-19-012 · Las alertas de seguridad salen del registro de auditoría

**Tipo:** Agregado · **Fecha:** 2026-10-28 · **Alcance:** `CU-AUT-INI`, `CU-USR-ALT`, `CU-USR-MOD`, `CO-048`, `CO-053`
**Estado:** Abierta — plan de la etapa 3, ambigüedades 7 y 8, aprobadas el 2026-10-28

**Qué apareció.**
El responsable pidió enterarse en el momento de lo que puede ser un ataque o un error grave.

**Qué dice la especificación.**
> «…el sistema bloquea el acceso por un período parametrizable (CU-CFG-PAR) y envía al correo
> registrado un aviso de bloqueo temporal.» (`CU-AUT-INI` E1)

Sobre avisarle al Administrador, `Nada`.

**Qué se hizo.**
Se escucha **lo que ya se audita**, no cada pantalla: así una operación que entre por otra puerta
también alerta. Avisan:
- el **bloqueo por intentos** de una cuenta que existe;
- el **ingreso del personal desde una IP** que esa cuenta no usó en los últimos 90 días. El primer
  ingreso de una cuenta no cuenta, y el Cliente tampoco;
- el **alta de un Administrador** y los **cambios de rol** que entran o salen de Administrador;
- las **propagaciones de precios** que alcanzan productos: el margen global (`CO-053`) y una fila de
  la tabla (`CO-048`).

Cada alerta dice qué pasó, quién, cuándo y desde qué IP, con el enlace a la auditoría. Sale después
de confirmar la transacción, y leer el registro no lo modifica.

**Qué habría que cambiar.**
`CU-AUT-INI`, `CU-USR-ALT`, `CU-USR-MOD`, `CO-048` y `CO-053`: el aviso de seguridad al Administrador,
por los canales que eligió.

---

### B-19-013 · `/estado`, los controles de salud y el respaldo diario de la VM

**Tipo:** Agregado · **Fecha:** 2026-10-28 · **Alcance:** `CU-AVI-EST`
**Estado:** Abierta — plan de la etapa 3, aprobado el 2026-10-28. `CU-AVI-EST` se asignó con la
autorización de B-19-001

**Qué apareció.**
El responsable pidió poder preguntarle al bot cómo anda el sistema y que avise si algo falla. Al
buscar qué mirar apareció que **la VM no se respaldaba sola**: el único respaldo era el de la base
local, al subir.

**Qué dice la especificación.**
`Nada` sobre el estado del sistema. `RESPALDOS.md` pide un respaldo diario, y en la VM no estaba.

**Qué se hizo.**
- `/estado`: el disco usado y libre, la memoria disponible (en Linux), el tamaño de la base, el
  último respaldo (cuándo y cuánto pesa) y cuándo se revisó la casilla. **Sólo lee.**
- Desde el reloj por minuto, un aviso «Estado del sistema» si el disco pasa el 85 % o si falta el
  respaldo de las últimas 26 horas. **Uno por día y por problema** mientras siga; si se arregla y
  vuelve, se avisa de nuevo.
- En la VM, `longbox-respaldo.timer` corre `respaldar_base` todos los días a las 03:30 y conserva los
  últimos siete. El respaldo sólo se vigila donde hay uno programado (`VIGILAR_RESPALDO`, que el
  instalador agrega al `.env` de la VM): en esta PC avisaría todos los días.

**Qué habría que cambiar.**
La ficha de `CU-AVI-EST`. `RESPALDOS.md`: la rutina de la VM.

---

### B-19-014 · El reclamo de devolución llega al chat con sus fotos

**Tipo:** Agregado · **Fecha:** 2026-10-28 · **Alcance:** `CU-DEV-SOL`, `CU-AVI-CAM`
**Estado:** Abierta — plan de la etapa 3, ambigüedad 6, aprobada el 2026-10-28

**Qué apareció.**
El responsable pidió ver las fotos del reclamo en el teléfono, con el enlace para resolverlo.

**Qué dice la especificación.**
> «El sistema crea el caso con estado Pendiente y notifica al Administrador de la existencia del
> nuevo caso.» (`CU-DEV-SOL` paso 5)

Las fotos se guardan fuera de lo público (`privado/`), porque son evidencia del Cliente.

**Qué se hizo.**
- Por Telegram, el aviso del reclamo va seguido de **sus fotos, achicadas a 800 px**, en un solo
  envío.
- Por correo van sin fotos, como antes.
- **Sin botones**: resolver un caso mueve dinero o stock y se hace en la web.
- **Mandarlas copia un dato personal del Cliente a los servidores de Telegram.** El responsable lo
  aprobó así, sólo hacia los Administradores vinculados.

**Qué habría que cambiar.**
`CU-DEV-SOL` paso 5: las fotos en el aviso por Telegram. La sección de datos personales del
documento: las evidencias que salen por Telegram.

---

### B-19-015 · Compartir un producto desde cualquier chat (modo inline)

**Tipo:** Agregado · **Fecha:** 2026-10-28 · **Alcance:** `CU-AVI-INL`
**Estado:** Abierta — plan de la etapa 3, ambigüedades 4 y 5, aprobadas el 2026-10-28.
`CU-AVI-INL` se asignó con la autorización de B-19-001

**Qué apareció.**
El responsable atiende clientes por Telegram y quería compartirles un producto sin salir del chat.

**Qué dice la especificación.**
`Nada`.

**Qué se hizo.**
- En cualquier chat se escribe `@longbox_comiqueria_bot berserk` y aparece una lista con los
  productos que coinciden. Al elegir uno se comparte **la ficha de la tienda**:
  - título, editorial o marca, precio con la oferta del día y disponibilidad (disponible, en
    pre-venta con su llegada o agotado);
  - el enlace a la tienda.
- **El stock exacto sólo aparece en la lista**, que ve únicamente quien busca. El mensaje compartido
  no lo lleva.
- Se muestra sólo lo que la tienda muestra: nada descatalogado ni sólo para adultos.
- **Contesta sólo a Administradores vinculados y activos.** Telegram informa quién pregunta; a
  cualquier otro se le contesta vacío. La respuesta es personal y vive diez segundos.
- Hace falta habilitarlo una vez en @BotFather (`/setinline`).

**Qué habría que cambiar.**
La ficha de `CU-AVI-INL`.

---

### B-19-016 · `/refresh` revisa la casilla desde el chat, y revisar a mano reinicia el reloj

**Tipo:** Agregado · **Fecha:** 2026-10-28 · **Alcance:** `CO-016`, `CU-PRV-COL`, `CU-AVI-COR`
**Estado:** Abierta — pedido del responsable el 2026-10-28

**Qué apareció.**
El responsable pidió revisar la casilla en el momento desde Telegram, además del botón de la cola, y
que cualquiera de los dos reiniciara la lectura automática. El botón (B-04-013) no se veía en la VM
porque la cola lo muestra sólo con una casilla configurada, y la VM no la tenía.

**Qué dice la especificación.**
> «Revisar la casilla ahora» ejecuta `CO-016` desde la cola (B-04-013, ya registrado).

Sobre el chat y sobre el reloj, `Nada`.

**Qué se hizo.**
- `/refresh` en el bot hace lo mismo que el botón de la cola: trae lo nuevo, **no procesa nada** y
  contesta cuántos correos llegaron. Si ese Administrador recibe los correos por Telegram, ya los
  tiene arriba, cada uno con sus botones; si no, el resumen los lista con el enlace a la cola. Sólo
  para un chat vinculado a un Administrador activo.
- **Los dos reinician el reloj**: la frecuencia de Parámetros cuenta desde la última revisión, sea
  automática o a pedido. La cola dice ahora cuándo se revisó y a qué hora toca la próxima
  automática; `/refresh` también lo dice. Si la casilla no contesta, la hora no se mueve.

**Qué habría que cambiar.**
`CO-016`: también desde el chat, y la frecuencia cuenta desde la última revisión, sea cual sea.
