> **Tipo: Normativo** una vez aprobado. Antes de la aprobación es una propuesta.
> Se escribe **antes** de programar y **no se reescribe** después: si algo cambió durante la
> construcción, eso va a la bitácora del módulo, no acá.

# Plan — `00` Pulido de interfaz

**Estado del plan:** Aprobado el 2026-10-21: ambigüedades 1 a 3 en (a), 4 con recursos de Uiverse.io u otros sitios de licencia libre, 5 y 6 aprobadas. Las mejoras del apartado 5 quedan sin elegir · **Fecha:** 2026-10-21

No es un caso de uso y no agrega contratos. Mejora cómo se ven y se usan pantallas que ya existen,
dentro de Viñeta Nocturna (`.contexto-ia/identidad_visual.md`, `.contexto-ia/TOKENS_VISUALES.md`).
Incluye un defecto funcional encontrado al revisar «Mi cuenta» (apartado 1, punto 1), que se
corrige primero.

Pasa por las puertas que le corresponden: suite, cobertura, análisis estático, formato y la prueba
del estilo (`apps/core/tests/test_estilo_vineta.py`). Ninguna operación cambia de dirección ni de
efecto, así que las pruebas de contratos siguen igual.

---

## 1. Qué cubre

| # | Pedido del responsable | Qué se hace |
| --- | --- | --- |
| 1 | Los pedidos para retirar no aparecen en «Mi cuenta» | **Defecto.** `Pedido.EN_LOCAL` no está ni en `ACTIVOS` ni en el filtro del historial (`apps/accounts/views_cuenta.py:65` y `:79`), así que el pedido desaparece de las dos listas. Se agrega donde corresponda (ambigüedad 1) con su prueba |
| 2 | El selector de entrega del checkout es feo | Hoy son dos botones de jerarquías distintas que se turnan (`boton-seccion` y `boton-texto`). Pasan a ser **dos tarjetas de opción**: botones de opción nativos con ícono, título y una línea con el costo. Ver 4.1 |
| 3 | Corregir el uso de los botones | Auditoría de las acciones que envían con `boton-texto` o `boton-menor` y de los `<a>` con `boton-primario`. Hallazgos y propuesta en el apartado 3 |
| 4 | Seguimiento del pedido con animación | **Riel de estados** en el pedido del cliente: los pasos con ícono (caja abierta, caja con cinta, camión, local), la fecha de cada paso alcanzado y el paso actual marcado. Un camión recorre el tramo hasta el estado actual una sola vez al cargar. Ver 4.2 |
| 5 | Mejorar la disposición de «Mi cuenta» | Dos columnas: un **carnet de cliente** fijo a la izquierda (nombre, código, saldo de puntos, artículos en el local) con la navegación debajo, y el contenido a la derecha. La portada de la cuenta pasa a ser un **resumen**. Ver 4.3 |
| 6 | Diálogos de confirmación en vez de pantallas | Las 18 pantallas de confirmación se abren en un `<dialog>` nativo sobre la pantalla actual, con el telón difuminado. Sin JavaScript se sigue navegando a la pantalla de siempre. Ver 4.4 |
| 7 | Otras mejoras | Propuestas en el apartado 5, para elegir |

### Las 18 confirmaciones que pasan a diálogo

Las que hoy son una pantalla entera con un texto y un botón:

| App | Pantallas |
| --- | --- |
| `pedidos` | Avanzar el pedido, confirmar el ingreso, cancelar la pre-venta |
| `accounts` | Dar de baja un usuario, eliminar un usuario |
| `catalog` | Dar de baja un producto, reactivarlo, restaurar el precio calculado, eliminar un precio, dar de baja una oferta, dar de baja un catálogo |
| `suppliers` | Dar de baja un proveedor, reactivarlo |
| `core` | Dar de baja un banner |
| `almacen` | Retirar del stock en local, retirar un pedido |
| `devoluciones` | Reembolsar en puntos, reembolsar por el medio de pago |

---

## 2. Conceptos que toca

Ninguno del modelo de dominio. Las vistas y las direcciones de las operaciones no cambian, salvo
el punto 1, que cambia qué pedidos lista `CU-CLI-HIS` y lleva su entrada en
`bitacora/11-cuenta-de-cliente.md`.

---

## 3. Auditoría de botones

Se aplica la jerarquía que ya está vigente (`identidad_visual.md`, «Botones»): `boton-primario`
para la acción principal, `boton-seccion` para la acción de un bloque, `boton-menor` para la de una
fila y `boton-texto` para navegar.

| Dónde | Hoy | Problema | Propuesta |
| --- | --- | --- | --- |
| Checkout, entrega | Dos botones que alternan `boton-seccion` y `boton-texto` | Una elección se dibuja como dos acciones de distinto peso | Tarjetas de opción (4.1) |
| Checkout, «Cubrir con N pts» sin saldo | `boton-menor` naranja al lado de «No alcanza el saldo» | Se ve disponible y no lo está | Estado **deshabilitado** del sistema: borde punteado, `--texto-2` y la razón |
| Carrito, «Quitar» | `boton-texto--critico` suelto al lado de la cantidad | Se confunde con un rótulo de la cantidad | Ícono de tacho + «Quitar» en `boton-menor--critico`, alineado con el importe |
| «Mi cuenta», «Cambiar el correo» y «Cambiar la contraseña» | `boton-texto` | Son acciones del bloque, no navegación | `boton-seccion--tenue` |
| Mostrador, fila del ítem | «Canjear» en `boton-menor` y «Quitar» en `boton-texto--critico` | Dos niveles para acciones de la misma fila | Las dos `boton-menor`; «Quitar» con `--critico` |
| Propuesta de restock, fila del ítem | «Guardar» y «Quitar» envían con `boton-texto` | Una acción que envía se dibuja como navegación | `boton-menor` y `boton-menor--critico` |
| Resultado del pago aprobado | «Seguir comprando» es el `boton-primario` | Lo que el cliente busca después de pagar es su pedido | «Ver mi pedido» primario y «Seguir comprando» `boton-texto` |

Se agrega a `test_estilo_vineta.py` una regla nueva: **un `<button type="submit">` no lleva
`boton-texto`**. La única excepción son los controles del carrusel y del menú, que no envían nada.
Si la regla se aprueba, la tiene que agregar el responsable a `identidad_visual.md` (apéndice A).

---

## 4. Cómo se ve cada pieza

### 4.1 Selector de entrega

```
 ENTREGA
 ┌────────────────────────────┐  ┌────────────────────────────┐
 │ ▣  [camión]                │  │ □  [local]                 │
 │    ENVÍO A DOMICILIO       │  │    RETIRO EN EL LOCAL      │
 │    $ 1.500 · gratis desde  │  │    Sin costo · te avisamos │
 │    $ 50.000                │  │    cuando esté listo       │
 └────────────────────────────┘  └────────────────────────────┘
   elegida: fondo --acento-suave, borde --acento, esquina con «✓» sesgada
```

Son `<input type="radio">` nativos dentro de `<label>`. Al cambiar la opción, el formulario se envía
solo. Sin JavaScript aparece un botón «Usar esta entrega». La opción de retiro no aparece para el
invitado (D4 del plan 07, octava parte).

### 4.2 Riel de estados del pedido

```
  [caja]──────[caja+cinta]──────[camión]──────[✓]
  PENDIENTE    ARMADO            EMPAQUETADO     DESPACHADO
  21/10 10:02  21/10 15:40       ◆ ahora
  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━▶ 🚚 (recorre el tramo una vez)
```

- Los pasos salen de `SIGUIENTE` o `SIGUIENTE_RETIRO`, según la modalidad. El retiro termina en
  «En el local», con el ícono del local en vez del camión.
- Un paso alcanzado muestra su fecha, el actual lleva el rombo `--acento` y los pendientes van en
  `--texto-2` con borde punteado.
- **Movimiento:** la barra se llena hasta el paso actual (`scaleX`) y el camión la recorre una sola
  vez, en `--dur-5` con `--curva-golpe`. Al llegar, el paso actual recibe un **sello** (escala de
  1,3 a 1 con un giro de −6°, como un sello sobre papel).
- Con movimiento reducido, todo aparece ya en su lugar.
- Cancelado y Esperando pre-venta o demorado no son pasos. Son un rótulo con `--cinta` encima del
  riel, con la palabra del estado.
- Se usa en «Mi cuenta» (pedido y tarjetas de la lista, en una versión reducida sin animación) y,
  sin animación, en la línea de tiempo del pedido en el operativo.

### 4.3 «Mi cuenta»

```
 ┌──────────────── CARNET ───────────────┐  ┌──────────── RESUMEN ────────────────────┐
 │ RAMONA QUIROGA                         │  │ PEDIDOS EN CURSO                         │
 │ CÓDIGO  380394   (mono, grande)        │  │  000025 ▸ riel reducido · $ 50.500       │
 │ ▮▮▮ 1200 PTS · vencen 120 el 08/05     │  │  000026 ▸ riel reducido · $ 10.500       │
 │ ▮ 2 artículos en el local · hasta 30/10│  │ LISTO PARA RETIRAR                        │
 ├────────────────────────────────────────┤  │  000024 ▸ Stock en local                  │
 │ ▸ Resumen                              │  │ PUNTOS                                    │
 │   Pedidos                              │  │  1200 pts = $ 12.000 · próximos a vencer  │
 │   Puntos                               │  └──────────────────────────────────────────┘
 │   Stock en local                       │
 │   Mis datos                            │
 └────────────────────────────────────────┘
```

- El carnet es una tarjeta `--fondo-2` con `--forma-corte`, una franja de `--trama-rayas` arriba
  y el código de cliente en `--fuente-datos` grande, para dictarlo en el mostrador.
- «Pedidos activos» e «Historial» se juntan en **Pedidos**, con dos grupos en la misma pantalla.
  Las direcciones actuales se conservan: `cuenta:historial` sigue respondiendo.
- Cada pedido de la lista es una tarjeta con las portadas en miniatura (hasta 3 y «+N»), el riel
  reducido, el total y el rótulo de estado alineado a la derecha. Hoy el rótulo queda flotando en el
  medio.
- En el celular, el carnet se reduce a una franja con el código y los puntos, y la navegación pasa a
  pestañas con desplazamiento horizontal.

### 4.4 Diálogos de confirmación

- Un enlace a una pantalla de confirmación lleva `data-dialogo`. Al hacer clic, el guion pide esa
  misma página, toma el bloque marcado con `data-dialogo-contenido` y lo muestra en un `<dialog>`
  nativo con `showModal()`. El formulario se envía como siempre.
- **Sin JavaScript, o si el pedido falla, se navega a la pantalla de siempre.** Las pruebas de
  contratos, que usan esas direcciones, no cambian.
- El aspecto es el que ya define `identidad_visual.md` para los diálogos: fondo `--fondo-2`,
  `--trazo-fuerte`, `--sombra-golpe-2` en `--acento` y `dialogo-entra`. Los destructivos llevan la
  franja de `--cinta` y el botón `--critico`.
- El telón es `--noche` al 70 % con `--trama-rayas` y desenfoque (ambigüedad 2).
- El foco va al botón de cancelar al abrir. `Escape` y «Cancelar» cierran el diálogo. Al cerrar,
  el foco vuelve al enlace que lo abrió.
- Si el envío devuelve un error de validación (el rechazo de una devolución sin motivo), se ve en la
  pantalla completa, como hoy.

---

## 5. Otras mejoras propuestas

Para elegir. Ninguna toca reglas de negocio.

| # | Qué | Por qué |
| --- | --- | --- |
| P1 | **Pasos de la compra** arriba del carrito y el checkout: `01 Carrito · 02 Entrega · 03 Pago`, con el encabezado de paso que ya existe en el alta de lotes | El cliente sabe dónde está y cuánto falta |
| P2 | **Portada de reemplazo diseñada** para productos sin imagen: `--trama-puntos-grande`, el título en `--fuente-display` y la editorial, dentro del marco de viñeta | Hoy es un ícono gris sobre puntos y se ve roto en todas las listas |
| P3 | **Botón cargando** en todos los envíos públicos (pagar, guardar mis datos, arrepentimiento): «Procesando…» y la `--cinta` que corre (`cinta-corre`, ya en el catálogo) | Evita el doble clic en el pago y da respuesta inmediata |
| P4 | **Medidor de puntos** en el carnet y en Puntos: barra con cortes cada 1000 pts y la marca de lo que vence pronto | Hace visible el aviso de caducidad del plan 10 |
| P5 | **Estados vacíos con sticker**: un sticker en `--fuente-grito` («¡NADA POR ACÁ!») sobre la trama, con el texto informativo de siempre abajo y un `boton-seccion` a la acción que corresponde («Ver el catálogo») | El estado vacío lleva a algún lado. La voz del escaparate admite el sticker; el texto informativo sigue sobrio |
| P6 | **Tarjeta de producto, presión**: al hacer clic, la tarjeta «se hunde» (`translate(0,0)` sin sombra), como el botón primario | Respuesta táctil coherente con el sistema |
| P7 | **Fila del pedido en el operativo** con el riel reducido en la lista de pedidos | El Administrador ve de un vistazo en qué etapa está cada uno |

---

## 6. Ambigüedades detectadas

| # | Dónde | Las lecturas | Qué se necesita |
| --- | --- | --- | --- |
| 1 | Pedido «En el local» en «Mi cuenta» | **(a)** En los pedidos en curso mientras quede algo sin retirar, y en el historial después. **(b)** Siempre en el historial, como estado final. **Recomiendo (a).** Para el cliente, un pedido que está esperando que lo busque no terminó | Elección |
| 2 | Telón difuminado | `TOKENS_VISUALES.md` prohíbe `backdrop-filter` y la prueba del estilo lo rechaza. **(a)** Se permite **sólo en `::backdrop` del `<dialog>`**: 4px, más el `--noche` al 70 % y la trama. Donde el navegador no lo soporte, queda el telón opaco. **(b)** El telón que ya está especificado (`--noche` al 80 % con `--trama-rayas`), sin desenfoque. **Recomiendo (a)**, que es lo que pediste, acotado a ese único lugar | Elección. Con (a) hay que enmendar `TOKENS_VISUALES.md` (apéndice A) |
| 3 | Animaciones nuevas | El catálogo de `identidad_visual.md` está cerrado y la prueba lo hace cumplir. El riel necesita tres: `riel-llena`, `camion-avanza` y `sello` | Aprobación. El texto para agregarlas al catálogo está en el apéndice A |
| 4 | Recursos de Uiverse.io | Se toma de ahí el **patrón** de la tarjeta de opción y del camión, pasado por «La regla de adaptación» de `RECURSOS_VISUALES.md`: sin radios, sin sombras difusas, sólo tokens y con el crédito del autor en un comentario. El camión se dibuja con el ícono `truck` de Tabler, la familia que ya usa el sistema | Nada, salvo objeción |
| 5 | Inspiración en Zenless Zone Zero | `identidad_visual.md`, «Inspiración, no copia»: se toma el **lenguaje** (sellos, rieles de misión, carnets, cintas, cortes) y **ningún** nombre, logo, ícono ni tipografía del juego | Nada, salvo objeción |
| 6 | Juntar «Pedidos activos» e «Historial» | `CU-CLI-HIS` no fija cuántas pantallas hay. Se mantiene `cuenta:historial` como dirección (va al grupo del historial), así no se rompe ningún enlace de los correos | Confirmación |

---

## 7. Orden de construcción

| # | Qué | Depende de | Motivo |
| --- | --- | --- | --- |
| 1 | Defecto del pedido «En el local», con prueba y entrada de bitácora | — | Es funcional y lo ve el cliente hoy |
| 2 | Enmiendas a `.contexto-ia/` aplicadas **por el responsable** (apéndice A) y la prueba del estilo actualizada | Aprobación | Sin eso, la prueba del estilo rechaza las piezas 4 y 5 |
| 3 | Selector de entrega y auditoría de botones | 2 | Son chicas y fijan los patrones de la tarjeta de opción y del deshabilitado |
| 4 | Diálogos: el guion, el parcial y las 18 pantallas | 2 | Es mecánico una vez que existe el parcial |
| 5 | Riel de estados | 2 | Lo usan la pieza 6 y la línea de tiempo del operativo |
| 6 | «Mi cuenta» con carnet y resumen | 5 | Necesita el riel reducido |
| 7 | Las mejoras del apartado 5 que se elijan | 3 a 6 | — |
| 8 | Capturas de cada pantalla en escritorio y en celular, y las siete puertas | todo | La prueba no ve si una pantalla se entiende |

---

## 8. Riesgos

| Riesgo | Cómo se cubre |
| --- | --- |
| Un diálogo rompe el flujo sin JavaScript | El enlace es una dirección real. Una prueba verifica que cada pantalla de confirmación marca su `data-dialogo-contenido` y sigue respondiendo por sí sola |
| El riel muestra un paso que el pedido no recorrió | Sale de la tabla de transiciones del servidor (`SIGUIENTE` / `SIGUIENTE_RETIRO`) y de `TransicionDePedido`. No hay una lista de pasos escrita en la plantilla |
| Las pruebas que buscan texto en «Mi cuenta» | Se conservan los textos y las direcciones; las que cambian se revisan una por una |
| Se pasa el 10 % de naranja | Se revisa en las capturas. El carnet y el riel usan el acento sólo en el paso actual y en el saldo |

---

## 9. Fuera de alcance

- Cambiar los tokens de color, las fuentes o la escala.
- El seguimiento del paquete en el correo (límite declarado: nada más allá de «Despachado»).
- Un tema claro.

---

## Apéndice A — Enmiendas a los documentos del responsable

Este plan no edita `.contexto-ia/`. Si se aprueba, el responsable agrega a mano:

**`TOKENS_VISUALES.md`, «Forma», la línea de prohibidos** (sólo si se elige 2a):

> Prohibido: `box-shadow` con desenfoque, `border-radius`, gradientes suaves de color como fondo,
> `backdrop-filter` **salvo en el `::backdrop` de un `<dialog>`: `blur(4px)` sobre `--noche` al
> 70 % con `--trama-rayas`**.

**`identidad_visual.md`, «Catálogo de animaciones»**, tres filas:

| Nombre | Qué hace | Duración · curva | Dónde | Movimiento reducido |
| --- | --- | --- | --- | --- |
| `riel-llena` | `scaleX(0 → n)` de la barra del riel hasta el paso actual | `--dur-5` · `--curva-golpe` · 1 vez | Riel de estados del pedido, sólo en el público | Ya llena |
| `camion-avanza` | El ícono recorre la barra con `translateX` y frena de golpe en el paso actual | `--dur-5` · `--curva-golpe` · 1 vez | Riel de estados del pedido, sólo en el público | Quieto en el paso actual |
| `sello` | Escala 1,3 → 1 con giro a `--giro-sticker` y aparece | `--dur-2` · `--curva-resorte` · 1 vez | Paso actual del riel | Aparece |

**`identidad_visual.md`, «Botones»**, una regla (si se aprueba el apartado 3):

> Un `<button type="submit">` no lleva `.boton-texto`: enviar es una acción y se dibuja como
> acción. `.boton-texto` queda para navegar y para los controles que no envían.

**`identidad_visual.md`, «Formularios»**, un patrón:

> **Tarjeta de opción**: para elegir entre pocas opciones con consecuencias distintas (la entrega).
> `<input type="radio">` nativo dentro de un `<label>` con borde `--trazo-fuerte` `--borde-control`,
> ícono de 24px, título en `--pub-titulo-3` y una línea en `--pub-chico`. Elegida: fondo
> `--acento-suave`, borde `--acento` y «✓» en una esquina sesgada `--sesgo`.

---

# Segunda parte — revisión del 2026-10-21

**Estado:** Aprobada el 2026-10-21, toda salvo los atajos de teclado (13.2). Historial de ventas en (a). Las mejoras U1 a U5 y P1 a P7, aprobadas. La ambigüedad 4 (qué revisar de Restock) quedó sin respuesta: se aplica el apartado 14 · **Fecha:** 2026-10-21

La segunda tanda de observaciones del responsable. Lo que es **corregir lo que ya existe** se hizo
en la misma sesión: está en el apartado 10. Lo que cambia el modelo o necesita un caso de uso está
en los apartados 11 a 15 y **espera aprobación**.

## 10. Hecho sin consulta: correcciones

| Observación | Causa | Qué se hizo |
| --- | --- | --- |
| Avanzar un pedido y arrepentirse tardan demasiado | Cada correo salía por SMTP **dentro** del pedido HTTP: 1 a 3 segundos por correo, y el arrepentimiento manda dos | Los avisos salen en un hilo propio después del commit (`apps/core/segundo_plano.py`). Son 27 lugares; lo que necesita saber si el correo salió (pedido a proveedor, activación) sigue igual. B-00-022 |
| Elementos muy juntos (mostrador, arrepentimiento, diálogos y otras 14) | `pila-4` se usaba en **17 plantillas y no existía** en la hoja | Se definió, y una prueba nueva falla si una plantilla usa una clase que la hoja no define. B-00-021 |
| Guardar y Quitar de Restock a distinta altura | Las celdas de las tablas se alineaban arriba y los controles quedaban más bajos que el texto | Toda tabla alinea al medio; el campo y su botón comparten fila |
| Quitar en el carrito y en Restock | Texto suelto al lado de la cantidad | Botón de ícono (papelera) del mismo alto que el control de cantidad, con su nombre en `aria-label` |
| «Iniciar sesión» y «Comprar como invitado» de distinto tamaño | Cada botón medía lo que su texto | Las acciones de un resumen lateral van a lo ancho |
| «Cambiar la contraseña» no entra en su botón | Botón con relleno del público en una columna de 18rem | Mismo arreglo; el código de cliente repetido sale de esa columna porque ya está en el carnet |
| Stock en local con otra lista | Usaba las líneas del carrito | Tarjetas de la lista de pedidos; la tarjeta entera elige el artículo y la acción queda separada abajo |
| Botón de arrepentimiento en la barra de arriba | — | Pasa al pie, como botón destacado en todas las páginas (Res. 424/2020: visible y de fácil acceso). B-09-009 |
| La confirmación del arrepentimiento | El código salía en una fila con un «·» suelto | El código grande, para copiarlo o dictarlo, y lo devuelto al lado |

## 11. Venta de mostrador: estado y modalidad propios

**Qué pasa hoy.** La venta de mostrador nace como `Pedido` con estado **Despachado** y modalidad
**Envío a domicilio** (el valor por defecto). En «Mi cuenta» aparece como un envío con su riel
completo, y en cualquier conteo por estado se mezcla con lo que salió por correo.

**Qué dice la especificación.** `CO-082`, postcondición (c): «pe.estado en Despachado (…) estado del
ítem en Despachado». Cambiarlo es una **corrección del contrato**.

| # | Propuesta | Alternativa |
| --- | --- | --- |
| 11.1 | Estado nuevo del pedido **«Vendido en el local»** (`vendido_en_local`), terminal, sólo para el canal presencial | Mantener Despachado y separar sólo por canal (no arregla la confusión en pantallas ni en la auditoría) |
| 11.2 | Modalidad nueva **«Mostrador»**, sólo para el canal presencial. Una restricción en la base ata canal, modalidad y estado | Dejar la modalidad vacía en lo presencial |
| 11.3 | Estado del ítem **«Entregado en el local»** | Mantener «Despachado» en el ítem |
| 11.4 | Migración de datos: las ventas presenciales existentes pasan a los valores nuevos | — |
| 11.5 | En «Mi cuenta» la compra en el local va al historial, sin riel: «Compra en el local» con su detalle | — |
| 11.6 | La garantía la admite igual que un pedido entregado; el arrepentimiento no (Ley 24.240, art. 34: sólo ventas a distancia) | — |

## 12. Historial de ventas del cajero

**No hay caso de uso** que lo cubra: `CU-CAJ-CIE` consolida la jornada y `CU-REP-GEN` (reportes)
está pendiente. Lo que ya existe: el comprobante de cada venta (`CO-082`) y el detalle de cada
cierre anterior con sus transacciones.

| Opción | Qué es | Caso de uso |
| --- | --- | --- |
| **(a) Recomendada** | En Caja, **«Ventas de la jornada»**: cada venta sin cerrar con hora, cliente, medio, total y enlace a su comprobante, con filtro por medio. En «Cierres anteriores», lo mismo por cierre | Consulta dentro de `CU-CAJ-CIE`: el A2 ya habla del «detalle de cada transacción individual del día». Se registra como agregado |
| (b) | Un historial de cualquier fecha con búsqueda | Es un reporte: va con `CU-REP-GEN` |

## 13. Interfaz del cajero: mostrador y cierre

Ideas de los puntos de venta más usados (Square, Shopify POS, Tiendanube POS), dentro de Viñeta
Nocturna:

| # | Qué | Por qué |
| --- | --- | --- |
| 13.1 | **El total como protagonista**: la cifra grande, un campo «Recibido» que calcula el **vuelto** si es efectivo, y los medios de pago como **tarjetas de opción** grandes con ícono | Se cobra mirando la pantalla de reojo; el vuelto es una cuenta que hoy hace el cajero |
| 13.2 | **Atajos de teclado**: `F2` al buscador, `Enter` agrega, `F9` confirma la venta; se muestran en la pantalla | El lector de código de barras escribe y da Enter: el cajero no toca el mouse |
| 13.3 | La fila recién agregada **destella** (`destello-fila`, ya en el catálogo) y el total hace `rebote-numero` | Confirma que el escaneo entró |
| 13.4 | Portada en miniatura en cada fila del ticket | Se reconoce el tomo sin leer |
| 13.5 | Caja: **recuadros de cifra** por medio de pago con su ícono y una barra de proporción; el total grande; el botón de cierre con su consecuencia escrita | Hoy es una tabla de texto plano |
| 13.6 | Después de confirmar, **«Venta registrada»** con el total, el vuelto, «Imprimir comprobante» y «Nueva venta» con el foco | El cajero sabe que terminó y arranca la siguiente con una tecla |

## 14. Restock

El mensaje quedó cortado en «revisemos lo del…» (ambigüedad 4). Lo que se propone para la
pantalla:

| # | Qué | Por qué |
| --- | --- | --- |
| 14.1 | Arriba, **recuadros de cifra**: productos, unidades a pedir, proveedores y suscriptores esperando | Se ve el tamaño de la propuesta antes de recorrerla |
| 14.2 | Cada proveedor en un bloque **plegable**, con su cantidad de productos y unidades en el título | Una propuesta automática trae cientos de filas |
| 14.3 | **Un solo «Guardar cantidades»** por proveedor en vez de un Guardar por fila | Hoy cambiar diez cantidades son diez envíos |
| 14.4 | Filtro dentro de la propuesta y orden por suscriptores | Primero lo que la gente está esperando |
| 14.5 | La portada en miniatura y el stock con su rótulo («Sin stock», «Stock bajo») | Se decide más rápido |

## 15. Suscripciones de reposición del Cliente

En «Mi cuenta», una sección **«Avisos de stock»**: cada producto que el Cliente pidió que le
avisen, desde cuándo, si sigue esperando o ya se le avisó, con «Cancelar aviso» (`CO-076`, el mismo
que hoy está en la ficha). La especificación ya lo prevé: `CU-RST-SUS`, postcondiciones, «la
suscripción permanece activa (…) hasta que el Cliente la cancele manualmente». Es un **agregado**:
otro lugar desde donde ejecutar el A1.

## 16. Otras mejoras de usabilidad propuestas

Para elegir. Las del primer plan (P1 a P7) siguen sin elegir.

| # | Qué | Inspirado en |
| --- | --- | --- |
| U1 | **Buscador con sugerencias**: al escribir, las primeras 5 coincidencias con portada y precio | Buscalibre, Mercado Libre |
| U2 | **Carrito lateral**: al agregar, un panel con lo agregado y «Ir a pagar», sin salir de la página | Tiendanube, Shopify |
| U3 | **Botón cargando** en todos los envíos (P3): evita el doble clic en el pago | — |
| U4 | **Portada de reemplazo diseñada** (P2): sin imagen, las listas parecen rotas | — |
| U5 | En el operativo, **contadores en el menú**: pedidos por armar, devoluciones abiertas, propuesta de restock pendiente | Paneles de Shopify y Tiendanube |

## 17. Ambigüedades de la segunda parte

| # | Pregunta |
| --- | --- |
| 1 | ¿Se aprueba el apartado 11 (estado, modalidad e ítem nuevos para la venta de mostrador)? ¿Los nombres? |
| 2 | Historial de ventas: ¿(a) o (b)? |
| 3 | ¿Qué del apartado 13 y del 14? |
| 4 | Restock: ¿qué querías revisar («revisemos lo del…»)? |
| 5 | ¿Se aprueba el apartado 15? |
| 6 | ¿Cuáles de U1 a U5 y de P1 a P7? |

---

# Tercera parte — pre-ventas, precios programados y el bot de Telegram

**Estado:** Propuesta · **Fecha:** 2026-10-21

## 21. Hecho sin consulta

| Observación | Causa | Qué se hizo |
| --- | --- | --- |
| Los documentos visuales no decían lo que el código hace | Las enmiendas del apéndice A y de B-00-023 estaban pendientes | Aplicadas en `TOKENS_VISUALES.md` e `identidad_visual.md` por autorización del responsable: telón difuminado, las tres animaciones del riel, el envío como acción, botón de ícono, tarjeta de opción, confirmaciones en diálogo, riel, barra de proporción, contador del menú y los componentes del público. B-00-018, B-00-019 y B-00-023, resueltas |
| En `/pedidos/` el estado y el riel se enciman | Iban en la misma celda | Columna propia «Seguimiento»; la venta de mostrador muestra «—» |
| En `/cuenta/avisos/` «Cancelar aviso» no hace nada | El enlace que cubre la tarjeta entera quedaba **encima** del botón: el clic abría la ficha del producto. La prueba no lo vio porque envía el formulario sin hacer clic | Lo que se puede tocar dentro de la tarjeta queda por encima del enlace. Verificado en Chrome: bajo el centro del botón está el botón. B-00-024 |

## 22. Pre-ventas: calendario y pantalla

Hoy la pantalla «Pre-ventas por llegar» es una sucesión de tablas por fecha y editorial, sin
resumen y sin una vista del mes.

| # | Qué | Por qué |
| --- | --- | --- |
| 22.1 | **Cifras** arriba: productos en pre-venta, unidades reservadas, llegan esta semana, atrasados | El tamaño de lo que viene, antes de recorrerlo |
| 22.2 | **Calendario del mes**: una grilla de lunes a domingo con, en cada día, las editoriales que llegan y cuántos productos. Hoy con borde de señal, lo atrasado con su rótulo. Un día lleva a su grupo. «Mes anterior» y «Mes siguiente» por dirección (`?mes=2026-11`): funciona sin guion | Se planifica la semana y se ve qué se atrasó |
| 22.3 | Cada fecha y editorial, un **bloque plegable** como en Restock, con portadas, reservadas y en el local | Hoy son tablas largas una detrás de otra |
| 22.4 | El rótulo de cada grupo dice cuándo: «Atrasado», «Llega hoy», «Llega en 3 días» | Una palabra en vez de una fecha para calcular |

El calendario es un **patrón nuevo** para `identidad_visual.md` («un calendario (…) no se
improvisa»). Propuesta: celdas cuadradas con `--trazo` `--linea`, el número del día en
`--fuente-datos`, los días de otro mes en `--texto-2`, hoy con `--trazo-fuerte` `--acento`, y en cada
día con llegadas una ficha por editorial con su cantidad. En el celular, la grilla pasa a una lista
de los días con llegadas.

## 23. Cambios de precio programados desde las tablas

**Qué hay hoy.** Modificar un precio de referencia (`CU-PVP-TBM`) cambia el PVP de la combinación
en el acto, y con él el de los productos vinculados. Las ofertas (`CU-PVP-ALT` a `CU-PVP-CON`) sí
tienen fechas: nacen Programadas, el Temporizador las activa el día de inicio y las vence el día
de fin.

**Por qué no alcanza con una oferta.** Una oferta es un **descuento con vencimiento** sobre el
precio: al vencer, el precio vuelve. Un aumento de lista es **permanente** y cambia el precio base
sobre el que después se calculan las ofertas. Usar una oferta «negativa» rompería el «Antes / Ahora»
de la tienda y los informes de descuento.

**Qué se puede hacer con la lógica de las ofertas.**

| # | Propuesta |
| --- | --- |
| 23.1 | Un concepto nuevo, **Cambio de precio programado**: combinación, PVP nuevo, fecha de vigencia, estado (Programado, Aplicado, Cancelado) y quién lo programó |
| 23.2 | En la tabla de precios, junto a «Modificar», **«Programar»**: el mismo formulario más la fecha. La tabla muestra el próximo cambio de cada combinación |
| 23.3 | El **Temporizador lo aplica** el día de vigencia, ejecutando exactamente la modificación de `CU-PVP-TBM`, con sus efectos sobre los productos vinculados y su auditoría, con el sistema como actor |
| 23.4 | **Uno programado por combinación a la vez**, con una restricción en la base. Si la combinación se dio de baja antes de la fecha, el cambio se cancela solo y se avisa al Administrador |
| 23.5 | Se cancela desde la tabla mientras esté Programado |

**Qué necesita.** No hay caso de uso ni contrato que lo cubra: un concepto nuevo en el modelo de
dominio y, como mínimo, programar, cancelar y aplicar. Puede ser un flujo alternativo de
`CU-PVP-TBM` o un caso de uso propio; **el código lo asignás vos**. Una sesión de trabajo.

## 24. El camino para el bot de Telegram

**La especificación no lo menciona**: no hay caso de uso, contrato ni requerimiento. Antes de
construir comportamiento hacen falta los casos de uso. Lo que sí se puede preparar ahora, sin cambiar
nada de lo que el sistema hace, y lo que habría que decidir.

### Qué podría hacer

| Para | Funciones candidatas |
| --- | --- |
| Cliente | Vincular su cuenta desde «Mi cuenta» (un enlace `t.me/…?start=<código>` de un solo uso). Recibir por Telegram los avisos que hoy recibe por correo: estado del pedido, aviso de stock, pre-venta que llegó, puntos por vencer. Consultar sus pedidos y buscar en el catálogo |
| Administrador | Alertas: pedidos por armar, correo nuevo de proveedor, reclamo de devolución, propuesta de restock lista. El resumen de la caja al cerrar |

### Qué se puede preparar sin casos de uso

| # | Pieza | Qué cambia hoy |
| --- | --- | --- |
| 24.1 | **Un aviso con canales.** Hoy cada aviso arma su correo por su cuenta. Se separa el *qué* (destinatario, asunto, texto, enlace) del *por dónde*, con un despachador por canal: el correo hoy; Telegram cuando exista. Todos los avisos ya pasan por `despues_del_commit` (B-00-022), que es el punto natural | Nada visible: los mismos correos, con las mismas pruebas |
| 24.2 | La salida a la API de Telegram por la **única puerta HTTP** (`integraciones.pedir`), para que la red cortada de las pruebas la cubra desde el primer día | Nada |
| 24.3 | Las variables de configuración (`TELEGRAM_BOT_TOKEN`, el secreto del webhook) en `.env.example`, vacías: sin token, el canal no existe | Nada |

### Qué hay que decidir

| # | Decisión | Lecturas |
| --- | --- | --- |
| 1 | ¿Qué funciones entran? | **(a)** Sólo avisos al Cliente y alertas al Administrador (salida). **(b)** Además consultas (pedidos, catálogo). **Recomiendo (a)** para noviembre: es lo que más valor da con menos superficie |
| 2 | Los casos de uso | Como mínimo: vincular la cuenta con Telegram, desvincularla y elegir los canales de aviso. **Los códigos los asignás vos** |
| 3 | Webhook o consulta periódica | El webhook necesita una dirección pública con HTTPS. **Recomiendo** webhook en producción y, en desarrollo, un comando que consulte las novedades, como la casilla de proveedores |
| 4 | Datos personales | El identificador del chat es un dato personal: la baja de la cuenta (`CU-CLI-BAJ`, pendiente) tiene que borrar el vínculo |

**Esfuerzo**: 24.1 a 24.3, media sesión. El bot de la opción (a), con sus casos de uso, dos
sesiones más.

## 25. Ambigüedades de la tercera parte

| # | Pregunta |
| --- | --- |
| 1 | ¿Se aprueba el apartado 22 y el patrón del calendario? ¿También un **calendario público de lanzamientos** en la tienda, con el mismo componente, de sólo lectura? |
| 2 | Cambios de precio programados: ¿se hacen? Si sí, ¿flujo alternativo de `CU-PVP-TBM` o caso de uso propio, y con qué códigos? |
| 3 | Telegram: ¿se aprueba preparar 24.1 a 24.3 ahora? ¿Qué opción de funciones, y los casos de uso? |
