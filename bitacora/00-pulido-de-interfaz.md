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
