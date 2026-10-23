> **Tipo: Bitácora.** Se anexa, no se reescribe.

# Bitácora — `00` Pulido de interfaz

> Registro de lo que se decidió construyendo este módulo. **Se anexa, no se reescribe.**
> Una entrada resuelta se marca; no se borra.
>
> Este archivo es el material que el responsable lee para decidir qué se enmienda en el documento
> de análisis. Escribí para alguien que conoce el dominio y no tiene el código a la vista.

El plan es [docs/planes/00-pulido-de-interfaz.md](../docs/planes/00-pulido-de-interfaz.md). El
defecto del pedido «En el local» en «Mi cuenta» está en `bitacora/11-cuenta-de-cliente.md`,
B-11-006.

---

## Entradas

### B-00-018 · El telón difuminado y las tres animaciones del riel esperan su enmienda

**Tipo:** Corrección · **Fecha:** 2026-10-21 · **Alcance:** `TOKENS_VISUALES.md`, `identidad_visual.md`
**Estado:** Resuelta el 2026-10-21 — enmendado en los documentos visuales por autorización del responsable

**Qué apareció.**
El responsable pidió un fondo difuminado detrás de las confirmaciones y un camión que recorra el
seguimiento del pedido. Las dos cosas las prohibían los documentos visuales tal como están.

**Qué dice la especificación.**
> «Prohibido: `box-shadow` con desenfoque, `border-radius`, gradientes suaves de color como fondo
> (…), `backdrop-filter`.» (`TOKENS_VISUALES.md`, «Forma»)

> «No se crean animaciones fuera de esta lista; si hace falta una, se pide.»
> (`identidad_visual.md`, «Catálogo de animaciones»)

**Qué se hizo.**
El `::backdrop` del diálogo lleva `blur(4px)` sobre la noche al 70 % con la trama, y es el único
desenfoque del sistema. El catálogo suma `riel-llena`, `camion-avanza` y `sello`, sólo en el
público y una vez por estado. La prueba del estilo ya admite exactamente eso y nada más.

**Qué habría que cambiar.**
Los textos del apéndice A del plan, en `TOKENS_VISUALES.md` («Forma») y en `identidad_visual.md`
(«Catálogo de animaciones», «Botones» y «Formularios»). Hasta que estén, la prueba y los
documentos dicen cosas distintas.

---

### B-00-019 · El diálogo toma la pantalla de confirmación entera, no una copia

**Tipo:** Agregado · **Fecha:** 2026-10-21 · **Alcance:** las 17 confirmaciones de dos tiempos
**Estado:** Resuelta el 2026-10-21 — enmendado en los documentos visuales por autorización del responsable

**Qué apareció.**
Pasar las confirmaciones a diálogos podía duplicar cada una: una versión para el diálogo y otra
para cuando no hay guion, que con el tiempo dirían cosas distintas.

**Qué dice la especificación.**
`Nada` sobre cómo se arma el diálogo. `identidad_visual.md` fija su aspecto («Diálogos»).

**Qué se hizo.**
El diálogo muestra el mismo bloque de la pantalla de confirmación, pedido a su misma dirección, y
el formulario se envía ahí. Sin guion, o si el pedido falla, se navega a la pantalla como antes.
El servidor recibe lo mismo en los dos casos, así que ningún contrato cambia. La confirmación del
ingreso de pre-ventas queda como pantalla: se llega con un formulario, no con un enlace.

**Qué habría que cambiar.**
`identidad_visual.md`, «Diálogos»: «Una confirmación de dos tiempos se abre en un diálogo cuando
hay guion; sin guion, es su pantalla.»

---

### B-00-020 · «Pedidos activos» e «Historial» se juntan en «Pedidos», y la portada es un resumen

**Tipo:** Agregado · **Fecha:** 2026-10-21 · **Alcance:** `CU-CLI-HIS`, `CO-192`
**Estado:** Abierta — decidida por el responsable el 2026-10-21 (plan 00 de interfaz, amb. 6)

**Qué apareció.**
Dos pestañas para una misma lista de pedidos, partida por estado, y el código de cliente perdido
en un antetítulo.

**Qué dice la especificación.**
> «En la sección Historial de Pedidos: el sistema lista los pedidos completados y cancelados.»
> (`CU-CLI-HIS`, paso 5)

No fija cuántas pantallas son.

**Qué se hizo.**
«Mi cuenta» abre en un resumen con los pedidos en curso. «Pedidos» muestra los en curso y, debajo,
el historial. A la izquierda queda un carnet con el código de cliente, el saldo con su próximo
vencimiento y lo guardado en el local. La dirección del historial anterior lleva al grupo del
historial, para los enlaces ya enviados.

**Qué habría que cambiar.**
`CU-CLI-HIS` paso 2: las secciones son Resumen, Pedidos, Puntos, Stock en local y Mis datos.

---

### B-00-021 · Una clase que no existía dejaba diecisiete pantallas sin espacio entre sus partes

**Tipo:** Corrección · **Fecha:** 2026-10-21 · **Alcance:** la hoja de componentes
**Estado:** Resuelta el 2026-10-21

**Qué apareció.**
El panel de cobro del mostrador, el arrepentimiento, los diálogos y otras catorce pantallas tenían
los elementos pegados. Usaban `pila-4`, que la hoja nunca definió: una clase inexistente no da
error, sólo no dibuja nada. Además, las tablas alineaban sus celdas arriba, y un campo o un botón
dentro de una fila quedaba más bajo que el texto (Guardar y Quitar de Restock).

**Qué dice la especificación.**
`TOKENS_VISUALES.md`, «Espaciado»: `--esp-4`, 16px, «campos de un formulario». No dice nada de la
clase.

**Qué se hizo.**
Se definió `pila-4`, las celdas alinean al medio y una prueba falla si una plantilla usa una clase
que la hoja no define.

**Qué habría que cambiar.**
`Nada`.

---

### B-00-022 · Los avisos por correo salen en segundo plano

**Tipo:** Agregado · **Fecha:** 2026-10-21 · **Alcance:** todos los avisos por correo
**Estado:** Abierta

**Qué apareció.**
Avanzar un pedido tardaba varios segundos y abrir un arrepentimiento, más. Cada correo salía por
SMTP dentro de la misma operación: conexión, cifrado y autenticación, de uno a tres segundos por
correo, y la pantalla esperaba a todos.

**Qué dice la especificación.**
`Nada` sobre si el aviso es parte de la operación. Los contratos declaran el aviso como una
postcondición más; su falla ya no deshacía la operación (B-08-002).

**Qué se hizo.**
Cuando la operación se confirma, sus avisos salen en un hilo propio y la pantalla responde en el
acto. Lo que necesita saber si el correo salió —el pedido a proveedor con sus reintentos, el enlace
de activación— sigue esperando como antes. Un comando de consola espera a que sus avisos terminen.

**Qué habría que cambiar.**
Requerimientos no funcionales: «los avisos por correo no demoran la respuesta de la operación que
los origina».

---

### B-00-023 · Botón de ícono para quitar una fila

**Tipo:** Agregado · **Fecha:** 2026-10-21 · **Alcance:** `identidad_visual.md`, «Botones»
**Estado:** Resuelta el 2026-10-21 — enmendado en los documentos visuales por autorización del responsable

**Qué apareció.**
«Quitar» en el carrito y en la propuesta de restock era un texto suelto al lado de la cantidad, a
otra altura. El responsable pidió una papelera alineada.

**Qué dice la especificación.**
`Nada`: la jerarquía de botones no tiene un botón de ícono.

**Qué se hizo.**
Un botón cuadrado del mismo alto que el control de cantidad, con la papelera y su nombre en
`aria-label` y `title`; al pasar el puntero, pasa al color de error.

**Qué habría que cambiar.**
`identidad_visual.md`, «Botones»: «Botón de ícono (`.boton-icono`): una acción de fila que se
reconoce por su ícono, como quitar. Lleva su nombre en `aria-label`. Con `--critico`, el puntero
lo pasa a `--error`.»

---

### B-00-024 · El enlace que cubre la tarjeta tapaba sus botones

**Tipo:** Corrección · **Fecha:** 2026-10-21 · **Alcance:** las tarjetas de «Mi cuenta»
**Estado:** Resuelta el 2026-10-21

**Qué apareció.**
En «Avisos de stock», «Cancelar aviso» no hacía nada: el clic abría la ficha del producto. La
tarjeta lleva un enlace que la cubre entera para que se pueda tocar en cualquier lado, y quedaba
por encima del botón. La prueba enviaba el formulario directo y no lo veía.

**Qué dice la especificación.**
`Nada`.

**Qué se hizo.**
Lo que se puede tocar dentro de una tarjeta queda por encima de ese enlace. Se verificó en el
navegador qué elemento recibe el clic, y una prueba impide que la regla se pierda.

**Qué habría que cambiar.**
`Nada`.

---

### B-00-025 · Calendario de las pre-ventas por llegar

**Tipo:** Agregado · **Fecha:** 2026-10-22 · **Alcance:** `CU-ALT-TRA`, `identidad_visual.md`
**Estado:** Resuelta el 2026-10-22 — patrón agregado a `identidad_visual.md`

**Qué apareció.**
La pantalla de pre-ventas por llegar era una sucesión de tablas por fecha y editorial, sin un
resumen ni una vista del mes. El responsable pidió un calendario.

**Qué dice la especificación.**
> «Si una pantalla necesita un patrón que no está descrito (un gráfico de reportes, un calendario,
> arrastrar y soltar), no se improvisa.» (`identidad_visual.md`)

**Qué se hizo.**
Arriba, las cifras (productos, unidades reservadas, lo que llega esta semana y lo atrasado) y el
calendario del mes, armado con los mismos grupos que la lista: cada llegada lleva a su grupo. Cada
grupo es un bloque plegable que dice cuándo llega con palabras («Atrasado», «Llega hoy», «Llega en
3 días») y queda abierto si es de la próxima semana. El ingreso sigue siendo el mismo (`CO-013`).
El calendario público de lanzamientos quedó sin decidir.

**Qué habría que cambiar.**
`CU-ALT-TRA` paso 4: «el sistema presenta las pre-ventas en un calendario del mes y agrupadas por
fecha de llegada y editorial».


---

### B-00-026 · Imágenes ordenables con «Usar como portada», visor en la tienda y calendario que se usa

**Tipo:** Agregado · **Fecha:** 2026-10-22 · **Alcance:** `CU-CAT-EDI` (`CO-030`), `CU-TDA-CAT`, `CU-ALT-TRA` (`CO-013`)
**Estado:** Abierta — plan 00 de interfaz, cuarta parte, C, D y E

**Qué apareció.**
Pedidos del responsable: las imágenes de un producto se manejaban con casillas sueltas y un campo
de archivo sin vista de la portada; en la tienda se abrían en otra pestaña; y el calendario de
pre-ventas sólo se miraba.

**Qué dice la especificación.**
Nada sobre el orden de las imágenes, el visor ni la interacción del calendario.

**Qué se hizo.**
- **Edición:** la portada y las adicionales en una grilla. Las adicionales se ordenan arrastrando
  o con flechas; cada una ofrece «Usar como portada», que **intercambia** (decisión del
  responsable): la portada anterior queda entre las adicionales, y ningún archivo se borra. La
  portada tiene su «Quitar». Las nuevas se ven antes de guardar. El historial registra el cambio
  de portada y el nuevo orden.
- **Tienda:** un visor con la imagen grande y miniaturas que la cambian; tocarla la amplía en un
  diálogo con flechas, teclado y deslizamiento.
- **Pre-ventas:** el mes cambia sin recargar; tocar una llegada abre su grupo y deja el foco en su
  primer campo; cada grupo ofrece «Completar con lo reservado»; lo que llega esta semana se
  distingue de lo atrasado.
- El menú ya no muestra «Próximamente»: con Reportes no queda ningún módulo por construir.

**Qué habría que cambiar.**
Nada en los casos de uso.

---

### B-00-027 · Lo que la revisión del responsable encontró en la cuarta parte

**Tipo:** Corrección · **Fecha:** 2026-10-22 · **Alcance:** plan 00 de interfaz, cuarta parte (C, D, E)
**Estado:** Resuelta el 2026-10-22

**Qué apareció.**
El responsable revisó la cuarta parte y encontró:

- La gestión de imágenes de la edición se veía rota, con imágenes a escala completa.
- La ampliación cambiaba también la imagen de fondo.
- La ficha del backoffice no tenía el visor.
- El calendario se veía pobre y no tenía «Hoy».
- El alta rápida de etiquetas dejaba la pantalla cargando, con un diálogo chico.
- La ficha pública decía «Sinopsis» para cualquier producto.

**Qué dice la especificación.**
Nada: son defectos de construcción.

**Qué se hizo.**
- **La causa común de la «pantalla rota».** La hoja de estilos no llevaba versión, y el navegador
  seguía usando la vieja. Ahora cada hoja y cada guion llevan la fecha del archivo en su
  dirección.
- **Capa de carga.** La de la pantalla operativa ya no aparece cuando un guion toma el envío de un
  formulario, ni en el formulario de un diálogo: eso dejaba la pantalla cargando para siempre.
- **Altas rápidas.** El alta de etiquetas y la de editorial, tipo y formato usan un diálogo del
  sistema, más ancho, con errores en el lugar y un estado «Creando…». Desaparecen `prompt`,
  `confirm` y `alert` del navegador.
- **Gestor de imágenes.** Es dueño de la portada y de las adicionales: tarjetas compactas con su
  barra de acciones, una zona para soltar imágenes nuevas y vista previa de todo.
- **Visor compartido.** El mismo visor en la ficha de la tienda y en la del backoffice. La
  ampliación tiene su propio índice, flechas, la tira de miniaturas, teclado y deslizamiento.
- **Calendario.** Celdas separadas, el número de hoy destacado, fichas con una barra de estado y
  su leyenda, y «Hoy».
- **«Descripción»** en lugar de «Sinopsis». La ficha del producto muestra los suscriptores de
  reposición, que decía «No disponible todavía» desde antes de que existiera Restock.

**Qué habría que cambiar.**
Nada.
