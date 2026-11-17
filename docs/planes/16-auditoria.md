> **Tipo: Normativo** una vez aprobado. Antes de la aprobación es una propuesta.
> Se escribe **antes** de programar y **no se reescribe** después: si algo cambió durante la
> construcción, eso va a la bitácora del módulo, no acá.

# Plan — `16` Auditoría

**Estado del plan:** Aprobado el 2026-09-30, con las respuestas registradas en `docs/DEUDA.md` · **Fecha:** 2026-09-30

---

## 1. Qué cubre

| Caso de uso | Contratos | Operaciones de escritura | Operaciones de consulta |
| --- | --- | --- | --- |
| `CU-AUD-CON` | `CO-205`, `CO-206`, `CO-129` | 1 (la exportación, que se audita) | 2 |

**Total: 3 contratos.** `RegistroAuditoria` existe, es inmutable y ya está poblado. Se construye
la pantalla de consulta: 50 entradas por página, de la más reciente a la más antigua, con
filtros por actor, tipo de acción, entidad y rango de fechas. Se suman el detalle de una
entrada y la exportación CSV de **todas** las entradas del filtro activo, no sólo la página.

La consulta no se audita. La exportación sí, con la acción «Exportación del log de auditoría»,
ya declarada en el modelo (INC-06).

La ficha dice que cualquier intento de escritura sobre el log se rechaza con 403. Las direcciones
nuevas responden 403, y no 405, a todo método que no sea de lectura, salvo la exportación.
La prueba lo ejerce con `POST`, `PUT` y `DELETE`.

---

## 2. Conceptos que toca

| Concepto | ¿Existe? | Qué hace este módulo con él |
| --- | --- | --- |
| `RegistroAuditoria` | Sí | Lo lee. Escribe sólo la entrada de la exportación |

---

## 3. Ambigüedades detectadas

| # | Dónde | Las dos lecturas | Qué se necesita para destrabarla |
| --- | --- | --- | --- |
| 1 | `CU-AUD-CON` paso 3: tipo de acción «alta / modificación / eliminación / cobro / cancelación / cambio de rol / inicio de sesión / cierre de sesión / exportación» | El log guarda un enumerado cerrado de acciones concretas (28 hoy). Las nueve categorías de la ficha no están mapeadas a ese enumerado en ninguna parte. **(a)** El filtro ofrece las acciones del enumerado, agrupadas. **(b)** Ofrece las nueve categorías, con un mapeo que hay que inventar. **Recomiendo (a)** | Decisión del responsable. Con (b), el mapeo lo tiene que escribir el documento |
| 2 | Paso 3: filtro por actor «usuario específico o tipo de rol» | La entrada guarda el correo del actor, no su rol en ese momento. **(a)** El filtro por rol usa el rol **actual** de la cuenta; una cuenta eliminada no entra en ningún rol. **(b)** Hay que guardar el rol en cada entrada, lo que cambia el modelo. **Recomiendo (a)**, y que la pantalla lo diga | Decisión del responsable |
| 3 | `CO-206`: «valor anterior y valor nuevo cuando aplican» | El modelo declara un único `detalle` que contiene los dos valores. Se presenta el detalle tal como se registró. No se separan con un análisis de texto que el modelo no declara | Nada, salvo objeción |
| 4 | Paso 3: «entidad afectada» | Es el tipo del objetivo genérico (P-10). El filtro ofrece los tipos que aparecen en el log | — |

---

## 4. Orden de construcción

| # | Qué | Depende de | Motivo |
| --- | --- | --- | --- |
| 1 | `CO-205` sin filtros de acción ni de rol | Estilo preliminar | Paginado y orden. Fija la pantalla |
| 2 | Filtros | **Ambigüedades 1 y 2** | Si siguen abiertas, se construyen actor por correo, entidad y fechas, y `CU-AUD-CON` queda `Parcial` |
| 3 | `CO-206` | 1 | — |
| 4 | `CO-129` | 2 | La prueba compara las filas del CSV con el total del filtro, en más de una página |

---

## 5. Riesgos

| Riesgo | Dónde aparece | Cómo se cubre |
| --- | --- | --- |
| Volumen del log | La exportación recorre todo el filtro | Se genera en flujo, sin cargar todas las entradas en memoria |
| Inyección de fórmulas en el CSV | Un correo o un detalle que empieza con `=`, `+`, `-` o `@` | Esas celdas se escapan. Con prueba |
| Control de acceso | Las tres operaciones | Prueba por la dirección real con Cajero, Cliente y sin sesión |

---

## 6. Fuera de alcance

Nada más en el módulo.

---

# Plan — `16` Auditoría · segunda parte: cómo estaba antes

**Estado del plan:** Aprobado el 2026-11-17, con las recomendaciones de la sección 3 · **Fecha:** 2026-11-17

Pedido del responsable del 2026-11-17, por exigencia de la cátedra: toda modificación tiene que dejar
registrado **qué se cambió y cómo estaba antes** —un valor, un banner, una imagen—. `CO-206` ya lo
pide («valor anterior y valor nuevo cuando aplican»), pero hoy los dos valores viven dentro del
texto libre de `detalle` (ambigüedad 3 de la primera parte), y en cuatro operaciones lo anterior se
pierde:

| Operación | Qué se pierde hoy |
| --- | --- |
| `CO-133` `editarBanner` | La imagen reemplazada se borra del almacenamiento; el log dice sólo «imagen reemplazada» |
| `CO-131` `actualizarIdentidadVisual` | Lo mismo con el logo, la imagen de fondo y la del ingreso |
| `CO-135`/`CO-136` FAQ | Se guarda sólo el largo del contenido anterior, no el contenido |
| Canales de aviso (`CU-AVI-CAM`) | Se guarda cómo quedaron, no cómo estaban |
| Secciones de la portada (`guardarSeccionesDeLaPortada`) | «Imagen cambiada en …», sin la anterior |

---

## 1. Qué cubre

| Caso de uso | Contratos | Operaciones de escritura | Operaciones de consulta |
| --- | --- | --- | --- |
| `CU-AUD-CON` | `CO-206` (el detalle), `CO-129` (la exportación) | 0 | 2 |
| Toda operación que **modifica** y audita | La entrada que crean: usuarios, datos y correo del Cliente, catálogos, ofertas, tabla de precios, margen y parámetros, modelo de lenguaje, producto, proveedor, banner, identidad visual, FAQ, secciones de la portada, plazo de retención, canales de aviso y avance del pedido | ~20 sitios | — |

Ningún contrato nuevo. Cambia la **forma** de la entrada de auditoría, no qué se audita.

---

## 2. Conceptos que toca

| Concepto | ¿Existe? | Qué hace este plan con él |
| --- | --- | --- |
| `RegistroAuditoria` | Sí | Campo nuevo `cambios` (JSON): lista de `{campo, antes, despues}`. **Migración** aditiva; la entrada sigue siendo inmutable (`save()`, `delete()` y el disparador de I-13 no cambian). `detalle` se conserva y, si el sitio no lo escribe, se arma con los cambios, para que la lista y el CSV sigan iguales |
| Imágenes reemplazadas (banner, identidad visual, secciones) | Sí | **Ya no se borran:** se mueven a `media/auditoria/` y la entrada guarda su ruta como «antes» |

---

## 3. Ambigüedades detectadas

| # | Dónde | Las dos lecturas | Recomendación |
| --- | --- | --- | --- |
| 1 | `CO-206` | **(a)** Campo estructurado y el detalle en tabla «Qué se cambió · Cómo estaba antes · Cómo quedó». **(b)** Seguir con el texto libre y sólo completar lo que falta | **(a).** Es lo que la cátedra va a mirar, y deja de depender de cómo cada sitio redacta el texto |
| 2 | `CO-133` Notas: «La imagen anterior no se conserva»; `CO-131` igual | Conservarla contradice la nota del contrato | **Conservarla** (corrección a la especificación, B-16-005). Las imágenes ya están en WebP y pesan poco |
| 3 | Entradas viejas | No tienen `cambios` | Se muestran como hasta hoy, con su detalle. No se reescriben: el log es inmutable |
| 4 | Bajas y reactivaciones | ¿Entran? | **No en esta parte.** Su «antes» es el estado (Activo → Inactivo), que la acción ya dice |

---

## 4. Orden de construcción

| # | Qué | Depende de | Motivo |
| --- | --- | --- | --- |
| 1 | `cambios` en el modelo, `registrar(..., cambios=...)` y la migración | — | La forma primero |
| 2 | Los sitios que ya calculan antes y después: pasan la lista en vez de sólo el texto | 1 | Mecánico |
| 3 | Los cinco que pierden lo anterior: banner, identidad, FAQ, canales, secciones | 1 | Lo que de verdad faltaba |
| 4 | El detalle (`CO-206`): la tabla, con miniatura cuando el valor es una imagen | 1 | — |
| 5 | Bitácora (B-16-005, corrección de `CO-133` y `CO-131`), `ESTADO.md` y la deuda del documento | 1 a 4 | — |

---

## 5. Riesgos

| Riesgo | Dónde aparece | Cómo se cubre |
| --- | --- | --- |
| Un sitio sigue escribiendo sólo texto | Cualquier modificación | Prueba que recorre las acciones de modificación y exige `cambios` con «antes» |
| Una imagen conservada se borra por otro camino | El reemplazo y la limpieza de `media/` | La prueba de `CO-133` verifica que el archivo anterior sigue existiendo |
| El disparador de inmutabilidad rechaza la columna nueva | La migración | Se aplica sobre la base de desarrollo antes de cerrar, como pide `CLAUDE.md` |

**Pruebas:** `test_CO206_el_detalle_muestra_como_estaba_antes`,
`test_CO133_el_banner_reemplazado_conserva_la_imagen_anterior`,
`test_CO131_la_identidad_conserva_el_logo_anterior`, `test_CO135_la_faq_guarda_el_contenido_anterior`,
la de los canales y la de las secciones, y la negativa: una entrada vieja, sin `cambios`, se sigue
viendo igual.

---

## 6. Fuera de alcance

- Las bajas y reactivaciones (ambigüedad 4).
- Reescribir las entradas viejas.
