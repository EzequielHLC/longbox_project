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

---
---

# Plan — `07` Tienda Online · sexta parte: la compra

**Estado del plan:** Aprobado el 2026-10-09, con las recomendaciones de la sección 3. En la 2, el
responsable precisó que tanto el costo como el monto mínimo de envío gratuito se fijan en la
configuración del sistema, y que la integración con costos logísticos se ve más adelante
(B-07-032) · **Fecha:** 2026-10-09

Sexta parte del plan del módulo. Las cinco de arriba están aprobadas y no se tocan. Ésta cubre la
compra online, con cuenta y como invitado. **Es la dependencia raíz de `docs/DEUDA.md`**: sin
`Pedido` y `TransaccionPago` no se puede empezar ninguno de los módulos 08, 09, 10, 14 y 18, ni
`CU-ALT-DEM`, `CU-ALT-CAN`, `CU-CLI-HIS` y `CU-CLI-BAJ`. Por eso va antes que cualquier otro módulo
pendiente.

Trae con ella la parte mínima de Puntos que `CO-089` exige para cerrarse (ambigüedad 3).

---

## 1. Qué cubre

| Caso de uso | Contratos | Operaciones de escritura | Operaciones de consulta |
| --- | --- | --- | --- |
| `CU-TDA-CMP` | `CO-179`, `CO-180`, `CO-087`, `CO-103`, `CO-088`, `CO-089` | 2 (`CO-088`, `CO-089`) | 4 |
| `CU-TDA-INV` | `CO-179`, `CO-181`, `CO-090`, `CO-091`, `CO-089` | 1 (`CO-089`) | 4 |
| `CU-PTS-CJE` (canal online) | `CO-103`, `CO-104`, `CO-190` | 0: ninguna toca `LotePuntos` hasta `CO-089` | 3 |
| `CU-TDA-CRC` (cierre) | El paso 3 pasa a avanzar al pago: cierra B-07-006 | — | — |
| `CU-CFG-PAR` (parcial) | Secciones Fidelización y Logística de `CO-130` | 1 | — |

**Total: 11 contratos distintos**, de los cuales `CO-089` es el pesado: crea `Pedido`,
`LineaPedido`, `TransaccionPago`, `LotePuntos` y `MovimientoPuntos` en una sola transacción, con
idempotencia y con bloqueo de stock.

`CU-PTS-CJE` queda `Parcial`: su rama de mostrador (`CU-VTA-REG` paso 4) espera al módulo 06.

---

## 2. Conceptos que toca

| Concepto | ¿Existe? | Qué hace este plan con él |
| --- | --- | --- |
| `Pedido` | **No** | Lo crea: número único, canal, estado (sólo los dos iniciales de DME-07), correo del invitado, dirección copiada (PD-09), costo de envío, fecha |
| `LineaPedido` | **No** | La crea: cantidad, precio unitario congelado, cubierta con puntos, estado del ítem (sólo Disponible y Reservado de DME-08). Los atributos de demora y compensación nacen vacíos: son del módulo 08 |
| `TransaccionPago` | **No** | La crea: medio Pasarela, monto, estado, referencia **única** en la base (idempotencia de `CO-089`, nota 1). `incluida en cierre` nace en no |
| `LotePuntos` | **No** | Lo crea con origen Compra, y lo consume en orden de caducidad (FIFO) en el débito |
| `MovimientoPuntos` | **No** | Lo crea: Acreditación y Débito, con saldo resultante |
| `Carrito`, `LineaCarrito` | Sí | `LineaCarrito` gana `cubierta con puntos`, que está en el modelo y no se construyó (plan 07, segunda parte, §6). `CO-089` vacía el carrito |
| `Producto` | Sí | `CO-089` descuenta stock con bloqueo de registro; el que llega a cero pasa de Activo a Agotado |
| `ConfiguracionSistema` | Sí | Gana la equivalencia de puntos, la caducidad en meses y el monto mínimo de envío gratuito, que `CU-CFG-PAR` ya especifica. Y lo que resuelva la ambigüedad 2 |
| `Usuario` | Sí | Sólo lo lee: la dirección predeterminada. **`CO-087` no la modifica** (postcondición negativa) |
| Registro del cobro en curso | **No, y no está en el modelo** | Ambigüedad 4 |

---

## 3. Ambigüedades detectadas

| # | Dónde | Las dos lecturas | Qué se necesita para destrabarla |
| --- | --- | --- | --- |
| 1 | **La Pasarela de Pago** (ACT-04; `ALCANCE.md`: «p. ej. MercadoPago») | **(a)** Sólo una pasarela simulada dentro del sistema: una pantalla «Pasarela de prueba» con el monto y los botones Aprobar y Rechazar, que avisa al sistema por el mismo webhook firmado que usaría la real, y que acepta reembolsos. **(b)** La simulada **más** un adaptador de MercadoPago Checkout Pro en modo de prueba, elegible en Parámetros: preferencia de pago, redirección, webhook que se verifica consultando el pago a la API, y reembolso por API. Todo por `core/integraciones.pedir`. Necesita credenciales de prueba de MercadoPago y que el webhook llegue por el túnel. **(c)** Sólo MercadoPago | Decisión. **Recomiendo (b), con MercadoPago en el último paso del orden**: la simulada cierra todos los contratos y es la que usan las pruebas y la demostración sin red; MercadoPago se suma detrás de la misma interfaz (RNF-07) si hay credenciales. Sin credenciales, (b) se reduce a (a) sin perder nada |
| 2 | **El costo de envío** (`CU-TDA-CMP` paso 2, `CU-TDA-INV` paso 5, `CO-087`: «recalcular el costo de envío») | Ningún artefacto dice cómo se calcula. El único dato es el «monto mínimo de envío gratuito» de `CU-CFG-PAR`. **(a)** Un costo fijo nuevo en Parámetros, sección Logística, y gratis desde el monto mínimo. **(b)** Una tabla de costo por provincia. **(c)** Cotizar con un operador logístico | Decisión. **Recomiendo (a)**: es lo mínimo que da sentido a «recalcular» sin inventar una integración. Es un agregado a `CU-CFG-PAR` y al modelo, y va a la bitácora. Con (a) el costo no depende del destino: `CO-087` guarda la dirección y devuelve el mismo costo |
| 3 | **Puntos**: `CO-089` (c) debita y acredita `LotePuntos`, que es del módulo 10 | **(a)** Este plan construye `LotePuntos`, `MovimientoPuntos`, la acreditación, el débito FIFO y el canje en el checkout (`CO-103`, `CO-104`, `CO-190`). La consulta de saldo, la caducidad y el ajuste manual quedan para el módulo 10. **(b)** La compra sin puntos, y `CU-TDA-CMP` queda `Parcial` | **Recomiendo (a)**: `CO-089` tiene la acreditación como postcondición incondicional del Cliente; sin ella el contrato no se verifica nunca. El canje viene casi gratis una vez que hay lotes |
| 4 | **Dónde vive el checkout entre `CO-088` y `CO-089`**. `CO-088` declara «ninguna [postcondición] sobre el dominio» y `CO-089` exige «un checkout confirmado asociado a la referencia». El webhook llega de servidor a servidor: no trae la sesión del Cliente | **(a)** Un registro técnico fuera del modelo de dominio, `CobroEnCurso`: referencia, carrito, dirección declarada, ítems cubiertos, importes congelados al confirmar y monto. `CO-089` lo materializa y lo marca procesado. **(b)** Crear `TransaccionPago` en «Pendiente de verificación» al confirmar | **Recomiendo (a)**. (b) contradice las dos postcondiciones: `CO-088` no crea nada y `CO-089` (a) dice que **ahí** se creó `tp`. Es un agregado y va a la bitácora |
| 5 | **Qué se materializa si el carrito cambia después de confirmar** (otra pestaña agrega algo mientras el Cliente está en la pasarela) | **(a)** Lo congelado en `CobroEnCurso` al confirmar, que es lo que se cobró; el carrito pierde sólo esas líneas. **(b)** El carrito tal como esté al llegar el webhook | **Recomiendo (a)**: el pedido tiene que ser lo que se pagó |
| 6 | **Stock perdido entre la confirmación y el pago aprobado.** `CO-083` dice que la reserva ocurre recién en `CO-089`: dos clientes pueden pagar el último ejemplar | **(a)** El segundo webhook encuentra el stock insuficiente bajo bloqueo y se trata como E3: no se crea nada, se pide el reembolso, se restaura el carrito y se avisa. **(b)** Reservar stock al confirmar | **Recomiendo (a)**: es lo que dicen los contratos, y es exactamente la condición de verificación de RNF-06 («sólo una transacción sea confirmada»). La prueba de concurrencia lo ejerce |
| 7 | **Redondeo de puntos.** RF-19: «M / E puntos»; `CU-PTS-CJE` paso 4: «precio del ítem dividido por la equivalencia» | **(a)** La acreditación redondea hacia abajo (no se regalan fracciones) y los puntos requeridos para un canje, hacia arriba (no se cobra de menos). **(b)** Al entero más cercano en los dos | **Recomiendo (a)**: los puntos son enteros (`MovimientoPuntos.cantidad`) y ninguna de las dos operaciones debe favorecer al error. Todo en `Decimal` |
| 8 | **¿El envío genera puntos, y se puede pagar con puntos?** `CO-089`: «monto abonado en dinero»; RF-20: «subtotal abonado en dinero, excluyendo los ítems cubiertos» | **(a)** Los puntos se acreditan sobre los productos pagados en dinero, sin el envío; el envío no se canjea. Consecuencia: A2 (total cero) sólo ocurre con envío gratuito. **(b)** El envío suma puntos y también se puede cubrir | **Recomiendo (a)**: RF-20 dice «subtotal» y el canje es «ítem por ítem». Va a la bitácora, porque A2 queda más estrecho de lo que parece |
| 9 | **El monto mínimo de envío gratuito** se compara contra… | **(a)** El subtotal de los productos a precio con oferta, antes del canje. **(b)** Lo que queda en dinero después del canje | **Recomiendo (a)**: es el valor de la compra; con (b), canjear puntos podría encarecer el envío, y el Cliente lo leería como una penalización |
| 10 | **Qué es un «ítem» del canje** | **(a)** Una línea entera, con todas sus unidades: el modelo pone `cubierta con puntos` en `LineaCarrito` y en `LineaPedido`. **(b)** Una unidad | **Recomiendo (a)**: es lo que declara el modelo |
| 11 | `CU-TDA-INV` A1: «si el usuario tiene una cuenta registrada, el sistema sugiere iniciar sesión», en el paso 1, cuando todavía no escribió su correo | **(a)** En el paso 1, siempre el enlace «¿Tenés cuenta? Iniciá sesión»; y al declarar los datos, si el correo es de una cuenta, la sugerencia explícita, que se puede ignorar. **(b)** Sólo lo primero | **Recomiendo (a)**. Ojo: (a) revela que un correo tiene cuenta, lo mismo que ya revela el aviso de duplicado del registro. Va a la bitácora |

**Ninguna bloquea un caso de uso entero.** Si la 1 se decidiera por (c) y no hubiera
credenciales, la compra no se podría demostrar; por eso la recomendación es (b).

---

## 4. Orden de construcción

| # | Qué | Depende de | Motivo |
| --- | --- | --- | --- |
| 1 | `Pedido`, `LineaPedido`, `TransaccionPago`, `LotePuntos`, `MovimientoPuntos`, `CobroEnCurso`, `LineaCarrito.cubierta con puntos` y los parámetros nuevos, con sus restricciones en la base: número y referencia únicos, cantidades ≥ 1, importes no negativos (I-09, la primera `CheckConstraint` sobre dinero) | — | Todo lo demás los usa |
| 2 | La interfaz de pasarela y la pasarela simulada, con webhook firmado y reembolso | 1 | Sin ella no hay `CO-089` que probar |
| 3 | `CO-179` y `CO-180`: «Ir a pagar» se habilita y el resumen verifica el stock (E1) | 1 | Cierra B-07-006 |
| 4 | `CO-087`: dirección editable y costo de envío | 3 | |
| 5 | `CO-088` y `CO-089` con cuenta, sin canje: pedido, stock, Agotado, acreditación, vaciado, correo, auditoría, idempotencia, E2, E3 y la carrera del último ejemplar | 2, 4 | El corazón del plan |
| 6 | `CO-103`, `CO-104`, `CO-190` y el débito FIFO en `CO-089`; A2 sin pasarela | 5 | Necesita lotes, que sólo crea el paso 5 |
| 7 | `CU-TDA-INV`: `CO-181`, `CO-090`, `CO-091` y la rama de invitado de `CO-089` | 5 | Reusa el cobro y la materialización |
| 8 | Las secciones Fidelización y Logística de `CU-CFG-PAR` | 1 | Para que el Administrador cambie lo que la compra usa |
| 9 | El adaptador de MercadoPago, si la ambigüedad 1 se decide por (b) y hay credenciales | 2 | Detrás de la misma interfaz; no cambia ningún contrato |

---

## 5. Riesgos

| Riesgo | Dónde aparece | Cómo se cubre |
| --- | --- | --- |
| Doble pedido por un webhook repetido | `CO-089`, nota 1 | Referencia única en la base, no sólo en el código. Prueba que envía el mismo aviso dos veces, también en paralelo |
| Doble venta del último ejemplar | `CO-089`, RNF-06 | `select_for_update` sobre los productos, en orden de clave para no interbloquear (antecedente: B-13-006). Prueba de concurrencia con dos hilos y base real |
| Un tercero falsifica el webhook y genera pedidos sin pagar | `CO-089` | Firma HMAC en la simulada; en MercadoPago el aviso no se cree: se consulta el pago a la API. Prueba con firma inválida por la dirección real |
| El monto del aviso no coincide con lo cobrado | `CO-089` | Se compara contra `CobroEnCurso`; si difiere, no se materializa y se registra el incidente |
| Un fallo a mitad de la transacción deja datos parciales | `CO-089` E3 | Todo dentro de un `atomic`; el reembolso y el aviso, fuera y después. Prueba que fuerza el fallo y verifica que no quedó **nada**: postcondición negativa |
| Dinero con flotantes, o el redondeo de puntos a favor del error | Totales, envío, puntos | `Decimal` en todo; pruebas de borde en la equivalencia (ambigüedad 7) |
| El canje debita antes de tiempo | `CO-103` | Postcondición negativa central: prueba que `LotePuntos` no cambia al marcar ni al revertir |
| Un rechazo que modifica algo | `CO-089` E2, `CU-TDA-INV` E3 | Prueba que compara stock, carrito, puntos y pedidos antes y después |
| `CO-087` pisa la dirección del perfil | `CO-087` | Postcondición negativa explícita, con prueba |
| El correo de confirmación falla y tumba la compra | `CU-TDA-CMP` paso 7 | El correo sale después del `commit`; si falla, el pedido queda y el fallo se registra |
| La red real en las pruebas | MercadoPago | Todo por `pedir`, que `sin_red` corta |
| El personal compra con su cuenta de trabajo | Toda la compra | Como el carrito (segunda parte, amb. 3): prueba con el rol equivocado por la dirección real |

---

## 6. Fuera de alcance

- **El seguimiento del pedido** (`CU-CLI-HIS`) y el listado del personal (`CU-PED-CON`): son lo
  siguiente, porque ya va a haber pedidos. El correo de confirmación lleva el número de pedido; el
  enlace de seguimiento se suma con `CU-CLI-HIS`.
- La transición de Esperando stock de pre-venta a Pendiente de armado (`CO-013`, `CU-ALT-TRA`).
- La consulta de saldo, la caducidad y el ajuste manual de puntos (`CU-PTS-CON`, `CAD`, `ADM`).
- La rama de mostrador del canje (`CU-VTA-REG`).
- La limpieza de cobros en curso abandonados: es un proceso periódico (P-05), como la de carritos.
- El recordatorio de carrito abandonado.

### Después de esta parte

El orden propuesto para lo que sigue, por cuánto desbloquea cada uno. Cada uno con su propio plan,
que se aprueba antes de programarlo:

1. **`11` `CU-CLI-HIS` y `08` `CU-PED-CON`, `EST`**: el pedido ya existe, y es lo que hace visible
   la compra.
2. **`10` Puntos** (`CON`, `ADM`, `CAD`): los lotes ya existen.
3. **`06` Ventas Presenciales** y después **`14` Caja**, que consolida las transacciones de los
   dos canales.
4. **`01` `CU-ALT-TRA`, `DEM`, `CAN` y `08` `OPC`, `CAN`, `CMP`**: el ciclo de la pre-venta y de
   la demora.
5. **`18` Stock Almacenado** y **`09` Devoluciones**.
6. **`05` Restock**.

---
---

# Plan — `07` Tienda Online · séptima parte: la barra del envío gratis

**Estado del plan:** Aprobado el 2026-10-09, las seis decisiones como se proponen · **Fecha:** 2026-10-09

A pedido del responsable («el envío gratis con una barrita de progreso»). Ningún contrato cambia
de efecto: es cómo se muestra lo que ya calcula `CO-180` (B-07-032, B-07-033). Va a la bitácora
como agregado.

## 1. Decisiones

| # | Punto | Propuesta |
| --- | --- | --- |
| 1 | Dónde | En el resumen del carrito, del checkout y del resumen del invitado. El carrito hoy no muestra el envío: pasa a mostrar «Envío» con el costo o «Gratis» |
| 2 | Qué dice | «Te faltan $ X para el envío gratis» con la barra llena en la proporción del subtotal sobre el monto mínimo. Al alcanzarlo: «Tenés envío gratis» con la barra completa |
| 3 | Contra qué mide | El subtotal de los productos a precio con oferta, antes del canje: lo mismo que decide el envío (B-07-033) |
| 4 | Accesibilidad | `role="progressbar"` con `aria-valuenow`, `aria-valuemin` y `aria-valuemax`, y el texto al lado: la barra no es la única forma de enterarse |
| 5 | En vivo | En el carrito, la barra se recalcula con el resto cuando cambia una cantidad (B-07-028), porque viaja en el mismo parcial |
| 6 | Estilo | Sólo tokens de la guía; sin animación fuera del catálogo de la guía |

---

# Plan — `07` Tienda Online · octava parte: retiro en el local

**Estado del plan:** Aprobado el 2026-10-19, con las recomendaciones de la sección 3 · **Fecha:** 2026-10-19

**Cambio de alcance pedido por el responsable** (2026-10-19): en la compra online, además del envío
a domicilio, el Cliente puede elegir **retirar el pedido en el local**. El pedido para retirar se
reutiliza sobre el stock en local (módulo 18), que hasta hoy sólo recibía el artículo de despacho
diferido. Cuatro decisiones del responsable, tomadas antes del plan:

| # | Decisión |
| --- | --- |
| D1 | Es un **flujo alternativo de `CU-TDA-CMP`**, y RF-25 se enmienda para que el stock en local tenga dos orígenes. Sin caso de uso ni contratos nuevos: se enmiendan los existentes |
| D2 | El pedido queda listo para retirar **cuando el local lo arma**, no al aprobarse el pago |
| D3 | Si no se retira dentro del plazo de retención, **vuelve al stock con reembolso en puntos** (RF-25 (4) cambia sólo para este origen) |
| D4 | **Sólo con cuenta**: el invitado no tiene «Mi cuenta» donde ver lo guardado |

---

## 1. Qué cubre

Ningún contrato nuevo. Se enmiendan los que el flujo atraviesa:

| Contrato | Qué gana |
| --- | --- |
| `CO-180 iniciarCheckout`, `CO-087 declararDireccionDeEnvio` | La modalidad de entrega: envío a domicilio o retiro en el local. Con retiro no se pide dirección y el envío cuesta cero |
| `CO-088 confirmarPedido`, `CO-089 registrarResultadoDePago` | El pedido nace con su modalidad. Con retiro, `costo de envío = 0` y sin dirección |
| `CO-092 avanzarEstadoDePedido` | Un pedido para retirar pasa de Armado a **En el local**: cada unidad entra al stock en local del Cliente, y se le avisa que puede retirarlo |
| `CO-154 ejecutarCicloDeVencimientoDeRetencion` | Un artículo de un pedido para retirar que vence vuelve al stock **con reembolso en puntos** (D3) |
| `CO-215`, `CO-217`, `CO-218` | Muestran el origen nuevo: «Pedido para retirar» |
| `CO-227 confirmarRetiroEnLocal` | Sin cambios de efecto; la ficha del pedido ofrece entregarlo entero (ambigüedad 5) |

Los casos de uso que se mueven: `CU-TDA-CMP` (alternativo nuevo), `CU-PED-EST` (el estado nuevo),
`CU-STK-*` (el origen nuevo) y `CU-STK-VEN` (el reembolso).

---

## 2. Conceptos que toca

| Concepto | ¿Existe? | Qué hace este plan con él |
| --- | --- | --- |
| `Pedido` | Sí | Gana **modalidad de entrega** {Envío a domicilio, Retiro en el local} y el estado **En el local** (DME-07). Restricción en la base: un pedido para retirar es de una cuenta y no cobra envío |
| `ArticuloRetenido` | Sí | Gana **origen** {Despacho diferido, Pedido para retirar}: el vencimiento decide por él (D3) |
| `LineaPedido` | Sí | Ambigüedad 2 |
| `LotePuntos`, `MovimientoPuntos` | Sí | El reembolso del vencimiento (D3) |
| `CobroEnCurso` | Sí | Congela la modalidad junto con lo demás (B-07-034) |

---

## 3. Ambigüedades detectadas

| # | Dónde | Las dos lecturas | Qué se necesita para destrabarla |
| --- | --- | --- | --- |
| 1 | **El estado del pedido después de armarlo.** DME-07 termina en Despachado | **(a)** Un estado terminal nuevo, **En el local**: el pedido se cierra ahí y el seguimiento sigue en el stock en local, artículo por artículo, como el despacho diferido (B-18-003). **(b)** Que el pedido espere a que se retiren todos sus artículos para cerrarse | **Recomiendo (a)**: un artículo puede retirarse, enviarse o vencer por separado, y el pedido no tiene por qué esperar al último |
| 2 | **El estado de las líneas** al pasar a En el local | **(a)** Quedan como están, igual que en el despacho diferido (B-18-003). **(b)** Un estado nuevo de línea | **Recomiendo (a)** |
| 3 | **Las pre-ventas en un pedido para retirar** | **(a)** Lo de hoy: el pedido espera en «Esperando stock de pre-venta» hasta que llega todo, y después se arma. Si una pre-venta se demora, las opciones de `CU-PED-OPC` siguen valiendo: la opción 2 pasa a decir «retirá ya lo disponible; lo demorado queda guardado cuando llegue», y entra por el camino que ya existe. **(b)** Otra regla para retiro | **Recomiendo (a)**, con los textos de las opciones adaptados a la modalidad |
| 4 | **Las devoluciones de lo retirado.** `CU-DEV-SOL` exige un pedido Despachado y cuenta el plazo desde el despacho (B-09-002); un pedido para retirar nunca se despacha | **(a)** Una línea se puede reclamar desde que se retiró (o se despachó desde el stock en local) alguna de sus unidades, con el plazo contado desde ese momento. **(b)** Lo retirado no admite reclamo por el sistema: se revisa en el mostrador | **Recomiendo (a)**: el derecho del Cliente es el mismo, retire o reciba |
| 5 | **Entregar el pedido entero en el mostrador.** `CO-227` entrega un artículo | **(a)** La ficha del pedido y la del stock en local ofrecen «Entregar todo», que aplica `CO-227` a cada artículo disponible, verificando al titular una sola vez, como el despacho de una solicitud entera (B-18-007). **(b)** De a uno | **Recomiendo (a)** |
| 6 | **El valor del reembolso al vencer** (D3) | **(a)** La regla de los demás reembolsos (B-01-010, B-09-004): el valor de la unidad a puntos hacia arriba; lo pagado con puntos devuelve su parte. **(b)** Otra | **Recomiendo (a)** |
| 7 | **El Cliente que cambia de idea** y quiere que se lo envíen | **(a)** Pide el envío desde «Stock en local» como cualquier artículo guardado (`CO-151`): gratis desde el monto mínimo o pago. **(b)** No se admite | **Recomiendo (a)**: no hay nada que construir |
| 8 | **El checkout con retiro.** La barra del envío gratis (séptima parte) y la dirección | **(a)** Con retiro, la dirección no se pide ni se muestra, el envío dice «Retiro en el local · sin costo» y la barra no aparece. Se puede volver a envío a domicilio antes de confirmar | **Recomiendo (a)** |

---

## 4. Orden de construcción

| # | Qué | Depende de | Motivo |
| --- | --- | --- | --- |
| 1 | La modalidad y el estado En el local en `Pedido`; el origen en `ArticuloRetenido`, con migración (lo existente es despacho diferido o envío a domicilio) | — | Todo lo demás los lee |
| 2 | El checkout con la modalidad (`CO-180`, `CO-087`, `CO-088`) y el pedido que nace con ella (`CO-089`) | 1 | |
| 3 | Armado → En el local, con el ingreso al stock en local y el aviso (`CO-092`) | 1 | |
| 4 | Entregar todo en el mostrador (ambigüedad 5) y el origen en las consultas (`CO-215`, `CO-217`, `CO-218`) | 3 | |
| 5 | El vencimiento con reembolso (`CO-154`, D3) | 3 | |
| 6 | Las devoluciones de lo retirado (ambigüedad 4) | 4 | Toca el módulo 09 |

---

## 5. Riesgos

| Riesgo | Dónde | Cómo se cubre |
| --- | --- | --- |
| Romper la compra a domicilio, que está verificada | `CO-087` a `CO-089` | La modalidad por defecto es envío a domicilio; la suite de la compra corre sin cambios |
| Un invitado elige retiro por la dirección del formulario | `CO-091` | Se rechaza en el servidor (D4), y la restricción de la base lo impide |
| Armar dos veces un pedido para retirar duplica artículos | `CO-092` | El pedido se toma con bloqueo y se compara el estado visto, como hoy; prueba de doble envío |
| El vencimiento reembolsa dos veces o reembolsa un despacho diferido | `CO-154` | Transacción por artículo con bloqueo; prueba de doble corrida y de los dos orígenes |
| El reembolso del vencimiento se equivoca de valor | `CO-154` | Pruebas con una unidad pagada en dinero y otra con puntos |
| Un pedido para retirar entra al flujo de despacho | `CO-092` | El siguiente estado depende de la modalidad; prueba de que nunca pasa a Empaquetado |

---

## 6. Fuera de alcance

- **Pagar en el local**: el pago sigue siendo online, por la pasarela o con puntos.
- El retiro para invitados (D4).
- Elegir otra sucursal: el local es uno.

---
---

# Plan — `07` Tienda Online · novena parte: el escaparate vivo

**Estado del plan:** Aprobado el 2026-11-11, con las recomendaciones de la sección 3 · **Fecha:** 2026-11-11

**Pedido del responsable** (2026-11-11): la tienda «está muy plana y poco llamativa, hay que hacerla
una experiencia». Que el diseño de la portada admita, además de las filas de productos, **filas o
carruseles de fotos** que se ordenen igual que ellas, **una fila de botones con foto debajo de las
novedades** que lleve directo a un grupo de productos, más imágenes y más animaciones. Inspiración:
tiendas existentes, Viñeta Nocturna y la estética de Zenless Zone Zero (dos conceptos de Figma en
`.contexto-ia/referencias-pantallas/`). Condición explícita: **se puede cambiar todo el diseño
siempre que la funcionalidad construida quede igual o mejor.** El modo operativo no se toca.

**Segunda vuelta del responsable** (2026-11-11, sobre la primera maqueta): vigilar que nada de lo
que funciona se rompa (los botones de agregar al carrito, entre otros); **se admiten esquinas
redondeadas, verde lima, desenfoques y animaciones si son coherentes**; quitar las cifras del
hero («a un cliente no le interesa»); arreglar el pie; mejorar la barra de arriba con íconos; y
sumar lo **retro, musical y de VHS** de la referencia.

Antes del plan se armó una maqueta navegable con datos e imágenes reales del sistema, con los
tokens y las fuentes del repositorio, que replica también la cáscara pública de hoy (encabezado,
tarjeta, cajón del carrito, avisos, globo de ayuda y pie) con su comportamiento. Las decisiones
visuales de este plan salen de su segunda versión.

## La regla de forma y de color del escaparate

Para que lo redondeado y el lima no queden sueltos, una sola regla:

| | Los aparatos | Lo impreso |
| --- | --- | --- |
| **Qué es** | La barra de arriba, el televisor, los controles de cinta, la botonera, el riel, el globo de ayuda, el cajón del carrito | Portadas, tarjetas de producto, viñetas, fotos, títulos de sección, papel |
| **Forma** | Redondeada (16px los contenedores, píldora los botones) | Recta, con cortes y sombras duras, como hoy |
| **Color propio** | **Lima** para «encendido / reproduciendo / elegido» | El acento de siempre |
| **Desenfoque** | Detrás de la barra fija y del telón del cajón | Nunca |

El **naranja sigue siendo la acción** (agregar, reservar, comprar, buscar) en las dos familias.

## Qué se tomó de las referencias, y qué no

| De la referencia | Cómo entra en LongBox |
| --- | --- |
| El televisor retro con perillas y un collage de viñetas | El carrusel de banners pasa al hero, dentro de un **televisor** con pantalla en VHS («▶ PLAY · SP», contador, «CH 01»), perillas, botones de canal y controles de cinta; el cambio de banner es un **cambio de canal** con una banda de ruido |
| La barra en pestañas: marca, botonera de íconos, el actual encendido | La **barra de arriba**: pestaña de marca, buscador en píldora y botonera de íconos con su nombre al pasar; el actual en lima |
| Lo retro y musical: VHS, cintas, ecualizadores | El ticker pasa a **«En rotación»** con un ecualizador; los títulos de sección son **lomos de cinta** numerados; los accesos llevan rótulo de cinta («● CINTA 01»); la vitrina, controles de reproductor; el pie, **«■ STOP · Fin de la cinta»** y «◀◀ Rebobinar»; líneas de barrido muy tenues sobre todo el escaparate; el título del hero con el corrimiento de color de una cinta gastada |
| La tarjeta de personaje: bloque de color en diagonal, número gigante rayado, figura que desborda las dos bandas, selector de miniaturas | La **vitrina**: un producto destacado con su número, la portada desbordando, y miniaturas para cambiarlo |
| Retratos recortados en paralelogramo (selector de personajes) | Los **accesos con foto**: paneles inclinados que encastran |
| El texto gigante cortado al pie de cada marco | El nombre de la tienda en contorno, detrás del hero, que se corre con el desplazamiento |
| El riel lateral con el número de la sección y flechas | El **riel de secciones** en escritorio |
| Las esquinas redondeadas y el verde lima | **Entran con una regla** (la tabla de arriba): sólo en los aparatos |
| Los íconos, logos, personajes y nombres del juego | **No entran**: los íconos son los de `_iconos.html` más dos nuevos (inicio y pre-ventas), y nada remite a una marca (`identidad_visual.md`, «Inspiración, no copia») |

## Lo que no se puede romper

La cáscara pública de hoy, entera. Cada punto se verifica en el sistema con su prueba o su captura
antes de cerrar cada paso:

- **Barra de arriba:** la marca y el logo configurables; el buscador con sus sugerencias desde la
  segunda letra, las flechas, Enter, Escape y el atajo «/»; el saldo de puntos del Cliente; el
  carrito con su contador, que rebota al agregar, y que no aparece para el personal; el menú de
  cuenta (correo, mis pedidos, mis puntos, mis datos, mi carrito, preguntas frecuentes, cerrar
  sesión por POST) o «Ingresar»; la barra que se compacta al bajar.
- **Tarjeta de producto:** los rótulos Disponible, Pre-venta y Sin stock; los carteles «¡TOMO 1!» y
  «¡NOVEDAD!»; la tapa dibujada sin imagen; la oferta con el precio anterior tachado; la fecha de
  llegada de la pre-venta; el botón **Agregar** o **Reservar** fuera del enlace, que no aparece sin
  stock ni para el personal; la portada que vuela a la ficha.
- **Al agregar:** el cajón del carrito con lo agregado, las unidades, el total, lo que falta para el
  envío gratis, «Ir al carrito» y «Seguir comprando»; el aviso «Listo:»; y si el guion falla, el
  formulario se envía como siempre.
- **El resto:** el globo de preguntas frecuentes, que se pliega al bajar y no aparece sin
  contenido; el ticker y el carrusel pausables; las filas con sus flechas y su barra de recorrido;
  «Lo que se viene»; los mensajes.
- **Pie:** el **botón de arrepentimiento** a la vista (Res. 424/2020); los accesos de la tienda; la
  ayuda; el correo, el teléfono y las redes de la identidad visual; «Volver arriba».

---

## 1. Qué cubre

| Caso de uso | Qué cambia | Contratos |
| --- | --- | --- |
| `CU-CFG-FIL` Administrar Filas de la Portada (código del 2026-11-08, sin ficha todavía; `NUEVO-CO-23 guardarFilasDeLaPortada`) | Pasa de filas de productos a **secciones de la portada** de varios tipos, en un único orden (ambigüedad 1) | `NUEVO-CO-23`, ampliado |
| `CU-TDA-POR` Consultar la Portada de la Tienda (sin ficha todavía) | Dibuja las secciones por tipo y en su orden; el hero suma el televisor | Sólo lectura |
| `CU-CFG-BNC` Consultar Banners | **Ninguno de efecto.** La galería se ve en el televisor del hero en lugar de una sección propia; intervalo, «Anterior», «Siguiente», «Pausar», indicadores y movimiento reducido quedan como están | `CO-132`, sin cambios |
| `CU-TDA-CAT` Consultar Catálogo Público | **Ninguno.** Los accesos y las imágenes llevan a filtros que el catálogo ya tiene (etiqueta, grupo, tipo, editorial, pre-venta) | `CO-176`, `CO-177`, sin cambios |
| Agregar al carrito desde la tarjeta | La vitrina usa el mismo camino que las tarjetas | `CO-083`, sin cambios |

**Total:** un contrato ampliado (todavía sin número definitivo) y ninguno modificado.

---

## 2. Conceptos que toca

| Concepto | ¿Existe? | Qué hace este plan con él |
| --- | --- | --- |
| `SeccionPortada` | **No** | Lo crea y **absorbe a `FilaPortada`**: tipo, título, antetítulo, orden, activa. Las filas de hoy pasan por migración de datos con su orden, título, imagen y estado |
| `ImagenDeSeccion` | **No** | Lo crea: imagen (RNF-05), título, texto, destino (ambigüedad 4) y orden dentro de su sección |
| `FilaPortada` | Sí | Se reemplaza; la tabla se quita en una segunda migración, después de copiar |
| `Banner`, `IdentidadVisual` | Sí | Sólo los lee (el televisor; los textos del hero) |
| `Etiqueta`, `GrupoEtiqueta`, `Tipo`, `Editorial`, `Producto` | Sí | Los lee: origen de las secciones de productos y destino de las imágenes |
| `RegistroAuditoria` | Sí | Una acción nueva: «Modificación de las secciones de la portada». Los registros viejos conservan la suya |

**Los tipos de sección.** Cada tipo cambia lo que el sistema muestra, así que es un campo y no
una etiqueta (regla 3 del dominio):

| Tipo | Qué es | Qué carga el Administrador |
| --- | --- | --- |
| **Productos** | La fila de hoy, que se recorre de costado, o la **vitrina** (campo *presentación*) | Etiqueta **o** grupo, como hoy |
| **Accesos con foto** | De 3 a 8 paneles inclinados con foto, nombre y cuántos productos hay | Una imagen por acceso, con su nombre y su destino |
| **Página de historieta** | De 3 a 6 viñetas de tamaños distintos, con recuadro de narración o globo | Una imagen por viñeta, con texto opcional y destino opcional |
| **Cinta de fotos** | Fotos con marco que corren de costado, pausables | De 4 a 12 imágenes con su epígrafe |
| **Panel destacado** | Una imagen grande y un llamado con botón, partido en diagonal | Una imagen, título, texto y destino |
| **Recién llegados** · **Lo que se viene** | Las dos secciones de hoy | Nada: el sistema las arma. Se mueven y se apagan, no se borran |

La restricción de hoy («etiqueta o grupo, nunca los dos») sigue en la base, ahora condicionada al
tipo Productos. La cantidad de imágenes por tipo se valida en el servidor.

---

## 3. Ambigüedades detectadas

| # | Dónde | Las dos lecturas | Qué se necesita para destrabarla |
| --- | --- | --- | --- |
| 1 | **El caso de uso.** `CU-CFG-FIL` nació para filas de productos y su ficha no está escrita | **(a)** Se amplía y se renombra **«Administrar Secciones de la Portada»**, con el código **`CU-CFG-SEC`** (verificado libre contra los vigentes y los retirados); `CU-CFG-FIL` queda retirado sin haber llegado al documento. El contrato pasa a `guardarSeccionesDeLaPortada`. **(b)** Se conserva `CU-CFG-FIL` con su nombre y las secciones nuevas se describen como filas de otro tipo | **Recomiendo (a)**: «filas» deja de describir lo que hace, y renombrarlo ahora cuesta una línea de `CODIGOS.md`. El número del contrato se confirma con el responsable |
| 2 | **El carrusel en el hero.** Hoy es una sección aparte debajo del ticker | **(a)** Pasa al televisor del hero, con todos sus controles; sin banners, el televisor muestra la portada destacada de hoy. **(b)** Queda donde está y el hero conserva sólo la portada destacada | **Recomiendo (a)**: hoy el hero es texto sobre un fondo vacío y el carrusel queda debajo del pliegue |
| 3 | **El lima y la identidad configurable.** `TOKENS_VISUALES.md` reserva el lima (`--ok`) al modo operativo, y el mapa de colores (B-17-019) no tiene un rol para él | **(a)** Un rol nuevo, **«Aparatos encendidos»** (`--rol-encendido`), con el lima como valor inicial y elegible entre los colores de la paleta como los demás roles; el modo operativo sigue con su `--ok`. **(b)** El lima fijo, fuera de la identidad configurable | **Recomiendo (a)**: si el Administrador cambia la paleta, el lima no queda desentonando. Requiere la enmienda de los tokens (ambigüedad 8). *Las cifras del hero que se proponían acá se descartaron en la segunda vuelta* |
| 4 | **El destino de una imagen** o de un acceso | **(a)** Una lista cerrada: etiqueta, grupo, tipo, editorial, pre-ventas, un producto o sin enlace; cada uno lleva al filtro del catálogo o a la ficha que ya existen, y el servidor rechaza cualquier otra cosa. **(b)** Una dirección libre | **Recomiendo (a)**: la restricción vive en el servidor y no hay enlaces rotos ni salidas a otros sitios |
| 5 | **Un destino que no muestra nada** (etiqueta dada de baja, producto descatalogado, filtro sin productos visibles) | **(a)** Ese acceso o esa imagen no se dibuja, como la fila sin productos de hoy (decisión 2 de la tercera parte). **(b)** Se dibuja sin enlace | **Recomiendo (a)** para accesos y productos; las viñetas y fotos sin destino válido se muestran sin enlace |
| 6 | **Texto alternativo** de las imágenes nuevas | **(a)** El título es obligatorio en accesos y en la cinta y sirve de alternativo; las viñetas sin texto son decorativas (`alt=""`). **(b)** Un campo propio de texto alternativo | **Recomiendo (a)** |
| 7 | **Superficie de cada sección** (noche o papel) | **(a)** La alterna el sistema según la posición, como páginas de una revista. **(b)** La elige el Administrador | **Recomiendo (a)**: dos noches seguidas no pierden la unión diagonal ni la cinta |
| 8 | **Enmiendas a la guía visual.** `TOKENS_VISUALES.md` prohíbe el radio, el lima en el público y el desenfoque fuera del `<dialog>`, y `identidad_visual.md` no admite animaciones fuera de su catálogo | Se piden, para que el responsable las agregue a los dos documentos: **la regla de aparatos e impresos** (radios `--radio-aparato` 16px y píldora; lima por `--rol-encendido`; desenfoque de 12px detrás de la barra fija); los patrones **barra de aparato**, **televisor**, **radio** (ticker con ecualizador), **lomo de cinta**, **vitrina con reproductor**, **acceso inclinado**, **página de viñetas**, **foto con cinta**, **riel de secciones** y **pie «fin de la cinta»**; las animaciones **`cambio-canal`** (la imagen entra por bandas en tres cuadros, `--dur-4`, `--curva-cuadro`; reducido: cambio instantáneo), **`banda-ruido`** (una franja de ruido cruza la pantalla una vez por cambio, 700ms; reducido: no ocurre), **`tracking`** (el título del hero se corre por bandas al pasar el puntero, como `titulo-glitch`; reducido: no ocurre), **`texto-deriva`** (atada al desplazamiento, nunca se mueve sola; reducido: quieta), **`vitrina-entra`** (la portada entra 40px desde la derecha, `--dur-3`; reducido: aparece) y **`cajon-entra`** (el cajón del carrito entra 40px desde la derecha, `--dur-3`). El ecualizador reutiliza `barras-carga`, la cinta de fotos `ticker` y la página `barrido-diagonal`; el ecualizador se detiene con la radio | **Aprobación de la lista**; mientras tanto se registra como agregado en la bitácora |
| 9 | **Proporción del acento** (10 % de la pantalla) | **(a)** El bloque de color de la vitrina y la marca del acceso bajo el puntero cuentan; la vitrina usa el acento sólo en el bloque del número, y el resto en neutros. **(b)** Se relaja la regla para el escaparate | **Recomiendo (a)** |

---

## 4. Orden de construcción

| # | Qué | Depende de | Motivo |
| --- | --- | --- | --- |
| 1 | `SeccionPortada` e `ImagenDeSeccion`, la migración de datos desde `FilaPortada` y las dos secciones fijas | — | Todo lo demás los lee. Las pruebas de las filas de hoy tienen que seguir en verde sobre el modelo nuevo |
| 2 | El gestor: «Secciones de la portada» con «Agregar sección» por tipo, la tarjeta de cada tipo y las imágenes de una sección como sub-tarjetas que también se arrastran | 1 | Mismo componente que hoy (B-07-010); el operativo no cambia de estilo |
| 3 | La cáscara: la barra de arriba con la botonera de íconos, el pie, el globo de ayuda, el cajón del carrito y el rol `--rol-encendido` | — | Se ve en todas las pantallas de la tienda, no sólo en la portada; se verifica contra la lista de lo que no se puede romper |
| 4 | La portada que dibuja por tipo y en orden; el hero con el televisor y el texto de fondo; la radio | 1, 3 | `CU-TDA-POR` |
| 5 | Los cinco tipos nuevos en el escaparate: accesos, vitrina, página, cinta y panel | 4 | Uno por vez, cada uno con su captura en escritorio y a 390 px |
| 6 | Lomos de cinta, riel de secciones, líneas de barrido y animaciones (ambigüedad 8) | 5 | Lo último: es lo que más se puede recortar si falta tiempo |
| 7 | El hueco de papel debajo de «Recién llegados» cuando hay pocos productos | 4 | Se ve en la captura del estado actual |

**Pruebas.** El contrato ampliado, por sus postcondiciones: secciones creadas, ordenadas, apagadas
y borradas; imágenes con su destino; la auditoría. Las negativas: un destino fuera de la lista, un
tipo con más o menos imágenes de las admitidas, una sección fija que se intenta borrar, una
sección de productos con etiqueta y grupo a la vez, y que nada de lo que dibuja la portada sea un
producto que el catálogo no mostraría. El rol equivocado entra por la dirección real del gestor.

---

## 5. Riesgos

| Riesgo | Dónde aparece | Cómo se cubre |
| --- | --- | --- |
| **La entrega es el 15/11** y el documento está en pleno ciclo de sincronización | Todo el plan | Los pasos 1 a 5 son el núcleo; el 6 y el 7 se recortan si hace falta. El impacto en el documento es la ficha de un caso de uso que todavía no está escrita (ambigüedad 1) |
| **Romper algo que funciona al cambiar la cáscara** (pasó en la primera maqueta con los botones de agregar) | Pasos 3 a 5 | La lista de lo que no se puede romper, punto por punto, con la suite de la tienda en verde y capturas del cajón, las sugerencias, el menú de cuenta y una tarjeta de cada estado, en escritorio y a 390 px. Las clases y los atributos `data-*` que leen los guiones de hoy no cambian de nombre |
| Perder filas configuradas al migrar | Paso 1 | Migración de datos con prueba sobre filas existentes; la tabla vieja se quita en una migración aparte, y se verifica a mano sobre la base de desarrollo |
| Romper la portada pública, que está verificada | Paso 3 | La suite de la tienda corre sin cambios de comportamiento; capturas antes y después |
| Que una paleta configurada deje ilegible algo nuevo | Pasos 3 y 4 | Los componentes nuevos leen sólo semánticos y roles del mapa de colores (`--acento`, `--rol-*`), nunca `--senal` directo; captura con una paleta distinta de la inicial |
| Muchas consultas en la portada (una cuenta por acceso, una lista por sección) | Paso 3 | Cuentas agrupadas en una consulta por tipo de destino; tope de secciones activas; prueba que cuenta consultas |
| Movimiento que no se puede detener | Pasos 4 a 6 | La radio, la cinta de fotos y el televisor se pausan con el puntero, el foco y un botón; `prefers-reduced-motion` los apaga (regla 7) |
| Que las líneas de barrido o el corrimiento de color dificulten leer | Paso 6 | Las líneas van a 10 % de opacidad y nunca sobre texto corrido; el corrimiento de color sólo en el título del hero; se revisa el contraste con ellas puestas |
| La hoja de estilos vieja en caché del navegador | Pasos 3 a 7 | La hoja sube de versión, como en el plan 00 de interfaz |

---

## 6. Fuera de alcance

- La ficha de producto, el catálogo y la cuenta del Cliente con el lenguaje nuevo: es la segunda
  etapa natural de este pedido y conviene planearla aparte, después de la entrega.
- Secciones con vigencia (que aparezcan y desaparezcan solas por fecha).
- Video en las secciones.
- Editar la portada arrastrando sobre la propia portada: el gestor sigue en el operativo.
- Fotos subidas por los clientes.
