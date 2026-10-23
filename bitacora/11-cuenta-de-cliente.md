# Bitácora — `11` Cuenta de Cliente

> Registro de lo que se decidió construyendo este módulo. **Se anexa, no se reescribe.**
> Una entrada resuelta se marca; no se borra.
>
> Este archivo es el material que el responsable lee para decidir qué se enmienda en el documento
> de análisis. Escribí para alguien que conoce el dominio y no tiene el código a la vista.

---

## Entradas

### B-11-001 · La consulta de cuentas de Cliente se construyó declarándose fuera de todo caso de uso

**Tipo:** Agregado · **Fecha:** 2026-09-14 · **Alcance:** `CU-CLI-CON`, `CU-CLI-BAJ`, `CO-194`, `CO-195`
**Estado:** Resuelta — comentario vencido; corregido el código el 2026-09-22

**Qué apareció.**
`ClienteListaView` lleva escrito en su docstring que no es un caso de uso, que es la contraparte de
lectura del registro público, y que dar de baja una cuenta de Cliente «es el `CU-CLI-BAJ`, que
todavía no está documentado». Las dos afirmaciones son falsas contra el esquema vigente:

- `CU-CLI-CON` · Consultar Cuentas de Cliente existe, con `CO-194 consultarCuentasDeCliente` y
  `CO-195 consultarFichaDeCliente`.
- `CU-CLI-BAJ` · Dar de Baja Cuenta existe, con ficha completa —mapeo de impacto sobre pedidos
  activos, stock almacenado y saldo de puntos, confirmación con contraseña, invalidación de
  sesiones— y con `CO-112` y `CO-113`.

La segunda afirmación es además la que más engaña: quien la lea va a creer que la baja de cuenta
está sin especificar y la va a resolver por su cuenta, cuando la ficha ya declara reglas que no se
adivinan.

**Qué dice la especificación.**
> `CU-CLI-BAJ` — «El sistema mapea el impacto sobre pedidos activos, stock almacenado y saldo de
> puntos, e informa al Cliente de las implicaciones antes de solicitar confirmación explícita con
> contraseña. Si existen condiciones bloqueantes no resueltas, el sistema las indica y no permite
> continuar hasta su resolución.»

**Qué se hizo.**
Nada sobre el comportamiento. La pantalla sigue siendo de sólo lectura, que es lo que corresponde:
la baja la pide el Cliente desde su panel, no el Administrador desde el listado, y el panel del
Cliente todavía no existe.

**Qué habría que cambiar.**
En el documento, nada. Hay que sacar del código la afirmación de que la baja no está documentada
—es la que puede inducir a implementarla mal— y verificar el listado contra `CO-194`. Queda
pendiente decidir si la ficha de cliente de `CO-195` se construye ahora o junto con el resto del
módulo: hoy no existe.

---

## Resoluciones

> Lo que el responsable decidió sobre cada entrada, con la fecha y con qué se hizo en
> consecuencia. **La entrada original no se toca**: sólo se le marca el estado. Una enmienda
> declarada «pendiente» manda sobre el texto que hoy está volcado en `.contexto-ia/`, que no se
> edita a mano y se actualiza recién cuando el documento de análisis cambie.

### R-11-001 · Resolución de B-11-001

**Fecha:** 2026-09-22 · **Enmienda al documento:** ninguna

**Qué se decidió.**
Como en `B-02-001` y `B-04-002`: **`CU-CLI-CON` y `CU-CLI-BAJ` se incorporaron al documento el
05/09**, después de que la pantalla existiera. Las dos afirmaciones del docstring fueron ciertas
cuando se escribieron.

La segunda —que la baja de cuenta «todavía no está documentada»— es la que había que sacar con
urgencia, porque induce a implementarla por las propias reglas en vez de por la ficha, que ya
declara el mapeo de impacto y la confirmación con contraseña.

**Qué se hizo.**
`ClienteListaView`: la referencia pasa a `CU-CLI-CON`, con `CO-194` y `CO-195`, y la nota sobre la
baja dice ahora lo que la ficha declara —la pide el Cliente desde su panel, que no existe— en vez
de decir que no está documentada. Queda dicho también que `CO-195` no está construido: hoy la
pantalla cubre el listado de `CO-194` y nada más.

---

### B-11-002 · El cambio de correo tiene su propio token: `TokenCambioCorreo`

**Tipo:** Agregado · **Fecha:** 2026-10-09 · **Alcance:** `CO-109`, `CO-110`, Área 1 del modelo
**Estado:** Abierta — decidida por el responsable el 2026-10-09 (plan 11, segunda parte, amb. 1)

**Qué apareció.**
El contrato pide un token para verificar el correo nuevo y aclara que no es el de recuperación. El
modelo no lo declara, y nadie dice cuánto dura.

**Qué dice la especificación.**
> «(a) Se creó un token de verificación de correo. El modelo de dominio declara TokenRecuperacion
> para la recuperación de contraseña; este token de verificación de correo es un concepto
> distinto.» (`CO-109`, postcondiciones)

**Qué se hizo.**
`TokenCambioCorreo` es hermano de `EnlaceActivacion` y `TokenRecuperacion`: se emite para una
cuenta, viaja por correo, se usa una sola vez y vence solo; además guarda el correo nuevo. Dura
**24 horas**. Pedir otro cambio deja vencido el anterior.

**Qué habría que cambiar.**
Modelo de dominio, Área 1: sumar `TokenCambioCorreo` (correo nuevo, emitido en, vence en, estado)
como `<<construido>>`, asociado a `Usuario`, con su vigencia de 24 horas.

---

### B-11-003 · El panel del Cliente no muestra la sección Stock en Local

**Tipo:** Agregado · **Fecha:** 2026-10-09 · **Alcance:** `CU-CLI-HIS` paso 7, `CO-192`
**Estado:** Resuelta — la sección se muestra desde el 2026-10-14, con el módulo 18 (plan 18)

**Qué apareció.**
El panel tiene cuatro secciones y una es el stock almacenado en el local, que no existe.

**Qué dice la especificación.**
> «El sistema presenta el panel con cuatro secciones navegables: (1) Pedidos Activos, (2)
> Historial de Pedidos, (3) Puntos, (4) Stock en Local.» (`CU-CLI-HIS`, paso 2)

**Qué se hizo.**
La sección queda oculta, por decisión del responsable: mostrarla vacía le diría al Cliente que no
tiene nada guardado, y el sistema todavía no lo puede saber. `CU-CLI-HIS` queda `Parcial`.

**Qué habría que cambiar.**
`Nada`. Se resuelve construyendo el módulo 18.

---

### B-11-004 · Pedidos activos e historial, y el panel suma «Mis datos»

**Tipo:** Agregado · **Fecha:** 2026-10-09 · **Alcance:** `CU-CLI-HIS` pasos 3 y 5, `CU-CLI-DAT` paso 1
**Estado:** Abierta — decidida por el responsable el 2026-10-09 (plan 11, segunda parte, amb. 3)

**Qué apareció.**
El historial lista «los pedidos completados y cancelados», y en DME-07 un pedido termina en
Despachado: no hay un pedido cancelado entero.

**Qué dice la especificación.**
> «En la sección Historial de Pedidos: el sistema lista los pedidos completados y cancelados.»
> (`CU-CLI-HIS`, paso 5)

**Qué se hizo.**
- Activos son todos los que todavía no se despacharon; el historial, los Despachados.
- El panel suma una quinta pestaña, «Mis datos», que es la puerta de `CU-CLI-DAT` («desde su
  panel de cuenta»).

**Qué habría que cambiar.**
`CU-CLI-HIS` paso 5: «los pedidos despachados». Paso 2: sumar el acceso a «Mis datos».

---

### B-11-005 · Cuando el correo cambia, el anterior recibe un aviso

**Tipo:** Agregado · **Fecha:** 2026-10-09 · **Alcance:** `CO-110`
**Estado:** Abierta — decidida por el responsable el 2026-10-09 (plan 11, segunda parte, amb. 4)

**Qué apareció.**
Si alguien con la sesión de otro cambia su correo, el titular pierde la cuenta sin enterarse.

**Qué dice la especificación.**
`Nada`. `CO-110` cambia el correo y lo audita.

**Qué se hizo.**
Al confirmarse el cambio, el correo anterior recibe un aviso con el correo nuevo enmascarado y la
indicación de escribir a la tienda si no fue el titular.

**Qué habría que cambiar.**
`CO-110`, postcondiciones: «se envió un aviso al correo anterior».

---

### B-11-006 · El pedido para retirar sigue en curso hasta que se retira

**Tipo:** Agregado · **Fecha:** 2026-10-21 · **Alcance:** `CU-CLI-HIS`, `CO-192`
**Estado:** Abierta — decidida por el responsable el 2026-10-21 (plan 00 de interfaz, amb. 1)

**Qué apareció.**
El estado «En el local» (plan 07, octava parte) no figuraba ni en los pedidos activos ni en el
historial: el Cliente dejaba de ver su pedido justo cuando estaba listo para buscarlo.

**Qué dice la especificación.**
`Nada` sobre este estado. B-11-004 fija activos («los que todavía no se despacharon») e historial
(«los Despachados»), antes de que existiera el retiro.

**Qué se hizo.**
Un pedido «En el local» figura entre los pedidos en curso mientras le quede algún artículo esperando
en el mostrador; cuando se retira todo, o vence lo que quedaba, pasa al historial.

**Qué habría que cambiar.**
`CU-CLI-HIS` pasos 3 y 5: sumar «En el local» con esa regla.

---

### B-11-007 · La baja de la cuenta deja un débito por cada lote, y su contador de intentos es propio

**Tipo:** Agregado · **Fecha:** 2026-10-22 · **Alcance:** `CU-CLI-BAJ`, `CO-112`, `CO-113`
**Estado:** Abierta — decidido en el plan 11, tercera parte (ambigüedades 1 a 3)

**Qué apareció.**
Al construir la baja: el contrato pone los lotes en cero sin movimiento, el historial de «Mi
cuenta» dejaría de explicar el saldo; la ficha nombra tres estados de pedido activo, y hoy hay
cinco; y el bloqueo tras tres intentos no dice con qué contador.

**Qué dice la especificación.**
> «El disponible de todos los LotePuntos del Cliente pasó a cero y su estado a Vencido» (`CO-113`) ·
> «Los pedidos activos en proceso (Pendiente de Armado / Armado / Empaquetado)» (`CU-CLI-BAJ`) ·
> «Tras tres intentos fallidos consecutivos, el sistema bloquea el flujo de baja» (E3)

**Qué se hizo.**
- Cada lote invalidado deja un débito «Baja de la cuenta» en el historial, como la caducidad.
- El informe y la entrada del log cuentan todos los pedidos del ciclo: también los que esperan una
  pre-venta o un artículo demorado ya decidido.
- Tres contraseñas equivocadas bloquean la baja por el período de Parámetros; el inicio de sesión
  tiene su propio contador y no se entera.

**Qué habría que cambiar.**
`CO-113`: agregar el débito por lote. `CU-CLI-BAJ` paso 2 (b): «los pedidos activos», sin
enumerarlos.

---

### B-11-008 · La cuenta de un Cliente dado de baja no tiene vuelta desde ninguna pantalla

**Tipo:** Corrección · **Fecha:** 2026-10-22 · **Alcance:** `CU-CLI-BAJ`, `CU-USR-REA`, `CU-USR-ELI`, `CO-124`
**Estado:** Resuelta el 2026-10-22 (B-11-009)

**Qué apareció.**
La baja ya funciona, y la cuenta queda Inactiva. Pero la reactivación y la eliminación del
Administrador sólo alcanzan cuentas de personal, y la reactivación pide elegir un rol.

**Qué dice la especificación.**
> «La cuenta no puede ser reactivada por el Cliente; solo el Administrador puede reactivarla desde
> CU-USR-REA o eliminarla desde CU-USR-ELI.» (`CU-CLI-BAJ`, postcondiciones) ·
> `confirmarReactivacionDeUsuario(usuario, rol)` (`CO-124`)

**Qué se hizo.**
Nada todavía, por decisión del plan: extender `CU-USR-REA` a clientes cambia lo que ese caso de uso
puede hacer, y su contrato no prevé un Cliente.

**Qué habría que cambiar.**
Una de dos: `CU-USR-REA` y `CU-USR-ELI` alcanzan también cuentas de Cliente (sin elegir rol), o
`CU-CLI-BAJ` deja de nombrarlos y la baja del Cliente pasa a ser definitiva.

---

### B-11-009 · El Administrador reactiva la cuenta de un Cliente; ninguna cuenta se elimina

**Tipo:** Corrección · **Fecha:** 2026-10-22 · **Alcance:** `CU-CLI-BAJ`, `CU-USR-REA`, `CU-USR-ELI`, `CO-124`
**Estado:** Abierta — consulta resuelta el 2026-10-23: `CU-USR-ELI` queda como única excepción (una cuenta de personal que nunca se activó); queda la enmienda

**Qué apareció.**
La consulta de B-11-008: la ficha de la baja del Cliente nombra la reactivación y la eliminación
por el Administrador, y esas pantallas sólo alcanzaban cuentas de personal.

**Qué dice la especificación.**
> «solo el Administrador puede reactivarla desde CU-USR-REA o eliminarla desde CU-USR-ELI.»
> (`CU-CLI-BAJ`, postcondiciones)

**Qué se hizo.**
Decisión del responsable: **el Administrador nunca elimina una cuenta**, sólo la da de baja o la
reactiva; los datos no se borran. La ficha de un Cliente dado de baja ofrece «Reactivar la
cuenta»: vuelve a Pendiente de activación y el Cliente recibe un enlace para elegir una contraseña
nueva, como el personal, sin elegir rol. Los puntos perdidos en la baja no vuelven. La
eliminación no se extiende a los clientes.

**Para consultar.** `CU-USR-ELI` hoy elimina una cuenta de personal que nunca se activó (por
ejemplo, cargada con un correo equivocado). Con la regla «ninguna cuenta se elimina», ¿se retira
ese caso de uso, o queda como la única excepción porque esa cuenta nunca llegó a tener datos?

**Qué habría que cambiar.**
`CU-CLI-BAJ`, postcondiciones: «solo el Administrador puede reactivarla desde CU-USR-REA», sin la
eliminación. `CO-124`: el rol no se elige cuando la cuenta es de Cliente.


---

### B-11-010 · El Administrador da de baja la cuenta de un Cliente, sin quitarle nada

**Tipo:** Agregado · **Fecha:** 2026-10-22 · **Alcance:** `CU-USR-BAJ`, `CO-123`, `CU-CLI-CON`
**Estado:** Abierta — pedido del responsable el 2026-10-22

**Qué apareció.**
Con la reactivación de clientes (B-11-009), el responsable pidió que el Administrador también
pueda dar de baja la cuenta de un Cliente: una baja lógica, nunca una eliminación.

**Qué dice la especificación.**
`CU-USR-BAJ` describe la baja de cuentas de personal. Ninguna ficha prevé que el Administrador dé
de baja a un Cliente: la única baja de un Cliente es la propia (`CU-CLI-BAJ`).

**Qué se hizo.**
La ficha del Cliente ofrece «Dar de baja». Es la baja del personal aplicada a un Cliente: la cuenta
queda Inactiva y se cierran sus sesiones. **No es la baja del propio Cliente**: no pierde puntos,
avisos ni carrito, porque una baja que decide otro tiene que poder revertirse sin pérdida. La
reactivación (B-11-009) la devuelve tal cual. Los pedidos en curso siguen su ciclo. La pantalla
de confirmación dice todo eso antes de confirmar.

**Qué habría que cambiar.**
`CU-USR-BAJ` y `CO-123`: alcanzar también cuentas de Cliente, con la aclaración de que no invalida
puntos. `CU-CLI-CON`: la ficha ofrece dar de baja y reactivar.
