> **Tipo: Normativo** una vez aprobado. Antes de la aprobación es una propuesta.
> Se escribe **antes** de programar y **no se reescribe** después: si algo cambió durante la
> construcción, eso va a la bitácora del módulo, no acá.

# Plan — `11` Cuenta de Cliente

**Estado del plan:** Aprobado el 2026-09-30, con las respuestas registradas en `docs/DEUDA.md` · **Fecha:** 2026-09-30

Primer plan del módulo. Esta sesión cubre sólo la consulta del padrón por el Administrador
(`CU-CLI-CON`). El resto del módulo depende del panel del Cliente o de Pedido.

---

## 1. Qué cubre

| Caso de uso | Contratos | Operaciones de escritura | Operaciones de consulta |
| --- | --- | --- | --- |
| `CU-CLI-CON` | `CO-194`, `CO-195` | 0 | 2 |

**Total: 2 contratos.** El listado de `CO-194` existe (`ClienteListaView`) y se verifica contra
el contrato. La ficha de `CO-195` no existe y se construye: identificación, contacto, domicilio,
estado, fecha de registro y fecha de aceptación de la política de privacidad, **sin ninguna
acción**. Cada fila del listado enlaza a la ficha.

---

## 2. Conceptos que toca

| Concepto | ¿Existe? | Qué hace este módulo con él |
| --- | --- | --- |
| `Usuario` con rol Cliente | Sí | Sólo lo lee |

---

## 3. Ambigüedades detectadas

| # | Dónde | Las dos lecturas | Qué se necesita para destrabarla |
| --- | --- | --- | --- |
| 1 | `CO-195`: «identificación» | La cuenta de Cliente no guarda documento. **(a)** Identificación es nombre y apellido. **(b)** Falta un dato. **Recomiendo (a)**: `CO-107` no pide documento en el alta | Nada, salvo objeción |
| 2 | `CO-195`: sin acciones de modificación | La ficha no ofrece ninguna acción, ni siquiera un enlace a otra pantalla que modifique. La prueba lo afirma sobre el HTML de la respuesta: no hay formularios ni enlaces a direcciones de escritura | — |

---

## 4. Orden de construcción

| # | Qué | Depende de | Motivo |
| --- | --- | --- | --- |
| 1 | Prueba de contrato de `CO-194`, con acceso por la dirección real con rol Cajero y Cliente | Estilo preliminar | Ya construido |
| 2 | Ficha de `CO-195` con su prueba | 1 | Datos personales (Ley 25.326): la restricción se prueba en el servidor |

---

## 5. Riesgos

| Riesgo | Dónde aparece | Cómo se cubre |
| --- | --- | --- |
| La ficha abierta a otro rol | `CO-195` | Prueba por la dirección real con Cajero, Cliente y sin sesión |
| La ficha muestra una cuenta de personal | La dirección recibe un identificador de `Usuario` | La vista filtra por rol Cliente; con una cuenta de personal responde 404. Con prueba |

---

## 6. Fuera de alcance

`CU-CLI-DAT`, `CU-CLI-HIS` y `CU-CLI-BAJ`.

---
---

# Plan — `11` Cuenta de Cliente · segunda parte: el panel del Cliente

**Estado del plan:** Aprobado el 2026-10-09, con las recomendaciones de la sección 3; en la 2,
la sección Stock en Local queda oculta · **Fecha:** 2026-10-09

A pedido del responsable («el perfil de usuario»). Desde la compra online hay pedidos y puntos, y
el Cliente no tiene dónde verlos: «Mi cuenta» en la tienda es un menú con el carrito y el cierre
de sesión. Esta parte construye el panel y la edición del perfil. La sección Puntos del panel es
`CU-PTS-CON` (plan 10).

---

## 1. Qué cubre

| Caso de uso | Contratos | Operaciones de escritura | Operaciones de consulta |
| --- | --- | --- | --- |
| `CU-CLI-HIS` | `CO-192`, `CO-193` | 0 | 2 |
| `CU-CLI-DAT` | `CO-108`, `CO-109`, `CO-110`, `CO-111` | 4 | 0 |
| `CU-TDA-CMP` (cierre) | El enlace de seguimiento en el correo de confirmación (paso 7) | — | — |

**Total: 6 contratos.**

---

## 2. Conceptos que toca

| Concepto | ¿Existe? | Qué hace este plan con él |
| --- | --- | --- |
| `Usuario` | Sí | `CO-108` cambia nombre, teléfono y dirección; `CO-110`, el correo; `CO-111`, la contraseña |
| Token de cambio de correo | **No** | Ambigüedad 1 |
| `Pedido`, `LineaPedido`, `TransicionDePedido` | Sí / plan 08 | Los lee: el detalle muestra la línea de tiempo (plan 08, ambigüedad 1) |
| `LotePuntos`, `MovimientoPuntos` | Sí | Los lee la sección Puntos (plan 10) |

---

## 3. Ambigüedades detectadas

| # | Dónde | Las dos lecturas | Qué se necesita para destrabarla |
| --- | --- | --- | --- |
| 1 | **El token de cambio de correo.** `CO-109`: «Se creó un token de verificación de correo […]; este token de verificación de correo es un concepto distinto» de `TokenRecuperacion`. El modelo no lo declara | **(a)** `TokenCambioCorreo`, hermano de `EnlaceActivacion` y `TokenRecuperacion` sobre la misma base (un solo uso, vigente, consumido o vencido), que además guarda el correo nuevo, con vigencia de 24 horas. **(b)** Reutilizar `TokenRecuperacion` | **Recomiendo (a)**: es lo que pide el contrato. La vigencia no está escrita en ningún lado; 24 horas queda entre los 30 minutos de la recuperación y las 48 horas de la activación. Agregado al modelo |
| 2 | **La sección Stock en Local** (`CU-CLI-HIS` paso 7) | `ArticuloRetenido` no existe (módulo 18). **(a)** La sección no se muestra hasta que exista, y `CU-CLI-HIS` queda `Parcial`. **(b)** Se muestra vacía | **Recomiendo (a)**: una sección vacía le diría al Cliente que no tiene nada guardado, y eso todavía no lo puede saber el sistema |
| 3 | **Activos e historial** (`CU-CLI-HIS` pasos 3 y 5: «completados y cancelados») | DME-07 termina en Despachado y no hay un pedido cancelado entero. **(a)** Activos: todo lo que no está Despachado. Historial: los Despachados | **Recomiendo (a)**. Si más adelante existe la cancelación entera, el historial la suma |
| 4 | **Aviso al correo anterior** cuando se confirma el cambio de correo | `Nada` en la especificación. **(a)** El correo anterior recibe un aviso de que la cuenta cambió de correo. **(b)** Nada | **Recomiendo (a)**: si alguien cambia el correo sin permiso, el titular se entera. Agregado |
| 5 | **«Invalida todas las sesiones en otros dispositivos»** (`CO-111`) | **(a)** Se cierran las demás sesiones abiertas y la actual sigue, con el mismo mecanismo que ya usa la gestión de usuarios. | Sin ambigüedad de lectura; se anota porque la prueba la ejerce con dos navegadores |
| 6 | **Los pedidos hechos como invitado con el mismo correo** | `CU-TDA-INV`, comentarios: «deberá crear una cuenta y vincular el pedido por número de orden». No hay caso de uso que vincule | No se muestran. Vincularlos sería un caso de uso nuevo, que no se inventa |

---

## 4. Orden de construcción

| # | Qué | Depende de | Motivo |
| --- | --- | --- | --- |
| 1 | El panel «Mi cuenta» con sus secciones (`CO-192`) y el menú de la tienda que lleva ahí | Plan 08, paso 1 | Es la puerta de todo lo demás |
| 2 | Detalle de un pedido propio con su línea de tiempo (`CO-193`); el enlace del correo de confirmación | 1 | Cierra `CU-TDA-CMP` |
| 3 | `CO-108`: editar nombre, teléfono y dirección, con las validaciones del registro | 1 | |
| 4 | `CO-111`: cambiar la contraseña | 1 | |
| 5 | `TokenCambioCorreo`, `CO-109` y `CO-110` | 1 | El único con concepto nuevo |

---

## 5. Riesgos

| Riesgo | Dónde | Cómo se cubre |
| --- | --- | --- |
| Un Cliente ve el pedido de otro cambiando el número en la dirección | `CO-193` | El pedido se busca entre los del Cliente: el de otro responde 404. Prueba por la dirección real |
| El correo nuevo ya es de otra cuenta, o se toma entre el pedido y la confirmación | `CO-109` E1, `CO-110` | Se valida en los dos momentos; la unicidad de la base (I-10) es la última barrera |
| Un token reutilizado | `CO-110` | Se consume dentro de la misma transacción que cambia el correo |
| `CO-109` cambia el correo antes de tiempo | `CO-109` | Postcondición negativa explícita: `u.correo` no fue modificado. Prueba |
| La contraseña actual equivocada cambia algo | `CO-111` | Prueba que compara el hash antes y después |
| El personal entra al panel | Acceso | 403 por la dirección real |

---

## 6. Fuera de alcance

- La sección Stock en Local y `CU-STK-DES` (módulo 18).
- El acceso a `CU-PED-OPC` desde un pedido con artículos demorados (plan 08, segunda parte).
- La baja de la cuenta (`CU-CLI-BAJ`).
