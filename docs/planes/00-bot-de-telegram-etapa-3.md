> **Tipo: Normativo** una vez aprobado. Antes de la aprobación es una propuesta.
> Se escribe **antes** de programar y **no se reescribe** después: si algo cambió durante la
> construcción, eso va a la bitácora del módulo, no acá.

# Plan — `00` El bot de Telegram, etapa 3

**Estado del plan:** Aprobado el 2026-10-28, con las decisiones recomendadas · **Fecha:** 2026-10-28

Sigue al [plan de las etapas 1 y 2](00-bot-de-telegram.md). El responsable aprobó el 2026-10-28
seis ideas para el bot. La foto de un remito que se convierte en borradores y las notas de voz
quedan para después: dependen de llevar LM Studio a la VM por un túnel.

1. Un resumen cada mañana.
2. Avisos de venta en el momento.
3. Compartir un producto desde cualquier chat (modo inline).
4. Alertas de seguridad.
5. El estado del sistema, y un aviso si algo falla.
6. El reclamo de devolución con sus fotos.

Como las etapas anteriores, es un cambio de alcance del módulo 19. Los códigos de los casos de uso
nuevos los asigno con la autorización de B-19-001. Los contratos `CO-NNN` siguen siendo del
responsable.

---

## 1. Qué cubre

| # | Pedido | Caso de uso | Qué es |
| --- | --- | --- | --- |
| 1 | Resumen de la mañana | `CU-AVI-RES` (nuevo) | Un mensaje por día, a la hora de Parámetros, a cada Administrador que lo eligió |
| 2 | Avisos de venta | Un tipo de aviso nuevo, **«Ventas»**, en `CU-AVI-CAM` | Pago online aprobado (con sus reservas de pre-venta) y pre-venta que agotó su cupo |
| 3 | Modo inline | `CU-AVI-INL` (nuevo) | `@longbox_comiqueria_bot berserk` en cualquier chat → elegir un producto → se comparte su ficha pública |
| 4 | Seguridad | Un tipo de aviso nuevo, **«Seguridad»** | Bloqueo por intentos, ingreso del personal desde una IP nueva, alta o cambio de rol de un Administrador, propagación masiva de precios |
| 5 | Salud del sistema | `CU-AVI-EST` (nuevo) y un tipo de aviso nuevo, **«Sistema»** | `/estado` (disco, memoria, base, último respaldo, última vuelta del reloj) y un aviso si el respaldo falta o el disco se llena |
| 6 | Devoluciones con fotos | El aviso «Reclamo nuevo» de `CU-AVI-CAM` | Por Telegram llega con las fotos del reclamo y el enlace para resolverlo. Sin botones: resolver mueve dinero |

---

## 2. Conceptos que toca

| Concepto | ¿Existe? | Qué hace este plan con él |
| --- | --- | --- |
| `PreferenciaAviso` | Sí | Gana tres tipos: `ventas`, `seguridad`, `sistema`, y el resumen (`resumen`) |
| `ConfiguracionSistema` | Sí | Gana **la hora del resumen** (09:00 por defecto) y cuándo salió el último (para no mandarlo dos veces) |
| `RegistroAuditoria` | Sí | Sólo lo lee: los inicios de sesión anteriores dicen si una IP es nueva |
| Un reloj por minuto | En parte | Hoy `longbox-casilla.timer` corre la casilla. Pasa a correr **`manage.py cada_minuto`**: la casilla, el resumen si toca y los controles de salud. En esta PC lo hace `telegram escuchar` |
| Un respaldo diario en la VM | **No** | La VM no se respalda sola: sólo se respalda la base local al subir. Se suma `longbox-respaldo.timer` (03:30, `respaldar_base`) para que el control de salud tenga algo que mirar |

---

## 3. Ambigüedades detectadas

| # | Dónde | Las dos lecturas | Recomendación |
| --- | --- | --- | --- |
| 1 | Canal por defecto de los tipos nuevos | Por correo, como los demás (decisión 3 del plan anterior) / sólo por Telegram | **Ventas, resumen y sistema: por Telegram si está vinculado, y si no, nada.** Por correo serían decenas de mensajes por día. **Seguridad: por los dos canales**, como el bloqueo de hoy |
| 2 | El resumen | Mandarlo siempre / sólo si hay algo pendiente | **Siempre**: también confirma que el bot y el reloj andan |
| 3 | Ventas de mostrador | También avisarlas / sólo las online | **Sólo las online**: la del mostrador la hace alguien que está en el local |
| 4 | Lo que se comparte en modo inline | Lo de la tienda / también el stock exacto | **Lo de la tienda** (título, precio, disponible, en pre-venta o agotado, y el enlace), porque el mensaje lo lee un cliente. **El stock exacto aparece sólo en la lista**, que ve únicamente el Administrador al elegir |
| 5 | Quién usa el modo inline | Cualquiera que conozca el bot / sólo los Administradores vinculados | **Sólo los vinculados y activos**: Telegram dice quién pregunta, y a cualquier otro se le contesta vacío |
| 6 | Las fotos del reclamo | Mandarlas al chat / sólo el enlace | **Mandarlas achicadas, sólo a los Administradores vinculados.** Son evidencia del Cliente y hoy viven fuera de lo público (`privado/`): mandarlas copia un dato personal a los servidores de Telegram |
| 7 | IP nueva | Nunca vista / no vista en un tiempo | **No vista en los inicios de sesión de esa cuenta en los últimos 90 días.** Sólo para el personal. El aviso le llega a todos los Administradores, el afectado incluido |
| 8 | Qué es «cambio masivo» | Cualquier cambio de precio / sólo la propagación | **La propagación del margen global (`CO-053`) y la de una fila de la tabla de precios**, que tocan muchos productos de una vez |

---

## 4. Orden de construcción

| # | Qué | Depende de | Motivo |
| --- | --- | --- | --- |
| 1 | **Los tipos nuevos y su canal por defecto**, y `cada_minuto` | — | Lo usan todos los demás |
| 2 | Avisos de venta | 1 | El más pedido y el más simple |
| 3 | Resumen de la mañana | 1 | Necesita el reloj |
| 4 | Seguridad | 1 | Se engancha en lo que ya se audita |
| 5 | `/estado`, el control de salud y el respaldo de la VM | 1 | El respaldo diario de la VM se instala con la próxima subida (con tu confirmación) |
| 6 | El reclamo con sus fotos | 1 | El envío de varias fotos juntas (`sendMediaGroup`) |
| 7 | Modo inline | — | Hace falta un paso tuyo en @BotFather |

---

## 5. Riesgos

| Riesgo | Dónde | Cómo se cubre |
| --- | --- | --- |
| El resumen sale dos veces, porque el reloj de la VM y `escuchar` corren a la vez | 3 | Se marca «enviado hoy» con bloqueo de fila; el segundo no lo manda. Prueba de concurrencia |
| Un aviso de venta frena el pago | 2 | Sale después de confirmar la transacción y en segundo plano. Si Telegram falla, el pago no se entera |
| El modo inline expone el catálogo o los precios internos | 7 | Sólo contesta a vinculados activos; el mensaje compartido no lleva stock ni costos. Prueba con un usuario ajeno |
| `cada_minuto` pesa en una VM de 1 GiB | 1, 5 | Cada parte mira primero si le toca y sale; los controles de salud leen archivos, no consultan de más |
| Un aviso de sistema se repite cada minuto | 5 | Uno por día y por problema, mientras el problema siga |

---

## 6. Fuera de alcance

- Resolver un reclamo, despachar restock o registrar llegadas desde el chat: mueven dinero o stock y se
  hacen en la web.
- Avisos al Cliente por Telegram.
- La foto de un remito y las notas de voz (dependen del modelo en la VM).

---

## 7. Lo que necesito del responsable

1. **Aprobar el plan**, o decir qué cambia.
2. **Las ocho ambigüedades** del apartado 3.
3. **Para el modo inline**, cuando lleguemos al punto 7: en Telegram, a **@BotFather**, `/setinline`,
   elegir `@longbox_comiqueria_bot` y escribir el texto de ayuda (por ejemplo «Buscar un producto…»).
4. **Subir a la VM** al final, para instalar el reloj por minuto y el respaldo diario.
