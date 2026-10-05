> **Tipo: Normativo** una vez aprobado. Antes de la aprobación es una propuesta.
> Se escribe **antes** de programar y **no se reescribe** después: si algo cambió durante la
> construcción, eso va a la bitácora del módulo, no acá.

# Plan — `07` Tienda Online

**Estado del plan:** Aprobado el 2026-10-02 por pedido explícito del responsable («crea un mini
apartado de tienda para la vista del cliente»), con las recomendaciones de la sección 3 aplicadas
· **Fecha:** 2026-10-02

Primer plan del módulo. Cubre sólo el catálogo público. El carrito, la compra y la consulta de
pedidos dependen de `Carrito`, `Pedido` y `TransaccionPago`, que no existen.

---

## 1. Qué cubre

| Caso de uso | Contratos | Operaciones de escritura | Operaciones de consulta |
| --- | --- | --- | --- |
| `CU-TDA-CAT` | `CO-176`, `CO-177` | 0 | 2 |

Las acciones de la ficha («Agregar al carrito», «Avisarme cuando haya stock», «Reservar») inician
`CU-TDA-CRA` y `CU-RST-SUS`, que no están construidos.

---

## 2. Conceptos que toca

| Concepto | ¿Existe? | Qué hace este módulo con él |
| --- | --- | --- |
| `Producto` y sus dos especializaciones | Sí | Sólo los lee |
| `Etiqueta`, `GrupoEtiqueta` | Sí | Sólo los lee: el filtro de franquicia es el filtro por etiqueta |
| `Banner`, `ContenidoFAQ`, `IdentidadVisual` | Sí | La portada los muestra |
| `Oferta` | **No** | Sin ofertas, ningún precio sale tachado |

---

## 3. Ambigüedades detectadas

| # | Dónde | Las dos lecturas | Qué se aplicó |
| --- | --- | --- | --- |
| 1 | Precondición de `CU-TDA-CAT` y `CO-176`: «el acceso es público» frente a la portada, que hoy es sólo de la cuenta de cliente (C-20) | **(a)** Catálogo y ficha públicos; la portada sigue esperando C-20. **(b)** Todo detrás del inicio de sesión | **(a)**: la precondición del contrato es explícita |
| 2 | `solo_adultos` | Ningún caso de uso dice qué ve el catálogo público de un producto para adultos, y no hay verificación de edad | Se excluye del catálogo público, para todos. Es lo que el campo declara hacer en el código |
| 3 | Las acciones de la ficha | Inician casos de uso no construidos | Se muestran deshabilitadas, con la línea «Disponible próximamente» |
| 4 | Estado «Agotado» | Un producto Activo con stock 0 y uno en estado Agotado | Los dos se presentan como «Sin stock» y caen en el filtro «Agotado» |
| 5 | Filtro «franquicia» | Es una faceta de etiquetas (`CO-042`), no un campo | Filtro por etiqueta activa, agrupado por faceta |
| 6 | «paginados» | Sin tamaño | 24 por página: múltiplo de las columnas de la estantería |

---

## 4. Orden de construcción

| # | Qué | Depende de |
| --- | --- | --- |
| 1 | `CO-176`: consulta con filtros, orden y paginación | — |
| 2 | `CO-177`: ficha pública con su acción según estado | 1 |
| 3 | Portada: carrusel, ticker y recién llegados | 1 |

---

## 5. Riesgos

| Riesgo | Cómo se cubre |
| --- | --- |
| Un Descatalogado o Cancelado visible por algún filtro | Prueba con los cinco estados contra cada valor del filtro de estado |
| Un producto para adultos visible | Prueba explícita |
| La ficha de un producto no visible se abre por la dirección | Responde 404 |

---

## 6. Fuera de alcance

- `CU-TDA-CRC`, `CRA`, `CRM`, `CRB`, `CMP`, `INV`: etapa B.
- El precio tachado por oferta: cuando exista `Oferta`.

---
---

# Plan — `07` Tienda Online · segunda parte: carrito

**Estado del plan:** Aprobado el 2026-10-03, con las recomendaciones de la sección 3 · **Fecha:** 2026-10-03

Segunda parte del plan del módulo. La primera, de arriba, está aprobada y no se toca. Ésta cubre
el carrito. Va **antes** que las ofertas (plan 03, segunda parte): los contratos de oferta, de
tabla de precios y de margen terminan en «las `LineaCarrito` afectadas quedaron actualizadas», y
sin carrito esa postcondición no tiene sobre qué cumplirse.

---

## 1. Qué cubre

| Caso de uso | Contratos | Operaciones de escritura | Operaciones de consulta |
| --- | --- | --- | --- |
| `CU-TDA-CRA` | `CO-083` | 1 | 0 |
| `CU-TDA-CRC` | `CO-178`, `CO-085`, `CO-086` | 2 | 1 |
| `CU-TDA-CRM` | `CO-084` | 1 | 0 |
| `CU-TDA-CRB` | `CO-085` | 1 | 0 |
| `CU-TDA-CAT` (cierre) | `CO-083` desde el paso 6 | — | — |
| `CU-AUT-INI` (cierre parcial) | `CO-086` | 1 | 0 |
| `CU-PVP-TBM`, `CU-PVP-MAR` (cierre) | `CO-048`, `CO-053`: la propagación a `LineaCarrito` | — | — |

**Total: 5 contratos nuevos** (`CO-083`, `CO-084`, `CO-085`, `CO-086`, `CO-178`) y la parte
pendiente de dos que ya existen (`CO-048`, `CO-053`). `CO-179 procederAlPago` queda fuera: sólo
transfiere a `CU-TDA-CMP`, que no existe.

---

## 2. Conceptos que toca

| Concepto | ¿Existe? | Qué hace este plan con él |
| --- | --- | --- |
| `Carrito` | **No** | Lo crea: `usuario` (opcional), `persistencia`, `actualizado_en`, y la clave de sesión del invitado |
| `LineaCarrito` | **No** | La crea: `cantidad`, `precio_vigente`. La disponibilidad se deriva, no se guarda (ambigüedad 2) |
| `Producto` | Sí | Lo lee: estado, stock y precio visible |
| `Usuario` | Sí | Se asocia al carrito persistente |
| `TablaPrecioReferencia`, margen global | Sí | Su propagación pasa a alcanzar a las líneas de carrito |

El precio visible de un producto pasa a salir de **una sola función**. Hoy es `producto.precio`;
con las ofertas, es el precio con la oferta vigente aplicada. El carrito, la tienda y más adelante
el mostrador leen esa función y no el campo.

---

## 3. Ambigüedades detectadas

| # | Dónde | Las dos lecturas | Qué se necesita para destrabarla |
| --- | --- | --- | --- |
| 1 | `CU-TDA-CRC` A2 («el precio cambió desde que se agregó») frente a `CO-048`, `CO-053` y los contratos de oferta («las `LineaCarrito` afectadas quedaron actualizadas») | Si la propagación pisa el precio de la línea, la consulta ya no tiene contra qué comparar y el aviso de A2 nunca aparece. **(a)** La línea guarda dos importes: el precio vigente, que la propagación actualiza, y el precio que el Cliente vio al agregar o al cambiar la cantidad. El aviso aparece cuando difieren y se apaga cuando el Cliente vuelve a tocar la línea. **(b)** La propagación no toca la línea; la consulta compara contra el precio del producto. Cumple A2, pero deja `CO-048` y `CO-053` sin cumplir, y `CU-PVP-TBM` y `MAR` en `Parcial` para siempre | Decisión. **Recomiendo (a)**: es la única que cumple los cuatro contratos. Es un agregado al modelo y va a la bitácora |
| 2 | `LineaCarrito.disponibilidad` en el modelo de dominio: «{Disponible, Producto no disponible}». `CO-178` deriva **tres** valores, con «Stock insuficiente» | **(a)** Se deriva en cada consulta del estado y del stock del producto, como dice `CO-178`, y no se guarda. **(b)** Se guarda, y hay que actualizarlo ante cada cambio de stock o de estado | **Recomiendo (a)**. La diferencia con el modelo va a la bitácora como corrección |
| 3 | Quién tiene carrito | Los casos de uso dicen «Cliente» e «invitado». Un Administrador o un Cajero con sesión que entra a la tienda… **(a)** No tiene carrito: las acciones de compra no se le ofrecen. **(b)** Lo tiene, como cualquiera | **Recomiendo (a)**: el personal no compra por la tienda con su cuenta de trabajo, y la prueba de acceso con el rol equivocado lo fija |
| 4 | Duración del carrito de invitado: «se destruye al cerrar el navegador» | La sesión del sistema ya vence a los 30 minutos sin actividad (`SESSION_COOKIE_AGE`). **(a)** El carrito de invitado vive lo que vive su sesión: se pierde al cerrar el navegador **o** tras 30 minutos sin actividad. **(b)** Sólo al cerrar el navegador, con una sesión de invitado distinta de la del personal | **Recomiendo (a)**: no abre una segunda política de sesión. Va a la bitácora |
| 5 | Avanzar al pago (`CU-TDA-CRC` paso 3, `CO-179`) | `CU-TDA-CMP` no existe | El botón se muestra deshabilitado con «Disponible próximamente», como las acciones de la ficha (B-07-002) |
| 6 | «Avisarme cuando haya stock» en la ficha | Inicia `CU-RST-SUS`, que no existe | Sigue deshabilitado |

---

## 4. Orden de construcción

| # | Qué | Depende de | Motivo |
| --- | --- | --- | --- |
| 1 | `Carrito`, `LineaCarrito` y el precio visible en una sola función | — | Todo lo demás los usa |
| 2 | `CU-TDA-CRA` (`CO-083`), y el botón de la ficha habilitado | 1 | Sin agregar no hay qué consultar |
| 3 | `CU-TDA-CRC` (`CO-178`), con disponibilidad y aviso de precio | 2 | |
| 4 | `CU-TDA-CRM` (`CO-084`) y `CU-TDA-CRB` (`CO-085`) | 3 | Se inician desde el carrito |
| 5 | `CO-086`, al iniciar sesión | 2 | Toca la autenticación, que ya existe |
| 6 | Propagación de `CO-048` y `CO-053` a las líneas | 1 | Cierra `CU-PVP-TBM` y `MAR` |

---

## 5. Riesgos

| Riesgo | Dónde aparece | Cómo se cubre |
| --- | --- | --- |
| Un invitado manipula la dirección y toca la línea de otro carrito | `CO-084`, `CO-085` | La línea se busca **dentro** del carrito de quien pide; la de otro responde 404. Prueba por la dirección real |
| El stock baja entre agregar y consultar | `CO-178` | Es el comportamiento declarado: la consulta lo marca «Stock insuficiente». Prueba explícita |
| Dos pestañas agregan el mismo producto a la vez y duplican la línea | `CO-083` | Unicidad (carrito, producto) en la base, y la suma dentro de una transacción |
| La fusión al iniciar sesión pierde el carrito de invitado | `CO-086` | Django rota la clave de sesión al iniciar sesión: el carrito se ubica por el identificador guardado en la sesión, que sí sobrevive. Prueba con el inicio de sesión real |
| Postcondiciones negativas | `CO-178` | La consulta no modifica nada: prueba que compara el carrito antes y después |

---

## 6. Fuera de alcance

- `CO-179 procederAlPago`, `CU-TDA-CMP` y `CU-TDA-INV`: necesitan `Pedido` y `TransaccionPago`.
- `LineaCarrito.cubierta con puntos`: no existe Puntos.
- La limpieza de carritos de invitado abandonados: es un proceso periódico (P-05).

---
---

# Plan — `07` Tienda Online · tercera parte: filas de la portada

**Estado del plan:** Aprobado el 2026-10-04 por pedido explícito del responsable («agregar a la
presentación de inicio de la tienda la capacidad de poner distintos grupos de catálogo por
etiqueta o grupos de etiqueta como barras de desplazamiento horizontal») · **Fecha:** 2026-10-04

Es un agregado: ningún caso de uso lo describe. Va a la bitácora (B-07-009).

## 1. Qué cubre

La portada de la tienda suma, debajo de «Recién llegados», filas de productos que se recorren de
costado. Cada fila sale de una **etiqueta** («Shonen») o de un **grupo de etiquetas** entero
(«Demografía»: los productos con cualquiera de sus etiquetas). El Administrador elige cuáles, en
qué orden y con qué título, desde «Tienda → Filas de la portada».

No toca ningún contrato existente. Los productos que muestra salen de la misma consulta que el
catálogo público (`CO-176`): nunca un producto que el catálogo no mostraría.

## 2. Conceptos

| Concepto | ¿Existe? | Qué hace este plan |
| --- | --- | --- |
| `FilaPortada` | **No** | Lo crea: etiqueta **o** grupo, título opcional, orden y si está activa |
| `Etiqueta`, `GrupoEtiqueta` | Sí | Las lee |
| `RegistroAuditoria` | Sí | Una acción nueva: «Modificación de las filas de la portada» |

## 3. Decisiones

| # | Punto | Decisión |
| --- | --- | --- |
| 1 | Cuántos productos por fila | Hasta 12, de lo más nuevo a lo más viejo, sólo los visibles en la tienda |
| 2 | Una fila sin productos | No se dibuja |
| 3 | Título | Si se deja vacío, el nombre de la etiqueta o del grupo |
| 4 | «Ver todo» | Al catálogo filtrado por esa etiqueta o, para un grupo, por el grupo (filtro nuevo del catálogo público, `?grupo=`) |
| 5 | Etiqueta o grupo dados de baja | La fila no se muestra mientras lo estén |
| 6 | Quién la ve | La portada sigue siendo de la cuenta de cliente (C-20) |

## 4. Fuera de alcance

- Filas por editorial, por tipo o elegidas a mano producto por producto.

---

# Plan — `07` Tienda Online · cuarta parte: la cáscara de la tienda y el gestor de filas

**Estado del plan:** Aprobado el 2026-10-04 por pedido explícito del responsable (gestor de filas
«por tarjetas … deslizables/acomodables», imagen en el título de cada fila, botón de preguntas
frecuentes «estilo burbuja de chat» más abajo, «la cinta para acceder a los distintos filtros»
debajo del encabezado, un pie mejor, un encabezado que acompaña al bajar con búsqueda y acceso a
la cuenta, y flechas de las filas con más personalidad) · **Fecha:** 2026-10-04

Es un agregado sobre la tercera parte. Ningún contrato cambia. Va a la bitácora (B-07-010 a
B-07-012).

## 1. Decisiones

| # | Punto | Decisión |
| --- | --- | --- |
| 1 | Gestor de filas | Una tarjeta por fila, como los ítems de la carga de lotes. Se reordenan **arrastrando** la tarjeta o con «Subir» / «Bajar» (teclado y lector de pantalla). El orden se guarda con «Guardar las filas», no al soltar |
| 2 | Imagen de la fila | Opcional. Se procesa como cualquier imagen del sistema (RNF-05: WebP, lado mayor acotado). En la portada abre la fila como una tarjeta titular, con su título |
| 3 | Encabezado | Queda **fijo** arriba al bajar (la guía decía que se escondía: B-07-011). Suma la búsqueda del catálogo y un menú de cuenta nativo (`<details>`) con el correo, el carrito y «Cerrar sesión» |
| 4 | Cinta de accesos | Debajo del encabezado, en todas las pantallas de la tienda: «Novedades», «Pre-ventas» y una entrada por cada fila de la portada activa, que lleva al catálogo filtrado igual que su «Ver todo» |
| 5 | Preguntas frecuentes | Sale del menú y de la estantería. Un globo de diálogo cuadrado fijo abajo a la derecha (`.globo` de la guía), sólo si hay contenido publicado |
| 6 | Pie | Cinta arriba; marca y descripción; «Tienda» (catálogo, pre-ventas, filas); «Ayuda» (preguntas frecuentes, carrito, cuenta); «Contacto» con el correo, el teléfono y las redes con íconos de trazo |
| 7 | Flechas de las filas | Bloques sesgados con chevrones dobles y sombra dura; se deshabilitan en cada extremo. Debajo de la pista, una barra que marca cuánto se recorrió |
| 8 | Animaciones | Sólo las del catálogo de la guía. Ninguna nueva |

## 2. Fuera de alcance

- Un panel propio del Cliente: el menú de cuenta enlaza lo que ya existe (`CU-CLI-DAT` sigue
  pendiente).
- Elegir a mano qué accesos lleva la cinta: salen de las filas de la portada.

---

# Plan — `07` Tienda Online · quinta parte: catálogo con panel, portada pública y correcciones visuales

**Estado del plan:** Aprobado el 2026-10-05 por pedido explícito del responsable (filtros «a tiempo
real», «la barra de filtros a un costado con interruptores, arriba solo la barra de búsqueda»; «un
invitado debería poder ver la pantalla de inicio de la tienda»; «Lo que se viene»; agregar al
carrito desde la tarjeta; carteles «¡TOMO 1!» y «¡ÚLTIMO TOMO!»; y siete correcciones gráficas:
botón de preguntas, barra de búsqueda, pantalla de ingreso, flechas de las filas, doble barra de
desplazamiento, desplegables con la lista del navegador, y el botón de limpiar filtros que movía al
de aplicar) · **Fecha:** 2026-10-05

Ningún contrato cambia de efecto. Va a la bitácora (B-07-013 a B-07-019, B-00-011) y resuelve C-20.

## 1. Decisiones

| # | Punto | Decisión |
| --- | --- | --- |
| 1 | Filtros | Panel al costado con interruptores; tipo, editorial, etiqueta y estado admiten varios valores. Dentro de un grupo de etiquetas alcanza con una; entre grupos, todas. Sólo se ofrecen opciones con productos visibles |
| 2 | Tiempo real | Los interruptores aplican al cambiar; la búsqueda y el precio, al dejar de escribir. Se reemplazan sólo los resultados y la dirección se actualiza (paso 7). Sin guion, el panel tiene «Aplicar filtros» |
| 3 | Orden | Lo más nuevo (por defecto, `CO-176`), próximos a llegar (fecha estimada o programada) y título |
| 4 | Portada | Pública (C-20). La raíz del sitio lleva a la portada |
| 5 | «Lo que se viene» | Una fila más, antes de las del Administrador: pre-ventas, la más próxima primero; «Ver todo» al catálogo de pre-ventas por llegada |
| 6 | Agregar desde la tarjeta | Una unidad, misma operación (`CO-083`) y mismas validaciones; sin recargar si hay guion, con aviso y el contador del encabezado. Invitado y cliente; nunca el personal; nunca un agotado |
| 7 | Carteles | «¡TOMO 1!» en el tomo 1 de una serie de más de un tomo; «¡NOVEDAD!» en lo dado de alta en los últimos 30 días (cambio del 2026-10-05, B-07-024; antes «¡ÚLTIMO TOMO!»). Las pre-ventas no llevan cartel |
| 8 | Acceso | Ingreso, registro y recuperación: pantalla partida en diagonal, sin búsqueda ni globo. A la izquierda, la imagen del ingreso de la identidad visual, o el logo, o el nombre (B-07-020) |
| 9 | Desplegables | Donde el navegador no tiene `appearance: base-select`, una lista propia sobre el `<select>` nativo |

**Ajustes del 2026-10-05, a pedido del responsable:** se quita la cinta de accesos (B-07-021); la
búsqueda marca el foco en su propio marco y «Buscar» tiene relieve; las flechas de las filas
pierden la franja de cinta (B-07-022); el ticker nombra cada serie una vez (B-07-023).
